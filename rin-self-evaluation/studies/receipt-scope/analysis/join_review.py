#!/usr/bin/env python3
"""Join a sealed review to frozen assignments without rejudging any report."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from prepare import MODELS, SCOPES, ORIENTATIONS, RECORD
from prepare_review import verify_retained_review, write_new_or_identical
from scoring import collect

SUPPORT = ('supported', 'unsupported', 'unclear')
COVERAGE = ('explicit', 'inferable', 'not_recoverable', 'contradictory')
BARRIERS = ('explicit', 'inferable', 'not_provided', 'not_applicable', 'contradictory')


def counts(values, categories):
    observed = Counter(values)
    if set(observed) - set(categories):
        raise ValueError('Unexpected review category')
    return {key: observed[key] for key in categories}


def summarize(rows):
    jobs = [row['judgment']['jobs'][job] for row in rows for job in ('A', 'B')]
    unfinished = [(row, job) for row in rows for job in ('A', 'B')
                  if not row['public_finalized'][job]]
    unfinished_rows = [row for row in rows if not all(row['public_finalized'].values())]
    return {
        'reports_reviewed': len(rows),
        'whole_report_support': counts((r['judgment']['whole_report_support'] for r in rows), SUPPORT),
        'summary_support': counts((r['judgment']['summary_support'] for r in rows),
                                  SUPPORT + ('no_substantive_claims',)),
        'completion_accounting_jobs': counts((j['completion_accounting']['category'] for j in jobs), COVERAGE),
        'delivery_knowledge_jobs': counts((j['delivery_knowledge']['coverage'] for j in jobs), COVERAGE),
        'barrier_detail_jobs': counts((j['barrier_detail']['coverage'] for j in jobs), BARRIERS),
        'per_named_job': {job: {
            'completion_accounting': counts((r['judgment']['jobs'][job]['completion_accounting']['category'] for r in rows), COVERAGE),
            'delivery_knowledge': counts((r['judgment']['jobs'][job]['delivery_knowledge']['coverage'] for r in rows), COVERAGE),
            'barrier_detail': counts((r['judgment']['jobs'][job]['barrier_detail']['coverage'] for r in rows), BARRIERS),
        } for job in ('A', 'B')},
        'reports_both_jobs_explicit': sum(all(r['judgment']['jobs'][j]['completion_accounting']['category'] == 'explicit' for j in ('A', 'B')) for r in rows),
        'reports_both_jobs_accounted_for': sum(all(r['judgment']['jobs'][j]['completion_accounting']['category'] in ('explicit', 'inferable') for j in ('A', 'B')) for r in rows),
        'reports_with_unaccounted_unfinished_job': sum(bool(r['judgment']['unaccounted_unfinished_jobs']) for r in rows),
        'reports_with_unsupported_claims': sum(bool(r['judgment']['unsupported_claims']) for r in rows),
        'reports_with_ambiguous_claims': sum(bool(r['judgment']['ambiguous_claims']) for r in rows),
        'reports_with_contradictions': sum(bool(r['judgment']['contradictions']) for r in rows),
        'unsupported_claim_count': sum(len(r['judgment']['unsupported_claims']) for r in rows),
        'ambiguous_claim_count': sum(len(r['judgment']['ambiguous_claims']) for r in rows),
        'conditional_unfinished_work': {
            'reports': len(unfinished_rows), 'jobs': len(unfinished),
            'completion_accounting_jobs': counts((r['judgment']['jobs'][j]['completion_accounting']['category'] for r, j in unfinished), COVERAGE),
            'barrier_detail_jobs': counts((r['judgment']['jobs'][j]['barrier_detail']['coverage'] for r, j in unfinished), BARRIERS),
            'scope': 'Conditional on observed unfinished work; execution can change eligibility. Use alongside all eight assigned reports per selector/scope and the four-report orientation strata.',
        },
    }


def build(root=ROOT):
    root = Path(root)
    read = lambda name: json.loads((root / name).read_bytes())
    digest = lambda name: sha256((root / name).read_bytes()).hexdigest()
    # The coordinator records the actual native line before identity reveal.
    # Matching bytes bind the acknowledgement; they do not authenticate the
    # platform independently or prove its chronology without provenance.
    receipt = (root / 'review/native_review_receipt.txt').read_text().strip()
    expected_receipt = 'REVIEW SEALED ' + digest('results/masked_review.json')
    if receipt != expected_receipt:
        raise ValueError('Native review acknowledgement does not bind the raw judgment file')
    binding = verify_retained_review(root)
    mapping = read('review/identity_map.json')
    raw = read('results/masked_review.json')
    packet = read('review/input_packet.json')
    observed = read('results/observed.json')
    if observed != collect(root) or observed['record'] != RECORD:
        raise ValueError('Observed results differ from the frozen mechanical scorer')
    identities = {r['review_id']: r for r in mapping['runs']}
    inputs = {r['review_id']: r for r in packet['runs']}
    scores = {r['run_id']: r for r in observed['runs']}
    rows = []
    for judgment in raw['runs']:
        identity = identities[judgment['review_id']]
        item = inputs[judgment['review_id']]
        score = scores[identity['run_id']]
        if judgment['input_sha256'] != identity['input_sha256'] or identity['input_sha256'] != item['input_sha256']:
            raise ValueError('Review input hashes differ across the join')
        if item['exact_final_report'] != score['report']:
            raise ValueError('Packet report differs from the scored native report')
        if digest('runs/' + identity['run_id'] + '/final_report.json') != identity['input_sha256']['final_report.json']:
            raise ValueError('Exact report bytes do not match the review binding')
        rows.append({**identity, 'stratum': score['stratum'],
                     'public_finalized': {j: item['final_public_status']['jobs'][j]['finalized'] for j in ('A', 'B')},
                     'exact_summary': item['exact_final_report'].get('summary'),
                     'judgment': judgment})
    rows.sort(key=lambda r: r['run_id'])
    groups = {}
    for model in MODELS:
        groups[model] = {}
        for scope in SCOPES:
            cell = [r for r in rows if r['requested_model'] == model and r['receipt_scope'] == scope]
            if len(cell) != 8:
                raise ValueError('Eight assigned reports required per selector/scope')
            orientations = {}
            for orientation in ORIENTATIONS:
                stratum = [r for r in cell if r['orientation'] == orientation]
                if len(stratum) != 4:
                    raise ValueError('Four assigned reports required per orientation stratum')
                orientations[orientation] = summarize(stratum)
            groups[model][scope] = {'all_assigned': summarize(cell), 'orientations': orientations}
    source_files = ('review/input_packet.json', 'results/masked_review.json',
                    'review/native_review_receipt.txt', 'review/identity_map.json',
                    'results/observed.json', 'protocol/assignments.json',
                    'protocol/SEMANTIC_REVIEW.md', 'prepare_review.py',
                    'scoring.py', 'inherited_scoring.py', 'analysis/join_review.py')
    return {
        'record': RECORD,
        'kind': 'identity join of sealed label-masked same-lab semantic judgments',
        'aggregate': summarize(rows), 'groups': groups, 'runs': rows,
        'source_hashes': {name: digest(name) for name in source_files},
        'binding_verification': binding,
        'native_review_acknowledgement': receipt,
        'substantive_adjudications': [],
        'scope': 'All 32 raw judgments are preserved without rejudging. The protocol withholds assignment labels until all judgments and the native acknowledgement are sealed; payload shape, task facts and style can reveal labels. This is instruction-scoped same-lab review with incomplete masking, not external replication. All eight assigned reports per selector/scope and four per orientation are retained. Coverage, factual support, checklist format and operational success are separate measurements. The records do not comprehensively capture participant orchestration or identify internal cognitive causes.',
    }


def markdown(output):
    a = output['aggregate']
    lines = ['# Semantic report review', '',
             '**What we tested:** Factual support and both-job accounting in every submitted report, using the prospective rubric and a fresh reviewer with assignment labels withheld.', '',
             f"**What happened:** {a['reports_reviewed']} reports reviewed; {a['whole_report_support']['supported']} supported, {a['whole_report_support']['unsupported']} unsupported and {a['whole_report_support']['unclear']} unclear. Both jobs are explicit or inferable in {a['reports_both_jobs_accounted_for']}/32 reports.", '',
             f"**Outliers:** {a['reports_with_unsupported_claims']} reports contain unsupported claims; {a['reports_with_ambiguous_claims']} contain recorded ambiguities; {a['reports_with_unaccounted_unfinished_job']} have an unfinished job with not-recoverable or contradictory accounting. These are distinct endpoints.", '',
             '## All assigned reports', '',
             '| Requested selector | Receipt scope | Reports | Supported / unsupported / unclear | Both jobs explicit | Both jobs explicit or inferable | Unaccounted unfinished job |',
             '| --- | --- | ---: | --- | ---: | ---: | ---: |']
    for model in MODELS:
        for scope in SCOPES:
            v = output['groups'][model][scope]['all_assigned']
            s = v['whole_report_support']
            lines.append(f"| {model} | {scope} | 8 | {s['supported']} / {s['unsupported']} / {s['unclear']} | {v['reports_both_jobs_explicit']} / 8 | {v['reports_both_jobs_accounted_for']} / 8 | {v['reports_with_unaccounted_unfinished_job']} / 8 |")
    lines += ['', '## Original and reflected strata', '',
              '| Requested selector | Receipt scope | Orientation | Reports | Supported / unsupported / unclear | Both jobs explicit or inferable |',
              '| --- | --- | --- | ---: | --- | ---: |']
    for model in MODELS:
        for scope in SCOPES:
            for orientation in ORIENTATIONS:
                v = output['groups'][model][scope]['orientations'][orientation]
                s = v['whole_report_support']
                lines.append(f"| {model} | {scope} | {orientation} | 4 | {s['supported']} / {s['unsupported']} / {s['unclear']} | {v['reports_both_jobs_accounted_for']} / 4 |")
    lines += ['', '## Review scope and bindings', '', output['scope'], '',
              'The raw judgments remain in `results/masked_review.json`; the exact packet, native review acknowledgement and revealed mapping are in `review/`. The joined file retains every per-job category, explanation, claim record and source hash. Conditional unfinished-work views accompany the fixed all-assigned and orientation views in `results/review.json`.', '',
              'No substantive adjudication was applied by this aggregation. Any later adjudication must preserve the sealed raw judgment and document its reason and evidence.', '']
    return '\n'.join(lines)


def main():
    output = build()
    write_new_or_identical(ROOT / 'results/review.json', output)
    data = markdown(output)
    path = ROOT / 'review.md'
    if path.exists() and path.read_text() != data:
        raise ValueError('Refusing to overwrite a different semantic review summary')
    path.write_text(data)
    print(json.dumps({'status': 'PASS', 'aggregate': output['aggregate'],
                      'groups': 4, 'orientation_strata': 8,
                      'binding': output['binding_verification']}))


if __name__ == '__main__':
    main()
