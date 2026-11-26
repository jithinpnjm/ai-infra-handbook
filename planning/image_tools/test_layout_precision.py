# Detailed simulation and verification script
import textwrap

cards = [
    {
        "id": "aid1",
        "col": 0, "row": 0,
        "x": 40, "y": 160, "w": 740, "h": 230,
        "title": "Bottom-up:",
        "lead": "physical, link, network, transport, application;",
        "rest": [
            "when many things fail at once or after a hardware",
            "change; physical problems are cheapest to rule out",
            "(a loose cable or dead optic shows in a light or counter)"
        ],
        "full": "Bottom-up: physical, link, network, transport, application; when many things fail at once or after a hardware change; physical problems are cheapest to rule out (a loose cable or dead optic shows in a light or counter)"
    },
    {
        "id": "aid2",
        "col": 0, "row": 1,
        "x": 40, "y": 430, "w": 740, "h": 140,
        "title": "Top-down:",
        "lead": "when only one application",
        "rest": [
            "misbehaves"
        ],
        "full": "Top-down: when only one application misbehaves"
    },
    {
        "id": "aid3",
        "col": 0, "row": 2,
        "x": 40, "y": 610, "w": 740, "h": 140,
        "title": "Divide and conquer (half-split):",
        "lead": "when",
        "rest": [
            "the path is long"
        ],
        "full": "Divide and conquer (half-split): when the path is long"
    },
    {
        "id": "aid4",
        "col": 0, "row": 3,
        "x": 40, "y": 790, "w": 740, "h": 230,
        "title": "Follow the path:",
        "lead": "trace the actual flow end to",
        "rest": [
            "end, including NAT, overlays and load balancers"
        ],
        "full": "Follow the path: trace the actual flow end to end, including NAT, overlays and load balancers"
    },
    {
        "id": "aid5",
        "col": 1, "row": 0,
        "x": 820, "y": 160, "w": 740, "h": 230,
        "title": "Compare with a working peer:",
        "lead": "diff a good",
        "rest": [
            "node against a bad one; check configs, firmware,",
            "ethtool, sysctls, routes and counters; configuration",
            "drift is the most common root cause in fleets"
        ],
        "full": "Compare with a working peer: diff a good node against a bad one; check configs, firmware, ethtool, sysctls, routes and counters; configuration drift is the most common root cause in fleets",
        "orange": True
    },
    {
        "id": "aid6",
        "col": 1, "row": 1,
        "x": 820, "y": 430, "w": 740, "h": 140,
        "title": "Change one thing at a time,",
        "lead": "and revert",
        "rest": [
            "the experiments that fail"
        ],
        "full": "Change one thing at a time, and revert the experiments that fail"
    },
    {
        "id": "aid7",
        "col": 1, "row": 2,
        "x": 820, "y": 610, "w": 740, "h": 140,
        "title": "Use the packet:",
        "lead": "a capture beats opinion",
        "rest": [],
        "full": "Use the packet: a capture beats opinion"
    },
    {
        "id": "side",
        "col": 1, "row": 3,
        "x": 820, "y": 790, "w": 740, "h": 230,
        "title": "Two engineers, same alert:",
        "lead": "one changes settings",
        "rest": [
            "at once and the evidence is gone by the time the",
            "cause would have shown; the other writes down",
            "the symptom, saves the counters, and only then",
            "changes one thing"
        ],
        "full": "Two engineers, same alert: one changes settings at once and the evidence is gone by the time the cause would have shown; the other writes down the symptom, saves the counters, and only then changes one thing"
    }
]

# Verify fidelity:
for c in cards:
    # reconstruct full text from title, lead, rest
    parts = [c["title"]]
    if c["lead"]:
        parts.append(c["lead"])
    parts.extend(c["rest"])
    reconstructed = " ".join(" ".join(parts).split())
    expected = " ".join(c["full"].split())
    assert reconstructed == expected, f"Mismatch in {c['id']}:\nReconstructed: '{reconstructed}'\nExpected:      '{expected}'"

print("All reconstructed texts match source labels 100% exactly!")
