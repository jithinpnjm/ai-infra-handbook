import re

# Conservative widths: 0.60 * font_size for sans, 0.62 * font_size for mono
def get_width(text, fs=24, is_mono=False):
    factor = 0.62 if is_mono else 0.60
    return len(text) * factor * fs

# Label 2: Inheritor
l2 = "Inheritor(Super): pass, inherits methods unchanged"
print("L2 width:", get_width(l2))

# Label 3: Replacer
l3 = "Replacer(Super): overrides method(self) completely"
print("L3 width:", get_width(l3))

# Label 4: Extender
# Needs 2 lines in 1400px width
# Let's break L4:
l4 = "Extender(Super): overrides method(self) and calls back Super.method(self); example Manager.giveRaise(self, percent, bonus=.10) calls Person.giveRaise(self, percent + bonus)"
l4_part1 = "Extender(Super): overrides method(self) and calls back Super.method(self);"
l4_part2 = "example Manager.giveRaise(self, percent, bonus=.10) calls Person.giveRaise(self, percent + bonus)"
print("L4 part 1 width:", get_width(l4_part1), "len:", len(l4_part1))
print("L4 part 2 width:", get_width(l4_part2), "len:", len(l4_part2))
assert l4_part1 + " " + l4_part2 == l4

# Label 5: Provider (orange)
l5 = "Provider(Super): implements the abstract action(self) hook that Super.delegate(self) expects, the Template Method pattern"
l5_part1 = "Provider(Super): implements the abstract action(self) hook that"
l5_part2 = "Super.delegate(self) expects, the Template Method pattern"
print("L5 part 1 width:", get_width(l5_part1), "len:", len(l5_part1))
print("L5 part 2 width:", get_width(l5_part2), "len:", len(l5_part2))
assert l5_part1 + " " + l5_part2 == l5

# Label 6: Mixins (title, 30px)
l6 = "Mixins"
print("L6 width:", get_width(l6, 30))

# Label 7: Mixin body (card width = 740, avail = 692, max char width ~ 46)
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
    "UpperDict(UpperCaseMixin, collections.UserDict):",
    "pass, so it intercepts calls before UserDict",
    "on the MRO"
]
assert " ".join(l7_lines) == l7
print("L7 lines max width:", max(get_width(line) for line in l7_lines))

# Label 8: Warning body (card width = 700 inside Mixins, or separate, avail = 650)
l8 = "subclassing a built-in C type such as dict or list directly is risky because C methods ignore Python overrides; use collections.UserDict, UserList or UserString"
l8_lines = [
    "subclassing a built-in C type such as dict",
    "or list directly is risky because C methods",
    "ignore Python overrides; use",
    "collections.UserDict, UserList or UserString"
]
assert " ".join(l8_lines) == l8
print("L8 lines max width:", max(get_width(line) for line in l8_lines))

# Label 9: Composition and delegation (title, 30px)
l9 = "Composition and delegation"
print("L9 width:", get_width(l9, 30))

# Label 10: Comp body (card width = 740, avail = 692)
l10 = "inheritance models is-a (PizzaRobot is a Chef, a Chef is an Employee); composition models has-a (PizzaShop contains Server, PizzaRobot and Oven; Department gathers Person and Manager objects); delegation: a wrapper holds an embedded object and forwards requests with def __getattr__(self, attr): return getattr(self.person, attr); special operators such as __str__ or __add__ are looked up on the class directly, so they bypass instance-level __getattr__"

l10_lines = [
    "inheritance models is-a (PizzaRobot is a Chef,",
    "a Chef is an Employee); composition models",
    "has-a (PizzaShop contains Server, PizzaRobot",
    "and Oven; Department gathers Person and",
    "Manager objects); delegation: a wrapper holds",
    "an embedded object and forwards requests with",
    "def __getattr__(self, attr): return",
    "getattr(self.person, attr); special operators",
    "such as __str__ or __add__ are looked up on",
    "the class directly, so they bypass",
    "instance-level __getattr__"
]
assert " ".join(l10_lines) == l10
print("L10 lines max width:", max(get_width(line) for line in l10_lines))

# Label 11: Bottom strip (width = 1520, avail = 1472, max chars ~ 98)
l11 = "isinstance(x, Base) and issubclass respect inheritance; type(x) is T checks the exact type, rarely wanted; Liskov: a subclass accepts at least what the base accepts, returns no less than the base promises, and adds no surprising exceptions"

l11_lines = [
    "isinstance(x, Base) and issubclass respect inheritance; type(x) is T checks the exact type, rarely",
    "wanted; Liskov: a subclass accepts at least what the base accepts, returns no less than the base",
    "promises, and adds no surprising exceptions"
]
assert " ".join(l11_lines) == l11
print("L11 lines max width:", max(get_width(line) for line in l11_lines))

# Label 12: Bottom bar
l12 = "Customize a component without touching its source"
print("L12 width:", get_width(l12, 24))

print("ALL ASSERTIONS PASSED!")
