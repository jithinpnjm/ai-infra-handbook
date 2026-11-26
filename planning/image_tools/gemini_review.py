#!/usr/bin/env python3
"""gemini_review.py LISTFILE... : vision-review every figure named in the review lists with gemini-3.8-flash (direct API). Writes /tmp/review_results.jsonl {name, ok, issues}. Skips names already reviewed. Renders PNG if missing."""
import sys,json,os,re,base64,subprocess,urllib.request,concurrent.futures as cf,glob
root=os.path.abspath(os.path.join(os.path.dirname(__file__),'../..'))
key=[l.split('=',1)[1].strip().strip('"').strip("'") for l in open(os.path.expanduser('~/.config/handbook/gemini.env')) if l.startswith('GEMINI_API_KEY=')][0]
OUT='/tmp/review_results.jsonl';done=set()
if os.path.exists(OUT): done={json.loads(l)['name'] for l in open(OUT)}
path={}
for f in glob.glob(f'{root}/docs/part-*/img/*.svg'): path[os.path.basename(f)[:-4]]=f
names=[]
for lf in sys.argv[1:]:
    for l in open(lf):
        if '|' in l: names+=l.strip().split('|',1)[1].split()
names=[n for n in dict.fromkeys(names) if n in path and n not in done]
PROMPT=("You are a strict visual QA reviewer of a technical infographic (SVG rendered to PNG) for a beginner-friendly engineering book. "
"Report ONLY serious defects: (1) text cut off at an edge or by a box, (2) text overlapping other text, icons or arrow lines so it is hard to read, (3) labels spilling out of their boxes, (4) arrows that are confusing or point at nothing, (5) a big empty panel or broken layout, (6) text too small to read at 800 px page width. "
"Ignore tiny cosmetic issues. Answer ONLY JSON: {\"ok\":true|false,\"issues\":[\"short specific issue naming the label/box\"]}.")
def render(n):
    p=f'/tmp/svgcheck/{n}.png'
    if os.path.exists(p) and os.path.getmtime(p)>=os.path.getmtime(path[n]): return p
    s=open(path[n]).read();h=re.search(r'viewBox="0 0 1600 (\d+)"',s);H=int(h.group(1)) if h else 900
    subprocess.run(['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome','--headless=new','--disable-gpu','--hide-scrollbars',f'--window-size=1600,{H}',f'--screenshot={p}',f'file://{path[n]}'],capture_output=True,timeout=60)
    return p
def review(n):
    try:
        p=render(n);b=base64.b64encode(open(p,'rb').read()).decode()
        body=json.dumps({'contents':[{'parts':[{'text':PROMPT},{'inline_data':{'mime_type':'image/png','data':b}}]}],'generationConfig':{'responseMimeType':'application/json','maxOutputTokens':8192}}).encode()
        req=urllib.request.Request('https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent',data=body,headers={'x-goog-api-key':key,'Content-Type':'application/json'})
        r=json.load(urllib.request.urlopen(req,timeout=120))
        t=''.join(x.get('text','') for x in r['candidates'][0]['content']['parts'])
        j=json.loads(t);return {'name':n,'ok':bool(j.get('ok')),'issues':j.get('issues',[])[:4]}
    except Exception as e: return {'name':n,'ok':None,'issues':['ERR '+str(e)[:80]]}
print(len(names),'to review',flush=True)
with cf.ThreadPoolExecutor(8) as ex, open(OUT,'a') as f:
    for r in ex.map(review,names): f.write(json.dumps(r)+'\n');f.flush()
