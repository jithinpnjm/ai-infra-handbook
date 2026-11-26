#!/usr/bin/env python3
"""svg_best.py NAME 'fix note' [attempts=4] : generate NAME via the direct Gemini API up to N times, score each with the real-bbox overflow checker (EDGE x3 + OVERLAP), keep the best in docs. Uses the original spec + fix note. Prints best score and attempts."""
import sys,json,glob,os,shutil,subprocess,re
root=os.path.abspath(os.path.join(os.path.dirname(__file__),'../..'))
name=sys.argv[1];note=sys.argv[2] if len(sys.argv)>2 else '';N=int(sys.argv[3]) if len(sys.argv)>3 else 4
idx={}
for f in glob.glob(f'{root}/planning/image_tools/specs/*.json')+glob.glob('/tmp/*.json'):
    try:
        for x in json.load(open(f)):
            if isinstance(x,dict) and 'spec' in x and 'part' in x: idx.setdefault(x['name'],x)
    except Exception: pass
x=dict(idx[name]);base=x['spec']
p=f"{root}/docs/{x['part']}/img/{name}.svg";os.makedirs('/tmp/attempts',exist_ok=True)
if os.path.exists(p): shutil.copy(p,f'/tmp/attempts/{name}_orig.svg')
def score(f):
    out=subprocess.run(['python3',f'{root}/planning/image_tools/svg_overflow2.py',f],capture_output=True,text=True).stdout
    cl=sum(int(v) for v in re.findall(r'CROSSLINE:(\d+)',out))
    return 3*out.count('EDGE:')+out.count('OVER:')+2*out.count('CROSSBOX:')+cl
best=None;fb=''
for k in range(N):
    spec=base+(' FIX (must follow): '+note if note else '')+' GENERAL (must follow): text at least 24 px; every text line inside its box with 20 px padding; boxes sized generously, wrap long text onto more lines or make the canvas taller (up to 1500); no overlap between any text, icon, arrow or box edge; arrow labels sit in free space on a background pill; titles fit within 1500 px width on at most two lines; no large empty panels.'+fb
    if os.path.exists(p): os.remove(p)
    j=f'/tmp/attempts/{name}.json';y=dict(x);y['spec']=spec;json.dump([y],open(j,'w'))
    env=dict(os.environ,SVG_API='1')
    subprocess.run(['python3',f'{root}/planning/image_tools/svg_batch.py',j,'1'],capture_output=True,text=True,env=env)
    if not os.path.exists(p): continue
    s=score(p);shutil.copy(p,f'/tmp/attempts/{name}_{k}.svg')
    if best is None or s<best[0]: best=(s,k)
    if s==0: break
    o=subprocess.run(['python3',f'{root}/planning/image_tools/svg_overflow2.py',p],capture_output=True,text=True).stdout
    fb=' PREVIOUS ATTEMPT PROBLEMS: '+o.strip().splitlines()[0][:300]+' Fix exactly these.' if o.strip() else ''
if best is None:
    if os.path.exists(f'/tmp/attempts/{name}_orig.svg'): shutil.copy(f'/tmp/attempts/{name}_orig.svg',p)
    print('FAILED',name);sys.exit(1)
shutil.copy(f'/tmp/attempts/{name}_{best[1]}.svg',p)
# re-render png
h=re.search(r'viewBox="0 0 1600 (\d+)"',open(p).read());H=int(h.group(1)) if h else 900
subprocess.run(['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome','--headless=new','--disable-gpu','--hide-scrollbars',f'--window-size=1600,{H}',f'--screenshot=/tmp/svgcheck/{name}.png',f'file://{p}'],capture_output=True)
print('BEST',name,'score',best[0],'attempt',best[1]+1)
