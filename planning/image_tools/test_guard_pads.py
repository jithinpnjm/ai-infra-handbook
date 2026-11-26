# Guard strip: h = 145
# Baseline 1 = y + 38
# dy2 = 28
# dy3 = 28
# dy4 = 28
# Baselines:
# b1 = 38
# b2 = 38 + 28 = 66
# b3 = 66 + 28 = 94
# b4 = 94 + 28 = 122

# Top of first line (fs=30): 38 - 0.72 * 30 = 38 - 21.6 = 16.4 px >= 16 px!
# Bottom of last line (fs=24): 122 + 0.22 * 24 = 122 + 5.3 = 127.3 px
# Bottom padding: 145 - 127.3 = 17.7 px >= 16 px!
print("Guard strip with h=145: top_pad=16.4, bot_pad=17.7 -> PERFECT!")
