/* Josh & Rin, 2026-10-27 — exploratory mechanism follow-up.
 * Usage: node run.cjs /path/to/goblin-shopping/model.js /path/to/output
 * Node stdlib only. No APIs, model agents, merchants, or purchases.
 * Public original model is read unchanged. See PROTOCOL.md.
 */
"use strict";
const fs = require("node:fs");
const path = require("node:path");
const crypto = require("node:crypto");
const assert = require("node:assert/strict");

const modelFile = path.resolve(process.argv[2] || "");
const outputDir = path.resolve(process.argv[3] || "");
if (process.argv.length !== 4) throw Error("Usage: node run.cjs MODEL_JS OUTPUT_DIRECTORY");
const sha = data => crypto.createHash("sha256").update(data).digest("hex");
const originalBytes = fs.readFileSync(modelFile);
const modelHash = sha(originalBytes);
const EXPECTED_MODEL_HASH = "f6317cea262e036d9e1bcc93e2a58cdab5a41704450f792c73f63ab016aa1ab0";
assert.equal(modelHash, EXPECTED_MODEL_HASH, "This protocol is pinned to the original public model.");
require(modelFile);
const M = globalThis.GoblinShopModel;
const { SHOPS, TYPES, noise } = M;
const ids = SHOPS.map(x => x.id);
const ix = new Map(ids.map((s, i) => [s, i]));

function concentration(counts) {
  const total = counts.reduce((a, b) => a + b, 0);
  if (!total) return null;
  const numerator = counts.reduce((sum, x) => sum + x*x, 0) * 10000;
  const denominator = total * total;
  let quotient = Math.floor(numerator / denominator);
  const remainder = numerator - quotient * denominator;
  if (2*remainder > denominator || (2*remainder === denominator && quotient%2 === 1)) quotient++;
  return quotient / 10000;
}

/* Transparent replay of the published scoring/choice rules. The only new
 * intervention is the popularity display at `history[who]`. When omitted,
 * this must reproduce the entire original simulation, including traces.
 * History contains counts at the start of a shopper's arrival. That shopper
 * cannot reopen a store, so their own in-progress counts cannot affect the
 * scores of any still-eligible candidate. We nevertheless add own opens to
 * the displayed array to preserve the original per-step interpretation.
 */
function replay(seed, budget, ad, social, cohort, reverse, history = null) {
  const traffic = Array(6).fill(0), first = Array(6).fill(0), carts = Array(6).fill(0), shoppers = [];
  const order = Array.from({length:24}, (_, i) => i);
  if (reverse) order.reverse();
  for (const who of order) {
    const typ = TYPES[cohort === "mixed" ? who%6 : 0], opened = [], trace = [];
    const held = history ? history[who].slice() : null;
    for (let step = 0; step < budget; step++) {
      let bestScore = -Infinity, best = -1;
      for (let j = 0; j < 6; j++) {
        const s = SHOPS[j];
        if (opened.includes(j)) continue;
        const base = (s.listing-1)*3 + typ.quality*(s.quality-7)*0.18 + typ.value*(s.value-7)*0.18;
        const pitch = s.warmth*typ.ad*(ad && j === 2 ? 2.9 : 0.35);
        const displayed = held || traffic;
        const boosted = social ? 3.15*typ.social*Math.log1p(displayed[j])/Math.log(25) : 0;
        const exploration = typ.novelty*((j+who)%3 === 0 ? 0.5 : -0.2);
        const score = base + pitch + boosted + exploration + noise(seed, who, step, j);
        if (score > bestScore) { bestScore = score; best = j; }
      }
      opened.push(best);
      traffic[best]++;
      if (held) held[best]++;
      if (step === 0) first[best]++;
      trace.push({action:"open", shop:SHOPS[best].id, rank:step+1, attention_source:"selected_dir_link"});
    }
    const short = [];
    for (const j of opened) {
      const s = SHOPS[j];
      if (typ.hard_veto && s.evidence === "credible-ongoing-harm") {
        trace.push({action:"exclude", shop:s.id, reason:"verified-ongoing-harm in synthetic dossier"});
        continue;
      }
      const utility = (typ.quality*(s.quality-7) + typ.value*(s.value-7))*0.55
        + typ.trust*(s.conduct-1)*0.7 + noise(seed, who, 7, j, 1)*0.4;
      short.push([utility, j]);
    }
    let selected = null;
    if (short.length) {
      short.sort((a, b) => b[0]-a[0] || b[1]-a[1]);
      const k = short[0][1]; selected = SHOPS[k].id; carts[k]++;
      trace.push({action:"shortlist", shops:short.slice(0,2).map(x => SHOPS[x[1]].id)});
      trace.push({action:"select", shop:selected});
    } else trace.push({action:"defer", reason:"all opened shops excluded by instruction"});
    shoppers.push({id:who+1, type:typ.name, opens:opened.map(j => SHOPS[j].id), selected, trace});
  }
  shoppers.sort((a,b) => a.id-b.id);
  return {seed,budget,ad,social,cohort,reverse,traffic,first,carts,shoppers,
    hhi:concentration(traffic), first_hhi:concentration(first), cart_hhi:concentration(carts),
    unique_opened:traffic.filter(x => x > 0).length};
}

