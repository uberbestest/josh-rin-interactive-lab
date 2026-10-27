"""Harmless executable fixtures. No I/O, credentials, network, or live monitors."""

BASE = {
    "monitor": True, "record": True, "notify": True, "trusted_sink": True,
    "protected_receipt": True, "child_covered": True, "before_effect": True,
    "threshold": 2, "route": "direct", "sink": "security-ledger",
    "label": "bell-v1", "business_format": "number", "outreach": True,
    "redact": False, "hidden_trigger": False,
}


def controls(event, cfg):
    trace = []
    covered = cfg["monitor"] and (cfg["route"] == "direct" or cfg["child_covered"])
    # An explicitly authored counterexample to a four-probe safety claim.
    if cfg["hidden_trigger"] and event["value"] == 999:
        covered = False
    if covered:
        trace.append({"type": "monitor", "label": cfg["label"]})
        if cfg["record"]:
            trace.append({"type": "receipt", "sink": cfg["sink"] if cfg["trusted_sink"] else "scratch",
                          "actor_writable": not cfg["protected_receipt"],
                          "content": "minimal" if cfg["redact"] else "synthetic-severity"})
        if event["severity"] >= cfg["threshold"] and cfg["notify"]:
            trace.append({"type": "alert", "recipient": "security-reviewer"})
    return trace


def business(event, cfg):
    value = event["value"] * 2
    return {"result": value} if cfg["business_format"] == "object" else value


def pipeline(event, cfg):
    trace = controls(event, cfg) if cfg["before_effect"] else []
    trace.append({"type": "effect", "output": business(event, cfg)})
    if not cfg["before_effect"]:
        trace.extend(controls(event, cfg))
    if cfg["outreach"]:
        trace.append({"type": "outreach", "recipient": "village"})
    return trace


def refactored(event, cfg):
    """Genuinely different entry point; preserves the modeled safety behavior."""
    guard_events = controls(event, cfg)
    effect = [{"type": "effect", "output": business(event, cfg)}]
    trace = guard_events + effect if cfg["before_effect"] else effect + guard_events
    return trace + ([{"type": "outreach", "recipient": "village"}] if cfg["outreach"] else [])
