#!/usr/bin/env python3
"""Power, BMC, BIOS, firmware and serial console rules from BCM 11 Administrator Manual chapter 4, sections 3.7, 14.5, 14.7, appendix N.

Not BCM. Each part names the manual section it follows. Where the manual is silent the code says so.
"""
import hashlib, ipaddress, os, re, subprocess, tempfile

class HwError(ValueError):
    pass

# ---- 4.1 power control method -------------------------------------------------------------------------------------
BMC_PREFIX = {"ipmi": "IPMI", "ilo": "iLO", "drac": "DRAC", "cimc": "CIMC", "rf": "Redfish"}

def power_method(powercontrol, pdus=(), bmc_ip_mode="static", pdu_manageable=True, power_off_pdu_outlet=False):
    """What actually controls a node's power.
      apc            PDU ports are used
      ipmi0/ilo0/... the BMC is used; configured PDU ports are IGNORED (4.1.2) unless PowerOffPDUOutlet is true,
                     in which case the PDU port is also switched off after the node is off (4.1.3)
      custom         the custom power script (4.1.4)
    A BMC with a DHCP-assigned address is not power-managed by BCM: it needs a custom script (3.7.4)."""
    if powercontrol == "apc":
        return {"method": "pdu", "pdu_ports": list(pdus), "note": "" if pdu_manageable else "PDU not manageable: BMC state shows unknown (4.1.1)"}
    if powercontrol == "custom":
        return {"method": "custom script"}
    m = re.fullmatch(r"(ipmi|ilo|drac|cimc|rf)\d+", powercontrol or "")
    if not m:
        raise HwError(f"power control '{powercontrol}' is not apc, custom, or a BMC interface name (ipmi0, ilo0, drac0, cimc0, rf0)")
    if bmc_ip_mode == "dhcp":
        return {"method": "none by BCM", "note": "a DHCP-assigned BMC address needs custom BMC power management (3.7.4)"}
    out = {"method": BMC_PREFIX[m.group(1)], "pdu_ports": [] if not power_off_pdu_outlet else list(pdus)}
    out["pdu_ports_used_for"] = "switching the outlet off after the node is off" if (power_off_pdu_outlet and pdus) else "ignored"
    return out

def shared_port_targets(port, devices_by_port):
    """4.1.1: if several devices share a PDU port (twin nodes), a power operation on one applies to all of them."""
    return sorted(devices_by_port.get(port, []))

POWER_STATUS = {"ON": "power is on", "OFF": "power is off", "RESET": "the short time the power is off during a reset",
                "FAILED": "power status script communication failure", "UNKNOWN": "power status script timeout"}

