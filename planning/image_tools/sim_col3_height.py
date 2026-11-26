# Let's test the vertical budget in Col 3:
# Total height available: 1200 - 80 (title) - 80 (bottom note) = 1040 px.

# If Col 3 has:
# Item 1: custom.metrics.k8s.io API (height 80)
# Gap 15
# Item 2: cmd_custom (height 150)
# Gap 30
# Item 3: HPA reads it and decides (height 80)
# Gap 15
# Item 4: cmd_hpa (height 90)
# Gap 15
# Item 5: Conditions box (height 200)
# Gap 30
# Item 6: external.metrics.k8s.io (height 80)
# Gap 15
# Item 7: cmd_ext (height 150)

h_items = [80, 15, 150, 30, 80, 15, 90, 15, 200, 30, 80, 15, 150]
print("Sum of heights in Col 3:", sum(h_items))
