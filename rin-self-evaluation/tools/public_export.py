"""Create path-neutralized public disclosure copies of three canonical studies.

The source directory and optional private prefix are command-line inputs. No
private source path is embedded in this program or its published manifests.
Original archives are read-only; historical digest fields are never rewritten.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
import zipfile

SPECS = [
    {'round': 'round-01', 'archive': 'Retry_Receipt_Evidence.zip',
     'sha256': '00872ec1c751056c9967c748a970d73ff8e463b414930fab7e725c5f77bc7bb7',
     'pdf': 'The_Retry_That_Needed_a_Receipt.pdf', 'raw_records': 42},
    {'round': 'round-02', 'archive': 'Receipt_Comparison_Evidence.zip',
     'sha256': '938f0128a3eaed15a2a3f0f3ee99639d4b84a68e681c6dfedc1a3196ed2a5fe9',
     'pdf': 'A_Receipt_That_Had_Not_Caught_Up.pdf', 'raw_records': 78},
    {'round': 'round-03', 'archive': 'Scientific_Identification_Evidence.zip',
     'sha256': '6294e44f587d2ec27ec6d04a77ba4cccdfbe4e423dda010345e135001d15360b',
     'pdf': 'The_Experiment_That_Answers_the_Question.pdf', 'raw_records': 72},
]
RAW_RECORD = re.compile(r'runs/[^/]+/(?:initial_state\.json|state\.json|events\.jsonl)$')
WORKSPACE_METADATA = re.compile(r'(?:runs/[^/]+/(?:prompt|launch_message)\.txt|protocol/(?:TOOL_CONTRACT\.md|CHALLENGE_CONTRACT\.md|frozen\.json)|vendor/baseline_contract\.md|provenance/review_packet\.json|results/freeze_receipt\.json)$')
PLACEHOLDER = '<PRIVATE_WORKSPACE>'


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_bytes(value) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode('utf-8')


def digest_values(value, location=()):
    """All retained hexadecimal digest values, regardless of their field names."""
    if isinstance(value, dict):
        for key in sorted(value):
            yield from digest_values(value[key], location + (key,))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from digest_values(child, location + (index,))
    elif isinstance(value, str) and re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', value):
        yield location, value


def read_archive(path: Path) -> tuple[str, dict[str, bytes]]:
    answer = {}
    roots = set()
    with zipfile.ZipFile(path) as bundle:
        for info in bundle.infolist():
            if info.is_dir():
                continue
            parts = info.filename.split('/')
            if len(parts) < 2 or any(p in ('', '.', '..') for p in parts) or '\\' in info.filename or ':' in info.filename:
                raise ValueError('Unsafe canonical archive path')
            mode = info.external_attr >> 16
            if stat.S_ISLNK(mode):
                raise ValueError('Canonical archive contains a symlink')
            roots.add(parts[0])
            name = '/'.join(parts[1:])
            if name in answer:
                raise ValueError('Duplicate canonical file')
            answer[name] = bundle.read(info)
    if len(roots) != 1:
        raise ValueError('Canonical archive must have one root')
    return next(iter(roots)), answer


def publication_note(spec: dict, frozen: dict) -> bytes:
    text = f'''# Post-run public disclosure copy — {spec['round']}

This is a public copy of **{frozen['record']}**. It was prepared after the
participant runs. Original session filesystem prefixes in prompt, launch,
contract and selected provenance metadata have been replaced by
`<PRIVATE_WORKSPACE>`. Optional baseline presentation-QA output filenames are
relative instead of pointing into a local temporary directory.

The PDF report is unchanged. Every raw initial state, final state and event log
is byte-identical to the canonical archive. Requested model selectors,
observations, responses, final reports, costs, outcomes, timestamps and raw
event/state hashes have not been edited. No new live trials were run.

## Identities and limits

Canonical original archive: `{spec['archive']}`

Canonical original archive SHA256:
`{spec['sha256']}`

`PUBLIC_EXPORT.json` records the original and public digest of every file,
the exact changed-file categories and counts, the original frozen-manifest
identity, and the new public inventory. It does not disclose the private prefix.
The old `frozen.json`, review records, result records and original inventory
retain their historical digest fields. Where path text was neutralized, the
containing file has a different public digest. The original timestamp and
digest claims describe the original record, not a newly frozen experiment.

This copy is **not byte-identical to the original archive**. Its companion
checksum identifies this public ZIP. The canonical originals remain retained
unchanged separately. These are same-lab records and verification, without
external attestation or an independently verified backend model identity.

## Verify this public copy

After extracting, run from this directory:

```sh
python3 verify_public_evidence.py
```

Or use the repository tool on the ZIP, with a fresh temporary extraction:

```sh
python3 tools/verify_public_evidence.py evidence/{spec['round']}.zip --output publication-verification.json
```

The checker requires only the Python standard library. It validates the public
inventory and retained original inventory, enforces every unchanged frozen
source hash, checks each declared path-redacted file against both its original
identity and its new disclosed identity, runs the original semantic tests,
and invokes the unchanged original scientific replay routines. For redacted
prompt and launch text, only in-memory copies of expected hash fields are
adapted to the public bytes. Original digest fields on disk are not rewritten.
Every mechanical result, final report, event count and final event hash must
match the archived original replay results.

The original README/PDF reproduction commands describe verification of the
canonical original bytes. Direct original inventory/replay commands will
reject changed path metadata in this disclosure copy; use the public checker
above. Its receipt is new publication verification, not a replacement for the
original independent-review record and not a claim of new external independence.
It cannot byte-verify the withheld original path text without that private text.
'''
    return text.encode('utf-8')


def export_one(spec: dict, source: Path, destination: Path, private_prefix: str,
               verifier: Path, created_at: str) -> dict:
    archive = source / spec['archive']
    canonical_bytes = archive.read_bytes()
    if sha(canonical_bytes) != spec['sha256']:
        raise ValueError('Canonical archive does not match retained identity: ' + spec['archive'])
    root_name, original = read_archive(archive)
    frozen = json.loads(original['protocol/frozen.json'])
    inventory_name = 'INVENTORY.json' if 'INVENTORY.json' in original else 'provenance/file_inventory.json'
    public = {}
    entries = []
    changed = []
    historical_digests = 0
    for name, before in sorted(original.items()):
        after = before
        rules = []
        try:
            text = before.decode('utf-8')
        except UnicodeDecodeError:
            text = None
        if text is not None:
            count = text.count(private_prefix)
            if count:
                if not WORKSPACE_METADATA.fullmatch(name):
                    raise ValueError('Workspace prefix appears outside the reviewed metadata allowlist: ' + name)
                if PLACEHOLDER in text:
                    raise ValueError('Public placeholder already present in canonical file')
                text = text.replace(private_prefix, PLACEHOLDER)
                rules.append({'category': 'session_workspace_prefix', 'replacement': PLACEHOLDER, 'occurrences': count})
            if name == 'src/report_qa.py':
                count = text.count('/tmp/')
                if count:
                    text = text.replace('/tmp/', '')
                    rules.append({'category': 'optional_qa_temporary_output_prefix',
                                  'replacement': 'relative PNG output filename', 'occurrences': count})
            after = text.encode('utf-8')
        if private_prefix.encode() in after:
            raise ValueError('Original workspace prefix remains in a public file: ' + name)
        if RAW_RECORD.fullmatch(name) and after != before:
            raise ValueError('Scientific record would change: ' + name)
        if name.endswith('.json'):
            old_digests = list(digest_values(json.loads(before)))
            if old_digests != list(digest_values(json.loads(after))):
                raise ValueError('A historical digest field would change: ' + name)
            historical_digests += len(old_digests)
        row = {'path': name, 'status': 'path_redacted' if after != before else 'unchanged',
               'original_sha256': sha(before), 'original_bytes': len(before),
               'public_sha256': sha(after), 'public_bytes': len(after)}
        if rules:
            row['redactions'] = rules
            changed.append(row)
        public[name] = after
        entries.append(row)
    raw_names = sorted(name for name in original if RAW_RECORD.fullmatch(name))
    if len(raw_names) != spec['raw_records'] or any(public[name] != original[name] for name in raw_names):
        raise ValueError('Canonical scientific record preservation failed')
    if public[spec['pdf']] != original[spec['pdf']]:
        raise ValueError('Original PDF changed')
    for name, data in [('PUBLICATION.md', publication_note(spec, frozen)),
                       ('verify_public_evidence.py', verifier.read_bytes())]:
        if name in public:
            raise ValueError('Publication addition collides with canonical file')
        public[name] = data
        entries.append({'path': name, 'status': 'publication_added', 'original_sha256': None,
                        'original_bytes': None, 'public_sha256': sha(data), 'public_bytes': len(data)})
    manifest = {
        'format': 'rin-public-evidence-disclosure-v1', 'round': spec['round'], 'record': frozen['record'],
        'publication_created_at_utc': created_at,
        'canonical_archive': {'name': spec['archive'], 'sha256': spec['sha256'], 'bytes': len(canonical_bytes)},
        'canonical_frozen_sha256': sha(original['protocol/frozen.json']),
        'canonical_inventory': {'path': inventory_name, 'sha256': sha(original[inventory_name])},
        'public_archive_name': spec['round'] + '.zip', 'archive_root': root_name,
        'preserved_scientific_record_files': len(raw_names),
        'scientific_records_byte_identical_to_canonical_at_export': True,
        'historical_digest_values_preserved': historical_digests,
        'redaction_policy': 'Only the original session workspace prefix in reviewed metadata and optional baseline QA temporary-output prefixes were neutralized. Private prefix values are not included. Agent task handles are retained as provenance, not treated as filesystem paths.',
        'changed_file_count': len(changed), 'files': sorted(entries, key=lambda row: row['path']),
        'scope': 'Post-run public disclosure copy, not the original pre-run frozen bytes. Original digest fields remain intact. No scientific data, labels, reports, costs, or outcomes were changed. Canonical original archive and inventory identities are retained separately from public identities.',
    }
    public['PUBLIC_EXPORT.json'] = json_bytes(manifest)
    evidence = destination / 'evidence'
    reports = destination / 'reports'
    evidence.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)
    public_zip = evidence / (spec['round'] + '.zip')
    with zipfile.ZipFile(public_zip, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for name, data in sorted(public.items()):
            info = zipfile.ZipInfo(root_name + '/' + name, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            bundle.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    public_zip_sha = sha(public_zip.read_bytes())
    (evidence / (spec['round'] + '.sha256')).write_text(public_zip_sha + '  ' + public_zip.name + '\n', encoding='utf-8')
    report = reports / (spec['round'] + '.pdf')
    report.write_bytes(original[spec['pdf']])
    with tempfile.TemporaryDirectory(prefix='rin-public-export-check-') as temporary:
        receipt = Path(temporary) / 'verification.json'
        command = [sys.executable, '-B', str(verifier), str(public_zip), '--output', str(receipt)]
        result = subprocess.run(command, text=True, encoding='utf-8', stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, timeout=60, check=False)
        if result.returncode:
            # Do not copy machine paths from diagnostic tracebacks into public artifacts.
            raise ValueError('Fresh public verification failed for ' + spec['round'] + '; rerun its verifier for diagnostics')
        verification = json.loads(receipt.read_text(encoding='utf-8'))
    if verification['status'] != 'PASS' or verification['public_archive_sha256'] != public_zip_sha:
        raise ValueError('Verification receipt and public archive disagree')
    publication = {
        'status': 'PASS', 'publication_kind': 'path-neutralized post-run public disclosure',
        'round': spec['round'], 'record': frozen['record'], 'created_at_utc': created_at,
        'public_archive': public_zip.name, 'public_archive_sha256': public_zip_sha,
        'public_archive_bytes': public_zip.stat().st_size,
        'public_report': '../reports/' + report.name, 'report_sha256': sha(report.read_bytes()),
        'report_byte_identical_to_canonical': True,
        'canonical_archive': manifest['canonical_archive'],
        'canonical_frozen_sha256': manifest['canonical_frozen_sha256'],
        'changed_file_count': len(changed), 'preserved_scientific_record_files': len(raw_names),
        'scientific_records_byte_identical_to_canonical_at_export': True,
        'verification': verification,
        'scope': 'A new publication receipt. It preserves the original scientific results and original evidence identities, but does not replace the original independent review or claim new external independence. All artifact references are relative public names.',
    }
    publication_bytes = json_bytes(publication)
    if private_prefix.encode() in publication_bytes:
        raise ValueError('Private prefix reached the public receipt')
    (evidence / (spec['round'] + '-publication.json')).write_bytes(publication_bytes)
    if sha(archive.read_bytes()) != spec['sha256']:
        raise ValueError('Canonical archive changed during export')
    return {'round': spec['round'], 'public_archive_sha256': public_zip_sha,
            'changed_files': len(changed), 'scientific_files_preserved': len(raw_names),
            'runs_replayed': verification['runs_replayed'], 'events_replayed': verification['events_replayed'],
            'semantic_tests_passed': verification['semantic_tests']['tests'], 'status': 'PASS'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--private-prefix', help='Original session prefix; defaults to the source directory')
    parser.add_argument('--created-at', help='UTC timestamp retained when reproducing this publication export')
    args = parser.parse_args()
    source = args.source_dir.resolve()
    destination = args.output_dir.resolve()
    private_prefix = args.private_prefix or str(source)
    if not private_prefix or private_prefix == '/' or not private_prefix.startswith('/'):
        raise ValueError('Supply a concrete original session prefix')
    verifier = Path(__file__).with_name('verify_public_evidence.py')
    created_at = args.created_at or datetime.datetime.now(datetime.timezone.utc).isoformat()
    summaries = [export_one(spec, source, destination, private_prefix, verifier, created_at) for spec in SPECS]
    print(json.dumps({'status': 'PASS', 'public_exports': summaries,
                      'total_scientific_files_preserved': sum(row['scientific_files_preserved'] for row in summaries)}, indent=2))


if __name__ == '__main__':
    main()
