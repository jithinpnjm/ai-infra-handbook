#!/usr/bin/env python3
"""dec2.py FILE id1 id2 ... : file holds one JSON text with images separated by @@@"""
import json,base64,re,sys,os
d=json.load(open(sys.argv[1]));t=d[0]['text'] if isinstance(d,list) else d['text']
parts=t.split('@@@')
for n,p in zip(sys.argv[2:],parts):
    i=p.index('DIMS:');r=p[i:].split(':',2)
    b=re.sub(r'[^A-Za-z0-9+/=]','',r[2]);b=b[:len(b)//4*4]
    open(os.path.expanduser(f'~/Downloads/handbook-images/final/g-{n}.jpg'),'wb').write(base64.b64decode(b))
print(len(parts))
