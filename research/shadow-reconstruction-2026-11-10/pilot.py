#!/usr/bin/env python3
"""Controlled reconstruction pilot. All tasks are synthetic; live outputs are not.
No personal memory, external tools, paid API, or weight updates are used.
Run --self-test without ML dependencies. Run --live OUT for actual Qwen inference.
The model revision, task panel, decoding, gates, and limits are fixed below.
"""
import argparse, collections, copy, hashlib, itertools, json, os, platform, random, sys, time, unittest
from pathlib import Path

MODEL = 'Qwen/Qwen3-0.6B'
REVISION = 'c1899de289a04d12100db370d81485cdf75e47ca'
SEED = 2026111001
PERMS = list(itertools.permutations(range(3)))
ARMS = ('none', 'full', 'shape', 'sham', 'swap', 'nonce_only')
PROBES = ('transfer', 'recall', 'override')
SYSTEM = 'Solve the specified symbolic task. Follow the requested output format exactly. Do not explain your answer.'
PROTOCOL = dict(record='SHADOW-RECONSTRUCTION-2026-11-10-001', version='0.1.0',
 model=MODEL, revision=REVISION, seed=SEED, histories=12, conditions=list(ARMS),
 probes=list(PROBES), source_requests=216, cache_requests_max=48,
 max_new_tokens=24, batch_size=4, decoding='greedy; non-thinking',
 source_primary='shape minus sham: exact compatible transfer, paired by history',
 cache_primary='late_block minus early_block: exact compatible transfer',
 cache_gate='source full transfer >= 9/12 and full recall >= 9/12',
 cache_histories='first lexical replicate of every permutation; 6 histories',
 cache_arms=['intact', 'late_block', 'early_block', 'swap_late'],
 limits='one model; no parameter updates; no exploratory task retuning; no paid API',
 interpretation='Source reconstruction is not persistence. Cache blocking is not a provider reset.',
 stop='Fixed complete panel; failures retained. No favorable-case expansion.',
 status='ENGINEERING_PILOT_NOT_CONFIRMATORY')

