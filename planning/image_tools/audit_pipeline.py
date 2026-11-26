#!/usr/bin/env python3
"""audit_pipeline.py : unattended. Waits for gemini_review.py to finish, retries API errors, regenerates failed figures (direct API, best-of-2, issues as fix note), re-reviews them, writes /tmp/audit_summary.json. Never builds/commits/pushes."""
import json,os,subprocess,time,concurrent.futures as cf
root=os.path.abspath(os.path.join(os.path.dirname(__file__),'../..'));T=f'{root}/planning/image_tools'
R='/tmp/review_results.jsonl';LISTS=[f'{root}/planning/nebius_plan/review/agent{i}.txt' for i in (1,2,3)]
while subprocess.run(['pgrep','-f','gemini_review.py'],capture_output=True).stdout.strip(): time.sleep(30)
def load(): 
    d={}
    for l in open(R): x=json.loads(l);d[x['name']]=x
    return d
def rerun(names):
    d=load()
    for n in names: d.pop(n,None)
    open(R,'w').write(''.join(json.dumps(x)+'\n' for x in d.values()))
    open('/tmp/audit_rerun.txt','w').write('x|'+' '.join(names)+'\n')
    subprocess.run(['python3',f'{T}/gemini_review.py','/tmp/audit_rerun.txt'])
# 1. fill in anything missing or errored
d=load();errs=[n for n,x in d.items() if x['ok'] is None]
subprocess.run(['python3',f'{T}/gemini_review.py']+LISTS)  # reviews names not yet done
if errs: rerun(errs)
d=load();failed=[n for n,x in d.items() if x['ok'] is False]
json.dump({'phase':'regenerating','failed':len(failed)},open('/tmp/audit_summary.json','w'))
def fix(n):
    note='Reviewer found these serious defects, fix exactly them: '+'; '.join(d[n]['issues'])
    r=subprocess.run(['python3',f'{T}/svg_best.py',n,note,'2'],capture_output=True,text=True,env=dict(os.environ,SVG_API='1'))
    return n,(r.stdout.strip().splitlines() or ['NOOUT'])[-1]
res={}
with cf.ThreadPoolExecutor(6) as ex:
    for n,o in ex.map(fix,failed): res[n]=o
rerun(failed)
d2=load();still=[n for n in failed if d2.get(n,{}).get('ok') is False]
json.dump({'phase':'done','reviewed':len(d2),'failed_first':len(failed),'still_failing':still,'regen_results':res,'still_issues':{n:d2[n]['issues'] for n in still}},open('/tmp/audit_summary.json','w'),indent=1)
