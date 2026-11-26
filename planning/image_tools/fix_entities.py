with open("make_full_svg.py") as f:
    code = f.read()

# In SVG text generation, escape & to &amp;
replacement = """    def esc(s):
        return s.replace("&", "&amp;")
"""
code = replacement + code
# Replace direct n["title"] in text output with esc(...)
code = code.replace('{n["title"][0]}', '{esc(n["title"][0])}')
code = code.replace('{n["title"][1]}', '{esc(n["title"][1])}')
code = code.replace('{n["sub"][0]}', '{esc(n["sub"][0])}')
code = code.replace('{n["sub"][1]}', '{esc(n["sub"][1])}')
code = code.replace('{n["sub"][2]}', '{esc(n["sub"][2])}')

with open("make_full_svg.py", "w") as f:
    f.write(code)

print("Entities escaped in make_full_svg.py")
