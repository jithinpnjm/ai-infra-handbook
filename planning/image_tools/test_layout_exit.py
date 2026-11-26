texts = [
    ("Success", "0"),
    ("General error. For grep, diff and cmp: no match or files differ, not an error", "1"),
    ("Misuse of a command, or a real error for grep and diff", "2"),
    ("Found but not executable", "126"),
    ("Command not found", "127"),
    ("Status out of range, or ssh connection failure", "255")
]

# What about 128 + N?
# Is 128 + N a segment on the line, and what is beneath it?
# In the prompt:
# "a wide segment labelled '128 + N' split into three small markers '130 Ctrl-C', '137 SIGKILL', '143 SIGTERM'"
# "Each marker has a short leader line down to its text box in a row beneath the line."
# "The 128 plus N segment in orange outline."

