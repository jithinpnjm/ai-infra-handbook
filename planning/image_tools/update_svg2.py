with open("generate_test_svg.py", "r") as f:
    content = f.read()

# Update Disk signals title y from 743 to 738
content = content.replace(
    '<text x="160" y="743" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#207448">Disk signals</text>',
    '<text x="160" y="738" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#207448">Disk signals</text>'
)

# Update Disk signals container height from 200 to 205
content = content.replace(
    '<rect x="60" y="685" width="1480" height="200" rx="16" fill="#ffffff" stroke="#207448" stroke-width="2"/>',
    '<rect x="60" y="685" width="1480" height="205" rx="16" fill="#ffffff" stroke="#207448" stroke-width="2"/>'
)

# Update Disk signals body y to 792
content = content.replace(
    '<text x="85" y="790" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">',
    '<text x="85" y="792" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">'
)

with open("generate_test_svg.py", "w") as f:
    f.write(content)

