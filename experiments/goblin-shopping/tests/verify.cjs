/* Run from experiment folder: node tests/verify.cjs
   Node standard library only. Tests scripted fixtures, not live agent behavior.
   Current JS implementation and saved records share the experiment author. */
"use strict";
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
require("../model.js");
const M=globalThis.GoblinShopModel;
const root=path.resolve(__dirname,"..");
const corpus=JSON.parse(fs.readFileSync(path.join(root,"results","scripted-sweep.json"),"utf8"));
function same(a,b){assert.deepEqual(a,b);}
function test(name,fn){fn();process.stdout.write("PASS "+name+"\n");}
test("release fixture identity",()=>{
 assert.equal(corpus.record_id,"GOBLIN-SHOPPING-ATTENTION-DEMO-2026-10-26-001");
 assert.equal(corpus.status,"SCRIPTED_POLICY_DEMO_NO_MODEL_AGENTS");
 assert.equal(corpus.cases.length,2048);
 assert.equal(corpus.scope.policy_executions,98304);
});
test("24 shoppers and exactly stated attention budget",()=>{
 for(const budget of [1,2,3,6]){
  const r=M.simulate(17,budget,true,true,"mixed");
  assert.equal(r.shoppers.length,24);assert.equal(r.traffic.reduce((a,b)=>a+b),24*budget);
  assert.equal(r.first.reduce((a,b)=>a+b),24);
  assert.equal(r.carts.reduce((a,b)=>a+b),24);
  for(const s of r.shoppers){
   assert.equal(s.opens.length,budget);assert.equal(new Set(s.opens).size,budget);
   assert.ok(s.selected===null||s.opens.includes(s.selected));
   assert.ok(s.trace.every(t=>t.action!=="purchase"));
  }
 }
});
test("24 paired identities remain stable",()=>{
 const x=M.contrast(17,3,"mixed",true);
 same(x.base.shoppers.map(y=>y.id),x.treatment.shoppers.map(y=>y.id));
 same(x.base.shoppers.map(y=>y.type),x.treatment.shoppers.map(y=>y.type));
});
test("seed-17 observable witness",()=>{
 const x=M.contrast(17,3,"mixed",true);
 same(x.base.traffic,[24,5,0,18,6,19]);same(x.treatment.traffic,[23,4,13,11,4,17]);
 same(x.base.carts,[0,3,0,3,3,15]);same(x.treatment.carts,[1,3,0,3,2,15]);
 assert.equal(x.changed_paths,14);assert.equal(x.changed_carts,4);
 assert.equal(x.base.hhi,0.2550);assert.equal(x.treatment.hhi,0.2199);
});
test("full browse saturates catalog; choices invariant",()=>{
 for(const seed of [1,17,40,128])for(const social of [false,true]){
  const x=M.contrast(seed,6,"mixed",social);
  assert.equal(x.changed_carts,0);same(x.base.traffic,x.treatment.traffic);
 }
});
test("first-glance budget allows promoted selection",()=>{
 const x=M.contrast(17,1,"mixed",true);
 assert.equal(x.treatment.traffic[2],4);assert.equal(x.treatment.carts[2],4);
});
test("independent conduct veto is respected in scripted policy",()=>{
 for(const seed of [1,17,40,128])for(const ad of [false,true])for(const social of [false,true]){
  for(const s of M.simulate(seed,3,ad,social,"mixed").shoppers)if(s.type==="Evidence"){
   assert.notEqual(s.selected,"gold");
   if(s.opens.includes("gold"))assert.ok(s.trace.some(t=>t.action==="exclude"&&t.shop==="gold"));
  }
 }
});
test("without social feedback, reversing arrival is a non-event",()=>{
 for(const seed of [1,17,40,128])for(const budget of [1,3,6]){
  const a=M.simulate(seed,budget,false,false,"mixed",false);
  const b=M.simulate(seed,budget,false,false,"mixed",true);
  same(a.shoppers,b.shoppers);same(a.traffic,b.traffic);same(a.carts,b.carts);
 }
});
test("social feedback produces path dependence in known witness",()=>{
 const a=M.simulate(17,3,false,true,"mixed",false);
 const b=M.simulate(17,3,false,true,"mixed",true);
 assert.notDeepEqual(a.traffic,b.traffic);
});
test("every archived finite-sweep count and metric replays",()=>{
 for(const row of corpus.cases){
  const r=M.contrast(row.seed,row.budget,row.cohort,row.social,false);
  for(const [key,value] of Object.entries({
   base_traffic:r.base.traffic,promo_traffic:r.treatment.traffic,
   base_first:r.base.first,promo_first:r.treatment.first,
   base_carts:r.base.carts,promo_carts:r.treatment.carts,
   base_hhi:r.base.hhi,promo_hhi:r.treatment.hhi,
   changed_paths:r.changed_paths,changed_first:r.changed_first,
   changed_carts:r.changed_carts
  }))same(row[key],value);
 }
});
process.stdout.write("Verified 10 test groups; 2,048 paired cases and 22,528 stored metrics matched the replay.\n");
