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

This chapter goes deeper into material that chapter 3.1 only introduces. You will meet it again whenever you read or write the Python behind schedulers, operators, exporters and training launchers.

## Building a realistic example: a Person class

Before the language details, this chapter takes a short detour into a realistic example. We will build a small set of classes that record and process information about people. You will see that instances and classes can play the same roles that records and programs play in more traditional code. The main difference is the customization that inheritance makes possible.

We will write two classes:

- `Person`, a class that creates and processes information about people.
- `Manager`, a customization of `Person` that changes some inherited behavior.

Along the way we will make instances of both classes and test them. At the end we will store those instances in a simple object-oriented database, so they outlive the program. You can use that code as a template for a larger personal database written entirely in Python.

The aim is also to teach. Many readers understand class syntax in the abstract but freeze when they must write a class from scratch. So we will build the classes one small step at a time.

### Step 1: Making instances

The first task is to start the main class, `Person`. Open a new file in your text editor for the code.

Python programmers usually start module names with a lowercase letter and class names with an uppercase letter. The language does not require this, but nearly everyone follows it, so deviating can confuse later readers. We will name the module file `person.py` and the class `Person`.

**Example 28-1.** `person_1.py` (start)

```text
class Person: # Start a class
```
We will change this file as we go. To track the versions, each example number appears in the caption, and the same number appears in the file name. The file stays the same across steps, but the book shows each revision separately.

A module can hold any number of functions and classes. The name `person.py` may stop making sense if we add unrelated code later. For now we will assume everything in it relates to `Person`. Modules work best with a single, cohesive purpose.

#### Coding constructors

The first real job for `Person` is to record basic facts about each person. In Python these facts are instance attributes. They are usually created by assigning values to `self` inside methods.

The normal way to give an instance its first values is the `__init__` constructor method. Python runs `__init__` automatically each time an instance is created.

**Example 28-2.** `person_2.py` (set attributes in the constructor)

```python
class Person:
    def __init__(self, name, job, pay): # Constructor takes three arguments
        self.name = name # Fill out fields when created
        self.job = job # self is the new instance object
        self.pay = pay
```
This is a very common pattern. We pass data to the constructor, then assign it to `self` so the instance keeps it. In object terms, `self` is the new instance, and `name`, `job`, and `pay` become state information. Other techniques, such as closures, can also save details. Instance attributes make the saving explicit.

The argument names appear twice, and that is not a mistake. The `job` argument is a local variable inside `__init__`. The `self.job` value is an attribute on the instance. They are two different variables that happen to share a name. Assigning `self.job = job` saves the local value on the instance for later use. In Python, what a name refers to depends on where it is assigned.

There is nothing special about `__init__` apart from its automatic call and its first argument named `self`. It is a normal function, so it supports everything we know about functions. We can give its arguments defaults.

Let us make `job` optional. It will default to `None`, which means the person is not currently employed. If `job` defaults to `None`, `pay` should default to `0` for consistency. Python requires this: once one argument has a default, every argument after it must have one too.

**Example 28-3.** `person_3.py` (defaults for optional arguments)

```python
class Person:
    def __init__(self, name, job=None, pay=0): # Normal function args
        self.name = name
        self.job = job
        self.pay = pay
```
Now a name is required when we make a `Person`, but `job` and `pay` are optional. If we omit them, they default to `None` and `0`. The `self` argument is filled in by Python. Assigning to attributes of `self` attaches those values to the new instance.

#### Testing as you go

This class does very little yet. It fills out the fields of a new record, but it is a working class. Python programming is mostly incremental. You write a little code, test it, and write more. Python's interactive session and fast turnaround make this natural.

Testing by hand at the prompt has limits. Retyping test cases each session gets tedious. Most programmers use the prompt for quick one-off checks. For real tests they put code at the bottom of the file that holds the class.

**Example 28-4.** `person_4.py` (self-test at the bottom)

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
Bob accepts the defaults for `job` and `pay`. Sue provides values explicitly. We use keyword arguments when we make Sue. Position would work too, but keywords remind us what each value means. They also let us pass arguments in any order.

When the file runs as a script, the test code makes two instances and prints two attributes of each.

```text
$ python3 person_4.py
Bob Smith 0
Sue Jones 100000
```

You can also type the test code at the interactive prompt after importing the class. Canned tests inside the module are easier to rerun later.

This small example already teaches something important. Each instance keeps its own name and pay, so changing one leaves the other untouched. Each instance is an independent record with its own copy of the state. Classes therefore work like a factory for objects, much as built-in types such as lists and dictionaries do. Functions and modules have no such idea. Closures keep per-call state, but they lack the methods, inheritance, and structure that classes provide.

#### Using code two ways

The test code has a catch. Its top-level `print` calls also execute during an import. If another program imports `Person`, it will see our test output. Client programs do not want that output mixed into their own.

We could move the tests to a separate file. It is often more convenient to keep them with the code they test. The fix is the `__name__` check. Test statements should run only when the file is run directly, not when it is imported. This check was covered in the modules chapter.

**Example 28-5.** `person_5.py` (test code runs only when run directly)

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
Now each use behaves correctly. Running the file tests it, because its `__name__` is `__main__`. Importing it only defines the class.

```text
$ python3 person_5.py
Bob Smith 0
Sue Jones 100000
$ python3
>>> import person_5
>>>
```

When imported, the file defines the class but does not use it. When run directly, it creates two instances and prints their attributes. The values differ because each instance is its own namespace.

### Step 2: Adding behavior methods

So far the class is a record factory. It creates instances and fills out their fields. We can still do useful work with those fields. Classes add structure, but they mostly work by processing core types such as lists and strings. If you already know those types, you already know much of the class story.

The `name` field is a plain string. We can get a last name by splitting on spaces and indexing. These are core-object operations, and they work the same whether the string sits in a class or not.

```python
>>> name = 'Bob Smith' # Simple string, outside class
>>> name.split() # Extract last name
['Bob', 'Smith']
>>> name.split()[-1] # Or [1], if always just two parts
'Smith'
```

We can also give a raise by changing the `pay` field in place with an assignment. The same core operations apply, whether the number is standalone or embedded in an object. The formatting here hides extra digits.

```python
>>> pay = 100000 # Simple variable, outside class
>>> pay *= 1.10 # Give a 10% raise
>>> print(f'{pay:,.2f}') # Or: pay = pay * 1.10, if you like to type
110,000.00 # Or: pay = pay + (pay * .10), if you really do
```

To apply these operations to our objects, use `bob.name` and `sue.pay` in place of `name` and `pay`. The operations stay the same. Only the subjects change, because they are now attributes of objects made from our class.

**Example 28-6.** `person_6.py` (operate on attributes directly)

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

Finding every copy is harder in a large program. The code may sit in many files and folders, split across steps. In a prototype like this, change is almost certain.

#### Coding methods

The better design is encapsulation. You wrap an operation behind an interface so it is coded once. If the need changes, there is one copy to update. You can also change its internals without breaking the code that calls it.

In Python, you put operations on objects in a class's methods, instead of scattering them through the program. Classes are very good at this kind of factoring. Turning operations into methods has another benefit. The methods work on any instance, not only the ones they were hardcoded for.

Example 28-7 moves the two operations into methods. The self-test code also switches to the new methods.

**Example 28-7.** `person_7.py` (move operations into methods)

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

The transformation is simple. The new `lastName` does for `self` what the old code did for `bob`. It also returns its result, so the caller can use the value however it likes. The new `giveRaise` does the same for `self` that we did for `sue` before.

The output is nearly the same as before. We mostly refactored the code so future changes are easier. Command lines for the latest version are often left out from here on to save space.

```text
Bob Smith 0
Sue Jones 100000
Smith Jones
110000
```

Notice that Sue's pay is still an integer after the raise. The `int` call inside the method converts the result back. Integer and float values mix freely in expressions, so this choice matters little in a demo. A real system with money needs more care about truncation and rounding.

The book notes several ways to handle money. Chapter 5 covered `round(N, 2)` for keeping cents, the `decimal` type for precise values, and floats displayed with a format string. For now we simply truncate cents with `int`.

We now print Sue's last name too. Because the logic lives in a method, it works on any instance. Python sends the right instance to the first argument, which is usually named `self`. In the first call, `bob` is the subject and goes to `self`. In the second call, `sue` goes to `self` instead.

Trace these calls until the instance-to-`self` link is clear. It is a key idea. The method always fetches the name of whichever instance it was called on. The same holds for `giveRaise`. We could give Bob a raise the same way. Bob's zero pay blocks it, because zero times anything is zero. That is a problem for a future release.

The `giveRaise` method also assumes `percent` is a fraction between zero and one. That assumption may be too loose for the real world, since a 1,000% raise is probably a bug. We allow it for this prototype. Later chapters show how decorators and the `assert` statement can check such values automatically. Chapter 39 builds a tool that validates arguments this way.

```python
@rangetest(percent=(0.0, 1.0)) # Use decorator to validate
def giveRaise(self, percent):
    self.pay = int(self.pay * (1 + percent))
```
### Step 3: Operator overloading

The class now creates instances and adds two behaviors. Testing is still awkward, though. To inspect an object, we print its attributes one at a time. It would be better if printing the whole object showed something useful.

The default display is not helpful. It shows the class name and the object's memory address. The address is only a unique identifier.

To see this, change the last line of the script to `print(sue)`. The output says `sue` is an object and nothing more.

```text
Bob Smith 0
Sue Jones 100000
Smith Jones
<__main__.Person object at 0x104972630>
```

#### Providing print displays

Operator overloading lets a class intercept built-in operations on its instances. The `__repr__` method, along with its twin `__str__`, is one of the most used overloads after `__init__`.

Python runs these methods each time an instance becomes a print string. Printing an object therefore shows whatever `__str__` or `__repr__` returns. The method can be defined on the class or inherited from a superclass. Double-underscore names are inherited like any other name.

Python prefers `__str__` for `print` and `str`. It falls back to `__repr__` when `__str__` is missing. Interactive echoes and nested displays use `__repr__` as well. You can give different displays for different contexts. In practice, coding `__repr__` alone gives one display everywhere. A client can still add `__str__` for a different print view.

The `__init__` method is also an overload, since it runs automatically when an instance is built. Constructors feel like a special case because they are so common. Methods such as `__repr__` let us customize specific operations.

Example 28-8 adds a `__repr__` that lists the attributes when the whole instance is displayed.

**Example 28-8.** `person_8.py` (add a `__repr__` display method)

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
The display string uses an f-string with comma separators for pay. Built-in operations do the real work inside the class. Everything you learned about built-in objects and functions still applies. A class adds a layer of structure that packages functions and data together and supports extension.

