#!/usr/bin/env python3
"""Rules from BCM 11 Administrator Manual chapter 3 (Configuring the cluster), as small testable functions.

Not BCM and not cmsh. Each function names the manual section it follows. Where the manual is silent, the code
says so and raises or returns None instead of guessing.

  3.2     networks: addresses inside the network, DHCP range, default gateway order, search-domain order,
          interface priority, 'ipaddresses --check' states
  3.3-3.5 bridges, VLANs, bonds: member rules, provisioning-interface rule, bonding modes, miimon
  3.13    disk layout inheritance (node overrides category; 'clear' falls back)
  3.14    fsmounts: category mounts inherited by nodes, how a category mount is removed
  3.16    racks: positions, the top-of-device convention, first free slots
  3.17    GPU settings: slot range syntax, node overrides category, power limit values
  3.20    files placed through the image: category and node paths, node wins
"""
import ipaddress, re

class ConfError(ValueError):
    pass

# ---- 3.2 networks ---------------------------------------------------------------------------------------
class Network:
    def __init__(self, name, base, bits, gateway="0.0.0.0", dyn_start=None, dyn_end=None, layer3=False):
        self.name = name
        self.net = ipaddress.ip_network(f"{base}/{bits}", strict=True)
        self.gateway = ipaddress.ip_address(gateway)
        self.dyn = (ipaddress.ip_address(dyn_start), ipaddress.ip_address(dyn_end)) if dyn_start else None
        self.layer3 = layer3
        if int(self.gateway) and self.gateway not in self.net:
            raise ConfError(f"gateway {gateway} is not inside {self.net}")
        if self.dyn and not (self.dyn[0] in self.net and self.dyn[1] in self.net and self.dyn[0] <= self.dyn[1]):
            raise ConfError("dynamic range must be inside the network and start before it ends")

    def contains(self, ip):
        return ipaddress.ip_address(ip) in self.net

    def check_static(self, ips):
        """Static node addresses must be inside the network and outside the temporary DHCP range (3.2.3, 'not recommended' note)."""
        bad = []
        for ip in ips:
            a = ipaddress.ip_address(ip)
            if a not in self.net:
                bad.append((ip, "outside network"))
            elif self.dyn and self.dyn[0] <= a <= self.dyn[1]:
                bad.append((ip, "inside the dynamic DHCP range"))
        return bad

    def layer3_prefix(self, layer3bits=31):
        """3.2.1: with layer3 on, each device and switch port pair gets a /31 (or /30 with layer3bits 30)."""
        if layer3bits not in (30, 31):
            raise ConfError("the manual names /31 (default) and /30 (some DataDirect switches)")
        return layer3bits


def default_gateway(node_gateway=None, category_gateway=None, network_gateway="0.0.0.0", head_internal_alias="10.141.255.254"):
    """3.2.3: category default gateway wins; else the internal network gateway; if that is unset or 0.0.0.0 the DHCP server
    on the head node hands out 10.141.255.254 (the head node). A node-level value is NOT described in the manual for this
    setting, so it is not modelled."""
    if category_gateway and category_gateway != "0.0.0.0":
        return category_gateway, "category"
    if network_gateway and network_gateway != "0.0.0.0":
        return network_gateway, "network"
    return head_internal_alias, "head node (DHCP default)"


def search_domains(global_net, other_nets, category=(), partition=(), limit=6):
    """3.1.2: sources in order: global network, other networks, category, partition. Domains may carry ':index'. CMDaemon sorts
    by index and writes the 6 with the lowest index, lowest first. Unindexed domains are 'handled automatically': modelled
    here as keeping source order after the indexed ones (my assumption, the manual does not say where they land)."""
    entries = []
    order = 0
    for src, items in (("global", [global_net]), ("network", other_nets), ("category", category), ("partition", partition)):
        for it in items:
            if not it:
                continue
            name, _, idx = it.partition(":")
            entries.append((int(idx) if idx else None, order, name, src))
            order += 1
    indexed = sorted([e for e in entries if e[0] is not None], key=lambda e: (e[0], e[1]))
    plain = [e for e in entries if e[0] is None]
    ordered = indexed + plain
    return [e[2] for e in ordered][:limit], [e[2] for e in ordered][limit:]


