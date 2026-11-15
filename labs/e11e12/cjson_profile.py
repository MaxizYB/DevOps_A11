"""B11's cJSON profile, integrated by A11 with conservative history reuse.

Source: B11 7b45b9c04686f3aefe861bb1d8a17aa63c969f23 (241880326).
Only cJSON_Utils.o is supported; this is not a general Make implementation.
"""
import difflib
import hashlib
import os
import re
import shlex
import subprocess
import time
from pathlib import Path

TARGET = "cJSON_Utils.o"
SOURCE = "cJSON_Utils.c"

def run(argv, cwd):
    result = subprocess.run(argv, cwd=cwd, text=True, capture_output=True, timeout=60)
    if result.returncode:
        raise ValueError(f"COMMAND_FAILED {argv!r}: {result.stderr}")
    return result.stdout

def compile_command(project):
    """Use the actual Make recipe/flags, not an unrelated bare gcc -MM call."""
    lines = [line.strip() for line in run(
        ["make", "--no-print-directory", "-Bn", TARGET], project).splitlines() if line.strip()]
    if len(lines) != 1:
        raise ValueError("UNSUPPORTED_RECIPE expected one compiler invocation")
    argv = shlex.split(lines[0])
    if (not argv or Path(argv[0]).name not in {"cc", "gcc"}
            or argv.count(SOURCE) != 1 or "-c" not in argv
            or any(token in {";", "&&", "||", "|", ">", "<"} for token in argv)):
        raise ValueError("UNSUPPORTED_RECIPE expected GCC-compatible C compilation")
    flags = []
    index = 1
    while index < len(argv):
        token = argv[index]
        if token == "-o":
            if index + 1 >= len(argv) or argv[index + 1] != TARGET:
                raise ValueError("UNSUPPORTED_RECIPE unexpected compiler output")
            index += 2
            continue
        if token not in {"-c", SOURCE}:
            if token.startswith(("@", "-M", "-o", "-fplugin", "-specs")):
                raise ValueError("UNSUPPORTED_RECIPE dependency/output side effects")
            flags.append(token)
        index += 1
    return argv, [argv[0], *flags, "-MM", "-MT", TARGET, SOURCE]


def preprocessor_lines(text):
    """Include continuation lines too; body-only edits may reuse dependencies."""
    selected, continued = [], False
    for line in text.splitlines():
        if continued or line.lstrip().startswith("#"):
            selected.append(line)
            continued = line.rstrip().endswith("\\")
    return selected


def scan(project, old=None):
    started = time.perf_counter()
    project = Path(project)
    database = run(["make", "-np", TARGET], project)
    rules = re.findall(r"^cJSON_Utils\.o:\s*([^\n]*)$", database, re.M)
    if len(rules) != 1:
        raise ValueError("UNSUPPORTED_RULE cJSON_Utils.o")
    declared = sorted(set(rules[0].split()))
    if any(x in declared for x in ("|",)) or any("$" in x for x in declared):
        raise ValueError("UNSUPPORTED_DECLARATION")
    recipe, observation = compile_command(project)
    # All local header contents and the source file set are conservative inputs.
    # Header macros, conditional includes, flags, compiler and environment changes
    # invalidate reuse. Ordinary C function-body edits do not.
    files = {p.relative_to(project).as_posix(): p.read_text()
             for p in sorted(project.rglob("*"))
             if p.is_file() and ".git" not in p.parts and p.suffix in {".c", ".h"}}
    key = {
        "version": "cjson-cache-1", "recipe": recipe,
        "directives": {name: preprocessor_lines(text) for name, text in files.items()},
        "headers": {name: hashlib.sha256(text.encode()).hexdigest()
                    for name, text in files.items() if name.endswith(".h")},
        "compiler": run([recipe[0], "--version"], project).splitlines()[0],
        "environment": {name: os.environ.get(name, "") for name in (
            "CPATH", "C_INCLUDE_PATH", "GCC_EXEC_PREFIX", "COMPILER_PATH",
            "CC", "CFLAGS", "CPPFLAGS", "MAKEFLAGS", "MAKEOVERRIDES")},
    }
    can_reuse = bool(old and old.get("profile") == "CJSON_UTILS_EXPLICIT_MAKE"
                     and old.get("key") == key and TARGET in old.get("actual", {}))
    if can_reuse:
        actual = sorted(set(old["actual"][TARGET]))
    else:
        output = run(observation, project)
        actual = sorted(set(output.replace("\\\n", " ").split(":", 1)[1].split()))
    findings = [
        {"type": kind, "target": TARGET, "dependency": dependency}
        for kind, deps in (("MISSING", set(actual) - set(declared)),
                           ("REDUNDANT", set(declared) - set(actual)))
        for dependency in sorted(deps)
    ]
    previous = {(f["type"], f["target"], f["dependency"]) for f in old["findings"]} if old else set()
    current = {(f["type"], f["target"], f["dependency"]) for f in findings}
    return {"schema_version": "e8e10-1", "profile": "CJSON_UTILS_EXPLICIT_MAKE",
            "commit": run(["git", "rev-parse", "HEAD"], project).strip(), "key": key,
            "actual": {TARGET: actual}, "declared": {TARGET: declared}, "findings": findings,
            "added": [list(item) for item in sorted(current - previous)],
            "resolved": [list(item) for item in sorted(previous - current)],
            "refreshed": [] if can_reuse else [TARGET],
            "reused": [TARGET] if can_reuse else [],
            "cache_source_commit": old.get("commit") if old else None,
            "observation_command": observation, "elapsed_s": time.perf_counter() - started}

