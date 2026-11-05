/* Local-only presentation. Curated cases are illustrations, not sampled trials. */
(function(){
'use strict';
const E=window.BreadEngine,R=window.BREAD_RESULTS,$=id=>document.getElementById(id);
const names={choir:'1 source × 10',loud_minority:'3 sources: 8 / 1 / 1',two_sources:'2 sources: 5 / 5',mixed:'4 sources: 4 / 3 / 2 / 1',five_pairs:'5 sources × 2',ten_roots:'10 distinct sources'};
const ruleNames={headcount:'Count the heads',receipts:'Count the receipts',shared_cause:'Model the shared cause'};
const actionNames={buy:'BUY · fresh',reject:'REJECT · stale',hold:'HOLD · more evidence'};
const assumptions={headcount:'Assumes every report is independent.',receipts:'Deduplicates copies; assumes roots are independent.',shared_cause:'Uses the supplied dependence model.'};
function pct(p,d=2){if(p===null)return '—';if(p>.999999&&p<1)return '>99.9999%';if(p>0&&p<.000001)return '<0.0001%';if((p>.99995&&p<1)||(p>0&&p<.00005))return (100*p).toFixed(4)+'%';return (100*p).toFixed(d)+'%';}
const rounds=[
 {title:'The perfect chorus',topology:'choir',bits:[1],r:.2,q:0,truth:0,context:'All ten goblins say “fresh.” Each root witness is 80% accurate. Is this enough to stake Puddle’s bread?',explain:'Every report came from the same observation. Ten copies push the headcount estimate above 99.9999%, but the model-supported fresh probability remains 80%. This selected lot happened to be stale.'},
 {title:'The loud minority',topology:'loud_minority',bits:[1,0,0],r:.2,q:0,truth:0,context:'Eight goblins say “fresh.” Two say “stale.” Trace the receipts before calling this an eight-to-two landslide.',explain:'Eight votes are copies of source A. The other two come from separate observations. Deduplicated evidence favors stale at 80%—still short of the 90% threshold for a decisive action. The model-supported action is hold, not blindly trust the minority.'},
 {title:'Ten receipts, one bad ledger',topology:'ten_roots',bits:Array(10).fill(1),r:.2,q:.15,truth:0,context:'Ten distinct receipts, all saying “fresh.” Each witness is still 80% accurate, but their upstream ledger has a shared 15% fault rate.',explain:'Distinct receipt IDs remove copying, not the common upstream fault. The model-supported fresh probability stays below 85%, while independent counting is almost certain. A fresh label does not make a fresh loaf.'},
 {title:'Evidence earns its confidence',topology:'ten_roots',bits:[1,1,1,1,1,1,1,1,1,0],r:.2,q:0,truth:1,context:'Nine fresh reports, one stale report. Ten separate observations, with no shared fault in this supplied model.',explain:'Here the agreement is genuinely supported by independent evidence. All three rules favor buying. This is the positive control: the lesson is not “consensus is bad.”'},
 {title:'The dissenter is not a prophet',topology:'ten_roots',bits:[1,1,1,1,1,1,1,1,0,0],r:.2,q:0,truth:1,context:'Eight fresh reports, two stale reports—the same visible split as inspection 02, but now every report has its own independent source.',explain:'An eight-to-two split can mean different things under different evidence structures. Here eight independent fresh observations dominate two stale observations. Disagreement alone is not a reason to reverse the majority.'}
];
let round=0,traced=false,answered=false;
function renderRound(){
 const c=rounds[round],copies=E.topologies[c.topology];
 $('round-count').textContent=`Inspection ${String(round+1).padStart(2,'0')} / 05`;
 $('round-title').textContent=c.title;$('round-context').textContent=c.context;$('lot-label').textContent=`LOT ${String(round+1).padStart(3,'0')}`;
 $('model-clue').textContent=`Root accuracy ${pct(1-c.r,0)} · shared fault ${pct(c.q,0)}`;
 let html='',n=0;copies.forEach((w,i)=>{for(let j=0;j<w;j++){n++;html+=`<div class="goblin ${c.bits[i]?'fresh':'stale'}"><span class="report-icon" aria-hidden="true">✦</span><span class="name">GOBLIN ${String(n).padStart(2,'0')}</span><span class="say">${c.bits[i]?'“Fresh.”':'“Stale.”'}</span><span class="origin">${traced?'Source '+String.fromCharCode(65+i):'Receipt not traced'}</span></div>`;}});
 $('reports').innerHTML=html;
 $('receipts').hidden=!traced;$('trace').setAttribute('aria-expanded',String(traced));$('trace').textContent=traced?'Hide the receipts':'Trace the receipts';
 $('receipt-list').innerHTML=copies.map((w,i)=>`<span class="receipt-token">${String.fromCharCode(65+i)} → ${w} report${w>1?'s':''}</span>`).join('');
 $('receipt-explanation').textContent=`Ten reports trace to ${copies.length} root observation${copies.length>1?'s':''}. `+(c.q>0?'Distinct roots still share the upstream fault. A different receipt is not a different failure mechanism.':'The model supplies no common upstream fault for this case.');
}
function resetRound(){traced=false;answered=false;$('feedback').hidden=true;$('feedback').textContent='';document.querySelectorAll('[data-action]').forEach(b=>{b.disabled=false;b.setAttribute('aria-pressed','false');});renderRound();}
$('trace').addEventListener('click',()=>{traced=!traced;renderRound();});
$('next-round').addEventListener('click',()=>{round=(round+1)%rounds.length;resetRound();});
document.querySelectorAll('[data-action]').forEach(button=>button.addEventListener('click',()=>{
 if(answered)return;answered=true;const c=rounds[round],action=button.dataset.action,p=E.predict(c.bits,E.topologies[c.topology],c.r,c.q),expected=E.expectedPayoff(action,p.shared_cause);
 const values=['buy','reject','hold'].map(a=>E.expectedPayoff(a,p.shared_cause)),best=Math.max(...values),supported=Math.abs(expected-best)<1e-10;
 const realized=E.payoff(action,c.truth);traced=true;renderRound();document.querySelectorAll('[data-action]').forEach(b=>{b.disabled=true;b.setAttribute('aria-pressed',String(b===button));});
 $('feedback').hidden=false;$('feedback').innerHTML=`<h4>${supported?'A model-supported decision.':'The receipts do not support that risk.'}</h4><div class="resultfacts"><span>Model-supported P(fresh)<b>${pct(p.shared_cause)}</b></span><span>Expected payoff of your choice<b>${expected.toFixed(3)} tokens</b></span><span>This selected lot was<b>${c.truth?'FRESH':'STALE'} · ${realized>0?'+':''}${realized} token${Math.abs(realized)!==1?'s':''}</b></span></div><p>${c.explain}</p><p><strong>Decision quality is not hindsight.</strong> The expected payoff uses the model before the outcome. The realized payoff describes only this authored example.</p>`;
}));
let bits=[1];
function renderWorkbench(){
 const topo=$('topology').value,copies=E.topologies[topo],r=Number($('accuracy').value),alpha=Number($('shared').value)/100,q=r*alpha;
 if(bits.length!==copies.length)bits=Array(copies.length).fill(1);
 $('shared-value').textContent=`${Math.round(100*alpha)}% of marginal error allocated to sharing → ${pct(q,1)} shared-fault probability`;
 $('root-description').textContent=`${copies.length} root observation${copies.length>1?'s':''}, ten reports. Click a root to change every copy.`;
 $('roots').innerHTML=copies.map((w,i)=>`<button type="button" class="root-toggle" data-root="${i}" aria-pressed="${Boolean(bits[i])}" aria-label="Source ${String.fromCharCode(65+i)} reports ${bits[i]?'fresh':'stale'}; click to toggle"><strong>${String.fromCharCode(65+i)} · ${bits[i]?'FRESH':'STALE'}</strong><span>${w} report${w>1?'s':''}</span></button>`).join('');
 $('roots').querySelectorAll('[data-root]').forEach(button=>button.addEventListener('click',()=>{const i=Number(button.dataset.root);bits[i]=1-bits[i];renderWorkbench();$('roots').querySelector(`[data-root="${i}"]`).focus();}));
 const ps=E.predict(bits,copies,r,q);
 $('predictions').innerHTML=E.rules.map(rule=>`<article class="prediction" data-rule="${rule}"><h3>${ruleNames[rule]}</h3><p class="assumption">${assumptions[rule]}</p><div class="prob">${pct(ps[rule])}</div><div class="prob-label">Probability the bread is fresh</div><div class="bar" aria-hidden="true"><div class="fill" style="width:${100*ps[rule]}%"></div></div><div class="verdict">${actionNames[E.decide(ps[rule])]}</div></article>`).join('');
 $('work-note').textContent=q>0?`Individual root accuracy stays at ${pct(1-r,0)}. The shared-cause posterior cannot be more confident than ${pct(1-q,1)} either way. Different receipts do not remove the shared failure.`:`At zero shared fault, counting each distinct root once is the correct model. Copying a receipt changes the headcount, not the evidence.`;
}
$('topology').addEventListener('change',()=>{bits=[];renderWorkbench();});$('accuracy').addEventListener('change',renderWorkbench);$('shared').addEventListener('input',renderWorkbench);$('all-fresh').addEventListener('click',()=>{bits=Array(E.topologies[$('topology').value].length).fill(1);renderWorkbench();});
function renderResults(){
 const acc=$('result-accuracy').value,alpha=$('result-shared').value,metric=$('metric').value,prefix=`a${acc}-s${String(alpha).padStart(2,'0')}-`;
 const cells=R.cells.filter(c=>c.id.startsWith(prefix));
 function fmt(v){if(v===null)return '—';return ['brier','payoff'].includes(metric)?v.toFixed(4):pct(v);}
 $('results-body').innerHTML=cells.map(c=>`<tr><td>${names[c.topology]}</td>${E.rules.map(rule=>`<td>${fmt(c.metrics[rule][metric])}</td>`).join('')}</tr>`).join('');
 $('table-caption').textContent=`${acc}% individual root accuracy; shared-fault probability ${pct(E.fraction(cells[0].shared_fault_probability),1)}. All cells use ten reports.`;
 const desc={brier:'Probability-weighted squared probability error. Lower is better. Unlike accuracy, this score penalizes misplaced confidence.',coverage:'Probability mass on which the rule buys or rejects rather than holding. Read alongside accuracy and wrong-decision mass.',decisive_accuracy:'Accuracy conditional on buying or rejecting. A dash means the rule never decides in this condition; inspect coverage too.',wrong_mass:'Unconditional probability of a wrong decisive action. Zero can mean the rule always holds; it is not by itself evidence of a useful policy.',payoff:'Expected payoff per case: +1 for a correct decisive action, −9 for a wrong one, 0 for holding. These are authored toy costs, not real trading advice.'};
 $('results-explanation').textContent=desc[metric];
}
['result-accuracy','result-shared','metric'].forEach(id=>$(id).addEventListener('change',renderResults));
resetRound();renderWorkbench();renderResults();
window.BREAD_UI_READY=true;
})();
