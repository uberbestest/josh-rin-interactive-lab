#!/usr/bin/env python3
"""Build the readable Round09 report from retained, already executed evidence."""
from pathlib import Path
import hashlib
import json
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

ROOT=Path(__file__).resolve().parents[1]
OUT=Path(__file__).resolve().parent
SUMMARY=json.loads((ROOT/'results/summary.json').read_text())
REPLAY=json.loads((ROOT/'provenance/reproduction.json').read_text())
FREEZE=json.loads((ROOT/'provenance/prerun_github_receipt.json').read_text())
assert SUMMARY['total_executions']==237 and SUMMARY['total_execution_errors']==0
assert REPLAY['runs_replayed']==237 and REPLAY['events_replayed']==2308
CELLS={(c['suite'],c['policy']):c for c in SUMMARY['cells']}
FONT=Path('/usr/share/fonts/truetype/dejavu')
for name,file in [('Body','DejaVuSans.ttf'),('Bold','DejaVuSans-Bold.ttf'),('Title','DejaVuSerif-Bold.ttf'),('Code','DejaVuSansMono.ttf')]:
    pdfmetrics.registerFont(TTFont(name,str(FONT/file)))
pdfmetrics.registerFontFamily('Body',normal='Body',bold='Bold',italic='Body',boldItalic='Bold')
INK=colors.HexColor('#18343e'); TEAL=colors.HexColor('#176b64'); MUTED=colors.HexColor('#58696d')
PALE=colors.HexColor('#edf4f3'); LINE=colors.HexColor('#d2e0de'); GOLD=colors.HexColor('#a56c26')
styles={
 'body':ParagraphStyle('body',fontName='Body',fontSize=9.4,leading=13.7,textColor=INK,spaceAfter=8),
 'small':ParagraphStyle('small',fontName='Body',fontSize=8.1,leading=11.5,textColor=MUTED,spaceAfter=7),
 'title':ParagraphStyle('title',fontName='Title',fontSize=27,leading=33,textColor=INK,spaceAfter=13),
 'h1':ParagraphStyle('h1',fontName='Title',fontSize=21,leading=27,textColor=INK,spaceAfter=12),
 'h2':ParagraphStyle('h2',fontName='Bold',fontSize=11.6,leading=16,textColor=TEAL,spaceBefore=7,spaceAfter=6),
 'eyebrow':ParagraphStyle('eyebrow',fontName='Bold',fontSize=8.2,leading=12,textColor=TEAL,spaceAfter=10),
 'cell':ParagraphStyle('cell',fontName='Body',fontSize=8.3,leading=11.4,textColor=INK),
 'head':ParagraphStyle('head',fontName='Bold',fontSize=8.1,leading=11,textColor=colors.white),
 'code':ParagraphStyle('code',fontName='Code',fontSize=8.2,leading=12,textColor=INK,spaceAfter=7),
}
story=[]
def para(text,kind='body'):return Paragraph(text,styles[kind])
def add(text,kind='body'):story.append(para(text,kind))
def h(text):add(text,'h2')
def page(number,title,subtitle=None):
    if story:story.append(PageBreak())
    add(f'JOSH &amp; RIN\'S LAB  /  BONDED RSI  /  ROUND 09  /  {number:02d}','eyebrow')
    add(title,'h1')
    if subtitle:add(subtitle,'small')
def table(rows,widths):
    data=[[para(escape(str(v)).replace('\n','<br/>'),'head' if i==0 else 'cell') for v in row] for i,row in enumerate(rows)]
    t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),TEAL),('VALIGN',(0,0),(-1,-1),'TOP'),
      ('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),
      ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),
      ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,PALE]),
      ('LINEBELOW',(0,0),(-1,0),.7,TEAL),('LINEBELOW',(0,-1),(-1,-1),.7,LINE)]))
    story.append(t);story.append(Spacer(1,10))
