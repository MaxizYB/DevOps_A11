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
make clean  -> remove the per-student E4 image
make lock   -> regenerate the hash-locked requirements inside the pinned base image
```

`doctor.py` records the local Git identity, source SHA, host resources, Docker client/server and tool versions. It requires Linux, at least 2 CPUs, 3.5 GiB visible memory and 40 GiB free disk; Buildx is reported as a warning because Compose may still be usable without the standalone subcommand. `secret_scan.py` checks tracked and unignored workspace files, the tracked index, Git history, image history and image environment; local `.env` is allowed but must be mode 600, and detected values are redacted to a four-character prefix. Ignored archives and local course materials are excluded from the workspace scan. Standalone private-key headers remain detectable in files, Git history and decoded image environment variables; quoted Python test examples are excluded.

The E4 `work/` output is intentionally ignored. Keep the successful run directory, source SHA and comparison with the second member in the Issue/PR or course submission record.

The initial E4 work was started before the teacher package was available. After
`E4实验包.zip` became available, A11 compared its `A-buildchecker` template with
this repository and adopted the compatible improvements (module entry point,
toolchain metadata, timeout/project isolation, and package-aware secret rules).
The existing E2 contracts and E3 fixtures remain the source of truth; the E4
scaffold is an environment boundary, not the final BuildChecker dependency-
analysis implementation.

## Smoke permission errors

Smoke builds and executes its temporary `app` under `/tmp`. Docker's tmpfs
defaults to `noexec`, so Compose explicitly uses
`/tmp:rw,exec,nosuid,nodev,size=128m`. Without `exec`, compilation can succeed
while running `app` fails with `PermissionError`. Smoke now writes the error
and an actionable hint to `smoke.json`; the orchestrator also points to
`smoke.stderr.log` for container errors.

After updating the source/Compose configuration, run `make all` again to create
a fresh evidence directory. Keep the failed run for diagnosis. A Compose-only
mount change applies to the next container; CLI/test changes are rebuilt by
`make all`.
