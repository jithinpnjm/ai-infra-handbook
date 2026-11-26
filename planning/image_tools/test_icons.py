# Icon definitions (50x50 viewBox or local coords (0,0,50,50))
# Using <g transform="translate(x, y)"> so the inner path is drawn in 0..50 x 0..50!
icons = {
    # 1. Flow: Containers / Database connection
    # Multiple containers connecting to a central database
    "flow": """
        <!-- Database cylinder and incoming client arrow -->
        <ellipse cx="25" cy="12" rx="18" ry="6" fill="none" stroke="#207448" stroke-width="3.5"/>
        <path d="M7 12 v24 c0 3.3 8 6 18 6 s18 -2.7 18 -6 v-24" fill="none" stroke="#207448" stroke-width="3.5"/>
        <path d="M7 24 c0 3.3 8 6 18 6 s18 -2.7 18 -6" fill="none" stroke="#207448" stroke-width="3.5"/>
    """,
    # 2. Arithmetic: Network port / gateway / socket
    "arithmetic": """
        <!-- Network switch / gateway with multiple ports -->
        <rect x="5" y="10" width="40" height="30" rx="4" fill="none" stroke="#207448" stroke-width="3.5"/>
        <line x1="12" y1="20" x2="16" y2="20" stroke="#207448" stroke-width="3.5" stroke-linecap="round"/>
        <line x1="23" y1="20" x2="27" y2="20" stroke="#207448" stroke-width="3.5" stroke-linecap="round"/>
        <line x1="34" y1="20" x2="38" y2="20" stroke="#207448" stroke-width="3.5" stroke-linecap="round"/>
        <line x1="12" y1="28" x2="16" y2="28" stroke="#207448" stroke-width="3.5" stroke-linecap="round"/>
        <line x1="23" y1="28" x2="27" y2="28" stroke="#207448" stroke-width="3.5" stroke-linecap="round"/>
        <line x1="34" y1="28" x2="38" y2="28" stroke="#207448" stroke-width="3.5" stroke-linecap="round"/>
    """,
    # 3. Failure: Timeout / clock alert
    "failure": """
        <!-- Clock face showing timeout -->
        <circle cx="25" cy="25" r="19" fill="none" stroke="#207448" stroke-width="3.5"/>
        <polyline points="25,14 25,25 34,25" fill="none" stroke="#207448" stroke-width="3.5" stroke-linecap="round"/>
        <line x1="6" y1="44" x2="44" y2="6" stroke="#207448" stroke-width="3" stroke-linecap="round"/>
    """,
    # 4. Metaphor: Car park / parking space
    "metaphor": """
        <!-- Parking P sign with stall barriers -->
        <rect x="6" y="6" width="38" height="38" rx="6" fill="none" stroke="#207448" stroke-width="3.5"/>
        <path d="M18 36 V14 h9 c4.4 0 7 2.5 7 6 s-2.6 6 -7 6 h-9" fill="none" stroke="#207448" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>
    """,
    # 5. Fix: Pooler / Wrench / settings
    "fix": """
        <!-- Wrench tool for fix -->
        <path d="M35 7 a9 9 0 0 0 -8 13 l-17 17 a3 3 0 0 0 4 4 l17 -17 a9 9 0 0 0 13 -8 l-5 5 -4 -1 -1 -4 5 -5 a9 9 0 0 0 -4 -4 z" fill="none" stroke="#207448" stroke-width="3.5" stroke-linejoin="round"/>
    """,
    # 6. Lesson: Tuple / checklist / 4 dimensions
    "lesson": """
        <!-- 4-tuple matrix / grid -->
        <rect x="7" y="7" width="36" height="36" rx="4" fill="none" stroke="#207448" stroke-width="3.5"/>
        <line x1="25" y1="7" x2="25" y2="43" stroke="#207448" stroke-width="3.5"/>
        <line x1="7" y1="25" x2="43" y2="25" stroke="#207448" stroke-width="3.5"/>
        <circle cx="16" cy="16" r="3" fill="#207448"/>
        <circle cx="34" cy="16" r="3" fill="#207448"/>
        <circle cx="16" cy="34" r="3" fill="#207448"/>
        <circle cx="34" cy="34" r="3" fill="#207448"/>
    """,
    # P2.1 Symptom: Kubernetes node / CPU chip
    "p2_symptom": """
        <!-- CPU chip with pins -->
        <rect x="12" y="12" width="26" height="26" rx="3" fill="none" stroke="#207448" stroke-width="3.5"/>
        <line x1="18" y1="5" x2="18" y2="12" stroke="#207448" stroke-width="3"/>
        <line x1="32" y1="5" x2="32" y2="12" stroke="#207448" stroke-width="3"/>
        <line x1="18" y1="38" x2="18" y2="45" stroke="#207448" stroke-width="3"/>
        <line x1="32" y1="38" x2="32" y2="45" stroke="#207448" stroke-width="3"/>
        <line x1="5" y1="18" x2="12" y2="18" stroke="#207448" stroke-width="3"/>
        <line x1="5" y1="32" x2="12" y2="32" stroke="#207448" stroke-width="3"/>
        <line x1="38" y1="18" x2="45" y2="18" stroke="#207448" stroke-width="3"/>
        <line x1="38" y1="32" x2="45" y2="32" stroke="#207448" stroke-width="3"/>
        <circle cx="25" cy="25" r="5" fill="#207448"/>
    """,
    # P2.2 Evidence: Terminal window / console
    "p2_evidence": """
        <!-- Terminal prompt window -->
        <rect x="6" y="9" width="38" height="32" rx="4" fill="none" stroke="#207448" stroke-width="3.5"/>
        <line x1="6" y1="18" x2="44" y2="18" stroke="#207448" stroke-width="3"/>
        <polyline points="12,24 17,28 12,32" fill="none" stroke="#207448" stroke-width="3" stroke-linecap="round"/>
        <line x1="22" y1="32" x2="30" y2="32" stroke="#207448" stroke-width="3" stroke-linecap="round"/>
    """,
    # P2.3 Causes: 5-day timer / calendar
    "p2_causes": """
        <!-- Calendar / flow timer -->
        <rect x="7" y="11" width="36" height="32" rx="4" fill="none" stroke="#207448" stroke-width="3.5"/>
        <line x1="7" y1="19" x2="43" y2="19" stroke="#207448" stroke-width="3"/>
        <line x1="16" y1="6" x2="16" y2="11" stroke="#207448" stroke-width="3" stroke-linecap="round"/>
        <line x1="34" y1="6" x2="34" y2="11" stroke="#207448" stroke-width="3" stroke-linecap="round"/>
        <circle cx="25" cy="30" r="6" fill="none" stroke="#207448" stroke-width="2.5"/>
        <polyline points="25,27 25,30 28,30" fill="none" stroke="#207448" stroke-width="2.5" stroke-linecap="round"/>
    """,
    # P2.4 Note: Shield with lock/status
    "p2_note": """
        <!-- Shield for established flow protection -->
        <path d="M25 7 L10 13 V24 C10 33 16 39 25 43 C34 39 40 33 40 24 V13 Z" fill="none" stroke="#207448" stroke-width="3.5" stroke-linejoin="round"/>
        <polyline points="18,24 23,29 32,19" fill="none" stroke="#207448" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
    """,
    # P2.5 Fix: Sliders / tuning knobs
    "p2_fix": """
        <!-- Slider controls for tuning sysctl -->
        <line x1="8" y1="14" x2="42" y2="14" stroke="#207448" stroke-width="3.5" stroke-linecap="round"/>
        <circle cx="18" cy="14" r="5" fill="#f5f8f5" stroke="#207448" stroke-width="3.5"/>
        <line x1="8" y1="25" x2="42" y2="25" stroke="#207448" stroke-width="3.5" stroke-linecap="round"/>
        <circle cx="32" cy="25" r="5" fill="#f5f8f5" stroke="#207448" stroke-width="3.5"/>
        <line x1="8" y1="36" x2="42" y2="36" stroke="#207448" stroke-width="3.5" stroke-linecap="round"/>
        <circle cx="22" cy="36" r="5" fill="#f5f8f5" stroke="#207448" stroke-width="3.5"/>
    """
}

print(f"Defined {len(icons)} icons successfully!")