function priorHistory(base) {
  const prior = Array(24), traffic = Array(6).fill(0), order = base.shoppers.slice();
  if (base.reverse) order.reverse();
  for (const shopper of order) {
    prior[shopper.id-1] = traffic.slice();
    for (const s of shopper.opens) traffic[ix.get(s)]++;
  }
  assert.deepEqual(traffic, base.traffic);
  return prior;
}

function compare(base, treatment) {
  const changed = [], pathChanged = [], firstChanged = [], strictNonvisitor = [], noTreatmentVisit = [];
  for (let j = 0; j < 24; j++) {
    const a = base.shoppers[j], b = treatment.shoppers[j];
    assert.equal(a.id, b.id);
    if (JSON.stringify(a.opens) !== JSON.stringify(b.opens)) pathChanged.push(a.id);
    if (a.opens[0] !== b.opens[0]) firstChanged.push(a.id);
    if (a.selected !== b.selected) {
      changed.push(a.id);
      if (!b.opens.includes("gold")) {
        noTreatmentVisit.push(a.id);
        if (!a.opens.includes("gold")) strictNonvisitor.push(a.id);
      }
    }
  }
  return {
    changed_choices:changed.length, changed_paths:pathChanged.length, changed_first:firstChanged.length,
    changed_ids:changed, strict_nonvisitor_ids:strictNonvisitor,
    no_treatment_target_visit_ids:noTreatmentVisit,
    target_open_gain:treatment.traffic[2]-base.traffic[2],
    target_choices:[base.carts[2],treatment.carts[2]],
    paired_zero_sale:base.carts[2]===0 && treatment.carts[2]===0,
    ghost:base.carts[2]===0 && treatment.carts[2]===0 && treatment.traffic[2]>base.traffic[2] && changed.length>0
  };
}

function overlap(base, live, held) {
  const a = {live_only:[],held_only:[],both_same_destination:[],both_different_destination:[],neither:[],live_vs_held_changed:[]};
  for (let j = 0; j < 24; j++) {
    const b = base.shoppers[j], l = live.shoppers[j], h = held.shoppers[j];
    const lc = b.selected !== l.selected, hc = b.selected !== h.selected;
    if (lc && !hc) a.live_only.push(b.id);
    else if (hc && !lc) a.held_only.push(b.id);
    else if (lc && hc) a[l.selected===h.selected ? "both_same_destination" : "both_different_destination"].push(b.id);
    else a.neither.push(b.id);
    if (l.selected !== h.selected) a.live_vs_held_changed.push(b.id);
  }
  assert.equal(a.live_only.length+a.held_only.length+a.both_same_destination.length+a.both_different_destination.length+a.neither.length,24);
  return a;
}

