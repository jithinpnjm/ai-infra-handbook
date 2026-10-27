#!/usr/bin/env python3
"""Self-checking lab for Chapter 3.8: Building CLIs, agents and exporters."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from python_clis_agents_exporters import (
    CircuitBreaker,
    MockRedfishTransport,
    RedfishSessionClient,
    build_gpuctl_parser,
    carriage_returns,
    collect_fleet_prometheus_metrics,
    evaluate_gpus,
    paginate_cursor,
    parse_smi_csv,
    unnamed_columns,
    zero_count_columns,
)

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


def main() -> None:
    # 1. Practical MLOps Ch. 11 csv-linter checks (zero_count_columns, unnamed_columns, carriage_returns)
    rows = [
        {"Unnamed: 0": "0", "name": "Lewis Cellars", "grape": "NaN", "notes": "Aged in French,\r\nHungarian, and American Oak barrel with long finish"},
        {"Unnamed: 0": "1", "name": "Napa Reserve", "grape": "", "notes": "Crisp acidity"},
    ]
    cr = carriage_returns(rows)
    check(
        "PM Ch. 11 csv-linter detects zero-count 'grape', 1 'Unnamed: 0' column, and carriage return truncated to 50 chars",
        zero_count_columns(rows) == ["grape"]
        and unnamed_columns(rows) == 1
        and cr is not None
        and cr[0] == 0
        and cr[1] == "notes"
        and len(cr[2]) == 50,
    )

    # 2. Section 2.1 gpuctl argparse subcommands (status & drain --dry-run)
    parser = build_gpuctl_parser()
    args_status = parser.parse_args(["-vv", "status", "gpu01", "gpu02", "--output", "json"])
    args_drain = parser.parse_args(["drain", "gpu03", "--timeout", "300", "--dry-run"])
    check(
        "gpuctl parser handles -vv status gpu01 gpu02 --output json and drain gpu03 --timeout 300 --dry-run",
        args_status.verbose == 2
        and args_status.cmd == "status"
        and args_status.hosts == ["gpu01", "gpu02"]
        and args_status.output == "json"
        and args_drain.cmd == "drain"
        and args_drain.host == "gpu03"
        and args_drain.timeout == 300
        and args_drain.dry_run is True,
    )

    # 3. Section 3.3 & 3.4 CircuitBreaker state transitions and cursor pagination (150 items across 2 pages)
    cb = CircuitBreaker(failure_threshold=2)
    for _ in range(2):
        try:
            cb.call(lambda: (_ for _ in ()).throw(ConnectionError("down")))
        except ConnectionError:
            pass
    open_state = cb.state
    cb.allow_half_open_probe()
    half_open_state = cb.state
    res = cb.call(lambda: "recovered")

    pages = {
        None: {"items": list(range(100)), "next_page_token": "p2"},
        "p2": {"items": list(range(100, 150)), "next_page_token": None},
    }
    all_items = list(paginate_cursor(lambda tok, sz: pages[tok], page_size=100))
    check(
        "CircuitBreaker transitions CLOSED -> OPEN -> HALF_OPEN -> CLOSED, and paginate_cursor fetches all 150 items",
        open_state == "OPEN"
        and half_open_state == "HALF_OPEN"
        and cb.state == "CLOSED"
        and res == "recovered"
        and len(all_items) == 150,
    )

    # 4. Section 4.3 Prometheus custom collector (reports fleet_host_up=0 on failed host without raising)
    def fake_temps(host: str):
        if host == "gpu02":
            raise TimeoutError("BMC timeout")
        return {0: 68.0, 1: 72.0}

    metrics = collect_fleet_prometheus_metrics(["gpu01", "gpu02"], fake_temps)
    check(
        "Prometheus collector emits gpu_temperature_celsius for gpu01 and fleet_host_up=0 for failing gpu02",
        'gpu_temperature_celsius{host="gpu01",gpu="0"} 68.0' in metrics
        and 'fleet_host_up{host="gpu01"} 1' in metrics
        and 'fleet_host_up{host="gpu02"} 0' in metrics,
    )

    # 5. Section 5.2 Redfish session login, @odata.id discovery, allowable ResetType validation, and logout cleanup
    transport = MockRedfishTransport()
    with RedfishSessionClient(transport, "admin", "secret") as rf:
        active_during = len(transport.active_sessions)
        sys_info = rf.system()
        rf.power("GracefulRestart")
        bad_reset = False
        try:
            rf.power("InvalidReset")
        except ValueError:
            bad_reset = True
    active_after = len(transport.active_sessions)
    check(
        "RedfishSessionClient logs in, discovers System.Embedded.1, validates AllowableValues, and deletes session on close",
        active_during == 1
        and sys_info["Model"] == "DGX-H100"
        and transport.last_reset == "GracefulRestart"
        and bad_reset is True
        and active_after == 0,
    )

    # 6. Section 10 Capstone parse_smi_csv (handling [N/A]) and evaluate_gpus health rules
    csv_text = (
        "0, NVIDIA H100, 71, 95, 64000, 81920, 0\n"
        "1, NVIDIA H100, 89, [N/A], 64000, 81920, 2\n"
    )
    gpus = parse_smi_csv(csv_text)
    problems = evaluate_gpus(gpus, expected=4, max_temp=85)
    check(
        "parse_smi_csv parses [N/A] as None and evaluate_gpus flags missing GPUs, temp 89C, and uncorrected ECC 2",
        len(gpus) == 2
        and gpus[1].util_pct is None
        and problems == ["expected 4 GPUs, found 2", "gpu1 temp 89C", "gpu1 uncorrected ECC 2"],
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
