#!/usr/bin/env python3
"""Run an argv without a shell; record output, cwd, timestamps and exit status."""
import argparse
import datetime
import html
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import time
import uuid

def render_journal(directory):
    lines = ['# Recorded commands', '',
             'Live records only. Earlier work is in [reconstructed history](history-reconstructed.md).',
             'Open the command record for full argv, working directory and timestamps.', '',
             '| Started (UTC) | Phase | Exit | Command | Output |',
             '| --- | --- | ---: | --- | --- |']
    for path in sorted(directory.glob('*.json')):
        row = json.loads(path.read_text())
        command = html.escape(row['command'].replace('\n', ' ')).replace('|', '&#124;')
        if len(command) > 160:
            command = command[:157] + '...'
        code = 'pending/unknown' if row['exit_code'] is None else str(row['exit_code'])
        lines.append(f"| {row['started_utc']} | {row['phase']} | {code} | "
                     f"[<code>{command}</code>](commands/{path.name}) | "
                     f"[transcript](commands/{row['output']}) |")
    (directory.parent / 'COMMANDS.md').write_text('\n'.join(lines) + '\n')

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--system', required=True)
    p.add_argument('--phase', required=True)
    p.add_argument('command', nargs=argparse.REMAINDER)
    args = p.parse_args()
    command = args.command
    if command and command[0] == '--':
        command = command[1:]
    for value in (args.system, args.phase):
        if not re.fullmatch(r'[A-Za-z0-9_-]+', value):
            p.error('System and phase must contain letters, numbers, underscores or hyphens.')
    if not command:
        p.error('Provide a command after --.')
    now = datetime.datetime.now(datetime.timezone.utc)
    directory = Path(__file__).resolve().parent / 'systems' / args.system / 'commands'
    directory.mkdir(parents=True, exist_ok=True)
    stem = now.strftime('%Y%m%dT%H%M%S.%fZ') + '-' + uuid.uuid4().hex[:6]
    metadata = {'provenance': 'live', 'system': args.system, 'phase': args.phase,
                'started_utc': now.isoformat(), 'cwd': os.getcwd(), 'argv': command,
                'command': shlex.join(command), 'output': stem + '.log',
                'exit_code': None}
    try:
        metadata['git_commit'] = subprocess.check_output(
            ['git', '-C', str(Path(__file__).resolve().parent), 'rev-parse', 'HEAD'],
            text=True, stderr=subprocess.DEVNULL).strip()
    except subprocess.CalledProcessError:
        metadata['git_commit'] = None
    target = directory / (stem + '.json')
    target.write_text(json.dumps(metadata, indent=2) + '\n')
    render_journal(directory)
    print('$ ' + metadata['command'], flush=True)
    started = time.monotonic()
    code = 127
    with (directory / (stem + '.log')).open('wb') as output:
        try:
            proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            while chunk := proc.stdout.read1(65536):
                output.write(chunk)
                output.flush()
                sys.stdout.buffer.write(chunk)
                sys.stdout.buffer.flush()
            code = proc.wait()
        except OSError as error:
            message = (str(error) + '\n').encode()
            output.write(message)
            sys.stderr.write(message.decode())
        except KeyboardInterrupt:
            # The foreground command receives the same terminal SIGINT.
            code = proc.wait()
    metadata.update(exit_code=code, duration_seconds=time.monotonic() - started,
                    ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    target.write_text(json.dumps(metadata, indent=2) + '\n')
    render_journal(directory)
    print(f'Command record: {target}', flush=True)
    return code if code >= 0 else 128 - code

if __name__ == '__main__':
    sys.exit(main())
