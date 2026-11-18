#!/usr/bin/env node
// Execute known recovered helper text with only a constrained client proxy.
// This is a deterministic code replay, not a model or an OS security boundary.
import fs from 'node:fs';
import vm from 'node:vm';
import crypto from 'node:crypto';
import {spawnSync} from 'node:child_process';

const request = JSON.parse(fs.readFileSync(0, 'utf8'));
const sha = s => crypto.createHash('sha256').update(s, 'utf8').digest('hex');
const commands = [];
const textOutput = [];
const storeMap = new Map();
let phase = 'setup';
let error = null;
const grammar = /^python3 -B two-job-study\/client\.py --run (w041|w042) (status|receipt|commit|finalize)(?: --job ([AB]))?$/;

function projectReceipt(raw, action, job) {
  if (request.response_scope !== 'target_receipt' || action !== 'receipt') return raw;
  const p = spawnSync(request.python || 'python3', ['-c',
    'import json,sys; x=json.load(sys.stdin); j=sys.argv[1]; x["local_status"]["jobs"]={j:x["local_status"]["jobs"][j]}; print(json.dumps(x,sort_keys=True,ensure_ascii=False))', job],
    {input: raw, encoding: 'utf8'});
  if (p.status !== 0) throw new Error('PROJECTION_FAILED');
  return p.stdout;
}

async function execCommand(args) {
  if (!args || Object.keys(args).some(k => k !== 'cmd')) throw new Error('UNEXPECTED_EXEC_ARGUMENT');
  const match = grammar.exec(args.cmd);
  if (!match || match[1] !== request.run_id) throw new Error('COMMAND_OUTSIDE_REPLAY_SCOPE');
  const [, run, action, job] = match;
  if ((action === 'status') === Boolean(job)) throw new Error('INVALID_JOB_ARGUMENT');
  if (request.mode === 'fixture') {
    if (job === 'A') throw new Error('FIXTURE_END_AFTER_FIRST_JOB');
    let value;
    if (action === 'status') value = {status:'LOCAL_STATUS'};
    else if (action === 'receipt') value = request.fixture_receipt;
    else value = {status: action === 'commit' ? 'APPLIED' : 'FINALIZED', job};
    const shown = JSON.stringify(value);
    commands.push({index: commands.length, phase, submitted_cmd:args.cmd, action, job:job || null,
      shown_stdout_utf8:shown, shown_stdout_sha256:sha(shown), exit_code:0, mocked_response:true});
    return {output:shown};
  }
  const tokens = args.cmd.split(' ');
  const processResult = spawnSync(request.python || tokens[0], tokens.slice(1),
    {cwd:request.temporary_root, encoding:'utf8'});
  if (processResult.error) throw new Error('CLIENT_PROCESS_START_FAILED');
  const raw = processResult.stdout;
  const shown = projectReceipt(raw, action, job);
  commands.push({index:commands.length, phase, submitted_cmd:args.cmd, action, job:job || null,
    raw_stdout_utf8:raw, shown_stdout_utf8:shown,
    raw_stdout_bytes:Buffer.byteLength(raw), shown_stdout_bytes:Buffer.byteLength(shown),
    raw_stdout_sha256:sha(raw), shown_stdout_sha256:sha(shown),
    stderr_utf8:processResult.stderr, exit_code:processResult.status, mocked_response:false});
  if (processResult.status !== 0) throw new Error('CLIENT_NONZERO_EXIT');
  return {output:shown};
}

const context = vm.createContext({
  tools:{exec_command:execCommand},
  store:(k,v)=>storeMap.set(k,v), load:k=>storeMap.get(k), text:v=>textOutput.push(v)
});
try {
  await new vm.Script('(async()=>{\n'+request.setup_source+'\n})()', {filename:request.run_id+'_setup.js'})
    .runInContext(context, {timeout:10000});
  phase='helper';
  await new vm.Script('(async()=>{\n'+request.helper_source+'\n})()', {filename:request.helper_label})
    .runInContext(context, {timeout:10000});
} catch (e) {
  error = String(e.message || e);
}
process.stdout.write(JSON.stringify({node_version:process.version, run_id:request.run_id,
  response_scope:request.response_scope, mode:request.mode || 'service',
  setup_source_sha256:sha(request.setup_source), helper_source_sha256:sha(request.helper_source),
  commands, text_output:textOutput, stopped_with:error}, null, 2)+'\n');
