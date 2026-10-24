#!/usr/bin/env python3
"""Facility arithmetic for GPU racks: circuit capacity, stranded power, airflow, PUE, energy cost.

Reproduces the NVIDIA DGX B200 data-center guide table and the AI Factory (volume 21) examples.
"""
import math


def circuit_kw(volts_ll, amps, derating, pf=0.95):
    """Usable power of one 3-phase circuit: sqrt(3) * V(line-to-line) * I * breaker derating * power factor."""
    return math.sqrt(3) * volts_ll * amps * derating * pf / 1000


def rack_plan(volts_ll, amps, derating, systems, system_kw=14.3, circuits=2):
    cap = circuits * circuit_kw(volts_ll, amps, derating)
    demand = systems * system_kw
    return cap, demand, cap - demand


def cfm_from_kw(kw, cfm_per_kw=150):                  # NVIDIA planning figure at sea level
    return kw * cfm_per_kw


def cfm_sensible(watts, delta_f):                      # AI Factory vol. 21: CFM ~= 3.16 * W / dT(F)
    return 3.16 * watts / delta_f


def pue(total_kw, it_kw):
    return total_kw / it_kw


if __name__ == "__main__":
    print("DGX B200 rack power table (14.3 kW per system, two circuits, power factor 0.95)")
    print(f"{'V(LL)':>6} {'A':>4} {'derate':>7} {'systems':>8} {'capacity kW':>12} {'demand kW':>10} {'stranded kW':>12}")
    for v, a, d, n in [(380, 32, .8, 2), (400, 32, .8, 2), (415, 32, .8, 2), (415, 60, .8, 4), (415, 63, .8, 4),
                       (380, 32, 1.0, 2), (415, 32, 1.0, 2), (415, 60, 1.0, 4), (415, 63, 1.0, 4)]:
        cap, dem, strand = rack_plan(v, a, d, n)
        print(f"{v:>6} {a:>4} {d:>7.0%} {n:>8} {cap:>12.1f} {dem:>10.1f} {strand:>12.1f}")
    print("\nAirflow: 2 B200 per rack =", round(cfm_from_kw(28.6)), "CFM; 4 per rack =", round(cfm_from_kw(57.2)), "CFM (guide: 4290 / 8580)")
    print("Airflow for 81.6 kW IT load, 20 C (36 F) rise:", round(cfm_sensible(81600, 36)), "CFM (vol. 21 text: about 7,160)")
    it = 8 * 10.2
    print(f"\n64-GPU H100 cluster: IT {it:.1f} kW, PUE 1.35 -> facility {it * 1.35:.0f} kW")
    kwh = 16 * 30 * 110 + 4 * 30 * 20 + 4 * 30 * 40
    print(f"Monthly energy {kwh:,} kWh, at $0.12/kWh = ${kwh * 0.12:,.0f}/month, ${kwh * 0.12 * 12:,.0f}/year")
    print("PUE check: 40% IT, 35-40% cooling, rest other  ->  PUE =", round(1 / 0.40, 2), "to", round(1 / 0.45, 2), "(book's rough shares)")
