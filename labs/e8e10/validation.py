"""Independent E10 evidence checks for the restricted A-track teaching fixture.

These oracles describe the fixture, rather than deriving an expected answer from
``scan()``. Timings are scan wall times; they do not measure a clean build.
"""
import copy
import csv
import json
import math
from collections import Counter
from pathlib import Path
from statistics import median


CASES = ('unchanged', 'body', 'include', 'declaration', 'flags', 'header')
TARGETS = ('main.o', 'helper.o')
TIMING_SCOPE = 'scan wall time (Git/compiler checks, parsing and gcc -MM); excludes clean build'


def _save(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def _graph(value):
    if not isinstance(value, dict):
        raise ValueError('graph must be a target-to-dependencies mapping')
    result = {}
    for target, dependencies in value.items():
        if not isinstance(target, str) or not target:
            raise ValueError('invalid graph target')
        if not isinstance(dependencies, list) or any(not isinstance(x, str) or not x for x in dependencies):
            raise ValueError('invalid dependency list for ' + target)
        if len(dependencies) != len(set(dependencies)):
            raise ValueError('duplicate dependency for ' + target)
        result[target] = sorted(dependencies)
    return result


def _findings(value):
    if not isinstance(value, list):
        raise ValueError('findings must be a list')
    triples = []
    for finding in value:
        if not isinstance(finding, dict):
            raise ValueError('invalid finding')
        triple = tuple(finding.get(k) for k in ('type', 'target', 'dependency'))
        if any(not isinstance(x, str) or not x for x in triple) or triple[0] not in ('MISSING', 'REDUNDANT'):
            raise ValueError('invalid finding identity')
        triples.append(triple)
    if len(triples) != len(set(triples)):
        raise ValueError('duplicate finding')
    return sorted(triples)


def _canonical(report):
    if not isinstance(report, dict):
        raise ValueError('report must be a mapping')
    try:
        return {'actual': _graph(report['actual']),
                'declared': _graph(report['declared']),
                'findings': _findings(report['findings'])}
    except KeyError as error:
        raise ValueError('missing report field: ' + str(error)) from error


def compare_reports(incremental, full, expected=None):
    """Check complete sets and, when given, an independently specified oracle.

Ordering and BuildChecker evidence metadata do not affect equality. Duplicate
edges/findings and missing fields are malformed evidence, never a passing set.
Optional oracle cache/change fields apply to the incremental report only.
"""
    checks, details, reports = {}, {}, {}
    inputs = {'incremental': incremental, 'full': full}
    if expected is not None:
        inputs['expected'] = expected
    for name, report in inputs.items():
        try:
            reports[name] = _canonical(report)
            checks[name + '_valid'] = True
        except (ValueError, TypeError) as error:
            checks[name + '_valid'] = False
            details[name + '_error'] = str(error)
    for field in ('actual', 'declared', 'findings'):
        same = ('incremental' in reports and 'full' in reports and
                reports['incremental'][field] == reports['full'][field])
        checks[field + '_equal'] = same
        if not same:
            details[field + '_difference'] = {
                name: report[field] for name, report in reports.items()}
        if expected is not None:
            for name in ('incremental', 'full'):
                matches = (name in reports and 'expected' in reports and
                           reports[name][field] == reports['expected'][field])
                checks[name + '_' + field + '_expected'] = matches
                if not matches:
                    details[name + '_' + field + '_expected'] = {
                        'expected': reports.get('expected', {}).get(field),
                        'observed': reports.get(name, {}).get(field)}
    if isinstance(incremental, dict) and isinstance(full, dict) and ('commit' in incremental or 'commit' in full):
        # Dynamic BuildChecker projections have no Git field. Both GCC scans do.
        if 'commit' in incremental and 'commit' in full:
            checks['commit_equal'] = incremental['commit'] == full['commit']
            if not checks['commit_equal']:
                details['commit_difference'] = [incremental['commit'], full['commit']]
    if expected is not None and isinstance(expected, dict):
        for field in ('reused', 'refreshed', 'added', 'resolved'):
            if field not in expected:
                continue
            observed = incremental.get(field) if isinstance(incremental, dict) else None
            wanted = expected[field]
            try:
                observed = sorted(tuple(x) if isinstance(x, list) else x for x in observed)
                wanted = sorted(tuple(x) if isinstance(x, list) else x for x in wanted)
                match = observed == wanted and len(observed) == len(set(observed))
            except (TypeError, ValueError):
                match = False
            checks[field + '_expected'] = match
            if not match:
                details[field + '_expected'] = {'expected': wanted, 'observed': observed}
    equality_checks = [value for key, value in checks.items()
                       if key.endswith('_equal') or key in ('incremental_valid', 'full_valid')]
    oracle_checks = [value for key, value in checks.items()
                     if key.endswith('_expected') or key == 'expected_valid']
    return {'passed': all(checks.values()), 'equal': all(equality_checks),
            'expected_match': all(oracle_checks), 'checks': checks, 'details': details}


def expected_case(case):
    """Complete oracle for each of the six cumulative reference scenarios."""
    if case not in CASES:
        raise ValueError('unknown case: ' + str(case))
    includes_extra = case in ('include', 'declaration', 'flags', 'header')
    repaired = case in ('declaration', 'flags', 'header')
    actual = {'main.o': ['config.h', 'extra.h', 'main.c'] if includes_extra else ['config.h', 'main.c'],
              'helper.o': ['helper.c']}
    declared = {'main.o': ['config.h', 'extra.h', 'main.c', 'unused.h'] if repaired else ['main.c', 'unused.h'],
                'helper.o': ['helper.c']}
    missing = [] if repaired else [
        {'type': 'MISSING', 'target': 'main.o', 'dependency': 'config.h'}]
    if includes_extra and not repaired:
        missing.append({'type': 'MISSING', 'target': 'main.o', 'dependency': 'extra.h'})
    findings = missing + [{'type': 'REDUNDANT', 'target': 'main.o', 'dependency': 'unused.h'}]
    reuse = case in ('unchanged', 'body', 'declaration')
    return {'actual': actual, 'declared': declared, 'findings': findings,
            'reused': list(TARGETS) if reuse else [],
            'refreshed': [] if reuse else list(TARGETS),
            'added': [['MISSING', 'main.o', 'extra.h']] if case == 'include' else [],
            'resolved': [['MISSING', 'main.o', 'config.h'], ['MISSING', 'main.o', 'extra.h']]
                        if case == 'declaration' else []}


def measure_case(project, out, case, previous, scan_fn, expected=None, repeats=5):
    """Save every report before checking it; reuse one immutable old baseline."""
    if repeats < 1:
        raise ValueError('repeats must be positive')
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    expected = expected_case(case) if expected is None else expected
    baseline = copy.deepcopy(previous)
    _save(out / (case + '-baseline.json'), baseline)
    # Write the independent answer before the first measured scan.
    _save(out / (case + '-expected.json'), expected)
    rows, last = [], None
    for repeat in range(1, repeats + 1):
        stem = case + '-r' + str(repeat)
        incremental_path = stem + '-incremental.json'
        full_path = stem + '-full.json'
        try:
            incremental = scan_fn(project, copy.deepcopy(baseline))
            _save(out / incremental_path, incremental)
            full = scan_fn(project)
            _save(out / full_path, full)
        except Exception as error:
            _save(out / (stem + '-error.json'), {'type': type(error).__name__, 'error': str(error)})
            raise
        comparison = compare_reports(incremental, full, expected)
        _save(out / (stem + '-comparison.json'), comparison)
        rows.append({'case': case, 'repeat': repeat, 'equal': comparison['equal'],
                     'expected_match': comparison['expected_match'], 'passed': comparison['passed'],
                     'incremental_s': incremental['elapsed_s'], 'full_s': full['elapsed_s'],
                     'reused': len(incremental['reused']), 'refreshed': len(incremental['refreshed']),
                     'baseline_commit': baseline['commit'], 'current_commit': incremental['commit'],
                     'incremental_json': incremental_path, 'full_json': full_path})
        last = incremental
    _save(out / (case + '.json'), last)
    return rows, last


def performance_summary(rows):
    """Summarize real positive scan times, preserving ratios below one."""
    cases = list(dict.fromkeys(row['case'] for row in rows))
    summary = []
    for case in cases:
        group = [row for row in rows if row['case'] == case]
        inc = [float(row['incremental_s']) for row in group]
        full = [float(row['full_s']) for row in group]
        if any(not math.isfinite(value) or value <= 0 for value in inc + full):
            raise ValueError('invalid scan timing: ' + case)
        mi, mf = median(inc), median(full)
        summary.append({'case': case, 'n': len(group), 'inc_median_s': mi,
                        'full_median_s': mf, 'inc_min_s': min(inc), 'inc_max_s': max(inc),
                        'full_min_s': min(full), 'full_max_s': max(full),
                        'full_over_inc': mf / mi, 'timing_scope': TIMING_SCOPE})
    return summary


def write_csv(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='') as stream:
        if rows:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)


