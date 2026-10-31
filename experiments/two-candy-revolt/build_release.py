#!/usr/bin/env python3
"""Package Candy Revolt from preserved (or verified reproduced) records.
No new treatment, cherry-picked trajectory, or invented dialogue is introduced.
"""
from __future__ import annotations
import argparse, hashlib, html, json, shutil, zipfile
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import mistune
ROOT=Path(__file__).resolve().parent
VERSION='0.1.2'
def sha(b): return hashlib.sha256(b).hexdigest()
def canonical(x): return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def dump(path,x): path.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def array_facts(path):
    with np.load(path,allow_pickle=False) as z:
        return {k:{'shape':list(z[k].shape),'dtype':z[k].dtype.str,'sha256':sha(z[k].tobytes(order='C'))} for k in sorted(z.files)}
def verify():
    expected=json.loads((ROOT/'original-data-manifest.json').read_text()); rows=[]
    for name,item in expected['files'].items():
        p=ROOT/name
        if not p.is_file(): raise ValueError(f'Missing scientific record: {name}')
        actual=sha(p.read_bytes());exact=actual==item['sha256']
        if not exact:
            if 'arrays' in item:
                if array_facts(p)!=item['arrays']: raise ValueError(f'Array mismatch: {name}')
            elif 'canonical_sha256' in item:
                data=json.loads(p.read_text());data.pop('elapsed_seconds',None)
                if sha(canonical(data))!=item['canonical_sha256']:raise ValueError(f'Scientific JSON mismatch: {name}')
            else:raise ValueError(f'Byte mismatch: {name}')
        rows.append({'path':name,'bytes_identical':exact,'sha256':actual,'scientific_content_identical':True})
    result={'status':'PASS','scope':'All original listed scientific records, every array element, shape and dtype; JSON elapsed time excluded. Author-run reproduction, not external peer review.','files':rows,'original_npz_files':sum(x['path'].endswith('.npz') for x in rows),'npz_bytes_identical':sum(x['bytes_identical'] for x in rows if x['path'].endswith('.npz'))}
    dump(ROOT/'results/release-data-verification.json',result)
    return expected,result

def make_data():
    s=json.loads((ROOT/'results/primary/summary.json').read_text())
    with np.load(ROOT/'results/primary/evaluation_trace.npz',allow_pickle=False) as z:
        a=np.stack([z[k][:30] for k in ['action','accept','proposer','receiver']],axis=-1)
        replay=a.reshape(30,24,64,4).transpose(1,2,0,3).tolist()
    data={'cells':s['cells'],'summary':s['summary'],'replay':replay,
          'baseline':json.loads((ROOT/'results/baseline/summary.json').read_text())['summary'],
          'protocol':json.loads((ROOT/'protocol.json').read_text()),
          'freeze':json.loads((ROOT/'protocol-freeze.json').read_text())}
    windows=[]
    with np.load(ROOT/'results/primary/training_trace.npz',allow_pickle=False) as z:
        assert z['action'].shape==(12000,1536)
        for label,start in [('Early',0),('Middle',5985),('Late',11970)]:
            a=np.stack([z[k][start:start+30] for k in ['action','accept','proposer','receiver']],axis=-1)
            windows.append({'label':label,'start_round':start+1,'replay':a.reshape(30,24,64,4).transpose(1,2,0,3).tolist()})
    data['trainingWindows']=windows
    data['uiRepair']={'version':'0.1.1','kind':'presentation-only repair; no new learning run',
        'training_sha256':sha((ROOT/'results/primary/training_trace.npz').read_bytes()),
        'evaluation_sha256':sha((ROOT/'results/primary/evaluation_trace.npz').read_bytes()),
        'window_selection':'First 30, centered 30, final 30 training rounds; same indices for every cell and seed. No selection by outcome.'}
    return data

