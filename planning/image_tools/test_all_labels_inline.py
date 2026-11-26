import xml.etree.ElementTree as ET
import re

labels_data = [
    # 1. Title
    ('<text x="800" y="58" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36" text-anchor="middle"><tspan x="800" dy="0">Eviction, node pressure and preemption: </tspan><tspan x="800" dy="54">who pulled the trigger</tspan></text>',
     "Eviction, node pressure and preemption: who pulled the trigger"),

    # 2. Row 1 Title
    ('<text x="75" y="254" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448"><tspan x="75" dy="0">API-initiated eviction </tspan><tspan x="75" dy="35">(kubectl drain, </tspan><tspan x="75" dy="35">Cluster Autoscaler, </tspan><tspan x="75" dy="35">Karpenter)</tspan></text>',
     "API-initiated eviction (kubectl drain, Cluster Autoscaler, Karpenter)"),

    # 3. Row 1 Initiator
    ('<text x="530" y="270" font-family="sans-serif" font-size="24" fill="#303a36"><tspan x="530" dy="0">a person or tool via </tspan><tspan x="530" dy="36">the Eviction subresource</tspan></text>',
     "a person or tool via the Eviction subresource"),

    # 4. Row 1 PDB
    ('<text x="975" y="254" font-family="sans-serif" font-size="24" fill="#303a36"><tspan x="975" dy="0">strictly enforced: rejected with 429 </tspan><tspan x="975" dy="35">Too Many Requests if it would break </tspan><tspan x="975" dy="35">minAvailable or maxUnavailable</tspan></text>',
     "strictly enforced: rejected with 429 Too Many Requests if it would break minAvailable or maxUnavailable"),

    # 5. Row 2 Title
    ('<text x="75" y="535" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448"><tspan x="75" dy="0">Kubelet node-pressure </tspan><tspan x="75" dy="38">eviction</tspan></text>',
     "Kubelet node-pressure eviction"),

    # 6. Row 2 Initiator
    ('<text x="530" y="540" font-family="sans-serif" font-size="24" fill="#303a36"><tspan x="530" dy="0">the node, short on </tspan><tspan x="530" dy="36">memory or disk</tspan></text>',
     "the node, short on memory or disk"),

    # 7. Row 2 PDB
    ('<text x="975" y="540" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36"><tspan x="975" dy="0">ignored, node is in </tspan><tspan x="975" dy="36">immediate danger</tspan></text>',
     "ignored, node is in immediate danger"),

    # 8. Row 3 Title
    ('<text x="75" y="825" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Scheduler preemption</text>',
     "Scheduler preemption"),

    # 9. Row 3 Initiator
    ('<text x="530" y="800" font-family="sans-serif" font-size="24" fill="#303a36"><tspan x="530" dy="0">scheduler, a </tspan><tspan x="530" dy="36">higher-priority pod </tspan><tspan x="530" dy="36">needs a place</tspan></text>',
     "scheduler, a higher-priority pod needs a place"),

    # 10. Row 3 PDB
    ('<text x="975" y="794" font-family="sans-serif" font-size="24" fill="#303a36"><tspan x="975" dy="0">best effort: prefers victims that </tspan><tspan x="975" dy="35">do not break a budget, still preempts </tspan><tspan x="975" dy="35">if no other feasible node</tspan></text>',
     "best effort: prefers victims that do not break a budget, still preempts if no other feasible node"),

    # 11. Footer
    ('<text x="800" y="998" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff" text-anchor="middle"><tspan x="800" dy="0">All three end in graceful termination; the reason recorded on the pod tells you </tspan><tspan x="800" dy="36">which path it was; training jobs should treat SIGTERM as checkpoint now</tspan></text>',
     "All three end in graceful termination; the reason recorded on the pod tells you which path it was; training jobs should treat SIGTERM as checkpoint now")
]

for i, (xml, expected) in enumerate(labels_data, 1):
    el = ET.fromstring(xml)
    raw = "".join(el.itertext()).strip()
    reg = re.sub(r'\s+', ' ', raw)
    spl = " ".join(raw.split())
    assert raw == expected, f"Label {i} raw mismatch: {repr(raw)} != {repr(expected)}"
    assert reg == expected, f"Label {i} reg mismatch: {repr(reg)} != {repr(expected)}"
    assert spl == expected, f"Label {i} spl mismatch: {repr(spl)} != {repr(expected)}"
    print(f"[{i:2d}/11] PASS: '{expected[:45]}...'")

print("\nALL 11 LABELS PASS IN ALL THREE STRING-EXTRACTION METHODS!")
