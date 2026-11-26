#!/usr/bin/env python3
import re

# Test layout and wrap lines for each label
labels = {
    "center": "one illusion of a giant computer",
    "tile1": "1 Identical software state: same OS image, kernel patch level, GPU driver, NIC firmware",
    "tile2": "2 Synchronized time and identity: chrony or NTP; same numeric UID and GID everywhere",
    "tile3": "3 Predictable naming and networking: DNS, hosts, DHCP and PXE, out-of-band management network, compute fabric",
    "tile4": "4 Uniform shared storage: same mount paths, enforced quotas",
    "tile5": "5 Centralized scheduling and accounting: users never start work on compute nodes directly; scheduler places jobs, isolates them in cgroups, logs usage",
    "tile6": "6 Comprehensive observability: node health, temperatures, power supplies, air conditioning, UPS, fabric symbol errors, GPU faults",
    "tile7": "7 Repeatable provisioning: a replacement server boots into an identical state within minutes",
    "tile8": "8 Spares and SLA discipline: on-site stock of key spares, vendor replacement SLAs",
    "fail1": "clock drift of a few seconds makes ranks disagree and looks like an application bug",
    "fail2": "one node with an older GPU driver runs slightly slower or different and nothing in the job log points to it; compare driver versions",
    "fail3": "a different UID makes a user unable to read their own checkpoint",
}

print("Labels loaded:", len(labels))
