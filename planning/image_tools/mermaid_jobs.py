#!/usr/bin/env python3
"""mermaid_jobs.py PART_DIR out.json : list every ```mermaid block (not yet replaced) as an svg_batch job.
mermaid_jobs.py PART_DIR out.json --apply : replace block k with the svg figure when docs/PART/img/NAME.svg exists (then run renumber_part.py)."""
import sys,re,glob,json,os
root=os.path.abspath(os.path.join(os.path.dirname(__file__),'../..'))
part=sys.argv[1]; out=sys.argv[2]; apply='--apply' in sys.argv
pn=int(part.split('-')[1]); jobs=[]
for f in sorted(glob.glob(f'{root}/docs/{part}/[0-9]*.md')):
    nn=os.path.basename(f)[:2]; t=open(f).read()
    pat=re.compile(r'^```mermaid\n(.*?)^```\n?',re.S|re.M); k=0; pieces=[]; last=0
    for m in pat.finditer(t):
        k+=1; name=f'm{pn}-{nn}-{k}'
        hs=[h for h in re.finditer(r'^#{1,4} (.+)$',t[:m.start()],re.M)]
        title=re.sub(r'[`*]','',hs[-1].group(1)) if hs else 'Diagram'
        title=re.sub(r'^\d+(\.\d+)*\.?\s*','',title)
        jobs.append(dict(part=part,name=name,title=title[:70],spec=m.group(1).strip()))
        svg=f'{root}/docs/{part}/img/{name}.svg'
        if apply and os.path.exists(svg):
            pieces.append((m.start(),m.end(),f'![{title}](./img/{name}.svg)\n\n*Figure {pn}.{int(nn)}.0. {title}, as a diagram.*\n'))
    if apply and pieces:
        s=t
        for a,b,r in reversed(pieces): s=s[:a]+r+s[b:]
        open(f,'w').write(s); print(nn,'replaced',len(pieces))
json.dump(jobs,open(out,'w'))
print(len(jobs),'mermaid blocks')
