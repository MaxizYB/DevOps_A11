"""Independently exercise the four E14 services for Issue #44."""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "labs/e13e14"))

from orchestrate import PORTS, container_path
from verify_evidence import verify

STAGES = ("draft", "full-check", "incremental-check", "repair", "recheck")
ROLE_COUNTS = {"draft": 1, "buildchecker": 3, "echecker": 1, "mdfixer": 1}


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def require(condition, message):
    if not condition:
        raise ValueError(message)


class Evidence:
    def __init__(self, out):
        self.out = out
        self.events = []

    def command(self, name, argv, expected=0):
        result = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, timeout=900)
        (self.out / (name + ".stdout.log")).write_text(result.stdout, encoding="utf-8")
        (self.out / (name + ".stderr.log")).write_text(result.stderr, encoding="utf-8")
        self.events.append({"name": name, "argv": argv, "exit": result.returncode, "expected": expected})
        save(self.out / "commands.json", self.events)
        require(result.returncode == expected, f"{name}: exit {result.returncode}, expected {expected}")
        return result.stdout

    def probe_http(self, rejected_path):
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        records = []
        for role, port in PORTS.items():
            outside = {
                "project": "/course/data",
                "out": rejected_path,
                "job_id": "issue44-http-probe",
                "trace_id": "issue44-http-probe",
            }
            probes = (
                ("health", "GET", "/health", None, 200, {"status": "ok", "role": role}),
                ("unknown-route", "GET", "/issue44-unknown", None, 404, {"error": "NOT_FOUND"}),
                ("invalid-json", "POST", "/v1/run", b"{", 422, {"error_code": "JSONDECODEERROR"}),
                ("invalid-path", "POST", "/v1/run", json.dumps(outside).encode(), 422,
                 {"error_code": "VALUEERROR", "error": "Path must be inside /course/work"}),
            )
            for name, method, route, body, status, expected in probes:
                url = f"http://127.0.0.1:{port}{route}"
                request = urllib.request.Request(url, data=body, method=method,
                                                 headers={"Content-Type": "application/json"})
                try:
                    with opener.open(request, timeout=10) as response:
                        actual_status, response_body = response.status, response.read().decode()
                except urllib.error.HTTPError as error:
                    with error:
                        actual_status, response_body = error.code, error.read().decode()
                records.append({"role": role, "probe": name, "url": url, "method": method,
                                "request_body": body.decode() if body else None,
                                "status": actual_status, "body": response_body})
                save(self.out / "http.json", records)
                actual = json.loads(response_body)
                require(actual_status == status and all(actual.get(k) == v for k, v in expected.items()),
                        f"{role} {name}: unexpected response")
        return len(records)


def inspect_services(evidence, compose):
    configurations = {}
    # Keep only settings needed for this audit. Container environment can hold credentials.
    fields = ("Id", "Image", "Config.User", "State.Health.Status", "HostConfig.PortBindings",
              "HostConfig.NanoCpus", "HostConfig.Memory", "HostConfig.PidsLimit",
              "HostConfig.SecurityOpt", "HostConfig.Privileged", "HostConfig.CapAdd", "Mounts")
    inspect_format = "\t".join("{{json ." + field + "}}" for field in fields)
    for role, port in PORTS.items():
        container = evidence.command(role + "-container", compose + ["ps", "-q", role]).strip()
        require(re.fullmatch(r"[0-9a-f]{64}", container), f"{role}: expected one Compose container")
        values = evidence.command(role + "-inspect", ["docker", "inspect", "--format", inspect_format, container])
        cfg = dict(zip(fields, (json.loads(value) for value in values.strip("\n").split("\t"))))
        configurations[role] = cfg
        save(evidence.out / "containers.json", configurations)
        require(cfg["State.Health.Status"] == "healthy", f"{role}: unhealthy")
        require(cfg["HostConfig.PortBindings"] == {"8080/tcp": [{"HostIp": "127.0.0.1", "HostPort": str(port)}]},
                f"{role}: unexpected host binding")
        require(cfg["HostConfig.NanoCpus"] == 10**9 and cfg["HostConfig.Memory"] == 768 * 1024**2
                and cfg["HostConfig.PidsLimit"] == 128, f"{role}: unexpected resource limits")
        require(cfg["Config.User"] == "0:0" and not cfg["HostConfig.Privileged"]
                and "no-new-privileges:true" in cfg["HostConfig.SecurityOpt"],
                f"{role}: unexpected security settings")
        require(set(cfg["HostConfig.CapAdd"] or []) == ({"CAP_SYS_PTRACE"} if role == "buildchecker" else set()),
                f"{role}: unexpected capabilities")
        mounts = {mount["Destination"]: mount for mount in cfg["Mounts"]}
        require(set(mounts) == ({"/course", "/var/run/docker.sock"} if role == "draft" else {"/course"}),
                f"{role}: unexpected mounts")
        require(Path(mounts["/course"]["Source"]).resolve() == ROOT, f"{role}: unexpected course mount")
    require(len({cfg["Id"] for cfg in configurations.values()}) == len(PORTS), "Roles share a container")
    require(len({cfg["Image"] for cfg in configurations.values()}) == 1, "Roles used different images")
    return configurations


