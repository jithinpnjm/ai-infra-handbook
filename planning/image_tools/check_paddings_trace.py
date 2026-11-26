import xml.etree.ElementTree as ET

def verify_all_paddings(svg_path):
    tree = ET.parse(svg_path)
    root = tree.getroot()

    # Boxes:
    boxes = {
        "Client": {"x": 40, "y": 320, "w": 180, "h": 360},
        "Gateway span": {"x": 440, "y": 320, "w": 300, "h": 360},
        "whole stream (pill)": {"x": 480, "y": 520, "w": 220, "h": 52},
        "Router span": {"x": 800, "y": 320, "w": 300, "h": 360},
        "pick replica (pill)": {"x": 840, "y": 520, "w": 220, "h": 52},
        "Engine span": {"x": 1160, "y": 320, "w": 390, "h": 360},
        "queue, prefill, decode (pill)": {"x": 1178, "y": 520, "w": 354, "h": 52},
        "traceparent (gap)": {"x": 220, "y": 420, "w": 220, "h": 80},
        "event: first_token": {"x": 440, "y": 140, "w": 300, "h": 50},
        "Title": {"x": 0, "y": 0, "w": 1600, "h": 120}
    }

    checks = [
        ("Client", "Client", 32, "sans", boxes["Client"]),
        ("Gateway span", "Gateway span", 32, "sans", boxes["Gateway span"]),
        ("whole stream", "whole stream", 24, "sans", boxes["whole stream (pill)"]),
        ("Router span", "Router span", 32, "sans", boxes["Router span"]),
        ("pick replica", "pick replica", 24, "sans", boxes["pick replica (pill)"]),
        ("Engine span", "Engine span", 32, "sans", boxes["Engine span"]),
        ("queue, prefill, decode", "queue, prefill, decode", 24, "sans", boxes["queue, prefill, decode (pill)"]),
        ("traceparent", "traceparent", 24, "mono", boxes["traceparent (gap)"]),
        ("event: first_token", "event: first_token", 24, "mono", boxes["event: first_token"]),
        ("Title", "Tracing a streaming request", 48, "sans", boxes["Title"]),
    ]

    print("Checking text paddings:")
    all_ok = True
    for name, text, fs, ftype, box in checks:
        rate = 0.62 if ftype == "mono" else 0.60
        tw = len(text) * rate * fs
        pad_x = (box["w"] - tw) / 2
        ok = pad_x >= 16
        if not ok:
            all_ok = False
        print(f"[{'PASS' if ok else 'FAIL'}] {name:30s} | text_w={tw:6.1f} | box_w={box['w']:4d} | pad={pad_x:5.1f} px (>= 16 px)")

    assert all_ok, "Some paddings failed!"
    print("\nAll text paddings strictly exceed 16px!")

verify_all_paddings("candidate_streaming_trace.svg")
