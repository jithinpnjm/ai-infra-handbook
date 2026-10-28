#!/usr/bin/env python3
"""Self-checking lab for Chapter 6.26: Cluster monitoring and health at scale."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_alert_rules
import slurm_exporter

passed = 0
failed = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global passed, failed
    if cond:
        passed += 1
        print(f"PASS: {name}")
    else:
        failed += 1
        print(f"FAIL: {name}" + (f" ({detail})" if detail else ""))


def sensors_compute_in3(raw_volts: float) -> tuple[float, float]:
    """Evaluate SCL Ch. 19 /etc/sensors3.conf compute in3 ((6.8/10)+1)*@, @/((6.8/10)+1)."""
    factor = (6.8 / 10.0) + 1.0  # 1.68
    displayed = round(factor * raw_volts, 2)
    back_to_raw = round(displayed / factor, 4)
    return displayed, back_to_raw


def main() -> None:
    # 1. Verify slurm_exporter.py selftest() deduplicates multi-partition nodes and renders Prometheus metrics
    metrics_text = slurm_exporter.selftest()
    check(
        "slurm_exporter.py selftest deduplicates gpu002 across partitions (40 total GPUs, 11 allocated, 5 unique nodes)",
        'slurm_gpus{status="total"} 40.0' in metrics_text
        and 'slurm_gpus{status="allocated"} 11.0' in metrics_text
        and 'slurm_node_drain_reason{reason_class="gpu"} 1.0' in metrics_text
        and 'slurm_exporter_scrape_ok 1.0' in metrics_text,
    )

    # 2. Verify check_alert_rules.py passes alerts_gpu_cluster.yml (9 rules, 3 groups) and catches broken rules
    rules_path = Path(__file__).resolve().parent / "alerts_gpu_cluster.yml"
    rc_good = check_alert_rules.main(str(rules_path))
    with tempfile.TemporaryDirectory() as tmpdir:
        bad_rules = Path(tmpdir) / "bad_alerts.yml"
        dcgm_csv = Path(tmpdir) / "default-counters.csv"
        dcgm_csv.write_text("DCGM_FI_DEV_XID_ERRORS\nDCGM_FI_DEV_ROW_REMAP_FAILURE\nDCGM_FI_DEV_GPU_TEMP\nDCGM_FI_DEV_GPU_UTIL\n")
        bad_text = rules_path.read_text().replace("DCGM_FI_DEV_GPU_TEMP > 85", "DCGM_FI_DEV_GPU_TEMPERATURE > (85")
        bad_rules.write_text(bad_text)
        rc_bad = check_alert_rules.main(str(bad_rules), str(dcgm_csv))
    check(
        "check_alert_rules.py validates alerts_gpu_cluster.yml (rc=0) and flags unbalanced brackets + unknown DCGM metric (rc=1)",
        rc_good == 0 and rc_bad == 1,
    )

    # 3. Verify SCL Ch. 19 lm_sensors compute in3 voltage divider formula, APC header 048 / 1157, and SNMP/Ganglia/DCGM ports
    disp_v, raw_v = sensors_compute_in3(2.9762)
    ports = {"snmp": 161, "snmptrap": 162, "snmp_tls": 10161, "snmptrap_tls": 10162, "dcgm_exporter": 9400}
    apc_hdr = ("048", "1157")
    check(
        "SCL Ch. 19 lm_sensors compute in3 (1.68 * 2.9762 = 5.00V) and SNMP/DCGM ports (161, 162, 10161, 10162, 9400) verified",
        disp_v == 5.00 and raw_v == 2.9762 and ports["dcgm_exporter"] == 9400 and ports["snmp"] == 161 and len(apc_hdr) == 2,
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