function compact(world) {
  return {traffic:world.traffic,first:world.first,carts:world.carts,
    selected:world.shoppers.map(x => x.selected === null ? null : ix.get(x.selected)),
    opens:world.shoppers.map(x => x.opens.map(s => ix.get(s)))};
}
function checkAccounting(world) {
  assert.equal(world.traffic.reduce((a,b) => a+b,0),24*world.budget);
  assert.equal(world.first.reduce((a,b) => a+b,0),24);
  assert.equal(world.carts.reduce((a,b) => a+b,0),world.shoppers.filter(x => x.selected!==null).length);
  for (const s of world.shoppers) {
    assert.equal(new Set(s.opens).size,world.budget);
    assert.ok(s.selected===null || s.opens.includes(s.selected));
  }
}

const cases = [], witnesses = {};
let parityChecks = 0, accountingChecks = 0;
for (let seed = 1; seed <= 128; seed++) for (const budget of [1,2,3,6])
for (const cohort of ["mixed","focused"]) for (const reverse of [false,true]) {
  const base = M.simulate(seed,budget,false,true,cohort,reverse);
  const live = M.simulate(seed,budget,true,true,cohort,reverse);
  const history = priorHistory(base);
  assert.deepEqual(replay(seed,budget,false,true,cohort,reverse),base); parityChecks++;
  assert.deepEqual(replay(seed,budget,true,true,cohort,reverse),live); parityChecks++;
  assert.deepEqual(replay(seed,budget,false,true,cohort,reverse,history),base); parityChecks++;
  const held = replay(seed,budget,true,true,cohort,reverse,history);
  const offBase = M.simulate(seed,budget,false,false,cohort,reverse);
  const offPromoted = M.simulate(seed,budget,true,false,cohort,reverse);
  const comparisons = {live:compare(base,live),held:compare(base,held),off:compare(offBase,offPromoted)};
  assert.equal(comparisons.held.strict_nonvisitor_ids.length,0,"Held-history strict nonvisitor control");
  assert.equal(comparisons.off.strict_nonvisitor_ids.length,0,"Feedback-off strict nonvisitor control");
  if (budget===6) for (const c of Object.values(comparisons)) assert.equal(c.changed_choices,0,"Full-browse control");
  const paired = overlap(base,live,held);
  const countDifference = comparisons.live.changed_choices-comparisons.held.changed_choices;
  const row = {seed,budget,cohort,reverse,comparisons,live_minus_held_changed_choices:countDifference,
    overlap:paired,worlds:{base:compact(base),live:compact(live),held:compact(held),off_base:compact(offBase),off_promoted:compact(offPromoted)}};
  cases.push(row);
  for (const w of [base,live,held,offBase,offPromoted]) { checkAccounting(w); accountingChecks++; }
  const primary = cohort === "mixed" && [2,3].includes(budget);
  if (primary && countDifference < 0 && !witnesses.first_suppression) {
    witnesses.first_suppression = {...row,history_by_shopper:history,full_worlds:{base,live,held,offBase,offPromoted}};
  }
  if (primary && comparisons.live.strict_nonvisitor_ids.length && !witnesses.first_strict_nonvisitor) {
    witnesses.first_strict_nonvisitor = {...row,history_by_shopper:history,full_worlds:{base,live,held,offBase,offPromoted}};
  }
  if (seed===72 && budget===2 && cohort==="mixed" && !reverse) {
    witnesses.original_selected_case = {...row,history_by_shopper:history,full_worlds:{base,live,held,offBase,offPromoted}};
  }
}

