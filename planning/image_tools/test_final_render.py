import re, os, subprocess
import xml.etree.ElementTree as ET

code = open("generate_perfect_timeline.py").read()

# Update Step 5 loop path to be compact and non-overlapping:
code = code.replace(
    'path d="M {s_x+24} {y} H {s_x+58} V {y+24} H {s_x}"',
    'path d="M {s_x+24} {y} H {s_x+54} V {y+14} H {s_x}"'
)

# Optimize step_y for maximum breathing room and >= 50px delta between same sender:
old_step_y = """    step_y = [
        264, # 1: U -> A
        306, # 2: A -> S
        350, # 3: S -> A (2 lines)
        392, # 4: A -> K
        438, # 5: K -> K (loop, 2 lines)
        487, # 6: K -> D (orange!)
        536, # 7: K -> V
        585, # 8: K -> R
        627, # 9: R -> C
        669, # 10: K -> R
        718, # 11: K -> R
        760, # 12: R -> X
        804, # 13: K -> A (2 lines)
        852, # 14: Note over K,X (note box)
        900, # 15: U -> A
        942, # 16: A -> K
        984, # 17: K -> X
        1033,# 18: K -> R
        1082,# 19: K -> V
        1131 # 20: K -> A (step 19)
    ]"""

new_step_y = """    step_y = [
        264, # 1: U -> A
        306, # 2: A -> S
        350, # 3: S -> A (2 lines)
        392, # 4: A -> K
        438, # 5: K -> K (loop, 2 lines)
        488, # 6: K -> D (orange!) [dy=50]
        538, # 7: K -> V [dy=50]
        588, # 8: K -> R [dy=50]
        630, # 9: R -> C
        672, # 10: K -> R
        722, # 11: K -> R [dy=50]
        764, # 12: R -> X
        808, # 13: K -> A (2 lines)
        856, # 14: Note over K,X (note box)
        904, # 15: U -> A
        946, # 16: A -> K
        986, # 17: K -> X
        1036,# 18: K -> R [dy=50]
        1086,# 19: K -> V [dy=50]
        1136 # 20: K -> A (step 19) [dy=50]
    ]"""

code = code.replace(old_step_y, new_step_y)

open("generate_perfect_timeline.py", "w").write(code)

subprocess.run(["python3", "generate_perfect_timeline.py"], check=True)
subprocess.run(["python3", "audit_timeline.py"], check=True)
subprocess.run(["python3", "test_message_padding.py"], check=True)
subprocess.run(["python3", "render_and_verify.py"], check=True)
print("ALL VERIFICATIONS COMPLETED SUCCESSFULLY!")
