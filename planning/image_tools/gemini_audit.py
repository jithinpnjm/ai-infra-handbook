#!/usr/bin/env python3
"""gemini_audit.py LISTFILE... : pass-4 gap audit. For each chapter, send the WHOLE chapter + its existing figures to gemini-3.8-flash (direct API). Returns a per-section ledger and new figure specs. Validates anchors/names; writes specs/p4_<vol>_<ch>.json and specs/p4_ledger_<vol>_<ch>.md."""
import sys,json,os,re,glob,urllib.request,concurrent.futures as cf
root=os.path.abspath(os.path.join(os.path.dirname(__file__),'../..'));S=f'{root}/planning/image_tools/specs'
key=[l.split('=',1)[1].strip().strip('"').strip("'") for l in open(os.path.expanduser('~/.config/handbook/gemini.env')) if l.startswith('GEMINI_API_KEY=')][0]
chs=[]
for lf in sys.argv[1:]:
    for l in open(lf):
        if '|' in l: chs.append(l.split('|')[0].strip())
chs=list(dict.fromkeys(chs))
allnames=set()
for f in glob.glob(f'{S}/*.json'):
    try:
        for x in json.load(open(f)):
            if isinstance(x,dict) and 'name' in x: allnames.add(x['name'])
    except Exception: pass
RULES=("You are the technical-illustration editor of a beginner-friendly engineering book (readers: SRE candidates, beginners in Linux/networking, preparing for a Senior SRE interview at an AI inference platform). "
"You are given ONE FULL CHAPTER in Markdown and the list of figures it already has. Read every line. "
"TASK A (ledger): for every ## and ### section write one row: heading | approx words | COVERED(figure name) / NEEDS FIGURE / NO FIGURE NEEDED + a few words why. "
"A section NEEDS a figure when a beginner would struggle to hold the idea from text alone: a mechanism, request/packet flow, state machine, topology/layout, comparison across 3+ dimensions, decision rule, failure cascade, command-output anatomy, worked calculation, or an ASCII/prose diagram. Do NOT add figures for plain definitions, pure lists, exercises, checkpoint questions or sources. Do not duplicate a concept an existing figure already draws. No cap: add as many as are genuinely needed, none if none are. "
"TASK B (specs): for each NEEDS FIGURE write a spec object {\"name\":\"p4-<vol><ch>-<shortword>\",\"title\":\"...\",\"anchor\":\"<EXACT heading line from the chapter, copied character for character including # marks>\",\"spec\":\"<detailed drawing content: exact labels, boxes, arrows, numbered steps, commands, numbers, all TAKEN FROM THE CHAPTER TEXT; never invent facts; describe layout>\",\"alt\":\"one plain sentence\",\"cap\":\"one plain sentence\"}. alt/cap must not contain < > { } characters. Use a different anchor heading for each figure where possible; the figure will be inserted right after the anchor heading. "
"Output ONLY JSON: {\"ledger\":[\"heading | words | verdict\",...],\"specs\":[...]}.")
def figs(md):
    L=md.split('\n');out=[];head=''
    for i,l in enumerate(L):
        if re.match(r'^#{1,4} ',l): head=l
        m=re.match(r'!\[([^\]]*)\]\(\./img/([^)]+)\.svg\)',l)
        if m: out.append(f"{m.group(2)} | after heading: {head} | alt: {m.group(1)[:150]}")
    return out
def call(prompt):
    body=json.dumps({'contents':[{'parts':[{'text':prompt}]}],'generationConfig':{'responseMimeType':'application/json','maxOutputTokens':60000}}).encode()
    req=urllib.request.Request('https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent',data=body,headers={'x-goog-api-key':key,'Content-Type':'application/json'})
    r=json.load(urllib.request.urlopen(req,timeout=900))
    open('/tmp/audit_usage.jsonl','a').write(json.dumps(r.get('usageMetadata',{}))+'\n')
    return json.loads(''.join(p.get('text','') for p in r['candidates'][0]['content']['parts']))
def run(path):
    fp=f'{root}/{path}';md=open(fp).read();lines=md.split('\n')
    part=path.split('/')[1];nn=os.path.basename(path)[:2];vol=part.split('-')[1]
    outj=f'{S}/p4_{vol}_{nn}.json'
    if os.path.exists(f'{S}/p4_ledger_{vol}_{nn}.md'): return path,'skip'
    prompt=RULES+f"\n\nCHAPTER FILE: {path}\nChapter number: vol {int(vol)} chapter {int(nn)}. Names must start p4-{vol}{nn}-.\nEXISTING FIGURES IN THIS CHAPTER:\n"+'\n'.join(figs(md))+"\n\nFULL CHAPTER:\n"+md
    feedback=''
    for attempt in range(3):
        try: j=call(prompt+feedback)
        except Exception as e: feedback=f"\n(previous call failed: {str(e)[:100]}; return valid JSON)";continue
        good=[];bad=[]
        for x in j.get('specs',[]):
            try:
                if not all(k in x for k in('name','title','anchor','spec','alt','cap')): bad.append('missing key');continue
                if lines.count(x['anchor'])!=1: bad.append('anchor not exact/unique: '+x['anchor'][:60]);continue
                if re.search(r'[<>{}]',x['alt']+x['cap']): bad.append('alt/cap has forbidden char: '+x['name']);continue
                if x['name'] in allnames: bad.append('name taken: '+x['name']);continue
                x['part']=part;x['ch']=nn;good.append(x);allnames.add(x['name'])
            except Exception: bad.append('bad spec')
        if bad and attempt<2 and len(bad)>max(1,len(good)//4):
            feedback='\nYOUR PREVIOUS ANSWER HAD PROBLEMS, fix them and return the full JSON again: '+'; '.join(bad[:8]);
            for x in good: allnames.discard(x['name'])
            continue
        json.dump(good,open(outj,'w'),indent=1)
        open(f'{S}/p4_ledger_{vol}_{nn}.md','w').write(f'# {path}\n'+'\n'.join('- '+r for r in j.get('ledger',[]))+f'\n\nSpecs kept {len(good)}, dropped {len(bad)}: {bad[:6]}\n')
        return path,f'specs {len(good)} dropped {len(bad)} ledger {len(j.get("ledger",[]))}'
    return path,'FAILED'
print(len(chs),'chapters',flush=True)
with cf.ThreadPoolExecutor(16) as ex:
    for p,r in ex.map(run,chs): print(p.split('/')[-1],r,flush=True)
