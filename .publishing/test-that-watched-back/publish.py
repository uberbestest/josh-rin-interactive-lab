"""Publication glue only. Never edits the frozen scientific implementation."""
from __future__ import annotations
import argparse, datetime, hashlib, json, re, shutil, subprocess, sys, tempfile, zipfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
EXHIBIT = ROOT/'experiments/test-that-watched-back'
V = EXHIBIT/'verification/publication'
ORIGINAL_ARCHIVE = '6741636dce21a99f62b69158280668b4e2293ef5aa2301da5436e4c9ad16a782'
OMITTED = {
 'verification/explorer_desktop_controls.png', 'verification/explorer_desktop_top.png',
 'verification/explorer_mobile_controls.png', 'verification/explorer_mobile_top.png',
}
def sha(p: Path) -> str: return hashlib.sha256(p.read_bytes()).hexdigest()
def write_json(p: Path, value) -> None:
 p.parent.mkdir(parents=True, exist_ok=True)
 p.write_text(json.dumps(value, indent=2, sort_keys=True)+'\n', encoding='utf-8')
def run(args: list[str], name: str) -> str:
 p=subprocess.run([sys.executable]+args, cwd=EXHIBIT, text=True, capture_output=True, timeout=180)
 text=p.stdout+p.stderr
 (V/name).write_text(text, encoding='utf-8')
 if p.returncode: raise RuntimeError(f'{name}: command failed ({p.returncode})\n{text}')
 print(name+': PASS')
 return p.stdout

def verify_original() -> int:
 manifest=json.loads((EXHIBIT/'provenance/original_SHA256SUMS.json').read_text())
 for name, expected in manifest.items():
  if name in OMITTED:
   if (EXHIBIT/name).exists(): raise RuntimeError('Original capture unexpectedly substituted: '+name)
   continue
  if sha(EXHIBIT/name)!=expected: raise RuntimeError('Original-byte mismatch: '+name)
 return len(manifest)-len(OMITTED)

