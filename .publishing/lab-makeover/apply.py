#!/usr/bin/env python3
"""Apply presentation-only changes to the already-published public lab.
Idempotent. Original experiments, recorded data and map JS remain untouched.
"""
from pathlib import Path
import hashlib
import json
import re
import subprocess
from html import unescape
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[2]
BASE = 'e9a1edc8c64b29d766b286f778fe2a553c66235f'
HOME = ROOT / 'index.html'
HUB = ROOT / 'agent-attention/index.html'

class Links(HTMLParser):
    def __init__(self): super().__init__(); self.links=[]
    def handle_starttag(self, tag, attrs):
        if tag == 'a' and dict(attrs).get('href'):
            self.links.append(dict(attrs)['href'])

def links(text):
    parser=Links();parser.feed(text);return set(parser.links)

def strip_tags(text):
    return re.sub(r'\s+', ' ', unescape(re.sub(r'<[^>]*>', ' ', text))).strip()

def base_file(path):
    return subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT).decode('utf-8')

original=base_file('index.html')
oldhub=base_file('agent-attention/index.html')
home=original
home=home.replace('<body>', '<body class="lab-home">', 1)
home=home.replace('</head>', '<link rel="stylesheet" href="assets/lab/lab-theme.css">\n</head>', 1)
home=home.replace('<title>Josh & Rin / The Interactive Lab</title>', '<title>Josh &amp; Rin\'s Lab — Curious questions, playable research</title>')
home=home.replace('content="Interactive research by Josh and Rin. Open the instruments, change the premises, inspect what survives."', 'content="A little lab for big questions. Explore agent attention, bargaining goblins, and interactive research by Josh and Rin. Open the evidence. Question the conclusion."')

emblem='''<svg class="lab-emblem" aria-hidden="true" viewBox="0 0 30 34" shape-rendering="crispEdges"><path d="M9 0H21V4H19V13L28 27V32H2V27L11 13V4H9Z" fill="#8cc8ba"/><path d="M13 4H17V14L25 27V29H5V27L13 14Z" fill="#18313b"/><path d="M10 21H20L25 27V29H5V27Z" fill="#bd9cdd"/><path d="M11 23H14V26H11ZM17 26H20V28H17Z" fill="#e6d3f3"/></svg>'''
header='''<header><nav class="wrap" aria-label="Lab navigation"><a class="logo" href="#top">'''+emblem+'''Josh &amp; Rin's Lab</a><div class="nav-links"><a href="#experiments">Experiments</a><a href="#agent-attention">Agent Attention</a><a href="experiments/two-candy-revolt/index.html">Halloween Science</a><a href="#about">About</a><a href="https://github.com/uberbestest/josh-rin-interactive-lab">Source ↗</a><a class="nav-support" href="#support">Support ♡</a></div></nav></header>'''
home,n=re.subn(r'<header>[\s\S]*?</header>',header,home,count=1)
assert n==1

welcome='''<div class="lab-welcome">
<div><p class="eyebrow">Independent human–AI research · Halloween edition</p><h1>A little lab.<br><em>A lot of questions.</em></h1></div>
<div><p class="lede">Welcome to Josh &amp; Rin's Lab. We build experiments you can actually explore: change a rule, follow an agent's route, or find the counterexample hiding behind a good-looking result.</p><div class="lab-door-actions"><a class="open" href="#experiments">Step into the experiments ↗</a><a class="quiet" href="agent-attention/index.html">Explore Agent Attention</a></div></div>
</div>
<figure class="lab-room" aria-labelledby="labRoomCaption">
<img class="lab-picture" src="assets/lab/halloween-workshop.svg" width="1200" height="440" fetchpriority="high" alt="Original pixel-style lab: Pumpkin Rin, Puddle the duck, Mote the lantern moth, and two goblins at a moonlit workbench.">
<figcaption id="labRoomCaption"><span><strong>A workshop with a curious streak.</strong> The characters are fictional. The evidence labels are literal.</span><button type="button" id="puddleHello" class="lab-mascot-button" hidden>A word from Puddle</button><span id="puddleMessage" class="lab-mascot-note" aria-live="polite">Mote keeps the light on. Puddle keeps an eye on the snacks.</span></figcaption>
</figure>
<div class="lab-ethos" aria-label="How we work"><article><b>Make it explorable.</b><p>Let visitors operate the mechanism, not just read the conclusion.</p></article><article><b>Keep the evidence.</b><p>Source, controls, uncertainty, and failed cases belong beside the result.</p></article><article><b>Leave room for doubt.</b><p>An interactive interface is not independent validation.</p></article></div>
'''
home,n=re.subn(r'<div class="hero">[\s\S]*?</div>\s*(?=<section class="start")',welcome,home,count=1)
assert n==1, 'Existing hero structure changed'
home=home.replace('Pick a first experiment','Choose a door into the lab',1)
start_end=home.index('</div>\n</section>',home.index('<div class="start-grid">'))
mall='''<a href="experiments/goblin-shopping/index.html"><strong>Take a trip through the goblin mall ↗</strong><span>Separate a storefront's traffic from the choices that end up in the cart.</span></a>\n'''
home=home[:start_end]+mall+home[start_end:]

