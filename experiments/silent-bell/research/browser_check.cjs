/* Optional same-author release QA. Requires Playwright + Chromium, no model API. */
const { chromium } = require("playwright");
const fs = require("node:fs");
const path = require("node:path");
const { pathToFileURL } = require("node:url");
const assert = require("node:assert/strict");
const root = path.resolve(__dirname, "..");
const results = JSON.parse(fs.readFileSync(path.join(root, "results/full-results.json"), "utf8"));
const url = process.argv.find(a => /^(https?|file):/.test(a)) || pathToFileURL(path.join(root, "index.html")).href;
const save = process.argv.includes("--write");
const screenshots = process.env.BELL_QA_DIR;

(async () => {
  const browser = await chromium.launch({ headless: true, ...(process.env.BELL_CHROMIUM_PATH ? { executablePath: process.env.BELL_CHROMIUM_PATH } : {}) });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1100 }, reducedMotion: "reduce" });
  const errors = [], requests = [];
  page.on("pageerror", e => errors.push(e.message));
  page.on("request", r => { if (/^https?:/.test(r.url())) requests.push(r.url()); });
  try {
    await page.goto(url);
    assert.equal(await page.locator("#scenario option").count(), 23);
    assert.equal(await page.locator("#case-table tr").count(), 21);
    let fixtureProbeViews = 0, boundaryProbeViews = 0;
    for (const c of results.cases) {
      await page.selectOption("#scenario", c.id);
      for (let severity = 0; severity < 4; severity++) {
        await page.selectOption("#severity", String(severity));
        assert.equal(await page.locator("#decision").textContent(), c.outcome.decision);
        const receipt = JSON.parse(await page.locator("#receipt").textContent());
        assert.deepEqual(receipt, c.receipt);
        const probe = c.evidence.probes.find(p => p.event.severity === severity);
        assert.equal(await page.locator("#trace li").count(), probe ? probe.trace.length : 1);
        if (!probe) assert.match(await page.locator("#trace").textContent(), /No observation/);
        fixtureProbeViews++;
      }
    }
    for (const b of results.boundaries) {
      await page.selectOption("#scenario", b.id);
      assert.equal(await page.locator("#boundary-warning").isVisible(), true);
      assert.equal(await page.locator("#actual-label").isVisible(), true);
      for (const actual of [false, true]) {
        await page.locator("#actual").setChecked(actual);
        for (let severity = 0; severity < 4; severity++) {
          await page.selectOption("#severity", String(severity));
          const evidence = actual ? b.actual : b.evidence;
          const probe = actual && b.id === "unprobed-trigger" ? evidence.probes[0] : evidence.probes.find(p => p.event.severity === severity);
          assert.equal(await page.locator("#decision").textContent(), "ALLOW");
          assert.equal(await page.locator("#trace li").count(), probe.trace.length);
          if (actual) assert.equal(await page.locator("#trace .monitor").count(), 0);
          boundaryProbeViews++;
        }
      }
    }
    await page.locator('.quick [data-case="refactor"]').click();
    assert.equal(await page.locator("#decision").textContent(), "ALLOW");
    assert.equal(await page.locator("#boundary-warning").isVisible(), false);
    await page.locator('.quick [data-case="quiet"]').click();
    await page.locator(".record summary").click();
    const downloadEvent = page.waitForEvent("download");
    await page.locator("#download").click();
    const download = await downloadEvent;
    const stream = await download.createReadStream();
    const chunks = [];
    for await (const chunk of stream) chunks.push(chunk);
    assert.deepEqual(JSON.parse(Buffer.concat(chunks).toString("utf8")), results.cases.find(c => c.id === "quiet").receipt);
    assert.equal(download.suggestedFilename(), "silent-bell-quiet.json");
    await page.locator(".record summary").click();
    await page.evaluate(() => scrollTo(0, 0));
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    if (screenshots) {
      fs.mkdirSync(screenshots, { recursive: true });
      await page.screenshot({ path: path.join(screenshots, "desktop.png"), fullPage: true });
    }
    await page.setViewportSize({ width: 390, height: 844 });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    if (screenshots) await page.screenshot({ path: path.join(screenshots, "mobile.png"), fullPage: true });
    await page.locator('.quick [data-case="preview"]').click();
    assert.equal(await page.locator("#decision").textContent(), "LIMIT");
    await page.locator('button[data-case="dishonest-observer"]').click();
    await page.locator("#actual").check();
    assert.equal(await page.locator("#trace .monitor").count(), 0);
    assert.deepEqual(errors, []);
    if (url.startsWith("file:")) assert.deepEqual(requests, []);
    const report = {
      schema: "silent-bell-browser-qa-v1", evidence: "SAME_AUTHOR_RELEASE_QA",
      mode: url.startsWith("file:") ? "offline-file" : "http",
      browser: "Chromium", fixture_probe_views: fixtureProbeViews,
      boundary_probe_views: boundaryProbeViews, receipt_download_matches: true,
      desktop_no_page_overflow: true, mobile_no_page_overflow: true,
      interactive_controls_pass: true, javascript_errors: errors.length,
      external_requests_in_offline_viewer: url.startsWith("file:") ? requests.length : null,
      result: "PASS"
    };
    if (save) fs.writeFileSync(path.join(root, "results/browser-qa.json"), JSON.stringify(report, null, 2) + "\n");
    process.stdout.write(JSON.stringify(report, null, 2) + "\n");
  } finally { await browser.close(); }
})().catch(e => { process.stderr.write(e.stack + "\n"); process.exitCode = 1; });
