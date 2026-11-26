import re
import xml.etree.ElementTree as ET

# We will construct the SVG cleanly.
# Canvas width = 1600, height = 1200.

svg_lines = []
svg_lines.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">')
svg_lines.append('  <title>Choosing a capture point: the closest point that sees what you need</title>')
svg_lines.append('  <desc>A decision tree mapping diagnostic questions to the optimal packet capture point, from client and server interfaces to pod namespaces, hardware mirrors, DPU captures, and kernel tracepoints.</desc>')
svg_lines.append('  <defs>')
svg_lines.append('    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
svg_lines.append('      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />')
svg_lines.append('    </marker>')
svg_lines.append('    <marker id="arrow-orange" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
svg_lines.append('      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#db8129" />')
svg_lines.append('    </marker>')
svg_lines.append('  </defs>')
svg_lines.append('')
svg_lines.append('  <!-- Canvas Background -->')
svg_lines.append('  <rect width="1600" height="1200" fill="#f5f8f5" />')
svg_lines.append('')
svg_lines.append('  <!-- Title (48px bold) -->')
svg_lines.append('  <text x="800" y="52" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Choosing a capture point: the closest point that sees what you need</text>')
svg_lines.append('')

print("Title appended.")
