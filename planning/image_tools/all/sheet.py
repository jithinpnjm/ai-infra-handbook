#!/usr/bin/env python3
"""sheet.py out.png id1 id2 id3 id4 : 2x2 contact sheet of g-ID.jpg"""
import sys,os
from PIL import Image
ids=sys.argv[2:];W,H=688,384
sh=Image.new('RGB',(W*2,H*2),'white')
for k,i in enumerate(ids):
    im=Image.open(os.path.expanduser(f'~/Downloads/handbook-images/final/g-{i}.jpg')).resize((W,H))
    sh.paste(im,((k%2)*W,(k//2)*H))
sh.save(sys.argv[1])