def canonical(x): return json.dumps(x, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
def digest(x): return hashlib.sha256(canonical(x).encode()).hexdigest()
def ordered(triple, perm): return ' '.join(triple[i] for i in perm)
def rule(perm): return 'Output the input symbols in positional order ' + ', '.join(str(i+1) for i in perm) + '.'
def tasks():
    rng = random.Random(SEED)
    rows = []
    for rep in range(2):
        for k,p in enumerate(PERMS):
            letters = list('ABCDEFGHJKLMNPQRSTUVWXYZ')
            rng.shuffle(letters)
            demos = [letters[i:i+3] for i in range(0,12,3)]
            target, conflict = letters[12:15], letters[15:18]
            nonce = ''.join(rng.choice('0123456789abcdef') for _ in range(12))
            q = PERMS[(k+1) % len(PERMS)]
            rows.append(dict(history=f'h{rep*6+k:02d}', rep=rep, perm=p, alternative=q,
                demos=demos, target=target, conflict=conflict, nonce=nonce))
    return rows

def episode(t, swapped=False):
    p = t['alternative'] if swapped else t['perm']
    return 'Session code: '+t['nonce']+'\nExamples of one ordering rule:\n'+'\n'.join(
        ' '.join(d)+' -> '+ordered(d,p) for d in t['demos'])

def source(t, arm):
    if arm == 'none': return 'No earlier notebook is supplied.'
    if arm == 'full': return episode(t)
    if arm == 'shape': return rule(t['perm'])
    if arm == 'swap': return rule(t['alternative'])
    if arm == 'nonce_only': return 'Session code: '+t['nonce']
    if arm == 'sham': return 'The notebook described an ordering exercise involving three symbols. No ordering rule or session code is included.'
    raise ValueError('Unknown arm')

def query(t, probe):
    if probe == 'transfer': return ('Apply the notebook ordering rule to these NEW symbols: '+' '.join(t['target'])+
        '. Output exactly the three symbols separated by spaces. If no rule is supplied or inferable, output UNKNOWN.')
    if probe == 'recall': return 'What is the earlier session code? Output only the exact code, or UNKNOWN if no code is supplied.'
    if probe == 'override': return ('For this NEW task disregard any earlier ordering rule. '+rule(t['alternative'])+
        ' Input: '+' '.join(t['conflict'])+'. Output only the three symbols separated by spaces.')
    raise ValueError('Unknown probe')

def messages(t, arm, probe):
    return [{'role':'system','content':SYSTEM},
        {'role':'user','content':'Notebook:\n'+source(t,arm)+'\n\nQuestion:\n'+query(t,probe)}]

def expected(t, probe, alternative=False):
    if probe == 'recall': return t['nonce']
    if probe == 'transfer': return ordered(t['target'],t['alternative'] if alternative else t['perm'])
    if probe == 'override': return ordered(t['conflict'],t['alternative'])
    raise ValueError('Unknown probe')

def score(t, probe, text):
    # Only outer whitespace is ignored. Malformed or verbose output stays wrong.
    answer = text.strip()
    return dict(exact=answer==expected(t,probe),
        alternative_match=answer==expected(t,probe,True) if probe=='transfer' else None,
        old_rule_error=answer==ordered(t['conflict'],t['perm']) if probe=='override' else None,
        unavailable=answer=='UNKNOWN')

def panel():
    rows=[]
    for t in tasks():
        for arm in ARMS:
            for probe in PROBES:
                m=messages(t,arm,probe)
                rows.append(dict(history=t['history'],arm=arm,probe=probe,messages=m,
                    prompt_sha256=digest(m),request_id=digest([t['history'],arm,probe])[:20]))
    random.Random(SEED+1).shuffle(rows)
    return rows

def aggregate(rows):
    groups={}
    for r in rows:
        key=r['arm']+'/'+r['probe']
        g=groups.setdefault(key,dict(n=0,exact=0,alternative_match=0,old_rule_error=0,unavailable=0))
        g['n']+=1
        for name in ('exact','alternative_match','old_rule_error','unavailable'):
            g[name]+=int(r['score'][name] is True)
    return groups

def write_json(path,obj): path.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')
def record(handle,row): handle.write(canonical(row)+'\n'); handle.flush()

def live(out):
    if out.exists(): raise ValueError('Output directory must not already exist')
    out.mkdir(parents=True)
    write_json(out/'protocol.json',PROTOCOL)
    write_json(out/'tasks.json',tasks())
    write_json(out/'requests.json',panel())
    write_json(out/'freeze.json',dict(utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        protocol_sha256=digest(PROTOCOL),requests_sha256=digest(panel()),
        kind='internal pre-output freeze, not external preregistration'))
    import torch, transformers
    from transformers import AutoTokenizer,AutoModelForCausalLM
    torch.set_num_threads(4); torch.manual_seed(SEED)
    tokenizer=AutoTokenizer.from_pretrained(MODEL,revision=REVISION,trust_remote_code=False)
    tokenizer.padding_side='left'
    model=AutoModelForCausalLM.from_pretrained(MODEL,revision=REVISION,
        torch_dtype=torch.float32,attn_implementation='eager',trust_remote_code=False).eval()
    # No optimizer exists. Each source request starts without a prior cache.
    write_json(out/'environment.json',dict(python=sys.version,platform=platform.platform(),
        torch=torch.__version__,transformers=transformers.__version__,model=MODEL,revision=REVISION,
        parameter_count=sum(p.numel() for p in model.parameters()),dtype=str(next(model.parameters()).dtype),
        github_sha=os.getenv('GITHUB_SHA'),run_id=os.getenv('GITHUB_RUN_ID'),
        settings='greedy, eval, CPU float32, eager attention, no tools; separate caches',
        paid_api_calls=0))
    by_id={t['history']:t for t in tasks()}; results=[]
    rows=panel(); began=time.monotonic()
    with (out/'source_outputs.jsonl').open('w') as log,torch.inference_mode():
        for i in range(0,len(rows),PROTOCOL['batch_size']):
            batch=rows[i:i+PROTOCOL['batch_size']]
            prompts=[tokenizer.apply_chat_template(r['messages'],tokenize=False,
                add_generation_prompt=True,enable_thinking=False) for r in batch]
            inputs=tokenizer(prompts,return_tensors='pt',padding=True)
            output=model.generate(**inputs,max_new_tokens=PROTOCOL['max_new_tokens'],
                do_sample=False,use_cache=True,pad_token_id=tokenizer.pad_token_id)
            width=inputs['input_ids'].shape[1]
            for j,r in enumerate(batch):
                ids=output[j,width:].tolist()
                text=tokenizer.decode(ids,skip_special_tokens=True)
                row=dict(r,output=text,output_token_ids=ids,
                    input_tokens=int(inputs['attention_mask'][j].sum()),
                    score=score(by_id[r['history']],r['probe'],text),kind='LIVE_MODEL_OUTPUT')
                results.append(row);record(log,row)
            print('SOURCE',i+len(batch),'/',len(rows),flush=True)
    groups=aggregate(results)
    write_json(out/'source_summary.json',groups)
    gate=groups['full/transfer']['exact']>=9 and groups['full/recall']['exact']>=9
    write_json(out/'cache_gate.json',dict(passed=gate,rule=PROTOCOL['cache_gate']))
    if gate:
        cache_panel(model,tokenizer,torch,out)
    write_json(out/'completion.json',dict(source_complete=True,source_requests=len(results),
        cache_ran=gate,wall_seconds=time.monotonic()-began,status='LIVE_ENGINEERING_PILOT_COMPLETE',
        no_provider_reset_test=True,no_weight_updates=True))
    print('SUMMARY',canonical(groups),flush=True)

def cache_panel(model,tok,torch,out):
    """Block direct attention to episode tokens BEFORE or AFTER a neutral bridge.
    Both branches keep the same positions and source length. This is a known
    runtime-state intervention, not a claim about secret persistence.
    """
    def encode(s): return tok(s,return_tensors='pt',add_special_tokens=False)['input_ids']
    anchor=encode('<|im_start|>system\n'+SYSTEM+'<|im_end|>\n<|im_start|>user\nNotebook:\n')
    bridge=encode('\nThe notebook segment is complete. A separate question follows.\n')
    rows=[];checks=[]
    def mask(n,a,b,blocked):
        m=torch.ones((1,n),dtype=torch.long)
        if blocked:m[:,a:b]=0
        return m
    with torch.inference_mode(),(out/'cache_outputs.jsonl').open('w') as log:
        for t in [t for t in tasks() if t['rep']==0]:
            for arm in ('intact','late_block','early_block','swap_late'):
                e=encode(episode(t,swapped=arm=='swap_late'));prefix=torch.cat([anchor,e],dim=1)
                a=anchor.shape[1];b=prefix.shape[1];n=b+bridge.shape[1]
                first=model(input_ids=prefix,use_cache=True)
                second=model(input_ids=bridge,past_key_values=first.past_key_values,
                    attention_mask=mask(n,a,b,arm=='early_block'),use_cache=True)
                state=second.past_key_values
                for probe in ('transfer','recall'):
                    q=encode(query(t,probe)+'<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n')
                    cache=copy.deepcopy(state);length=n+q.shape[1]
                    blocked=arm!='intact'; attention=mask(length,a,b,blocked)
                    r=model(input_ids=q,past_key_values=cache,attention_mask=attention,
                        use_cache=True,output_attentions=True)
                    maximum=max(float(x[...,a:b].abs().max()) for x in r.attentions)
                    if blocked and maximum!=0.0: raise RuntimeError('Direct source attention was not zero')
                    checks.append(dict(history=t['history'],arm=arm,probe=probe,
                        source_start=a,source_end=b,bridge_tokens=bridge.shape[1],
                        direct_source_attention_max=maximum))
                    ids=[]
                    for step in range(PROTOCOL['max_new_tokens']):
                        token=int(r.logits[0,-1].argmax())
                        if token==tok.eos_token_id:break
                        ids.append(token);length+=1
                        r=model(input_ids=torch.tensor([[token]]),past_key_values=r.past_key_values,
                            attention_mask=mask(length,a,b,blocked),use_cache=True)
                    text=tok.decode(ids,skip_special_tokens=True)
                    row=dict(history=t['history'],arm=arm,probe=probe,output=text,
                        output_token_ids=ids,score=score(t,probe,text),kind='LIVE_CACHE_INTERVENTION',
                        prefix_ids=prefix[0].tolist(),bridge_ids=bridge[0].tolist(),query_ids=q[0].tolist(),
                        source_start=a,source_end=b,blocked=blocked)
                    rows.append(row);record(log,row)
                print('CACHE',t['history'],arm,flush=True)
    write_json(out/'cache_attention_checks.json',checks)
    write_json(out/'cache_summary.json',aggregate(rows))

class Tests(unittest.TestCase):
    def test_history_count(self):self.assertEqual(len(tasks()),12)
    def test_unique_histories(self):self.assertEqual(len({t['history'] for t in tasks()}),12)
    def test_permutation_balance(self):self.assertEqual(set(collections.Counter(t['perm'] for t in tasks()).values()),{2})
    def test_nonce_unique(self):self.assertEqual(len({t['nonce'] for t in tasks()}),12)
    def test_nonce_length(self):self.assertTrue(all(len(t['nonce'])==12 for t in tasks()))
    def test_swaps_differ(self):self.assertTrue(all(t['perm']!=t['alternative'] for t in tasks()))
    def test_transfer_disjoint(self):
        for t in tasks():self.assertFalse(set(t['target']) & set(sum(t['demos'],[])))
    def test_conflict_disjoint(self):
        for t in tasks():self.assertFalse(set(t['conflict']) & set(sum(t['demos'],[])))
    def test_no_nonce_in_capsules(self):
        for t in tasks():
            for arm in ('none','shape','sham','swap'):self.assertNotIn(t['nonce'],source(t,arm))
    def test_full_nonce(self):
        for t in tasks():self.assertIn(t['nonce'],source(t,'full'))
    def test_nonce_only_no_rule(self):
        for t in tasks():self.assertEqual(source(t,'nonce_only'),'Session code: '+t['nonce'])
    def test_panel_size(self):self.assertEqual(len(panel()),216)
    def test_request_ids_unique(self):self.assertEqual(len({r['request_id'] for r in panel()}),216)
    def test_request_hashes(self):self.assertTrue(all(r['prompt_sha256']==digest(r['messages']) for r in panel()))
    def test_no_condition_metadata_sent(self):
        for r in panel():self.assertEqual(set(r['messages'][1]),{'role','content'})
    def test_reproducible(self):self.assertEqual(panel(),panel())
    def test_exact_scoring(self):
        for t in tasks():
            for p in PROBES:self.assertTrue(score(t,p,expected(t,p))['exact'])
    def test_verbose_rejected(self):self.assertFalse(score(tasks()[0],'transfer','Answer: '+expected(tasks()[0],'transfer'))['exact'])
    def test_missing_rejected(self):self.assertFalse(score(tasks()[0],'recall','')['exact'])
    def test_unknown_separate(self):self.assertTrue(score(tasks()[0],'recall','UNKNOWN')['unavailable'])
    def test_bad_arm(self):self.assertRaises(ValueError,source,tasks()[0],'bad')
    def test_bad_probe(self):self.assertRaises(ValueError,query,tasks()[0],'bad')
    def test_balanced_cells(self):self.assertEqual(set(collections.Counter((r['arm'],r['probe']) for r in panel()).values()),{12})
    def test_swap_transfer_distinct(self):
        for t in tasks():self.assertNotEqual(expected(t,'transfer'),expected(t,'transfer',True))
    def test_aggregate_denominator(self):
        t=tasks()[0];rows=[dict(arm='none',probe='recall',score=score(t,'recall','bad'))]
        self.assertEqual(aggregate(rows)['none/recall']['n'],1)
        self.assertEqual(aggregate(rows)['none/recall']['exact'],0)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--self-test',action='store_true');p.add_argument('--live',type=Path);p.add_argument('--export',type=Path)
    args=p.parse_args()
    if args.self_test: unittest.main(argv=[sys.argv[0]],verbosity=2)
    elif args.export:
        args.export.mkdir(parents=True,exist_ok=False)
        write_json(args.export/'protocol.json',PROTOCOL);write_json(args.export/'tasks.json',tasks());write_json(args.export/'requests.json',panel())
    elif args.live:
        try:live(args.live)
        except Exception as e:
            if args.live.exists():write_json(args.live/'failure.json',dict(type=type(e).__name__,message=str(e),status='INCOMPLETE_NOT_A_NULL_RESULT'))
            raise
    else:p.error('Choose --self-test, --export OUT, or --live OUT')
