"""Issue #39: independent EChecker tests before E11-A foundation integration."""
import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import lab


class Student231880027E11RefreshReuseTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.project = Path(directory.name) / 'sample'
        lab.fixture(self.project)
        self.actual = {'main.o': ['config.h', 'main.c'], 'helper.o': ['helper.c']}
        self.declared = {'main.o': ['main.c', 'unused.h'], 'helper.o': ['helper.c']}
        self.findings = [
            {'type': 'MISSING', 'target': 'main.o', 'dependency': 'config.h'},
            {'type': 'REDUNDANT', 'target': 'main.o', 'dependency': 'unused.h'},
        ]

    def assert_report(self, report, actual, findings):
        self.assertEqual(report['actual'], actual)
        self.assertEqual(report['declared'], self.declared)
        self.assertEqual(report['findings'], findings)

    def assert_reused_without_dependency_scan(self, previous):
        snapshot = copy.deepcopy(previous)
        with patch.object(lab, 'run', wraps=lab.run) as commands:
            report = lab.scan(self.project, previous)
        dependency_calls = [
            call.args[0] for call in commands.call_args_list
            if call.args[0][0] == 'gcc' and '-MM' in call.args[0]
        ]
        self.assertEqual(dependency_calls, [])
        self.assertEqual(previous, snapshot)
        self.assertEqual(report['key'], previous['key'])
        self.assertEqual(report['reused'], ['main.o', 'helper.o'])
        self.assertEqual(report['refreshed'], [])
        self.assertEqual(report['added'], [])
        self.assertEqual(report['resolved'], [])
        self.assert_report(report, self.actual, self.findings)
        return report

    def test_unchanged_reuses_both_targets_without_dependency_scan(self):
        previous = lab.scan(self.project)
        self.assert_report(previous, self.actual, self.findings)
        report = self.assert_reused_without_dependency_scan(previous)
        self.assertEqual(report['commit'], previous['commit'])

    def test_body_only_new_commit_reuses_dependency_graph(self):
        previous = lab.scan(self.project)
        self.assert_report(previous, self.actual, self.findings)
        (self.project / 'helper.c').write_text('int helper(void){return 0+0;}\n')
        target = lab.commit(self.project, 'student 231880027: E11 body-only change')
        report = self.assert_reused_without_dependency_scan(previous)
        self.assertRegex(target, r'^[0-9a-f]{40}$')
        self.assertNotEqual(target, previous['commit'])
        self.assertEqual(report['commit'], target)
        self.assert_report(lab.scan(self.project), self.actual, self.findings)

    def test_shared_header_include_refreshes_and_attributes_both_targets(self):
        helper = self.project / 'helper.c'
        helper.write_text('#include "config.h"\n' + helper.read_text())
        lab.commit(self.project, 'student 231880027: E11 shared-header baseline')
        previous = lab.scan(self.project)
        shared_actual = {
            'main.o': ['config.h', 'main.c'],
            'helper.o': ['config.h', 'helper.c'],
        }
        shared_findings = self.findings + [
            {'type': 'MISSING', 'target': 'helper.o', 'dependency': 'config.h'},
        ]
        self.assert_report(previous, shared_actual, shared_findings)
        snapshot = copy.deepcopy(previous)
        inputs = {name: (self.project / name).read_bytes()
                  for name in ['main.c', 'helper.c', 'Makefile']}
        (self.project / 'config.h').write_text('#include "extra.h"\n#define VALUE 1\n')
        target = lab.commit(self.project, 'student 231880027: E11 shared-header include')
        incremental = lab.scan(self.project, previous)
        full = lab.scan(self.project)
        actual = {
            'main.o': ['config.h', 'extra.h', 'main.c'],
            'helper.o': ['config.h', 'extra.h', 'helper.c'],
        }
        findings = [
            {'type': 'MISSING', 'target': 'main.o', 'dependency': 'config.h'},
            {'type': 'MISSING', 'target': 'main.o', 'dependency': 'extra.h'},
            {'type': 'REDUNDANT', 'target': 'main.o', 'dependency': 'unused.h'},
            {'type': 'MISSING', 'target': 'helper.o', 'dependency': 'config.h'},
            {'type': 'MISSING', 'target': 'helper.o', 'dependency': 'extra.h'},
        ]
        for report in [incremental, full]:
            self.assert_report(report, actual, findings)
            self.assertEqual(report['commit'], target)
        self.assertNotEqual(target, previous['commit'])
        self.assertEqual(incremental['refreshed'], ['main.o', 'helper.o'])
        self.assertEqual(incremental['reused'], [])
        self.assertEqual(incremental['added'], [
            ['MISSING', 'helper.o', 'extra.h'],
            ['MISSING', 'main.o', 'extra.h'],
        ])
        self.assertEqual(incremental['resolved'], [])
        self.assertNotEqual(incremental['key']['directives']['config.h'],
                            previous['key']['directives']['config.h'])
        for field in ['recipes', 'flags', 'compiler']:
            self.assertEqual(incremental['key'][field], previous['key'][field])
        self.assertEqual(previous, snapshot)
        for name, content in inputs.items():
            self.assertEqual((self.project / name).read_bytes(), content)


if __name__ == '__main__':
    unittest.main()
