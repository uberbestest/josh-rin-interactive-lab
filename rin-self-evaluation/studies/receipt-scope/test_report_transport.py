"""The real CLI must seal supplied report content without adding a checklist."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from engine import report_bytes, replay
from test_engine import initial


class ReportTransportTests(unittest.TestCase):
    def test_core_only_report_is_accepted_and_never_backfilled(self):
        source = Path(__file__).resolve().parent
        with tempfile.TemporaryDirectory(prefix='two-job-open-report-test-') as folder:
            root = Path(folder)
            for name in ('engine.py', 'client.py', 'presentation.py'): shutil.copyfile(source/name, root/name)
            directory = root/'runs/test'; directory.mkdir(parents=True)
            (directory/'transport.json').write_bytes(report_bytes({'receipt_scope':'combined'}))
            start = initial('F07')
            for name in ('initial_state.json', 'state.json'): (directory/name).write_bytes(report_bytes(start))
            report = {'joint_complete': False, 'uses_remaining': 4, 'tick': 0,
                      'summary': 'No job was completed.', 'additional_note': 'This is an authored CLI fixture.'}
            output = subprocess.run([sys.executable, '-B', str(root/'client.py'), '--run', 'test',
                                     'finish', '--report-json', json.dumps(report)],
                                    text=True, capture_output=True, check=True)
            observation = json.loads(output.stdout)
            raw = (directory/'final_report.json').read_bytes()
            self.assertEqual(raw, report_bytes(report))
            self.assertNotIn('jobs', json.loads(raw))
            self.assertEqual(observation['receipt_line'], 'SEALED test ' + hashlib.sha256(raw).hexdigest())
            events = [json.loads(line) for line in (directory/'events.jsonl').read_text().splitlines()]
            self.assertEqual(events[0]['parameters']['report'], report)
            self.assertEqual(replay(start, events), json.loads((directory/'state.json').read_text()))


if __name__ == '__main__':
    unittest.main()
