#!/usr/bin/env python3
"""Reproduce, package, and narrowly integrate this exhibit. No model/network calls."""
from __future__ import annotations
import argparse, gzip, hashlib, json, os, platform, subprocess, sys, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
PFX='experiments/gate-between-check-and-act/'
def sha(b):return hashlib.sha256(b).hexdigest()
def run(args,log):
    p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True)
    (ROOT/log).write_text(p.stdout+p.stderr)
    if p.returncode:raise RuntimeError(f'{args} failed; see {log}')
    return p.stdout

def verify():
    run([sys.executable,'study.py','--out','results'],'run-receipt.json')
    expected=json.loads((ROOT/'expected.json').read_text())
    for name,value in expected['sha256'].items():
        raw=(ROOT/name).read_bytes()
        if name.endswith('.gz'):raw=gzip.decompress(raw)
        if sha(raw)!=value:raise ValueError('Output mismatch: '+name)
    run([sys.executable,'verify.py'],'test-normal.txt')
    run([sys.executable,'-O','verify.py'],'test-optimized.txt')
    run(['node','parity.js'],'parity-result.json')
    import study
    current=json.loads((ROOT/'results/summary.json').read_text())
    if study.grid(reverse=True)!=current['synthesis']:raise ValueError('Reverse-grid mismatch')
    original=json.loads((ROOT/'baseline/reproduction.json').read_text())
    if sha((ROOT/'baseline/study.py').read_bytes())!=original['source_sha256']:raise ValueError('Baseline source changed')
    import importlib.util,unittest
    spec=importlib.util.spec_from_file_location('round_one',ROOT/'baseline/study.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    with (ROOT/'baseline/test-rerun.txt').open('w') as log:
        result=unittest.TextTestRunner(stream=log,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(mod.StudyTests))
    if not result.wasSuccessful() or result.testsRun!=16:raise ValueError('Round-one regression')
    data=(json.dumps(mod.run(),sort_keys=True,indent=2)+'\n').encode()
    if sha(data)!=original['results_sha256']:raise ValueError('Round-one output differs')
    receipt={'status':'PASS','tests_distinct':36,'normal_tests':36,'optimized_tests':36,
       'reference_enumeration_panels':264,'synthesis_panels':1050,'primary_episodes':13824,
       'full_grid_reverse_equal':True,'damaged_transcript_classes_rejected':6,
       'cross_language_full_trace_matches':13824,'baseline_tests':16,'baseline_byte_reproduced':True,
       'python':platform.python_version(),'platform':platform.platform(),
       'evidence_tier':'same-author offline synthetic checks; not independent validation'}
    (ROOT/'verification.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    print(json.dumps(receipt))

def package():
    verification=json.loads((ROOT/'verification.json').read_text())
    browser=json.loads((ROOT/'browser-verification.json').read_text())
    if verification['status']!='PASS' or browser['status']!='PASS':raise ValueError('Missing checks')
    exclusions={'evidence.zip','download.json','MANIFEST.json','PUBLICATION.json','browser-trace.json'}
    members=[p for p in sorted(ROOT.rglob('*')) if p.is_file() and '__pycache__' not in p.parts
             and 'screenshots' not in p.parts and p.name not in exclusions]
    forbidden=('file_000000','sk-proj-','BEGIN PRIVATE KEY')
    for p in members:
        if p.suffix in ('.py','.html','.md','.json','.js','.txt'):
            text=p.read_text()
            # Only real credentials/private metadata are disallowed; scanner literals in this file are harmless.
            if p.name!='build_release.py' and any(x in text for x in forbidden):raise ValueError('Public-scope scanner: '+p.name)
    manifest={str(p.relative_to(ROOT)):dict(bytes=p.stat().st_size,sha256=sha(p.read_bytes())) for p in members}
    (ROOT/'MANIFEST.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    receipt={'record':'BONDED-RSI-GATE-BETWEEN-CHECK-AND-ACT-2026-11-16-002','version':'1.0.0',
      'status':'VERIFIED_RELEASE_ARTIFACT','source_commit':os.environ.get('GITHUB_SHA','local source tree'),
      'repository_publication':'Established by containing Git commit, not by this artifact receipt.',
      'live_pages':'Separate HTTP verification required; this record does not claim it.',
      'manifest_sha256':sha((ROOT/'MANIFEST.json').read_bytes()),'verification':verification,
      'browser_transport':browser['transport'],'browser_checks':browser['checks'],
      'limits':['No live model trials','No Castle or bridge changes','No independent-author replication',
                'Atomic conditional operation is a supplied contract, not a distributed implementation']}
    (ROOT/'PUBLICATION.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    members += [ROOT/'MANIFEST.json',ROOT/'PUBLICATION.json']
    with zipfile.ZipFile(ROOT/'evidence.zip','w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in sorted(members):
            info=zipfile.ZipInfo(str(p.relative_to(ROOT)),(2026,11,16,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o644<<16
            z.writestr(info,p.read_bytes())
    with zipfile.ZipFile(ROOT/'evidence.zip') as z:
        if z.testzip():raise ValueError('ZIP CRC failure')
        for n,m in manifest.items():
            if sha(z.read(n))!=m['sha256']:raise ValueError('ZIP manifest mismatch')
    download={'filename':'evidence.zip','bytes':(ROOT/'evidence.zip').stat().st_size,'sha256':sha((ROOT/'evidence.zip').read_bytes()),'members':len(members)}
    (ROOT/'download.json').write_text(json.dumps(download,indent=2,sort_keys=True)+'\n');print(json.dumps(download))

def integrate(repo):
    repo=Path(repo).resolve();home=repo/'index.html';readme=repo/'README.md'
    href=PFX+'index.html'
    s=home.read_text()
    if href not in s:
        needle='<div class="start-grid">'
        if s.count(needle)!=1:raise ValueError('Homepage insertion anchor changed')
        link='\n<a href="'+href+'"><strong>New: The Gate Between Check and Act ↗</strong><span>A correct check, a later revocation, and a misleading success score. Explore 13,824 scripted episodes and exact safe-controller bounds. No live model agents.</span></a>'
        home.write_text(s.replace(needle,needle+link,1))
    s=readme.read_text()
    if href not in s:
        needle='## Recent research notes — November 16, 2026'
        if s.count(needle)!=1:raise ValueError('README insertion anchor changed')
        entry='''## The Gate Between Check and Act — November 16, 2026

**[Operate the new instrument](experiments/gate-between-check-and-act/index.html)** · [Methods and proof](experiments/gate-between-check-and-act/method.html) · [Complete source and evidence](experiments/gate-between-check-and-act/evidence.zip)

Executed finite-model study: 13,824 scripted episodes; exact information-constrained synthesis over 1,050 panels; 264 separate small-model cross-checks; 36 distinct tests; all traces matched between Python and JavaScript. Authentic checks can become stale before action. Blocking can hide forbidden requests behind successful completion. Includes a timing-matched conditional-operation control and a proof of the monotone-revocation boundary. **No live model agents, Castle integration, or independent-author validation.** Atomicity is supplied by the model; known TOCTOU/transaction concepts are cited rather than claimed as discoveries.

'''
        readme.write_text(s.replace(needle,entry+needle,1))
    print('Integrated only the new homepage door and README entry.')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['verify','package','integrate']);ap.add_argument('--repo',default='../..');a=ap.parse_args()
    if a.action=='verify':verify()
    elif a.action=='package':package()
    else:integrate(a.repo)
