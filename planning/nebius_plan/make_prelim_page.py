#!/usr/bin/env python3
"""Builds docs/prelim-plan.md (TEMPORARY page, delete after interview) from PRELIM_PLAN.md, linking chapter numbers like 1.3 to chapter files."""
import re,glob,os
root=os.path.abspath(os.path.join(os.path.dirname(__file__),'../..'))
vol={}
for d in glob.glob(f'{root}/docs/part-*/'):
    v=int(os.path.basename(d.rstrip('/')).split('-')[1]);vol[v]=d
def link(m):
    v,c=int(m.group(1)),int(m.group(2))
    d=vol.get(v)
    if not d or v==0: return m.group(0)
    f=glob.glob(f'{d}{c:02d}-*.md')
    if not f: return m.group(0)
    return f"[{m.group(0)}](./{os.path.basename(d.rstrip('/'))}/{os.path.basename(f[0])})"
src=open(f'{root}/planning/nebius_plan/PRELIM_PLAN.md').read()
out=[]
for line in src.split('\n'):
    if line.startswith('Chapter refs:'): out.append(line);continue
    parts=re.split(r'(\[[^\]]*\]\([^)]*\))',line)
    parts=[x if x.startswith('[') and '](' in x else re.sub(r'(?<![\w.`/])(\d{1,2})\.(\d{1,2})\b(?!\s*(?:h\b|hours|min|%|KB))(?![\d.])',link,x) for x in parts]
    line=''.join(parts)
    out.append(line)
body='\n'.join(out)
open(f'{root}/docs/prelim-plan.md','w').write('---\nid: prelim-plan\ntitle: "TEMPORARY: Preliminary interview plan (27 Nov - 11 Dec)"\nsidebar_label: "Prelim interview plan (temporary)"\nsidebar_position: 0\n---\n\n:::caution Temporary page\nDelete `docs/prelim-plan.md` after the interview (source: planning/nebius_plan/PRELIM_PLAN.md).\n:::\n\n'+body)
print('written',body.count('](./'),'links')
