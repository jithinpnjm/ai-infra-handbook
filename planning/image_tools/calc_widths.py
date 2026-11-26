#!/usr/bin/env python3
"""Calculate exact positions and paddings for the SVG infographic."""

def mono_w(text, fs=24):
    return len(text) * fs * 0.62

def sans_w(text, fs=24):
    return len(text) * fs * 0.60

print("=== MONOSPACE WIDTHS (fs=24) ===")
cols = ["metadata.resourceVersion", "metadata.generation", "status.observedGeneration"]
for c in cols:
    w = mono_w(c, 26)
    print(f"{c:28s} (fs=26): {w:.1f}px")

print("\n=== CELL LOGIC WIDTHS (fs=24) ===")
logic = [
    "resourceVersion changes on every write (metadata, spec or status)",
    "generation increments only when spec changes",
    "observedGeneration is written by the controller to record the generation it last reconciled"
]
for l in logic:
    print(f"'{l}': len={len(l)}, sans_w={sans_w(l, 24):.1f}px")

print("\n=== EVENT WIDTHS (fs=26) ===")
events = [
    "spec edit",
    "label edit",
    "status write by controller",
    "controller finishes reconcile"
]
for e in events:
    print(f"'{e}': len={len(e)}, sans_w={sans_w(e, 26):.1f}px")

print("\n=== STATUS WIDTHS (fs=24) ===")
statuses = [
    "controller has not caught up",
    "status reflects the latest spec"
]
for s in statuses:
    print(f"'{s}': len={len(s)}, sans_w={sans_w(s, 24):.1f}px")

print("\n=== SIDE NOTES WIDTHS (fs=24) ===")
notes = [
    "resourceVersion is opaque, compare only for equality, derived from the etcd mod_revision",
    "uid identifies one instance; a recreated object gets a new uid",
    "kubectl rollout status uses this"
]
for n in notes:
    print(f"'{n}': len={len(n)}, sans_w={sans_w(n, 24):.1f}px")
