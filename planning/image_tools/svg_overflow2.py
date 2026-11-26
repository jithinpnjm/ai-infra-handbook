#!/usr/bin/env python3
"""svg_overflow2.py FILE... : real text-bbox check in headless Chrome. Flags text whose bbox leaves the viewBox, or overlaps another text (>=30% of the smaller)."""
import sys,subprocess,json,re,os,tempfile
files=sys.argv[1:]; out={}
CH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
JS="""<script>
function chk(svg){const vb=svg.viewBox.baseVal;const T=[...svg.querySelectorAll('text')];const bad=[];const bs=T.map(t=>{try{const b=t.getBBox();return {t:t.textContent.trim().slice(0,30),x:b.x,y:b.y,w:b.width,h:b.height}}catch(e){return null}}).filter(b=>b&&b.t);
for(const b of bs){if(b.x<vb.x-2||b.x+b.w>vb.x+vb.width+2||b.y<vb.y-2||b.y+b.h>vb.y+vb.height+2)bad.push('EDGE:'+b.t)}
let ov=0;for(let i=0;i<bs.length;i++)for(let j=i+1;j<bs.length;j++){const a=bs[i],b=bs[j];const w=Math.min(a.x+a.w,b.x+b.w)-Math.max(a.x,b.x),h=Math.min(a.y+a.h,b.y+b.h)-Math.max(a.y,b.y);if(w>4&&h>4&&w*h>0.3*Math.min(a.w*a.h,b.w*b.h)){ov++;if(ov<=2)bad.push('OVER:'+a.t+'|'+b.t)}}

const R=[...svg.querySelectorAll('rect')].map(r=>{try{const b=r.getBBox();return {x:b.x,y:b.y,w:b.width,h:b.height}}catch(e){return null}}).filter(b=>b&&b.w>20&&b.h>20&&!(b.w>=vb.width-4&&b.h>=vb.height-4));
let cr=0;for(const a of bs){for(const r of R){const ix=Math.min(a.x+a.w,r.x+r.w)-Math.max(a.x,r.x),iy=Math.min(a.y+a.h,r.y+r.h)-Math.max(a.y,r.y);if(ix>3&&iy>3){const inside=a.x>=r.x-3&&a.x+a.w<=r.x+r.w+3&&a.y>=r.y-3&&a.y+a.h<=r.y+r.h+3;if(!inside){cr++;if(cr<=2)bad.push('CROSSBOX:'+a.t);break}}}}
let cp=0;const pts=[];svg.querySelectorAll('path,line,polyline').forEach(e=>{try{if(e.closest('defs,marker,symbol,pattern'))return;const L=e.getTotalLength?e.getTotalLength():0;if(!L||L<12)return;const n=Math.min(80,Math.ceil(L/8));let hit=false;for(let i=0;i<=n&&!hit;i++){const q=e.getPointAtLength(L*i/n);const m=e.getCTM();for(const a of bs){if(q.x>a.x+2&&q.x<a.x+a.w-2&&q.y>a.y+3&&q.y<a.y+a.h-3){hit=true;break}}}if(hit)cp++}catch(er){}});
if(cp>0)bad.push('CROSSLINE:'+cp);
return bad}
const r={};document.querySelectorAll('svg').forEach(s=>{r[s.id]=chk(s)});document.title='R'+JSON.stringify(r);
</script>"""
for i in range(0,len(files),40):
    chunk=files[i:i+40];h='<html><body style="margin:0">'
    for k,f in enumerate(chunk):
        s=open(f).read();s=re.sub(r'<\?xml[^>]*\?>','',s);s=re.sub(r'<svg ','<svg id="%s" '%os.path.basename(f),s,1);h+=s
    h+=JS+'</body></html>'
    p=tempfile.mktemp(suffix='.html');open(p,'w').write(h)
    r=subprocess.run([CH,'--headless=new','--disable-gpu','--virtual-time-budget=3000','--dump-dom','file://'+p],capture_output=True,text=True).stdout
    m=re.search(r'<title>R(.*?)</title>',r,re.S)
    if m:
        import html;out.update(json.loads(html.unescape(m.group(1))))
    os.remove(p)
n=0
for f,v in out.items():
    if v: n+=1;print(f,v[:3])
print(n,'flagged of',len(out))
