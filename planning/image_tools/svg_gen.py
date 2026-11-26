#!/usr/bin/env python3
"""Generate an SVG figure with google/gemini-3.8-flash via opencode, then render a PNG to check it.
Usage: svg_gen.py PART NAME "Title" "spec text"   (or: svg_gen.py PART NAME @specfile)
Writes docs/PART/img/NAME.svg and /tmp/svgcheck/NAME.png. Rules: planning/luna_rules.md."""
import sys, re, subprocess, pathlib
root = pathlib.Path(__file__).resolve().parents[2]
part, name, title = sys.argv[1], sys.argv[2], sys.argv[3]
spec = sys.argv[4]
if spec.startswith('@'): spec = pathlib.Path(spec[1:]).read_text()
rules = (root/'planning/luna_rules.md').read_text()
prompt = (f"IMPORTANT: words like orange, green, grey, bold, monospace, arrow in the content are STYLE INSTRUCTIONS, never print them as text. Print only the labels.\n\nDraw an SVG infographic that explains the concept below visually.\nTitle: {title}\n\nCONTENT (use exactly these labels, each once, spelled exactly; add nothing else):\n{spec}\n\n{rules}")
out = subprocess.run(['opencode','run','-m',__import__('os').environ.get('SVG_MODEL','google/gemini-3.8-flash'),prompt],capture_output=True,text=True,timeout=600).stdout
m = re.search(r'<svg.*</svg>', out, re.S)
if not m: print('NO_SVG', out[-300:]); sys.exit(1)
svg = re.sub(r'<!--.*?-->','',m.group(0),flags=re.S)
import xml.etree.ElementTree as ET
try: ET.fromstring(svg)
except Exception as e: print('BAD_XML',e); sys.exit(1)
dst = root/'docs'/part/'img'/f'{name}.svg'; dst.parent.mkdir(exist_ok=True); dst.write_text(svg)
d = pathlib.Path('/tmp/svgcheck'); d.mkdir(exist_ok=True)
h = re.search(r'viewBox="0 0 1600 (\d+)"', svg); H = int(h.group(1)) if h else 900
subprocess.run(['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome','--headless=new','--disable-gpu','--hide-scrollbars',f'--window-size=1600,{H}',f'--screenshot={d}/{name}.png',f'file://{dst}'],capture_output=True,timeout=60)
print('OK', dst, f'{d}/{name}.png')
