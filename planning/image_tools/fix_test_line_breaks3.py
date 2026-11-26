with open("test_line_breaks.py", "r") as f:
    code = f.read()

old_l10 = '''l10_lines = [
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
]'''

new_l10 = '''l10_lines = [
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
]'''

code = code.replace(old_l10, new_l10)

with open("test_line_breaks.py", "w") as f:
    f.write(code)

