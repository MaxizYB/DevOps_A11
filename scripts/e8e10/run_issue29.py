"""Replay leader experiments with new inputs and retained evidence (Refs #29).

Standard E8/E9 reuse Experiment's teaching steps contributed in #31. Personal
cases belong to student 241880439. No other student's saved outputs are reused.
Run this script inside the existing course image, with the repository mounted.
"""
import argparse
import hashlib
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'labs/e8e10'))
import lab
from leader_cases import change, expected, prepare
from run_issue31 import Experiment
from validation import compare_reports, measure_case, performance_summary, write_csv


def source_identity(out):
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=ROOT, text=True)
    paths = git('ls-files', 'labs/e8e10', 'scripts/e8e10', 'run_lab.py',
                '.github/workflows/e8e10.yml').splitlines()
    manifest = {}
    for name in paths:
        path = ROOT / name
        destination = out / 'source' / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
        manifest[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    lab.save(out / 'source-file-sha256.json', manifest)
    (out / 'student-source-commit.txt').write_text(git('rev-parse', 'HEAD'))
    (out / 'source.patch').write_text(git('diff', 'HEAD', '--', *paths))
    lab.save(out / 'environment.json', {'python': sys.version, 'system': platform.platform(),
        'machine': platform.machine(), 'tools': {
            tool: subprocess.check_output([tool, '--version'], text=True).splitlines()[0]
            for tool in ('gcc', 'make', 'git', 'strace')}})


def preserve_history(directory):
    for project in directory.rglob('project'):
        if not (project / '.git').is_dir():
            continue
        for filename, args in [('history.log', ['log', '--reverse', '--format=fuller', '--stat']),
                               ('history.patch', ['log', '--reverse', '-p', '--format=fuller'])]:
            result = subprocess.check_output(['git', *args], cwd=project)
            (project.parent / filename).write_bytes(result)
        subprocess.run(['git', 'bundle', 'create', str((project.parent / 'history.bundle').resolve()),
                        '--all'], cwd=project, check=True, capture_output=True)


def personal_case(out, stage):
    experiment = Experiment(out)
    try:
        prepare(experiment.project, stage)
        lab.commit(experiment.project, '241880439 ' + stage + ' personal baseline')
        experiment.snapshot('baseline')
        baseline = lab.scan(experiment.project)
        lab.save(out / 'baseline.json', baseline)
        rows, checks = [], []
        for restore in ([False, True] if stage == 'e10' else [False]):
            name = ('macro-off' if restore else 'macro-on') if stage == 'e10' else stage + '-change'
            answer = expected(stage, restore=restore)
            # Persist the answer before modifying or scanning the input.
            lab.save(out / (name + '-expected.json'), answer)
            change(experiment.project, stage, restore=restore)
            lab.commit(experiment.project, '241880439 ' + name)
            experiment.snapshot(name)
            if stage == 'e10':
                group, current = measure_case(experiment.project, out, name, baseline,
                                              lab.scan, answer, repeats=5)
                rows.extend(group)
                if not all(row['passed'] for row in group):
                    raise ValueError(name + ': at least one measured pair failed')
            else:
                current = lab.scan(experiment.project, baseline)
                full = lab.scan(experiment.project)
                lab.save(out / (name + '.json'), current)
                lab.save(out / (name + '-full.json'), full)
                check = compare_reports(current, full, answer)
                lab.save(out / (name + '-comparison.json'), check)
                if not check['passed']:
                    raise ValueError(name + ': independent oracle mismatch')
            # Dynamic reports do not contain change metadata. Only compare graphs/findings.
            dynamic_answer = {key: answer[key] for key in ('actual', 'declared', 'findings')}
            experiment.dynamic_check(name + '-buildchecker', current, dynamic_answer)
            checks.append(name)
            baseline = current
        if rows:
            write_csv(out / 'results.csv', rows)
            write_csv(out / 'performance-summary.csv', performance_summary(rows))
        lab.save(out / 'gate.json', {'passed': True, 'student_id': '241880439',
            'stage': stage, 'cases': checks, 'rows': len(rows),
            'timing_scope': 'scan wall time; personal subprocess journaling included; excludes clean build'})
    finally:
        lab.run = experiment.original_run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    out = (ROOT / args.out).resolve()
    if not out.is_relative_to(ROOT / 'work') or out == ROOT / 'work' or out.exists():
        parser.error('--out must be a fresh subdirectory of work/')
    out.mkdir(parents=True)
    source_identity(out)
    result = {'student_id': '241880439', 'issue': 29, 'passed': False,
              'stages': [], 'scope': 'AI-assisted leader personal execution; teaching profile only'}
    try:
        for stage in ('e8', 'e9'):
            stage_out = out / stage
            stage_out.mkdir()
            experiment = Experiment(stage_out)
            try:
                getattr(experiment, stage)()
            finally:
                lab.run = experiment.original_run
            lab.save(stage_out / 'gate.json', {'passed': True, 'stage': stage, 'student_id': '241880439'})
            if stage == 'e8':
                (stage_out / '结论.txt').write_text(
                    '真实BuildChecker对象图：MD(main.o,config.h)、RD(main.o,unused.h)；未变化时两个目标复用。\n')
            result['stages'].append(stage)
            print('PASS', stage, flush=True)
        lab.demo('e10', out / 'e10', 'A')
        (out / 'e10' / '结论.txt').write_text(
            '六类各五次，完整actual/declared/findings及独立预期通过；最终另做动态重检。\n')
        result['stages'].append('e10')
        print('PASS e10', flush=True)
        for stage in ('e8', 'e9', 'e10'):
            destination = out / (stage + '-personal')
            destination.mkdir()
            personal_case(destination, stage)
            result['stages'].append(stage + '-personal')
            print('PASS', stage + '-personal', flush=True)
        preserve_history(out)
        result['passed'] = True
    except Exception as error:
        result['error'] = type(error).__name__ + ': ' + str(error)
        raise
    finally:
        lab.save(out / 'run-result.json', result)
        manifest = {path.relative_to(out).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                    for path in sorted(out.rglob('*'))
                    if path.is_file() and '.git' not in path.parts and '__pycache__' not in path.parts}
        lab.save(out / 'sha256-manifest.json', manifest)
    print('COMPLETED', out)


if __name__ == '__main__':
    main()
