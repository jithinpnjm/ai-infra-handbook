#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

H = 1200
title_text = "Match the symptom to the lifecycle stage"

stages = [
    "Admission",
    "Scheduling",
    "Kubelet admit",
    "Volumes",
    "Sandbox and CNI",
    "Image",
    "Create or start",
    "Run",
    "Readiness",
    "Termination"
]

symptoms = [
    "forbidden, exceeded quota, webhook denied",
    "Pending with no node",
    "OutOf..., NodeAffinity, TopologyAffinityError",
    "ContainerCreating, FailedMount, FailedAttachVolume, Multi-Attach error",
    "FailedCreatePodSandBox",
    "ErrImagePull, ImagePullBackOff",
    "CreateContainerError, RunContainerError, StartError",
    "CrashLoopBackOff, OOMKilled",
    "Running but 0/1",
    "Terminating forever"
]

commands = [
    "API error text, describe resourcequota",
    "describe pod events, taints, Kueue Workload",
    "describe pod, kubelet logs, device plugin health",
    "events, kubectl get volumeattachment, CSI logs",
    "CNI logs, /etc/cni/net.d, IPAM exhaustion, crictl pods",
    "crictl pull, credentials, rate limits, DNS",
    "journalctl -u containerd, runc text",
    "logs --previous, exit codes, dmesg",
    "probe events, app logs",
    "kubelet logs, lsof or fuser on mounts, crictl ps -a"
]

# Splits for wrapping
stage_splits = [
    ["Admission"],
    ["Scheduling"],
    ["Kubelet ", "admit"],
    ["Volumes"],
    ["Sandbox and ", "CNI"],
    ["Image"],
    ["Create or ", "start"],
    ["Run"],
    ["Readiness"],
    ["Termination"]
]

symptom_splits = [
    ["forbidden, exceeded quota, ", "webhook denied"],
    ["Pending with no node"],
    ["OutOf..., NodeAffinity, ", "TopologyAffinityError"],
    ["ContainerCreating, FailedMount, ", "FailedAttachVolume, Multi-Attach error"],
    ["FailedCreatePodSandBox"],
    ["ErrImagePull, ImagePullBackOff"],
    ["CreateContainerError, ", "RunContainerError, StartError"],
    ["CrashLoopBackOff, OOMKilled"],
    ["Running but 0/1"],
    ["Terminating forever"]
]

command_splits = [
    ["API error text, ", "describe resourcequota"],
    ["describe pod events, ", "taints, Kueue Workload"],
    ["describe pod, kubelet logs, ", "device plugin health"],
    ["events, kubectl get ", "volumeattachment, CSI logs"],
    ["CNI logs, /etc/cni/net.d, ", "IPAM exhaustion, crictl pods"],
    ["crictl pull, credentials, ", "rate limits, DNS"],
    ["journalctl -u containerd, ", "runc text"],
    ["logs --previous, ", "exit codes, dmesg"],
    ["probe events, app logs"],
    ["kubelet logs, lsof or ", "fuser on mounts, crictl ps -a"]
]

#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

H = 1200
title_text = "Match the symptom to the lifecycle stage"

stages = [
    "Admission",
    "Scheduling",
    "Kubelet admit",
    "Volumes",
    "Sandbox and CNI",
    "Image",
    "Create or start",
    "Run",
    "Readiness",
    "Termination"
]

symptoms = [
    "forbidden, exceeded quota, webhook denied",
    "Pending with no node",
    "OutOf..., NodeAffinity, TopologyAffinityError",
    "ContainerCreating, FailedMount, FailedAttachVolume, Multi-Attach error",
    "FailedCreatePodSandBox",
    "ErrImagePull, ImagePullBackOff",
    "CreateContainerError, RunContainerError, StartError",
    "CrashLoopBackOff, OOMKilled",
    "Running but 0/1",
    "Terminating forever"
]

commands = [
    "API error text, describe resourcequota",
    "describe pod events, taints, Kueue Workload",
    "describe pod, kubelet logs, device plugin health",
    "events, kubectl get volumeattachment, CSI logs",
    "CNI logs, /etc/cni/net.d, IPAM exhaustion, crictl pods",
    "crictl pull, credentials, rate limits, DNS",
    "journalctl -u containerd, runc text",
    "logs --previous, exit codes, dmesg",
    "probe events, app logs",
    "kubelet logs, lsof or fuser on mounts, crictl ps -a"
]

