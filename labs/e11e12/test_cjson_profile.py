import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

try:
    import cjson_profile
except ModuleNotFoundError:
    cjson_profile = None

class CjsonProfileTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "cJSON.h").write_text("#define VALUE 1\n")
        (self.root / "cJSON_Utils.h").write_text('#include "cJSON.h"\n')
        (self.root / "cJSON_Utils.c").write_text('#include "cJSON_Utils.h"\nint value(void) { return VALUE; }\n')
        (self.root / "Makefile").write_text("UTILS_OBJ = cJSON_Utils.o\n$(UTILS_OBJ): cJSON_Utils.c cJSON_Utils.h\n\t$(CC) -c cJSON_Utils.c -o $@\n")
        with (self.root / "Makefile").open("a") as makefile:
            makefile.write(".PHONY: clean test\nclean:\n\trm -f cJSON_Utils.o\ntest:\n\t@true\n")
        for args in (["init", "-q", "-b", "main"], ["config", "user.name", "Test"], ["config", "user.email", "test@example.invalid"], ["add", "."], ["commit", "-qm", "fixture"]):
            subprocess.run(["git", "-C", str(self.root), *args], check=True)
        self.addCleanup(self.tmp.cleanup)

    def test_detects_and_repairs_transitive_header_dependency(self):
        self.assertIsNotNone(cjson_profile, "cJSON profile must be available")
        report = cjson_profile.scan(self.root)
        self.assertIn({"type": "MISSING", "target": "cJSON_Utils.o", "dependency": "cJSON.h"}, report["findings"])
        diff, edits = cjson_profile.patch(self.root, report)
        self.assertIn("+$(UTILS_OBJ): cJSON_Utils.c cJSON_Utils.h cJSON.h", diff)
        self.assertEqual(edits[0]["dependency"], "cJSON.h")
        self.assertNotIn("cJSON.h\n", (self.root / "Makefile").read_text())

    def test_stale_report_is_rejected(self):
        self.assertIsNotNone(cjson_profile)
        report = cjson_profile.scan(self.root)
        report["commit"] = "0" * 40
        with self.assertRaisesRegex(ValueError, "STALE_REPORT"):
            cjson_profile.patch(self.root, report)

    def test_validation_runs_real_rebuild_after_header_change(self):
        self.assertIsNotNone(cjson_profile)
        report = cjson_profile.scan(self.root)
        diff, _ = cjson_profile.patch(self.root, report)
        patch_path = self.root.parent / (self.root.name + ".patch")
        patch_path.write_text(diff)
        self.addCleanup(patch_path.unlink, missing_ok=True)
        evidence = self.root.parent / (self.root.name + "-evidence")
        self.addCleanup(__import__("shutil").rmtree, evidence, ignore_errors=True)
        result = cjson_profile.validate(self.root, patch_path, evidence)
        self.assertTrue(result["accepted"], result)
        self.assertTrue(result["checks"]["header_change"])
        self.assertTrue(result["checks"]["no_missing"])
        self.assertIn("cJSON_Utils.h cJSON.h", (self.root / "Makefile").read_text())

    def test_pipeline_accepts_cjson_snapshot(self):
        import pipeline
        (self.root / "cJSON.c").write_text("int placeholder(void) {return 0;}\n")
        subprocess.run(["git", "-C", str(self.root), "add", "cJSON.c"], check=True)
        subprocess.run(["git", "-C", str(self.root), "commit", "-qm", "add source"], check=True)
        destination = self.root.parent / (self.root.name + "-snapshot")
        logs = self.root.parent / (self.root.name + "-logs")
        self.addCleanup(__import__("shutil").rmtree, destination, ignore_errors=True)
        self.addCleanup(__import__("shutil").rmtree, logs, ignore_errors=True)
        sha = pipeline.snapshot(self.root, "HEAD", destination, logs, profile="cjson")
        self.assertEqual(sha, subprocess.check_output(["git", "-C", str(self.root), "rev-parse", "HEAD"], text=True).strip())

    def test_api_rejects_broken_dockerfile_outside_data(self):
        import pipeline
        import server
        data = pipeline.ROOT / "data"
        data.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=data) as d:
            root = Path(d)
            candidate = root / "candidate"
            candidate.write_text("FROM scratch\n")
            store = server.Store(root / "jobs")
            request = {"mode": "e12", "project_profile": "cjson", "repo": str(root),
                       "base": "a" * 40, "target": "b" * 40, "candidate": str(candidate),
                       "broken_dockerfile": str(root.parent.parent / "outside")}
            try:
                with self.assertRaisesRegex(ValueError, "broken_dockerfile"):
                    store.submit(request, "k")
            finally:
                store.pool.shutdown()

    def test_candidate_preserves_original_commands(self):
        import pipeline
        from draft.autobuild import prepare_candidate
        folder = pipeline.ROOT / "labs/e11e12/examples"
        broken = (folder / "cjson.Dockerfile.broken").read_text()
        candidate = (folder / "cjson.Dockerfile.candidate").read_text()
        baseline = prepare_candidate(broken, candidate)
        self.assertIn("RUN make cJSON_Utils.o", baseline)
        self.assertIn("RUN make test", baseline)
        self.assertIn("build-essential", candidate)

    def test_unchanged_reuses_without_gcc_dependency_observation(self):
        baseline = cjson_profile.scan(self.root)
        with patch.object(cjson_profile, 'run', wraps=cjson_profile.run) as run:
            current = cjson_profile.scan(self.root, baseline)
        self.assertEqual(current['reused'], [cjson_profile.TARGET])
        self.assertEqual(current['refreshed'], [])
        self.assertFalse(any('-MM' in call.args[0] for call in run.call_args_list))
        self.assertEqual(current['actual'], baseline['actual'])
        self.assertEqual(current['cache_source_commit'], baseline['commit'])

    def test_body_only_commit_reuses_and_matches_fresh_observation(self):
        baseline = cjson_profile.scan(self.root)
        source = self.root/'cJSON_Utils.c'
        source.write_text(source.read_text().replace('return VALUE;', 'return VALUE + 0;'))
        subprocess.run(['git','-C',str(self.root),'commit','-qam','Real body-only change'],check=True)
        with patch.object(cjson_profile, 'run', wraps=cjson_profile.run) as run:
            current = cjson_profile.scan(self.root, baseline)
        self.assertFalse(any('-MM' in call.args[0] for call in run.call_args_list))
        self.assertNotEqual(current['commit'], baseline['commit'])
        self.assertEqual(current['reused'], [cjson_profile.TARGET])
        fresh = cjson_profile.scan(self.root)
        for field in ['actual','declared','findings']:
            self.assertEqual(current[field], fresh[field])

    def test_header_change_invalidates_cache(self):
        baseline = cjson_profile.scan(self.root)
        (self.root/'extra.h').write_text('#define EXTRA 0\n')
        (self.root/'cJSON.h').write_text('#include "extra.h"\n#define VALUE 1\n')
        current = cjson_profile.scan(self.root, baseline)
        self.assertEqual(current['refreshed'], [cjson_profile.TARGET])
        self.assertEqual(current['reused'], [])
        self.assertIn('extra.h', current['actual'][cjson_profile.TARGET])

    def test_make_flags_used_by_oracle_and_invalidate_cache(self):
        (self.root/'extra.h').write_text('#define EXTRA 0\n')
        source = self.root/'cJSON_Utils.c'
        source.write_text('#ifdef EXTRA_ENABLED\n#include "extra.h"\n#endif\n'+source.read_text())
        makefile = self.root/'Makefile'
        makefile.write_text(makefile.read_text().replace('$(CC) -c', '$(CC) $(CFLAGS) -c'))
        baseline = cjson_profile.scan(self.root)
        makefile.write_text('CFLAGS = -DEXTRA_ENABLED\n'+makefile.read_text())
        current = cjson_profile.scan(self.root, baseline)
        self.assertEqual(current['reused'], [])
        self.assertIn('-DEXTRA_ENABLED', current['observation_command'])
        self.assertIn('extra.h', current['actual'][cjson_profile.TARGET])

    def test_declaration_only_change_reuses_actual_graph_but_updates_findings(self):
        baseline = cjson_profile.scan(self.root)
        makefile = self.root/'Makefile'
        makefile.write_text(makefile.read_text().replace(
            '$(UTILS_OBJ): cJSON_Utils.c cJSON_Utils.h',
            '$(UTILS_OBJ): cJSON_Utils.c cJSON_Utils.h cJSON.h'))
        current = cjson_profile.scan(self.root, baseline)
        self.assertEqual(current['reused'], [cjson_profile.TARGET])
        self.assertEqual(current['findings'], [])
        self.assertIn(['MISSING', 'cJSON_Utils.o', 'cJSON.h'], current['resolved'])

    def test_preprocessor_continuation_participates_in_cache_key(self):
        text = '\n'.join(['#if '+chr(92), '1', '#endif', 'int a;'])
        self.assertEqual(cjson_profile.preprocessor_lines(text),
                         ['#if \\', '1', '#endif'])

    def test_failed_validation_preserves_makefile(self):
        report = cjson_profile.scan(self.root)
        diff, _ = cjson_profile.patch(self.root, report)
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            candidate = root/'candidate.patch'
            candidate.write_text(diff)
            original = (self.root/'Makefile').read_bytes()
            result = cjson_profile.validate(self.root,candidate,root/'validation',fail_test=True)
        self.assertFalse(result['accepted'])
        self.assertTrue(result['rollback'])
        self.assertEqual((self.root/'Makefile').read_bytes(), original)

    def test_profile_and_harness_request_boundaries(self):
        import pipeline
        data = pipeline.ROOT/'data'
        data.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=data) as d:
            root=Path(d)
            candidate=root/'candidate'
            candidate.write_text('FROM scratch\n')
            broken=root/'broken'
            broken.write_text('FROM scratch\n')
            request={'mode':'e12','project_profile':'cjson','repo':str(root),
                     'base':'a'*40,'target':'b'*40,'candidate':str(candidate),'broken_dockerfile':str(broken)}
            self.assertEqual(pipeline.validate_request(request),request)
            invalid=[(dict(request,project_profile='other'),'teaching or cjson'),
                     (dict(request,project_profile=[]),'teaching or cjson'),
                     (dict(request,project_profile='teaching'),'only supported for cjson'),
                     ({k:v for k,v in request.items() if k!='broken_dockerfile'},'broken_dockerfile')]
            for value,message in invalid:
                with self.subTest(message=message), self.assertRaisesRegex(pipeline.Failure,message):
                    pipeline.validate_request(value)

    def test_cjson_pipeline_seeds_cache_and_binds_stage_metadata(self):
        import json
        import pipeline
        source=self.root/'cJSON.c'
        source.write_text('int placeholder(void) {return 0;}\n')
        subprocess.run(['git','-C',str(self.root),'add','.'],check=True)
        subprocess.run(['git','-C',str(self.root),'commit','-qm','Add source'],check=True)
        base=subprocess.check_output(['git','-C',str(self.root),'rev-parse','HEAD'],text=True).strip()
        (self.root/'cJSON_Utils.c').write_text((self.root/'cJSON_Utils.c').read_text().replace('return VALUE;', 'return VALUE + 0;'))
        subprocess.run(['git','-C',str(self.root),'commit','-qam','Body-only target'],check=True)
        target=subprocess.check_output(['git','-C',str(self.root),'rev-parse','HEAD'],text=True).strip()
        with tempfile.TemporaryDirectory() as d, \
                patch.object(pipeline,'data_path',side_effect=lambda value,field:Path(value)):
            out=Path(d)/'e11-a'
            result=pipeline.execute({'mode':'e11-a','project_profile':'cjson','repo':str(self.root),
                                     'base':base,'target':target},out)
            self.assertEqual(result['status'],'SUCCEEDED',result.get('error'))
            current=json.loads((out/'incremental-report.json').read_text())
            self.assertEqual(current['reused'],[cjson_profile.TARGET])
            self.assertEqual(current['baseline_commit'],base)
            self.assertTrue(current['baseline_cache_sha256'])
            for name in ['full-check','incremental-check']:
                envelope=json.loads((out/(name+'.json')).read_text())
                self.assertEqual(envelope['configuration_id'],result['configuration_id'])
                self.assertEqual(envelope['job_id'],result['job_id'])
                self.assertEqual(envelope['trace_id'],result['trace_id'])
                self.assertEqual(envelope['commit'],base if name=='full-check' else target)

if __name__ == "__main__":
    unittest.main()
