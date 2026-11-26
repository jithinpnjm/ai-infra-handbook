#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

# Test labels
labels = [
    "Eleven long requests leave room for five normal ones",
    "KV arithmetic with 147,456 B per token and a 50.6 GB KV budget (assumed)",
    "One long request: 30,000 tokens = 4.42 GB",
    "One normal request: 2,500 tokens = 0.37 GB",
    "normal requests alone: 50.6 / 0.369 = 137 fit",
    "long requests that fill the GPU: 50.6 / 4.42 = 11",
    "left for others when 11 long run: 50.6 - 48.7 = 1.94 GB = 5 requests",
    "cap at 25 percent of KV: 12.65 / 4.42 = 2 long requests",
    "cap is per replica but the router sends all of the tenant's long requests to one replica: the cap must hold across the pool",
    "shared pool, long-context pool, dedicated endpoint",
    "eleven long requests take capacity from 137 down to 5 for everyone else: the case for charging by cost (tokens x context), not request count"
]

print(f"Total labels: {len(labels)}")
for i, l in enumerate(labels, 1):
    print(f"{i:2d}: '{l}'")
