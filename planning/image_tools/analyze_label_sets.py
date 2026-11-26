# Let's analyze candidate label sets:

# Candidate Set 1 (Clause-based splitting):
set1 = [
    "How rsync decides what to send",
    "source and destination compared by quick check: size and modification time",
    "Match",
    "skip",
    "different",
    "send only the changed blocks",
    "-c checksum (slower, thorough)",
    "--ignore-existing",
    "-b backup",
    "-u skip files newer at destination",
    "-P partial plus progress",
    "a second rsync -av should list nothing, but the quick check trusts two numbers, so use -c for data you cannot rebuild",
    "rsync -nva dir host:dest_dir"
]

# Candidate Set 2 (With "Dry run" as label):
set2 = [
    "How rsync decides what to send",
    "source and destination compared by quick check: size and modification time",
    "Match",
    "skip",
    "different",
    "send only the changed blocks",
    "-c checksum (slower, thorough)",
    "--ignore-existing",
    "-b backup",
    "-u skip files newer at destination",
    "-P partial plus progress",
    "a second rsync -av should list nothing, but the quick check trusts two numbers, so use -c for data you cannot rebuild",
    "Dry run: rsync -nva dir host:dest_dir"
]

# Candidate Set 3 (Flow split: source and destination -> quick check):
set3 = [
    "How rsync decides what to send",
    "source and destination",
    "quick check: size and modification time",
    "Match",
    "skip",
    "different",
    "send only the changed blocks",
    "-c checksum (slower, thorough)",
    "--ignore-existing",
    "-b backup",
    "-u skip files newer at destination",
    "-P partial plus progress",
    "a second rsync -av should list nothing, but the quick check trusts two numbers, so use -c for data you cannot rebuild",
    "rsync -nva dir host:dest_dir"
]

print("Set 1 len:", len(set1))
print("Set 2 len:", len(set2))
print("Set 3 len:", len(set3))
