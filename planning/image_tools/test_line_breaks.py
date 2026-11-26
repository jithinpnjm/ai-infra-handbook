def check_lines(name, lines, orig, start_x, end_x, is_mono=False):
    assert " ".join(lines) == orig, f"{name}: line rejoin mismatch!"
    factor = 0.62 if is_mono else 0.60
    max_w = 0
    for l in lines:
        w = len(l) * factor * 24
        if w > max_w:
            max_w = w
        right = start_x + w
        pad = end_x - right
        assert pad >= 16, f"{name}: line '{l}' pad {pad:.1f} < 16 (right={right:.1f}, end={end_x})"
    print(f"PASS {name}: max_w={max_w:.1f}, pad_min={end_x - (start_x + max_w):.1f}")

# Four patterns table: start_x = 140, end_x = 1540 (box 40..1560, right margin 20)
l2 = "Inheritor(Super): pass, inherits methods unchanged"
check_lines("L2", [l2], l2, 140, 1540, True)

l3 = "Replacer(Super): overrides method(self) completely"
check_lines("L3", [l3], l3, 140, 1540, True)

l4 = "Extender(Super): overrides method(self) and calls back Super.method(self); example Manager.giveRaise(self, percent, bonus=.10) calls Person.giveRaise(self, percent + bonus)"
l4_lines = [
    "Extender(Super): overrides method(self) and calls back Super.method(self);",
    "example Manager.giveRaise(self, percent, bonus=.10) calls",
    "Person.giveRaise(self, percent + bonus)"
]
check_lines("L4", l4_lines, l4, 140, 1540, True)

l5 = "Provider(Super): implements the abstract action(self) hook that Super.delegate(self) expects, the Template Method pattern"
l5_lines = [
    "Provider(Super): implements the abstract action(self) hook that",
    "Super.delegate(self) expects, the Template Method pattern"
]
check_lines("L5", l5_lines, l5, 140, 1540, True)

# Mixins card: box 40..780, start_x = 64, end_x = 764
l7 = "a small class named ...Mixin adding one independent capability through multiple inheritance: AttrDisplay, ListInstance (inspects self.__dict__), ListInherited (dir(self)), ListTree (climbs __class__ and __bases__); UpperCaseMixin uppercases string keys with super().__setitem__(_upper(key), item) and must be listed first: class UpperDict(UpperCaseMixin, collections.UserDict): pass, so it intercepts calls before UserDict on the MRO"
l7_lines = [
    "a small class named ...Mixin adding one",
    "independent capability through multiple",
    "inheritance: AttrDisplay, ListInstance",
    "(inspects self.__dict__), ListInherited",
    "(dir(self)), ListTree (climbs __class__ and",
    "__bases__); UpperCaseMixin uppercases string",
    "keys with super().__setitem__(_upper(key),",
    "item) and must be listed first: class",
    "UpperDict(UpperCaseMixin,",
    "collections.UserDict): pass, so it intercepts",
    "calls before UserDict on the MRO"
]
check_lines("L7", l7_lines, l7, 64, 764, True)

# Warning card: box 60..760, start_x = 135 (with 56px warning icon at x=68), end_x = 744
# Wait, if warning icon is on the left (x=72, w=48), start_x = 135, end_x = 744 (avail w = 609px).
# 609 / (0.62 * 24) = 40.9 chars.
l8 = "subclassing a built-in C type such as dict or list directly is risky because C methods ignore Python overrides; use collections.UserDict, UserList or UserString"
l8_lines = [
    "subclassing a built-in C type such",
    "as dict or list directly is risky",
    "because C methods ignore Python",
    "overrides; use collections.UserDict,",
    "UserList or UserString"
]
check_lines("L8", l8_lines, l8, 135, 744, True)

# Comp card: box 820..1560, start_x = 844, end_x = 1544
l10 = "inheritance models is-a (PizzaRobot is a Chef, a Chef is an Employee); composition models has-a (PizzaShop contains Server, PizzaRobot and Oven; Department gathers Person and Manager objects); delegation: a wrapper holds an embedded object and forwards requests with def __getattr__(self, attr): return getattr(self.person, attr); special operators such as __str__ or __add__ are looked up on the class directly, so they bypass instance-level __getattr__"
l10_lines = [
    "inheritance models is-a (PizzaRobot is a",
    "Chef, a Chef is an Employee); composition",
    "models has-a (PizzaShop contains Server,",
    "PizzaRobot and Oven; Department gathers",
    "Person and Manager objects); delegation: a",
    "wrapper holds an embedded object and",
    "forwards requests with def",
    "__getattr__(self, attr): return",
    "getattr(self.person, attr); special",
    "operators such as __str__ or __add__ are",
    "looked up on the class directly, so they",
    "bypass instance-level __getattr__"
]
check_lines("L10", l10_lines, l10, 844, 1544, True)

# Bottom strip: box 40..1560, start_x = 135 (with icon at x=60), end_x = 1540
l11 = "isinstance(x, Base) and issubclass respect inheritance; type(x) is T checks the exact type, rarely wanted; Liskov: a subclass accepts at least what the base accepts, returns no less than the base promises, and adds no surprising exceptions"
l11_lines = [
    "isinstance(x, Base) and issubclass respect inheritance; type(x) is T",
    "checks the exact type, rarely wanted; Liskov: a subclass accepts",
    "at least what the base accepts, returns no less than the base",
    "promises, and adds no surprising exceptions"
]
check_lines("L11", l11_lines, l11, 135, 1540, True)

# Bottom bar: box 40..1560, start_x = 135, end_x = 1540
l12 = "Customize a component without touching its source"
check_lines("L12", [l12], l12, 135, 1540, False)

print("\nALL LINES SATISFY CONSERVATIVE PADDING >= 16 PX!")
