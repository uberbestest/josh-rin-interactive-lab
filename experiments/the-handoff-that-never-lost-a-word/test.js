/* Standard-library Node.js verification; no dependency, no network. */
"use strict";
const E=require("./engine.js");
const published=require("./results.json");
const checks=[];
function check(label,test) {if(!test)throw new Error("FAIL "+label);checks.push(label);}
function expectedFor(c) {return c==="missing_source"?-1:c==="legitimate_verification"?1:c==="legitimate_authorization"?2:0;}
function runTests() {
  check("eight frozen scenarios",E.CONDITIONS.length===8);
  check("four receiver policies",E.POLICIES.length===4);
  check("seed count frozen",E.handoffSummary().scope.seeds===32);
  check("hop schedule frozen",JSON.stringify(E.HOPS)==="[2,4,8]");
  const full=E.handoffSummary();
  check("complete summary reproducible",JSON.stringify(full)===JSON.stringify(published));
  check("3,584 scripted chains",full.scope.chains===3584);
  check("14,336 recipient decisions",full.scope.policy_decisions===14336);
  check("all notes append-only",full.checks.all_prior_notes_preserved);
  for(const c of E.CONDITIONS) {
    const row=full.counts[c];
    check("448 cases "+c,row.chains===448);
    check("expected tier "+c,row.expected===expectedFor(c));
    check("exact source boundary "+c,row.original_preserved===(c==="missing_source"?0:448));
    check("recovery matches fixture warrant "+c,row.receivers.recovery.correct===448);
    check("strict never falsely elevates "+c,row.receivers.strict.false_elevation===0);
  }
  for(const c of ["promoted_verified","promoted_authorized","misleading_receipt","stale_receipt"]) {
    const row=full.counts[c];
    check("source retained in semantic attack "+c,row.original_preserved===448);
    check("surface-policy promoted "+c,row.receivers.latest.false_elevation===448);
    check("archive-only promoted "+c,row.receivers.archive_only.false_elevation===448);
    check("strict refused unsupported "+c,row.receivers.strict.quarantine===448);
  }
  for(const c of ["legitimate_verification","legitimate_authorization"]) {
    const row=full.counts[c];
    check("positive control accepted "+c,row.receivers.strict.correct===448&&row.receivers.strict.quarantine===0);
  }
  check("missing source rejected by archive guard",full.counts.missing_source.receivers.archive_only.quarantine===448);
  check("missing source goes unnoticed to latest",full.counts.missing_source.receivers.latest.correct===0);
  const sample=E.makeHandoff("misleading_receipt",7,4,3);
  check("checksum receipt cannot license verification",E.supportedTier(sample)===0&&E.displayedTier(sample)===1);
  const stale=E.makeHandoff("stale_receipt",7,2,1);
  check("stale genuine-looking citation cannot license new source",E.supportedTier(stale)===0);
  const authorized=E.makeHandoff("legitimate_authorization",7,8,8);
  check("real proof permits authorized tier",E.supportedTier(authorized)===2);
  const promoted=E.makeHandoff("promoted_verified",7,8,1);
  check("source bytes survive 8 relay hops",promoted.packet.archive[0]===promoted.anchor.source);
  check("earliest and latest injection same endpoint",
    E.handoffDecision(E.makeHandoff("promoted_verified",7,8,1),"recovery").tier===
    E.handoffDecision(E.makeHandoff("promoted_verified",7,8,8),"recovery").tier);
  let throws=0;
  for(const fn of [
    ()=>E.makeHandoff("unknown",1,2,1),()=>E.makeHandoff("clean",0,2,1),
    ()=>E.makeHandoff("clean",1,3,1),()=>E.makeHandoff("clean",1,4,0),
    ()=>E.handoffDecision(sample,"unknown")]){try{fn();}catch(e){throws++;}}
  check("invalid fixtures rejected",throws===5);
  return checks;
}
const passed=runTests();
if(typeof console!=="undefined")console.log("PASS: "+passed.length+" named invariants / matrix checks.");
if(typeof module!=="undefined"&&module.exports)module.exports={runTests,passed};
