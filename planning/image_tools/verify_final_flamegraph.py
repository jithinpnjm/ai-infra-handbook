#!/usr/bin/env python3
import asyncio
from playwright.async_api import async_playwright
import xml.etree.ElementTree as ET
import re, os

async def verify():
    # 1. Audit SVG structure
    with open("flamegraph_perfect.svg", "r") as f:
        svg_str = f.read()
        
    tree = ET.parse("flamegraph_perfect.svg")
    root = tree.getroot()
    
    # Check dimensions
    assert root.attrib["width"] == "1600"
    assert root.attrib["viewBox"] == "0 0 1600 1180"
    
    # Check title and desc
    children = list(root)
    assert children[0].tag.endswith("title")
    assert children[1].tag.endswith("desc")
    
    # Check forbidden words
    forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
    for t in root.iter('{http://www.w3.org/2000/svg}text'):
        full_text = "".join(t.itertext()).strip()
        words = re.findall(r'\b[a-zA-Z]+\b', full_text.lower())
        for f_word in forbidden:
            assert f_word not in words, f"Forbidden word '{f_word}' in '{full_text}'"
            
    print("[PASS] No forbidden words found.")
    
    # Playwright render & bounding boxes check
    async with async_playwright() as p:
        b = await p.chromium.launch()
        page = await b.new_page(viewport={"width": 1600, "height": 1180})
        await page.goto("file://" + os.path.abspath("flamegraph_perfect.svg"))
        await page.screenshot(path="flamegraph_render.png")
        print("[PASS] Rendered to flamegraph_render.png.")
        await b.close()

asyncio.run(verify())
