import re, glob, pathlib

# Let's search all python scripts for any mention of 0503 or ingress
for p in pathlib.Path('.').rglob('*.py'):
    txt = p.read_text(errors='ignore')
    if '0503' in txt or 'ingress' in txt.lower():
        print(f"Match in {p}")
