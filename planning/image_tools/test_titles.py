# Let's inspect the exact labels and line breaks:

stages = {
    1: "shell fork and execve",
    2: "kernel checks the file and picks a format handler",
    3: "ELF loader maps LOAD segments, builds the stack",
    4: "PT_INTERP: kernel maps ld.so, execution starts in the dynamic linker",
    5: "ld.so loads DT_NEEDED libraries, relocates, runs constructors",
    6: "_start, __libc_start_main, main"
}

# What if:
# Can font size be 24px?
# "Node and step titles at least 30 px bold. Secondary text and monospace at least 24 px. NO text smaller than 24 px anywhere."
# Stage titles can be 24px or 30px! Wait, "Node and step titles at least 30 px bold."
# If node titles are >= 30px bold:
# At 30px bold: sans coefficient is 0.60 * 30 = 18 px/char!
# Then "__libc_start_main," (18 chars) = 18 * 18 = 324 px!

print("Testing text width calculations:")
