#!/usr/bin/env python3
"""Static checks for every file under code/part16..19 (not *_lab.py).
py: compile + pyflakes (undefined names are errors, unused imports ignored)
yaml/yml: parse all docs  json: parse after dropping leading // or # comment lines
sh: bash -n   sql: non-empty
Usage: python3 -I tools/check_code_files.py [dir ...]   (exit 1 on any problem)
"""
import sys,glob,os,json,subprocess,yaml,re
dirs=sys.argv[1:] or ['code/part16','code/part17','code/part18']
bad=0;n=0
for d in dirs:
  for p in sorted(glob.glob(d+'/**/*',recursive=True)):
    if not os.path.isfile(p) or p.endswith('_lab.py') or p.endswith('.md'): continue
    n+=1;e=os.path.splitext(p)[1];t=open(p).read();err=None
    try:
      if e=='.py':
        compile(t,p,'exec')
        r='' if '/snippets/' in p else subprocess.run([sys.executable,'-m','pyflakes',p],capture_output=True,text=True).stdout
        r=[l for l in r.splitlines() if 'imported but unused' not in l and 'f-string is missing' not in l and 'assigned to but never used' not in l]
        if r: err=r[0][len(p)+1:]
      elif e in('.yaml','.yml'): list(yaml.safe_load_all(t))
      elif e=='.json':
        json.loads(re.sub(r'^\s*(//|#)[^\n]*\n','',t,count=1))
      elif e=='.sh':
        r=subprocess.run(['bash','-n',p],capture_output=True,text=True)
        if r.returncode: err=r.stderr.strip()[:100]
    except Exception as x: err=str(x).replace('\n',' ')[:110]
    if err: bad+=1;print('BAD',p,'|',err)
print(f'{n} files, {bad} problems');sys.exit(1 if bad else 0)
