"""Shared helpers for the Part 17 operations scripts. State lives under $OPS_HOME (default ./.ops).
Nothing here sends a message: notices are appended to outbox.jsonl, which a real deployment would
hand to Slack/PagerDuty/email. That is the one place the scripts are a stand-in."""
import json, os, re, sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

def home():
    p = Path(os.environ.get("OPS_HOME", ".ops")); p.mkdir(parents=True, exist_ok=True); return p

def outbox(kind, **fields):
    rec = {"kind": kind, **fields}
    with (home() / "outbox.jsonl").open("a") as f: f.write(json.dumps(rec, sort_keys=True) + "\n")
    return rec

def parse_ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)

def parse_duration(s):
    m = re.fullmatch(r"(\d+(?:\.\d+)?)(s|m|h|d)", s.strip())
    if not m: raise ValueError(f"bad duration {s!r} (use 30m, 4h, 1d)")
    return timedelta(**{{"s": "seconds", "m": "minutes", "h": "hours", "d": "days"}[m[2]]: float(m[1])})

def check_date(d):
    return datetime.strptime(d, "%Y-%m-%d").date()

def fmt_td(td):
    m = round(td.total_seconds() / 60); return f"{m} minutes"

def load_yaml(name, default):
    import yaml
    f = home() / name
    return yaml.safe_load(f.read_text()) if f.exists() else default

def save_yaml(name, obj):
    import yaml
    (home() / name).write_text(yaml.safe_dump(obj, sort_keys=False))

def stale(items, days, key="last_reviewed", now=None):
    now = now or datetime.now(timezone.utc)
    return [i for i in items if (now - parse_ts(str(i[key]) + ("T00:00:00Z" if len(str(i[key])) == 10 else ""))).days > days]
