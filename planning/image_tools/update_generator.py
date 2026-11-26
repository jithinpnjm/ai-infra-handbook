with open("generate_and_audit_mistakes.py") as f:
    text = f.read()

# Replace rows_data
new_rows_data = '''    rows_data = [
        {
            "id": "exceptions",
            "area_title": ["Exceptions"],
            "rh": 104,
            "mistake_lines": [
                "bare except and except Exception: pass;",
                "catching too much around too much code",
                "loses tracebacks and hides bugs"
            ],
            "fix_lines": [
                "catch the narrowest exception,",
                "log once at the top"
            ],
            "orange": False
        },
        {
            "id": "files",
            "area_title": ["Files"],
            "rh": 130,
            "mistake_lines": [
                "writing in place leads to partial writes;",
                "declaring success before an fsync;",
                "exists-then-create checks leave gaps; no",
                "explicit encoding; mixing bytes and str"
            ],
            "fix_lines": [
                "atomic replace, fsync, attempt",
                "then handle, encoding=utf-8"
            ],
            "orange": False
        },
        {
            "id": "subprocess",
            "area_title": ["Subprocess"],
            "rh": 178,
            "mistake_lines": [
                "shell=True with interpolated input; missing",
                "timeouts; ignored return codes; parsing",
                "human-formatted output; secrets in command",
                "lines; capturing huge output in memory; pipe",
                "deadlocks; unreaped children; os.system,",
                "os.popen and the deprecated commands module"
            ],
            "fix_lines": [
                "argument list, timeout, check,",
                "machine-readable output,",
                "communicate, wait"
            ],
            "orange": False
        },
        {
            "id": "global_state",
            "area_title": ["Global", "state"],
            "rh": 104,
            "mistake_lines": [
                "mutating os.environ or os.chdir inside a",
                "library affects every caller; assuming the",
                "current directory"
            ],
            "fix_lines": [
                "copy the environment for the",
                "child, pass explicit paths"
            ],
            "orange": True
        },
        {
            "id": "reruns",
            "area_title": ["Re-runs"],
            "rh": 104,
            "mistake_lines": [
                "scripts unsafe to re-run"
            ],
            "fix_lines": [
                "dry-run mode, a lock against",
                "overlapping runs, UTC timestamps",
                "rather than naive ones"
            ],
            "orange": False
        },
        {
            "id": "signals",
            "area_title": ["Signals"],
            "rh": 78,
            "mistake_lines": [
                "heavy work in signal handlers;",
                "ignoring SIGTERM in containers"
            ],
            "fix_lines": [
                "set a flag, finish and exit"
            ],
            "orange": False
        },
        {
            "id": "untrusted_input",
            "area_title": ["Untrusted", "input"],
            "rh": 104,
            "mistake_lines": [
                "extracting tar or zip archives without",
                "validating paths; yaml.load or pickle on",
                "data from the network"
            ],
            "fix_lines": [
                "validate member paths,",
                "filter=data, safe_load"
            ],
            "orange": False
        }
    ]'''

# Replace in file
import re
text = re.sub(r'rows_data = \[.*?\]\n    \]', new_rows_data, text, flags=re.DOTALL)

# Update positions
text = re.sub(r'header_y = \d+', 'header_y = 100', text)
text = re.sub(r'cur_y = \d+', 'cur_y = 150', text)
text = re.sub(r'm_start_y = cur_y \+ \d+', 'm_start_y = cur_y + 34', text)
text = re.sub(r'f_start_y = cur_y \+ \d+', 'f_start_y = cur_y + 34', text)
text = re.sub(r'dy = 0 if idx == 0 else \d+', 'dy = 0 if idx == 0 else 25', text)
text = re.sub(r'stories_y = cur_y \+ \d+', 'stories_y = cur_y + 12', text)
text = re.sub(r'bottom_y = stories_y \+ stories_h \+ \d+', 'bottom_y = stories_y + stories_h + 12', text)

with open("generate_and_audit_mistakes.py", "w") as f:
    f.write(text)

