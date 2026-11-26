"""Test text wrapping and box dimensions for all 14 nodes."""

nodes = [
    ("EV", "Event: CR created/updated/deleted OR owned object changed OR periodic resync"),
    ("RQ", "Work queue (namespace/name)"),
    ("R", "Reconcile(request)"),
    ("G", "Get CR (cache); if gone → return"),
    ("D", "deletionTimestamp set?"),
    ("F", "Run finalizer cleanup → remove finalizer → return"),
    ("FIN", "Ensure finalizer present"),
    ("V", "Validate / default (defensive), resolve references"),
    ("C", "Compute desired children from spec"),
    ("A", "Create/patch/delete children (SSA or CreateOrUpdate), set ownerRefs"),
    ("S", "Observe actual state: children status, external systems"),
    ("U", "Update CR status.conditions, observedGeneration (status subresource)"),
    ("RQR", "Needs requeue?"),
    ("END", "return Result{}")
]

for nid, text in nodes:
    print(f"{nid:5s}: len={len(text):2d} | '{text}'")
