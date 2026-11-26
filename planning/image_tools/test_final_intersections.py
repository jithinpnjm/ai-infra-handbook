import xml.etree.ElementTree as ET

def ccw(A, B, C):
    return (C[1]-A[1]) * (B[0]-A[0]) > (B[1]-A[1]) * (C[0]-A[0])

def intersect(p1, p2, p3, p4):
    if p1 == p3 or p1 == p4 or p2 == p3 or p2 == p4:
        return False
    return ccw(p1, p3, p4) != ccw(p2, p3, p4) and ccw(p1, p2, p3) != ccw(p1, p2, p4)

tree = ET.parse('slurm_daemons.svg')
arrows = tree.find('.//{http://www.w3.org/2000/svg}g[@id="arrows"]')
paths = arrows.findall('{http://www.w3.org/2000/svg}path')

parsed_paths = []
for p in paths:
    d = p.get('d')
    tokens = d.replace('M', ' ').replace('L', ' ').split()
    pts = [(float(tokens[i]), float(tokens[i+1])) for i in range(0, len(tokens), 2)]
    parsed_paths.append(pts)

intersections = 0
for i in range(len(parsed_paths)):
    for j in range(i + 1, len(parsed_paths)):
        p1 = parsed_paths[i]
        p2 = parsed_paths[j]
        for s1 in range(len(p1) - 1):
            a, b = p1[s1], p1[s1+1]
            for s2 in range(len(p2) - 1):
                c, d = p2[s2], p2[s2+1]
                if intersect(a, b, c, d):
                    print(f"Intersection between Arrow {i+1} seg {s1} ({a}->{b}) and Arrow {j+1} seg {s2} ({c}->{d})")
                    intersections += 1

if intersections == 0:
    print("SUCCESS: 0 ARROW INTERSECTIONS!")
