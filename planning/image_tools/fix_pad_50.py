import re

with open("output_perfect.svg") as f:
    text = f.read()

# Let's adjust height from 46 to 50, and ty from +32 to +34
# For example:
# y="180" height="46" -> y="178" height="50", ty="212"
# y="295" height="46" -> y="293" height="50", ty="327"
# y="382" height="46" -> y="380" height="50", ty="414"
# y="450" height="46" -> y="448" height="50", ty="482"
# y="504" height="46" -> y="502" height="50", ty="536"
# y="674" height="46" -> y="672" height="50", ty="706"
# y="754" height="46" -> y="752" height="50", ty="786"
# y="964" height="46" -> y="962" height="50", ty="996"

replacements = [
    ('y="180" width="190" height="46"', 'y="178" width="190" height="50"'),
    ('y="295" width="160" height="46"', 'y="293" width="160" height="50"'),
    ('y="382" width="270" height="46"', 'y="380" width="270" height="50"'),
    ('y="450" width="480" height="46"', 'y="448" width="480" height="50"'),
    ('y="504" width="320" height="46"', 'y="502" width="320" height="50"'),
    ('y="674" width="590" height="46"', 'y="672" width="590" height="50"'),
    ('y="754" width="720" height="46"', 'y="752" width="720" height="50"'),
    ('y="964" width="690" height="46"', 'y="962" width="690" height="50"'),
]

for old, new in replacements:
    assert old in text, f"Missing {old}"
    text = text.replace(old, new)

with open("output_perfect.svg", "w") as f:
    f.write(text)

print("Updated output_perfect.svg with height 50.")
