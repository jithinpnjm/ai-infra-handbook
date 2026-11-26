# Let's write a python layout that defines boxes, arrows, labels, and checks bounding boxes!

class Rect:
    def __init__(self, x, y, w, h, name=""):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.name = name
    
    def overlaps(self, other, pad=10):
        # returns True if overlaps within pad
        return not (self.x + self.w + pad <= other.x or
                    other.x + other.w + pad <= self.x or
                    self.y + self.h + pad <= other.y or
                    other.y + other.h + pad <= self.y)

print("Rect helper defined.")