# Splits for wrapping
stage_splits = [
    ["Admission"],
    ["Scheduling"],
    ["Kubelet ", "admit"],
    ["Volumes"],
    ["Sandbox and ", "CNI"],
    ["Image"],
    ["Create or ", "start"],
    ["Run"],
    ["Readiness"],
    ["Termination"]
]

symptom_splits = [
    ["forbidden, exceeded quota, ", "webhook denied"],
    ["Pending with no node"],
    ["OutOf..., NodeAffinity, ", "TopologyAffinityError"],
    ["ContainerCreating, FailedMount, ", "FailedAttachVolume, Multi-Attach error"],
    ["FailedCreatePodSandBox"],
    ["ErrImagePull, ImagePullBackOff"],
    ["CreateContainerError, ", "RunContainerError, StartError"],
    ["CrashLoopBackOff, OOMKilled"],
    ["Running but 0/1"],
    ["Terminating forever"]
]

command_splits = [
    ["API error text, ", "describe resourcequota"],
    ["describe pod events, ", "taints, Kueue Workload"],
    ["describe pod, kubelet logs, ", "device plugin health"],
    ["events, kubectl get ", "volumeattachment, CSI logs"],
    ["CNI logs, /etc/cni/net.d, ", "IPAM exhaustion, crictl pods"],
    ["crictl pull, credentials, ", "rate limits, DNS"],
    ["journalctl -u containerd, ", "runc text"],
    ["logs --previous, ", "exit codes, dmesg"],
    ["probe events, app logs"],
    ["kubelet logs, lsof or ", "fuser on mounts, crictl ps -a"]
]

svg = []
svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 {H}" width="1600" height="{H}">')
svg.append(f'  <title>{title_text}</title>')
svg.append('  <desc>Ten-row debugging ladder matching Kubernetes pod lifecycle stages to common failure symptoms and their diagnostic commands.</desc>')

