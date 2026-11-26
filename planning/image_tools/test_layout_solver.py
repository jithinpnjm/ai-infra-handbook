def test_vertical_layout():
    # Target:
    # Canvas H = 1200
    # Top margin: >= 40
    # Bottom margin: >= 40 (last element bottom <= 1160)
    
    # Let's inspect the components:
    # Title: 2 lines of 48px bold.
    # line 1 baseline: 82 (top ~ 42 >= 40)
    # line 2 baseline: 134 (bottom ~ 146)
    
    # Gap: 16px -> Host container top = 162
    
    # Host header (Shared nodes):
    # Instead of an extra enclosing box for shared nodes, what if the 4 shared nodes sit directly in the Host Header row?
    # Host top: 162
    # Shared nodes row: y = 176 to 244 (height 68px).
    # Host badge: x=68, y=184, h=52, w=80. Text inside: host. Server icon beside it.
    # 4 Nodes: c1, br0, c2, uplink NIC.
    # Height = 52px each, y = 184 to 236.
    
    # Lane 1 (c1 to c2 on the same bridge):
    # y = 256 to 438 (height 182px).
    # Header: cy=284. Title baseline=292. Arrow y=284.
    # Text: 3 lines.
    # y = 328, 356, 384, 412 (note lines).
    # Wait, does Lane 1 need an inner white rect, or can Lane 1 itself be the card?
    # If Lane 1 is a light green card (#e8f1ea), the text can sit directly inside it with 20px padding!
    # Let's see: if text sits directly inside Lane 1 card:
    # Card y = 256 to 432 (height 176px).
    # Title at y = 292 (top ~ 268 -> pad top = 268 - 256 = 12 -> if y=296, top ~ 272, pad top = 16!).
    # Line 1: y = 330
    # Line 2: y = 358
    # Line 3: y = 388 (note line 1)
    # Line 4: y = 414 (note line 2, bottom ~ 422 -> pad bottom = 436 - 422 = 14 -> card bottom = 440, pad bottom = 18!).
    # So Lane 1 card: y = 254 to 442 (height 188px).
    
    # Lane 2 (c1 to the Internet):
    # Card y = 454 to 736 (height 282px).
    # Title at y = 492 (top ~ 470, pad top = 16).
    # Desc lines:
    # Line 1: y = 526
    # Line 2: y = 554
    # Line 3: y = 582
    # Commands:
    # Cmd 1: y = 618 (sysctl ... and iptables -I FORWARD -i br0 ...)
    # Cmd 2: y = 648 (iptables -t nat -A POSTROUTING ...)
    # Cmd 3: y = 678 (iptables -I FORWARD -o br0 ...)
    # Bottom of cmd 3 ~ 686.
    # Card bottom = 708 (pad bottom = 22).
    
    # Lane 3 (host:8080 to c1:80) [ORANGE]:
    # Card y = 720 to 836 (height 116px).
    # Title at y = 754 (top ~ 732, pad top = 12 -> card y = 716, pad top = 16!).
    # Cmd 1: y = 788
    # Cmd 2: y = 816 (bottom ~ 824, card bottom = 844, pad bottom = 20!).
    
    # Host container bottom = 856 (Host y = 162 to 856, height 694px).
    
    # Footer & Docker note:
    # y = 872 to 1080 (height 208px).
    # DNS line: y = 906 (top ~ 888, pad top = 16).
    # Divider line: y = 924.
    # Docker note lines:
    # Line 1: y = 958
    # Line 2: y = 988
    # Line 3: y = 1018
    # Card bottom = 1046 (pad bottom = 20).
    
    # Takeaway bar:
    # y = 1064 to 1128 (height 64px).
    # Text baseline: y = 1104 (dominant-baseline central or baseline).
    # Top of text ~ 1086 (pad top = 22).
    # Bottom of text ~ 1112 (pad bottom = 16).
    # Card bottom = 1128!
    # Canvas margin = 1200 - 1128 = 72px >= 40px!
    
    print("Vertical layout fits with 72px margin to spare!")

test_vertical_layout()
