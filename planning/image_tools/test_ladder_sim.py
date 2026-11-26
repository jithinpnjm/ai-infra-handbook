import re

# Font metrics conservative estimators from rules:
# sans: 0.6 * font-size per char
# mono: 0.62 * font-size per char

def sans_w(text, fs=24):
    return len(text) * 0.6 * fs

def mono_w(text, fs=24):
    return len(text) * 0.62 * fs

commands = [
    ("uptime", 24),
    ("dmesg -T | tail", 24),
    ("vmstat -SM 1", 24),
    ("mpstat -P ALL 1", 24),
    ("pidstat 1", 24),
    ("iostat -sxz 1", 24),
    ("free -m", 24),
    ("sar -n DEV 1", 24),
    ("sar -n TCP,ETCP 1", 24),
    ("top", 24),
]

for cmd, fs in commands:
    print(f"Command '{cmd}': mono width = {mono_w(cmd, fs):.1f} px")

