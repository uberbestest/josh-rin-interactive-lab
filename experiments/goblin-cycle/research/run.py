"""Run deterministic scenario sweep and emit public evidence JSON (stdlib only)."""
import json,hashlib,sys,collections
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from core import make_network,record

MODES=['single','triangle','star','coordinated','double','clean']
SEEDS=range(1,257)
VOCABS=(8,16,32)
rows=[record(make_network(seed,vocab,mode)) for mode in MODES for vocab in VOCABS for seed in SEEDS]
summary={}
for mode in MODES:
    subset=[r for r in rows if r['mode']==mode]
    stat=collections.Counter(x['status'] for x in subset)
    summary[mode]={
        'cases':len(subset),
        'status_counts':dict(sorted(stat.items())),
        'wrong_links_min':min(x['oracle_wrong_links'] for x in subset),
        'wrong_links_max':max(x['oracle_wrong_links'] for x in subset),
        'repaired_oracle_exact':sum(x['exactly_repaired'] for x in subset),
        'path_vote_matches_cases':sum(x['path_vote_matches'] for x in subset),
    }
meta={
 'record_id':'GOBLIN-CYCLE-2026-10-26-001',
 'date':'2026-10-26',
 'title':'The Goblins Found a Liar Without Knowing Any Words',
 'status':'OFFLINE_SYNTHETIC_EXPLORATION_NOT_EXTERNAL_VALIDATION',
 'source':'research/core.py + research/run.py',
 'protocol':{'seed_start':1,'seed_end_inclusive':256,'vocabularies':list(VOCABS),'scenarios':MODES,'all_cases':len(rows)},
 'scenario_definitions':{
    'single':'K4, one link output transposition',
    'triangle':'K3, one link output transposition',
    'star':'4 nodes, star topology, one link output transposition',
    'coordinated':'K4, reassign symbols at one node on all three adjacent channels',
    'double':'K4, two independently swapped links',
    'clean':'K4, no edited links'},
 'summary':summary,
 'not_validated':['external data','learned neural languages','arbitrary protocols','semantics/meaning','colluding adversaries beyond these planted scenarios','live deployment browser behavior'],
 'citation':'Lerman & Shi (2022), Robust Group Synchronization via Cycle-Edge Message Passing, Foundations of Computational Mathematics. doi:10.1007/s10208-021-09532-w',
}
# Store all raw records for audit, source SHA-256 (not a scientific certificate).
root=Path(__file__).resolve().parents[1]
(rroot:=root/'results').mkdir(exist_ok=True)
rows_bytes=(json.dumps(rows,ensure_ascii=False,indent=2,sort_keys=True)+'\n').encode('utf-8')
(rroot/'sweep-records.json').write_bytes(rows_bytes)
meta['rows_sha256']=hashlib.sha256(rows_bytes).hexdigest()
for relative in ['research/core.py','research/run.py']:
    meta.setdefault('source_sha256',{})[relative]=hashlib.sha256((root/relative).read_bytes()).hexdigest()
meta_bytes=(json.dumps(meta,ensure_ascii=False,indent=2,sort_keys=True)+'\n').encode()
(rroot/'run-receipt.json').write_bytes(meta_bytes)
print(json.dumps({'record_id':meta['record_id'],'all_cases':len(rows),'summary':summary,'rows_sha256':meta['rows_sha256'],'source_sha256':meta['source_sha256']},indent=2))
