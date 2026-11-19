"""Two explicitly authored scheduling baselines, not model participants.

Both use the same authoritative public status as the candidate. They enforce
per-job evidence and resource admission. They do not search joint futures.
"""
from __future__ import annotations


def finish(status, reason):
    return {'action': 'finish', 'report': {
        'joint_complete': status['joint_complete'],
        'uses_remaining': status['uses_remaining'], 'tick': status['tick'],
        'summary': reason,
        'jobs': {j: {'finalized': d['finalized'], 'delivery': d['delivery']}
                 for j, d in status['jobs'].items()}}}


class GreedyRecovery:
    """Earliest-deadline job first; wait for its guaranteed receipt if needed.

    This has recovery and validates resources. It cannot reason about another
    job's useful work during a wait or shared-budget priority tradeoffs.
    """
    def __init__(self, wait_all=False):
        self.wait_all = wait_all

    def observe_response(self, request, response):
        action = request['action']
        ok = action not in ('receipt', 'commit', 'finalize') or response.get('job') == request.get('job')
        return {'accepted': ok, 'needs_fresh_status': not ok,
                'reason': 'public_status_reconciled_on_next_iteration' if ok else 'job_mismatch'}

    def next_action(self, status):
        if status['joint_complete'] or status['report_sealed'] or status['actions_taken'] >= status['action_limit']:
            return finish(status, 'No further admitted service work.')
        jobs = status['jobs']
        pending = [j for j in jobs if not jobs[j]['finalized']]
        priority = status['priority_if_only_one_can_be_guaranteed']
        pending.sort(key=lambda j: (jobs[j]['deadline'], j != priority, j))
        if self.wait_all:
            future = [jobs[j]['receipt_timing']['guaranteed_by_tick'] - 2
                      for j in pending if jobs[j]['original_write_receipt'] == 'unknown'
                      and jobs[j]['receipt_timing']['kind'] == 'bounded']
            delay = max(future, default=status['tick']) - status['tick']
            if delay > 0:
                return {'action': 'wait', 'ticks': min(20, delay)}
        for job in pending:
            data = jobs[job]
            if data['confirmed_exactly_one_delivery']:
                action, cost, duration = 'finalize', 1, 1
            elif data['original_write_receipt'] == 'ABSENT' and data['acknowledged_recovery_writes'] == 0:
                action, cost, duration = 'commit', 1, 1
            elif data['original_write_receipt'] == 'unknown':
                timing = data['receipt_timing']
                if timing['kind'] != 'bounded':
                    continue
                ready = timing['guaranteed_by_tick']
                delay = max(0, ready - 2 - status['tick'])
                if status['uses_remaining'] < data['query_key_cost'] or status['tick'] + delay + 2 > data['deadline']:
                    continue
                if delay:
                    return {'action': 'wait', 'ticks': min(20, delay)}
                action, cost, duration = 'receipt', data['query_key_cost'], 2
            else:
                continue
            if status['uses_remaining'] >= cost and status['tick'] + duration <= data['deadline']:
                return {'action': action, 'job': job}
        return finish(status, 'The selected deadline-first heuristic found no admitted evidence-backed action.')


POLICIES = {'deadline_greedy': lambda: GreedyRecovery(),
            'wait_all_greedy': lambda: GreedyRecovery(wait_all=True)}
