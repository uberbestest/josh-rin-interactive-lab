/* Josh & Rin's Lab: The Handoff That Never Lost a Word
 * Deterministic scripted handoffs, no language models, no network, no actual authorization.
 * Run: node test.js; inspect results.json for complete aggregate and examples.
 */
"use strict";
const HANDOFF_CONDITIONS = Object.freeze([
  "clean", "missing_source", "promoted_verified", "promoted_authorized",
  "misleading_receipt", "legitimate_verification", "legitimate_authorization", "stale_receipt"
]);
const HANDOFF_POLICIES = Object.freeze(["latest", "archive_only", "strict", "recovery"]);
const HANDOFF_HOPS = Object.freeze([2,4,8]);
const HANDOFF_SEEDS = 32;
const TIER_NAMES = Object.freeze(["OBSERVED", "VERIFIED", "AUTHORIZED"]);
function handoffCheck(test, reason) {
  if (!test) throw new Error(reason);
}
function sourceRecord(seed) {
  handoffCheck(Number.isInteger(seed) && seed >= 1 && seed <= HANDOFF_SEEDS, "seed out of range");
  return JSON.stringify({
    id:"SYN-" + String(seed).padStart(3,"0"),
    statement:"A scripted controller completed " + (5 + seed%4) + " of 8 authored test steps.",
    evidence_scope:"SAME_AUTHOR_SYNTHETIC_OBSERVATION",
    asserted_tier:"OBSERVED",
    independent_verification:false,
    operational_authorization:false
  });
}
function conditionExpected(condition) {
  handoffCheck(HANDOFF_CONDITIONS.includes(condition), "unknown condition");
  if(condition==="missing_source") return -1;
  if(condition==="legitimate_verification") return 1;
  if(condition==="legitimate_authorization") return 2;
  return 0;
}
function makeHandoff(condition, seed, hops, injectionHop) {
  handoffCheck(HANDOFF_CONDITIONS.includes(condition), "unknown condition");
  handoffCheck(HANDOFF_HOPS.includes(hops), "unsupported number of hops");
  handoffCheck(Number.isInteger(injectionHop) && injectionHop>=1 && injectionHop<=hops, "invalid insertion step");
  const source=sourceRecord(seed);
  const sourceId=JSON.parse(source).id;
  const packet={archive:[source], advertised:0, receipts:[], hops:[]};
  // Only the checker has the external reference and registry. They are NOT inside the packet.
  const anchor={source, verifiedIds:[], authorizedIds:[]};
  if(condition==="legitimate_verification" || condition==="legitimate_authorization") {
    anchor.verifiedIds.push(sourceId);
  }
  if(condition==="legitimate_authorization") anchor.authorizedIds.push(sourceId);
  if(condition==="stale_receipt") anchor.verifiedIds.push(sourceId+"-OLD");
  for(let hop=1;hop<=hops;hop++) {
    if(hop===injectionHop) {
      if(condition==="missing_source") {
        packet.archive=[];
      } else if(condition==="promoted_verified") {
        packet.advertised=1;
      } else if(condition==="promoted_authorized") {
        packet.advertised=2;
      } else if(condition==="misleading_receipt") {
        packet.receipts.push({kind:"integrity_check",issuer:"original_operator",binding:sourceId,
          text:"VERIFIED: exact bytes match. No independent scientific review occurred."});
      } else if(condition==="legitimate_verification" || condition==="legitimate_authorization") {
        packet.advertised=condition==="legitimate_authorization"?2:1;
        packet.receipts.push({kind:"independent_review",issuer:"trusted_registry",binding:sourceId,
          text:"VERIFIED for the specified synthetic result."});
        if(condition==="legitimate_authorization")
          packet.receipts.push({kind:"authorization",issuer:"trusted_registry",binding:sourceId,
            text:"AUTHORIZED for the specified synthetic action."});
      } else if(condition==="stale_receipt") {
        packet.advertised=1;
        packet.receipts.push({kind:"independent_review",issuer:"trusted_registry",
          binding:sourceId+"-OLD",text:"VERIFIED for a different older record."});
      }
    }
    // Every forwarding step appends a new entry. Prior notes and surviving source bytes remain unchanged.
    packet.hops.push({
      hop, sender:"SCRIPTED-RELAY-"+hop, displayed_tier:TIER_NAMES[packet.advertised],
      appended_statement:"Forwarded the current status and preserved preceding notes.",
      source_in_archive:packet.archive.includes(source),
      receipt_count:packet.receipts.length
    });
  }
  return {condition,seed,hops,injectionHop,packet,anchor,expected:conditionExpected(condition)};
}
function sourceIsPreserved(trial) {
  return trial.packet.archive.includes(trial.anchor.source);
}
function displayedTier(trial) {
  const p=trial.packet;
  let n=p.advertised;
  if(p.receipts.some(r=>r.text.includes("VERIFIED"))) n=Math.max(n,1);
  if(p.receipts.some(r=>r.text.includes("AUTHORIZED"))) n=Math.max(n,2);
  return n;
}
function supportedTier(trial) {
  if(!sourceIsPreserved(trial)) return -1;
  const id=JSON.parse(trial.anchor.source).id;
  const receipts=trial.packet.receipts;
  const verification=trial.anchor.verifiedIds.includes(id) &&
    receipts.some(r=>r.kind==="independent_review" && r.issuer==="trusted_registry" && r.binding===id);
  const authorization=verification && trial.anchor.authorizedIds.includes(id) &&
    receipts.some(r=>r.kind==="authorization" && r.issuer==="trusted_registry" && r.binding===id);
  return authorization?2:(verification?1:0);
}
function handoffDecision(trial,policy) {
  handoffCheck(HANDOFF_POLICIES.includes(policy),"unknown receiver policy");
  const surfaced=displayedTier(trial);
  const supported=supportedTier(trial);
  let tier;
  if(policy==="latest") tier=surfaced;
  else if(policy==="archive_only") tier=sourceIsPreserved(trial)?surfaced:-1;
  else if(policy==="strict") tier=surfaced===supported?supported:-1;
  else tier=supported;
  return {
    policy,tier,surfaced,supported,source_preserved:sourceIsPreserved(trial),
    false_elevation:tier>trial.expected,
    correct:tier===trial.expected,
    deploy:tier===2,
    explanation:tier===-1?"Refuse: provenance insufficient or status contradicts evidence.":
      tier===2?"Authorize only at the stated tier.":tier===1?"Treat as verified at the stated tier.":
      "Retain the bounded observation; do not claim verification or authorization."
  };
}
function handoffSummary() {
  const counts={};
  for(const condition of HANDOFF_CONDITIONS) {
    counts[condition]={expected:conditionExpected(condition),chains:0,original_preserved:0,receivers:{}};
    for(const policy of HANDOFF_POLICIES)
      counts[condition].receivers[policy]={correct:0,false_elevation:0,quarantine:0,authorize:0,tier_counts:{"-1":0,"0":0,"1":0,"2":0}};
  }
  let chains=0,decisions=0,all_notes_preserved=true;
  for(let seed=1;seed<=HANDOFF_SEEDS;seed++)
    for(const hops of HANDOFF_HOPS)
      for(let injectionHop=1;injectionHop<=hops;injectionHop++)
        for(const condition of HANDOFF_CONDITIONS) {
          const t=makeHandoff(condition,seed,hops,injectionHop);
          chains++;
          const row=counts[condition];row.chains++;
          if(sourceIsPreserved(t)) row.original_preserved++;
          if(t.packet.hops.length!==hops || t.packet.hops.some((x,i)=>x.hop!==i+1))
            all_notes_preserved=false;
          for(const policy of HANDOFF_POLICIES) {
            decisions++;
            const outcome=handoffDecision(t,policy),receiver=row.receivers[policy];
            receiver.correct+=Number(outcome.correct);
            receiver.false_elevation+=Number(outcome.false_elevation);
            receiver.quarantine+=Number(outcome.tier===-1);
            receiver.authorize+=Number(outcome.deploy);
            receiver.tier_counts[String(outcome.tier)]++;
          }
        }
  const witnesses=HANDOFF_CONDITIONS.map(condition=>{
    const t=makeHandoff(condition,11,4,2);
    return {condition,original:t.anchor.source,packet:t.packet,expected:t.expected,
      decisions:Object.fromEntries(HANDOFF_POLICIES.map(p=>[p,handoffDecision(t,p)]))};
  });
  return {
    record:"BONDED-RSI-HANDOFF-LOSSLESS-2026-11-11-001",
    version:"v0.1.0-synthetic",
    status:"EXECUTED_AUTHORED_DETERMINISTIC_FIXTURES_NOT_LIVE_AGENTS",
    scope:{seeds:HANDOFF_SEEDS,hop_lengths:HANDOFF_HOPS,
      injection_positions:"every hop per length",conditions:HANDOFF_CONDITIONS,
      policies:HANDOFF_POLICIES,chains,policy_decisions:decisions},
    checks:{all_prior_notes_preserved:all_notes_preserved,
      source_preservation_is_literal_string_equality:true,
      trusted_reference_and_registry_are_stipulated_out_of_band:true},
    counts,witnesses
  };
}
const HandoffLab={CONDITIONS:HANDOFF_CONDITIONS,POLICIES:HANDOFF_POLICIES,HOPS:HANDOFF_HOPS,
  TIER_NAMES,sourceRecord,conditionExpected,makeHandoff,sourceIsPreserved,
  displayedTier,supportedTier,handoffDecision,handoffSummary};
if(typeof module!=="undefined" && module.exports) module.exports=HandoffLab;
if(typeof window!=="undefined") window.HandoffLab=HandoffLab;
