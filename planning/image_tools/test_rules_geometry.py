def check_rules():
    box_x = 55
    box_w = 905
    box_right = box_x + box_w # 960
    
    rules = [
        ("Rule 1", "match with probability 1/N, else fall through"),
        ("rule 2", "match with probability 1/(N-1), else fall through"),
        ("rule 3", "match with probability 1/(N-2)"),
        ("last rule", "match always")
    ]
    
    for r_title, r_cond in rules:
        # circle at cx=85, r=20 -> right=105
        # title at x=120, fs=26 sans
        t_w = len(r_title) * 26 * 0.6
        t_right = 120 + t_w
        
        # cond at x=235 (or 245 for last rule)
        c_x = max(235, t_right + 16)
        c_w = len(r_cond) * 24 * 0.6
        c_right = c_x + c_w
        
        pad_right = box_right - c_right
        print(f"Rule '{r_title}': title ends {t_right:.1f}, cond at {c_x}, cond ends {c_right:.1f}, pad_right = {pad_right:.1f}px")
        assert pad_right >= 16, f"Failed pad_right: {pad_right}"
        
    print("ALL RULES FIT ON A SINGLE ROW WITH PAD >= 16px!")

check_rules()
