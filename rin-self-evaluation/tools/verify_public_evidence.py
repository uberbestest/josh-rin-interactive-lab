"""Verify a trusted public disclosure archive without its private original.

From the repository: python3 tools/verify_public_evidence.py evidence/round-01.zip
Inside an extracted disclosure archive: python3 verify_public_evidence.py
An optional --output writes a new receipt outside the extracted study.

This post-run checker verifies disclosed bytes and replays retained scientific
records. It cannot recover or attest the withheld portions of original paths.
It runs the archive's retained Python semantic tests; use trusted lab archives.
"""
from __future__ import annotations

import argparse
import copy
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import platform
import re
import stat
import subprocess
import sys
import tempfile
import zipfile

MANIFEST = 'PUBLIC_EXPORT.json'
RAW_RECORD = re.compile(r'runs/[^/]+/(?:initial_state\.json|state\.json|events\.jsonl)$')
WORKSPACE_METADATA = re.compile(r'(?:runs/[^/]+/(?:prompt|launch_message)\.txt|protocol/(?:TOOL_CONTRACT\.md|CHALLENGE_CONTRACT\.md|frozen\.json)|vendor/baseline_contract\.md|provenance/review_packet\.json|results/freeze_receipt\.json)$')
CANONICAL = {
    'round-01': {'archive_sha256': '00872ec1c751056c9967c748a970d73ff8e463b414930fab7e725c5f77bc7bb7',
                 'runs': 14, 'events': 84, 'semantic_tests': 12},
    'round-02': {'archive_sha256': '938f0128a3eaed15a2a3f0f3ee99639d4b84a68e681c6dfedc1a3196ed2a5fe9',
                 'runs': 26, 'events': 184, 'semantic_tests': 17},
    'round-03': {'archive_sha256': '6294e44f587d2ec27ec6d04a77ba4cccdfbe4e423dda010345e135001d15360b',
                 'runs': 24, 'events': 78, 'semantic_tests': 33},
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def relative_path(name: str) -> PurePosixPath:
    if not isinstance(name, str) or not name or '\\' in name or ':' in name or '\x00' in name:
        raise ValueError('Invalid public artifact path')
    if any(part in ('', '.', '..') for part in name.split('/')):
        raise ValueError('Noncanonical public artifact path')
    path = PurePosixPath(name)
    if path.is_absolute():
        raise ValueError('Absolute public artifact path')
    return path


def extract(archive: Path, destination: Path) -> Path:
    with zipfile.ZipFile(archive) as bundle:
        entries = []
        names = set()
        roots = set()
        for info in bundle.infolist():
            name = info.filename.rstrip('/') if info.is_dir() else info.filename
            path = relative_path(name)
            if name in names:
                raise ValueError('Duplicate public archive member')
            names.add(name)
            roots.add(path.parts[0])
            mode = info.external_attr >> 16
            if stat.S_ISLNK(mode) or stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR):
                raise ValueError('Nonregular public archive member')
            if info.flag_bits & 1:
                raise ValueError('Encrypted public archive member')
            entries.append((info, destination.joinpath(*path.parts)))
        if len(roots) != 1:
            raise ValueError('Public archive must contain one portable root directory')
        for info, target in entries:
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open('xb') as stream:
                    stream.write(bundle.read(info))
        root = destination / next(iter(roots))
        if not (root / MANIFEST).is_file():
            raise ValueError('Public disclosure manifest is missing')
        return root


def files(root: Path) -> dict[str, Path]:
    result = {}
    for path in root.rglob('*'):
        relative = path.relative_to(root)
        if '__pycache__' in relative.parts or path.suffix in ('.pyc', '.pyo'):
            continue
        if path.is_symlink():
            raise ValueError('Symlink in extracted public study')
        if path.is_file():
            result[relative.as_posix()] = path
        elif not path.is_dir():
            raise ValueError('Nonregular file in extracted public study')
    return result


def original_inventory(root: Path, manifest: dict) -> dict:
    name = relative_path(manifest['canonical_inventory']['path']).as_posix()
    data = (root / name).read_bytes()
    if sha(data) != manifest['canonical_inventory']['sha256']:
        raise ValueError('Retained original inventory changed')
    original = json.loads(data)['files']
    if isinstance(original, list):
        return {row['path']: row for row in original}
    if isinstance(original, dict):
        return original
    raise ValueError('Unsupported original inventory shape')


