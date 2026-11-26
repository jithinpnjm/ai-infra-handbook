#!/usr/bin/env python3
import re

# Let's write an exact validator script for our planned SVG!

def simulate_svg():
    # Dimensions: 1600 x 1060
    W = 1600
    H = 1060
    
    # Text strings to test:
    t_title = "Three probes for a slow model server"
    t_startup = "startupProbe: periodSeconds 10, failureThreshold 180, up to 30 minutes; liveness and readiness are disabled until it succeeds once"
    t_readiness = "readinessProbe periodSeconds 5: on failure the pod IP leaves the EndpointSlices, container is NOT restarted"
    t_liveness = "livenessProbe periodSeconds 20, failureThreshold 6: restarts only after 2 full minutes of no response"
    t_left_note = "during loading the server downloads or maps weights and captures CUDA graphs"
    t_red_cross = "liveness with no startup probe on a slow starter creates a restart loop"
    t_footer = "Never tie liveness to dependencies"
    
    # Line breaks and text width checks:
    # Rule: sans 0.60 * font_size per character
    # Monospace 0.62 * font_size per character
    
    # 1. Title: 48px bold
    w_title = len(t_title) * 48 * 0.60
    print(f"Title width: {w_title:.1f}px (fits in 1600, margin {(1600-w_title)/2:.1f}px)")
    assert w_title < 1500
    
    # 2. Left Note: in box x=80, y=145, w=650, h=145
    # Icon at x=105, y=185, size 56x56.
    # Text x=185, usable width = 650 - (185 - 80) - 24 = 650 - 105 - 24 = 521 px.
    # font-size: 26px. char_w = 26 * 0.6 = 15.6 px. max chars per line: 521 / 15.6 = 33 chars.
    left_note_lines = [
        "during loading the server downloads or maps",
        "weights and captures CUDA graphs"
    ]
    assert " ".join(left_note_lines) == t_left_note
    print("\nLeft Note lines:")
    for ln in left_note_lines:
        w = len(ln) * 26 * 0.60
        print(f"  '{ln}' : len={len(ln)}, width={w:.1f}px / 521px (padding right {521-w:.1f}px)")
        assert w <= 521
        
    # 3. startupProbe: in box x=80, y=320, w=650, h=280
    # Icon at x=105, y=360, size 56x56.
    # Text x=185, usable width = 521 px.
    # font-size: 26px.
    startup_lines = [
        "startupProbe: periodSeconds 10, failureThreshold 180, ",
        "up to 30 minutes; liveness and readiness ",
        "are disabled until it succeeds once"
    ]
    # Check text joins exactly:
    joined_startup = re.sub(r'\s+', ' ', "".join(startup_lines)).strip()
    assert joined_startup == t_startup
    print("\nstartupProbe lines:")
    for ln in startup_lines:
        w = len(ln.strip()) * 26 * 0.60
        print(f"  '{ln}' : len={len(ln.strip())}, width={w:.1f}px / 521px (padding right {521-w:.1f}px)")
        assert w <= 521

    # 4. Red cross failure note: in box x=80, y=630, w=650, h=155
    # Icon at x=105, y=675, size 56x56.
    # Text x=185, usable width = 521 px.
    # font-size: 26px.
    red_cross_lines = [
        "liveness with no startup probe on a slow ",
        "starter creates a restart loop"
    ]
    joined_red_cross = re.sub(r'\s+', ' ', "".join(red_cross_lines)).strip()
    assert joined_red_cross == t_red_cross
    print("\nRed cross lines:")
    for ln in red_cross_lines:
        w = len(ln.strip()) * 26 * 0.60
        print(f"  '{ln}' : len={len(ln.strip())}, width={w:.1f}px / 521px (padding right {521-w:.1f}px)")
        assert w <= 521

    # 5. readinessProbe: in box x=870, y=210, w=650, h=280
    # Icon at x=895, y=250, size 56x56.
    # Text x=975, usable width = 521 px.
    # font-size: 26px.
    readiness_lines = [
        "readinessProbe periodSeconds 5: on failure ",
        "the pod IP leaves the EndpointSlices, ",
        "container is NOT restarted"
    ]
    joined_readiness = re.sub(r'\s+', ' ', "".join(readiness_lines)).strip()
    assert joined_readiness == t_readiness
    print("\nreadinessProbe lines:")
    for ln in readiness_lines:
        w = len(ln.strip()) * 26 * 0.60
        print(f"  '{ln}' : len={len(ln.strip())}, width={w:.1f}px / 521px (padding right {521-w:.1f}px)")
        assert w <= 521

    # 6. livenessProbe: in box x=870, y=530, w=650, h=280
    # Icon at x=895, y=570, size 56x56.
    # Text x=975, usable width = 521 px.
    # font-size: 26px.
    liveness_lines = [
        "livenessProbe periodSeconds 20, failureThreshold 6: ",
        "restarts only after 2 full minutes of ",
        "no response"
    ]
    joined_liveness = re.sub(r'\s+', ' ', "".join(liveness_lines)).strip()
    assert joined_liveness == t_liveness
    print("\nlivenessProbe lines:")
    for ln in liveness_lines:
        w = len(ln.strip()) * 26 * 0.60
        print(f"  '{ln}' : len={len(ln.strip())}, width={w:.1f}px / 521px (padding right {521-w:.1f}px)")
        assert w <= 521

    # 7. Footer: in bar x=50, y=945, w=1500, h=70
    w_footer = len(t_footer) * 28 * 0.60
    print(f"\nFooter width: {w_footer:.1f}px / 1500px (margin {(1500-w_footer)/2:.1f}px)")
    assert w_footer < 1400

simulate_svg()
