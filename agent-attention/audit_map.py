#!/usr/bin/env python3
"""Audit the map's source claims and the browser reconstruction.
No outside agent, browser capture, or shopping episode is executed here."""
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from datetime import datetime

ROOT=Path(__file__).resolve().parent
SITE=ROOT.parent
trace=json.loads((ROOT/"pilot-trace.json").read_text(encoding="utf-8"))
events=trace["events"]
assert len(events)==15, "The pilot report covers E01–E15; do not silently drop events"
assert [x["id"] for x in events]==["E%02d"%n for n in range(1,16)]
assert [x["time_local"] for x in events] == sorted(x["time_local"] for x in events)
assert len({x["id"] for x in events})==15
assert sum(x["action"]=="search" for x in events)==5
assert sum(x["evidence"]=="opened" for x in events)==7
assert sum(x["action"]=="attempt" for x in events)==2
assert sum(x["action"]=="selection" for x in events)==1
assert {x["id"] for x in events if x["evidence"]=="surfaced-only"}=={"E11","E12"}
assert {x["id"] for x in events if x["evidence"]=="unconfirmed"}=={"E03","E07"}
assert next(x for x in events if x["id"]=="E14")["evidence"]=="uncertain-transition"
assert next(x for x in events if x["id"]=="E15")["url"].split("?")[0].endswith("B07C3Q3BC2")
assert trace["outcome"]["type"]=="recommendation_not_purchase"
assert trace["setup"]["browser"].lower().startswith("personalized")
assert len(trace["notes"])==3 and [x["id"] for x in trace["notes"]]==["N01","N02","N03"]
assert len({x["url"] for x in events if x["evidence"]=="opened"})==6
assert "full raw archive" in " ".join(trace["limits"]).lower()

html=(ROOT/"index.html").read_text(encoding="utf-8")
payload=re.search(r'<script id="pilotData" type="application/json">([\s\S]*?)</script>',html)
assert payload, "Interactive map lost its data"
assert json.loads(payload.group(1))==trace, "Page events diverge from the public source file"
assert 'id="eventRange"' in html and 'id="witnessChoice"' in html
assert 'id="branchFilter"' in html
assert 'id="traceGraph"' in html and 'id="detailNote"' in html
assert 'id="ladder"' in html and 'id="journey"' in html
assert 'method.html' in html and 'pilot-trace.json' in html
assert 'No purchase' in html and 'scripted' in html.lower()
assert "purgatory" not in html.lower()

class Links(HTMLParser):
    def __init__(self):super().__init__();self.links=[]
    def handle_starttag(self,t,a):
        if t=="a":
            h=dict(a).get("href")
            if h:self.links.append(h)

for target in [ROOT/"index.html",ROOT/"method.html",SITE/"index.html"]:
    if not target.exists():
        if target==SITE/"index.html":
            print("Homepage not in this checkout; homepage wiring check deferred.")
            continue
        raise FileNotFoundError(target)
    parser=Links();parser.feed(target.read_text(encoding="utf-8"))
    for link in parser.links:
        if link.startswith(("https://","http://","mailto:","#")):continue
        dest=(target.parent/link.split("#")[0].split("?")[0]).resolve()
        assert dest.is_file(),f"Broken local link {link} in {target}"
    if target==SITE/"index.html":
        home=target.read_text(encoding="utf-8")
        assert "Agent Attention" in home and 'agent-attention/index.html' in home

summary={
    "scope":"Structured source and map integrity only; not independent review or recovered raw telemetry",
    "pilot_events":len(events),"reported_agent_notes":len(trace["notes"]),
    "search_result_pages":sum(x["action"]=="search" for x in events),
    "confirmed_visit_events":sum(x["evidence"]=="opened" for x in events),
    "distinct_nonsearch_visited_urls":len({x["url"] for x in events if x["evidence"]=="opened"}),
    "search_only_result_branches":sum(x["evidence"]=="surfaced-only" for x in events),
    "unconfirmed_operation_ids":["E03","E07"],
    "uncertain_transition_interval":"E14–E15",
    "transactions":0,
    "independent_agent_replicates":0,
    "result":"PASS",
}
print(json.dumps(summary,indent=2))
