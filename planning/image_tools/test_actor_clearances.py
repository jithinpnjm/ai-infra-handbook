def check_clearances():
    # Actor 1
    box1 = (40, 145, 460, 260)
    icon1 = (270 - 24, 155, 48, 48)
    text1_lines = [
        ("kube-scheduler:", 30, 245),
        ("sees requests, labels,", 25, 282),
        ("allocatable; not", 25, 318),
        ("NUMA alignment", 25, 354)
    ]
    # Check text1
    for content, fs, y in text1_lines:
        w = len(content) * fs * 0.6
        left = 270 - w/2
        right = 270 + w/2
        top = y - fs * 0.8
        bottom = y + fs * 0.2
        print(f"Actor 1 '{content}': left={left:.1f}, right={right:.1f}, top={top:.1f}, bottom={bottom:.1f}")
        assert left >= box1[0] + 16, f"left padding fail: {left} vs {box1[0]+16}"
        assert right <= box1[0] + box1[2] - 16, f"right padding fail: {right} vs {box1[0]+box1[2]-16}"
        assert top >= icon1[1] + icon1[3] + 10, f"icon gap fail: {top} vs {icon1[1]+icon1[3]}"
        assert bottom <= box1[1] + box1[3] - 16, f"bottom padding fail: {bottom} vs {box1[1]+box1[3]-16}"

    # Actor 2
    box2 = (540, 145, 460, 260)
    icon2 = (770 - 24, 155, 48, 48)
    text2_lines = [
        ("kubelet", 30, 235),
        ("Topology Manager:", 30, 268),
        ("at admission tries to align", 25, 302),
        ("CPU, memory and devices", 25, 334),
        ("on one NUMA node", 25, 366)
    ]
    for content, fs, y in text2_lines:
        w = len(content) * fs * 0.6
        left = 770 - w/2
        right = 770 + w/2
        top = y - fs * 0.8
        bottom = y + fs * 0.2
        print(f"Actor 2 '{content}': left={left:.1f}, right={right:.1f}, top={top:.1f}, bottom={bottom:.1f}")
        assert left >= box2[0] + 16, f"left padding fail: {left} vs {box2[0]+16}"
        assert right <= box2[0] + box2[2] - 16, f"right padding fail: {right} vs {box2[0]+box2[2]-16}"
        assert top >= icon2[1] + icon2[3] + 5, f"icon gap fail: {top} vs {icon2[1]+icon2[3]}"
        assert bottom <= box2[1] + box2[3] - 16, f"bottom padding fail: {bottom} vs {box2[1]+box2[3]-16}"

    print("Actor 1 and Actor 2 clearances: ALL PASS!")

check_clearances()
