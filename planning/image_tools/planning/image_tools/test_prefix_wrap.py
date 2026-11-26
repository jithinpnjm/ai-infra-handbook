import xml.etree.ElementTree as ET
import re

def test_wrap():
    text_intro = "v0.32.0 prefix caching is on by default; vLLM hashes each block from its tokens and its prefix; caches only full blocks"
    print("Total len:", len(text_intro))
    # Let's break into 3 or 4 lines
    lines = [
        "v0.32.0 prefix caching is on by default;",
        "vLLM hashes each block from its tokens",
        "and its prefix; caches only full blocks"
    ]
    for l in lines:
        print(f"[{len(l):2d} chars, {len(l)*14.4:5.1f}px] '{l}'")
    assert " ".join(lines) == text_intro

test_wrap()
