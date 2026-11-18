#!/usr/bin/env python3
"""usage: decode_result.py <tool-result-file> <NAME>  -- decodes 'DIMS:WxH:<base64>' (or plain base64) into handbook-images originals/final."""
import json,base64,sys,subprocess,os
f,name=sys.argv[1],sys.argv[2]
t=json.load(open(f))[0]['text'].strip().strip('"')
dims=''
if t.startswith('DIMS:'):
    _,dims,t=t.split(':',2)
import re; t=re.match(r'[A-Za-z0-9+/=]+',t).group(0)
raw=base64.b64decode(t)
assert raw[:3]==b'\xff\xd8\xff', 'not a jpeg'
H=os.path.expanduser('~/Downloads/handbook-images')
src=f'{H}/originals/{name}.src.jpeg'; open(src,'wb').write(raw)
out=f'{H}/final/{name}.jpg'
import shutil; shutil.copy(src,out)  # keep native resolution, never upscale
print(name, 'dims',dims,'orig bytes',len(raw),'final bytes',os.path.getsize(out))
