with open("build_full_table.py", "r") as f:
    code = f.read()

# Fix Row 3 tspans and height:
# r3_tspans:
old_r3 = """    r3_tspans = [
        (116, 38, 30, True, "3 Host networking:"),
        (116, 64, 24, False, "hostNetwork true with dnsPolicy"),
        (116, 90, 24, False, "ClusterFirstWithHostNet; simplest"),
        (116, 116, 24, False, "high-performance option; costs port"),
        (116, 142, 24, False, "conflicts, less isolation, no per-pod"),
        (116, 168, 24, False, "NetworkPolicy")
    ]"""

new_r3 = """    r3_tspans = [
        (116, 40, 30, True, "3 Host networking:"),
        (116, 66, 24, False, "hostNetwork true with dnsPolicy"),
        (116, 92, 24, False, "ClusterFirstWithHostNet; simplest"),
        (116, 118, 24, False, "high-performance option; costs port"),
        (116, 144, 24, False, "conflicts, less isolation, no per-pod"),
        (116, 170, 24, False, "NetworkPolicy")
    ]"""

code = code.replace(old_r3, new_r3)
code = code.replace("(3, 184, r3_tspans, False),", "(3, 188, r3_tspans, False),")

with open("build_full_table.py", "w") as f:
    f.write(code)

