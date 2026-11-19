import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(ROOT/'labs/e11e12/vendor'),str(ROOT/'labs/e8e10'),str(ROOT/'labs/e11e12/environment/services/buildchecker')]
spec=importlib.util.spec_from_file_location('e14_service_test',ROOT/'labs/e13e14/service.py')
service=importlib.util.module_from_spec(spec)
with patch.dict(os.environ,{'E14_ROLE':'echecker'}):
    spec.loader.exec_module(service)

class ServiceTests(unittest.TestCase):
    def test_service_import_path_exposes_e11e12_profile(self):
        self.assertEqual(Path(service.cjson_profile.__file__).name, 'cjson_profile.py')
        self.assertIn('labs/e11e12', service.cjson_profile.__file__)

    def test_profile_tools_support_cjson_scope(self):
        scan, patch, validate, targets, command = service.profile_tools('cjson')
        self.assertEqual(targets, ('cJSON_Utils.o',))
        self.assertEqual(command, 'make cJSON_Utils.o')
        self.assertIs(scan, service.cjson_profile.scan)
        self.assertIs(patch, service.cjson_profile.patch)
        self.assertIs(validate, service.cjson_profile.validate)

    def test_profile_tools_reject_unknown_scope(self):
        with self.assertRaisesRegex(ValueError, 'Unsupported project profile'):
            service.profile_tools('unknown')

    def test_independent_service_import_does_not_rely_on_other_tests(self):
        code = ("import importlib.util, os, sys; "
                "sys.path[:0] = [sys.argv[2], sys.argv[3], sys.argv[4]]; "
                "os.environ['E14_ROLE'] = 'echecker'; "
                "spec = importlib.util.spec_from_file_location('isolated_e14', sys.argv[1]); "
                "module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); "
                "assert module.profile_tools('cjson')[3] == ('cJSON_Utils.o',)")
        result = subprocess.run([sys.executable, '-I', '-c', code,
            str(ROOT/'labs/e13e14/service.py'), str(ROOT/'labs/e8e10'),
            str(ROOT/'labs/e11e12/vendor'),
            str(ROOT/'labs/e11e12/environment/services/buildchecker')],
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_cjson_mdfixer_uses_profile_validation(self):
        with tempfile.TemporaryDirectory() as temp, \
                patch.object(service, 'ROOT', Path(temp).resolve()), \
                patch.object(service, 'ROLE', 'mdfixer'), \
                patch.object(service, 'mark_safe'), \
                patch.object(service.cjson_profile, 'patch', return_value=('fixture diff', [])) as profile_patch, \
                patch.object(service.cjson_profile, 'validate', return_value={'accepted': True}) as profile_validate, \
                patch.object(service, 'validate', side_effect=AssertionError('teaching validator called')):
            work = Path(temp)/'work'
            work.mkdir()
            project = work/'project'
            project.mkdir()
            report = work/'report.json'
            report.write_text(json.dumps(dict(schema_version='e11e12-1', kind='incremental-check',
                status='SUCCEEDED', commit='a'*40, job_id='job-test', trace_id='trace-test',
                project_profile='cjson', data={})))
            output = work/'output'
            result = service.run(dict(project=str(project), out=str(output), project_profile='cjson',
                report=str(report), report_sha256=hashlib.sha256(report.read_bytes()).hexdigest(),
                target_commit='a'*40, job_id='job-test', trace_id='trace-test'))
            self.assertEqual(result['status'], 'SUCCEEDED')
            profile_patch.assert_called_once_with(project, {})
            profile_validate.assert_called_once_with(project, output/'candidate.patch', output/'validation')

    def test_mdfixer_rejects_report_from_other_profile_before_patch(self):
        with tempfile.TemporaryDirectory() as temp, \
                patch.object(service, 'ROOT', Path(temp).resolve()), \
                patch.object(service, 'ROLE', 'mdfixer'), patch.object(service, 'mark_safe'), \
                patch.object(service.cjson_profile, 'patch') as profile_patch:
            work = Path(temp)/'work'
            work.mkdir()
            project = work/'project'
            project.mkdir()
            report = work/'report.json'
            report.write_text(json.dumps(dict(schema_version='e11e12-1', kind='incremental-check',
                status='SUCCEEDED', commit='a'*40, job_id='job-test', trace_id='trace-test',
                project_profile='teaching', data={})))
            with self.assertRaisesRegex(ValueError, 'profile mismatch'):
                service.run(dict(project=str(project), out=str(work/'output'), project_profile='cjson',
                    report=str(report), report_sha256=hashlib.sha256(report.read_bytes()).hexdigest(),
                    target_commit='a'*40, job_id='job-test', trace_id='trace-test'))
            profile_patch.assert_not_called()
            self.assertFalse((work/'output').exists())

    @unittest.skipUnless(all(shutil.which(x) for x in ('gcc', 'make', 'git', 'strace')),
                         'requires actual GCC/Make/Git/strace')
    def test_cjson_real_full_incremental_repair_and_recheck(self):
        with tempfile.TemporaryDirectory() as temp, \
                patch.object(service, 'ROOT', Path(temp).resolve()), patch.object(service, 'mark_safe'):
            work = Path(temp)/'work'
            base = work/'base'
            base.mkdir(parents=True)
            (base/'cJSON.c').write_text('int placeholder(void) { return 0; }\n')
            (base/'cJSON.h').write_text('#define VALUE 1\n')
            (base/'cJSON_Utils.h').write_text('#include "cJSON.h"\n')
            (base/'cJSON_Utils.c').write_text('#include "cJSON_Utils.h"\nint value(void) { return VALUE; }\n')
            (base/'Makefile').write_text('UTILS_OBJ = cJSON_Utils.o\n'
                '$(UTILS_OBJ): cJSON_Utils.c cJSON_Utils.h\n\t$(CC) -c cJSON_Utils.c -o $@\n'
                '.PHONY: clean test\nclean:\n\trm -f cJSON_Utils.o\ntest:\n\t@true\n')
            for args in (['init', '-q', '-b', 'main'], ['config', 'user.name', 'Fixture'],
                         ['config', 'user.email', 'fixture@example.invalid'], ['add', '.'],
                         ['commit', '-qm', 'Synthetic profile fixture']):
                subprocess.run(['git', '-C', str(base), *args], check=True, capture_output=True)
            target = work/'target'
            shutil.copytree(base, target)
            source = target/'cJSON_Utils.c'
            source.write_text(source.read_text().replace('return VALUE;', 'return VALUE + 0;'))
            subprocess.run(['git', '-C', str(target), 'commit', '-qam', 'Body-only fixture target'],
                           check=True, capture_output=True)
            commit = subprocess.check_output(['git', '-C', str(target), 'rev-parse', 'HEAD'], text=True).strip()
            def run(role, project, folder, **extra):
                with patch.object(service, 'ROLE', role):
                    return service.run(dict(project=str(project), out=str(work/folder),
                        project_profile='cjson', job_id='job-real', trace_id='trace-real',
                        target_commit=commit, **extra))
            run('buildchecker', base, 'baseline-full')
            run('buildchecker', target, 'target-full')
            inc = run('echecker', target, 'incremental', base=str(base),
                baseline_graph=str(work/'baseline-full/actual-graph.json'),
                target_findings=str(work/'target-full/findings.json'))
            self.assertEqual(inc['findings'], [dict(type='MISSING', target='cJSON_Utils.o', dependency='cJSON.h')])
            envelope = json.loads(Path(inc['report']).read_text())
            self.assertEqual(envelope['project_profile'], 'cjson')
            self.assertEqual(envelope['data']['reused'], ['cJSON_Utils.o'])
            fixed = run('mdfixer', target, 'repair', report=inc['report'], report_sha256=inc['sha256'])
            self.assertTrue(fixed['validation']['accepted'], fixed)
            final = run('buildchecker', target, 'final-full')
            self.assertEqual(final['result']['findings'], [])
            self.assertNotIn('cJSON_Utils.h cJSON.h', (base/'Makefile').read_text())

    def test_allowlists_one_exact_snapshot_not_wildcard(self):
        with patch.object(service.subprocess,'run') as command:
            service.mark_safe(Path('/course/work/example/base-project'))
        self.assertEqual(command.call_args.args[0],['git','config','--global','--add','safe.directory','/course/work/example/base-project'])

    def test_rejects_work_root_and_outside_paths(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(service,'ROOT',Path(temp).resolve()):
            for value in (str(Path(temp)/'work'),str(Path(temp)/'data/p'),'/tmp/outside'):
                with self.subTest(value=value),self.assertRaises(ValueError):
                    service.local(value)

    def test_symlink_escape_rejected(self):
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as other, patch.object(service,'ROOT',Path(temp).resolve()):
            work=Path(temp)/'work';work.mkdir()
            (work/'link').symlink_to(other,target_is_directory=True)
            with self.assertRaises(ValueError):service.local(str(work/'link/report.json'))

    def test_mdfixer_rejects_transfer_hash_before_json_parse(self):
        with tempfile.TemporaryDirectory() as temp,patch.object(service,'ROOT',Path(temp).resolve()),patch.object(service,'ROLE','mdfixer'),patch.object(service,'mark_safe'):
            work=Path(temp)/'work';work.mkdir()
            report=work/'report.json';report.write_text('not json')
            project=work/'project';project.mkdir()
            with self.assertRaisesRegex(ValueError,'hash mismatch'):
                service.run(dict(project=str(project),out=str(work/'output'),report=str(report),report_sha256='0'*64))
            self.assertFalse((work/'output').exists())

if __name__=='__main__':unittest.main()
