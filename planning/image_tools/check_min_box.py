# Let's test the width requirements of each stage box label:
labels = [
    (1, "shell fork and execve"),
    (2, "kernel checks the file and picks a format handler"),
    (3, "ELF loader maps LOAD segments, builds the stack"),
    (4, "PT_INTERP: kernel maps ld.so, execution starts in the dynamic linker"),
    (5, "ld.so loads DT_NEEDED libraries, relocates, runs constructors"),
    (6, "_start, __libc_start_main, main"),
]

for num, text in labels:
    words = text.split()
    print(f"\nStage {num}: '{text}'")
    for w in words:
        sans_w = len(w) * 0.6 * 24
        mono_w = len(w) * 0.62 * 24
        min_box_sans = sans_w + 32
        min_box_mono = mono_w + 32
        if min_box_sans > 220:
            print(f"  Word '{w}' requires min box width: {min_box_sans:.1f} (sans) or {min_box_mono:.1f} (mono)!")
