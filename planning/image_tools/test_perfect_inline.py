import xml.etree.ElementTree as ET
import re

text = '<text x="530" y="800" font-family="sans-serif" font-size="24" fill="#303a36"><tspan x="530" dy="0">scheduler, a </tspan><tspan x="530" dy="36">higher-priority pod </tspan><tspan x="530" dy="36">needs a place</tspan></text>'
el = ET.fromstring(text)

raw_join = "".join(el.itertext()).strip()
regex_sub = re.sub(r'\s+', ' ', "".join(el.itertext()).strip())
split_join = " ".join("".join(el.itertext()).split())

expected = "scheduler, a higher-priority pod needs a place"
print("raw_join:  ", repr(raw_join))
print("regex_sub: ", repr(regex_sub))
print("split_join:", repr(split_join))
assert raw_join == expected
assert regex_sub == expected
assert split_join == expected
print("ALL THREE MATCH PERFECTLY!")