# Defs
svg.append('  <defs>')
svg.append('    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
svg.append('      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />')
svg.append('    </marker>')
svg.append('    <marker id="arrow-orange" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
svg.append('      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#db8129" />')
svg.append('    </marker>')
svg.append('  </defs>')

# Background
svg.append(f'  <rect width="1600" height="{H}" fill="#f5f8f5" />')

# Title
svg.append(f'  <text x="800" y="62" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">{title_text}</text>')

# Layout coordinates:
# Rows 1..10
# y starts at 108, row_h = 94, gap = 10
# stage_box: x=40, w=380, h=94
# symptom_box: x=445, w=585, h=94
# arrow: x1=1030, y1=ry+47, x2=1085, y2=ry+47
# command_box: x=1085, w=475, h=94

# Icon definitions (48x48 inside a g transform):
icons = [
    # 1. Admission: Security shield
    '''<path d="M 24 6 L 42 12 V 26 C 42 36 24 44 24 44 C 24 44 6 36 6 26 V 12 Z" stroke="{color}" stroke-width="3.5" fill="none" stroke-linejoin="round"/>
       <circle cx="24" cy="22" r="3.5" fill="{color}"/>
       <line x1="24" y1="26" x2="24" y2="32" stroke="{color}" stroke-width="3" stroke-linecap="round"/>''',
    # 2. Scheduling: Target / Crosshairs placement
    '''<circle cx="24" cy="24" r="18" stroke="{color}" stroke-width="3.5" fill="none"/>
       <line x1="24" y1="6" x2="24" y2="42" stroke="{color}" stroke-width="3" stroke-linecap="round"/>
       <line x1="6" y1="24" x2="42" y2="24" stroke="{color}" stroke-width="3" stroke-linecap="round"/>
       <circle cx="24" cy="24" r="6" fill="{color}"/>''',
    # 3. Kubelet admit: Hardware node check
    '''<rect x="6" y="10" width="36" height="26" rx="4" stroke="{color}" stroke-width="3.5" fill="none"/>
       <line x1="14" y1="36" x2="14" y2="42" stroke="{color}" stroke-width="3.5" stroke-linecap="round"/>
       <line x1="34" y1="36" x2="34" y2="42" stroke="{color}" stroke-width="3.5" stroke-linecap="round"/>
       <line x1="8" y1="42" x2="40" y2="42" stroke="{color}" stroke-width="3.5" stroke-linecap="round"/>
       <circle cx="16" cy="23" r="3" fill="{color}"/>
       <circle cx="24" cy="23" r="3" fill="{color}"/>
       <circle cx="32" cy="23" r="3" fill="{color}"/>''',
    # 4. Volumes: Disk storage cylinder
    '''<ellipse cx="24" cy="12" rx="18" ry="6" stroke="{color}" stroke-width="3.5" fill="none"/>
       <path d="M 6 12 V 36 C 6 41 14 44 24 44 C 34 44 42 41 42 36 V 12" stroke="{color}" stroke-width="3.5" fill="none"/>
       <path d="M 6 24 C 6 29 14 32 24 32 C 34 32 42 29 42 24" stroke="{color}" stroke-width="3.5" fill="none"/>''',
    # 5. Sandbox and CNI: Network nodes connection
    '''<circle cx="12" cy="36" r="6" stroke="{color}" stroke-width="3.5" fill="none"/>
       <circle cx="36" cy="36" r="6" stroke="{color}" stroke-width="3.5" fill="none"/>
       <circle cx="24" cy="12" r="6" stroke="{color}" stroke-width="3.5" fill="none"/>
       <line x1="24" y1="18" x2="12" y2="30" stroke="{color}" stroke-width="3" stroke-linecap="round"/>
       <line x1="24" y1="18" x2="36" y2="30" stroke="{color}" stroke-width="3" stroke-linecap="round"/>
       <line x1="18" y1="36" x2="30" y2="36" stroke="{color}" stroke-width="3" stroke-linecap="round"/>''',
    # 6. Image: Registry package cube
    '''<path d="M 24 6 L 42 16 V 34 L 24 44 L 6 34 V 16 Z" stroke="{color}" stroke-width="3.5" fill="none" stroke-linejoin="round"/>
       <line x1="24" y1="6" x2="24" y2="44" stroke="{color}" stroke-width="2.5"/>
       <line x1="24" y1="25" x2="42" y2="16" stroke="{color}" stroke-width="2.5"/>
       <line x1="24" y1="25" x2="6" y2="16" stroke="{color}" stroke-width="2.5"/>''',
    # 7. Create or start: Terminal execution prompt
    '''<rect x="6" y="8" width="36" height="32" rx="4" stroke="{color}" stroke-width="3.5" fill="none"/>
       <polyline points="14,20 20,24 14,28" stroke="{color}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
       <line x1="24" y1="28" x2="32" y2="28" stroke="{color}" stroke-width="3" stroke-linecap="round"/>''',
    # 8. Run: CPU chip
    '''<rect x="12" y="12" width="24" height="24" rx="3" stroke="{color}" stroke-width="3.5" fill="none"/>
       <rect x="18" y="18" width="12" height="12" rx="2" fill="{color}"/>
       <line x1="18" y1="6" x2="18" y2="12" stroke="{color}" stroke-width="3" stroke-linecap="round"/>
       <line x1="30" y1="6" x2="30" y2="12" stroke="{color}" stroke-width="3" stroke-linecap="round"/>
       <line x1="18" y1="36" x2="18" y2="42" stroke="{color}" stroke-width="3" stroke-linecap="round"/>
       <line x1="30" y1="36" x2="30" y2="42" stroke="{color}" stroke-width="3" stroke-linecap="round"/>
       <line x1="6" y1="18" x2="12" y2="18" stroke="{color}" stroke-width="3" stroke-linecap="round"/>
       <line x1="6" y1="30" x2="12" y2="30" stroke="{color}" stroke-width="3" stroke-linecap="round"/>
       <line x1="36" y1="18" x2="42" y2="18" stroke="{color}" stroke-width="3" stroke-linecap="round"/>
       <line x1="36" y1="30" x2="42" y2="30" stroke="{color}" stroke-width="3" stroke-linecap="round"/>''',
    # 9. Readiness: Health pulse wave
    '''<circle cx="24" cy="24" r="18" stroke="{color}" stroke-width="3.5" fill="none"/>
       <polyline points="10,24 17,24 21,15 27,33 31,24 38,24" stroke="{color}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" fill="none"/>''',
    # 10. Termination: Power off / Stop circle
    '''<circle cx="24" cy="24" r="18" stroke="{color}" stroke-width="3.5" fill="none"/>
       <line x1="24" y1="12" x2="24" y2="24" stroke="{color}" stroke-width="3.5" stroke-linecap="round"/>
       <path d="M 16 16 A 11 11 0 1 0 32 16" stroke="{color}" stroke-width="3.5" fill="none" stroke-linecap="round"/>'''
]

start_y = 108
row_h = 94
gap = 10

for i in range(10):
    ry = start_y + i * (row_h + gap)
    is_orange = (i == 7) # Row 8 (Run) is orange highlight
    # Keep icons and standard stage borders green, use orange specifically for the single most important item / arrow:
    stroke_col = "#207448"
    stroke_w = "2"
    
    sym_stroke = "#db8129" if is_orange else "#207448"
    sym_stroke_w = "3.5" if is_orange else "1.5"
    arrow_stroke = "#db8129" if is_orange else "#207448"
    arrow_marker = "url(#arrow-orange)" if is_orange else "url(#arrow-green)"
    
    svg.append(f'  <!-- ==================== ROW {i+1}: {stages[i]} ==================== -->')
    svg.append(f'  <g id="row-{i+1}">')
    
    # 1. Stage panel: x=40, w=380, h=94
    svg.append(f'    <rect x="40" y="{ry}" width="380" height="{row_h}" rx="12" fill="#e8f1ea" stroke="{stroke_col}" stroke-width="{stroke_w}" />')
    
    # Number circle: cx=76, cy=ry+47, r=24
    svg.append(f'    <circle cx="76" cy="{ry+47}" r="24" fill="#207448" />')
    svg.append(f'    <text x="76" y="{ry+47}" text-anchor="middle" dominant-baseline="central" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">{i+1}</text>')
    
    # Icon: x=114, y=ry+23
    icon_svg = icons[i].format(color="#207448")
    svg.append(f'    <g transform="translate(114, {ry+23})">')
    for line in icon_svg.strip().split('\n'):
        svg.append(f'      {line.strip()}')
    svg.append('    </g>')
    
    # Stage title text: starts at x=176.
    st_lines = stage_splits[i]
    if len(st_lines) == 1:
        svg.append(f'    <text x="176" y="{ry+58}" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">{st_lines[0]}</text>')
    else:
        # Two lines for stage title
        svg.append(f'    <text x="176" y="{ry+44}" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">')
        svg.append(f'      <tspan x="176" dy="0">{st_lines[0]}</tspan>')
        svg.append(f'      <tspan x="176" dy="32">{st_lines[1]}</tspan>')
        svg.append('    </text>')
        
    # 2. Symptom panel: x=445, w=585, h=94
    svg.append(f'    <rect x="445" y="{ry}" width="585" height="{row_h}" rx="12" fill="#ffffff" stroke="{sym_stroke}" stroke-width="{sym_stroke_w}" />')
    
    sym_lines = symptom_splits[i]
    if len(sym_lines) == 1:
        svg.append(f'    <text x="465" y="{ry+56}" font-family="sans-serif" font-size="24" fill="#303a36">{sym_lines[0]}</text>')
    else:
        svg.append(f'    <text x="465" y="{ry+43}" font-family="sans-serif" font-size="24" fill="#303a36">')
        svg.append(f'      <tspan x="465" dy="0">{sym_lines[0]}</tspan>')
        svg.append(f'      <tspan x="465" dy="28">{sym_lines[1]}</tspan>')
        svg.append('    </text>')
        
    # 3. Arrow: from x1=1030 to x2=1085 at y=ry+47
    svg.append(f'    <line x1="1030" y1="{ry+47}" x2="1085" y2="{ry+47}" stroke="{arrow_stroke}" stroke-width="3" marker-end="{arrow_marker}" />')
    
    # 4. Command panel: x=1085, w=475, h=94
    svg.append(f'    <rect x="1085" y="{ry}" width="475" height="{row_h}" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />')
    
    cmd_lines = command_splits[i]
    if len(cmd_lines) == 1:
        svg.append(f'    <text x="1105" y="{ry+56}" font-family="monospace" font-size="24" fill="#207448">{cmd_lines[0]}</text>')
    else:
        svg.append(f'    <text x="1105" y="{ry+43}" font-family="monospace" font-size="24" fill="#207448">')
        svg.append(f'      <tspan x="1105" dy="0">{cmd_lines[0]}</tspan>')
        svg.append(f'      <tspan x="1105" dy="28">{cmd_lines[1]}</tspan>')
        svg.append('    </text>')
        
    svg.append('  </g>')

svg.append('</svg>')

out_path = "p3-0508-pod-stage-symptoms.svg"
with open(out_path, "w") as f:
    f.write("\n".join(svg))

print(f"Generated {out_path} successfully.")

