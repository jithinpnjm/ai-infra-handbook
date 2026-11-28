#!/usr/bin/env python3
"""put_all.py ID : insert ~/Downloads/handbook-images/final/g-ID.jpg after first paragraph under the heading of worklist item ID"""
import json,sys,os,re,shutil
R='/Users/jithinpjoseph/Documents/GitHub/ai-infra-handbook';D=R+'/planning/image_tools/all'
i=int(sys.argv[1])
w=json.load(open(D+'/worklist.json'))[i]
sp={}
for f in('specs_a.json','specs_b.json'):
    try:
        for x in json.load(open(f'{D}/{f}')):sp[x['id']]=x
    except Exception:pass
x=sp[i]
path=f"{R}/{w['f']}";dirn=os.path.dirname(path);os.makedirs(dirn+'/img',exist_ok=True)
src=os.path.expanduser(f'~/Downloads/handbook-images/final/g-{i}.jpg')
shutil.copy(src,f'{dirn}/img/g-{i}.jpg')
L=open(path).read().split('\n')
if any(f'img/g-{i}.jpg' in l for l in L):print('already');sys.exit()
h=[k for k,l in enumerate(L) if l==w['h']][0]
# vol.ch.V numbering later by renumber_part; use placeholder 
k=h+1
while k<len(L) and not L[k].strip():k+=1
# skip leading images/figure captions/blank, find first plain paragraph
j=k
while j<len(L) and (L[j].startswith('![') or L[j].startswith('*Figure') or not L[j].strip() or L[j].startswith('#')):
    if L[j].startswith('#') and j>h:break
    j+=1
# advance to end of that paragraph
e=j
while e<len(L) and L[e].strip() and not L[e].startswith(('#','```','|','![')):e+=1
if j>=len(L) or L[j].startswith('#'):e=h+1
ins=['',f"![{x['alt']}](./img/g-{i}.jpg)",f"*Figure {int(w['f'].split('/')[1].split('-')[1])}.{int(os.path.basename(w['f'])[:2])}.V. {x['caption']}*",'']
L[e:e]=ins
open(path,'w').write('\n'.join(L));print('inserted',i,os.path.basename(path))
