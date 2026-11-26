import re

spec = '''Two side-by-side flow diagrams for the same three commands. Left panel 'if a; then b; else c; fi' (correct): start, diamond 'a succeeds?' yes goes to box 'b' then end; no goes to box 'c' then end. Right panel 'a && b || c' (trap): start, diamond 'a succeeds?'; yes goes to box 'b', then a second diamond 'b succeeded?' with yes to end and no to box 'c' (orange outlined, 'c runs even though a succeeded'); the first diamond's no arrow goes to box 'c'. Two arrows into box 'c' in the right panel are labelled 'a failed' and 'b failed'. Below, a short list of good one-line guards from the chapter in monospace: '[ -d "$d" ] || mkdir -p "$d"', 'command -v nvidia-smi >/dev/null || exit 0', 'cd "$dir" || exit 1', '[ -z "$x" ] && { echo "empty" >&2; exit 1; }'. Bottom note: '&& runs the next command only if the last one succeeded; || only if it failed'.'''

quoted = re.findall(r"'([^']+)'", spec)
print("Quoted strings in spec:")
for i, q in enumerate(quoted, 1):
    print(f"  {i:2d}. '{q}'")
