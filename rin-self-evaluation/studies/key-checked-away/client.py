#!/usr/bin/env python3
"""Participant CLI for an already initialized synthetic service instance."""
from __future__ import annotations

import argparse
import datetime
import fcntl
import json
import os
from pathlib import Path
import re
import sys

from engine import digest, new_event, report_bytes, transition

ROOT = Path(__file__).resolve().parent


def atomic_json(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("wb") as stream:
        stream.write(report_bytes(value))
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True)
    parser.add_argument("action", choices=("status", "receipt", "authority", "wait", "commit", "finalize", "finish"))
    parser.add_argument("--ticks", type=int)
    parser.add_argument("--report-json")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", args.run):
        parser.error("Invalid run identifier")
    if args.action == "wait" and args.ticks is None:
        parser.error("wait requires --ticks")
    if args.action != "wait" and args.ticks is not None:
        parser.error("--ticks is only valid for wait")
    report = None
    if args.action == "finish":
        if args.report_json is None or len(args.report_json.encode("utf-8")) > 16384:
            parser.error("finish requires --report-json (at most 16 KiB)")
        try:
            report = json.loads(args.report_json, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
        except (json.JSONDecodeError, ValueError):
            parser.error("--report-json must be valid JSON")
        if not isinstance(report, dict):
            parser.error("--report-json must be a JSON object")
    elif args.report_json is not None:
        parser.error("--report-json is only valid for finish")
    directory = ROOT / "runs" / args.run
    if not directory.is_dir() or directory.is_symlink():
        parser.error("Unknown run identifier")
    with (directory / ".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        state_path = directory / "state.json"
        before = json.loads(state_path.read_text(encoding="utf-8"))
        if before["config"].get("run_id", args.run) != args.run:
            raise RuntimeError("Run identifier does not match the initialized state")
        events_path = directory / "events.jsonl"
        rows = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines()] if events_path.exists() else []
        initial = json.loads((directory / "initial_state.json").read_text(encoding="utf-8"))
        expected = rows[-1]["after_state_sha256"] if rows else digest(initial)
        if digest(before) != expected:
            raise RuntimeError("State/event checkpoint mismatch; stop and report infrastructure error")
        after, observation, oracle = transition(before, args.action, args.ticks, report)
        parameters = {}
        if args.ticks is not None:
            parameters["ticks"] = args.ticks
        if report is not None:
            parameters["report"] = report
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        row = new_event(len(rows), rows[-1]["event_sha256"] if rows else "0" * 64,
                        before, after, args.action, parameters, observation, oracle, timestamp)
        # A crash between these writes fails closed on the next invocation; it
        # cannot silently continue from a state not justified by the event log.
        with events_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        atomic_json(state_path, after)
        if args.action == "finish" and not before["sealed"]:
            atomic_json(directory / "final_report.json", report)
        print(json.dumps(observation, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
