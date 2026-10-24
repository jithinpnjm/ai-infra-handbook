#!/usr/bin/env python3
"""Simulate the staged UPS shutdown described in the SCL book (chapter 28, apcupsd 'haltall' example).

Book algorithm, in plain steps (minute-level):
  1. Power fails (apcupsd runs 'onbattery' -> haltall).  Log it.
  2. Wait 30 minutes: if power returns, abort (most outages are short).
  3. Power off idle nodes (load average < 10 in the book) to stretch the battery for busy nodes.
  4. Wait until about 5 minutes of battery are left.
  5. Stop the queue, cancel running jobs, wait 1 minute.
  6. Power off all nodes; 1 minute later power off the head node.
Also: UPS temperature watch: warn above 25 C, immediate halt above 30 C.

The simulation models battery time-left falling faster as more nodes are on, to show why step 3 helps.
"""

def simulate(power_back_at=None, nodes=100, busy=60, battery_min_full=60.0, per_node_kw=0.4, ups_kw_at_full=50.0):
    """Return a timeline of events. Battery runtime ~ battery_min_full * ups_kw_at_full / load_kw."""
    t, charge, ev = 0, 1.0, []
    on = nodes
    def runtime_left():
        load = max(on * per_node_kw, 0.1)
        return charge * battery_min_full * ups_kw_at_full / load
    ev.append((0, "power failed: onbattery -> haltall starts"))
    phase = "wait"
    while True:
        load = max(on * per_node_kw, 0.1)
        charge -= load / (battery_min_full * ups_kw_at_full)           # per minute drain
        t += 1
        if power_back_at is not None and t >= power_back_at:
            ev.append((t, f"power restored: shutdown aborted ({on} nodes still on, {runtime_left():.0f} min left)"))
            return ev
        if phase == "wait" and t == 30:
            on = busy
            ev.append((t, f"30 min elapsed: powered off {nodes - busy} idle nodes; {runtime_left():.0f} min of battery left"))
            phase = "drain"
        if phase == "drain" and runtime_left() <= 5:
            ev.append((t, f"battery at {runtime_left():.1f} min: queue stopped, running jobs cancelled"))
            phase = "kill"; kill_t = t
        if phase == "kill" and t == kill_t + 1:
            on = 0
            ev.append((t, "all nodes powered off"))
            phase = "head"
        if phase == "head" and t == kill_t + 2:
            ev.append((t, "head node powered off. End of shutdown."))
            return ev
        if charge <= 0:
            ev.append((t, "BATTERY EXHAUSTED: hard power loss"))
            return ev


def temperature_policy(temp_c, warn=25.0, halt=30.0):
    return "HALT cluster now" if temp_c > halt else ("warn admin (mail + wall)" if temp_c > warn else "ok")


if __name__ == "__main__":
    for label, back in (("outage lasts 10 min", 10), ("outage lasts 45 min", 45), ("long outage", None)):
        print(f"--- {label}")
        for m, e in simulate(back):
            print(f"  t+{m:3d} min  {e}")
    print("--- UPS temperature policy")
    for temp in (22, 26, 31):
        print(f"  {temp} C -> {temperature_policy(temp)}")
