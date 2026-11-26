#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

# Let's list the expected labels and verify them
expected_labels = [
    "Cutting a path apart with parameter expansion, no external commands",
    "/data/run42",
    "/",
    "model.final",
    ".",
    "ckpt",
    "${path##*/}",
    "removes the longest matching prefix up to the last slash: result 'model.final.ckpt' (same as basename)",
    "${path%/*}",
    "removes the shortest matching suffix starting at the last slash: result '/data/run42' (same as dirname)",
    "${path%.*}",
    "removes the shortest suffix starting at the last dot: result '/data/run42/model.final'",
    "${path##*.}",
    "removes the longest prefix up to the last dot: result 'ckpt'",
    "# / ## remove shortest / longest prefix",
    "% / %% remove shortest / longest suffix",
    "${#path} length",
    "${var:-default}",
    "${var:=default}",
    "${var:?message}"
]

print(f"Total expected labels: {len(expected_labels)}")
for i, l in enumerate(expected_labels, 1):
    print(f"{i:2d}. {l}")