def check_inventory(root: Path, manifest: dict) -> dict[str, dict]:
    expected = {}
    for row in manifest['files']:
        name = relative_path(row['path']).as_posix()
        if name in expected or name == MANIFEST:
            raise ValueError('Duplicate or self-referential public inventory row')
        expected[name] = row
    actual = files(root)
    if set(actual) != set(expected) | {MANIFEST}:
        raise ValueError('Public inventory file membership differs')
    canonical = original_inventory(root, manifest)
    for name, row in expected.items():
        data = actual[name].read_bytes()
        if len(data) != row['public_bytes'] or sha(data) != row['public_sha256']:
            raise ValueError('Public file digest mismatch: ' + name)
        if row['status'] == 'publication_added':
            if row['original_sha256'] is not None or name not in ('PUBLICATION.md', 'verify_public_evidence.py'):
                raise ValueError('Unexpected publication-added file: ' + name)
            continue
        if name in canonical:
            before = canonical[name]
            if row['original_sha256'] != before['sha256'] or row['original_bytes'] != before['bytes']:
                raise ValueError('Public entry disagrees with original inventory: ' + name)
        elif name != manifest['canonical_inventory']['path']:
            raise ValueError('Original file absent from retained original inventory: ' + name)
        if row['status'] == 'unchanged':
            if row['original_sha256'] != row['public_sha256'] or row['original_bytes'] != row['public_bytes']:
                raise ValueError('Unchanged-file assertion is false: ' + name)
        elif row['status'] == 'path_redacted':
            if RAW_RECORD.fullmatch(name):
                raise ValueError('Scientific event/state files may not be redacted')
            rules = row.get('redactions', [])
            if not rules or any(rule['category'] not in ('session_workspace_prefix', 'optional_qa_temporary_output_prefix')
                                or not isinstance(rule['occurrences'], int) or rule['occurrences'] < 1 for rule in rules):
                raise ValueError('Undeclared public path change: ' + name)
            text = data.decode('utf-8')
            for rule in rules:
                if rule['category'] == 'session_workspace_prefix':
                    if not WORKSPACE_METADATA.fullmatch(name):
                        raise ValueError('Workspace redaction outside reviewed metadata: ' + name)
                    if rule['replacement'] != '<PRIVATE_WORKSPACE>' or text.count('<PRIVATE_WORKSPACE>') != rule['occurrences']:
                        raise ValueError('Workspace placeholder count differs: ' + name)
                elif name != 'src/report_qa.py' or rule['replacement'] != 'relative PNG output filename':
                    raise ValueError('Unexpected QA path change')
        else:
            raise ValueError('Unknown public disclosure status: ' + name)
    if set(canonical) != {name for name, row in expected.items()
                          if row['status'] != 'publication_added' and name != manifest['canonical_inventory']['path']}:
        raise ValueError('Original inventory coverage changed during public disclosure')
    return expected


def check_declared_hash(name: str, declared: str, entries: dict[str, dict]) -> bool:
    row = entries[name]
    if row['original_sha256'] != declared:
        raise ValueError('Historical declared hash disagrees with original file identity: ' + name)
    return row['status'] == 'unchanged'


def semantic_tests(root: Path, count: int) -> dict:
    command = [sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'src', '-p', 'test_*.py']
    result = subprocess.run(command, cwd=root, text=True, encoding='utf-8',
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60, check=False)
    diagnostic = result.stdout + '\n' + result.stderr
    match = re.search(r'Ran (\d+) tests? in ', diagnostic)
    if result.returncode or match is None or int(match.group(1)) != count:
        raise ValueError('Retained semantic tests failed or had an unexpected count')
    return {'status': 'PASS', 'tests': count, 'returncode': result.returncode,
            'command': 'python3 -B -m unittest discover -s src -p "test_*.py"',
            'scope': 'Retained instrument/oracle tests; no participant trials or network calls.'}


