"""Assemble a deterministic full-data evidence ZIP after both verifiers pass."""
import hashlib,json,zipfile
from pathlib import Path
root=Path(__file__).resolve().parent
expected=(root/'expected-data-sha256.txt').read_text()
assert (root/'data/SHA256SUMS.txt').read_text()==expected, 'Scientific data changed from first local run'
for name in ['verification.json','browser-verification.json']:
 assert json.loads((root/name).read_text())['status']=='PASS',name
files=sorted(p for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts and 'screenshots' not in p.parts and p.name not in ('evidence.zip','evidence.sha256'))
with zipfile.ZipFile(root/'evidence.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for p in files:
  info=zipfile.ZipInfo(str(p.relative_to(root)),date_time=(2026,11,6,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
  z.writestr(info,p.read_bytes())
(root/'evidence.sha256').write_text(hashlib.sha256((root/'evidence.zip').read_bytes()).hexdigest()+'  evidence.zip\n')
print('Packaged',len(files),'files; event tape included; no model calls.')
