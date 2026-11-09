#!/usr/bin/env python3
"""Prepare restoration units (backup current target files + prompt). Usage: prep_restore.py U022 U028 ..."""
import json, os, shutil, sys
S='/private/tmp/claude-501/-Users-jithinpjoseph-Documents-GitHub-trading-bot/edaf2c97-5b6e-4b55-b8a8-db04599ac342/scratchpad'
U={u['id']:u for u in json.load(open('planning/restore/QUEUE.json'))}
tpl=open(os.environ.get('WORKER_PROMPT','planning/restore/WORKER_PROMPT.md')).read()
for i in sys.argv[1:]:
    u=U[i]; d=f'planning/restore/backup/{i}'; shutil.rmtree(d,ignore_errors=True); os.makedirs(d)
    for f in u['files']: shutil.copy(f,d)
    v=dict(u); v['files']=', '.join(u['files']); v['labels']=' '.join(u['labels'])
    open(f'planning/restore/{i}_prompt.md','w').write(tpl.format(scratch=S,**v)); print(i,u['prefix'],u['pct'],u['files'][0].split('/')[-1][:30])