The self-test now prints the objects directly. The lines in square brackets come from `__repr__`, and print runs them automatically.

```text
[Person: Bob Smith $0]
[Person: Sue Jones $100,000]
Smith Jones
[Person: Sue Jones $110,000]
```

### Step 4: Customizing behavior by subclassing

The class now does a lot. It creates instances, provides methods, and overloads printing. It packages data and logic into one component, which makes the code easy to find and change. By factoring code into methods, it also avoids repetition.

One major idea is still missing: customization through inheritance. Instances already inherit methods from their class, but that is not the full power of OOP. We need a superclass and a subclass, so we can extend the software and replace parts of the inherited behavior. OOP's core promise is that you build on work already done. Used well, it can cut development time a great deal.

#### Coding subclasses

Next we define a subclass of `Person` called `Manager`. It replaces the inherited `giveRaise` with a more specialized version. The class header looks like this.

```text
class Manager(Person): # Define a subclass of Person
```
The new class `Manager` inherits from `Person` and may add customizations. A manager is almost a person, although the book admits that is a long journey for a small joke. A `Manager` gets raises in a special way.

Assume a manager gets the passed-in percentage plus an extra bonus. The bonus defaults to 10%. A manager who is given a 10% raise therefore receives 20%. Any link to real people is coincidental.

The subclass's new `giveRaise` sits lower in the class tree than the `Person` version. Python's search rule picks the lowest version of a name, so the new method replaces the original for managers.

```text
class Manager(Person): # Inherit Person attrs
def giveRaise(self, percent, bonus=.10): # Redefine to customize
```
#### Augmenting methods: the bad way

There are two ways to write this `Manager` customization. The bad way is easier to see first. You copy the `giveRaise` code from `Person` and edit the copy for managers.

```python
class Manager(Person):
    def giveRaise(self, percent, bonus=.10):
        self.pay = int(self.pay * (1 + percent + bonus)) # Bad: cut and paste
```
This works. A call to `giveRaise` on a `Manager` runs the custom version with the bonus. So what is wrong with code that runs?

Copying code doubles your maintenance work. If the way raises are given changes, which it probably will, you must edit two places instead of one. The example is small, but the issue is universal. When you feel tempted to copy code this way, look for a better design.

#### Augmenting methods: the good way

We want to augment the original `giveRaise`, not replace it. In Python you do that by calling the original version directly with adjusted arguments.

```python
class Manager(Person):
    def giveRaise(self, percent, bonus=.10):
        Person.giveRaise(self, percent + bonus) # Good: augment original
```
A method can be called two ways. Usually you call it through an instance, and Python passes the instance to `self`. Less often you call it through the class, and you pass the instance yourself.

In symbols, a normal call such as `instance.method(args…)` is translated by Python into `class.method(instance, args…)`. The class is found by the inheritance search for the method's name. Both forms work. The asymmetry is that a call through the class requires you to pass the instance manually.

A method always needs a subject instance. Python fills in that argument on its own only when you call through an instance. A call through the class name needs the instance passed by hand. Inside a method such as `giveRaise`, `self` is already the subject, so you pass `self` along.

Calling through the class skips the usual lookup and runs a specific version higher in the tree. That lets us run the default `giveRaise` in `Person`, even though `Manager` redefines it. We must call through `Person` here. A call to `self.giveRaise()` inside the `Manager` method would find `Manager`'s version again and recurse until memory ran out.

The good version may look like a small difference, but the effect on maintenance is large. The raise logic lives in one place, `Person`'s method. Future changes need one edit. The form also states our intent: perform the standard raise, then add a bonus. Example 28-9 shows the full module with this step applied.

**Example 28-9.** `person_9.py` (subclass redefines `giveRaise`)

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
The test code now makes a `Manager`, calls its methods, and prints it. We pass a name and optional job and pay, as before. `Manager` has no constructor of its own, so it inherits `__init__` from `Person`. The output follows.

```text
[Person: Bob Smith $0]
[Person: Sue Jones $100,000]
Smith Jones
[Person: Sue Jones $110,000]
Jones
[Person: Pat Jones $60,000]
```

Pat is a manager. A 10% raise gives Pat 20%, so pay goes from $50K to $60K. The custom `giveRaise` runs for Pat only. Pat also gets `lastName`, the `__init__` constructor, and the `__repr__` display from `Person` by inheritance.

#### The super alternative

The examples so far extend an inherited method by naming the superclass directly, as in `Person.giveRaise(…)`. This is the explicit, traditional, and simplest approach. Most of this book uses it. It follows the same pattern used for class attributes, which are names attached to a class and shared by its instances. Methods are simply callable class attributes.

Java programmers may know that Python also has a `super` built-in. It lets you call a superclass method more generically. In the custom `giveRaise` of `Manager`, these two lines behave the same way.

```python
Person.giveRaise(self, percent + bonus) # Explicit, general use
super().giveRaise(percent + bonus) # Implicit, special case
```

The `super` built-in relies on unusual rules. It works unevenly with operator overloading. It does not always fit multiple inheritance, where one call may not be enough. It is a special-case tool with a single role, and class-name references already do that job.

`super` does have a valid role. It supports cooperative dispatch of same-named methods in multiple inheritance. That role depends on the method resolution order (MRO) explained in Chapter 31. Many programmers find the MRO artificial. Cooperative use requires every class in the tree to follow the same convention. It also does not fully handle method replacement or changing argument lists. For most real Python code, it is a rare need.

This book prefers explicit superclass names, recommends the same for newcomers, and delays `super` until Chapter 32. You are free to decide for yourself. Still, `super` is usually best learned after the simpler and more explicit techniques, especially if you are new to OOP.

To Java programmers the advice is the same. Resist using `super` until you have studied its subtleties. In single inheritance it behaves as you expect. With Python's multiple inheritance, it can pick a class that varies by context, and that class may not even be a superclass.

#### Polymorphism in action

To make inherited behavior more visible, add the following code to the end of the file. The book keeps this as a separate example, `person_9_plus.py`, so it has no full listing.

```python
if __name__ == '__main__':
…
print('--All three--')
for obj in (bob, sue, pat): # Process objects generically
obj.giveRaise(.10) # Run this object's giveRaise
print(obj) # Run the common __repr__
```

The output shows only the new lines, along with the effect of two raises for each person.

```text
…
--All three--
[Person: Bob Smith $0]
[Person: Sue Jones $121,000]
[Person: Pat Jones $72,000]
```

In the loop, `obj` is either a `Person` or a `Manager`. Python picks the right `giveRaise` for each one. Bob and Sue use the original version in `Person`. Pat uses the custom version in `Manager`. Trace the calls yourself to see how each method is selected.

This is polymorphism, which we met earlier in the book. What `giveRaise` does depends on the object you call it on. Sue gets another 10%, but Pat gets another 20%, because the dispatch depends on the object's type. Passing any of the three objects to a function that calls `giveRaise` would produce the same effect. Python's flexibility depends on this idea.

Printing behaves differently. It runs the same `__repr__` for all three objects, because that method is written once in `Person`. `Manager` both specializes the class and reuses the code we first wrote in `Person`. Even in a small example, this shows how classes reuse and customize code.

#### Inherit, customize, and extend

Classes can do more than our example suggests. A subclass can inherit, customize, or extend code from its superclasses. Our example focuses on customization. A subclass can also add methods that the superclass does not have, if the subclass needs them. The following abstract sketch shows the three cases. `giveRaise` customizes an inherited method. `someThingElse` extends the class with something new.

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

An extra method such as `someThingElse` adds to the existing software. It exists only on `Manager` objects, not on `Person` objects. For this tutorial we limit ourselves to customizing `Person` by redefining some of its behavior.

#### OOP: the big idea

Our code is small, but it works, and it shows the main point of OOP. You program by customizing what already exists, rather than copying or changing existing code. Newcomers may not see this as an advantage at first, because classes need extra code. Over time, though, this style can cut development time a great deal.

Consider the alternatives to subclassing for our custom `giveRaise`. Each one falls short.

- We could write `Manager` as new, independent code. Then we must rewrite every behavior that `Manager` shares with `Person`.
- We could change the `Person` class directly. That breaks code that still needs the original `Person` behavior.
- We could copy the whole `Person` class, rename the copy, and edit its `giveRaise`. Later changes to `Person` would not reach the copy automatically, so each change would have to be made twice.

Copying looks quick now, but it doubles the work later. Hierarchies of classes handle software that evolves over time much better. Subclasses let you build on your earlier work instead of starting over, breaking working code, or creating redundant copies. Used well, OOP is a powerful ally.

### Step 5: Customizing constructors, too

The code works, but one detail is odd. A `Manager` must be given the job name `mgr`, even though the class already implies it. The job should be filled in automatically when a `Manager` is made.

The fix uses the same technique as the `giveRaise` customization. We redefine `__init__` in `Manager` so it supplies the `mgr` string. We also call the original `Person.__init__` by class name, so the instance attributes still get set.

Example 28-10 applies this change. The call that creates `pat` no longer passes the `mgr` job name.

**Example 28-10.** `person_10.py` (subclass redefines `__init__`)

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

Calling a superclass constructor this way is a very common Python pattern. By default, Python runs only one `__init__` during construction: the lowest one in the class tree. If higher constructors must run, and usually they do, you call them yourself. You can name the superclass explicitly, choose which arguments to pass up, or skip the call entirely. Skipping the call replaces the superclass logic rather than adding to it.

The output matches the earlier version. We have only removed some redundancy.

```text
$ python3 person_10.py
[Person: Bob Smith $0]
[Person: Sue Jones $100,000]
Smith Jones
[Person: Sue Jones $110,000]
Jones
[Person: Pat Jones $60,000]
```

The sidebar on `super` notes that `super().__init__(…)` without `self` would also run the superclass constructor. That is a common job for `super` in single-inheritance trees. For the reasons already given, this book keeps the explicit form.

### OOP is simpler than you may think

The complete classes cover most of the important ideas in Python's OOP machinery.

- Instance creation: filling out instance attributes.
- Behavior methods: encapsulating logic inside a class.
- Operator overloading: providing behavior for built-in operations such as printing.
- Customizing behavior: redefining methods in subclasses to specialize them.
- Customizing constructors: adding initialization logic on top of superclass steps.

Three simple ideas support most of these concepts. The first is the inheritance search for attributes in a tree of objects. The second is the special `self` argument in methods. The third is operator overloading, which sends built-in operations automatically to methods.