def patch(project, report):
    project = Path(project)
    if report["commit"] != run(["git", "rev-parse", "HEAD"], project).strip():
        raise ValueError("STALE_REPORT")
    original = (project / "Makefile").read_text()
    changed = original
    edits = []
    for finding in report["findings"]:
        if finding["type"] != "MISSING":
            continue
        target, dependency = finding["target"], finding["dependency"]
        if target != TARGET:
            raise ValueError("UNSUPPORTED_TARGET")
        if not re.fullmatch(r"[\w./-]+", dependency) or ".." in Path(dependency).parts or Path(dependency).is_absolute():
            raise ValueError("UNSAFE_PATH")
        if not (project / dependency).is_file():
            raise ValueError("MISSING_INPUT")
        matches = list(re.finditer(r"^(?:\$\(UTILS_OBJ\)|cJSON_Utils\.o):[ \t]*([^\n]*)$", changed, re.M))
        if len(matches) != 1:
            raise ValueError("UNSUPPORTED_RULE")
        match = matches[0]
        changed = changed[:match.end()] + " " + dependency + changed[match.end():]
        edits.append({"target": target, "dependency": dependency, "style": "variable-target"})
    diff = "".join(difflib.unified_diff(original.splitlines(True), changed.splitlines(True),
                                         fromfile="a/Makefile", tofile="b/Makefile"))
    return diff, edits

def validate(project, patchfile, evidence, fail_test=False):
    import shutil
    project, patchfile, evidence = Path(project), Path(patchfile).resolve(), Path(evidence)
    evidence.mkdir(parents=True)
    before = (project / "Makefile").read_bytes()
    sandbox = evidence / "sandbox"
    shutil.copytree(project, sandbox, ignore=shutil.ignore_patterns(".git", "*.o", "cJSON_test"))
    run(["git", "init", "-q", "-b", "main"], sandbox)
    run(["git", "config", "user.name", "ValidationSandbox"], sandbox)
    run(["git", "config", "user.email", "fixture@localhost"], sandbox)
    run(["git", "add", "."], sandbox)
    run(["git", "commit", "-qm", "sandbox input"], sandbox)
    checks, error = {}, None
    try:
        (evidence / "unpatched-build.log").write_text(
            run(["make", "clean"], sandbox) + run(["make", TARGET], sandbox))
        original_query = subprocess.run(["make", "-q", "-W", "cJSON.h", TARGET],
                                       cwd=sandbox, text=True, capture_output=True, timeout=60)
        run(["git", "apply", "--check", str(patchfile)], sandbox)
        run(["git", "apply", str(patchfile)], sandbox)
        checks["patch_applies"] = True
        log = run(["make", "clean"], sandbox) + run(["make", TARGET], sandbox)
        (evidence / "build.log").write_text(log)
        checks["build"] = True
        (evidence / "test.log").write_text(run(["make", "test"], sandbox))
        checks["test"] = not fail_test
        query = subprocess.run(["make", "-q", "-W", "cJSON.h", TARGET],
                               cwd=sandbox, text=True, capture_output=True, timeout=60)
        if query.returncode not in (0, 1):
            raise ValueError("MAKE_QUERY_FAILED " + query.stderr)
        checks["header_change"] = original_query.returncode == 0 and query.returncode == 1
        if checks["header_change"]:
            (evidence / "incremental.log").write_text(run(["make", "-W", "cJSON.h", TARGET], sandbox))
        (evidence / "header-change.json").write_text(__import__("json").dumps({
            "method": "GNU Make -W cJSON.h: simulate a newer header, then actually rebuild",
            "query_exit_code": query.returncode,
            "original_query_exit_code": original_query.returncode,
            "rebuild_command": ["make", "-W", "cJSON.h", TARGET],
        }, indent=2) + "\n")
        recheck = scan(sandbox)
        (evidence / "recheck.json").write_text(__import__("json").dumps(recheck, indent=2) + "\n")
        checks["no_missing"] = not any(f["type"] == "MISSING" for f in recheck["findings"])
    except (ValueError, subprocess.TimeoutExpired) as exc:
        error = str(exc)
    accepted = bool(checks) and all(checks.values()) and error is None
    if accepted:
        (project / "Makefile").write_bytes((sandbox / "Makefile").read_bytes())
    unchanged = (project / "Makefile").read_bytes() == before
    result = {"accepted": accepted, "checks": checks, "error": error,
              "source_unchanged": unchanged, "rollback": not accepted and unchanged}
    (evidence / "validation.json").write_text(__import__("json").dumps(result, indent=2) + "\n")
    return result
