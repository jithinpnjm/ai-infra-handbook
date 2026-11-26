import xml.etree.ElementTree as ET
import re

title = "Histogram buckets: keep le, then take the quantile once"

spec_labels = [
    "Histogram buckets: keep le, then take the quantile once",
    "Each box counts every request at or under its bound: cumulative",
    "histogram_quantile interpolates inside the bucket that holds the quantile",
    "Trap: sum by (model) drops le",
    "Breaks histogram_quantile",
    "Right: sum by (le, model)",
    "Keep le in the by clause, then take the quantile once",
    "Pod A buckets",
    "Pod B buckets",
    "rate per series",
    "sum by (le, model)",
    "histogram_quantile(0.99)",
    "le stands for less than or equal to."
]

print(f"Total expected labels: {len(spec_labels)}")
for i, l in enumerate(spec_labels, 1):
    print(f"{i:2d}. '{l}'")
