import re

parts = [
    "call the interpreter by absolute path: ",
    "/path/to/.venv/bin/python -m pip install requests; ",
    "systemd ExecStart=/opt/myops/.venv/bin/myops with Environment=PYTHONUNBUFFERED=1, ",
    "a dedicated user and ProtectSystem= hardening from chapter 1.15; log sys.executable"
]
joined = " ".join("".join(parts).split())
target = "call the interpreter by absolute path: /path/to/.venv/bin/python -m pip install requests; systemd ExecStart=/opt/myops/.venv/bin/myops with Environment=PYTHONUNBUFFERED=1, a dedicated user and ProtectSystem= hardening from chapter 1.15; log sys.executable"
print("Matches target:", joined == target)
