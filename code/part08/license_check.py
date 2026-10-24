#!/usr/bin/env python3
"""Read BCM license information and warn early. Understands the two text formats shown in the Installation Manual:
the 'cmsh -c "main licenseinfo"' table and the 'verify-license info' block (chapter 4).

  license_check.py FILE [--now 2025-06-24] [--warn-months 3]

Checks: expired, expires within N months, nodes or accelerators in use compared with the licensed number
(head nodes count as nodes). Teaching tool: the real checks are 'verify-license verify' and 'monthsleft'.
"""
import datetime as dt, re, sys


def parse(text):
    d = {}
    for line in text.splitlines():
        m = re.match(r"^(Licensee|Serial number|Start time|End time|Version|Edition|Type|Licensed nodes|Licensed accelerators|Accelerators details|"
                     r"Allow edge sites|Expiration date|Starting date|Licensed tokens|MAC address / Cloud ID|Common name|Organization|License type)\s{2,}(.*)$", line.strip())
        if m:
            d[m.group(1)] = m.group(2).strip()
    return d


def parse_date(s):
    for fmt in ("%a %b %d %H:%M:%S %Y", "%d/%b/%Y"):
        try:
            return dt.datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    m = re.search(r"([A-Za-z]{3}) +(\d{1,2}) .* (\d{4})$", s)
    if m:
        return dt.datetime.strptime(f"{m.group(1)} {m.group(2)} {m.group(3)}", "%b %d %Y").date()
    raise ValueError(f"cannot read date: {s}")


def check(text, now, warn_months=3):
    d = parse(text)
    problems = []
    end = parse_date(d.get("End time") or d.get("Expiration date"))
    days = (end - now).days
    if days < 0:
        problems.append(f"EXPIRED {-days} days ago on {end}: CMDaemon will not start (the manual's log line is 'Fatal: License has expired')")
    elif days < warn_months * 30:
        problems.append(f"expires in {days} days on {end}: request a new license now")
    for key, label in (("Licensed nodes", "nodes"), ("Licensed accelerators", "accelerators")):
        m = re.match(r"(\d+)\s*/\s*(\d+)", d.get(key, ""))
        if m and int(m.group(1)) > int(m.group(2)):
            problems.append(f"{label} in use {m.group(1)} exceeds licensed {m.group(2)}")
        elif m and int(m.group(1)) > 0.9 * int(m.group(2)):
            problems.append(f"{label} in use {m.group(1)} is above 90 percent of {m.group(2)}")
    if d.get("Type", d.get("License type", "")).lower() == "free":
        problems.append("license type is Free: check that this is an evaluation or free-tier cluster and what support it carries")
    return d, days, problems


if __name__ == "__main__":
    a = sys.argv
    now = dt.date.fromisoformat(a[a.index("--now") + 1]) if "--now" in a else dt.date.today()
    d, days, problems = check(open(a[1]).read(), now, int(a[a.index("--warn-months") + 1]) if "--warn-months" in a else 3)
    print(f"{d.get('Edition', '?')} license, {days} days left")
    for p in problems:
        print("  -", p)
    sys.exit(1 if any(p.startswith(("EXPIRED", "expires", "nodes", "accel")) for p in problems) else 0)
