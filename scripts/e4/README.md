# E4 scripts

`run.py` is the single orchestration entry point:

```text
make doctor -> env.json
make build  -> build.log, image.json, toolchain.lock
make test   -> test.log
make smoke  -> smoke.json
make scan   -> secret-scan.txt
make all    -> all five steps in one new work/<timestamp>/ directory
make shell  -> an interactive shell in the non-root service container
```

`doctor.py` records the local Git identity, source SHA, host resources, Docker client/server and tool versions. `secret_scan.py` checks the checkout workspace, tracked index, Git history, image history and image environment; it prints only a four-character prefix for a detected value.

The E4 `work/` output is intentionally ignored. Keep the successful run directory, source SHA and comparison with the second member in the Issue/PR or course submission record.

The repository did not contain a teacher-provided `A-buildchecker` template. A11
therefore owns this equivalent scaffold: the E2 contracts and E3 fixtures remain
the source of truth, while E4 adds only the reproducible container, orchestration,
and evidence tooling. The scaffold is an environment boundary, not the final
BuildChecker dependency-analysis implementation.
