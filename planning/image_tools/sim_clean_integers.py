# Clean integer solution
# Widths:
# B0 (kubectl): w=160
# B1 (kube-apiserver): w=196
# B2 (etcd): w=110
# B3 (controller-manager): w=232
# B4 (scheduler): w=196
# B5 (kubelet (node)): w=160
# B6 (runtime (containerd)): w=210

# Total w = 1264
# Total available = 1600 - 80 = 1520
# 1520 - 1264 = 256
# 256 = 42 + 43 + 43 + 43 + 43 + 42
gaps = [42, 43, 43, 43, 43, 42]
widths = [160, 196, 110, 232, 196, 160, 210]

x = 40
boxes = []
for i in range(7):
    w = widths[i]
    boxes.append({
        "i": i,
        "x": x,
        "w": w,
        "cx": x + w // 2,
        "right": x + w
    })
    if i < 6:
        x += w + gaps[i]

for b in boxes:
    print(f"Box {b['i']}: x={b['x']}, w={b['w']}, right={b['right']}, cx={b['cx']}")

for i in range(6):
    print(f"Gap {i}-{i+1}: {boxes[i+1]['x'] - boxes[i]['right']}")

print("Right margin:", 1600 - boxes[-1]['right'])
