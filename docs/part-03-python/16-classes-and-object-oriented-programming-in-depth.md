---
id: "c03-16"
title: "3.16 Classes and object-oriented programming in depth"
sidebar_label: "3.16 Classes and object-oriented programming in depth"
sidebar_position: 16
description: "A realistic class example, class coding details, operator overloading, designing with classes and class odds and ends."
status: "drafted"
tier: "2"
level: "I"
lab_venue: "Mac"
---

# 3.16 Classes and object-oriented programming in depth

Chapter 3.1 met classes and then walked on, because it had a lot of ground to cover. This chapter comes back to them and stays a while. The material here is what you reach for when you read the Python behind schedulers, operators, exporters and training launchers, and it is what you need when you write that Python yourself.

## Building a realistic example: a Person class

Before any language rules, we build something real. The example in this section is a small set of classes that record and process information about people. You will see that instances and classes can play the same roles that records and programs play in older code. The one difference that matters is the customization inheritance makes possible.

We will write two classes:

- `Person`, a class that creates and processes information about people.
- `Manager`, a customization of `Person` that changes some inherited behavior.

Along the way we make instances of both classes and test them. At the end we store those instances in a simple object-oriented database, so they outlive the program. You can use that code as a template for a larger personal database written entirely in Python.

The example is also meant to teach. Many readers understand class syntax in the abstract and then freeze when they must write a class from scratch. So we build the classes one small step at a time, and each step is small enough to check before the next one starts.

### Step 1: Making instances

Our first task is to start the main class, `Person`. Open a new file in your text editor and keep it open, because every step in this section adds to that same file.

Python programmers usually start module names with a lowercase letter and class names with an uppercase letter. The language does not require this, but nearly everyone follows it, so deviating can confuse later readers. We will follow the convention here. We will name the module file `person.py` and the class `Person`.

File `person_1.py` (start)

```text
class Person: # Start a class
```
We will change this file as we go, so the versions need labels. Each example number appears in the caption, and the same number appears in the file name. The file stays the same across steps, but the book shows each revision separately.

A module can hold any number of functions and classes, and nothing stops you from mixing them. The name `person.py` may stop making sense if we add unrelated code later. For now we will assume everything in it relates to `Person`. Modules work best with a single, cohesive purpose, and a name that still describes the contents six months later.

#### Coding constructors

The first real job for `Person` is to record basic facts about each person. In Python these facts are instance attributes, which simply means values stored on one particular object. They are usually created by assigning values to `self` inside methods.

The normal way to give an instance its first values is the `__init__` constructor method. A constructor is the code Python runs when a new object is built, and it runs automatically each time an instance is created.

File `person_2.py` (set attributes in the constructor)

```python
class Person:
    def __init__(self, name, job, pay): # Constructor takes three arguments
        self.name = name # Fill out fields when created
        self.job = job # self is the new instance object
        self.pay = pay
```
This is a very common pattern. We pass data to the constructor, then assign it to `self` so the instance keeps it. In object terms, `self` is the new instance, and `name`, `job`, and `pay` become state information. Other techniques, such as closures, can also save details. Instance attributes make the saving explicit, and you can read the saved values later by name.

The argument names appear twice, and that is not a mistake. It is worth pausing here, because this is the first place where two different kinds of name meet. The `job` argument is a local variable inside `__init__`. The `self.job` value is an attribute on the instance. They are two different variables that happen to share a name. Assigning `self.job = job` saves the local value on the instance for later use. In Python, what a name refers to depends on where it is assigned.

There is nothing special about `__init__` apart from its automatic call and its first argument named `self`. It is a normal function, so it supports everything we know about functions. We can give its arguments defaults, the same way we would for any other function.

Let us make `job` optional. It will default to `None`, which means the person is not currently employed. If `job` defaults to `None`, `pay` should default to `0` for consistency. Python requires this: once one argument has a default, every argument after it must have one too.

File `person_3.py` (defaults for optional arguments)

```python
class Person:
    def __init__(self, name, job=None, pay=0): # Normal function args
        self.name = name
        self.job = job
        self.pay = pay
```
Now a name is required when we make a `Person`, but `job` and `pay` are optional. If we omit them, they default to `None` and `0`. The `self` argument is filled in by Python. Assigning to attributes of `self` attaches those values to the new instance, so every object carries its own name, job and pay.

#### Testing as you go

This class does very little yet. It fills out the fields of a new record, but it is a working class, and that is the point. Python programming is mostly incremental. You write a little code, test it, and write more. Python's interactive session and fast turnaround make this natural, so there is no reason to write a hundred lines before the first check.

Testing by hand at the prompt has limits, though. Retyping test cases each session gets tedious, and small slips creep in. Most programmers use the prompt for quick one-off checks. For real tests they put code at the bottom of the file that holds the class, so the tests travel with the code.

File `person_4.py` (self-test at the bottom)

```python
class Person:
    def __init__(self, name, job=None, pay=0):
        self.name = name
        self.job = job
        self.pay = pay
bob = Person('Bob Smith') # Test the class
sue = Person('Sue Jones', job='dev', pay=100000) # Runs __init__ automatically
print(bob.name, bob.pay) # Fetch attached attributes
print(sue.name, sue.pay) # sue's and bob's attrs differ
```
Bob accepts the defaults for `job` and `pay`. Sue provides values explicitly. We use keyword arguments when we make Sue. Position would work too, but keywords remind us what each value means. They also let us pass arguments in any order, which matters once a constructor grows past two or three fields.

When the file runs as a script, the test code makes two instances and prints two attributes of each. Two lines of output are enough to prove that the constructor ran and that each instance kept its own values.

```text
$ python3 person_4.py
Bob Smith 0
Sue Jones 100000
```

You can also type the test code at the interactive prompt after importing the class. Canned tests inside the module are easier to rerun later, and they do not depend on your memory of what to type.

This small example already teaches something important. Each instance keeps its own name and pay, so changing one leaves the other untouched. Each instance is an independent record with its own copy of the state. Classes therefore work like a factory for objects, much as built-in types such as lists and dictionaries do.

Functions and modules have no such idea. Closures keep per-call state, but they lack the methods, inheritance, and structure that classes provide.

#### Using code two ways

The test code has a catch, and it bites the first time someone imports your file. Its top-level `print` calls also execute during an import. If another program imports `Person`, it will see our test output. Client programs do not want that output mixed into their own.

We could move the tests to a separate file. It is often more convenient to keep them with the code they test, because then nobody forgets to run them. The fix is the `__name__` check. Test statements should run only when the file is run directly, not when it is imported. This check was covered in the modules chapter, and it is worth seeing again here.

File `person_5.py` (test code runs only when run directly)

```python
class Person:
    def __init__(self, name, job=None, pay=0):
        self.name = name
        self.job = job
        self.pay = pay
if __name__ == '__main__': # When run for testing only
    bob = Person('Bob Smith')
    sue = Person('Sue Jones', job='dev', pay=100000)
    print(bob.name, bob.pay)
    print(sue.name, sue.pay)
```
Now each use behaves correctly. Running the file tests it, because its `__name__` is `__main__`. Importing it only defines the class, and the module sits quietly in memory until someone builds an instance.

```text
$ python3 person_5.py
Bob Smith 0
Sue Jones 100000
$ python3
>>> import person_5
>>>
```

When imported, the file defines the class but does not use it. When run directly, it creates two instances and prints their attributes. The values differ because each instance is its own namespace, a private table of names that belongs to that object alone.

### Step 2: Adding behavior methods

So far the class is a record factory. It creates instances and fills out their fields, but it does no work with them. That is still useful, and we can do the work ourselves from outside the class.

Classes add structure, but they mostly work by processing core types such as lists and strings. If you already know those types, you already know much of the class story. The class is a wrapper around values you already understand.

The `name` field is a plain string, for example. We can get a last name by splitting on spaces and indexing. These are core-object operations, and they work the same whether the string sits in a class or not.

```python
>>> name = 'Bob Smith' # Simple string, outside class
>>> name.split() # Extract last name
['Bob', 'Smith']
>>> name.split()[-1] # Or [1], if always just two parts
'Smith'
```

We can also give a raise by changing the `pay` field in place with an assignment. The same core operations apply, whether the number is standalone or embedded in an object. The formatting here hides extra digits, which is exactly what you want when the figure is money.

```python
>>> pay = 100000 # Simple variable, outside class
>>> pay *= 1.10 # Give a 10% raise
>>> print(f'{pay:,.2f}') # Or: pay = pay * 1.10, if you like to type
110,000.00 # Or: pay = pay + (pay * .10), if you really do
```

The move to objects is smaller than it looks. To apply these operations to our objects, use `bob.name` and `sue.pay` in place of `name` and `pay`. The operations stay the same. Only the subjects change, because they are now attributes of objects made from our class.

File `person_6.py` (operate on attributes directly)

```python
class Person:
    def __init__(self, name, job=None, pay=0):
        self.name = name
        self.job = job
        self.pay = pay
if __name__ == '__main__':
    bob = Person('Bob Smith')
    sue = Person('Sue Jones', job='dev', pay=100000)
    print(bob.name, bob.pay)
    print(sue.name, sue.pay)
    print(bob.name.split()[-1]) # Extract object's last name
    sue.pay *= 1.10 # Give this object a raise
    print(f'{sue.pay:,.2f}')
```
The last three lines extract Bob's last name with string and list operations. They also give Sue a raise by changing her `pay` attribute in place. In a sense Sue is mutable, much as a list changes after `append`. Running the file prints the following.

```text
$ python3 person_6.py
Bob Smith 0
Sue Jones 100000
Smith
110,000.00
```

This works, but an experienced developer would object to the approach. Operations hardcoded outside the class cause maintenance trouble later. If we hardcode last-name extraction in many places, a change to name handling means hunting down every copy. The same is true for the raise code. If raises later need approval or a database update, we may have several copies to change.

Finding every copy is harder in a large program. The code may sit in many files and folders, split across steps. In a prototype like this, change is almost certain, so the copies will drift apart sooner or later.

#### Coding methods

The better design is encapsulation. You wrap an operation behind an interface so it is coded once. If the need changes, there is one copy to update. You can also change its internals without breaking the code that calls it, which is the real gift.

In Python, you put operations on objects in a class's methods, instead of scattering them through the program. A method is simply a function that lives on a class and works on its instances. Classes are very good at this kind of factoring. Turning operations into methods has another benefit. The methods work on any instance, not only the ones they were hardcoded for.

The `person_7.py` version moves the two operations into methods. The self-test code also switches to the new methods, so the test proves the methods work rather than the old inline code.

File `person_7.py` (move operations into methods)

```python
class Person:
    def __init__(self, name, job=None, pay=0):
        self.name = name
        self.job = job
        self.pay = pay
    def lastName(self): # Behavior methods
        return self.name.split()[-1] # self is implied subject
    def giveRaise(self, percent):
        self.pay = int(self.pay * (1 + percent)) # Must change here only
if __name__ == '__main__':
    bob = Person('Bob Smith')
    sue = Person('Sue Jones', job='dev', pay=100000)
    print(bob.name, bob.pay)
    print(sue.name, sue.pay)
    print(bob.lastName(), sue.lastName()) # Use the new methods
    sue.giveRaise(.10) # instead of hardcoding
    print(sue.pay)
```
Methods are normal functions attached to a class. They process instances of that class. The instance is the subject of the call, and Python passes it to `self` automatically.

The transformation is simple, and it is worth following name by name. The new `lastName` does for `self` what the old code did for `bob`. It also returns its result, so the caller can use the value however it likes. The new `giveRaise` does the same for `self` that we did for `sue` before.

The output is nearly the same as before. We mostly refactored the code so future changes are easier. Command lines for the latest version are often left out from here on to save space.

```text
Bob Smith 0
Sue Jones 100000
Smith Jones
110000
```

Notice that Sue's pay is still an integer after the raise. The `int` call inside the method converts the result back. Integer and float values mix freely in expressions, so this choice matters little in a demo. A real system with money needs more care about truncation and rounding.

The book notes several ways to handle money. Chapter 5 covered `round(N, 2)` for keeping cents, the `decimal` type for precise values, and floats displayed with a format string. For now we simply truncate cents with `int`, and we know we are doing it.

We now print Sue's last name too. Because the logic lives in a method, it works on any instance. Python sends the right instance to the first argument, which is usually named `self`. In the first call, `bob` is the subject and goes to `self`. In the second call, `sue` goes to `self` instead.

Trace these calls until the instance-to-`self` link is clear. It is a key idea, and everything later in the chapter leans on it. The method always fetches the name of whichever instance it was called on. The same holds for `giveRaise`. We could give Bob a raise the same way. Bob's zero pay blocks it, because zero times anything is zero. That is a problem for a future release.

The `giveRaise` method also assumes `percent` is a fraction between zero and one. That assumption may be too loose for the real world, since a 1,000% raise is probably a bug. We allow it for this prototype. Later chapters show how decorators and the `assert` statement can check such values automatically. Chapter 39 builds a tool that validates arguments this way.

```python
@rangetest(percent=(0.0, 1.0)) # Use decorator to validate
def giveRaise(self, percent):
    self.pay = int(self.pay * (1 + percent))
```
### Step 3: Operator overloading

The class now creates instances and gives them two behaviors. Testing it is still awkward, though. To inspect an object, we print its attributes one at a time, and we have to remember which ones to ask for. It would be better if printing the whole object showed something useful on its own.

The default display is not helpful, and the first time you meet it, it looks like a mistake. It shows the class name and the object's memory address. The address is only a unique identifier, so it tells you which object you have and nothing about what the object holds.

To see this for yourself, change the last line of the script to `print(sue)`. The output says `sue` is an object and nothing more. A reader of that line learns the type and the address, which is rarely what you wanted to show.

```text
Bob Smith 0
Sue Jones 100000
Smith Jones
<__main__.Person object at 0x104972630>
```

#### Providing print displays

Operator overloading lets a class intercept built-in operations on its instances. The idea is simple once you see it. When Python is about to print an object, it first looks for a method the class may have supplied for that job. The `__repr__` method, along with its twin `__str__`, is one of the most used overloads after `__init__`.

Python runs these methods each time an instance becomes a print string. Printing an object therefore shows whatever `__str__` or `__repr__` returns. That return value is the whole display, so it may be one short label or several lines of detail. The method can be defined on the class or inherited from a superclass. Double-underscore names are inherited like any other name.

Python prefers `__str__` for `print` and `str`. It falls back to `__repr__` when `__str__` is missing, so a class with only one of the two still prints sensibly. Interactive echoes and nested displays use `__repr__` as well. You can give different displays for different contexts, one for people reading a printout and one for a developer inspecting a value. In practice, coding `__repr__` alone gives one display everywhere. A client can still add `__str__` for a different print view.

The `__init__` method is also an overload, since it runs automatically when an instance is built. Constructors feel like a special case because they are so common, and because we meet them first. Methods such as `__repr__` show the general pattern. Each one gives a class a say in an operation that would otherwise belong to Python alone.

The `person_8.py` version adds a `__repr__` that lists the attributes when the whole instance is displayed. One method, and the object starts describing itself.

File `person_8.py` (add a `__repr__` display method)

```python
class Person:
    def __init__(self, name, job=None, pay=0):
        self.name = name
        self.job = job
        self.pay = pay
    def lastName(self):
        return self.name.split()[-1]
    def giveRaise(self, percent):
        self.pay = int(self.pay * (1 + percent))
    def __repr__(self): # Added method
        return f'[Person: {self.name} ${self.pay:,}]' # String to print
if __name__ == '__main__':
    bob = Person('Bob Smith')
    sue = Person('Sue Jones', job='dev', pay=100000)
    print(bob)
    print(sue)
    print(bob.lastName(), sue.lastName())
    sue.giveRaise(.10)
    print(sue)
```
The display string uses an f-string with comma separators for pay, so a large number reads the way a person would write it. Built-in operations do the real work inside the class. Everything you learned about built-in objects and functions still applies here. A class adds a layer of structure that packages functions and data together and supports extension.

The self-test now prints the objects directly. The lines in square brackets come from `__repr__`, and print runs them automatically. Nothing in the test code asks for that formatting, which is the point: the object carries its own display with it.

```text
[Person: Bob Smith $0]
[Person: Sue Jones $100,000]
Smith Jones
[Person: Sue Jones $110,000]
```

### Step 4: Customizing behavior by subclassing

The class now does a lot for its size. It creates instances, provides methods, and overloads printing. It packages data and logic into one component, which makes the code easy to find and change. By factoring code into methods, it also avoids repetition.

One major idea is still missing: customization through inheritance. Instances already inherit methods from their class, but that is not the full power of OOP. We need a superclass and a subclass, so we can extend the software and replace parts of the inherited behavior.

Put plainly, a superclass is the general class you start from, and a subclass is the more specific class built on top of it. OOP's core promise is that you build on work already done. Used well, it can cut development time a great deal.

#### Coding subclasses

Next we define a subclass of `Person` called `Manager`. It replaces the inherited `giveRaise` with a more specialized version, and it keeps everything else exactly as `Person` wrote it. The class header looks like this.

```text
class Manager(Person): # Define a subclass of Person
```
The new class `Manager` inherits from `Person` and may add customizations. The parenthesised class name is the whole syntax for inheritance, and the parentheses hold the class you are building on. A manager is almost a person, although the book admits that is a long journey for a small joke. A `Manager` gets raises in a special way.

Assume a manager gets the passed-in percentage plus an extra bonus. The bonus defaults to 10%. A manager who is given a 10% raise therefore receives 20%, which makes the arithmetic easy to follow in the output. Any link to real people is coincidental.

The subclass's new `giveRaise` sits lower in the class tree than the `Person` version. Python's search rule picks the lowest version of a name, so the new method replaces the original for managers. Hold on to that rule. It explains almost everything that follows in this chapter.

```text
class Manager(Person): # Inherit Person attrs
def giveRaise(self, percent, bonus=.10): # Redefine to customize
```
#### Augmenting methods: the bad way

There are two ways to write this `Manager` customization. The bad way is easier to see first, so we start there. You copy the `giveRaise` code from `Person` and edit the copy for managers.

```python
class Manager(Person):
    def giveRaise(self, percent, bonus=.10):
        self.pay = int(self.pay * (1 + percent + bonus)) # Bad: cut and paste
```
This works. A call to `giveRaise` on a `Manager` runs the custom version with the bonus. So what is wrong with code that runs? Nothing, today. The cost shows up the next time someone changes how raises work.

Copying code doubles your maintenance work. If the way raises are given changes, which it probably will, you must edit two places instead of one. The two copies then drift apart, and the one you forget becomes a quiet bug. The example is small, but the issue is universal. When you feel tempted to copy code this way, look for a better design.

#### Augmenting methods: the good way

We want to augment the original `giveRaise`, not replace it. Augmenting means running the inherited version and adding to its effect. In Python you do that by calling the original version directly with adjusted arguments.

```python
class Manager(Person):
    def giveRaise(self, percent, bonus=.10):
        Person.giveRaise(self, percent + bonus) # Good: augment original
```
A method can be called two ways, and the difference matters here. Usually you call it through an instance, and Python passes the instance to `self`. Less often you call it through the class, and you pass the instance yourself.

In symbols, a normal call such as `instance.method(args…)` is translated by Python into `class.method(instance, args…)`. The class is found by the inheritance search for the method's name. Both forms work, and they reach the same code. The asymmetry is that a call through the class requires you to pass the instance manually.

A method always needs a subject instance, because the method has to know which object's data it is working on. Python fills in that argument on its own only when you call through an instance. A call through the class name needs the instance passed by hand. Inside a method such as `giveRaise`, `self` is already the subject, so you pass `self` along.

Calling through the class skips the usual lookup and runs a specific version higher in the tree. That lets us run the default `giveRaise` in `Person`, even though `Manager` redefines it. We must call through `Person` here. A call to `self.giveRaise()` inside the `Manager` method would find `Manager`'s version again and recurse until memory ran out.

The good version may look like a small difference, but the effect on maintenance is large. The raise logic lives in one place, `Person`'s method. Future changes need one edit. The form also states our intent: perform the standard raise, then add a bonus. A reader can see both steps in one line. The `person_9.py` version shows the full module with this step applied.

File `person_9.py` (subclass redefines `giveRaise`)

```python
class Person:
    def __init__(self, name, job=None, pay=0):
        self.name = name
        self.job = job
        self.pay = pay
    def lastName(self):
        return self.name.split()[-1]
    def giveRaise(self, percent):
        self.pay = int(self.pay * (1 + percent))
    def __repr__(self):
        return f'[Person: {self.name} ${self.pay:,}]'
class Manager(Person):
    def giveRaise(self, percent, bonus=.10): # Redefine at this level
        Person.giveRaise(self, percent + bonus) # Call Person's version
if __name__ == '__main__':
    bob = Person('Bob Smith')
    sue = Person('Sue Jones', job='dev', pay=100000)
    print(bob)
    print(sue)
    print(bob.lastName(), sue.lastName())
    sue.giveRaise(.10)
    print(sue)
    pat = Manager('Pat Jones', 'mgr', 50000) # Make a Manager: __init__
    pat.giveRaise(.10) # Runs custom version
    print(pat.lastName()) # Runs inherited method
    print(pat) # Runs inherited __repr__
```
The test code now makes a `Manager`, calls its methods, and prints it. We pass a name and optional job and pay, as before. `Manager` has no constructor of its own, so it inherits `__init__` from `Person`. Inheritance covers constructors as well as ordinary methods, which surprises people at first. The output follows.

```text
[Person: Bob Smith $0]
[Person: Sue Jones $100,000]
Smith Jones
[Person: Sue Jones $110,000]
Jones
[Person: Pat Jones $60,000]
```

Pat is a manager. A 10% raise gives Pat 20%, so pay goes from $50K to $60K. The custom `giveRaise` runs for Pat only. Pat also gets `lastName`, the `__init__` constructor, and the `__repr__` display from `Person` by inheritance. One class supplies the general behavior, and the other changes just the part that differs.

#### The super alternative

The examples so far extend an inherited method by naming the superclass directly, as in `Person.giveRaise(…)`. This is the explicit, traditional, and simplest approach. Most of this book uses it, and it is the form to learn first. It follows the same pattern used for class attributes, which are names attached to a class and shared by its instances. Methods are simply callable class attributes.

Java programmers may know that Python also has a `super` built-in. It lets you call a superclass method more generically, without naming the class. In the custom `giveRaise` of `Manager`, these two lines behave the same way.

```python
Person.giveRaise(self, percent + bonus) # Explicit, general use
super().giveRaise(percent + bonus) # Implicit, special case
```

The `super` built-in relies on unusual rules. It works unevenly with operator overloading. It does not always fit multiple inheritance, where one call may not be enough. It is a special-case tool with a single role, and class-name references already do that job.

`super` does have a valid role. It supports cooperative dispatch of same-named methods in multiple inheritance. That role depends on the method resolution order, or MRO, explained in Chapter 31. The MRO is simply the order Python follows when it searches a family of classes for a name. Many programmers find the MRO artificial. Cooperative use requires every class in the tree to follow the same convention. It also does not fully handle method replacement or changing argument lists. For most real Python code, it is a rare need.

This book prefers explicit superclass names, recommends the same for newcomers, and delays `super` until Chapter 32. You are free to decide for yourself. Still, `super` is usually best learned after the simpler and more explicit techniques, especially if you are new to OOP. Learn to say exactly which class you mean before you learn the shortcut that hides the name.

To Java programmers the advice is the same. Resist using `super` until you have studied its subtleties. In single inheritance it behaves as you expect, and nothing surprises you. With Python's multiple inheritance, it can pick a class that varies by context, and that class may not even be a superclass.

#### Polymorphism in action

To make inherited behavior more visible, add the following code to the end of the file. Now one loop handles all three objects, which is where inheritance starts to pay off. The book keeps this as a separate example, `person_9_plus.py`, so it has no full listing.

```python
if __name__ == '__main__':
…
print('--All three--')
for obj in (bob, sue, pat): # Process objects generically
obj.giveRaise(.10) # Run this object's giveRaise
print(obj) # Run the common __repr__
```

The output shows only the new lines, along with the effect of two raises for each person. Bob's pay stays at zero, Sue's climbs by a tenth twice, and Pat's climbs by a fifth twice.

```text
…
--All three--
[Person: Bob Smith $0]
[Person: Sue Jones $121,000]
[Person: Pat Jones $72,000]
```

In the loop, `obj` is either a `Person` or a `Manager`. Python picks the right `giveRaise` for each one. Bob and Sue use the original version in `Person`. Pat uses the custom version in `Manager`. Trace the calls yourself to see how each method is selected, one object at a time.

This is polymorphism, which we met earlier in the book. What `giveRaise` does depends on the object you call it on. Sue gets another 10%, but Pat gets another 20%, because the dispatch depends on the object's type. Passing any of the three objects to a function that calls `giveRaise` would produce the same effect. Python's flexibility depends on this idea, and so does most of the design advice in the rest of the chapter.

Printing behaves differently. It runs the same `__repr__` for all three objects, because that method is written once in `Person`. `Manager` both specializes the class and reuses the code we first wrote in `Person`. Even in a small example, this shows how classes reuse and customize code at the same time.

#### Inherit, customize, and extend

Classes can do more than our example suggests. A subclass can inherit, customize, or extend code from its superclasses. Our example focuses on customization. A subclass can also add methods that the superclass does not have, if the subclass needs them.

The following abstract sketch shows the three cases. `giveRaise` customizes an inherited method. `someThingElse` extends the class with something new.

```python
class Person:
def lastName(self): …
def giveRaise(self): …
def __repr__(self): …
class Manager(Person): # Inherit
def giveRaise(self, …): … # Customize
def someThingElse(self, …): … # Extend
pat = Manager()
pat.lastName() # Inherited verbatim
pat.giveRaise() # Customized version
pat.someThingElse() # Extension here
print(pat) # Inherited overload method
```

An extra method such as `someThingElse` adds to the existing software. It exists only on `Manager` objects, not on `Person` objects. A `Person` never sees it, which is what extension means here. For this tutorial we limit ourselves to customizing `Person` by redefining some of its behavior.

#### OOP: the big idea

Our code is small, but it works, and it shows the main point of OOP. You program by customizing what already exists, rather than copying or changing existing code. Newcomers may not see this as an advantage at first, because classes need extra code. Over time, though, this style can cut development time a great deal, and it keeps the customizations in one readable place.

Consider the alternatives to subclassing for our custom `giveRaise`. Each one falls short, and the reasons are worth knowing because you will meet all three in real code.

- We could write `Manager` as new, independent code. Then we must rewrite every behavior that `Manager` shares with `Person`.
- We could change the `Person` class directly. That breaks code that still needs the original `Person` behavior.
- We could copy the whole `Person` class, rename the copy, and edit its `giveRaise`. Later changes to `Person` would not reach the copy automatically, so each change would have to be made twice.

Copying looks quick now, but it doubles the work later. Hierarchies of classes handle software that evolves over time much better. Subclasses let you build on your earlier work instead of starting over, breaking working code, or creating redundant copies. Used well, OOP is a powerful ally.

### Step 5: Customizing constructors, too

The code works, but one detail is odd, and users of the class notice it straight away. A `Manager` must be given the job name `mgr`, even though the class already implies it. The job should be filled in automatically when a `Manager` is made, so callers cannot get it wrong.

The fix uses the same technique as the `giveRaise` customization. We redefine `__init__` in `Manager` so it supplies the `mgr` string. We also call the original `Person.__init__` by class name, so the instance attributes still get set. The specialized constructor prepares the arguments and then hands over to the general one.

The `person_10.py` version applies this change. The call that creates `pat` no longer passes the `mgr` job name, so the caller says only what the caller actually knows.

File `person_10.py` (subclass redefines `__init__`)

```python
class Person:
    def __init__(self, name, job=None, pay=0):
        self.name = name
        self.job = job
        self.pay = pay
    def lastName(self):
        return self.name.split()[-1]
    def giveRaise(self, percent):
        self.pay = int(self.pay * (1 + percent))
    def __repr__(self):
        return f'[Person: {self.name} ${self.pay:,}]'
class Manager(Person):
    def __init__(self, name, pay): # Redefine constructor
        Person.__init__(self, name, 'mgr', pay) # Run original with 'mgr'
    def giveRaise(self, percent, bonus=.10):
        Person.giveRaise(self, percent + bonus)
if __name__ == '__main__':
    bob = Person('Bob Smith')
    sue = Person('Sue Jones', job='dev', pay=100000)
    print(bob)
    print(sue)
    print(bob.lastName(), sue.lastName())
    sue.giveRaise(.10)
    print(sue)
    pat = Manager('Pat Jones', 50000) # Job name set by class
    pat.giveRaise(.10)
    print(pat.lastName())
    print(pat)
```
We use the same augmentation technique for `__init__` that we used for `giveRaise`. We run the superclass version through the class name and pass `self` explicitly. The constructor name is unusual, but the effect is the same. `Person`'s setup code must run, or instances would have no attributes.

Calling a superclass constructor this way is a very common Python pattern. By default, Python runs only one `__init__` during construction: the lowest one in the class tree. If higher constructors must run, and usually they do, you call them yourself. You can name the superclass explicitly, choose which arguments to pass up, or skip the call entirely. Skipping the call replaces the superclass logic rather than adding to it, and the missing attributes usually show up later as an error somewhere else.

The output matches the earlier version. We have only removed some redundancy, which is exactly what a good refactoring should do.

```text
$ python3 person_10.py
[Person: Bob Smith $0]
[Person: Sue Jones $100,000]
Smith Jones
[Person: Sue Jones $110,000]
Jones
[Person: Pat Jones $60,000]
```

The sidebar on `super` notes that `super().__init__(…)` without `self` would also run the superclass constructor. That is a common job for `super` in single-inheritance trees, and it is the one place many teams use it. For the reasons already given, this book keeps the explicit form.

### OOP is simpler than you may think

The complete classes cover most of the important ideas in Python's OOP machinery. It is worth listing them, because the list is shorter than the code suggests.

- Instance creation: filling out instance attributes.
- Behavior methods: encapsulating logic inside a class.
- Operator overloading: providing behavior for built-in operations such as printing.
- Customizing behavior: redefining methods in subclasses to specialize them.
- Customizing constructors: adding initialization logic on top of superclass steps.

Three simple ideas support most of these concepts. The first is the inheritance search for attributes in a tree of objects. The second is the special `self` argument in methods. The third is operator overloading, which sends built-in operations automatically to methods. Learn those three and the rest is detail you can look up.

Along the way, the code became easy to change because we factored out repetition. We wrapped logic in methods. We called superclass methods from subclass methods, so no logic is copied. Most of these steps follow naturally from what classes are good at, and none of them needed a clever trick.

That is most of OOP in Python. Classes can grow much larger, and later chapters cover advanced topics such as decorators and metaclasses. The basics are covered here. Once you understand how these classes work, most OOP code in Python should be within reach.

### Other ways to combine classes: composites

The mechanics of OOP are simple in Python. The craft in larger programs lies in how classes fit together. This tutorial focuses on inheritance because Python provides it directly. Programmers also combine classes in other ways, and one of those ways is worth a short look before we move on.

A common pattern nests objects inside other objects to build composites. A composite is an object that holds other objects and uses them to do its work. Chapter 31 explores this pattern in more depth, and it is more about design than about Python syntax. As a quick preview, we can build the `Manager` extension by embedding a `Person` inside it instead of inheriting from `Person`.

The `person-composite.py` version does this. It uses the `__getattr__` method to intercept attribute fetches that are not found, and the `getattr` built-in to forward them to the embedded object. In plain words, the outer object answers what it can and passes the rest to the object inside it.

`__getattr__` gets full coverage in Chapter 30. Its use here is simple. Python runs it for every fetch of an undefined attribute, meaning one that the inheritance search does not find on the instance. If the method returns a value, the fetch succeeds as if the attribute existed. The name also appears in the module-attribute hook from Chapter 25.

The built-in `getattr` was introduced in Chapter 25. It works like the `X.Y` fetch and performs inheritance too. The difference is that the attribute name is a string computed at run time, not a name written literally in the source. That is what lets the outer object forward a name it has never heard of.

In this version, the constructor creates the embedded object with the job name. `giveRaise` changes the argument it passes to the embedded object. `lastName` triggers `__getattr__`, which reroutes the call to the embedded object. `Manager` becomes a controller that passes calls down to the embedded object, instead of passing them up to superclass methods. The direction of the delegation is the difference between the two designs.

File `person-composite.py` (`Manager` embeds a `Person`)

```python
from person_10 import Person # Example 28-10's Person
class Manager:
    def __init__(self, name, pay):
        self.person = Person(name, 'mgr', pay) # Embed a Person object
    def giveRaise(self, percent, bonus=.10):
        self.person.giveRaise(percent + bonus) # Intercept and delegate
    def __getattr__(self, attr):
        return getattr(self.person, attr) # Delegate all other attrs
    def __repr__(self):
        return str(self.person) # Must overload again per ahead
if __name__ == '__main__':
    pat = Manager('Pat Jones', 50000) # Embed a Person
    pat.giveRaise(.10) # Run Manager.giveRaise
    print(pat.lastName()) # Delegate to embedded
    print(pat) # Run Manager.__repr__
```
The output tests only this `Manager` class. The imported `Person` from `person_10.py` tests its own code. The custom `giveRaise` still turns a 10% raise into 20%. Other calls go to the embedded `Person`, either directly or through attribute rerouting.

```text
$ python3 person-composite.py
Jones
[Person: Pat Jones $60,000]
```

This structure is called delegation. A composite object manages a wrapped object and passes method calls to it. The outer object stays thin, and the inner object does the work.

Delegation works here, but it needs about twice as much code as inheritance. It also fits direct customization less well. `Manager` is not really a `Person` in this design, so we write extra code to dispatch calls. Operator methods such as `__repr__` must be redefined, as the sidebar explained. Adding new `Manager` behavior is harder too, because the state sits one level removed. Few programmers would write this example this way in practice.

Embedding and delegation still fit some jobs well. They suit cases where the embedded object needs only limited interaction with its container. A controller or proxy like this `Manager` can adapt a class to an interface it does not support. It can also trace or validate calls to another object's methods. Class decorators, covered later, use a nearly identical pattern, which is why it is worth seeing once now.

A `Department` class can use composition to treat several people as one set. Composition simply means one object holds others and works through them. The `person-department.py` version shows a prototype.

File `person-department.py` (group objects in a composite)

```python
from person_10 import Person, Manager # Example 28-10's classes
class Department:
    def __init__(self, *args):
        self.members = list(args) # Manage an objects list
    def addMember(self, person):
        self.members.append(person)
    def giveRaises(self, percent): # Apply methods to all objects
        for person in self.members:
            person.giveRaise(percent)
    def showAll(self): # Display all nested objects
        for person in self.members:
            print(person)
if __name__ == '__main__':
    bob = Person('Bob Smith')
    sue = Person('Sue Jones', job='dev', pay=100000)
    pat = Manager('Pat Jones', 50000)
    development = Department(bob, sue) # Embed objects in a composite
    development.addMember(pat)
    development.giveRaises(.10) # Runs embedded objects' giveRaise
    development.showAll() # Runs embedded objects' __repr__
```
`showAll` lists every contained object after `giveRaises` updates each one in a polymorphic way. Nobody wrote a special case for managers, because the loop asks each object to raise itself. The output looks like this.

```text
$ python3 person-department.py
[Person: Bob Smith $0]
[Person: Sue Jones $110,000]
[Person: Pat Jones $60,000]
```

Our code mixes two techniques. The `Department` class is a composite that holds and controls other objects. The `Person` and `Manager` objects inside it use inheritance to customize their behavior. That mix is normal in real programs, so do not read the chapter as a vote for one technique over the other.

A GUI works the same way. It may use inheritance to customize labels and buttons, and composition to build forms, calculators, and editors from those widgets. The right structure depends on what you are modeling. Modeling real-world things this way is one of OOP's strengths.

Chapter 31 covers design issues such as composition in detail. For now, `Person` and `Manager` already show the basic mechanics of OOP. The next natural step is writing general tools that make OOP easier to apply in scripts.

#### Delegating built-ins, or not

The `person-composite.py` version redefines `__repr__` so that `print` reaches the embedded `Person`. It does not let `__getattr__` handle that method, as it does for other attributes. In general, a class cannot pass operator methods used by built-in operations to a wrapped object without redefining them. `__repr__` is the only such name in this example, but the issue applies to all delegation-based classes.

Built-in operations such as printing and addition call operator methods, such as `__repr__` and `__add__`, implicitly. These implicit calls do not go through the general attribute managers. Neither `__getattr__`, which runs only for undefined attributes, nor `__getattribute__`, which runs for all attributes, is invoked. The implicit `object` superclass at the top of every class tree also supplies defaults that can stop `__getattr__` from running.

That is why `Manager` must define `__repr__` itself. Comment out that method and watch the result. The `Manager` instance prints with the default display, because `__getattr__` never runs for printing. The output looks like the early person examples again, with a memory address where a description should be.

```text
$ python3 person-composite.py
Jones
<__main__.Manager object at 0x10a292c30>
```

Built-in operations begin their search for method names at the class. They skip the instance entirely. Explicit attribute fetches, by contrast, check the instance first. Every class also inherits a default `__repr__` from `object`, which can also block `__getattr__`. The `__getattribute__` method does not catch this name either. Methods that are not in `object`, such as `__add__` for `+`, are also missed by `__getattr__`.

This was a limitation in Python 3.X, but it is not a showstopper. Delegation-based classes can still redefine operator methods to forward them to wrapped objects. They can do it by hand, with tools, or through superclasses. The topic is too advanced for this tutorial. Watch for it in Chapter 38, which covers the issue, Chapter 39, which solves it, and Chapter 40, where it appears as a special case in the formal inheritance definition.

### Step 6: Using introspection tools

Before we store the objects, we make one more improvement. The classes are complete and show most of the basics of OOP. Two problems remain to fix before we use them for real, and both become obvious the first time you print an object and cannot find what you need.

First, printing `pat` shows the object as a `Person`. That is not wrong, because a `Manager` is a specialized `Person`. Still, an object should display the most specific class it was made from, since that is the class whose behavior it actually follows.

Second, the display shows only the attributes that `__repr__` names. It may not show every field we need. For example, we cannot yet verify that `pat`'s job was set to `mgr`, because the `Person` display leaves out the job field. If we add or rename attributes in `__init__`, we must also remember to update `__repr__`. Otherwise the display falls out of sync, silently, and the next reader trusts the wrong output.

The second problem is another form of redundancy. A mismatch in `__repr__` shows up in the program's output, so it may be more obvious than the others. Still, avoiding extra future work is always good, and a tool that reads attributes for itself removes the whole class of mistakes.

#### Special class attributes

The fix uses Python's introspection tools. Introspection means a program looking inside an object to see how it is built. These are special attributes and functions that expose the internals of objects. They are advanced, and they are mostly used by people who write tools for other programmers. Even so, a basic understanding helps you write code that processes classes in general ways. Two hooks from the previous chapter are useful here.

The first is `instance.__class__`. It links an instance to the class that created it. A class has a `__name__`, just as a module does. It also has a `__bases__` sequence, which gives access to its superclasses. We can use these to print the name of the instance's real class, instead of a name we hardcode. A hardcoded name is wrong for every subclass, which is exactly the problem we are fixing.

The second is `object.__dict__`. It is a dictionary with one key and value for each attribute on a namespace object, such as a module, class, or instance. Because it is a dictionary, we can get its keys, index by key, and loop over it. That lets us process every attribute generically. Chapter 25 used the same approach for module tools.

Here is a quick review at the interactive prompt, using the latest `person.py` classes from `person_10.py`. A `from` statement loads `Person`, because class names live in modules and are imported like other names. Follow the output line by line, and watch the class name appear where the hardcoded string used to be.

```python
>>> from person import Person
>>> pat = Person('Pat Jones')
>>> pat # Run pat's __repr__
[Person: Pat Jones $0]
>>> pat.__class__ # Show pat's class and its name
<class 'person.Person'>
>>> pat.__class__.__name__
'Person'
>>> list(pat.__dict__.keys()) # Attributes are dict keys
['name', 'job', 'pay']
>>> for key in pat.__dict__:
print(key, '=>', pat.__dict__[key]) # Index manually: no inheritance
name => Pat Jones
job => None
pay => 0
>>> for key in pat.__dict__: # obj.attr, but attr is a string
print(key, '=>', getattr(pat, key)) # Runs attr inheritance
…same as prior output…
```

Some attributes may not appear in `__dict__`. A class that defines `__slots__` stores attributes differently. The feature is optional, somewhat obscure, and covered in full in Chapter 32. Slots belong to the class, not the instance, and they are rarely used. We can safely ignore them here and focus on the normal `__dict__`.

Programs that might use slots should guard against a missing `__dict__`. They can catch the exception or use `hasattr`, `getattr`, and `dir`. The generic code in the next section works with slots, because the class without them still has a `__dict__`. Slot attributes and other virtual attributes are not reported as instance data, though.

#### A generic display tool

We can use these two hooks inside a base class. That base class shows the correct class name and formats every attribute of an instance of any class. The code goes in a new, independent module named `classtools.py`, so other programs can import the tool without the person classes. The `classtools.py` version shows it.

The `__repr__` in this class uses generic introspection, so it works on any instance, whatever attributes the instance has. Because it is a class, it can be mixed into any class that wants this display format. Mixing in means inheriting from the tool alongside your own class, and the method arrives with it.

If we ever change the display format, we only need to change this one class. Every class that inherits its `__repr__` picks up the new format the next time a program uses it. One edit, and a hundred classes change their output together.

File `classtools.py` (new)

```python
"Assorted class utilities and tools"
class AttrDisplay:
    """
    Provides an inheritable display overload method that shows
    instances with their class names and a name=value pair for
    each attribute stored on the instance itself (but not attrs
    inherited from its classes). Can be mixed into any class,
    and will work on any instance.
    """
    def gatherAttrs(self):
        attrs = []
        for key in sorted(self.__dict__):
            attrs.append(f'{key}={getattr(self, key)}')
        return ', '.join(attrs)
    def __repr__(self):
        return f'[{self.__class__.__name__}: {self.gatherAttrs()}]'
if __name__ == '__main__':
    class TopTest(AttrDisplay):
        count = 0
        def __init__(self):
            self.attr1 = TopTest.count
            self.attr2 = TopTest.count+1
            TopTest.count += 2
    class SubTest(TopTest):
        pass
    X, Y = TopTest(), SubTest() # Make two instances
    print(X) # Show all instance attrs
    print(Y) # Show lowest class name
```
The docstrings matter here. This is a general-purpose tool, so it should explain itself to the people who use it. Docstrings can appear at the top of functions, modules, classes, and methods. The `help` function and the PyDoc tool display them, so a reader never has to open the source file. The classes chapter returns to docstrings in Chapter 29.

Run directly, the module's self-test makes two instances and prints them. The display shows each instance's class and all of its attribute names and values, in sorted order. Notice that the subclass reports its own name, `SubTest`, without anyone writing code for that case.

```text
$ python3 classtools.py
[TopTest: attr1=0, attr2=1]
[SubTest: attr1=2, attr2=3]
```

This class uses `__repr__` rather than `__str__`, so its display applies in every context. Clients can still add `__str__`, but it affects only `print` and `str`. They lose the option of a different low-level display unless they define `__repr__` too.

A more general tool might use `__str__`, which leaves clients room to add a `__repr__` for interactive prompts and nested displays. The expanded version of this class in Chapter 31 follows that approach. For this demo we keep the all-inclusive `__repr__`.

#### Instance versus class attributes

The self-test in `classtools` shows only instance attributes. These are attached to `self`, the object at the bottom of the inheritance tree. That is what `self.__dict__` holds. As a result, the display leaves out attributes inherited from classes higher in the tree.

The `TopTest.count` attribute is a class attribute. It lives on the class, not on the instances. It is assigned inside the class body like a method and referenced in methods by its full class name. Instances inherit it, but the value is attached to the class and not copied onto each instance. Chapter 29 covers more about such nonmethod class attributes, so the main point here is that `AttrDisplay` does not show `count`.

To include inherited attributes, you can climb from the instance to its class with `__class__`. Then read the class's `__dict__` for class attributes. Use `__bases__` to climb to higher superclasses, and repeat as needed. For simpler code, call `dir` on the instance. `dir` includes inherited names in a sorted list, along with built-in `__X__` names that you can filter out.

```text
$ python3
>>> from person_10 import Person
>>> pat = Person('Pat Jones')
>>> list(pat.__dict__)
['name', 'job', 'pay']
>>> [a for a in dir(pat) if not a.startswith('__')]
['giveRaise', 'job', 'lastName', 'name', 'pay']
```

Displaying inherited class attributes is left as an experiment for now, and it is a good one to try at the prompt. Chapter 29 introduces a `classtree.py` tool that climbs an inheritance tree. Chapter 31 includes attribute listers and climbers in `lister.py`.

#### Name considerations in tool classes

`AttrDisplay` is a general tool meant to be mixed into arbitrary classes. That creates a risk of name collisions with client classes. A collision here means two classes using the same method name for different jobs. The code assumes that subclasses may want both `__repr__` and `gatherAttrs`. A subclass may not expect `gatherAttrs`, though. If a subclass defines its own `gatherAttrs`, that version will be used instead of ours, and our class may break.

To see this, add a `gatherAttrs` method to `TopTest` in the self-test. Unless the new method is identical or deliberately customizes the original, the tool stops working as planned. The `self.gatherAttrs` call inside `AttrDisplay` searches again from the `TopTest` instance, so it finds the new method. This is the same inheritance search that helped us earlier, now working against us.

```python
class TopTest(AttrDisplay):
…
def gatherAttrs(self): # Replaces method in AttrDisplay!
return 'Oops'
```

This is not always a problem. Sometimes we want subclasses to call a method or customize it. If we only meant to provide `__repr__`, though, this behavior is not ideal, and it is the kind of surprise that makes a shared tool hard to trust.

Python programmers reduce collisions by prefixing methods that are not for external use with a single underscore. In our case the name becomes `_gatherAttrs`. The underscore is a signal to other programmers, not a rule the language enforces. This is not foolproof, because another class may use the same private-looking name. It is usually good enough, and it is a common convention for internal methods.

A stronger option is two leading underscores, such as `__gatherAttrs`. Python expands such a name to include the enclosing class's name, which makes it unique during the inheritance search. This is called a pseudoprivate attribute. Chapter 31 covers it and uses it in an expanded version of this class. For now we keep both methods available.

#### Our classes' final form

To use the generic display tool, we import it, mix it in by inheritance at the top class, and remove the specific `__repr__` we wrote earlier. The new display method is inherited by `Person` instances and by `Manager` instances. `Manager` gets `__repr__` from `Person`, which in turn gets it from `AttrDisplay` in another module. Two hops of inheritance, and one tool serves both classes. The `person_14.py` version is the final `person.py` with these changes.

File `person_14.py` (final)

```python
"""
Record and process information about people.
Run this file directly to test its classes.
"""
from classtools import AttrDisplay # Use generic display tool
class Person(AttrDisplay): # Mix in a repr at this level
    """
    Create and process person records
    """
    def __init__(self, name, job=None, pay=0):
        self.name = name
        self.job = job
        self.pay = pay
    def lastName(self): # Assumes last is last
        return self.name.split()[-1]
    def giveRaise(self, percent): # Percent must be 0..1
        self.pay = int(self.pay * (1 + percent))
class Manager(Person):
    """
    A customized Person with special requirements
    """
    def __init__(self, name, pay):
        Person.__init__(self, name, 'mgr', pay) # Job name is implied
    def giveRaise(self, percent, bonus=.10):
        Person.giveRaise(self, percent + bonus)
if __name__ == '__main__':
    bob = Person('Bob Smith')
    sue = Person('Sue Jones', job='dev', pay=100000)
    print(bob)
    print(sue)
    print(bob.lastName(), sue.lastName())
    sue.giveRaise(.10)
    print(sue)
    pat = Manager('Pat Jones', 50000)
    pat.giveRaise(.10)
    print(pat.lastName())
    print(pat)
```
This is the final revision. It has docstrings for functional descriptions and `#` comments for smaller notes. It also has blank lines between methods, which help readability once classes grow. Earlier versions skipped these to keep the code short.

Now every attribute of each object appears in the display, not only the ones we hardcoded earlier. Each object shows the name of its lowest class. `pat` now displays as a `Manager`, not a `Person`. We can also confirm that the `Manager` constructor filled in the job name, because the output shows `job=mgr` where the old display showed nothing.

```text
$ python3 person_14.py
[Person: job=None, name=Bob Smith, pay=0]
[Person: job=dev, name=Sue Jones, pay=100000]
Smith Jones
[Person: job=dev, name=Sue Jones, pay=110000]
Jones
[Manager: job=mgr, name=Pat Jones, pay=60000]
```

The attribute display is now a general tool. Any class can inherit it to get the same format, and every client picks up future changes automatically. Later chapters cover more powerful tools, such as decorators and metaclasses. Together with Python's introspection tools, they let you augment and manage classes in structured ways.

### Step 7 (final): Storing objects in a database

The work is almost complete. We now have two modules. One implements the original design for representing people. The other is a general attribute display tool for other programs. Coding in functions and classes in module files makes the code reusable. Coding the software as classes makes it easy to extend.

The objects are still not real database records, though. If Python or the program stops, the instances disappear, because they live only in memory. Object persistence solves this. Persistence means saving an object somewhere so it can be rebuilt later, after the process that made it is long gone. The final step is to make our objects permanent.

#### Pickles and shelves

Three standard-library modules, installed with Python, implement object persistence. Each one works at a different level, so it helps to see them side by side before we use one.

- `pickle`: serializes arbitrary Python objects to and from a string of bytes.

- `dbm`: implements an access-by-key file system for storing strings.

- `shelve`: uses the other two modules to store Python objects in a file by key.

Chapter 9 introduced `pickle` and briefly mentioned `shelve` when we studied file basics. These modules offer simple but useful storage. A short introduction is enough to get started, though the book cannot cover them fully here.

#### The pickle module

The `pickle` module formats and parses objects. Given almost any Python object in memory, it converts the object to a byte string. It can later rebuild the original object from that string. `pickle` handles most objects, including lists, dictionaries, nested combinations of them, and class instances. Instances are especially useful to pickle, because they hold both data as attributes and behavior as methods. That pairing is roughly like keeping records and programs together, which is the whole promise of objects in the first place.

`pickle` can replace code you might otherwise write to build and parse custom text-file formats. You store an object's pickle string in a file, which makes the object persistent. Later, you load and unpickle the string to rebuild the object. The object comes back with its attributes as they were, without a line of parsing code from you.

#### The shelve module

You can store pickles in flat files with `pickle` alone. The `shelve` module adds a layer of structure. It stores pickled objects under keys. Under the hood, `shelve` turns each object into a pickle with `pickle`, and saves the string under a key in a `dbm` file. When you load a key, `shelve` fetches the string and rebuilds the object with `pickle`. You never see the two steps, but knowing they happen explains most of the behavior.

To your script, a shelf looks like a dictionary. You index by key to fetch, assign to a key to store, and use tools such as `len`, `in`, and `dict.keys` to inspect it. Shelves map these dictionary operations onto pickled objects in a file. If you already know dictionaries, you already know the interface.

The main difference from a normal dictionary is that you must open a shelf first and close it after you change it. The result is a simple database for native Python objects, stored by key and persistent across runs.

It has no SQL query support, though Python's `sqlite3` module does. It also lacks advanced features such as real transaction processing, which other Python database tools provide. Shelves still store native Python objects, and you can use the full language on them after fetching by key.

#### Storing objects on a shelve database

Pickles and shelves are advanced topics, and this book does not cover every detail. The standard-library manuals describe them fully. Since the code is simpler than the explanation, we start with the code.

The new script stores our objects on a shelf. Because it is a new file, it must import the classes to make instances. There are two ways to load a class from a module, and both are worth recognising in other people's code.

```python
import person # Load class with import
bob = person.Person(…) # Go through module name
from person import Person # Load class with from
bob = Person(…) # Use name directly
```

The script uses `from` because it is shorter. It repeats some of the self-test lines from `person.py` to create instances to store. The redundancy is acceptable in a demo. Once we have instances, storing them on a shelf is simple. Import `shelve`, open a shelf with an external file name, assign each object to a key, and close the shelf.

File `makedb.py` (save `Person` objects to a shelf)

```python
from person_14 import Person, Manager # Load our classes
bob = Person('Bob Smith') # Re-create objects to be stored
sue = Person('Sue Jones', job='dev', pay=100000)
pat = Manager('Pat Jones', 50000)
import shelve
db = shelve.open('persondb') # Filename where objects are stored
for obj in (bob, sue, pat): # Use object's name attr as key
    db[obj.name] = obj # Store object in shelf by key
db.close() # Close after making changes
```
The example uses each object's name as its key. This is for convenience, and it makes the database easy to read at the prompt. A key can be any string, including one built from process IDs and timestamps with the `os` and `time` modules. Keys must be strings and should be unique, because each key stores one object. That object can be a list, a dictionary, or any object that holds many others.

The values can be almost any Python object. That includes built-in types such as strings, lists, tuples, and dictionaries. It also includes class instances and nested combinations of all of these. The `name` and `job` attributes could be nested dictionaries and lists, as in earlier examples, though the code would need some redesign.

The script prints nothing. If it runs without output, it probably worked, and that silence takes some getting used to. It creates and stores objects in a file-based database, and the next section opens that database to prove it.

```text
$ python3 makedb.py
```

#### Exploring shelves interactively

After the script runs, files whose names start with `persondb` exist in the current directory. The exact file names vary by system. Like the built-in `open`, `shelve.open()` resolves a relative file name against the current working directory, unless the name includes a directory path.

These files form a keyed-access store that holds the pickled form of our three objects. Do not delete them. They are your database, and you must copy them when you back up or move the data.

You can inspect the files from a file browser, a shell, or the Python prompt. They are binary hash files, and their contents make little sense outside `shelve`. The standard `glob` module can list them. On macOS the shelf is a single file named `persondb.db`, which keeps the demo easy to follow. You can open it in binary mode to look at the bytes.

```python
>>> import glob
>>> glob.glob('persondb*')
['persondb.db']
>>> print(open('persondb.db', 'rb').read())
b'\x00\x06\x15a\x00\x00\x00\x02\x00\x00\x04\xd2\x00\x00…much more omitted…
```

The bytes vary, and they are hard to decode. This is not a friendly database interface, and nobody expects you to read it. A better check is another script, or a session at the prompt. Shelves are Python objects that contain Python objects, so normal Python syntax works on them. The prompt acts as a database client.

```python
$ python3
>>> import shelve
>>> db = shelve.open('persondb') # Reopen the shelf
>>> len(db) # Three objects stored
3
>>> list(db.keys()) # keys is the index
['Bob Smith', 'Sue Jones', 'Pat Jones']
>>> pat = db['Pat Jones'] # Fetch an object by key
>>> pat.lastName() # Runs lastName from Person
'Jones'
>>> pat # Runs __repr__ from AttrDisplay
[Manager: job=mgr, name=Pat Jones, pay=50000]
>>> for key in sorted(db): # Iterate, sort, fetch, print
print(key, '=>', db[key])
Bob Smith => [Person: job=None, name=Bob Smith, pay=0]
Pat Jones => [Manager: job=mgr, name=Pat Jones, pay=50000]
Sue Jones => [Person: job=dev, name=Sue Jones, pay=100000]
```

We do not need to import `Person` or `Manager` to use the stored objects. We can call `pat.lastName()` and get the custom display, even though those classes are not in scope. When Python pickles an instance, it records the instance's attributes, the name of its class, and the module that holds the class. Later, unpickling imports the class by name and makes a new instance with the saved attributes.

So loaded instances get all their class behavior back. We import classes only to make new instances. We do not need them to process existing ones. This design has trade-offs, and both sides are worth knowing before you rely on it.

The downside is that the classes and their module files must be importable when an instance loads. The class must sit at the top level of a module on `sys.path`. It should not live in the `__main__` script unless the script is always the module in use. For this reason, some programs pickle plain dictionaries or lists instead, especially when the data moves across networks.

The upside is that edits to a class's source file are picked up automatically when instances load again. The stored objects often need no update, because changing the class changes their behavior. You fix the method once, and every saved object inherits the fix on its next load.

Shelves have other limitations, which the standard library manual covers. For simple object storage, though, shelves and pickles are easy tools for personal databases, program configuration, and similar uses.

#### Updating objects on a shelf

One more script shows that the objects persist. Each run prints the database and gives a raise to one stored object. The `updatedb.py` version does this. Tracing it shows how much comes for free. Printing uses the general `__repr__`, and the raise uses the `giveRaise` method we wrote earlier. The same class behavior still works after the object comes back from disk, which is the whole point of persistence.

File `updatedb.py` (change a stored `Person` and save it)

```python
import shelve
db = shelve.open('persondb') # Reopen shelf with same filename
for key in sorted(db): # Iterate to display database objects
    print(key, '\t=>', db[key]) # Prints with custom format
sue = db['Sue Jones'] # Index by key to fetch
sue.giveRaise(.10) # Update in memory using class's method
db['Sue Jones'] = sue # Assign to key to update in shelf
db.close() # Close after making changes
```
The script prints the database at startup, so you must run it at least twice to see a change. Each run raises Sue's pay by 10%. The book suggests scheduling it as a regular `cron` job, purely to watch the numbers climb.

```text
$ python3 updatedb.py
Bob Smith => [Person: job=None, name=Bob Smith, pay=0]
Pat Jones => [Manager: job=mgr, name=Pat Jones, pay=50000]
Sue Jones => [Person: job=dev, name=Sue Jones, pay=100000]
$ python3 updatedb.py
Bob Smith => [Person: job=None, name=Bob Smith, pay=0]
Pat Jones => [Manager: job=mgr, name=Pat Jones, pay=50000]
Sue Jones => [Person: job=dev, name=Sue Jones, pay=110000]
$ python3 updatedb.py
Bob Smith => [Person: job=None, name=Bob Smith, pay=0]
Pat Jones => [Manager: job=mgr, name=Pat Jones, pay=50000]
Sue Jones => [Person: job=dev, name=Sue Jones, pay=121000]
```

The `shelve` and `pickle` modules provide the storage. Our classes provide the behavior. You can verify the result at the prompt, which again acts as a database client. Fetch the record, call a method, and the object behaves exactly as it did before it was saved.

```python
$ python3
>>> import shelve
>>> db = shelve.open('persondb') # Reopen database
>>> rec = db['Sue Jones'] # Fetch object by key
>>> rec
[Person: job=dev, name=Sue Jones, pay=133100]
>>> rec.lastName(), rec.pay
('Jones', 133100)
```

Chapter 9 covers file basics, and Chapter 37 covers string tools and Unicode. Both give more background on pickles.

## Future directions

The chapter's tutorial is complete. You have seen the basics of Python's OOP machinery at work. You have learned ways to avoid redundancy and its maintenance costs. You built full classes that do real work. You also made them persistent by storing them in a shelf.

Much more is possible. You could make the classes more realistic, add behaviors, and extend them in other ways. A raise, for example, should check that the rate is between zero and one. Decorators, covered later, can do that check.

You could also turn this example into a personal contacts database by changing the stored state and the methods that process it. That is left as an exercise for you.

Other tools are also worth exploring. GUIs, websites, and apps make a database usable by people who do not program. Other database interfaces, such as `sqlite3`, and formats such as JSON offer more options. Those topics go beyond this tutorial and this book. The standard library manuals, the web, and application-level books cover them. The next section returns to class fundamentals and completes the core language.

## Chapter summary

This chapter explored Python's class fundamentals by building one realistic example step by step. We added constructors, methods, operator overloading, subclass customization, and introspection tools. Along the way we met composition, delegation, and polymorphism, and saw how each one earns its place.

We also stored the objects on a `shelve` database. That gives a simple way to save and retrieve native Python objects by key. While learning class basics, we saw several ways to factor code and reduce redundancy. Less redundancy means lower maintenance costs later, and that is the argument for all of it.

The next chapters resume the details of Python's class model. They also cover how classes combine in larger designs.

## Class coding details: the class statement

The `class` statement looks familiar if you have used other object-oriented languages. It behaves differently in one key way. In C++, `class` is a declaration. In Python, a `class` statement is an object builder and an implicit assignment. When Python runs it, the statement creates a class object and stores a reference to that object in the name used in the header. In other words, the class is a value, and the header name is the variable that holds it.

Like `def`, the `class` statement is executable code. Your class does not exist until Python reaches and runs the statement that defines it. That usually happens while Python imports the module that holds the class, and not before. A class defined inside a branch that never runs simply never exists.

### General syntax and usage

A `class` statement is a compound statement. Its body is indented under the header. Superclasses go in parentheses after the class name, separated by commas. Listing more than one superclass creates multiple inheritance, which Chapter 31 covers more formally. The left-to-right order of the superclasses gives the search order.

```text
class name(superclass,…):   # Assign to name
    attr = value            # Shared class data
    def method(self,…):     # Methods
        self.attr = value   # Per-instance data
x = name(…)                 # Make an instance
x.method(…)                 # Call a method
```

Inside the `class` statement, every assignment creates a class attribute. That covers data items and functions, which are called methods. Specially named methods implement built-in operations. For example, a function named `__init__` runs when an instance is built, if you define it. Calling the class after its `class` statement has run makes instances, one per call.

### Class attributes and shared data

Classes are mostly namespaces. They define names, called attributes, that export data and logic to clients. A module file works the same way. The statements nested in a `class` body create the class's namespace.

When Python runs the statement, it runs each nested statement from top to bottom. Each assignment creates a name in the class's local scope, and that name becomes an attribute of the class object.

Classes resemble both modules and functions:

- Like functions, `class` statements are local scopes where nested assignments create names.
- Like modules, names assigned in a `class` statement become attributes of the class object.

The main difference is inheritance. A class's namespace is the basis of inheritance. If Python cannot find an attribute on an instance, it looks for it in the classes above. That single rule explains why a class attribute can be read through an instance.

Any statement can appear in a class body, including `print`, assignments, `if`, and `def`. All of them run when the `class` statement runs, not later when the class makes an instance. Assignments usually create data attributes, and nested `def` statements create method attributes. Any name assigned at the top level of a `class` statement becomes an attribute with that same name.

A simple nonfunction object assigned to a class attribute becomes a data attribute shared by all instances. The example below assigns a number, but the same holds for a list or a dictionary:

```python
>>> class SharedData:
...     attr = 16              # Generates a class data attribute
...
>>> x = SharedData()           # Make two instances
>>> y = SharedData()
>>> x.attr, y.attr             # They inherit and share 'attr' (a.k.a. SharedData.attr)
(16, 16)
```

Here `attr` is assigned at the top level of the class, so it attaches to the class. Every instance shares it through the search from instance to class. You can change it through the class name. You can read it through an instance or through the class, and both reads see the same value.

```python
>>> SharedData.attr = 32
>>> x.attr, y.attr, SharedData.attr
(32, 32, 32)
```

Class attributes like this can track information about all instances, such as a count of how many were made. Chapter 32 shows that idea with a full example. Now assign the same name through an instance, and watch where the value goes:

```python
>>> x.attr = 64
>>> x.attr, y.attr, SharedData.attr
(64, 32, 32)
```

An assignment to an instance attribute creates or changes a name on that instance, not on the shared class. Inheritance searches happen on attribute references, not on attribute assignments. Assigning to an object's attribute changes only that object. The name `y.attr` still comes from the class. The assignment to `x.attr` attaches a new name to `x`, which hides the class version. The class value is still there, and `SharedData.attr` still reads it.

Readers who know other languages may call class attributes like `SharedData.attr` static data members. Python needs no special term for them. Every class attribute is just a name assigned in a `class` statement. When that name refers to a function, it acts as a method and receives an instance when called through one.

Here is a class that stores the same name in two places. Read it slowly, because the two places are the heart of this section:

```python
>>> class MixedNames:                          # Define class
...     data = 'text'                          # Assign class attr
...     def __init__(self, value):             # Assign method name
...         self.data = value                  # Assign instance attr
...     def display(self):
...         print(self.data, MixedNames.data)  # Instance attr, class attr
...
```

The class has two `def` statements, which assign method functions to class attributes. The top-level `data = 'text'` assignment lives in the class's local scope and becomes an attribute of the class object. Like every class attribute, it is shared by the instances that do not have their own `data`.

Making instances attaches `data` to each of them, through the `self.data` assignment in `__init__`. Now the same name exists in three namespaces at once:

```python
>>> x = MixedNames(1)                          # Make two instance objects
>>> y = MixedNames(2)                          # Each has its own data
>>> x.display(); y.display()                   # self.data differs, MixedNames.data is the same
1 text
2 text
```

The name `data` now lives in two places. Each instance holds its own copy, and the class holds one shared copy. The `display` method prints both by qualifying `self` first and then the class. Names attached to classes are shared. Names attached to instances record data for one object.

Although inheritance searches find names for us, we can reach any attribute by naming the object that holds it. The object you start from focuses and limits the search. In this example, `x.data` and `self.data` return the instance name, which hides the class name. `MixedNames.data` fetches the class version on purpose.

Attribute assignment has exceptions. Assigning to an object's attribute changes only that object, unless its class redefines assignment with the `__setattr__` operator-overloading method. Chapter 30 covers that method. Properties and descriptors can also intercept assignments. Chapters 32 and 38 cover them. Most code follows the normal rule, which is enough to read and write everyday classes.

## Methods and how they are called

A method is a function that lives inside a class, and the class is what gives it its extra power. Methods are function objects created by `def` statements nested in a `class` body. From an abstract view, methods give instances behavior to inherit. From a programming view, they work like simple functions.

There is one crucial exception. A method's first argument receives the instance that is the subject of the call.

A method call made through an instance looks like this:

```text
instance.method(args…)
```

Python translates it into a call on the class:

```text
class.method(instance, args…)
```

Python finds the class by the inheritance search for the method's name. Both forms are valid. In the second form, the class name narrows the search, and you pass the instance yourself. The result is the same, which is why the two forms are worth keeping side by side in your head.

By convention, the first argument of a method is named `self`. Only its position matters, not its name. The argument gives the method a link back to the instance being processed. Because a class makes many instances, `self` is how each method manages its own instance's data.

In Python, `self` is always explicit. A method must list `self` and use it to fetch or change instance attributes. That makes it clear that a name refers to an instance attribute and not to a local or global name.

### A method example

Here is a small class with one method, short enough to follow at the prompt:

```python
>>> class NextClass:                         # Define class
...     def printer(self, text):             # Define method
...         self.message = text              # Change instance
...         print(self.message)              # Access instance
...
```

The name `printer` refers to a normal function object. Because it is assigned in the `class` statement, it becomes a class attribute. Every instance inherits it, which is why it counts as a method. Methods like this one process instances, so we usually call them through instances:

```python
>>> x = NextClass()                          # Make instance
>>> x.printer('instance call')               # Call its method
instance call
>>> x.message                                # Instance changed
'instance call'
```

Python first finds `printer` by inheritance. Then it passes `x` to `self` automatically, and `'instance call'` goes to `text`. Python fills in the first argument for us, so we pass just one argument. Inside `printer`, `self` reads and writes per-instance data.

We can also call the method through the class name, as long as we pass an instance to `self` ourselves. Nothing new happens inside the method. Only who supplies the subject changes:

```python
>>> NextClass.printer(x, 'class call')       # Direct class call
class call
>>> x.message                                # Instance changed again
'class call'
```

Calls through the instance and calls through the class have the same effect, as long as we pass the same instance by hand. Calling the method through the class with no instance fails, and the error message is worth reading once:

```python
>>> NextClass.printer('bad call')
TypeError: NextClass.printer() missing 1 required positional argument: 'text'
```

Class methods are really just functions assigned to class attributes. Some of them expect an instance. Python supplies that instance automatically only when the call goes through an instance. Fetching a method through the class uses the same `class.attribute` pattern that fetches any class attribute. That tool works on any object, callable or not.

### Other method-call possibilities

Calling a method through the class is the basis for extending inherited behavior, instead of replacing it. The call needs an explicit instance, because a normal method always receives one. Methods called through instances are instance methods unless special code changes that.

Chapter 32 introduces static methods, which do not expect an instance even when called through one. Static methods act like simple functions with names local to their class. Class methods receive the class instead of an instance. They can manage data for the whole class. Metaclasses also use class methods, and Chapter 40 covers them. These are optional and less common extensions. Normally, you pass an instance to a method, either automatically through an instance or by hand through the class.

## Inheritance in detail

Inheritance happens when an object is qualified. Python searches a tree of attribute namespaces. For an expression like `object.attr`, the search starts at `object` and moves upward. It stops at the first `attr` it finds. The same search runs for `self` attributes inside methods.

Lower definitions override higher ones, and that override is the basis of specialization. Picture a filing cabinet with drawers stacked from the floor to the ceiling. You always open the lowest drawer that has the label you want, and you stop looking there.

### Building the attribute tree

Three kinds of code build the tree. Between them they cover every name an instance can reach:

- Instance attributes come from assignments to `self` attributes in methods.
- Class attributes come from assignments nested in a `class` statement.
- Superclass links come from the classes listed in parentheses in a `class` header.

The result is a tree of namespaces. It leads from an instance to the class that made it, and then to every superclass in the header. Python searches up this tree from instance to superclass. With several superclasses, it searches them from left to right. The search happens each time you fetch an attribute from an instance.

Attributes can also be created by assignments outside `class` statements. In Python, all attributes are accessible by default. Privacy is an add-on. Chapter 30 covers attribute privacy with `__setattr__`, Chapter 31 covers `__X` names, and Chapter 39 builds privacy with a class decorator. Changes made outside a class are uncommon and easy to get wrong. Classes work best when they manage their own instances.

The full inheritance story gets more complicated with advanced topics. Metaclasses, diamond-pattern method resolution orders, and descriptors can all change the picture. Chapter 31 starts to formalize the inheritance algorithm, and Chapter 40 finishes it. In most Python code, though, inheritance is a simple way to redefine and customize behavior.

### Specializing inherited methods

Because the search finds names in subclasses before superclasses, a subclass can replace default behavior. A subclass may replace an inherited attribute completely. It may also provide an attribute that the superclass expects. Or it may extend a superclass method by calling back to it. You can build whole systems as class hierarchies, then extend them by adding subclasses instead of copying logic.

Here is a small example of extension:

```python
>>> class Super:
...     def method(self):
...         print('in Super.method')
...
>>> class Sub(Super):
...     def method(self):                     # Override method
...         print('starting Sub.method')      # Add actions here
...         Super.method(self)                # Run default action
...         print('ending Sub.method')
...
```

The `Sub` class replaces `Super`'s `method`. Inside the replacement, it calls the `Super` version to run the default behavior. So `Sub.method` extends the superclass method instead of replacing it completely. Three print calls, and you can see the order of events:

```python
>>> x = Super()                              # Make a Super instance
>>> x.method()                               # Runs Super.method
in Super.method
>>> x = Sub()                                # Make a Sub instance
>>> x.method()                               # Runs Sub.method, calls Super.method
starting Sub.method
in Super.method
ending Sub.method
```

Calls from one class to a superclass method are the core of this pattern. Constructors are the most common place for them. Python looks up `__init__` through inheritance, like any other attribute. At construction time, Python finds and calls only one `__init__`, not one in every superclass. If a subclass needs the superclass's setup logic to run too, it must call that `__init__` itself:

```python
>>> class Super:
...     def __init__(self, x):
...         print('default code')
...
>>> class Sub(Super):
...     def __init__(self, x, y):
...         Super.__init__(self, x)           # Run superclass __init__
...         print('custom code')              # Do my extra init actions
...
>>> I = Sub(1, 2)
default code
custom code
```

This is one of the few places where you call an operator-overloading method directly. Call the superclass constructor this way only when you want it to run. Without the call, the subclass replaces the superclass constructor completely, and the attributes it would have set are simply missing.

Redefining a constructor inside the same class with a different argument list does not add a second constructor. Later `def` statements simply reassign the method name, so only the last one is used. Starred arguments can handle this, but they are rarely used. Chapter 31 explains polymorphism more fully. Its lesson is about interfaces, not about call signatures.

### The super alternative

Python also has a `super` built-in. It calls a superclass method more generally, without naming the class. The following two lines do the same job in the `Sub` class above:

```python
Super.method(self)                 # Explicit, general tool
super().method()                   # Implicit, special case
```

The same equivalence holds for constructors:

```python
Super.__init__(self, x)            # Explicit fundamental
super().__init__(x)                # Implicit alternative
```

The `super` built-in relies on special rules. It has trade-offs in basic use, and it has a narrow advanced use that needs every class in a tree to follow it. Because of these issues, this book calls superclasses by explicit name. If you are new to Python, consider doing the same, especially on your first pass through OOP. Learn the simple and general form first. Chapter 32 covers `super` in full, so you can weigh it against the explicit form later.

### Class interface techniques

Subclasses can interface with a superclass in more than one way. The file `specialize.py` in Example 29-1 defines several classes that show common techniques. Study how each one customizes the shared superclass. The list below names the five techniques before the code shows them.

- `Super` defines a `method` function and a `delegate` method that expects an `action` in a subclass.
- `Inheritor` provides no new names, so it gets everything from `Super`.
- `Replacer` overrides `Super`'s `method` with its own version.
- `Extender` customizes `Super`'s `method` by overriding it and calling back to the default.
- `Provider` implements the `action` method that `Super`'s `delegate` method expects.

```python
class Super:
    def method(self):
        print('in Super.method')                 # Default behavior
    def delegate(self):
        self.action()                             # Expected to be defined
class Inheritor(Super):                           # Inherit method verbatim
    pass
class Replacer(Super):                            # Replace method completely
    def method(self):
        print('in Replacer.method')
class Extender(Super):                            # Extend method behavior
    def method(self):
        print('starting Extender.method')
        Super.method(self)                        # Or: super().method()
        print('ending Extender.method')
class Provider(Super):                            # Fill in a required method
    def action(self):
        print('in Provider.action')
if __name__ == '__main__':
    for klass in (Inheritor, Replacer, Extender):
        print('\n' + klass.__name__ + '...')
        klass().method()
    print('\nProvider...')
    x = Provider()
    x.delegate()
```

Two details in this file are worth noticing. The self-test creates instances of three classes in one `for` loop. Classes, like functions, are first-class objects here. You can store them in a tuple and create instances from them with no extra syntax. Classes also have a built-in `__name__` attribute, just as modules do. It holds the name from the class header, which is why the loop can label its own output. Running the file produces this output:

```text
$ python3 specialize.py
Inheritor...
in Super.method
Replacer...
in Replacer.method
Extender...
starting Extender.method
in Super.method
ending Extender.method
Provider...
in Provider.action
```

Trace the code yourself to see how each line of output is produced. The exercise takes two minutes and is worth more than a paragraph of explanation.

### Abstract superclasses

`Provider` is one of the most important classes in that example, because it shows how a superclass can call code it has never seen. When you call `delegate` through a `Provider` instance, two separate inheritance searches happen:

1. The first `x.delegate` call finds the `delegate` method in `Super`. The search starts at the `Provider` instance and moves upward. The instance `x` goes to the method's `self` argument.
2. Inside `Super.delegate`, `self.action` starts a new search from `self` upward. Because `self` refers to a `Provider` instance, the search finds `action` in `Provider`.

This filling-in-the-blanks structure is typical of object-oriented frameworks. A framework might handle a GUI event, render data in a web page, or process a tag in an XML file. Your subclass supplies the specific actions. The framework handles the rest and runs your actions when they are needed.

For `delegate`, the superclass is an abstract superclass. It expects parts of its behavior to come from its subclasses. If a subclass does not define the expected method, the inheritance search fails, and Python raises an undefined-name exception. The word abstract here means incomplete on purpose, not vague.

Class coders often make such requirements clearer. They use `assert` statements, or they raise the built-in `NotImplementedError` in stub methods. A stub is a method that exists only to complain if nobody replaces it. Chapters 33 and 34 cover `assert` and exceptions in depth. Here is the `assert` version:

```python
>>> class Super:
...     def delegate(self):
...         self.action()
...     def action(self):
...         assert False, 'action must be defined!'    # Error if called
...
>>> X = Super()
>>> X.delegate()
AssertionError: action must be defined!
```

An `assert` raises an exception with the message you give when its first expression is false. Here the expression is always false, so the stub triggers an error if a subclass forgets to redefine the method. The `NotImplementedError` version signals the same mistake, with a more explicit name:

```python
>>> class Super:
...     def delegate(self):
...         self.action()
...     def action(self):
...         raise NotImplementedError('action must be defined!')
...
>>> X = Super()
>>> X.delegate()
NotImplementedError: action must be defined!
```

Subclasses still get the exception, unless they provide the expected method and replace the superclass stub. The first subclass below inherits the complaint, and the second one fixes it:

```python
>>> class Sub(Super): pass
...
>>> X = Sub()
>>> X.delegate()
NotImplementedError: action must be defined!
>>> class Sub(Super):
...     def action(self): print('okay')
...
>>> X = Sub()
>>> X.delegate()
okay
```

Exercise 8, "Zoo animal hierarchy," in the Part VI exercises offers a bigger example of these ideas. Its solution appears in Appendix B of the book. Taxonomies like that are a traditional way to teach OOP, although most developers work on other kinds of code.

#### Abstract base classes with library tools

Abstract superclasses are also called abstract base classes. Python's standard library offers special syntax for them. The `abc` module provides a metaclass keyword argument in the class header, and an `@abstractmethod` decorator. Both features are covered later in the book, so this is a preview:

```python
>>> from abc import ABCMeta, abstractmethod
>>> class Super(metaclass=ABCMeta):
...     def delegate(self):
...         self.action()
...     @abstractmethod
...     def action(self):
...         pass
...
```

This version prevents instance creation unless the method is defined lower in the tree:

```python
>>> X = Super()
TypeError: Can't instantiate abstract class Super without an implementation
for abstract method 'action'
>>> class Sub(Super): pass
...
>>> X = Sub()
TypeError: Can't instantiate abstract class Sub without an implementation
for abstract method 'action'
>>> class Sub(Super):
...     def action(self): print('okay')
...
>>> X = Sub()
>>> X.delegate()
okay
```

A class with an abstract method cannot be instantiated unless every abstract method is defined in a subclass. This takes more code and more knowledge. Its advantage is that missing methods are reported when you try to make an instance. The older scheme reports them later, when you call the missing method, often far from the cause. This approach can also define an expected interface that client classes must meet.

This scheme depends on tools we have not covered yet. It uses function decorators, which Chapter 32 introduces and Chapter 39 covers in depth. It also uses metaclass declarations, which Chapter 32 mentions and Chapter 40 covers. Python's standard manuals describe this option further, along with the abstract superclasses that Python already provides.

## Namespaces and scopes in classes

With classes and instances covered, the Python namespace story is complete. This section summarizes the rules for resolving names, and it extends them to classes. Two ideas come first. Qualified and unqualified names are handled differently, and some scopes initialize object namespaces.

- Unqualified names, such as `X`, deal with scopes.
- Qualified attribute names, such as `object.X`, use object namespaces.
- Some scopes initialize object namespaces, namely those for modules and classes.

These ideas interact. In `object.X`, Python first looks up `object` by scope. Then it looks up `X` in the object it found. Two lookups, in two different systems, and the rest of the section is detail on each one.

### Simple names: global unless assigned

Unqualified simple names follow the LEGB rule. The letters stand for local, enclosing, global and built-in, in that search order. Chapter 17 introduced the rule when we studied functions. Its two parts work this way:

- Assignment (`X = value`) makes a name local by default. It creates or changes `X` in the current local scope, unless the scope declares it `global` or `nonlocal`. These declarations work in `def` for functions and in `class` for classes.
- Reference (`X`) looks in the current local scope first. Then it checks enclosing functions from inner to outer. Then it checks the global scope of the current module. Last, it checks the built-in module. Enclosing classes are never searched, so class names are reached as object attributes.

Some constructs localize names further. Examples include some comprehensions and some `try` statement clauses. Nested class scopes also have quirks that come from old bug reports. Those quirks are too obscure to cover here. Most names still follow the LEGB rule.

The `class` statement accepts `global` and `nonlocal`, just as `def` does. You need to nest the class inside a function to see how `nonlocal` works, because the statement needs an enclosing function scope to reach:

```python
>>> gvar = 111
>>> class C:
...     global gvar                  # Change name gvar in enclosing module
...     gvar = 222                   # Else it would be class attribute C.gvar
...
>>> gvar
222
>>> def outer():
...     nvar = 111
...     class C:
...         nonlocal nvar            # Change name nvar in enclosing function
...         nvar = 222               # Else it would be class attribute C.nvar
...         print(nvar)
...
>>> outer()
222
```

These declarations are rare, and they are worth recognising rather than using. They map assignments to outer scopes instead of making class attributes. They also stop assignments from creating local variables in a function. The section on nested classes covers how this interacts with scopes.

### Attribute names: object namespaces

Qualified attribute names refer to attributes of specific objects. They follow the rules for modules and classes. For class and instance objects, the reference rules also include the inheritance search, which is the part that carries the surprises:

- Assignment (`object.X = value`) creates or changes the attribute `X` in the namespace of the qualified object only. Climbing the inheritance tree happens on reference, not on assignment.
- Reference (`object.X`) searches for `X` in the object first. Then it searches each accessible class above it, using inheritance. For module objects, Python fetches `X` from the module directly.

These rules cover typical code. Advanced tools change them. Metaclasses can make reference inheritance richer. Properties, descriptors, and `__setattr__` can route assignments in other ways. Some inheritance also runs on assignment, to find descriptors with a `__set__` method. Chapter 38 covers attribute management tools, and Chapter 40 formalizes inheritance. For now, focus on the normal rules, which cover most application code.

### The rule of assignments: assignments classify names

Name lookup has separate search paths for qualified and unqualified names. Each path has several layers. It can be hard to tell where a name will end up. The key idea is that the place where you assign a name decides where it lives. An assignment decides the scope or object for that name, and every other rule follows from that.

The file `manynames.py` in Example 29-2 shows this idea in code. It leaves out obscure special cases such as comprehensions.

```python
X = 11                  # Global (module) X (manynames.X post import)
def f():
    print(X)            # Access global X per LEGB lookup
def g():
    X = 22              # Local (function) X (hides module X)
    print(X)
class C:
    X = 33              # Class attribute C.X (self.X pre self.m())
    def m(self):
        X = 44          # Local (function) X in method (unused here)
        self.X = 55     # Instance attribute self.X (hides class X)
```

This file assigns the name `X` five times. It is not best practice, but it teaches a point. Each assignment is in a different place, so the five `X` names are five different variables. The assignments create a module attribute, a function local, a class attribute, a method local, and an instance attribute. Each one is a separate variable, even though the name is the same.

Example 29-3 holds the rest of the file, which includes a self-test. It makes an instance and prints each `X` it can reach, in the order the comments predict:

```python
if __name__ == '__main__':
    print(X)            # 11: module (a.k.a. manynames.X outside file)
    f()                 # 11: global
    g()                 # 22: local
    print(X)            # 11: module name unchanged
    I = C()             # Make instance
    print(I.X)          # 33: class name inherited by instance
    I.m()               # Attach attribute name X to instance now
    print(I.X)          # 55: instance
    print(C.X)          # 33: class (a.k.a. I.X if no X in I)
    #print(C.m.X)       # FAILS: only visible in method
    #print(g.X)         # FAILS: only visible in function
```

The comments show the expected output. Trace each line to see which variable named `X` it reaches. You can fetch a class attribute through the class, `C.X`. You cannot fetch a function's or method's locals from outside its `def`. Locals are visible only to code inside that `def`. They exist in memory only while the call runs.

Other modules can import the names in this file. You must import a module before you use its names, because name separation is the main job of modules. Example 29-4 shows what a client sees:

```python
import manynames
X = 66
print(X)                # 66: the global here
print(manynames.X)      # 11: globals become attributes after imports
manynames.f()           # 11: manynames's X, not the one here!
manynames.g()           # 22: local in other file's function
print(manynames.C.X)    # 33: attribute of class in other module
I = manynames.C()
print(I.X)              # 33: still from class here
I.m()
print(I.X)              # 55: now from instance!
```

The call to `manynames.f()` prints the `X` in `manynames`, not the `X` in this file. Scopes are set by the position of assignments in the source code. Imports do not change them.

The instance's own `X` does not exist until `I.m()` runs. Attributes, like all variables, appear when they are assigned. We usually create instance attributes in an `__init__` constructor, but other options exist.

Functions can change names outside themselves with `global` and `nonlocal` statements. These give write access, and they also change which namespace an assignment binds to. Example 29-5 shows the rules:

```python
X = 11                  # Global in module
def g1():
    print(X)            # Reference global in module (11)
def g2():
    global X
    X = 22              # Change global in module
def h1():
    X = 33              # Local in function
    def nested():
        print(X)        # Reference local in enclosing scope (33)
def h2():
    X = 33              # Local in function
    def nested():
        nonlocal X
        X = 44          # Change local in enclosing scope
```

Even when scripts reuse one name in several places, Python's namespaces keep those uses apart. Still, you should not give every variable the same name in a real script. The example exists to show the machinery, not to recommend it.

### Nested classes and the LEGB rule

Classes can be nested inside functions. This is a useful pattern in some programs, especially when a function builds a class to fit its arguments. The scope effects follow from what you already know about functions. They may still surprise you the first time you see them.

Classes often appear nested in the functions that generate them. This resembles the factory function, or closure, idea from Chapter 17. The function keeps state for the class to use later. Each `class` statement creates a new local scope, just as `def` does. The LEGB rule applies to the top level of the class and to the top level of its methods. Both are local scopes, and both can see their own names, enclosing function names, module globals, and built-ins.

While the `class` statement runs, the class body is a local scope. After it finishes, the class body becomes an attribute namespace, like a module does.

A class can see enclosing functions, but it is not an enclosing scope for the code nested inside it. Python searches enclosing functions for names. It never searches enclosing classes. Method functions must therefore reach class attributes through `self` or the class name, using inheritance. That one sentence explains every odd result in the examples that follow.

Example 29-6 shows this effect. The name `X` stays global for the class body and for the first method, because nothing assigns it closer:

```python
X = 1
def nester():
    print(X)                # Global: 1
    class C:
        print(X)            # Global: 1
        def method1(self):
            print(X)        # Global: 1
        def method2(self):
            X = 3           # Hides global
            print(X)        # Local: 3
    I = C()
    I.method1()
    I.method2()
    print(X)                # Global: 1
nester()                    # Rest: 1, 1, 1, 3
```

Example 29-7 reassigns the name in the enclosing function. Each reassignment creates a local name that hides the names in enclosing scopes. A class layer in the middle does not change that rule:

```python
X = 1
def nester():
    X = 2                   # Hides global
    print(X)                # Local: 2
    class C:
        print(X)            # In enclosing def (nester): 2
        def method1(self):
            print(X)        # In enclosing def (nester): 2
        def method2(self):
            X = 3           # Hides enclosing (nester)
            print(X)        # Local: 3
    I = C()
    I.method1()
    I.method2()
    print(X)                # Global: 1
nester()                    # Rest: 2, 2, 2, 3
```

Example 29-8 reassigns the name at several levels. Assignments in the local scopes of both functions and classes hide globals and enclosing function locals with the same name. Read the comments beside each `print` before you run it, and the output will make sense:

```python
X = 1
def nester():
    X = 2                   # Hides global
    print(X)                # Local: 2
    class C:
        X = 3               # Class local hides nester's: C.X or I.X (not scoped)
        print(X)            # Local: 3
        def method1(self):
            print(X)        # In enclosing def (not 3 in class!): 2
            print(self.X)   # Inherited class local: 3
        def method2(self):
            X = 4           # Hides enclosing (nester, not class)
            print(X)        # Local: 4
            self.X = 5      # Hides class's
            print(self.X)   # Located in instance: 5
    I = C()
    I.method1()
    I.method2()
    print(X)                # Global: 1
nester()                    # Rest: 2, 3, 2, 3, 4, 5
```

The main point is that simple-name lookup never searches enclosing classes. It searches `def` scopes, modules, and built-ins. In `method1`, the name `X` is found in the enclosing `def`, even though the class has its own `X`. To reach names assigned in a class, such as methods or class attributes, use object attributes, such as `self.X`.

You will see this nested-class pattern later in the book, especially in some decorators from Chapter 39. There, the enclosing function usually builds a class or instance and keeps state for the class to use.

## Namespace dictionaries and class trees

Picture a class as a dictionary with a few pointers to other dictionaries. Chapter 23 showed that module namespaces are dictionaries, exposed through the `__dict__` attribute. Classes and instances work the same way. Attribute access is mostly a dictionary lookup, and attribute inheritance searches a chain of linked dictionaries. Instance and class objects are largely dictionaries with links between them. Python exposes these dictionaries and their links for advanced uses.

We can see how attributes work by watching the namespace dictionaries grow. First, define a superclass and a subclass. Each one has a method that stores data on its instances, so the dictionaries start empty and fill up as we call them:

```python
>>> class Super:
...     def hello(self):
...         self.data1 = 'hack'
...
>>> class Sub(Super):
...     def hola(self):
...         self.data2 = 'code'
...
```

When you make an instance of the subclass, its namespace dictionary starts out empty. It still links back to the class, so the inheritance search can follow those links. Instances have a `__class__` attribute that links to their class. Classes have a `__bases__` attribute, a tuple that links to their superclasses:

```python
>>> X = Sub()
>>> X.__dict__                      # Instance namespace dict
{}
>>> X.__class__                     # Class of instance
<class '__main__.Sub'>
>>> Sub.__bases__                   # Superclasses of class
(<class '__main__.Super'>,)
>>> Super.__bases__                 # Implied above top-levels
(<class 'object'>,)
```

When methods assign `self` attributes, those attributes go into the instance's dictionary, not the class's. An instance's namespace holds data that can differ from one instance to another. The name `self` is the hook into that namespace:

```python
>>> Y = Sub()
>>> X.hello()
>>> X.__dict__
{'data1': 'hack'}
>>> X.hola()
>>> X.__dict__
{'data1': 'hack', 'data2': 'code'}
>>> list(Sub.__dict__.keys())
['__module__', 'hola', '__doc__']
>>> list(Super.__dict__.keys())
['__module__', 'hello', '__dict__', '__weakref__', '__doc__']
>>> Y.__dict__
{}
```

The class dictionaries include extra underscore names. Python sets these automatically, and most are not used in typical programs. Tools use some of them, such as `__doc__`, which holds the docstrings from Chapter 15. You can filter them out with a comprehension.

Notice that `Y` still has an empty dictionary. Its instance was made before `X` gained attributes, and each instance has its own independent dictionary. Two instances of the same class can record completely different attributes, which is why a class is a template and not a record.

Instance attributes are also dictionary keys, so you can read and write them in two ways. You can qualify the name with a dot, or you can index the dictionary by key. The two forms touch the same storage:

```python
>>> X.data1, X.__dict__['data1']
('hack', 'hack')
>>> X.data3 = 'docs'
>>> X.__dict__
{'data1': 'hack', 'data2': 'code', 'data3': 'docs'}
>>> X.__dict__['data3'] = 'apps'
>>> X.data3
'apps'
```

Key indexing works only for attributes stored on the instance. Qualification also runs the inheritance search, so it can reach inherited attributes that the dictionary cannot. For example, `X.hello` is reachable, but `X.__dict__['hello']` fails.

Try these special attributes yourself. The `dir` function is similar to `X.__dict__.keys()`, but `dir` sorts its list and also includes inherited names.

Chapter 32 introduces slots, an advanced class feature. Slots store attributes in the instance without using its namespace dictionary. They look like class attributes, because they appear in class namespaces where they manage per-instance values.

A slot may prevent a `__dict__` from being created for the instance. Generic tools must allow for that, so they often use `dir` to list names and `getattr` to fetch them. Slots are rare, which is how they should be.

### Namespace links: a tree climber

The special `__class__` and `__bases__` attributes let you inspect inheritance hierarchies in your own code. They can display a class tree. The module in Example 29-9, `classtree.py`, does this. It is short, and worth reading all the way through before you run it:

```python
"""
classtree.py: Climb inheritance trees using namespace links,
displaying higher superclasses with indentation for height
"""
def classtree(cls, indent):
    print('.' * indent + cls.__name__)          # Print class name here
    for supercls in cls.__bases__:               # Recur to all superclasses
        classtree(supercls, indent+3)            # May visit super > once
def instancetree(inst):
    print('Tree of', inst)                       # Show instance
    classtree(inst.__class__, 3)                 # Climb to its class
def selftest():
    class A: pass
    class B(A): pass
    class C(A): pass
    class D(B,C): pass
    class E: pass
    class F(D,E): pass
    instancetree(B())
    instancetree(F())
if __name__ == '__main__': selftest()
```

The `classtree` function is recursive. It prints a class's name with `__name__`, then calls itself on each superclass. This lets it walk any shape of class tree. The recursion stops at root superclasses, whose `__bases__` is empty.

Chapter 19 explains recursion. Each active call gets its own copy of the local names, so `cls` and `indent` differ at each level.

Most of the file is self-test code. When you run it, it builds a small class tree, makes two instances, and prints their trees. Each tree includes the implied `object` superclass at the top. Chapter 32 covers `object` in more detail:

```text
$ python3 classtree.py
Tree of <__main__.selftest.<locals>.B object at 0x10733a000>
...B
......A
.........object
Tree of <__main__.selftest.<locals>.F object at 0x10733a000>
...F
......D
.........B
............A
...............object
.........C
............A
...............object
......E
.........object
```

Periods mark the height of each class in the tree. The output is not pretty, but it shows the shape at a glance. You could improve this display, or draw it in a GUI. You can also import these functions anywhere you want a quick view of a class tree:

```text
$ python3
>>> class Employee: pass
>>> class Person(Employee): pass
>>> pat = Person()
>>> import classtree
>>> classtree.instancetree(pat)
Tree of <__main__.Person object at 0x1072a1b80>
...Person
......Employee
.........object
```

This example shows one of many ways to use special attributes that expose interpreter internals. Chapter 31 uses the same technique to display attributes in each object in a class tree. Chapter 39 applies such tools to attribute privacy and argument validation. Not every Python programmer needs these tools. They are still powerful when a project needs them.

## Documentation strings in classes

Docstrings can appear in class components, not only in modules. A docstring is a string literal at the top of a module, function, class, or method. Python saves it in the object's `__doc__` attribute. Chapter 15 covers docstrings in detail.

Example 29-10, `docstr.py`, summarizes where they can appear. Each one can be a triple-quoted block or a short one-line literal:

```python
"I am: docstr.__doc__"
def func(args):
    "I am: docstr.func.__doc__"
    pass
class Klass:
    "I am: Klass.__doc__ or docstr.Klass.__doc__ or self.__doc__"
    def method(self):
        "I am: Klass.method.__doc__ or self.method.__doc__"
        print(self.__doc__)
        print(self.method.__doc__)
```

The main advantage of a docstring is that it stays available while the program runs. You qualify an object with `__doc__` to fetch its documentation. Calling `print` on a multiline string shows its line breaks, so the same text serves a reader and a program:

```python
$ python3
>>> import docstr
>>> docstr.__doc__
'I am: docstr.__doc__'
>>> docstr.func.__doc__
'I am: docstr.func.__doc__'
>>> docstr.Klass.__doc__
'I am: Klass.__doc__ or docstr.Klass.__doc__ or self.__doc__'
>>> docstr.Klass.method.__doc__
'I am: Klass.method.__doc__ or self.method.__doc__'
>>> x = docstr.Klass()
>>> x.method()
I am: Klass.__doc__ or docstr.Klass.__doc__ or self.__doc__
I am: Klass.method.__doc__ or self.method.__doc__
```

The PyDoc tool formats these strings into reports and web pages. Chapter 15 covers it. The `help` function runs it, and this is what it shows for the same module:

```text
>>> help(docstr)
Help on module docstr:
NAME
    docstr - I am: docstr.__doc__
CLASSES
    builtins.object
        Klass
    class Klass(builtins.object)
     |  I am: Klass.__doc__ or docstr.Klass.__doc__ or self.__doc__
     |
     |  Methods defined here:
     |
     |  method(self)
     |      I am: Klass.method.__doc__ or self.method.__doc__
     |
     |  ----------------------------------------------------------------------
     |  Data descriptors defined here:
     |
     |  __dict__
     |      dictionary for instance variables
     |
     |  __weakref__
     |      list of weak references to the object
FUNCTIONS
    func(args)
        I am: docstr.func.__doc__
```

Docstrings are available at runtime, but they are less flexible than `#` comments. Comments can appear anywhere in a program, and they cost nothing to keep. Both are useful, and accurate documentation of either kind is good. A common rule of thumb is to use docstrings for higher-level documentation of functions and classes. Use hash-mark comments for fine-grained notes on the code itself.

## Classes versus modules

Modules and classes both create namespaces, so the difference can be confusing. A namespace is just a table of names, and both kinds of object have one. The contrast is easier to see side by side:

- Modules implement packages of data and logic. They are created from Python files or from other-language extensions. You use them by importing. They form the top level of a Python program's structure.
- Classes implement new, full-featured objects. You create them with `class` statements. You use them by calling them. They always live inside a module.

Classes also support features that modules do not. These include operator overloading, multiple instance generation, and inheritance. Both classes and modules are namespaces, but they serve different purposes. Chapter 30 starts the next topic, operator overloading.

## Class coding details summary

This section took a second, deeper pass through Python's class mechanics. It covered classes, methods, and inheritance. It also summarized how names and scopes work once classes are included. Along the way, it introduced abstract superclasses, class data attributes, namespace links, and manual calls to superclass methods and constructors. Keep these ideas in mind when you read real class hierarchies.

## Operator overloading

Operator overloading lets a class intercept the built-in operations that Python runs on its instances. You have already met it through `__init__`. This section fills in more of the picture. It covers a representative sample of the methods you will use most often, and it leaves the rest to the language reference.

The key ideas are short:

- Operator overloading lets classes intercept normal Python operations.
- Classes can overload all built-in expression operators.
- Classes can also overload other operations, such as printing, function calls, and attribute access.
- Overloading works by providing specially named methods, and Python predefines those names.

When a class provides one of these methods, Python calls it whenever an instance appears in the matching operation. The method's return value becomes the result of that operation. That is the whole mechanism: a fixed name, a fixed trigger, and a return value.

### Overloading methods are optional

Operator-overloading methods are never required, and they generally have no defaults. The exception is a handful that every class gets from the implied `object` root class. If a class does not code or inherit a method, it does not support that operation. Using the operation then raises an exception, which is Python's way of saying the class never signed up for it.

Printing is one of the built-in operations that has a default from `object`. Most others fail for an instance when the matching method is missing. When you do provide these methods, your class can emulate the interface of a built-in object. That makes it consistent and compatible with more code.

Most overloading methods appear only in advanced programs. The `__init__` constructor is the main exception, because most classes use it. Do not feel obliged to overload everything a class could support. Add a method when a real operation needs it.

### Constructors and expressions: `__init__` and `__sub__`

Example 30-1 shows a `Number` class with two hooks. The `__init__` method runs when an instance is built. The `__sub__` method catches the subtraction operator.

```python
class Number:
    def __init__(self, start):          # On Number(start)
        self.data = start
    def __sub__(self, other):           # On instance - other
        return Number(self.data - other)   # Result is a new instance
```

```text
>>> from number import Number
>>> X = Number(5)          # Number.__init__(X, 5)
>>> Y = X - 2              # Number.__sub__(X, 2)
>>> Y.data                 # Y is a new Number instance
3
```

The `__sub__` method plays the binary-operator role that `__add__` played in Chapter 27. It returns a new instance, and creating that instance runs `__init__` again. So one subtraction quietly runs two methods, which is worth tracing once.

Instance creation actually begins with `__new__`. That method creates the object, and Python then passes the object to `__init__`. Most classes never define `__new__`, because its built-in version covers nearly every case. Chapter 40 uses it with metaclasses. It is also sometimes used to customize how instances of immutable types are created.

### Common operator-overloading methods

Table 30-1 lists some of the most common overloading methods. Python supports many more, and the table is a place to look things up rather than a list to memorise.

| Method | Implements | Called for |
|---|---|---|
| `__init__` | Constructor | Object creation: `X = Class(args)` |
| `__del__` | Destructor | Object reclamation of `X` |
| `__add__` | Operator `+` (among others) | `X + Y`, `X += Y` if no `__iadd__` |
| `__or__` | Operator `\|` (bitwise OR) | `X \| Y`, `X \|= Y` if no `__ior__` |
| `__repr__`, `__str__` | Printing, conversions | `print(X)`, `X`, `repr(X)`, `str(X)`, `f'{X!r}'` |
| `__call__` | Function calls | `X(*pargs, **kargs)` |
| `__getattr__` | Attribute fetch | `X.undefined` |
| `__setattr__` | Attribute assignment | `X.any = value` |
| `__delattr__` | Attribute deletion | `del X.any` |
| `__getattribute__` | Attribute fetch | `X.any` |
| `__getitem__` | Indexing, slicing, iteration | `X[i]`, `X[i:j]`, `for` and other iterations if no `__iter__` |
| `__setitem__` | Index and slice assignment | `X[i] = value`, `X[i:j] = iterable` |
| `__delitem__` | Index and slice deletion | `del X[i]`, `del X[i:j]` |
| `__len__` | Length | `len(X)`, truth tests if no `__bool__` |
| `__bool__` | Boolean tests | `bool(X)`, truth tests |
| `__lt__`, `__gt__`, `__le__`, `__ge__`, `__eq__`, `__ne__` | Comparisons | `X < Y`, `X > Y`, `X <= Y`, `X >= Y`, `X == Y`, `X != Y` |
| `__radd__` | Right-side operators | `other + X` |
| `__iadd__` | In-place augmented operators | `X += Y` (or else `__add__`) |
| `__iter__`, `__next__` | Iteration tools | `I=iter(X)`, `next(I)`, `for` and other iterations, `in` if no `__contains__` |
| `__contains__` | Membership test | `item in X` |
| `__index__` | Integer value | `hex(X)`, `bin(X)`, `oct(X)`, `O[X]`, `O[X:]` |
| `__enter__`, `__exit__` | Context manager (Chapter 34) | `with obj as var:` |
| `__get__`, `__set__`, `__delete__` | Descriptor attributes (Chapter 38) | `X.attr`, `X.attr = value`, `del X.attr` |
| `__new__` | Creation (Chapter 40) | Object creation, before `__init__` |

Many overloading methods come in several versions. Addition, for example, has `__add__`, `__radd__`, and `__iadd__`. The Python language reference lists every special method name, and it is the authority when this table runs out.

Every overloading method name starts and ends with two underscores. That keeps it distinct from names you define yourself. The name `__add__` always maps to the `+` expression, whatever its code does. The method is mainly a dispatch mechanism, a hook that Python knows to call.

Overloading methods can be inherited from superclasses, like any other method. If none is coded or inherited, the operation is unsupported. Inheritance applies here exactly as it does elsewhere, with no special case.

#### Measure before you optimize

Calling an operator method directly is not faster than using the operator. Calling `__len__` directly is about twice as slow as `len`. Python avoids or optimizes the function-call overhead in the built-in case. Some advice in circulation recommends the slower call for speed, so measure before you adopt it. This is a small example of a general habit: trust the timer, not the folklore.

Here is the comparison on Python 3.12 and macOS, using the timing techniques from Chapter 21:

```text
$ python3 -m timeit -n 10000 -r 10 \
-s "L = list(range(100))" "x = L.__len__()"
10000 loops, best of 10: 53.4 nsec per loop
$ python3 -m timeit -n 10000 -r 10 \
-s "L = list(range(100))" "x = len(L)"
10000 loops, best of 10: 25.3 nsec per loop
```

### Indexing and slicing: `__getitem__` and `__setitem__`

Indexing is the first operation most people want to intercept. The `__getitem__` method lets a class mimic some behavior of sequences and mappings. If a class defines it, or inherits it, Python calls it for indexing. For `X[i]`, Python calls `X.__getitem__` and passes the index as the second argument.

The class decides what the expression means. It should usually imitate a sequence index or a mapping key fetch. The following class returns the square of the index. That is an unusual choice, but it shows the mechanism clearly, because you cannot mistake the result for a real lookup.

```python
class Indexer:
    def __getitem__(self, index):
        return index ** 2
```

```text
>>> X = Indexer()
>>> X[2]                    # X[i] calls X.__getitem__(i)
4
>>> for i in range(5):
...     print(X[i], end=' ')    # Runs __getitem__(X, i) each time
0 1 4 9 16
```

#### Intercepting slices

The `__getitem__` method is also called for slice expressions. Built-in types handle slicing the same way. Slice bounds are bundled into a slice object, and that object is passed to the indexing operation. A slice object is simply a small record of start, stop and step. You can also pass a slice object yourself:

```text
>>> L = [5, 6, 7, 8, 9]
>>> L[2:4]                  # Slice with slice syntax
[7, 8]
>>> L[slice(2, 4)]          # Slice with a slice object
[7, 8]
>>> L[slice(None, None, 2)]
[5, 7, 9]
```

Slice syntax is mostly shorthand for indexing with a slice object. A class with `__getitem__` receives the same object. The method gets an integer for plain indexing and a slice object for slicing. One method, two kinds of argument, and the method can tell them apart.

```python
class Indexer:
    def __init__(self, data):
        self.data = data
    def __getitem__(self, index):      # Called for index or slice
        print('getitem:', index)
        return self.data[index]        # Perform index or slice
```

```text
>>> X = Indexer([5, 6, 7, 8, 9])
>>> X[0]                    # Indexing sends __getitem__ an integer
getitem: 0
5
>>> X[2:4]                  # Slicing sends __getitem__ a slice object
getitem: slice(2, 4, None)
[7, 8]
>>> X[::2]
getitem: slice(None, None, 2)
[5, 7, 9]
```

The method can test the type of its argument. A slice object has the attributes `start`, `stop`, and `step`. Any of them can be `None` when omitted, so the method must handle missing bounds as well as numbers.

```python
class Indexer:
    def __getitem__(self, index):
        if isinstance(index, int):          # Test usage mode
            print('indexing', index)
        else:
            print('slicing', index.start, index.stop, index.step)
```

```text
>>> X = Indexer()
>>> X[99]
indexing 99
>>> X[1:99:2]
slicing 1 99 2
>>> X[1:]
slicing 1 None None
```

Run `help(slice)` in a REPL to learn more about this special built-in type. The four attributes are easy to remember once you have seen them printed.

#### Intercepting item assignments

The `__setitem__` method catches index assignment. It also catches slice assignment, and it receives a slice object in that case. The method can pass the index or slice along to the embedded object. Reads and writes are separate hooks, so a class may support one and not the other.

```python
class IndexSetter:
    def __init__(self, data):
        self.data = data
    def __setitem__(self, index, value):   # Catch index or slice assignment
        print('setitem:', index)
        self.data[index] = value           # Assign index or slice
```

```text
>>> X = IndexSetter([5, 6, 7, 8, 9])
>>> X[0] = 555
setitem: 0
>>> X[-2:] = [888, 999, 111]
setitem: slice(-2, None, None)
>>> X.data
[555, 6, 7, 888, 999, 111]
```

#### But `__index__` means as-integer

The `__index__` method is easy to confuse with `__getitem__`. It does not intercept indexing. It returns an integer value for an instance when Python needs one. The name is a little unfortunate, and `__asindex__` might have been a better choice. Read it as "use this object as an integer" and the confusion disappears.

Built-ins that convert numbers to digit strings use `__index__`. The class below claims the value 255 whenever an integer is wanted:

```text
>>> class C:
...     def __index__(self):
...         return 255
>>> X = C()
>>> hex(X)
'0xff'
>>> bin(X)
'0b11111111'
>>> oct(X)
'0o377'
```

Contexts that need an integer also use it, including indexing and slicing. The instance supplies the integer, and the list does the rest. Notice that the brackets hold the object, not a number, and Python still knows what to do.

```text
>>> eds = [f'LP{i}e' for i in range(256)]
>>> eds[255]
'LP255e'
>>> X = C()
>>> eds[X]                  # As index, not X[i]
'LP255e'
>>> eds[X:]                 # As index, not X[i:]
['LP255e']
```

### Index iteration: `__getitem__`

The `for` statement has a fallback. Without a more specific iteration method, it indexes an object from zero upward. It stops when an `IndexError` exception appears. So a class with only `__getitem__` supports `for` loops too. This is the older mechanism, and it still works.

```text
>>> class StepperIndex:
...     def __getitem__(self, i):
...         return self.data[i]
>>> X = StepperIndex()
>>> X.data = 'hack'
>>> X[1]
'a'
>>> for item in X:          # for loops call __getitem__
...     print(item, end=' ')
h a c k
```

This is a case of getting one feature and receiving a bunch more. Any object that supports `for` loops also supports the other iteration tools. These include the `in` test, list comprehensions, `map`, sequence assignment, and some type constructors. The iteration protocol is shared, so every tool that speaks it can use your object.

```text
>>> 'k' in X
True
>>> [c for c in X]
['h', 'a', 'c', 'k']
>>> list(map(str.upper, X))
['H', 'A', 'C', 'K']
>>> (a, b, c, d) = X
>>> a, d
('h', 'k')
>>> ''.join(X)
'hack'
```

This technique can give an object a sequence interface. It can also add logic to built-in sequence operations. Chapter 32 revisits that idea when it extends built-in types.

### Iterable objects: `__iter__` and `__next__`

The `__getitem__` method works for iteration, but it is a legacy fallback. Python tries `__iter__` first. Only if that method is missing does it index the object. Prefer `__iter__` in new code, because it supports general iteration tools better.

Iteration tools call `__iter__` to get an iterator object. They then call the iterator's `__next__` method to get each item. When no items are left, `__next__` raises `StopIteration`. The built-in `iter` and `next` functions are convenient wrappers for these two steps.

An iterator is simply an object that remembers where it is and can hand out the next value. The iterable is the thing you loop over; the iterator is the cursor that walks it.

Example 30-2 defines a user-defined iterable that produces squares on demand. Read the two methods as a pair: one hands out the cursor, and the other moves it.

```python
class Squares:
    def __init__(self, start, stop):     # Save state when created
        self.value = start - 1
        self.stop = stop
    def __iter__(self):                  # Return iterator object
        return self                      # Also called by iter() built-in
    def __next__(self):                  # Return a square on each iteration
        if self.value == self.stop:      # Also called by next() built-in
            raise StopIteration
        self.value += 1
        return self.value ** 2
```

Once the class is imported, its instances work in iteration tools:

```text
>>> from squares import Squares
>>> for i in Squares(1, 5):             # for calls __iter__
...     print(i, end=' ')              # Each iteration calls __next__
1 4 9 16 25
```

The `raise` statement ends the iteration. Chapter 29 introduced it, and the next part of the book covers it fully. Manual iteration works the same on your class as on built-in objects. A `try` statement can catch the `StopIteration` that `next` raises at the end.

```text
>>> X = Squares(1, 5)
>>> I = iter(X)             # iter calls __iter__
>>> next(I)                 # next calls __next__
1
>>> next(I)
4
```

#### Single versus multiple scans

Iteration over `Squares` supports only one scan. Its `__iter__` returns `self`, so the iteration state lives in the one object. Once the items are used up, the object is empty. Calling `__iter__` again returns the same, exhausted object.

The picture to keep is a book with one bookmark. Once you read to the end, the bookmark stays at the end, and picking the book up again does not start over.

```text
>>> X = Squares(1, 5)
>>> [n for n in X]          # Exhausts items: __iter__ returns self
[1, 4, 9, 16, 25]
>>> [n for n in X]          # Now it is empty
[]
>>> [n for n in Squares(1, 5)]   # A new object gives a fresh copy of state
[1, 4, 9, 16, 25]
```

Each new iteration needs a new iterable object. The membership test, sequence assignment, and string joins all call `__iter__` in the same way. Every tool starts from the beginning only because it gets a fresh object.

```text
>>> 36 in Squares(1, 10)
True
>>> a, b, c = Squares(1, 3)
>>> ':'.join(map(str, Squares(1, 5)))
'1:4:9:16:25'
```

Converting the iterable to a list allows several scans. It also costs time and memory, which may or may not matter for your program. The trade is simple: pay once to store everything, or regenerate it each time.

```text
>>> X = Squares(1, 5)
>>> tuple(X), tuple(X)      # Iterator exhausted in second tuple()
((1, 4, 9, 16, 25), ())
>>> X = list(Squares(1, 5))
>>> tuple(X), tuple(X)
((1, 4, 9, 16, 25), (1, 4, 9, 16, 25))
```

The `Squares` class does not overload indexing. Its iterable is designed for iteration, not random access. The expression `X[1]` raises `TypeError: 'Squares' object is not subscriptable`. Collecting the items in a list makes indexing possible, at the cost described above.

### Classes versus generators

The `Squares` class would be shorter as a generator function or a generator expression. Those tools save their state and create the iteration methods for you. A generator is a function that produces values one at a time and pauses between them.

```text
>>> def gsquares(start, stop):          # Generator function
...     for i in range(start, stop + 1):
...         yield i ** 2
>>> for i in gsquares(1, 5):
...     print(i, end=' ')
1 4 9 16 25
>>> for i in (x ** 2 for x in range(1, 6)):   # Generator expression
...     print(i, end=' ')
1 4 9 16 25
```

Generators have automatic `__iter__` and `__next__` methods. For a simple case like this one, that is enough. A class offers more explicit attributes, inheritance hierarchies, and support for several behaviors. Those features suit richer cases better.

For this artificial example, a list comprehension is simpler still. Unless performance data says otherwise, the simplest tool is often the fastest one.

```text
>>> [x ** 2 for x in range(1, 6)]
[1, 4, 9, 16, 25]
```

Classes model complex iterations well, especially when those iterations need the other strengths of classes. An iterable that produces items from a database or web service result is a good example.

### Multiple iterators on one object

Each active loop over a string gets its own iterator. The loops can move through the string independently, so a nested loop starts from the beginning rather than from wherever the outer loop is.

```text
>>> S = 'ace'
>>> for x in S:
...     for y in S:
...         print(x + y, end=' ')
aa ac ae ca cc ce ea ec ee
```

The outer loop calls `iter` on the string, and each nested loop does the same. Each iterator keeps its own position. The string object itself supports several scans, so no copy is needed.

Generator functions, generator expressions, `map`, and `zip` each return a single-iterator object. The `range` built-in and lists support several active iterators with independent positions. A user-defined class decides which behavior it provides. To support several iterations, `__iter__` must return a new stateful object for each request, not `self`.

Example 30-3 defines an iterable that skips every other item. Each `__iter__` call creates a new iterator object from a supplemental class. That lets several loops run at once, each with its own cursor. The extra class is small, and it is the price of independent scans.

```python
class SkipObject:
    def __init__(self, wrapped):                 # Save item to be used
        self.wrapped = wrapped
    def __iter__(self):
        return SkipIterator(self.wrapped)        # New iterator each time

class SkipIterator:
    def __init__(self, wrapped):
        self.wrapped = wrapped                   # Iterator state information
        self.offset = 0
    def __next__(self):
        if self.offset >= len(self.wrapped):    # Terminate iterations
            raise StopIteration
        else:
            item = self.wrapped[self.offset]    # else return and skip
            self.offset += 2
            return item

if __name__ == '__main__':
    alpha = 'abcdef'
    skipper = SkipObject(alpha)                  # Make container object
    I = iter(skipper)                            # Make an iterator on it
    print(next(I), next(I), next(I))             # Visit offsets 0, 2, 4
    for x in skipper:                            # for calls __iter__ automatically
        for y in skipper:                        # Nested fors call __iter__ again
            print(x + y, end=' ')                # Each iterator has its own state
```

```text
$ python3 skipper.py
a c e
aa ac ae ca cc ce ea ec ee
```

The `Squares` class of Example 30-2 supports only one active loop. A nested loop would run only once unless it created a new object. Here, there is one `SkipObject` and several iterator objects, so the nested loops do not fight over a single cursor.

#### Classes versus slices

Slicing can give similar results, and it needs no class at all. The third bound skips items.

```text
>>> S = 'abcdef'
>>> for x in S[::2]:
...     for y in S[::2]:            # New objects on each iteration
...         print(x + y, end=' ')
aa ac ae ca cc ce ea ec ee
```

The two approaches differ in two ways. Each slice stores its whole result in memory at once. An iterable produces one value at a time, which can save space and startup time for large results. Slices also create new objects, so no single object is being scanned in several places.

To be closer to the class, slice the string once and then loop over the result. Now both loops walk the same object, each with its own iterator:

```text
>>> S = 'abcdef'
>>> S = S[::2]
>>> for x in S:
...     for y in S:                 # Same object, new iterators
...         print(x + y, end=' ')
aa ac ae ca cc ce ea ec ee
```

That is closer, but it still builds the slice in memory all at once. It also works only for this case of skipping every other item. User-defined iterables can do anything a class can do. A database object could support several cursors into the same query result, for example.

### Iteration with `__iter__` and `yield`

You can shorten a user-defined iterable by combining `__iter__` with the `yield` statement from Chapter 20. Any function that contains `yield` becomes a generator function. Calling it returns a generator object.

That object keeps its local scope and code position. It also has an automatic `__iter__` that returns itself and an automatic `__next__` that resumes the function.

```text
>>> def gen(x):
...     for i in range(x): yield i ** 2
>>> G = gen(5)
>>> G.__iter__() is G          # Both methods exist on the same object
True
>>> I = iter(G)                # Runs __iter__: generator returns itself
>>> next(I), next(I)           # Runs __next__
(0, 1)
>>> list(gen(5))               # Iteration tools run iter and next
[0, 1, 4, 9, 16]
```

The same holds when the generator function is a method named `__iter__`. Each call from an iteration tool returns a new generator with its own `__next__`. Generator methods also reach saved state in both instance attributes and local variables.

Example 30-4 is equivalent to the explicit `Squares` class of Example 30-2, and it is shorter. The loop you would have written by hand becomes a `for` statement inside the method.

```python
class Squares:                       # __iter__ + yield generator
    def __init__(self, start, stop): # __next__ is automatic/implied
        self.start = start
        self.stop = stop
    def __iter__(self):
        for value in range(self.start, self.stop + 1):
            yield value ** 2
```

```text
>>> from squares_yield import Squares
>>> for i in Squares(1, 5): print(i, end=' ')    # Runs __iter__, then __next__
1 4 9 16 25
>>> S = Squares(1, 5)                    # Runs __init__: class saves instance state
>>> I = iter(S)                          # Runs __iter__: returns a generator
>>> I
<generator object Squares.__iter__ at 0x109ecb3e0>
>>> next(I)                              # Runs generator's __next__
1
```

The generator method could have another name, such as `gen`. Then you would call it by hand, as in Example 30-5. Naming it `__iter__` skips that extra step, because iteration tools call `__iter__` for you.

```python
import squares_yield                 # Reuse prior example's __init__

class Squares(squares_yield.Squares):    # Non __iter__ equivalent
    def gen(self):
        for value in range(self.start, self.stop + 1):
            yield value ** 2
```

```text
>>> from squares_yield_manual import Squares
>>> for i in Squares(1, 5).gen(): print(i, end=' ')
1 4 9 16 25
```

Both forms create a new generator object for each iteration. With `__iter__`, iteration triggers the method, and the method returns a new generator. Without it, your code calls the method to make the generator, and the generator returns itself for `__iter__`.

The `yield` version is shorter, but it relies on two implicit mechanisms. Some readers find that too much magic, and they are not wrong to be cautious. The explicit `__next__` version is more general, and it sometimes fits a broader job. Know both, and choose the one that fits the task.

#### Multiple iterators with `yield`

The `__iter__` and `yield` combination also supports multiple active iterators automatically. Each call to `__iter__` is a new call to a generator function. That call returns a new generator with its own local scope. Two cursors, two positions, no shared state to manage.

```text
>>> from squares_yield import Squares
>>> S = Squares(1, 5)
>>> I = iter(S)
>>> next(I); next(I)
1
4
>>> K = iter(S)                # With yield, multiple iterators are automatic
>>> next(K)
1
>>> next(I)                    # I is independent of K: its own local state
9
```

Each `for` loop asks the class for a new generator. So nested loops over the same instance work, and the output below shows all nine pairs rather than a single row.

```text
>>> S = Squares(1, 3)
>>> for i in S:                # Each "for" calls __iter__
...     for j in S:
...         print(f'{i}:{j}', end=' ')
1:1 1:4 1:9 4:1 4:4 4:9 9:1 9:4 9:9
```

Without `yield`, the class needs a supplemental iterator class that stores the state by hand. Example 30-6 does this. It takes 15 lines, which is 8 more than the `yield` version. The extra lines are the price of making the state visible.

```python
class Squares:
    def __init__(self, start, stop):      # Non-yield generator
        self.start = start                # Multiscans: extra object
        self.stop = stop
    def __iter__(self):
        return SquaresIter(self.start, self.stop)

class SquaresIter:
    def __init__(self, start, stop):
        self.value = start - 1
        self.stop = stop
    def __next__(self):
        if self.value == self.stop:
            raise StopIteration
        self.value += 1
        return self.value ** 2
```

The explicit version works the same way, with more code. The generator-based approach can also simplify the skipper of Example 30-3. Example 30-7 does that in 9 lines, compared with 16 for the original, and it leaves out the self-test.

```python
class SkipObject:                        # Another __iter__ + yield generator
    def __init__(self, wrapped):         # Instance scope retained normally
        self.wrapped = wrapped           # Local scope state saved automatically
    def __iter__(self):
        offset = 0
        while offset < len(self.wrapped):
            item = self.wrapped[offset]
            offset += 2
            yield item
```

```text
>>> from skipper_yield import SkipObject
>>> skipper = SkipObject('abcdef')
>>> I = iter(skipper)
>>> next(I); next(I); next(I)
'a'
'c'
'e'
>>> for x in skipper:          # Each "for" calls __iter__: new automatic generator
...     for y in skipper:
...         print(x + y, end=' ')
aa ac ae ca cc ce ea ec ee
```

These examples are artificial, and comprehensions could replace them. Study the alternatives to see how they compare. The best tool for the job is the one that fits your job, and it is worth being able to write all three.

### Membership: `__contains__`, `__iter__`, and `__getitem__`

Membership tests are a good example of layered dispatch. Operator overloading is often layered. A class can provide a specific method, plus a more general fallback. Membership with `in` follows this pattern. It can use `__iter__`, or `__getitem__` as a fallback. A `__contains__` method is more specific, so Python prefers it over both.

The order is worth memorising: specific first, general second, oldest last. Python does the same thing with `__iter__` and `__getitem__` for loops.

For a mapping, `__contains__` should check keys, and it can use quick lookups. For a sequence, it should search the items.

Example 30-8 defines a class with all three methods. Each method prints a trace message, so you can see which one runs. This is a good habit when you are learning dispatch: let the code tell you what happened.

```python
def trace(msg, end=''):
    print(f'{msg} ', end=end)          # print sans newline

class Iters:
    def __init__(self, value):
        self.data = value
    def __getitem__(self, i):          # Fallback for iteration
        trace(f'@get[{i}]')            # Also for index, slice
        return self.data[i]
    def __iter__(self):                # Preferred for iteration
        trace('@iter')                 # Allows only one active iterator
        self.ix = 0
        return self
    def __next__(self):
        trace('@next')
        if self.ix == len(self.data): raise StopIteration
        item = self.data[self.ix]
        self.ix += 1
        return item
    def __contains__(self, x):         # Preferred for 'in' membership
        trace('@contains')
        return x in self.data

def self_test(Iters):
    X = Iters([1, 2, 3, 4])            # Make one instance
    tests = 'In', 'For', 'Comp', 'Map', 'Manual'
    for test in tests:
        trace(test.ljust(max(map(len, tests)) + 1))
        match test:
            case 'In':
                trace(3 in X)                    # Membership
            case 'For':
                for i in X:                      # for-loop iteration
                    trace(i, end='| ')
            case 'Comp':
                trace([i ** 2 for i in X])       # Other iteration tools
            case 'Map':
                trace(list(map(bin, X)))
            case 'Manual':
                I = iter(X)                      # Manual iteration
                while True:
                    try:
                        trace(next(I), end='| ')
                    except StopIteration:
                        break
        print()

if __name__ == '__main__': self_test(Iters)    # Test Iters here
```

This `__iter__` supports only one active scan at a time. Each attempt resets the cursor to the front, so nested loops fail. Example 30-9 uses `yield` to allow several active scans. It also saves five lines.

```python
from contains import *

class ItersYield(Iters):
    def __iter__(self):                # Preferred for iteration
        trace('@iter @next')           # Allows multiple active iterators
        for x in self.data:            # Implicit generator alternative
            yield x
            trace('@next')

if __name__ == '__main__': self_test(ItersYield)   # Test Iters here
```

With `__contains__` present, the output shows that `in` calls it, and the other tools call `__iter__`. The `__getitem__` method is never called. Read the trace labels in the output and match each one to a method.

```text
$ python3 contains.py
In @contains True
For @iter @next 1 | @next 2 | @next 3 | @next 4 | @next
Comp @iter @next @next @next @next @next [1, 4, 9, 16]
Map @iter @next @next @next @next @next ['0b1', '0b10', '0b11', '0b100']
Manual @iter @next 1 | @next 2 | @next 3 | @next 4 | @next
```

If you comment out `__contains__`, membership falls back to `__iter__`. The same test now walks the data instead of asking it directly:

```text
$ python3 contains.py
In @iter @next @next @next True
For @iter @next 1 | @next 2 | @next 3 | @next 4 | @next
```

If you comment out both `__contains__` and `__iter__`, Python uses `__getitem__` with successively higher indexes. It stops when `IndexError` is raised. Three layers of fallback, and the trace shows which layer answered.

```text
$ python3 contains.py
In @get[0] @get[1] @get[2] True
For @get[0] 1 | @get[1] 2 | @get[2] 3 | @get[3] 4 | @get[4]
```

The `__getitem__` method also handles explicit indexing and slicing. Slice expressions call it with a slice object. The following output comes from the class with `__iter__` disabled, so every request lands on the indexing hook.

```text
>>> from contains import Iters
>>> X = Iters('hack')
>>> X[0]                       # Indexing: __getitem__(0)
@get[0] 'h'
>>> X[1:]                      # Slicing: __getitem__(slice(...))
@get[slice(1, None, None)] 'ack'
>>> list(X)
@get[0] @get[1] @get[2] @get[3] @get[4] ['h', 'a', 'c', 'k']
```

For sequence-oriented classes, `__getitem__` works well. In other iteration cases, `__iter__` is often easier to write. It does not need to manage an integer index. A `__contains__` method also lets membership tests run faster when that matters.

### Attribute access: `__getattr__` and `__setattr__`

Attribute access is another operation a class can take over. Classes can intercept attribute access too. For an object, `object.attribute` can be implemented by your code. That covers reference, assignment, and deletion. Chapter 28 showed a small rerouting example. This section covers the topic in more detail.

#### Attribute reference

The `__getattr__` method intercepts attribute references. Python calls it with the attribute name as a string. It runs only when the name is not found through the normal inheritance search. That last clause matters: this hook is the last resort, not the first stop.

`__getattr__` is useful as a generic hook for attribute requests. Delegation is one common use. A controller object can forward requests to an embedded object. The method can also adapt a class to an interface or add accessors after the fact.

```text
>>> class Empty:
...     def __getattr__(self, attrname):       # On self.undefined
...         if attrname == 'age':
...             return 40
...         else:
...             raise AttributeError(attrname)
>>> X = Empty()
>>> X.age                       # Becomes X.__getattr__('age')
40
>>> X.name                      # Unsupported attribute
AttributeError: name
```

Here, `Empty` has no real attributes. The lookup for `X.age` reaches `__getattr__`, and `attrname` holds the string `'age'`. The method returns a computed value, so `age` behaves like a real attribute. For names it does not handle, the method raises `AttributeError`, which is what a missing attribute should raise.

#### Attribute assignment and deletion

The `__setattr__` method intercepts all attribute assignments. Once it is defined, `self.attr = value` becomes a call to `self.__setattr__('attr', value)`. You can then validate or transform the value.

This method is tricky, and the trap is easy to fall into. Any assignment to a `self` attribute inside `__setattr__` calls `__setattr__` again. That causes infinite recursion and a stack overflow. The rule applies to every `self` assignment in the class, even in other methods.

To avoid the loop, assign through the instance dictionary. Writing to `self.__dict__` does not trigger the method, because the hook watches attribute assignment and not dictionary keys.

```text
>>> class Accesscontrol:
...     def __setattr__(self, attr, value):
...         if attr == 'age':
...             self.__dict__[attr] = value + 10     # Not self.name=val or setattr
...         else:
...             raise AttributeError(attr + ' not allowed')
>>> X = Accesscontrol()
>>> X.age = 40                  # Becomes X.__setattr__('age', 40)
>>> X.age                       # Found in __dict__ as usual
50
>>> X.name = 'Pat'              # Unsupported attribute
AttributeError: name not allowed
```

If you write `self.age = value + 10` or `setattr(self, attr, value + 10)` inside the method, the call loops. Assigning any other `self` attribute recurs too. In this class, that recursion ends with the `AttributeError` instead of a loop, which is luck rather than design.

A call to the superclass avoids the loop as well. Calling `object.__setattr__(self, attr, value + 10)` works. The `super().__setattr__(...)` form works too. Some classes need this approach, though it is uncommon.

The `__delattr__` method handles deletions, as in `del object.attr`. It also needs to avoid loops. It should delete through `__dict__` or route the call to a superclass.

Attributes created with slots or properties are not stored in the instance `__dict__`. For those virtual attributes, `__setattr__` may need the `object.__setattr__` form instead of `__dict__` indexing. Chapter 32 and Chapter 38 cover those tools.

#### Other attribute-management tools

The three methods above control attribute access in specialized ways. Python offers other tools as well, each with a narrower job.

- The `__getattribute__` method intercepts all attribute fetches, not only undefined ones. It must avoid loops too, usually by rerouting to `object`.
- The `property` built-in associates methods with fetch and set operations for one class attribute. It cannot catch all accesses, but it can define what some of them do.
- Descriptors use `__get__` and `__set__` methods for a specific attribute. They are as focused as `property`, and Python uses them to implement it.
- Slots declare attributes in a class and create implicit storage in each instance. Generic tools may need special handling for them.

Chapter 32 covers these tools in more detail, and Chapter 38 covers descriptors. For now, remember that they all intercept access and all carry the same risk of loops.

#### Emulating privacy for instance attributes

Attribute tools can also emulate privacy. Example 30-10, `private0.py`, lets each subclass keep its own list of private names. Those names cannot be assigned on its instances.

```python
class Privacy:
    def __setattr__(self, attr, value):          # On self.attr = value
        if attr in self.privates:
            raise NameError(f'{attr!r} for {self}')
        else:
            self.__dict__[attr] = value          # Avoid loops by using dict key

class Test1(Privacy):
    privates = ['age']

class Test2(Privacy):
    privates = ['name', 'pay']
    def __init__(self):
        self.__dict__['name'] = 'Pat'            # To do better, see Chapter 39

if __name__ == '__main__':
    x = Test1()
    x.name = 'Sue'                               # Works
    print(x.name)
    #x.age = 40                                  # Fails
    y = Test2()
    y.age = 30                                   # Works
    print(y.age)
    #y.name = 'Bob'                              # Fails
```

This is a first-cut solution. It blocks changes to attribute names outside a class. It is also clumsy, because the constructor must use `__dict__` to avoid triggering `__setattr__`. A more complete approach needs a proxy class and a `__getattr__` method. Chapter 39 shows a fuller version using class decorators.

Python programmers rarely emulate privacy this way in practice. They write large frameworks without private declarations. Catching attribute references and assignments is still a useful technique. It supports delegation, where a controller wraps embedded objects and routes operations to them.

### String representation: `__repr__` and `__str__`

Display formats matter for objects, because the default display of an instance is not useful. The following `adder` class has `__init__` and `__add__` but no display method, and the output shows the cost.

```text
>>> class adder:
...     def __init__(self, value=0):
...         self.data = value                # Initialize data
...     def __add__(self, other):
...         self.data += other               # Add other in place
>>> x = adder()
>>> print(x)                                 # str or else repr
<__main__.adder object at 0x106110c80>
>>> x                                        # repr
<__main__.adder object at 0x106110c80>
```

A subclass can add a `__repr__` method. The subclass inherits `__init__` and `__add__`.

```text
>>> class addrepr(adder):
...     def __repr__(self):                  # Add string representation
...         return f'addrepr({self.data})'   # Convert to as-code string
>>> x = addrepr(2)
>>> x + 1
>>> x                                        # Runs __repr__
addrepr(3)
>>> print(x)                                 # Runs __repr__
addrepr(3)
>>> str(x), repr(x)
('addrepr(3)', 'addrepr(3)')
```

Python calls `__repr__` automatically when an instance is printed or converted to a string. The method can turn `self.data` into a friendlier string. The form with parentheses around the value is a convention: it looks like the code that would build the object.

#### Why two display methods?

Python has two display methods because they serve different audiences. `__str__` is tried first by `print` and by the `str` built-in. It should return a user-friendly display, something you would show to an end user.

`__repr__` serves every other context. That includes interactive echoes, the `repr` function, and nested appearances. It is also the fallback for `print` and `str` when `__str__` is missing. It should return an as-code string that could re-create the object, or a detailed display for developers.

Coding `__repr__` alone gives one display for every context. Coding `__str__` alone gives a display only for `print` and `str`. The reverse is not true. Interactive echoes use `__repr__` and never try `__str__`. If you only write one method, write `__repr__`.

```text
>>> class addstr(adder):
...     def __str__(self):                   # __str__ but no __repr__
...         return f'[Value: {self.data}]'   # Convert to nice string
>>> x = addstr(3)
>>> x + 1
>>> x                                        # Default __repr__ (in object)
<__main__.addstr object at 0x106111b20>
>>> print(x)                                 # Runs __str__ (in addstr)
[Value: 4]
>>> str(x), repr(x)
('[Value: 4]', '<__main__.addstr object at 0x106111b20>')
```

Defining both methods gives a different display in each context. A class can show a friendly view with `__str__` and a developer view with `__repr__`. The output below compares them side by side.

```text
>>> class addboth(adder):
...     def __str__(self):
...         return f'[Value: {self.data}]'   # User-friendly string
...     def __repr__(self):
...         return f'addboth({self.data})'   # As-code string
>>> x = addboth(4)
>>> x + 1
>>> x                                        # Runs __repr__
addboth(5)
>>> print(x)                                 # Runs __str__
[Value: 5]
>>> str(x), repr(x)
('[Value: 5]', 'addboth(5)')
```

The string-formatting tools in Chapter 7 also call these methods. The `!s` and `!r` conversions use `str` and `repr`, as does `%r` with the `%` operator. So the choice you make here reaches every formatting style in the language.

```text
>>> f'{x!s} {x!r}', '{!s} {!r}'.format(x, x), '%s %r' % (x, x)
('[Value: 5] addboth(5)', '[Value: 5] addboth(5)', '[Value: 5] addboth(5)')
```

When you choose, use `__str__` for high-level displays and `__repr__` for low-level, all-inclusive ones. A general tool that codes `__str__` leaves clients room to add a `__repr__` later.

#### Display usage notes

Three points matter when you write display methods. First, both methods must return strings. Other result types are not converted, and they raise errors. Run the value through `str` or an f-string if needed.

Second, a container may ignore `__str__` for the objects it holds. The friendly display may apply only at the top level of a `print`. Objects nested inside a list still show their `__repr__` or the default, which surprises people the first time it happens.

```text
>>> class Printer:
...     def __init__(self, val):
...         self.val = val
...     def __str__(self):                   # Used for instance itself
...         return str(self.val)
>>> objs = [Printer(2), Printer(3)]
>>> for x in objs: print(x)                  # __str__ runs when instance printed
2
3
>>> print(objs)                              # But not when instance is in a list
[<__main__.Printer object at 0x106110c80>, <__main__.Printer object at 0x1060d2570>]
```

To make a custom display appear everywhere, code `__repr__` instead. It runs in every case where `__str__` does not apply, including nested appearances.

Third, display methods can cause infinite recursion in rare cases. An object's display may include the display of another object. If that display leads back to the first object, the calls loop. Chapter 31 shows an example of this looping risk.

`__str__` and `__repr__` are among the most used operator-overloading methods, after `__init__`. Whenever an object prints as a custom display, one of them is usually at work.

### Right-side and in-place operators: `__radd__` and `__iadd__`

Binary operator methods such as `__add__` and `__sub__` have variants. Each binary operator can have a left, right, and in-place version. Python applies defaults if you skip some of them. The roles your objects play decide how many you need, so it helps to see what each one covers.

#### Right-side addition

The `__add__` method does not handle an instance on the right side of `+`. This class shows the problem, and the error message names both operand types.

```text
>>> class Adder:
...     def __init__(self, value=0):
...         self.data = value
...     def __add__(self, other):
...         return self.data + other
>>> x = Adder(5)
>>> x + 2
7
>>> 2 + x
TypeError: unsupported operand type(s) for +: 'int' and 'Adder'
```

The `__radd__` method supports that case. Python calls it only when your instance is on the right side, and the left operand is not an instance of your class. In all other cases, the left operand's `__add__` runs. The r in the name stands for reflected, meaning the operands are handled in the other order.

```python
class Commuter1:
    def __init__(self, val):
        self.val = val
    def __add__(self, other):
        print('add', self.val, other)
        return self.val + other
    def __radd__(self, other):
        print('radd', self.val, other)
        return other + self.val
```

```text
>>> from commuter import Commuter1
>>> x = Commuter1(88)
>>> y = Commuter1(99)
>>> x + 1                      # __add__: instance + noninstance
add 88 1
89
>>> 1 + y                      # __radd__: noninstance + instance
radd 99 1
100
>>> x + y                      # __add__: instance + instance => triggers __radd__
add 88 <commuter.Commuter1 object at 0x1011b63f0>
radd 99 88
187
```

In `__radd__`, `self` sits on the right side of the `+`, and `other` sits on the left. When two instances are added, `__add__` runs first. It then triggers `__radd__` by simplifying its left operand and adding again. The trace lines in the output show both calls.

Sometimes one method can serve both sides. For a truly commutative operation, `__radd__` can call `__add__` directly. It can also swap the order and add again. The third option is an alias at class level, as in `__radd__ = __add__`.

That last form saves one extra call, so it may run faster. In every case, the right-side instance triggers the shared `__add__` method.

#### Propagating the class type

Results may need to keep the class type. Without a type test, adding two instances can nest one object inside another. The `isinstance` test in the following class prevents that. It checks the other operand and unwraps it before doing the arithmetic.

```python
class Commuter5:                              # Propagate class type in results
    def __init__(self, val):
        self.val = val
    def __add__(self, other):
        if isinstance(other, Commuter5):      # Type test to avoid object nesting
            other = other.val
        return Commuter5(self.val + other)    # Else + result is another Commuter
    def __radd__(self, other):
        return Commuter5(other + self.val)
    def __repr__(self):
        return f'Commuter5({self.val})'
```

```text
>>> from commuter import Commuter5
>>> x = Commuter5(88)
>>> y = Commuter5(99)
>>> z = x + y                  # Not nested: doesn't recur to __radd__
>>> z
Commuter5(187)
>>> z + 10
Commuter5(197)
>>> z + z + 1
Commuter5(375)
```

Without the `isinstance` test, the results nest objects. The math stays correct, but the code makes pointless recursive calls and extra constructor calls. The printed value grows parentheses until it becomes unreadable.

```text
>>> z = x + y                  # With isinstance test commented out
>>> z
Commuter5(Commuter5(187))
>>> z + z
Commuter5(Commuter5(Commuter5(Commuter5(374))))
```

Another option is to test and simplify in the constructor. The following class does that, and it behaves the same as `Commuter5`. Only the location of the check changes.

```python
class Commuter6:                              # Propagate class type in results
    def __init__(self, val):
        if isinstance(val, Commuter6):        # Type test to avoid object nesting
            self.val = val.val
        else:
            self.val = val
    def __add__(self, other):
        return Commuter6(self.val + other)
    def __radd__(self, other):
        return Commuter6(other + self.val)
    def __repr__(self):
        return f'Commuter6({self.val})'
```

Classes are first-class objects, so you can place them in a tuple and loop over them. Aliasing `__radd__` to `__add__` in `Commuter5` or `Commuter6` saves a line. It does not prevent nesting without the `isinstance` tests. Python's manuals describe other options. For example, a class can return `NotImplemented` for an unsupported operand. That differs from the `NotImplementedError` exception, and the missing `Error` is not a typo.

#### In-place addition

To support `+=`, code either `__iadd__` or `__add__`. Python uses `__add__` when `__iadd__` is absent, and it assigns the result to the name. So the `Commuter` classes already support `+=`, without a line of extra code.

The `__iadd__` method allows a faster in-place change where it applies. Its return value is assigned to the target on the left of `+=`. Usually it returns `self`. Otherwise `None` is returned and assigned, which silently loses the object, so always return `self` unless you mean something else.

```text
>>> class Number:
...     def __init__(self, val):
...         self.val = val
...     def __iadd__(self, other):            # __iadd__ explicit: x += y
...         self.val += other
...         return self
>>> x = Number(5)
>>> x += 1
>>> x += 1
>>> x.val
7
```

For mutable objects, `__iadd__` can make a quicker in-place change. The list case below grows in place rather than building a new object:

```text
>>> y = Number([1])
>>> y += [2]                   # In-place change faster than +
>>> y += [3]
>>> y.val
[1, 2, 3]
```

Without `__iadd__`, the normal `__add__` runs as a fallback. It may not optimize in-place cases. The result is correct, and only the efficiency differs.

```text
>>> class Number:
...     def __init__(self, val):
...         self.val = val
...     def __add__(self, other):             # __add__ fallback: x = (x + y)
...         return Number(self.val + other)   # Propagates class type
>>> x = Number(5)
>>> x += 1
>>> x += 1
>>> x.val
7
```

Every binary operator has right-side and in-place variants that work the same way, such as `__mul__`, `__rmul__`, and `__imul__`. These methods are uncommon. Code the right-side version when the object must appear on either side. Code the in-place version for code economy or speed, and only if you need the operator at all. A `Vector` class may use these tools, but a `Button` class probably would not.

### Call expressions: `__call__`

The `__call__` method runs when your instance is called like a function. Python passes along any positional or keyword arguments. That lets an instance follow a function-based API, which matters when an existing library expects to call something.

```text
>>> class Callee:
...     def __call__(self, *pargs, **kargs):      # Intercept instance calls
...         print(f'Called: {pargs=} {kargs=}')    # Accept arbitrary arguments
>>> C = Callee()
>>> C(1, 2, 3)                # C is a "callable" object
Called: pargs=(1, 2, 3) kargs={}
>>> C(1, 2, 3, x=4, y=5)
Called: pargs=(1, 2, 3) kargs={'x': 4, 'y': 5}
```

The `__call__` method accepts every argument-passing mode from Chapter 18. The instance is passed as `self`, and the rest of the arguments follow the usual rules. These definitions all match the same calls, so the choice is about what the method does with them:

```python
class C:
    def __call__(self, a, b, c=5, d=6): ...          # Normals and defaults

class C:
    def __call__(self, *pargs, **kargs): ...         # Collect arbitrary arguments

class C:
    def __call__(self, *pargs, d=6, **kargs): ...    # Keyword-only argument (Python 3)
```

```text
X = C()
X(1, 2)                       # Omit defaults
X(1, 2, 3, 4)                 # Positionals
X(a=1, b=2, d=4)              # Keywords
X(*[1, 2], **dict(c=3, d=4))  # Unpack arbitrary arguments
X(1, *(2,), c=3, **dict(d=4)) # Mixed modes
```

A class with `__call__` supports the same argument syntax and behavior as a function. An instance can also keep state for each call. The next example stores a value once, and each call uses it.

```text
>>> class Prod:
...     def __init__(self, value):          # Accept just one argument
...         self.value = value
...     def __call__(self, other):
...         return self.value * other
>>> x = Prod(2)                             # Remembers 2 in state
>>> x(3)                                    # 3 (passed) * 2 (state)
6
>>> x(4)
8
```

A plain method could do the same job. The `__call__` method matters when a library expects a function. The instance can then match that call interface while keeping state and inheriting from classes.

#### Function interfaces and callback-based code

Python's `tkinter` GUI module lets you register functions as event handlers, also called callbacks. When an event occurs, `tkinter` calls the registered object. An instance with `__call__` can serve as a handler that keeps state between events. A closure from Chapter 17 can do similar work, but it supports less customization.

The following class remembers the color a button should use when pressed. The color is state, and the call is the event:

```python
class Callback:
    def __init__(self, color):             # Function + state information
        self.color = color
    def __call__(self):                    # Support calls with no arguments
        print('turn', self.color)
```

```python
cb1 = Callback('blue')                     # Remember blue
cb2 = Callback('green')                    # Remember green
B1 = Button(command=cb1)                   # Register handlers
B2 = Button(command=cb2)
```

When the button is pressed, the GUI calls the instance like a plain function with no arguments. The instance remembers its state, so it acts as a stateful function object. Some programmers consider this the cleanest way to keep state in Python, because the state is explicit in attributes.

Other techniques also keep state. These include closures with `nonlocal`, default arguments in a `lambda`, and bound methods. All three appear below, so you can compare them with the class version.

```python
def callback(color):                       # Enclosing scope versus attrs
    def oncall():
        print('turn', color)
    return oncall

cb3 = callback('yellow')                   # Handler to be registered
cb3()                                      # On event: prints 'turn yellow'
```

```python
cb4 = (lambda color='red':                 # Defaults retain state too
       print('turn', color))
cb4()                                      # On event: prints 'turn red'
```

A bound method is created when you reference an instance method without calling it. It remembers both the instance and the function. Chapter 31 covers bound methods in more depth, and Chapter 39 revisits the trade-offs between these techniques.

```python
class Callback:
    def __init__(self, color):             # Class with state information
        self.color = color
    def changeColor(self):                 # A normally named method
        print('turn', self.color)

cb1 = Callback('blue')
cb2 = Callback('yellow')
B1 = Button(command=cb1.changeColor)       # Bound method: reference, not call
B2 = Button(command=cb2.changeColor)       # Remembers instance + function pair
```

When the button is pressed, the GUI behaves as if it ran the bound method. The method processes the state of its own instance, and no arguments cross the boundary.

```python
cb1 = Callback('blue')
cmd = cb1.changeColor                      # Registered event handler
cmd()                                      # On event: prints 'turn blue'
```

A `lambda` is needed only when you must pass extra arguments. A bound method reference already defers the call. This approach does not need `__call__`, and either scheme may suit a given program.

Chapter 32 uses `__call__` to build a function decorator, a callable object that adds logic around a function. Because `__call__` attaches state to a callable object, it fits that job well. Chapters 39 and 40 show more `__call__` examples.

### Comparisons: `__lt__`, `__gt__`, and others

Classes can catch all six comparison operators: `<`, `>`, `<=`, `>=`, `==`, and `!=`. Keep three qualifications in mind, because comparisons behave differently from arithmetic in a few ways.

Comparison methods have no right-side variants. When only one operand supports comparison, Python uses a reflected method. For example, `__lt__` and `__gt__` reflect each other, so one of them can cover both operand orders.

The comparison operators do not imply one another. A true `==` does not make `!=` false. So define both `__eq__` and `__ne__` when both operators must behave correctly.

The following class prints a trace for each comparison, so you can see which method runs. Watch the reflected calls in the second block: the same methods answer, with the operands swapped.

```text
>>> class Vetter:
...     data = 'hack'
...     def __gt__(self, other):
...         print(f'gt: {self=} {other=}')
...         return self.data > other
...     def __lt__(self, other):
...         print(f'lt: {self=} {other=}')
...         return self.data < other
>>> X = Vetter()
>>> X > 'code', X < 'code'
gt: self=<__main__.Vetter object at 0x10898f650> other='code'
lt: self=<__main__.Vetter object at 0x10898f650> other='code'
(True, False)
>>> 'code' < X, 'code' > X
gt: self=<__main__.Vetter object at 0x10898f650> other='code'
lt: self=<__main__.Vetter object at 0x10898f650> other='code'
(True, False)
```

The `__lt__` method also drives sorting. Both the list `sort` method and the `sorted` built-in use it, so one small method gives your objects a place in any ordered sequence.

```text
>>> class Order:
...     def __init__(self, data):
...         self.data = data
...     def __lt__(self, other):
...         return self.data < other.data
...     def __repr__(self):
...         return f'Order({self.data})'
>>> sorted(Order(i) for i in [3, 1, 4, 2])
[Order(1), Order(2), Order(3), Order(4)]
```

Python's manuals cover the rest of this area. The `__eq__` method for equality is paired with `__hash__` for keys and sets. Comparison methods can also return `NotImplemented` for unsupported arguments. That is a different object from `NotImplementedError`, and mixing them up is a common mistake.

### Boolean tests: `__bool__` and `__len__`

Truth tests run constantly in Python, so a class should say what it means. Every object is true or false in Boolean contexts. Your class decides what that means for its instances. Python first tries `__bool__` to get a direct True or False value. If that method is missing, Python tries `__len__`. A length of zero means false, and any other length means true.

This matters in ordinary code, because every `if` and `while` asks the question. An empty container is false, and so is an object that reports a zero length.

```text
>>> class Truth:
...     def __bool__(self): return True
>>> X = Truth()
>>> if X: print('yes!')
yes!
>>> class Truth:
...     def __bool__(self): return False
>>> X = Truth()
>>> bool(X)
False
```

Without `__bool__`, Python falls back on the length. A zero length means false, just as it does for built-in objects. The example below gets the whole rule from a single line.

```text
>>> class Truth:
...     def __len__(self): return 0          # Empty means false too
>>> X = Truth()
>>> if not X: print('no!')
no!
```

If both methods exist, Python prefers `__bool__` because it is more specific. The specific hook always wins over the general one.

```text
>>> class Truth:
...     def __bool__(self): return True      # Preferred over length
...     def __len__(self): return 0          # Object length: fallback
>>> if Truth(): print('yes!')
yes!
```

If neither method exists, the object is considered true. This is the default, and it catches people out when they expect an empty-looking object to be false.

```text
>>> class Truth:
...     pass
>>> X = Truth()
>>> bool(X)
True
```

### Object destruction: `__del__`

The `__init__` method runs when an instance is created. Its counterpart is the destructor, also called the finalizer. Python runs `__del__` when the instance's space is reclaimed during garbage collection.

```text
>>> class Life:
...     def __init__(self, name):
...         print('Hello', name)
...         self.name = name
...     def live(self):
...         print(self.name + '...')
...     def __del__(self):
...         print('Goodbye', self.name)
>>> pat = Life('Pat')
Hello Pat
>>> pat.live()
Pat...
>>> pat = 'end'
Goodbye Pat
```

Here, assigning a string to `pat` removes the last reference to the instance. That triggers the destructor. Destructors can handle cleanup, such as closing a server connection. Still, Python programmers use them less often than programmers in some other languages do, for reasons that follow.

#### Destructor usage notes

The destructor works as documented, but it has caveats that make it rare in Python code. Read these before you put real cleanup work in one.

Destructors are less necessary in Python than in some other languages. Python reclaims the memory an instance holds, so you do not need a destructor for space management. CPython also closes file objects when they are reclaimed. Chapter 9 explains that closing files yourself is still a good habit, because this behavior can vary between Python implementations.

You also cannot always predict when an instance will be reclaimed. System tables may hold lingering references that stop the destructor from running on time. Python also does not guarantee that destructors run for objects still alive when the interpreter exits.

An exception raised inside `__del__` does not reach your program. Python prints a warning to `sys.stderr` instead. The garbage collector runs the method in an unpredictable context, so there is no clear place to deliver the error.

Cyclic references are another problem. Objects that refer to each other may not be collected when you expect. An optional cycle detector is enabled by default, and it collects such objects eventually. That includes objects with `__del__` methods, as of Python 3.4. The `gc` module and Python's manuals cover the details.

For these reasons, put cleanup in an explicitly called method, such as `shutdown`. The `try`/`finally` statement and the `with` statement also support cleanup. Chapter 34 covers the `with` statement and its context managers.

### Operator overloading summary

The remaining overloading methods follow the same shape as the ones above. Each one is a hook that intercepts a built-in operation. Some have unusual argument lists or return values, but the usage pattern is the same.

Later chapters use several more of these methods. Chapter 34 uses `__enter__` and `__exit__` in `with` statement context managers. Chapter 38 uses the `__get__` and `__set__` descriptor methods. Chapter 40 uses `__new__` in the context of metaclasses. Methods such as `__call__` and `__str__` appear in later examples as well.

Provide operator overloading when a class naturally matches a built-in type's interface, or needs to emulate one. A collection might imitate a sequence or a mapping. A callable object might serve an API that expects a function. Avoid overloading expression operators that do not map naturally to your objects. A normally named method is clearer in those cases, and a reader will thank you.

## Designing with classes

Up to now we have used the `class` statement as a tool. This section asks a different question: how do we use classes to model useful objects? Design means choosing which classes to write, how they relate, and which parts stay hidden.

The patterns here are inheritance, composition, delegation, and factories. Along the way we also meet pseudoprivate attributes, multiple inheritance, bound methods, and the method resolution order, or MRO, that multiple inheritance depends on.

### Python and OOP

Python's object-oriented model rests on three ideas. Each one is simple on its own. Together they explain most of the design choices in this section, so it is worth naming them plainly before the examples start.

- Inheritance: attribute lookup. The expression `X.name` searches the instance, its class, and then its superclasses.
- Polymorphism: in `X.method`, the meaning of `method` depends on the class of the subject object `X`.
- Encapsulation: methods and operators implement behavior, while data hiding is a convention by default.

We already know the mechanics of inheritance, so we treat it as a given. It is the mechanism behind flexible code customization, and the other two ideas depend on it.

Polymorphism comes from the fact that Python has no type declarations. Attributes are resolved at runtime. Objects that implement the same interface can therefore replace each other. The code that calls a method does not need to know which kind of object implements it, only that the method exists.

Encapsulation in Python means packaging. It means hiding implementation details behind an object's interface. It does not mean enforced privacy, although code can enforce some privacy in part, as Chapter 39 shows. Encapsulation still helps. It lets you change how an object works without affecting the code that uses it.

#### Polymorphism means interfaces, not call signatures

Polymorphism means something different in Python than in languages with overloading. Some languages define polymorphism as overloading. In those languages, a function is chosen by the types or the number of its arguments. Python has no such overloading, because it does not check types in declarations. Polymorphism in Python is based on object interfaces.

If you miss overloading from another language, you might try to write it this way. It looks reasonable, and it does not do what you expect.

```python
class C:
    def meth(self, x):
        ...
    def meth(self, x, y, z):
        ...
```

This code runs without an error. The second `def` simply assigns a new function object to the name `meth` in the class scope. The last definition is the only one kept. It works like assigning `X = 1` and then `X = 2`. The value of `X` ends up as `2`, and the first value is gone without complaint.

A class can have only one definition for each method name. The rule also covers `__init__`, which is special only because Python calls it automatically.

If you truly need dispatch by call signature, you can branch on the arguments. You can test the number of arguments, or their types, with the tools from Chapters 4, 9, and 18.

```python
class C:
    def meth(self, *args):
        if len(args) == 1:  # Branch on number of arguments
            ...
        elif type(args[0]) == int:  # Branch on argument types (or use isinstance())
            ...
```

You normally should not write code like this. It is not the Python way. Write your code to expect an object interface, not a specific type. That way the code works with more kinds of objects, now and later, including the ones you have not written yet.

```python
class C:
    def meth(self, x):
        x.operation()  # Assume x does the right thing
```

Distinct operations should also get distinct method names. This advice holds in every language. Names are clearer than call signatures, and a good name saves a comment.

Python's object model is simple. Much of the skill in OOP lies in how you combine classes to reach a program's goals. The next sections tour some of the ways larger programs use classes.

### Inheritance: the is-a relationship

Inheritance has two faces, one for programmers and one for designers. It also models the real world. From a programmer's point of view, it begins with attribute qualification. From a designer's point of view, inheritance specifies set membership. A class defines a set of properties. More specific sets, the subclasses, inherit those properties and customize them.

Imagine that we open a pizza restaurant. We need employees to serve customers and prepare food. We decide to build a robot to make the pizzas. We also want the robot to be a full employee with a salary, which is where the design gets interesting.

The classes in the next example model this team. It is a small story, and every relationship in it is an "is-a" link you can name out loud.

The most general class is `Employee`. It is a takeoff on the demo from Chapter 28. It provides common behavior, such as raising a salary with `giveRaise` and printing with `__repr__`. There are two kinds of employees, so there are two subclasses: `Chef` and `Server`. Both override the inherited `work` method with more specific messages. The `PizzaRobot` class is a kind of `Chef`. In OOP terms, these are "is-a" links: a robot is a chef, and a chef is an employee.

File `employees.py`

```python
class Employee:
    def __init__(self, name, salary=0):
        self.name = name
        self.salary = salary
    def giveRaise(self, percent):
        self.salary += self.salary * percent
    def work(self):
        print(self.name, 'does stuff')
    def __repr__(self):
        return (f'<{self.__class__.__name__}: '
                f'name="{self.name}", salary={self.salary:,.2f}>')
class Chef(Employee):
    def __init__(self, name):
        Employee.__init__(self, name, 50000)
    def work(self):
        print(self.name, 'makes food')
class Server(Employee):
    def __init__(self, name):
        Employee.__init__(self, name, 40000)
    def work(self):
        print(self.name, 'interfaces with customer')
class PizzaRobot(Chef):
    def __init__(self, name):
        Chef.__init__(self, name)
    def work(self):
        print(self.name, 'makes pizza')
if __name__ == '__main__':
    pat = PizzaRobot('pat')  # Make a robot named pat
    print(pat)  # Run inherited __repr__
    pat.work()  # Run type-specific action
    pat.giveRaise(0.20)  # Give pat a 20% raise
    print(pat); print()
    for klass in Employee, Chef, Server, PizzaRobot:
        object = klass(klass.__name__)
        object.work()
```

When we run the self-test, we create a pizza robot named `pat`. The robot inherits names from three classes: `PizzaRobot`, `Chef`, and `Employee`. Printing `pat` and giving the robot a raise run the `__repr__` and `giveRaise` methods from `Employee`, two levels up. The inheritance search finds them there, and nothing in `PizzaRobot` mentions them.

```text
$ python3 employees.py
<PizzaRobot: name="pat", salary=50,000.00>
pat makes pizza
<PizzaRobot: name="pat", salary=60,000.00>
Employee does stuff
Chef makes food
Server interfaces with customer
PizzaRobot makes pizza
```

In a hierarchy like this, you can usually make instances of any class, not only the bottom ones. The `for` loop creates one instance of each of the four classes. Each one responds differently when asked to work, because `work` differs in each class. The robot `pat` gets `work` from the lowest class, `PizzaRobot`.

These classes only simulate real objects. The `work` method prints a message for now. It could later control real devices, such as serial ports, Arduino boards, or a Raspberry Pi, without changing the shape of the hierarchy.

**Note.** This example calls superclass constructors by naming the class, as in `Employee.__init__(self, name, 50000)`. The `super().__init__(...)` form does the same job in single-inheritance trees, and it avoids passing `self`. It becomes harder to read in multiple inheritance. Chapter 32 introduces `super`. The examples package also includes an alternative version, `employees-super.py`, if you want to see that form now.

### Composition: the has-a relationship

Composition answers a different question: what is this thing made of? Composition is the second design tool. From a programmer's point of view, it means embedding other objects inside a container object. The container activates those objects to carry out its own methods. From a designer's point of view, composition describes parts of a whole. Where inheritance means set membership, composition means "has-a" relationships.

Some design texts separate composition from aggregation. Aggregation describes a weaker tie between container and contained parts. In this book, "composition" simply means a collection of embedded objects. The composite class usually offers its own interface, and it implements that interface by directing the parts.

Our pizza shop is a composite. It has an oven, and it has employees such as servers and chefs. When a customer places an order, the parts of the shop take action. The server takes the order, the chef makes the pizza, and the oven bakes it. The next example simulates this scene.

File `pizzashop.py`

```python
from employees import PizzaRobot, Server  # From Example 31-1
class Customer:
    def __init__(self, name):
        self.name = name
    def order(self, server):
        print(self.name, 'orders from', server)
    def pay(self, server):
        print(self.name, 'pays for item to', server)
class Oven:
    def bake(self):
        print('oven bakes')
class PizzaShop:
    def __init__(self):
        self.server = Server('Jan')  # Embed other objects
        self.chef = PizzaRobot('Pat')  # A robot named Pat
        self.oven = Oven()
    def order(self, name):
        customer = Customer(name)  # Activate other objects
        customer.order(self.server)  # Customer orders from server
        self.chef.work()
        self.oven.bake()
        customer.pay(self.server)
if __name__ == '__main__':
    scene = PizzaShop()  # Make the composite
    scene.order('Sue')  # Simulate Sue's order
    print('...')
    scene.order('Bob')  # Simulate Bob's order
```

The `PizzaShop` class is a container and a controller. Its constructor creates and embeds instances of the employee classes from the last section. It also embeds an `Oven` object, which this module defines. When the self-test calls `order`, the embedded objects take their turns.

We create a new `Customer` for each order. We pass the embedded `Server` object into the customer's methods. Customers come and go, but the server remains part of the shop. Employees still take part in inheritance here too. Composition and inheritance are complementary tools, and most real designs use both.

The shop handles two orders, one from Sue and one from Bob. The overlap of orders with coroutines from Chapter 20 is outside the scope of this example.

```text
$ python3 pizzashop.py
Sue orders from <Server: name="Jan", salary=40,000.00>
Pat makes pizza
oven bakes
Sue pays for item to <Server: name="Jan", salary=40,000.00>
...
Bob orders from <Server: name="Jan", salary=40,000.00>
Pat makes pizza
oven bakes
Bob pays for item to <Server: name="Jan", salary=40,000.00>
```

This is a toy simulation, but its objects and interactions show how composites work. A useful rule of thumb follows. Classes can represent almost any object or relationship you can describe in a sentence. Replace the nouns with classes, such as `Oven`, and the verbs with methods, such as `bake`. The result is a first draft of a design.

#### Stream processors revisited

A composition example that is more concrete than pizza robots comes from the stream processor in Chapter 26. Here is that generic function again, so the class version has something to improve on.

```python
def processor(reader, converter, writer):
    while True:
        data = reader.read()
        if not data: break
        data = converter(data)
        writer.write(data)
```

For more structure and support for inheritance, we can write this as a class. The class uses composition to do its work. The `streams.py` version shows one way to code it. This version also renames the method `read` to `readline`, because it reads actual files in this example.

File `streams.py`

```python
class Processor:
    def __init__(self, reader, writer):
        self.reader = reader
        self.writer = writer
    def process(self):
        while True:
            data = self.reader.readline()
            if not data: break
            data = self.converter(data)
            self.writer.write(data)
    def converter(self, data):
        assert False, 'converter must be defined'  # Or raise exception
```

The class defines a `converter` method that subclasses must fill in. This is the abstract superclass model from Chapter 29. The `assert` statement raises an exception when its test is false.

The `reader` and `writer` objects are embedded in the instance, which is composition. The conversion logic lives in a subclass instead of being passed in as a function, which is inheritance. The `converters.py` version shows the subclass.

File `converters.py`

```python
from streams import Processor
class Uppercase(Processor):
    def converter(self, data):
        return data.upper()
if __name__ == '__main__':
    import sys
    obj = Uppercase(open('trihack.txt'), sys.stdout)
    obj.process()
```

The `Uppercase` class inherits the loop from `process`, along with anything else its superclasses provide. It defines only what is unique to it, which is the conversion. When you run this file, it reads `trihack.txt` from the current directory. It writes the uppercase text to `stdout`, which usually means the window you work in.

```text
$ cat trihack.txt  # Use "type" on Windows
hack
Hack
HACK!
$ python3 converters.py
HACK
HACK
HACK!
```

To process other kinds of streams, pass different objects to the constructor. This example sends the output to a file instead of a stream. Exit the REPL to finalize the file.

```text
$ python3
>>> import converters
>>> scan = converters.Uppercase(open('trihack.txt'), open('trihackup.txt', 'w'))
>>> scan.process()
$ cat trihackup.txt
HACK
HACK
HACK!
```

You can also pass in any object that has the required methods. Here, a writer class wraps each line in HTML tags. Lines are read from a file, converted to uppercase, and printed inside `<PRE>` tags. Nothing in `Processor` changes to allow this.

```text
$ python3
>>> from converters import Uppercase
>>> class HTMLize:
...     def write(self, line):
...         print(f'<PRE>{line.rstrip()}</PRE>')
...
>>> Uppercase(open('trihack.txt'), HTMLize()).process()
<PRE>HACK</PRE>
<PRE>HACK</PRE>
<PRE>HACK!</PRE>
```

Trace the control flow, and you see two kinds of reuse. The uppercase step comes from inheritance. The HTML formatting comes from composition. The `Processor` superclass knows nothing about either step. It only requires that the writer has a `write` method and that a `converter` method exists. It does not care what those methods do. This kind of polymorphism and encapsulation gives classes much of their power in Python.

As written, `Processor` only provides a file-scanning loop. In more realistic work, we could add more tools for its subclasses. That would turn it into a full application framework. Code written once in a superclass can be reused in every program. In this example, the HTML step was the only code we wrote. The rest came packaged and inherited.

Composition is used as much as inheritance in large systems. Python itself provides inheritance as its main OOP tool, which is why this book focuses on it. Composition is a design issue beyond the Python language, so this book leaves it to other resources. Inheritance and composition often complement each other, and sometimes they are alternatives.

#### Classes and persistence

Earlier in this part of the book we explored `pickle` and `shelve`. Those modules work especially well with class instances. Pickling an instance stores both its data and its logic. This is often enough reason to use classes at all, since a plain dictionary would lose the methods.

The pizza shop classes could also serve as the start of a restaurant database. Pickling an instance to a file keeps it between program runs.

```text
>>> from pizzashop import PizzaShop
>>> shop = PizzaShop()
>>> shop.chef
<PizzaRobot: name="Pat", salary=50,000.00>
>>> import pickle
>>> pickle.dump(shop, open('shopfile.pkl', 'wb'))
```

One call stores the whole composite `shop` object in a file. Another session or program can load it back with one step. The restored objects keep both their state and their behavior, including the embedded employees and the oven.

```text
>>> import pickle
>>> shop = pickle.load(open('shopfile.pkl', 'rb'))
>>> shop.chef
<PizzaRobot: name="Pat", salary=50,000.00>
>>> shop.order('sue')
sue orders from <Server: name="Jan", salary=40,000.00>
Pat makes pizza
oven bakes
sue pays for item to <Server: name="Jan", salary=40,000.00>
```

This is only a prototype. We could extend the shop to track inventory and revenue. Saving the shop to its file after each change keeps the updated state. For more on pickles and shelves, see the standard library manual and Chapters 9, 28, and 37.

### Delegation: the like-a relationship

There is a third way to combine classes, and it looks like a manager with a team. Inheritance and composition are not the only tools. Object-oriented programmers also talk about delegation. Delegation usually means a controller object embeds another object. The controller passes operation requests to that object. Controllers can handle administrative work, such as logging or validating access. They can also add steps to interface components or monitor active instances.

Delegation is a special form of composition. A single embedded object is managed by a proxy class, also called a wrapper. A proxy is a stand-in that answers on another object's behalf. The proxy keeps most or all of the embedded object's interface.

Proxies can apply to other mechanisms too, such as function calls. Here we care about proxies for an object's full behavior, including method calls and other operations.

Chapter 28 introduced this idea with an example. In Python, it is usually built with the `__getattr__` method hook from Chapter 30. Python calls `__getattr__` for attributes that do not exist on the instance. A wrapper class can route any such access to the object it wraps. Because the routing is generic, the wrapper keeps the wrapped object's interface and can add operations of its own.

The `trace.py` version reviews this idea with a small module, `trace.py`. The whole wrapper is three methods' worth of code, and one of them is the constructor.

File `trace.py`

```python
class Wrapper:
    def __init__(self, object):
        self.wrapped = object  # Save object
    def __getattr__(self, attrname):
        print('Trace: ' + attrname)  # Trace fetch
        return getattr(self.wrapped, attrname)  # Delegate fetch
```

Recall from Chapter 30 that `__getattr__` receives the attribute name as a string. This code uses the `getattr` built-in to fetch an attribute from the wrapped object by a name string. The call `getattr(X, N)` works like `X.N`. The difference is that `N` is an expression that becomes a string at runtime.

The call `getattr(X, N)` is also similar to `X.__dict__[N]`. The `getattr` version also searches the inheritance tree, but the dictionary version does not. Chapters 23 and 29 cover the `__dict__` attribute in more detail.

You can use this wrapper approach to manage access to any object that has attributes. That includes lists, dictionaries, classes, and instances. The `Wrapper` class prints a trace message on each access, then passes the request to the wrapped object.

```text
>>> from trace import Wrapper
>>> x = Wrapper([1, 2, 3])  # Wrap a list
>>> x.append(4)  # Delegate to list method
Trace: append
>>> x.wrapped  # Print my member
[1, 2, 3, 4]
>>> x = Wrapper({'a': 1, 'b': 2})  # Wrap a dictionary
>>> list(x.keys())  # Delegate to dictionary method
Trace: keys
['a', 'b']
```

The result augments the whole interface of the wrapped object. We can log method calls, send them to custom logic, or adapt a class to a new interface. The wrapped object never knows, because it only sees its own methods being called.

Chapter 32 revives wrapped objects and delegated operations as one way to extend built-in types. Chapters 32 and 39 also cover function decorators. A decorator augments one function or method rather than an entire interface. Class decorators can add this kind of wrapper to every instance of a class automatically.

**Note.** Delegating built-in operations has a limit. A general proxy like `Wrapper` cannot catch calls to operator-overloading methods that built-in operations run. The list's `__add__`, for example, is not caught, and the wrapper fails.

```text
>>> [1, 2, 3] + [4, 5]
[1, 2, 3, 4, 5]
>>> [1, 2, 3].__add__([4, 5])
[1, 2, 3, 4, 5]
>>> Wrapper([1, 2, 3]) + [4, 5]
TypeError: unsupported operand type(s) for +: 'Wrapper' and 'list'
```

Explicit attribute fetches reach `__getattr__`. Built-in operations work differently, and that affects some delegation tools. Chapters 38 and 39 return to this issue in the context of managed attributes and decorators. For now, remember that a delegating proxy may need to define operator methods itself. It can do this by code, by tools, or through superclasses. It must do so if the embedded object uses those methods.

### Pseudoprivate class attributes

Class designs must also deal with name usage. Chapter 28 noted that methods in a general tool class can be replaced by subclasses if they are exposed. That policy supports customization. It also allows accidental replacement, which is the price of the same freedom.

In Part V, you learned that every name assigned at the top level of a module is exported. The same holds for classes. Data hiding is a convention. Clients can read or change any attribute of a class or instance they can reach.

Python attributes are public and virtual in C++ terms. They are accessible everywhere and looked up at runtime. You can even change or delete a class's method at runtime, although programs rarely do. Python is a scripting language, so it favors enabling over restricting.

Python does support name mangling. Mangling links a name to the class that created it. Such names are often called private attributes, but "pseudoprivate" is more accurate. Mangling does not prevent access from outside the class. Its main purpose is to avoid name collisions in instances. It is not a way to restrict access, and the name says so once you know the term.

Pseudoprivate names are an advanced and optional feature. You may not need them until you write general tools or large class hierarchies for multiple-programmer projects. Python programmers often use a single leading underscore instead, as in `_X`. That is only an informal signal that a name should not be changed. Python itself does not treat it differently. You may still see double underscores in other people's code, so you should understand them.

#### Name mangling overview

Within a `class` statement, a name that starts with two underscores and does not end with two underscores is expanded automatically. The expansion adds the enclosing class name at the front. For example, a name `__X` inside a class named `Hack` becomes `_Hack__X`. The original name gets a single underscore and the class name.

Because the class name is part of the result, the name is usually unique. It will not clash with similar names from other classes in a hierarchy.

Mangling applies only to names that appear inside a `class` statement, and only to names with two leading underscores. It covers class attributes, including method names. It also covers instance attributes assigned to `self`. In a class named `Hack`, a method `__meth` becomes `_Hack__meth`. An instance reference `self.__X` becomes `self._Hack__X`.

If a class uses the double-underscore name everywhere, all references still work, because every one of them is mangled the same way. Mangling helps avoid clashes when several classes add attributes to the same instance. An example shows how.

#### Why use pseudoprivate attributes?

Pseudoprivate attributes address a problem with how instance attributes are stored. In Python, instance attributes usually end up in the single instance object at the bottom of the class tree. Class-level method functions share that object, because the instance is passed into them. C++ works differently. There, each class gets its own space for the data members it defines.

When a method assigns to a `self` attribute, it creates or changes an attribute on the instance. Inheritance searches happen only when you fetch a name, not when you assign one. If several classes in a hierarchy assign to the same attribute name, they collide.

Suppose one programmer writes a class that assumes it owns the attribute name `X` on the instance. The methods set and fetch that name, and the class works perfectly on its own.

```python
class C1:
    def meth1(self): self.X = 88  # I assume X is mine
    def meth2(self): print(self.X)
```

Now suppose another programmer, working alone, makes the same assumption in another class. Neither programmer has done anything wrong, and neither has seen the other's code.

```python
class C2:
    def metha(self): self.X = 99  # Me too
    def methb(self): print(self.X)
```

Each class works on its own. The problem appears when you mix them in one class tree with multiple inheritance. Two reasonable designs meet, and they fight over one name.

```python
class C3(C1, C2): ...
I = C3()  # But only 1 X in I!
```

The value that `self.X` returns depends on which class assigned it last. All assignments refer to the same instance. There is only one `X` attribute, `I.X`, no matter how many classes use that name. That sharing is normal, because it is how classes communicate. The instance acts as shared memory.

When a class must own an attribute, prefix its name with two underscores everywhere the class uses it. The `pseudoprivate.py` version shows this.

File `pseudoprivate.py`

```python
class C1:
    def meth1(self): self.__X = 88  # Now X is mine
    def meth2(self): print(self.__X)  # Becomes _C1__X in I
class C2:
    def metha(self): self.__X = 99  # Me too
    def methb(self): print(self.__X)  # Becomes _C2__X in I
class C3(C1, C2): pass
I = C3()  # Two X names in I
I.meth1(); I.metha()  # Set names
print(I.__dict__)  # Actual storage
I.meth2(); I.methb()  # Fetch names
```

The prefixed `X` attributes expand to include their class names. The expanded names are `_C1__X` and `_C2__X`. The name `X` does not appear. Running `dir` on `I`, or inspecting its namespace dictionary, shows the expanded names. Because the names are more unique, each class can safely assume it owns the names it prefixes with two underscores.

```text
$ python3 pseudoprivate.py
{'_C1__X': 88, '_C2__X': 99}
88
99
```

This avoids collisions in the instance, but it is not true privacy. If you know the enclosing class name, you can still reach either attribute through its full name, as in `I._C1__X = 77`. Someone could also collide with the expanded pattern on purpose, which is unlikely but possible. The feature still makes it much less likely that you step on another class's names by accident.

Pseudoprivate names also help in larger frameworks and tools. They keep a new method name from hiding a definition elsewhere in the class tree. They also reduce the chance that a name lower in the tree replaces an internal method.

If a method is meant for use only within a class that other classes may mix in, the double underscore nearly guarantees that it will not interfere with other names. This matters most with multiple inheritance.

```python
class Super:
    def method(self): ...  # A real application method
class Tool:
    def __method(self): ...  # Becomes _Tool__method
    def other(self): self.__method()  # Use my internal method
class Sub1(Tool, Super):
    def actions(self): self.method()  # Runs Super.method as expected
class Sub2(Tool):
    def __init__(self): self.method = 99  # Doesn't break Tool.__method
    def method(self): ...  # Ditto
```

Recall that superclasses are searched left to right in the `class` header. Here, `Sub1` prefers attributes from `Tool` over those in `Super`. You could switch the order of the superclasses in the `Sub1` header to make Python pick the application's methods first. Pseudoprivate names solve the problem completely. They also stop subclasses from accidentally redefining the internal method's name, as in `Sub2`.

This feature is mostly useful in larger projects with several programmers, and only for selected names. Do not clutter simple code with it. Use it only for names that a single class must control. In general tools it can help. In simple programs it is usually overkill.

**Note.** Chapter 30 covers emulating private instance attributes with `__getattr__` and `__setattr__`. Chapter 39 builds a broader `Private` class decorator with delegation. Privacy controls are possible in Python, yet they are rarely used, even in large systems.

### Method objects: bound or not

A method is an object in its own right, and that fact unlocks several designs. Methods, and bound methods in particular, make many design goals easy in Python. We met bound methods briefly when we studied `__call__` in Chapter 30. The full story is more general and flexible than it first seems.

Chapter 19 showed that functions are normal objects. Methods are objects too. You can assign them to names, pass them to functions, and store them in data structures. Like functions, modules, and classes, methods are first-class objects. A class's methods can be reached from an instance or from the class itself, so there are two flavors.

- Bound methods: when a method is referenced through an instance. Qualifying an instance with a function attribute of its class returns a bound method object. That object packages the instance with the function as a pair. When you call a bound method later, Python passes the instance to the `self` argument.
- Plain functions: when a method is referenced through a class. Qualifying a class with a function attribute returns a plain function object. To call it, you must pass an instance explicitly as the `self` argument, if the function expects one.

Both kinds are full objects, and you can move them around like strings or numbers. A bound method remembers its instance. A plain function does not. That is why earlier examples passed the instance explicitly when a subclass called a superclass method. Those calls produced plain functions along the way, as in `employees.py` in `employees.py`.

When you call a bound method, Python supplies the instance for you. The instance is the one used to create the bound method object. That makes bound methods interchangeable with ordinary functions. They are especially useful for interfaces that were written for functions.

**Note.** Python once required every method in a class to take an instance argument. Methods fetched directly from a class were called unbound methods. They needed an instance when called later.

Today, methods in a class are plain functions. Their only special quality is that Python binds them to an instance when they are fetched through the instance. Unbound methods are gone. Long live plain functions.

#### Bound methods in action

Suppose we define a class in the REPL. One method is enough to show everything that follows.

```text
>>> class Hack:
...     def doit(self, message):
...         print(message)
```

In normal use, we make an instance and call its method in one step. The call prints the argument, and nothing about the pair is visible.

```text
>>> inst = Hack()
>>> inst.doit('hello')  # Typical method calls
hello
```

Python actually creates a bound method object along the way, just before the call's parentheses. You can fetch a bound method without calling it. The expression `object.name` evaluates to an object, like any other expression.

Here it returns a bound method that pairs the instance `inst` with the function `Hack.doit`. We can assign that pair to a new name and call it like a function that takes no `self`.

```text
>>> inst = Hack()
>>> meth = inst.doit  # Bound method object: instance+function
>>> meth('hola')  # Same effect as inst.doit('...')
hola
```

The pair is visible if you look for it. The bound method exposes its instance through `__self__` and its function through `__func__`. Two attributes, and the whole illusion of a method disappears.

```text
>>> meth
<bound method Hack.doit of <__main__.Hack object at 0x108f2e8a0>>
>>> meth.__self__
<__main__.Hack object at 0x108f2e8a0>
>>> meth.__func__
<function Hack.doit at 0x108f37ce0>
```

If you qualify the class instead, you get a plain function with no instance attached. To call it, you usually pass an instance as the leftmost argument. The expression has no instance to supply, and the method expects one.

```text
>>> inst = Hack()
>>> meth = Hack.doit  # Plain function: requires self
>>> meth(inst, 'ciao')  # Pass in instance (if the method expects one)
ciao
>>> meth
<function Hack.doit at 0x108f37ce0>
```

The same rules apply inside a method. In `self.method`, `self` is an instance, so the expression is a bound method. In `Class.method`, the expression is a simple function that may require `self` when it runs.

```text
>>> class Hack2(Hack):
...     def doit2(self):
...         meth = self.doit  # Bound method object: instance+function
...         meth('bonjour')  # Looks like a simple function
...         meth = Hack.doit
...         meth(self, 'privit')  # Plain function: requires self
>>> Hack2().doit2()
bonjour
privit
```

Most of the time you call a method right after fetching it. You never notice the bound method made along the way. When you write code that calls objects generically, you must treat unbound methods with care. They usually need an explicit instance.

Classes can also contain methods that take no `self` at all. These behave like functions in a module, apart from inheritance. You can call them through the class.

```text
>>> class Hack3:
...     def doit3(message):  # A self-less method (function)
...         print(message)
>>> Hack3.doit3('guten tag')  # No "self" is passed
guten tag
```

Calling the same method through an instance fails. The bound method made along the way passes the instance too, so the call sends one argument too many.

```text
>>> x = Hack3()
>>> x.doit3('namaste')
TypeError: Hack3.doit3() takes 1 positional argument but 2 were given
```

So you can write self-less functions in a class and call them through the class without an instance. To call them through an instance too, you need static methods and class methods. Chapter 32 covers those. The `super` built-in also binds an instance to a method. It is more involved than the bound method pairs shown here, and Chapter 32 explains it.

Bound methods are also flexible in data structures. The next example stores four of them in a list and calls them with ordinary call expressions.

```text
>>> class Number:
...     def __init__(self, base):
...         self.base = base
...     def double(self):
...         return self.base * 2
...     def triple(self):
...         return self.base * 3
>>> x, y, z = Number(2), Number(3), Number(4)  # Class instance objects
>>> x.double()  # Normal immediate calls
4
>>> acts = [x.double, y.double, z.double, z.triple]  # List of bound methods
>>> for act in acts:  # Calls are deferred
...     print(act(), end=' ')
4 6 8 12
```

Each call to `act` runs a method on a saved instance. The instance travels with the method in the bound method pair, so the list needs no parallel list of objects.

#### Why you will care: bound method callbacks

Callbacks are where bound methods earn their keep. Bound methods pair an instance with a method function. You can use them anywhere a simple function is expected. A common place for this is event callbacks in GUI code. Python's `tkinter` standard-library module is one example.

The contrast below is the point of the whole section. A plain callback has no instance, so its state has to live somewhere else.

A plain callback takes no arguments. It keeps state in globals or in an enclosing function scope, which is called a closure.

```python
def handler():
    ...  # use globals or closure scopes for state
...
widget = Button(text='Tap', command=handler)
```

With `tkinter`, you pass a callable that takes no arguments to the `command` keyword. Function names and `lambda` expressions work. Class methods also work, but if they expect an instance, they must be bound methods.

```python
class MyGui:
    def handler(self):
        ...  # use self.attr for state
    def makewidgets(self):
        b = Button(text='Tap', command=self.handler)
```

Here the event handler is `self.handler`. It is a bound method that remembers both `self` and `MyGui.handler`. When an event calls `handler`, `self` refers to the original instance. The handler can read and write instance attributes that keep state between events. With plain functions, state must live in globals or closures instead.

Chapter 30 covers `__call__` as another way to make a class fit a function-based API. Chapter 19 covers `lambda`, which is also common in callback roles. You do not need to wrap a bound method in a `lambda` unless you must add extra arguments. A bound method already defers the call. There are no parentheses to trigger it, so a `lambda` would add nothing.

### Classes are objects: generic object factories

Some class-based designs must create objects in response to conditions that cannot be predicted when the program is written. The factory design pattern allows this deferred creation. A factory is simply code whose job is to make other objects. Python's flexibility lets factories take many forms. Some of them do not look special at all.

Classes are first-class objects too. You can pass them around, store them in data structures, and hand them to functions. A function that generates objects of any kind is called a factory in OOP design. Factories can be a large project in a statically typed language such as C++. In Python they are almost trivial to write.

The call syntax from Chapter 18 can call any class with any positional or keyword arguments in one step. The `factory.py` version shows the underlying code. It is four lines, and only three of them matter.

File `factory.py`

```python
def factory(aClass, *pargs, **kargs):  # Varargs tuple, dict
    return aClass(*pargs, **kargs)  # Call aClass
class Hack:
    def doit(self, message):
        print(message)
class Person:
    def __init__(self, name, job=None):
        self.name = name
        self.job = job
object1 = factory(Hack)  # Make a Hack object
object2 = factory(Person, 'Sue', 'dev')  # Make a Person object
object3 = factory(Person, name='Bob')  # Ditto, with keywords and default
```

The `factory` function receives a class and zero or more constructor arguments. It uses star syntax to collect the arguments and unpack them, then calls the class to return an instance. The function can call any callable, including functions and methods. Here we use it only with classes.

The rest of the example defines two classes and makes instances of both through `factory`. This one function works for any class and any constructor arguments. You may never need to write another factory in Python. If you run the example live, the objects look like this.

```text
>>> from factory import *
>>> object1.doit(99)
99
>>> object2.name, object2.job
('Sue', 'dev')
>>> object3.name, object3.job
('Bob', None)
```

Everything in Python is a first-class object, classes included. In languages such as C++, a class is usually only compiler input. Passing classes around is natural in Python. As noted at the start of this part of the book, only objects made from classes do full OOP.

#### Why factories?

The `factory` function is a neat illustration, but what is it good for? Showing real uses takes more code than fits here. In general, a factory insulates code from the details of dynamically configured object creation.

Recall the `Processor` class from `streams.py`. It accepts reader and writer objects to process any data stream. Chapter 26 passed in specialized objects by hand. Later examples passed in hardcoded file, stream, and formatter objects. In a more dynamic program, a configuration file or a GUI might choose the streams.

In that dynamic world, you may not know the stream objects when you write the script. You may need to create them at runtime, from the contents of a configuration file. The file might name a stream class in a module, with an optional constructor argument.

A factory can fetch and pass in classes that the program did not hardcode. Those classes might not even exist yet when you write the code.

Here is a hypothetical version of that idea. The names in angle brackets stand in for values that come from the configuration file.

```text
classname = …parse from config file…
classarg = …parse from config file…
import streamtypes  # Customizable code
aclass = getattr(streamtypes, classname)  # Fetch from module
reader = factory(aclass, classarg)  # Or aclass(classarg)
processor(reader, …)
```

The `getattr` built-in fetches a module attribute from a string name. It works like `obj.attr`, except that `attr` is a string. This snippet does not strictly need `factory`. It could create the instance with `aclass(classarg)`. A separate function is more useful when extra work is needed at creation time, such as caching objects for reuse. Either way, factories are almost trivial with Python's dynamic typing and first-class objects.

### Multiple inheritance and the MRO

Our last design pattern is one of the most useful. It also serves as the subject for more realistic examples, and some of its code can serve as real tools. This is the pattern that makes mix-ins possible, so it earns a careful reading.

Most examples so far used single inheritance. Each class has one superclass. That is enough for simple hierarchies, and it supports customization. In the pizza shop example, each worker belonged to one category and inherited names from one branch of the tree. In outline form:

```python
class B: ...
class A(B): ...
I = A()  # Use attributes from I, A, and B - in that order
```

Many designs need to combine different sets of methods. A class header can list more than one superclass in parentheses. This is multiple inheritance. The class and its instances inherit names from all the listed superclasses.

```python
class C: ...
class B: ...
class A(B, C): ...
I = A()  # Use attributes from I, A, B, and C – in that order
```

Multiple inheritance suits objects that belong to more than one set. A person may be an engineer, a writer, and a musician. Such a person would inherit properties from all of those sets. The object gets the union of the behavior in its superclasses.

Later in this section, multiple inheritance also supports mix-in classes. A mix-in is a class that packages mixable attributes, meaning a bundle of methods you can add to any class that needs them.

Multiple inheritance adds another dimension to attribute search. Single inheritance searches depth first. It checks the instance, then its class, then each superclass from lowest to highest. The order comes from the class the instance was made from and from the superclass in each `class` header. The `__bases__` attribute of a class mirrors that order.

Multiple inheritance also searches left to right, in the order of the classes in parentheses. This is a nested step. It runs only after the branches to the left reach the top of the tree and are exhausted.

Together these two rules form DFLR, for depth first and then left to right. DFLR is enough when an attribute name appears in only one branch, which is typical. When the same name appears in several branches, DFLR is weak. A lower and more specialized subclass to the right cannot redefine a name in a higher superclass reached through a branch on the left.

To solve this, multiple inheritance uses a slightly different order called the MRO, the method resolution order. The MRO applies to all attributes, not just methods, despite the name. In typical trees, the MRO works the same as DFLR. It differs in diamonds.

A diamond forms when several classes share a common superclass. The tree looks like a diamond with its corners turned. In a diamond, the MRO moves across a level before it climbs up. It is more breadth-first there.

The MRO is used for every class tree. It visits a common superclass only once, and only after all of its subclasses. Every class tree is also a diamond in one sense. Python adds the built-in `object` class above every root class. Without the MRO, the defaults in `object` could hide methods that you define in your classes.

#### How multiple inheritance works

The simple case comes first. Class `A` inherits from `B` and `C`. Both `B` and `C` are root classes that define their own attributes. When we make an instance `I` of `A` and ask for an attribute, Python searches `I`, then `A`, then `B`, then `C`.

So `attr1` is found in `B` and `attr2` is found in `C`. If you work along in the REPL, type a blank line after each class.

```text
>>> class C: attr2 = 'C2'
>>> class B: attr1 = 'B1'
>>> class A(B, C): pass
>>> I = A()
>>> I.attr1, I.attr2
('B1', 'C2')
```

If `B` and `C` both define the same name, `B` wins. That follows from the left-to-right rule. Lower classes such as `A` still beat their superclasses.

```text
>>> class C: attr2 = 'C2'
>>> class B: attr2 = 'B2'; attr1 = 'B1'
>>> class A(B, C): attr1 = 'A1'
>>> I = A()
>>> I.attr1, I.attr2
('A1', 'B2')
```

Next, add a higher superclass above `B`. Now `B` inherits from `D`, and `C` is a root class with no superclass. Under DFLR, Python searches `I`, `A`, `B`, and `D` before it checks `C`. So `attr2` is found in `D`. Depth wins here, and the left branch is searched to the top before the right branch is touched.

```text
>>> class D: attr2 = 'D2'
>>> class C: attr2 = 'C2'
>>> class B(D): attr1 = 'B1'
>>> class A(B, C): pass
>>> I = A()
>>> I.attr1, I.attr2
('B1', 'D2')
```

Now make `B` and `C` both inherit from `D`, and let `C` define the same attribute as `D`. Under the MRO, the lower class `C` wins. Its version replaces the one in `D`, even though `D` is reached first by depth.

```text
>>> class D: attr2 = 'D2'
>>> class C(D): attr2 = 'C2'
>>> class B(D): attr1 = 'B1'
>>> class A(B, C): pass
>>> I = A()
>>> I.attr1, I.attr2
('B1', 'C2')
```

This last case is the diamond pattern. Two classes, `B` and `C`, inherit from the same superclass. In this case, the lower class's version of an attribute wins over the superclass version. That happens even when the superclass could be reached first by depth alone.

The difference appears only in diamonds. Without a diamond, the search still picks a higher superclass before a lower class. The third example shows this. The MRO lets a class override attributes from a higher class it inherits. In the last example, `C` replaces names in `D`, even though `D` comes first under DFLR.

To summarize, the search goes all the way up and then to the right in a nondiamond tree. That is DFLR. In a diamond, the search checks classes to the right before it climbs to the common superclass. That is the MRO.

Strictly speaking, each of these examples is an implicit diamond. The root classes inherit from the built-in `object` class. That class supplies defaults for some methods, such as the display string for `print`. The MRO keeps those `object` defaults from hiding methods in user classes below it. The next section gives the exact order.

#### How the MRO works

Formally, the MRO works as if all classes were listed in DFLR order. Then all but the rightmost copy of each duplicate class is removed. The computation has these steps, and the second one is the only part people forget.

- List all the classes an instance inherits from, in DFLR order. Include a class more than once if it is visited more than once.
- Scan the list for duplicate classes. Remove all but the last, or rightmost, occurrence of each duplicate.

The MRO for a class holds the class itself, its superclasses, and all higher superclasses. It ends with the implicit or explicit `object` root class. Each class appears before its parents. Multiple parents keep the order they have in the `class` header.

A common parent in a diamond appears only at its last visit in the MRO. So lower classes are searched first when attribute inheritance uses the list. That makes the search more breadth-first than depth-first, but only in diamonds. Each class appears once, no matter how many paths lead to it.

The `mro_nondiamond.py` version shows a nondiamond tree. Its shape is sketched in the comments, so the code doubles as a small diagram.

File `mro_nondiamond.py`

```python
class E: attr = 'E'  # D E
class D: attr = 'D'  # | |
class C(E): attr = 'C'  # B C
class B(D): pass  # \ /
class A(B, C): pass  # A
# |
X = A()  # X
print(X.attr)  # D
```

To find the MRO for this tree, Python lists all the classes reachable by DFLR. Then it removes duplicates. Remember that `object` sits above all root classes.

```text
DFLR => [X, A, B, D, object, C, E, object]
MRO => [X, A, B, D, C, E, object]
```

In this tree, DFLR and the MRO give the same result. The output is `D`, because `attr` comes from class `D` at the top left. The MRO differs only in where `object` appears. It is kept once at the end, after its duplicates are removed. That does not matter here, because these classes do not redefine any `object` default.

The `mro_diamond.py` version shows a user-defined diamond. The difference is clearer, and the answer changes.

File `mro_diamond.py`

```python
class D: attr = 'D'  # D
class C(D): attr = 'C'  # / \
class B(D): pass  # B C
class A(B, C): pass  # \ /
# A
X = A()  # |
print(X.attr)  # C  # X
```

In this tree, DFLR reaches the common class `D` twice. The MRO keeps only the last, rightmost `D`. So the lower class `C` defines the winning `attr`. The output is now `C` instead of `D`.

```text
DFLR => [X, A, B, D, object, C, D, object]
MRO => [X, A, B, C, D, object]
```

Every class has a built-in `__mro__` attribute. You can see its search order there. The tuple lists the classes searched for instances of that class, after the instance itself. Python sets it when the class is created. The `mro` class method computes it. That method can be customized, but the details are too advanced for this book.

The `__mro__` tuple is easier to read if you select class names, as in this check of the nondiamond tree.

```text
>>> from mro_nondiamond import *
D
>>> [c.__name__ for c in A.__mro__]
['A', 'B', 'D', 'C', 'E', 'object']
>>> [c.__name__ for c in C.__mro__]
['C', 'E', 'object']
```

Here is the same check for the diamond in `mro_diamond.py`. Compare the two tuples, and the difference between the trees becomes obvious.

```text
>>> from mro_diamond import *
C
>>> [c.__name__ for c in A.__mro__]
['A', 'B', 'C', 'D', 'object']
>>> [c.__name__ for c in C.__mro__]
['C', 'D', 'object']
```

The full `__mro__` lists the classes used in inheritance for a class. The `__bases__` attribute lists only the direct superclasses. Both are worth inspecting once on a tree you understand.

```text
>>> A.__mro__
(<class 'mro_diamond.A'>, <class 'mro_diamond.B'>, <class 'mro_diamond.C'>,
<class 'mro_diamond.D'>, <class 'object'>)
>>> X.__class__.__mro__
(<class 'mro_diamond.A'>, <class 'mro_diamond.B'>, <class 'mro_diamond.C'>,
<class 'mro_diamond.D'>, <class 'object'>)
>>> A.__bases__
(<class 'mro_diamond.B'>, <class 'mro_diamond.C'>)
>>> D.__bases__
(<class 'object'>,)
```

Try `__mro__` on your own classes. It is the best way to confirm how Python will search a tree you are unsure about, and it takes one line at the prompt.

**Note.** The MRO has more detail than this book covers. The sketch here is an approximation by design. It will not give accurate results for some complex class trees. The full details are in Python's documentation. Keeping your class trees simple keeps them clear of the tricky parts. Obscurity is rarely good engineering, in your code or in Python itself.

#### Attribute conflict resolution

Conflicts are the price of multiple inheritance, so plan for them. Multiple inheritance has one main drawback. The same method name, or another attribute name, can appear in more than one branch. When that happens, the conflict is settled either by the search order or by your code.

- Default: the search picks the first occurrence it finds. When you reference an attribute normally, as in `self.attr`, Python scans the MRO of the instance's class from left to right. It uses the first match.
- Explicit: you select the attribute yourself, by naming the class that holds it, as in `superclass.attr`. Your code overrides the search's default choice.

By default, multiple inheritance favors names on the left over names on the right. The MRO also favors lower classes over same-named attributes in a common superclass of a diamond. Assumptions are convenient, but they can be wrong. In the `mro_diamond.py` version, what if you need some same-named attributes from `B` and others from `C`?

There is an escape hatch, and it is worth knowing before you need it. If the default order does not work, you can force the selection. Assign or name the attribute you want at the place where the classes are combined. Any of these choices is allowed in `mro_diamond.py`. The last two are explicit, so they do not depend on the subtle choices of the MRO.

```python
class A(B, C): pass  # Use the default MRO choice (C)
class A(B, C): attr = B.attr  # Choose attr from the left branch (D)
class A(B, C): attr = C.attr  # Choose attr from the right branch (C)
```

Methods are attributes too. They are assignable names that refer to callable function objects. The choice can also be made inside a call.

```text
class A(B, C):
    def method(self, ...):
        self.method(...)  # Use the default MRO choice
class A(B, C):
    def method(self, ...):
        B.method(self, ...)  # Choose method from the left branch
class A(B, C):
    def method(self, ...):
        C.method(self, ...)  # Choose method from the right branch
```

Calls like these can override the MRO. They can also skip the class's own version and call up the tree. The next chapter introduces `super().method()`. That form selects the class after the host class in the MRO of `self`.

It is simple in single inheritance. In multiple inheritance it can be hard to follow, and it gives less control than explicit class names.

Manual overrides are needed only when the same name appears in several superclasses and you do not want the first one. For example, they let you choose unambiguously among same names on both the left and right branches. Normal inheritance would pick only from the left. You can also use overrides to make choices explicit, even in nondiamonds.

This topic matters less in typical Python code than it sounds. This book defers the details until the `super` built-in in the next chapter. It returns to the topic as a gotcha at the end of that chapter.

**Note.** The inheritance story continues. The complete algorithm has special cases for metaclasses, descriptors, and built-ins. Chapter 32 extends inheritance to the metaclass tree and applies the MRO in `super`. Chapter 38 covers the special case for built-in operations. A full formal definition appears in Chapter 40. The remaining details rarely affect application programs. For most programmers, this part is an optional read.

#### Example: mix-in attribute listers

Multiple inheritance is often used to mix in general methods from superclasses. Those superclasses are called mix-in classes. A mix-in provides methods that you add to application classes through inheritance. In a sense, a mix-in works like a module. It offers a package of methods for its client subclasses.

Unlike module functions, mix-in methods take part in the inheritance hierarchy. They also have access to `self`, so they can use state and other methods in the tree.

Python's default printing of an instance is not very useful, as the next example shows before we fix it.

```text
>>> class Hack:
...     def __init__(self, what):  # No __repr__ or __str__
...         self.data1 = what
>>> X = Hack('code')
>>> print(X)  # Default: class name + address (id)
<__main__.Hack object at 0x10ba464e0>
```

Chapter 28 and Chapter 30 showed that a class can provide `__str__` or `__repr__` for a custom display. Coding that method in every class is repetitive, and the copies drift apart. A better design codes it once in a general tool class and inherits it everywhere. That is the job of a mix-in.

Defining the display in a mix-in lets you reuse it wherever you want that format. This works even in classes that already have another superclass.

Earlier tools did related work. Chapter 28's `AttrDisplay` class formats instance attributes in a generic `__repr__`. It does not climb class trees, and it works only in single inheritance. Chapter 29's `classtree.py` module defines functions that climb and sketch class trees. It does not show object attributes, and it was not written as an inheritable class.

This section revisits both ideas. It builds three mix-in classes. They list instance attributes, inherited attributes, and the attributes of every object in a class tree. These classes also work in multiple inheritance.

This version uses `__str__` instead of `__repr__`. That choice is partly a matter of style. It limits the display to `print` and `str`, which is where people read output. The displays are meant for people, not as code-like output.

The choice also leaves client classes free to add a `__repr__` for interactive echoes and nested displays. It also avoids the `__repr__` looping problem covered below.

##### Listing instance attributes with `__dict__`

We start with the simple case. The next example lists attributes attached to an instance. The file `listinstance.py` defines a mix-in called `ListInstance`. It overloads `__str__` for every class that includes it in its header. Because it is a class, `ListInstance` works for instances of any client subclass.

File `listinstance.py`

```python
class ListInstance:
    """
    Mix-in class that provides a formatted print() or str() of instances via
    inheritance of __str__ coded here. Displays instance attrs only; self is
    instance of lowest class; __X naming avoids clashing with client's attrs.
    Works for classes with slots: a __dict__ is ensured by lack of slots here.
    """
    def __attrnames(self):
        result = '\n'
        for attr in sorted(self.__dict__):  # Slots okay
            result += f'\t{attr}={self.__dict__[attr]!r}\n'  # Repr for quotes
        return result
    def __str__(self):
        return (f'<Instance of {self.__class__.__name__}, '  # My class's name
                f'address {id(self):#x}:'  # My address (hex)
                f'{self.__attrnames()}>')  # name=value list
if __name__ == '__main__':
    import testmixin
    testmixin.tester(ListInstance)  # Test class in this module
```

The `__attrnames` method uses a classic comprehension pattern. You could write it more concisely with a generator expression and a `''.join()` call. That change is left as an exercise.

As coded, `ListInstance` uses techniques we have seen before. It gets the instance's class name with `self.__class__.__name__`. Each instance has a `__class__` attribute that names the class that created it. Each class has a `__name__` attribute that holds the name from its header.

The class does most of its work by scanning the instance's attribute dictionary in `__dict__`. It builds a string that shows each name and value. The keys are sorted by name, so the output is easy to read. The dictionary's insertion order is not used, which is deliberate: two runs should look alike.

`ListInstance` is much like the `AttrDisplay` tool from Chapter 28. It adds two techniques. It shows the instance's memory address by calling the `id` built-in. The `id` function returns any object's address, which is a unique identifier.

The class also uses pseudoprivate naming for its helper method, `__attrnames`. Python expands that name to `_ListInstance__attrnames`. The same expansion applies to class attributes such as methods and to instance attributes. In a general tool, this keeps the helper's name from clashing with names in client subclasses.

Because `ListInstance` defines `__str__`, instances display their attributes when printed. That is more useful than a bare address. Here is the class mixed in with a simple class, and the inherited display does all the work.

```text
>>> from listinstance import ListInstance
>>> class Hack(ListInstance):  # Inherit a __str__ method
...     def __init__(self, what):
...         self.data1 = what
>>> X = Hack('code')
>>> print(X)  # print() and str() run __str__
<Instance of Hack, address 0x10c890b90:
data1='code'
>
```

You can also get the listing as a string with `str`. Then you can apply escapes with `print` later. Interactive echoes and nested displays still use the default format, because we did not define `__repr__`. That is the split we discussed earlier, seen from the client side.

```text
>>> str(X)
"<Instance of Hack, address 0x10c890b90:\n\tdata1='code'\n>"
>>> X
<__main__.Hack object at 0x10c890b90>
```

`ListInstance` works with any class you write, even one that already has superclasses. Add it to the list of superclasses in the header, and you get its `__str__` for free. You keep the existing superclasses too. The file `testmixin.py` in `testmixin.py` contains test classes that show this.

File `testmixin.py`

```python
"""
Generic lister-mixin tester: similar to transitive reloader in
Chapter 25, but passes a class object to tester (not function),
and testByNames adds loading of both module and class by name
strings here, in keeping with Chapter 31's factories pattern.
"""
import importlib
def tester(listerclass, sept=False):
    "Pass any lister class to listerclass"
    class Super:
        def __init__(self):  # Superclass __init__
            self.data1 = 'code'  # Create instance attrs
        def method1(self):
            pass
    class Sub(Super, listerclass):  # Mix in method1 and a __str__
        def __init__(self):  # Listers have access to self
            Super.__init__(self)  # Or super().__init__()
            self.data2 = 'Python'  # More instance attrs
            self.data3 = 3.12
        def method2(self):  # Define another method here
            pass
    instance = Sub()  # Build instance with lister's __str__
    print(instance)  # Run mixed-in __str__ (or via str(x))
    if sept: print(f'\n{'-' * 80}\n')  # Python 3.12+ f-string
def testByNames(modname, classname, sept=False):
    modobject = importlib.import_module(modname)  # Import mod by namestring
    listerclass = getattr(modobject, classname)  # Fetch attr by namestring
    tester(listerclass, sept)
if __name__ == '__main__':
    testByNames('listinstance', 'ListInstance', True)  # Test all three here
    testByNames('listinherited', 'ListInherited', True)  # See others ahead...
    testByNames('listtree', 'ListTree', False)
```

This file is built to test many listers. It receives a lister class, `listerclass`, and mixes it into test classes nested in a function. Classes are first-class objects, so the lister can be a parameter that varies per test. The file also fetches classes by name strings. We will use that part later.

The self-test in `listinstance.py` imports `tester` and passes in `ListInstance`. The class `Sub` inherits names from `Super` and from `ListInstance`. It is a composite of its own names and the names of both superclasses. When you make a `Sub` instance and print it, the custom display from `ListInstance` appears.

```text
$ python3 listinstance.py
<Instance of Sub, address 0x10caae300:
data1='code'
data2='Python'
data3=3.12
>
```

The `ListInstance` display works in any class it joins. `self` refers to an instance of whatever subclass mixes it in. Mix-ins are the class equivalent of modules. They are packages of methods for many clients.

They also make maintenance easier. If you later extend `__str__` to show inherited class attributes, every class that mixes in `ListInstance` picks up the change. Such a change needs no edits in the subclasses.

##### Listing inherited attributes with `dir`

`ListInstance` shows only attributes attached to the instance. Extending it to show every attribute the instance can reach is easy. The trick is to call the `dir` built-in instead of scanning `__dict__`. The dictionary holds only instance attributes. The `dir` function also collects inherited attributes.

The `listinherited.py` version puts this change in `listinherited.py`. The module is separate for testing. Existing clients could switch to this version and get the new display automatically. A `from` import with an `as` clause can rename the new version to an old name.

File `listinherited.py`

```python
class ListInherited:
    """
    Use dir() to collect both instance attrs and names inherited from
    its classes. This includes default names inherited from the implied
    'object' superclass above topmost classes. getattr() can fetch
    inherited names not in self.__dict__.
    Caution: use __str__, not __repr__, or else this loops when printing
    bound methods that may be returned for some attributes by getattr().
    This will normally fail for class "slots" attributes not yet assigned.
    """
    def __attrnames(self, unders=False):
        result = '\n'
        for attr in dir(self):  # Instance dir()
            if attr[:2] == '__' and attr[-2:] == '__':  # Built-in names
                result += f'\t{attr}\n' if unders else ''  # Skip built-ins?
            else:
                result += f'\t{attr}={getattr(self, attr)!r}\n'
        return result
    def __str__(self):
        return (f'<Instance of {self.__class__.__name__}, '  # My class's name
                f'address {id(self):#x}:'  # My address (hex)
                f'{self.__attrnames()}>')  # name=value list
if __name__ == '__main__':
    import testmixin
    testmixin.tester(ListInherited)  # Test class in this module
```

By default this code skips all `__X__` names to keep the output short. The test case has 27 such names. Most are internal names that a generic listing does not need. Some are operator methods, such as the `__str__` method we defined. Most come from the implied `object` root class. There is no easy way to tell which class each one came from.

The `dir` results can include names from anywhere in the tree. So this version fetches each value with `getattr`, not by indexing `__dict__`. The `getattr` built-in runs the inheritance search. Some names in the list are not stored on the instance itself.

To test this version, run its file. It passes `ListInherited` to the test function in `testmixin.py`. The output includes the extra inherited names. It also shows the name mangling in the lister's method name.

```text
$ python3 listinherited.py
<Instance of Sub, address 0x101d76600:
_ListInherited__attrnames=<bound method ListInherited.__attrnames of <…>>
data1='code'
data2='Python'
data3=3.12
method1=<bound method tester.<locals>.Super.method1 of <testmixin.tester…>>
method2=<bound method tester.<locals>.Sub.method2 of <testmixin.tester…>>
>
```

The output truncates the bound methods to fit the page. The first two look like this, with a line break added. Run the file yourself for the full, current picture.

```text
_ListInherited__attrnames=<bound method ListInherited.__attrnames of
<testmixin.tester.<locals>.Sub object at 0x101d76600>>
method1=<bound method tester.<locals>.Super.method1 of
<testmixin.tester.<locals>.Sub object at 0x101d76600>>
```

The display format is open-ended. Python's standard `pprint` module can help with it, as an exercise. The next version gives a more useful view of the tree, so we move on.

**Note.** Once the display includes inherited methods, `__str__` must replace `__repr__` for printing. With `__repr__`, the code falls into a recursive loop. The `getattr` call returns a bound method. Its display includes the instance. That triggers `__repr__` again, and the loop continues until the stack overflows.

The problem is subtle, but it is real. Change `__str__` to `__repr__` to see it happen. One way to avoid the loop is to skip `getattr` results that are instances of `types.MethodType`. Using `__str__` is simpler.

##### Listing attributes per object in class trees

The last lister extends the earlier ones. The inherited list gives no sign of where each name comes from. Chapter 29's `classtree.py` climbs inheritance trees with straightforward code. The mix-in in `listtree.py` uses the same technique.

It shows attributes grouped by the classes they live in. It sketches the full class tree and lists the attributes of each object on the way.

The reader still has to work out which attributes are inherited. The final section of this chapter helps with that. Even so, this version gives much more detail than a flat list.

File `listtree.py`

```python
class ListTree:
    """
    Mix-in that returns a __str__ trace of the entire class tree and all
    its objects' attrs at and above the self instance. The display is
    run by print() automatically; use str() to fetch as a string. This:
    -Uses __X pseudoprivate attr names to avoid conflicts with clients
    -Recurses to superclasses explicitly in DLFR (though not MRO) order
    -Uses __dict__ instead of dir() because attrs are listed per object
    -Supports classes with slots: lack of slots here ensures a __dict__
    """
    def __attrnames(self, obj, indent, unders=True):
        spaces = ' ' * (indent + 1)
        result = ''
        for attr in sorted(obj.__dict__):
            if attr.startswith('__') and attr.endswith('__'):
                if unders: result += f'{spaces}{attr}\n'
            else:
                result += f'{spaces}{attr}={getattr(obj, attr)!r}\n'
        return result
    def __listclass(self, aClass, indent):
        dots = '.' * indent
        preamble = (f'\n{dots}'
                    f'<Class {aClass.__name__}'
                    f', address {id(aClass):#x}')
        if aClass in self.__visited:
            return preamble + ': (see above)>\n'  # Already listed
        elif aClass is object:
            self.__visited[aClass] = True
            return preamble + ': (see dir(object))>\n'  # Skip object's 24
        else:
            self.__visited[aClass] = True
            here = self.__attrnames(aClass, indent)  # My attrs + supers
            above = ''
            for Super in aClass.__bases__:
                above += self.__listclass(Super, indent + 4)
            return preamble + f':\n{here}{above}{dots}>\n'
    def __str__(self):
        self.__visited = {}
        here = self.__attrnames(self, 0)  # My attrs
        above = self.__listclass(self.__class__, 4)  # My supers tree
        return (f'<Instance of {self.__class__.__name__}'  # My class's name
                f', address {id(self):#x}'  # My address (hex)
                f':\n{here}{above}>')  # attrs + supers
if __name__ == '__main__':
    import testmixin
    testmixin.tester(ListTree)  # Test class in this module
```

The class walks the inheritance tree. It starts at the instance's `__class__`. Then it follows each class's `__bases__` to every superclass, recursively. At each object it scans the `__dict__` for attributes. As the recursion unwinds, it joins the strings from each part of the tree.

Recursive code like this takes a while to understand. Read it twice before you run it. Class trees have arbitrary shapes and depths, so recursion is the natural choice here. An explicit stack would work too, as in Chapters 19 and 25. It is usually no simpler, so we skip it. The class keeps its logic explicit to maximize clarity.

Run the module file to test it. The file passes `ListTree` to the `testmixin.py` tester, which mixes it into a subclass. The tree sketch looks like this, with indentation showing depth.

```text
$ python3 listtree.py
<Instance of Sub, address 0x10a45f980:
_ListTree__visited={}
data1='code'
data2='Python'
data3=3.12
....<Class Sub, address 0x7fb26a448530:
__doc__
__init__
__module__
method2=<function tester.<locals>.Sub.method2 at 0x10a482ac0>
........<Class Super, address 0x7fb26a445c00:
__dict__
__doc__
__init__
__module__
__weakref__
method1=<function tester.<locals>.Super.method1 at 0x10a4823e0>
............<Class object, address 0x10a01b100: (see dir(object))>
........>
........<Class ListTree, address 0x7fb26a443d20:
_ListTree__attrnames=<function ListTree.__attrnames at 0x10a480f40>
_ListTree__listclass=<function ListTree.__listclass at 0x10a480fe0>
__dict__
__doc__
__module__
__str__
__weakref__
............<Class object, address 0x10a01b100: (see above)>
........>
....>
>
```

A few points are worth noticing in this output. The `__visited` table is mangled in the instance dictionary, as a pseudoprivate name. Unless you are unlucky, it will not clash with other data there. Some of the lister's own methods are mangled too.

To keep the display short, `__X__` attributes appear by name only, without values. The implied `object` class above every top class gets a single line. That line points you to its `dir` result. The `object` class has 24 attributes, which would be wasteful to repeat in every display.

The attributes that were bound methods in the previous version now appear as plain functions. This version fetches methods from the classes, not from the instance. The `getattr` call runs on the current tree object whose `__dict__` is being scanned. In this context, `getattr` and `__dict__` indexing are equivalent.

Class methods are plain functions. They become bound only when you fetch them through an instance.

The `visited` table prevents listing a class twice. A dictionary works because class objects are hashable, so they can be keys. A set would also work.

Cycles are not normally possible in a class tree. A superclass must already exist before you name it. Python also raises an exception if you try to create a cycle later by changing `__bases__`. The visited table is still needed, because it stops a class from being listed twice.

```text
>>> class C: pass
>>> class B(C): pass
>>> C.__bases__ = (B,)  # Dark magic
TypeError: a __bases__ item causes an inheritance cycle
```

This class also works with bigger classes. Try mixing it into the `Button` class from the `tkinter` GUI module. In a `class` header, put `ListTree` first, on the left. That way its `__str__` is found first.

`Button` has a `__str__` too. In multiple inheritance, the leftmost superclass is searched first.

```text
>>> from tkinter import Button
>>> from listtree import ListTree
>>> class ButtonPlus(ListTree, Button): pass  # ListTree's str, not Button's
>>> print(ButtonPlus())
…our class's display…
>>> class ButtonPlus(Button, ListTree): pass  # Mix-in order can matter!
>>> print(ButtonPlus())
.!buttonplus2
```

Order matters in multiple inheritance. A manual override can force the choice, and the line below does it in one assignment.

```text
>>> class ButtonPlus(Button, ListTree): __str__ = ListTree.__str__
…our class's display…
```

You can also run `testmixin.py` directly. Its self-test runs the three lister classes in turn, using their module and class name strings. It is a small class factory in action.

```text
$ python3 testmixin.py
…all three listers' results…
```

The tree lister works as planned. It does not fully follow the MRO through trees with diamonds, though. It sketches the DFLR order and leaves readers to work out where each attribute comes from. The next example fixes that.

##### Example: mapping attributes to inheritance sources

This example shows the MRO in a programming tool. The tree lister shows where attributes sit in the physical tree. By matching the `dir` results to the linear MRO sequence, a tool can name the class each inherited attribute really comes from. Programmers find that useful too.

The `mapattrs.py` version starts that work in `mapattrs.py`. Its `mapattrs` function shows how inheritance really searches the class tree. The MRO is handled for us by the built-in `__mro__` attribute.

File `mapattrs.py`

```python
"""
Main tool: mapattrs() maps all attributes on or inherited by an
instance to the instance or class from which they are inherited.
Also here: assorted dictionary tools using comprehensions.
Assumes dir() gives all attributes of an instance. To emulate
inheritance, this uses the class's __mro__ tuple, which gives the
MRO search order for classes in Python 3.X. A recursive tree
traversal for the DFLR order of classes is included but unused.
"""
import pprint
def trace(label, X, end='\n'):
    print(f'{label}\n{pprint.pformat(X)}{end}')  # Print nicely
def filterdictvals(D, V):
    """
    dict D with entries for value V removed.
    filterdictvals(dict(a=1, b=2, c=1), 1) => {'b': 2}
    """
    return {K: V2 for (K, V2) in D.items() if V2 != V}
def invertdict(D):
    """
    dict D with values changed to keys (grouped by values).
    Values must all be hashable to work as dict/set keys.
    invertdict(dict(a=1, b=2, c=1)) => {1: ['a', 'c'], 2: ['b']}
    """
    def keysof(V):
        return sorted(K for K in D.keys() if D[K] == V)
    return {V: keysof(V) for V in set(D.values())}
def dflr(cls):
    """
    Depth-first left-to-right order of class tree at cls.
    Cycles not possible: Python disallows on __bases__ changes.
    """
    here = [cls]
    for sup in cls.__bases__:
        here += dflr(sup)
    return here
def inheritance(instance):
    """
    Inheritance order sequence: MRO or DFLR.
    DFLR alone is no longer used in Python 3.X.
    """
    if hasattr(instance.__class__, '__mro__'):
        return (instance,) + instance.__class__.__mro__
    else:
        return [instance] + dflr(instance.__class__)
def mapattrs(instance, withobject=False, bysource=False):
    """
    dict with keys giving all inherited attributes of instance,
    with values giving the object that each is inherited from.
    withobject: False=remove object built-in class attributes.
    bysource: True=group result by objects instead of attributes.
    Supports classes with slots that preclude __dict__ in instances.
    """
    attr2obj = {}
    inherits = inheritance(instance)
    for attr in dir(instance):
        for obj in inherits:
            if hasattr(obj, '__dict__') and attr in obj.__dict__:  # Slots okay
                attr2obj[attr] = obj
                break
    if not withobject:
        attr2obj = filterdictvals(attr2obj, object)
    return attr2obj if not bysource else invertdict(attr2obj)
if __name__ == '__main__':
    class D: attr2 = 'D'
    class C(D): attr2 = 'C'
    class B(D): attr1 = 'B'
    class A(B, C): pass
    I = A()
    I.attr0 = 'I'
    print(f'Py=>{I.attr0=}, {I.attr1=}, {I.attr2=}\n')  # Python's search
    trace('INHERITANCE', inheritance(I))  # [Inheritance order]
    trace('ATTRIBUTES', mapattrs(I))  # {Attr => Source}
    trace('SOURCES', mapattrs(I, bysource=True))  # {Source => [Attrs]}
```

The main `mapattrs` function uses `dir` to collect every attribute an instance has. For each name, it finds the source by scanning the MRO in the `__mro__` of the instance's class. At each object it checks the namespace in `__dict__`. The result copies Python's real search for each attribute reachable from the instance.

The self-test applies these tools to a diamond tree like the ones above. The `pprint` standard-library module displays the lists and dictionaries neatly. `pprint.pprint` prints them, and `pprint.pformat` returns the text.

The attribute `attr2` is defined in `C` and `D`. The output shows that it comes from `C`, as the MRO predicts.

```text
$ python3 mapattrs.py
Py=>I.attr0='I', I.attr1='B', I.attr2='C'
INHERITANCE
(<__main__.A object at 0x10cc33e00>,
 <class '__main__.A'>,
 <class '__main__.B'>,
 <class '__main__.C'>,
 <class '__main__.D'>,
 <class 'object'>)
ATTRIBUTES
{'__dict__': <class '__main__.D'>,
 '__doc__': <class '__main__.A'>,
 '__module__': <class '__main__.A'>,
 '__weakref__': <class '__main__.D'>,
 'attr0': <__main__.A object at 0x10cc33e00>,
 'attr1': <class '__main__.B'>,
 'attr2': <class '__main__.C'>}
SOURCES
{<__main__.A object at 0x10cc33e00>: ['attr0'],
 <class '__main__.D'>: ['__dict__', '__weakref__'],
 <class '__main__.C'>: ['attr2'],
 <class '__main__.B'>: ['attr1'],
 <class '__main__.A'>: ['__doc__', '__module__']}
```

`mapattrs.py` is not built as a mix-in. Still, listers can use its results. They can look up an attribute's source, or the attributes of a source. Wrapping the results in a `__str__` turns it into a mix-in. The next session lists the sources in the test classes from `testmixin.py`.

```text
$ python3
>>> import pprint
>>> from mapattrs import mapattrs
>>> class ListAttr2Source:
...     def __str__(self):
...         return pprint.pformat(mapattrs(self))
>>> from testmixin import tester
>>> tester(ListAttr2Source)
{'__dict__': <class 'testmixin.tester.<locals>.Super'>,
 '__doc__': <class 'testmixin.tester.<locals>.Sub'>,
 '__init__': <class 'testmixin.tester.<locals>.Sub'>,
 '__module__': <class 'testmixin.tester.<locals>.Sub'>,
 '__str__': <class '__main__.ListAttr2Source'>,
 '__weakref__': <class 'testmixin.tester.<locals>.Super'>,
 'data1': <testmixin.tester.<locals>.Sub object at 0x102a8fa40>,
 'data2': <testmixin.tester.<locals>.Sub object at 0x102a8fa40>,
 'data3': <testmixin.tester.<locals>.Sub object at 0x102a8fa40>,
 'method1': <class 'testmixin.tester.<locals>.Super'>,
 'method2': <class 'testmixin.tester.<locals>.Sub'>}
```

Listing the attributes of each source is just as easy. The same data is grouped the other way round. The `pprint` options, such as `compact` and `width`, change the layout.

```text
>>> class ListSource2Attr:
...     def __str__(self):
...         return pprint.pformat(mapattrs(self, bysource=True))
>>> tester(ListSource2Attr)
{<testmixin.tester.<locals>.Sub object at 0x102ad12e0>: ['data1',
                                                          'data2',
                                                          'data3'],
 <class 'testmixin.tester.<locals>.Super'>: ['__dict__',
                                             '__weakref__',
                                             'method1'],
 <class 'testmixin.tester.<locals>.Sub'>: ['__doc__',
                                           '__init__',
                                           '__module__',
                                           'method2'],
 <class '__main__.ListSource2Attr'>: ['__str__']}
```

Study this example for more ideas. It uses `hasattr` to check whether an object has a `__dict__` before it indexes the dictionary. Some instances have no `__dict__`, because they use `__slots__`. Slots are the class extension covered earlier.

`ListTree` and `ListInstance` work with slots as they are. Their own lack of slots guarantees an instance `__dict__`. `ListInherited` can fail for slots that were never assigned. Chapter 32 clarifies these findings.

Other "virtual" attributes live on the class, not the instance. Properties and descriptors are examples, and so are slots. These may need generic handling. Tools can use `dir`, `getattr`, tree climbs, or MRO scans.

The examples in this section handle them, but not evenly. Some names are linked to the class where their code lives, not to the instance used to reach them.

No lister can show attribute names that methods such as `__getattr__` compute on the fly. Those names have no physical location to report. A class can define a `__dir__` method to control what `dir` returns. General tools cannot rely on that optional method being present.

Finally, the attribute listers and mappers here work for normal instances. They do not work for classes. Printing a class gives the default display. The `mapattrs` function also attributes many names to a class called `type`. The listers skip classes because `print` skips the "instance" of a class.

The `type` oddity comes from the fact that a class gets names from two trees. One is its own superclass tree and MRO. The other is a tree formed by metaclasses, which Chapter 32 covers.

To understand the split caused by metaclasses, and special attributes such as slots, properties, and descriptors, we move on to the next chapter.

### Other design-related topics

This chapter sampled several design patterns for combining classes. It only scratches the surface of design, though. Other chapters cover related topics, and the list below is a map for later reading.

- Abstract superclasses (Chapter 29)
- Decorators (Chapters 32 and 39)
- Type subclasses (Chapter 32)
- Static and class methods (Chapter 32)
- Managed attributes (Chapters 32 and 38)
- Metaclasses (Chapters 32 and 40)

Design patterns are important in OOP, and they fit Python more naturally than many other languages. They are not specific to Python, though. This book refers you to other OOP resources for more. Experience teaches most of them best.

### Chapter summary: designing with classes

This chapter was about composing classes into larger designs, not about syntax. It covered common ways to use and combine classes. The goal is reuse and better factoring, which are design issues. They are mostly independent of the language, although Python makes them easier to implement.

We studied inheritance, which acquires behavior from other classes. We studied composition, which controls embedded objects. We studied delegation, which wraps objects in proxy classes. We also covered pseudoprivate attributes, bound methods, factories, multiple inheritance, and the MRO.

The next chapter finishes our look at classes. It surveys class-related topics that are more advanced than what we have seen. Some of that material interests tool writers more than application programmers. Most people who write OOP in Python should still review it, to understand code they reuse.

## Extending built-in types

Classes are sometimes used to extend Python's built-in types. A plain list can store items, but it cannot enforce rules such as keeping items unique. A class can add that behavior.

There are two ways to do it: wrap a built-in object inside your own class, or subclass the built-in type directly. The next two sections show both, and the second one also explains why it is possible at all.

### Extending types by embedding

Earlier chapters wrote set functions that took lists as arguments. Here is the same idea as a class. The class in `setwrapper.py` moves those functions into methods and adds some operator overloading. Most of its work is done by a list it keeps inside.

Because it is a class, you can make several independent sets. Each one holds its own data and can be customized through inheritance. The list inside is the storage, and the class is the interface.

```python
class Set:
    def __init__(self, value=[]):           # Constructor
        self.data = []                      # Manages a list
        self.concat(value)                  # Removes duplicates
    def intersect(self, other):             # other is any iterable
        res = []                            # self is the subject
        for x in self.data:
            if x in other:                  # Pick common items
                res.append(x)
        return Set(res)                     # Return a new Set
    def union(self, other):                 # other is any iterable
        res = self.data[:]                  # Copy of my list
        for x in other:                     # Add items in other
            if not x in res:
                res.append(x)
        return Set(res)
    def concat(self, value):                # value: list, Set...
        for x in value:                     # Removes duplicates
            if not x in self.data:
                self.data.append(x)
    def __len__(self): return len(self.data)                # len(self), if self
    def __getitem__(self, key): return self.data[key]       # self[i], self[i:j]
    def __and__(self, other): return self.intersect(other)  # self & other
    def __or__(self, other): return self.union(other)       # self | other
    def __repr__(self): return f'Set({self.data!r})'        # print(self),...
    def __iter__(self): return iter(self.data)              # for x in self,...
```

You use this class the same way as any other class. You make instances, call methods, and run the operators it defines.

```text
$ python3
>>> from setwrapper import Set
>>> x = Set([1, 3, 5, 7, 3])
>>> x.union(Set([1, 4, 7]))
Set([1, 3, 5, 7, 4])
>>> x | Set([1, 4, 6, 4])
Set([1, 3, 5, 7, 4, 6])
```

Overloading indexing and iteration lets a `Set` act much like a real list. Keep this class in mind. The exercises at the end of the chapter ask you to extend it.

### Extending types by subclassing

Embedding works, but Python's built-in types can also be subclassed directly. Type-conversion calls such as `list('text')` are really calls to a type's constructor. Each of those names is a class you can subclass.

An instance of your subclass can usually be used anywhere the original built-in type can appear. Suppose you dislike that list offsets start at 0. You can subclass `list` and change that one behavior.

```python
"""
Subclass built-in list type/class.
Map 1..N to 0..N-1, call back to built-in version.
"""
class MyList(list):
    def __getitem__(self, offset):
        print(f'<indexing {self} at {offset}>')
        return list.__getitem__(self, offset - 1)

if __name__ == '__main__':
    print(list('abc'))
    x = MyList('abc')            # __init__ inherited from list
    print(x)                     # __str__/__repr__ inherited from list
    print(x[1])                  # MyList.__getitem__
    print(x[3])                  # Customizes list superclass method
    x.append('hack!'); print(x)  # Attributes from list superclass
    x.reverse(); print(x)
```

The subclass changes only `__getitem__`. It decrements the index and then calls the built-in version. Everything else comes from `list`, including the constructor, the printing and the append method.

```text
$ python3 typesubclass.py
['a', 'b', 'c']
['a', 'b', 'c']
<indexing ['a', 'b', 'c'] at 1>
a
<indexing ['a', 'b', 'c'] at 3>
c
['a', 'b', 'c', 'hack!']
['hack!', 'c', 'b', 'a']
```

The trace text comes from the print call inside `__getitem__`. Changing indexing this way is a powerful tool. It is also confusing, because users of `MyList` expect normal sequence behavior. Use it with care.

The same pattern gives another way to build a set. You can subclass `list` instead of wrapping one. Python already has a built-in `set` type, as Chapter 5 showed. Writing your own is still a good way to learn how type subclassing works.

The file `setsubclass.py` adds only the set methods and operators. Everything else is inherited from `list`.

```python
class Set(list):
    def __init__(self, value=[]):           # Constructor
        list.__init__(self)                 # Customizes list
        self.concat(value)                  # Copies mutable defaults
    def intersect(self, other):             # other is any iterable
        res = []                            # self is the subject
        for x in self:
            if x in other:                  # Pick common items
                res.append(x)
        return Set(res)                     # Return a new Set
    def union(self, other):                 # other is any iterable
        res = Set(self)                     # Copy me and my list
        res.concat(other)
        return res
    def concat(self, value):                # value: list, Set, etc.
        for x in value:                     # Removes duplicates
            if not x in self:
                self.append(x)
    def __and__(self, other): return self.intersect(other)
    def __or__(self, other): return self.union(other)
    def __repr__(self): return f'Set({list.__repr__(self)})'

if __name__ == '__main__':
    x = Set([1, 3, 5, 7])
    y = Set([2, 1, 4, 5, 6])
    print(x, y, len(x))
    print(x.intersect(y), y.union(x))
    print(x & y, x | y)
    x.reverse(); print(x)
```

Here is the self-test output from the end of the file. Notice that `reverse` works with no code from the new class, because it comes from `list`.

```text
$ python3 setsubclass.py
Set([1, 3, 5, 7]) Set([2, 1, 4, 5, 6]) 4
Set([1, 5]) Set([2, 1, 4, 5, 6, 3, 7])
Set([1, 5]) Set([1, 3, 5, 7, 2, 4, 6])
Set([7, 5, 3, 1])
```

Some inherited list operations can add duplicates to this `Set`. The nested searches also make it slower than a dictionary-based design. Sets are fun to experiment with, but you do not need them in Python today. Use the built-in `set` for real work.

Why can we subclass `list` at all? The next section answers that question, and the answer is the foundation of Python's object model.

## The Python object model

The short answer is that a type is a class, and a class is a type. The reason we could subclass built-in types is that types and classes are largely the same thing. This unification came with the new-style class model.

For built-ins, some instances have literal syntax, such as `[]`, `'lp6e'`, and `3.12`. Instead of calling `list()` or `str()`, you write the value directly. These values are still instances of a class.

Built-in types and user-defined classes are both classes. Both are also instances of the built-in `type` class. A `type` object creates classes as its instances. A class creates instances of itself. The built-in `object` class supplies defaults for every object.

### Classes are types are classes

You can see this in code. With one argument, `type` returns any object's type. That is normally the same as the object's `__class__`. The `isinstance` function checks whether an object inherits from a given class.

```text
>>> class Hack: pass            # A humble user-defined class
>>> I = Hack()                  # Make an instance by calling the class
>>> type(I)                     # Type is the user-defined class of origin
<class '__main__.Hack'>
>>> type(Hack)                  # User-defined classes are instances of type
<class 'type'>
>>> I.__class__, Hack.__class__
(<class '__main__.Hack'>, <class 'type'>)
>>> isinstance(I, object), isinstance(Hack, object)
(True, True)
```

Built-in types work the same way. They are classes too, but they also have literal syntax for making instances. Replace the user-defined class with `str` and every line still holds.

```text
>>> I = 'hack'                  # Make an instance by literal syntax, or str()
>>> type(I)                     # Built-in objects are instances of classes
<class 'str'>
>>> type(str)                   # Built-in classes are instances of type
<class 'type'>
>>> I.__class__, str.__class__
(<class 'str'>, <class 'type'>)
>>> isinstance(I, object), isinstance(str, object)
(True, True)
```

The `type` class ends the chain. It reports itself as a class, so the chain loops back on itself.

```text
>>> type(type)                  # The type class ends the chain
<class 'type'>
>>> type(type(type))            # Hmm...the top of the chain
<class 'type'>
```

This model can seem academic. It still matters in two ways. It lets you specialize built-in types with normal class statements. It also affects type-testing code, because you must know what a type is before you can test for it correctly.

### Some instances are more equal than others

It is tempting to conclude that classes and types are the same. The full story is richer. The instances you make from these objects differ in both behavior and inheritance.

A metaclass is a class that creates other classes. The `type` built-in is itself a metaclass, and you can customize it with subclasses. You select a metaclass with special syntax in a class header. Metaclasses are covered in full in Chapter 40. For now, here is how instances, classes, and types fit together.

- Instances are created from classes, both built-in and user-defined.
- Classes are created from the built-in `type` class or one of its subclasses.
- The `object` built-in class is a superclass of every object, whether it is an instance, a class, or both.

Everything is ultimately an instance in Python. Even so, there are two different kinds of instances, and mixing them up hides how the model really works. The real split is not about user-defined classes. It is about how a class is created. Classes are created from `type` in a special way.

A class can name its metaclass in the header. If you omit it, the metaclass defaults to `type`. Other instances get their types from a class call or a literal.

```text
class C(metaclass=Meta): ...    # Class creation: metaclass defaults to "type"
I = C(...)                      # Instance creation: user-defined classes
X = [1, 2]                      # Instance creation: built-in classes
```

These statements all produce instances in some sense. They still create two very different kinds of objects, and the difference explains several odd results later.

Nonclass instances do not make instances. Classes are created from `type`, much as instances are created from classes. Once created, though, the analogy fails. A class creates instances of its own. A nonclass instance does not.

Classes also get an extra inheritance search. Python has two inheritance trees, which are distinct but not completely separate. The second tree is formed by `type` and its subclasses. Python searches it only for classes, never for nonclass instances.

### The inheritance bifurcation

Inheritance for a class is a two-stage search, and that is the heart of the model. Inheritance for classes differs from inheritance for nonclass instances. This difference may be the most important one in the model. Inheritance always follows the MRO you studied earlier, in the multiple inheritance section. The search order changes depending on what you are searching.

For a nonclass instance, Python checks the instance's `__dict__` first. It then follows `__class__` to the class and walks the class's `__bases__` to its superclasses. Python uses `__bases__` to build the `__mro__` that inheritance scans.

Inheritance run on a class works in two steps. First, Python searches the class and its superclasses, as usual. If the name is still missing, it searches the separate class tree formed by `type` and its metaclass subclasses. That second tree is used only as a last resort, and only for lookups on classes.

You can inspect these sources if you know where to look. The output is not pretty, but it shows the difference.

```text
>>> isinstance(I, C), type(I)
(True, <class '__main__.C'>)
>>> I, I.__class__, I.__class__.__bases__
(<__main__.C object at 0x101265d60>, <class '__main__.C'>, (<class 'object'>,))
>>> C, C.__bases__, C.__class__, C.__class__.__bases__
(<class '__main__.C'>, (<class 'object'>,), <class 'type'>, (<class 'object'>,))
```

Each `__mro__` is a flattened version of the tree. These lines show the search order for the instance and for the class, side by side.

```text
>>> I, I.__class__.__mro__
(<__main__.C object at 0x101265d60>, (<class '__main__.C'>, <class 'object'>))
>>> C.__mro__, C.__class__.__mro__
((<class '__main__.C'>, <class 'object'>), (<class 'type'>, <class 'object'>))
```

Inheritance checks the `__dict__` of each item in these lists. For a nonclass instance, the search is the instance's dictionary followed by the dictionaries of its class's MRO. For a class, the search is the MRO of the class and then the MRO of its metaclass tree. Some descriptors take precedence in both trees. You will learn about them in Chapter 40.

The second tree sounds like a complication, and it is. Most application code never touches it. It explains a surprising result, though. Some class attributes, such as `__bases__`, are not inherited by instances. They live in the second tree.

```text
>>> '__bases__' in I.__dict__            # Not in instance
False
>>> '__bases__' in C.__dict__            # Not in instance's class
False
>>> '__bases__' in C.__class__.__dict__  # In instance's class's class
True
```

Because of this two-tree model, names that classes inherit are not passed down to their instances. The error message below even suggests the attribute you probably meant.

```text
>>> C.__bases__                 # Instance does not inherit!
(<class 'object'>,)
>>> I.__bases__
AttributeError: 'C' object has no attribute '__bases__'. Did you mean: '__class__'?
```

### The metaclass/class dichotomy

Where does this leave us? Types behave as classes. You can extend them with normal class syntax in the primary tree and the metaclass tree. The model also has visible seams. There is special syntax for creating classes. There is an extra search for classes only. There are two very different kinds of instances. Metaclasses also have unique rules for customizing classes.

Some people argue that the old type/class split of earlier Pythons has simply turned into a metaclass/class split. That trades a clear distinction for several seams. It also complicates inheritance and the meaning of names. All of this supports a rare use case. You must decide whether that trade is worth it.

Part of the confusion comes from `type` itself. It has two roles. With one argument, it returns the type of an object. With three arguments, it creates a new class. The second role is what a `class` statement does behind the scenes.

```python
type(object)                             # Fetch object type
type(classname, superclasses, attributedict)  # Make a class/type
```

The first role might have been better named "typeof." The second role leads into the metaclass material in Chapter 40.

### One object to rule them all

Every class inherits from the built-in `object` class, directly or through a superclass. This is true even when you do not write `object` yourself, and the two forms below behave identically.

```text
>>> class C: pass
>>> class D(object): pass
>>> dir(C) == dir(D)
True
>>> C.__bases__, D.__bases__
((<class 'object'>,), (<class 'object'>,))
```

The `type` class inherits from `object`. But `object` is an instance of `type`, so the two relationships form a circle. The two objects are different, though, and the checks below keep them apart.

```text
>>> type is object
False
>>> type(type), type(object)
(<class 'type'>, <class 'type'>)
>>> isinstance(type, object), isinstance(object, type)
(True, True)
>>> type.__bases__, object.__bases__
((<class 'object'>,), ())
```

In `isinstance`, a result is True for a subclass relationship or a creation source. For classes, this result depends on inheritance through the secondary type tree.

This has practical effects. You must remember the default methods that come from `object`. For example, `object` provides a `__repr__` for display.

```text
>>> class C: pass              # All classes inherit object defaults
>>> X = C()
>>> X.__repr__
<method-wrapper '__repr__' of C object at 0x1091a7920>
```

The `object` root also lets you write code that assumes an `object` superclass. You can count on it as the end of a call chain. You can also reroute attribute-interception methods to it, so the default behavior runs. For example, the earlier chapter on operator overloading used this form.

```python
object.__setattr__(self, attr, value)
```

## Advanced attribute tools

Besides normal class and instance attributes, Python has attribute tools with narrower scope. These include slots, properties, and descriptors. Slots are an optimization. Properties and descriptors change how attribute access works.

None of these tools are required. You may still meet them in code you read. Chapter 38 covers properties and descriptors in depth. Slots get full coverage here.

### Slots: attribute declarations

You have seen the effects of slots several times in this part of the book. In short, you assign a list of attribute names to the special `__slots__` class attribute. This limits which attributes instances can have. It can also save memory and sometimes speed up code.

Slots add complexity, though. They can break code that you did not write. They also work only when every class in the tree uses them. Use them only when the application clearly needs them.

Slot basics

Assign an iterable of attribute names to `__slots__` at the top level of a class statement. Only those names can be assigned as instance attributes. Slots do not change how these attributes work. Like all names in Python, an attribute must be assigned before it is read, even if it is listed in `__slots__`.

```text
>>> class Limiter:
...     __slots__ = ['age', 'name', 'job']  # Slots "declaration"
>>> I = Limiter()
>>> I.age                       # Must assign before use
AttributeError: 'Limiter' object has no attribute 'age'
>>> I.age = 40                  # Looks like instance data
>>> I.age
40
>>> I.ape = 1000                # Fails: not in __slots__
AttributeError: 'Limiter' object has no attribute 'ape'
```

Slots serve two purposes. They catch typos, because assignments to names outside `__slots__` raise an error instead of creating a new attribute. They also save memory. Every instance normally gets a namespace dictionary, and that dictionary is costly when you make many instances with only a few attributes.

With slots, Python reserves just enough space in each instance for the slot values. The speed benefit depends on the program, the platform, and the Python version. As you will see, the speed gain is small today.

You should not use slots by default

Slots break Python's dynamic nature. Python normally lets any name be created by assignment. Slots partly imitate C++ for efficiency, and they can break some programs. They also come with many special rules.

Python's own manual says to use slots only when clearly justified. The reasons are plain. They are hard to deploy correctly. They complicate code. They are best left to rare, memory-critical programs that create very large numbers of instances. Slots still show up in Python code more often than they should. Be wary of them, and check whether you really need them.

#### Slots and namespace dictionaries

Slots move data out of the instance dictionary, and that changes what code can rely on. Slots change how an instance stores its data. Some instances with slots have no `__dict__` at all. Others keep some data outside `__dict__`. This is a major break from the traditional class model. Code that reads attributes by name may fail.

With slots, an instance usually has no attribute dictionary. Python manages the slot storage through class descriptors. The values live in reserved space inside the object, not in a dictionary keyed by name.

```text
>>> class C:
...     __slots__ = ['a', 'b']  # __slots__ means no __dict__ by default
>>> I = C()
>>> I.a = 1
>>> I.a
1
>>> I.__dict__
AttributeError: 'C' object has no attribute '__dict__'. Did you mean: '__dir__'?
```

You can still get and set slot attributes with the storage-neutral tools `getattr` and `setattr`. The `dir` function lists them too.

```text
>>> getattr(I, 'a')
1
>>> setattr(I, 'b', 2)          # But getattr() and setattr() still work
>>> I.b
2
>>> 'a' in dir(I)               # And dir() finds slot attributes too
True
>>> 'b' in dir(I)               # Though __dict__ access will fail
True
```

Without a namespace dictionary, you cannot add new names that are not in `__slots__`.

```python
class D:
    __slots__ = ['a', 'b']
    def __init__(self):
        self.d = 4              # Cannot add new names if no __dict__
```

You can add a dictionary back by listing `__dict__` in `__slots__`. Then the instance has both kinds of storage.

```python
class D:
    __slots__ = ['a', 'b', '__dict__']   # Name __dict__ to include one too
    c = 3                                # Class attrs work normally
    def __init__(self):
        self.d = 4                       # d stored in __dict__, a is a slot
```

```text
>>> I = D()
>>> I.d
4
>>> I.c
3
>>> I.a                         # All instance attrs undefined until assigned
AttributeError: 'D' object has no attribute 'a'
>>> I.a = 1
>>> I.b = 2
>>> I.__dict__                  # Some objects have both __dict__ and slot names
{'d': 4}
>>> I.__slots__
['a', 'b', '__dict__']
>>> getattr(I, 'a'), getattr(I, 'c'), getattr(I, 'd')   # Fetches all 3 forms
(1, 3, 4)
```

Now both storage forms exist, and `__dict__` alone is too narrow. Generic tools such as `getattr` can still treat both forms as one set of attributes. The `dir` function is broader. It also includes methods and all the `object` defaults.

A program that lists only instance attributes needs to handle both forms. A first attempt might look like this.

```python
for attr in list(I.__dict__) + I.__slots__:   # Wrong...
    print(attr, '=>', getattr(I, attr))
```

Either source may be missing, so you can use `getattr` with defaults. This version is less wrong, but it is still not complete.

```python
for attr in list(getattr(I, '__dict__', [])) + getattr(I, '__slots__', []):
    print(attr, '=>', getattr(I, attr))
```

```text
d => 4
a => 1                          # Less wrong...
b => 2
__dict__ => {'d': 4}
```

#### Multiple `__slots__` lists in superclasses

The previous code works in one case, but not in general. It looks only at the lowest `__slots__` attribute that an instance inherits. A class tree can have several `__slots__` lists. A name missing from the lowest list can still appear in a higher one. Each slot name becomes a class-level attribute, so an instance gets the union of all slot names in the tree.

```python
class E:
    __slots__ = ['c', 'd']                 # Superclass has slots

class D(E):
    __slots__ = ['a', '__dict__']          # But so does its subclass
```

```text
>>> I = D()                     # The instance gets the union of each
>>> dir(I)
[...names omitted..., 'a', 'c', 'd']
>>> I.a = 1; I.b = 2; I.c = 3   # slots: a, c, __dict__: b
>>> I.a, I.c
(1, 3)
>>> E.__slots__                 # But __slots__ not concatenated
['c', 'd']
>>> D.__slots__
['a', '__dict__']
>>> I.__slots__                 # Instance inherits *lowest* __slots__
['a', '__dict__']
>>> I.__dict__                  # And has its own attr dict
{'b': 2}
>>> for attr in list(getattr(I, '__dict__', [])) + getattr(I, '__slots__', []):
...     print(attr, '=>', getattr(I, attr))
b => 2                          # Other superclass slots missed!
a => 1
__dict__ => {'b': 2}
>>> dir(I)                      # But dir() includes all slot names
[...names omitted..., 'a', 'b', 'c', 'd']
```

Inspecting only the inherited `__slots__` list misses slots defined higher in the tree. Listing instance attributes generically means facing the full inheritance search. Tools must choose a policy for this.

#### Handling slots and other "virtual" attributes generically

Tools that list instance data must handle slots. They must also handle other "virtual" attributes, such as properties and descriptors. These names live in classes, but they can supply values for instances on request. Slots are the most data-centric of this group.

These attributes need one of three approaches. You can include them with an inclusive method. You can treat them with special handling. Or you can avoid them, which becomes unsatisfactory once any code uses slots.

Class-level instance attributes like slots push us to redefine "instance data." It can mean locally stored attributes, all inherited attributes, or some subset of them.

Some programs treat slot names as class attributes instead. The slot values do not live in instance dictionaries, after all. A more inclusive program uses `dir` to find all inherited names and `getattr` to read their values. This works without caring where a value is stored. If you must support slots as instance data, this is the most robust approach.

```text
>>> class Slotful:
...     __slots__ = ['a', 'b', '__dict__']
...     def __init__(self, data):
...         self.c = data
>>> I = Slotful(3)
>>> I.a, I.b = 1, 2
>>> I.a, I.b, I.c               # Normal attribute fetch
(1, 2, 3)
>>> I.__dict__                  # Both __dict__ and slots storage
{'c': 3}
>>> [x for x in dir(I) if not x.startswith('__')]
['a', 'b', 'c']
>>> I.__dict__['c']             # __dict__ is only one attr source
3
>>> getattr(I, 'c'), getattr(I, 'a')    # dir+getattr is broader than __dict__
(3, 1)                          # applies to slots, properties, descriptors
>>> for a in (x for x in dir(I) if not x.startswith('__')):
...     print(a, '=>', getattr(I, a))
a 1
b 2
c 3
```

With this `dir` and `getattr` model, you can still map attributes to their inheritance sources. You can filter them by source or type by scanning the MRO. The mapattrs tool from the earlier chapter on attributes does this. Properties and descriptors are more clearly computed values. This approach works for them too.

Slots also affect the `__setattr__` method from the earlier chapter on operator overloading. Slots and some other attributes are not stored in `__dict__`. Sometimes `__dict__` does not exist at all. Because of this, a class's `__setattr__` often sends assignments to the `object` superclass.

#### Slot usage rules

Slot declarations can appear in several classes in a tree. When they do, a set of constraints applies. These rules are hard to explain unless you understand the implementation. Each slot name is a class-level descriptor. Instances inherit that descriptor, and the space for the value is reserved in the instance. Here are the main constraints.

- Slots in a subclass are pointless when the superclass has none. The superclass creates an instance `__dict__`, and that dictionary is always accessible. The subclass still manages its slots, but it does not avoid the dictionary. Avoiding the dictionary is the main reason to use slots.
- Slots in a superclass are pointless when the subclass has none. A `__slots__` declaration applies only to the class where it appears. A subclass without `__slots__` creates an instance `__dict__`.
- Redefinition hides a superclass slot. If a class defines a slot name that its superclass also defines, the new definition hides the old one, as normal inheritance does. You can reach the superclass version only by fetching its descriptor directly from the superclass.
- Slots prevent class-level defaults. Slots are class-level descriptors. A class attribute with the same name overwrites the slot descriptor. You cannot use a class attribute as a default the way you can for normal instance attributes.
- Slots cannot be combined in multiple inheritance. If more than one mixed-in class has a nonempty `__slots__`, the class that does the mixing fails. This is true even when the slot names differ. Empty `__slots__` lists let the mixer define slots or not.
- Slots can change `__dict__`. Slots block both the instance `__dict__` and assignments to unlisted names, unless you list `__dict__` explicitly. Slots also block the `__weakref__` attribute that supports weak references. Those are rare, so this book covers them only briefly.

These rules are easier to see in code. The first bullet is the reason a namespace dictionary appears when any class in a tree omits slots. That removes the memory saving, but it also supports classes that need a `__dict__` when mixed with others.

```text
>>> class C: pass                       # Bullet 1: slots in sub but not super
>>> class D(C): __slots__ = ['a']       # Makes instance dict for nonslots
>>> I = D()                             # But slot name still managed in class
>>> I.a = 1; I.b = 2
>>> I.__dict__
{'b': 2}
>>> D.__dict__.keys()
dict_keys([... '__slots__', 'a', ...])
>>> class C: __slots__ = ['a']          # Bullet 2: slots in super but not sub
>>> class D(C): pass                    # Makes instance dict for nonslots
>>> I = D()                             # But slot name still managed in class
>>> I.a = 1; I.b = 2
>>> I.__dict__
{'b': 2}
>>> C.__dict__.keys()
dict_keys([... '__slots__', 'a', ...])
>>> class C: __slots__ = ['a']          # Bullet 3: only lowest slot accessible
>>> class D(C): __slots__ = ['a']       # Superclass slot 'a' is pointless
>>> class C: __slots__ = ['a']; a = 99  # Bullet 4: no class-level defaults
ValueError: 'a' in __slots__ conflicts with class variable
>>> class C: __slots__ = ['a']          # Bullet 5: only one nonempty in mixins
>>> class D: __slots__ = ['a']          # Use empty slots or omit in all but one
>>> class E(C, D): pass
TypeError: multiple bases have instance lay-out conflict
```

Slots work only when every class in the tree uses them carefully. A slot does not compute its value the way a property does. So slots are mostly pointless unless each class uses them and defines only new slot names. The feature is all or nothing. The `super` call has the same problem, as you will see later in this chapter.

```text
>>> class C: __slots__ = ['a']          # Assumes universal use, differing names
>>> class D(C): __slots__ = ['b']
>>> I = D()                             # And may break code and tools you use
>>> I.a = 1; I.b = 2
>>> I.__dict__
AttributeError: 'D' object has no attribute '__dict__'. Did you mean: '__dir__'?
>>> C.__dict__.keys(), D.__dict__.keys()
(dict_keys([... '__slots__', 'a', ...]), dict_keys([... '__slots__', 'b', ...]))
```

These rules and others omitted here explain why slots are rarely recommended. Use them only in unusual cases where the space savings are large. Even then, weigh the risk of breaking code. Slots must be spread throughout a framework. They can also break tools you depend on.

#### Example impacts of slots: ListTree and mapattrs

Slots can affect real tools. The first rule above explains why the `ListTree` class from the earlier attributes chapter still works when another class with `__slots__` is mixed in. `ListTree` has no slots of its own, so every instance it touches still has a `__dict__`. Its scan of that dictionary never fails.

Both of the following single-inheritance trees display without error. The second one also lets you assign names that are not in the slots list, because the superclass supplies a `__dict__`.

```python
class C(ListTree): pass
I = C()                                 # OK: no __slots__ used
print(I)

class C(ListTree):
    __slots__ = ['a', 'b']              # OK: superclass produces __dict__
I = C()
I.c = 3
print(I)                                # Displays c at I, a and b at C
```

These multiple-inheritance classes also display correctly. Any class that is not slotted, like `ListTree`, creates an instance `__dict__`. It can rely on that dictionary being there. Its subclass slots become pointless, but that is a helpful side effect for tool classes like `ListTree`.

```python
class A:
    __slots__ = ['a']                   # Both OK by bullet 1 above

class B(A, ListTree): pass
print(B())

class A:
    __slots__ = ['a']

class B(A, ListTree):
    __slots__ = ['b']                   # Displays b at B, a at A
print(B())
```

Tools that do not inherit from `ListTree` need more care. They may need to catch exceptions when `__dict__` is missing. They can also test with `hasattr`, or use `getattr` with a default, if slots may prevent a namespace dictionary. The `mapattrs` module checks for `__dict__` explicitly, because it is not mixed into other classes and cannot assume the attribute exists. Like `ListTree`, it also maps slots to their classes.

Run these examples yourself. The impact of slots can be heavy, but knowing the rules is your best defense.

#### What about slots speed?

Slots mainly save memory. Their speed effect is less clear. The following test uses the `timeit` technique from the earlier chapter on built-in tools. For both the slots model and the normal dictionary model, it creates 1,000 instances. It assigns and fetches four attributes on each one. It repeats this 1,000 times. It takes the best of 5 runs. Each model therefore runs a total of 8M attribute operations.

```python
import timeit

base = """
Is = []
for i in range(1000):
    I = C()
    I.a = 1; I.b = 2; I.c = 3; I.d = 4
    t = I.a + I.b + I.c + I.d
    Is.append(I)
"""
stmt = """
class C:
    __slots__ = ['a', 'b', 'c', 'd']
""" + base
print('Slots =>', end=' ')
print(min(timeit.repeat(stmt, number=1000, repeat=5)))

stmt = """
class C:
    pass
""" + base
print('Nonslots=>', end=' ')
print(min(timeit.repeat(stmt, number=1000, repeat=5)))
```

On one macOS test host with CPython 3.12, slots were only slightly quicker. This says little about memory, and it may change in future versions. PyPy 7.3 ran this test about 10 times slower than CPython. It still showed a similar pattern.

```text
$ python3 slots-test.py
Slots => 0.17895982996560633
Nonslots=> 0.18887511501088738
```

For more on slots, see the Python standard manual. The `Private` decorator case study in Chapter 39 also handles attributes stored both ways. It does this with delegation and storage-neutral tools like `getattr`.

### Properties: attribute accessors

A property is another way for a class to run methods when an instance attribute is read or assigned. Properties resemble the getters and setters of Java and C#. In Python, use them sparingly.

Add them to an attribute after the fact, when needs change. Properties let you compute an attribute's value on access, so callers do not have to call a method.

Properties can replace some uses of the `__getattr__` and `__setattr__` methods from the earlier chapter on operator overloading. A property does the same job for specific attributes. It adds an extra method call only when the attribute is computed. Other attributes are read normally, with no extra call.

The `__getattr__` method runs only for undefined names. The `__setattr__` method runs on every assignment, which is why the property version can be cheaper.

Properties and slots are related, but they serve different goals. Both are "virtual" attributes that do not live in the instance's namespace dictionary. Both rely on class-level descriptors. Slots manage storage. A property intercepts access and computes the value.

Property basics

A property is an object assigned to a class attribute name. You create one by calling the `property` built-in. You can pass up to three accessor methods: one for get, one for set, and one for delete. You can also pass a docstring. If an argument is `None` or omitted, that operation is not supported.

You usually assign the property at the top level of a class statement. Then reading `obj.name` runs one of the accessor methods. A special decorator syntax, covered later in this chapter, can do this assignment for you.

Here is a `__getattr__` version of an attribute that always returns 40. Keep it in mind as the baseline, because the property version does the same job with less risk.

```text
>>> class WithOperators:
...     def __getattr__(self, name):    # On undefined attr
...         if name == 'age':
...             return 40
...         else:
...             raise AttributeError(name)
>>> x = WithOperators()
>>> x.age                       # Runs __getattr__
40
>>> x.name                      # Runs __getattr__
AttributeError: name
```

The same example with a property looks like this. The property works for one name, and every other name behaves like a normal missing attribute.

```text
>>> class WithProperties:
...     def getage(self):
...         return 40
...     age = property(getage)  # (get?, set?, del?, docs?), or @
>>> x = WithProperties()
>>> x.age                       # Runs getage
40
>>> x.name                      # Normal fetch
AttributeError: 'WithProperties' object has no attribute 'name'
```

Properties can be simpler and faster than the older techniques. They become more attractive once you add assignment support. There is less code to write, and assignments to unmanaged attributes make no extra calls.

```text
>>> class WithProperties:
...     def getage(self):
...         print('get age')
...         return 40
...     def setage(self, value):
...         print('set age:', value)
...         self._age = value
...     age = property(getage, setage)
>>> x = WithProperties()
>>> x.age                       # Runs getage
get age
40
>>> x.age = 42                  # Runs setage
set age: 42
>>> x._age                      # Normal fetch: no getage call
42
>>> x.job = 'hacker'            # Normal assign: no setage call
>>> x.job                       # Normal fetch: no getage call
'hacker'
```

The same class built with operator overloading makes extra calls. Every assignment, even to attributes you do not manage, goes through `__setattr__`. You must route assignments through the instance dictionary to avoid loops. You can also send them to the `object` superclass's `__setattr__`, which supports virtual attributes such as slots and properties.

```text
>>> class WithOperators:
...     def __getattr__(self, name):    # On undefined attr
...         if name == 'age':
...             print('get age')
...             return 40
...         else:
...             raise AttributeError(name)
...     def __setattr__(self, name, value):   # On all assignments
...         print('set:', name, value)
...         if name == 'age':
...             self.__dict__['_age'] = value # Or object.__setattr__(self, ...)
...         else:
...             self.__dict__[name] = value
>>> x = WithOperators()
>>> x.age                       # Runs __getattr__
get age
40
>>> x.age = 41                  # Runs __setattr__
set: age 41
>>> x._age                      # Defined: no __getattr__ call
41
>>> x.job = 'coder'             # Runs __setattr__ again
set: job coder
>>> x.job                       # Defined: no __getattr__ call
'coder'
```

Properties look like a win for this simple case. Some uses of `__getattr__` and `__setattr__` still need more generic interfaces. The attribute names may be unknown when the class is written. They may not exist yet at all.

For example, you may delegate arbitrary attribute references to an embedded object. In that situation, a generic handler that receives the attribute name is better. Properties may still be preferred for simpler cases, though, because they avoid extra calls on assignment.

You can also write properties with the `@` decorator syntax, which Chapter 38 covers in depth. It is an automatic alternative to assigning the property in the class body.

```python
class WithProperties:
    @property                   # Coding properties with decorators: ahead
    def age(self):              # On instance.age
        ...

    @age.setter
    def age(self, value):       # On instance.age = value
        ...
```

Decorator syntax makes more sense after you understand the mechanics beneath it. We cover that next.

### `__getattribute__` and descriptors

The `__getattribute__` method intercepts every attribute reference, not only undefined ones. That makes it more powerful than `__getattr__`. It is also harder to use, because it can loop in several ways, much as `__setattr__` can.

For more specialized control, Python provides descriptors. A descriptor is a class with `__get__` and `__set__` methods. You assign it to a class attribute, and instances inherit it. It intercepts reads and writes to that one attribute. Here is one of the simplest descriptors you are likely to see.

```text
>>> class AgeDesc:
...     def __get__(self, instance, owner): return 40
...     def __set__(self, instance, value): instance._age = value
>>> class WithDescriptors:
...     age = AgeDesc()        # Assign descriptor instance
>>> x = WithDescriptors()
>>> x.age                      # Runs AgeDesc.__get__
40
>>> x.age = 42                 # Runs AgeDesc.__set__
>>> x._age                     # Normal fetch: no AgeDesc call
42
```

A descriptor can access its own state and the state of its client class. In this sense, it is a more general form of property. A property is a simplified descriptor that runs functions on access. Descriptors also power the slots feature you saw earlier. They also have special cases in attribute inheritance.

The full coverage of `__getattribute__` and descriptors is too large for this chapter. The book defers it. Chapter 38 covers descriptors and properties in more depth. Chapter 39 uses them in examples. Chapter 40 explains how they affect inheritance.

## Static and class methods

Most methods expect an instance as their first argument. Python also lets a class define two other kinds of methods that do not need an instance. A static method works like a simple function that lives inside a class. A class method receives the class instead of an instance.

Other languages have similar features, such as C++ static methods. The bound-method section of the earlier chapter touched on these briefly. This section finishes the story.

To turn on these special modes, call the built-in functions `staticmethod` or `classmethod` inside the class. You can also use the `@` decorator syntax, which you will meet later.

A class method always needs `classmethod`. A static method does not need `staticmethod` if you call it only through the class name. It does need `staticmethod` when you call it through an instance.

### Why the special methods?

Some work belongs to the class rather than to any one object, and that is where these two method kinds come in. Usually a method receives an instance as its first argument. That instance is the subject of the call. This is the "object" in object-oriented programming. Two formal options can change that pattern. Before the syntax, consider why you might need them.

Some work is about the class, not any one instance. Imagine you want to count how many instances a class has made. You might also want a list of the instances that are still in use. This data belongs to the class. It is usually stored on the class itself, and processed without any instance.

Simple functions outside the class could do this work. They can reach class attributes through the class name, so they do not need an instance. But it is better to put that code inside the class. That keeps it near the class's other code. It also lets subclasses customize it through inheritance.

To make this work, the class needs methods that do not receive a `self` argument.

Calling a class's function through the class works for a plain function. Calling it through an instance fails, because the instance is passed automatically. Python solves this with static methods. A static method is a plain function nested in a class. It never receives an automatic `self`, however you call it.

You only need one for methods that are accessed through instances. Methods used only through the class do not need one.

Python also supports class methods. These receive the class object as their first argument instead of an instance. This happens whether you call them through an instance or through the class. A class method can access class data through its class argument. That argument is what we have been calling `self`.

Normal instance methods still receive a subject instance. Static and class methods do not.

### Plain-function methods

Suppose you want to use class attributes to count the instances made from a class. The first attempt stores a counter as a class attribute. The constructor adds one to it each time a new instance is made. A method displays the counter. Class attributes are stored once and shared by all instances. That makes this counter span all of them.

```python
class Hack:
    numInstances = 0
    def __init__(self):
        Hack.numInstances += 1
    def printNumInstances():
        print('Number of instances created:', Hack.numInstances)
```

The `printNumInstances` method works with class data, not instance data. It is about all the instances, not one of them. You want to call it without passing an instance. You also do not want to create an instance just to read the count. That would change the count you are trying to read.

You want a `self`-less "static" method.

Whether this method works depends on how you call it. Calls through the class work, because they produce plain functions. Calls through an instance produce bound methods, and those fail.

```text
$ python3
>>> from hack1 import Hack
>>> a, b, c = Hack(), Hack(), Hack()    # Make three instances
>>> Hack.printNumInstances()            # Okay to call from instance – only!
Number of instances created: 3
>>> a.printNumInstances()
TypeError: Hack.printNumInstances() takes 0 positional arguments but 1 was given
```

Calls through the class succeed. Calls through an instance fail, because Python passes the instance to a method that has no argument to receive it. If you call `self`-less methods only through classes, you already have a static method in practice. To call them through instances as well, you need a different design or a way to mark the method as special.

### Static method alternatives

You can sometimes avoid marking the method at all. If you only need functions that read class data, use ordinary functions outside the class. Then no instance is expected. The next example shows this.

```python
def printNumInstances():
    print('Number of instances created:', Hack.numInstances)

class Hack:
    numInstances = 0
    def __init__(self):
        Hack.numInstances += 1
```

The function can find the class through its global name, so this works. The function name becomes global, but only inside this one module. It will not clash with names in other files.

```text
>>> import hack2 as hack
>>> a = hack.Hack()
>>> b = hack.Hack()
>>> c = hack.Hack()
>>> hack.printNumInstances()    # But function may be too far removed
Number of instances created: 3
>>> hack.Hack.numInstances      # And cannot be changed via inheritance
3
```

Before Python had static methods, this was the usual approach. Modules already partition names. You might argue that functions do not need to be packaged in classes unless they implement object behavior. Functions in the module do much of what instance-less class methods could do. They are also associated with the class, because they live in the same file.

This approach has weaknesses, though. It adds a name to the file that is used for only one class. The function is not structurally tied to the class. Its `def` may sit hundreds of lines away from the class. Subclasses also cannot customize a module-level function by redefining it.

You could instead use a normal method and always call it through an instance. That fails when no instance exists. Making an instance also changes the class data, which we just saw. The better solution is to mark a method inside the class as never requiring an instance.

### Using static and class methods

To mark a `self`-less method that works through either the class or an instance, call `staticmethod` or `classmethod` on it. Each one marks a function object as special. A static method needs no instance. A class method needs a class argument. The next module shows all three kinds.

```python
class Methods:
    def imeth(self, x):         # Instance method: passed a self
        print([self, x])        # Always expects a self instance
    def smeth(x):               # Static method: no instance passed
        print([x])              # Also a plain function from the class
    def cmeth(cls, x):          # Class method: gets class, not instance
        print([cls, x])         # Always expects a class, not instance
    smeth = staticmethod(smeth) # Make smeth a static method (or use @: ahead)
    cmeth = classmethod(cmeth)  # Make cmeth a class method (or use @: ahead)
```

The last two assignments rebind the names `smeth` and `cmeth`. Any assignment inside a `class` statement creates or changes an attribute. These final lines overwrite the functions that the `def` statements made.

The `@` decorator form does the same job. It makes little sense until you understand the assignment form it replaces.

Python has three kinds of class methods, and each has a different argument rule. The list below is the whole distinction, so keep it nearby for the examples that follow.

- Instance methods receive a `self` instance object. This is the default.
- Static methods receive no extra instance object. You create one with `staticmethod`.
- Class methods receive a class object. You create one with `classmethod`. Metaclasses also use this rule.

A simple function inside a class can also act as a static method when you call it through the class only. The `allmethods` module illustrates all three kinds. We will look at each in turn.

Instance methods are the normal case, and this book has used them throughout. An instance method must be called with an instance. When you call it through an instance, Python passes the instance as the first argument. When you call it through the class, you pass the instance yourself.

```text
>>> from allmethods import Methods      # Normal instance methods
>>> obj = Methods()                     # Callable through instance or class
>>> obj.imeth(1)                        # Becomes imeth(obj, 1)
[<allmethods.Methods object at 0x1015a79b0>, 1]
>>> Methods.imeth(obj, 2)
[<allmethods.Methods object at 0x1015a79b0>, 2]
```

Static methods are called without an instance argument. Their names are local to the class where they are defined. Inheritance can find them, unlike names in a module.

A function without `staticmethod` works when you call it through the class. The `staticmethod` built-in lets you call it through an instance too. The first line below works without `staticmethod`. The second does not.

```text
>>> Methods.smeth(3)                    # Static method: call through class
[3]                                     # No instance passed or expected
>>> obj.smeth(4)                        # Static method: call through instance
[4]                                     # Instance not passed – requires staticmethod
```

Class methods are similar, but Python passes the class to the first argument. It does this whether you call through the class or through an instance.

```text
>>> Methods.cmeth(5)                    # Class method: call through class
[<class 'allmethods.Methods'>, 5]       # Becomes cmeth(Methods, 5)
>>> obj.cmeth(6)                        # Class method: call through instance
[<class 'allmethods.Methods'>, 6]       # Becomes cmeth(Methods, 6)
```

Chapter 40 covers metaclass methods. They live in the secondary class tree of types. Their behavior is similar to the explicit class methods shown here.

### Counting instances with static methods

Using these built-ins, you can rewrite the instance counter as a static method. The method is marked as special, so Python never passes it an instance.

```python
class Hack:
    numInstances = 0                    # Use static method for class data
    def __init__(self):
        Hack.numInstances += 1
    def printNumInstances():
        print('Number of instances:', Hack.numInstances)
    printNumInstances = staticmethod(printNumInstances)
```

The static method can now be called through the class or through any instance. Both calls read the same counter.

```text
>>> from hack_static import Hack
>>> a, b, c = Hack(), Hack(), Hack()
>>> Hack.printNumInstances()            # Call as simple function
Number of instances: 3
>>> a.printNumInstances()               # Instance argument not passed
Number of instances: 3
```

Compared with the module-level function, this version needs an extra `staticmethod` call, or an `@` line. It has real advantages, though. The function name lives in the class scope, so it cannot clash with other names in the module. The code sits close to where it is used.

Subclasses can customize the static method through inheritance. That is more convenient than importing functions from the files where superclasses are written.

A subclass can override the static method and still call the original. The override adds a line, and the original does the counting.

```text
>>> class Sub(Hack):
...     def printNumInstances():            # Override a static method
...         print('Extra stuff...')        # But call back to original
...         Hack.printNumInstances()
...     printNumInstances = staticmethod(printNumInstances)
>>> a, b = Sub(), Sub()
>>> a.printNumInstances()                   # Call from subclass instance
Extra stuff...
Number of instances: 5
>>> Sub.printNumInstances()                 # Call from subclass itself
Extra stuff...
Number of instances: 5
>>> Hack.printNumInstances()                # Call original version
Number of instances: 5
```

A class can also inherit the static method without redefining it. Python runs it without an instance, wherever it sits in the tree.

```text
>>> class Other(Hack): pass                 # Inherit static method verbatim
>>> c = Other()
>>> c.printNumInstances()
Number of instances: 6
```

Creating `Other` also ran the inherited constructor. That bumped the superclass's counter too. This behavior leads into the next topic, where the class argument changes what the counter means.

### Counting instances with class methods

A class method can do the same work. Example 32-9 behaves like the static method version. It uses a class method instead, which receives the instance's class in its first argument. The code does not hardcode the class name. It uses the class that Python passes in.

```python
class Hack:
    numInstances = 0                    # Use class method instead of static
    def __init__(self):
        Hack.numInstances += 1
    def printNumInstances(cls):
        print('Number of instances:', cls.numInstances)
    printNumInstances = classmethod(printNumInstances)
```

The class is used the same way as before. Its method receives the `Hack` class, not an instance. This happens whether you call it through the class or through an instance.

```text
>>> from hack_class import Hack
>>> a, b = Hack(), Hack()
>>> a.printNumInstances()               # Passes class to first argument
Number of instances: 2
>>> Hack.printNumInstances()            # Also passes class to first argument
Number of instances: 2
```

A class method always receives the most specific, or lowest, class of the call's subject. That has subtle effects when the method updates class data through the class it receives. The next example subclasses `Hack`, as the static method example did. It also prints the `cls` argument, so you can see which class arrived.

```python
class Hack:
    numInstances = 0                    # Trace class passed in
    def __init__(self):
        Hack.numInstances += 1
    def printNumInstances(cls):
        print('Number of instances:', cls.numInstances, cls)
    printNumInstances = classmethod(printNumInstances)

class Sub(Hack):
    def printNumInstances(cls):         # Override a class method
        print('Extra stuff...', cls)    # But call back to original
        Hack.printNumInstances()
    printNumInstances = classmethod(printNumInstances)

class Other(Hack): pass                 # Inherit class method verbatim
```

Running this in a REPL shows that Python passes the lowest class. That is true even for a subclass that has no class method of its own.

```text
>>> from hack_class2 import Hack, Sub, Other
>>> x = Sub()
>>> y = Hack()
>>> x.printNumInstances()               # Call from subclass instance
Extra stuff... <class 'hack_class2.Sub'>
Number of instances: 2 <class 'hack_class2.Hack'>
>>> Sub.printNumInstances()             # Call from subclass itself
Extra stuff... <class 'hack_class2.Sub'>
Number of instances: 2 <class 'hack_class2.Hack'>
>>> y.printNumInstances()               # Call from superclass instance
Number of instances: 2 <class 'hack_class2.Hack'>
```

In the first call, the subclass instance triggers a class method. Python passes `Sub` to it. The subclass version then calls `Hack` explicitly, so `Hack`'s method receives `Hack` in its first argument. Now look at an object that inherits the method without changing it.

```text
>>> z = Other()                         # Call from lower sub's instance
>>> z.printNumInstances()
Number of instances: 3 <class 'hack_class2.Other'>
```

Here Python passes `Other` to `Hack`'s class method. The method works in this example, because the counter is found in `Hack` through inheritance. If the method assigned to the passed class's data, though, it would update `Other`, not `Hack`. Here, `Hack` is better off naming its own class. That way it counts instances of all its subclasses.

### Counting instances per class with class methods

Class methods always receive the lowest class in an instance's tree. That suggests a rule of thumb, and it is the sentence to remember from this section.

- Static methods and explicit class names are a good fit for data local to one class.
- Class methods suit data that may differ for each class in a hierarchy.

Per-class instance counters are a good example of the second case. The top-level superclass in the next example uses a class method. It manages state that is stored on each class in the tree. This is similar to how an instance method manages state that varies per instance.

```python
class Hack:
    numInstances = 0
    def count(cls):                     # Per-class instance counters
        cls.numInstances += 1           # cls is lowest class above instance
    def __init__(self):
        self.count()                    # Passes self.__class__ to count
    count = classmethod(count)

class Sub(Hack):
    numInstances = 0
    def __init__(self):                 # Redefines __init__ (to demo)
        Hack.__init__(self)

class Other(Hack):                      # Inherits __init__
    numInstances = 0
```

When this runs, `Hack` tracks each subclass's instances with a counter on that subclass. Three classes, three counters, and one shared method.

```text
>>> from hack_class3 import Hack, Sub, Other
>>> x = Hack()
>>> y1, y2 = Sub(), Sub()
>>> z1, z2, z3 = Other(), Other(), Other()
>>> x.numInstances, y1.numInstances, z1.numInstances   # Per-class data!
(1, 2, 3)
>>> Hack.numInstances, Sub.numInstances, Other.numInstances
(1, 2, 3)
```

Static and class methods have more advanced roles too. This chapter skips them, and other resources cover them. Later Python versions added function decoration syntax. That made both designations simpler.

Decorators also go well beyond the static method role that started them. They can augment classes, such as initializing a counter like `numInstances` in the last example. The next section explains how.

Note

The methods finale: Chapter 40 covers metaclass methods. They process a class that is itself an instance of a metaclass. They are similar to the class methods here. They need no `classmethod` declaration, and they apply only to the metaclass realm previewed next.

## Decorators and metaclasses

The `staticmethod` and `classmethod` call technique can look obscure at first. Python added a simpler device for it. Decorators are the answer. They are similar to annotations in Java.

A decorator is a general tool. It adds logic that manages functions and classes, or calls to them.

A decoration runs extra processing at function and class definition time. The syntax is explicit. There are two kinds, and they differ only in what follows the `@` line.

- Function decorators augment `def` statements. They set operation modes for simple functions and for class methods. They wrap a function in another layer of logic, implemented as another function. That helper is often called a metafunction, though the name is just terminology.
- Class decorators augment `class` statements. They wrap a whole class. They manage objects and their interfaces, not just one function.

Chapter 19 introduced decorators briefly, for simple functions. They are more general than that. They also work on class methods and classes. They can add almost any logic to functions and classes.

Function decorators can add logging, check argument types during debugging, or time calls. They manage either the function itself or later calls to it. In the second mode, they resemble the delegation pattern from Chapter 31. They differ because they wrap one function call, not a whole object interface.

Python provides a few built-in function decorators. They mark static and class methods and define properties. The `property` built-in works as a decorator automatically.

You can also write your own decorators. These are often classes, so the decorator can save the original function and keep other data as state.

Class decorators came later and extend the same idea to classes. They manage classes themselves or later instance creation. They often delegate an entire interface when they handle instance creation. Their roles overlap with metaclasses. Decorators are the lighter tool for some goals.

### Function decorator basics

A function decorator is a runtime declaration about the function that follows it. It sits on its own line, just before the `def` that defines a function or method. It starts with the `@` symbol. That is followed by a metafunction.

A metafunction is a plain function, or another callable, that takes one argument: the function it manages. The name after `@` is usually a metafunction with an optional argument list. Since Python 3.9, it can be any expression that returns a one-argument function. Listing several decorators on consecutive lines nests them. Later in the book you will see that.

The static method from the previous section can use decorator syntax. The two versions below are the same code, written two ways.

```python
class C:
    @staticmethod               # Function decoration syntax
    def meth():
        ...
```

Behind the scenes, this is the same as passing the function through the decorator and assigning the result back to the name.

```python
class C:
    def meth():
        ...
    meth = staticmethod(meth)   # Name rebinding equivalent
```

Decoration rebinds the method name to whatever the decorator returns. Later calls to the name first trigger the decorator's result. A decorator can return any object. This lets it insert a layer of logic that runs on every later call.

The decorator can return the original function. It can also return a proxy object that saves the original and calls it after the extra logic runs.

Example 32-12 is a cleaner way to write the static method from Example 32-8. The behaviour is identical, and the intent is easier to see.

```python
class Hack:
    numInstances = 0
    def __init__(self):
        Hack.numInstances += 1
    @staticmethod
    def printNumInstances():
        print('Number of instances:', Hack.numInstances)
```

```text
>>> from hack_static_deco import Hack
>>> a, b, c = Hack(), Hack(), Hack()
>>> Hack.printNumInstances()            # Calls from classes and instances work
Number of instances: 3
>>> a.printNumInstances()
Number of instances: 3
```

The built-in `classmethod` and `property` functions also work as decorators. They accept and return functions. Example 32-13 shows all three built-in decorators from this chapter.

```python
class Methods:
    def imeth(self, x):         # Normal instance method: passed a self
        print([self, x])
    @staticmethod
    def smeth(x):              # Static: no instance passed
        print([x])
    @classmethod
    def cmeth(cls, x):         # Class: gets class, not instance
        print([cls, x])
    @property                   # Property: computed on fetch
    def name(self):
        return 'Pat ' + self.__class__.__name__
```

```text
>>> from alldecorators import Methods
>>> obj = Methods()
>>> obj.imeth(1)
[<alldecorators.Methods object at 0x10d2839b0>, 1]
>>> obj.smeth(2)
[2]
>>> obj.cmeth(3)
[<class 'alldecorators.Methods'>, 3]
>>> obj.name
'Pat Methods'
```

These built-ins are still ordinary functions. They work as decorators because they take a function and return a callable. The original name is then rebound to that callable. Any function with this shape can be a decorator, including functions you write yourself.

### A first look at user-defined function decorators

Python has a few built-in decorators. You can also write your own. This book saves the full treatment for a later chapter. Here is a quick example, enough to read other people's decorators without fear.

The `__call__` method from the operator overloading chapter gives an instance a function-call interface. The next example uses it. A call proxy class saves the decorated function inside the instance, and it intercepts calls to the original name. Because it is a class, it can also hold state, such as a count of the calls made.

```python
class tracer:
    def __init__(self, func):       # Remember original, init counter
        self.calls = 0
        self.func = func
    def __call__(self, *args):      # On later calls: add logic, run original
        self.calls += 1
        print(f'call {self.calls} to {self.func.__name__}')
        return self.func(*args)

@tracer                             # Same as hack = tracer(hack)
def hack(a, b, c):                  # Wrap hack in a decorator object
    return a + b + c

if __name__ == '__main__':
    print(hack(1, 2, 3))            # Really calls the tracer wrapper object
    print(hack('a', 'b', 'c'))      # Invokes __call__ in class
```

When the decorated `hack` name is called, it actually runs `__call__`. That method counts and logs the call. It then passes the call to the original function. The `*args` syntax packs and unpacks the arguments. Because of that, this decorator can wrap any function that takes positional arguments.

The output shows the added layer. The first line comes from the `tracer` class. The second is the return value of `hack`.

```text
$ python3 tracer1.py
call 1 to hack
6
call 2 to hack
abc
```

This decorator has limits. It handles positional arguments only, not keyword arguments. It also cannot decorate methods inside a class. For a method, its `__call__` would receive the `tracer` instance and nothing else. Part VIII covers other ways to write function decorators. Some suit methods better.

Nested functions are one alternative. They keep state in an enclosing scope instead of in an instance. That makes the decorator work on class methods too. The full details come later.

The next example uses this closure model. It stores its counter as a function attribute, which keeps it portable. A `nonlocal` variable could do the same job.

```python
def tracer(func):                   # Remember original
    def oncall(*args):             # On later calls
        oncall.calls += 1
        print(f'call {oncall.calls} to {func.__name__}')
        return func(*args)
    oncall.calls = 0
    return oncall

class C:
    @tracer
    def hack(self, a, b, c): return a + b + c

if __name__ == '__main__':
    x = C()
    print(x.hack(1, 2, 3))
    print(x.hack('a', 'b', 'c'))
```

The output matches the earlier version. This time the decorator wraps a class method. Keep in mind that the method receives `self` through the wrapper.

### Class decorators and metaclasses

Python later extended decorators to classes. A class decorator runs at the end of a `class` statement. It rebinds the class name to whatever it returns. It can manage a class right after the class is created.

It can also wrap instance creation, so every later instance passes through extra logic. The two forms below are equivalent.

```python
def decorator(aClass): ...

@decorator                      # Class decoration syntax
class C: ...
```

```python
def decorator(aClass): ...

class C: ...                    # Name rebinding equivalent
C = decorator(C)
```

The decorator can add to the class itself, or return a proxy that intercepts later instance creation. In the earlier section on counting instances per class, a class decorator could do the setup. It could add an instance counter to each class automatically.

```python
def count(aClass):
    aClass.numInstances = 0
    return aClass                   # Return class itself instead of a wrapper

@count
class Hack: ...                     # Same as Hack = count(Hack)

@count
class Sub(Hack): ...                # numInstances = 0 not needed here
```

As written, this decorator works on classes and functions alike. It returns the object it received, after setting an attribute on it. That is the simplest kind of decorator: change the object, then hand it back.

```python
@count
def hack(): pass                    # Like hack = count(hack)

@count
class Hack: pass                    # Like Hack = count(Hack)

hack.numInstances                   # Both are set to zero
Hack.numInstances
```

Class decorators can also manage an object's whole interface. They do this by intercepting construction and wrapping the new instance in a proxy. The proxy then handles later attribute requests. This technique supports attribute privacy, which Chapter 39 implements. Here is a preview of the model.

```python
def decorator(cls):                 # On @ decoration
    class Proxy:
        def __init__(self, *args):  # On instance creation: make a cls
            self.wrapped = cls(*args)
        def __getattr__(self, name):    # On attribute fetch: extra ops here
            return getattr(self.wrapped, name)
    return Proxy

@decorator
class C: ...                        # Like C = decorator(C)

X = C()                             # Makes a Proxy that wraps a C, and catches later X.attr
```

Metaclasses are a similar tool. They are more advanced, and their roles often overlap with class decorators. A metaclass routes class creation to a subclass of `type`. That happens at the end of a `class` statement.

```python
class Meta(type):
    def __new__(meta, classname, supers, classdict):
        ...                         # extra logic + class creation via type call

class C(metaclass=Meta):
    ...                             # my creation routed to Meta; like C = Meta('C', (), {...})
```

Python calls the class's metaclass to create the class object. It passes in the data gathered during the `class` statement. If no metaclass is given, the default is `type`. At the end of a class statement with a metaclass, the effect is roughly this.

```text
classname = Meta(classname, superclasses, attributedict)
```

To control class creation, a metaclass usually overrides `__new__` or `__init__` of `type`. Both intercept the call that `type` would handle. Code in these methods then runs automatically at class creation time. The class name is bound to the result of calling the metaclass.

Both class decorators and metaclasses can augment a class. Both can also return an arbitrary object in its place. That gives almost unlimited customization. Metaclasses can also define methods that process their instance classes. This is similar to class methods. A class decorator can imitate it with methods and data in its proxy.

Chapter 40 covers these ideas in full. They can be mind-bending, so take them one step at a time.

### For more details

There is more to the decorator and metaclass stories than shown here. Some packages require them. Writing new user-defined decorators and metaclasses is an advanced topic, though. It matters most to tool writers, not application programmers. For that reason, the book saves more detail for its optional final part.

- Chapter 38 shows how to code properties with function decorator syntax, in more depth.
- Chapter 39 focuses on decorators and includes larger examples.
- Chapter 40 covers metaclasses and more of the class and instance management story.

## The super function

`super` solves two problems at once, and the second one is where the trouble starts. The `super` built-in does two jobs. It refers to superclass attributes without naming the superclass. It also routes method calls through multiple-inheritance trees in an orderly way.

So far, `super` has appeared only in a sidebar and in some notes. It has not been used in code. That was a deliberate choice. `super` is complex and has real drawbacks. It is hard to recommend to beginners. It is an all-or-nothing tool. It has several strict coding rules. Its semantics are implicit in a way that runs against Python's usual style.

Many programmers use `super` anyway, and it is common in Python code. Programmers who come from Java often reach for it because it looks familiar. They may not notice its subtle effects in multiple inheritance until adding a second superclass breaks their code. This section covers how `super` works and where it can trip you up. The decision to use it is yours.

### The super basics

Start with the explicit form, which fits Python's idioms more closely. You can always reach a superclass attribute, method or data, by naming its source class. You pass `self` yourself.

```text
>>> class C:
...     def act(self):
...         print('hack')
>>> class D(C):
...     def act(self):
...         C.act(self)             # Name superclass explicitly, pass self
...         print('code')
>>> I = D()
>>> I.act()
hack
code
```

In a single-inheritance tree, `super` looks simpler. Its most common form picks the calling class's superclass automatically. An explicit call like `class.method(self)` becomes `super().method()`.

```text
>>> class C:
...     def act(self):
...         print('hack')
>>> class D(C):
...     def act(self):
...         super().act()           # Reference superclass implicitly, omit self
...         print('code')
>>> I = D()
>>> I.act()
hack
code
```

This works as advertised. You do not pass `self`. You do not need to update the call if the superclass changes. You also do not need long superclass names or import paths.

### The super details

Look closely at that example and something seems odd. The `super` call knows the class, its superclass, and `self`. None of them appear in the call. The explanation involves the MRO, a proxy object, and an algorithm. Anyone who uses `super` should understand all three.

The MRO comes first. You must understand the MRO before `super` makes sense. Once you do, the core idea is simple. In a class method, `super` returns a proxy. The proxy finds an attribute in a class that follows the containing class on the MRO of `self`'s class.

The result is an attribute from a superclass or another relative of the class that holds the call.

In single inheritance, the superclass always comes next on the MRO. This works as expected. The mechanism behind it is more magic than it looks.

`super` inspects the runtime call stack to find the calling method's arguments. It also reads the `__class__` variable that Python adds to the closure of methods that use `super`. These two pieces locate `self` and the containing class. `super` then pairs them in a proxy. The proxy sends later attribute fetches to the right superclass version of a name.

The no-argument form is equivalent to passing the class and the instance yourself. Inside a method, these two forms do the same thing. The second form also works outside a method.

```text
super()
super(class-containing-the-super-call, method-self-argument)
```

Here is the explicit version of the example above. It is longer, and every part of it is visible.

```python
class D(C):
    def act(self):
        super(D, self).act()       # Works the same as super().act()
        print('code')              # And D is available as __class__
```

If that sounds complicated, it is. The no-argument form does not work at all outside a method.

```text
>>> super                       # A "magic" proxy object that routes later calls
<class 'super'>
>>> super()                     # This form has no meaning outside a method
RuntimeError: super(): no arguments
```

Where the no-argument form does work, it hides the class and instance. Nothing in your code shows them, and the proxy is the only evidence they exist.

```text
>>> class E(C):
...     def method(self):
...         proxy = super()        # self is implicit in super - only!
...         return proxy
>>> prx = E().method()             # The normally hidden proxy object
>>> prx
<super: <class 'E'>, <E object>>
>>> prx.act()                      # Find act on MRO past hidden E, bind with hidden self, call (!)
hack
```

This call does not look like a bound method or an unbound method. It fills in the class and `self` even though you leave both out. That breaks Python's usual rule that `self` is explicit. Class methods list and use `self` directly. Operator overloading implies a `self` too, but that is much simpler. Hiding the instance is a second strike against `super`, at least for those who value explicit code.

#### Attribute-fetch algorithm

In a single-inheritance tree, `super` is simple. There is only one obvious follower on the MRO. That is the superclass of the class with the `super` call. In that case, you can read the immediate superclass from `__class__.__bases__`. You do not need the MRO for it.

```text
>>> E.__mro__
(<class '__main__.E'>, <class '__main__.C'>, <class 'object'>)
>>> E().__class__.__bases__[0]
<class '__main__.C'>
```

Multiple inheritance needs the full algorithm. The proxy that `super` returns resolves attribute references like this, step by step.

- Fetch the MRO of the saved `self` instance's class, which is `self.__class__.__mro__`.
- Scan this MRO from left to right to find the saved containing class, and skip it.
- Search the namespace dictionaries of the remaining classes in the MRO, from left to right, until the attribute is found.
- If the attribute is a method, bind it to the saved `self` instance.

This procedure runs on every attribute fetch. It depends entirely on MRO order. It starts from `self`'s MRO, not the containing class's MRO. The containing class may have been mixed with other classes, so its own MRO does not apply. The tree shape can be arbitrary for instances of lower classes. In rare cases, the MRO can even change at runtime.

In realistic Python code, you cannot ignore these mechanics except in simple trees. Mix-in classes are common. Multiple inheritance from disjoint, independent superclasses is therefore normal. Once you add more than one superclass, `super` becomes much harder to predict.

### Universal deployment and call-chain anchors

Here is an example to make the problem concrete. Suppose you wrote these classes. Each uses `super` in simple single inheritance, to call a method one level up.

```text
>>> class A:
...     def act(self): print('A')
>>> class B:
...     def act(self): print('B')
>>> class C(B):
...     def act(self):
...         super().act()          # super applied to a single-inheritance tree
>>> C().act()                      # Make an instance and call its method
B
```

Suppose these classes later grow to use more than one superclass. `super` then behaves in a surprising way. It does not raise an error when the same name appears in several superclasses. It picks the leftmost superclass that has the method.

In other words, it takes the first match in the flattened MRO. That may or may not be the class you want. It is completely wrong if you want both.

```text
>>> class C(B, A):                 # Add an A mix-in class with the same method
...     def act(self):
...         super().act()          # Doesn't fail on conflicts - picks just one
>>> C().act()
B
>>> class C(A, B):
...     def act(self):
...         super().act()          # If A is listed first, B.act() is no longer run
>>> C().act()
A
```

This silent masking causes many class bugs. Explicit calls solve the problem. With explicit class names, you choose the left class, the right class, or both. There is much less drama. If you might need explicit names later, why not use them now?

```text
>>> class C(A, B):                 # Explicit form
...     def act(self):            # You probably want to be more explicit here
...         A.act(self)           # This handles both single and multiple inheritance
...         B.act(self)           # So why use the super special case at all?
>>> C().act()
A
B
```

Explicit inheritance also searches the metaclass tree for names not defined in the superclasses. That is covered in the earlier discussion of the inheritance bifurcation. `super` searches only the tail of the instance's MRO, which is the superclass tree. For defined names this difference does not matter. It is unlikely to matter for undefined names either.

The real problem with `super` is that every class must call it. The call chain stops at the first class that does not call `super`. In the example above, `A` and `B` do not. You can add `super` to them too. But that is the first of several strict requirements, and it leads to another problem.

Both `A` and `B` lie on `C`'s MRO. You might try to make both methods run by adding `super` calls to both. This is called cooperative method dispatch. Each class runs `super` to pass the call to the next class on the MRO that cares about it.

Done correctly, each class runs once. A method in a diamond's shared superclass also runs only once, because it appears only once in an MRO. The approach assumes the MRO order suits your calls. Explicit class names are the fallback when it does not.

Here is the attempt, with `super` added to both classes. Read the trace in the error message carefully, because it shows both methods running before the failure.

```text
>>> class A:
...     def act(self):
...         print('A')
...         super().act()          # Add a super here too
>>> class B:
...     def act(self):
...         print('B')
...         super().act()          # Add a super here too
>>> class C(B, A):
...     def act(self):
...         super().act()          # Hope this winds up running all methods
>>> C().act()
B
A
AttributeError: 'super' object has no attribute 'act'
```

It fails. Inspect the MRO to find out why.

```text
>>> I = C()
>>> I.__class__.__mro__
(<class '__main__.C'>, <class '__main__.B'>, <class '__main__.A'>, <class 'object'>)
```

The `super` in `C` selects `act` in `B`, the next class on the MRO. The `super` in `B` then selects `act` in `A`. The `super` in `A` looks for `act` in `object` and beyond. Nothing defines it there, so the call fails. The chain has no anchor, meaning no end point to stop the propagation.

This failure is the third strike against `super`. Dropping `super` from `A` would work for this one case. That policy does not help in general. Classes like `A` and `B` are often written to be mixed into other classes. Specializing them for one tree makes no sense.

To propagate `super` calls, every class must use `super`. The chain also needs an anchor to end it.

You can add an anchor by writing a class that defines the method but does not call `super` again. That is another arduous requirement. It takes more work than the explicit-name alternative.

```text
>>> class X:                       # Code a bogus class, just to appease super
...     def act(self):
...         print('anchor')
>>> class A: ...same...
>>> class B: ...same...
>>> class C(B, A, X):              # Add a final anchor, just to appease super
...     def act(self):
...         super().act()
>>> C().act()
B
A
anchor
>>> [c.__name__ for c in C().__class__.__mro__]
['C', 'B', 'A', 'X', 'object']
```

This works because `X` comes before `object` on the MRO. It stops the `act` chain. You can also make `X` a common superclass of `A` and `B`, forming a diamond. The MRO comes out the same. The MRO removes all but the rightmost appearance of each class in the flattened order.

```text
>>> class X: ...same...
>>> class A(X): ...same...
>>> class B(X): ...same...
>>> class C(B, A): ...same...
>>> C().act()
B
A
anchor
>>> [c.__name__ for c in C().__class__.__mro__]
['C', 'B', 'A', 'X', 'object']
```

If you must write a special class just to satisfy `super`, consider explicit class names instead. Similarity to other languages is a weak reason, especially where those languages do not have the same feature.

The class `super` picks may not be a superclass at all. It can vary by tree. In the example, `super` in `B` dispatches to `A`. `A` is the next class on the MRO, but it is a sibling, not a superclass.

This may not matter in most programs. If you must run an immediate superclass's method, use explicit class names instead of `super`.

### Same argument lists

`super` always needs a call-chain anchor. Sometimes you get one for free. The built-in `object` defines a constructor, and it can anchor some chains. Remember that `__init__` is an ordinary class attribute, despite its special name and automatic call.

```text
>>> class A:
...     def __init__(self):
...         print('A')
...         super().__init__()     # Propagate constructor calls
>>> class B:
...     def __init__(self):
...         print('B')
...         super().__init__()     # Propagate constructor calls
>>> class C(B, A):
...     def __init__(self):
...         super().__init__()     # Assume object anchors constructor chain
>>> I = C()
B
A
```

The constructor call travels through `C`, `B`, `A`, and `object`, in MRO order. This works only for constructors that take no arguments besides `self`. If a constructor takes arguments, the chain breaks at `object`, because its constructor does not expect them.

```text
>>> class A:
...     def __init__(self, name):  # Add an argument to the method
...         print('A')
...         super().__init__(name)
>>> class B:
...     def __init__(self, name):
...         print('B')
...         super().__init__(name)
>>> class C(B, A):
...     def __init__(self, name):
...         super().__init__(name) # But object's arguments list differs
>>> I = C('Pat')
B
A
TypeError: object.__init__() takes exactly one argument (the instance to initialize)
```

This is another strict requirement. `super` assumes every method in a chain uses the same argument list. The MRO order can change when the tree changes. Any change in inheritance can therefore reorder the calls.

This limits flexibility. A single program may let you control the classes and their arguments. Starred argument collectors can sometimes soften the problem. Neither approach works for code meant to be reused in several contexts. Reuse across contexts is one of the main points of Python programming.

### Noncalls and operator overloading

`super` has two more oddities. First, it is not only about methods. Despite the jargon, it can also fetch class data attributes. It returns bound methods too, as the earlier chapter on bound methods described.

```text
>>> class C:
...     attr1 = 'hack'            # super also fetches data attributes
...     def attr2(self):         # And returns bound methods sans calls
...         return 'code'
>>> class D(C):
...     def act(self):
...         return super().attr1, super().attr2
>>> I = D()
>>> I.act()
('hack', <bound method C.attr2 of <__main__.D object at 0x103993200>>)
>>> I.act()[1]()
'code'
```

When `super` returns a method like `attr2`, the proxy binds it to the saved instance. Fetching a method as a plain function may require an explicit class name, such as `C.attr2`. The details get deep. The point is that `super` departs from normal behavior here too.

Second, `super` does not fully work with `__X__` operator-overloading methods. The next example shows the problem. Explicit named calls to overloading methods in the superclass work. Using `super` in an expression fails to reach the superclass method.

```text
>>> class C:
...     def __getitem__(self, ix):  # Indexing overload method
...         print('C index')
>>> class D(C):
...     def __getitem__(self, ix):  # Redefine to extend here
...         print('D index')
...         C.__getitem__(self, ix) # Explicit call form works
...         super().__getitem__(ix) # Direct name calls work too
...         super()[ix]             # But operators do not! (__getattribute__)
>>> I = C()
>>> I[99]
C index
>>> I = D()
>>> I[99]
D index
C index
C index
TypeError: 'super' object is not subscriptable
```

The `super` proxy catches later attribute requests through `__getattribute__`. Built-in operations skip that step. Expressions such as `I[99]` begin their search in the class, not the instance. So the proxy never sees the automatic `__X__` call.

This is the same limitation that affects delegation with built-in operations. Operators should generally behave like the equivalent method call. The failure here is one more exception that `super` users must learn. In Python, `self` is explicit, mix-ins and operator overloading are common, and superclass renames are rare.

### The super wrap-up

`super` is a brief tutorial topic, and you can find many supplements elsewhere. Some of those defend `super` as much as they document it. This section aims for a balanced view of the trade-offs.

In a single-inheritance tree, `super` refers to parent classes without naming them. In a multiple-inheritance tree, it can implement cooperative method dispatch. Each superclass is visited once in a conforming chain. That is especially useful in diamonds.

These are real benefits. `super` can also be highly implicit. It may not call the superclasses your program expects. Three coding requirements come with the method dispatch technique, and the list below names all of them.

- Anchors: the method called by `super` must exist. Without an anchor, you need extra code and calls. Mix-in classes also cannot be specialized for a single tree.
- Arguments: the method called by `super` must have the same signature across the whole tree. This can limit flexibility, especially for constructors.
- Deployment: every class that defines the method must use `super`, except the last one. That makes existing code harder to reuse, changes to call order harder, and self-contained classes harder to write.

`super` also builds on the already complex MRO. It can hide problems when a single-inheritance tree becomes a multiple-inheritance tree. It can select a class that is not a superclass. It is also one more special case in attribute inheritance, which Chapter 40 revisits.

`super` is easy to use and mostly harmless in single inheritance. Its unusual rules, strict requirements, and small net benefit make it a mixed bag. Programmers who are learning Python should often prefer the more general and transparent style of explicit class-name references. Judge this for yourself in the OOP programs you meet.

## Class gotchas

Most class bugs are namespace bugs, and the list below collects the common ones. You have now seen the main OOP tools in this book. Pitfalls remain. Most class problems come down to namespaces, since classes are mainly namespaces with a few extra tricks. Some of the items below are usage tips more than true problems. Even experienced class programmers stumble on them.

### Changing class attributes can have side effects

Classes and class instances are mutable objects. You can change them in place by assigning to their attributes. Like lists and dictionaries, they can be referenced from several places. Changing one can affect every reference to it.

That is usually what you want. It is how objects change state in general. The effect is especially important for class attributes. Every instance of a class shares the class's namespace. A change at the class level appears in every instance that lacks its own copy of that attribute.

In the next example, the assignment to `a` inside the class body creates the attribute `X.a`. It lives on the class object and every instance inherits it.

```text
>>> class X:
...     a = 1                     # Class attribute
>>> I = X()
>>> I.a                           # Inherited by instance
1
>>> X.a                           # Accessible through class
1
```

Now change the class attribute outside the `class` statement. That changes every object that inherits from the class. New instances made later also see the new value, whatever the class source code says.

```text
>>> X.a = 2                       # May change more than X
>>> I.a                           # I changes too
2
>>> J = X()                       # J inherits from X's runtime values
>>> J.a                           # (but assigning to J.a changes a in J, not X or I)
2
```

Is this useful or a trap? You decide. Chapter 27 showed that you can get work done by changing class attributes without ever making an instance. That can simulate records or structs from other languages. Here is an unusual but legal program.

```python
class X: pass                   # Make a few attribute namespaces
class Y: pass

X.a = 1                         # Use class attributes as variables
X.b = 2                         # No instances anywhere to be found
X.c = 3
Y.a = X.a + X.b + X.c
for X.i in range(Y.a):
    print(X.i)                  # Prints 0..5
```

The classes `X` and `Y` act like fileless modules. They are namespaces for variables that should not clash. This is a legal trick, but it is risky with classes that others wrote. You cannot always know which class attributes are critical to a class's internal behavior.

If you want a C-style struct, use instances instead. Then only one object is affected.

```python
class Record: pass

X = Record()
X.name = 'pat'
X.job = 'Pizza maker'
```

### Changing mutable class attributes can have side effects, too

This gotcha extends the previous one. Class attributes are shared by all instances. If a class attribute refers to a mutable object, changing that object in place from any instance affects every instance.

```text
>>> class C:
...     shared = []               # Class attribute
...     def __init__(self):
...         self.perobj = []      # Instance attribute
>>> x, y = C(), C()               # Two instances
>>> y.shared, y.perobj            # Implicitly share class attrs
([], [])
>>> x.shared.append('hack')       # Impacts y's view too!
>>> x.perobj.append('code')       # Impacts x's data only
>>> x.shared, x.perobj
(['hack'], ['code'])
>>> y.shared, y.perobj            # y sees change made through x
(['hack'], [])
>>> C.shared                      # Stored on class and shared
['hack']
```

This effect is not new. You have seen it with mutable objects shared by variables, globals shared by functions, module objects shared by importers, and mutable arguments shared by caller and callee. All of these involve several references to a mutable object. Changing it in place affects all of them.

Assignment to an instance attribute works differently, which can make this subtle. The two lines below look almost identical, and they do different things.

```python
x.shared.append('hack')         # Changes shared object attached to class - in place
x.shared = 'hack'               # Changed or creates instance attribute attached to x
```

This is not a bug. It is something to be aware of. Shared mutable class attributes have many valid uses, and the danger is only in forgetting how they behave.

### Multiple inheritance: order matters

It is worth repeating: in multiple inheritance, the order of superclasses in the `class` header can be critical. Python always searches superclasses from left to right, in the order they appear in the header.

Imagine a `Super` class with a `__str__` method, next to a `ListTree` class that also has one. Both methods are valid, and only one can win.

```python
class ListTree:
    def __str__(self): ...

class Super:
    def __str__(self): ...

class Sub(ListTree, Super):         # Get ListTree's __str__ by listing it first
    x = Sub()                       # Inheritance searches ListTree before Super
```

Which `__str__` does `Sub` inherit? It inherits the one from the leftmost class in its header. You would list `ListTree` first, because its purpose is its custom `__str__`. The earlier chapter needed exactly that, when it mixed this class with a `tkinter.Button` that had its own `__str__`.

Now suppose both classes have other same-named attributes too. If you want one name from `Super` and another from `ListTree`, the header order cannot give you both. You must override inheritance by assigning the attribute name in `Sub` itself.

```python
class ListTree:
    def __str__(self): ...
    def other(self): ...

class Super:
    def __str__(self): ...
    def other(self): ...

class Sub(ListTree, Super):         # Get ListTree's __str__ by listing it first
    other = Super.other             # But explicitly pick Super's version of other
    def __init__(self):
        ...

x = Sub()                           # Inheritance searches Sub before ListTree/Super
```

The assignment to `other` in `Sub` creates `Sub.other`. It refers to the same object as `Super.other`. Because `Sub` is lower in the tree, it hides `ListTree.other`. If you list `Super` first to get its `other`, you must select `ListTree`'s `__str__` explicitly.

```python
class Sub(Super, ListTree):         # Get Super's other by order
    __str__ = ListTree.__str__      # Explicitly pick ListTree.__str__
```

The earlier section on attribute conflict resolution shows this technique in another example. Multiple inheritance is an advanced tool. Use it sparingly and carefully. Otherwise a name's meaning can depend on the order of classes mixed into a distant subclass.

A good rule of thumb is to keep mix-in classes as self-contained as possible. They may be used in many contexts. They should not assume anything about names in other classes of the tree.

The pseudoprivate `__X` names from the earlier chapter help here. They localize the names a class depends on. They also limit the names a mix-in adds. In the example, if `ListTree` only means to export its custom `__str__`, it can name its `other` method `__other`. That avoids clashes with like-named classes in the tree.

### Scopes in methods and classes

Class code follows the same scope rules as function code. Classes create local scopes, and methods are nested functions. In the next example, `generate` returns an instance of the nested `Hack` class. The name `Hack` is assigned in `generate`'s local scope. That makes it visible to nested functions, including the code in `method`. It sits in the enclosing-function layer of the LEGB rule.

```python
def generate():
    class Hack:                     # Hack is a name in generate's local scope
        count = 1
        def method(self):
            print(Hack.count)       # Visible in generate's scope, per LEGB rule (E)
    return Hack()

generate().method()
```

The example works, because nested `def` statements see the local scopes of enclosing functions. That includes nested method definitions.

Method definitions cannot see the scope of the enclosing class, though. They see only the scopes of enclosing functions. So a method must reach class names through `self` or the class name. In the example, the method must use `self.count` or `Hack.count`. Plain `count` will not work.

You can avoid nesting by moving the class to the top level of the module. Then both `generate` and the method find `Hack` in the global scope. The name is not local to a function, but it stays local to one module.

```python
def generate():
    return Hack()

class Hack:                         # Define at top level of module
    count = 1
    def method(self):
        print(Hack.count)           # Found in global scope (enclosing module)

generate().method()
```

Simpler code usually avoids nesting classes and functions. Nesting a class can still help in closures. There, the enclosing function's scope keeps state that the class or its methods use.

In the next example, the nested method can see its own scope, the enclosing function's scope through `label`, the module's global scope, the `self` instance, and the class through its enclosing name.

```text
>>> def generate(label):           # Returns a class instead of an instance
...     class Hack:
...         count = 1
...         def method(self):
...             print(f'{label}={Hack.count}')
...     return Hack
>>> aclass = generate('Gotchas')
>>> I = aclass()
>>> I.method()
Gotchas=1
```

### Miscellaneous class gotchas

These are a few more class warnings. Most of them are reminders, and each one has cost someone a debugging session.

Choose per-instance or class storage wisely. Be careful about whether an attribute belongs on the class or on its instances. Class attributes are shared by all instances. Instance attributes differ from one instance to the next. In a GUI program, you might want data shared by all windows, such as the last directory used for a Save operation. That belongs at the class level. If you store it on each window as an instance attribute, each window has its own copy. The value may also be missing when looked up through inheritance.

You usually want to call superclass constructors. Python runs only one `__init__` method when it makes an instance. It is the first one found through inheritance. It does not run the constructors of superclasses higher in the tree. Constructors usually do required startup work. So a subclass constructor often has to run its superclass constructor too. Use an explicit call through the superclass name, or `super`, and pass the arguments it needs. The exceptions are when you mean to replace the superclass constructor, or when the superclass has no constructor at all.

Watch out for `__getattr__` and built-ins. The earlier chapters noted this too. A class that uses `__getattr__` to delegate attribute fetches may fail on built-in operations. Operator-overloading methods that built-ins fetch implicitly do not go through generic attribute interception. To work around this, redefine those methods in the wrapper class. You can do that by hand, with tools, or by defining them in superclasses. Chapter 39 shows how.

### Overwrapping-itis

Abstraction is a tool, and like any tool it can be overused. Code reuse is one of the main reasons to use OOP. It can cut development time. Sometimes, though, OOP's abstraction is overused. Classes layered too deeply can make code hard to understand. To find out what one operation does, you may need to search through many classes.

Imagine a framework with hundreds of classes and a dozen levels of inheritance. The details are changed here, but the situation is real. Following a method call through such a system can be a major task. Several classes may need checking for even a simple operation. The logic can be so wrapped that understanding one piece takes days of reading related files. That hurts productivity.

The most general rule of Python programming applies here too. Do not make things complicated unless they truly must be. Wrapping code in layers of classes until it is incomprehensible is always a bad idea.

Abstraction is the basis of polymorphism and encapsulation. Used well, it is very effective. You will debug faster and maintain code more easily if your class interfaces are intuitive. Keep the hierarchies short and small, unless you have a good reason. Code you write is usually code that others must read.

## Class odds and ends summary

This chapter covered an assortment of class topics. It included subclassing built-in types, the relationship between types and classes, slots, properties, static methods, decorators, and `super`. Most of these are optional extensions to the OOP toolbox. They become more useful as your programs grow.

They are also worth knowing when they appear in code you must understand. Some of these topics continue in the final part of the book. Look ahead there for more on properties, descriptors, decorators, and metaclasses.

### Practice exercises

The book closes its class material with practice exercises. Try these with your own code. Each one asks for a small program, and together they cover everything in the chapter.

- Write an `Adder` class with an `add(self, x, y)` method that prints a "Not Implemented" message. Then write `ListAdder` and `DictAdder` subclasses that implement `add` for lists and dictionaries.
- Extend `Adder` with a constructor that stores data, and overload `+` with `__add__` so it dispatches to `add`. Decide which classes should hold the constructor and the operator method.
- Write a `MyList` class that wraps a list and overloads most list operators. Experiment with copying the initial value, with slicing, and with mixing `MyList` and regular lists.
- Write a `MyListSub` subclass that counts `+` calls. Decide whether the counters should be per instance or per class.
- Write an `Attrs` class that prints a message on every attribute fetch and assignment. Then see what happens when you use the instance in expressions.
- Use the set class from this chapter to compute intersections and unions with `&` and `|`. Then extend it with `*args` so it handles several operands.
- Model a fast-food order with `Lunch`, `Customer`, `Employee`, and `Food` classes. Let `Lunch` embed the other objects and pass the order along.
- Build a zoo hierarchy of six classes. Give each a `speak` method, and give the top `Animal` class a `reply` method that calls `self.speak`.

## Checkpoint questions

1. When you fetch a `Manager` object from a shelf and print it, where does the display logic come from?

Answer: `Manager` inherits `__repr__` from `AttrDisplay` in the separate `classtools` module, two levels up the class tree. `Manager` has no `__repr__` of its own, and `Person` does not define one either, so the search climbs until it finds `AttrDisplay`. The class names in parentheses in a `class` header provide the links to higher superclasses, which is what makes the second hop possible.

2. If a script loads a stored `Person` and never imports the module, how can it still call `giveRaise`?

Answer: When Python pickles an instance, it records the attributes, the class name, and the module that holds the class. On loading, Python reimports the class internally and creates a new instance with the saved attributes.

The loaded object therefore gets all its original methods, such as `lastName`, `giveRaise`, and `__repr__`, even if its class was never imported in the loading script. That is why the shelf examples work with no import line at all.

3. Why is it important to move processing into methods instead of hardcoding it outside the class?

Answer: Methods keep one copy of each operation, so changes are made in one place. Methods also work on any instance, not just the one you were looking at when you wrote the code. This is encapsulation, the wrapping of logic behind an interface for future maintenance. Hardcoded logic creates redundancy that multiplies work as the code evolves.

4. Why is it better to customize by subclassing than by copying the original and modifying the copy?

Answer: Subclassing reduces development effort. You code by customizing what already exists, so the shared part is written once. Copying doubles future work, because changes to the original must be copied by hand. Subclassing lets you extend earlier work without starting over or creating redundant copies.

5. Why is it better to call back to a superclass method for default actions than to copy and modify its code in a subclass?

Answer: Copying the code creates redundancy, which multiplies maintenance as the code changes. Calling the original through the superclass name, or with the `super` built-in, keeps one copy. The same reasoning applies to superclass constructors, which is why subclasses so often call them.

6. Why is it better to use generic tools such as `__dict__` than to write custom code for each class?

Answer: Generic tools avoid hardcoded solutions that must be kept in sync as the class evolves. A generic `__repr__` need not change when a new attribute is added in `__init__`. A generic method inherited by all classes is changed in one place, and every class that inherits it picks up the change.

7. In general terms, when might you choose object embedding and composition instead of inheritance?

Answer: Inheritance suits direct customization, where a subclass is a specialized version of its parent. Composition suits cases where several objects combine into a whole and a controller class directs them.

Inheritance passes calls up to reuse code, and composition passes calls down to delegate them. The two can be combined, and the embedded objects are often customized through inheritance.

8. Suppose names were stored in a dictionary and jobs in a list, as in earlier chapters. What would need to change?

Answer: Not much, since this was a first-cut prototype. The `lastName` method would need to change for the new name format. The `Person` constructor would need to change the job default to an empty list. The `Manager` class would probably pass a job list to its constructor instead of a single string.

Those changes stay in one place, because the details are encapsulated in the classes. The database scripts would work as they are, apart from the object-construction calls, because shelves support nested data.

9. What changes would turn these classes into a personal contacts database?

Answer: The classes can serve as template code for many kinds of database. Change the constructors to record different attributes, such as `name`, `address`, `birthday`, `phone`, and `email`. Then add methods that suit the application.

A method such as `sendmail` could use the standard-library `smtplib` module to email a contact. The `AttrDisplay` tool works unchanged, and most of the `shelve` code can store your objects with minor changes.

10. What is an abstract superclass?

Answer: An abstract superclass calls a method but does not define it. It expects a subclass to fill in that method. This lets a general class describe behavior before a specific subclass exists. Frameworks use the same pattern to hand off work to operations that client classes define.

11. What happens when a simple assignment appears at the top level of a `class` statement?

Answer: It creates a data attribute on the class, written `Class.X`. Every instance that does not have its own attribute of that name shares it. Methods are usually created with nested `def` statements instead.

12. Why might a subclass need to call the superclass `__init__` manually?

Answer: When a subclass defines its own constructor, Python runs only the lowest `__init__` in the tree. If the superclass setup code must also run, the subclass calls it, usually as `Superclass.__init__(self, …)`. The `super().__init__(…)` form also works, but this chapter uses the explicit form.

13. How can you augment an inherited method instead of replacing it?

Answer: Redefine the method in the subclass, then call the superclass version from inside it. Pass `self` by hand, as in `Superclass.method(self, …)`. The `super().method(…)` form does the same job implicitly, and Chapter 32 weighs the two.

14. How does a class's local scope differ from a function's local scope?

Answer: A class body is a local scope while it runs, and it can see enclosing function scopes. Code nested inside the class cannot see the class's names as plain variables. Methods reach them through `self` or the class name.

After the `class` statement finishes, the local scope becomes an attribute namespace, which is the second half of the story.

15. Which two methods can support iteration in a class, and which one does Python try first?

Answer: A class can define or inherit `__iter__` or `__getitem__`. Python tries `__iter__` first. That method returns an iterator with a `__next__` method.

If no `__iter__` is found, Python falls back on `__getitem__`, calling it with successively higher indexes. A `yield` statement can create `__next__` automatically, which saves writing the index logic by hand.

16. Which two methods handle printing, and in what contexts?

Answer: `__str__` is called by `print` and the `str` built-in. `__repr__` is called by `print` and `str` only when no `__str__` exists. It is also used by the `repr` built-in, by interactive echoes, and for nested appearances.

`__str__` is usually the user-friendly display, and `__repr__` gives extra detail or the as-code form. If you only write one of them, write `__repr__`.

17. How can you intercept slice operations in a class?

Answer: Slices are caught by the `__getitem__` method. Python calls it with a slice object instead of a plain integer. The method can pass the slice object along or inspect its `start`, `stop`, and `step` attributes.

18. How can you catch in-place addition in a class?

Answer: Define `__iadd__` for `+=`. If it is missing, Python uses `__add__` and assigns the result to the name. The `__radd__` method handles addition with the instance on the right side.

19. When should you provide operator overloading?

Answer: Provide it when a class naturally matches, or needs to emulate, a built-in type's interface. Do not overload expression operators that do not map naturally to your objects. A normally named method is clearer in that case, and a reader will find it faster.

20. What is multiple inheritance?

Answer: Multiple inheritance occurs when a class lists more than one superclass. It is useful for mixing together several packages of class-based code. The left-to-right order in the `class` header sets the general search order. The MRO refines that search for diamonds with common superclasses.

21. What is composition?

Answer: Composition is a technique in which a controller class embeds and directs several objects and offers an interface of its own. It is a way to build larger structures from classes.

22. What is delegation?

Answer: Delegation wraps an object in a proxy class. The proxy adds behavior and passes other operations to the wrapped object. The proxy usually keeps the interface of the wrapped object.

23. What are bound methods?

Answer: A bound method combines an instance and a method function. You can call it without passing an instance, because the instance is kept in the pair.

24. What are pseudoprivate attributes used for?

Answer: Names that begin with two underscores but do not end with two underscores, such as `__X`, are expanded to include the enclosing class name. This localizes the name to its class. It covers class attributes, such as methods, and `self` attributes assigned inside the class. The expanded names are usually unique across an inheritance tree.

25. How does the MRO differ from DFLR?

Answer: The MRO selects a same-named attribute in a lower subclass over one in a higher common superclass in a diamond tree. It searches across before it climbs up in that case. Otherwise the MRO matches DFLR.

It is defined by starting with the DFLR order and then removing all but the rightmost copy of each class visited more than once. The built-in `object` makes every multiple-inheritance tree a diamond, so this happens often, though it is usually implicit.

26. Name two ways to extend a built-in object type.

Answer: You can embed the built-in object in a wrapper class, or subclass the built-in type directly. Subclassing tends to be simpler, because most of the original behavior is inherited automatically. It works because types are classes.

27. What are function and class decorators used for?

Answer: Function decorators manage a function or method, or add a layer of logic that runs each time it is called. They can log or count calls and check argument types. They also declare static methods, class methods, and properties. Class decorators are similar, but they manage whole objects and their interfaces.

28. How are normal methods and static methods different?

Answer: A normal (instance) method receives a `self` argument that holds the implied instance. A static method receives no instance, however it is called. Python allows simple functions in a class to be called through the class without a declaration. Calls through instances still need `staticmethod`.

29. Are tools like `__slots__` and `super` valid to use in your code?

Answer: They are valid, but use them only after weighing their effects. Slots can break code, and they work only with universal deployment. `super` can mask later problems in single inheritance. In multiple inheritance it adds substantial complexity for an isolated use case.

30. Why does a class attribute named `__bases__` not show up on an instance?

Answer: Inheritance for classes uses a second search through the `type` tree. Names found only in that tree are not inherited by nonclass instances. So `C.__bases__` works, but `I.__bases__` raises an `AttributeError` for an instance `I` of `C`.

31. When should you choose a static method instead of a module-level function?

Answer: Choose a static method when the function works with class data and belongs with the class. The method name stays in the class scope, so it cannot clash with other module names. It also sits near the code that uses it. Subclasses can customize it through inheritance, which a module-level function cannot do.

## Sources and review notes

- Source: *Learning Python*, 6th edition (`learning-python-6th-edition`). Chapters used are listed in each section.
- Chapter 28, "A More Realistic Example," from *Learning Python*, 6th edition (`learning-python-6th-edition`).
- Chapter 29, "Class Coding Details," from *Learning Python*, 6th edition (`learning-python-6th-edition`).
- Chapter 30, "Operator Overloading," from *Learning Python*, 6th edition (`learning-python-6th-edition`).
- Chapter 31, "Designing with Classes," from *Learning Python*, 6th edition (`learning-python-6th-edition`).
- Chapter 32, "Class Odds and Ends," from *Learning Python*, 6th edition (`learning-python-6th-edition`).
