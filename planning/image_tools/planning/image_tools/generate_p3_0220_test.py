#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re
import sys

# Define all content strings exactly as specified in the prompt:
title_text = "Pick the algorithm by the unit of work it counts"
bottom_bar_text = "Name the unit of work first, then pick the algorithm that counts it"
right_panel_title = "Four principles"

principles = [
    # Principle 1
    (
        "choose the metric that represents work: connections, requests, tokens and GPU-seconds differ",
        [
            "choose the metric that",
            "represents work:",
            "connections, requests,",
            "tokens and GPU-seconds",
            "differ"
        ]
    ),
    # Principle 2
    (
        "many LB instances each doing local least connections herd onto the same backend, like drivers following one satnav to one empty car park; a randomised pick breaks it up",
        [
            "many LB instances each",
            "doing local least",
            "connections herd onto",
            "the same backend, like",
            "drivers following one",
            "satnav to one empty car",
            "park; a randomised pick",
            "breaks it up"
        ]
    ),
    # Principle 3
    (
        "hash affinity serves cache locality and state but accepts uneven load: plan for reshuffling with consistent or resilient hashing",
        [
            "hash affinity serves",
            "cache locality and",
            "state but accepts",
            "uneven load: plan for",
            "reshuffling with",
            "consistent or resilient",
            "hashing"
        ]
    ),
    # Principle 4
    (
        "slow start ramps up the weight of a new or recovered backend while its JIT, caches and GPU warm up",
        [
            "slow start ramps up the",
            "weight of a new or",
            "recovered backend while",
            "its JIT, caches and GPU",
            "warm up"
        ]
    )
]

rows_data = [
    # Row 1
    (
        ("Short stateless equal requests", ["Short stateless", "equal requests"]),
        ("round robin or weighted round robin", ["round robin or", "weighted round robin"]),
        ("ignores request cost and backend load", ["ignores request cost", "and backend load"]),
        False
    ),
    # Row 2
    (
        ("Long-lived connections or variable-length requests", ["Long-lived connections", "or variable-length", "requests"]),
        ("least connections", ["least connections"]),
        ("counts connections, not work; needs shared state across LB instances", ["counts connections, not", "work; needs shared state", "across LB instances"]),
        False
    ),
    # Row 3
    (
        ("HTTP or gRPC requests", ["HTTP or gRPC requests"]),
        ("least outstanding requests", ["least outstanding", "requests"]),
        ("same, request-granular", ["same, request-granular"]),
        False
    ),
    # Row 4
    (
        ("Heterogeneous backends", ["Heterogeneous", "backends"]),
        ("least response time, EWMA, peak-EWMA", ["least response time,", "EWMA, peak-EWMA"]),
        ("needs measurement; can oscillate (herding)", ["needs measurement; can", "oscillate (herding)"]),
        False
    ),
    # Row 5 (orange)
    (
        ("Large pools with imperfect load info", ["Large pools with", "imperfect load info"]),
        ("power of two random choices", ["power of two", "random choices"]),
        ("needs load info per backend", ["needs load info", "per backend"]),
        True
    ),
    # Row 6
    (
        ("Session affinity or cache locality", ["Session affinity or", "cache locality"]),
        ("source, URL or header hash", ["source, URL or", "header hash"]),
        ("remaps most keys when N changes", ["remaps most keys", "when N changes"]),
        False
    ),
    # Row 7
    (
        ("Caches, sticky sessions, sharded stores", ["Caches, sticky", "sessions, sharded", "stores"]),
        ("consistent hashing (ring, rendezvous, jump hash)", ["consistent hashing", "(ring, rendezvous,", "jump hash)"]),
        ("load imbalance; virtual nodes help; hot keys", ["load imbalance; virtual", "nodes help; hot keys"]),
        False
    ),
    # Row 8
    (
        ("L4 LBs behind ECMP", ["L4 LBs behind ECMP"]),
        ("Maglev hashing", ["Maglev hashing"]),
        ("table rebuild cost; small disruption on change", ["table rebuild cost;", "small disruption", "on change"]),
        False
    ),
    # Row 9
    (
        ("Cost and latency", ["Cost and latency"]),
        ("locality or zone-aware", ["locality or", "zone-aware"]),
        ("capacity imbalance across zones", ["capacity imbalance", "across zones"]),
        False
    ),
    # Row 10
    (
        ("DR and spillover", ["DR and spillover"]),
        ("priority or failover groups", ["priority or failover", "groups"]),
        ("cold backups", ["cold backups"]),
        False
    ),
    # Row 11
    (
        ("LLM inference", ["LLM inference"]),
        ("load-aware custom: GPU, queue, KV-cache", ["load-aware custom:", "GPU, queue, KV-cache"]),
        ("needs telemetry; careful staleness handling", ["needs telemetry; careful", "staleness handling"]),
        False
    )
]

print("Loaded all data successfully!")
