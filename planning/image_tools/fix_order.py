# Regroup columns in DOM order: Col 1 (title + cards), Col 2 (title + cards), Col 3 (title + cards)
with open("build_models_svg.py", "r") as f:
    code = f.read()

# Let's inspect how generate_full_svg assembled it and make it group per column