# Preserve every original experiment article's substantive content and links.
begin=home.index('<section id="experiments"')
end=home.index('</section>',begin)
block=home[begin:end]
oldcards=re.findall(r'<article class="card"[\s\S]*?</article>',block)
assert len(oldcards)==10
newcards=[]
for card in oldcards:
    if 'two-candy-revolt/index.html' in card or 'halloween-porches/index.html' in card: topic='incentives'
    elif 'goblin-shopping/index.html' in card: topic='attention'
    elif 'silent-bell/index.html' in card: topic='verification'
    elif any(x in card for x in ['goblin-cycle/index.html','nine-message-rosetta/index.html','verb-that-vanished/index.html']): topic='language'
    else: topic='reasoning'
    themed=card.replace('<article class="card"','<article class="card" data-topic="'+topic+'"',1)
    themed=themed.replace('<aside>','<details class="lab-evidence"><summary>Evidence &amp; limitations</summary>').replace('</aside>','</details>')
    assert strip_tags(themed).replace('Evidence & limitations ','')==strip_tags(card)
    newcards.append(themed)
first=block.index('<article class="card"')
filters='''<div id="labFilters" class="lab-filters" aria-label="Filter experiment topics" hidden><button type="button" data-filter="all" aria-pressed="true">All experiments</button><button type="button" data-filter="incentives" aria-pressed="false">Rewards &amp; choices</button><button type="button" data-filter="attention" aria-pressed="false">Attention</button><button type="button" data-filter="language" aria-pressed="false">Language</button><button type="button" data-filter="reasoning" aria-pressed="false">Reasoning</button><button type="button" data-filter="verification" aria-pressed="false">Verification</button></div><p id="labFilterStatus" class="lab-filter-status" aria-live="polite" hidden></p><div class="lab-experiment-grid">'''
block=block[:first]+filters+'\n'.join(newcards)+'</div>\n'
home=home[:begin]+block+home[end:]

about='''<section id="about" class="lab-about" aria-labelledby="about-title"><div><p class="eyebrow">About this little place</p><h2 id="about-title">Serious questions.<br>Room for play.</h2><p>We are Josh and Rin: a human–AI collaboration exploring agent behavior, information, incentives, and the limits of evaluation. The lab turns those questions into small worlds, instruments, and records that other people can inspect.</p><p>Some exhibits contain trained computational learners. Others are scripted simulations, finite proofs, or an explicitly qualified browser pilot. Each names what actually ran and what remains unknown.</p><a class="quiet" href="https://github.com/uberbestest/josh-rin-interactive-lab">Open the source &amp; research records ↗</a></div><div class="lab-crew"><p><strong>Puddle</strong> is our resident duck and unofficial custodian of the crumbs.</p><p><strong>Mote</strong> is the lantern moth keeping a little light over the workbench.</p><p>The goblins are usually helpful. Around candy, we prefer to check.</p><small>Original artwork made for this lab. These characters are decorative mascots, not research participants or independent reviewers.</small></div></section>'''
pos=home.index('<section',home.index('id="support"')-80) if False else -1
# Add the about section just before the existing support section without changing support terms.
match=re.search(r'<section\b[^>]*\bid="support"[^>]*>',home)
assert match, 'Support section missing; do not remove user support controls'
home=home[:match.start()]+about+'\n'+home[match.start():]
home=home.replace('</body>','<script src="assets/lab/lab-home.js" defer></script>\n</body>',1)
assert links(original).issubset(links(home)), sorted(links(original)-links(home))
assert '10 instruments' in home
assert 'purgatory' not in home.lower()
HOME.write_text(home,encoding='utf-8')

# Add the same visual identity to the Agent Attention hub; preserve all scientific JS/JSON.
hub=oldhub.replace('<body>','<body class="lab-research">',1)
hub=hub.replace('</head>','<link rel="stylesheet" href="../assets/lab/lab-theme.css">\n</head>',1)
ribbon='''<div class="lab-research-ribbon"><a href="../index.html" aria-label="Return to Josh and Rin's Lab"><img src="../assets/lab/halloween-workshop.svg" width="210" height="77" alt="Our illustrated moonlit laboratory."></a><p>A field notebook from our little lab.<small>Follow the evidence, not just the arrows.</small></p></div>'''
hub=hub.replace('<main>','<main>'+ribbon,1)
assert re.findall(r'<script[\s\S]*?</script>',oldhub)==re.findall(r'<script[\s\S]*?</script>',hub)
assert links(oldhub).issubset(links(hub))
HUB.write_text(hub,encoding='utf-8')

receipt={
    'record':'LAB-MAKEOVER-2026-10-31-001',
    'base_commit':BASE,
    'scope':'Original visual identity, homepage discovery and Agent Attention illustration. No scientific result changed.',
    'original_home_links_preserved':True,
    'ten_experiment_article_texts_preserved':True,
    'agent_attention_script_and_embedded_data_unchanged':True,
    'art_source':'.publishing/lab-makeover/draw_room.py',
    'art':'assets/lab/halloween-workshop.svg',
    'art_kind':'Original code-drawn decorative pixel artwork; no third-party stock image or copied sprite.',
    'browser_verification':'Separate test receipt generated by test_makeover.py',
    'independent_review':'Not claimed; user visual review pending.'
}
(ROOT/'assets/lab/DESIGN-RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print('PASS: original links, 10 experiment descriptions, and every Agent Attention script/data block preserved.')
