/* Dependency-free package checks. These do not replace a browser rendering test. */
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const assert = require("node:assert/strict");
const root = path.resolve(__dirname, "..");
const full = JSON.parse(fs.readFileSync(path.join(root, "results/full-results.json"), "utf8"));
let scripts = 0, links = 0;
for (const name of ["index.html", "method.html"]) {
  const html = fs.readFileSync(path.join(root, name), "utf8");
  const ids = [...html.matchAll(/\bid="([^"]+)"/g)].map(m => m[1]);
  assert.equal(ids.length, new Set(ids).size, `${name}: duplicate IDs`);
  for (const match of html.matchAll(/<script([^>]*)>([\s\S]*?)<\/script>/g)) {
    if (match[1].includes('type="application/json"')) {
      const data = JSON.parse(match[2]);
      const expected = { ...full };
      delete expected.grid;
      assert.deepEqual(data, expected);
    } else {
      new vm.Script(match[2]);
      for (const id of match[2].matchAll(/\$\("([^"]+)"\)/g)) assert.ok(ids.includes(id[1]), `Missing DOM ID: ${id[1]}`);
      scripts++;
    }
  }
  for (const [, href] of html.matchAll(/\bhref="([^"]+)"/g)) {
    if (/^(?:https?:|#)/.test(href)) continue;
    assert.ok(fs.existsSync(path.resolve(root, href)), `Missing target: ${href}`);
    links++;
  }
  assert.ok(html.includes("<main>"));
  assert.ok(!html.includes("__RESULTS_JSON__"));
  assert.ok(!/<script[^>]*\bsrc=|@import|https?:\/\//.test(html), "Unexpected remote runtime dependency");
}
assert.equal(full.external_model_runs, 0);
assert.equal(full.boundary_false_allows, 2);
process.stdout.write(JSON.stringify({result:"PASS", compiled_inline_scripts:scripts, checked_relative_links:links,
  embedded_data_matches_full_record:true, duplicate_ids:0, remote_runtime_dependencies:0}, null, 2) + "\n");