def box(text):
    t=Table([[para(text)]],colWidths=[524])
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),PALE),('BOX',(0,0),(-1,-1),.7,LINE),
                          ('LEFTPADDING',(0,0),(-1,-1),12),('RIGHTPADDING',(0,0),(-1,-1),12),
                          ('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),4)]))
    story.append(t);story.append(Spacer(1,10))

add('JOSH &amp; RIN\'S LAB  /  BONDED RSI  /  NOVEMBER 19, 2026','eyebrow')
add('The Guard That<br/>Kept the Job','title')
add('A reproducible repair for safe continuation, with a stronger baseline tie kept visible.','body')
add('JRR-CONTINUATION-REPAIR-2026-11-19-009<br/>237 prespecified scripted executions; zero fresh model participants. Same-lab verification.','small')
box('<b>What we tested:</b> Can a controller preserve the guard\'s evidence requirements while completing work the guard leaves unfinished?<br/><br/><b>What happened:</b> Historical safe joint completion rose from 3/8 for each saved guarded helper to 8/8 for the repair. On the separate challenge, both the planner and a simpler deadline-first policy attained 64/64 positive guarantees.<br/><br/><b>Outliers:</b> The simpler policy also completed three additional favorable-world jobs. Two later diagnostic cases expose its limits; those cases do not change the prospective tie.')
h('The separate challenge')
table([
 ['Endpoint','Planner','Deadline-first','Wait-for-all'],
 ['Positive guarantees attained','64 / 64','64 / 64','50 / 64'],
 ['Both jobs completed where initially guaranteed','43 / 43','43 / 43','31 / 43'],
 ['Runs with unsafe operations attempted','0 / 71','0 / 71','0 / 71'],
 ['Runs that sacrificed an available guarantee','0 / 71','0 / 71','14 / 71'],
 ['Both jobs completed across all selected worlds','49 / 71','52 / 71','40 / 71'],
], [245,93,93,93])
add('Seven zero-guarantee controls are separate from the 64 positive-guarantee denominator. Physical completion across all worlds includes favorable outcomes that were not guaranteed initially. Counts describe authored synthetic cases, not production error rates.','small')
add('<b>Supported result:</b> the retained scaffold repairs the demonstrated stopping behavior. The main challenge does not show that exact search is superior to the simpler recovery policy.','body')

page(2,'What changed in the failure','The repair adds a continuation decision after the guard checks the evidence.')
h('A guard can be safe and leave the job unfinished')
add('The previous helpers loop over B and A, query each receipt, require a resolved status bound to the selected job, and stop when evidence is pending or mismatched. That blocks the tested unsupported actions. It does not decide when to wait, which already-known job to finish first, or how to spend a shared limited-use key.')
table([['Historical comparison','w041 guard','w042 guard','Planner'],
 ['Same eight initial cases: safely complete both','3 / 8','3 / 8','8 / 8'],
 ['Unsafe attempts','0','0','0'],
 ['Stops with a safe joint continuation still available','4','4','0'],
 ['Wrong-job headers rejected, then work completed','0 / 2','0 / 2','2 / 2']], [260,88,88,88])
add('The fifth incomplete case for each old helper had already lost its joint guarantee by checking too early. The original helpers never seal a final report; the candidate does. Their unchanged behavior and evidence remain available.','small')
h('One recorded continuation: pending_absent')
add('A already has exactly-one evidence. B remains uncertain, its receipt becomes authoritative at tick 4, and B must finish by tick 6. Six shared uses remain. The repaired policy first performs useful work on A, then queries B at the right time.')
table([['Operation','Completion tick','Uses left','Evidence or result'],
 ['Finalize A','1','5','A is complete'],
 ['Wait one tick','2','5','No check budget spent'],
 ['Query B receipt','4','4','Authoritative ABSENT'],
 ['Commit B once','5','3','Authoritative acknowledgement'],
 ['Finalize B','6','2','Both complete by deadline']], [175,90,70,189])
h('The trusted recovery channel matters')
add('Two cases replace the first displayed B receipt header with an A COMMITTED header. The candidate rejects that mismatch and obtains a fresh authentic local status. That status can expose the genuine receipt facts. Recovery therefore depends on an explicitly trusted channel; header shape checking alone does not authenticate a remote service.')
add('The candidate queries later than the original helpers. Its canonical B receipt is already resolved when substituted. The historical adapter is pending-only; the candidate adapter changes the first B header regardless of readiness. This disclosed fault-model extension is not an identical-observation trajectory comparison.','small')

page(3,'Design and decision rule','Preserve the initial public guarantee, not merely a fortunate hidden outcome.')
table([['Part','Design','Assigned executions'],
 ['Separate challenge','24 configurations; all 71 consistent hidden worlds; three policies','213'],
 ['Historical candidate regression','Eight exact Round08 initial cases','8'],
 ['Historical saved programs','Two unchanged guarded helpers, eight cases each','16'],
 ['Main study total','One execution per assignment; no replacements','237'],
 ['Later exploratory diagnostics','Two configurations, three worlds, two unchanged policies','6, kept separate']], [145,300,79])
add('The challenge author fixed cases and assignments before computing evaluator labels and before inspecting the candidate. The candidate author had read the earlier contract and failures. This is same-lab separation of authorship, not externally enforced blinding. Twelve configurations cover 43 joint-guaranteed worlds, nine cover 21 one-job worlds, and three cover seven zero-guarantee worlds.')
h('An observation-only planner')
add('The candidate receives public status and displayed responses through a JSONL process. It has no reference-engine import, fixture lookup, oracle call, file access, or network operation. The evaluator alone retains the selected hidden world. Process separation defines the interface; it is not an operating-system security boundary.')
add('Its symbolic state contains remaining uses, logical time, remaining actions, each job\'s evidence/completion phase, and receipt-readiness possibilities. Each receipt can branch into absent, committed, or pending outcomes. The planner chooses the action whose worst allowed branch has the best continuation value.')
box('<b>Objective:</b> first maximize the number of safely finalized jobs that can be guaranteed; then prefer the declared priority job when counts tie. Commit only from established absence, and finalize only from exactly-one evidence. Both operations must fit the selected deadline and available uses.')
add('The solver can replace a certainly-pending paid check with waiting, reuse immutable known evidence, and perform another job during a delay. It treats an unresolved unbounded receipt as providing no finite completion guarantee. Exact search is an established method; the contribution here is the inspectable repair and evidence package for this particular failure.')
h('Comparison policies')
add('Deadline-first chooses the earliest-deadline unfinished job, using priority only to break deadline ties. It waits for that job\'s guaranteed receipt and checks immediate admission. Wait-for-all first waits for all bounded unresolved receipts, then applies the same greedy policy. They are two transparent authored heuristics sharing code, not a sample of competitive agents.')

page(4,'The tie and its boundaries','The exploratory examples constrain interpretation without rewriting the original result.')
h('The simpler policy matched the declared challenge')
add('Planner and deadline-first each attained all 64 positive guarantees, all 43 initially guaranteed joint completions, and zero risky selections. The candidate made 88 receipt queries across 71 worlds; deadline-first made 96. These logical-resource totals do not measure CPU time or model inference cost, and the policies did not finish equal amounts of opportunistic work.')
add('Deadline-first completed both jobs in 52 worlds versus 49 for the planner. In C07-W02, C08-W03 and C14-W03, it secured the priority job, then used remaining resources to query the other job. A favorable COMMITTED result permitted an extra safe completion. The planner stopped when no additional completion could be guaranteed. That stopping rule fits the declared objective but leaves useful opportunities unused.')
h('Diagnostic 1: a deadline does not override priority')
add('After seeing the tie, we authored a case with both jobs already known present and only one remaining key use. A expires at tick 1; B expires at tick 2 and is the declared priority. The planner finalizes B at tick 1, attaining value (1, 1). Deadline-first finalizes A, spends the only use, and attains (1, 0). Its action is safe but loses the achievable priority guarantee.')
h('Diagnostic 2: fill the waiting interval')
add('A\'s receipt becomes ready at tick 4 and A must finish by tick 6. B is known absent and must finish by tick 7; five uses remain. The planner commits and finalizes B during ticks 1-2, queries A to tick 4, and completes A by tick 6 in both hidden A worlds. Deadline-first waits first. It misses B\'s finalization deadline when A was absent; when A was already present, it happens to finish both despite having sacrificed the initial guarantee.')
box('<b>Exploratory status:</b> these two configurations were selected after the primary tie, then hash-frozen before their six executions. The planner attained 3/3 initial guarantees; deadline-first attained 1/3 and made a risky selection in all three worlds. Neither attempted an unsafe write. These are counterexamples to general equivalence, not held-out superiority evidence or population rates.')
add('The next objective question is whether safe opportunistic completion should be rewarded after the worst-case guarantee is secured. This report retains the current objective and does not retrofit that preference into its success labels.','body')

page(5,'What the guard still assumes','The bounded result is useful only when its evidence contract is preserved.')
h('Structural checks have limits')
add('A separate source audit ran 35 small structural/control probes and retained four boundary witnesses. The candidate source was not changed to remove those witnesses. These checks are outside both the 237 primary executions and the six exploratory executions.')
table([['Retained boundary witness','Consequence'],
 ['A well-formed same-job forged receipt is accepted','The parser does not authenticate origin.'],
 ['An identical matching response is accepted again','No request nonce or consumed-response ledger prevents replay.'],
 ['Finalized/exact flags can contradict ABSENT plus zero writes','Validation relies on a genuine canonical status channel.'],
 ['Boolean true is accepted as a one-tick wait acknowledgement','Validation does not strictly type-check every reply field.']], [280,244])
h('Scope of the experiment')
add('The service contains two jobs with independent original-write outcomes, stable active authorization, immutable original receipts, fixed declared operation costs, inclusive logical deadlines, and a finite action cap. It does not test revoked approvals, changed payloads, concurrent writers, arbitrary malicious service responses, crash-safe persistence, actual network retries, or a production orchestration framework.')
add('The planner\'s own proof field records a search witness and a public-status digest. It is not an independent formal certificate. Large public inputs have no demonstrated CPU or memory bound. The harness applies a host deadline and retains failures rather than converting them into successful tasks.')
h('Improvement in a retained scaffold')
add('The engineered controller, tests and evidence can be retained and reused. That is the measured locus of the Bonded RSI improvement. No model weights changed; retained model experience and cross-session behavioral uptake were not tested. No fresh native model participant was requested, and there is no new GPT-6 versus GPT-6.2 comparison.')
add('The engineering session was declared GPT-6.2 Astra Pro. This inherited declaration is not independent attestation of a serving snapshot. The two historical JavaScript helpers came from earlier 6.2-context records, but replaying their code does not resample those models.','small')
h('Reports and outcomes remain separate')
add('All 221 new-policy runs sealed mechanically truthful required report fields. The verifier checks strict counter types, completion, recognized per-job facts and reported guaranteed value. Free prose semantics and unknown optional fields are not fully machine-verified. Mechanical completion, compliant attempts, preserved guarantees and truthful accounting remain distinct endpoints.')

page(6,'Evidence, reproduction and use','A complete result can be inspected and rerun without invoking a language model.')
h('Prospective order and verification')
add('The 40-file source manifest and 41-file publication were placed on GitHub in commit '+FREEZE['commit'][:12]+' before any assigned main execution. The commit time was 13:18:47 UTC; the first event was 13:18:57.350806 UTC on November 19, 2026. The case file had been frozen earlier, at 13:08:37.991617 UTC. Git publication records order; it is not independent timestamp attestation.')
add('All 237 original trajectories replayed exactly, covering 2,308 canonical events. Fresh reproduction repeated every assigned controller and saved-helper execution. Decisions, observations, states, counters and normalized results matched. Wall-clock timestamps, their dependent chain hashes and runtime-version metadata are excluded only from cross-execution equality; each original chain is validated in full.')
add('The separately written arithmetic checker imports neither the controller nor the reference engine. It reconstructed evidence, resource spending and actual effects for all 237 main trajectories, plus all six exploratory diagnostic trajectories. Risk counts reuse the reference oracle; they are not a second independent policy oracle. Separate model reviewers in the same lab are not external scientific replication.')
h('Run the evidence package')
add('Extract the evidence ZIP and enter its <font name="Code">continuation-repair</font> directory. Python 3.12 and Node.js reproduce the main study; no network, paid API, or model inference is required.','body')
add('python3 -B verify.py --records results --reproduce<br/>&nbsp;&nbsp;--output /tmp/round09-check.json','code')
add('Use the command on one line. The verifier writes new executions to a temporary directory and preserves the retained records. For the separately labeled diagnostics:','small')
add('python3 -B verify_posthoc.py<br/>&nbsp;&nbsp;--output /tmp/round09-posthoc-check.json','code')
h('A practical use, still to be tested externally')
add('The result supplies a worked example for a bounded workflow continuation audit: reproduce the failure, identify the evidence and scheduling boundary, repair it, and rerun matched legitimate and failure cases. Transfer requires an adapter and an external-state oracle for a real workflow. The present study establishes no customer demand, paid engagement, revenue, or production certification.')
add('The general integration problem is documented elsewhere: LangGraph describes node replay around interrupts and the possibility of repeated effects after a post-commit failure. This study did not execute LangGraph or discover a new flaw in it. [3]','body')
h('References and artifact identity')
add('[1] <link href="https://uberbestest.github.io/josh-rin-interactive-lab/rin-self-evaluation/round-08.html" color="#176b64">Round08: Finalization Without Target Evidence.</link><br/>[2] <link href="https://github.com/uberbestest/josh-rin-interactive-lab/commit/'+FREEZE['commit']+'" color="#176b64">Prospective Round09 source freeze.</link><br/>[3] <link href="https://docs.langchain.com/oss/python/langgraph/interrupts" color="#176b64">LangGraph official documentation: Interrupts.</link> Accessed November 19, 2026.','small')
add('Frozen manifest SHA-256:<br/>'+FREEZE['freeze_sha256'],'small')

def footer(canvas,doc):
    canvas.saveState();canvas.setStrokeColor(LINE);canvas.line(44,39,568,39)
    canvas.setFont('Body',7.3);canvas.setFillColor(MUTED)
    canvas.drawString(44,26,'Josh & Rin\'s Lab | Round09 | November 19, 2026')
    canvas.drawRightString(568,26,str(doc.page));canvas.restoreState()

OUT.mkdir(parents=True,exist_ok=True)
path=OUT/'round-09.pdf'
doc=SimpleDocTemplate(str(path),pagesize=letter,rightMargin=44,leftMargin=44,topMargin=39,bottomMargin=53,
                      title='The Guard That Kept the Job',author="Josh & Rin's Lab")
doc.build(story,onFirstPage=footer,onLaterPages=footer)
print(json.dumps({'path':path.name,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}))