IFACE_PRIORITY = {"bridge": 80, "bond": 70, "physical": 60, "vlan": 50, "alias": 40, "tunnel": 30, "netmap": 20, "bmc": 10}

def name_resolution_interface(ifaces):
    """3.2.3 onnetworkpriority: resolution takes place via the interface with the higher value. Defaults by type."""
    best = max(ifaces, key=lambda i: i.get("onnetworkpriority", IFACE_PRIORITY[i["type"]]))
    return best["name"]


def ipaddresses_check(configured, detected):
    """3.2.4: States OK / Mismatch / Not detected / Not configured. DHCP interfaces are OK when an address was detected.
    configured: {iface: ip or 'dhcp'}, detected: {iface: ip}. Returns (rows, exit_code)."""
    rows = []
    for i in sorted(set(configured) | set(detected)):
        c, d = configured.get(i), detected.get(i)
        if c == "dhcp":
            state = "OK" if d else "Not detected"
        elif c and d:
            state = "OK" if c == d else "Mismatch"
        elif c:
            state = "Not detected"
        else:
            state = "Not configured"
        rows.append((i, c, d, state))
    return rows, (0 if all(r[3] == "OK" for r in rows) else 1)


def iperf_pairs(n):
    """3.2.4 cm-iperf.py: n(n-1)/2 pairs, each checked for about 10 s by default."""
    return n * (n - 1) // 2


def iperf_days(n, seconds_per_pair=10, parallel=1):
    return iperf_pairs(n) * seconds_per_pair / parallel / 86400.0

# ---- 3.3-3.5 bridges, VLANs, bonds ---------------------------------------------------------------------
BOND_MODES = {0: "balance-rr", 1: "active-backup", 2: "balance-xor", 3: "broadcast", 4: "802.3ad", 5: "balance-tlb", 6: "balance-alb"}

def validate_interfaces(ifaces):
    """ifaces: list of dicts {name,type,ip,network,members,mode,options,provisioning,member_of}. Returns a list of problems."""
    problems = []
    by = {i["name"]: i for i in ifaces}
    for i in ifaces:
        t = i["type"]
        if t in ("bridge", "bond"):
            for m in i.get("members", []):
                mi = by.get(m)
                if mi is None:
                    problems.append(f"{i['name']}: member {m} does not exist")
                    continue
                if t == "bridge" and (mi.get("ip") not in (None, "", "0.0.0.0") or mi.get("network")):
                    problems.append(f"{i['name']}: bridge member {m} must have empty IP and network (3.3)")
                if t == "bond" and mi.get("provisioning"):
                    problems.append(f"{m} is the provisioning interface and a member of {i['name']}: not allowed (3.5.2)")
        if t == "bond":
            mode = i.get("mode", 0)
            if mode not in BOND_MODES:
                problems.append(f"{i['name']}: bonding mode {mode} is not one of 0-6")
            if re.search(r"(^|\s)mode=", i.get("options", "")):
                problems.append(f"{i['name']}: mode must be set with the mode property, not as option mode=... (commit fails validation, 3.5.1)")
            if mode == 1 and "miimon" not in i.get("options", ""):
                problems.append(f"{i['name']}: active-backup failover needs miimon (off by default); the manual suggests miimon=100 (3.5.7)")
        if t == "vlan" and not i.get("network"):
            problems.append(f"{i['name']}: a VLAN interface still needs a network")
        if t == "bridge" and not re.match(r"^br\d+$", i["name"]):
            problems.append(f"{i['name']}: bridge names take the form br<number> (3.3)")
    return problems

# ---- 3.13 disk layout, 3.14 mounts, 3.20 image files -------------------------------------------------------
def disksetup_for(node_value, category_value):
    """3.13.3: node value overrides category; 'clear' on the node (None here) falls back to the category."""
    return (node_value, "node") if node_value else (category_value, "category")


