with open("output.svg") as f:
    c = f.read()

c = c.replace('y="74"', 'y="76"')
c = c.replace('y="118"', 'y="120"')

with open("output.svg", "w") as f:
    f.write(c)

print("Updated title y.")
