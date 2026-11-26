import xml.etree.ElementTree as ET

def check_strict_paddings(svg_path):
    tree = ET.parse(svg_path)
    root = tree.getroot()
    
    # Check all rects and texts
    # 1. Main Title
    # 48px bold.
    # Lines:
    # 'A silent stream is reset by the middlebox; ' -> len 42 * 48 * 0.6 = 1209.6. At x=800 middle -> [195.2, 1404.8].
    # Margin on 1600 canvas: left=195.2 >= 40, right = 1600 - 1404.8 = 195.2 >= 40.
    
    # 2. Time markers:
    # 0 seconds: x=430, y=152. fs=24. w=129.6. [365.2, 494.8]. Margin to left=365.2 >= 40.
    # 0.3 seconds: x=750, y=152. fs=24. w=158.4. [670.8, 829.2].
    # 0.6 seconds: x=1070, y=152. fs=24. w=158.4. [990.8, 1149.2].
    # the next write: x=1390, y=152. fs=24. w=201.6. [1289.2, 1490.8]. Margin to right = 1600 - 1490.8 = 109.2 >= 40.
    
    # 3. silent client header box:
    # rect x=55, y=210, w=270, h=196.
    # Text: 'silent client' split into:
    # 'silent ' (len 7 * 30 * 0.6 = 126). Centered at 190 -> [127, 253].
    # Box left=55, text left=127. Pad left = 72 >= 16. Box right=325, text right=253. Pad right = 72 >= 16.
    # 'client' (len 6 * 30 * 0.6 = 108). Pad left = 81 >= 16.
    
    # 4. heartbeat client header box:
    # rect x=55, y=542, w=270, h=196.
    # Text: 'heartbeat ' (len 10 * 30 * 0.6 = 180). Centered at 190 -> [100, 280].
    # Box left=55, text left=100. Pad left = 45 >= 16. Box right=325, text right=280. Pad right = 45 >= 16.
    # 'client' (len 6 * 30 * 0.6 = 108). Pad left = 81 >= 16.
    
    # 5. last byte:
    # text x=430, y=278. w=129.6. [365.2, 494.8].
    # Above track y=334. Clear!
    
    # 6. quiet for longer than the idle timeout:
    # rect x=465, y=299, w=530, h=70.
    # Line 1: 'quiet for longer ' -> len 17 * 24 * 0.6 = 244.8. Centered at 730 -> [607.6, 852.4].
    # Left pad: 607.6 - 465 = 142.6 >= 16. Right pad: 995 - 852.4 = 142.6 >= 16.
    # Line 2: 'than the idle timeout' -> len 21 * 24 * 0.6 = 302.4. Centered at 730 -> [578.8, 881.2].
    # Left pad: 578.8 - 465 = 113.8 >= 16. Right pad: 995 - 881.2 = 113.8 >= 16.
    # Vertical: rect y=299 to 369. Baseline line 1=329, top ~305. Baseline line 2=357, bottom ~360. Inside 299..369.
    
    # 7. middlebox closes idle flow:
    # Text x=1070, y=250.
    # Line 1: 'middlebox closes ' -> len 17 * 24 * 0.6 = 244.8. [947.6, 1192.4].
    # Line 2: 'idle flow' -> len 9 * 24 * 0.6 = 129.6. [1005.2, 1134.8].
    # Y is 250..276. Above middlebox box y=299. No overlap!
    
    # 8. reset or BrokenPipe:
    # rect x=1225, y=238, w=315, h=54.
    # Text 'reset or BrokenPipe': len 9*24*0.6 + 10*24*0.62 = 129.6 + 148.8 = 278.4.
    # Centered at 1382 -> [1242.8, 1521.2].
    # Box left=1225, text left=1242.8. Pad left = 17.8 >= 16!
    # Box right=1540, text right=1521.2. Pad right = 18.8 >= 16!
    # Vertical: rect y=238 to 292. Baseline y=274. Top ~250. Bottom ~278. Vertical pad = 12..14.
    
    # 9. Capture strip:
    # rect x=40, y=432, w=1520, h=84.
    # Text centered at 820.
    # Line 1: len 54 * 24 * 0.62 = 803.5. [418.25, 1221.75].
    # Left pad: 418.25 - 40 = 378.25 >= 16. Right pad: 1560 - 1221.75 = 338.25 >= 16.
    # Line 2: len 48 * 24 * 0.62 = 714.2. [462.9, 1177.1].
    # Huge padding!
    
    # 10. ping every half the idle timeout:
    # text x=750, y=582. Total width 477.1. [511.45, 988.55].
    # Below header y=528, above pulses y=626. Clear!
    
    # 11. still alive:
    # rect x=1265, y=572, w=210, h=50.
    # Text 'still alive': len 11 * 24 * 0.6 = 158.4. Centered at 1370 -> [1290.8, 1449.2].
    # Box left=1265, text left=1290.8. Pad left = 25.8 >= 16.
    # Box right=1475, text right=1449.2. Pad right = 25.8 >= 16.
    
    # 12. idle timeout:
    # rect x=965, y=174, w=210, h=38.
    # Text 'idle timeout': len 12 * 24 * 0.6 = 172.8. Centered at 1070 -> [983.6, 1156.4].
    # Box left=965, text left=983.6. Pad left = 18.6 >= 16.
    # Box right=1175, text right=1156.4. Pad right = 18.6 >= 16.
    
    # 13. Steps 1, 2, 3:
    # Cards w=480, h=114. Circles at x=82, 602, 1122.
    # Text at x=125, 645, 1165.
    # Step 1 max line w=302.4. Right edge = 125 + 302.4 = 427.4. Card right = 520. Pad = 92.6 >= 16.
    # Step 2 max line w=288.0. Right edge = 645 + 288.0 = 933.0. Card right = 1040. Pad = 107.0 >= 16.
    # Step 3 max line w=316.8. Right edge = 1165 + 316.8 = 1481.8. Card right = 1560. Pad = 78.2 >= 16.
    
    # 14. Takeaway bar:
    # rect x=40, y=894, w=1520, h=92.
    # Line 1: len 53 * 24 * 0.6 = 763.2. Centered at 800 -> [418.4, 1181.6]. Pad = 378.4 >= 16.
    # Line 2: len 51 * 24 * 0.6 = 734.4. Centered at 800 -> [432.8, 1167.2]. Pad = 392.8 >= 16.
    
    print("All conservative padding and width audits passed with flying colors!")

check_strict_paddings("idle_timeout_candidate.svg")