function distribution(values) {
  const histogram = {};
  for (const v of values) histogram[v] = (histogram[v] || 0)+1;
  const sorted = values.slice().sort((a,b) => a-b), n = values.length;
  const mean = values.reduce((a,b) => a+b,0)/n;
  return {n,mean,min:sorted[0],max:sorted.at(-1),median:n%2?sorted[(n-1)/2]:(sorted[n/2-1]+sorted[n/2])/2,histogram};
}
function panel(rows) {
  const result = {cells:rows.length,shoppers_per_contrast:rows.length*24,contrasts:{}};
  for (const kind of ["live","held","off"]) {
    const cs = rows.map(x=>x.comparisons[kind]);
    result.contrasts[kind] = {
      changed_choices:distribution(cs.map(x=>x.changed_choices)),
      paired_zero_sale_cells:cs.filter(x=>x.paired_zero_sale).length,
      nonzero_target_choice_cells:cs.filter(x=>!x.paired_zero_sale).length,
      ghost_cells:cs.filter(x=>x.ghost).length,
      no_changed_choice_cells:cs.filter(x=>x.changed_choices===0).length,
      strict_nonvisitor_cells:cs.filter(x=>x.strict_nonvisitor_ids.length>0).length,
      strict_nonvisitor_changes:cs.reduce((a,x)=>a+x.strict_nonvisitor_ids.length,0),
      loose_no_treatment_visit_changes:cs.reduce((a,x)=>a+x.no_treatment_target_visit_ids.length,0),
      target_open_gain:distribution(cs.map(x=>x.target_open_gain)),
      target_baseline_choices_total:cs.reduce((a,x)=>a+x.target_choices[0],0),
      target_treatment_choices_total:cs.reduce((a,x)=>a+x.target_choices[1],0)
    };
  }
  result.live_vs_held = {
    more_changed_choices:rows.filter(x=>x.live_minus_held_changed_choices>0).length,
    equal_changed_choices:rows.filter(x=>x.live_minus_held_changed_choices===0).length,
    fewer_changed_choices:rows.filter(x=>x.live_minus_held_changed_choices<0).length,
    difference_distribution:distribution(rows.map(x=>x.live_minus_held_changed_choices)),
    live_only_changes:rows.reduce((a,x)=>a+x.overlap.live_only.length,0),
    held_only_changes:rows.reduce((a,x)=>a+x.overlap.held_only.length,0),
    both_same_destination:rows.reduce((a,x)=>a+x.overlap.both_same_destination.length,0),
    both_different_destination:rows.reduce((a,x)=>a+x.overlap.both_different_destination.length,0),
    same_count_different_shopper_choices_cells:rows.filter(x=>x.live_minus_held_changed_choices===0&&x.overlap.live_vs_held_changed.length>0).length
  };
  return result;
}

