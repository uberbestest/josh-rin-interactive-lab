"""Verify this self-contained public distribution without private parent files."""
from pathlib import Path
import hashlib,json,subprocess,sys,tempfile
ROOT=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    receipt=json.loads((ROOT/'published_result.json').read_text())
    for name,want in receipt['scientific_source_sha256'].items():
        if sha(ROOT/name)!=want:raise ValueError('Scientific source mismatch: '+name)
    tests={}
    for label,flags in [('normal',[]),('optimized',['-O'])]:
        r=subprocess.run([sys.executable,*flags,'-m','unittest','-v','test_audit'],cwd=ROOT,capture_output=True,text=True)
        if r.returncode:raise RuntimeError(r.stdout+r.stderr)
        tests[label]=r.stderr.strip().splitlines()[-1]
    matches=[]
    with tempfile.TemporaryDirectory(prefix='reset-diagnostics-') as t:
        for mode,flags in [('forward',[]),('reverse',['--reverse'])]:
            out=Path(t)/mode
            subprocess.run([sys.executable,str(ROOT/'audit.py'),'--out',str(out),*flags],check=True)
            if sorted(p.name for p in out.iterdir())!=sorted(receipt['result_sha256']):
                raise ValueError('Unexpected result file set')
            for name,want in receipt['result_sha256'].items():
                if sha(out/name)!=want:raise ValueError('Result mismatch: '+mode+'/'+name)
                matches.append(mode+'/'+name)
    print(json.dumps({'scientific_files_checked':len(receipt['scientific_source_sha256']),
                      'tests':tests,'exact_result_matches':matches,
                      'scope':'same-author engineering reproduction; no live-model test'},indent=2))
if __name__=='__main__':main()
