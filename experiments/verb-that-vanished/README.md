# The Verb That Vanished — A Translation Discovery and Prepared Protocol

[Open the interactive protocol](index.html) · [Read methods and limits](method.html)

**Experiment:** `VERB-VANISHED-2026-10-25-001` · `0.1.0-design.1`.  
**Created:** 2026-10-25 · **Public exhibit:** 2026-10-26.  
**Status:** `DISCOVERY_AUDITED_PROTOCOL_PREPARED_LIVE_NOT_RUN`.

## Question

A translation may weaken a source-language distinction even when subsequent commentary can name it. Can a controlled revision preserve the distinction without exaggerating it? Is commentary before or after translation different from an ordinary retry?

**The one discovery excerpt is post hoc.** It was manually transcribed from one selected conversation, not exported as an independently authenticated raw provider log. It is an anomaly to investigate, not evidence that any model consistently behaves this way or an insight into its internal mechanism.

## Interactive instrument

Browse **12 author-created French passages**, choose among **4 planned trial conditions** (direct, retry, analysis before, analysis after), inspect the initial prompt, copy it, or export the planned protocol. The page does not contact model providers or record responses. The prepared protocol calls for 48 independent sessions and bilingual review, but **zero model trial sessions and zero independent bilingual ratings** have occurred in this packet.

An analysis condition also gives an extra turn/token budget; it is not a clean test of an internal mechanism. Translation quality must be assessed by blind bilingual reviewers for meaning, force, register, attribution, negation, and amplification; preferred-word matching is not a valid sole scoreboard.

## Local checks and provenance

- **17/17** Python fixture tests re-ran and passed on 2026-10-26, checking the planned session structure, source/request isolation, and protocol handling. They are **not 17 model trials**.
- Chromium injected-document smoke check exercised passage/condition selection and JSON export, with no script exceptions. Direct file/navigation, native Windows clipboard, and hosted-page behavior are not certified by this check.
- Archived original at [original.html](original.html), preserved byte-for-byte: **24,460 bytes**.
- SHA-256: `5159ceb535967237b0fe8af5b9f7d660ad4b43636a9fad07ca58f01c1b24a18a`.
- Git blob SHA-1: `57330f031d31145183009e3bd9e0a2e390799c19`.

The full unpublished pilot package contains the session plan, protocol fixtures, tests, and discovery record; only the reviewed standalone viewer and public explanatory notes appear here.

**A prepared test is not a result.** Its value is that it can be run, contested, and potentially falsify our interpretation.

## Gallery navigation update · 2026-10-27

The public [index.html](index.html) adds only a scoped navigation bar and its styles, linking to the gallery and this exhibit's methods. The scientific scripts, embedded data, and original instrument content are unchanged. The [archived standalone original](original.html) retains the historical bytes and hashes recorded above. Those historical hashes identify `original.html`, not the navigation-adapted `index.html`.
