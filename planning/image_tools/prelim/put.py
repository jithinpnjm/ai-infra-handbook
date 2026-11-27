#!/usr/bin/env python3
"""put.py NAME : copy jpg to docs img, insert after first paragraph under heading, then caller renumbers."""
import json,glob,shutil,sys,re,os
n=sys.argv[1];R='/Users/jithinpjoseph/Documents/GitHub/ai-infra-handbook'
m=[x for x in json.load(open(R+'/planning/image_tools/prelim/meta.json')) if x[0]==n][0]
_,p,nn,h,alt,cap=m
f=glob.glob(f'{R}/docs/{p}/{nn}-*.md')[0]
src=os.path.expanduser(f'~/Downloads/handbook-images/final/pre-{n}.jpg')
os.makedirs(f'{R}/docs/{p}/img',exist_ok=True);shutil.copy(src,f'{R}/docs/{p}/img/pre-{n}.jpg')
ls=open(f).read().split('\n')
if f'pre-{n}.jpg' in '\n'.join(ls): print('already');sys.exit()
i=[k for k,l in enumerate(ls) if l.startswith(h)][0]+1
while ls[i].strip()=='': i+=1
if re.match(r'[A-Za-z*_`(]',ls[i]) and not ls[i].startswith('!['):
    while i<len(ls) and ls[i].strip()!='': i+=1
else: i=[k for k,l in enumerate(ls) if l.startswith(h)][0]+1
lab=re.match(r'(\d+)',nn).group(1).lstrip('0') or '0'
vol=re.match(r'part-(\d+)',p).group(1).lstrip('0')
ins=['',f'![{alt}](./img/pre-{n}.jpg)','',f'*Figure {vol}.{lab}.V. {cap}*']
ls[i:i]=ins
open(f,'w').write('\n'.join(ls));print('inserted',n,'in',os.path.basename(f))
