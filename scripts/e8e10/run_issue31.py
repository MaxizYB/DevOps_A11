"""Personal A-track evidence runner for Issue #31; outer sources stay uncommitted.

Run inside the teaching image. Git commits created by fixture()/commit() belong
only to the generated project under work/, and describe the tested input history.
"""
import argparse
import csv
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'labs/e8e10'))
import lab
from validation import compare_reports, measure_case, performance_summary, project_buildchecker


def expected(include_extra=False, fixed=False):
    """Hand-written oracle from the fixture sources and explicit Make rules."""
    actual = {'main.o': ['config.h', 'main.c'], 'helper.o': ['helper.c']}
    declared = {'main.o': ['main.c', 'unused.h'], 'helper.o': ['helper.c']}
    findings = [{'type': 'REDUNDANT', 'target': 'main.o', 'dependency': 'unused.h'}]
    if include_extra:
        actual['main.o'] = ['config.h', 'extra.h', 'main.c']
    if fixed:
        declared['main.o'] = ['config.h', 'extra.h', 'main.c', 'unused.h']
    else:
        findings.insert(0, {'type': 'MISSING', 'target': 'main.o', 'dependency': 'config.h'})
        if include_extra:
            findings.insert(1, {'type': 'MISSING', 'target': 'main.o', 'dependency': 'extra.h'})
    return {'actual': actual, 'declared': declared, 'findings': findings}


