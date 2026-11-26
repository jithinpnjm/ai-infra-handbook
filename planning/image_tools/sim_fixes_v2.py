def w_sans(text, size=24):
    return len(text) * size * 0.6

lines = [
    ("Item 1", "restrict a port with the DOCKER-USER chain"),
    ("Item 2a", "bind the port to a specific address (for example"),
    ("Item 2b", "127.0.0.1:8080:80)"),
    ("Item 3a", "if a published port must stay private on a shared host,"),
    ("Item 3b", "restrict it in DOCKER-USER before you publish it")
]

avail = 846
for name, text in lines:
    w = w_sans(text, 24)
    print(f"{name:8s}: {w:5.1f}px / {avail}px (pad={avail-w:5.1f}px) : '{text}'")
