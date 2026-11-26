#!/usr/bin/env python3
"""regen.py NAME 'fix note' [BACKUPDIR] : back up docs svg, regenerate it with Gemini using the original spec plus the fix note, re-render PNG at /tmp/svgcheck/NAME.png. Prints OK or FAILED (old file restored)."""
import sys,json,glob,os,shutil,subprocess
root=os.path.abspath(os.path.join(os.path.dirname(__file__),'../..'))
name,note=sys.argv[1],sys.argv[2];bak=sys.argv[3] if len(sys.argv)>3 else '/tmp/svgbak_regen'
idx={}
for f in glob.glob(f'{root}/planning/image_tools/specs/*.json')+glob.glob('/tmp/*.json'):
    try:
        for x in json.load(open(f)):
            if isinstance(x,dict) and 'spec' in x and 'part' in x: idx.setdefault(x['name'],x)
    except Exception: pass
if name not in idx: print('NO SPEC FOUND for',name);sys.exit(1)
x=dict(idx[name]);x['spec']+=' FIX (must follow): '+note+' GENERAL: text at least 24 px, every line inside its box, no overlap between text, icons and arrows, titles inside the canvas, no large empty panels.'
p=f"{root}/docs/{x['part']}/img/{name}.svg";os.makedirs(bak,exist_ok=True);shutil.copy(p,f'{bak}/{name}.svg');os.remove(p)
j=f'/tmp/regen_{name}.json';json.dump([x],open(j,'w'))
subprocess.run(['python3',f'{root}/planning/image_tools/svg_batch.py',j,'1'],capture_output=True,text=True)
if os.path.exists(p): print('OK',name)
else: shutil.copy(f'{bak}/{name}.svg',p);print('FAILED (old restored)',name)
