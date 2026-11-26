with open("test_generated.svg", "r", encoding="utf-8") as f:
    s = f.read()

s = s.replace('height="1" rx="10"', 'height="832" rx="10"')

with open("test_generated.svg", "w", encoding="utf-8") as f:
    f.write(s)

print("Updated height in test_generated.svg!")
