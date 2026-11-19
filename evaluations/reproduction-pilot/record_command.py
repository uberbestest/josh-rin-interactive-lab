#!/usr/bin/env python3
"""Record an actual local process; no model or provider API calls."""
import argparse,datetime,hashlib,json,subprocess,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--cwd',required=True);p.add_argument('--log',required=True);p.add_argument('command',nargs=argparse.REMAINDER);a=p.parse_args()
cmd=a.command[1:] if a.command[:1]==['--'] else a.command
if not cmd: p.error('command is required')
start=datetime.datetime.now(datetime.timezone.utc).isoformat();timer=time.monotonic()
r=subprocess.run(cmd,cwd=a.cwd,text=True,capture_output=True)
row={'started_at_utc':start,'finished_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'elapsed_seconds':round(time.monotonic()-timer,6),'working_directory_label':Path(a.cwd).name,'argv':cmd,'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'stdout_sha256':hashlib.sha256(r.stdout.encode()).hexdigest(),'stderr_sha256':hashlib.sha256(r.stderr.encode()).hexdigest()}
log=Path(a.log);log.parent.mkdir(parents=True,exist_ok=True)
with log.open('a') as f:f.write(json.dumps(row,sort_keys=True)+'\n')
print(r.stdout,end='');print(r.stderr,end='');raise SystemExit(r.returncode)
