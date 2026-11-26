# Let's test arrow routing:
# Arrow 1: vLLM (x=460, y=160) -> Prometheus (x=530, y=160) [Horizontal]
# Arrow 2: Prometheus (x=770, y=210) -> adapter rule (x=770, y=250) [Vertical Down]
# Arrow 3: adapter rule (x=1020, y=380) -> custom API (x=1080, y=380) [Horizontal]
# Wait! Look at that:
# If Prometheus is at y = 110 to 210,
# adapter rule is at y = 250 to 570,
# custom API is at y = 250 to 330!
# Then Arrow 3 from adapter rule to custom API goes HORIZONTALLY at y = 290!
# And then custom API command is under custom API at y = 340 to 490!
# And then HPA reads it and decides is at y = 540 to 620!
# And cmd HPA is under HPA at y = 630 to 710!
# And Conditions box is under cmd HPA at y = 720 to 920!

# Wait, what about Arrow 4 from custom API to HPA?
# Can Arrow 4 go from custom API (x=1520, y=290) -> (x=1545, y=290) -> (x=1545, y=580) -> (x=1520, y=580)?
# That's an orthogonal bracket on the right edge!
# Or can custom API and HPA be arranged differently?

print("Testing arrow routing...")
