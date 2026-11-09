#!/usr/bin/env python3
"""Check the complete retained package inventory; no assertions disabled by -O."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path,nargs='?',default=Path('.'))
a=p.parse_args();root=a.root.resolve();inventory=json.loads((root/'SHA256SUMS.json').read_text())
for name,expected in inventory.items():
    path=(root/name).resolve()
    if not path.is_relative_to(root) or not path.is_file():raise SystemExit(f'Invalid or absent inventory entry: {name}')
    if hashlib.sha256(path.read_bytes()).hexdigest()!=expected:raise SystemExit(f'Hash mismatch: {name}')
print(f'PASS: {len(inventory)} inventoried files match. This does not authenticate conclusions.')
