import xml.etree.ElementTree as ET
import re

checks = [
    # Stage A card
    ("Stage A Title", "Stage A", 30, "sans", 135, 142, 40, 90, 710, 235),
    ("Stage A line 1", "zero to one: the switch, handled by", 24, "sans", 76, 196, 58, 162, 674, 150),
    ("Stage A line 2", "KEDA operator (a plain HPA cannot", 24, "sans", 76, 224, 58, 162, 674, 150),
    ("Stage A line 3", "scale to zero because the formula", 24, "sans", 76, 252, 58, 162, 674, 150),
    ("Stage A line 4", "multiplies by zero)", 24, "sans", 76, 280, 58, 162, 674, 150),

    # Stage B card
    ("Stage B Title", "Stage B", 30, "sans", 945, 142, 850, 90, 710, 235),
    ("Stage B line 1", "one to N: the dimmer, handled by the", 24, "sans", 886, 196, 868, 162, 674, 150),
    ("Stage B line 2", "HPA that KEDA creates, fed by KEDA", 24, "sans", 886, 224, 868, 162, 674, 150),
    ("Stage B line 3", "metrics adapter on the", 24, "sans", 886, 252, 868, 162, 674, 150),
    ("Stage B line 4", "External Metrics API", 24, "sans", 886, 280, 868, 162, 674, 150),

    # ScaledObject batch-embed Title
    ("SO Title", "ScaledObject batch-embed", 30, "sans", 135, 392, 40, 340, 1520, 425),

    # Knobs
    ("minReplicaCount", "minReplicaCount 0", 24, "mono", 237 - len("minReplicaCount 0")*0.62*24/2, 450, 65, 415, 345, 54),
    ("maxReplicaCount", "maxReplicaCount 50", 24, "mono", 608 - len("maxReplicaCount 50")*0.62*24/2, 450, 435, 415, 347, 54),
    ("pollingInterval", "pollingInterval 15", 24, "mono", 423 - len("pollingInterval 15")*0.62*24/2, 513, 65, 480, 717, 50),

    ("cooldown line 1", "cooldownPeriod 300", 24, "mono", 85, 570, 65, 540, 717, 74),
    ("cooldown line 2", "(quiet time before one to zero)", 24, "mono", 85, 598, 65, 540, 717, 74),

    ("scaleDown", "scaleDown stabilizationWindowSeconds 600", 24, "mono", 85, 657, 65, 624, 717, 50),

    # Triggers
    ("kafka", "kafka lagThreshold 200", 24, "sans", 874, 450, 808, 415, 727, 54),
    ("prom line 1", "prometheus query sum", 24, "sans", 874, 515, 808, 480, 727, 84),
    ("prom line 2", "vllm:num_requests_waiting threshold 5", 24, "sans", 874, 543, 808, 480, 727, 84),
    ("cron line 1", "cron 0 8 to 0 20 Monday to Friday", 24, "sans", 874, 610, 808, 575, 727, 84),
    ("cron line 2", "desiredReplicas 4 (pre-warm business hours)", 24, "sans", 874, 638, 808, 575, 727, 84),

    # Rule bar
    ("rule", "the largest desired count across active triggers wins, so cron acts as a floor in business hours", 24, "sans", 800 - 96*0.6*24/2, 726, 65, 688, 1470, 60),

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
print("\n>>> ALL 32 TEXT SEGMENT PADDINGS >= 16.0px (100% PASS)! <<<")
