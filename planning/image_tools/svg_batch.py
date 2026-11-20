#!/usr/bin/env python3
"""svg_batch.py specs.json [parallel=4]  -- specs: [{"part","name","title","spec"}...]; runs svg_gen.py in parallel, skips ones whose svg exists."""
import sys,json,subprocess,pathlib,concurrent.futures as cf
here=pathlib.Path(__file__).parent; root=here.parents[1]
specs=json.load(open(sys.argv[1])); n=int(sys.argv[2]) if len(sys.argv)>2 else 4
def run(s):
    if (root/'docs'/s['part']/'img'/(s['name']+'.svg')).exists(): return s['name']+' SKIP'
    try:
        r=subprocess.run(['python3',str(here/'svg_gen.py'),s['part'],s['name'],s['title'],s['spec']],capture_output=True,text=True,timeout=900)
        return s['name']+' '+(r.stdout.strip().split('\n')[-1] if r.stdout else 'FAIL '+r.stderr[-200:])
    except Exception as e: return s['name']+' ERR '+str(e)
with cf.ThreadPoolExecutor(n) as ex:
    for r in ex.map(run,specs): print(r,flush=True)
