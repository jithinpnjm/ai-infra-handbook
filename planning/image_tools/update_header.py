#!/usr/bin/env python3
import xml.etree.ElementTree as ET

def generate_and_audit():
    with open("test_connection_fails.svg", "r") as f:
        svg_content = f.read()
    
    # Replace the header text y coordinates
    # Col 1:
    svg_content = svg_content.replace(
        '<text x="525" y="210" text-anchor="middle" font-size="28" font-weight="bold" fill="#ffffff" font-family="sans-serif">\n      <tspan x="525" dy="0">Error the</tspan>\n      <tspan x="525" dy="30">client sees</tspan>',
        '<text x="525" y="202" text-anchor="middle" font-size="28" font-weight="bold" fill="#ffffff" font-family="sans-serif">\n      <tspan x="525" dy="0">Error the</tspan>\n      <tspan x="525" dy="28">client sees</tspan>'
    )
    # Col 2:
    svg_content = svg_content.replace(
        '<text x="950" y="210" text-anchor="middle" font-size="28" font-weight="bold" fill="#ffffff" font-family="sans-serif">\n      <tspan x="950" dy="0">What actually happened</tspan>\n      <tspan x="950" dy="30">on the wire</tspan>',
        '<text x="950" y="202" text-anchor="middle" font-size="28" font-weight="bold" fill="#ffffff" font-family="sans-serif">\n      <tspan x="950" dy="0">What actually happened</tspan>\n      <tspan x="950" dy="28">on the wire</tspan>'
    )
    # Col 3:
    svg_content = svg_content.replace(
        '<text x="1380" y="224" text-anchor="middle" font-size="28" font-weight="bold" fill="#ffffff" font-family="sans-serif">Where to look</text>',
        '<text x="1380" y="216" text-anchor="middle" font-size="28" font-weight="bold" fill="#ffffff" font-family="sans-serif">Where to look</text>'
    )
    
    with open("test_connection_fails.svg", "w") as f:
        f.write(svg_content)
    print("Updated SVG")

generate_and_audit()
