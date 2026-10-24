#!/usr/bin/env python3
"""Arithmetic and rules from two NVIDIA documents, as testable pieces:
  * DGX SuperPOD Reference Architecture, DGX GB300 (compute, networks, scalable units)
  * Data Center Best Practices with DGX B200 (power, cooling, deployment patterns)
Not a design tool: the documents say the configurations 'must be finalized based on actual design' with an NVIDIA representative. Where I derive a number the code says so.
"""
import math

class SuperpodError(ValueError):
    pass

# ---- GB300 scalable unit -----------------------------------------------------------------------------------------------------
GB300 = {"racks_per_su": 8, "trays_per_rack": 18, "gpus_per_rack": 72, "superchips_per_tray": 2, "gpus_per_superchip": 2, "su_tdp_mw": 1.2, "max_racks": 128, "max_gpus": 9216,
         "cx8_per_tray": 4, "cx8_gbps": 800, "storage_gbps_per_tray": 400, "inband_min_gbps": 200}

def gpus_per_tray():
    return GB300["superchips_per_tray"] * GB300["gpus_per_superchip"]

def gb300_totals(sus):
    """Racks, trays, GPUs and TDP for `sus` scalable units. 72 GPUs per rack = 18 trays x 4 GPUs (derived; the document states 72 per rack and 18 trays)."""
    racks = sus * GB300["racks_per_su"]
    if racks > GB300["max_racks"]:
        raise SuperpodError(f"{racks} racks exceeds the reference architecture's 128 racks")
    return {"racks": racks, "trays": racks * GB300["trays_per_rack"], "gpus": racks * GB300["gpus_per_rack"], "tdp_mw": round(sus * GB300["su_tdp_mw"], 2)}

def gb300_bandwidth_tbps(sus=1):
    """Derived from per-tray port counts: compute fabric 4 x 800 Gb/s per tray; storage 400 Gb/s per tray; in-band at least 200 Gb/s per tray."""
    trays = gb300_totals(sus)["trays"]
    return {"compute_tbps": trays * GB300["cx8_per_tray"] * GB300["cx8_gbps"] / 1000, "storage_tbps": trays * GB300["storage_gbps_per_tray"] / 1000,
            "inband_tbps_min": trays * GB300["inband_min_gbps"] / 1000}

def bluefield_split_ok():
    """The BlueField-3 offers 2 x 400 Gb/s: one 400 Gb/s port to storage, one link of at least 200 Gb/s to in-band (dedicated links, not one bonded interface)."""
    return 400 + 400 >= GB300["storage_gbps_per_tray"] + GB300["inband_min_gbps"]

def su_count_for_gpus(gpus):
    per_su = GB300["racks_per_su"] * GB300["gpus_per_rack"]
    return math.ceil(gpus / per_su)

# ---- B200 power and cooling ------------------------------------------------------------------------------------------------------
B200 = {"kw_per_system": 14.3, "psus": 6, "psus_needed": 5, "su_systems": 32, "cfm_per_kw": 150, "max_systems_full_superpod": 127, "max_supply_air_c": 30}

def rack_kw(systems):
    return round(systems * B200["kw_per_system"], 1)

def su_kw(systems=32):
    """A scalable unit of up to 32 DGX B200 is 458 kW (32 x 14.3 = 457.6)."""
    return round(systems * B200["kw_per_system"])

def cfm(systems=None, kw=None):
    """150 CFM per kW at sea level; about 2145 CFM per system. Actual requirements vary by site."""
    kw = rack_kw(systems) if systems is not None else kw
    return round(kw * B200["cfm_per_kw"])

def circuit_capacity_kw(v_line_to_neutral, amps, derating, pf=0.95):
    """Usable power of one three-phase circuit: 3 x V(L-N) x I x breaker derating x power factor. Derived; it reproduces the document's table values."""
    return 3 * v_line_to_neutral * amps * derating * pf / 1000

def rack_capacity_kw(v_ln, amps, derating, circuits=2):
    return circuits * circuit_capacity_kw(v_ln, amps, derating)

def systems_supported(capacity_kw, patterns=(4, 2)):
    """The deck deploys 2 B200 per rack (typical) or 4 (high density); a rack supports the largest pattern whose peak demand fits the capacity (0 if neither fits).
    This is how the document's 'supported systems per rack' column is built; it is not simply capacity divided by 14.3."""
    for n in patterns:
        if rack_kw(n) <= capacity_kw:
            return n
    return 0

