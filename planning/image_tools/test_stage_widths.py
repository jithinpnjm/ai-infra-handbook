# Test wrapping of each stage box label

def text_width(s, fs=24, is_mono=False):
    rate = 0.62 if is_mono else 0.60
    return len(s) * fs * rate

stage_labels = [
    (1, [
        "shell fork",
        "and execve"
    ]),
    (2, [
        "kernel checks the file",
        "and picks a",
        "format handler"
    ]),
    (3, [
        "ELF loader maps",
        "LOAD segments,",
        "builds the stack"
    ]),
    (4, [
        "PT_INTERP: kernel",
        "maps ld.so, execution",
        "starts in the",
        "dynamic linker"
    ]),
    (5, [
        "ld.so loads",
        "DT_NEEDED libraries,",
        "relocates, runs",
        "constructors"
    ]),
    (6, [
        "_start,",
        "__libc_start_main,",
        "main"
    ])
]

print("=== CHECKING STAGE BOX WRAPS ===")
for num, lines in stage_labels:
    max_w = max(text_width(line, 24) for line in lines)
    print(f"Stage {num}: max line width = {max_w:.1f} px, needed box width (with 32px pad) = {max_w + 32:.1f} px")
    for l in lines:
        print(f"   '{l}': {text_width(l, 24):.1f} px")
