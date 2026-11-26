#!/usr/bin/env python3

def check_col_header(name, text, w, fs=24, is_mono=True):
    coeff = 0.62 if is_mono else 0.60
    txt_w = len(text) * fs * coeff
    pad = (w - txt_w) / 2
    ok = pad >= 16.0
    print(f"{name}: text='{text}' | w={w}, txt_w={txt_w:.1f}, pad={pad:.1f} [{'OK' if ok else 'FAIL'}]")

check_col_header("Col 1 Header", "metadata.resourceVersion", 395)
check_col_header("Col 2 Header", "metadata.generation", 345)
check_col_header("Col 3 Header", "status.observedGeneration", 415)
