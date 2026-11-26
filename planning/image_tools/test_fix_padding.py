# Test the fixes:
# 1. drain_to_quar:
w = 280
line1 = "validation failed"
line2 = "→ hardware repair"
line3 = "queue"
for l in [line1, line2, line3]:
    txt_w = len(l) * 14.4
    pad = (w - txt_w) / 2
    print(f"drain_to_quar '{l}': text_w={txt_w:.1f}, pad={pad:.1f} >= 16: {pad >= 16}")

# 2. quar_to_prov:
w = 280
l = "repaired/reimaged"
txt_w = len(l) * 14.4
pad = (w - txt_w) / 2
print(f"quar_to_prov '{l}': text_w={txt_w:.1f}, pad={pad:.1f} >= 16: {pad >= 16}")
