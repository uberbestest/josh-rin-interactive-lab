"""A temporary-copy CLI boundary check; never touches assigned participant runs."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from engine import replay, report_bytes
from test_engine import initial


class ClientBoundaryTests(unittest.TestCase):
    def test_job_arguments_checkpoints_and_seal_through_real_cli(self):
        source=Path(__file__).resolve().parent
        with tempfile.TemporaryDirectory(prefix='second-door-cli-test-') as folder:
            root=Path(folder)
            for name in ('engine.py','client.py'):
                shutil.copyfile(source/name,root/name)
            directory=root/'runs/test';directory.mkdir(parents=True)
            start=initial('F07')
            for name in ('initial_state.json','state.json'):
                (directory/name).write_bytes(report_bytes(start))
            def invoke(*args):
                result=subprocess.run([sys.executable,'-B',str(root/'client.py'),'--run','test',*args],
                                      capture_output=True,text=True,check=True)
                return json.loads(result.stdout)
            self.assertEqual(invoke('status')['local_status']['uses_remaining'],4)
            for job in ('A','B'):
                self.assertEqual(invoke('commit','--job',job)['status'],'APPLIED')
                self.assertEqual(invoke('finalize','--job',job)['status'],'FINALIZED')
            report={'joint_complete':True,'jobs':{j:{'delivery':'present','finalized':True,'barriers':[]} for j in ('A','B')},
                    'uses_remaining':0,'tick':4,'summary':'Both jobs were committed once and finalized.'}
            sealed=invoke('finish','--report-json',json.dumps(report))
            raw=(directory/'final_report.json').read_bytes()
            self.assertEqual(raw,report_bytes(report))
            self.assertEqual(sealed['receipt_line'],'SEALED test '+hashlib.sha256(raw).hexdigest())
            events=[json.loads(line) for line in (directory/'events.jsonl').read_text().splitlines()]
            self.assertEqual(len(events),6)
            self.assertEqual(replay(start,events),json.loads((directory/'state.json').read_text()))


if __name__=='__main__':
    unittest.main()
