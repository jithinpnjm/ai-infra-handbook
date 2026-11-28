#!/usr/bin/env python3
"""dec.py RESULTFILE id1 id2 ... : decode browser_batch/js result json into ~/Downloads/handbook-images/final/g-ID.jpg"""
import json,base64,re,sys,os
d=json.load(open(sys.argv[1]));ids=sys.argv[2:]
if isinstance(d,dict):d=[d]
for n,x in zip(ids,d):
    t=x['text'];i=t.index('DIMS:');r=t[i:].split(':',2)
    b=re.sub(r'[^A-Za-z0-9+/=]','',r[2]);b=b[:len(b)//4*4]
    open(os.path.expanduser(f'~/Downloads/handbook-images/final/g-{n}.jpg'),'wb').write(base64.b64decode(b));print(n,r[1])
