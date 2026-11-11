#!/usr/bin/env python3
"""Synthetic signal injection for the observability capstone (Chapter 19.7).

Standard library only, plus code/part20/slo_burn_rate.py for the alert policy.

A Scenario describes one gateway fault as per-minute request counts. From it
this module does two independent things:

  1. promtool_test(): writes a `promtool test rules` file that feeds the same
     counters to the real Prometheus rule files in code/part20.
  2. model_alerts(): evaluates the multiwindow burn-rate policy in plain Python
     on the same counters.

The acceptance runner compares the two. If they disagree, either the rule file
or the model is wrong.
"""
import json
import pathlib
import subprocess
import sys
import tempfile
from dataclasses import dataclass

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "part20"))
import slo_burn_rate  # noqa: E402

SLO = 0.999
FAST = (1.0, 5 / 60, 14.4)   # long window h, short window h, burn rate
SLOW = (6.0, 0.5, 6.0)
ALERT_FAST = "GatewayAvailabilityBurnFast"
ALERT_SLOW = "GatewayAvailabilityBurnSlow"
ANNOTATIONS = {
    ALERT_FAST: "m1 burns 2% of the 30 day budget per hour",
    ALERT_SLOW: "m1 burns 5% of the budget in 6 hours",
}


@dataclass
class Scenario:
    """Per-minute counts. bad_ratio[m] is the share of requests that fail in minute m."""
    name: str
    minutes: int
    per_minute: int
    bad_ratio: callable
    eval_minutes: tuple

    def cumulative(self):
        """Return (good, bad) cumulative counter samples, one per minute, starting at 0."""
        good, bad = [0], [0]
        for m in range(self.minutes):
            b = round(self.per_minute * self.bad_ratio(m))
            good.append(good[-1] + self.per_minute - b)
            bad.append(bad[-1] + b)
        return good, bad


def window_ratio(good, bad, t, window_min):
    """Error ratio over the last window_min minutes ending at minute t, using the
    samples that exist. This is increase(bad)/increase(all), the ratio the
    recording rules compute with rate()."""
    lo = max(0, t - int(round(window_min)))
    dg = good[t] - good[lo]
    db = bad[t] - bad[lo]
    total = dg + db
    return db / total if total else 0.0


def model_alerts(sc, t):
    """Set of alert names the policy says are firing at minute t."""
    good, bad = sc.cumulative()
    fired = set()
    for name, (long_h, short_h, burn) in ((ALERT_FAST, FAST), (ALERT_SLOW, SLOW)):
        lr = window_ratio(good, bad, t, long_h * 60)
        sr = window_ratio(good, bad, t, short_h * 60)
        if slo_burn_rate.should_alert(lr, sr, SLO, burn):
            fired.add(name)
    return fired


def _values(samples):
    return " ".join(str(v) for v in samples)


def promtool_test(sc):
    """Return the text of a promtool test file for the scenario."""
    good, bad = sc.cumulative()
    lines = [
        "rule_files:",
        "  - ../part20/slo_recording_rules.yaml",
        "  - ../part20/slo_burn_alerts_availability.yaml",
        "evaluation_interval: 1m",
        "tests:",
        f"  - name: {json.dumps(sc.name)}",
        "    interval: 1m",
        "    input_series:",
        f"      - series: 'gateway_requests_total{{tenant=\"a\",model=\"m1\",code=\"200\"}}'",
        f"        values: '{_values(good)}'",
        f"      - series: 'gateway_requests_total{{tenant=\"a\",model=\"m1\",code=\"500\"}}'",
        f"        values: '{_values(bad)}'",
        "    alert_rule_test:",
    ]
    for t in sc.eval_minutes:
        for alert in (ALERT_FAST, ALERT_SLOW):
            lines.append(f"      - eval_time: {t}m")
            lines.append(f"        alertname: {alert}")
            if alert in model_alerts(sc, t):
                lines.append("        exp_alerts:")
                lines.append("          - exp_labels: {model: m1, severity: page, slo: availability}")
                lines.append("            exp_annotations:")
                lines.append(f"              summary: {json.dumps(ANNOTATIONS[alert])}")
                lines.append('              runbook: "runbooks/gateway-availability.md"')
            else:
                lines.append("        exp_alerts: []")
    return "\n".join(lines) + "\n"


def run_promtool(sc, promtool="promtool"):
    """Run the scenario through promtool. Returns (ok, output). The temp file is
    placed in code/part19 so the ../part20 rule paths resolve."""
    with tempfile.NamedTemporaryFile("w", suffix="_test.yaml", dir=HERE, delete=False) as f:
        f.write(promtool_test(sc))
        path = f.name
    try:
        r = subprocess.run([promtool, "test", "rules", path], capture_output=True, text=True)
        return r.returncode == 0, (r.stdout + r.stderr).strip()
    finally:
        pathlib.Path(path).unlink(missing_ok=True)


# Minute 0 is the first sample. Evaluation minutes are chosen away from the
# threshold edges so a one-sample difference cannot flip the result.
SCENARIOS = [
    Scenario("healthy: 0.05 percent errors", 70, 6000, lambda m: 0.0005, (30, 65)),
    Scenario("fast burn: 3 percent errors for 70 minutes", 70, 6000, lambda m: 0.03, (10, 65)),
    Scenario("slow leak: 0.8 percent errors", 70, 6000, lambda m: 0.008, (30, 65)),
    Scenario("blip: three minutes of total failure, then clean", 70, 6000,
             lambda m: 1.0 if m < 3 else 0.0, (2, 10, 65)),
]


def main():
    ok = True
    for sc in SCENARIOS:
        passed, out = run_promtool(sc)
        print(("PASS " if passed else "FAIL ") + sc.name)
        if not passed:
            print(out)
        ok &= passed
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
