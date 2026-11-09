#!/usr/bin/env python3
"""Prepare a voice-rewrite unit: python3 tools/restore/prep_voice.py 1.2 -> writes planning/restore/V<label>_prompt.md"""
import sys, glob, os, shutil, subprocess
BOOKS={'17.11':'ai-systems-performance-engineering (appendix checklist), production-kubernetes','16.14':'production-kubernetes (ch 12 Multitenancy), ai-factory','18.3':'production-kubernetes (ch 15 Software Supply Chain)'}
S='/private/tmp/claude-501/-Users-jithinpjoseph-Documents-GitHub-trading-bot/edaf2c97-5b6e-4b55-b8a8-db04599ac342/scratchpad/v'
for label in sys.argv[1:]:
    p,c=label.split('.'); f=glob.glob(f'docs/part-{int(p):02d}-*/{int(c):02d}-*.md')[0]
    W=f'{S}/{label}'; shutil.rmtree(W,ignore_errors=True)
    subprocess.run(['python3','tools/restore/sections.py','split',f,W],check=True,capture_output=True)
    shutil.copy(f,f'{W}/chapter_old.md'); os.makedirs(f'planning/restore/backup/V{label}',exist_ok=True); shutil.copy(f,f'planning/restore/backup/V{label}/')
    open(f'planning/restore/V{label}_prompt.md','w').write(open(os.environ.get('VOICE_PROMPT','planning/restore/VOICE_PROMPT.md')).read().format(label=label,target=f,work=W,part=p.zfill(2) if False else p,books=BOOKS.get(label,{'16':'production-kubernetes, ai-factory','17':'ai-systems-performance-engineering, production-kubernetes, ai-factory','18':'production-kubernetes, ai-factory'}.get(p.lstrip('0'),'production-kubernetes'))))
    print(label,f.split('/')[-1][:50])
