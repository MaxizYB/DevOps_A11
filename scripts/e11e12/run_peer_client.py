"""One peer command: run a real cJSON API job and archive success/failure evidence."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import uuid
import zipfile

from api_client import run, save


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--operator',required=True,help='Actual B11 operator student ID/name')
    parser.add_argument('--url',default='http://127.0.0.1:18080')
    parser.add_argument('--request',type=Path,default=Path(__file__).with_name('cjson-request.json'))
    parser.add_argument('--deployment-file',type=Path,default=Path(__file__).with_name('deployment.json'))
    parser.add_argument('--out',type=Path,default=Path('records'))
    parser.add_argument('--timeout',type=int,default=1800)
    args=parser.parse_args()
    request=json.loads(args.request.read_text(encoding='utf-8'))
    deployment=json.loads(args.deployment_file.read_text(encoding='utf-8'))
    if request.get('project_profile')!='cjson' or request.get('mode')!='e12':
        parser.error('This handoff must run the agreed cjson/e12 request')
    identifier='b11-cjson-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
    output=args.out/identifier
    started=datetime.now(timezone.utc).isoformat()
    result=run(args.url.rstrip('/'),request,identifier,output,args.timeout,deployment['implementation_sha256'])
    save(output/'operator-record.json',{
        'operator_self_declared':args.operator, 'started_at_utc':started,
        'finished_at_utc':datetime.now(timezone.utc).isoformat(),
        'scope':'Independent B11 client access to integrated server; not a pressure test',
        'input_provenance':'third-party-upstream-history-replay; no original-maintenance claim',
        'agreed_deployment':deployment, 'actual_server_deployment':result.get('deployment'),
        'request_file_sha256':hashlib.sha256(args.request.read_bytes()).hexdigest(),
        'api_client_sha256':hashlib.sha256(Path(__file__).with_name('api_client.py').read_bytes()).hexdigest(),
        'status':result['status'], 'job_id':result.get('job_id'), 'trace_id':result.get('trace_id'),
    })
    archive=output.parent/('B11-E12-cJSON-联调记录-'+identifier+'.zip')
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for path in sorted(output.rglob('*')):
            if path.is_file() and not path.is_symlink():
                z.write(path,identifier+'/'+path.relative_to(output).as_posix())
    print(json.dumps({'status':result['status'],'job_id':result.get('job_id'),
                      'archive':str(archive),'error':result.get('error')},ensure_ascii=False,indent=2))
    return 0 if result['status']=='SUCCEEDED' else 1


if __name__=='__main__':
    raise SystemExit(main())