class Experiment:
    def __init__(self, out):
        self.out = out
        self.project = out / 'project'
        self.sequence = 0
        self.original_run = lab.run
        lab.run = self.command

    def command(self, argv, cwd):
        """Retain real stdout, stderr and exit status, including failed commands."""
        self.sequence += 1
        log = self.out / 'commands' / ('%03d' % self.sequence)
        log.mkdir(parents=True)
        try:
            result = subprocess.run(argv, cwd=cwd, text=True, capture_output=True, timeout=30)
        except subprocess.TimeoutExpired as error:
            def decoded(value):
                return value.decode(errors='replace') if isinstance(value, bytes) else value or ''
            (log / 'stdout.log').write_text(decoded(error.stdout))
            (log / 'stderr.log').write_text(decoded(error.stderr))
            lab.save(log / 'command.json', {'argv': argv, 'cwd': str(cwd),
                     'exit_code': None, 'timed_out': True, 'timeout_s': 30})
            raise
        (log / 'stdout.log').write_text(result.stdout)
        (log / 'stderr.log').write_text(result.stderr)
        lab.save(log / 'command.json', {'argv': argv, 'cwd': str(cwd), 'exit_code': result.returncode})
        if result.returncode:
            raise ValueError('COMMAND_FAILED ' + repr(argv) + '\n' + result.stdout + result.stderr)
        return result.stdout

    def snapshot(self, name):
        destination = self.out / 'inputs' / name
        destination.mkdir(parents=True)
        for path in sorted(self.project.iterdir()):
            if path.is_file() and (path.suffix in ['.c', '.h'] or path.name in ['Makefile', '.gitignore']):
                (destination / path.name).write_bytes(path.read_bytes())
        (destination / 'commit.txt').write_text(self.command(['git', 'rev-parse', 'HEAD'], self.project))
        (self.out / 'internal-history.log').write_text(self.command(
            ['git', 'log', '--reverse', '--format=%H %s', '--stat'], self.project))

    def build(self, name):
        output = self.command(['make', 'app'], self.project)
        (self.out / (name + '-build.log')).write_text(output)
        result = self.command(['./app'], self.project)
        (self.out / (name + '-app.log')).write_text(result)
        if result.strip() != '1':
            raise ValueError(name + ': application output must remain 1')

    def check(self, name, incremental, full, oracle, reused, refreshed, added, resolved):
        lab.save(self.out / (name + '.json'), incremental)
        lab.save(self.out / (name + '-full.json'), full)
        comparison = compare_reports(incremental, full, oracle)
        checks = comparison['checks']
        checks.update({
            'reused': incremental['reused'] == reused,
            'refreshed': incremental['refreshed'] == refreshed,
            'added': sorted(incremental['added']) == sorted(added),
            'resolved': sorted(incremental['resolved']) == sorted(resolved),
        })
        comparison['passed'] = comparison['passed'] and all(checks.values())
        lab.save(self.out / (name + '-comparison.json'), comparison)
        if not comparison['passed']:
            raise ValueError(name + ': complete oracle or history behavior mismatch')
        return comparison

    def dynamic_check(self, name, report, oracle):
        directory = self.out / name
        lab.buildchecker(self.project, directory)
        projected = project_buildchecker(directory, ['main.o', 'helper.o'])
        lab.save(self.out / (name + '-projection.json'), projected)
        comparison = compare_reports(report, projected, oracle)
        lab.save(self.out / (name + '-comparison.json'), comparison)
        if not comparison['passed']:
            raise ValueError(name + ': dynamic object-target projection mismatch')
        return projected

    def e8(self):
        oracle = expected()
        lab.save(self.out / 'expected.json', oracle)
        lab.fixture(self.project)
        self.snapshot('C0')
        baseline = lab.scan(self.project)
        lab.save(self.out / 'gcc-baseline.json', baseline)
        projected = self.dynamic_check('buildchecker', baseline, oracle)
        baseline['actual'] = projected['actual']
        baseline['baseline_source'] = 'buildchecker/actual-graph.json projected to main.o/helper.o'
        lab.save(self.out / 'baseline.json', baseline)
        incremental = lab.scan(self.project, baseline)
        self.check('incremental', incremental, lab.scan(self.project), oracle,
                   ['main.o', 'helper.o'], [], [], [])

    def e9(self):
        oracles = {'C0': expected(), 'C1': expected(), 'C2': expected(True), 'C3': expected(True, True)}
        lab.save(self.out / 'expected.json', oracles)
        lab.fixture(self.project)
        baseline = lab.scan(self.project)
        lab.save(self.out / 'baseline.json', baseline)
        self.snapshot('C0')
        self.build('C0')
        self.check('C0', baseline, lab.scan(self.project), oracles['C0'], [],
                   ['main.o', 'helper.o'], [['MISSING', 'main.o', 'config.h'], ['REDUNDANT', 'main.o', 'unused.h']], [])
        time.sleep(1.05)
        source = self.project / 'main.c'
        source.write_text(source.read_text().replace('VALUE+helper()', 'VALUE+helper()+0'))
        lab.commit(self.project, 'C1 body change')
        self.snapshot('C1')
        self.build('C1')
        one = lab.scan(self.project, baseline)
        self.check('C1', one, lab.scan(self.project), oracles['C1'], ['main.o', 'helper.o'], [], [], [])
        time.sleep(1.05)
        source.write_text('#include "extra.h"\n' + source.read_text())
        lab.commit(self.project, 'C2 include change')
        self.snapshot('C2')
        self.build('C2')
        two = lab.scan(self.project, one)
        self.check('C2', two, lab.scan(self.project), oracles['C2'], [], ['main.o', 'helper.o'],
                   [['MISSING', 'main.o', 'extra.h']], [])
        makefile = self.project / 'Makefile'
        makefile.write_text(makefile.read_text().replace('main.c unused.h', 'main.c unused.h config.h extra.h'))
        lab.commit(self.project, 'C3 repair declarations')
        self.snapshot('C3')
        self.build('C3')
        three = lab.scan(self.project, two)
        self.check('C3', three, lab.scan(self.project), oracles['C3'], ['main.o', 'helper.o'], [], [],
                   [['MISSING', 'main.o', 'config.h'], ['MISSING', 'main.o', 'extra.h']])

    def e8_extra(self):
        """Persist the independent shared transitive-header test inputs/results."""
        before = expected()
        after = {
            'actual': {'main.o': ['config.h', 'main.c', 'shared.h'],
                       'helper.o': ['config.h', 'helper.c', 'shared.h']},
            'declared': {'main.o': ['main.c', 'unused.h'], 'helper.o': ['helper.c']},
            'findings': [
                {'type': 'MISSING', 'target': 'main.o', 'dependency': 'config.h'},
                {'type': 'MISSING', 'target': 'main.o', 'dependency': 'shared.h'},
                {'type': 'REDUNDANT', 'target': 'main.o', 'dependency': 'unused.h'},
                {'type': 'MISSING', 'target': 'helper.o', 'dependency': 'config.h'},
                {'type': 'MISSING', 'target': 'helper.o', 'dependency': 'shared.h'}],
        }
        lab.save(self.out / 'expected.json', {'before': before, 'after': after})
        lab.fixture(self.project)
        self.snapshot('before')
        baseline = lab.scan(self.project)
        self.check('baseline', baseline, lab.scan(self.project), before, [], ['main.o', 'helper.o'],
                   [['MISSING', 'main.o', 'config.h'], ['REDUNDANT', 'main.o', 'unused.h']], [])
        baseline_snapshot = json.dumps(baseline, sort_keys=True)
        (self.project / 'shared.h').write_text('#define SHARED 0\n')
        (self.project / 'config.h').write_text('#include "shared.h"\n#define VALUE 1\n')
        (self.project / 'helper.c').write_text('#include "config.h"\nint helper(void){return 0;}\n')
        lab.commit(self.project, 'student 241880411: shared transitive header')
        self.snapshot('after')
        incremental = lab.scan(self.project, baseline)
        self.check('incremental', incremental, lab.scan(self.project), after, [], ['main.o', 'helper.o'],
                   [['MISSING', 'helper.o', 'config.h'], ['MISSING', 'helper.o', 'shared.h'],
                    ['MISSING', 'main.o', 'shared.h']], [])
        history_checks = {'key_invalidated': incremental['key'] != baseline['key'],
                          'baseline_unchanged': json.dumps(baseline, sort_keys=True) == baseline_snapshot}
        lab.save(self.out / 'history-checks.json', history_checks)
        if not all(history_checks.values()):
            raise ValueError('Shared transitive-header history behavior mismatch')

    def e9_extra(self):
        """Persist equal-count old-to-new dependency replacement evidence."""
        before = expected()
        before['actual']['main.o'] = ['config.h', 'main.c', 'old.h']
        before['findings'].insert(1, {'type': 'MISSING', 'target': 'main.o', 'dependency': 'old.h'})
        after = expected()
        after['actual']['main.o'] = ['config.h', 'main.c', 'new.h']
        after['findings'].insert(1, {'type': 'MISSING', 'target': 'main.o', 'dependency': 'new.h'})
        lab.save(self.out / 'expected.json', {'before': before, 'after': after})
        lab.fixture(self.project)
        (self.project / 'old.h').write_text('#define OLD 0\n')
        (self.project / 'new.h').write_text('#define NEW 0\n')
        (self.project / 'config.h').write_text('#include "old.h"\n#define VALUE 1\n')
        lab.commit(self.project, 'student 241880411: old transitive header baseline')
        self.snapshot('before')
        baseline = lab.scan(self.project)
        self.check('baseline', baseline, lab.scan(self.project), before, [], ['main.o', 'helper.o'],
                   [['MISSING', 'main.o', 'config.h'], ['MISSING', 'main.o', 'old.h'],
                    ['REDUNDANT', 'main.o', 'unused.h']], [])
        (self.project / 'config.h').write_text('#include "new.h"\n#define VALUE 1\n')
        lab.commit(self.project, 'student 241880411: replace indirect old header with new')
        self.snapshot('after')
        incremental = lab.scan(self.project, baseline)
        self.check('incremental', incremental, lab.scan(self.project), after, [], ['main.o', 'helper.o'],
                   [['MISSING', 'main.o', 'new.h']], [['MISSING', 'main.o', 'old.h']])
        history_checks = {
            'equal_finding_count': len(incremental['findings']) == len(baseline['findings']),
            'different_findings': incremental['findings'] != baseline['findings'],
            'same_file_set': set(incremental['key']['directives']) == set(baseline['key']['directives']),
            'old_header_preserved': (self.project / 'old.h').is_file(),
            'new_header_preserved': (self.project / 'new.h').is_file(),
        }
        history_checks.update({field + '_unchanged': incremental['key'][field] == baseline['key'][field]
                               for field in ['recipes', 'flags', 'compiler']})
        lab.save(self.out / 'history-checks.json', history_checks)
        if not all(history_checks.values()):
            raise ValueError('Equal-count dependency replacement history behavior mismatch')

    def extension(self):
        oracle = expected()
        lab.save(self.out / 'expected.json', dict(oracle,
                 reused=[], refreshed=['main.o', 'helper.o'], added=[],
                 resolved=[['MISSING', 'main.o', 'extra.h']]))
        lab.fixture(self.project)
        source = self.project / 'main.c'
        source.write_text('#include "extra.h"\n' + source.read_text())
        lab.commit(self.project, 'D0 include extra.h before deleting it')
        baseline = lab.scan(self.project)
        lab.save(self.out / 'baseline.json', baseline)
        baseline_check = compare_reports(baseline, baseline, expected(True))
        lab.save(self.out / 'baseline-comparison.json', baseline_check)
        if not baseline_check['passed']:
            raise ValueError('Deletion baseline does not match independent oracle')
        self.snapshot('before-deletion')
        source.write_text(source.read_text().replace('#include "extra.h"\n', ''))
        (self.project / 'extra.h').unlink()
        lab.commit(self.project, 'D1 remove include and delete extra.h')
        self.snapshot('after-deletion')
        history_oracle = dict(oracle, reused=[], refreshed=['main.o', 'helper.o'],
                              added=[], resolved=[['MISSING', 'main.o', 'extra.h']])
        rows, incremental = measure_case(self.project, self.out, 'delete-header', baseline,
                                         lab.scan, history_oracle, repeats=5)
        self.csv('results.csv', rows)
        self.csv('performance-summary.csv', performance_summary(rows))
        if len(rows) != 5 or not all(row['passed'] for row in rows):
            raise ValueError('Deletion extension does not match all five independent oracles')
        self.dynamic_check('final-buildchecker', incremental, oracle)
        lab.save(self.out / 'measurement.json', {
            'scope': 'scan() wall time; not clean-build speed',
            'repeats': 5, 'history': 'Every repeat uses the same baseline.json',
            'logging': 'subprocess stdout/stderr/exit recording included in scan wall time',
            'deleted_header_absent': not (self.project / 'extra.h').exists(),
        })

    def csv(self, name, rows):
        with (self.out / name).open('w', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', choices=['e8', 'e9', 'e8-extra', 'e9-extra', 'extension'], required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    out = (ROOT / args.out).resolve()
    if not out.is_relative_to(ROOT / 'work') or out == ROOT / 'work':
        parser.error('--out must be a new subdirectory of work/')
    if out.exists():
        parser.error('output directory exists; use a new name')
    out.mkdir(parents=True)
    result = {'student_id': '241880411', 'issue': 31, 'stage': args.stage, 'passed': False}
    try:
        experiment = Experiment(out)
        getattr(experiment, args.stage.replace('-', '_'))()
        result['passed'] = True
    except Exception as error:
        result['error'] = type(error).__name__ + ': ' + str(error)
        raise
    finally:
        lab.save(out / 'gate.json', result)
    print('COMPLETED', args.stage, out)


if __name__ == '__main__':
    main()
