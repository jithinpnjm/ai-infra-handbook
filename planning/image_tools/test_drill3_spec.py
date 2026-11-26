import re
import xml.etree.ElementTree as ET

expected_labels = [
    "Drill 3: a liveness probe kills a slow load",
    "what exists",
    "weights load for about 90 seconds ('loading weights 62%' then nothing in the previous logs)",
    "broken probes",
    "liveness initialDelaySeconds 5, periodSeconds 10, failureThreshold 1, no startup probe",
    "first check near 5 s fails, event 'Unhealthy: Liveness probe failed' three times then 'Killing: failed liveness probe, will be restarted'",
    "restart count 40, one restart every four minutes",
    "fixed",
    "startup probe with failureThreshold 30 and period 10 gives a 300 second window",
    "liveness only starts after the startup probe passes",
    "starts at 10 s, doubles, capped at 300 s, resets after ten clean minutes",
    "OOM kill shows Last State Terminated, Reason OOMKilled, Exit Code 137; here Reason is Error and no OOMKilled",
    "liveness answers is this process stuck, not is it ready; slow starters get a startup probe sized to a measured load time"
]

print("Total expected labels:", len(expected_labels))
for i, l in enumerate(expected_labels):
    print(f"{i:2d}. len={len(l):3d} : '{l}'")
