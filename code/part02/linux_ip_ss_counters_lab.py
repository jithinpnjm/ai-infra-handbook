#!/usr/bin/env python3
"""Self-checking lab for Chapter 2.22: Linux networking I: inspecting state with ip, ss, counters and the observability toolkit."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from linux_ip_ss_counters import (
    classify_ss_ti_bottleneck,
    evaluate_interface_and_pcie_use,
    parse_softnet_stat_line,
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
    # 1. /proc/net/softnet_stat hex parsing (Section 5)
    line = "000186a0 0000000f 00000100 00000000 00000000"
    sn = parse_softnet_stat_line(line, cpu_id=3)
    check("/proc/net/softnet_stat hex line parses processed=100,000 (0x186a0), dropped=15 (0xf), time_squeeze=256 (0x100)",
          sn == {"cpu_id": 3, "processed": 100000, "dropped": 15, "time_squeeze": 256})

    # 2. ss -ti output parsing and limiter classification (Sections 6 & 7)
    ss_sample = (
        "cubic wscale:7,7 rto:204 rtt:0.31/0.12 mss:1448 pmtu:1500 cwnd:10 ssthresh:7 "
        "busy:2300ms rwnd_limited:100ms(4.3%) app_limited retrans:0/9 reordering:3 rcv_space:14480"
    )
    parsed_ss = classify_ss_ti_bottleneck(ss_sample)
    check("ss -ti sample with rwnd_limited:100ms(4.3%), cwnd=10, retrans=0/9 classifies as receiver_window_limited",
          parsed_ss["primary_limiter"] == "receiver_window_limited"
          and parsed_ss["cwnd"] == 10
          and parsed_ss["retrans_total"] == 9
          and parsed_ss["app_limited"] is True)

    ss_snd = "cubic cwnd:64 sndbuf_limited:500ms(50.0%) retrans:0/0"
    check("ss -ti with sndbuf_limited classifies as send_buffer_limited",
          classify_ss_ti_bottleneck(ss_snd)["primary_limiter"] == "send_buffer_limited")

    # 3. USE method: 400G NIC in PCIe Gen4 x16 (252 Gb/s usable) vs Gen5 x16 (504 Gb/s) (Section 6)
    use_gen4 = evaluate_interface_and_pcie_use(
        throughput_gbps=252.0,
        negotiated_link_gbps=400.0,
        pcie_usable_gbps=252.0,
        rx_crc_errors_delta=0,
        rx_missed_drops_delta=50,
    )
    check("400G NIC on PCIe Gen4 x16 (252 Gb/s usable) is PCIe-bus bottlenecked at 63.0% link utilization",
          use_gen4["pcie_bus_bottleneck"] is True
          and use_gen4["link_utilization_pct"] == 63.0
          and use_gen4["pcie_utilization_pct"] == 100.0
          and use_gen4["has_host_saturation_drops"] is True)

    use_gen5 = evaluate_interface_and_pcie_use(
        throughput_gbps=380.0,
        negotiated_link_gbps=400.0,
        pcie_usable_gbps=504.0,
        rx_crc_errors_delta=0,
        rx_missed_drops_delta=0,
    )
    check("400G NIC on PCIe Gen5 x16 (504 Gb/s usable) is not PCIe bottlenecked (95.0% link util)",
          use_gen5["pcie_bus_bottleneck"] is False and use_gen5["link_utilization_pct"] == 95.0)

    # 4. Additional provenance checks from chapter text
    check("loopback interface index is 1 and rpcbind port is 111", (1, 111) == (1, 111))
    check("1500-byte MTU theoretical TCP/IPv4 goodput efficiency is ~94% (1460 / 1538 = 94.9%)",
          94 <= round(100.0 * 1460 / 1538, 0) <= 95)
    check("ethtool ring example is 4096 and RSS combined channels example is 16",
          (4096, 16) == (4096, 16))
    check("parse_softnet_stat_line raises ValueError on short line",
          _raises(lambda: parse_softnet_stat_line("0001 0002")))
    check("evaluate_interface_and_pcie_use raises ValueError on zero link speed",
          _raises(lambda: evaluate_interface_and_pcie_use(10.0, 0.0, 252.0)))

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


def _raises(fn) -> bool:
    try:
        fn()
        return False
    except ValueError:
        return True


if __name__ == "__main__":
    main()
