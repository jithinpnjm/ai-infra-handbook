#!/usr/bin/env python3

def check_line(text, font_size, max_w):
    w = len(text) * 0.6 * font_size
    print(f"[{font_size}px] '{text}' ({len(text)} chars) -> est width: {w:.1f}px / max {max_w}px (pad: {max_w - w:.1f}px)")
    return w <= max_w

print("\n--- Bars ---")
# Box width 690.
check_line("normal requests alone:", 26, 600)
check_line("50.6 / 0.369 = 137 fit", 28, 600)

check_line("long requests that fill the GPU:", 26, 600)
check_line("50.6 / 4.42 = 11", 28, 600)

check_line("left for others when 11 long run:", 26, 600)
check_line("50.6 - 48.7 = 1.94 GB = 5 requests", 26, 600)

print("\n--- Right Side ---")
# Box width 690
check_line("cap at 25 percent of KV:", 26, 600)
check_line("12.65 / 4.42 = 2 long requests", 28, 600)

check_line("cap is per replica but the router sends all of", 25, 600)
check_line("the tenant's long requests to one replica:", 25, 600)
check_line("the cap must hold across the pool", 25, 600)

check_line("shared pool, long-context pool,", 26, 600)
check_line("dedicated endpoint", 26, 600)

print("\n--- Bottom Headline ---")
# Banner width 1500. Usable 1400.
check_line("eleven long requests take capacity from 137 down to 5 for everyone else:", 28, 1400)
check_line("the case for charging by cost (tokens x context), not request count", 28, 1400)

