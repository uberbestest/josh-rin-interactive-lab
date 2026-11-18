"""Shared verification helpers; all writes use temporary paths outside evidence."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_forensics(root):
    root=Path(root)
    with tempfile.TemporaryDirectory(prefix='receipt-forensic-verification-') as temporary:
        receipt=Path(temporary)/'replay.json'
        process=subprocess.run([sys.executable,'-B',str(root/'forensics/replay.py'),'--output',str(receipt)],
                               capture_output=True,text=True)
        if process.returncode:
            raise AssertionError('Retrospective forensic verification failed: '+process.stderr+process.stdout)
        result=json.loads(receipt.read_text())
    retained=json.loads((root/'forensics/retained/replay.json').read_text())
    # Runtime versions are recorded as diagnostics, not scientific observations.
    def scientific(value):
        if isinstance(value,dict):return {k:scientific(v) for k,v in value.items() if k not in ('node_version','python_version')}
        if isinstance(value,list):return [scientific(v) for v in value]
        return value
    if scientific(result)!=scientific(retained):
        raise AssertionError('Retrospective forensic replay differs from retained results')
    keys=('status','inputs_verified','scripted_service_replays','parser_routing_fixtures',
          'original_combined_prefixes_exact','original_combined_full_states_exact_after_archived_finish',
          'projection_counterfactual_safe_joint_completions','predicate_only_counterfactual_safe_joint_completions',
          'scoped_parser_counterfactual_safe_joint_completions')
    return {**{key:result[key] for key in keys},'retained_scientific_results_exact':True,
            'retained_result_sha256':sha(root/'forensics/retained/replay.json'),
            'scope':'Retrospective authored helper/service replays and mocked parser-routing fixtures; not native participant contexts or prospective native outcomes.'}
