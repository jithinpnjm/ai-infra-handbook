import xml.etree.ElementTree as ET
import re

tree = ET.parse("test_keda_candidate.svg")
root = tree.getroot()

# Let's inspect all text and tspan elements and check conservative character bounds
# Sans: 0.60 * font_size per character
# Monospace: 0.62 * font_size per character
# Padding >= 16px required on all sides

# Map text elements to their container rectangles
checks = [
    # (label_name, text_line, font_size, font_family, x, y, rect_x, rect_y, rect_w, rect_h)
    # Stage A card
    ("Stage A Title", "Stage A", 30, "sans", 135, 146, 40, 95, 710, 225),
    ("Stage A line 1", "zero to one: the switch, handled by", 24, "sans", 76, 196, 58, 165, 674, 140),
    ("Stage A line 2", "KEDA operator (a plain HPA cannot", 24, "sans", 76, 224, 58, 165, 674, 140),
    ("Stage A line 3", "scale to zero because the formula", 24, "sans", 76, 252, 58, 165, 674, 140),
    ("Stage A line 4", "multiplies by zero)", 24, "sans", 76, 280, 58, 165, 674, 140),

    # Stage B card
    ("Stage B Title", "Stage B", 30, "sans", 945, 146, 850, 95, 710, 225),
    ("Stage B line 1", "one to N: the dimmer, handled by the", 24, "sans", 886, 196, 868, 165, 674, 140),
    ("Stage B line 2", "HPA that KEDA creates, fed by KEDA", 24, "sans", 886, 224, 868, 165, 674, 140),
    ("Stage B line 3", "metrics adapter on the", 24, "sans", 886, 252, 868, 165, 674, 140),
    ("Stage B line 4", "External Metrics API", 24, "sans", 886, 280, 868, 165, 674, 140),

    # ScaledObject batch-embed Title
    ("SO Title", "ScaledObject batch-embed", 30, "sans", 135, 392, 40, 340, 1520, 425),

    # Knobs
    ("minReplicaCount", "minReplicaCount 0", 24, "mono", 177 - len("minReplicaCount 0")*0.62*24/2, 456, 65, 420, 225, 56),
    ("maxReplicaCount", "maxReplicaCount 50", 24, "mono", 423 - len("maxReplicaCount 50")*0.62*24/2, 456, 306, 420, 235, 56),
    ("pollingInterval", "pollingInterval 15", 24, "mono", 669 - len("pollingInterval 15")*0.62*24/2, 456, 557, 420, 225, 56),

    ("cooldown line 1", "cooldownPeriod 300", 24, "mono", 85, 527, 65, 492, 717, 84),
    ("cooldown line 2", "(quiet time before one to zero)", 24, "mono", 85, 557, 65, 492, 717, 84),

    ("scaleDown", "scaleDown stabilizationWindowSeconds 600", 24, "mono", 85, 634, 65, 592, 717, 66),

    # Triggers
    ("kafka", "kafka lagThreshold 200", 24, "sans", 874, 459, 808, 420, 727, 62),
    ("prom line 1", "prometheus query sum", 24, "sans", 874, 533, 808, 498, 727, 78),
    ("prom line 2", "vllm:num_requests_waiting threshold 5", 24, "sans", 874, 561, 808, 498, 727, 78),
    ("cron line 1", "cron 0 8 to 0 20 Monday to Friday", 24, "sans", 874, 627, 808, 592, 727, 84),
    ("cron line 2", "desiredReplicas 4 (pre-warm business hours)", 24, "sans", 874, 655, 808, 592, 727, 84),

    # Rule bar
    ("rule", "the largest desired count across active triggers wins, so cron acts as a floor in business hours", 24, "sans", 800 - 96*0.6*24/2, 730, 65, 694, 1470, 54),

    # ScaledJob contrast
    ("SJ title", "ScaledJob transcribe-job", 30, "sans", 125, 838, 40, 785, 730, 195),
    ("SJ line 1", "one short Job per queued message,", 24, "sans", 65, 884, 40, 785, 730, 195),
    ("SJ line 2", "aws-sqs-queue queueLength 1,", 24, "sans", 65, 914, 40, 785, 730, 195),
    ("SJ line 3", "maxReplicaCount 20, strategy accurate", 24, "sans", 65, 944, 40, 785, 730, 195),

    # ScaledObject contrast
    ("SO contrast title", "ScaledObject", 30, "sans", 915, 838, 830, 785, 730, 195),
    ("SO contrast line 1", "keeps a long-running Deployment", 24, "sans", 855, 888, 830, 785, 730, 195),
    ("SO contrast line 2", "and changes its size", 24, "sans", 855, 920, 830, 785, 730, 195),

    # Warning
    ("warning line 1", "scale-to-zero on a GPU service costs a cold start; fine for a nightly batch job,", 24, "sans", 140, 1058, 40, 1000, 1520, 140),
    ("warning line 2", "painful for a person typing in chat", 24, "sans", 140, 1092, 40, 1000, 1520, 140),
]

all_passed = True
print(f"Testing paddings for {len(checks)} text segments:")
for name, text, fs, ff, tx, ty, rx, ry, rw, rh in checks:
    char_factor = 0.62 if ff == "mono" else 0.60
    est_w = len(text) * char_factor * fs
    # In SVG baseline: top of glyph is approximately y - fs*0.8, bottom is y + fs*0.2
    top_y = ty - fs * 0.8
    bot_y = ty + fs * 0.2
    right_x = tx + est_w

    pad_left = tx - rx
    pad_right = (rx + rw) - right_x
    pad_top = top_y - ry
    pad_bot = (ry + rh) - bot_y

    min_pad = min(pad_left, pad_right, pad_top, pad_bot)
    status = "OK" if min_pad >= 16.0 else "FAIL"
    if status == "FAIL":
        all_passed = False
    print(f"[{status}] {name:20s}: pad=(L:{pad_left:5.1f}, R:{pad_right:5.1f}, T:{pad_top:5.1f}, B:{pad_bot:5.1f}) min={min_pad:5.1f}px")

assert all_passed, "Some paddings were < 16px!"
print("\n>>> ALL PADDINGS >= 16px (100% PASS)! <<<")
