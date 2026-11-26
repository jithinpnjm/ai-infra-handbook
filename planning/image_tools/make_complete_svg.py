import sys

def build_svg():
    # Colors:
    # background #f5f8f5
    # text #303a36
    # main green #207448
    # light green panels #e8f1ea
    # one orange #db8129 used only for the single most important item or arrow.
    
    # Let's write the complete SVG
    svg = []
    svg.append('<?xml version="1.0" encoding="UTF-8"?>')
    svg.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">')
    svg.append('  <title>What the kubelet does</title>')
    svg.append('  <desc>Architecture and control flow of the Kubernetes kubelet node agent, including pod sources, per-pod sync workers, managers, runtime CRI integration, probers, and status reporting.</desc>')
    
    # Styles
    svg.append('  <defs>')
    svg.append('    <marker id="arrow" viewBox="0 0 12 12" refX="10" refY="6" markerWidth="9" markerHeight="9" orient="auto-start-reverse">')
    svg.append('      <path d="M 2 2 L 10 6 L 2 10 z" fill="#207448" />')
    svg.append('    </marker>')
    svg.append('    <filter id="shadow" x="-3%" y="-5%" width="106%" height="112%">')
    svg.append('      <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#000" flood-opacity="0.05" />')
    svg.append('    </filter>')
    svg.append('  </defs>')
    
    # Canvas background
    svg.append('  <rect width="1600" height="1200" fill="#f5f8f5" />')
    
    # Title
    svg.append('  <text x="800" y="58" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36" text-anchor="middle">What the kubelet does</text>')
    
    return "\n".join(svg)

print(build_svg()[:300])
