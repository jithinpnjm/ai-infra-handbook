#!/usr/bin/env python3

def est_width(text, fs, is_mono=False):
    factor = 0.62 if is_mono else 0.60
    return len(text) * fs * factor

labels_info = [
    ("Cutting a path apart with parameter expansion, no external commands", 48, False),
    ("/data/run42", 28, True),
    ("/", 32, True),
    ("model.final", 28, True),
    (".", 32, True),
    ("ckpt", 28, True),
    ("${path##*/}", 26, True),
    ("removes the longest matching prefix up to the last slash: result 'model.final.ckpt' (same as basename)", 24, False),
    ("${path%/*}", 26, True),
    ("removes the shortest matching suffix starting at the last slash: result '/data/run42' (same as dirname)", 24, False),
    ("${path%.*}", 26, True),
    ("removes the shortest suffix starting at the last dot: result '/data/run42/model.final'", 24, False),
    ("${path##*.}", 26, True),
    ("removes the longest prefix up to the last dot: result 'ckpt'", 24, False),
    ("# / ## remove shortest / longest prefix", 24, False),
    ("% / %% remove shortest / longest suffix", 24, False),
    ("${#path} length", 24, False),
    ("${var:-default}", 26, True),
    ("${var:=default}", 26, True),
    ("${var:?message}", 26, True)
]

for text, fs, is_mono in labels_info:
    w = est_width(text, fs, is_mono)
    print(f"[{'M' if is_mono else 'S'} {fs}px] w={w:6.1f}px | '{text}'")
