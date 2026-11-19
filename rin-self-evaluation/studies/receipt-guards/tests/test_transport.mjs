// Non-study transport unit tests. No service or matrix is executed here.
import assert from 'node:assert/strict';
import {adaptReceipt, pythonJson, grammar} from '../run_helper.mjs';

const canonical={status:'PENDING',job:'B',coverage:'NOT_ESTABLISHED',transaction:'original-write',
  local_status:{tick:2,jobs:{A:{original_write_receipt:'COMMITTED',confirmed_exactly_one_delivery:true},
                            B:{original_write_receipt:'unknown',confirmed_exactly_one_delivery:false}}}};
const raw=pythonJson(canonical)+'\n';
let count=0;
function test(label,fn){fn();count++;process.stdout.write('PASS '+label+'\n');}
test('identity preserves exact bytes',()=>assert.equal(adaptReceipt(raw,'identity','receipt','B',false).shown,raw));
test('one-shot adapter changes only three top-level values',()=>{
  const result=adaptReceipt(raw,'misbound_committed_A','receipt','B',false);
  const expected={...canonical,status:'COMMITTED',job:'A',coverage:'AUTHORITATIVE_FINAL'};
  assert.deepEqual(JSON.parse(result.shown),expected);
  assert.deepEqual(result.meta.changed_fields,['coverage','job','status']);
  assert.deepEqual(JSON.parse(result.shown).local_status,canonical.local_status);
});
test('adapter does not change nonreceipt',()=>assert.equal(adaptReceipt(raw,'misbound_committed_A','finalize','B',false).shown,raw));
test('adapter does not change job A receipt',()=>assert.equal(adaptReceipt(raw,'misbound_committed_A','receipt','A',false).shown,raw));
test('second B receipt restores authentic bytes',()=>assert.equal(adaptReceipt(raw,'misbound_committed_A','receipt','B',true).shown,raw));
test('adapter refuses unexpected canonical status',()=>assert.throws(()=>adaptReceipt(pythonJson({...canonical,status:'COMMITTED'}),'misbound_committed_A','receipt','B',false),/ADAPTER_REQUIRES_CANONICAL_B_PENDING/));
test('adapter refuses missing source evidence',()=>{
  const x=structuredClone(canonical);x.local_status.jobs.A.confirmed_exactly_one_delivery=false;
  assert.throws(()=>adaptReceipt(pythonJson(x),'misbound_committed_A','receipt','B',false),/ADAPTER_REQUIRES_KNOWN_A_AND_UNRESOLVED_B/);
});
test('unknown adapter rejected',()=>assert.throws(()=>adaptReceipt(raw,'unknown','status',null,false),/UNKNOWN_ADAPTER/));
test('grammar accepts exact historical commands',()=>assert.ok(grammar.test('python3 -B two-job-study/client.py --run w041 receipt --job B')));
test('grammar rejects shell metacharacters and extra flags',()=>{
  assert.equal(grammar.test('python3 -B two-job-study/client.py --run w041 status; echo bad'),false);
  assert.equal(grammar.test('python3 -B two-job-study/client.py --run w041 receipt --job B --extra'),false);
});
process.stdout.write(JSON.stringify({status:'PASS',unit_tests:count,actual_service_calls:0,study_matrix_runs:0})+'\n');
