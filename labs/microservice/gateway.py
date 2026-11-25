"""Use the E12 task API to submit jobs to the E14 Compose roles."""

from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'labs' / part) for part in ('e11e12', 'e13e14')]
from orchestrate import DownstreamFailure, execute, host_path
from pipeline import artifact, save, validate_request
from server import Store, make_server
from telemetry import Metrics, log


STAGES = {
    'draft-response.json': 'draft',
    'baseline-response.json': 'full-check',
    'target-response.json': 'full-check',
    'incremental-response.json': 'incremental-check',
    'repair-response.json': 'repair',
    'recheck-response.json': 'recheck',
}
MAX_ATTEMPTS = 3
opener = build_opener(ProxyHandler({}))
metrics = Metrics('a11_jobs', 'service="api"')


def validate_input(request):
    validate_request(request)
    if request['mode'] != 'e12':
        raise ValueError('The microservice API accepts mode=e12')
    if request.get('build_timeout', 600) > 600:
        raise ValueError('build_timeout must be at most 600 seconds')


def role_call(role, payload, evidence):
    phase = STAGES[evidence.name]
    url = f'http://{role}:8080/v1/run'
    request = Request(url, data=json.dumps(payload).encode(),
                      headers={'Content-Type': 'application/json'})
    fields = dict(job_id=payload['job_id'], trace_id=payload['trace_id'],
                  stage=phase, downstream=role)
    begin = time.monotonic()
    for attempt in range(1, MAX_ATTEMPTS + 1):
        log('api', 'stage_attempt', attempt=attempt, **fields)
        retry = False
        upstream = None
        try:
            with opener.open(request, timeout=660 if role == 'draft' else 120) as response:
                result = json.load(response)
            if result['status'] != 'SUCCEEDED':
                raise ValueError('Role returned an unexpected state')
            save(evidence, result)
            log('api', 'stage_finished', status='SUCCEEDED', attempts=attempt,
                duration_ms=round((time.monotonic() - begin) * 1000), **fields)
            return result
        except HTTPError as exc:
            with exc:
                raw = exc.read(65536).decode(errors='replace')
            upstream = {'http': exc.code, 'response': raw}
            try:
                is_timeout = json.loads(raw).get('error_code') == 'TIMEOUT'
            except (ValueError, AttributeError):
                is_timeout = False
            code = 'DOWNSTREAM_TIMEOUT' if is_timeout else 'DOWNSTREAM_REJECTED'
            message = f'{role} returned HTTP {exc.code}'
        except (URLError, TimeoutError) as exc:
            reason = exc.reason if isinstance(exc, URLError) else exc
            if isinstance(reason, TimeoutError):
                code, message = 'DOWNSTREAM_TIMEOUT', f'{role} timed out'
            else:
                code, message = 'DOWNSTREAM_UNAVAILABLE', f'{role}: {reason}'
                # A read timeout can occur after the role started writing output.
                retry = isinstance(reason, (ConnectionRefusedError, socket.gaierror))
        except (OSError, ValueError, TypeError, KeyError) as exc:
            code, message = 'DOWNSTREAM_RESPONSE_ERROR', f'{role}: {exc}'
        log('api', 'stage_attempt_failed', error_code=code, attempt=attempt, **fields)
        if retry and attempt < MAX_ATTEMPTS:
            time.sleep(0.5)
            continue
        error = dict(code=code, message=message, stage=phase, role=role, attempts=attempt)
        if upstream:
            error['upstream'] = upstream
        save(evidence, error)
        log('api', 'stage_finished', status='TIMED_OUT' if code == 'DOWNSTREAM_TIMEOUT' else 'FAILED',
            error_code=code, attempts=attempt, duration_ms=round((time.monotonic() - begin) * 1000),
            **fields)
        raise DownstreamFailure(error)


def publish(result, runtime, out):
    """Expose the five stage envelopes and patch via the course E12 client."""
    job_id = result['job_id']
    exported = {key: result[key] for key in ('job_id', 'trace_id', 'status', 'project_profile')}
    exported.update(schema_version='e11e12-1', backend='e14-compose-1', artifacts=[], stages=[])
    for key in ('base_commit', 'target_commit'):
        if key in result:
            exported[key] = result[key]

    def read(path):
        return json.loads((runtime / path).read_text())

    def add(path):
        descriptor = artifact(path, out, job_id)
        exported['artifacts'].append(descriptor)
        return descriptor

    if result['status'] == 'SUCCEEDED':
        repair = read('repair.json')['data']
        for stage in result['stages']:
            name = stage['name']
            path = out / (name + '.json')
            envelope = read(stage['artifact']['uri'])
            envelope.update(schema_version='e11e12-1', kind=name)
            if name == 'recheck':
                envelope['data'].update(validation=repair['validation'],
                                        findings=envelope['data']['result']['result']['findings'])
            save(path, envelope)
            exported['stages'].append(dict(name=name, artifact=add(path)))
        patch = host_path(repair['patch'])
        if not patch.is_relative_to(runtime) or hashlib.sha256(patch.read_bytes()).hexdigest() != repair['sha256']:
            raise ValueError('Patch is outside this job or changed')
        shutil.copyfile(patch, out / 'candidate.patch')
        add(out / 'candidate.patch')
        built = read('draft.json')['data']['result']
        environment = dict(
            draft_image_ids=[item['image_id'] for item in built['attempts'] if 'image_id' in item],
            roles={role: os.environ.get('A11_RUNTIME_IMAGE') for role in ('draft', 'buildchecker', 'echecker', 'mdfixer')},
            draft_image_used_by_downstream=False,
        )
        save(out / 'environment.json', environment)
        add(out / 'environment.json')
    else:
        failure = result.get('error')
        exported['error'] = failure if isinstance(failure, dict) else {
            'code': 'PIPELINE_FAILED', 'message': str(failure),
        }
    save(out / 'result.json', exported)
    return exported


def run(request, out, job_id, trace_id):
    log('api', 'job_started', job_id=job_id, trace_id=trace_id)
    runtime = out / 'runtime'
    request = dict(request, base=request['base'].lower(), target=request['target'].lower())
    result = execute(request, runtime, job_id=job_id, trace_id=trace_id, role_call=role_call)
    return publish(result, runtime, out)


def finished(state):
    seconds = (datetime.fromisoformat(state['finished_at'])
               - datetime.fromisoformat(state['started_at'])).total_seconds()
    metrics.observe(state['status'], max(seconds, 0))
    log('api', 'job_finished', job_id=state['job_id'], trace_id=state['trace_id'],
        status=state['status'], error_code=state.get('error', {}).get('code'),
        duration_ms=round(seconds * 1000))


if __name__ == '__main__':
    deployment = dict(backend='a11-microservice-e14', runtime_image=os.environ.get('A11_RUNTIME_IMAGE'))
    store = Store(ROOT / 'work' / 'microservice-jobs', executor=run,
                  validator=validate_input, finished=finished)
    with make_server('0.0.0.0', 8080, store, deployment, metrics=metrics.render) as http:
        http.serve_forever()
