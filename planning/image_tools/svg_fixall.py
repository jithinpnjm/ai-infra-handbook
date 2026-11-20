#!/usr/bin/env python3
"""Strip comments from all generated svgs, report invalid ones (and delete them so batch re-runs)."""
import re,glob,xml.etree.ElementTree as ET,os,sys
bad=[]
for f in glob.glob(os.path.expanduser('~/Documents/GitHub/ai-infra-handbook/docs/*/img/*.svg')):
    t=open(f).read(); u=re.sub(r'<!--.*?-->','',t,flags=re.S)
    if u!=t: open(f,'w').write(u)
    try: ET.fromstring(u)
    except Exception as e:
        bad.append(f); print('BAD',f.split('/')[-1],e)
        if '--delete' in sys.argv: os.remove(f)
