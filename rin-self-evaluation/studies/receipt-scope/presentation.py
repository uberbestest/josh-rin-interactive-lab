"""Pure receipt projection and an exact-output hash chain, independent of mechanics."""
from __future__ import annotations
import copy
import hashlib
import json
from engine import digest

SCOPES = ('combined', 'target')

def validate_transport(value):
    if not isinstance(value, dict) or set(value) != {'receipt_scope'} or value['receipt_scope'] not in SCOPES:
        raise ValueError('Invalid receipt transport settings')
    return value['receipt_scope']

def project(observation, action, job, scope):
    if scope not in SCOPES:
        raise ValueError('Unknown receipt scope')
    result = copy.deepcopy(observation)
    if (action == 'receipt' and scope == 'target'
            and isinstance(result.get('local_status'), dict)
            and isinstance(result['local_status'].get('jobs'), dict)):
        if job not in ('A', 'B') or result.get('job') not in (None, job):
            raise ValueError('Receipt target mismatch')
        jobs = result['local_status']['jobs']
        if job not in jobs:
            raise ValueError('Target job is missing from canonical status')
        result['local_status']['jobs'] = {job:jobs[job]}
    return result

def stdout_text(observation):
    # Identical serialization to the inherited client, including trailing newline.
    return json.dumps(observation, sort_keys=True, ensure_ascii=False) + '\n'

def new_presentation(event, previous_hash, scope):
    job = event['parameters'].get('job')
    shown = project(event['observation'], event['action'], job, scope)
    output = stdout_text(shown)
    row = {'event_index':event['index'], 'action':event['action'], 'job':job,
           'raw_event_sha256':event['event_sha256'], 'previous_presentation_sha256':previous_hash,
           'shown_observation':shown, 'stdout':output,
           'stdout_sha256':hashlib.sha256(output.encode('utf-8')).hexdigest()}
    row['presentation_sha256'] = digest(row)
    return row

def verify_presentations(events, presentations, scope):
    if len(events) != len(presentations):
        raise ValueError('Service/presentation checkpoint counts differ')
    previous = '0' * 64
    for event, row in zip(events, presentations):
        expected = new_presentation(event, previous, scope)
        if row != expected:
            raise ValueError('Presentation bytes, projection or hash chain differs at event ' + str(event['index']))
        previous = row['presentation_sha256']
    return {'presentation_events_verified':len(events), 'exact_stdout_records_verified':len(events),
            'stdout_bytes_verified':sum(len(row['stdout'].encode('utf-8')) for row in presentations),
            'last_presentation_sha256':previous}
