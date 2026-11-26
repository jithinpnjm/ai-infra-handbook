from test_wrap_solver import wrap_text, w_sans, w_mono

e1 = 'UTF-8 default for new work, ASCII is a subset, Latin-1 maps bytes one to one onto code points 0 to 255 which carries arbitrary bytes through text APIs'
b1 = 'b"abc"[0] == 97 indexing bytes returns integers'
b2 = 'bytes.hex(), bytes.fromhex, int.from_bytes, struct.pack and unpack for binary protocols, base64, hashlib'

print("=== Encodings ===")
for l in wrap_text(e1, 42):
    w = w_sans(l)
    print(f"  '{l}' -> {w:.1f}px (pad: {(700-w)/2:.1f}px)")

print("=== Bytes fact 1 ===")
for l in wrap_text(b1, 42):
    w = w_sans(l)
    print(f"  '{l}' -> {w:.1f}px (pad: {(700-w)/2:.1f}px)")

print("=== Bytes fact 2 ===")
for l in wrap_text(b2, 42):
    w = w_sans(l)
    print(f"  '{l}' -> {w:.1f}px (pad: {(700-w)/2:.1f}px)")
