"""Run real source mutations against unit tests, in temporary directories."""
import json, shutil, subprocess, sys, tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
MUTANTS={
 'count_copies_as_roots':('receipt = independent_posterior(sum(bits), len(bits), marginal)','receipt = head'),
 'deduplicate_headcount':('head = independent_posterior(sum(b*w for b, w in zip(bits, copies)), sum(copies), marginal)','head = independent_posterior(sum(bits), len(bits), marginal)'),
 'ignore_shared_fault':('aware = shared + (1-2*shared) * conditional','aware = conditional'),
 'wrong_local_calibration':('return (marginal-shared) / (1-2*shared)','return marginal'),
 'wrong_truth_signal':('truth ^ fault ^ err','truth ^ err'),
 'exclude_boundary_buy':('if p >= F(9, 10):','if p > F(9, 10):'),
 'cheap_wrong_decision':('else -9','else -1'),
 'drop_truth_prior':('weight = F(1, 2) * fault_mass','weight = F(1) * fault_mass'),
}
source=(HERE/'engine.py').read_text()
results=[]
for name,(old,new) in MUTANTS.items():
 if old not in source: raise RuntimeError('Mutation target missing: '+name)
 with tempfile.TemporaryDirectory() as td:
  p=Path(td); (p/'engine.py').write_text(source.replace(old,new,1)); shutil.copy2(HERE/'test_engine.py',p)
  run=subprocess.run([sys.executable,'-m','unittest','-q','test_engine'],cwd=p,capture_output=True,text=True)
  killed=run.returncode!=0 and ('FAIL:' in run.stderr or 'ERROR:' in run.stderr)
  results.append({'mutant':name,'detected':killed,'returncode':run.returncode})
  if not killed: raise AssertionError('Surviving mutant: '+name)
print(json.dumps({'status':'PASS','mutants_detected':len(results),'mutants':results},indent=2))
