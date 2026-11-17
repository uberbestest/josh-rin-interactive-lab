'use strict';
const fs=require('fs'),zlib=require('zlib'),assert=require('assert/strict');
const lab=require('./explorer.js');
const rows=zlib.gunzipSync(fs.readFileSync('results/traces.jsonl.gz')).toString().trim().split('\n').map(JSON.parse);
for(const row of rows){assert.deepStrictEqual(lab.simulate(row.schedule,row.lag,row.policy,row.enforcement),row);}
console.log(JSON.stringify({status:'PASS',complete_trace_parity:rows.length,implementations:'Python and JavaScript, same author'}));
