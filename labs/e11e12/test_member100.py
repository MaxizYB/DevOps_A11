"""Behavioral E11-B extensions: rebuild dependencies and reject stale reports."""
import copy
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch as mock_patch

import lab
import pipeline


class Member100Extensions(unittest.TestCase):
    def setUp(self):
        evidence = os.environ.get("E11_EXTENSION_EVIDENCE")
        if evidence:
            self.root = Path(evidence) / self._testMethodName
            self.root.mkdir(parents=True, exist_ok=False)
        else:
            temp = tempfile.TemporaryDirectory()
            self.addCleanup(temp.cleanup)
            self.root = Path(temp.name)

    def check_style_rebuild(self, style):
        project = self.root / "project"
        lab.fixture(project, style)
        source = (project / "main.c").read_text()
        (project / "main.c").write_text(
            '#include "extra.h"\n' + source.replace("VALUE+helper()", "VALUE+helper()+EXTRA")
        )
        lab.commit(project, "Use extra header in output")
        before = (project / "Makefile").read_text()
        report = lab.scan(project)
        lab.save(self.root / "fixed-report.json", report)
        self.assertEqual(
            {f["dependency"] for f in report["findings"] if f["type"] == "MISSING"},
            {"config.h", "extra.h"},
        )

        # Negative control: missing dependencies keep the old executable.
        (self.root / "before-build.log").write_text(lab.run(["make", "app"], project))
        self.assertEqual(lab.run(["./app"], project).strip(), "1")
        time.sleep(1.05)
        (project / "config.h").write_text("#define VALUE 2\n")
        (self.root / "before-incremental.log").write_text(lab.run(["make", "app"], project))
        self.assertEqual(lab.run(["./app"], project).strip(), "1")
        (project / "config.h").write_text("#define VALUE 1\n")

        diff, edits = lab.patch(project, report)
        self.assertEqual({e["style"] for e in edits}, {style})
        self.assertEqual((project / "Makefile").read_text(), before)
        candidate = self.root / "candidate.patch"
        candidate.write_text(diff)
        verdict = lab.validate(project, candidate, self.root / "validation")
        self.assertTrue(verdict["accepted"], verdict)
        self.assertEqual(
            verdict["checks"],
            dict(patch_applies=True, build=True, test=True, header_change=True, no_missing=True),
        )
        repaired = (project / "Makefile").read_text()
        if style == "macro":
            self.assertIn("DEPS = main.c unused.h config.h extra.h\n", repaired)
            self.assertIn("main.o: $(DEPS)\n", repaired)
        else:
            self.assertIn("HEADERS = unused.h\n", repaired)
            self.assertIn("main.o: main.c $(HEADERS) config.h extra.h\n", repaired)

        # validate already changed config.h to 2; now independently exercise extra.h.
        sandbox = self.root / "validation" / "sandbox"
        time.sleep(1.05)
        (sandbox / "extra.h").write_text("#define EXTRA 3\n")
        rebuild = lab.run(["make", "app"], sandbox)
        (self.root / "extra-incremental.log").write_text(rebuild)
        self.assertIn("-c main.c", rebuild)
        self.assertEqual(lab.run(["./app"], sandbox).strip(), "5")
        findings = lab.scan(sandbox)["findings"]
        self.assertFalse(any(f["type"] == "MISSING" for f in findings))
        self.assertTrue(any(f["type"] == "REDUNDANT" and f["dependency"] == "unused.h"
                            for f in findings))
        lab.save(self.root / "observed.json", {
            "style": style, "unpatched_after_config_change": "1",
            "patched_after_config_change": "2", "patched_after_extra_change": "5",
            "checks": verdict["checks"], "findings": findings,
        })

    def test_macro_rebuilds_for_both_missing_headers(self):
        self.check_style_rebuild("macro")

    def test_mixed_rebuilds_for_both_missing_headers(self):
        self.check_style_rebuild("mixed")

    def test_stale_envelope_and_payload_stop_before_repair(self):
        project = self.root / "project"
        lab.fixture(project)
        old_report = lab.scan(project)
        base = old_report["commit"]
        (project / "main.c").write_text('#include "extra.h"\n' + (project / "main.c").read_text())
        target = lab.commit(project, "New source version")
        before = (project / "Makefile").read_bytes()
        outcomes = []
        for mismatch in ("envelope", "payload"):
            with self.subTest(mismatch=mismatch):
                report = {
                    "schema_version": "e11e12-1", "kind": "fixed-md",
                    "status": "SUCCEEDED",
                    "commit": base if mismatch == "envelope" else target,
                    "data": copy.deepcopy(old_report),
                }
                fixed = self.root / (mismatch + "-input.json")
                lab.save(fixed, report)
                request = {
                    "mode": "e11-b", "repo": str(project), "base": base, "target": target,
                    "candidate": str(self.root / "unused.Dockerfile"), "fixed_report": str(fixed),
                }
                Path(request["candidate"]).write_text("FROM scratch\n")
                out = self.root / mismatch
                # Isolate report validation; actual Docker execution is covered by the E11-B run.
                def draft_result(_project, _candidate, output, *_args, **_kwargs):
                    value = {"status": "SUCCEEDED"}
                    lab.save(output / "result.json", value)
                    return value

                # Request paths are normally restricted to data/. These fixtures
                # use TemporaryDirectory; isolate only path placement here.
                with mock_patch.object(pipeline, "data_path", side_effect=lambda value, field: Path(value)), \
                     mock_patch("draft.autobuild.auto_build", side_effect=draft_result):
                    result = pipeline.execute(request, out)
                self.assertEqual(result["status"], "FAILED")
                self.assertEqual(result["error"]["code"], "STALE_REPORT")
                self.assertEqual([s["name"] for s in result["stages"]], ["draft"])
                self.assertFalse((out / "candidate.patch").exists())
                self.assertFalse((out / "validation").exists())
                self.assertEqual((out / "target-project" / "Makefile").read_bytes(), before)
                self.assertEqual((project / "Makefile").read_bytes(), before)
                outcomes.append({
                    "mismatch": mismatch, "error": result["error"]["code"],
                    "patch_created": False, "makefile_unchanged": True,
                    "draft_stage": "mocked; this test isolates stale-report handling",
                })
        lab.save(self.root / "observed.json", outcomes)


if __name__ == "__main__":
    unittest.main()
