#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

title = "Hedging buys tail latency with GPU time"

labels = [
    "Hedging buys tail latency with GPU time",
    "request is slow because one replica is slow; after a short delay (only on a per-try timeout) send a second copy to another replica without cancelling the first; use whichever answers first; cancel the loser at once",
    "hedge at the 95th percentile: duplicates 5 percent of requests, p99 from 4.02 to 3.57, about 11 percent better",
    "hedge at the 90th: duplicates 10 percent, p99 from 4.01 to 3.30, about 18 percent better",
    "gain per duplicate is modest and shrinks as the delay grows",
    "a hedge repeats the whole prefill on a second GPU and holds KV cache until the loser is cancelled; 5 percent duplicates is roughly 5 percent more prefill work; a fleet at 80 percent utilisation moves to about 84 percent and queueing delay rises steeply near the top; independence fails exactly when you need hedging most",
    "hedge only before the first token, only for tail time to first token, only below a fleet utilisation threshold, only inside the retry budget"
]

print("Total labels:", len(labels))
for i, l in enumerate(labels, 1):
    print(f"{i}. ({len(l)} chars) {l}")