def stranded_kw(capacity_kw, systems):
    return round(capacity_kw - rack_kw(systems), 1)

def n_circuit_ok(systems, circuit_kw):
    """N deployment pattern, 2 circuits: each circuit must handle 50 percent of the rack's peak demand (after derating)."""
    return circuit_kw >= rack_kw(systems) / 2

# ---- PSU and feed resilience ---------------------------------------------------------------------------------------------------------
def feed_map(scheme, systems=2):
    """Which feed (PDU) each of a system's 6 PSUs sits on. Schemes from the deck:
      dual source N       system i entirely on PDU (i mod 2); PDU1 from UPS A, PDU2 from UPS B
      single source       like dual source N, but both PDUs from UPS A
      interleaved         PSUs split 3/3 across PDU1 and PDU2
      6 to make 5         PSU k of every system on its own feed k (six discrete feeds)"""
    out = {}
    for s in range(systems):
        if scheme in ("dual source", "single source"):
            out[s] = [f"PDU{s % 2 + 1}"] * 6
        elif scheme == "interleaved":
            out[s] = ["PDU1", "PDU2", "PDU1", "PDU2", "PDU1", "PDU2"]
        elif scheme == "6 to make 5":
            out[s] = [f"PDU{k + 1}" for k in range(6)]
        else:
            raise SuperpodError("unknown power scheme")
    return out

UPS_OF = {"dual source": {"PDU1": "UPS A", "PDU2": "UPS B"}, "single source": {"PDU1": "UPS A", "PDU2": "UPS A"}, "interleaved": {"PDU1": "UPS A", "PDU2": "UPS B"},
          "6 to make 5": {f"PDU{k}": f"UPS {k}" for k in range(1, 7)}}

def systems_down(scheme, failed, systems=2):
    """A system runs while at least 5 of its 6 PSUs are energized. `failed` is a PDU name or a UPS name."""
    down = []
    for s, feeds in feed_map(scheme, systems).items():
        alive = sum(1 for f in feeds if f != failed and UPS_OF[scheme][f] != failed)
        if alive < B200["psus_needed"]:
            down.append(s)
    return down

def scheme_recommended(scheme):
    """The deck: interleaved is not recommended (more interdependencies); static transfer switch not tested or validated by NVIDIA; '6 to make 5' is optimal for availability but
    often not feasible (six discrete UPS sources, rack space, limited to about 2 systems per rack)."""
    return {"dual source": "OK: fewest interdependencies with two UPS sources", "single source": "OK but a UPS failure takes the whole rack",
            "interleaved": "not recommended", "6 to make 5": "optimal for availability; needs six discrete sources", "static transfer switch": "not tested or validated by NVIDIA"}[scheme]

def supply_air_ok(celsius):
    """DGX B200 allows supply air up to 30 C; recommended ASHRAE range is 18 to 27 C."""
    if celsius > B200["max_supply_air_c"]:
        return "above the allowed 30 C"
    return "recommended range" if 18 <= celsius <= 27 else "allowed but outside the recommended range"

def b200_superpod_max_systems(ufm_appliance=True):
    """A UFM appliance displaces one DGX B200 in the deployment pattern: at most 127 DGX B200 in a full SuperPOD."""
    return B200["max_systems_full_superpod"] if ufm_appliance else 128

# ---- network facts ------------------------------------------------------------------------------------------------------------------------
NETWORKS = {"compute": "Quantum-X800 InfiniBand, rail-optimized full fat tree", "storage": "Spectrum-4 SN5600 Ethernet, RoCEv2, 400 Gb/s per tray", "in-band": "Ethernet, provisioning, user services, NFS tier, at least 200 Gb/s",
            "out-of-band": "SN2201 48 x 1 Gb/s; BMCs, BlueField BMCs, NVSwitch management, PDUs; isolated from users; carries IB and NVLink fabric management"}

def edge_uplink_ok(links, gbps_each=100):
    """Customer edge: at least 2 x 100GbE with DR1 single-mode; eBGP peering for route handover; the building management system traffic flows through the uplink as part of the untrusted zone."""
    return links >= 2 and gbps_each >= 100
