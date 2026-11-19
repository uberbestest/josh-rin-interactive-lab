"""Isolated fault tests for evidence retention; no service or study run executes."""
from __future__ import annotations
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import execute


class RetentionTests(unittest.TestCase):
    def exercise(self, failure):
        with tempfile.TemporaryDirectory(prefix='retention-unit-') as temp:
            root=Path(temp)
            sources=root/'source'
            (sources/'input').mkdir(parents=True)
            (sources/'helpers').mkdir()
            for name in ('client.py','engine.py'):
                (sources/'input'/name).write_text('# unit fixture; never executed\n')
            for part in ('setup','recovered'):
                (sources/'helpers'/f'w041_{part}.js').write_text('// unit fixture; never executed\n')
            sentinel={'sentinel':'unit fixture, not a study state'}
            case={'case_id':'unit_failure_retention','adapter':'identity'}
            output=root/'output'
            def interrupted(*args, **kwargs):
                request=json.loads(kwargs['input'])
                directory=Path(request['temporary_root'])/'two-job-study/runs/w041'
                (directory/'events.jsonl').write_text('{"sentinel":"unit event"}\n')
                if failure=='timeout':
                    raise subprocess.TimeoutExpired('/private/unit/path',120)
                if failure=='nonzero':
                    return subprocess.CompletedProcess(args[0],7,'','private stderr must not be retained')
                return subprocess.CompletedProcess(args[0],0,'not-json','')
            with patch.object(execute,'ROOT',sources), patch.object(execute,'initial_for',return_value=sentinel), patch.object(execute.subprocess,'run',side_effect=interrupted):
                with self.assertRaisesRegex(RuntimeError,'available evidence retained'):
                    execute.run_one(None,'unused-node',case,'w041','recovered',output)
            record=output/'runs/unit_failure_retention_w041_recovered'
            self.assertEqual(json.loads((record/'initial_state.json').read_text()),sentinel)
            self.assertEqual(json.loads((record/'state.json').read_text()),sentinel)
            self.assertEqual((record/'events.jsonl').read_text(),'{"sentinel":"unit event"}\n')
            raw=(record/'harness_error.json').read_text()
            self.assertNotIn('/private',raw)
            self.assertNotIn('private stderr',raw)
            meta=json.loads(raw)
            self.assertEqual(meta['status'],'INFRASTRUCTURE_ERROR')
            self.assertEqual(meta['retained_canonical_files'],['initial_state.json','state.json','events.jsonl'])
            expected_code=None if failure=='timeout' else 7 if failure=='nonzero' else 0
            self.assertEqual(meta['subprocess_returncode'],expected_code)

    def test_timeout_retains_canonical_files(self):
        self.exercise('timeout')

    def test_nonzero_retains_canonical_files(self):
        self.exercise('nonzero')

    def test_bad_json_retains_canonical_files(self):
        self.exercise('bad-json')


if __name__=='__main__':
    unittest.main()
