import glob,re
import sys
PART=sys.argv[1] if len(sys.argv)>1 else "part-03-python"
N=PART.split("-")[1].lstrip("0")
root="/Users/jithinpjoseph/Documents/GitHub/ai-infra-handbook/docs/"+PART
for f in sorted(glob.glob(root+'/[0-9]*.md')):
    nn=int(f.split('/')[-1][:2]); c=[0]
    s=open(f).read()
    def r(m):
        c[0]+=1; return f'*Figure {N}.{nn}.{c[0]}.'
    t=re.sub(r'^\*Figure %s\.\d+\.\w+\.'%N,r,s,flags=re.M)
    if t!=s: open(f,'w').write(t); print(f.split('/')[-1][:2],c[0])