def merged_mounts(category_mounts, node_mounts):
    """3.14.2: a node lists its category mounts (shown as '[category]') plus its own. Same mountpoint: node entry wins (my reading;
    the manual shows both listed and says to remove a category mount from the category)."""
    out = {mp: (dev, "category") for mp, dev in category_mounts.items()}
    for mp, dev in node_mounts.items():
        out[mp] = (dev, "node")
    return out


def can_remove_mount(mounts, mountpoint):
    dev, src = mounts[mountpoint]
    if src == "category":
        return False, "defined at category level: remove it from the category, not from the node"
    return True, "ok (the umount happens at reboot, not at once)"


def image_file_source(image, target, node=None, category=None, mac=None, present=()):
    """3.20.2: files under /cm/images/<image>/cm/conf/{category/<cat>,node/<node>,node/<MAC with dashes>}/<target> are copied
    just before the finalize stage; node-level overrides category-level."""
    base = f"/cm/images/{image}/cm/conf"
    cands = []
    if mac:
        cands.append(f"{base}/node/{mac.lower().replace(':', '-')}/{target.lstrip('/')}")
    if node:
        cands.append(f"{base}/node/{node}/{target.lstrip('/')}")
    if category:
        cands.append(f"{base}/category/{category}/{target.lstrip('/')}")
    for c in cands:
        if c in present:
            return c
    return None

# ---- 3.16 racks ------------------------------------------------------------------------------------------
class Rack:
    def __init__(self, name, height=42):
        self.name, self.height, self.slots = name, height, {}

    def place(self, device, position, height=1, force=False):
        """3.16.2: position is where the TOP of the device is; a device of height h occupies position..position+h-1 (my reading of
        'top is position'; the manual only says the bottom position is ignored)."""
        span = range(position, position + height)
        if position < 1 or position + height - 1 > self.height:
            raise ConfError(f"{device} does not fit in {self.height}U at {position} with height {height}")
        taken = [u for u in span if u in self.slots]
        if taken and not force:
            raise ConfError(f"U{taken[0]} is used by {self.slots[taken[0]]} (use --force to overlap)")
        for u in span:
            self.slots[u] = device

    def add_positions(self, devices, start=1, height=1):
        """addrackposition: fills devices into the first free slots, starting at --position."""
        pos = start
        for d in devices:
            while any(u in self.slots for u in range(pos, pos + height)):
                pos += 1
            self.place(d, pos, height)
            pos += height

# ---- 3.17 GPU settings ---------------------------------------------------------------------------------------
def parse_gpu_range(text, count):
    """'all' or '*' = every GPU; '3'; '0-2'; '1,3-5'."""
    if text in ("all", "*"):
        return list(range(count))
    out = []
    for part in text.split(","):
        if re.fullmatch(r"\d+", part):
            out.append(int(part))
        elif re.fullmatch(r"\d+-\d+", part):
            a, b = map(int, part.split("-"))
            if a > b:
                raise ConfError(f"range {part} runs backwards")
            out.extend(range(a, b + 1))
        else:
            raise ConfError(f"cannot read GPU range '{part}'")
    bad = [g for g in out if g >= count]
    if bad:
        raise ConfError(f"GPU slot(s) {bad} do not exist on a node with {count} GPUs")
    return sorted(set(out))


def effective_gpu_setting(category_settings, node_settings, gpu, key):
    """3.17.2: node settings override category settings; no value means the hardware default. Settings are lists of (range-text, dict)."""
    def find(settings, count=64):
        val = None
        for rng, d in settings:
            if gpu in parse_gpu_range(rng, count) and key in d:
                val = d[key]
        return val
    n = find(node_settings)
    if n is not None:
        return n, "node"
    c = find(category_settings)
    if c is not None:
        return c, "category"
    return None, "hardware default"


def power_limit_ok(value, minimum, maximum):
    """powerlimit may be min, max, default or a number between min and max."""
    if value in ("min", "max", "default"):
        return True
    return minimum <= float(value) <= maximum