Along the way, the code became easy to change because we factored out repetition. We wrapped logic in methods. We called superclass methods from subclass methods, so no logic is copied. Most of these steps follow naturally from what classes are good at.

That is most of OOP in Python. Classes can grow much larger, and later chapters cover advanced topics such as decorators and metaclasses. The basics are covered here. Once you understand how these classes work, most OOP code in Python should be within reach.

### Other ways to combine classes: composites

The mechanics of OOP are simple in Python. The craft in larger programs lies in how classes fit together. This tutorial focuses on inheritance because Python provides it directly. Programmers also combine classes in other ways.

A common pattern nests objects inside other objects to build composites. Chapter 31 explores this pattern in more depth, and it is more about design than about Python syntax. As a quick preview, we can build the `Manager` extension by embedding a `Person` inside it instead of inheriting from `Person`.

Example 28-11 does this. It uses the `__getattr__` method to intercept attribute fetches that are not found, and the `getattr` built-in to forward them to the embedded object.

`__getattr__` gets full coverage in Chapter 30. Its use here is simple. Python runs it for every fetch of an undefined attribute, meaning one that the inheritance search does not find on the instance. The name also appears in the module-attribute hook from Chapter 25.

The built-in `getattr` was introduced in Chapter 25. It works like the `X.Y` fetch and performs inheritance too. The difference is that the attribute name is a string computed at run time, not a name written literally in the source.

In this version, the constructor creates the embedded object with the job name. `giveRaise` changes the argument it passes to the embedded object. `lastName` triggers `__getattr__`, which reroutes the call to the embedded object. `Manager` becomes a controller that passes calls down to the embedded object, instead of passing them up to superclass methods.

**Example 28-11.** `person-composite.py` (`Manager` embeds a `Person`)

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
The output tests only this `Manager` class. The imported `Person` from Example 28-10 tests its own code. The custom `giveRaise` still turns a 10% raise into 20%. Other calls go to the embedded `Person`, either directly or through attribute rerouting.

```text
$ python3 person-composite.py
Jones
[Person: Pat Jones $60,000]
```

This structure is called delegation. A composite object manages a wrapped object and passes method calls to it.

Delegation works here, but it needs about twice as much code as inheritance. It also fits direct customization less well. `Manager` is not really a `Person` in this design, so we write extra code to dispatch calls. Operator methods such as `__repr__` must be redefined, as the sidebar explained. Adding new `Manager` behavior is harder too, because the state sits one level removed. Few programmers would write this example this way in practice.

Embedding and delegation still fit some jobs well. They suit cases where the embedded object needs only limited interaction with its container. A controller or proxy like this `Manager` can adapt a class to an interface it does not support. It can also trace or validate calls to another object's methods. Class decorators, covered later, use a nearly identical pattern.

A `Department` class can use composition to treat several people as one set. Example 28-12 shows a prototype.

**Example 28-12.** `person-department.py` (group objects in a composite)

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
`showAll` lists every contained object after `giveRaises` updates each one in a polymorphic way. The output looks like this.

```text
$ python3 person-department.py
[Person: Bob Smith $0]
[Person: Sue Jones $110,000]
[Person: Pat Jones $60,000]
```

Our code mixes two techniques. The `Department` class is a composite that holds and controls other objects. The `Person` and `Manager` objects inside it use inheritance to customize their behavior. A GUI works the same way. It may use inheritance to customize labels and buttons, and composition to build forms, calculators, and editors from those widgets. The right structure depends on what you are modeling. Modeling real-world things this way is one of OOP's strengths.

Chapter 31 covers design issues such as composition in detail. For now, `Person` and `Manager` already show the basic mechanics of OOP. The next natural step is writing general tools that make OOP easier to apply in scripts.

#### Delegating built-ins, or not

Example 28-11 redefines `__repr__` so that `print` reaches the embedded `Person`. It does not let `__getattr__` handle that method, as it does for other attributes. In general, a class cannot pass operator methods used by built-in operations to a wrapped object without redefining them. `__repr__` is the only such name in this example, but the issue applies to all delegation-based classes.

Built-in operations such as printing and addition call operator methods, such as `__repr__` and `__add__`, implicitly. These implicit calls do not go through the general attribute managers. Neither `__getattr__`, which runs only for undefined attributes, nor `__getattribute__`, which runs for all attributes, is invoked. The implicit `object` superclass at the top of every class tree also supplies defaults that can stop `__getattr__` from running.

That is why `Manager` must define `__repr__` itself. Comment out that method and watch the result. The `Manager` instance prints with the default display, because `__getattr__` never runs for printing.

```text
$ python3 person-composite.py
Jones
<__main__.Manager object at 0x10a292c30>
```

Built-in operations begin their search for method names at the class. They skip the instance entirely. Explicit attribute fetches, by contrast, check the instance first. Every class also inherits a default `__repr__` from `object`, which can also block `__getattr__`. The `__getattribute__` method does not catch this name either. Methods that are not in `object`, such as `__add__` for `+`, are also missed by `__getattr__`.

This was a limitation in Python 3.X, but it is not a showstopper. Delegation-based classes can still redefine operator methods to forward them to wrapped objects. They can do it by hand, with tools, or through superclasses. The topic is too advanced for this tutorial. Watch for it in Chapter 38, which covers the issue, Chapter 39, which solves it, and Chapter 40, where it appears as a special case in the formal inheritance definition.

### Step 6: Using introspection tools

Before we store the objects, we make one more improvement. The classes are complete and show most of the basics of OOP. Two problems remain to fix before we use them for real.

First, printing `pat` shows the object as a `Person`. That is not wrong, because a `Manager` is a specialized `Person`. Still, an object should display the most specific class it was made from.

Second, the display shows only the attributes that `__repr__` names. It may not show every field we need. For example, we cannot yet verify that `pat`'s job was set to `mgr`, because the `Person` display leaves out the job field. If we add or rename attributes in `__init__`, we must also remember to update `__repr__`. Otherwise the display falls out of sync.

The second problem is another form of redundancy. A mismatch in `__repr__` shows up in the program's output, so it may be more obvious than the others. Still, avoiding extra future work is always good.

#### Special class attributes

The fix uses Python's introspection tools. These are special attributes and functions that expose the internals of objects. They are advanced, and they are mostly used by people who write tools for other programmers. Even so, a basic understanding helps you write code that processes classes in general ways. Two hooks from the previous chapter are useful here.

The first is `instance.__class__`. It links an instance to the class that created it. A class has a `__name__`, just as a module does. It also has a `__bases__` sequence, which gives access to its superclasses. We can use these to print the name of the instance's real class, instead of a name we hardcode.

The second is `object.__dict__`. It is a dictionary with one key and value for each attribute on a namespace object, such as a module, class, or instance. Because it is a dictionary, we can get its keys, index by key, and loop over it. That lets us process every attribute generically. Chapter 25 used the same approach for module tools.

Here is a quick review at the interactive prompt, using the latest `person.py` classes from Example 28-10. A `from` statement loads `Person`, because class names live in modules and are imported like other names.

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

We can use these two hooks inside a base class. That base class shows the correct class name and formats every attribute of an instance of any class. The code goes in a new, independent module named `classtools.py`. Example 28-13 shows it.

The `__repr__` in this class uses generic introspection, so it works on any instance, whatever attributes the instance has. Because it is a class, it can be mixed into any class that wants this display format.

If we ever change the display format, we only need to change this one class. Every class that inherits its `__repr__` picks up the new format the next time a program uses it.

**Example 28-13.** `classtools.py` (new)

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
The docstrings matter here. This is a general-purpose tool, so it should explain itself to the people who use it. Docstrings can appear at the top of functions, modules, classes, and methods. The `help` function and the PyDoc tool display them. The classes chapter returns to docstrings in Chapter 29.

Run directly, the module's self-test makes two instances and prints them. The display shows each instance's class and all of its attribute names and values, in sorted order.

```text
$ python3 classtools.py
[TopTest: attr1=0, attr2=1]
[SubTest: attr1=2, attr2=3]
```

This class uses `__repr__` rather than `__str__`, so its display applies in every context. Clients can still add `__str__`, but it affects only `print` and `str`. They lose the option of a different low-level display unless they define `__repr__` too. A more general tool might use `__str__`, which leaves clients room to add a `__repr__` for interactive prompts and nested displays. The expanded version of this class in Chapter 31 follows that approach. For this demo we keep the all-inclusive `__repr__`.

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

Displaying inherited class attributes is left as an experiment for now. Chapter 29 introduces a `classtree.py` tool that climbs an inheritance tree. Chapter 31 includes attribute listers and climbers in `lister.py`.

#### Name considerations in tool classes

`AttrDisplay` is a general tool meant to be mixed into arbitrary classes. That creates a risk of name collisions with client classes. The code assumes that subclasses may want both `__repr__` and `gatherAttrs`. A subclass may not expect `gatherAttrs`, though. If a subclass defines its own `gatherAttrs`, that version will be used instead of ours, and our class may break.

To see this, add a `gatherAttrs` method to `TopTest` in the self-test. Unless the new method is identical or deliberately customizes the original, the tool stops working as planned. The `self.gatherAttrs` call inside `AttrDisplay` searches again from the `TopTest` instance, so it finds the new method.

```python
class TopTest(AttrDisplay):
…
def gatherAttrs(self): # Replaces method in AttrDisplay!
return 'Oops'
```

This is not always a problem. Sometimes we want subclasses to call a method or customize it. If we only meant to provide `__repr__`, though, this behavior is not ideal.

Python programmers reduce collisions by prefixing methods that are not for external use with a single underscore. In our case the name becomes `_gatherAttrs`. This is not foolproof, because another class may use the same private-looking name. It is usually good enough, and it is a common convention for internal methods.

A stronger option is two leading underscores, such as `__gatherAttrs`. Python expands such a name to include the enclosing class's name, which makes it unique during the inheritance search. This is called a pseudoprivate attribute. Chapter 31 covers it and uses it in an expanded version of this class. For now we keep both methods available.

#### Our classes' final form

To use the generic display tool, we import it, mix it in by inheritance at the top class, and remove the specific `__repr__` we wrote earlier. The new display method is inherited by `Person` instances and by `Manager` instances. `Manager` gets `__repr__` from `Person`, which in turn gets it from `AttrDisplay` in another module. Example 28-14 is the final `person.py` with these changes.

**Example 28-14.** `person_14.py` (final)

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

Now every attribute of each object appears in the display, not only the ones we hardcoded earlier. Each object shows the name of its lowest class. `pat` now displays as a `Manager`, not a `Person`. We can also confirm that the `Manager` constructor filled in the job name.

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

