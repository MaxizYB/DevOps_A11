"""Host entry; installed alongside E8-E10 files without replacing run_lab.py."""
import argparse
import json
import os
import re
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('stage', choices=['build', 'prepare', 'run', 'serve', 'test'])
parser.add_argument('--request')
parser.add_argument('--out')
parser.add_argument('--port', type=int, default=8080)
args = parser.parse_args()

if os.name != 'posix':
    parser.error('Run on the Linux cloud host after SSH login')
student_id = subprocess.check_output(
    ['git', 'config', '--local', 'user.name'], cwd=root, text=True
).strip()
if not re.fullmatch(r'[0-9]{6,16}', student_id):
    parser.error('Set local git user.name to your numeric student ID')
image = 'course-e11e12:' + student_id

if args.stage == 'build':
    command = [
        'docker', 'build', '-f',
        str(root / 'labs/e11e12/environment/services/buildchecker/Dockerfile'),
        '-t', image, str(root / 'labs/e11e12/environment'),
    ]
else:
    needs_docker_socket = args.stage == 'serve'
    request_path = None
    output_path = None
    if args.stage == 'run':
        if not args.request or not args.out:
            parser.error('--request and --out required')
        request_path = (root / args.request).resolve()
        output_path = (root / args.out).resolve()
        data_root = (root / 'data').resolve()
        if not request_path.is_relative_to(data_root) or not request_path.is_file():
            parser.error('--request must name a JSON file below data/')
        if not output_path.is_relative_to(root / 'work') or output_path == root / 'work':
            parser.error('--out must be a new directory below work/')
        try:
            mode = json.loads(request_path.read_text(encoding='utf-8')).get('mode')
        except (json.JSONDecodeError, AttributeError) as exc:
            parser.error(f'Invalid request JSON: {exc}')
        needs_docker_socket = mode in ('e11-b', 'e12')

    if needs_docker_socket:
        try:
            socket_group = str(Path('/var/run/docker.sock').stat().st_gid)
        except OSError as exc:
            parser.error(f'Docker socket is required for this stage: {exc}')
        network_args = [
            '--network', 'bridge', '--group-add', socket_group,
            '-v', '/var/run/docker.sock:/var/run/docker.sock',
        ]
    else:
        network_args = ['--network', 'none']
    port_args = []
    if args.stage == 'serve':
        if not 1 <= args.port <= 65535:
            parser.error('--port must be between 1 and 65535')
        port_args = ['-p', f'127.0.0.1:{args.port}:8080']
    command = [
        'docker', 'run', '--rm', *network_args, *port_args,
        '--cap-add', 'SYS_PTRACE', '--user', f'{os.getuid()}:{os.getgid()}',
        '-e', 'HOME=/tmp',
        '-e', 'PYTHONPATH=/course/labs/e11e12:/course/labs/e8e10:/course/labs/e11e12/vendor:/app',
        '-v', str(root) + ':/course', '-w', '/course', image, 'python3',
    ]
    if args.stage == 'prepare':
        command += ['labs/e11e12/prepare.py']
    elif args.stage == 'serve':
        command += ['labs/e11e12/server.py', '--host', '0.0.0.0', '--port', '8080']
    elif args.stage == 'test':
        command += ['-m', 'unittest', 'discover', '-s', 'labs/e11e12', '-p', 'test_*.py', '-v']
    else:
        command += [
            'labs/e11e12/pipeline.py', '--request',
            '/course/' + str(request_path.relative_to(root)), '--out',
            '/course/' + str(output_path.relative_to(root)),
        ]

print('IMAGE=' + image, flush=True)
raise SystemExit(subprocess.call(command, cwd=root))
