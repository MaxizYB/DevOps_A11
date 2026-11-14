"""Independently verify the controlled E11-A evidence for Issue #38.

This oracle is deliberately specific to prepare.py's two-source C0/C1 dataset.
It never calls scan(), normalized(), or the producer's graph parser. The only
producer function exercised is load_artifact(), for a copied-file tamper probe.
This checks local classroom evidence; it does not certify an external project,
an ECS run, B11, or the E12 cross-team integration.
"""

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
import tempfile
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
OBJECTS = {"main.o", "helper.o"}
EXPECTED_DECLARED = {"main.o": ["main.c", "unused.h"], "helper.o": ["helper.c"]}
EXPECTED_BASE = {"main.o": ["config.h", "main.c"], "helper.o": ["helper.c"]}
EXPECTED_TARGET = {"main.o": ["config.h", "extra.h", "main.c"], "helper.o": ["helper.c"]}
BASE_FINDINGS = {("MISSING", "main.o", "config.h"), ("REDUNDANT", "main.o", "unused.h")}
TARGET_FINDINGS = BASE_FINDINGS | {("MISSING", "main.o", "extra.h")}
FULL_SHA = re.compile(r"[0-9a-f]{40}")


class VerificationError(ValueError):
    pass


class Verifier:
    def __init__(self, out):
        self.out = Path(out).resolve()
        self.checks = []
        self.artifact_count = 0
        self.trace_edges = 0

    def require(self, condition, name):
        self.checks.append({"check": name, "passed": bool(condition)})
        if not condition:
            raise VerificationError(name)

    def read(self, relative):
        return json.loads((self.out / relative).read_text(encoding="utf-8"))

    def graph(self, edges, name):
        self.require(isinstance(edges, list), name + ": edge list")
        projected = {target: [] for target in OBJECTS}
        for edge in edges:
            if edge["target"] in OBJECTS:
                projected[edge["target"]].append(edge["dependency"])
        for target, dependencies in projected.items():
            self.require(len(dependencies) == len(set(dependencies)), name + ": no duplicate " + target)
            projected[target] = sorted(dependencies)
        return projected

    def findings(self, entries, expected, name):
        self.require(isinstance(entries, list), name + ": findings list")
        projected = [(item["type"], item["target"], item["dependency"])
                     for item in entries if item["target"] in OBJECTS]
        self.require(len(projected) == len(set(projected)), name + ": no duplicate findings")
        self.require(set(projected) == expected, name + ": exact handwritten MD/RD oracle")

    def expected_commit(self, relative):
        # A baseline checkout log describes the baseline, even though it lives
        # below logs/ rather than baseline-full/.
        path = PurePosixPath(relative)
        if (path.parts[0] == "baseline-full"
                or relative in {"baseline-cache.json", "full-check.json"}
                or (path.parts[0] == "logs" and path.name in {
                    "base-project-resolve.log", "base-project-clone.log", "base-project-checkout.log"})):
            return self.base
        return self.target

    def artifact(self, item, name, metadata=True, commit=None):
        uri = item["uri"]
        self.require(isinstance(uri, str), name + ": URI string")
        parsed = urlsplit(uri)
        self.require(parsed.scheme == "artifact" and parsed.netloc == self.job
                     and not parsed.query and not parsed.fragment, name + ": task-local URI")
        relative = parsed.path.removeprefix("/")
        parts = relative.split("/")
        self.require(bool(relative) and all(part not in {"", ".", "..", ".git"} for part in parts)
                     and "%" not in relative and "\\" not in relative,
                     name + ": canonical safe relative URI")
        self.require(not any(part in {"base-project", "target-project", "project", "sandbox"} for part in parts)
                     and relative not in {"request.json", "result.json", "verifier.json"},
                     name + ": only public evidence")
        path = self.out / relative
        self.require(path.resolve().is_relative_to(self.out) and path.is_file()
                     and not any((self.out / Path(*parts[:i])).is_symlink() for i in range(1, len(parts) + 1)),
                     name + ": existing regular file inside evidence")
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        self.require(item.get("sha256") == digest, name + ": content SHA256")
        self.require(type(item.get("bytes")) is int and item["bytes"] == len(data), name + ": byte count")
        self.require(item.get("artifact_id") == relative and item.get("producer_job_id") == self.job,
                     name + ": artifact ID and producer")
        self.require(item.get("type") in {"ACTUAL_GRAPH", "DECLARED_GRAPH", "ERROR_REPORT", "BUILD_LOG", "TEST_RESULT", "PATCH"}
                     and item.get("media_type") in {"application/json", "text/plain", "text/x-diff"},
                     name + ": artifact type and media type")
        if metadata:
            self.require(item.get("commit") == (commit or self.expected_commit(relative)), name + ": commit attribution")
            self.require(item.get("configuration_id") == self.configuration, name + ": configuration ID")
        self.artifact_count += 1
        return relative

    def trace_evidence(self, folder, edges):
        traces = self.out / folder / "trace"
        files = list(traces.glob("t.*"))
        self.require(bool(files) and all(path.stat().st_size > 0 for path in files), folder + ": nonempty real traces")
        for edge in edges:
            if edge["target"] not in OBJECTS:
                continue
            proof = edge["evidence"]
            filename = proof["trace_file"]
            self.require(re.fullmatch(r"t\.\d+", filename) is not None, folder + ": trace filename")
            lines = (traces / filename).read_text(encoding="utf-8").splitlines()
            line = proof["line"]
            self.require(type(line) is int and 1 <= line <= len(lines), folder + ": trace line exists")
            raw = lines[line - 1]
            self.require(proof.get("source") == "system_call"
                         and proof.get("operation") in {"open", "openat", "openat2"}
                         and re.search(r"\bopen(?:at2?)?\(", raw) is not None
                         and "O_RDONLY" in raw and edge["dependency"] in raw
                         and re.search(r"=\s*\d+", raw) is not None,
                         folder + ": successful raw read for " + edge["target"] + " -> " + edge["dependency"])
            self.trace_edges += 1

    def verify(self):
        result = self.read("result.json")
        request = self.read("request.json")
        self.require(request.get("mode") == "e11-a", "request is E11-A")
        self.base, self.target = request["base"], request["target"]
        self.require(isinstance(self.base, str) and FULL_SHA.fullmatch(self.base) is not None
                     and isinstance(self.target, str) and FULL_SHA.fullmatch(self.target) is not None
                     and self.base != self.target, "different full base/target SHAs")
        self.require(result.get("schema_version") == "e11e12-1" and result.get("status") == "SUCCEEDED"
                     and not result.get("error"), "successful versioned result")
        self.require(result.get("base_commit") == self.base and result.get("target_commit") == self.target,
                     "result SHAs match request")
        self.job, self.trace = result["job_id"], result["trace_id"]
        self.configuration = result["configuration_id"]
        self.require(re.fullmatch(r"job-[0-9a-f]{32}", self.job) is not None
                     and re.fullmatch(r"trace-[0-9a-f]{32}", self.trace) is not None,
                     "complete job and trace identifiers")
        self.require(re.fullmatch(r"cfg-e11e12-[0-9a-f]{16}", self.configuration) is not None,
                     "configuration fingerprint present")

        manifest = result["artifacts"]
        self.require(isinstance(manifest, list) and bool(manifest), "nonempty public artifact manifest")
        indexed = {}
        for i, item in enumerate(manifest):
            relative = self.artifact(item, "manifest[" + str(i) + "]")
            self.require(relative not in indexed, "manifest unique URI: " + relative)
            indexed[relative] = item
        mandatory = {"baseline-cache.json", "incremental-report.json", "full-check.json", "incremental-check.json"}
        mandatory.update(folder + "/" + filename for folder in ("baseline-full", "target-full")
                         for filename in ("actual-graph.json", "declared-graph.json", "findings.json", "make-db.txt", "processes.json"))
        mandatory.update("logs/" + prefix + "-" + action + ".log"
                         for prefix in ("base-project", "target-project") for action in ("resolve", "clone", "checkout"))
        self.require(mandatory.issubset(indexed), "manifest includes all reports, graphs and checkout logs")

        stages = result["stages"]
        self.require([stage["name"] for stage in stages] == ["full-check", "incremental-check"], "exact E11-A stage order")
        envelopes = {}
        for stage, commit in zip(stages, (self.base, self.target)):
            name = stage["name"]
            relative = self.artifact(stage["artifact"], name + " index", metadata=False)
            self.require(relative == name + ".json", name + ": index points to its envelope")
            self.require(all(stage["artifact"].get(key) == indexed[relative].get(key)
                             for key in stage["artifact"]), name + ": index agrees with manifest")
            envelope = self.read(relative)
            self.require(envelope.get("schema_version") == "e11e12-1"
                         and envelope.get("kind") == name and envelope.get("status") == "SUCCEEDED"
                         and envelope.get("commit") == commit and envelope.get("job_id") == self.job
                         and envelope.get("trace_id") == self.trace
                         and envelope.get("configuration_id") == self.configuration,
                         name + ": shared identity and correct version/commit/configuration")
            self.require(bool(envelope["artifacts"]), name + ": stage evidence present")
            for i, item in enumerate(envelope["artifacts"]):
                child = self.artifact(item, name + " artifacts[" + str(i) + "]", commit=commit)
                self.require(indexed.get(child) == item, name + ": child metadata agrees with manifest")
            envelopes[name] = envelope

        baseline = self.read("baseline-cache.json")
        current = self.read("incremental-report.json")
        self.require(baseline.get("commit") == self.base and current.get("commit") == self.target,
                     "cache and incremental report commits")
        self.require(envelopes["incremental-check"]["data"] == current, "incremental envelope equals raw report")
        for report, actual, findings, name in (
                (baseline, EXPECTED_BASE, BASE_FINDINGS, "baseline cache"),
                (current, EXPECTED_TARGET, TARGET_FINDINGS, "target incremental")):
            self.require(report.get("schema_version") == "e8e10-1", name + ": profile version")
            self.require(report.get("actual") == actual, name + ": exact handwritten actual graph")
            self.require(report.get("declared") == EXPECTED_DECLARED, name + ": exact handwritten declared graph")
            self.findings(report["findings"], findings, name)
        self.require({tuple(item) for item in current["added"]} == {("MISSING", "main.o", "extra.h")}
                     and current.get("resolved") == [], "target delta is exactly newly missing extra.h")
        self.require(sorted(current.get("refreshed", [])) == sorted(OBJECTS) and current.get("reused") == [],
                     "include change conservatively refreshes both objects")

        for folder, actual, findings in (("baseline-full", EXPECTED_BASE, BASE_FINDINGS),
                                         ("target-full", EXPECTED_TARGET, TARGET_FINDINGS)):
            edges = self.read(folder + "/actual-graph.json")
            declared = self.read(folder + "/declared-graph.json")
            full_report = self.read(folder + "/findings.json")
            self.require(full_report.get("status") == "SUCCEEDED", folder + ": successful real full check")
            self.require(self.graph(edges, folder + " actual") == actual, folder + ": actual matches independent oracle")
            self.require(self.graph(declared, folder + " declared") == EXPECTED_DECLARED,
                         folder + ": declared matches independent oracle")
            self.findings(full_report["findings"], findings, folder)
            self.trace_evidence(folder, edges)
            self.require(all(folder + "/trace/" + edge["evidence"]["trace_file"] in indexed
                             for edge in edges if edge["target"] in OBJECTS), folder + ": cited traces are hash-covered")
        self.require(envelopes["full-check"]["data"] == self.read("baseline-full/findings.json"),
                     "full-check envelope equals raw full report")

        # Exercise the actual consumer with a corrupted copy, leaving producer
        # evidence and its manifest unchanged. Whitespace keeps it valid JSON.
        source = self.out / "incremental-report.json"
        expected_hash = indexed["incremental-report.json"]["sha256"]
        sys.path.insert(0, str(ROOT / "labs/e11e12"))
        import pipeline
        rejected = None
        with tempfile.TemporaryDirectory(prefix="e11a-241880411-tamper-") as temporary:
            copied = Path(temporary) / source.name
            copied.write_bytes(source.read_bytes() + b"\n ")
            try:
                pipeline.load_artifact(copied, expected_hash)
            except pipeline.Failure as exc:
                rejected = exc.code
        self.require(rejected == "ARTIFACT_HASH_MISMATCH", "consumer rejects tampered copy with ARTIFACT_HASH_MISMATCH")
        self.require(hashlib.sha256(source.read_bytes()).hexdigest() == expected_hash, "original evidence preserved after tamper probe")

        return {"job_id": self.job, "trace_id": self.trace, "base_commit": self.base,
                "target_commit": self.target, "configuration_id": self.configuration,
                "manifest_entries": len(manifest), "artifact_references_checked": self.artifact_count,
                "raw_read_edges_checked": self.trace_edges, "tamper_error_code": rejected}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="Existing E11-A output directory")
    args = parser.parse_args(argv)
    out = args.out.resolve()
    if not out.is_dir():
        parser.error("--out must be an existing evidence directory")
    report_path = out / "verifier.json"
    if report_path.exists():
        parser.error("verifier.json already exists; preserve the previous verification")
    verifier = Verifier(out)
    report = {"verifier": "e11a-independent-241880411", "issue": 38,
              "dataset_scope": "course-generated prepare.py C0/C1; E11-A only",
              "oracle": "handwritten expected graphs/findings and raw trace references"}
    try:
        report.update(verifier.verify(), status="SUCCEEDED")
    except (VerificationError, OSError, ValueError, KeyError, TypeError, IndexError) as exc:
        report.update(status="FAILED", error={"type": type(exc).__name__, "message": str(exc)})
    report["checks"] = verifier.checks
    # Exclusive creation protects existing verification and producer output.
    with report_path.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"status": report["status"], "checks": len(verifier.checks),
                      "report": str(report_path), "error": report.get("error")}, ensure_ascii=False))
    return 0 if report["status"] == "SUCCEEDED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
