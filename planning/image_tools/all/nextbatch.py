import json,os,re,glob,sys
from mk import specs,prompt
s=specs()
have={int(re.search(r'g-(\d+)\.jpg',f).group(1)) for f in glob.glob(os.path.expanduser('~/Downloads/handbook-images/final/g-*.jpg'))}
rem=[i for i in sorted(s) if not s[i].get('skip') and i not in have][:int(sys.argv[1])]
print(' '.join(map(str,rem)))
ps=[]
for i in rem:
    p=prompt(s[i]); p='@@'+p[p.index(' Title at top'):]
    ps.append(p.replace(' The layout wording only describes structure; the visible text is exactly the list below.',''))
print(json.dumps(ps))