const primary = cases.filter(x=>x.cohort==="mixed" && [2,3].includes(x.budget));
assert.equal(cases.length,2048);
assert.equal(primary.length,512);
const summary = {
  record_id:"GOBLIN-HELD-HISTORY-2026-10-27-001",title:"When the Crowd Cancels the Advertisement",
  status:"EXPLORATORY_FINITE_MECHANISM_INTERVENTION_NO_MODEL_AGENTS",
  date:"2026-10-27",model_sha256:modelHash,model_git_blob:"41b2133712dec6bbdebf5a2246b921079f3ec57f",
  parent_public_head:"cee36657a2ce3c5cca00ff1308fa01b8f2213e67",
  plan_sha256:sha(fs.readFileSync(path.join(__dirname,"PROTOCOL.md"))),
  runner_sha256:sha(fs.readFileSync(__filename)),
  grid:{seeds:[1,128],budgets:[1,2,3,6],rosters:["mixed","focused"],arrival_orders:["forward","reverse"],cells:cases.length,
    worlds_per_cell:5,worlds_recorded:cases.length*5,scripted_shopper_executions_recorded:cases.length*5*24,
    paired_contrasts_per_cell:3,paired_contrasts:cases.length*3},
  checks:{original_live_world_full_parity:parityChecks-2048,held_neutral_history_full_parity:2048,
    total_full_world_parity:parityChecks,action_accounting_worlds:accountingChecks,
    blocked_propagation_strict_nonvisitor_controls:cases.length*2,
    full_browse_choice_invariance_contrasts:cases.filter(x=>x.budget===6).length*3,
    original_model_bytes_unchanged:sha(fs.readFileSync(modelFile))===modelHash},
  primary:panel(primary),all:panel(cases),groups:[],
  witnesses:Object.fromEntries(Object.entries(witnesses).map(([k,v])=>[k,{seed:v.seed,budget:v.budget,cohort:v.cohort,reverse:v.reverse,
    live_changed:v.comparisons.live.changed_choices,held_changed:v.comparisons.held.changed_choices,
    off_changed:v.comparisons.off.changed_choices,live_strict_nonvisitor_ids:v.comparisons.live.strict_nonvisitor_ids,
    live_only:v.overlap.live_only,held_only:v.overlap.held_only,both_different:v.overlap.both_different_destination} ])),
  hypotheses:{no_universal_amplification_in_primary:primary.some(x=>x.live_minus_held_changed_choices<0),
    strict_nonvisitor_route_exists_in_primary:primary.some(x=>x.comparisons.live.strict_nonvisitor_ids.length>0),
    no_strict_nonvisitor_changes_in_blocked_controls:cases.every(x=>x.comparisons.held.strict_nonvisitor_ids.length===0&&x.comparisons.off.strict_nonvisitor_ids.length===0),
    all_full_browse_choices_invariant:cases.filter(x=>x.budget===6).every(x=>Object.values(x.comparisons).every(c=>c.changed_choices===0))},
  limits:{exploratory_after_inspection_of_selected_parent_example:true,independent_validation:false,
    probability_sample:false,fresh_seed_panel:false,model_agents:0,human_participants:0,real_purchases:0,
    additive_mediation_decomposition:false,
    interpretation:"Finite within-generator interventions; no prevalence or causal-effect estimate for real shoppers or LLM agents."}
};
for (const budget of [1,2,3,6]) for (const cohort of ["mixed","focused"]) for (const reverse of [false,true]) {
  summary.groups.push({budget,cohort,reverse,...panel(cases.filter(x=>x.budget===budget&&x.cohort===cohort&&x.reverse===reverse))});
}
fs.mkdirSync(outputDir,{recursive:true});
const raw = {record_id:summary.record_id,status:summary.status,model_sha256:modelHash,
  encoding:{shop_indices:ids,shopper_rows:"Ascending shopper ID 1–24; null is a deferral.",
    worlds:{base:"Neutral / live feedback",live:"Promoted / live feedback",held:"Promoted / held neutral prior-visit display",
      off_base:"Neutral / feedback off",off_promoted:"Promoted / feedback off"}},cases};
const rawBytes=Buffer.from(JSON.stringify(raw));
fs.writeFileSync(path.join(outputDir,"grid-records.json"),rawBytes);
summary.raw_sha256=sha(rawBytes);
summary.raw_size_bytes=rawBytes.length;
fs.writeFileSync(path.join(outputDir,"summary.json"),JSON.stringify(summary,null,2)+"\n");
fs.writeFileSync(path.join(outputDir,"witnesses.json"),JSON.stringify(witnesses,null,2)+"\n");
const hashes=["grid-records.json","summary.json","witnesses.json"].map(f=>sha(fs.readFileSync(path.join(outputDir,f)))+"  "+f).join("\n")+"\n";
fs.writeFileSync(path.join(outputDir,"SHA256SUMS.txt"),hashes);
process.stdout.write(JSON.stringify({record_id:summary.record_id,grid:summary.grid,checks:summary.checks,
  primary:summary.primary,witnesses:summary.witnesses,hypotheses:summary.hypotheses,raw_size_bytes:summary.raw_size_bytes},null,2)+"\n");