def patch_home(site):
    path=site/'index.html';s=path.read_text()
    if 'experiments/two-candy-revolt/index.html' not in s:
        marker='<div class="start-grid">';assert s.count(marker)==1
        s=s.replace(marker,marker+'\n<a href="experiments/two-candy-revolt/index.html"><strong>New: The Two-Candy Revolt ↗</strong><span>Start with the TL;DR, watch the goblins learn, and test whether a generous deal survives an incentive to break it.</span></a>',1)
        s=s.replace('repeat(3,minmax(0,1fr))','repeat(2,minmax(0,1fr))')
        assert '09 instruments' in s;s=s.replace('09 instruments','10 instruments',1)
        s=s.replace('<a href="#experiments">The experiments</a>','<a href="#experiments">The experiments</a><a href="experiments/two-candy-revolt/index.html">Halloween Science ↗</a>',1)
        card='''<article class="card" id="two-candy-revolt">
<div><div class="meta"><span>10 / Learning, bargaining &amp; unstable agreements</span><span>Halloween 2026-10-31 · v0.1.2</span></div>
<h3>The Two-Candy Revolt</h3>
<p>Ten goblins can collect every candy and still leave someone in the two-candy job. We let the two unequal roles bargain. Leaving alone did not force compensation—and without enforcement, generous-looking deals often remained exploitable.</p>
<p><strong>Read the TL;DR, then press Play.</strong> Replay actual saved training, change the rules to inspect another completed run, and test a hypothetical contract. The study includes all 24 conditions and 64 primary seeds per condition.</p>
<div class="actions"><a class="open" href="experiments/two-candy-revolt/index.html">Open the Candy Revolt ↗</a><a class="quiet" href="experiments/two-candy-revolt/method.html">Methods, results &amp; limits</a><a class="quiet" href="experiments/two-candy-revolt/index.html#downloads">Full evidence bundle ↓</a></div></div>
<aside><p class="eyebrow">Evidence label · Executed synthetic learners</p><dl><dt>Measured</dt><dd>24 bargaining conditions; 64 seeds each; 12,000 training rounds per seed</dd><dt>Key result</dt><dd>58/64 unenforced veto runs admitted a profitable proposer deviation</dd><dt>Boundary</dt><dd>Two negotiating learners, eight fixed bystanders; not LLMs or invented institutions. Independent review pending.</dd></dl></aside>
</article>
'''
        anchor='<article class="card">';assert anchor in s;s=s.replace(anchor,card+anchor,1)
        path.write_text(s)
    path=site/'README.md';s=path.read_text()
    if '[The Two-Candy Revolt]' not in s:
        marker='| --- | --- | --- | --- |';assert marker in s
        row='| 2026-10-31 | [The Two-Candy Revolt](experiments/two-candy-revolt/index.html) | Read the TL;DR, replay recorded learning, compare refusal and enforcement, and test a hypothetical contract. | Executed synthetic pilot: 24 bargaining cells x 64 seeds; complete records; 58/64 unenforced veto policies admit a profitable proposer deviation. Independent review pending. |'
        s=s.replace(marker,marker+'\n'+row,1)
        marker='## Halloween 2026: The Porch That Ate Halloween';assert marker in s
        s=s.replace(marker,'## Halloween 2026: The Two-Candy Revolt\n\n[The newest exhibit](experiments/two-candy-revolt/index.html) opens with a plain-language TL;DR and a working recorded-learning replay. It separates production, distribution and incentive stability. The [full methods](experiments/two-candy-revolt/method.html) retain the negative shock result and distinguish supplied mechanisms from learned choices. Source, complete training traces and a versioned research ZIP are linked from its downloads section. No external model-agent run or independent Rinball review is claimed.\n\n'+marker,1)
        path.write_text(s)

