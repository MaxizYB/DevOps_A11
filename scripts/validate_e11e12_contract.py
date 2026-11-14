#!/usr/bin/env python3
"""Dependency-free checks for the A11 E11/E12 orchestration request contract."""

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / 'contracts/samples/e12-orchestration-request.json'
SCHEMA = ROOT / 'contracts/schemas/e12-orchestration-request.schema.json'
COMMIT = re.compile(r'^[0-9a-fA-F]{40}$')


def fail(message):
    raise SystemExit('E11/E12 contract validation failed: ' + message)


def main():
    schema = json.loads(SCHEMA.read_text(encoding='utf-8'))
    if schema.get('title') != 'E11-E12 orchestration request':
        fail('unexpected schema title')
    sample = json.loads(SAMPLE.read_text(encoding='utf-8'))
    if sample.get('mode') != 'e12':
        fail('sample must exercise e12')
    if sample.get('mode') not in {'e11-a', 'e11-b', 'e12'}:
        fail('unknown mode')
    for field in ('repo', 'base', 'target'):
        if not isinstance(sample.get(field), str) or not sample[field]:
            fail(f'{field} is required')
    if not COMMIT.fullmatch(sample['base']) or not COMMIT.fullmatch(sample['target']):
        fail('base/target must be complete commit SHAs')
    if sample['base'].lower() == sample['target'].lower():
        fail('base and target must differ')
    if not isinstance(sample.get('candidate'), str) or not sample['candidate']:
        fail('e12 candidate is required')
    if 'fixed_report' in sample:
        fail('e12 sample must not carry a fixed report')
    if isinstance(sample.get('build_timeout'), bool) or not isinstance(sample.get('build_timeout'), int) or sample['build_timeout'] < 1:
        fail('build_timeout must be positive')
    print('E11/E12 orchestration contract: PASS')


if __name__ == '__main__':
    main()