# ---- misc numbers from 3.1 -------------------------------------------------------------------------------------
def file_max_rule_of_thumb(memory_gb):
    """3.1.4: kernel source suggests memory in MB x 10 per MB: 128 GB -> 1,280,000 (the manual rounds 128 GB as 128000 MB)."""
    return int(memory_gb * 1000 * 10)


# ---- 3.6 InfiniBand, mlxconfig, IPoIB (added in gap pass) -------------------------------------------------------------------
def resolve_mlx_extra_values(category_extra=None, node_extra=None, iface_extra=None):
    """3.6.2 (pp. 133-134): persistent Mellanox adapter settings use extra_values keys starting with MLX_.
    Precedence: category.extra_values < node.extra_values < interface.extra_values.
    Boolean values are converted to 1 or 0 when applied to mlxconfig; --desired shows resolved source and value."""
    resolved = {}
    for src, d in (("category", category_extra or {}), ("node", node_extra or {}), ("interface", iface_extra or {})):
        for k, v in d.items():
            if not k.startswith("MLX_"):
                continue
            field = k[4:]
            mlx_val = (1 if v else 0) if isinstance(v, bool) else v
            resolved[field] = {"source": src, "value": v, "mlxconfig_value": mlx_val}
    return resolved


def ipoib_max_mtu(connected_mode=False):
    """3.6.4 (p. 135): by default an InfiniBand interface uses datagram mode (scales better, MTU up to 4k = 4096).
    With connectedmode=yes, MTU is up to 64k = 65536."""
    return 65536 if connected_mode else 4096


# ---- 3.8-3.12 Switches, Cumulus, showport/finddevicebyswitchport/setmacviaswitchport, remotedaemon (added in gap pass) --------
def cumulus_nv_commands(mode, auto_cmds, manual_cmds=(), yaml_file=None):
    """3.9.2 (pp. 153-155): nvconfigurationmode is auto, manual, or file.
    - auto: runs auto_cmds + manual_cmds, applied with 'apply'; only manual_cmds can be deleted with 'nv del'.
    - manual: 'manual' command copies auto_cmds into manual stack; auto stack is ignored; applied with 'apply'.
    - file: uses YAML file (e.g. startup.yaml) over ZTP; 'apply' is not used."""
    mode = mode.lower()
    if mode == "auto":
        return {"effective": [("auto", c) for c in auto_cmds] + [("manual", c) for c in manual_cmds], "uses_apply": True}
    if mode == "manual":
        stack = list(manual_cmds) if manual_cmds else list(auto_cmds)
        return {"effective": [("manual", c) for c in stack], "uses_apply": True}
    if mode == "file":
        if not yaml_file:
            raise ConfError("nvconfigurationmode=file requires nvconfigurationfile (e.g. startup.yaml)")
        return {"effective": [("file", yaml_file)], "uses_apply": False}
    raise ConfError(f"unknown nvconfigurationmode: {mode}")


def find_device_by_switch_port(port_map, queries, uplinks=()):
    """3.9.3 & 3.9.7 (pp. 157, 160-161): uplink ports must be ignored in port-to-device mapping.
    When one port is queried, returns just the hostname; when multiple ports are queried, prefixes each with switch:port."""
    uplink_set = set(uplinks)
    results = []
    for q in queries:
        if q in uplink_set:
            continue
        dev = port_map.get(q)
        if dev:
            results.append(dev if len(queries) == 1 else f"{q} {dev}")
    return results


def set_mac_via_switch_port(devices, discovered_port_macs, force=False, index=0):
    """3.9.8 (p. 161): sets device MAC from switch port table. Without --force, refuses to overwrite an existing MAC.
    --index selects which MAC to pick when a port has multiple MACs."""
    out = {}
    for dev, info in sorted(devices.items()):
        cur_mac = info.get("mac")
        port = info.get("port")
        macs = discovered_port_macs.get(port, [])
        if cur_mac and not force:
            out[dev] = (False, "no force and MAC already set")
        elif not macs or index >= len(macs):
            out[dev] = (False, "no MAC discovered on port")
        else:
            out[dev] = (True, macs[index])
    return out


