#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

def build_svg():
    lines = []
    lines.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">')
    lines.append('  <title>Two ways to find the broken layer: bottom up, or bisect from the middle</title>')
    lines.append('  <desc>Comparison of bottom-up network layer testing against bisection troubleshooting from the gateway.</desc>')
    
    # Defs
    lines.append('  <defs>')
    lines.append('    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
    lines.append('      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />')
    lines.append('    </marker>')
    lines.append('    <marker id="arrow-orange" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
    lines.append('      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#db8129" />')
    lines.append('    </marker>')
    lines.append('  </defs>')
    
    # Background
    lines.append('  <!-- Canvas Background -->')
    lines.append('  <rect width="1600" height="1200" fill="#f5f8f5" />')
    
    # Title
    lines.append('  <!-- Title -->')
    lines.append('  <text x="800" y="50" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Two ways to find the broken layer: bottom up, or bisect from the middle</text>')
    
    return "\n".join(lines)

print("Builder skeleton ready")