The objects are still not real database records, though. If Python or the program stops, the instances disappear, because they live only in memory. Object persistence solves this. It makes objects outlive the program that created them. The final step is to make our objects permanent.

#### Pickles and shelves

Three standard-library modules, installed with Python, implement object persistence.

- `pickle`: serializes arbitrary Python objects to and from a string of bytes.

- `dbm`: implements an access-by-key file system for storing strings.

- `shelve`: uses the other two modules to store Python objects in a file by key.

Chapter 9 introduced `pickle` and briefly mentioned `shelve` when we studied file basics. These modules offer simple but useful storage. A short introduction is enough to get started, though the book cannot cover them fully here.

#### The pickle module

The `pickle` module formats and parses objects. Given almost any Python object in memory, it converts the object to a byte string. It can later rebuild the original object from that string. `pickle` handles most objects, including lists, dictionaries, nested combinations of them, and class instances. Instances are especially useful to pickle, because they hold both data as attributes and behavior as methods. That pairing is roughly like keeping records and programs together.

`pickle` can replace code you might otherwise write to build and parse custom text-file formats. You store an object's pickle string in a file, which makes the object persistent. Later, you load and unpickle the string to rebuild the object.

#### The shelve module

You can store pickles in flat files with `pickle` alone. The `shelve` module adds a layer of structure. It stores pickled objects under keys. Under the hood, `shelve` turns each object into a pickle with `pickle`, and saves the string under a key in a `dbm` file. When you load a key, `shelve` fetches the string and rebuilds the object with `pickle`.

To your script, a shelf looks like a dictionary. You index by key to fetch, assign to a key to store, and use tools such as `len`, `in`, and `dict.keys` to inspect it. Shelves map these dictionary operations onto pickled objects in a file.

The main difference from a normal dictionary is that you must open a shelf first and close it after you change it. The result is a simple database for native Python objects, stored by key and persistent across runs. It has no SQL query support, though Python's `sqlite3` module does. It also lacks advanced features such as real transaction processing, which other Python database tools provide. Shelves still store native Python objects, and you can use the full language on them after fetching by key.

#### Storing objects on a shelve database

Pickles and shelves are advanced topics, and this book does not cover every detail. The standard-library manuals describe them fully. The code is simpler than the explanation, so we start with it.

The new script stores our objects on a shelf. Because it is a new file, it must import the classes to make instances. There are two ways to load a class from a module.

```python
import person # Load class with import
bob = person.Person(…) # Go through module name
from person import Person # Load class with from
bob = Person(…) # Use name directly
```

The script uses `from` because it is shorter. It repeats some of the self-test lines from `person.py` to create instances to store. The redundancy is acceptable in a demo. Once we have instances, storing them on a shelf is simple. Import `shelve`, open a shelf with an external file name, assign each object to a key, and close the shelf.

**Example 28-15.** `makedb.py` (save `Person` objects to a shelf)

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
The example uses each object's name as its key. This is for convenience. A key can be any string, including one built from process IDs and timestamps with the `os` and `time` modules. Keys must be strings and should be unique, because each key stores one object. That object can be a list, a dictionary, or any object that holds many others.

The values can be almost any Python object. That includes built-in types such as strings, lists, tuples, and dictionaries. It also includes class instances and nested combinations of all of these. The `name` and `job` attributes could be nested dictionaries and lists, as in earlier examples, though the code would need some redesign.

The script prints nothing. If it runs without output, it probably worked. It creates and stores objects in a file-based database.

```text
$ python3 makedb.py
```

#### Exploring shelves interactively

After the script runs, files whose names start with `persondb` exist in the current directory. The exact file names vary by system. Like the built-in `open`, `shelve.open()` resolves a relative file name against the current working directory, unless the name includes a directory path. These files form a keyed-access store that holds the pickled form of our three objects. Do not delete them. They are your database, and you must copy them when you back up or move the data.

You can inspect the files from a file browser, a shell, or the Python prompt. They are binary hash files, and their contents make little sense outside `shelve`. The standard `glob` module can list them. On macOS the shelf is a single file named `persondb.db`. You can open it in binary mode to look at the bytes.

```python
>>> import glob
>>> glob.glob('persondb*')
['persondb.db']
>>> print(open('persondb.db', 'rb').read())
b'\x00\x06\x15a\x00\x00\x00\x02\x00\x00\x04\xd2\x00\x00…much more omitted…
```

The bytes vary, and they are hard to decode. This is not a friendly database interface. A better check is another script, or a session at the prompt. Shelves are Python objects that contain Python objects, so normal Python syntax works on them. The prompt acts as a database client.

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

So loaded instances get all their class behavior back. We import classes only to make new instances. We do not need them to process existing ones. This design has trade-offs.

The downside is that the classes and their module files must be importable when an instance loads. The class must sit at the top level of a module on `sys.path`. It should not live in the `__main__` script unless the script is always the module in use. For this reason, some programs pickle plain dictionaries or lists instead, especially when the data moves across networks.

The upside is that edits to a class's source file are picked up automatically when instances load again. The stored objects often need no update, because changing the class changes their behavior.

Shelves have other limitations, which the standard library manual covers. For simple object storage, though, shelves and pickles are easy tools for personal databases, program configuration, and similar uses.

#### Updating objects on a shelf

One more script shows that the objects persist. Each run prints the database and gives a raise to one stored object. Example 28-16 does this. Tracing it shows how much comes for free. Printing uses the general `__repr__`, and the raise uses the `giveRaise` method we wrote earlier. The same class behavior still works after the object comes back from disk.

**Example 28-16.** `updatedb.py` (change a stored `Person` and save it)

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
The script prints the database at startup, so you must run it at least twice to see a change. Each run raises Sue's pay by 10%. The book suggests scheduling it as a regular `cron` job.

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

The `shelve` and `pickle` modules provide the storage. Our classes provide the behavior. You can verify the result at the prompt, which again acts as a database client.

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

Much more is possible. You could make the classes more realistic, add behaviors, and extend them in other ways. A raise, for example, should check that the rate is between zero and one. Decorators, covered later, can do that check. You could also turn this example into a personal contacts database by changing the stored state and the methods that process it. That is left as an exercise for you.

Other tools are also worth exploring. GUIs, websites, and apps make a database usable by people who do not program. Other database interfaces, such as `sqlite3`, and formats such as JSON offer more options. Those topics go beyond this tutorial and this book. The standard library manuals, the web, and application-level books cover them. The next section returns to class fundamentals and completes the core language.

## Chapter summary

This chapter explored Python's class fundamentals by building one realistic example step by step. We added constructors, methods, operator overloading, subclass customization, and introspection tools. Along the way we met composition, delegation, and polymorphism.

We also stored the objects on a `shelve` database. That gives a simple way to save and retrieve native Python objects by key. While learning class basics, we saw several ways to factor code and reduce redundancy. Less redundancy means lower maintenance costs later.

The next chapters resume the details of Python's class model. They also cover how classes combine in larger designs.

## Class coding details: the class statement

The `class` statement looks familiar if you have used other object-oriented languages. It behaves differently in one key way. In C++, `class` is a declaration. In Python, a `class` statement is an object builder and an implicit assignment. When Python runs it, the statement creates a class object and stores a reference to that object in the name used in the header.

Like `def`, the `class` statement is executable code. Your class does not exist until Python reaches and runs the statement that defines it. That usually happens while Python imports the module that holds the class, and not before.

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

Inside the `class` statement, every assignment creates a class attribute. That covers data items and functions, which are called methods. Specially named methods implement built-in operations. For example, a function named `__init__` runs when an instance is built, if you define it. Calling the class after its `class` statement has run makes instances.

### Class attributes and shared data

Classes are mostly namespaces. They define names, called attributes, that export data and logic to clients. A module file works the same way. The statements nested in a `class` body create the class's namespace. When Python runs the statement, it runs each nested statement from top to bottom. Each assignment creates a name in the class's local scope, and that name becomes an attribute of the class object.

Classes resemble both modules and functions:

- Like functions, `class` statements are local scopes where nested assignments create names.
- Like modules, names assigned in a `class` statement become attributes of the class object.

The main difference is inheritance. A class's namespace is the basis of inheritance. If Python cannot find an attribute on an instance, it looks for it in the classes above.

Any statement can appear in a class body, including `print`, assignments, `if`, and `def`. All of them run when the `class` statement runs, not later when the class makes an instance. Assignments usually create data attributes, and nested `def` statements create method attributes. Any name assigned at the top level of a `class` statement becomes an attribute with that same name.

A simple nonfunction object assigned to a class attribute becomes a data attribute shared by all instances:

```python
>>> class SharedData:
...     attr = 16              # Generates a class data attribute
...
>>> x = SharedData()           # Make two instances
>>> y = SharedData()
>>> x.attr, y.attr             # They inherit and share 'attr' (a.k.a. SharedData.attr)
(16, 16)
```

Here `attr` is assigned at the top level of the class, so it attaches to the class. Every instance shares it through the search from instance to class. You can change it through the class name. You can read it through an instance or through the class:

```python
>>> SharedData.attr = 32
>>> x.attr, y.attr, SharedData.attr
(32, 32, 32)
```

Class attributes like this can track information about all instances, such as a count of how many were made. Chapter 32 shows that idea with a full example. Now assign the same name through an instance:

```python
>>> x.attr = 64
>>> x.attr, y.attr, SharedData.attr
(64, 32, 32)
```

An assignment to an instance attribute creates or changes a name on that instance, not on the shared class. Inheritance searches happen on attribute references, not on attribute assignments. Assigning to an object's attribute changes only that object. The name `y.attr` still comes from the class. The assignment to `x.attr` attaches a new name to `x`, which hides the class version.

Readers who know other languages may call class attributes like `SharedData.attr` static data members. Python needs no special term for them. Every class attribute is just a name assigned in a `class` statement. When that name refers to a function, it acts as a method and receives an instance when called through one.

Here is a class that stores the same name in two places:

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

Making instances attaches `data` to each of them, through the `self.data` assignment in `__init__`:

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

Methods are function objects created by `def` statements nested in a `class` body. From an abstract view, methods give instances behavior to inherit. From a programming view, they work like simple functions. There is one crucial exception. A method's first argument receives the instance that is the subject of the call.

A method call made through an instance looks like this:

```text
instance.method(args…)
```

Python translates it into a call on the class:

```text
class.method(instance, args…)
```

Python finds the class by the inheritance search for the method's name. Both forms are valid. In the second form, the class name narrows the search, and you pass the instance yourself. The result is the same.

