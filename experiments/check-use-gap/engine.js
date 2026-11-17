/* Exact finite optimizer, independently implemented in JavaScript.
 * No API calls, learner, hidden model state, or realized-future input to policy.
 * CommonJS export plus browser global; all time/cost quantities are integers.
 */
(function (root) {
  'use strict';
  const order = ['raw','conditional','compare','main','inspect','wait','stop'];
  function build(c) {
    if (!Number.isInteger(c.horizon) || c.horizon < 1 || c.horizon > 10 || c.switches < 0 || c.switches > c.horizon || !['snapshot','compare','atomic'].includes(c.mode)) throw Error('Invalid configuration');
    const worlds=[];
    for(let value=0; value<2**c.horizon; value++) {
      const bits=[c.initial,...value.toString(2).padStart(c.horizon,'0').split('').map(Number)];
      const versions=[0];
      for(let t=1;t<bits.length;t++) versions.push(versions[t-1]+Number(bits[t]!==bits[t-1]));
      if(versions[c.horizon]<=c.switches) worlds.push({bits,versions});
    }
    const cache=new Map();
    const key=(t,B,token)=>`${t}|${B.join(',')}|${token}`;
    function solve(t=0,B=worlds.map((_,i)=>i),token=0) {
      const id=key(t,B,token); if(cache.has(id)) return cache.get(id);
      const candidates=[]; const n=B.length;
      function add(action,wins,cost){candidates.push({action,wins,cost});}
      add('stop',0,0);
      if(t<c.horizon) {
        const next=t+1;
        if(B.every(i=>worlds[i].bits[next]===1)) add('raw',n,n);
        if(t+c.main_cost<=c.horizon) add('main',n,n*c.main_cost);
        let v=solve(next,B,token); add('wait',v.wins,v.cost+n);
        const groups=new Map();
        for(const i of B) {
          const w=worlds[i],label=`${w.bits[next]}:${w.versions[next]}`;
          if(!groups.has(label))groups.set(label,{ids:[],ver:w.versions[next]});
          groups.get(label).ids.push(i);
        }
        let qw=0,qc=n;
        for(const g of groups.values()){v=solve(next,g.ids,g.ver);qw+=v.wins;qc+=v.cost;}
        add('inspect',qw,qc);
        if(c.mode!=='snapshot') {
          const bad=B.filter(i=>!worlds[i].bits[next]||(c.mode==='compare'&&worlds[i].versions[next]!==token));
          v=bad.length?solve(next,bad,token):{wins:0,cost:0};
          add(c.mode==='atomic'?'conditional':'compare',n-bad.length+v.wins,n+v.cost);
        }
      }
      candidates.sort((a,b)=>(b.wins-a.wins)||(a.cost-b.cost)||(order.indexOf(a.action)-order.indexOf(b.action)));
      const best=candidates[0]; cache.set(id,best); return best;
    }
    function replay(index) {
      const real=worlds[index]; if(!real)throw Error('No such schedule');
      let B=worlds.map((_,i)=>i),t=0,token=0,completed=false;
      const events=[];
      while(t<=c.horizon) {
        const a=solve(t,B,token).action,start=t; if(a==='stop')break;
        let observation=null,admitted=null;
        t+=a==='main'?c.main_cost:1;
        if(a==='main'){admitted=true;completed=true;}
        else if(a==='raw') {if(!real.bits[t])throw Error('unsafe synthesized raw action');admitted=true;completed=true;}
        else if(a==='inspect') {
          observation=[real.bits[t],real.versions[t]];token=real.versions[t];
          B=B.filter(i=>worlds[i].bits[t]===real.bits[t]&&worlds[i].versions[t]===token);
        } else if(a==='conditional'||a==='compare') {
          admitted=Boolean(real.bits[t]&&(a==='conditional'||real.versions[t]===token));completed=admitted;
          if(!admitted)B=B.filter(i=>!(worlds[i].bits[t]&&(a==='conditional'||worlds[i].versions[t]===token)));
        }
        events.push({from_tick:start,to_tick:t,action:a,observation,admitted,permission:real.bits[t],version:real.versions[t],possible:B.length});
        if(completed)break;
      }
      return {completed,ticks:t,events};
    }
    return {worlds,solve,replay,cache,config:c};
  }
  const api={build,order};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
  else root.CheckUse=api;
})(typeof globalThis!=='undefined'?globalThis:this);
