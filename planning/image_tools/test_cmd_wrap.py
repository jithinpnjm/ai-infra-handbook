#!/usr/bin/env python3

raw_commands = {
    11: "nvidia-smi",
    12: "nvidia-smi dmon -s pucvmet -d 1",
    13: "nvidia-smi topo -m and nvidia-smi nvlink -s",
    14: "dcgmi dmon -e ... or dcgmi diag -r 1",
    15: 'journalctl -k | grep -iE "NVRM|Xid|nvidia"',
    16: "ibstat, ibv_devinfo, rdma link, perfquery or ethtool -S",
    17: "cat /proc/pressure/{cpu,memory,io}",
    18: "numastat, lstopo, cat /proc/cmdline, sysctl -a diff versus baseline"
}

# Proposed wrapping for <= 28 chars:
wrapped_commands = {
    11: ["nvidia-smi"],
    12: ["nvidia-smi dmon", "-s pucvmet -d 1"],
    13: ["nvidia-smi topo -m and", "nvidia-smi nvlink -s"],
    14: ["dcgmi dmon -e ... or", "dcgmi diag -r 1"],
    15: ["journalctl -k |", 'grep -iE "NVRM|Xid|nvidia"'],
    16: ["ibstat, ibv_devinfo,", "rdma link, perfquery or", "ethtool -S"],
    17: ["cat /proc/pressure/", "{cpu,memory,io}"],
    18: ["numastat, lstopo,", "cat /proc/cmdline,", "sysctl -a diff", "versus baseline"]
}

print("Checking wrapped commands:")
for r, lines in wrapped_commands.items():
    joined = " ".join([l.strip() for l in lines])
    orig = " ".join(raw_commands[r].split())
    # verify joined matches orig
    # For line breaking, if we join by space:
    # Notice for cat /proc/pressure/{cpu,memory,io}, if we join by space it would have a space!
    # Wait! In SVG: <text><tspan>cat /proc/pressure/</tspan><tspan>{cpu,memory,io}</tspan></text>
    # itertext() joins without space if no trailing space!
    print(f"Row {r}: max line len = {max(len(l) for l in lines)} chars")
    for l in lines:
        print(f"   '{l}' ({len(l)} chars, {len(l)*14.88:.1f}px)")
        assert len(l) * 14.88 <= 418, f"Line '{l}' too long!"

print("ALL COMMANDS FIT WITHIN 418 PX (<= 28 chars)!")