def verify(root: Path) -> dict:
    raw_manifest = (root / MANIFEST).read_bytes()
    manifest = json.loads(raw_manifest)
    if manifest.get('format') != 'rin-public-evidence-disclosure-v1':
        raise ValueError('Unknown public disclosure format')
    expected = CANONICAL[manifest['round']]
    if manifest['canonical_archive']['sha256'] != expected['archive_sha256']:
        raise ValueError('Unrecognized canonical study archive')
    entries = check_inventory(root, manifest)
    frozen = read_json(root / 'protocol/frozen.json')
    historical = read_json(root / 'results/replay.json')
    if historical['frozen_protocol_sha256'] != manifest['canonical_frozen_sha256']:
        raise ValueError('Original replay and original freeze identity differ')
    if entries['protocol/frozen.json']['original_sha256'] != manifest['canonical_frozen_sha256']:
        raise ValueError('Original freeze identity differs from disclosure manifest')
    unchanged_sources = disclosed_sources = 0
    for name, declared in frozen['source_hashes'].items():
        if check_declared_hash(name, declared, entries):
            unchanged_sources += 1
        else:
            if not name.endswith(('CONTRACT.md', 'baseline_contract.md')):
                raise ValueError('Frozen scientific code was changed: ' + name)
            disclosed_sources += 1
    if len(frozen['runs']) != expected['runs'] or historical['run_count'] != expected['runs']:
        raise ValueError('Run count differs from canonical study')
    raw_records = {name: row for name, row in entries.items() if RAW_RECORD.fullmatch(name)}
    if len(raw_records) != expected['runs'] * 3 or any(row['status'] != 'unchanged' for row in raw_records.values()):
        raise ValueError('Canonical scientific records are missing or altered')
    if len(raw_records) != manifest['preserved_scientific_record_files']:
        raise ValueError('Preserved scientific record count differs')

    test_result = semantic_tests(root, expected['semantic_tests'])
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(root / 'src'))
    spec = importlib.util.spec_from_file_location('retained_replay', root / 'src/replay.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    originals = {row['run_id']: row for row in historical['runs']}
    if len(originals) != expected['runs'] or set(originals) != {row['run_id'] for row in frozen['runs']}:
        raise ValueError('Original replay rows and declared runs differ')
    events = metadata_changes = mechanical_fields = 0
    comparisons = []
    for original_spec in frozen['runs']:
        rid = original_spec['run_id']
        adapted = copy.deepcopy(original_spec)
        for filename, key in [('prompt.txt', 'prompt_sha256'), ('launch_message.txt', 'launch_message_sha256')]:
            name = 'runs/' + rid + '/' + filename
            unchanged = check_declared_hash(name, original_spec[key], entries)
            if not unchanged:
                metadata_changes += 1
                adapted[key] = entries[name]['public_sha256']
        if 'initial_state_sha256' in original_spec:
            check_declared_hash('runs/' + rid + '/initial_state.json', original_spec['initial_state_sha256'], entries)
        if manifest['round'] == 'round-01':
            actual = module.replay_run(root / 'runs' / rid)
        elif manifest['round'] == 'round-02':
            actual = module.replay_run(root / 'runs' / rid, adapted, frozen)
        else:
            actual = module.replay_run(adapted, frozen)
        original = originals[rid]
        for key, value in actual.items():
            if key not in original or value != original[key]:
                raise ValueError('Replayed scientific result differs: ' + rid + '/' + key)
        for key in ['mechanical', 'report', 'events', 'final_event_hash']:
            if key not in actual:
                raise ValueError('Retained replay omitted a required endpoint')
        events += actual['events']
        mechanical_fields += len(actual['mechanical'])
        comparisons.append({'run_id': rid, 'mechanical_result_exact': True,
                            'final_report_exact': True, 'events': actual['events'],
                            'final_event_hash_exact': True})
    if events != expected['events'] or events != historical['event_count']:
        raise ValueError('Replayed event count differs')
    check_inventory(root, manifest)
    if (root / MANIFEST).read_bytes() != raw_manifest:
        raise ValueError('Disclosure manifest changed during verification')
    return {
        'status': 'PASS', 'verification_kind': 'post-run public disclosure verification',
        'round': manifest['round'], 'record': frozen['record'], 'python_version': platform.python_version(),
        'canonical_archive': manifest['canonical_archive'],
        'canonical_frozen_sha256': manifest['canonical_frozen_sha256'],
        'public_manifest_sha256': sha(raw_manifest),
        'public_inventory_files': len(entries), 'public_inventory_before': 'PASS',
        'public_inventory_after': 'PASS', 'all_public_files_unchanged_during_verification': True,
        'preserved_scientific_record_files': len(raw_records),
        'unchanged_frozen_sources_verified': unchanged_sources,
        'path_redacted_frozen_contracts_verified_against_disclosure': disclosed_sources,
        'changed_prompt_or_launch_files_verified_against_disclosure': metadata_changes,
        'semantic_tests': test_result, 'runs_replayed': len(comparisons), 'events_replayed': events,
        'mechanical_results_exact': len(comparisons), 'mechanical_field_comparisons': mechanical_fields,
        'final_reports_exact': len(comparisons), 'runs': comparisons,
        'scope': 'The unchanged retained replay routines verify every recorded response and state/event hash chain. Prompt/launch hash adaptations exist only in memory and refer to disclosed public bytes. Historical digest fields on disk are unchanged. This is same-lab post-run verification, not new participant evidence, new external independence, or byte verification of withheld original path text.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path, nargs='?')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.archive is not None:
        archive = args.archive.resolve()
        if args.output is not None and args.output.resolve() == archive:
            raise ValueError('A verification receipt cannot overwrite its input archive')
        with tempfile.TemporaryDirectory(prefix='rin-public-evidence-') as folder:
            root = extract(archive, Path(folder))
            result = verify(root)
        result.update({'public_archive': archive.name, 'public_archive_sha256': sha(archive.read_bytes()),
                       'fresh_extraction': True, 'temporary_extraction_removed': True})
    else:
        root = Path(__file__).resolve().parent
        if args.output is not None and args.output.resolve().is_relative_to(root):
            raise ValueError('Write a verification receipt outside the extracted study')
        result = verify(root)
        result['fresh_extraction'] = False
    result['verified_at_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({key: result[key] for key in ['status', 'round', 'runs_replayed', 'events_replayed',
                                                 'preserved_scientific_record_files', 'mechanical_results_exact',
                                                 'final_reports_exact']} | {'semantic_tests_passed': result['semantic_tests']['tests']}, indent=2))


if __name__ == '__main__':
    main()
