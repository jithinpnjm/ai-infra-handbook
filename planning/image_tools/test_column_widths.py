import re

# Test all labels inside their proposed cards

col1_card_w = 260 # inside col1 (w=290, padding 15 each side -> card w=260)
# Pod labels:
# "glibc resolver" -> 26px sans: 14 * 26 * 0.6 = 218.4 < 260. Pad = (260-218.4)/2 = 20.8 >= 16.
# "one UDP socket" -> 24px mono: 14 * 24 * 0.62 = 208.3 < 260. Pad = (260-208.3)/2 = 25.8 >= 16.
# "both to the same source IP and port":
#   "both to the same" (16 chars * 24 * 0.6 = 230.4 < 260. Pad = 14.8? Let's check card width 270)
#   If col1 card w = 270: pad = (270 - 230.4)/2 = 19.8 >= 16!
#   "source IP and port" (18 chars * 24 * 0.6 = 259.2. In 270 card, pad = 5.4! Too small!)
# What if 3 lines for "both to the same source IP and port":
#   Line 1: "both to the" (11 chars -> 158.4 px)
#   Line 2: "same source" (11 chars -> 158.4 px)
#   Line 3: "IP and port" (11 chars -> 158.4 px)
# Wow! Each line is 11 chars = 158.4 px! In a 260px card, padding is (260 - 158.4) / 2 = 50.8 px!
print("Col 1 3-line wrap for 'both to the same source IP and port' max width:", 11 * 24 * 0.6)

# Step 4 on pod side:
# "waits for default 5 s timeout, then retries"
# 3 lines:
#   Line 1: "waits for" (9 chars -> 129.6 px)
#   Line 2: "default 5 s timeout," (20 chars * 24 * 0.6 = 288 px? In 260 card that overflows!)
# Let's split into 3 lines:
#   Line 1: "waits for default" (17 chars * 14.4 = 244.8 px)
#   Line 2: "5 s timeout," (12 chars * 14.4 = 172.8 px)
#   Line 3: "then retries" (12 chars * 14.4 = 172.8 px)
# Or:
#   Line 1: "waits for default 5 s" (21 chars) -> wait, what if col1 is 310 px, card is 280 px?
#   21 * 24 * 0.6 = 302.4. In 280 card it's slightly > 280.
#   What if 4 lines?
#   Line 1: "waits for" (9 chars, 130 px)
#   Line 2: "default 5 s" (11 chars, 158 px)
#   Line 3: "timeout," (8 chars, 115 px)
#   Line 4: "then retries" (12 chars, 173 px)
# Max width is only 173 px! In a 260px card, padding is (260 - 173)/2 = 43.5 px >= 16 px!
print("Step 4 4-line wrap max width:", 12 * 24 * 0.6)

# Col 3: "kube-proxy DNAT to a CoreDNS pod chosen by KUBE-SVC"
# Split into 4 lines:
#   Line 1: "kube-proxy DNAT" (15 chars * 14.4 = 216 px)
#   Line 2: "to a CoreDNS pod" (16 chars * 14.4 = 230.4 px)
#   Line 3: "chosen by" (9 chars * 14.4 = 129.6 px)
#   Line 4: "KUBE-SVC" (8 chars * 24 * 0.62 = 119 px)
# Max width is 230.4 px! In a 280px card, padding is (280 - 230.4)/2 = 24.8 px >= 16 px!
print("Col 3 4-line wrap max width:", 16 * 24 * 0.6)

# "the two packets may go to different CoreDNS pods"
# Split into 3 lines:
#   Line 1: "the two packets" (15 chars * 14.4 = 216 px)
#   Line 2: "may go to different" (19 chars * 14.4 = 273.6 px)
#   Line 3: "CoreDNS pods" (12 chars * 14.4 = 172.8 px)
# What if 4 lines:
#   Line 1: "the two packets" (15 chars -> 216 px)
#   Line 2: "may go to" (9 chars -> 130 px)
#   Line 3: "different" (9 chars -> 130 px)
#   Line 4: "CoreDNS pods" (12 chars -> 173 px)
# Max width is only 216 px! In a 280px card, padding is (280 - 216)/2 = 32 px >= 16 px!
print("Col 3 note 4-line wrap max width:", 15 * 24 * 0.6)

# Col 4: "the second insertion collides with the first"
# Split into 3 lines:
#   Line 1: "the second" (10 chars -> 144 px)
#   Line 2: "insertion collides" (18 chars * 14.4 = 259.2 px)
#   Line 3: "with the first" (14 chars * 14.4 = 201.6 px)
# In a 300px card (Col 4 w=340), padding is (300 - 259.2)/2 = 20.4 px >= 16 px!
print("Col 4 3-line wrap max width:", 18 * 24 * 0.6)

# "the packet is silently dropped"
# Split into 2 lines:
#   Line 1: "the packet is" (13 chars * 14.4 = 187.2 px)
#   Line 2: "silently dropped" (16 chars * 14.4 = 230.4 px)
# Max width 230.4 px in 300px card -> padding (300 - 230.4)/2 = 34.8 px >= 16 px!
print("Col 4 drop 2-line wrap max width:", 16 * 24 * 0.6)
