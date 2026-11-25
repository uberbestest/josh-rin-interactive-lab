"""Small, platform-independent encodings shared by the runner and its ledger."""
from __future__ import annotations

import datetime as dt
from decimal import Decimal, InvalidOperation
import hashlib
import json


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def digest(value):
    data = value if isinstance(value, bytes) else canonical(value).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="microseconds")


def money(value):
    if isinstance(value, bool):
        raise ValueError("A Boolean is not a monetary amount")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError("Invalid monetary amount") from exc
    if not result.is_finite() or result < 0:
        raise ValueError("Money must be finite and nonnegative")
    return result
