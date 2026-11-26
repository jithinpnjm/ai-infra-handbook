import re
import pathlib

svg_file = "kube_proxy_iptables.svg"
content = pathlib.Path(svg_file).read_text(encoding="utf-8")

# Fix 1: Implementation options text y
content = content.replace(
    '<text x="842" y="162" font-family="sans-serif" font-size="26" font-weight="bold" fill="#207448">Implementation options</text>\n\n    <!-- 3 Implementation chips/rows -->\n    <text x="806" y="206"',
    '<text x="842" y="172" font-family="sans-serif" font-size="26" font-weight="bold" fill="#207448">Implementation options</text>\n\n    <!-- 3 Implementation chips/rows -->\n    <text x="806" y="208"'
)
content = content.replace(
    '<text x="806" y="238"',
    '<text x="806" y="240"'
)
content = content.replace(
    '<text x="806" y="270"',
    '<text x="806" y="272"'
)

# Fix 2: A chain of rules title y
content = content.replace(
    '<text x="510" y="366" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#207448">A chain of rules for a Service with N pods</text>',
    '<text x="510" y="372" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#207448">A chain of rules for a Service with N pods</text>'
)

# Fix 3: Supporting pieces title y
content = content.replace(
    '<text x="800" y="782" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#207448">Supporting pieces</text>',
    '<text x="800" y="792" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#207448">Supporting pieces</text>'
)

pathlib.Path(svg_file).write_text(content, encoding="utf-8")
print("Applied 3 fixes.")
