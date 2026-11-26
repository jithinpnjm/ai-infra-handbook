with open("test_line_breaks.py", "r") as f:
    code = f.read()

old_l7 = '''    "item) and must be listed first: class",
    "UpperDict(UpperCaseMixin, collections.UserDict):",
    "pass, so it intercepts calls before UserDict",
    "on the MRO"'''

new_l7 = '''    "item) and must be listed first: class",
    "UpperDict(UpperCaseMixin,",
    "collections.UserDict): pass, so it intercepts",
    "calls before UserDict on the MRO"'''

code = code.replace(old_l7, new_l7)

with open("test_line_breaks.py", "w") as f:
    f.write(code)

