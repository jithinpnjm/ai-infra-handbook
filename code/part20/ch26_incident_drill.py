"""Run a 30-minute stress-interview drill. Usage:
  python3 ch26_incident_drill.py list
  python3 ch26_incident_drill.py run INCIDENT_ID [--minutes 30]
  python3 ch26_incident_drill.py replay INCIDENT_ID SCRIPT   (lines: seconds|input)
"""
import argparse
import sys

from ch26_model import load_incidents
from ch26_score import format_scorecard
from ch26_session import Session


class ReplayClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


def run_interactive(inc, minutes):
    s = Session(inc, minutes)
    print("INTERVIEWER:", inc["opening"])
    print("Commands: /sev /roles /hyp /do /status /cause /hint /done. Anything else is a question.")
    while not s.finished:
        try:
            line = input("[%02d:%02d] > " % divmod(int(s.elapsed()), 60))
        except EOFError:
            break
        print(s.handle(line))
    return s


def run_replay(inc, script_path):
    clock = ReplayClock()
    s = Session(inc, 30, clock)
    for raw in open(script_path):
        if "|" not in raw:
            continue
        secs, line = raw.rstrip("\n").split("|", 1)
        clock.now = float(secs)
        s.handle(line)
    return s


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("cmd", choices=["list", "run", "replay"])
    p.add_argument("incident", nargs="?")
    p.add_argument("script", nargs="?")
    p.add_argument("--minutes", type=int, default=30)
    p.add_argument("--file", default=None)
    a = p.parse_args(argv)
    incidents = load_incidents(a.file) if a.file else load_incidents()
    if a.cmd == "list":
        for inc in sorted(incidents.values(), key=lambda i: i["number"]):
            print("%2d  %-32s %-10s %s" % (inc["number"], inc["id"], inc["kind"], inc["title"]))
        return 0
    if a.incident not in incidents:
        print("unknown incident id; run the list command", file=sys.stderr)
        return 2
    inc = incidents[a.incident]
    s = run_interactive(inc, a.minutes) if a.cmd == "run" else run_replay(inc, a.script)
    print(format_scorecard(s))
    return 0


if __name__ == "__main__":
    sys.exit(main())
