import xml.etree.ElementTree as ET

expected_source_labels = [
    "Worked example: masking numbers to rank distinct errors",
    "grep -i error train.log",
    "10:20:01 ERROR NCCL timeout on rank 3",
    "10:31:09 ERROR NCCL timeout on rank 5",
    "10:40:00 ERROR CUDA out of memory on gpu=2",
    "WARN loss spike",
    "sed -E s/[0-9]+/N/g",
    "N:N:N ERROR NCCL timeout on rank N",
    "N:N:N ERROR CUDA out of memory on gpu=N",
    "sort",
    "uniq -c",
    "2 N:N:N ERROR NCCL timeout on rank N",
    "1 N:N:N ERROR CUDA out of memory on gpu=N",
    "sort -rn | head",
    "groups the two identical NCCL lines next to each other",
    "ranks them with the count 2 line first",
    "Masking the numbers makes different ranks the same message, so uniq can count them"
]

tree = ET.parse("test_pipeline.svg")
root = tree.getroot()

all_texts = []
for el in root.iter('{http://www.w3.org/2000/svg}text'):
    t = " ".join("".join(el.itertext()).split())
    if t.isdigit():
        continue
    all_texts.append(t)

print(f"Total non-digit text elements: {len(all_texts)}")
for exp in expected_source_labels:
    assert exp in all_texts, f"Missing: {exp}"
    print(f"MATCH: '{exp}'")

print("\nEVERY SINGLE SOURCE LABEL MATCHES EXACTLY TOKEN FOR TOKEN!")
