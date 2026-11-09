#!/usr/bin/env python3
"""Summarise `ss -tan` output: states, full accept queues, port budget.
For LISTEN sockets Recv-Q is the current accept queue length and Send-Q is
the configured limit (see the chapter, scenario 1). Standard library only."""
import sys
from collections import Counter

STATE = {"ESTAB": "ESTABLISHED", "LISTEN": "LISTEN", "TIME-WAIT": "TIME-WAIT",
         "CLOSE-WAIT": "CLOSE-WAIT", "SYN-SENT": "SYN-SENT",
         "SYN-RECV": "SYN-RECV", "FIN-WAIT-1": "FIN-WAIT-1",
         "FIN-WAIT-2": "FIN-WAIT-2", "LAST-ACK": "LAST-ACK",
         "CLOSING": "CLOSING", "ESTABLISHED": "ESTABLISHED"}

def parse(text):
    """Return rows (state, recvq, sendq, local, peer). Skips header and junk."""
    rows = []
    for line in text.splitlines():
        f = line.split()
        if len(f) < 5 or f[0] not in STATE:
            continue
        if not (f[1].isdigit() and f[2].isdigit()):
            continue
        rows.append((STATE[f[0]], int(f[1]), int(f[2]), f[3], f[4]))
    return rows

def summarize(rows):
    counts = Counter(r[0] for r in rows)
    full = [r for r in rows if r[0] == "LISTEN" and r[2] > 0 and r[1] >= r[2]]
    return {"counts": dict(counts), "full_listeners": [r[3] for r in full]}

def max_new_conn_rate(port_lo, port_hi, time_wait_s=60):
    """Sustained connects per second to one dst ip:port before ports run out.
    Every closed connection holds its source port for time_wait_s."""
    return (port_hi - port_lo + 1) / time_wait_s

if __name__ == "__main__":
    print(summarize(parse(sys.stdin.read())))