By convention, the first argument of a method is named `self`. Only its position matters, not its name. The argument gives the method a link back to the instance being processed. Because a class makes many instances, `self` is how each method manages its own instance's data. In Python, `self` is always explicit. A method must list `self` and use it to fetch or change instance attributes. That makes it clear that a name refers to an instance attribute and not to a local or global name.

### A method example

Here is a small class with one method:

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

We can also call the method through the class name, as long as we pass an instance to `self` ourselves:

```python
>>> NextClass.printer(x, 'class call')       # Direct class call
class call
>>> x.message                                # Instance changed again
'class call'
```

Calls through the instance and calls through the class have the same effect, as long as we pass the same instance by hand. Calling the method through the class with no instance fails:

```python
>>> NextClass.printer('bad call')
TypeError: NextClass.printer() missing 1 required positional argument: 'text'
```

Class methods are really just functions assigned to class attributes. Some of them expect an instance. Python supplies that instance automatically only when the call goes through an instance. Fetching a method through the class uses the same `class.attribute` pattern that fetches any class attribute. That tool works on any object, callable or not.

### Other method-call possibilities

Calling a method through the class is the basis for extending inherited behavior, instead of replacing it. The call needs an explicit instance, because a normal method always receives one. Methods called through instances are instance methods unless special code changes that.

Chapter 32 introduces static methods, which do not expect an instance even when called through one. Static methods act like simple functions with names local to their class. Class methods receive the class instead of an instance. They can manage data for the whole class. Metaclasses also use class methods, and Chapter 40 covers them. These are optional and less common extensions. Normally, you pass an instance to a method, either automatically through an instance or by hand through the class.

## Inheritance in detail

Inheritance happens when an object is qualified. Python searches a tree of attribute namespaces. For an expression like `object.attr`, the search starts at `object` and moves upward. It stops at the first `attr` it finds. The same search runs for `self` attributes inside methods. Lower definitions override higher ones, and that override is the basis of specialization.

### Building the attribute tree

Three kinds of code build the tree:

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

The `Sub` class replaces `Super`'s `method`. Inside the replacement, it calls the `Super` version to run the default behavior. So `Sub.method` extends the superclass method instead of replacing it completely:

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

This is one of the few places where you call an operator-overloading method directly. Call the superclass constructor this way only when you want it to run. Without the call, the subclass replaces the superclass constructor completely.

Redefining a constructor inside the same class with a different argument list does not add a second constructor. Later `def` statements simply reassign the method name, so only the last one is used. Starred arguments can handle this, but they are rarely used. Chapter 31 explains polymorphism more fully. Its lesson is about interfaces, not about call signatures.

### The super alternative

Python also has a `super` built-in. It calls a superclass method more generally. The following two lines do the same job in the `Sub` class above:

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

Subclasses can interface with a superclass in more than one way. The file `specialize.py` in Example 29-1 defines several classes that show common techniques. Study how each one customizes the shared superclass.

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

Two details in this file are worth noticing. The self-test creates instances of three classes in one `for` loop. Classes, like functions, are first-class objects. You can store them in a tuple and create instances from them with no extra syntax. Classes also have a built-in `__name__` attribute, just as modules do. It holds the name from the class header. Running the file produces this output:

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

Trace the code yourself to see how each line of output is produced.

### Abstract superclasses

`Provider` is one of the most important classes in that example. When you call `delegate` through a `Provider` instance, two separate inheritance searches happen:

1. The first `x.delegate` call finds the `delegate` method in `Super`. The search starts at the `Provider` instance and moves upward. The instance `x` goes to the method's `self` argument.
2. Inside `Super.delegate`, `self.action` starts a new search from `self` upward. Because `self` refers to a `Provider` instance, the search finds `action` in `Provider`.

This filling-in-the-blanks structure is typical of object-oriented frameworks. A framework might handle a GUI event, render data in a web page, or process a tag in an XML file. Your subclass supplies the specific actions. The framework handles the rest and runs your actions when they are needed.

For `delegate`, the superclass is an abstract superclass. It expects parts of its behavior to come from its subclasses. If a subclass does not define the expected method, the inheritance search fails, and Python raises an undefined-name exception.

Class coders often make such requirements clearer. They use `assert` statements, or they raise the built-in `NotImplementedError` in stub methods. Chapters 33 and 34 cover `assert` and exceptions in depth. Here is the `assert` version:

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

An `assert` raises an exception with the message you give when its first expression is false. Here the expression is always false, so the stub triggers an error if a subclass forgets to redefine the method. The `NotImplementedError` version signals the same mistake:

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

Subclasses still get the exception, unless they provide the expected method and replace the superclass stub:

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

A class with an abstract method cannot be instantiated unless every abstract method is defined in a subclass. This takes more code and more knowledge. Its advantage is that missing methods are reported when you try to make an instance. The older scheme reports them later, when you call the missing method. This approach can also define an expected interface that client classes must meet.

This scheme depends on tools we have not covered yet. It uses function decorators, which Chapter 32 introduces and Chapter 39 covers in depth. It also uses metaclass declarations, which Chapter 32 mentions and Chapter 40 covers. Python's standard manuals describe this option further, along with the abstract superclasses that Python already provides.

## Namespaces and scopes in classes

With classes and instances covered, the Python namespace story is complete. This section summarizes the rules for resolving names. It also extends them to classes. Two ideas come first. Qualified and unqualified names are handled differently. Some scopes initialize object namespaces.

- Unqualified names, such as `X`, deal with scopes.
- Qualified attribute names, such as `object.X`, use object namespaces.
- Some scopes initialize object namespaces, namely those for modules and classes.

These ideas interact. In `object.X`, Python first looks up `object` by scope. Then it looks up `X` in the object it found. Let us flesh out the rules.

### Simple names: global unless assigned

Unqualified simple names follow the LEGB rule. Chapter 17 introduced it when we studied functions. Its two parts work this way:

- Assignment (`X = value`) makes a name local by default. It creates or changes `X` in the current local scope, unless the scope declares it `global` or `nonlocal`. These declarations work in `def` for functions and in `class` for classes.
- Reference (`X`) looks in the current local scope first. Then it checks enclosing functions from inner to outer. Then it checks the global scope of the current module. Last, it checks the built-in module. Enclosing classes are never searched, so class names are reached as object attributes.

Some constructs localize names further. Examples include some comprehensions and some `try` statement clauses. Nested class scopes also have quirks that come from old bug reports. Those quirks are too obscure to cover here. Most names still follow the LEGB rule.

The `class` statement accepts `global` and `nonlocal`, just as `def` does. You need to nest the class inside a function to see how `nonlocal` works:

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

These declarations are rare. They map assignments to outer scopes instead of making class attributes. They also stop assignments from creating local variables in a function. The section on nested classes covers how this interacts with scopes.

### Attribute names: object namespaces

Qualified attribute names refer to attributes of specific objects. They follow the rules for modules and classes. For class and instance objects, the reference rules also include the inheritance search:

- Assignment (`object.X = value`) creates or changes the attribute `X` in the namespace of the qualified object only. Climbing the inheritance tree happens on reference, not on assignment.
- Reference (`object.X`) searches for `X` in the object first. Then it searches each accessible class above it, using inheritance. For module objects, Python fetches `X` from the module directly.

These rules cover typical code. Advanced tools change them. Metaclasses can make reference inheritance richer. Properties, descriptors, and `__setattr__` can route assignments in other ways. Some inheritance also runs on assignment, to find descriptors with a `__set__` method. Chapter 38 covers attribute management tools, and Chapter 40 formalizes inheritance. For now, focus on the normal rules, which cover most application code.

### The rule of assignments: assignments classify names

Name lookup has separate search paths for qualified and unqualified names. Each path has several layers. It can be hard to tell where a name will end up. The key idea is that the place where you assign a name decides where it lives. An assignment decides the scope or object for that name. The file `manynames.py` in Example 29-2 shows this idea in code. It leaves out obscure special cases such as comprehensions.

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

Example 29-3 holds the rest of the file, which includes a self-test. It makes an instance and prints each `X` it can reach:

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

The call to `manynames.f()` prints the `X` in `manynames`, not the `X` in this file. Scopes are set by the position of assignments in the source code. Imports do not change them. The instance's own `X` does not exist until `I.m()` runs. Attributes, like all variables, appear when they are assigned. We usually create instance attributes in an `__init__` constructor, but other options exist.

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

Even when scripts reuse one name in several places, Python's namespaces keep those uses apart. Still, you should not give every variable the same name in a real script.

### Nested classes and the LEGB rule

Classes can be nested inside functions. This is a useful pattern in some programs. The scope effects follow from what you already know about functions. They may still surprise you the first time you see them.

Classes often appear nested in the functions that generate them. This resembles the factory function, or closure, idea from Chapter 17. The function keeps state for the class to use later. Each `class` statement creates a new local scope, just as `def` does. The LEGB rule applies to the top level of the class and to the top level of its methods. Both are local scopes, and both can see their own names, enclosing function names, module globals, and built-ins. While the `class` statement runs, the class body is a local scope. After it finishes, the class body becomes an attribute namespace, like a module does.

A class can see enclosing functions, but it is not an enclosing scope for the code nested inside it. Python searches enclosing functions for names. It never searches enclosing classes. Method functions must therefore reach class attributes through `self` or the class name, using inheritance.

Example 29-6 shows this effect:

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

Example 29-8 reassigns the name at several levels. Assignments in the local scopes of both functions and classes hide globals and enclosing function locals with the same name:

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

The main point is that simple-name lookup never searches enclosing classes. It searches `def` scopes, modules, and built-ins. In `method1`, the name `X` is found in the enclosing `def`, even though the class has its own `X`. To reach names assigned in a class, such as methods or class attributes, use object attributes, such as `self.X`. You will see this nested-class pattern later in the book, especially in some decorators from Chapter 39. There, the enclosing function usually builds a class or instance and keeps state for the class to use.

## Namespace dictionaries and class trees

Chapter 23 showed that module namespaces are dictionaries, exposed through the `__dict__` attribute. Classes and instances work the same way. Attribute access is mostly a dictionary lookup, and attribute inheritance searches a chain of linked dictionaries. Instance and class objects are largely dictionaries with links between them. Python exposes these dictionaries and their links for advanced uses.

We can see how attributes work by watching the namespace dictionaries grow. First, define a superclass and a subclass. Each one has a method that stores data on its instances:

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

