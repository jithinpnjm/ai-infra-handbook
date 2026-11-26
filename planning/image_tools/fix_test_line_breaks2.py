with open("test_line_breaks.py", "r") as f:
    code = f.read()

old_l8 = '''l8_lines = [
    "subclassing a built-in C type such as",
    "dict or list directly is risky because C",
    "methods ignore Python overrides; use",
    "collections.UserDict, UserList or UserString"
]'''

new_l8 = '''l8_lines = [
    "subclassing a built-in C type such",
    "as dict or list directly is risky",
    "because C methods ignore Python",
    "overrides; use collections.UserDict,",
    "UserList or UserString"
]'''

code = code.replace(old_l8, new_l8)

with open("test_line_breaks.py", "w") as f:
    f.write(code)

