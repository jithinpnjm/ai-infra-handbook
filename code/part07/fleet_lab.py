#!/usr/bin/env python3
"""Self-checking lab for chapter 7.12: run a task on many BMCs, some of them broken, without making things worse.

Starts 15 mock BMCs in-process: healthy ones, a slow one, one that answers 503 twice then recovers, one that
always answers 503, one with a wrong password, one that hangs, one that is not listening at all, and one with a
different layout. Then checks the runner's behaviour. Delays use small real sleeps.
"""
import sys, threading, time
from redfish_mock import make_server
import fleet_run

ok_count = fail_count = 0


def check(name, cond, detail=""):
    global ok_count, fail_count
    ok_count += bool(cond); fail_count += (not cond)
    print(f"{'PASS' if cond else 'FAIL'}  {name}" + (f"   [{detail}]" if detail and not cond else ""))


def main():
    eps, states, servers = [], {}, []
    def add(name, profile="dgx", faults=None, password="adminpass", listen=True):
        srv, st = make_server(profile, 0)
        port = srv.server_address[1]
        if faults:
            st.faults = dict(faults)
        if listen:
            threading.Thread(target=srv.serve_forever, daemon=True).start()
            servers.append(srv)
        else:
            srv.server_close()
        states[name] = st
        eps.append(dict(name=name, url=f"http://127.0.0.1:{port}", user="admin", password=password))
    for i in range(1, 9):
        add(f"ok{i:02d}")
    add("slow", faults={"delay": 0.6})
    add("flaky", faults={"fail_first": 2})
    add("down503", faults={"fail_first": 999})
    add("badpw", password="wrong-password")
    add("hang", faults={"hang": True, "hang_seconds": 5})
    add("closed", listen=False)
    add("generic", profile="generic")
    sleeps = []
    t0 = time.time()
    res = fleet_run.run(eps, fleet_run.task_health, workers=6, timeout=1.0, retries=3, sleep=lambda s: (sleeps.append(s), time.sleep(min(s, 0.05)))[1])
    took = time.time() - t0
    R = {r["name"]: r for r in res}

    check("every host ends in exactly one outcome (15 results for 15 hosts)", len(res) == 15 and len({r["name"] for r in res}) == 15, len(res))
    check("the 8 healthy BMCs succeed on the first try", all(R[f"ok{i:02d}"]["ok"] and R[f"ok{i:02d}"]["attempts"] == 1 for i in range(1, 9)))
    check("a slow BMC (0.6 s per request) still succeeds within the 1 s timeout", R["slow"]["ok"], R["slow"])
    check("a flaky BMC (503 twice) succeeds on the third attempt", R["flaky"]["ok"] and R["flaky"]["attempts"] == 3, R["flaky"])
    check("a BMC that always answers 503 fails after 1 + 3 retries with kind 'http 503'", not R["down503"]["ok"] and R["down503"]["attempts"] == 4 and R["down503"]["kind"] == "http 503", R["down503"])
    check("a wrong password is NOT retried (1 attempt): retrying could lock the account", not R["badpw"]["ok"] and R["badpw"]["attempts"] == 1 and "401" in R["badpw"]["kind"], R["badpw"])
    check("a BMC that hangs is cut off by the timeout and reported as 'timeout'", not R["hang"]["ok"] and R["hang"]["kind"] == "timeout", R["hang"])
    check("a closed port is reported as 'connection refused'", not R["closed"]["ok"] and R["closed"]["kind"] == "connection refused", R["closed"])
    check("a BMC with a different layout (generic profile) works with no change", R["generic"]["ok"] and R["generic"]["result"]["systems"] == 1, R["generic"])
    check("one bad BMC never stops the run: the other hosts all finished", sum(r["ok"] for r in res) == 11, sum(r["ok"] for r in res))
    n, ok, kinds = fleet_run.summary(res)
    check("the summary counts failures by kind", (n, ok) == (15, 11) and kinds == {"http 503": 1, "http 401": 1, "timeout": 1, "connection refused": 1}, kinds)
    check("backoff waits grow: the 503 host's waits roughly double (with jitter)", len(sleeps) >= 6, sleeps[:8])
    check("sessions were closed on the healthy hosts (no leftover sessions)", all(not states[f"ok{i:02d}"].sessions for i in range(1, 9)), {k: len(v.sessions) for k, v in states.items() if v.sessions})

    # concurrency: 8 slow-ish hosts, one worker vs many
    for n in range(8):
        pass
    slow_eps = []
    for i in range(8):
        srv, st = make_server("dgx", 0); st.faults = {"delay": 0.05}
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        slow_eps.append(dict(name=f"s{i}", url=f"http://127.0.0.1:{srv.server_address[1]}", user="admin", password="adminpass"))
    t = time.time(); fleet_run.run(slow_eps, fleet_run.task_inventory, workers=1, timeout=5, retries=0); serial = time.time() - t
    t = time.time(); fleet_run.run(slow_eps, fleet_run.task_inventory, workers=8, timeout=5, retries=0); par = time.time() - t
    check(f"8 workers are much faster than 1 on 8 slow hosts ({serial:.1f}s against {par:.1f}s)", par < serial / 3, (serial, par))

    print(f"\n{ok_count} passed, {fail_count} failed")
    return 1 if fail_count else 0


if __name__ == "__main__":
    sys.exit(main())
