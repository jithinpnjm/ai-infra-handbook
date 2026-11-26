import re

with open("test_generated.svg") as f:
    s = f.read()

# Let's inspect each box that failed:

# 1. node-prometheus:
# was: rect x="40" y="290" width="450" height="135"
# text: y=388, dy=34 -> y=422. 290+135 = 425. bottom = 3px.
# Fix: make height 155, so bottom = 23px!
# Arrow from vllm ends at 285. Arrow to rule starts at 360.
s = s.replace('rect x="40" y="290" width="450" height="135"', 'rect x="40" y="285" width="450" height="155"')
s = s.replace('line x1="265" y1="260" x2="265" y2="290"', 'line x1="265" y1="260" x2="265" y2="285"')
s = s.replace('line x1="490" y1="357" x2="520" y2="357"', 'line x1="490" y1="365" x2="520" y2="365"')

# 2. cmd-custom-api:
# was: y=210, h=160. text y=246, dy=34. top was 246-24-210 = 12px.
# Fix: text y=250. height 170.
s = s.replace('rect x="1060" y="235" width="480" height="155"', 'rect x="1060" y="235" width="480" height="165"')
s = s.replace('text x="1080" y="270"', 'text x="1080" y="275"')

# 3. node-hpa:
# was: rect y=400, h=120. text y=495, dy=34 -> y=529. 400+120=520 -> bottom = -9px.
# Fix: rect y=415, h=135. text y=485, dy=34 -> y=519. bottom = 550 - 519 = 31px.
s = s.replace('rect x="1060" y="400" width="480" height="120"', 'rect x="1060" y="415" width="480" height="130"')
s = s.replace('g transform="translate(1085, 412)"', 'g transform="translate(1085, 422)"')
s = s.replace('text x="1085" y="495"', 'text x="1085" y="488"')
s = s.replace('L 1565 440 L 1540 440', 'L 1565 465 L 1540 465')

# 4. cmd-hpa:
# was: rect y=530, h=90. text y=568. top was 568-24-530 = 14px.
# Fix: rect y=560, h=95. text y=595, dy=33 -> y=628. bottom = 655-628=27. top = 595-24-560=11? Wait, y=598-24=574 -> top 14.
# If rect y=560, h=95, text y=600 -> top = 600-24-560 = 16px! bottom = 655-(600+33) = 22px!
s = s.replace('rect x="1060" y="530" width="480" height="90"', 'rect x="1060" y="560" width="480" height="95"')
s = s.replace('text x="1080" y="568"', 'text x="1080" y="600"')

# 5. box-conditions:
# was: rect y=630, h=195. text y=665, 725, 785 (+30+30=845). 630+195=825. bottom = -20px.
# Fix: rect y=670, h=230 (ends at 900).
# text 1: y=705, dy=26, 26 (ends 757)
# text 2: y=765, dy=26 (ends 791)
# text 3: y=815, dy=26, 26 (ends 867). bottom = 900 - 867 = 33px. top = 705-24-670 = 11? text y=712 -> top 18px!
# Wait! Let's check where external api is:
# external API was at y=840. If box-conditions ends at 890, external API can be at y=910!
# Wait, let's write a dedicated python script to balance all y coordinates properly!
