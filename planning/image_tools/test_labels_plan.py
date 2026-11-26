#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

# Let us define the labels we have identified
labels = [
    "Expressions: reading values out of the context",
    "cluster.name",
    "opens the drawer cluster and takes the name folder",
    'cluster["name"]',
    "item form",
    "lists",
    "list[0]",
    "list[-1]",
    "list[1:3]",
    "Literals",
    "strings, numbers, true and false (Python True and False also work), none, lists [1, 2], dicts {a: 1}, tuples",
    "arithmetic + - * / // % **",
    "comparison == != < > <= >=",
    "logic and or not",
    "membership in",
    "conditional: {{ a if cond else b }}",
    "is applies a test",
    "join strings with ~, not +: ~ always treats its operands as text so a node number of 1 joins cleanly as gpu ~ 1; + tries arithmetic first and mixing text with a number fails",
    "Use ~ to join text"
]

print(f"Total labels: {len(labels)}")
for i, l in enumerate(labels, 1):
    print(f"{i:2d}. {l}")
