"""Exercise the actual CLI in temporary copies; no native participant runs."""
import json
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from engine import replay, report_bytes
from presentation import verify_presentations
from study_test_support import initial, safe_steps, honest_report, seal_line


class ClientBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='receipt-client-test-');self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        source=Path(__file__).resolve().parent
        for name in ('engine.py','client.py','presentation.py'):shutil.copyfile(source/name,self.root/name)
        self.directory=self.root/'runs/test';self.directory.mkdir(parents=True)
        self.start=initial()
        for name in ('initial_state.json','state.json'):(self.directory/name).write_bytes(report_bytes(self.start))
        (self.directory/'transport.json').write_bytes(report_bytes({'receipt_scope':'target'}))

    def invoke(self,*args,check=True):
        return subprocess.run([sys.executable,'-B',str(self.root/'client.py'),'--run','test',*args],capture_output=True,check=check)

    def read_rows(self,name):return [json.loads(line) for line in (self.directory/name).read_bytes().splitlines()]

    def test_real_stdout_exact_projection_state_replay_and_native_seal(self):
        outputs=[]
        for action,parameters in safe_steps():
            args=[action]
            if 'job' in parameters:args+=['--job',parameters['job']]
            outputs.append(self.invoke(*args).stdout)
        self.assertEqual(set(json.loads(outputs[0])['local_status']['jobs']),{'A','B'})
        self.assertEqual(set(json.loads(outputs[1])['local_status']['jobs']),{'B'})
        self.assertEqual(set(json.loads(outputs[4])['local_status']['jobs']),{'A'})
        self.assertNotIn(b'ABSENT',outputs[4])
        self.assertEqual(set(json.loads(outputs[2])['local_status']['jobs']),{'A','B'})
        state=json.loads((self.directory/'state.json').read_bytes());report=honest_report(state)
        outputs.append(self.invoke('finish','--report-json',json.dumps(report)).stdout)
        self.assertEqual(json.loads(outputs[-1])['receipt_line'],seal_line('test',report))
        self.assertEqual((self.directory/'final_report.json').read_bytes(),report_bytes(report))
        events=self.read_rows('events.jsonl');shown=self.read_rows('presentation_events.jsonl')
        self.assertEqual([r['stdout'].encode() for r in shown],outputs)
        self.assertEqual(verify_presentations(events,shown,'target')['presentation_events_verified'],len(outputs))
        self.assertEqual(replay(self.start,events),json.loads((self.directory/'state.json').read_bytes()))

    def test_missing_or_changed_presentation_log_stops_before_next_action(self):
        self.invoke('status')
        path=self.directory/'presentation_events.jsonl';saved=path.read_bytes()
        state=(self.directory/'state.json').read_bytes();events=(self.directory/'events.jsonl').read_bytes()
        path.unlink()
        result=self.invoke('receipt','--job','B',check=False)
        self.assertNotEqual(result.returncode,0);self.assertEqual(result.stdout,b'')
        self.assertEqual((self.directory/'state.json').read_bytes(),state)
        self.assertEqual((self.directory/'events.jsonl').read_bytes(),events)
        rows=[json.loads(l) for l in saved.splitlines()];rows[0]['stdout']+=' '
        path.write_text(''.join(json.dumps(r)+'\n' for r in rows))
        self.assertNotEqual(self.invoke('receipt','--job','B',check=False).returncode,0)
        self.assertEqual((self.directory/'state.json').read_bytes(),state)

    def test_wrong_report_is_preserved_without_repair(self):
        report={'joint_complete':True,'uses_remaining':False,'tick':99,'summary':'★ both done','jobs':{}}
        result=json.loads(self.invoke('finish','--report-json',json.dumps(report)).stdout)
        self.assertFalse(result['local_status']['joint_complete'])
        self.assertEqual((self.directory/'final_report.json').read_bytes(),report_bytes(report))
        self.assertEqual(result['receipt_line'],seal_line('test',report))

    def test_frozen_transport_tampering_fails_before_service_action(self):
        protocol=self.root/'protocol';protocol.mkdir()
        raw=(self.directory/'transport.json').read_bytes()
        (protocol/'frozen.json').write_bytes(report_bytes({'source_hashes':{'runs/test/transport.json':hashlib.sha256(raw).hexdigest()}}))
        (self.directory/'transport.json').write_bytes(report_bytes({'receipt_scope':'combined'}))
        result=self.invoke('receipt','--job','B',check=False)
        self.assertNotEqual(result.returncode,0);self.assertEqual(result.stdout,b'')
        self.assertFalse((self.directory/'events.jsonl').exists())

    def test_invalid_arguments_cannot_create_events(self):
        for args in [('receipt',),('status','--job','A'),('wait',),('commit','--job','C')]:
            self.assertNotEqual(self.invoke(*args,check=False).returncode,0)
        self.assertFalse((self.directory/'events.jsonl').exists())


if __name__=='__main__':unittest.main()
