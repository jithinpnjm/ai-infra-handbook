import re

# We will define each node with:
# - id
# - box (x, y, w, h)
# - icon (path / shapes)
# - text lines with (text, size, font_family, is_bold, dy, is_code)
# - style overrides (e.g. orange for PW)

nodes = {
    # Node Lease
    "LEASE": {
        "x": 40, "y": 105, "w": 350, "h": 150,
        "icon": """
            <!-- Heartbeat / Lease -->
            <path d="M 65 180 h 18 l 8 -24 l 12 40 l 12 -28 l 8 12 h 20" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
            <rect x="55" y="140" width="90" height="70" rx="8" fill="none" stroke="#207448" stroke-width="3"/>
        """,
        "lines": [
            {"text": "Node lease +", "fs": 30, "bold": True, "font": "sans-serif", "x": 220, "y": 160},
            {"text": "node status", "fs": 24, "bold": False, "font": "sans-serif", "x": 220, "y": 195},
            {"text": "heartbeats", "fs": 24, "bold": False, "font": "sans-serif", "x": 220, "y": 225}
        ]
    },
    
    # Subgraph Sources Container
    "Sources_box": {
        "x": 410, "y": 95, "w": 1150, "h": 170,
        "title": "Pod sources"
    },
    
    # Sources children:
    "API": {
        "x": 430, "y": 135, "w": 380, "h": 115,
        "icon": """
            <!-- API / Cloud Server -->
            <rect x="445" y="152" width="48" height="34" rx="4" fill="none" stroke="#207448" stroke-width="3"/>
            <line x1="455" y1="174" x2="465" y2="174" stroke="#207448" stroke-width="3" stroke-linecap="round"/>
            <line x1="477" y1="174" x2="483" y2="174" stroke="#207448" stroke-width="3" stroke-linecap="round"/>
            <path d="M 469 186 v 10 M 457 196 h 24" stroke="#207448" stroke-width="3" stroke-linecap="round"/>
        """,
        "lines": [
            {"text": "API server", "fs": 30, "bold": True, "font": "sans-serif", "x": 580, "y": 172},
            {"text": "(watch pods with", "fs": 24, "bold": False, "font": "sans-serif", "x": 620, "y": 208},
            {"text": "spec.nodeName=this node)", "fs": 24, "bold": False, "font": "monospace", "x": 620, "y": 236}
        ]
    },
    "FILE": {
        "x": 830, "y": 135, "w": 340, "h": 115,
        "icon": """
            <!-- Static Manifest Folder -->
            <path d="M 850 162 h 20 l 8 8 h 24 a 4 4 0 0 1 4 4 v 30 a 4 4 0 0 1 -4 4 h -52 a 4 4 0 0 1 -4 -4 v -38 a 4 4 0 0 1 4 -4 z" fill="none" stroke="#207448" stroke-width="3" stroke-linejoin="round"/>
        """,
        "lines": [
            {"text": "Static pod", "fs": 30, "bold": True, "font": "sans-serif", "x": 985, "y": 182},
            {"text": "manifests dir", "fs": 26, "bold": False, "font": "sans-serif", "x": 985, "y": 220}
        ]
    },
    "HTTP": {
        "x": 1190, "y": 135, "w": 350, "h": 115,
        "icon": """
            <!-- HTTP Globe / URL -->
            <circle cx="1225" cy="188" r="24" fill="none" stroke="#207448" stroke-width="3"/>
            <ellipse cx="1225" cy="188" rx="10" ry="24" fill="none" stroke="#207448" stroke-width="2.5"/>
            <line x1="1201" y1="188" x2="1249" y2="188" stroke="#207448" stroke-width="2.5"/>
        """,
        "lines": [
            {"text": "HTTP manifest URL", "fs": 30, "bold": True, "font": "sans-serif", "x": 1375, "y": 182},
            {"text": "(rare)", "fs": 24, "bold": False, "font": "sans-serif", "x": 1375, "y": 220}
        ]
    },
    
    # Row 2:
    "CAD": {
        "x": 40, "y": 295, "w": 440, "h": 120,
        "icon": """
            <!-- cAdvisor Stats / Metrics -->
            <rect x="58" y="325" width="48" height="56" rx="4" fill="none" stroke="#207448" stroke-width="3"/>
            <line x1="68" y1="368" x2="68" y2="352" stroke="#207448" stroke-width="4" stroke-linecap="round"/>
            <line x1="82" y1="368" x2="82" y2="338" stroke="#207448" stroke-width="4" stroke-linecap="round"/>
            <line x1="96" y1="368" x2="96" y2="346" stroke="#207448" stroke-width="4" stroke-linecap="round"/>
        """,
        "lines": [
            {"text": "cAdvisor/cgroup stats", "fs": 30, "bold": True, "font": "sans-serif", "x": 275, "y": 344},
            {"text": "→ /metrics, /stats/summary", "fs": 24, "bold": False, "font": "monospace", "x": 275, "y": 386}
        ]
    },
    "PM": {
        "x": 580, "y": 300, "w": 440, "h": 115,
        "icon": """
            <!-- Pod Manager Merge -->
            <circle cx="610" cy="335" r="7" fill="none" stroke="#207448" stroke-width="3"/>
            <circle cx="610" cy="380" r="7" fill="none" stroke="#207448" stroke-width="3"/>
            <circle cx="640" cy="358" r="7" fill="none" stroke="#207448" stroke-width="3"/>
            <path d="M 617 338 c 12 4 16 12 16 16 M 617 377 c 12 -4 16 -12 16 -15" fill="none" stroke="#207448" stroke-width="3"/>
        """,
        "lines": [
            {"text": "Pod manager", "fs": 30, "bold": True, "font": "sans-serif", "x": 765, "y": 348},
            {"text": "/ config merge", "fs": 26, "bold": False, "font": "sans-serif", "x": 765, "y": 388}
        ]
    },
    "IMG": {
        "x": 1120, "y": 300, "w": 440, "h": 115,
        "icon": """
            <!-- Image GC / Trash -->
            <path d="M 1145 340 h 36 m -24 0 v -8 h 12 v 8 m -16 8 l 4 28 h 20 l 4 -28" fill="none" stroke="#207448" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
            <line x1="1158" y1="352" x2="1158" y2="368" stroke="#207448" stroke-width="2.5"/>
            <line x1="1168" y1="352" x2="1168" y2="368" stroke="#207448" stroke-width="2.5"/>
        """,
        "lines": [
            {"text": "Image GC /", "fs": 30, "bold": True, "font": "sans-serif", "x": 1315, "y": 348},
            {"text": "container GC", "fs": 30, "bold": True, "font": "sans-serif", "x": 1315, "y": 388}
        ]
    },
    
    # Row 3:
    "EV": {
        "x": 40, "y": 460, "w": 440, "h": 115,
        "icon": """
            <!-- Eviction Manager / Alert Shield -->
            <path d="M 65 485 l 20 -8 l 20 8 v 22 c 0 16 -20 28 -20 28 c 0 0 -20 -12 -20 -28 z" fill="none" stroke="#207448" stroke-width="3" stroke-linejoin="round"/>
            <line x1="85" y1="497" x2="85" y2="513" stroke="#207448" stroke-width="3" stroke-linecap="round"/>
            <circle cx="85" cy="523" r="2" fill="#207448"/>
        """,
        "lines": [
            {"text": "Eviction manager", "fs": 30, "bold": True, "font": "sans-serif", "x": 275, "y": 508},
            {"text": "(node pressure)", "fs": 24, "bold": False, "font": "sans-serif", "x": 275, "y": 548}
        ]
    },
    "PW": {
        # THE ORANGE ACCENT NODE!
        "x": 560, "y": 450, "w": 480, "h": 135,
        "is_orange": True,
        "icon": """
            <!-- Per-Pod Workers / Gears in Orange -->
            <circle cx="605" cy="517" r="16" fill="none" stroke="#db8129" stroke-width="4"/>
            <path d="M 605 493 v 8 m 0 32 v 8 m -24 -24 h 8 m 32 0 h 8 m -20 -14 l 6 6 m 16 16 l 6 6 m -28 0 l 6 -6 m 16 -16 l 6 -6" stroke="#db8129" stroke-width="3.5" stroke-linecap="round"/>
            <circle cx="605" cy="517" r="6" fill="#db8129"/>
        """,
        "lines": [
            {"text": "Per-pod workers", "fs": 32, "bold": True, "font": "sans-serif", "x": 780, "y": 505, "fill": "#db8129"},
            {"text": "(syncPod)", "fs": 26, "bold": True, "font": "monospace", "x": 780, "y": 548, "fill": "#303a36"}
        ]
    },
    "CRI": {
        "x": 1120, "y": 460, "w": 440, "h": 115,
        "icon": """
            <!-- Container Box -->
            <path d="M 1145 492 l 22 -10 l 22 10 v 26 l -22 10 l -22 -10 z" fill="none" stroke="#207448" stroke-width="3" stroke-linejoin="round"/>
            <line x1="1167" y1="482" x2="1167" y2="528" stroke="#207448" stroke-width="2.5"/>
            <line x1="1145" y1="492" x2="1167" y2="505" stroke="#207448" stroke-width="2.5"/>
            <line x1="1189" y1="492" x2="1167" y2="505" stroke="#207448" stroke-width="2.5"/>
        """,
        "lines": [
            {"text": "CRI client →", "fs": 30, "bold": True, "font": "sans-serif", "x": 1320, "y": 508},
            {"text": "containerd/CRI-O", "fs": 26, "bold": False, "font": "monospace", "x": 1320, "y": 548}
        ]
    },
    
    # Row 4:
    "VM": {
        "x": 40, "y": 620, "w": 440, "h": 125,
        "icon": """
            <!-- Storage Cylinder Stack -->
            <ellipse cx="80" cy="655" rx="22" ry="8" fill="none" stroke="#207448" stroke-width="3"/>
            <path d="M 58 655 v 16 c 0 4.4 9.8 8 22 8 s 22 -3.6 22 -8 v -16" fill="none" stroke="#207448" stroke-width="3"/>
            <path d="M 58 671 v 16 c 0 4.4 9.8 8 22 8 s 22 -3.6 22 -8 v -16" fill="none" stroke="#207448" stroke-width="3"/>
        """,
        "lines": [
            {"text": "Volume manager", "fs": 30, "bold": True, "font": "sans-serif", "x": 275, "y": 660},
            {"text": "(CSI, emptyDir,", "fs": 24, "bold": False, "font": "sans-serif", "x": 275, "y": 698},
            {"text": "configmap...)", "fs": 24, "bold": False, "font": "sans-serif", "x": 275, "y": 728}
        ]
    },
    "PLEG": {
        "x": 1120, "y": 620, "w": 440, "h": 120,
        "icon": """
            <!-- PLEG Relist Cycle -->
            <path d="M 1145 680 a 20 20 0 1 1 36 10" fill="none" stroke="#207448" stroke-width="3.5" stroke-linecap="round"/>
            <path d="M 1184 682 l -4 10 l -10 -4" fill="none" stroke="#207448" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
            <circle cx="1165" cy="680" r="4" fill="#207448"/>
        """,
        "lines": [
            {"text": "PLEG: relist container", "fs": 30, "bold": True, "font": "sans-serif", "x": 1325, "y": 668},
            {"text": "states → events", "fs": 26, "bold": False, "font": "sans-serif", "x": 1325, "y": 710}
        ]
    },
    
    # Row 5:
    "DM": {
        "x": 40, "y": 780, "w": 440, "h": 130,
        "icon": """
            <!-- CPU / Device Chip -->
            <rect x="58" y="818" width="44" height="44" rx="5" fill="none" stroke="#207448" stroke-width="3"/>
            <rect x="68" y="828" width="24" height="24" rx="2" fill="none" stroke="#207448" stroke-width="2.5"/>
            <!-- Pins -->
            <line x1="68" y1="812" x2="68" y2="818" stroke="#207448" stroke-width="3"/>
            <line x1="80" y1="812" x2="80" y2="818" stroke="#207448" stroke-width="3"/>
            <line x1="92" y1="812" x2="92" y2="818" stroke="#207448" stroke-width="3"/>
            <line x1="68" y1="862" x2="68" y2="868" stroke="#207448" stroke-width="3"/>
            <line x1="80" y1="862" x2="80" y2="868" stroke="#207448" stroke-width="3"/>
            <line x1="92" y1="862" x2="92" y2="868" stroke="#207448" stroke-width="3"/>
        """,
        "lines": [
            {"text": "Resource managers", "fs": 30, "bold": True, "font": "sans-serif", "x": 275, "y": 822},
            {"text": "CPU / memory /", "fs": 24, "bold": False, "font": "sans-serif", "x": 275, "y": 860},
            {"text": "topology / device", "fs": 24, "bold": False, "font": "sans-serif", "x": 275, "y": 892}
        ]
    },
    "PR": {
        "x": 580, "y": 780, "w": 440, "h": 125,
        "icon": """
            <!-- Prober / Stethoscope / Pulse -->
            <circle cx="612" cy="832" r="14" fill="none" stroke="#207448" stroke-width="3"/>
            <path d="M 612 846 v 14 a 8 8 0 0 0 16 0 v -18" fill="none" stroke="#207448" stroke-width="3" stroke-linecap="round"/>
            <circle cx="636" cy="840" r="5" fill="#207448"/>
        """,
        "lines": [
            {"text": "Prober", "fs": 30, "bold": True, "font": "sans-serif", "x": 785, "y": 830},
            {"text": "(startup/readiness/liveness)", "fs": 24, "bold": False, "font": "sans-serif", "x": 785, "y": 872}
        ]
    },
    "SM": {
        "x": 1120, "y": 780, "w": 440, "h": 125,
        "icon": """
            <!-- Status Manager / Checklist -->
            <rect x="1145" y="818" width="42" height="52" rx="4" fill="none" stroke="#207448" stroke-width="3"/>
            <line x1="1157" y1="835" x2="1175" y2="835" stroke="#207448" stroke-width="2.5" stroke-linecap="round"/>
            <line x1="1157" y1="848" x2="1175" y2="848" stroke="#207448" stroke-width="2.5" stroke-linecap="round"/>
            <line x1="1157" y1="860" x2="1171" y2="860" stroke="#207448" stroke-width="2.5" stroke-linecap="round"/>
        """,
        "lines": [
            {"text": "Status manager", "fs": 30, "bold": True, "font": "sans-serif", "x": 1330, "y": 835},
            {"text": "→ API server", "fs": 26, "bold": False, "font": "sans-serif", "x": 1330, "y": 878}
        ]
    },
    
    # Row 6:
    "KAPI": {
        "x": 150, "y": 960, "w": 1300, "h": 150,
        "icon": """
            <!-- HTTPS Server :10250 Lock & Terminal -->
            <rect x="180" y="1005" width="56" height="60" rx="6" fill="none" stroke="#207448" stroke-width="3.5"/>
            <path d="M 194 1005 v -14 a 14 14 0 0 1 28 0 v 14" fill="none" stroke="#207448" stroke-width="3.5"/>
            <circle cx="208" cy="1035" r="4" fill="#207448"/>
            <line x1="208" y1="1039" x2="208" y2="1052" stroke="#207448" stroke-width="3"/>
        """,
        "lines": [
            {"text": "Kubelet HTTPS server :10250", "fs": 30, "bold": True, "font": "sans-serif", "x": 750, "y": 1018},
            {"text": "(logs, exec, attach, port-forward, metrics, pods)", "fs": 24, "bold": False, "font": "sans-serif", "x": 750, "y": 1068}
        ]
    }
}

print("Node dictionary populated.")
