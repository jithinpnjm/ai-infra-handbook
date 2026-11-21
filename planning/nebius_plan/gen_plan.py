import re,json,datetime,sys
def load(k):
    v,c=k.split('.'); t=open(f'map/{int(v):02d}-{int(c):02d}.md').read()
    title=t.split('\n')[0][2:]; m=s=0
    ver=re.search(r'Chapter verdict: *(.*)',t); ver=ver.group(1).strip() if ver else ''
    for l in t.split('\n'):
        if l.startswith('|') and not l.startswith('| #') and not l.startswith('|---'):
            c_=[x.strip() for x in l.strip('|').split('|')]
            if len(c_)>=7:
                try: mm=float(c_[-1])
                except: continue
                p=c_[-2].upper().split()[0] if c_[-2] else ''
                if p=='MUST': m+=mm
                if p=='SHOULD': s+=mm
    return title,m,s,ver
order="20.1 20.2 1.1 1.2 1.3 1.4 1.5 1.6 1.8 1.9 1.11 1.12 1.15 1.16 1.17 1.18 1.19 1.23 20.3 20.4 20.5 2.1 2.2 2.3 2.4 2.5 2.6 2.7 2.8 2.10 2.20 2.22 2.25 2.26 2.30 20.6 20.7 3.1 3.2 3.3 3.4 3.5 3.6 3.8 3.9 20.8 20.9 20.10 4.3 4.4 4.5 4.6 4.7 4.8 4.9 4.10 5.1 5.3 5.5 5.6 5.7 5.8 5.9 5.10 5.11 5.15 5.16 5.18 5.23 5.25 20.23 20.24 6.1 6.7 6.10 6.11 6.12 20.12 20.13 20.14 20.15 20.16 20.17 20.18 20.19 20.20 20.21 20.22 20.25 20.26 20.27 20.28".split()
cap=int(sys.argv[1]) if len(sys.argv)>1 else 300
days=[];cur=[];tot=0
for k in order:
    t,m,s,v=load(k)
    if cur and tot+m>cap+25: days.append(cur);cur=[];tot=0
    cur.append((k,t,m,s,v));tot+=m
days.append(cur)
print(len(days),'days',sum(x[2] for d in days for x in d)/60,'h')
for i,d in enumerate(days,1): print(i,round(sum(x[2] for x in d)),' '.join(x[0] for x in d))
json.dump(days,open('/tmp/days2.json','w'))

start=datetime.date(2026,11,25)
practice={1:"Terminal: set up a Linux VM/WSL/container; type every command from the chapters, do not just read.",
2:"Terminal: run ps, top, free, df, lsof, strace on your own box; break something small and fix it.",
3:"Do one full triage on a VM using the 20.3 checklist; write the 60-second USE summary.",
4:"Terminal: ip, ss, ping, traceroute, dig on your machine; read one tcpdump capture.",
5:"Terminal: curl -v/-w timing; dig +trace; ss -tnp; explain each aloud.",
6:"Network triage drill aloud (20.6). Start the 20.11 coding problems: 3 today.",
7:"Coding: 4 problems from 20.11 under a 30-min timer; write one subprocess/log-parsing script.",
8:"Ansible: write inventory + a playbook that installs and configures a service on a VM/container; run with --check, then for real, then again (idempotent). kind/minikube: create a cluster.",
9:"K8s: deploy, break a pod (ImagePullBackOff, CrashLoop), fix with kubectl describe/logs. Coding: 4 problems.",
10:"K8s: DNS from inside a pod, a Service with no endpoints, a Pending pod (5.25 playbooks). Slurm: read-only today, write the sbatch/srun/squeue/scancel cheat sheet.",
11:"Slurm: write one sbatch script (GPU request, array, dependency) and explain each line. First system-design drill: pick one prompt in 20.17, 35 min timed, speak aloud.",
12:"Second and third design drills; incident drill #1 (disk-full-node, ch26 script). Coding: 4 problems.",
13:"Incident drills #2 and #3 (dns-intermittent-failures, bad-config-push). Fill the project dossier (20.28). Then one full mock of each round type (see below)."}
out=["# Nebius SRE interview: personalised 14-day plan (25 Nov to 8 Dec 2026, interview 9 Dec)\n",
"Built from the section-level maps in `map/` (one file per chapter, written by agents that read the whole chapter). Each map lists every section with level, interview use, priority (MUST/SHOULD/OPTIONAL/SKIP) and minutes. **Daily reading budget = MUST sections only (about 5 h), plus 1-1.5 h hands-on practice and 20 min flashcards.**",
"For you: beginner in Linux and networking (so these come first, with real terminal work), refresh for Python and Kubernetes, Ansible and Slurm basics added, first Linux-troubleshooting and first system-design interview (design drills from day 11, incident drills from day 12).\n",
"How to use a day: open the chapter map, read ONLY the rows marked MUST in order (the sections column lists them), do the hands-on listed in the map, then the day's practice block.\n"]
for i,d in enumerate(days,1):
    dt=start+datetime.timedelta(days=i-1); tot=sum(x[2] for x in d)
    out.append(f"\n## Day {i} - {dt.strftime('%a %d %b')} - MUST reading {tot/60:.1f} h\n")
    out.append("| Chapter | MUST min | Also if time (SHOULD min) | Sections to read (from map) |\n|---|---|---|---|")
    for k,t,m,s,v in d:
        v1,c1=k.split('.'); out.append(f"| {t[:60]} (`map/{int(v1):02d}-{int(c1):02d}.md`) | {m:.0f} | {s:.0f} | {v[:170]} |")
    out.append(f"\nPractice: {practice.get(i,'')}\n")
out.append("""
## Day 13 mocks (after the reading above)
Spoken aloud with a timer: (1) 45-min Linux console triage using 20.3 + the 20.26 drill, (2) 30-min coding (2 problems), (3) 45-min system design from a fresh 20.17 prompt, (4) 20-min project walk-through (20.28).

## Day 14 - Tue 8 Dec: light day, no new material
1 h flashcards, one short incident drill, re-read your own notes and the one-page cheat sheet, check setup (Zoom, camera, quiet room; no AI tools allowed). Sleep early.

## If you fall behind
Drop in this order: 5.23, 3.9, 3.8, 2.20, 4.10, 6.12, 20.22, 20.25. Never drop: 20.3, 20.6, 20.7, 20.13, 20.18, 20.26, 20.28 and the Linux/network terminal practice.

## Not in the core plan (still mapped, read only if ahead)
Best first picks: 17.6, 17.7 (SLOs, failure modes), 4.18, 4.19 (Terraform basics, state), 5.12 (ingress), 6.2 (cluster anatomy), 6.8 and 6.9 (Slurm config, accounting), 20.36 (Soperator). Also: 1.7, 1.10, 1.13, 1.14, 1.20-1.22, 1.24-1.30; 2.9, 2.11-2.12, 2.21, 2.23-2.24, 2.31-2.32; 3.7; 5.2, 5.4, 5.13-5.14, 5.17, 5.19-5.22, 5.24; 17.1-17.3; 4.1, 4.2; 10.21; 11.2. Vol 20 ch30-38 (Nebius architecture) are not mapped yet.
""")
open('STUDY_PLAN.md','w').write('\n'.join(out))