# ---- 4.2 scheduling -------------------------------------------------------------------------------------------------
def power_schedule(nodes, delay=1.0, parallel=0, parallel_delay=20.0):
    """4.2.3: with several devices CMDaemon waits `delay` seconds (default 1) between devices. With -p N the devices (or racks) are started
    in batches of N, `parallel_delay` seconds (default 20) between batches, and inside a batch the delay is 0. Returns [(start_second, node)]."""
    out = []
    if parallel:
        for i, n in enumerate(nodes):
            out.append((float((i // parallel) * parallel_delay), n))
    else:
        for i, n in enumerate(nodes):
            out.append((i * delay, n))
    return out

def power_blocked_in_loop(command):
    """2.5.5: power commands are refused inside foreach/range."""
    return command.split()[0] == "power"

def allowed_on_closed(force):
    """4.2: a closed device is skipped by power commands unless -f/--force."""
    return bool(force)

# ---- custom power script contract ---------------------------------------------------------------------------------------
def run_custom_power(script, operation, device, arg=None, env_mac=None):
    """4.1.4: the script is run as `script <operation> <device> [arg]`; operation is ON, OFF, RESET or STATUS; it exits 0 on success and non-zero
    on failure. CMDaemon also sets environment variables such as CMD_MAC. This runs a real script to prove the contract."""
    if operation not in ("ON", "OFF", "RESET", "STATUS"):
        raise HwError("operation must be ON, OFF, RESET or STATUS")
    env = dict(os.environ)
    if env_mac:
        env["CMD_MAC"] = env_mac
    cmd = [script, operation, device] + ([arg] if arg is not None else [])
    r = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=30)
    return r.returncode == 0, r.stdout.strip()

# ---- 3.7 BMC network, settings, credentials -------------------------------------------------------------------------------
BMC_NET = {"base": "10.148.0.0", "bits": 16, "broadcast": "10.148.255.255"}

def addinterface_ips(first_ip, count, increment=1):
    """addinterface -n node001..node150 bmc ipmi0 bmcnet 10.148.0.1 gives sequential addresses; --increment changes the step (3.7.1, 2.5.5)."""
    base = ipaddress.ip_address(first_ip)
    ips = [str(base + i * increment) for i in range(count)]
    net = ipaddress.ip_network(f"{BMC_NET['base']}/{BMC_NET['bits']}")
    bad = [ip for ip in ips if ipaddress.ip_address(ip) not in net]
    if bad:
        raise HwError(f"{bad[0]} is outside the default BMC network {net}")
    return ips

def effective_bmc(node, category, partition):
    """3.7.2: partition settings are the default; category overrides partition; node overrides category. `bmcsettings --show` prints the first
    level that has settings defined and where they came from."""
    for level, src in ((node, "device"), (category, "category"), (partition, "partition")):
        if level:
            return dict(level), src
    return None, "not set"

def credential_fingerprint(password, session_salt):
    """3.7.3: passwords are shown as a short SHA-256 fingerprint salted per cmsh session, so equal passwords look equal inside one session
    and differently in another session."""
    if not password:
        return "<not set>"
    return hashlib.sha256((session_salt + password).encode()).hexdigest()[:12]

def credentials_overview(devices, categories, partition, salt, inverse=False):
    """devices: {name: {'category': c, 'bmc': {...} or None}}."""
    rows = {}
    for name, d in devices.items():
        cfg, src = effective_bmc(d.get("bmc"), categories.get(d.get("category")), partition)
        user = f"{cfg['user']} ({src}{': ' + d['category'] if src == 'category' else ''})" if cfg and cfg.get("user") else "<not set> (partition: base)"
        rows[name] = (user, credential_fingerprint(cfg.get("password") if cfg else None, salt))
    if not inverse:
        return rows
    groups = {}
    for name, key in rows.items():
        groups.setdefault(key, []).append(name)
    return sorted(((len(v), k, sorted(v)) for k, v in groups.items()), key=lambda r: (r[0], r[2]))

# ---- 14.5 BIOS: four states -------------------------------------------------------------------------------------------------
class BiosSettings:
    """Configured (CMDaemon database) --`bios apply`--> Pending (stored in the BIOS) --reboot--> Live. A configured value of <default> (null,
    set by `clear`) does nothing. A model must be set before anything else."""
    def __init__(self, live):
        self.model = None
        self.configured, self.pending, self.live = {}, {}, dict(live)
        self.pending = {}

    def set_model(self, model):
        self.model = model

    def set(self, key, value):
        if not self.model:
            raise HwError("No model defined (set the BIOS model first)")
        if key not in self.live:
            raise HwError(f"unknown BIOS parameter {key}")
        self.configured[key] = value          # takes effect only on commit -> database; modelled as immediate

    def clear(self, key):
        self.configured.pop(key, None)

    def apply(self):
        if not self.model:
            raise HwError("No model defined")
        self.pending.update(self.configured)

    def reboot(self):
        self.live.update(self.pending)
        self.pending = {}

    def status(self, key):
        return (self.configured.get(key, "<default>"), self.pending.get(key, "-"), self.live.get(key))

# ---- 14.5.3 firmware ------------------------------------------------------------------------------------------------------------
FIRMWARE_MODES = {"auto", "b200", "b300", "gb200", "gb200sw", "gb300", "gb300sw", "h100", "iLO", "none"}
FWPKG_DIR = "/cm/local/apps/cmd/etc/htdocs/bios/firmware/"

class FirmwareComponent:
    """available -> flashing (progress) -> pending (needs activation) -> current. For the DGX H100 GPU tray the activation is an AC power cycle:
    a normal `power reset` (a DC power cycle) is not enough."""
    def __init__(self, name, version, needs_ac=True):
        self.name, self.version, self.state, self.progress, self.result = name, version, "current", None, ""
        self.new_version, self.needs_ac = None, needs_ac

    def flash(self, new_version):
        self.new_version, self.state, self.progress = new_version, "flashing", 0.0

    def finish_flash(self):
        self.state, self.progress = "pending", None
        self.result = "success: AC power cycle to activate" if self.needs_ac else "success: reboot to activate"

    def power_cycle(self, kind):
        if self.state != "pending":
            return
        if self.needs_ac and kind != "ac":
            return
        self.version, self.state, self.result, self.new_version = self.new_version, "current", "success: activated", None

def firmware_mode_check(mode):
    if mode not in FIRMWARE_MODES:
        raise HwError(f"firmwaremanagemode must be one of {sorted(FIRMWARE_MODES)}")
    return mode

# ---- 14.7 serial over LAN -------------------------------------------------------------------------------------------------------
def sol_problems(bmc_bios, kernel, node_bios, arch="x86_64", bmc_lan_shared_nic=False, client_on_dedicated_port=False):
    """14.7.1: three places must agree: BMC BIOS, node kernel (the image's SOL settings), node BIOS. Rules of thumb: 115200 bps, flow control on,
    COM1 = ttyS0 (x86_64) / ttyAMA0 (aarch64). BCM cannot configure SOL in the BMC BIOS; a factory reset can break the match."""
    p = []
    keys = ("speed", "flow", "port")
    for k in keys:
        vals = {bmc_bios.get(k), kernel.get(k), node_bios.get(k)}
        if len(vals) > 1:
            p.append(f"SOL {k} differs between BMC BIOS, kernel and node BIOS: {sorted(map(str, vals))}")
    want = "ttyS0" if arch == "x86_64" else "ttyAMA0"
    if kernel.get("port") not in (want, "ttyS1", "ttyAMA1"):
        p.append(f"kernel SOL port {kernel.get('port')} is unusual for {arch}; the manual expects {want} (COM1) or the second port")
    if kernel.get("speed") and int(kernel["speed"]) > 115200:
        p.append("speeds above 115200 are sometimes possible but more likely to have problems")
    if bmc_lan_shared_nic and client_on_dedicated_port:
        p.append("BMC LAN traffic is on the shared NIC: a client on the dedicated BMC port shows no console")
    return p
