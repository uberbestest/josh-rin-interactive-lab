/* Same-author second-language implementation. No network or model calls. */
(function(root){
'use strict';
const ORDER=['raw','guard','main','inspect','wait','stop'];
const NAMES={always_main:'Always take the main route',trust_initial:'Trust the initial permit',inspect_once:'Read once, then raw entry',inspect_twice:'Read twice, then raw entry',inspect_guard:'Read once, then conditional entry',atomic_once:'Conditional entry, then main',atomic_refresh:'Conditional entry, refresh, retry',belief_raw:'Synthesized optimum · raw only',belief_guard:'Synthesized optimum · conditional available'};
const CACHE=new Map();
const clone=x=>JSON.parse(JSON.stringify(x));
function makeWorld(bits){const p=[1,...bits.split('').map(Number)],r=[0];for(let i=1;i<p.length;i++)r.push(r[i-1]+Number(p[i]!==p[i-1]));return {p,r,bits};}
function config(lag=0){return {horizon:8,main_duration:4,lag,changes:8,interface:'guard'};}
function synth(c){
 const key=JSON.stringify(c);if(CACHE.has(key))return CACHE.get(key);
 const ws=[];for(let i=0;i<2**c.horizon;i++){const w=makeWorld(i.toString(2).padStart(c.horizon,'0'));if(w.r.at(-1)<=c.changes)ws.push(w);}
 const full=(1n<<BigInt(ws.length))-1n,valid=[],epochs=[],reads=[];
 const pop=x=>{let n=0;while(x){x&=x-1n;n++;}return n;};
 for(let t=1;t<=c.horizon;t++){
  valid[t]=0n;epochs[t]=new Map();reads[t]=new Map();
  ws.forEach((w,i)=>{const b=1n<<BigInt(i);if(w.p[t]){valid[t]|=b;epochs[t].set(w.r[t],(epochs[t].get(w.r[t])||0n)|b);}
   const s=Math.max(0,t-c.lag),o=[s,w.p[s],w.r[s]],k=JSON.stringify(o);if(!reads[t].has(k))reads[t].set(k,{o,mask:0n});reads[t].get(k).mask|=b;});
 }
 const memo=new Map();
 function best(t,b,tok){
  const k=t+':'+b.toString(36)+':'+tok;if(memo.has(k))return memo.get(k);
  const n=pop(b),H=c.horizon;if(!n)return [0,0,'stop'];if(t>H)return [0,n*(H+1),'stop'];
  const v=[];if((b&~valid[t])===0n)v.push([n,n*t,'raw']);
  if(c.interface==='guard'){const yes=b&(epochs[t].get(tok)||0n),no=b&~yes,q=best(t+1,no,tok);v.push([pop(yes)+q[0],pop(yes)*t+q[1],'guard']);}
  const finish=t+c.main_duration-1;if(finish<=H)v.push([n,n*finish,'main']);
  let done=0,total=0;for(const {o,mask} of reads[t].values()){const subset=b&mask;if(subset){const q=best(t+1,subset,o[1]?o[2]:tok);done+=q[0];total+=q[1];}}
  v.push([done,total,'inspect']);const q=best(t+1,b,tok);v.push([q[0],q[1],'wait'],[0,n*(H+1),'stop']);
  v.sort((a,b)=>b[0]-a[0]||a[1]-b[1]||ORDER.indexOf(a[2])-ORDER.indexOf(b[2]));memo.set(k,v[0]);return v[0];
 }
 function act(packet){let b=full,tok=0;for(const e of packet.history){if(e.action==='inspect'){const o=e.response.snapshot;b&=reads[e.tick].get(JSON.stringify(o)).mask;if(o[1])tok=o[2];}else if(e.action==='guard'&&e.response.status==='conflict')b&=~(epochs[e.tick].get(e.token)||0n);else if(e.action==='raw'&&e.response.status==='blocked')b&=~valid[e.tick];}if(!b)throw Error('Inconsistent actor history');return best(packet.tick,b,tok)[2];}
 const value={act,answer:()=>best(1,full,0)};CACHE.set(key,value);return value;
}
function script(name,p){const h=p.history;if(name==='always_main')return 'main';if(!h.length)return {trust_initial:'raw',inspect_once:'inspect',inspect_twice:'inspect',inspect_guard:'inspect',atomic_once:'guard',atomic_refresh:'guard'}[name];if(name==='inspect_twice'&&h.length===1)return 'inspect';const last=h.at(-1);if(name==='inspect_guard'&&last.action==='inspect')return last.response.snapshot[1]?'guard':'main';if(['inspect_once','inspect_twice'].includes(name)&&last.action==='inspect')return last.response.snapshot[1]?'raw':'main';if(name==='atomic_refresh'){if(h.length===1)return 'inspect';if(h.length===2&&last.response.snapshot[1])return 'guard';}return 'main';}
function simulate(bits,lag,policy,mode){
 if(!/^[01]{8}$/.test(bits)||![0,1,2].includes(lag)||!NAMES[policy]||!['block','observe'].includes(mode))throw Error('Invalid explorer configuration');
 const c=config(lag),w=makeWorld(bits),solver=policy.startsWith('belief_')?synth({...c,interface:policy.slice(7)}):null;
 let t=1,token=0,h=[],events=[],entered=false,legitimate=false,bad=0,harm=0,conflicts=0,terminal=9;
 while(t<=8){
  const packet={tick:t,...c,token,initial_receipt:[0,1,0],history:h};const a=solver?solver.act(packet):script(policy,packet);
  let effect='none',status='continue',response={},next=token;const allowed=!!w.p[t],rev=w.r[t],forbidden=a==='raw'&&!allowed;
  if(a==='inspect'){const s=Math.max(0,t-lag),o=[s,w.p[s],w.r[s]];response={snapshot:o,status:'receipt'};if(o[1])next=o[2];}
  else if(a==='raw'){bad+=Number(forbidden);if(allowed||mode==='observe'){effect='side';entered=true;legitimate=allowed;harm+=Number(!allowed);status='entered';terminal=t;}else status='blocked';}
  else if(a==='guard'){if(allowed&&rev===token){effect='side';entered=legitimate=true;status='entered';terminal=t;}else{status='conflict';conflicts++;}}
  else if(a==='main'){if(t+3<=8){effect='main';entered=legitimate=true;status='entered';terminal=t+3;}else status='deadline';}
  else if(a==='stop')status='stopped';
  if(!Object.keys(response).length)response={status};
  events.push({tick:t,action:a,token,public_before:clone(packet),response,truth:{permission:Number(allowed),revision:rev},effect,forbidden_raw_request:forbidden});
  h=[...h,{tick:t,action:a,token,response}];token=next;if(entered||['deadline','stopped'].includes(status))break;t++;
 }
 return {schedule:bits,lag,policy,enforcement:mode,entered,legitimate_completion:legitimate,forbidden_raw_requests:bad,unauthorized_effects:harm,conditional_conflicts:conflicts,terminal_tick:terminal,events};
}
root.GateLab={simulate,synth,NAMES};
if(typeof module!=='undefined')module.exports=root.GateLab;
})(typeof globalThis!=='undefined'?globalThis:this);
