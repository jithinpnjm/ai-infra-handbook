#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re
import subprocess
import pathlib

# Let's check the exact character lengths and required box widths for all labels:

labels = {
    "title": "SSH forwards compared: which side listens and where traffic goes",
    "q1": "Which side listens?",
    "q2": "Where does the traffic go?",
    "m1": "Your machine",
    "m2": "Server",
    "ssh_conn": "SSH connection, port 22",
    "l1_title": "-L local forward",
    "l1_cmd": "ssh -L 6006:localhost:6006 gpu01",
    "l1_listen": "listens on 6006",
    "l1_dest": "localhost:6006 on gpu01",
    "l1_note": "open http://localhost:6006 to reach TensorBoard",
    "l2_title": "-R remote forward",
    "l2_cmd": "ssh -R 9000:localhost:8000 server",
    "l2_listen": "listens on 9000",
    "l2_dest": "localhost:8000 on your machine",
    "l3_title": "-D dynamic forward",
    "l3_cmd": "ssh -D 1080 bastion",
    "l3_listen": "SOCKS proxy on 1080",
    "l3_dest": "traffic goes through bastion to any destination",
    "footer": "-N -f: no remote command, go to background"
}

for k, text in labels.items():
    is_mono = "cmd" in k
    fs = 24 if is_mono or "note" in k or "ssh" in k or "dest" in k else (48 if k == "title" else 30)
    w = len(text) * (0.62 if is_mono else 0.6) * fs
    print(f"{k:12s} ({fs}px, {'mono' if is_mono else 'sans'}): len={len(text):2d}, min_w={w:6.1f} | '{text}'")
