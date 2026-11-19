#!/usr/bin/env python3
"""Verify and reproduce the standalone Round09 controller evidence archive."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tempfile
import zipfile


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive',type=Path)
    parser.add_argument('--frozen-sha256',required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='continuation-public-check-') as folder:
        destination=Path(folder)
        with zipfile.ZipFile(args.archive) as archive:
            names=archive.namelist()
            if len(names)!=len(set(names)):
                raise ValueError('Duplicate archive entry')
            for item in archive.infolist():
                path=PurePosixPath(item.filename)
                if path.is_absolute() or '..' in path.parts or '\\' in item.filename:
                    raise ValueError('Unsafe archive path')
                if item.external_attr>>16 & 0o170000 == 0o120000:
                    raise ValueError('Archive symlink not permitted')
            archive.extractall(destination)
        root=destination/'continuation-repair'
        inventory=json.loads((root/'INVENTORY.json').read_text())
        actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
        expected=set(inventory['files'])|{'INVENTORY.json'}
        if actual!=expected:
            raise AssertionError('Archive inventory differs')
        for name,meta in inventory['files'].items():
            raw=(root/name).read_bytes()
            if len(raw)!=meta['bytes'] or sha(raw)!=meta['sha256']:
                raise AssertionError('Archive payload differs: '+name)
        if sha((root/'protocol/frozen.json').read_bytes())!=args.frozen_sha256:
            raise AssertionError('Wrong prospective freeze')
        check=destination/'reproduction.json'
        completed=subprocess.run([sys.executable,'-B',str(root/'verify.py'),'--reproduce',
                                  '--output',str(check)],text=True,capture_output=True,timeout=180)
        if completed.returncode:
            raise RuntimeError('Archive reproduction failed: '+completed.stderr[-2000:])
        result=json.loads(check.read_text())
        result.pop('checks',None)
        diagnostic_check=destination/'posthoc-reproduction.json'
        diagnostic_run=subprocess.run([sys.executable,'-B',str(root/'verify_posthoc.py'),
                                       '--output',str(diagnostic_check)],
                                      text=True,capture_output=True,timeout=180)
        if diagnostic_run.returncode:
            raise RuntimeError('Separate diagnostic reproduction failed: '+diagnostic_run.stderr[-2000:])
        diagnostics=json.loads(diagnostic_check.read_text())
        if diagnostics['status']!='PASS' or diagnostics['runs_reproduced']!=6:
            raise AssertionError('Unexpected exploratory diagnostic verification')
        result.update(public_archive_sha256=sha(args.archive.read_bytes()),
                      preserved_scientific_record_files=len(inventory['files']),
                      final_reports_exact=True,
                      exploratory_diagnostics=diagnostics)
        # Every original file is rechecked after reproduction; no retained record
        # is overwritten or repaired by the verifier.
        for name,meta in inventory['files'].items():
            if sha((root/name).read_bytes())!=meta['sha256']:
                raise AssertionError('Verification changed retained input: '+name)
        result['all_public_files_unchanged_during_verification']=True
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,indent=2,sort_keys=True))


if __name__=='__main__':main()
