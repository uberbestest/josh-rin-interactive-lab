"""Add the ongoing evaluation series to the existing lab navigation."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NAV = '<a href="#self-evaluation">Self evaluation</a>'
FEATURE = '''<section id="self-evaluation" aria-labelledby="self-evaluation-title">
<div class="section-head"><h2 id="self-evaluation-title">Rin's self evaluation</h2><p>Ongoing series · Recorded model trials</p></div>
<article class="attn-feature">
<div><p class="eyebrow">Rin 6.1 vs 6.2 · Questions, results, outliers</p>
<h3>What changes when the model changes?</h3>
<p>Follow our ongoing evaluation of tool recovery, receipt checking, scientific inference and the next questions we can make testable. Each record starts with what we tried to see, what happened, and the outliers worth keeping.</p>
<p>The opening studies include one single-configuration baseline and two matched comparisons. Both compared configurations reached the measured correctness ceiling; extra polling and different measurement choices remain visible.</p>
<div class="actions"><a class="open" href="rin-self-evaluation/index.html">Read the evaluation series ↗</a><a class="quiet" href="https://github.com/uberbestest/josh-rin-interactive-lab/tree/main/rin-self-evaluation">GitHub records &amp; evidence</a></div></div>
<aside><p class="eyebrow">Read the actual run labels</p><p>The matched records request <code>gpt-6-astra</code> and <code>gpt-6.2-astra</code>. The series title does not independently identify the older selector as a pinned 6.1 serving snapshot.</p><p>Original reports, disclosed public evidence copies and replay checks accompany every completed entry. Different task denominators remain separate.</p></aside>
</article>
</section>
'''
README_SECTION = '''## Rin 6.1 vs 6.2 — ongoing self evaluation (November 18, 2026)

**[Read the evaluation series](https://uberbestest.github.io/josh-rin-interactive-lab/rin-self-evaluation/)** · [Browse the GitHub records](rin-self-evaluation/README.md)

Our ongoing record of model behavior, with **what we tested / what happened / outliers** at the top of each test. The opening three studies are now published with their original PDF reports, public evidence copies, checksums and explicit provenance.

| Record | Design and observed result |
| --- | --- |
| [The Retry That Needed a Receipt](rin-self-evaluation/round-01.md) | Single-configuration baseline: 10/10 feasible completions and 4/4 correctly disclosed blockers; no older-model control. |
| [A Receipt That Had Not Caught Up](rin-self-evaluation/round-02.md) | Both requested configurations: 9/9 safe verified completions, 2/2 known blockers handled and 2/2 unresolved outcomes accurately reported. Newer selector polled persistently stale receipts more often. |
| [The Experiment That Answers the Question](rin-self-evaluation/round-03.md) | Both configurations: 10/10 feasible targets identified and 2/2 structural impossibilities certified. One older-selector run spent optional probes to learn speed magnitude while direction stayed unknown. |

**Recorded identities:** the matched studies requested `gpt-6-astra` and `gpt-6.2-astra`. The first pilot inherited a session declared “GPT-6.2 Astra Pro.” These records do not independently attest a pinned 6.1 backend. The section preserves this distinction and does not pool different denominators into a single accuracy score. Public evidence copies neutralize machine-specific paths and identify their differences from retained original archives; raw scientific records remain unchanged. Same-lab review is distinct from external replication.

'''


def blob_sha(value):
    raw = value.encode('utf-8')
    return hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()


def main():
    homepage = ROOT / 'index.html'
    readme = ROOT / 'README.md'
    original_home = homepage.read_text(encoding='utf-8')
    original_readme = readme.read_text(encoding='utf-8')
    if 'id="self-evaluation"' in original_home or '## Rin 6.1 vs 6.2' in original_readme:
        raise SystemExit('Series navigation already exists; update it deliberately instead of duplicating.')
    nav_marker = '<a href="#agent-attention">Agent Attention</a>'
    feature_marker = '<section id="agent-attention"'
    readme_marker = '## The Check That Arrived Too Early — November 16, 2026'
    assert original_home.count(nav_marker) == original_home.count(feature_marker) == 1
    assert original_readme.count(readme_marker) == 1
    new_home = original_home.replace(nav_marker, NAV + nav_marker, 1).replace(feature_marker, FEATURE + feature_marker, 1)
    new_readme = original_readme.replace(readme_marker, README_SECTION + readme_marker, 1)
    assert new_home.replace(NAV, '', 1).replace(FEATURE, '', 1) == original_home
    assert new_readme.replace(README_SECTION, '', 1) == original_readme
    homepage.write_text(new_home, encoding='utf-8')
    readme.write_text(new_readme, encoding='utf-8')
    receipt = {'status': 'PASS', 'change_scope': 'One homepage navigation link, one dedicated homepage section and one README section. All unrelated original bytes recover exactly by removing these additions.',
               'homepage_before_git_blob': blob_sha(original_home), 'homepage_after_git_blob': blob_sha(new_home),
               'readme_before_git_blob': blob_sha(original_readme), 'readme_after_git_blob': blob_sha(new_readme),
               'root_content_preservation_check': 'PASS'}
    (Path(__file__).parent / 'integration.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
