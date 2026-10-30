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

```python
class Person: # Start a class
```

We will change this file as we go. To track the versions, each example number appears in the caption, and the same number appears in the file name. The file stays the same across steps, but the book shows each revision separately.

A module can hold any number of functions and classes. The name `person.py` may stop making sense if we add unrelated code later. For now we will assume everything in it relates to `Person`. Modules work best with a single, cohesive purpose.

#### Coding constructors

The first real job for `Person` is to record basic facts about each person. In Python these facts are instance attributes. They are usually created by assigning values to `self` inside methods.

The normal way to give an instance its first values is the `__init__` constructor method. Python runs `__init__` automatically each time an instance is created.

**Example 28-2.** `person_2.py` (add attribute initialization)

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

**Example 28-3.** `person_3.py` (add constructor defaults)

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

**Example 28-4.** `person_4.py` (add incremental self-test code)

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

This simple code already shows something important. Bob's name is not Sue's, and Sue's pay is not Bob's. Each instance is an independent record with its own copy of the state. Classes therefore work like a factory for objects, much as built-in types such as lists and dictionaries do. Functions and modules have no such idea. Closures keep per-call state, but they lack the methods, inheritance, and structure that classes provide.

#### Using code two ways

The test code has a catch. Its top-level `print` statements run both when the file is run as a script and when it is imported. If another program imports `Person`, it will see our test output. Client programs do not want that output mixed into their own.

We could move the tests to a separate file. It is often more convenient to keep them with the code they test. The fix is the `__name__` check. Test statements should run only when the file is run directly, not when it is imported. This check was covered in the modules chapter.

**Example 28-5.** `person_5.py` (support both imports and run/tests)

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

**Example 28-6.** `person_6.py` (process embedded built-in objects)

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

**Example 28-7.** `person_7.py` (add methods to encapsulate operations)

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

**Example 28-8.** `person_8.py` (add __repr__ overload method for displays)

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

```python
class Manager(Person): # Define a subclass of Person
```

The new class `Manager` inherits from `Person` and may add customizations. A manager is almost a person, although the book admits that is a long journey for a small joke. A `Manager` gets raises in a special way.

Assume a manager gets the passed-in percentage plus an extra bonus. The bonus defaults to 10%. A manager who is given a 10% raise therefore receives 20%. Any link to real people is coincidental.

The subclass's new `giveRaise` sits lower in the class tree than the `Person` version. Python's search rule picks the lowest version of a name, so the new method replaces the original for managers.

```python
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

A method always needs a subject instance. Python supplies it only for calls made through an instance. For calls through the class name, you supply the instance yourself. Inside a method such as `giveRaise`, `self` is already the subject, so you pass `self` along.

Calling through the class skips the usual lookup and runs a specific version higher in the tree. That lets us run the default `giveRaise` in `Person`, even though `Manager` redefines it. We must call through `Person` here. A call to `self.giveRaise()` inside the `Manager` method would find `Manager`'s version again and recurse until memory ran out.

The good version may look like a small difference, but the effect on maintenance is large. The raise logic lives in one place, `Person`'s method. Future changes need one edit. The form also states our intent: perform the standard raise, then add a bonus. Example 28-9 shows the full module with this step applied.

**Example 28-9.** `person_9.py` (add method customization in a subclass)

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

**Example 28-10.** `person_10.py` (add constructor customization in a subclass)

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

**Example 28-11.** `person-composite.py` (embedding-based Manager alternative)

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

**Example 28-12.** `person-department.py` (aggregate embedded objects into a composite)

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

This code uses both inheritance and composition. `Department` is a composite that embeds and controls other objects. The `Person` and `Manager` objects themselves use inheritance to customize behavior. A GUI works the same way. It may use inheritance to customize labels and buttons, and composition to build forms, calculators, and editors from those widgets. The right structure depends on what you are modeling. Modeling real-world things this way is one of OOP's strengths.

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

We can put these interfaces to work in a superclass. This superclass shows the correct class name and formats every attribute of an instance of any class. The code goes in a new, independent module named `classtools.py`. Example 28-13 shows it.

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

`pickle`
: Serializes arbitrary Python objects to and from a string of bytes.

`dbm`
: Implements an access-by-key file system for storing strings.

`shelve`
: Uses the other two modules to store Python objects in a file by key.

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

**Example 28-15.** `makedb.py` (store Person objects in a shelve database)

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

One more script shows that the objects persist. Each run prints the database and gives a raise to one stored object. Example 28-16 does this. Tracing it shows how much comes for free. Printing uses the general `__repr__`, and the raise uses the `giveRaise` method we wrote earlier. This works for OOP objects even when they live in a file.

**Example 28-16.** `updatedb.py` (modify Person object in a shelve database)

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

## Checkpoint questions

1. When you fetch a `Manager` object from a shelf and print it, where does the display logic come from?

   Answer: `Manager` inherits `__repr__` from `AttrDisplay` in the separate `classtools` module, two levels up the class tree. `Manager` has no `__repr__` of its own, and `Person` does not define one either, so the search climbs until it finds `AttrDisplay`. The class names in parentheses in a `class` header provide the links to higher superclasses.

2. When you fetch a `Person` object from a shelf without importing its module, how does the object know it has a `giveRaise` method?

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

8. What would you have to change if the objects in this chapter used a dictionary for names and a list for jobs, as in earlier examples?

   Answer: Not much, since this was a first-cut prototype. The `lastName` method would need to change for the new name format. The `Person` constructor would need to change the job default to an empty list. The `Manager` class would probably pass a job list to its constructor instead of a single string. Those changes stay in one place, because the details are encapsulated in the classes. The database scripts would work as they are, apart from the object-construction calls, because shelves support nested data.

9. How might you modify the classes in this chapter to implement a personal contacts database in Python?

   Answer: The classes can serve as template code for many kinds of database. Change the constructors to record different attributes, such as `name`, `address`, `birthday`, `phone`, and `email`. Then add methods that suit the application. A method such as `sendmail` could use the standard-library `smtplib` module to email a contact. The `AttrDisplay` tool works unchanged, and most of the `shelve` code can store your objects with minor changes.

## Sources and review notes

- Source: *Learning Python*, 6th edition (`learning-python-6th-edition`). Chapters used are listed in each section.
- Chapter 28, "A More Realistic Example," from *Learning Python*, 6th edition (`learning-python-6th-edition`).
