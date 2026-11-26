with open("output.svg") as f:
    c = f.read()

# Replace <text class="title" x="800" y="74"> with explicit text-anchor="middle"
c = c.replace('<text class="title" x="800"', '<text class="title" text-anchor="middle" x="800"')
c = c.replace('<text class="takeaway-text" x="800"', '<text class="takeaway-text" text-anchor="middle" x="800"')
c = c.replace('<text class="circle-text" x="92"', '<text class="circle-text" text-anchor="middle" dominant-baseline="central" x="92"')
c = c.replace('<text class="badge-text" x="113"', '<text class="badge-text" text-anchor="middle" dominant-baseline="central" x="113"')

with open("output.svg", "w") as f:
    f.write(c)

print("Updated output.svg with explicit text-anchor attributes.")
