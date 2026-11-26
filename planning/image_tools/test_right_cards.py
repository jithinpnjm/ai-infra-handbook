def check_right_cards():
    w = 560
    
    # Card 1:
    h1 = 180
    lines1 = [
        "each decision is random and made",
        "per connection, with no view of",
        "how busy each pod is"
    ]
    for l in lines1:
        lw = len(l) * 24 * 0.6
        pad = (w - lw) / 2
        print(f"Card 1 line '{l}': w={lw:.1f}, pad={pad:.1f}")
        assert pad >= 16
        
    # Card 2 (Orange):
    h2 = 210
    lines2 = [
        "a slow pod still gets its",
        "random share, and a gRPC",
        "channel that picked it stays",
        "there for its whole life"
    ]
    for l in lines2:
        lw = len(l) * 24 * 0.6
        pad = (w - lw) / 2
        print(f"Card 2 line '{l}': w={lw:.1f}, pad={pad:.1f}")
        assert pad >= 16
    print("Right cards geometry: PASS!")

check_right_cards()
