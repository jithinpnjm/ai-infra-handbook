#!/usr/bin/env python3

boxes = [
    # 1. Trigger box: x=40, y=145, w=240, h=395
    {
        "name": "trigger-origin",
        "box": (40, 145, 240, 395),
        "lines": [
            ("docker stop or", 24, "sans", 160, "middle", 335),
            ("kubelet sends", 24, "sans", 160, "middle", 367),
            ("SIGTERM", 24, "sans", 160, "middle", 399),
        ]
    },
    # 2. Track 1 Box 1: PID 1 has no default action...
    # rect x=325, y=194, w=330, h=132
    {
        "name": "t1-box1",
        "box": (325, 194, 330, 132),
        "lines": [
            ("PID 1 has no default", 24, "sans", 490, "middle", 230),
            ("action, so with no", 24, "sans", 490, "middle", 256),
            ("handler the signal", 24, "sans", 490, "middle", 282),
            ("is ignored", 24, "sans", 490, "middle", 308),
        ]
    },
    # 3. Track 1 Box 2: wait bar 'grace period, 30 seconds in Kubernetes by default'
    # rect x=680, y=194, w=270, h=132
    {
        "name": "t1-box2",
        "box": (680, 194, 270, 132),
        "lines": [
            ("grace period, 30", 24, "sans", 815, "middle", 230),
            ("seconds in", 24, "sans", 815, "middle", 256),
            ("Kubernetes", 24, "sans", 815, "middle", 282),
            ("by default", 24, "sans", 815, "middle", 308),
        ]
    },
    # 4. Track 1 Box 3: 'SIGKILL from the parent namespace'
    # rect x=975, y=194, w=265, h=132
    {
        "name": "t1-box3",
        "box": (975, 194, 265, 132),
        "lines": [
            ("SIGKILL from the", 24, "sans", 1107.5, "middle", 250),
            ("parent namespace", 24, "sans", 1107.5, "middle", 282),
        ]
    },
    # 5. Track 1 Box 4: 'training job loses its chance to checkpoint'
    # rect x=1265, y=194, w=295, h=132
    {
        "name": "t1-box4",
        "box": (1265, 194, 295, 132),
        "lines": [
            ("training job loses", 24, "sans", 1412.5, "middle", 240),
            ("its chance to", 24, "sans", 1412.5, "middle", 270),
            ("checkpoint", 24, "sans", 1412.5, "middle", 300),
        ]
    },
    # 6. Track 2 Box 1: 'handler runs'
    # rect x=325, y=405, w=340, h=120
    {
        "name": "t2-box1",
        "box": (325, 405, 340, 120),
        "lines": [
            ("handler runs", 26, "sans", 495, "middle", 472),
        ]
    },
    # 7. Track 2 Box 2: 'checkpoint written'
    # rect x=740, y=405, w=400, h=120
    {
        "name": "t2-box2",
        "box": (740, 405, 400, 120),
        "lines": [
            ("checkpoint written", 26, "sans", 940, "middle", 472),
        ]
    },
    # 8. Track 2 Box 3: 'clean exit'
    # rect x=1215, y=405, w=345, h=120
    {
        "name": "t2-box3",
        "box": (1215, 405, 345, 120),
        "lines": [
            ("clean exit", 26, "sans", 1387.5, "middle", 472),
        ]
    },
    # 9. Card 1: rect x=40, y=610, w=480, h=310
    {
        "name": "card-1",
        "box": (40, 610, 480, 310),
        "lines": [
            ("Signals: from inside the", 24, "sans", 65, "start", 700),
            ("namespace a signal reaches", 24, "sans", 65, "start", 728),
            ("PID 1 only if it installed", 24, "sans", 65, "start", 756),
            ("a handler; SIGKILL and", 24, "sans", 65, "start", 784),
            ("SIGSTOP from inside are", 24, "sans", 65, "start", 812),
            ("ignored; from the parent", 24, "sans", 65, "start", 840),
            ("namespace they still work", 24, "sans", 65, "start", 868),
        ]
    },
    # 10. Card 2: rect x=560, y=610, w=480, h=310
    {
        "name": "card-2",
        "box": (560, 610, 480, 310),
        "lines": [
            ("Zombies: orphans are", 24, "sans", 585, "start", 715),
            ("re-parented to PID 1,", 24, "sans", 585, "start", 747),
            ("which must call wait();", 24, "sans", 585, "start", 779),
            ("otherwise zombies pile up", 24, "sans", 585, "start", 811),
            ("and can exhaust pids.max", 24, "sans", 585, "start", 843),
        ]
    },
    # 11. Card 3: rect x=1080, y=610, w=480, h=310
    {
        "name": "card-3",
        "box": (1080, 610, 480, 310),
        "lines": [
            ("When PID 1 exits the", 24, "sans", 1105, "start", 700),
            ("kernel kills every other", 24, "sans", 1105, "start", 732),
            ("process in the namespace", 24, "sans", 1105, "start", 764),
            ("with SIGKILL, which is why", 24, "sans", 1105, "start", 796),
            ("a container dies when its", 24, "sans", 1105, "start", 828),
            ("main process dies", 24, "sans", 1105, "start", 860),
        ]
    },
    # 12. Fix strip: rect x=40, y=940, w=1520, h=110
    {
        "name": "fix-strip",
        "box": (40, 940, 1520, 110),
        "lines": [
            ("exec in the entrypoint; tini; docker run --init; dumb-init;", 24, "mono", 135, "start", 985),
            ("Kubernetes shareProcessNamespace; exec form [\"python\",\"train.py\"] not the shell form", 24, "mono", 135, "start", 1019),
        ]
    },
    # 13. Bottom bar: rect x=40, y=1075, w=1520, h=90
    {
        "name": "bottom-bar",
        "box": (40, 1075, 1520, 90),
        "lines": [
            ("End the script with exec so the program becomes PID 1", 30, "sans", 800, "middle", 1130),
        ]
    }
]

print("Checking paddings across all boxes:")
all_pass = True
for b in boxes:
    bx, by, bw, bh = b["box"]
    for text, fs, font, anchor_x, anchor_type, y in b["lines"]:
        mult = 0.62 if font == "mono" else 0.60
        text_w = len(text) * mult * fs
        if anchor_type == "middle":
            x_start = anchor_x - text_w / 2
            x_end = anchor_x + text_w / 2
        else: # start
            x_start = anchor_x
            x_end = anchor_x + text_w
        
        left_pad = x_start - bx
        right_pad = (bx + bw) - x_end
        top_pad = (y - fs * 0.8) - by
        bot_pad = (by + bh) - y

        ok = (left_pad >= 16 and right_pad >= 16 and top_pad >= 15 and bot_pad >= 15)
        if not ok:
            all_pass = False
            print(f"FAIL in {b['name']}: '{text[:30]}...' left_pad={left_pad:.1f}, right_pad={right_pad:.1f}, top_pad={top_pad:.1f}, bot_pad={bot_pad:.1f}")
        else:
            print(f"PASS in {b['name']}: '{text[:25]}...' left={left_pad:.1f}px, right={right_pad:.1f}px, top={top_pad:.1f}px, bot={bot_pad:.1f}px")

if all_pass:
    print("\nALL BOX PADDINGS >= 16px (and vertical >= 15px) VERIFIED PERFECTLY!")
else:
    print("\nSOME PADDINGS FAILED!")
