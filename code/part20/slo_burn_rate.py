"""Burn-rate calculator for SLO alert design. Standard library only.

Run `python3 slo_burn_rate.py` to print the budget table and the alert table.
Numbers follow the Google SRE Workbook chapter "Alerting on SLOs".
"""
import argparse

# (severity, long window h, short window h, burn rate), SRE Workbook Table 5-8
PAGE_TICKET_POLICY = [
    ("page", 1.0, 5 / 60, 14.4),
    ("page", 6.0, 0.5, 6.0),
    ("ticket", 72.0, 6.0, 1.0),
]


def error_budget(slo):
    """Allowed bad fraction, for example 0.001 for a 99.9 percent SLO."""
    if not 0 < slo < 1:
        raise ValueError("slo must be between 0 and 1, exclusive")
    return 1 - slo


def budget_minutes(slo, period_days=30):
    """Minutes of full outage the SLO allows in the period."""
    return error_budget(slo) * period_days * 24 * 60


def burn_rate(error_ratio, slo):
    """How many times faster than allowed the budget is being spent."""
    return error_ratio / error_budget(slo)


def budget_consumed(burn, window_h, period_days=30):
    """Fraction of the period budget spent by running at `burn` for `window_h`."""
    return burn * window_h / (period_days * 24)


def hours_to_exhaustion(burn, period_days=30):
    """Hours until a full budget is gone at a constant burn rate."""
    if burn <= 0:
        return float("inf")
    return period_days * 24 / burn


def error_ratio_threshold(burn, slo):
    """Error ratio an alert rule compares against for a given burn rate."""
    return burn * error_budget(slo)


def minutes_to_detect(true_error_ratio, slo, burn, long_window_h):
    """Minutes after a step change until the long window average crosses the
    threshold, assuming the window was clean before and the error ratio is
    constant. Returns None when the error ratio can never reach it."""
    thr = error_ratio_threshold(burn, slo)
    if true_error_ratio < thr:
        return None
    return thr / true_error_ratio * long_window_h * 60


def should_alert(long_ratio, short_ratio, slo, burn):
    """Multiwindow rule: both windows must be above the threshold."""
    thr = error_ratio_threshold(burn, slo)
    return long_ratio > thr and short_ratio > thr


def alert_table(slo, period_days=30):
    rows = []
    for sev, long_h, short_h, burn in PAGE_TICKET_POLICY:
        rows.append({
            "severity": sev,
            "long_h": long_h,
            "short_h": short_h,
            "burn": burn,
            "threshold": error_ratio_threshold(burn, slo),
            "consumed": budget_consumed(burn, long_h, period_days),
            "exhaust_h": hours_to_exhaustion(burn, period_days),
        })
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--slo", type=float, default=0.999)
    ap.add_argument("--days", type=int, default=30)
    a = ap.parse_args()
    print(f"SLO {a.slo:.4%} over {a.days} days: "
          f"{budget_minutes(a.slo, a.days):.2f} minutes of budget")
    for r in alert_table(a.slo, a.days):
        print(f"{r['severity']:6} long {r['long_h']:5.1f}h short {r['short_h']*60:5.0f}m "
              f"burn {r['burn']:4.1f} ratio>{r['threshold']:.4f} "
              f"budget {r['consumed']:.1%} gone in {r['exhaust_h']:.0f}h")
    m = minutes_to_detect(1.0, a.slo, 14.4, 1.0)
    print(f"Total outage trips the 14.4 page after {m*60:.0f} seconds")


if __name__ == "__main__":
    main()
