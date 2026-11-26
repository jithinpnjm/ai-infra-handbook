"""Test grid configurations to find non-crossing layout."""

# Let's test a 3-column or 4-column layout
# In a 3-column layout:
# Row 0: EV (col 0) -> RQ (col 1) -> R (col 2)
# Row 1: F (col 0) <- D (col 1) <- G (col 2)  [Wait: G is below R; D is left of G; F is left of D; D --no--> goes DOWN to FIN!]
# Row 2: (empty col 0) FIN (col 1) -> V (col 2)
# Row 3: S (col 0) <- A (col 1) <- C (col 2)  [Wait: V goes DOWN to C; C goes left to A; A goes left to S]
# Row 4: U (col 0) -> RQR (col 1) -> END (col 2) [Wait: S goes DOWN to U; U goes right to RQR; RQR goes right to END; RQR loops back UP to RQ!]

# Look at this:
# Col 0      Col 1      Col 2
# -----------------------------
# EV   --->  RQ   --->  R
#             ^         |
#             |         v
# F    <---   D   <---  G
#             |
#             v
#            FIN  --->  V
#                       |
#                       v
# S    <---   A   <---  C
# |
# v
# U    --->  RQR  --->  END
#             |
#             +--- (loopback up to RQ)

print("Look at this layout!")
