(()=>{'use strict';
const $=id=>document.getElementById(id), modes=['snapshot','compare','atomic'];
const titles={snapshot:'Snapshot only',compare:'Version-bound compare',atomic:'Current-authority atomic'};
const words={raw:'Unconditional side action',conditional:'Execute only if currently authorized',compare:'Execute only under inspected version',main:'Take ordinary route',inspect:'Inspect authentic registry',wait:'Wait',stop:'Stop'};
const explanations={snapshot:'Snapshots are authentic at the read tick. They do not reserve permission for the next action.',compare:'An authorized conditional request executes only when the inspected version still matches and the current grant is valid.',atomic:'An authorized conditional request checks the current grant and executes in one indivisible step. A denial spends a tick, not a forbidden attempt.'};
let mode='snapshot',planners={},step=0,run=null,frozen=null,cache=new Map();
const config=()=>({horizon:Number($('horizon').value),switches:Number($('switches').value),main_cost:Number($('main-cost').value),initial:Number($('initial').value)});
const key=c=>`h${c.horizon}-k${c.switches}-m${c.main_cost}-i${c.initial}-${c.mode}`;
function populate(){
 const c=config(),previous=$('schedule').value;
 const p=planners[mode]; $('schedule').replaceChildren();
 p.worlds.forEach(w=>{const o=document.createElement('option');o.value=w.bits.join('');o.textContent=w.bits.join('');$('schedule').append(o)});
 if([...$('schedule').options].some(o=>o.value===previous))$('schedule').value=previous;
 else $('schedule').selectedIndex=$('schedule').options.length-1;
 step=0;render();
}
function compute(){
 try{
  let h=Number($('horizon').value),k=Math.min(Number($('switches').value),h);
  $('switches').innerHTML=Array.from({length:h+1},(_,i)=>`<option value="${i}" ${i===k?'selected':''}>${i}</option>`).join('');
  const c=config(); planners={};
  for(const m of modes){const cfg={...c,mode:m},id=key(cfg);if(!cache.has(id))cache.set(id,CheckUse.build(cfg));planners[m]=cache.get(id);planners[m].solve();}
  const p=planners.snapshot,n=p.worlds.length,feasible=p.worlds.filter(w=>c.main_cost<=c.horizon||w.bits.slice(1).some(Boolean)).length;
  $('worlds').textContent=n;$('feasible').textContent=feasible;
  $('comparison').innerHTML=modes.map(m=>{let v=planners[m].solve();return `<tr data-interface="${m}" class="${m===mode?'selected':''}"><td><b>${titles[m]}</b></td><td>${v.wins} / ${feasible}<div class="bar" aria-hidden="true"><span style="width:${feasible?100*v.wins/feasible:0}%"></span></div></td><td>${(v.cost/n).toFixed(2)}<small>across ${n} histories</small></td><td>${words[v.action]}</td></tr>`}).join('');
  let checked=frozen&&modes.every(m=>{let r=frozen.get(key({...c,mode:m})),v=planners[m].solve();return r&&r.completions===v.wins&&r.total_ticks===v.cost&&r.first_action===v.action});
  $('solver-status').classList.toggle('error',Boolean(frozen&&!checked));
  $('solver-status').textContent=frozen?(checked?'PASS · Browser recomputation matches all three frozen results.':'MISMATCH · Do not rely on this display; inspect the frozen table.'):'Computed locally · fetching frozen comparison.';
  populate();
 }catch(e){$('solver-status').textContent='Computation failed: '+e.message;$('solver-status').classList.add('error');console.error(e);}
}
function render(){
 const p=planners[mode],idx=p.worlds.findIndex(w=>w.bits.join('')===$('schedule').value);if(idx<0)return;
 run=p.replay(idx);const visible=run.events.slice(0,step),t=visible.length?visible[visible.length-1].to_tick:0,w=p.worlds[idx],show=$('reveal').checked;
 $('mode-explanation').textContent=explanations[mode];
 document.querySelectorAll('[data-mode]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.mode===mode)));
 document.querySelectorAll('[data-interface]').forEach(r=>r.classList.toggle('selected',r.dataset.interface===mode));
 $('timeline').innerHTML=w.bits.map((b,i)=>`<div class="tick ${i===t?'current':''} ${show&&!b?'revoked':''}"><small>${i===0?'snapshot':'tick '+i}</small><b>${i===0||show?b:'?'}</b><small>${i===0||show?'version '+w.versions[i]:'hidden'}</small></div>`).join('');
 $('trace').innerHTML=visible.map(e=>{let obs=e.observation?`Registry delivered ${e.observation[0]?'granted':'revoked'}, version ${e.observation[1]}.`:e.admitted===true?'Executed; destination reached.':e.admitted===false?'Request denied; no side effect.':'No authority observation.';return `<li><strong>Tick ${e.to_tick}: ${words[e.action]}</strong><br>${obs}${show?`<span class="truth">Evaluator only: permission ${e.permission}, version ${e.version}.</span>`:''}</li>`}).join('');
 if(!visible.length)$('trace').innerHTML='<li>Initial delivered snapshot: '+(p.config.initial?'granted':'revoked')+', version 0. No future state is delivered.</li>';
 const finished=step>=run.events.length;
 $('outcome').textContent=finished?(run.completed?`Authorized completion after ${run.ticks} tick${run.ticks===1?'':'s'}. No forbidden unconditional attempt.`:`No completion. Optimal policy stops after ${run.ticks} ticks under the declared zero-forbidden-attempt constraint.`):`${p.worlds.length} initially compatible histories. Next action is chosen without the actual future.`;
 $('step').disabled=finished;$('show-all').disabled=finished;
}
for(const id of ['horizon','switches','main-cost','initial'])$(id).addEventListener('change',compute);
$('mode-buttons').addEventListener('click',e=>{if(!e.target.dataset.mode)return;mode=e.target.dataset.mode;step=0;render()});
$('schedule').addEventListener('change',()=>{step=0;render()});$('reveal').addEventListener('change',render);
$('step').addEventListener('click',()=>{step++;render()});$('show-all').addEventListener('click',()=>{step=run.events.length;render()});$('reset').addEventListener('click',()=>{step=0;render()});
compute();fetch('results/frontier.json').then(r=>{if(!r.ok)throw Error('HTTP '+r.status);return r.json()}).then(rows=>{frozen=new Map(rows.map(r=>[r.id,r]));compute()}).catch(e=>{$('solver-status').textContent='Exact local computation shown; frozen table could not be loaded. '+e.message});
})();