The class dictionaries include extra underscore names. Python sets these automatically. Most are not used in typical programs. Tools use some of them, such as `__doc__`, which holds the docstrings from Chapter 15. You can filter them out with a comprehension.

Notice that `Y` still has an empty dictionary. Its instance was made before `X` gained attributes, and each instance has its own independent dictionary. Two instances of the same class can record completely different attributes.

Instance attributes are also dictionary keys, so you can read and write them in two ways. You can qualify the name with a dot, or you can index the dictionary by key:

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

Key indexing works only for attributes stored on the instance. Qualification also runs the inheritance search, so it can reach inherited attributes that the dictionary cannot. For example, `X.hello` is reachable, but `X.__dict__['hello']` fails. Try these special attributes yourself. The `dir` function is similar to `X.__dict__.keys()`, but `dir` sorts its list and also includes inherited names.

Chapter 32 introduces slots, an advanced class feature. Slots store attributes in the instance without using its namespace dictionary. They look like class attributes, because they appear in class namespaces where they manage per-instance values. A slot may prevent a `__dict__` from being created for the instance. Generic tools must allow for that, so they often use `dir` to list names and `getattr` to fetch them. Slots are rare, which is how they should be.

### Namespace links: a tree climber

The special `__class__` and `__bases__` attributes let you inspect inheritance hierarchies in your own code. They can display a class tree. The module in Example 29-9, `classtree.py`, does this:

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

The `classtree` function is recursive. It prints a class's name with `__name__`, then calls itself on each superclass. This lets it walk any shape of class tree. The recursion stops at root superclasses, whose `__bases__` is empty. Chapter 19 explains recursion. Each active call gets its own copy of the local names, so `cls` and `indent` differ at each level.

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

Periods mark the height of each class in the tree. You could improve this display, or draw it in a GUI. You can also import these functions anywhere you want a quick view of a class tree:

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

Docstrings can appear in class components, not only in modules. A docstring is a string literal at the top of a module, function, class, or method. Python saves it in the object's `__doc__` attribute. Chapter 15 covers docstrings in detail. Example 29-10, `docstr.py`, summarizes where they can appear. Each one can be a triple-quoted block or a short one-line literal:

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

The main advantage of a docstring is that it stays available while the program runs. You qualify an object with `__doc__` to fetch its documentation. Calling `print` on a multiline string shows its line breaks:

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

Docstrings are available at runtime, but they are less flexible than `#` comments. Comments can appear anywhere in a program. Both are useful, and accurate documentation of either kind is good. A common rule of thumb is to use docstrings for higher-level documentation of functions and classes. Use hash-mark comments for fine-grained notes on the code itself.

## Classes versus modules

Modules and classes both create namespaces, so the difference can be confusing. The contrast is easier to see side by side:

- Modules implement packages of data and logic. They are created from Python files or from other-language extensions. You use them by importing. They form the top level of a Python program's structure.
- Classes implement new, full-featured objects. You create them with `class` statements. You use them by calling them. They always live inside a module.

Classes also support features that modules do not. These include operator overloading, multiple instance generation, and inheritance. Both classes and modules are namespaces, but they serve different purposes. Chapter 30 starts the next topic, operator overloading.

## Class coding details summary

This section took a second, deeper pass through Python's class mechanics. It covered classes, methods, and inheritance. It also summarized how names and scopes work once classes are included. Along the way, it introduced abstract superclasses, class data attributes, namespace links, and manual calls to superclass methods and constructors. Keep these ideas in mind when you read real class hierarchies.

## Operator overloading

Operator overloading lets a class intercept the built-in operations that Python runs on its instances. You have already met it through `__init__`. This section fills in more of the picture. It covers a representative sample of the methods you will use most often.

The key ideas are short:

- Operator overloading lets classes intercept normal Python operations.
- Classes can overload all built-in expression operators.
- Classes can also overload other operations, such as printing, function calls, and attribute access.
- Overloading works by providing specially named methods, and Python predefines those names.

When a class provides one of these methods, Python calls it whenever an instance appears in the matching operation. The method's return value becomes the result of that operation.

### Overloading methods are optional

Operator-overloading methods are never required, and they generally have no defaults. The exception is a handful that every class gets from the implied `object` root class. If a class does not code or inherit a method, it does not support that operation. Using the operation then raises an exception.

Printing is one of the built-in operations that has a default from `object`. Most others fail for an instance when the matching method is missing. When you do provide these methods, your class can emulate the interface of a built-in object. That makes it consistent and compatible with more code.

Most overloading methods appear only in advanced programs. The `__init__` constructor is the main exception, because most classes use it.

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

The `__sub__` method plays the binary-operator role that `__add__` played in Chapter 27. It returns a new instance, and creating that instance runs `__init__` again.

Instance creation actually begins with `__new__`. That method creates the object, and Python then passes the object to `__init__`. Most classes never define `__new__`, because its built-in version covers nearly every case. Chapter 40 uses it with metaclasses. It is also sometimes used to customize how instances of immutable types are created.

### Common operator-overloading methods

Table 30-1 lists some of the most common overloading methods. Python supports many more.

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

Many overloading methods come in several versions. Addition, for example, has `__add__`, `__radd__`, and `__iadd__`. The Python language reference lists every special method name.

Every overloading method name starts and ends with two underscores. That keeps it distinct from names you define yourself. The name `__add__` always maps to the `+` expression, whatever its code does. The method is mainly a dispatch mechanism.

Overloading methods can be inherited from superclasses, like any other method. If none is coded or inherited, the operation is unsupported.

#### Measure before you optimize

Calling an operator method directly is not faster than using the operator. Calling `__len__` directly is about twice as slow as `len`. Python avoids or optimizes the function-call overhead in the built-in case. Some advice in circulation recommends the slower call for speed, so measure before you adopt it.

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

The `__getitem__` method lets a class mimic some behavior of sequences and mappings. If a class defines it, or inherits it, Python calls it for indexing. For `X[i]`, Python calls `X.__getitem__` and passes the index as the second argument.

The class decides what the expression means. It should usually imitate a sequence index or a mapping key fetch. The following class returns the square of the index. That is an unusual choice, but it shows the mechanism clearly.

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

The `__getitem__` method is also called for slice expressions. Built-in types handle slicing the same way. Slice bounds are bundled into a slice object, and that object is passed to the indexing operation. You can also pass a slice object yourself.

```text
>>> L = [5, 6, 7, 8, 9]
>>> L[2:4]                  # Slice with slice syntax
[7, 8]
>>> L[slice(2, 4)]          # Slice with a slice object
[7, 8]
>>> L[slice(None, None, 2)]
[5, 7, 9]
```

Slice syntax is mostly shorthand for indexing with a slice object. A class with `__getitem__` receives the same object. The method gets an integer for plain indexing and a slice object for slicing.

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

The method can test the type of its argument. A slice object has the attributes `start`, `stop`, and `step`. Any of them can be `None` when omitted.

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

Run `help(slice)` in a REPL to learn more about this special built-in type.

#### Intercepting item assignments

The `__setitem__` method catches index assignment. It also catches slice assignment, and it receives a slice object in that case. The method can pass the index or slice along to the embedded object.

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

The `__index__` method is easy to confuse with `__getitem__`. It does not intercept indexing. It returns an integer value for an instance when Python needs one. The name is a little unfortunate, and `__asindex__` might have been a better choice.

Built-ins that convert numbers to digit strings use `__index__`:

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

Contexts that need an integer also use it, including indexing and slicing. The instance supplies the integer, and the list does the rest.

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

The `for` statement has a fallback. Without a more specific iteration method, it indexes an object from zero upward. It stops when an `IndexError` exception appears. So a class with only `__getitem__` supports `for` loops too.

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

This is a case of getting one feature and receiving a bunch more. Any object that supports `for` loops also supports the other iteration tools. These include the `in` test, list comprehensions, `map`, sequence assignment, and some type constructors.

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

Example 30-2 defines a user-defined iterable that produces squares on demand.

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

```text
>>> X = Squares(1, 5)
>>> [n for n in X]          # Exhausts items: __iter__ returns self
[1, 4, 9, 16, 25]
>>> [n for n in X]          # Now it is empty
[]
>>> [n for n in Squares(1, 5)]   # A new object gives a fresh copy of state
[1, 4, 9, 16, 25]
```

Each new iteration needs a new iterable object. The membership test, sequence assignment, and string joins all call `__iter__` in the same way.

```text
>>> 36 in Squares(1, 10)
True
>>> a, b, c = Squares(1, 3)
>>> ':'.join(map(str, Squares(1, 5)))
'1:4:9:16:25'
```

Converting the iterable to a list allows several scans. It also costs time and memory, which may or may not matter for your program.

```text
>>> X = Squares(1, 5)
>>> tuple(X), tuple(X)      # Iterator exhausted in second tuple()
((1, 4, 9, 16, 25), ())
>>> X = list(Squares(1, 5))
>>> tuple(X), tuple(X)
((1, 4, 9, 16, 25), (1, 4, 9, 16, 25))
```

The `Squares` class does not overload indexing. Its iterable is designed for iteration, not random access. The expression `X[1]` raises `TypeError: 'Squares' object is not subscriptable`. Collecting the items in a list makes indexing possible.

### Classes versus generators

The `Squares` class would be shorter as a generator function or a generator expression. Those tools save their state and create the iteration methods for you.

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

Each active loop over a string gets its own iterator. The loops can move through the string independently.

```text
>>> S = 'ace'
>>> for x in S:
...     for y in S:
...         print(x + y, end=' ')
aa ac ae ca cc ce ea ec ee
```

The outer loop calls `iter` on the string, and each nested loop does the same. Each iterator keeps its own position. The string object itself supports several scans, so no copy is needed.

Generator functions, generator expressions, `map`, and `zip` each return a single-iterator object. The `range` built-in and lists support several active iterators with independent positions. A user-defined class decides which behavior it provides. To support several iterations, `__iter__` must return a new stateful object for each request, not `self`.

Example 30-3 defines an iterable that skips every other item. Each `__iter__` call creates a new iterator object from a supplemental class. That lets several loops run at once.

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

The `Squares` class of Example 30-2 supports only one active loop. A nested loop would run only once unless it created a new object. Here, there is one `SkipObject` and several iterator objects.

#### Classes versus slices

Slicing can give similar results. The third bound skips items.

```text
>>> S = 'abcdef'
>>> for x in S[::2]:
...     for y in S[::2]:            # New objects on each iteration
...         print(x + y, end=' ')
aa ac ae ca cc ce ea ec ee
```

The two approaches differ in two ways. Each slice stores its whole result in memory at once. An iterable produces one value at a time, which can save space and startup time for large results. Slices also create new objects, so no single object is being scanned in several places.