def verify_artifacts(folder):
    result = read(folder / "result.json")
    require([stage["name"] for stage in result["stages"]] == list(STAGES), f"{folder}: wrong stage order")
    identity = (result["job_id"], result["trace_id"])
    present = {p.relative_to(folder).as_posix() for p in folder.rglob("*")
               if p.is_file() and not p.is_symlink() and ".git" not in p.parts and p != folder / "result.json"}
    listed = [item["uri"] for item in result["artifacts"]]
    require(len(listed) == len(present) and set(listed) == present, f"{folder}: missing or duplicate artifacts")
    for stage in result["stages"]:
        item = read(folder / stage["artifact"]["uri"])
        commit = result["base_commit"] if stage["name"] == "full-check" else result["target_commit"]
        require((item["job_id"], item["trace_id"]) == identity and item["commit"] == commit,
                f"{folder}: stage identity mismatch")
    verified = verify(folder)
    verified["unique_artifact_files"] = len(listed)
    verified["base"] = result["base_commit"]
    verified["remaining_rd"] = [
        item for item in read(folder / "final-full/findings.json")["findings"] if item["type"] == "REDUNDANT"
    ]
    return verified


def verify_role_logs(evidence, compose, folder, results):
    counts = Counter()
    for role in PORTS:
        raw = evidence.command(role + "-service", compose + ["logs", "--no-color", "--no-log-prefix", role])
        for line in raw.splitlines():
            if not line.startswith("{"):
                continue
            event = json.loads(line)
            for name, result in results.items():
                if (event.get("job_id"), event.get("trace_id")) != (result["job_id"], result["trace_id"]):
                    continue
                require(event["role"] == role, "Service log role mismatch")
                if name == "timeout":
                    require(event["status"] == "FAILED" and event["error_code"] == "TIMEOUT",
                            "Timeout log must show failure")
                else:
                    require(event["status"] == "SUCCEEDED", f"{role}: unexpected {name} status")
                counts[name, role] += 1
    verified = {name: {role: counts[name, role] for role in PORTS} for name in results}
    save(folder / "role-log-counts.json", verified)
    for name, actual in verified.items():
        expected = {role: int(role == "draft") for role in PORTS} if name == "timeout" else ROLE_COUNTS
        require(actual == expected, f"{name}: service log counts {actual}, expected {expected}")
    return verified


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--successful-run", required=True, type=Path, help="Existing successful run of this request")
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--project", required=True, help="Running dedicated Compose project")
    args = parser.parse_args()
    out = args.out.resolve()
    require(out.is_relative_to(ROOT / "work") and out != ROOT / "work", "Use a new folder below work/")
    out.mkdir(parents=True)
    evidence = Evidence(out)
    compose = ["docker", "compose", "-f", "labs/e13e14/compose.yaml", "-p", args.project]
    require(Path(os.environ["E14_ROOT"]).resolve() == ROOT, "E14_ROOT must be this worktree")
    request = read(args.request)
    first = args.successful_run.resolve()
    require(first.is_relative_to(ROOT / "work") and read(first / "request.json") == request,
            "Existing run must use the same request")
    configs = inspect_services(evidence, compose)
    rejected = out / "rejected-request"
    probe_count = evidence.probe_http(container_path(rejected))
    require(not rejected.exists(), "Rejected HTTP request created output")
    timeout_request = out / "timeout-request.json"
    save(timeout_request, {**request, "build_timeout": 0.01})
    run = [sys.executable, "labs/e13e14/orchestrate.py"]
    timeout_folder = out / "timeout"
    evidence.command("timeout", run + ["--request", str(timeout_request), "--out", str(timeout_folder)], expected=1)
    failed = read(timeout_folder / "result.json")
    inner = read(timeout_folder / "draft-build/result.json")
    response = read(timeout_folder / "draft-response.json")
    require(failed["status"] == "FAILED" and not failed["stages"] and inner["status"] == "TIMED_OUT"
            and response["http"] == 422 and json.loads(response["error"])["error_code"] == "TIMEOUT",
            "Timeout did not stop at DRAFT with HTTP 422/TIMEOUT")
    require(len(inner["attempts"]) == 1 and "verification" not in inner
            and not (timeout_folder / "draft-build/verify-container-id.txt").exists(),
            "Timeout reached candidate runtime verification")
    tag = inner["attempts"][0]["tag"]
    evidence.command("timeout-image-absent", ["docker", "image", "inspect", tag], expected=1)
    draft_top = evidence.command("draft-after-timeout",
                                 ["docker", "top", configs["draft"]["Id"], "-eo", "pid,ppid,args"])
    require(not re.search(r"\bdocker build\b", draft_top), "DRAFT has a remaining Docker build client")
    failure_sha = hashlib.sha256((timeout_folder / "result.json").read_bytes()).hexdigest()
    recovery = out / "recovery"
    evidence.command("recovery", run + ["--request", str(args.request.resolve()), "--out", str(recovery)])
    require(hashlib.sha256((timeout_folder / "result.json").read_bytes()).hexdigest() == failure_sha,
            "Recovery rewrote the timeout result")
    runs = {"initial": read(first / "result.json"), "timeout": failed, "recovery": read(recovery / "result.json")}
    for field in ("job_id", "trace_id"):
        require(len({result[field] for result in runs.values()}) == len(runs), f"Repeated {field} between runs")
    role_logs = verify_role_logs(evidence, compose, out, runs)
    evidence.command("compose-after", compose + ["ps", "--format", "json"])
    summary = {
        "http_probes": probe_count,
        "image_id": configs["draft"]["Image"],
        "initial": verify_artifacts(first),
        "timeout": {"job_id": failed["job_id"], "trace_id": failed["trace_id"],
                    "http": response["http"], "outer": failed["status"], "draft": inner["status"],
                    "error_code": "TIMEOUT", "result_sha256": failure_sha},
        "recovery": verify_artifacts(recovery),
        "role_log_counts": role_logs,
    }
    save(out / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
