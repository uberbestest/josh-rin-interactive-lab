/* Josh & Rin, 2026-10-26.
   The Shop That Sold Nothing — post-hoc witness replay.
   From experiments/goblin-shopping/notes:
       node ghost-seller.test.cjs
   Node stdlib only; deterministic scripted policies, zero LLM agents.
*/
"use strict";
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
require("../model.js");
const M=globalThis.GoblinShopModel;
const sweep=JSON.parse(fs.readFileSync(path.join(__dirname,"..","results","scripted-sweep.json"),"utf8"));
const note=JSON.parse(fs.readFileSync(path.join(__dirname,"ghost-seller-record.json"),"utf8"));
let n=0;
function test(title,fn){fn();n++;process.stdout.write("PASS "+title+"\n");}
function nonVisitors(x){return x.pairs.filter(p=>p.selected_changed&&!p.treat_opened.includes("gold")).map(p=>p.id);}
function qualifies(x){return x.promo_traffic[2]>x.base_traffic[2]&&x.base_carts[2]===0&&x.promo_carts[2]===0&&x.changed_carts>0;}
const witness=M.contrast(72,2,"mixed",true,false);

test("original archived input has 2,048 paired scenarios",()=>{
 assert.equal(sweep.cases.length,2048);
 assert.equal(sweep.status,"SCRIPTED_POLICY_DEMO_NO_MODEL_AGENTS");
 assert.equal(note.lineage.original_sweep_git_blob,"bcec812b05be7a981e4561407ee67c1775181b12");
});
test("post-hoc selection rule matches 494 archived cases",()=>{
 const qualifying=sweep.cases.filter(qualifies);
 assert.equal(qualifying.length,494);
 const peak=Math.max(...qualifying.map(x=>x.changed_carts));
 assert.equal(peak,16);
 assert.deepEqual(qualifying.filter(x=>x.changed_carts===peak).map(x=>[x.seed,x.budget,x.social,x.cohort]),[[72,2,true,"mixed"]]);
 assert.equal(note.selection.qualifying_cases,qualifying.length);
 assert.equal(note.selection.maximum_changed_final_selections,peak);
});
test("golden store attracts eleven opens and sells zero",()=>{
 assert.equal(witness.base.traffic[2],0);
 assert.equal(witness.treatment.traffic[2],11);
 assert.equal(witness.base.carts[2],0);
 assert.equal(witness.treatment.carts[2],0);
});
test("sixteen carts move between other stores",()=>{
 assert.equal(witness.changed_carts,16);
 assert.deepEqual(witness.base.carts,[1,3,0,5,3,12]);
 assert.deepEqual(witness.treatment.carts,[11,5,0,3,3,2]);
 assert.equal(witness.base.carts.reduce((a,b)=>a+b),24);
 assert.equal(witness.treatment.carts.reduce((a,b)=>a+b),24);
});
test("five changed without opening promoted seller",()=>{
 assert.deepEqual(nonVisitors(witness),[8,9,16,19,22]);
 assert.deepEqual(note.witness.changed_without_promoted_store_open,[8,9,16,19,22]);
});
test("saved witness matches replay by all stored fields",()=>{
 const x=sweep.cases.find(x=>x.seed===72&&x.budget===2&&x.social&&x.cohort==="mixed");
 assert.ok(x);
 for(const [field,value] of Object.entries({base_traffic:witness.base.traffic,promo_traffic:witness.treatment.traffic,
   base_carts:witness.base.carts,promo_carts:witness.treatment.carts,
   base_first:witness.base.first,promo_first:witness.treatment.first,changed_paths:witness.changed_paths,
   changed_first:witness.changed_first,changed_carts:witness.changed_carts,
   base_hhi:witness.base.hhi,promo_hhi:witness.treatment.hhi}))assert.deepEqual(x[field],value,field);
});
test("feedback-off same-seed control has four changed choices and no indirect changes",()=>{
 const x=M.contrast(72,2,"mixed",false,false);
 assert.equal(x.changed_carts,4);
 assert.deepEqual(nonVisitors(x),[]);
 assert.deepEqual([x.base.traffic[2],x.treatment.traffic[2]],[0,10]);
 assert.deepEqual([x.base.carts[2],x.treatment.carts[2]],[0,0]);
});
test("full-browse control changes no cart, although ordering can change",()=>{
 const x=M.contrast(72,6,"mixed",true,false);
 assert.equal(x.changed_carts,0);
 assert.equal(x.changed_paths,13);
 assert.deepEqual(x.base.carts,x.treatment.carts);
});
test("homogeneous reliability roster is invariant at selected seed",()=>{
 const x=M.contrast(72,2,"focused",true,false);
 assert.equal(x.changed_paths,0);
 assert.equal(x.changed_carts,0);
});
test("one-opening control does show advertised-store sales",()=>{
 const x=M.contrast(72,1,"mixed",true,false);
 assert.equal(x.changed_carts,8);
 assert.deepEqual([x.base.carts[2],x.treatment.carts[2]],[0,4]);
});
test("feedback-on reversal changes the allocation",()=>{
 const x=M.contrast(72,2,"mixed",true,true);
 assert.equal(x.changed_carts,20);
 assert.equal(x.treatment.traffic[2],12);
 assert.notDeepEqual(x.treatment.carts,witness.treatment.carts);
});
test("no-feedback negative control across 256 budget 2/3 cases",()=>{
 for(const budget of [2,3])for(let seed=1;seed<=128;seed++){
  const x=M.contrast(seed,budget,"mixed",false,false);
  assert.deepEqual(nonVisitors(x),[]);
 }
});
process.stdout.write("PASS: "+n+" regression groups; post-hoc selection and controls reproduced. Scripted-policy inference only.\n");