To be closer to the class, slice the string once and then loop over the result.

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

You can shorten a user-defined iterable by combining `__iter__` with the `yield` statement from Chapter 20. Any function that contains `yield` becomes a generator function. Calling it returns a generator object. That object keeps its local scope and code position. It also has an automatic `__iter__` that returns itself and an automatic `__next__` that resumes the function.

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

Example 30-4 is equivalent to the explicit `Squares` class of Example 30-2, and it is shorter.

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

The `yield` version is shorter, but it relies on two implicit mechanisms. Some readers find that too much magic. The explicit `__next__` version is more general, and it sometimes fits a broader job. Know both, and choose the one that fits the task.

#### Multiple iterators with `yield`

The `__iter__` and `yield` combination also supports multiple active iterators automatically. Each call to `__iter__` is a new call to a generator function. That call returns a new generator with its own local scope.

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

Each `for` loop asks the class for a new generator. So nested loops over the same instance work.

```text
>>> S = Squares(1, 3)
>>> for i in S:                # Each "for" calls __iter__
...     for j in S:
...         print(f'{i}:{j}', end=' ')
1:1 1:4 1:9 4:1 4:4 4:9 9:1 9:4 9:9
```

Without `yield`, the class needs a supplemental iterator class that stores the state by hand. Example 30-6 does this. It takes 15 lines, which is 8 more than the `yield` version.

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

These examples are artificial, and comprehensions could replace them. Study the alternatives to see how they compare. The best tool for the job is the one that fits your job.

### Membership: `__contains__`, `__iter__`, and `__getitem__`

Operator overloading is often layered. A class can provide a specific method, plus a more general fallback. Membership with `in` follows this pattern. It can use `__iter__`, or `__getitem__` as a fallback. A `__contains__` method is more specific, so Python prefers it over both.

For a mapping, `__contains__` should check keys, and it can use quick lookups. For a sequence, it should search the items.

Example 30-8 defines a class with all three methods. Each method prints a trace message, so you can see which one runs.

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

With `__contains__` present, the output shows that `in` calls it, and the other tools call `__iter__`. The `__getitem__` method is never called.

```text
$ python3 contains.py
In @contains True
For @iter @next 1 | @next 2 | @next 3 | @next 4 | @next
Comp @iter @next @next @next @next @next [1, 4, 9, 16]
Map @iter @next @next @next @next @next ['0b1', '0b10', '0b11', '0b100']
Manual @iter @next 1 | @next 2 | @next 3 | @next 4 | @next
```

If you comment out `__contains__`, membership falls back to `__iter__`:

```text
$ python3 contains.py
In @iter @next @next @next True
For @iter @next 1 | @next 2 | @next 3 | @next 4 | @next
```

If you comment out both `__contains__` and `__iter__`, Python uses `__getitem__` with successively higher indexes. It stops when `IndexError` is raised.

```text
$ python3 contains.py
In @get[0] @get[1] @get[2] True
For @get[0] 1 | @get[1] 2 | @get[2] 3 | @get[3] 4 | @get[4]
```

The `__getitem__` method also handles explicit indexing and slicing. Slice expressions call it with a slice object. The following output comes from the class with `__iter__` disabled.

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

Classes can intercept attribute access too. For an object, `object.attribute` can be implemented by your code. That covers reference, assignment, and deletion. Chapter 28 showed a small rerouting example. This section covers the topic in more detail.

#### Attribute reference

The `__getattr__` method intercepts attribute references. Python calls it with the attribute name as a string. It runs only when the name is not found through the normal inheritance search.

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

Here, `Empty` has no real attributes. The lookup for `X.age` reaches `__getattr__`, and `attrname` holds the string `'age'`. The method returns a computed value, so `age` behaves like a real attribute. For names it does not handle, the method raises `AttributeError`.

#### Attribute assignment and deletion

The `__setattr__` method intercepts all attribute assignments. Once it is defined, `self.attr = value` becomes a call to `self.__setattr__('attr', value)`. You can then validate or transform the value.

This method is tricky. Any assignment to a `self` attribute inside `__setattr__` calls `__setattr__` again. That causes infinite recursion and a stack overflow. The rule applies to every `self` assignment in the class, even in other methods.

To avoid the loop, assign through the instance dictionary. Writing to `self.__dict__` does not trigger the method.

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

If you write `self.age = value + 10` or `setattr(self, attr, value + 10)` inside the method, the call loops. Assigning any other `self` attribute recurs too. In this class, that recursion ends with the `AttributeError` instead of a loop.

A call to the superclass avoids the loop as well. Calling `object.__setattr__(self, attr, value + 10)` works. The `super().__setattr__(...)` form works too. Some classes need this approach, though it is uncommon.

The `__delattr__` method handles deletions, as in `del object.attr`. It also needs to avoid loops. It should delete through `__dict__` or route the call to a superclass.

Attributes created with slots or properties are not stored in the instance `__dict__`. For those virtual attributes, `__setattr__` may need the `object.__setattr__` form instead of `__dict__` indexing. Chapter 32 and Chapter 38 cover those tools.

#### Other attribute-management tools

The three methods above control attribute access in specialized ways. Python offers other tools as well.

- The `__getattribute__` method intercepts all attribute fetches, not only undefined ones. It must avoid loops too, usually by rerouting to `object`.
- The `property` built-in associates methods with fetch and set operations for one class attribute. It cannot catch all accesses, but it can define what some of them do.
- Descriptors use `__get__` and `__set__` methods for a specific attribute. They are as focused as `property`, and Python uses them to implement it.
- Slots declare attributes in a class and create implicit storage in each instance. Generic tools may need special handling for them.

Chapter 32 covers these tools in more detail, and Chapter 38 covers descriptors.

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

Display formats matter for objects. The default display of an instance is not useful. The following `adder` class has `__init__` and `__add__` but no display method.

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

Python calls `__repr__` automatically when an instance is printed or converted to a string. The method can turn `self.data` into a friendlier string.

#### Why two display methods?

Python has two display methods because they serve different audiences. `__str__` is tried first by `print` and by the `str` built-in. It should return a user-friendly display.

`__repr__` serves every other context. That includes interactive echoes, the `repr` function, and nested appearances. It is also the fallback for `print` and `str` when `__str__` is missing. It should return an as-code string that could re-create the object, or a detailed display for developers.

Coding `__repr__` alone gives one display for every context. Coding `__str__` alone gives a display only for `print` and `str`. The reverse is not true. Interactive echoes use `__repr__` and never try `__str__`.

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

Defining both methods gives a different display in each context. A class can show a friendly view with `__str__` and a developer view with `__repr__`.

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

The string-formatting tools in Chapter 7 also call these methods. The `!s` and `!r` conversions use `str` and `repr`, as does `%r` with the `%` operator.

```text
>>> f'{x!s} {x!r}', '{!s} {!r}'.format(x, x), '%s %r' % (x, x)
('[Value: 5] addboth(5)', '[Value: 5] addboth(5)', '[Value: 5] addboth(5)')
```

When you choose, use `__str__` for high-level displays and `__repr__` for low-level, all-inclusive ones. A general tool that codes `__str__` leaves clients room to add a `__repr__` later.

#### Display usage notes

Three points matter when you write display methods. First, both methods must return strings. Other result types are not converted, and they raise errors. Run the value through `str` or an f-string if needed.

Second, a container may ignore `__str__` for the objects it holds. The friendly display may apply only at the top level of a `print`. Objects nested inside a list still show their `__repr__` or the default.

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

Binary operator methods such as `__add__` and `__sub__` have variants. Each binary operator can have a left, right, and in-place version. Python applies defaults if you skip some of them. The roles your objects play decide how many you need.

#### Right-side addition

The `__add__` method does not handle an instance on the right side of `+`. This class shows the problem.

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

The `__radd__` method supports that case. Python calls it only when your instance is on the right side, and the left operand is not an instance of your class. In all other cases, the left operand's `__add__` runs.

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

In `__radd__`, `self` sits on the right side of the `+`, and `other` sits on the left. When two instances are added, `__add__` runs first. It then triggers `__radd__` by simplifying its left operand and adding again.

Sometimes one method can serve both sides. For a truly commutative operation, `__radd__` can call `__add__` directly. It can also swap the order and add again. The third option is an alias at class level, as in `__radd__ = __add__`. That last form saves one extra call, so it may run faster. In every case, the right-side instance triggers the shared `__add__` method.

#### Propagating the class type

Results may need to keep the class type. Without a type test, adding two instances can nest one object inside another. The `isinstance` test in the following class prevents that.

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

Without the `isinstance` test, the results nest objects. The math stays correct, but the code makes pointless recursive calls and extra constructor calls.

```text
>>> z = x + y                  # With isinstance test commented out
>>> z
Commuter5(Commuter5(187))
>>> z + z
Commuter5(Commuter5(Commuter5(Commuter5(374))))
```

Another option is to test and simplify in the constructor. The following class does that, and it behaves the same as `Commuter5`.

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

Classes are first-class objects, so you can place them in a tuple and loop over them. Aliasing `__radd__` to `__add__` in `Commuter5` or `Commuter6` saves a line. It does not prevent nesting without the `isinstance` tests. Python's manuals describe other options. For example, a class can return `NotImplemented` for an unsupported operand. That differs from the `NotImplementedError` exception.

#### In-place addition

To support `+=`, code either `__iadd__` or `__add__`. Python uses `__add__` when `__iadd__` is absent, and it assigns the result to the name. So the `Commuter` classes already support `+=`.

The `__iadd__` method allows a faster in-place change where it applies. Its return value is assigned to the target on the left of `+=`. Usually it returns `self`. Otherwise `None` is returned and assigned.

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

For mutable objects, `__iadd__` can make a quicker in-place change.

```text
>>> y = Number([1])
>>> y += [2]                   # In-place change faster than +
>>> y += [3]
>>> y.val
[1, 2, 3]
```

Without `__iadd__`, the normal `__add__` runs as a fallback. It may not optimize in-place cases.

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

The `__call__` method runs when your instance is called like a function. Python passes along any positional or keyword arguments. That lets an instance follow a function-based API.

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

The `__call__` method accepts every argument-passing mode from Chapter 18. The instance is passed as `self`, and the rest of the arguments follow the usual rules. These definitions all match the same calls:

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

The following class remembers the color a button should use when pressed.

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

Other techniques also keep state. These include closures with `nonlocal`, default arguments in a `lambda`, and bound methods.

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