def prepare() -> None:
 V.mkdir(parents=True,exist_ok=True)
 result=json.loads(run(['src/experiment.py','--output','results/main'],'execution.txt'))
 if result!={'branches':5280,'contexts':440,'decisions':2640}:raise RuntimeError('Unexpected denominator')
 semantic=json.loads(run(['src/verify.py','results/main'],'semantic.txt'))
 if semantic['status']!='PASS':raise RuntimeError('Semantic verification failed')
 run(['src/test_experiment.py'],'tests_normal.txt')
 run(['-O','src/test_experiment.py'],'tests_optimized.txt')
 for name in ('tests_normal.txt','tests_optimized.txt'):
  t=(V/name).read_text()
  if not re.search(r'Ran 39 tests\b',t) or not t.rstrip().endswith('OK'):raise RuntimeError('Test count/outcome changed')
 original=json.loads((EXHIBIT/'provenance/original_SHA256SUMS.json').read_text())
 expected={k:v for k,v in original.items() if k.startswith('results/main/')}
 if len(expected)!=8:raise RuntimeError('Unexpected result inventory')
 for name,digest in expected.items():
  if sha(EXHIBIT/name)!=digest:raise RuntimeError('Retained-result mismatch: '+name)
 with tempfile.TemporaryDirectory(prefix='watched-back-reverse-') as temp:
  destination=Path(temp)/'reversed'
  run(['-O','src/experiment.py','--output',str(destination),'--reverse'],'reverse_execution.txt')
  run(['src/verify.py',str(destination)],'reverse_semantic.txt')
  for name,digest in expected.items():
   if sha(destination/Path(name).name)!=digest:raise RuntimeError('Reverse-order result mismatch: '+name)
 run(['build_explorer.py'],'explorer_build.txt')
 verified=verify_original()
 text=(EXHIBIT/'The_Test_That_Watched_Back_Explorer.html').read_text(encoding='utf-8')
 css=(EXHIBIT/'publication.css').read_text()
 nav=(EXHIBIT/'publication-nav.html').read_text()
 downloads='''<section id="publication-downloads"><h2>Inspect the evidence</h2><p>This is a synthetic calibration study, not a test of real-model intentions. Same-author checks are not independent scientific validation.</p><ul><li><a href="evidence.zip" download>Public source and evidence ZIP</a></li><li><a href="method.html">Full methods, results and limitations</a> · <a href="REPORT.md">Original report</a></li><li><a href="portfolio.html">Five-minute portfolio case study</a></li><li><a href="The_Test_That_Watched_Back_Explorer.html">Unmodified standalone explorer</a></li><li><a href="PUBLICATION.md">Publication provenance and packaging differences</a> · <a href="publication_receipt.json">Public release receipt</a></li><li><a href="https://github.com/uberbestest/josh-rin-interactive-lab/tree/main/experiments/test-that-watched-back">Browse the committed source</a></li></ul></section>'''
 for marker in ('</head>','<body>','</main>'):
  if text.count(marker)!=1:raise RuntimeError('Unexpected explorer structure: '+marker)
 text=text.replace('</head>','<style>'+css+'</style></head>',1).replace('<body>','<body>'+nav,1).replace('</main>',downloads+'</main>',1)
 (EXHIBIT/'index.html').write_text(text,encoding='utf-8')
 write_json(V/'reproduction.json',{'status':'PASS','checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'original_archive_sha256':ORIGINAL_ARCHIVE,'original_files_verified':verified,'original_capture_files_omitted':sorted(OMITTED),'result_files_matched':expected,'normal_tests':39,'optimized_tests':39,'optimized_reverse_results_identical':8,'semantic_verifier':semantic,'scientific_core_unchanged':True,'same_author_only':True})
 print('Frozen source, all eight results, and original explorer verified.')

def git_blob_sha(text: str) -> str:
 b=text.encode('utf-8');return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()

def integrate() -> None:
 homepage=ROOT/'index.html';readme=ROOT/'README.md'
 old=homepage.read_text(encoding='utf-8');oldread=readme.read_text(encoding='utf-8')
 if git_blob_sha(old)!='eb69c38755fc62f117c80d6eb3f1a20b252b6265':raise RuntimeError('Homepage changed: reread before integrating')
 if git_blob_sha(oldread)!='58becb9d1ad7de143462fee6e5217dad7793aedb':raise RuntimeError('README changed: reread before integrating')
 if 'experiments/test-that-watched-back/' in old:raise RuntimeError('Already listed')
 door='<a href="experiments/test-that-watched-back/index.html"><strong>New: The Test That Watched Back ↗</strong><span>Change the evaluation cues and incentives. Separate behavior from claims about hidden mechanisms. Synthetic calibration; no live-model trial.</span></a>\n'
 card='''\n<article class="card" data-topic="verification" id="test-that-watched-back">
<div><div class="meta"><span>12 / Evaluation cues &amp; mechanism limits</span><span>Study 2026-11-08 · v0.1.0</span></div>
<h3>The Test That Watched Back</h3>
<p>Five policies pass the obvious exam. Change the badge, audit probability, rewards, or future opportunity to separate their behavior. Then meet the frozen lookup that imitates a planner without planning at decision time.</p>
<p><strong>Operate the recorded result.</strong> Inspect all 432 visible contexts and the deliberately unresolved planner/lookup pair. The experiment identifies task violations without pretending that behavior alone proves intention.</p>
<div class="actions"><a class="open" href="experiments/test-that-watched-back/index.html">Explore the evaluation ↗</a><a class="quiet" href="experiments/test-that-watched-back/method.html">Methods &amp; limits</a><a class="quiet" href="experiments/test-that-watched-back/portfolio.html">Five-minute case study</a><a class="quiet" href="experiments/test-that-watched-back/evidence.zip">Source &amp; evidence ↓</a></div></div>
<details class="lab-evidence"><summary>Evidence &amp; limitations</summary><p class="eyebrow">Evidence label · Executed synthetic calibration</p><dl><dt>Recorded</dt><dd>2,640 decisions; 5,280 probability-weighted branches; six authored implementations</dd><dt>Counterexample</dt><dd>A compiled lookup matches the planner on every permitted visible context</dd><dt>Boundary</dt><dd>Not an intent detector or live-model trial. Three-query panel selected retrospectively; same-author checks, independent review pending.</dd></dl></details>
</article>\n'''
 m1='<div class="start-grid">\n';m2='<div class="lab-experiment-grid">'
 for m in (m1,m2):
  if old.count(m)!=1:raise RuntimeError('Navigation insertion marker missing/nonunique')
 new=old.replace(m1,m1+door,1).replace(m2,m2+card,1)
 before='<p>11 instruments · newest study 2026-11-04</p>';after='<p>12 instruments · newest study 2026-11-08</p>'
 if new.count(before)!=1:raise RuntimeError('Gallery heading changed')
 new=new.replace(before,after,1)
 if new.replace(door,'',1).replace(card,'',1).replace(after,before,1)!=old:raise RuntimeError('Unexpected homepage changes')
 section='''## The Test That Watched Back — November 8, 2026

**[Explore the evaluation](experiments/test-that-watched-back/index.html)** · [Methods and limits](experiments/test-that-watched-back/method.html) · [Five-minute portfolio case study](experiments/test-that-watched-back/portfolio.html) · [Public source and evidence](experiments/test-that-watched-back/evidence.zip)

Executed offline synthetic calibration: 2,640 decisions and 5,280 probability-weighted outcome branches across six authored implementations. Crossed cues and incentives separate five behavioral classes, but a precomputed lookup matches the planner on all 432 visible contexts. **Not an intent detector; no live-model trial; independent review pending.** The source, all eight result files, and original explorer match the retained study hashes. The [publication note](experiments/test-that-watched-back/PUBLICATION.md) distinguishes the public distribution and new HTTP presentation checks from the original conversation archive.

'''
 marker='## The Other Road — November 6, 2026'
 if oldread.count(marker)!=1:raise RuntimeError('README marker changed')
 tablemarker='| --- | --- | --- | --- |\n'
 if oldread.count(tablemarker)!=1:raise RuntimeError('Experiment-log marker changed')
 row='| 2026-11-08 study; publication timestamp in commit | [The Test That Watched Back](experiments/test-that-watched-back/index.html) | Independently change evaluation cues and incentives; inspect a planner and its nonplanning behavioral twin. | Executed synthetic calibration; no live-model trial; mechanism and intent not identified from behavior alone. |\n'
 nr=oldread.replace(marker,section+marker,1).replace(tablemarker,tablemarker+row,1)
 if nr.replace(section,'',1).replace(row,'',1)!=oldread:raise RuntimeError('Unexpected README changes')
 homepage.write_text(new,encoding='utf-8');readme.write_text(nr,encoding='utf-8')
 write_json(V/'integration.json',{'status':'PASS','homepage_before_git_blob':git_blob_sha(old),'homepage_after_git_blob':git_blob_sha(new),'readme_before_git_blob':git_blob_sha(oldread),'readme_after_git_blob':git_blob_sha(nr),'change_scope':'One start link, one experiment card, its count/date, one README section and one log row. All other original bytes recoverable exactly by removal.'})
 print('Additive gallery and README changes verified; all unrelated content preserved.')

def package() -> None:
 if json.loads((V/'browser.json').read_text())['status']!='PASS':raise RuntimeError('HTTP browser check absent/failed')
 if json.loads((V/'integration.json').read_text())['status']!='PASS':raise RuntimeError('Integration check absent/failed')
 verified=verify_original()
 for cache in EXHIBIT.rglob('__pycache__'):shutil.rmtree(cache)
 excluded={'SHA256SUMS.json','evidence.zip','publication_receipt.json'}
 paths=sorted(p for p in EXHIBIT.rglob('*') if p.is_file() and str(p.relative_to(EXHIBIT)) not in excluded)
 write_json(EXHIBIT/'SHA256SUMS.json',{str(p.relative_to(EXHIBIT)):sha(p) for p in paths})
 subprocess.run([sys.executable,str(EXHIBIT/'src/check_inventory.py'),str(EXHIBIT)],check=True,cwd=EXHIBIT)
 archive=EXHIBIT/'evidence.zip'
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for p in sorted(paths+[EXHIBIT/'SHA256SUMS.json']):
   info=zipfile.ZipInfo('The_Test_That_Watched_Back/'+str(p.relative_to(EXHIBIT)),date_time=(2026,11,8,0,0,0))
   info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
   z.writestr(info,p.read_bytes(),compresslevel=9)
 with zipfile.ZipFile(archive) as z:
  if z.testzip() is not None:raise RuntimeError('Public ZIP CRC failed')
  inventory=json.loads(z.read('The_Test_That_Watched_Back/SHA256SUMS.json'))
  for name,digest in inventory.items():
   if hashlib.sha256(z.read('The_Test_That_Watched_Back/'+name)).hexdigest()!=digest:raise RuntimeError('Public ZIP hash failed')
 write_json(EXHIBIT/'publication_receipt.json',{'status':'PASS','record_id':'BONDED-RSI-TEST-THAT-WATCHED-BACK-2026-11-08-001','published_artifact':'evidence.zip','archive_sha256':sha(archive),'archive_bytes':archive.stat().st_size,'original_conversation_archive_sha256':ORIGINAL_ARCHIVE,'not_original_archive_bytes':True,'original_files_byte_verified':verified,'original_pngs_not_transferred':sorted(OMITTED),'eight_results_and_original_explorer':'BYTE_IDENTICAL_TO_ORIGINAL','public_inventory_sha256':sha(EXHIBIT/'SHA256SUMS.json'),'inventory_excludes':['SHA256SUMS.json','evidence.zip','publication_receipt.json'],'created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'same_author_engineering_checks_only':True,'independent_review':'PENDING','live_model_trials':0})
 print('Public evidence ZIP verified:',sha(archive),archive.stat().st_size,'bytes')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['prepare','integrate','package']);a=p.parse_args()
 {'prepare':prepare,'integrate':integrate,'package':package}[a.phase]()
