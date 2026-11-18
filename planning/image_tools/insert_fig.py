#!/usr/bin/env python3
"""usage: insert_fig.py <chapter-number NN> <anchor substring (unique, inside the paragraph to insert AFTER)> <image name without ext> <figure label e.g. 1.2.1> <alt> <caption>
Copies final/<name>.jpg into docs/part-01-linux/img/ and inserts the figure after the paragraph containing the anchor."""
import sys,glob,shutil,os
nn,anchor,name,label,alt,cap=sys.argv[1:7]
root='/Users/jithinpjoseph/Documents/GitHub/ai-infra-handbook/docs/'+os.environ.get('PART','part-01-linux')
p=glob.glob(f'{root}/{nn}-*.md')[0]
s=open(p).read()
assert s.count(anchor)==1, f'anchor count {s.count(anchor)} for {anchor!r}'
i=s.index(anchor)
j=s.find('\n\n',i)
if j==-1: j=len(s)
# if the paragraph is followed by a code fence belonging to it, stay simple: insert right after the paragraph
shutil.copy(os.path.expanduser(f'~/Downloads/handbook-images/final/{name}.jpg'),f'{root}/img/{name}.jpg')
block=f"\n\n![{alt}](./img/{name}.jpg)\n\n*Figure {label}. {cap}*"
s=s[:j]+block+s[j:]
open(p,'w').write(s)
print('inserted',name,'into',os.path.basename(p))
