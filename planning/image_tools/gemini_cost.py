#!/usr/bin/env python3
"""gemini_cost.py : snapshot of today's google/* usage from `opencode stats` (estimated cost from opencode's price table, not the Google bill).
Prints a table and appends a row to planning/ledgers/gemini_cost.csv. Use --quiet to only log."""
import subprocess,json,time,os,sys
d=json.loads(subprocess.run(['opencode','stats','--days','0','--models','--cost','--json'],capture_output=True,text=True,cwd='/tmp').stdout)
led=os.path.join(os.path.dirname(os.path.abspath(__file__)),'../ledgers/gemini_cost.csv')
new=not os.path.exists(led)
tot=0; rows=[]
for m in d['models']:
    if m['model']['providerID']!='google': continue
    t=m['tokens']; rows.append((m['model']['id'],m['steps'],t['input'],t['output'],t['reasoning'],t['cache']['read'],m['cost'])); tot+=m['cost']
now=time.strftime('%Y-%m-%d %H:%M')
with open(led,'a') as f:
    if new: f.write('time,model,steps,input,output,reasoning,cache_read,est_cost_usd_today\n')
    for r in rows: f.write(now+','+','.join(str(x) for x in r)+'\n')
if '--quiet' not in sys.argv:
    print(f'{now}  (today, estimated USD)')
    for r in rows: print(f'{r[0]:22} steps={r[1]:5} in={r[2]:>9} out={r[3]:>8} reason={r[4]:>9} cache={r[5]:>10} cost=${r[6]:.2f}')
    print(f'TOTAL google today: ${tot:.2f}')
