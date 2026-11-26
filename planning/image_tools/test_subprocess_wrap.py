text = "shell=True with interpolated input; missing timeouts; ignored return codes; parsing human-formatted output; secrets in command lines; capturing huge output in memory; pipe deadlocks; unreaped children; os.system, os.popen and the deprecated commands module"

# Let's see what happens with 5 lines at width 700
lines_5 = [
    "shell=True with interpolated input; missing timeouts;",
    "ignored return codes; parsing human-formatted output;",
    "secrets in command lines; capturing huge output",
    "in memory; pipe deadlocks; unreaped children;",
    "os.system, os.popen and the deprecated commands module"
]

print("Matches?", " ".join(lines_5) == text)
for l in lines_5:
    w = len(l) * 24 * 0.60 # sans
    wm = len(l) * 24 * 0.62 # mono
    print(f"len={len(l):2d} | sans={w:5.1f}px | mono={wm:5.1f}px | '{l}'")