def build(site=None):
    expected,verification=verify();data=make_data()
    scientific={k:v for k,v in data.items() if k!='uiRepair'}
    if sha(canonical(scientific))!=expected['repaired_exhibit_scientific_payload_sha256']: raise ValueError('Exhibit payload differs from the original repaired exhibit')
    template=(ROOT/'exhibit_template.html').read_text();assert template.count('__DATA__')==1
    (ROOT/'index.html').write_text(template.replace('__DATA__',json.dumps(data,separators=(',',':')).replace('</','<\\/')))
    md=mistune.create_markdown(escape=True,plugins=['table'])
    content=md((ROOT/'README.md').read_text()+'\n\n---\n\n'+(ROOT/'METHODS.md').read_text())
    methods='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="dark"><title>Candy Revolt · Methods and evidence</title><style>:root{color-scheme:dark}*{box-sizing:border-box}body{margin:0;background:#10151b;color:#eee9df;font:17px/1.8 system-ui,sans-serif}main{max-width:960px;margin:auto;padding:30px 24px 70px}nav{display:flex;flex-wrap:wrap;gap:22px;margin-bottom:32px}a{color:#aae3c1}h1,h2,h3{line-height:1.2;color:#ffc07a;margin-top:1.8em}h1{font:3rem/1.1 Georgia,serif}p,li{color:#c2ccd0}table{border-collapse:collapse;display:block;max-width:100%;overflow-x:auto;font-size:.86rem}td,th{padding:12px;border-bottom:1px solid #40505c;text-align:left}pre{overflow-x:auto;padding:18px;background:#1d2933;border-radius:8px}code{font-size:.85em;overflow-wrap:anywhere}blockquote{border-left:3px solid #ffc07a;margin:24px 0;padding:10px 22px;background:#1d2933}:focus-visible{outline:3px solid #ffc07a;outline-offset:4px}</style></head><body><main><nav><a href="../../index.html">← All lab experiments</a><a href="index.html">Open the interactive study</a><a href="index.html#downloads">Downloads and source</a></nav>'''+content+'</main></body></html>'
    (ROOT/'method.html').write_text(methods)
    if site:patch_home(site)
    receipt={'study_id':'CANDY-REVOLT-2026-10-31-001','science_version':'0.1.0','presentation_version':VERSION,
        'status':'PACKAGED_EXECUTED_SYNTHETIC_PILOT','built_at_utc':datetime.now(timezone.utc).isoformat(),
        'independent_review':'Pending. A GitHub queue ticket is not a completed Rinball review.',
        'source_protocol_sha256':sha((ROOT/'protocol.json').read_bytes()),'simulation_source_sha256':sha((ROOT/'run_experiment.py').read_bytes()),
        'scientific_payload_sha256':sha(canonical(scientific)),
        'data_verification':'results/release-data-verification.json','replay_records':184320,
        'original_science_preserved':True,'replay_default':'Recorded learning / Early / seed 2000',
        'changes':['TL;DR at the top','repaired replay incorporated','lab homepage shortcut and newest exhibit card','methods and full evidence downloads'],
        'limits':['Synthetic tabular learners, not LLMs','Two bargaining agents and eight fixed bystanders','Mechanisms supplied, not invented by agents','Frozen-partner incentive probe, not a mutual-adaptation rollout'],
        'source_build':'Results may be deterministically regenerated in the release builder; each scientific array is checked against original content fingerprints. Runtime timestamps are new and raw ZIP-container differences are reported, not hidden.',
        'api_credits_spent':0}
    dump(ROOT/'RELEASE_RECEIPT.json',receipt)
    print('Built',ROOT/'index.html', 'and method.html; original science verified')

def bundle(output):
    omit={'__pycache__','.DS_Store','SHA256SUMS.txt'}
    files=[p for p in sorted(ROOT.rglob('*')) if p.is_file() and not any(x in omit for x in p.relative_to(ROOT).parts) and p.suffix!='.zip']
    (ROOT/'SHA256SUMS.txt').write_text(''.join(sha(p.read_bytes())+'  '+p.relative_to(ROOT).as_posix()+'\n' for p in files))
    files.append(ROOT/'SHA256SUMS.txt')
    with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6,strict_timestamps=False) as z:
        for p in files:z.write(p,'candy-revolt/'+p.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(output) as z: assert z.testzip() is None
    print('Packaged',output,'SHA256',sha(output.read_bytes()))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--site',type=Path);ap.add_argument('--zip',type=Path);ap.add_argument('--bundle-only',action='store_true');a=ap.parse_args()
    if not a.bundle_only:build(a.site)
    if a.zip:bundle(a.zip)
