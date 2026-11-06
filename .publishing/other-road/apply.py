"""Add exactly two navigation entries; preserve every prior byte otherwise."""
from pathlib import Path
root=Path(__file__).resolve().parents[2]
changes=[
 ('index.html','<div class="start-grid">','\n<a href="experiments/other-road/index.html"><strong>New: The Other Road ↗</strong><span>Checkpoint friction, a permitted detour, and a quietly smaller task. Executed synthetic learning study; no language-model participants.</span></a>'),
 ('README.md','[Browse the gallery](index.html)','\n\n## The Other Road — November 6, 2026\n\n**[Explore the authorized fork](experiments/other-road/index.html)** · [Methods](experiments/other-road/method.html) · [Complete evidence](experiments/other-road/evidence.zip)\n\nExecuted synthetic learning study: 1,536 seeded bandit runs, 4,608,000 preserved training decisions, and 38,178 exact parameter cells. Expected checkpoint cost produces complete detours under one scoring rule and undisclosed undercompletion under another. Auditing without an alternate can improve disclosure without restoring completion. **Zero language-model participants; not an explanation of Astra; independent review pending.**\n')]
for filename,anchor,addition in changes:
 p=root/filename
 if not p.exists():raise SystemExit(f'Missing existing gallery file: {filename}')
 old=p.read_text(encoding='utf-8')
 if 'experiments/other-road/index.html' in old:
  print(f'Already linked: {filename}');continue
 assert old.count(anchor)==1, f'Gallery anchor changed: {filename}'
 new=old.replace(anchor,anchor+addition,1)
 assert new.replace(addition,'',1)==old, 'Non-additive change'
 p.write_text(new,encoding='utf-8')
 print(f'One additive navigation entry: {filename}')
