import xml.etree.ElementTree as ET

# Update generator and produce final SVG
with open("build_refined_svg.py") as f:
    code = f.read()

# Replace outcome box dimensions
code = code.replace(
    """    # Outcome 1: probe succeeds: closed again (x=120, y=980, w=420, h=65)
    parts.append('    <!-- Probe Succeeds Box -->')
    parts.append('    <rect x="120" y="980" width="420" height="65" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    parts.append('    <text x="330" y="1021" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">probe succeeds: closed again</text>')
    
    # Outcome 2: probe fails: open again (x=620, y=980, w=360, h=65)
    parts.append('    <!-- Probe Fails Box -->')
    parts.append('    <rect x="620" y="980" width="360" height="65" rx="8" fill="#fff9f2" stroke="#db8129" stroke-width="2" />')
    parts.append('    <text x="800" y="1021" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#db8129">probe fails: open again</text>')
    
    # Return Arrows (non-overlapping, perfectly orthogonal)
    # Path for probe fails:
    # Leaves bottom of Half-open (x=1220, y=940), down to y=1012, left to right edge of probe fails box (x=980, y=1012)
    # Then from left edge of probe fails box (x=620, y=1012), left to x=580, up to bottom of Open box (x=580, y=940)
    parts.append('    <!-- Return Path: probe fails -> Open -->')
    parts.append('    <path d="M 1220 940 L 1220 1012 L 980 1012" fill="none" stroke="#db8129" stroke-width="3.5" marker-end="url(#arrow-orange)" />')
    parts.append('    <path d="M 620 1012 L 580 1012 L 580 948" fill="none" stroke="#db8129" stroke-width="3.5" marker-end="url(#arrow-orange)" />')
    
    # Path for probe succeeds:
    # Leaves bottom of Half-open (x=1400, y=940), down to y=1058 (below probe fails path!), left to x=330, then up to bottom of probe succeeds box (x=330, y=1045)
    # Then from left edge of probe succeeds box (x=120, y=1012), left to x=80, up to bottom of Closed box (x=80, y=940)
    parts.append('    <!-- Return Path: probe succeeds -> Closed -->')
    parts.append('    <path d="M 1400 940 L 1400 1058 L 330 1058 L 330 1045" fill="none" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />')
    parts.append('    <path d="M 120 1012 L 80 1012 L 80 948" fill="none" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />')""",
    """    # Outcome 1: probe succeeds: closed again (x=80, y=980, w=460, h=65)
    parts.append('    <!-- Probe Succeeds Box -->')
    parts.append('    <rect x="80" y="980" width="460" height="65" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    parts.append('    <text x="310" y="1021" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">probe succeeds: closed again</text>')
    
    # Outcome 2: probe fails: open again (x=600, y=980, w=400, h=65)
    parts.append('    <!-- Probe Fails Box -->')
    parts.append('    <rect x="600" y="980" width="400" height="65" rx="8" fill="#fff9f2" stroke="#db8129" stroke-width="2" />')
    parts.append('    <text x="800" y="1021" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#db8129">probe fails: open again</text>')
    
    # Return Arrows (non-overlapping, perfectly orthogonal)
    # Path for probe fails:
    # Leaves bottom of Half-open (x=1220, y=940), down to y=1012, left to right edge of probe fails box (x=1000, y=1012)
    # Then from left edge of probe fails box (x=600, y=1012), left to x=565, up to bottom of Open box (x=565, y=940)
    parts.append('    <!-- Return Path: probe fails -> Open -->')
    parts.append('    <path d="M 1220 940 L 1220 1012 L 1000 1012" fill="none" stroke="#db8129" stroke-width="3.5" marker-end="url(#arrow-orange)" />')
    parts.append('    <path d="M 600 1012 L 565 1012 L 565 948" fill="none" stroke="#db8129" stroke-width="3.5" marker-end="url(#arrow-orange)" />')
    
    # Path for probe succeeds:
    # Leaves bottom of Half-open (x=1400, y=940), down to y=1058 (below probe fails path!), left to x=310, then up to bottom of probe succeeds box (x=310, y=1045)
    # Then from left edge of probe succeeds box (x=80, y=1012), left to x=60, up to bottom of Closed box (x=60, y=940)
    parts.append('    <!-- Return Path: probe succeeds -> Closed -->')
    parts.append('    <path d="M 1400 940 L 1400 1058 L 310 1058 L 310 1045" fill="none" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />')
    parts.append('    <path d="M 80 1012 L 60 1012 L 60 948" fill="none" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />')"""
)

with open("build_refined_svg.py", "w") as f:
    f.write(code)

print("Updated build_refined_svg.py")
