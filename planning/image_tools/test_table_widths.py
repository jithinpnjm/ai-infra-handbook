# Test wrapping for Col 1 (w=550), Col 2 (w=350), Col 3 (w=620)
# monospace char width: 0.62 * 24 = 14.88 px
# sans-serif char width: 0.6 * 24 = 14.4 px

def check_wrap(text, max_w, is_mono=False):
    char_w = 14.88 if is_mono else 14.4
    limit_chars = int((max_w - 32) / char_w)
    print(f"Max chars for w={max_w} (mono={is_mono}): {limit_chars}")

check_wrap("", 550, True)
check_wrap("", 350, False)
check_wrap("", 620, False)
