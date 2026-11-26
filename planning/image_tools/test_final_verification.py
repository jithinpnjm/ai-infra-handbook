import re

svg_content = open("test_candidate_weak_host.svg").read()

# Update Result row and Bottom bar rects:
svg_content = re.sub(
    r'<rect x="40" y="963" width="1520" height="88"',
    '<rect x="40" y="958" width="1520" height="94"',
    svg_content
)

svg_content = re.sub(
    r'<rect x="40" y="1070" width="1520" height="90"',
    '<rect x="40" y="1066" width="1520" height="94"',
    svg_content
)

open("test_candidate_weak_host.svg", "w").write(svg_content)
print("Updated test_candidate_weak_host.svg")
