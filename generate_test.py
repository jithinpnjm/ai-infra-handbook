import re, subprocess, pathlib
import xml.etree.ElementTree as ET

# Let us verify all text strings and layout
labels_to_check = [
    "What a network namespace owns",
    "host",
    "red",
    "default",
    "own interfaces",
    "own IP addresses",
    "own routing tables",
    "own ARP and ND neighbour tables",
    "own netfilter rules",
    "own conntrack table",
    "own /proc/net",
    "two containers can both serve on port 8080: each has its own port space",
    "ip netns add red",
    "ip netns exec red ip link",
    "(only a down loopback at first)",
    "ip -n red link set lo up",
    "nsenter -t <pid> -n ip addr enters a container namespace by PID"
]

print("Checking labels definition...")