def remotedaemon_check(defined_as_compute_node, os_distro, ssh_reachable, https_to_active_head):
    """3.10.7 (pp. 164-165): remotedaemon install deploys CMDaemon onto an already-running device (such as a DPU installed by DPF)
    without reprovisioning. Prerequisites: defined in BCM as a compute node, running Ubuntu, SSH reachable from active head,
    and able to reach active head over HTTPS."""
    problems = []
    if not defined_as_compute_node:
        problems.append("target device must already be defined in BCM as a compute node")
    if not os_distro.lower().startswith("ubuntu"):
        problems.append("target must be running Ubuntu")
    if not ssh_reachable:
        problems.append("target must be reachable over SSH from the active head node using device access settings")
    if not https_to_active_head:
        problems.append("target must be able to reach the active head node over HTTPS")
    return problems


# ---- 3.17.3 MIG configuration commands and slice allocation rules (added in gap pass) ----------------------------------------
def mig_reboot_required(gpu_model):
    """3.17.3 (p. 207): on A100 GPUs, pending MIG enable/disable states only become active after a node reboot.
    For H100 and newer GPUs, changes do not require a reboot."""
    return gpu_model.upper().startswith("A100")


def expand_mig_colon_syntax(spec):
    """3.17.3 (pp. 210-212): for a profile '<N>g.<M>gb' (with N <= 7), ':k' (0-indexed) specifies a compute instance of (k+1)
    GPU slices, written '(k+1)c.<profile>'. ':N-1' equals the full '<profile>'. Example: '2g.10gb:0:0' -> '2g.10gb:1c.2g.10gb:1c.2g.10gb'.
    On A100-PCIE-40GB, '7g.40gb:3' is allowed but '7g.40gb:4' is not."""
    parts = spec.split(":")
    base = parts[0]
    m = re.fullmatch(r"(\d+)g\.(\d+)gb(\+me)?", base)
    if not m:
        raise ConfError(f"invalid MIG base profile: {base}")
    n_slices = int(m.group(1))
    if len(parts) == 1:
        return base
    ci_parts = []
    for p in parts[1:]:
        if re.fullmatch(r"\d+", p):
            k = int(p)
            if k < 0 or k >= n_slices:
                raise ConfError(f"compute slice index :{k} out of range for {base}")
            if base == "7g.40gb" and k == 4:
                raise ConfError("on A100-PCIE-40GB, 7g.40gb:4 is not permitted by hardware restrictions (p. 212)")
            ci_slices = k + 1
            ci_parts.append(f"{ci_slices}c.{base}")
        else:
            ci_parts.append(p)
    return ":".join([base] + ci_parts)


def allocate_mig_profiles(profile_spec, max_gpu_slices=7):
    """3.17.3 (pp. 209-213): parses comma- or space-separated MIG profile items like '5*1g.5gb,2g.10gb'.
    Overallocating slices is not possible: any instance whose slice requirement exceeds the remaining slices (out of 7)
    is silently not allocated (e.g. '6*1g.5gb,2g.10gb' allocates 6 of 1g.5gb and 0 of 2g.10gb; '70*1g.5gb,2g.10gb' allocates 7 of 1g.5gb)."""
    tokens = [t.strip() for t in re.split(r"[,\s]+", profile_spec.strip()) if t.strip()]
    allocated = []
    used_slices = 0
    for tok in tokens:
        mult = 1
        if "*" in tok:
            m_str, tok = tok.split("*", 1)
            mult = int(m_str)
        base = tok.split(":", 1)[0]
        m = re.match(r"(\d+)g\.(\d+)gb", base)
        if not m:
            raise ConfError(f"cannot parse MIG profile '{base}'")
        slices = int(m.group(1))
        count = 0
        for _ in range(mult):
            if used_slices + slices <= max_gpu_slices:
                used_slices += slices
                count += 1
        if count:
            allocated.append((base, count, count * slices))
    return {"allocated": allocated, "used_slices": used_slices, "unallocated_slices": max_gpu_slices - used_slices}

