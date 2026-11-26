col2_left = 505
col2_right = 945
col2_w = col2_right - col2_left # 440 px

# Row 4 check commands:
# text1: "quota -u"
w1 = len("quota -u") * 24 * 0.62 # 119.04
# text2: "xfs_quota"
w2 = len("xfs_quota") * 24 * 0.62 # 133.92
# text3: "repquota"
w3 = len("repquota") * 24 * 0.62 # 119.04

# If line 1 has quota -u and xfs_quota:
# Let quota -u be at x=530 -> right edge = 530 + 119.04 = 649.04
# Let xfs_quota be at x=710 -> right edge = 710 + 133.92 = 843.92
# Left padding from col2_left = 530 - 505 = 25 px >= 16 px
# Right padding to col2_right = 945 - 843.92 = 101.08 px >= 16 px
# Gap between commands = 710 - 649.04 = 60.96 px >= 16 px
# Line 2 has repquota centered:
# cx = (505 + 945)/2 = 725
# x = 725 - w3/2 = 665.48 -> say 665. Right edge = 665 + 119.04 = 784.04
# Left padding = 665 - 505 = 160 px, Right padding = 945 - 784 = 161 px

print("Row 4 layout:")
print(f"quota -u: [530, {530+w1:.1f}], pad_l={530-col2_left}")
print(f"xfs_quota: [710, {710+w2:.1f}], pad_r={col2_right-(710+w2):.1f}")
print(f"gap: {710-(530+w1):.1f}")
print(f"repquota: [665, {665+w3:.1f}], pad_l={665-col2_left}, pad_r={col2_right-(665+w3):.1f}")

assert 530 - col2_left >= 16
assert col2_right - (710 + w2) >= 16
assert 710 - (530 + w1) >= 16
assert 665 - col2_left >= 16
assert col2_right - (665 + w3) >= 16
print("PASS: Row 4 all paddings >= 16 px!")