When the button is pressed, the GUI behaves as if it ran the bound method. The method processes the state of its own instance.

```python
cb1 = Callback('blue')
cmd = cb1.changeColor                      # Registered event handler
cmd()                                      # On event: prints 'turn blue'
```

A `lambda` is needed only when you must pass extra arguments. A bound method reference already defers the call. This approach does not need `__call__`, and either scheme may suit a given program.

Chapter 32 uses `__call__` to build a function decorator, a callable object that adds logic around a function. Because `__call__` attaches state to a callable object, it fits that job well. Chapters 39 and 40 show more `__call__` examples.

### Comparisons: `__lt__`, `__gt__`, and others

Classes can catch all six comparison operators: `<`, `>`, `<=`, `>=`, `==`, and `!=`. Keep three qualifications in mind.

Comparison methods have no right-side variants. When only one operand supports comparison, Python uses a reflected method. For example, `__lt__` and `__gt__` reflect each other.

The comparison operators do not imply one another. A true `==` does not make `!=` false. So define both `__eq__` and `__ne__` when both operators must behave correctly.

The following class prints a trace for each comparison, so you can see which method runs.

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

The `__lt__` method also drives sorting. Both the list `sort` method and the `sorted` built-in use it.

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

Python's manuals cover the rest of this area. The `__eq__` method for equality is paired with `__hash__` for keys and sets. Comparison methods can also return `NotImplemented` for unsupported arguments. That is a different object from `NotImplementedError`.

### Boolean tests: `__bool__` and `__len__`

Every object is true or false in Boolean contexts. Your class decides what that means for its instances. Python first tries `__bool__` to get a direct True or False value. If that method is missing, Python tries `__len__`. A length of zero means false, and any other length means true.

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

Without `__bool__`, Python falls back on the length. A zero length means false, just as it does for built-in objects.

```text
>>> class Truth:
...     def __len__(self): return 0          # Empty means false too
>>> X = Truth()
>>> if not X: print('no!')
no!
```

If both methods exist, Python prefers `__bool__` because it is more specific.

```text
>>> class Truth:
...     def __bool__(self): return True      # Preferred over length
...     def __len__(self): return 0          # Object length: fallback
>>> if Truth(): print('yes!')
yes!
```

If neither method exists, the object is considered true.

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

Here, assigning a string to `pat` removes the last reference to the instance. That triggers the destructor. Destructors can handle cleanup, such as closing a server connection. Still, Python programmers use them less often than programmers in some other languages do.

#### Destructor usage notes

The destructor works as documented, but it has caveats that make it rare in Python code.

Destructors are less necessary in Python than in some other languages. Python reclaims the memory an instance holds, so you do not need a destructor for space management. CPython also closes file objects when they are reclaimed. Chapter 9 explains that closing files yourself is still a good habit, because this behavior can vary between Python implementations.

You also cannot always predict when an instance will be reclaimed. System tables may hold lingering references that stop the destructor from running on time. Python also does not guarantee that destructors run for objects still alive when the interpreter exits.

An exception raised inside `__del__` does not reach your program. Python prints a warning to `sys.stderr` instead. The garbage collector runs the method in an unpredictable context, so there is no clear place to deliver the error.

Cyclic references are another problem. Objects that refer to each other may not be collected when you expect. An optional cycle detector is enabled by default, and it collects such objects eventually. That includes objects with `__del__` methods, as of Python 3.4. The `gc` module and Python's manuals cover the details.

For these reasons, put cleanup in an explicitly called method, such as `shutdown`. The `try`/`finally` statement and the `with` statement also support cleanup. Chapter 34 covers the `with` statement and its context managers.

### Operator overloading summary

Most of the other overloading methods work like the ones above. Each one is a hook that intercepts a built-in operation. Some have unusual argument lists or return values, but the usage pattern is the same.

Later chapters use several more of these methods. Chapter 34 uses `__enter__` and `__exit__` in `with` statement context managers. Chapter 38 uses the `__get__` and `__set__` descriptor methods. Chapter 40 uses `__new__` in the context of metaclasses. Methods such as `__call__` and `__str__` appear in later examples as well.

Provide operator overloading when a class naturally matches a built-in type's interface, or needs to emulate one. A collection might imitate a sequence or a mapping. A callable object might serve an API that expects a function. Avoid overloading expression operators that do not map naturally to your objects. A normally named method is clearer in those cases.

## Checkpoint questions

1. When you fetch a `Manager` object from a shelf and print it, where does the display logic come from?

   Answer: `Manager` inherits `__repr__` from `AttrDisplay` in the separate `classtools` module, two levels up the class tree. `Manager` has no `__repr__` of its own, and `Person` does not define one either, so the search climbs until it finds `AttrDisplay`. The class names in parentheses in a `class` header provide the links to higher superclasses.

2. If a script loads a stored `Person` and never imports the module, how can it still call `giveRaise`?

   Answer: When Python pickles an instance, it records the attributes, the class name, and the module that holds the class. On loading, Python reimports the class internally and creates a new instance with the saved attributes. The loaded object therefore gets all its original methods, such as `lastName`, `giveRaise`, and `__repr__`, even if its class was never imported in the loading script.

3. Why is it important to move processing into methods instead of hardcoding it outside the class?

   Answer: Methods keep one copy of each operation, so changes are made in one place. Methods also work on any instance. This is encapsulation, the wrapping of logic behind an interface for future maintenance. Hardcoded logic creates redundancy that multiplies work as the code evolves.

4. Why is it better to customize by subclassing than by copying the original and modifying the copy?

   Answer: Subclassing reduces development effort. You code by customizing what already exists. Copying doubles future work, because changes to the original must be copied by hand. Subclassing lets you extend earlier work without starting over or creating redundant copies.

5. Why is it better to call back to a superclass method for default actions than to copy and modify its code in a subclass?

   Answer: Copying the code creates redundancy, which multiplies maintenance as the code changes. Calling the original through the superclass name, or with the `super` built-in, keeps one copy. The same reasoning applies to superclass constructors.

6. Why is it better to use generic tools such as `__dict__` than to write custom code for each class?

   Answer: Generic tools avoid hardcoded solutions that must be kept in sync as the class evolves. A generic `__repr__` need not change when a new attribute is added in `__init__`. A generic method inherited by all classes is changed in one place, and every class that inherits it picks up the change.

7. In general terms, when might you choose object embedding and composition instead of inheritance?

   Answer: Inheritance suits direct customization, where a subclass is a specialized version of its parent. Composition suits cases where several objects combine into a whole and a controller class directs them. Inheritance passes calls up to reuse code, and composition passes calls down to delegate them. The two can be combined, and the embedded objects are often customized through inheritance.

8. Suppose names were stored in a dictionary and jobs in a list, as in earlier chapters. What would need to change?

   Answer: Not much, since this was a first-cut prototype. The `lastName` method would need to change for the new name format. The `Person` constructor would need to change the job default to an empty list. The `Manager` class would probably pass a job list to its constructor instead of a single string. Those changes stay in one place, because the details are encapsulated in the classes. The database scripts would work as they are, apart from the object-construction calls, because shelves support nested data.

9. What changes would turn these classes into a personal contacts database?

   Answer: The classes can serve as template code for many kinds of database. Change the constructors to record different attributes, such as `name`, `address`, `birthday`, `phone`, and `email`. Then add methods that suit the application. A method such as `sendmail` could use the standard-library `smtplib` module to email a contact. The `AttrDisplay` tool works unchanged, and most of the `shelve` code can store your objects with minor changes.

10. What is an abstract superclass?

   Answer: An abstract superclass calls a method but does not define it. It expects a subclass to fill in that method. This lets a general class describe behavior before a specific subclass exists. Frameworks use the same pattern to hand off work to operations that client classes define.

11. What happens when a simple assignment appears at the top level of a `class` statement?

   Answer: It creates a data attribute on the class, written `Class.X`. Every instance that does not have its own attribute of that name shares it. Methods are usually created with nested `def` statements instead.

12. Why might a subclass need to call the superclass `__init__` manually?

   Answer: When a subclass defines its own constructor, Python runs only the lowest `__init__` in the tree. If the superclass setup code must also run, the subclass calls it, usually as `Superclass.__init__(self, …)`. The `super().__init__(…)` form also works, but this chapter uses the explicit form.

13. How can you augment an inherited method instead of replacing it?

   Answer: Redefine the method in the subclass, then call the superclass version from inside it. Pass `self` by hand, as in `Superclass.method(self, …)`. The `super().method(…)` form does the same job implicitly.

14. How does a class's local scope differ from a function's local scope?

   Answer: A class body is a local scope while it runs, and it can see enclosing function scopes. Code nested inside the class cannot see the class's names as plain variables. Methods reach them through `self` or the class name. After the `class` statement finishes, the local scope becomes an attribute namespace.

15. Which two methods can support iteration in a class, and which one does Python try first?

   Answer: A class can define or inherit `__iter__` or `__getitem__`. Python tries `__iter__` first. That method returns an iterator with a `__next__` method. If no `__iter__` is found, Python falls back on `__getitem__`, calling it with successively higher indexes. A `yield` statement can create `__next__` automatically.

16. Which two methods handle printing, and in what contexts?

   Answer: `__str__` is called by `print` and the `str` built-in. `__repr__` is called by `print` and `str` only when no `__str__` exists. It is also used by the `repr` built-in, by interactive echoes, and for nested appearances. `__str__` is usually the user-friendly display, and `__repr__` gives extra detail or the as-code form.

17. How can you intercept slice operations in a class?

   Answer: Slices are caught by the `__getitem__` method. Python calls it with a slice object instead of a plain integer. The method can pass the slice object along or inspect its `start`, `stop`, and `step` attributes.

18. How can you catch in-place addition in a class?

   Answer: Define `__iadd__` for `+=`. If it is missing, Python uses `__add__` and assigns the result to the name. The `__radd__` method handles addition with the instance on the right side.

19. When should you provide operator overloading?

   Answer: Provide it when a class naturally matches, or needs to emulate, a built-in type's interface. Do not overload expression operators that do not map naturally to your objects. A normally named method is clearer in that case.

## Sources and review notes

- Source: *Learning Python*, 6th edition (`learning-python-6th-edition`). Chapters used are listed in each section.
- Chapter 28, "A More Realistic Example," from *Learning Python*, 6th edition (`learning-python-6th-edition`).
- Chapter 29, "Class Coding Details," from *Learning Python*, 6th edition (`learning-python-6th-edition`).
- Chapter 30, "Operator Overloading," from *Learning Python*, 6th edition (`learning-python-6th-edition`).
