with open("generate_svg.py") as f:
    s = f.read()

s = s.replace('font-size="28" font-weight="bold" fill="#207448">single-node training, all GPUs:</text>',
              'font-size="30" font-weight="bold" fill="#207448">single-node training, all GPUs:</text>')

s = s.replace('font-size="26" font-weight="bold" fill="#207448">multi-node, one process</text>',
              'font-size="30" font-weight="bold" fill="#207448">multi-node, one process</text>')
s = s.replace('font-size="26" font-weight="bold" fill="#207448">per GPU (PyTorch):</text>',
              'font-size="30" font-weight="bold" fill="#207448">per GPU (PyTorch):</text>')

s = s.replace('font-size="26" font-weight="bold" fill="#207448">several independent tasks</text>',
              'font-size="30" font-weight="bold" fill="#207448">several independent tasks</text>')
s = s.replace('font-size="26" font-weight="bold" fill="#207448">in one allocation:</text>',
              'font-size="30" font-weight="bold" fill="#207448">in one allocation:</text>')

s = s.replace('font-size="28" font-weight="bold" fill="#207448">interactive:</text>',
              'font-size="30" font-weight="bold" fill="#207448">interactive:</text>')

with open("generate_svg.py", "w") as f:
    f.write(s)

print("Updated titles to 30px")
