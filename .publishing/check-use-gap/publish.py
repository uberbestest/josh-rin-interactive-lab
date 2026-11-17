#!/usr/bin/env python3
"""Bounded public release builder. No model, credential, bridge, or Castle access.
Called on an isolated staging branch; never pushes or merges itself.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SITE=ROOT/'experiments/check-use-gap'

def require(ok,message):
    if not ok:raise RuntimeError(message)

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def execute(args,name,cwd=SITE,env=None):
    logs=SITE/'checks';logs.mkdir(exist_ok=True)
    p=subprocess.run(args,cwd=cwd,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    (logs/(name+'.log')).write_text(p.stdout)
    print(name,p.returncode,flush=True)
    require(p.returncode==0, name+' failed: '+p.stdout[-3000:])
    return p.stdout

def prepare():
    execute([sys.executable,'-m','unittest','-v','study.StudyTests'],'baseline-tests',SITE/'baseline')
    execute([sys.executable,'-m','unittest','-v','test_study'],'tests')
    execute([sys.executable,'-O','-m','unittest','-v','test_study'],'tests-optimized')
    with tempfile.TemporaryDirectory() as tmp:
        execute([sys.executable,'study.py','--out',tmp],'baseline-reproduction',SITE/'baseline')
        require((Path(tmp)/'results.json').read_bytes()==(SITE/'baseline/results.json').read_bytes(),'baseline result mismatch')
    execute([sys.executable,'study.py','--out','results'],'primary')
    execute([sys.executable,'audit.py'],'mutations')
    frozen=json.loads((SITE/'frozen-results.json').read_text())
    for name,digest in frozen.items():require(sha(SITE/name)==digest,'frozen output mismatch '+name)
    compared=[]
    with tempfile.TemporaryDirectory() as tmp:
        execute([sys.executable,'study.py','--reverse','--out',tmp],'reverse',env={**os.environ,'PYTHONHASHSEED':'29'})
        for path in sorted(Path(tmp).iterdir()):
            require(path.read_bytes()==(SITE/'results'/path.name).read_bytes(),'order mismatch '+path.name);compared.append(path.name)
    cert=json.loads(execute([sys.executable,'verify_certificates.py'],'certificates'))
    js=json.loads(execute(['node','verify_js.cjs'],'javascript'))
    summary=json.loads((SITE/'results/summary.json').read_text())
    require(cert['nodes']==summary['certificate_nodes'],'certificate node count')
    require(cert['certificates']==summary['parameter_cells'],'certificate count')
    require(js['cells']==summary['parameter_cells'] and js['replays']==summary['schedule_policy_replays'],'JS coverage')
    for path in SITE.rglob('*'):
        if path.suffix in ('.py','.js','.html','.md','.json','.txt'):
            text=path.read_text()
            require('file_00000000' not in text,'private file reference in '+str(path))
    receipt={'record':summary['record'],'status':'NUMERICAL_CHECKS_PASSED_BROWSER_PENDING',
             'baseline_tests':16,'new_named_tests':31,'new_tests_modes':['ordinary','optimized (same tests)'],
             'baseline_original_results_sha256':sha(SITE/'baseline/results.json'),
             'exact_outputs_matched':len(frozen),'reverse_order_files_identical':compared,
             'certificate_checker':cert,'javascript_cross_check':js,
             'primary':summary,'external_independent_review':False,'live_model_calls':0,'castle_changes':0}
    (SITE/'verification.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')

def integrate():
    path=ROOT/'index.html';text=path.read_text()
    if 'id="check-use-gap"' not in text:
        marker='<div class="lab-experiment-grid">';require(text.count(marker)==1,'gallery anchor')
        card='''
<article class="card" data-topic="verification" id="check-use-gap"><div><div class="meta"><span>Permission freshness &amp; safe progress</span><span>2026-11-16 · Exact policy synthesis</span></div><h3>The Check That Arrived Too Early</h3><p>A genuine permission check can still arrive too early. Before calling an agent unhelpful, calculate what a safe agent could accomplish through its action interface.</p><p><strong>Change the contract, not the intelligence.</strong> Compare snapshot-only, version-bound and current-atomic actions. Replay the optimal policy without leaking the operator's hidden future.</p><div class="actions"><a class="open" href="experiments/check-use-gap/index.html">Operate the instrument ↗</a><a class="quiet" href="experiments/check-use-gap/method.html">Methods &amp; proofs</a><a class="quiet" href="experiments/check-use-gap/evidence.zip">Source &amp; evidence ↓</a></div></div><details class="lab-evidence"><summary>Evidence &amp; limitations</summary><p class="eyebrow">Executed finite-game policy synthesis</p><dl><dt>Verified</dt><dd>1,056 parameter cells; 55,272 schedule–policy replays; 1,587,332 certificate states</dd><dt>Default result</dt><dd>Best safe completion: 3/10, 9/10 and 10/10 feasible histories under three interfaces</dd><dt>Boundary</dt><dd>Zero live agents. Known finite model, same-author cross-checks; not a production guard or Castle integration.</dd></dl></details></article>
'''
        text=text.replace(marker,marker+card,1)
        count=len(re.findall(r'<article class="card"',text))
        text=re.sub(r'\d+ instruments · newest study \d{4}-\d{2}-\d{2}',f'{count} instruments · newest study 2026-11-16',text,count=1)
        start='<div class="start-grid">'
        if start in text:
            text=text.replace(start,start+'\n<a href="experiments/check-use-gap/index.html"><strong>New: The Check That Arrived Too Early ↗</strong><span>Can a perfectly safe agent be unfairly scored as unhelpful? Calculate the exact interface limit.</span></a>',1)
        path.write_text(text)
    path=ROOT/'README.md';text=path.read_text()
    if '## The Check That Arrived Too Early' not in text:
        note='''## The Check That Arrived Too Early — November 16, 2026

**[Operate the instrument](experiments/check-use-gap/index.html)** · [Methods and proofs](experiments/check-use-gap/method.html) · [Source and complete evidence](experiments/check-use-gap/evidence.zip) · [Verification receipt](experiments/check-use-gap/verification.json)

Executed finite-game policy synthesis: **1,056 parameter cells**, **55,272 schedule–policy replays**, and **1,587,332 machine-checked certificate states**. In the default deadline case, the best safe policy completes 3/10, 9/10, or 10/10 feasible histories depending on the action interface. Python, JavaScript, certificate checking, and tiny-horizon policy enumeration agree. **Zero live model calls; designed overlapping histories, not independent trials; same-author checks, not external validation.** No Castle or bridge changes.

'''
        first=text.find('\n## ');require(first>=0,'README section anchor')
        text=text[:first+1]+note+text[first+1:];path.write_text(text)

def package():
    browser=json.loads((SITE/'checks/browser.json').read_text());require(browser['status']=='PASS' and browser['scope']=='exhibit and integrated repository gallery','integrated HTTP browser check not passed')
    receipt=json.loads((SITE/'verification.json').read_text())
    require(receipt['status']=='NUMERICAL_CHECKS_PASSED_BROWSER_PENDING','unexpected preparation receipt')
    receipt['status']='PUBLIC_PACKAGE_VERIFIED';receipt['browser']=browser
    (SITE/'verification.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
    files=[p for p in sorted(SITE.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.name not in ('MANIFEST.json','evidence.zip')]
    payload={str(p.relative_to(SITE)):{'sha256':sha(p),'bytes':p.stat().st_size} for p in files}
    archive=SITE/'evidence.zip'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in files:
            info=zipfile.ZipInfo('check-use-gap/'+str(p.relative_to(SITE)),date_time=(2000,1,1,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o644<<16
            z.writestr(info,p.read_bytes())
    with zipfile.ZipFile(archive) as z:require(z.testzip() is None,'ZIP CRC failed')
    manifest={'record':receipt['record'],'files':payload,'archive':{'name':'evidence.zip','sha256':sha(archive),'bytes':archive.stat().st_size},'self_excluded':True}
    (SITE/'MANIFEST.json').write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':'PACKAGED','files':len(files),'archive':manifest['archive']}))

if __name__=='__main__':
    cli=argparse.ArgumentParser();cli.add_argument('step',choices=['prepare','integrate','package']);args=cli.parse_args()
    globals()[args.step]()
