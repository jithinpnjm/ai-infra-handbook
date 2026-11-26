import re
import xml.etree.ElementTree as ET

# 15 Expected labels from spec
expected_labels = [
    "Where did my RAM go: reading free and /proc/meminfo",
    "total 1.9Ti  used 120Gi  free 40Gi  shared 1.2Gi  buff/cache 1.7Ti  available 1.7Ti",
    "0B 0B 0B",
    "available",
    "MemAvailable: how much you can use to start new applications without swapping; counts reclaimable page cache and slab",
    "free",
    "idle memory, deliberately small",
    "AnonPages: process private heap and stack",
    "Cached: page cache, including mapped files and tmpfs through Shmem",
    "Slab = SReclaimable (can be freed) + SUnreclaim (cannot)",
    "PageTables and KernelStack: kernel overhead",
    "HugePages_*: explicitly reserved, ordinary allocation cannot use it",
    "Mlocked and Unevictable: reclaim cannot touch",
    "In buff/cache, shared and tmpfs pages and mlocked pages are not reclaimable",
    "Read available, not free"
]

print(f"Total expected labels: {len(expected_labels)}")
for i, l in enumerate(expected_labels):
    print(f"{i:2d}: {l}")
