/* Josh & Rin / Where Do the Goblins Go Shopping?
   Browser source, v0.1, 2026-10-26.
   A scripted-policy demonstration: no language model, external service,
   inferred internal attention or real purchase. Versioned, deterministic. */
(function(global){
"use strict";
const SHOPS=[
 {id:"moth",name:"Mothlight Market",quality:7,value:7,conduct:1,evidence:"unresolved",warmth:0.7,listing:1.05},
 {id:"copper",name:"Copper Commons",quality:9,value:4,conduct:2,evidence:"verified-remediation",warmth:0.3,listing:0.95},
 {id:"gold",name:"Golden Goblin Goods",quality:5,value:7,conduct:0,evidence:"credible-ongoing-harm",warmth:1.0,listing:0.85},
 {id:"lantern",name:"Lantern & Nail",quality:8,value:6,conduct:2,evidence:"unknown",warmth:0.4,listing:1.00},
 {id:"stone",name:"Stone & Star",quality:6,value:9,conduct:1,evidence:"unresolved",warmth:0.2,listing:0.92},
 {id:"duck",name:"Duck Cart Co.",quality:7,value:8,conduct:2,evidence:"clean-record-synthetic",warmth:0.6,listing:1.02}
];
const TYPES=[
 {name:"Reliability",quality:1.7,value:0.45,trust:0.5,ad:0.1,social:0.25,novelty:0.1,hard_veto:false},
 {name:"Budget",quality:0.55,value:1.9,trust:0.2,ad:0.25,social:0.6,novelty:0.15,hard_veto:false},
 {name:"Evidence",quality:0.8,value:0.75,trust:1.7,ad:0.1,social:0.1,novelty:0.2,hard_veto:true},
 {name:"Wanderer",quality:0.9,value:0.8,trust:0.35,ad:0.05,social:-0.45,novelty:1.15,hard_veto:false},
 {name:"Crowd",quality:0.9,value:0.9,trust:0.25,ad:0.6,social:1.6,novelty:0,hard_veto:false},
 {name:"Copy",quality:0.8,value:0.8,trust:0.1,ad:1.6,social:0.55,novelty:0.1,hard_veto:false}
];
function noise(seed,who,step,shop,salt=0){
 let x=(seed ^ Math.imul(who+1,0x9e3779b9) ^ Math.imul(step+1,0x85ebca6b) ^ Math.imul(shop+1,0xc2b2ae35) ^ Math.imul(salt,0x27d4eb2f))>>>0;
 x^=x>>>16;x=Math.imul(x,0x7feb352d)>>>0;
 x^=x>>>15;x=Math.imul(x,0x846ca68b)>>>0;x^=x>>>16;
 return ((x>>>0)/0xffffffff-0.5)*1.18;
}
function simulate(seed=17,budget=3,ad=false,social=false,cohort="mixed",reverse=false){
 if(!Number.isInteger(seed)||seed<1||seed>128)throw Error("Seed 1–128");
 if(![1,2,3,6].includes(budget))throw Error("Budget must be 1,2,3,6");
 if(!["mixed","focused"].includes(cohort))throw Error("Unknown roster");
 const traffic=Array(6).fill(0),first=Array(6).fill(0),carts=Array(6).fill(0),shoppers=[];
 const order=Array.from({length:24},(_,i)=>i);if(reverse)order.reverse();
 for(const who of order){
  const typ=TYPES[cohort==="mixed"?who%6:0],opened=[],trace=[];
  for(let step=0;step<budget;step++){
   let bestScore=-Infinity,best=-1;
   for(let j=0;j<6;j++){
    const s=SHOPS[j];if(opened.includes(j))continue;
    const base=(s.listing-1)*3+typ.quality*(s.quality-7)*0.18+typ.value*(s.value-7)*0.18;
    const pitch=s.warmth*typ.ad*(ad&&j===2?2.9:0.35);
    const boosted=social?3.15*typ.social*Math.log1p(traffic[j])/Math.log(25):0;
    const exploration=typ.novelty*((j+who)%3===0?0.5:-0.2);
    const score=base+pitch+boosted+exploration+noise(seed,who,step,j);
    if(score>bestScore){bestScore=score;best=j;}
   }
   opened.push(best);traffic[best]++;if(step===0)first[best]++;
   trace.push({action:"open",shop:SHOPS[best].id,rank:step+1,attention_source:"selected_dir_link"});
  }
  const short=[];
  for(const j of opened){
   const s=SHOPS[j];
   if(typ.hard_veto&&s.evidence==="credible-ongoing-harm"){
    trace.push({action:"exclude",shop:s.id,reason:"verified-ongoing-harm in synthetic dossier"});
    continue;
   }
   const utility=(typ.quality*(s.quality-7)+typ.value*(s.value-7))*0.55+typ.trust*(s.conduct-1)*0.7+noise(seed,who,7,j,1)*0.4;
   short.push([utility,j]);
  }
  let selected=null;
  if(short.length){
   short.sort((a,b)=>b[0]-a[0]||b[1]-a[1]);
   const k=short[0][1];selected=SHOPS[k].id;carts[k]++;
   trace.push({action:"shortlist",shops:short.slice(0,2).map(x=>SHOPS[x[1]].id)});
   trace.push({action:"select",shop:selected});
  }else{trace.push({action:"defer",reason:"all opened shops excluded by instruction"});}
  shoppers.push({id:who+1,type:typ.name,opens:opened.map(j=>SHOPS[j].id),selected,trace});
 }
 shoppers.sort((a,b)=>a.id-b.id);
 function concentration(counts){
  const total=counts.reduce((a,b)=>a+b,0);
  if(!total)return null;
  const numerator=counts.reduce((sum,x)=>sum+x*x,0)*10000;
  const denominator=total*total;
  let quotient=Math.floor(numerator/denominator);
  const remainder=numerator-quotient*denominator;
  if(2*remainder>denominator||(2*remainder===denominator&&quotient%2===1))quotient++;
  return quotient/10000;
 }
 return {seed,budget,ad,social,cohort,reverse,traffic,first,carts,shoppers,hhi:concentration(traffic),first_hhi:concentration(first),cart_hhi:concentration(carts),unique_opened:traffic.filter(x=>x>0).length};
}
function contrast(seed=17,budget=3,cohort="mixed",social=true,reverse=false){
 const base=simulate(seed,budget,false,social,cohort,reverse);
 const treatment=simulate(seed,budget,true,social,cohort,reverse);
 const pairs=base.shoppers.map((a,i)=>{const b=treatment.shoppers[i];
  return {id:a.id,type:a.type,opened_delta:JSON.stringify(a.opens)!==JSON.stringify(b.opens),first_changed:a.opens[0]!==b.opens[0],selected_changed:a.selected!==b.selected,
  base_opened:a.opens,treat_opened:b.opens,base_selected:a.selected,treat_selected:b.selected};
 });
 return {base,treatment,pairs,changed_first:pairs.filter(x=>x.first_changed).length,changed_carts:pairs.filter(x=>x.selected_changed).length,changed_paths:pairs.filter(x=>x.opened_delta).length};
}
global.GoblinShopModel={SHOPS,TYPES,noise,simulate,contrast};
})(typeof window!=="undefined"?window:globalThis);
