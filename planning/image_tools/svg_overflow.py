#!/usr/bin/env python3
"""svg_overflow.py PART... : flag svgs whose text runs past the canvas edge or past its enclosing rect (estimate)."""
import sys,re,glob,xml.etree.ElementTree as ET
def num(v,d=0):
    try: return float(re.sub(r'[a-z%]','',v))
    except: return d
bad={}
for part in sys.argv[1:]:
    for f in glob.glob(f'docs/{part}/img/*.svg'):
        try: root=ET.parse(f).getroot()
        except: continue
        vb=[float(x) for x in root.get('viewBox','0 0 1600 900').split()];W=vb[2]
        for el in root.iter():
            if not el.tag.endswith('text'): continue
            fs=num(el.get('font-size'),24);txt=''.join(el.itertext()).strip()
            if not txt: continue
            x=num(el.get('x'),0);anc=el.get('text-anchor','start')
            w=len(txt)*fs*0.55
            # use tspans: longest line
            lines=[''.join(t.itertext()) for t in el if t.tag.endswith('tspan')]
            if lines: w=max(len(l.strip()) for l in lines)*fs*0.55
            l,r=(x,x+w) if anc=='start' else (x-w/2,x+w/2) if anc=='middle' else (x-w,x)
            if l<-2 or r>W+2: bad.setdefault(f,[]).append((txt[:40],int(r-W)))
for f,v in sorted(bad.items()): print(f.split('/')[-1],v[:2])
print(len(bad),'flagged')
