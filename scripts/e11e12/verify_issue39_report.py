"""Issue #39 consumer: apply the public hash and envelope validators."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def consume(report_path, expected_sha256, expected_commit, kind, out):
    # Import only the checked-out public foundation; do not fetch or copy it.
    sys.path.insert(0, str(ROOT / 'labs/e11e12'))
    import pipeline

    result = {
        'scope': 'issue39 personal report consumer',
        'input': str(report_path),
        'expected_sha256': expected_sha256,
        'expected_commit': expected_commit,
        'expected_kind': kind,
        'status': 'RUNNING',
        'accepted': False,
    }
    try:
        report = pipeline.load_artifact(report_path, expected_sha256)
        pipeline.check_envelope(report, expected_commit, kind)
    except pipeline.Failure as error:
        result.update(status='FAILED', error={'code': error.code, 'message': str(error)})
    else:
        result.update(status='SUCCEEDED', accepted=True,
                      commit=report['commit'], configuration_id=report.get('configuration_id'),
                      job_id=report.get('job_id'), trace_id=report.get('trace_id'),
                      schema_version=report['schema_version'])
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--commit', required=True)
    parser.add_argument('--kind', required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = consume(args.report, args.sha256, args.commit, args.kind, args.out)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['accepted'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
