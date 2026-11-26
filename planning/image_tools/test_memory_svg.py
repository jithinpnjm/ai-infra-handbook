import xml.etree.ElementTree as ET
import re

# Let's define the labels exactly:
expected_labels = [
    "Five steps for a memory problem, changing one thing at a time",
    "USE check: utilisation, saturation, errors",
    "Characterise: kernel or user memory, cache or anonymous, top RSS, cgroup limits",
    "Growth or leak?",
    "Growth: normal use at a higher rate, or a cache warming up",
    "Check the configuration, cache sizes and allocator",
    "Leak: allocated and never freed, a bug",
    "Find the allocation path: memleak, jemalloc or tcmalloc profiling, tracemalloc, memray",
    "Check the static setup: DIMMs, NUMA mode, huge pages, overcommit, limits, allocator",
    "Tune last, one change at a time",
    "A memory investigation goes wrong when three settings change at once."
]

step_numbers = {"1", "2", "3", "4", "5"}

forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'callout', 'sub-line', 'subline', 'takeaway']

print("Test setup ready")
