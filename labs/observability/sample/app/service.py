"""Small HTTP task and worker services for the observability lab."""

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
from http.client import HTTPException
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import threading
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import uuid


def encode(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True).encode('utf-8')


def log(service, event, job, **fields):
    entry = {'timestamp': datetime.now(timezone.utc).isoformat(), 'service': service,
             'event': event, 'job_id': job['job_id'], 'trace_id': job['trace_id'], **fields}
    print(encode(entry).decode(), flush=True)


def compare_dependencies():
    data = json.loads(Path(__file__).with_name('dependencies.json').read_text(encoding='utf-8'))
    actual, declared = set(data['actual']), set(data['declared'])
    return {'target': data['target'], 'missing': sorted(actual - declared),
            'redundant': sorted(declared - actual)}


class Jobs:
    def __init__(self, worker_url):
        self.worker_url = worker_url
        self.lock = threading.Lock()
        self.pool = ThreadPoolExecutor(max_workers=2)
        self.jobs = {}
        self.keys = {}
        self.totals = dict.fromkeys(('SUCCEEDED', 'FAILED', 'TIMED_OUT'), 0)
        self.duration = 0.0

    def submit(self, body):
        if not isinstance(body, dict):
            return 400, {'error_code': 'INVALID_REQUEST'}
        key, sample = body.get('idempotency_key'), body.get('sample')
        if not isinstance(key, str) or not 1 <= len(key) <= 100 or sample not in ('dependencies', 'slow'):
            return 400, {'error_code': 'INVALID_REQUEST'}
        with self.lock:
            if key in self.keys:
                job = self.jobs[self.keys[key]]
                if job['sample'] != sample:
                    return 409, {'error_code': 'IDEMPOTENCY_CONFLICT'}
                return 202, dict(job)
            job = {'job_id': 'job-' + uuid.uuid4().hex, 'trace_id': 'trace-' + uuid.uuid4().hex,
                   'sample': sample, 'status': 'QUEUED'}
            self.jobs[job['job_id']] = job
            self.keys[key] = job['job_id']
            log('api', 'job_queued', job, stage='queue', level='INFO')
            self.pool.submit(self.run, job)
            return 202, dict(job)

    def run(self, job):
        started = time.monotonic()
        with self.lock:
            job['status'] = 'RUNNING'
        report = None
        status, error = 'FAILED', 'DOWNSTREAM_UNAVAILABLE'
        request = Request(self.worker_url, data=encode({k: job[k] for k in ('job_id', 'trace_id', 'sample')}),
                          headers={'Content-Type': 'application/json'})
        for attempt in range(1, 4):
            log('api', 'worker_call', job, stage='check', attempt=attempt, level='INFO')
            try:
                with urlopen(request, timeout=2) as response:
                    report = json.load(response)
                status, error = 'SUCCEEDED', None
                break
            except HTTPError as exc:
                status, error = 'FAILED', 'DOWNSTREAM_HTTP_ERROR'
                log('api', 'worker_error', job, stage='check', attempt=attempt, level='WARN',
                    error_code=error, http_status=exc.code)
                exc.close()
                if exc.code < 500:
                    break
            except (OSError, HTTPException) as exc:
                timed_out = isinstance(getattr(exc, 'reason', exc), TimeoutError)
                status = 'TIMED_OUT' if timed_out else 'FAILED'
                error = 'DOWNSTREAM_TIMEOUT' if timed_out else 'DOWNSTREAM_UNAVAILABLE'
                log('api', 'worker_error', job, stage='check', attempt=attempt, level='WARN', error_code=error)
            except ValueError:
                status, error = 'FAILED', 'INVALID_WORKER_RESPONSE'
                log('api', 'worker_error', job, stage='check', attempt=attempt, level='WARN', error_code=error)
                break
            if attempt < 3:
                time.sleep(0.5)
        elapsed = time.monotonic() - started
        with self.lock:
            job.update(status=status, error_code=error, attempts=attempt, duration_ms=round(elapsed * 1000))
            if report is not None:
                job['report'] = report
                job['artifact'] = {'path': f"/v1/jobs/{job['job_id']}/report",
                                   'sha256': hashlib.sha256(encode(report)).hexdigest()}
            self.totals[status] += 1
            self.duration += elapsed
            log('api', 'job_finished', job, stage='finish', status=status, error_code=error,
                level='INFO' if error is None else 'ERROR', attempts=attempt, duration_ms=job['duration_ms'])

    def get(self, job_id):
        with self.lock:
            return dict(self.jobs[job_id]) if job_id in self.jobs else None

    def metrics(self):
        with self.lock:
            lines = ['# TYPE lab_jobs_total counter']
            lines += [f'lab_jobs_total{{status="{key}"}} {value}' for key, value in self.totals.items()]
            lines += ['# TYPE lab_job_duration_seconds summary',
                      f'lab_job_duration_seconds_count {sum(self.totals.values())}',
                      f'lab_job_duration_seconds_sum {self.duration:.6f}']
        return ('\n'.join(lines) + '\n').encode()


def serve(role, port):
    jobs = Jobs(os.environ.get('WORKER_URL', 'http://worker:8080/check')) if role == 'api' else None

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def reply(self, code, payload, content_type='application/json; charset=utf-8'):
            data = payload if isinstance(payload, bytes) else encode(payload)
            try:
                self.send_response(code)
                self.send_header('Content-Type', content_type)
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def do_GET(self):
            if self.path == '/health':
                return self.reply(200, {'status': 'ok', 'service': role})
            if self.path == '/metrics':
                data = jobs.metrics() if jobs else b'# TYPE lab_worker_ready gauge\nlab_worker_ready 1\n'
                return self.reply(200, data, 'text/plain; version=0.0.4; charset=utf-8')
            parts = self.path.strip('/').split('/')
            if jobs and len(parts) in (3, 4) and parts[:2] == ['v1', 'jobs']:
                job = jobs.get(parts[2])
                if job and len(parts) == 3:
                    return self.reply(200, {k: v for k, v in job.items() if k != 'report'})
                if job and parts[3:] == ['report'] and 'report' in job:
                    return self.reply(200, job['report'])
            return self.reply(404, {'error_code': 'NOT_FOUND'})

        def do_POST(self):
            if self.path != ('/v1/jobs' if jobs else '/check'):
                return self.reply(404, {'error_code': 'NOT_FOUND'})
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 4096:
                    raise ValueError('invalid length')
                body = json.loads(self.rfile.read(length))
            except ValueError:
                return self.reply(400, {'error_code': 'INVALID_REQUEST'})
            if jobs:
                return self.reply(*jobs.submit(body))
            if not isinstance(body, dict) or not all(isinstance(body.get(k), str) for k in ('job_id', 'trace_id', 'sample')):
                return self.reply(400, {'error_code': 'INVALID_REQUEST'})
            if body['sample'] not in ('dependencies', 'slow'):
                return self.reply(400, {'error_code': 'INVALID_REQUEST'})
            log('worker', 'check_started', body, stage='check', level='INFO')
            if body['sample'] == 'slow':
                time.sleep(3)
            result = compare_dependencies()
            log('worker', 'check_finished', body, stage='check', level='INFO')
            return self.reply(200, result)

    ThreadingHTTPServer(('0.0.0.0', port), Handler).serve_forever()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('role', choices=('api', 'worker'))
    parser.add_argument('--port', type=int, default=8080)
    args = parser.parse_args()
    serve(args.role, args.port)
