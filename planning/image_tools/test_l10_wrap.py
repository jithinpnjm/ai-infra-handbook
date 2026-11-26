from test_l8_wrap import wrap

l10 = "inheritance models is-a (PizzaRobot is a Chef, a Chef is an Employee); composition models has-a (PizzaShop contains Server, PizzaRobot and Oven; Department gathers Person and Manager objects); delegation: a wrapper holds an embedded object and forwards requests with def __getattr__(self, attr): return getattr(self.person, attr); special operators such as __str__ or __add__ are looked up on the class directly, so they bypass instance-level __getattr__"

lines = wrap(l10, 42)
print(f"lines={len(lines)}, max len={max(len(l) for l in lines)}")
for l in lines:
    print(f"  ({len(l):2d}) {l}")

