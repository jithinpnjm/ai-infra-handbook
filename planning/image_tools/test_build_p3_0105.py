#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re
import subprocess
import pathlib

# Height budget: 1100 px
W = 1600
H = 1100

expected_labels = [
    "SSH forwards compared: which side listens and where traffic goes",
    "Which side listens?",
    "Where does the traffic go?",
    "Your machine",
    "Server",
    "SSH connection, port 22",
    "-L local forward",
    "ssh -L 6006:localhost:6006 gpu01",
    "listens on 6006",
    "localhost:6006 on gpu01",
    "open http://localhost:6006 to reach TensorBoard",
    "-R remote forward",
    "ssh -R 9000:localhost:8000 server",
    "listens on 9000",
    "localhost:8000 on your machine",
    "-D dynamic forward",
    "ssh -D 1080 bastion",
    "SOCKS proxy on 1080",
    "traffic goes through bastion to any destination",
    "-N -f: no remote command, go to background"
]

print(f"Total expected labels: {len(expected_labels)}")
