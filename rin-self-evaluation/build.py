"""Render the static evaluation notebook from its public, reviewed data.

This is presentation code. It never launches participants or changes evidence.
Run `python3 rin-self-evaluation/build.py` from the repository root.
Use --check to verify that committed pages match studies.json without writing.
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parent
REPO_URL = 'https://github.com/uberbestest/josh-rin-interactive-lab/tree/main/rin-self-evaluation'
SITE_URL = 'https://uberbestest.github.io/josh-rin-interactive-lab/rin-self-evaluation/'


def esc(value):
    return html.escape(str(value), quote=True)


def date_label(value):
    return dt.date.fromisoformat(value).strftime('%B %d, %Y').replace(' 0', ' ') if value else 'Not run'


def local_path(value):
    path = PurePosixPath(value)
    if path.is_absolute() or '..' in path.parts or '\\' in value or ':' in value:
        raise ValueError('Expected a relative publication path')
    return esc(value)


def validate(data):
    studies = data['studies']
    if not studies or len({s['round'] for s in studies}) != len(studies):
        raise ValueError('Study rounds must be present and unique')
    for study in studies:
        for key in ['round', 'title', 'record_id', 'status', 'kind', 'design', 'run_date',
                    'published_date', 'model_note', 'tldr', 'columns', 'results', 'files',
                    'interpretation', 'scope_caveats', 'verification_notes', 'original_digests']:
            if key not in study:
                raise ValueError(f'Missing {key} in round {study.get("round")}')
        if study['status'] not in ('executed', 'planned', 'blocked'):
            raise ValueError('Unknown study execution status')
        if set(study['tldr']) != {'tested', 'happened', 'outliers'}:
            raise ValueError('Every study requires all three TLDR fields')
        if study['status'] == 'executed' and not study['run_date']:
            raise ValueError('Executed study has no run date')
        if any(len(row) != len(study['columns']) for row in study['results']):
            raise ValueError('Result table shape is inconsistent')
        for path in study['files'].values():
            local_path(path)


def page_name(study):
    return f'round-{study["round"]:02d}.html'


def document(title, description, body, current=''):
    active = ' aria-current="page"' if current == 'series' else ''
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="dark">
<meta name="description" content="{esc(description)}">
<title>{esc(title)} · Josh &amp; Rin’s Lab</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<a class="skip-link" href="#main">Skip to the evaluation</a>
<header class="site-header"><nav class="site-nav wrap" aria-label="Lab navigation">
<a class="brand" href="../index.html"><svg aria-hidden="true" viewBox="0 0 30 34" shape-rendering="crispEdges"><path d="M9 0H21V4H19V13L28 27V32H2V27L11 13V4H9Z" fill="#afe6cf"/><path d="M13 4H17V14L25 27V29H5V27L13 14Z" fill="#18313b"/><path d="M10 21H20L25 27V29H5V27Z" fill="#cfb8ed"/></svg>Josh &amp; Rin’s Lab</a>
<div class="nav-links"><a href="index.html"{active}>All evaluations</a><a href="index.html#recording">How we record</a><a href="{REPO_URL}">Source &amp; records ↗</a></div>
</nav></header>
<main id="main" class="wrap">{body}</main>
<footer class="site-footer"><div class="wrap"><span>Josh &amp; Rin · Ongoing model evaluation</span><span>Keep the evidence. Keep the outliers.</span></div></footer>
</body>
</html>
'''


def tldr(study, card=False):
    labels = [('tested', 'What we tested'), ('happened', 'What happened'), ('outliers', 'Outliers')]
    rows = ''.join(f'<div><dt>{label}</dt><dd>{esc(study["tldr"][key])}</dd></div>' for key, label in labels)
    if card:
        return f'<dl class="card-summary">{rows}</dl>'
    return f'<section class="tldr" aria-labelledby="tldr-heading"><h2 id="tldr-heading">TL;DR</h2><dl class="tldr-grid">{rows}</dl></section>'


def kind_badge(study):
    style = ' baseline' if study['kind'] == 'baseline' else ''
    if study['status'] != 'executed':
        return f'<span class="badge planned">{esc(study["status"].capitalize())}</span>'
    return f'<span class="badge{style}">{"Baseline pilot" if study["kind"] == "baseline" else "Matched comparison"}</span>'


def study_card(study):
    return f'''<article class="study-card{' is-baseline' if study['kind'] == 'baseline' else ''}" id="round-{study['round']:02d}" aria-labelledby="title-{study['round']:02d}">
<div class="card-heading"><div><p class="eyebrow">Round {study['round']:02d} · Run {esc(date_label(study['run_date']))}</p><h3 id="title-{study['round']:02d}"><a href="{page_name(study)}">{esc(study['title'])}</a></h3></div>{kind_badge(study)}</div>
{tldr(study, card=True)}
<div class="card-footer"><div class="actions"><a class="button" href="{page_name(study)}">Read this evaluation <span aria-hidden="true">&nbsp;↗</span></a><a href="{local_path(study['files']['report'])}">Report PDF</a></div><p>{esc(study['sample_label'])} · {esc(study['status'].capitalize())}</p></div>
</article>'''


def hub(data):
    studies = sorted(data['studies'], key=lambda s: s['round'], reverse=True)
    executed = [s for s in studies if s['status'] == 'executed']
    matched = sum(s['kind'] == 'matched' for s in executed)
    baseline = sum(s['kind'] == 'baseline' for s in executed)
    jump = ''.join(f'<a href="#round-{s["round"]:02d}">Round {s["round"]:02d}</a>' for s in studies)
    cards = '\n'.join(study_card(s) for s in studies)
    body = f'''<div class="hero">
<p class="eyebrow">An ongoing lab notebook · Opened {esc(date_label(data['publication_date']))}</p>
<h1>Rin 6.1 vs 6.2<br><span class="accent">Self evaluation.</span></h1>
<p class="lede">{esc(data['description'])}</p>
<div class="identity"><strong>Recorded model identities</strong><p>{esc(data['identity_note'])}</p></div>
<div class="stats" aria-label="Series contents"><div class="stat"><b>{len(executed)}</b><span>completed studies</span></div><div class="stat"><b>{matched}</b><span>matched comparisons</span></div><div class="stat"><b>{baseline}</b><span>baseline pilot</span></div></div>
<p class="fine">Each study keeps its own denominators. There is no pooled accuracy score.</p>
</div>
<section aria-labelledby="evaluations-heading"><div class="section-heading"><h2 id="evaluations-heading">The evaluation notebook</h2><p>Newest round first · Every test opens with its TL;DR</p></div>
<p class="prose">{esc(data['current_readout'])}</p><nav class="jump-links" aria-label="Jump to a round">{jump}</nav><div class="study-list">{cards}</div></section>
<section class="series-policy" id="recording" aria-labelledby="recording-heading"><p class="eyebrow">The format for the next round</p><h2 id="recording-heading">A short answer first. Evidence close by.</h2>
<div class="two-columns"><div><h3>At the top of every test</h3><p><strong>What we tested.</strong> The question and the contrast we intended to examine.</p><p><strong>What happened.</strong> The observed result with its eligible denominator.</p><p><strong>Outliers.</strong> Errors, unusual behavior, or informative differences. If none appeared on the measured endpoints, say so.</p></div>
<div><h3>Preserve the record underneath</h3><p>Keep the actual requested selectors, control condition, run and publication dates, protocol, results, reports, and checks. Separate a prepared test from an executed run, and a same-lab check from external replication.</p><p>Retain earlier rounds when the result changes. Add corrections with a date and explanation.</p><div class="actions"><a href="ENTRY_TEMPLATE.md">Next-entry template</a><a href="studies.json">Structured study index</a><a href="README.md">Repository overview</a></div></div></div>
</section>'''
    return document(data['title'], data['description'], body, current='series')


def result_table(study):
    heading = ''.join(f'<th scope="col">{esc(value)}</th>' for value in study['columns'])
    rows = []
    for row in study['results']:
        cells = f'<th scope="row">{esc(row[0])}</th>' + ''.join(f'<td>{esc(value)}</td>' for value in row[1:])
        rows.append('<tr>' + cells + '</tr>')
    return f'<div class="table-wrap" tabindex="0" role="region" aria-label="Recorded result table"><table><caption>{esc(study["result_caption"])}</caption><thead><tr>{heading}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'


def detail(study, data):
    number = study['round']
    model_items = '<br>'.join('<code>' + esc(x) + '</code>' for x in study['selectors']) if study['selectors'] else 'Inherited session; no explicit selector override'
    result = result_table(study)
    observations = ''.join('<p>' + esc(text) + '</p>' for text in study['observations'])
    verification = ''.join('<li>' + esc(text) + '</li>' for text in study['verification_notes'])
    caveats = ''.join('<li>' + esc(text) + '</li>' for text in study['scope_caveats'])
    download_items = [
        ('report', 'Original report · PDF', f'{study["pdf_pages"]} pages. The retained report is published without changing its bytes.'),
        ('evidence', 'Public evidence · ZIP', 'Source, recorded observations and supporting records in a separately identified public disclosure copy.'),
        ('checksum', 'Public archive checksum', 'SHA-256 for the downloadable public ZIP.'),
        ('publication', 'Disclosure and verification receipt', 'What differs from the retained original archive and what was checked for this publication.')]
    downloads = ''.join(f'<a class="download" href="{local_path(study["files"][key])}"><strong>{label}</strong><span>{esc(explanation)}</span></a>' for key, label, explanation in download_items)
    digests = ''.join(f'<dt>{esc(label)}</dt><dd><code>{esc(study["original_digests"][key])}</code></dd>' for key, label in [
        ('report_sha256', 'Original PDF SHA-256'), ('archive_sha256', 'Retained original archive SHA-256 — not the public ZIP checksum'), ('protocol_sha256', 'Retained original frozen-protocol SHA-256')])
    neighboring = sorted(data['studies'], key=lambda s: s['round'])
    nav = []
    pos = next(i for i, s in enumerate(neighboring) if s['round'] == number)
    if pos:
        prev = neighboring[pos - 1]
        nav.append(f'<a href="{page_name(prev)}">← Round {prev["round"]:02d}: {esc(prev["short_title"])}</a>')
    else:
        nav.append('<a href="index.html">← All evaluations</a>')
    if pos + 1 < len(neighboring):
        nxt = neighboring[pos + 1]
        nav.append(f'<a href="{page_name(nxt)}">Round {nxt["round"]:02d}: {esc(nxt["short_title"])} →</a>')
    else:
        nav.append('<a href="index.html#recording">The next-entry format →</a>')
    body = f'''<div class="hero">
<p class="eyebrow">Rin self evaluation · Round {number:02d}</p>
<div class="status-line">{kind_badge(study)}<span>Run: {esc(date_label(study['run_date']))} ({esc(study['run_date_timezone'])})</span><span>Published: {esc(date_label(study['published_date']))}</span></div>
<h1>{esc(study['title'])}</h1>
{tldr(study)}
<div class="actions"><a class="button" href="{local_path(study['files']['report'])}">Read the full report <span aria-hidden="true">&nbsp;↗</span></a><a class="button secondary" href="{local_path(study['files']['evidence'])}">Download public evidence</a><a href="#results">Result table ↓</a></div>
</div>
<section class="content-section" aria-labelledby="setup-heading"><h2 id="setup-heading">Recorded setup</h2>
<dl class="facts"><div><dt>Design</dt><dd>{esc(study['design'])}</dd></div><div><dt>Requested configuration</dt><dd>{model_items}</dd></div><div><dt>Participants</dt><dd>{esc(study['sample_label'])}</dd></div><div><dt>Record identifier</dt><dd><code>{esc(study['record_id'])}</code></dd></div></dl>
<div class="identity"><strong>Model provenance</strong><p>{esc(study['model_note'])}</p></div></section>
<section class="content-section" id="results" aria-labelledby="results-heading"><h2 id="results-heading">Results, with their denominators</h2>{result}<p class="fine">{esc(study['denominator_note'])}</p><p class="prose"><strong>{esc(study['interpretation'])}</strong></p></section>
<section class="content-section" aria-labelledby="differences-heading"><h2 id="differences-heading">Outliers and informative differences</h2><div class="prose">{observations}</div></section>
<section class="content-section" aria-labelledby="verification-heading"><h2 id="verification-heading">What was checked</h2><ul class="detail-list">{verification}</ul><p class="fine">These are retained same-lab checks, including separate model reviewers where recorded. They are not external scientific replication.</p><details class="read-more"><summary>Scope and limits of this result</summary><ul class="detail-list">{caveats}</ul></details></section>
<section class="content-section" id="evidence" aria-labelledby="evidence-heading"><h2 id="evidence-heading">Open the evidence</h2><p class="prose">The original report and the public evidence copy have separate identities. Use the public ZIP’s own checksum and publication receipt when checking the download; its packaging and path disclosures differ from the retained original archive.</p><div class="downloads">{downloads}</div><details class="read-more"><summary>Original artifact identities</summary><dl class="hashes">{digests}</dl></details><div class="actions"><a href="studies.json">Structured study record</a><a href="{REPO_URL}">Browse the committed files ↗</a></div></section>
<nav class="next-links" aria-label="Adjacent evaluations">{''.join(nav)}</nav>'''
    return document(study['title'], study['tldr']['tested'], body)


def readme(data):
    output = [f'# {data["title"]}', '', data['description'], '',
              f'[Open the evaluation notebook]({SITE_URL}) · [Structured index](studies.json) · [Next-entry template](ENTRY_TEMPLATE.md)', '',
              '## Model identity', '', data['identity_note'], '',
              f'This section was first published on {date_label(data["publication_date"])}. Each record lists its run date and timezone separately from its publication date, with its own denominators; there is no pooled accuracy score.', '',
              '## Current readout', '', data['current_readout'], '']
    for study in sorted(data['studies'], key=lambda s: s['round'], reverse=True):
        output.extend([f'## Round {study["round"]:02d} — {study["title"]}', '',
                       f'**What we tested:** {study["tldr"]["tested"]}', '',
                       f'**What happened:** {study["tldr"]["happened"]}', '',
                       f'**Outliers:** {study["tldr"]["outliers"]}', '',
                       f'**Design:** {study["design"]}', '',
                       f'[Read the GitHub record](round-{study["round"]:02d}.md) · [Open the web page]({SITE_URL}{page_name(study)}) · [Report PDF]({study["files"]["report"]}) · [Public evidence ZIP]({study["files"]["evidence"]}) · [Public checksum]({study["files"]["checksum"]}) · [Disclosure receipt]({study["files"]["publication"]})', ''])
    output.extend(['## Ongoing publication format', '',
                   'Start every new test with **What we tested**, **What happened**, and **Outliers**. Record actual requested selectors, serving-snapshot uncertainty, control conditions, execution status, run date, publication date, eligible denominators, protocol, raw evidence, and verification scope. Preserve negative results and earlier versions. Label an unrun protocol as planned.', '',
                   'The original PDFs remain unchanged. Evidence ZIPs are explicitly identified public disclosure copies; their own checksums and disclosure receipts distinguish them from canonical retained archives. Separate model review and independently written checks within this lab are same-lab verification, not external replication.', '',
                   '## Maintain the pages', '',
                   '`studies.json` is the reviewed presentation record. After updating it, run `python3 rin-self-evaluation/build.py` from the repository root to generate the hub, HTML and Markdown study records, and this README. Run `python3 rin-self-evaluation/build.py --check` to check for stale generated pages without writing. The generator launches no models and changes no evidence.', '',
                   'See [the entry template](ENTRY_TEMPLATE.md) and [section instructions](AGENTS.md) before adding another result. Publication checks and public evidence verification are supplied separately; passing a presentation check does not create an additional experiment.', '',
                   'The collected lab has no open-source license selected. Public availability does not establish a reuse license.', ''])
    return '\n'.join(output)


def markdown_record(study):
    output = [f'# Round {study["round"]:02d} — {study["title"]}', '', '## TL;DR', '',
              f'**What we tested:** {study["tldr"]["tested"]}', '',
              f'**What happened:** {study["tldr"]["happened"]}', '',
              f'**Outliers:** {study["tldr"]["outliers"]}', '',
              f'[Open the web page]({SITE_URL}{page_name(study)}) · [Report PDF]({study["files"]["report"]}) · [All evaluations](README.md)', '',
              '## Recorded setup', '',
              f'- **Status:** {study["status"].capitalize()}.',
              f'- **Run date:** {date_label(study["run_date"])} (America/New_York).',
              f'- **Publication date:** {date_label(study["published_date"])}.',
              f'- **Record:** `{study["record_id"]}`.',
              f'- **Design:** {study["design"]}',
              f'- **Participants:** {study["sample_label"]}.', '',
              f'**Model provenance:** {study["model_note"]}', '',
              '## Results, with their denominators', '', study['result_caption'], '',
              '| ' + ' | '.join(study['columns']) + ' |',
              '| ' + ' | '.join(['---'] * len(study['columns'])) + ' |']
    output += ['| ' + ' | '.join(str(value).replace('|', '\\|') for value in row) + ' |' for row in study['results']]
    output += ['', study['denominator_note'], '', f'**Interpretation:** {study["interpretation"]}', '',
               '## Outliers and informative differences', '']
    for text in study['observations']:
        output += [text, '']
    output += ['## What was checked', ''] + ['- ' + text for text in study['verification_notes']]
    output += ['', 'These are retained same-lab checks, including separate model reviewers where recorded. They are not external scientific replication.', '', '## Scope and limits', '']
    output += ['- ' + text for text in study['scope_caveats']]
    output += ['', '## Evidence and publication provenance', '',
               'The original report and public evidence copy have separate identities. Use the public ZIP’s own checksum and disclosure receipt when checking the download. Its packaging and path disclosures differ from the retained original archive.', '',
               f'- [Original report PDF]({study["files"]["report"]}) — {study["pdf_pages"]} pages, unchanged bytes.',
               f'- [Public evidence ZIP]({study["files"]["evidence"]}).',
               f'- [Public archive checksum]({study["files"]["checksum"]}).',
               f'- [Disclosure and verification receipt]({study["files"]["publication"]}).',
               '- [Structured study index](studies.json).', '',
               '### Original artifact identities', '',
               f'- Original PDF SHA-256: `{study["original_digests"]["report_sha256"]}`.',
               f'- Retained original archive SHA-256: `{study["original_digests"]["archive_sha256"]}`. This is not the public ZIP checksum.',
               f'- Retained original frozen-protocol SHA-256: `{study["original_digests"]["protocol_sha256"]}`.', '',
               'Further studies and dated corrections belong in this series. The entry template preserves the same three-field TLDR and provenance structure.', '']
    return '\n'.join(output)


def outputs(data):
    validate(data)
    result = {'index.html': hub(data), 'README.md': readme(data)}
    result.update({page_name(study): detail(study, data) for study in data['studies']})
    result.update({f'round-{study["round"]:02d}.md': markdown_record(study) for study in data['studies']})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    data = json.loads((ROOT / 'studies.json').read_text(encoding='utf-8'))
    generated = outputs(data)
    stale = []
    for name, text in generated.items():
        path = ROOT / name
        if args.check:
            if not path.is_file() or path.read_text(encoding='utf-8') != text:
                stale.append(name)
        else:
            path.write_text(text, encoding='utf-8')
    if stale:
        raise SystemExit('Generated pages are stale: ' + ', '.join(stale))
    print(json.dumps({'status': 'PASS', 'mode': 'check' if args.check else 'build', 'files': list(generated), 'studies': len(data['studies'])}))


if __name__ == '__main__':
    main()
