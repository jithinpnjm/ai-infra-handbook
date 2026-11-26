import math

def min_distance_box_to_diamond(box, poly_pts):
    # poly_pts is [(cx, top), (right, cy), (cx, bottom), (left, cy)]
    # or general 4 vertices.
    # We want the minimum distance from the 4 corners of the box to the 4 line segments of the diamond.
    # Box corners:
    bx0, by0, bx1, by1 = box['x'], box['y'], box['x'] + box['width'], box['y'] + box['height']
    corners = [(bx0, by0), (bx1, by0), (bx0, by1), (bx1, by1)]
    
    # Diamond segments:
    # Segment 1: top to right
    # Segment 2: right to bottom
    # Segment 3: bottom to left
    # Segment 4: left to top
    # For a diamond centered at (cx, cy) with half-width rx and half-height ry:
    # Equation of the 4 edges: |x - cx|/rx + |y - cy|/ry = 1
    # For any point (px, py) inside the diamond:
    # The normal distance to the diagonal edge is:
    # d = (1 - (|px - cx|/rx + |py - cy|/ry)) / sqrt(1/rx^2 + 1/ry^2)
    # Let's compute this for all 4 corners!
    cx = (poly_pts[0][0] + poly_pts[2][0]) / 2
    cy = (poly_pts[1][1] + poly_pts[3][1]) / 2
    rx = abs(poly_pts[1][0] - poly_pts[3][0]) / 2
    ry = abs(poly_pts[2][1] - poly_pts[0][1]) / 2
    
    scale = math.sqrt(1/(rx*rx) + 1/(ry*ry))
    min_d = 999999
    for px, py in corners:
        val = abs(px - cx)/rx + abs(py - cy)/ry
        d = (1.0 - val) / scale
        if d < min_d:
            min_d = d
    return min_d

print("Distance test ready.")
