#!/usr/bin/env python3
"""mk.py prompt ID -> prints Gemini prompt for spec ID (from specs_a/b.json)"""
import json,sys,os
D=os.path.dirname(os.path.abspath(__file__))
def specs():
    s={}
    for f in('specs_a.json','specs_b.json'):
        p=f'{D}/{f}'
        if os.path.exists(p):
            try:
                for x in json.load(open(p)):s[x['id']]=x
            except Exception:pass
    return s
def prompt(x):
    labs=', '.join(l.rstrip('. ') for l in x['labels'])
    note=f" Bottom orange note: {x['note'].rstrip('. ')}." if x.get('note') else ''
    return (f"Create an image: a polished educational infographic, 16:9, light background, dark-grey and green palette with one orange highlight, flat vector style, large readable text. Title at top: {x['title']}. Layout: {x['layout']}{note} The layout wording only describes structure; the visible text is exactly the list below. TEXT RULES: use only these words, each written exactly once, spelled exactly, no other text anywhere: {labs}.")
if __name__=='__main__':
    s=specs();i=int(sys.argv[2]);print(prompt(s[i]))
