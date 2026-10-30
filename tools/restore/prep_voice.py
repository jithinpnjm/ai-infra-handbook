#!/usr/bin/env python3
"""Prepare a voice-rewrite unit: python3 tools/restore/prep_voice.py 1.2 -> writes planning/restore/V<label>_prompt.md"""
import sys, glob, os, shutil, subprocess
S='/private/tmp/claude-501/-Users-jithinpjoseph-Documents-GitHub-ai-infra-handbook/4207da9b-4841-4181-b14d-4ebf9acb1a7e/scratchpad/v'
for label in sys.argv[1:]:
    p,c=label.split('.'); f=glob.glob(f'docs/part-{int(p):02d}-*/{int(c):02d}-*.md')[0]
    W=f'{S}/{label}'; shutil.rmtree(W,ignore_errors=True)
    subprocess.run(['python3','tools/restore/sections.py','split',f,W],check=True,capture_output=True)
    shutil.copy(f,f'{W}/chapter_old.md'); os.makedirs(f'planning/restore/backup/V{label}',exist_ok=True); shutil.copy(f,f'planning/restore/backup/V{label}/')
    open(f'planning/restore/V{label}_prompt.md','w').write(open('planning/restore/VOICE_PROMPT.md').read().format(label=label,target=f,work=W))
    print(label,f.split('/')[-1][:50])