def project_buildchecker(out, targets=TARGETS):
    """Project both dynamic graphs and findings onto exactly the same targets."""
    out = Path(out)
    report = json.loads((out / 'findings.json').read_text())
    if report.get('status') != 'SUCCEEDED' or report.get('build_exit_code') != 0 or report.get('clean_exit_code') != 0:
        raise ValueError('dynamic BuildChecker did not complete a successful clean build')
    if not set(targets).issubset(report.get('observed_targets', [])):
        raise ValueError('dynamic BuildChecker did not observe every projected target')
    result = {}
    for field, filename in [('actual', 'actual-graph.json'), ('declared', 'declared-graph.json')]:
        edges = json.loads((out / filename).read_text())
        result[field] = {target: sorted(edge['dependency'] for edge in edges if edge['target'] == target)
                         for target in targets}
    result['findings'] = [{key: finding[key] for key in ('type', 'target', 'dependency')}
                          for finding in report['findings'] if finding['target'] in targets]
    result['projection_targets'] = list(targets)
    result['baseline_source'] = 'BuildChecker strace and GNU Make database object-target projection'
    _canonical(result)
    return result


def matrix_gate(rows, out, dynamic_check, cases=CASES, repeats=5, expecteds=None):
    """Re-read raw evidence, fixed oracles, metadata and the historical chain.

    Standard cases always use the independent ``expected_case`` oracle. A caller
    adding a custom case must explicitly provide its oracle in ``expecteds``;
    editing a saved expected JSON never changes the gate's expected answer.
    """
    out = Path(out)
    counts = Counter(row['case'] for row in rows)
    checks = {'case_counts': counts == Counter({case: repeats for case in cases}),
              'row_count': len(rows) == len(cases) * repeats,
              'dynamic_crosscheck': dynamic_check.get('passed') is True}
    pairs, raw_paths = [], set()
    try:
        previous_report = json.loads((out / 'baseline.json').read_text())
        _canonical(previous_report)
        checks['initial_baseline'] = True
        if cases and cases[0] == 'unchanged':
            checks['initial_baseline_oracle'] = compare_reports(previous_report, expected_case('unchanged'))['passed']
    except (OSError, ValueError, TypeError) as error:
        previous_report = None
        checks['initial_baseline'] = False
    for case in cases:
        group = [row for row in rows if row['case'] == case]
        checks[case + '_repeats'] = sorted(row['repeat'] for row in group) == list(range(1, repeats + 1))
        expected = expected_case(case) if case in CASES else (expecteds or {}).get(case)
        checks[case + '_oracle_available'] = expected is not None
        try:
            baseline = json.loads((out / (case + '-baseline.json')).read_text())
            saved_expected = json.loads((out / (case + '-expected.json')).read_text())
            _canonical(baseline)
        except (OSError, ValueError, TypeError) as error:
            checks[case + '_inputs'] = False
            pairs.append({'case': case, 'passed': False, 'error': str(error)})
            previous_report = None
            continue
        checks[case + '_inputs'] = True
        checks[case + '_independent_oracle'] = (expected is not None and
            compare_reports(saved_expected, expected, expected)['passed'])
        checks[case + '_baseline_chain'] = previous_report is not None and baseline == previous_report
        checks[case + '_same_baseline'] = all(row.get('baseline_commit') == baseline.get('commit') for row in group)
        last_report, current_commits = None, set()
        for row in group:
            repeat = row['repeat']
            pair_checks = {}
            try:
                # Exact names bind each row to its own measured pair and exclude
                # reused paths, path traversal, or references outside this OUT.
                stem = case + '-r' + str(repeat)
                pair_checks['paths_match_repeat'] = (
                    type(repeat) is int and 1 <= repeat <= repeats and
                    row['incremental_json'] == stem + '-incremental.json' and
                    row['full_json'] == stem + '-full.json')
                if not pair_checks['paths_match_repeat']:
                    raise ValueError('raw report paths do not match case/repeat')
                paths = [(out / row[name]).resolve() for name in ('incremental_json', 'full_json')]
                pair_checks['paths_unique'] = len(set(paths)) == 2 and not any(path in raw_paths for path in paths)
                incremental = json.loads((out / row['incremental_json']).read_text())
                full = json.loads((out / row['full_json']).read_text())
                raw_paths.update(paths)
                comparison = compare_reports(incremental, full, expected)
                pair_checks['reports'] = comparison['passed']
                # CSV values must describe the raw pair, rather than a cached gate.
                pair_checks['csv_result'] = (row['passed'] is comparison['passed'] and
                           row['equal'] is comparison['equal'] and
                           row['expected_match'] is comparison['expected_match'])
                pair_checks['csv_timing'] = (
                           row['incremental_s'] == incremental['elapsed_s'] and
                           row['full_s'] == full['elapsed_s'])
                pair_checks['positive_timing'] = all(
                    type(value) in (int, float) and math.isfinite(value) and value > 0
                    for value in (incremental['elapsed_s'], full['elapsed_s']))
                pair_checks['csv_identity'] = (row['current_commit'] == incremental['commit'] == full['commit'] and
                           row['baseline_commit'] == baseline['commit'] and
                           isinstance(incremental['key'], dict) and incremental['key'] == full['key'])
                pair_checks['csv_cache_counts'] = (type(row['reused']) is int and type(row['refreshed']) is int and
                           row['reused'] == len(incremental['reused']) and
                           row['refreshed'] == len(incremental['refreshed']))
                pair_checks['full_refresh'] = (full['reused'] == [] and
                           sorted(full['refreshed']) == sorted(TARGETS))
                matches = all(value for name, value in pair_checks.items() if name.startswith('csv_'))
                pairs.append({'case': case, 'repeat': repeat,
                              'passed': all(pair_checks.values()), 'checks': pair_checks,
                              'incremental_json': row['incremental_json'], 'full_json': row['full_json'],
                              'comparison': comparison, 'csv_matches_raw': matches})
                current_commits.add(incremental['commit'])
                if repeat == repeats:
                    last_report = incremental
            except (OSError, ValueError, KeyError, TypeError) as error:
                pairs.append({'case': case, 'repeat': repeat, 'passed': False,
                              'checks': pair_checks, 'error': str(error)})
        checks[case + '_same_current_commit'] = len(current_commits) == 1
        try:
            summary = json.loads((out / (case + '.json')).read_text())
            checks[case + '_last_report'] = last_report is not None and summary == last_report
        except (OSError, ValueError) as error:
            checks[case + '_last_report'] = False
        previous_report = last_report
    checks['raw_pairs'] = len(pairs) == len(cases) * repeats and all(pair['passed'] for pair in pairs)
    checks['unique_raw_json_count'] = len(raw_paths) == len(cases) * repeats * 2
    return {'track': 'A', 'passed': all(checks.values()), 'rows': len(rows),
            'raw_json_count': len(raw_paths),
            'cases': dict(counts), 'checks': checks, 'pairs': pairs,
            'dynamic_crosscheck': dynamic_check, 'timing_scope': TIMING_SCOPE}
