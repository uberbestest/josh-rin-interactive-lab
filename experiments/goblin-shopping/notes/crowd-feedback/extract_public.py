"""Extract reviewable display witnesses from a completed fixed grid; no runs.

Usage: python3 extract_public.py RESULTS_DIRECTORY
The equal-count and nonzero-target display selectors were specified after the
grid completed. The corresponding counts/denominators were in PROTOCOL.md.
"""
import hashlib
import json
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: python3 extract_public.py RESULTS_DIRECTORY")
p = Path(sys.argv[1])
raw = json.loads((p / "grid-records.json").read_text())
summary = json.loads((p / "summary.json").read_text())
witnesses = json.loads((p / "witnesses.json").read_text())
primary = [x for x in raw["cases"] if x["cohort"] == "mixed" and x["budget"] in (2, 3)]
shop_ids = raw["encoding"]["shop_indices"]
names = ["Mothlight Market", "Copper Commons", "Golden Goblin Goods", "Lantern & Nail", "Stone & Star", "Duck Cart Co."]
types = ["Reliability", "Budget", "Evidence", "Wanderer", "Crowd", "Copy"]

selected = [
    ("suppression", next(x for x in primary if x["live_minus_held_changed_choices"] < 0),
     "First primary-panel cell with fewer changed choices under live feedback than held history, in fixed seed/budget/roster/arrival loop order.",
     "Specified in protocol before new-grid execution"),
    ("parent_case", next(x for x in primary if x["seed"] == 72 and x["budget"] == 2 and not x["reverse"]),
     "Original post-hoc extreme parent example, selected before this mechanism follow-up.",
     "Previously post-hoc selected parent example"),
    ("equal_count_different_choices", next(x for x in primary if x["live_minus_held_changed_choices"] == 0 and x["overlap"]["live_vs_held_changed"]),
     "First primary-panel cell with equal changed-choice counts but different live/held shopper choices, in fixed loop order.",
     "Post-hoc display selection from the completed fixed grid; aggregate metric was specified before execution"),
    ("nonzero_target", next(x for x in primary if not x["comparisons"]["live"]["paired_zero_sale"]),
     "First primary-panel cell failing the paired zero-sale condition under live feedback, in fixed loop order.",
     "Post-hoc display selection from the completed fixed grid; inclusion in denominators was specified before execution"),
]

public = {
    "record_id": summary["record_id"],
    "title": "When the Crowd Gives a Cart Back",
    "status": summary["status"],
    "selection_note": "These are transparent selected witnesses, not representative samples. Both display selections made after the grid are identified below.",
    "stores": [{"id": s, "name": n} for s, n in zip(shop_ids, names)],
    "witnesses": [],
}
for key, row, rule, status in selected:
    item = {k: row[k] for k in ("seed", "budget", "cohort", "reverse", "comparisons", "overlap", "live_minus_held_changed_choices")}
    item.update({
        "id": key, "selection_rule": rule, "selection_status": status,
        "world_totals": {k: {q: v[q] for q in ("traffic", "first", "carts")} for k, v in row["worlds"].items()},
        "shoppers": [],
    })
    for i in range(24):
        shopper = {"id": i + 1, "type": types[i % 6]}
        for output_name, source_name in [("neutral", "base"), ("held", "held"), ("live", "live"), ("off_neutral", "off_base"), ("off_promoted", "off_promoted")]:
            world = row["worlds"][source_name]
            shopper[output_name] = {
                "opens": [shop_ids[j] for j in world["opens"][i]],
                "selected": None if world["selected"][i] is None else shop_ids[world["selected"][i]],
            }
        shopper["live_changed"] = shopper["neutral"]["selected"] != shopper["live"]["selected"]
        shopper["held_changed"] = shopper["neutral"]["selected"] != shopper["held"]["selected"]
        shopper["held_vs_live_changed"] = shopper["held"]["selected"] != shopper["live"]["selected"]
        item["shoppers"].append(shopper)
    public["witnesses"].append(item)
(p / "public-witnesses.json").write_text(json.dumps(public, indent=2) + "\n")

note = {k: summary[k] for k in ("record_id", "status", "date", "model_sha256", "raw_sha256", "grid", "primary", "checks", "limits")}
note["title"] = "The Crowd Can Cancel a Detour"
note["witnesses"] = {}
for name, row in witnesses.items():
    note["witnesses"][name] = {k: row[k] for k in ("seed", "budget", "cohort", "reverse", "comparisons", "overlap", "worlds")}
note["first_suppression_shopper_16"] = {k: a["shoppers"][15] for k, a in witnesses["first_suppression"]["full_worlds"].items()}
note["nonzero_target_primary_cells"] = [
    {**{k: x[k] for k in ("seed", "budget", "cohort", "reverse")}, "target_choices": x["comparisons"]["live"]["target_choices"]}
    for x in primary if not x["comparisons"]["live"]["paired_zero_sale"]
]
(p / "note-data.json").write_text(json.dumps(note, separators=(",", ":")) + "\n")

files = ("public-witnesses.json", "note-data.json")
(p / "PUBLIC-SHA256SUMS.txt").write_text("".join(
    hashlib.sha256((p / f).read_bytes()).hexdigest() + "  " + f + "\n" for f in files
))
print(json.dumps({"display_witnesses": [x[0] for x in selected], "simulation_runs_added": 0}))
