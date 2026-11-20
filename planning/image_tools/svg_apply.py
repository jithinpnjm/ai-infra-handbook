#!/usr/bin/env python3
"""svg_apply.py specs.json : insert every spec whose svg exists and is not yet in the chapter. Then renumbers. Specs need ch, anchor, alt, cap (plus part, name)."""
import sys,json,subprocess,glob,os
here=os.path.dirname(os.path.abspath(__file__)); root=os.path.abspath(os.path.join(here,'../..'))
for s in json.load(open(sys.argv[1])):
    d=f"{root}/docs/{s['part']}"
    if not os.path.exists(f"{d}/img/{s['name']}.svg"): print('MISSING',s['name']); continue
    md=glob.glob(f"{d}/{s['ch']}-*.md")[0]
    if f"./img/{s['name']}.svg" in open(md).read(): continue
    r=subprocess.run(['python3',f'{here}/insert_fig.py',s['ch'],s['anchor'],s['name'],f"{int(s['part'].split('-')[1])}.0.0",s['alt'],s['cap']],env={**os.environ,'PART':s['part']},capture_output=True,text=True)
    print(r.stdout.strip() or r.stderr.strip()[-200:])
subprocess.run(['python3',f'{here}/renumber_part.py',json.load(open(sys.argv[1]))[0]['part']])
