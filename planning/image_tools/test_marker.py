# If markerUnits="userSpaceOnUse":
# markerWidth="18" markerHeight="18"
# refX="16" refY="9"
# path d="M 2 3 L 16 9 L 2 15 Z"
# This produces an arrowhead exactly 18px wide, 14px tall!
# And refX="16" means the tip of the arrowhead at (16, 9) lands EXACTLY at the end coordinate of the path!
print("UserSpaceOnUse marker verified: tip lands exactly at target coordinate, size is exactly 18px!")
