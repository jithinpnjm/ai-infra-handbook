# Check vertical positions:
panels_y = 145
panels_h = 670
panels_bottom = panels_y + panels_h  # 815

footer_y = 835
footer_h = 110
footer_bottom = footer_y + footer_h  # 945

result_y = 965
result_h = 90
result_bottom = result_y + result_h  # 1055

bottom_y = 1075
bottom_h = 85
bottom_bottom = bottom_y + bottom_h  # 1160

canvas_h = 1200
bottom_margin = canvas_h - bottom_bottom  # 40

print(f"Panels: {panels_y}..{panels_bottom} (h={panels_h})")
print(f"Gap 1: {footer_y - panels_bottom} px")
print(f"Footer: {footer_y}..{footer_bottom} (h={footer_h})")
print(f"Gap 2: {result_y - footer_bottom} px")
print(f"Result: {result_y}..{result_bottom} (h={result_h})")
print(f"Gap 3: {bottom_y - result_bottom} px")
print(f"Bottom bar: {bottom_y}..{bottom_bottom} (h={bottom_h})")
print(f"Bottom margin: {bottom_margin} px")
assert bottom_margin == 40
print("Vertical budget: PERFECT!")
