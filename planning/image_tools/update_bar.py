with open("test_generated.svg", "r", encoding="utf-8") as f:
    s = f.read()

s = s.replace('font-size="28" font-weight="bold" fill="#ffffff">Read the error line first, then find the matching row',
              'font-size="30" font-weight="bold" fill="#ffffff">Read the error line first, then find the matching row')

with open("test_generated.svg", "w", encoding="utf-8") as f:
    f.write(s)

print("Updated bottom bar font size to 30px!")
