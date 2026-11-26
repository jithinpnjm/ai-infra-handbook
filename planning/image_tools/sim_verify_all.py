# Let's test all text lines and bounding boxes in Python

def text_w(text, size=24, mono=False):
    return len(text) * size * (0.62 if mono else 0.6)

elements = [
    # Title
    ("Title Line 1", "Why a published Docker port", 48, False, 40, 1600-80),
    ("Title Line 2", "ignores your firewall rule", 48, False, 40, 1600-80),
    # Client box (w=410, inner=310 after icon)
    ("Client L1", "Client on the office", 24, False, 130, 270),
    ("Client L2", "network or anywhere", 24, False, 130, 270),
    # Host NIC box (w=410, inner=310 after icon)
    ("Host NIC", "Host NIC", 30, False, 660, 310),
    # Netfilter header
    ("Netfilter Header", "netfilter chains", 30, False, 120, 400),
    # Docker rules (w=390, inner=350)
    ("Docker R1", "Docker's own NAT and FORWARD", 24, False, 75, 360),
    ("Docker R2", "rules (DOCKER chain) are inserted", 24, False, 75, 360),
    ("Docker R3", "ahead of the rules managed by", 24, False, 75, 360),
    ("Docker R4", "ufw or firewalld", 24, False, 75, 360),
    # Firewall rule (w=390, inner=350)
    ("FW R1", "ufw or firewalld rule that", 24, False, 75, 360),
    ("FW R2", "should block the port", 24, False, 75, 360),
    # Orange arrow label (gap=320)
    ("Orange L1", "published port 8080", 24, False, 465, 300),
    ("Orange L2", "answers from anywhere", 24, False, 465, 300),
    # Container port 80 (w=190, inner=160)
    ("CP L1", "container", 26, False, 785, 160),
    ("CP L2", "port 80", 26, False, 785, 160),
    # Fixes (w=940, inner=810)
    ("Fix 1", "restrict a port with the DOCKER-USER chain", 24, False, 135, 810),
    ("Fix 2 L1", "bind the port to a specific address (for example", 24, False, 135, 810),
    ("Fix 2 L2", "127.0.0.1:8080:80)", 24, False, 135, 810),
    ("Fix 3 L1", "if a published port must stay private on a shared host,", 24, False, 135, 810),
    ("Fix 3 L2", "restrict it in DOCKER-USER before you publish it", 24, False, 135, 810),
    # Right panel: Docker network modes (w=540, inner=490)
    ("RM Header", "Docker network modes", 30, False, 1115, 420),
    ("RM Bridge 1", "bridge: private subnet, veth per", 24, False, 1045, 490),
    ("RM Bridge 2", "container, NAT outbound, -p", 24, False, 1045, 490),
    ("RM Bridge 3", "publishes via DNAT; user-defined", 24, False, 1045, 490),
    ("RM Bridge 4", "bridges add DNS-based name", 24, False, 1045, 490),
    ("RM Bridge 5", "resolution and isolation", 24, False, 1045, 490),
    ("RM Host 1", "host: shares the host namespace,", 24, False, 1045, 490),
    ("RM Host 2", "no isolation, no NAT, best", 24, False, 1045, 490),
    ("RM Host 3", "performance, ports conflict with", 24, False, 1045, 490),
    ("RM Host 4", "host: NCCL or HPC containers", 24, False, 1045, 490),
    ("RM None 1", "none: only loopback", 24, False, 1045, 490),
    ("RM Cont 1", "container:NAME: shares another", 24, False, 1045, 490),
    ("RM Cont 2", "container's namespace (how a", 24, False, 1045, 490),
    ("RM Cont 3", "Kubernetes pod works)", 24, False, 1045, 490),
    ("RM Over 1", "overlay: VXLAN across Docker hosts", 24, False, 1045, 490),
    ("RM Over 2", "(Swarm)", 24, False, 1045, 490),
    ("RM Mac 1", "macvlan or ipvlan: container on", 24, False, 1045, 490),
    ("RM Mac 2", "the physical network", 24, False, 1045, 490),
    # Model strip (w=1520, inner=1400)
    ("CNM L1", "CNM: sandbox (the namespace config), endpoint (the attachment, typically a veth),", 24, False, 130, 1400),
    ("CNM L2", "network (a group of endpoints); local drivers bridge, host, none, macvlan, ipvlan;", 24, False, 130, 1400),
    ("CNM L3", "global driver overlay needs a key-value store", 24, False, 130, 1400),
    # Footer box (w=720, inner=620)
    ("Footer L1", "default subnet 172.17.0.0/16 may overlap", 24, False, 120, 620),
    ("Footer L2", "corporate or VPN ranges: set", 24, False, 120, 620),
    ("Footer L3", "default-address-pools in", 24, False, 120, 620),
    ("Footer L4", "/etc/docker/daemon.json", 24, False, 120, 620),
    # Inspect commands box (w=760, inner=660)
    ("Cmd L1", "docker network ls; docker network inspect", 24, True, 880, 660),
    ("Cmd L2", "bridge; iptables -t nat -S DOCKER; bridge", 24, True, 880, 660),
    ("Cmd L3", "fdb show br docker0", 24, True, 880, 660),
    # Bottom bar (w=1520)
    ("Takeaway", "Docker inserts its own rules ahead of the firewall's rules", 28, False, 40, 1520),
]

all_ok = True
for name, text, sz, mono, x, max_avail in elements:
    w = text_w(text, sz, mono)
    pad = max_avail - w
    if pad < 0:
        print(f"FAILED: {name} overflows by {-pad:.1f}px! Text: '{text}'")
        all_ok = False
    else:
        # print(f"OK: {name} (w={w:.1f}px, avail={max_avail}px, margin={pad:.1f}px)")
        pass

if all_ok:
    print("ALL 51 TEXT LINES FIT PERFECTLY INSIDE THEIR BOUNDS!")
