"""Verify source pins, 22 tests twice and forward/reverse evidence byte identity.

Hashes establish equality relative to this manifest, not author/provider origin.
Run only source you have reviewed; this verifier is not a hostile-code sandbox.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
INPUTS = {'README.md', 'audit.py', 'test_audit.py', 'protocol.json', 'verify_public.py'}
OUTPUTS = {'results.json', 'miswire.jsonl', 'raw_half_two.jsonl', 'calibration.json'}


def check(ok, message):
    if not ok:
        raise RuntimeError(message)


def pairs(items):
    result = {}
    for key, value in items:
        check(key not in result, 'duplicate JSON key: '+key)
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError('non-finite JSON: '+value)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(args, env):
    proc = subprocess.run([sys.executable, *args], cwd=ROOT, env=env,
                          capture_output=True, text=True, timeout=180)
    text = proc.stdout+proc.stderr
    check(proc.returncode == 0, 'subprocess failed:\n'+text)
    return text


def main():
    manifest = json.loads((ROOT/'published_result.json').read_text(encoding='utf-8'),
                          object_pairs_hook=pairs, parse_constant=reject_constant)
    check(set(manifest['source_sha256']) == INPUTS, 'unexpected source inventory')
    check(set(manifest['output_sha256']) == OUTPUTS, 'unexpected evidence inventory')
    for name, expected in manifest['source_sha256'].items():
        check(digest(ROOT/name) == expected, 'source hash mismatch: '+name)
    print('PASS: all five source/document pins')
    env = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}
    with tempfile.TemporaryDirectory(prefix='reset-switch-verify-') as directory:
        for label, mode, reverse, seed in (('normal', [], [], '17'),
                                            ('optimized', ['-O'], ['--reverse'], '919')):
            local_env = {**env, 'PYTHONHASHSEED': seed}
            result = run([*mode, '-m', 'unittest', '-v', 'test_audit'], local_env)
            check('Ran 22 tests' in result and '\nOK' in result, 'unexpected test report')
            target = Path(directory)/label
            run([*mode, 'audit.py', '--out', str(target), *reverse], local_env)
            check({p.name for p in target.iterdir()} == OUTPUTS, 'output inventory mismatch')
            for name, expected in manifest['output_sha256'].items():
                check(digest(target/name) == expected, label+' output mismatch: '+name)
            print('PASS:', label, '22 tests and four frozen output hashes')
    print('VERIFIED: same-author exact reproduction; no live-model or authentication claim')


if __name__ == '__main__':
    main()
