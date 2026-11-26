#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

def check_label_fits(x1, x2, text, size=24):
    w = len(text) * size * 0.6
    space = x2 - x1
    fits = w + 32 <= space
    print(f"'{text}': est_w={w:.1f}px, space={space:.1f}px, margin={(space-w)/2:.1f}px, fits={fits}")
    return fits

print("--- Testing Red Arrow Label Fits ---")
check_label_fits(420, 980, "Nearest region:", 25)
check_label_fits(420, 980, "breaks the promise without an error", 25)

print("\n--- Testing Metering Label Fits ---")
check_label_fits(1020, 1540, "Metering events leave only", 25)
check_label_fits(1020, 1540, "after content is stripped", 25)

print("\n--- Testing Logs Stay Label Fits ---")
check_label_fits(90, 530, "Prompts, completions and", 24)
check_label_fits(90, 530, "logs stay in region", 24)

print("\n--- Testing Green Arrow Label Fits ---")
check_label_fits(280, 700, "Routed by endpoint region", 26)
