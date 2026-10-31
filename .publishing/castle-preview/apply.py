from pathlib import Path
import hashlib
ROOT=Path(__file__).resolve().parents[2]
p=ROOT/'index.html'
b=p.read_bytes()
blob=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
assert blob=='a9abca6e60aa2d89d022daf27e2653e520db0de3', 'Homepage changed: stop rather than overwrite another update'
s=b.decode()
assert 'id="major-projects"' not in s
s=s.replace('<a href="#agent-attention">Agent Attention</a>','<a href="#agent-attention">Agent Attention</a><a href="#major-projects">Projects</a>',1)
s=s.replace('<div class="start-grid">','<div class="start-grid">\n<a href="projects/rle-castle/index.html"><strong>In development: RLE Castle — The Faire ↗</strong><span>A first look at the adventure, the local footrace playtest, and the research questions underneath.</span></a>',1)
feature='<section id="major-projects" aria-labelledby="major-projects-title"><div class="section-head"><h2 id="major-projects-title">Major projects</h2><p>In development · separate from completed instruments</p></div><article class="castle-project"><div><p class="eyebrow">Development preview / RLE Castle</p><h3>The Faire</h3><p>A fair full of games, rumors and choices on the way to the castle. An adventure for people to enjoy, and a proposed environment for studying how agents explore, follow evidence and respond to incentives.</p><p><strong>Local footrace playtest reported October 31.</strong> View a shared Faire-window capture and the development scope. This is a project preview, not a public playable build or a validated agent benchmark.</p><div class="actions"><a class="open" href="projects/rle-castle/index.html">Preview the Castle project ↗</a><a class="quiet" href="projects/rle-castle/index.html#evidence">What is demonstrated?</a></div></div><figure><img src="projects/rle-castle/assets/faire-doorway.webp" width="575" height="200" loading="lazy" alt="A cropped development capture of the Faire\'s lamp-lit lab doorway and Puddle\'s booth."><figcaption>Shared development capture · cropped to exclude desktop overlays.</figcaption></figure></article></section>\n'
css='\n/* Castle development preview is not an experiment card. */\n.castle-project{display:grid;grid-template-columns:1.08fr 1fr;gap:32px;align-items:center;border:1px solid #5c655e;border-radius:13px;padding:clamp(23px,4vw,39px);background:linear-gradient(125deg,#243331,#182632)}.castle-project h3{font:500 clamp(2rem,4vw,3rem)/1.1 Georgia,serif;margin:14px 0}.castle-project p{color:var(--muted)}.castle-project figure{margin:0;min-width:0}.castle-project img{display:block;width:100%;height:auto;border-radius:7px;border:1px solid var(--line)}.castle-project figcaption{font-size:.79rem;color:var(--muted);margin-top:12px}.castle-project .actions{gap:12px}@media(max-width:800px){.castle-project{grid-template-columns:1fr;gap:22px}}\n'
s=s.replace('<section id="agent-attention"',feature+'<section id="agent-attention"',1)
s=s.replace('</style>',css+'</style>',1)
assert s.count('class="card"')==b.decode().count('class="card"')==10
p.write_text(s)
print('PASS: homepage navigation, shortcut and Major projects feature; 10 instruments unchanged')
