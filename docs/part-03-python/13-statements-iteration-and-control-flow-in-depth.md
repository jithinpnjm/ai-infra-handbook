---
id: "c03-13"
title: "3.13 Statements, iteration and control flow in depth"
sidebar_label: "3.13 Statements, iteration and control flow in depth"
sidebar_position: 13
description: "Assignments, expressions, if and match selections, while and for loops, and the iteration protocol, with the syntax habits that keep scripts readable."
status: "drafted"
tier: "2"
level: "I"
lab_venue: "Mac"
---

# 3.13 Statements, iteration and control flow in depth

This chapter goes deeper into material that chapter 3.1 only introduces. You will meet it again whenever you read or write the Python behind schedulers, operators, exporters and training launchers.

## Assignments

Assignment is how Python attaches a name, or a slot inside a data structure, to an object. The target on the left of the equals sign can be a name or an object component. The right side can be any expression that creates an object. Most assignments are simple, but a few properties are worth knowing from the start.

Assignments create object references. An assignment stores a reference to an object in a name or a component. It never copies the object. That makes Python variables behave more like pointers than like boxes that hold data.

Names are created when first assigned. You do not declare a name ahead of time. Some data structure slots appear on first assignment too, such as dictionary entries and some object attributes. After that, a name is replaced by its value wherever it appears in an expression.

Names must be assigned before they are referenced. Using a name that has no value raises an exception. Python does not hand back an ambiguous default in its place. This matters because names are never declared, so a silent default would hide typos in your code.

Some operations assign implicitly. Module imports, function and class definitions, `for` loop variables, and function arguments all bind names at runtime. Assignment works the same way in each of these places, so you can read every one of them as a binding.

### Assignment syntax forms

Assignment has several syntax forms. The basic form is by far the most common, and you could finish most work with it alone. The other forms are optional, but many programmers find them convenient in practice.

| Operation | Interpretation |
|---|---|
| `target = 'Hack'` | Basic assignment |
| `code, hack = 'py', 'PY'` | Tuple assignment |
| `[code, hack] = ['py', 'PY']` | List assignment |
| `a, b, c, d = 'hack'` | Sequence assignment |
| `a, *b = 'hack'` | Extended-unpacking assignment |
| `code = hack = 'python'` | Multiple-target assignment |
| `code += 1, hack *= 2` | Augmented assignments |
| `(python := 3.12) + 0.01` | Named assignment expression |

The sections that follow take each form in turn. The first four rows are statements, and the last is an expression.

### Basic assignments

A basic assignment binds one target to one value. The target may be a name, an index, a slice, or an attribute. The value can be any expression. Here is a short session at the REPL prompt:

```
$ python3
>>> L = [1, 2] # Name target
>>> L[0] = 3 # Index target
>>> L[-1:] = [4, 5] # Slice target
>>> L
[3, 4, 5]
```

Attribute targets show up with classes, which come later. The assignment looks the same, though:

```
object.attr = L # Attribute target (see Part VI)
```

Any of these four kinds of target can appear in any assignment form, unless a form says otherwise. Named assignment expressions are one exception, because they accept only a name.

A basic assignment can also carry an annotation. You write a colon right after the target, and the annotation is used for type hinting. This form allows only a single target. This handbook skips it, because Python itself does not rely on it and it sits at odds with the language's usual style. Consult Python's documentation if you meet it in the wild.

### Sequence assignments

Tuple and list assignments unpack items into separate variables. Python pairs the values on the right with the targets on the left, by position. It assigns them one at a time, from left to right.

```
>>> first = 1 # Basic assignment
>>> second = 2
>>> A, B = first, second # Tuple assignment
>>> A, B # Similar to A = first; B = second
(1, 2)
>>> [C, D] = [first, second] # List assignment
>>> C, D
(1, 2)
```

The third line really holds two tuples, with their parentheses left out. The same holds when the equals sign has lists on each side.

Tuple assignment gives a common trick for swapping two variables without a temporary variable of your own. Python builds a temporary tuple that keeps the original values while the statement runs. The tuple on the right remembers the prior values automatically.

```
>>> first = 1
>>> second = 2
>>> first, second = second, first # Tuples: swaps values
>>> first, second # Like T = first; first = second; second = T
(2, 1)
```

The original tuple and list forms now accept any sequence on the right, as long as the lengths match. You can assign a tuple of values to a list of names, or a string of characters to a tuple of names. Python still assigns by position, from left to right.

```
>>> [a, b, c] = (1, 2, 3) # Assign tuple of values to list of names
>>> a, c
(1, 3)
>>> (a, b, c) = 'ABC' # Assign string of characters to tuple names
>>> a, c
('A', 'C')
```

The left side of a sequence assignment is still a sequence of targets. The right side may be any iterable, which is a broader group. Iterables include physical collections such as lists and virtual ones such as the lines of a file. For now, read the "sequence" in an assignment as the left side of the equals sign.

### Advanced sequence-assignment patterns

Although you can mix sequence types around the equals sign, the counts usually have to match. If the right side has more or fewer items than the left has targets, Python raises an error. Extended unpacking relaxes this rule, as the next section shows.

```
>>> string = 'TEXT'
>>> a, b, c, d = string # Same number on both sides
>>> a, b, c, d
('T', 'E', 'X', 'T')
>>> a, b, c = string # Error if not
ValueError: too many values to unpack (expected 3)
```

To be more flexible, you can slice. There are several ways to use slicing so that the last case works.

```
>>> a, b, c = string[0], string[1], string[2:] # Index and slice
>>> a, b, c # a, b, c = ('T', 'E', 'XT')
('T', 'E', 'XT')
>>> a, b, c = list(string[:2]) + [string[2:]] # Slice and concatenate
>>> a, b, c # a, b, c = ['T', 'E', 'XT']
('T', 'E', 'XT')
>>> a, b = string[:2] # Slice and unpack directly
>>> c = string[2:] # a, b = 'TE'; c = 'XT'
>>> a, b, c
('T', 'E', 'XT')
>>> (a, b), c = string[:2], string[2:] # Nested sequences
>>> a, b, c # (a, b), c = 'TE', 'XT'
('T', 'E', 'XT')
```

Sequences can also nest. Python unpacks their parts according to their shape. In the last example, the right side is a tuple of two items, and its first item is a nested string. It is the same as writing the nesting out in full.

```
>>> ((a, b), c) = ('TE', 'XT') # Paired by shape and position
>>> a, b, c
('T', 'E', 'XT')
```

Python pairs the first string with the first tuple on the left, and assigns it one character at a time. It assigns the second string to `c` all at once. The shape of the left side must match the shape of the right side. Nested assignment like this is rare, but it can pick out parts of data with a known shape.

The same technique works in `for` loops, because loop items are assigned to the loop header's target as if an `=` statement had run.

```
for (a, b, c) in [(1, 2, 3), (4, 5, 6)]: … # Simple tuple assignment
for ((a, b), c) in [((1, 2), 3), ((4, 5), 6)]: … # Nested tuple assignment
```

Nested sequence assignments can also be done with the `match` statement, which the next chapter covers. Sequence unpacking gives one more common idiom, which assigns a series of integers to a set of names.

```
>>> red, green, blue = range(3)
>>> red, blue
(0, 2)
```

This code sets the three names to `0`, `1`, and `2`, in that order. Each name gets a unique value. It is Python's simplest equivalent to the enumerated types found in other languages. The `range` built-in returns an iterable that generates successive integers. Wrap it in `list` to display all of its values at once.

```
>>> list(range(3)) # list() required for display
[0, 1, 2]
```

Tuple assignment also splits a sequence into its front and the rest. A `while` loop is a common place to see it.

```
>>> L = [1, 2, 3, 4]
>>> while L: # Repeat until L becomes empty (false)
... front, L = L[0], L[1:] # See next section for * alternative
... print(front, L)
...
1 [2, 3, 4]
2 [3, 4]
3 [4]
4 []
```

The tuple assignment in that loop could be written as two separate lines. It is often more convenient to string them together.

```
... front = L[0]
... L = L[1:]
```

This code treats the list like a stack. The `append` and `pop` methods of a list can do much the same job. Here, `front = L.pop(0)` gives nearly the same result as the tuple assignment, but it changes the list in place. The chapter on `while` and `for` loops covers other, often better, ways to step through a sequence.

### Extended-unpacking assignments

The previous section showed how to use manual slicing to make sequence assignment more general. Later versions of Python made this easier. A starred target, written `*X`, can appear on the left of the equals sign. It matches the iterable on the right more generally. The starred name is assigned a list of every item that no other target took.

This is especially handy for splitting a sequence into its front and its rest, as in the loop above.

### Extended unpacking in action

Start with an example. Ordinary sequence assignment needs exactly as many targets on the left as there are items on the right. The lengths must agree, unless you slice on the right by hand.

```
>>> seq = [1, 2, 3, 4]
>>> a, b, c, d = seq
>>> a, d
(1, 4)
>>> a, b = seq
ValueError: too many values to unpack (expected 2)
```

A single starred target lets the same example match more generally. In the next session, `a` matches the first item, and `b` matches the rest.

```
>>> a, *b = seq
>>> a
1
>>> b
[2, 3, 4]
```

When a starred target is present, the number of targets need not match the length of the iterable. The starred target can also appear first. Here, `b` matches the last item, and `a` matches everything before it.

```
>>> *a, b = seq
>>> a
[1, 2, 3]
>>> b
4
```

A starred target in the middle collects everything between the other targets. In the next session, `a` and `c` get the first and last items, and `b` gets everything in between.

```
>>> a, *b, c = seq
>>> a
1
>>> b
[2, 3]
>>> c
4
```

Wherever the starred target appears, it collects every unassigned item at that position.

```
>>> a, b, *c = seq
>>> a
1
>>> b
2
>>> c
[3, 4]
```

Extended unpacking works for any iterable, not only lists. The next examples unpack a string and a `range`, which generates the values from zero through three on demand.

```
>>> a, *b = 'hack'
>>> a, b
('h', ['a', 'c', 'k'])
>>> a, *b, c = 'hack'
>>> a, b, c
('h', ['a', 'c'], 'k')
>>> a, *b, c = range(4)
>>> a, b, c
(0, [1, 2], 3)
```

This is similar in spirit to slicing, but the two are not the same. An unpacking assignment always returns a list for the starred items. Slicing returns a sequence of the same type as the object sliced.

```
>>> S = 'hack'
>>> a, b, c = S[0], S[1:-1], S[-1] # Slices are type specific
>>> a, b, c
('h', 'ac', 'k')
>>> a, *b, c = S # But * always returns a list
>>> a, b, c
('h', ['a', 'c'], 'k')
```

The loop from the last section gets simpler with this form. You no longer need to slice by hand to get the first item and the rest. The rest always becomes a list after the starred name.

```
>>> L = [1, 2, 3, 4]
>>> while L:
... front, *L = L # Get first, rest without slicing
... print(front, L)
...
1 [2, 3, 4]
2 [3, 4]
3 [4]
4 []
```

### Boundary cases of extended unpacking

Some edge cases are worth knowing. First, a starred target that matches a single item is still assigned a list.

```
>>> seq = [1, 2, 3, 4]
>>> a, b, c, *d = seq
>>> print(a, b, c, d)
1 2 3 [4]
```

Second, if nothing is left for the starred target, it gets an empty list. This holds wherever the starred target sits. In the next example, the names `a` through `d` take every item. Python gives `e` an empty list instead of raising an error.

```
>>> a, b, c, d, *e = seq
>>> print(a, b, c, d, e)
1 2 3 4 []
>>> a, b, *e, c, d = seq
>>> print(a, b, c, d, e)
1 2 3 4 []
```

Some errors still occur. They happen when there is more than one starred target, when there are too few values and no star, and when the starred target is not inside a sequence.

```
>>> a, *b, c, *d = seq
SyntaxError: multiple starred expressions in assignment
>>> a, b = seq
ValueError: too many values to unpack (expected 2)
>>> *a = seq
SyntaxError: starred assignment target must be in a list or tuple
>>> *a, = seq # A one-item tuple sans parentheses
>>> a # Same as a = seq, but makes a new copy!
[1, 2, 3, 4]
```

The rule against more than one starred target applies to each sequence when both sides are nested. You still cannot use more than one starred target in any one nested sequence.

```
>>> [(a, *b), (c, *d)] = [(1, 2, 3, 4), (5, 6, 7, 8)]
>>> a, b, c, d
(1, [2, 3, 4], 5, [6, 7, 8])
>>> [(a, *b, *x), (c, *d)] = [(1, 2, 3, 4), (5, 6, 7, 8)]
SyntaxError: multiple starred expressions in assignment
```

Any assignment target can be starred, even if you rarely see it in real code. That includes names, indexes, slices, and attributes.

```
>>> a, *L = [1, 2, 3] # Name target
>>> a, L
(1, [2, 3])
>>> a, *L[0] = [4, 5, 6] # Index target
>>> a, L
(4, [[5, 6], 3])
>>> a, *L[1:] = [7, 8, 9] # Slice target
>>> a, L
(7, [[5, 6], 8, 9])
>>> class C: …code… # See Part VI
>>> a, *C.attr = 'yikes' # Attribute target
>>> a, C.attr
('y', ['i', 'k', 'e', 's'])
```

### Extended unpacking as a convenience

Extended unpacking is only a convenience. You can usually get the same effect with explicit indexing and slicing. It is simply easier to write. The common "first, rest" split can be coded either way, but slicing takes extra work.

```
>>> seq
[1, 2, 3, 4]
>>> a, *b = seq # First, rest
>>> a, b
(1, [2, 3, 4])
>>> a, b = seq[0], seq[1:] # First, rest sans *
>>> a, b
(1, [2, 3, 4])
```

The "rest, last" split works the same way. Extended unpacking needs noticeably fewer keystrokes for it.

```
>>> *a, b = seq # Rest, last
>>> a, b
([1, 2, 3], 4)
>>> a, b = seq[:-1], seq[-1] # Rest, last sans *
>>> a, b
([1, 2, 3], 4)
```

Because it is both simpler and more natural, extended-unpacking syntax is common in Python code.

### Extended unpacking in for loops

The loop variable in a `for` statement can be any assignment target. That means extended unpacking works there too. A simple name is more common after `for`, but a starred target is allowed.

```
for (a, *b, c) in [(1, 2, 3, 4), (5, 6, 7, 8)]: …
```

Each time the loop runs, Python hands the next tuple of values to the tuple of targets. On the first pass, that matches this assignment.

```
a, *b, c = (1, 2, 3, 4) # b gets [2, 3]
```

The names `a`, `b`, and `c` can then be used in the loop body. This is really no special case. It is ordinary assignment at work. You can also do simpler tuple assignment in a loop, as shown here.

```
for (a, b, c) in [(1, 2, 3), (4, 5, 6)]: … # a, b, c = (1, 2, 3), …
```

You can also copy the behavior of extended unpacking by slicing by hand.

```
for all in [(1, 2, 3, 4), (5, 6, 7, 8)]: …
a, b, c = all[0], all[1:-1], all[-1]
```

Loop syntax is covered in more detail in the `for` loop section, so the topic returns there.

### The many stars of Python

The `*` symbol has appeared in many special roles over the years. Before Python 3.5, starred items could appear in these places:

- Assignments, where one starred target of any kind collects unmatched items into a new list. It can repeat in nested parts.
- Function headers, where `*X` and `**X` collect unmatched positional and keyword arguments into a tuple and a dictionary.
- Function calls, where `*X` and `**X` unpack iterables and mappings into individual positional and keyword arguments.

As of Python 3.5, function calls accept any number of `*X` and `**X` unpacking expressions. Starred expressions can also appear in object literals. They unpack collections of the type that the literal implies.

```
[x, *iter] # List: unpack items in iterables
(x, *iter, y) # Tuple: ditto, parentheses or not
{*iter, x} # Set: ditto, though values are unordered and unique
{x: y, **map} # Dict: unpack keys/values in mappings, rightmost dup wins
```

As of Python 3.10, both `*X` and `**X` can appear in the patterns of the `match` statement. They play roles similar to sequence assignment. Only `*X` overlaps between the two, and in `match` its assignment is really a side effect of a true-or-false test.

As of Python 3.11, `except*` can appear in `try` statements. It lets several handlers run to process multiple exceptions wrapped in an exception group. This adds another layer to `try`, which the book saves for later.

The use of stars has wandered over the years, and other parts of the language may take up stars in the future. Check the official reference for the current rules.

### Multiple-target assignments

A multiple-target assignment gives the same object to every target on the left. The object is the one farthest to the right. The next example assigns three names to one string.

```
>>> a = b = c = 'code'
>>> a, b, c
('code', 'code', 'code')
```

This form does the same work as three separate assignments. It is easier to write and shorter on the page.

```
>>> c = 'code'
>>> b = c
>>> a = b
```

There is one object here, and all three names share it. This is safe for immutable types. Suppose you set a group of counters to zero. Variables must be assigned before use, so you start the counters at zero before adding to them.

```
>>> a = b = 0
>>> b = b + 1
>>> a, b
(0, 1)
```

Changing `b` changes only `b`, because numbers do not support in-place changes. When the object is immutable, it does not matter that several names refer to it.

Empty mutable objects need more care. Lists and dictionaries can change in place, so a shared object is a real risk.

```
>>> a = b = []
>>> b.append(42)
>>> a, b
([42], [42])
```

Here, `a` and `b` refer to the same list. Appending through `b` also changes what `a` shows. This is the shared reference effect from the earlier chapter on objects. To avoid it, create each mutable object in its own statement, with its own literal.

```
>>> a = []
>>> b = [] # a and b do not share the same object
>>> b.append(42)
>>> a, b
([], [42])
```

A tuple assignment can do this in one line. Each list literal creates a separate object.

```
>>> a, b = [], [] # a and b do not share the same object
```

### Augmented assignments

Besides the basic, sequence, and multiple forms, Python has augmented assignments. The idea came from the C language. These forms combine a binary expression and an assignment in one shorter form. The next two lines are equivalent in result, although the second may change `X` in place.

```
X = X + Y # Basic form
X += Y # Augmented form
```

Augmented assignment works on any type that supports the binary expression. The next example shows two ways to add one to a name. Both change the name to refer to a new value.

```
>>> x = 1
>>> x = x + 1 # Basic
>>> x
2
>>> x += 1 # Augmented
>>> x
3
```

For a string, the augmented form performs concatenation, because that is what `+` means for strings. The second line below is equal to `S = S + 'HACK'`.

```
>>> S = 'hack'
>>> S += 'HACK' # Implied concatenation
>>> S
'hackHACK'
```

Python has an augmented form for most binary operators. Each operator takes a value on its left and right side. The forms are listed below. The matrix-multiplication form, `@=`, is unused and unimplemented by Python itself today.

```
X += Y
X -= Y
X *= Y
X /= Y
X @= Y
X //= Y
X %= Y
X **= Y
X >>= Y
X <<= Y
X &= Y
X |= Y
X ^= Y
```

Augmented assignments have three useful advantages. Each one matters for a different reason.

- There is less to type.
- The left side is evaluated only once. In `X += Y`, `X` may be a complicated expression, and it runs only once. In the long form, `X = X + Y`, the left side appears twice and runs twice. Because of this, augmented assignments usually run faster.
- The best technique is chosen automatically. For objects that support in-place changes, the augmented form performs an in-place operation rather than a slower copy.

The last point needs more explanation. For mutable objects, the augmented form may use an in-place operation as an optimization. Lists can grow in several ways. To add one item to the end of a list, you can concatenate or call `append`.

```
>>> L = [1, 2]
>>> L = L + [3] # Concatenate one: slower
>>> L
[1, 2, 3]
>>> L.append(4) # Faster, but in place
>>> L
[1, 2, 3, 4]
```

To add several items, you can concatenate again or call the list `extend` method.

```
>>> L = L + [5, 6] # Concatenate many: slower
>>> L
[1, 2, 3, 4, 5, 6]
>>> L.extend([7, 8]) # Faster, but in place
>>> L
[1, 2, 3, 4, 5, 6, 7, 8]
```

Concatenation is less prone to shared-reference side effects, but it usually runs slower than the in-place call. Concatenation must create a new object, copy the list on the left, and then copy the list on the right. An in-place call adds items at the end of an existing block of memory. Internally it is more complicated, but this picture is enough for now.

When you use augmented assignment to extend a list, you can mostly forget these details. Python calls the faster `extend` method, or its equivalent, instead of the slower concatenation that `+` implies.

```
>>> L += [9, 10] # Mapped to L.extend([9, 10])
>>> L
[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
```

Slice assignment, such as `L[len(L):] = [11,12,13]`, also works, but it does roughly the same job as `extend` or `+=`. The `extend` method and the `+=` form are simpler to read. Note also that for lists, `+=` is not always the same as `+` followed by `=`. The `+=` form accepts any sequence, just as `extend` does. Ordinary concatenation usually does not.

```
>>> L = []
>>> L += 'hack' # += and extend allow any sequence, but + does not!
>>> L
['h', 'a', 'c', 'k']
>>> L = L + 'code'
TypeError: can only concatenate list (not "str") to list
```

Index and slice targets can also change a mutable object in place when you use augmented assignment.

```
>>> L = [1, 2]
>>> L[0] += 10 # Change an item of a list, in place
>>> L
[11, 2]
>>> L[-1:] += [3, 4] # Change a section of a list, in place
>>> L
[11, 2, 3, 4]
```

### Augmented assignment and shared references

The in-place change in `+=` for lists is very different from the new object that `+` creates. As with any shared reference, the difference matters when several names point to one object.

```
>>> L = [1, 2]
>>> M = L # L and M reference the same object
>>> L = L + [3, 4] # Concatenation makes a new object
>>> L, M # Changes L but not M
([1, 2, 3, 4], [1, 2])
>>> L = [1, 2]
>>> M = L
>>> L += [3, 4] # But += really means extend, not +
>>> L, M # M sees the in-place change too!
([1, 2, 3, 4], [1, 2, 3, 4])
```

This matters only for mutable objects such as lists and dictionaries. It is an obscure case, until it affects your code. If you need to break a shared reference, make a copy of the mutable object.

C and C++ programmers should note one difference. Python now supports statements like `X += Y`. It still has no auto-increment or auto-decrement operators such as `X++` or `--X`. Those do not fit Python's object model, because Python has no in-place change for immutable objects such as numbers. Python also has no augmented named-expression form. A form like `:+= 1` would be close to `++`, but it does not exist.

### Named assignment expressions

For most of its history, Python avoided the assignment-as-expression idiom from C. The reason was that it is subtle, error-prone, and can make code hard to read. Python 3.8 added a limited version called named assignment. It does not turn the `=` statement into a nestable expression, as in C. Instead, it adds a new operator, `:=`.

The new operator has a different and limited syntax, which avoids many pitfalls of other languages. You still cannot type `=` by mistake where you meant `==`. The `:=` symbol also looks visually distinct.

The expression `name := value` does two things. It evaluates `value` first. Then it assigns the result to `name`, and returns that result as the value of the whole `:=` expression.

There is no reason to use this syntax for the assignment alone, because every `=` statement already assigns names. In fact, `:=` used as a statement without parentheses is a syntax error. Because `:=` returns the value it assigns, you can nest it where statements are not allowed. It can also test a value and then use the assigned name in the same place.

As an artificial example, the next line both assigns `2` to `b` and returns it for the string repetition assigned to `a`.

```
>>> a = 'hack' * (b := 2)
>>> a
'hackhack'
>>> b
2
```

Named assignment has deliberate limits. Only a simple name can appear on the left. Neither other assignment forms nor data structure components work there.

```
>>> (python := 3.12) + 0.01 # Just a name on the left
3.13
>>> python
3.12
>>> (python, Python := 3.12, 3.13) + 0.01
TypeError: can only concatenate tuple (not "float") to tuple
>>> (python[0] := 3.12) + 0.01
SyntaxError: cannot use assignment expressions with subscript
>>> (python.attr := 3.12) + 0.01
SyntaxError: cannot use assignment expressions with attribute
```

The first failure shows why. Python reads the line as a three-item tuple with `:=` in the middle. It does not read it as a two-target named sequence assignment. Named assignment also has no augmented forms. There is no `:+=`, for example. A statement such as `X += 1` is shorter than `(X := X + 1)`. A `:=+` form does exist, but it only applies the `+` identity operator to the expression on the right.

### When to use named assignment

The most common use of `:=` is inside `if` and `while` headers. Without it, a common pattern assigns a variable before the statement, tests it in the header, and uses it in the body. Reading lines from a file is a good example. You must detect the end of the file, which is an empty string that counts as false.

```
line = file.readline() # Sans the := expression
if line:
    print(line)
line = file.readline() # Ditto, in while loops
while line:
    print(line)
    line = file.readline()
```

To avoid the repeated call, you can write the loop another way. It uses `while True` and a `break` on an empty line.

```
while True: # Sans both := and redundancy
    line = file.readline()
    if not line: break
    print(line)
```

These forms still work well, and `:=` is never required. With `:=`, you can combine the fetch, the assignment, and the test into the statement header.

```
if line := file.readline(): # The := alternatives
    print(line)
while line := file.readline(): # Read all lines (vs: for line in file)
    print(line)
```

In both cases, `:=` returns the result of the `readline` call, so its truth value can be tested in the header. It also assigns that result to `line`, which the body can then use. The operator gives a short way to do several steps in one place.

When you use `:=`, enclosing parentheses are often needed. Comparing its result to an explicit value is one case. The parentheses are required there, although they are not needed in the plain statements.

```
if (line := file.readline()) != ignore: # Parentheses required
    print(line)
while (line := file.readline()) != stop: # And not a bad idea
    print(line)
```

As a rule of thumb, wrap `:=` in parentheses whenever you use it. The parentheses set the expression off visually. They also prevent surprises if the surrounding code changes meaning. Without them, `!=` would bind tighter than `:=`, so the names would receive the results of the tests. The rules for `:=` also favor parenthesized use.

The `:=` operator has other roles. It can reuse a result inside a literal, or capture the last result in a comprehension or another iteration tool. It can also appear inside f-strings, and it can be nested inside itself, with parentheses.

```
>>> [val := 'Py!', val * 2, val * 3] # Reusing a value
['Py!', 'Py!Py!', 'Py!Py!Py!']
>>> list(pow := 2 ** num for num in [2, 4, 8]) # Capturing a result
[4, 16, 256]
>>> pow
256
>>> f'Hello {(name := input('Who are you? '))}' # Nesting in f-strings (hmm)
Who are you? Pat
'Hello Pat'
>>> name
'Pat'
>>> (x := (y := (z := 1) + 1) + 1) # Nesting in itself (hmm * 2)
3
>>> x, y, z
(3, 2, 1)
```

A deeply nested `:=` may seem clever, but it is much harder to read than a plain assignment. Use it sparingly and wisely, as you would any nestable tool. A clear extra line or two is usually worth it.

## Variable name rules

Now that you have seen assignment statements and expressions, it helps to be precise about variable names. A name comes into existence when you assign a value to it. A few rules govern the names you pick for the parts of your programs.

### Legal names

A name must start with an underscore or a letter. It can then have any number of letters, digits, or underscores after that. The names `_hack`, `hack`, and `Hack_1` are legal. The names `1_hack`, `hack$`, and `@#!` are not.

Python also accepts non-ASCII Unicode characters in names. Those characters can make code hard to use in some settings, and the rules for them are intricate. The book covers the topic in a note later on, and Python's language manuals give the full details.

### Case matters

Python pays attention to case, in names you create and in reserved words. The names `X` and `x` are two different variables. Case also matters in the names of imported module files, even on platforms with case-insensitive filesystems, such as most Windows setups. That keeps imports working when a program moves between platforms.

### Reserved words are off-limits

Names you define cannot match words that have special meaning in the language. Python raises a syntax error if you use `class` as a variable name. The names `klass` and `Class` both work fine. The words below are reserved, so they cannot be used for your own names.

| Reserved words | | | | |
|---|---|---|---|---|
| `False` | `await` | `else` | `import` | `pass` |
| `None` | `break` | `except` | `in` | `raise` |
| `True` | `class` | `finally` | `is` | `return` |
| `and` | `continue` | `for` | `lambda` | `try` |
| `as` | `def` | `from` | `nonlocal` | `while` |
| `assert` | `del` | `global` | `not` | `with` |
| `async` | `elif` | `if` | `or` | `yield` |

Python's documentation now calls these "keywords." That name also describes pass-by-name function arguments, so this book uses "reserved words" to avoid confusion.

Four more words are soft reserved words: `match`, `case`, `_`, and `type`. They are reserved only inside the statement they belong to. Elsewhere they can serve as variable names. The first three belong to the `match` statement. The last belongs to the `type` statement, which creates type aliases for type hinting.

Most reserved words are lowercase. The exceptions are `False`, `None`, and `True`. Those three are also names in the built-in scope, and they are technically objects. They are fully reserved, though, and cannot be used for anything except the objects they stand for. The other reserved words are built into the syntax, and each one works only in its own context.

Other Python implementations, such as Jython, may allow reserved words as identifiers in some contexts. Chapter 2 of the book covers alternative Pythons.

Module names also become variables. A file named `and.py` or `my-code.py` can run as a top-level script. You cannot import either one, because its name becomes a variable on import. Reserved words and dashes are not allowed in such names, but underscores are fine. The same constraint applies to package folder names.

### Python's deprecation policies

Making a new word reserved can break a lot of code. For that reason, Python usually phases such changes in. When a change could affect existing code, Python first makes it an option. It then issues deprecation warnings for one or more releases before the change is enabled. That gives you time to notice the warnings and update your code.

A newer category, the soft reserved word, lets Python add a reserved word with neither warnings nor breakage. This is partly an admission that deprecations only go so far.

Deprecation policies are not always followed. Major releases such as 3.0 broke existing code widely. Some newer changes were also made without the full process, because their promoters judged them justifiable or harmless. A steering committee is meant to enforce the policies, but it has done little to stop the flood of change.

Even when warnings are issued, programs that are hard to change will break. Source code shipped to users who upgrade Python without warning is the usual case. Those users may see deprecation warnings as a bandage on a serious wound rather than a courtesy. A warning does not make a breaking change acceptable.

### Naming conventions

Besides the required rules, Python has naming conventions. They are not enforced, but programmers usually follow them. Names with two leading and trailing underscores, such as `__name__`, have special meaning to the interpreter. Avoid that pattern for your own names, except where it is expected. The conventions are:

- Names that begin with a single underscore, such as `_X`, are not imported by a `from module import *` statement. The chapter on modules covers that statement.
- Names that have two leading and trailing underscores, such as `__X__`, are system-defined. They have special meaning to the interpreter and provide implementation details for classes.
- Names that begin with two underscores but do not end with two more, such as `__X`, are localized, or "mangled," to their enclosing class. The chapter on classes covers this pseudoprivate form.
- The name that is just a single underscore, `_`, keeps the result of the last expression at some interactive prompts. It is also a soft reserved word for a wildcard in `match`.

Programmers also follow other conventions. Some write long names in camelCase, as in `aLongName`. Others use underscores, as in `a_long_name`. Both are valid under Python and under this book.

Later, class names usually start with an uppercase letter. Module names usually start with a lowercase letter. The name `self` is not reserved, but it usually plays a special role in classes. Built-in names are predefined but not reserved, so you can reassign them. Setting `open = 99` silently works, though you may wish it did not.

### Names have no type, but objects do

It is important to keep names and objects apart. Objects have a type, such as integer or list. They may be mutable or immutable. Names, also called variables, are always references to objects. A name has no mutability and no type of its own. It only has the type of the object it refers to at a given moment.

That means you can assign different kinds of objects to the same name over time.

```
>>> x = 0 # x bound to an integer object
>>> x = 'Hello' # Now it's a string
>>> x = [1, 2, 3] # And now it's a list
```

Functions and classes make this flexibility useful. A name also lives in a scope, a region that sets where the name can be used. Where you assign a name determines where it is visible.

C++ programmers may also note that Python has no `const` declaration. Some objects are immutable, but a name can always be assigned again. Python does have ways to hide names in classes and modules. Those ways differ from C++ declarations. Later chapters cover single-underscore module names, double-underscore class names, and a class decorator that hides attributes.

## Expression statements

In Python, you can use any expression as a statement. That usually means putting it on a line by itself. The result of the expression is not saved, so an expression statement is useful only when it does something as a side effect. Expressions appear as statements in two common situations.

The first is a call to a function or method. Some functions do their work without returning a value. Other languages call these procedures. You can call them as expression statements, because there is no result you need to keep. Methods are simply functions with an implied subject, so the same applies to them.

The second is printing a value at the interactive prompt. Python echoes the result of each expression you type. Technically these are expression statements too. They are a shorthand for `print` statements.

These are the common expression statement forms.

```
hack('Py', 3.12) # Function calls
code.hack('Py') # Method calls
hack # Printing results in the interactive interpreter (REPL)
print(a, b, c, sep='') # Printing operations (a special function call)
yield x ** 2 # Yielding expression statements (generators)
await producer() # Pausing for steps to finish (coroutines)
```

Calls take zero or more argument objects in parentheses, after the function or method name. An argument is really an expression that evaluates to an object.

The last three forms are special cases. Printing is a function call that usually sits alone on a line, so it deserves its own section. The `yield` and `await` forms appear in generator and coroutine functions, which come later. All three are expressions that look like statements.

For example, you normally run `print` alone on a line. It still returns a value, like any other function call. That value is `None`, the default return for functions that return nothing useful. You need a second `print` to see it.

```
>>> x = print('code') # print is a function-call expression
code
>>> print(x) # But is usually coded as an expression statement
None
```

Expressions can appear as statements, but the reverse is not true. A statement cannot be used as an expression. A statement that is not also an expression usually has to stand alone on its line. It cannot nest inside a larger structure.

Python does not let you put a basic `=` assignment inside another expression. This prevents a common mistake, where you type `=` when you meant the equality test `==`. The `:=` operator, covered earlier, works as a nested assignment with less risk of confusion. Other coding patterns can achieve similar goals, too.

### Expression statements and in-place changes

Here is a mistake worth repeating, because it shows up so often. Expression statements frequently call list methods that modify a list directly.

```
>>> L = [1, 2]
>>> L.append(3) # Append is an in-place change
>>> L
[1, 2, 3]
```

Newcomers sometimes assign the result of such a call back to the name. The result is `None`, not the list.

```
>>> L = L.append(4) # But append returns None, not L
>>> print(L) # So we lose our list!
None
```

In-place methods such as `append`, `sort`, and `reverse` change the list directly. They do not return the list. They return `None`. Assigning that result back to the name loses your reference to the list, which is then usually garbage-collected.

So call in-place operations without assigning their results. The same pitfall can appear with some looping statements, which later chapters cover.

## Print operations

In Python, `print` prints things. It is a friendly interface to the standard output stream. It is a function-call expression, but it is so common that it is usually written as a statement.

Printing converts one or more objects to their text, adds a little formatting, and sends the result to standard output or another file-like stream. Printing ties closely to files and streams.

### File methods and the standard output stream

Chapter 9 of the book covers file methods that write text, such as `file.write(str)`. Printing is similar but more focused. A file write method writes strings to any file. A `print` call writes objects to the `stdout` stream by default, and it converts and formats them for you. You do not need to turn objects into strings first.

The standard output stream, often called `stdout`, is a default place for a program's text output. Together with standard input and standard error, it is one of three data connections made when a script starts. Standard output usually maps to the window where you started Python. It can be redirected to a file or pipe by the operating system shell, or rerouted by a coding GUI.

The `stdout` file object lives in the built-in `sys` module as `sys.stdout`. You can emulate `print` with calls to its `write` method. However, `print` is much simpler in most cases. It also makes it easy to print to other files and streams.

Printing was one place where Python 3 and Python 2 diverged. In Python 2, printing was a statement. In Python 3, it became a built-in function, and that broke nearly every existing program. The book no longer covers the Python 2 statement. The change still acts as a natural brake on language changes, and some coders still type `print x` out of habit.

### The print function

Printing is not really a separate statement form. It is an instance of the expression statement from the previous section. Because `print` returns no value you care about, it usually stands alone on a line. It is a normal function, though. It accepts standard call syntax, including keyword arguments for special modes. You can also pass it around as an object or reassign it to another implementation.

Calls to `print` have this form.

```
print([object, …][, sep=' '][, end='\n'][, file=sys.stdout][, flush=False])
```

Items in square brackets are optional. Values after `=` are the defaults for keyword arguments. The function prints the text of one or more objects. It separates them with the `sep` string and ends with the `end` string. It writes to the `file` stream, and it flushes buffered output if `flush` is true.

The `sep`, `end`, `file`, and `flush` parts must be given as keyword arguments. You pass them with `name=value` syntax. Keyword arguments can appear in any left-to-right order after the objects to print. Each one controls a part of the output.

- `sep` is a string placed between each object's text. It defaults to a single space. Passing an empty string removes the separators.
- `end` is a string added at the end of the printed text. It defaults to a newline character, `\n`. Passing an empty string keeps the cursor on the same line, so the next `print` continues that line.
- `file` names the file, standard stream, or other file-like object that receives the text. It defaults to `sys.stdout`. Any object with a `write(string)` method works, including a real file opened for output.
- `flush` defaults to `False`. Passing a true value forces the text through the output stream right away. Normally, the file object decides whether output is buffered in memory.

Each object is turned into text by the `str` built-in, or the equivalent inside Python. That built-in returns a user-friendly display string for any object. With no arguments, `print` writes only a newline. That shows as a blank line.

Printing is simpler than the full details suggest. The examples below run at the REPL. They print several object types with the default separator and end. These defaults fit the most common use.

```
>>> print() # Display a blank line
>>> x = 'python'
>>> y = 3.12
>>> z = ['lp6e']
>>> print(x, y, z) # Print objects per defaults
python 3.12 ['lp6e']
```

You do not need to convert objects to strings here, unlike with file write methods. By default, `print` adds a space between objects. To remove it, pass an empty string to `sep`. Or pass a separator of your own.

```
>>> print(x, y, z, sep='') # Suppress separator
python3.12['lp6e']
>>>
>>> print(x, y, z, sep=', ') # Custom separator
python, 3.12, ['lp6e']
```

By default, `print` also ends the line. You can suppress the line break by passing an empty string to `end`. You can also pass a different ending, including a `\n` if you want a manual break. The second example below is two statements on one line, separated by a semicolon, to show how custom endings behave.

```
>>> print(x, y, z, end='') # Suppress line break (see >>>)
python 3.12 ['lp6e']>>>
>>>
>>> print(x, y, z, end=''); print(x, y, z) # Two prints, same output line
python 3.12 ['lp6e']python 3.12 ['lp6e']
>>> print(x, y, z, end='...\n') # Custom line end
python 3.12 ['lp6e']...
>>>
```

You can combine `sep` and `end` in one call. They can appear in either order, but they must come after all the objects.

```
>>> print(x, y, z, sep='...', end='!\n') # Multiple keywords
python...3.12...['lp6e']!
>>> print(x, y, z, end='!\n', sep='...') # Order doesn't matter
python...3.12...['lp6e']!
```

The `file` keyword sends the text to an open output file for that one `print` call. This is a form of stream redirection, which the next section explores.

```
>>> print(x, y, z, sep='...', file=open('data.txt', 'w')) # Print to a file
>>> print(x, y, z) # Back to stdout
python 3.12 ['lp6e']
>>> print(open('data.txt').read()) # Display file text
python...3.12...['lp6e']
```

The `sep` and `end` options are only conveniences. For more specific formatting, do not rely on them. Build a custom string first, either ahead of time or inside `print`. Then print the string in one go. String formatting expressions and f-strings were designed for this job.

```
>>> text = '%s: %-.4f, %05d' % (x, y, int(z[0][-2]))
>>> print(text)
python: 3.1200, 00006
>>> print(f'{x}: {y:-0.4f}, {int(z[0][-2]):05d}')
python: 3.1200, 00006
```

Some programmers think f-strings are required for `print`, and they add them where they are not needed. For simply printing objects separated by spaces, f-strings are overkill.

```
>>> a, b, c, = 11, 3.14, 'hack'
>>> print(f'{a} {b} {c}')
11 3.14 hack
>>> print(a, b, c)
11 3.14 hack
```

Use the right tool for the job.

### Print stream redirection

By default, `print` sends text to the standard output stream. Sometimes you want it elsewhere. You might save results to a text file for later use or for testing. You can redirect in the operating system shell, but Python can redirect a script's streams too.

Start with the usual language benchmark, the "hello world" program. Printing a string is all it takes.

```
>>> print('hello world') # Print a string object
hello world
```

At the interactive prompt, you often do not need `print` at all. Expressions you type are echoed back.

```
>>> 'hello world' # Interactive echoes
'hello world'
```

This is not much of a program. It does show how printing works. The `print` operation is a convenience layer over `sys.stdout`, with a little default formatting. You can also write to `sys.stdout` directly, which is harder but shows the mechanism. Chapter 9's file methods make this possible.

```
>>> import sys # Printing the hard way
>>> sys.stdout.write('hello world\n')
hello world
```

This code calls the `write` method of `sys.stdout`. That object is an open file connected to the output stream, set up when Python starts. The `print` operation hides these details, which makes simple printing simpler.

### Manual stream redirection

The direct `sys.stdout` form matters because it is the basis of a common technique. A `print` call is equivalent to a longer write sequence. The next pair of lines shows the link.

```
print(X, Y)
```

This is equivalent to the longer form below.

```
import sys
sys.stdout.write(str(X) + ' ' + str(Y) + '\n')
```

The longer form converts each value with `str`. It adds a separator and a newline with `+`. Then it calls the output stream's `write` method. That is exactly what `print` does. The long form is not useful for printing alone. The useful part is that you can reassign `sys.stdout` to something else. That sends every `print` somewhere different.

```
import sys
sys.stdout = open('log.txt', 'a') # Redirects prints to a file
…
print(x, y, x) # Now printed text shows up in log.txt
```

This code points `sys.stdout` at a file named `log.txt`, in the current working directory. It opens the file in `'a'` append mode, so new text goes after the existing content. After the change, every `print` in the program writes to that file. There is one `sys` module per program, so the change applies everywhere.

You can even set `sys.stdout` to an object that is not a file, as long as it has the expected interface. That interface is a method named `write` that receives the printed text. If the object is a class, you can route or process the text however you like in its `write` method.

Redirecting by resetting `sys.stdout` is handy for programs first written with `print` statements. If output should go to a file from the start, you can call the file's write methods instead. To redirect a program that uses `print`, resetting `sys.stdout` avoids editing every `print`. It also avoids shell redirection syntax, which may be above some users' pay grades.

The same trick appears elsewhere. Streams can be reset to objects that show text in pop-up windows in a GUI, or that color text in an IDE such as IDLE.

### Automatic stream redirection

Redirecting printed text by assigning `sys.stdout` is useful. But there is no direct way to restore the original stream afterward. The fix is simple, because `sys.stdout` is an ordinary file object. You can save it first and restore it later.

```
>>> import sys
>>> temp = sys.stdout # Save for restoring later
>>> sys.stdout = open('log.txt', 'a') # Redirect prints to a file
>>> print('lp6e was here') # Prints go to file, not here
>>> print(1, 2, 3)
>>> sys.stdout.close() # Flush output to disk
>>> sys.stdout = temp # Restore original stream
>>> print('back in the REPL') # Prints show up here again
back in the REPL
>>> print(open('log.txt').read()) # Result of earlier prints
lp6e was here
1 2 3
```

Saving and restoring the stream like this takes some extra work. Because the need comes up often, the `print` function has an extension that makes this unnecessary.

The `file` keyword sends a single `print` call to a file, without resetting `sys.stdout`. The redirection is temporary, so normal `print` calls still go to the original stream. The next snippet sends one print to `log.txt`.

```
log = open('log.txt', 'a')
print(x, y, z, file=log) # Print to a file-like object
print(a, b, c) # Print to original stdout
```

These redirected forms are useful when a program needs to print to both a file and standard output. Give them a file object, or an object with the same `write` method. Do not give them a file name as a string. Here is the technique in action.

```
>>> log = open('log2.txt', 'w')
>>> print(1, 2, 3, file=log)
>>> print(4, 5, 6, file=log)
>>> log.close()
>>> print(7, 8, 9)
7 8 9
>>> print(open('log2.txt').read())
1 2 3
4 5 6
```

The same keyword is common for error messages. Python keeps standard error open as `sys.stderr`. You can write to it with its `write` method and format the text yourself. Or you can print with redirection.

```
>>> import sys
>>> sys.stderr.write(('Bad!' * 8) + '\n')
Bad!Bad!Bad!Bad!Bad!Bad!Bad!Bad!
>>> print('Bad!' * 8, file=sys.stderr)
Bad!Bad!Bad!Bad!Bad!Bad!Bad!Bad!
```

With redirection in mind, the link between printing and file writes should be clear. The next demo prints both ways. Then it sends the output to external files, to confirm that both produce the same text. The `rb` mode shows the raw bytes, and on Windows each newline comes out as `\r\n`.

```
>>> import sys
>>> X, Y = 1, 2
>>> print(X, Y) # Print: the easy way
1 2
>>> sys.stdout.write(str(X) + ' ' + str(Y) + '\n') # Print: the hard way
1 2
4
>>> print(X, Y, file=open('temp1', 'w')) # Redirect text to file
>>> open('temp2', 'w').write(str(X) + ' ' + str(Y) + '\n') # Send to file manually
4
>>> print(open('temp1', 'rb').read()) # Binary mode for bytes
b'1 2\r\n'
>>> print(open('temp2', 'rb').read())
b'1 2\r\n'
```

Unless you enjoy typing, `print` is usually the best choice for showing text. A later chapter shows a `print` emulation that uses the same patterns, and that can be customized.

The `sys.__stdout__` attribute also helps. It holds the value that `sys.stdout` had when the program started. You still have to assign it back to `sys.stdout` to return to that stream. Some GUI programs have no console, so `sys.stdout` may be `None` there. Check for that where it matters.

### Why you will care: print and stdout

The link between `print` and `sys.stdout` lets you replace `sys.stdout` with any object that has the same `write` method as a file. Because `print` just sends text to `sys.stdout.write`, you can capture printed text. Assign `sys.stdout` to an object whose `write` method processes the text however you need.

For example, you can send printed text to a GUI window, or copy it to several destinations. You do this by defining an object whose `write` method does the routing. A later chapter on classes shows a full example. Here is a short preview.

```
class FileFaker:
    def write(self, string):
        # Do something with the printed text in string
import sys
sys.stdout = FileFaker()
print(someObjects) # Sends text to class write method
```

This works because `print` is a polymorphic operation. It does not care what `sys.stdout` is. It cares only that the object has a `write` method. The `file` keyword makes this even simpler, because you do not need to reset `sys.stdout`. Normal prints still reach the standard output stream.

```
myobj = FileFaker() # Redirect to object for one print
print(someObjects, file=myobj) # Does not reset sys.stdout
```

The built-in `input` function reads from `sys.stdin`. You can intercept reads in a similar way, using classes with file-like `read` methods.

This also explains how printed text reaches a web page. Server-side scripts that print to standard output send their HTML reply that way. The same stream makes it possible to redirect a script's input and output from the operating system shell.

```
python script.py < inputfile > outputfile
python script.py | filterProgram
```

The `print` redirection tools in Python are pure-Python versions of some of these shell forms. Other resources cover web scripts and shell syntax in more depth.

## Chapter summary

This chapter covered assignments, expressions, and print operations. Each of them is simple to use, but each has optional forms that save manual work. Augmented and named assignments are examples, and so is the `file` keyword for `print`. Along the way, you learned the rules for variable names, the ways to redirect streams, and common mistakes. One of those mistakes is assigning the result of an `append` call back to the list's name.

The next chapter covers the `if` statement, which is Python's main selection tool. It also looks at Boolean expressions and the `match` statement.

## if statements

The `if` statement selects the actions a program performs. Along with the `if` expression, it is Python's main selection tool. Much of a program's logic lives in `if` statements. It is also the first compound statement we study in depth. Like every compound statement, it can contain other statements, including other `if` statements.

Python lets you combine statements in two ways. They can run one after another, in sequence. They can also be nested, so that they run only under certain conditions. Selections and loops both work this way.

### General format

The `if` statement looks like the `if` in most procedural languages. It starts with an `if` test. It can then have one or more optional `elif` tests, which mean "else if." It can end with an optional `else` block. Each test and the `else` has its own block of nested statements, indented under a header line.

When the statement runs, Python runs the block under the first test that is true. If every test is false, it runs the `else` block instead. The general form looks like this:

```
if test1:          # Main if test
    statements1    # Associated block
elif test2:        # Optional elif test(s)
    statements2    # Associated block
else:              # Optional else default
    statements3    # Associated block
```

### Basic examples

Only the first `if` test and its statements are required. Every other part is optional. Here is the simplest form, typed at the interactive prompt.

```
>>> if 1:
...     print('true')
...
true
```

In many interactive interfaces, the prompt changes to `...` on continuation lines. In IDLE, you simply drop to an indented line instead. Press Backspace to move back. A blank line, made by pressing Enter twice, ends the statement and runs it.

The number `1` is Boolean true, so this test always succeeds. To handle a false result, add an `else`. Its block runs when the `if` test is not true.

```
>>> if not 1:
...     print('true')
... else:
...     print('false')
...
false
```

The next example uses every optional part. It names the roots of today's mobile operating systems. The list is not complete, and it will go out of date as new systems appear.

```
if os in ['iOS', 'iPhoneOS']:
    print('macOS')
elif mode == 'mobile' and os != 'Windows':
    print('Linux')
else:
    print('unknown?')
```

```
>>> os, mode = 'Windows', 'mobile'
>>> …insert the code above here…
unknown?
```

The whole statement runs from the `if` line through the block under `else`. Python runs the statements under the first true test. If all tests are false, it runs the `else` part. Both the `elif` and `else` parts can be left out. Each section can hold more than one statement. The words `if`, `elif`, and `else` line up at the same indentation, which shows they belong together.

The `and` operator in that example is true only when both of its sides are true. The next sections explain logical tests in more detail.

You can nest an `if` inside another `if` to make choices that depend on earlier ones. This example first checks that the mode is `mobile`. Only then does it check the system name. The outer and inner tests act as an implied `and`.

```
if mode == 'mobile':
    if os == 'Android':
        print('Linux')
    elif os != 'Windows':
        print('macOS')
```

```
>>> os, mode = 'Android', 'mobile'
>>> …insert the code above here…
Linux
```

## Multiple-choice selections

Until Python 3.10, the language had no multiple-choice statement like the `switch` in some other languages. Python 3.10 added `match`, which covers the same goal and more. Even so, multiple-choice logic can be written with a series of `if`/`elif` tests. It can also be written by indexing a dictionary or searching a list.

Dictionaries and lists can be built while the program runs. That makes them more flexible than fixed `if` or `match` logic. The following example picks an operating system's release year from its name. The years are roughly right, not exact.

```
>>> choice = 'Windows'
>>> print({'macos': 2001, # A dictionary-based 'switch'
       'Linux': 1991,      # Use get() for a default (covered next)
       'Windows': 1985}[choice])
1985
```

Indexing on the key `choice` branches to one of several values. It works much like a `switch` in other languages. It can take a moment to see this clearly the first time. An almost equivalent `if` statement looks like this.

```
if choice == 'macos':
    print(2001)
elif choice == 'Linux':
    print(1991)
elif choice == 'Windows':
    print(1985)
else:
    print('Bad choice')
```

```
>>> …insert the code above here…
1985
```

The `if` version is more readable. Its weakness is that it cannot handle choices that are unknown until the program runs, unless you build the code as a string and run it with the `eval` or `exec` tools. A dictionary handles such dynamic data more easily. In more dynamic programs, data structures give you more flexibility.

### Handling switch defaults

The `else` clause handles the default case, when no key matches. Earlier, you saw that dictionary defaults can be coded with `in` tests, `get` method calls, or exception catching with `try`. All three techniques work for dictionary-based multiple choice too. Here is `get` with a default. The `dict` call builds the same dictionary more compactly.

```
>>> branch = dict(macos=2001, Linux=1991, Windows=1985)
>>> print(branch.get('Windows', 'Bad choice'))
1985
>>> print(branch.get('Solaris', 'Bad choice'))
Bad choice
```

An `in` membership test in an `if` statement gives the same default effect.

```
>>> choice = 'AmigaOS'
>>> if choice in branch:
...     print(branch[choice])
... else:
...     print('Bad choice')
...
Bad choice
```

The `try` statement is a general way to handle dictionary defaults. It catches the error that a missing key would raise. For more on exceptions, see the earlier material on `try`.

```
>>> choice = 'GEM'
>>> try:
...     print(branch[choice])
... except KeyError:
...     print('Bad choice')
...
Bad choice
```

### Handling larger actions

Dictionaries link keys to values. The blocks under an `if` can hold much larger actions. Later, you will learn that dictionaries can also hold functions. Those functions represent complex actions, and they make a general "jump table." A dictionary value can be a function name or an inline `lambda`. Adding parentheses runs the action.

The sample below is abstract. It is revisited after function definitions are covered.

```
def action(): ...
def default(): ...
branch = {'Android': lambda: ...,  # A table of callable function objects
          'iOS': action,           # Via inline lambdas, or def elsewhere
          'Symbian OS': lambda: ...}
choice = 'Android'
branch.get(choice, default)()      # Fetch and run associated action
```

Dictionary-based branching is useful when your data is dynamic. Most programmers will still find an `if` statement the straightforward way to do this job. As a rule of thumb, when in doubt, favor simplicity and readability. That is the "Pythonic" way.

The `match` statement may now handle basic multiple-choice selections better. But it does not do general logic the way `if` does. It cannot use dynamic data like a dictionary lookup. It also adds a good deal of complexity for other roles. The next section covers it.

## match statements

For most of its history, Python had no multiple-choice statement. The tools described above were enough, and they still appear in plenty of Python code written today. Other languages, however, keep copying features from one another. Their own distinctions blur as a result, often for no better reason than familiarity. The `match` statement, new in Python 3.10, is one such feature.

At its basic level, `match` adds a multiple-choice statement to Python. It works much like a `switch` in other languages. In some contexts, it can replace `if`/`elif`/`else` chains and dictionary indexing. In its full form, `match` implements structural pattern matching. That feature quickly becomes complex. Many programmers never asked for it, and it is hard to justify, especially for newcomers.

This section focuses on the basic roles of `match`. It touches on the advanced pattern features only briefly. For the full story, Python's own documentation is the place to go.

### Basic match usage

The basic usage of `match` is straightforward. The following snippets mimic traffic lights in some countries. To run them, first assign `state` to one of the values named in the comments.

```
# state = 'go' or 'stop' or other
if state == 'go':
    print('green')
elif state == 'stop':        # if-based multiple choice
    print('red')
else:
    print('yellow')

colors = dict(go='green', stop='red')    # Dictionary-based multiple choice
print(colors.get(state, 'yellow'))
```

The equivalent `match` statement gives explicit syntax for the same logic. It takes more lines and more indentation.

```
match state:
    case 'go':
        print('green')        # match-based multiple choice: 3.10+
    case 'stop':
        print('red')
    case _:
        print('yellow')
```

The `match` statement first evaluates the expression in its header, here `state`. It then compares the result with each `case` value below it, from top to bottom. When the first match is found, the block under that `case` runs, and the whole `match` ends. If no `case` matches, the `_` case runs as a fallback default. The `_` case must come last. If there is no `_` case, the statement exits silently.

A `case` block can hold several statements, and it can contain nested statements. A `match` can also sit inside other statements. A `case` header can list several values separated by `|`, which means "or." It can name a variable with `as` to hold the matched value. A bare name works as a catch-all, much like `_`, but it stores the value.

```
# state = 'go' or 'proceed' or 'start', or 'stop' or 'halt', or any other
match state:
    case 'go' | 'proceed' | 'start':    # Match any one of these 3
        print('green')                  # First left-to-right match wins
        print('means go')
    case 'stop' | 'halt' as what:       # Match any, and assign it to what
        print('red')                    # what outlives match if assigned
        print('means', what)
    case other:                         # Set other to state, and match
        print('catchall', other)        # other outlives match if assigned
```

Variables assigned in a `case` header, such as `what` and `other`, keep their values after the `match` ends. Code that follows the `match` can use them. That works as long as the code is in the same scope, which roughly means the same module or function.

### Match versus if

This live example maps statements to categories. It also assigns variables for later use. The `for` loop here is explained in more detail later.

```
>>> for stmt in ['if', 'while', 'try']:
...     match stmt:
...         case 'if' | 'match':
...             print('logic')
...         case 'for' | 'while' as which:
...             print('loop')
...         case other:
...             print('tbd')
...
logic
loop
tbd
>>> which, other
('while', 'try')
```

The equivalent `if` version must assign the variables explicitly. It needs less indentation, but this example is artificial. An `if` can handle more complex logic than `match` can. It is not only a multiple-choice tool.

```
>>> for stmt in ['if', 'while', 'try']:
...     if stmt in ['if', 'match']:
...         print('logic')
...     elif stmt in ['for', 'while']:
...         which = stmt
...         print('loop')
...     else:
...         other = stmt
...         print('tbd')
...
…same results…
```

You will see basic `match` statements again in later chapters. Although `match` cannot code general logic like `if`, it makes multiple-choice selection explicit. Its extension to structural pattern matching is harder to justify. Read on, and decide for yourself.

### Advanced match usage

Beyond its basic level, `match` becomes too complex to cover fully here. It goes well beyond multiple-choice logic. It defines a small language of its own for pulling components out of structured objects. In brief, a `case` value can be any of these patterns:

- Literal patterns: a literal `X` matches the same value, by equality or identity.
- Wildcard patterns: `_` matches anything, but the value is not assigned to `_`.
- Capture patterns: the variable `X` matches anything, and is assigned the value.
- Or patterns: `X | Y | Z` matches `X`, `Y`, or `Z`, and stops at the first match.
- As patterns: `X as Y` matches pattern `X`, and assigns the matched value to `Y`.
- Additional patterns that match sequences, mappings, attributes, and instances by their structure.

Example 12-1 is an artificial, if dense, example. It shows literal, sequence, and mapping patterns. Its `[…]` and `(…)` patterns both match any sequence, and they are interchangeable. Its `{…}` pattern matches a mapping. A single `*` or `**` name collects the unmatched parts of a sequence or mapping. This is similar to the extended unpacking you saw earlier. But `**` is unique to patterns, and not every part of a pattern must be a variable. Assignments to starred names happen as a side effect of the match test.

Example 12-1. matchdemo.py

```
# state = 1 or
# [1, 2, 3] or [0, 2, 3] or (1, 2, 3) or (0, 2, 3) or
# dict(a=1, b=2, c=3) or dict(a=0, b=2, c=3) or other
match state:
    case 1 | 2 | 3 as what:                   # Match integer literals, what = 1
        print('or', what)
    case [1, 2, what]:                        # Match sequence (1), what = 3
        print('list', what)
    case [0, *what]:                          # Match sequence (0), what = [2, 3]
        print('list', what)
    case {'a': 1, 'b': 2, 'c': what}:         # Match mapping, what = 3
        print('dict', what)
    case {'a': 0, **what}:                    # Match mapping, what = {'b': 2, 'c': 3}
        print('dict', what)
    case (1, 2, what):                        # Match sequence: same as [1, 2, what]
        print('tuple', what)
    case (0, *what):                          # Match sequence: same as [0, *what]
        print('tuple', what)
    case _ as what:                           # Match all other, what = other
        print('other', what)
```

The `[…]`, `{…}`, and `(…)` patterns in these `case` headers are not ordinary object literals. They are special syntax forms that contain nested patterns. Many of those nested patterns happen to be literal patterns here. Nested patterns can also be captures, possibly after one `*` or `**`. They can use `|` ors or `_` wildcards. The header `[*a, 2 | 3, _]` is a valid sequence pattern, though it has little to do with list literals.

Attribute and instance patterns depend on classes, which you will meet later. They check attribute values and membership in an inheritance tree. Some of their parts are nested patterns too. Here is a preview. You can return to it after you have read the material on classes.

```
class Emp:
    def __init__(self, name): self.name = name

pat = Emp('Pat')      # pat.name becomes 'Pat': see the classes material
# state = 'Pat' or pat
match state:
    case pat.name as what:         # Match object's attribute, what = 'Pat'
        print('attr', what)
    case Emp(name=what):           # Match an Emp instance, what = 'Pat'
        print('instance', what)
```

Parentheses can group any pattern, as they do in ordinary expressions. Nested structures match recursively, much like sequence assignment. Each `case` header can also end with an optional guard. A guard is an `if` test that follows the optional `as` name. It must be true for the `case` to be selected and its block to run.

```
state = ((1, 2), 3)
guard1 = True    # a=1, b=3 if True; a=(1, 2) if False
match state:
    case ((a, 2), b) if guard1:     # Match+run only if guard1 is True
        print(f'case1 {a=} {b=}')
    case (a, 3) as what:            # Reached only if guard1 is False
        print(f'case2 {a=} {what=}')
    case [a, (3 | 4)] as what if guard1:
        print(f'case3 {a=} {what=}')
```

All of this is a lot of machinery for mostly simple jobs. So this handbook stops short of the full pattern language. For the advanced roles of `match`, including every detail of its special patterns, consult Python's online documentation.

It is worth pausing on one fact first. Python ran successfully for about three decades without a `match` statement. Adding a complex subsystem to replace a small amount of code may be harder to justify than it looks. Many readers will weigh that trade-off for themselves.

`match` can still be useful in simpler roles. You still have to choose among `if`, dictionary lookups, and `match` when you code multiple-choice logic. Avoid doing something only because another language does it. You are writing Python now, and the choice is yours.

## Python syntax revisited

The basic syntax model was introduced earlier. Now that `if` and `match` are larger statements, this section reviews the rules and adds detail. Python's syntax is simple and statement-based. These are its main points.

**Statements run one after another.** Python normally runs statements in a file or nested block from first to last. Statements such as `if`, loops, and exceptions make the interpreter jump around. The path through a program is called the control flow. Statements that affect it are often called control-flow statements.

**Block and statement boundaries are automatic.** Python has no braces or begin/end words around blocks. It uses the indentation of statements under a header to group them. Python statements also do not need semicolons. The end of a line usually ends the statement. Special cases let a statement span lines or share a line with another.

**Compound statements are a header, a colon, and indented statements.** Every compound statement follows this pattern. The header line ends with a colon, and the nested statements are usually indented under it. The indented statements form a block, sometimes called a suite. In an `if`, the `elif` and `else` parts are also headers, each with a block of its own. As a special case, a simple block can sit on the header line.

**Blank lines, spaces, and comments are usually ignored.** Blank lines are optional in files. At the interactive prompt, though, a blank line ends a compound statement. Spaces inside statements are almost always ignored, except in string literals and in indentation. A comment starts with `#`, outside a string, and runs to the end of the line.

**Docstrings are ignored by Python but kept for tools.** A documentation string, or docstring, is a string at the top of a file or some statements. Unlike a `#` comment, a docstring is retained at runtime. Python does not act on its content, but tools can display it.

### Block delimiters: indentation rules

Python detects block boundaries from indentation. That is the empty space to the left of your code. This section repeats the rules with a few more details.

All statements indented the same distance belong to the same block. They line up vertically, like a column. A block ends at a less-indented line, at the end of the file, or at a blank line in the REPL. A more deeply nested block is indented further to the right.

For example, this code has three blocks. The top-level code is not indented at all. The block inside the outer `if` is indented four spaces. The `print` under the nested `if` is indented eight spaces.

```
x = 1
if x:
    y = 2
    if y:
        print('block2')
    print('block1')
print('block0')
```

*Figure 12-1. Nested blocks of code denoted by their indentation*

Top-level code must start in column 1. Nested blocks can start in any column. Indentation can use any number of spaces or tabs, as long as every statement in one block uses the same amount. Python does not care how you indent, only that you are consistent. Four spaces or one tab per level are common, but there is no single rule.

Indenting code is natural in practice. Errors of indentation are easy to spot, because the lines look wrong. The example with the `'Hack'` string shows three typical mistakes. The first line is indented when it should not be. One line is indented unexpectedly after an `if` block. And a line is indented inconsistently with the rest of its block. Python reports each of these as an error.

The corrected version looks like this. Even in a small example, proper indentation makes the intent clear.

```
x = 'Hack'
if 'tho' in 'python':
    print(x * 8)                 # Prints 8 Hack
x += 'More!'
if x.endswith('re!'):
    x *= 2
print(x)                         # Prints HackMore!HackMore!
```

Whitespace matters in only one major place: the indentation at the left of your code. Elsewhere, you can add spaces or leave them out. Indentation is part of Python's syntax, not a style suggestion. All statements in a single block must have the same indentation. Otherwise, Python reports a syntax error. Because blocks need no explicit start and end markers, some syntactic clutter from other languages is unnecessary.

Indentation also enforces consistency, which supports readability. The indentation of each line shows what it belongs to. That makes code easier to maintain and to reuse. Indentation is easier than it may sound. Consistently indented code always follows the rules. Most editors, IDLE included, indent automatically as you type.

### Avoid mixing tabs and spaces

You can use spaces or tabs to indent. It is usually a bad idea to mix them within one block, so pick one. Technically, a tab moves the current column to the next multiple of 8. Code can therefore work with a consistent mix of tabs and spaces. Even so, mixing them makes code hard to read and change. A tab can look very different in another programmer's editor.

Python reports an error when a script mixes tabs and spaces inconsistently within a block. That means the meaning would depend on how many spaces a tab equals. So avoid it. Use consistent indentation, not a mix.

### Statement delimiters: lines and continuations

A statement normally ends at the end of the line it appears on. A statement that is too long for one line has a few options.

- Open pairs: a statement can continue onto the next line inside `()`, `{}`, or `[]`. Parenthesized expressions and dictionary and list literals can span any number of lines. The statement ends on the line with the closing `)`, `}`, or `]`. Continuation lines can start at any indentation, but aligning them vertically reads best.
- Backslashes: if a statement ends a line with a backslash (`\`) that is not inside a string or comment, the statement continues on the next line. A backslash is best used as a fallback. Forgetting one can cause a syntax error, or make the next line run on its own. Parentheses usually do the same job, so backslashes are rare.
- Semicolons: you can separate noncompound statements with a semicolon to place several on one line. Compound statements cannot share a line this way.
- Multiline strings: triple-quoted strings span lines by design. Adjacent string literals are concatenated. With the open-pair rule, wrapping them in parentheses lets them span lines.

### Special syntax cases in action

An open pair lets a list span several lines.

```
L = ['app',
     'script',
     'program']    # Open pairs may span lines
```

The same rule covers list comprehensions in `[]`. It also covers anything in `()`, such as tuples, expressions, function arguments and headers, and generator expressions. It covers anything in `{}`, such as dictionary and set literals and comprehensions. Some of these come in later chapters. The rule still covers most multiline constructs you will write.

Backslash continuations also work, though they are not common practice.

```
if a == b and c == d and \
   d == e and f == g:
    print('old school')    # Backslashes allow continuations...
```

Because any expression can go in parentheses, the open-pair form is usually the better choice.

```
if (a == b and c == d and
    d == e and e == f):
    print('new school')    # But parentheses usually do too, and are obvious
```

Backslashes are discouraged, because they are easy to miss and easy to leave out. In the following example, `x` is assigned `10`, as intended. If the backslash is dropped, `x` is assigned `6` instead, and Python reports no error. The `+4` line is a valid expression statement by itself. In a real program, this could cause a very hard-to-find bug.

```
x = 1 + 2 + 3 \
+4    # Omitting the \ makes this very different!
```

Python also lets you put more than one simple statement on a line, separated by semicolons. Some people use this to save space. Most of your code reads better with one statement per line.

```
x = 1; y = 2; print(x)    # More than one simple statement
```

Triple-quoted strings span lines. Adjacent string literals join as if a `+` were placed between them. With the open-pair rule, wrapping them in parentheses lets them span lines. The first assignment below puts newline characters at the line breaks. The other two join the pieces into one string. In the first form, any `#` text is part of the string, not a comment. In the second form, `#` starts a comment that is ignored. Each f-string piece needs its own `f` prefix, even on continuation lines.

```
S = """
aaaa
bbbb
cccc"""
S = ('aaaa'
     'bbbb'    # Comments here are ignored, add \n if needed
     'cccc')
S = (f'{'a' * 4}'    # Also makes 'aaaabbbbcccc'
     f'{'b' * 4}'    # Use f'' on each f-string part
     r'cccc')        # And ditto for r'' raw-string parts
```

The first assignment makes `S` equal to `'\naaaa\nbbbb\ncccc'`. The other two make `S` equal to `'aaaabbbbcccc'`. Each `r` prefix marks a raw string, and each `f` prefix marks an f-string.

Python also lets you move a compound statement's body up to the header line, if the body holds only simple statements. You will see this mostly in simple `if` statements with one test and one action.

```
if 1: print('hello')    # Simple statement on header line
```

You can combine these special cases to write code that is hard to read. That is not recommended. As a rule of thumb, put each statement on a line of its own, and indent all but the simplest blocks. Six months from now, you will be glad you did.

## Truth values revisited

Comparisons, equality, and truth values were introduced earlier. The `if` is the first statement that relies on them heavily, so this section adds detail. Python's Boolean operators differ a little from those in some other languages. In Python:

- Every object has an inherent Boolean true or false value.
- Any nonzero number or nonempty object is true.
- Zero, empty objects, and the special object `None` are false.
- Comparisons and equality tests apply recursively to data structures.
- Comparisons and equality tests return `True` or `False`, which are custom versions of `1` and `0`.
- The Boolean `and` and `or` operators return a true or false operand object.
- Boolean operators stop evaluating, or short-circuit, as soon as the result is known.

The `if` statement acts on truth values. Boolean operators combine the results of other tests into richer truth values. There are three Boolean expression operators.

| Expression | True when | Returns |
| --- | --- | --- |
| `X and Y` | both `X` and `Y` are true | either `X` or `Y` |
| `X or Y` | either `X` or `Y` is true | either `X` or `Y` |
| `not X` | `X` is false | either `True` or `False` |

Here, `X` and `Y` can be any truth value, or any expression that returns one, such as an `==` equality test or an `in` membership check. Python spells these operators as words. C uses `&&`, `||`, and `!` instead. Do not confuse them with `&`, `|`, and `^`, which work on numbers, sets, and dictionaries.

The most unusual part is that `and` and `or` return an object, not a plain `True` or `False`. Here is an example.

```
>>> 2 < 3, 3 < 2    # Less than: return True or False (1 or 0)
(True, False)
```

Magnitude comparisons return `True` or `False`. Those are just custom versions of `1` and `0`. The `and` and `or` operators always return one of their operands, either the left object or the right one. In an `if`, their results behave as you expect. You just do not get back a simple `True` or `False`.

For `or`, Python checks the operands from left to right. It returns the first true one and stops there. This is called short-circuit evaluation, because the result is known early and the rest is skipped.

```
>>> 2 or 3, 3 or 2    # Return left operand if true
(2, 3)                # Else, return right operand (true or false)
>>> [] or 3
3
>>> [] or {}
{}
```

In the first line, both operands are true, so Python stops and returns the left one. In the other two lines, the left operand is empty, so Python returns the right one. That right operand may be true or false, but it decides the result of the `or`.

The `and` operator also short-circuits. Python checks from left to right. If the left operand is false, Python stops, because a false left side settles the result.

```
>>> 2 and 3, 3 and 2    # Return left operand if false
(3, 2)                  # Else, return right operand (true or false)
>>> [] and {}
[]
>>> 3 and []
[]
```

In the first line, both operands are true, so Python returns the right one. In the second line, the left operand is `[]`, which is false. Python returns it without running the right side. In the last line, the left side is true, so Python returns the right side, which is an empty list.

The end result matches other languages. When you test the value in an `if` or `while`, you get the logic you expect from `or` and `and`. The difference is that Python returns either the left or the right object, not a simple integer flag. A later section shows how this behavior is useful.

## The if/else ternary expression

A common use of Boolean operators is writing an expression that works like an `if` statement. Consider this code, which sets `A` to `Y` or `Z`, based on the truth of `X`.

```
if X:
    A = Y
else:
    A = Z
```

Sometimes these items are so simple that four lines feel like too many. Other times you want the choice inside a larger expression. For these cases, Python offers a three-part, or "ternary," expression. It says the same thing in one line. It is also a comfortable form for programmers who know C.

```
A = Y if X else Z
```

This expression has the same effect as the four-line `if` statement. In a similar way, `:=` is an expression form of assignment. The ternary expression is an expression form of `if`. It has narrower rules. You cannot place full statements in its parts. You can, however, use it anywhere Python allows an expression.

Like the statement, the ternary expression runs `Y` only when `X` is true, and runs `Z` only when `X` is false. It short-circuits, like the Boolean operators, so only one of the two parts runs. Here are two examples.

```
>>> tone = 'formal'
>>> a = 'code' if tone == 'formal' else 'hack'
>>> a
'code'
>>> tone = 'informal'
>>> a = 'code' if tone == 'formal' else 'hack'
>>> a
'hack'
```

The same effect can often come from a careful combination of `and` and `or`. Those operators return one of their operands, as described earlier. The ternary expression and the Boolean expression below behave the same way.

```
A = Y if X else Z          # Ternary if/else
A = ((X and Y) or Z)       # and+or equivalent
```

This works, but only if `Y` is guaranteed to be true. When it is, the `and` runs first. It returns `Y` if `X` is true. If `X` is false, the `and` skips `Y` and returns the false `X`. Then the `or` returns `Z`. The result is "if `X` then `Y` else `Z`," the same meaning in a different order.

The `and`/`or` form takes a moment of careful thought to understand. That is a reason to avoid it. Use the `if`/`else` expression when you need this structure. Use a full `if` statement when the parts are nontrivial.

A related trick uses `bool`. The `bool` function turns any `X` into `True` or `False`, which work as the index 1 or 0 into a list. That lets you pick one of two values.

```
A = [Z, Y][bool(X)]
```

The `bool` is not needed when `X` already gives a truth value. It is needed when `X` is an object such as a string.

```
>>> ['hack', 'code'][tone == 'formal']
'hack'
>>> ['hack', 'code'][bool('formal')]
'code'
```

This trick is not the same as the ternary expression. Python does not short-circuit here. It always evaluates both `Z` and `Y`, whatever `X` is. The `if`/`else` expression is simpler and easier to read. Like any nestable tool, the ternary expression can produce code that is hard to read. If you struggle to pack logic into one, stop and think about how hard it will be to unpack later. Your teammates will thank you.

## Why you will care: Booleans

One common use of Python's Boolean operators is selecting from a set of objects with `or`.

```
X = A or B or C or None
```

This assigns `X` to the first nonempty, or true, object among `A`, `B`, and `C`. If all of them are empty, `X` becomes `None`. The `or` operator returns one of its two operands, so you can chain fixed candidates together to pick the first nonempty one. A simpler form designates a default.

```
X = A or default
```

Here, `X` is `A` when `A` is true, which means nonzero or nonempty. Otherwise, `X` is `default`.

Short-circuiting can also stop actions from running. An expression on the right of a Boolean operator may call functions that do important work or have side effects. Those calls do not happen when the short-circuit rule applies.

```
if f1() or f2(): ...
```

If `f1` returns a true or nonempty value, Python never runs `f2`. To make sure both functions run, call them before the `or`.

```
tmp1, tmp2 = f1(), f2()
if tmp1 or tmp2: ...
```

The expression `((A and B) or C)` can emulate an `if` statement, though only almost. The ternary expression section explains the details.

Earlier chapters met other Boolean uses. Every object is inherently true or false. So it is easier to test an object directly, as in `if X:`, than to compare it to an empty value, as in `if X != '':`. For a string, the two tests are equivalent. `True` and `False` are the same as `1` and `0`. They are useful for initializing variables (`X = False`), for loop tests (`while True:`), and for showing results at the interactive prompt.

When you define classes later, you can set an object's Boolean nature with either `__bool__` or `__len__`. Python tries `__len__` if `__bool__` is missing. A length of zero makes the object false, because an empty object is false.

Other tools also select true values. The `filter` call and list comprehensions can pick out true values when the candidates are not known until the program runs. They evaluate all values and return every true one. The `any` and `all` built-ins test whether any or all items are true. They short-circuit like `and`, `or`, and `if`/`else`, but they do not select an item.

```
>>> L = [1, 0, 2, 0, 'hack', '', 'py', []]
>>> list(filter(bool, L))    # Get true values
[1, 2, 'hack', 'py']
>>> [x for x in L if x]      # Comprehensions
[1, 2, 'hack', 'py']
>>> any(L), all(L)           # Aggregate truth
(True, False)
```

The `bool` function returns the truth value of its argument, as if the argument were tested in an `if`. Later chapters cover these tools in more depth.

## while loops

Loops repeat an action until some condition changes. Python has two main loop statements. The `while` statement is the most general one. It can handle repetitive work of all kinds. The `for` statement is more specialized. It steps through the items of any iterable object with very little code.

The `while` statement repeats its block as long as a test at the top stays true. The word "loop" comes from control looping back to the top each time. When the test becomes false, control moves to the statement after the loop. If the test is false at the start, the body never runs and the loop is skipped.

### General format

A `while` statement has a header with a test, an indented body, and an optional `else` part. The `else` runs only when control leaves the loop without hitting a `break`. Python checks the test at the top and runs the body. It keeps doing this until the test returns a false value.

```
while test:               # Loop test
    statements            # Repeated loop body
else:                     # Optional else
    statements            # Run if didn't exit loop body with break
```

### Examples

The first example prints a message forever. `True` is a custom version of the integer `1`, and it always means true. Because the test never changes, the body keeps running. Python is not stuck for good, but you may need Ctrl+C to stop it. This kind of loop is called an infinite loop.

```
while True:
    print('Type Ctrl+C to stop me!')
```

The next example removes the first character of a string on each pass. It stops when the string is empty, which is false. Testing an object directly like this is common. It is shorter than writing `while x != '':`. The `end=' '` argument keeps all the output on one line, as the print operations section above explains.

```
x = 'code'
while x:                  # While x is not empty
    print(x, end=' ')     # Print next character
    x = x[1:]             # Strip first character off x
```

The output is `code ode de e`.

The next loop counts from `a` up to, but not including, `b`. Loops like this often generate index values. A `for` loop with `range` is an easier way to do the same job, as you will see below.

```
a = 0
b = 10
while a < b:              # One way to code counter loops
    print(a, end=' ')
    a += 1                # Or, a = a + 1
```

The output is `0 1 2 3 4 5 6 7 8 9`.

Python has no "do until" loop statement. You can simulate one with a test and a `break` at the bottom of the body. The body then always runs at least once.

```
while True:
    # loop body here: always runs at least once
    if test: break        # Test for loop exit at the bottom
```

The `break` statement is what makes this structure work. The next section covers it.

## break, continue, pass, and the loop else

Some statements only do something inside a loop. `break` and `continue` are two of them. The loop `else` clause is tied to `break`, so the two work together. `pass` is a placeholder that is not tied to loops at all. It belongs in the same group of one-word statements.

| Statement | What it does |
|---|---|
| `break` | Jumps out of the closest enclosing loop, past the entire loop statement |
| `continue` | Jumps to the top of the closest enclosing loop, to the loop's header line |
| `pass` | Does nothing at all. It is an empty statement placeholder |
| Loop `else` block | Runs if and only if the loop exits normally, without hitting a `break` |

### General loop format

With `break` and `continue` included, the `while` loop looks like this. Both can appear anywhere in the body. They usually sit inside an `if` test that reacts to some condition.

```
while test:
    statements
    if test: break        # Exit loop now, skip else if present
    if test: continue     # Go to test at top of loop now
else:
    statements            # Run on exit if didn't hit a 'break'
```

### pass

The `pass` statement does nothing. You use it when the syntax needs a statement, but you have nothing useful to say yet. It is often the body of a compound statement. An infinite loop that does nothing is one example.

```
while True: pass          # Type Ctrl+C to stop me!
```

Python gets stuck in this loop, because the body is an empty statement. In a way, `pass` is to statements what `None` is to objects. It is an explicit nothing. Here the body sits on the same line as the header, after the colon. That works only when the body is not a compound statement.

This program does nothing forever. It is not very useful, unless you want to warm up a laptop on a cold day. You will see `pass` in better places later. It can ignore exceptions caught by `try` statements. It can define empty classes that act like structs or records in other languages. It is also a way to stub out a function body for now.

```
def func1():
    pass                  # Add real code here later

def func2():
    pass
```

We cannot leave the body empty without a syntax error, so we write `pass` instead.

Python has a similar, more obscure option. An ellipsis, written as `...`, can appear anywhere an expression can. It is three plain dots, not the single Unicode ellipsis character. An ellipsis does nothing by itself. So it can stand in for `pass`, especially for code you plan to fill in later.

```
def func1():
    ...                   # Alternative to pass

func1()                   # Does nothing if called
```

This works because any expression can appear as a statement, and `...` is an expression. An ellipsis can also sit on the header line by itself. It can start a name when no specific type is needed, which makes it an alternative to `None`.

```
def func1(): ...          # Works on same line too
```

```
>>> tbd = ...             # Alternative to both pass and None
>>> tbd                   # Ellipsis is a real (if oddball!) thing
Ellipsis
```

The ellipsis goes well beyond its original role in slicing extensions, where Python itself does not use it. Time will tell whether it can rival `pass` and `None` in these roles.

### continue

The `continue` statement jumps right back to the top of a loop. It is often used to avoid nesting. The next example uses `continue` to skip odd numbers. Only the even values from 8 down to 0 get printed. Zero counts as false in a test. The `%` operator gives the remainder of a division.

The loop counts down to 0 and skips every number that is not a multiple of 2. The output is `8 6 4 2 0`.

```
x = 10
while x:
    x -= 1                # Or, x = x - 1
    if x % 2 != 0: continue    # Odd? -- skip print
    print(x, end=' ')
```

Because `continue` jumps to the top, the `print` does not need an `if` around it. The `print` runs only when the `continue` is not reached.

Some readers see a resemblance to a "go to" statement from other languages. Python has no `go to`, but `continue` still moves control around. Many of the warnings about `go to` apply to it. Use `continue` sparingly, especially while you are learning. Here the same loop reads more clearly, with the `print` nested under the `if`.

```
x = 10
while x:
    x -= 1
    if x % 2 == 0:        # Even? -- print
        print(x, end=' ')
```

Exceptions can also act like a controlled "go to" later on. They can even break out of several nested loops at once, which `break` alone cannot do.

### break

The `break` statement exits a loop right away. When loops are nested, it exits only the closest enclosing loop. Code after `break` does not run when it is reached. So `break` can sometimes avoid nesting, much like `continue`. The next loop is a simple interactive one. It asks for a favorite language and stops when the user types `stop`.

```
num = 1
while True:
    tool = input(f'{num}) What\'s your favorite language? ')
    if tool == 'stop': break
    print('Bravo!' if tool == 'Python' else 'Try again...')
    num += 1
```

A session with this loop looks like this.

```
1) What's your favorite language? Java
Try again...
2) What's your favorite language? Python
Bravo!
3) What's your favorite language? stop
```

Because `break` ends the `while` immediately, there is no reason to nest the code below it in an `else`.

You can shorten this loop with the `:=` expression from the named assignment section above. The result is concise. It loses its role as a `break` demo, though. It may also look hard to read, so judge for yourself.

```
num = 1
while (tool := input(f'{num}) What\'s your favorite language? ')) != 'stop':
    print('Bravo!' if tool == 'Python' else 'Try again...')
    num += 1
```

Nesting `:=` inside another `:=`, as in the next example, is a different matter. This version is too wide to print on one line here. Unless you can defend it in front of your code reviewers, just say no.

```
num = 0
while (tool := input(f'{(num := num + 1)}) What\'s your favorite language? ')) != 'stop':
    print('Bravo!' if tool == 'Python' else 'Try again...')
```

A preview: `input` also raises an exception at end-of-file. That happens when a user presses Ctrl+Z on Windows or Ctrl+D on Unix. Wrapping `input` in a `try` statement lets a program handle that case too.

### Loop else

When you combine `break` with the loop `else` clause, you often avoid the search flags used in other languages. The `break` skips the `else` on the way out of the loop. This abstract outline shows the pattern.

```text
while continuing:
    if found:
        found code
        break
    else advance
else:
    not-found code
```

The next example checks whether a positive integer `num` is prime. A prime has no factors other than 1 and itself. The loop searches for factors greater than 1. Assign `num` before you paste this code into a live session.

```
x = num // 2              # For some num > 1, start at half
while x > 1:
    if num % x == 0:      # Remainder 0? Factor found
        print(num, 'has factor', x)
        break             # Exit now and skip else
    x -= 1
else:                     # Normal exit, when x reaches 1
    print(num, 'is prime')
```

Rather than setting a flag, this code inserts a `break` where a factor is found. The loop `else` can then assume it runs only when no factor is found. If the loop never hits the `break`, the number is prime. Trace through the code to see how this works.

The `else` also runs when the loop body never executes. In a `while` loop, that happens when the header test is false at the start. So this example still prints "is prime" when `x` starts at 1 or less, such as when `num` is 2.

A note on accuracy: this example finds primes only informally. The strict mathematical definition says numbers below 2 are not prime. This code classifies 1 and 0 as prime, though. It also fails for negative numbers, and it accepts floating-point numbers whose decimal digits are all zero. The code uses `//` instead of `/`, so the first division truncates the remainder. Wrapping it in a function is a good next step for reuse.

Why does the loop `else` exist? It is unique to Python, so it confuses many newcomers. Some people write it with no `break`. Others never learn it exists. In general, it gives explicit syntax for a common pattern. It catches the other way out of a loop, without setting and checking flags.

Suppose you search a list for a value, and you need to know afterward whether it was found. This sketch is abstract, and it leaves parts out. `x` stands for any sequence. `match` is a tester function you would define yourself.

```
found = False
while x and not found:
    if match(x[0]):       # Value at front?
        print('Found')
        found = True
    else:
        x = x[1:]         # Slice off front and repeat
if not found:
    print('Not found')
```

This code sets, then tests, a `found` flag. It is valid, and it works. But this is exactly the structure the loop `else` clause handles. Here is the `else` version.

```
while x:                  # Exit when x empty
    if match(x[0]):
        print('Found')
        break             # Exit, go around else
    x = x[1:]
else:
    print('Not found')    # Only here if exhausted x
```

This version is more concise. The flag is gone. The `else` lines up vertically with `while`. The `break` exits the loop and goes around the `else`. So the `else` becomes a structured way to catch the search-failure case.

You could replace the `else` with a test for an empty `x` after the loop, such as `if not x:`. In this example that works. But the `else` is explicit syntax for the pattern, and an empty test may not fit every case. The loop `else` is even more useful with `for`, because you do not control how sequence iteration ends.

## for loops

The `for` loop is a generic iterator. It steps through the items of any ordered sequence or other iterable object. That includes strings, lists, tuples, sets, dictionaries, and other built-in iterables. It also works with new objects you define with classes. You have already used `for` with sequences. This section looks at it more formally.

### General format

The `for` header names an assignment target and the object to step through. The header is followed by an indented block of statements that repeat.

```
for target in object:     # Assign object items to target
    statements            # Repeated loop body: use target
else:                     # Optional else
    statements            # Run if didn't exit loop body with break
```

Python assigns the items of the iterable to `target` one by one. It runs the loop body once for each item. The body usually uses the target like a cursor that steps along the sequence.

The target can be any assignment target. It is often a simple name. That name is a possibly new variable in the scope where the `for` statement is coded. You can even change it inside the body. Python still sets it to the next item when control returns to the top. After the loop, the name refers to the last item visited. That is the last item in the sequence, unless `break` ended the loop early.

The `for` loop's `else` works exactly as it does in a `while` loop. It runs if the loop finishes without a `break`, which means every item was visited. `break` and `continue` behave the same here. The complete format looks like this.

```
for target in object:     # Assign object items to target
    statements
    if test: break        # Exit loop now, skip else
    if test: continue     # Go to top of loop now
else:
    statements            # Run on exit if didn't hit a 'break'
```

### Examples

The next examples type a few `for` loops in the REPL, so you can see them in practice.

A `for` loop can step across any kind of sequence. The first example assigns `x` to each of three list items, from left to right. The `print` runs once per item. Inside the body, `x` refers to the current item.

```
for x in ['app', 'script', 'program']:
    print(x, end=' ')
```

The output is `app script program`.

The next two examples add and multiply the items of a list. Later you will see tools that apply `+` and `*` to list items automatically. A `for` loop is often just as easy.

```
>>> sum = 0
>>> for x in [1, 2, 3, 4]:
...     sum = sum + x
>>> sum
10
>>> prod = 1
>>> for item in [1, 2, 3, 4]: prod *= item
>>> prod
24
```

Any sequence works in a `for`, since it is a generic tool. Strings and tuples work too.

```
>>> S = 'Python'
>>> T = ('web', 'num', 'app')
>>> for x in S: print(x, end=' ')     # Iterate over a string
P y t h o n
>>> for x in T: print(x, end=' ')     # Iterate over a tuple
web num app
```

Some objects that are not sequences also work in a `for`, including files. The iterable behavior behind this gets a full treatment later.

#### Tuple assignment in for loops

If you iterate through a sequence of tuples, the loop target can be a tuple of targets. This is the tuple-unpacking assignment from the assignments section above, at work. The `for` loop assigns each item to the target, and assignment works the same everywhere.

```
>>> T = [(1, 2), (3, 4), (5, 6)]
>>> for (a, b) in T:                  # Tuple assignment at work
...     print(a, b)
1 2
3 4
5 6
```

The first time through, the loop acts like `(a,b) = (1,2)`. The second time it acts like `(a,b) = (3,4)`, and so on. The net effect is to unpack the current tuple on each pass. A list works as a target too, because tuple and list assignment are both sequence assignment. The parentheses around a tuple are optional. So `for [a, b] in T:` and `for a, b in T:` have the same effect.

This list-of-tuples format is common. It pairs well with `zip`, which you will meet below. It also shows up with SQL databases in Python. Query results come back as sequences of sequences. The outer list is the table, the nested tuples are its rows, and tuple assignment extracts the columns.

Tuples in `for` loops also help with dictionaries. The `items` method gives you keys and values together. You do not need to loop over the keys and index each one to fetch its value.

```
>>> D = {'a': 1, 'b': 2}
>>> for key in D:
...     print(key, '=>', D[key])      # Use dict keys iterator and index
a => 1
b => 2
>>> list(D.items())
[('a', 1), ('b', 2)]
>>> for (key, value) in D.items():
...     print(key, '=>', value)       # Iterate over both keys and values
a => 1
b => 2
```

Tuple assignment in a `for` is not a special case. Any assignment target works after the word `for`. You can always assign manually inside the loop to unpack the values.

```
>>> T
[(1, 2), (3, 4), (5, 6)]
>>> for both in T:
...     a, b = both                   # Manual assignment equivalent
...     print(a, b)
1 2
3 4
5 6
```

The tuple form in the header saves a step when you iterate through sequences of sequences. Nested structures unpack the same way.

```
>>> ((a, b), c) = ((1, 2), 3)         # Nested sequences work too
>>> a, b, c
(1, 2, 3)
>>> for ((a, b), c) in [((1, 2), 3), ((4, 5), 6)]: print(a, b, c)
1 2 3
4 5 6
```

This is not a special case either. The loop runs the same kind of assignment on each pass. Any nested sequence can be unpacked this way, because sequence assignment is generic.

```
>>> for ((a, b), c) in [([1, 2], 3), ['XY', 6]]: print(a, b, c)
1 2 3
X Y 6
```

#### Starred targets in for loops

The loop variable can be any assignment target. So the starred names of extended unpacking also work here. They can pull out items and sections of sequences inside sequences. This works because the same syntax works in assignment statements.

Tuple assignment runs on each pass, just like a simple assignment statement.

```
>>> a, b, c = (1, 2, 3)
>>> a, b, c
(1, 2, 3)
>>> for (a, b, c) in [(1, 2, 3), (4, 5, 6)]:
...     print(a, b, c)
1 2 3
4 5 6
```

A starred target collects several items into a list. The same syntax then pulls parts out of nested sequences.

```
>>> a, *b, c = (1, 2, 3, 4)
>>> a, b, c
(1, [2, 3], 4)
>>> for (a, *b, c) in [(1, 2, 3, 4), (5, 6, 7, 8)]:
...     print(a, b, c)
1 [2, 3] 4
5 [6, 7] 8
```

In practice, you might use this to pick several columns from rows of data. Slicing can do the same job. The difference is the type of the result. A slice returns the sequence type you sliced. A starred target always receives a list.

```
>>> for all in [(1, 2, 3, 4), (5, 6, 7, 8)]:    # Manual slicing version
...     a, b, c = all[0], all[1:-1], all[-1]
...     print(a, b, c)
1 (2, 3) 4
5 (6, 7) 8
```

Every starred-target form works in a `for`, as it does in `=` assignment. That includes nested sequences, indexes, and slices. Code this intricate is rare, though.

```
>>> L, M = [1, 2], [3, 4]
>>> pairs = [[(5, 6), (7, 8), (9, 10)]] * 2
>>> for [(a, *X), (b, *L[0]), (c, *M[:0])] in pairs:
...     print(f'<{a=} {X=}> <{b=} {L=}> <{c=} {M=}>')
<a=5 X=[6]> <b=7 L=[[8], 2]> <c=9 M=[10, 3, 4]>
<a=5 X=[6]> <b=7 L=[[8], 2]> <c=9 M=[10, 10, 3, 4]>
```

#### Nested for loops

The next loops are a bit more involved. The first shows nested `for` loops. The inner loop runs for every iteration of the outer loop. The `+` in the inner loop combines the current items from both loops.

```
>>> for x in 'abc':                          # For each item in one string
...     for y in '123':                      # And for each item in another string
...         print(x + y, end=' ')           # Concatenate current items from both
a1 a2 a3 b1 b2 b3 c1 c2 c3
```

The next example adds a third level of nesting and a loop `else`. Given a list of objects, `items`, and a list of keys, `tests`, it searches for each key and reports the result.

```
>>> items = ['aaa', 111, (4, 5), 2.01]       # A list of objects
>>> tests = [(4, 5), 3.14]                   # Keys to search for
>>>
>>> for key in tests:                        # For all keys
...     for item in items:                   # For all items
...         if item == key:                  # Check for match
...             print(key, 'was found')
...             break
...     else:
...         print(key, 'not found!')
(4, 5) was found
3.14 not found!
```

The `break` runs when a match is found. So if the inner loop's `else` runs, the search failed. Two loops run at the same time here. The outer loop scans the keys, and the inner loop scans the items for each key. The inner `else` lines up with the inner `for` header, so it belongs to that loop. It does not belong to the `if` or the outer loop.

The `in` operator can simplify this. It scans an object for a match, so it replaces the inner loop.

```
>>> for key in tests:                        # For all keys
...     if key in items:                     # Let Python check for a match
...         print(key, 'was found')
...     else:
...         print(key, 'not found!')
(4, 5) was found
3.14 not found!
```

In general, let Python do as much of the work as it can. That helps both brevity and performance.

The final example builds a list as it goes, for later use. It collects the common items in two sequences. This is nearly an intersection, unless the sequences contain duplicate values. After the loop, `res` refers to a list of every item found in both `seq1` and `seq2`.

```
>>> seq1 = 'trippy'
>>> seq2 = 'python'
>>>
>>> res = []                                 # Start empty
>>> for x in seq1:                           # Scan first sequence
...     if x in seq2:                        # Common item?
...         res.append(x)                    # Add to result end
>>> res
['t', 'p', 'p', 'y']
```

This code works only on the two specific variables, `seq1` and `seq2`. It would be better as a tool you can use again and again. That idea leads to functions, which come later.

Python also has sets. The `&` operator on sets gives a real intersection. The catch is that order is lost, duplicates vanish, and you need extra conversions to line things up.

```
>>> list(set(seq1) & set(seq2))              # Real intersection with sets
['p', 'y', 't']
```

The loop above is also a classic list comprehension pattern. It collects a results list with an iteration and an optional filter test. A comprehension can express that more concisely.

```
>>> [x for x in seq1 if x in seq2]           # Let Python collect results
['t', 'p', 'p', 'y']
```

Comprehensions get a full treatment later in this handbook.

## Loop coding techniques

The `for` loop covers most counter-style loops. It is simpler to write and often quicker to run than a `while`. So reach for `for` first whenever you need to step through a sequence or another iterable. Python programmers should avoid counting by hand when they can. Its iteration tools handle much of the bookkeeping that lower-level languages like C leave to you.

Some jobs need more specialized iteration. You might visit every second or third item, or change a list along the way. You might walk two sequences in parallel, or need the indexes too. You can always handle these with a `while` loop and manual indexing. Python also provides built-ins that let a `for` loop handle them.

- The built-in `range` function produces a series of successively higher integers. You can use them as indexes in a `for`.
- The built-in `zip` function returns a series of parallel-item tuples. You can use them to traverse multiple sequences in a `for`.
- The built-in `enumerate` function generates both the values and the indexes of items. You do not need to count manually.

Because `for` loops often run faster than counter-based `while` loops, use these tools whenever you can. Each one below has a common role. Some loop-coding alternatives are better than others.

### Counter loops with range

The `range` function is a general tool. You can call it anywhere you need a series of integers, not only for indexes. It generates items on demand. So you wrap it in `list` to display all of its results at once in the REPL. Its results support some sequence operations, but not all.

```
>>> list(range(5)), list(range(2, 5)), list(range(0, 10, 2))
([0, 1, 2, 3, 4], [2, 3, 4], [0, 2, 4, 6, 8])
>>> range(5)[2], range(5)[1:3], list(range(5)) + [6, 7]
(2, range(1, 3), [0, 1, 2, 3, 4, 6, 7])
>>> range(5) + [6, 7]
TypeError: unsupported operand type(s) for +: 'range' and 'list'
```

With one argument, `range` generates integers from zero up to, but not including, that value. With two arguments, the first is the lower bound. An optional third argument sets a step, which defaults to +1. A range can also be negative or count downward.

```
>>> list(range(-5, 5))
[-5, -4, -3, -2, -1, 0, 1, 2, 3, 4]
>>> list(range(5, -5, -1))
[5, 4, 3, 2, 1, 0, -1, -2, -3, -4]
```

Python 2 had an optimized built-in named `xrange`. It did not build a full result list in memory. Python 3 later replaced it with the on-demand behavior of `range`. The Python 3 docs then classified `range` as a sequence type, which can be confusing. The upshot is that today's `range` uses little space, because it produces numbers only when asked.

A `range` is handy for repeating an action a set number of times. To print three lines, use `range` to generate the right number of integers.

```
>>> for i in range(3):
...     print(i, 'Pythons')
0 Pythons
1 Pythons
2 Pythons
```

A `for` loop pulls results from `range` automatically, so you do not need a `list` wrapper. In fact, you should not add one. Producing results one at a time takes far less memory than building them all up front.

### Sequence scans with while, range, and for

The `range` function can step through a sequence indirectly. It is often not the best approach for that job. The easiest and fastest way to visit every item is a simple `for`. Python handles most of the details in quick internal code.

```
>>> X = 'hack'
>>> for item in X: print(item, end=' ')      # Automatic iteration with for
h a c k
```

The `for` loop manages the iteration on its own. If you need to take over the indexing yourself, a `while` loop does it.

```
>>> i = 0
>>> while i < len(X):                        # Manual iteration with while
...     print(X[i], end=' ')
...     i += 1
h a c k
>>> i = -1
>>> while (i := i + 1) < len(X):             # Manual, but with := operator
...     print(X[i], end=' ')
h a c k
```

You can also index by hand with a `for`, using `range` to produce indexes. It takes several steps. You ask for the `range` of the subject's `len`. That gives you offsets, not the items at those offsets.

```
>>> X
'hack'
>>> len(X)                                   # Length of string
4
>>> list(range(len(X)))                      # All legal offsets into X
[0, 1, 2, 3]
>>>
>>> for i in range(len(X)): print(X[i], end=' ')    # Manual range/len iteration
h a c k
```

Because this loop walks offsets, not items, it must index back into `X` to fetch each item. If that feels like overkill, it is. This example has no real need for it.

The `range` and `len` combination has its uses. It is still rarely the best option. It can run slower, and it needs more code. Unless you have a special indexing need, use the simple `for` form.

```
>>> for item in X: print(item, end=' ')      # Use auto iteration if you can
```

As a rule of thumb, prefer `for` over `while` when you can. Keep `range` calls in `for` loops for the rare cases where nothing else fits. The simple form usually wins. Rules of thumb have exceptions, and the next section shows one.

### Sequence shufflers with range and len

The `range` and `len` pattern is not ideal for simple scans. It does allow more specialized traversals, though. Some algorithms reorder sequences. They generate alternatives in searches, or test the effect of different value orders. These jobs need offsets to pull a sequence apart and put it back together. In the code below, `range` gives a repeat count in the first loop and a position for slicing in the second.

```
>>> S = 'hack'
>>> for i in range(len(S)):                  # For repeat counts 0..3
...     S = S[1:] + S[:1]                    # Move front item to end
...     print(S, end=' ')
ackh ckha khac hack
>>> S
'hack'
>>> for i in range(len(S)):                  # For positions 0..3
...     X = S[i:] + S[:i]                    # Rear part + front part
...     print(X, end=' ')
hack ackh ckha khac
```

Trace these one iteration at a time if they seem confusing. The second loop creates the same results as the first, in a different order. It does not change the original variable as it goes. Both loops slice to get the parts they concatenate. So they work on any sequence type. Shuffling a list gives you reordered lists.

```
>>> L = [1, 2, 3, 4]
>>> for i in range(len(L)):
...     X = L[i:] + L[:i]                    # Works on any sequence type
...     print(X, end=' ')
[1, 2, 3, 4] [2, 3, 4, 1] [3, 4, 1, 2] [4, 1, 2, 3]
```

The results of `range` itself do not work here. They are not true sequences.

```
>>> L = range(4)
>>> …same code as prior example…
TypeError: unsupported operand type(s) for +: 'range' and 'range'
```

You will use code like this to test functions with different argument orders. The same idea extends to generators and full permutations. It is a widely useful tool.

### Skipping items with range and slices

The previous section showed one valid use of the `range` and `len` combination. You can also use it to skip items as you go.

```
>>> S = 'abcdefghijk'
>>> list(range(0, len(S), 2))
[0, 2, 4, 6, 8, 10]
>>> for i in range(0, len(S), 2): print(S[i], end=' ')
a c e g i k
```

This visits every second item in `S`, walking the offsets that `range` generates. For every third item, set the third argument to `3`. With `range`, you can skip items and still keep the simplicity of the `for` statement.

In most cases, though, this is not the best practice in Python today. If you mean to skip items, the extended three-limit form of the slice expression is simpler. To visit every second character in `S`, slice with a stride of 2.

```
>>> S = 'abcdefghijk'
>>> for c in S[::2]: print(c, end=' ')
a c e g i k
```

The result is the same, and the slice is much easier to write and read. The one advantage of `range` here is space. Slicing makes a copy of the string, while `range` does not. For very large strings, that can save significant memory. Whether your program needs to care depends on what it does.

### Changing lists with range and comprehensions

Another place where you may use `range` with `len` is a loop that changes a list while it traverses the list. Suppose you need to add 1 to every item, such as when you update ages at year end. A simple `for` loop may not do what you expect.

```
>>> L = [10, 20, 30, 40, 50]
>>> for x in L:
...     x += 1                               # Changes x, not L!
>>> L                                        # L's objects unchanged
[10, 20, 30, 40, 50]
>>> x                                        # x is not a cursor into L
51
```

This does not work as hoped. The loop variable `x` changes, while the list `L` stays put. The explanation takes a little thought. On each pass, `x` refers to the next integer pulled out of the list. Adding to `x` with `+=` sets `x` to a different object. The list still holds the original value. The new value lives in separate memory, not in the list.

To change the list as you march across it, use indexes. Then you can assign an updated value to each position. `range` and `len` produce the indexes for you.

```
>>> L = [10, 20, 30, 40, 50]
>>> for i in range(len(L)):                  # Add one to each item in L
...     L[i] += 1                            # Or L[i] = L[i] + 1
>>> L
[11, 21, 31, 41, 51]
```

The list changes as the loop proceeds. A simple `for x in L` cannot do this, because it iterates through actual items, not their positions. What about the equivalent `while` loop? It needs more work from you. It may also run more slowly, depending on your Python and your device.

```
>>> i = 0
>>> while i < len(L):                        # And similar with := assignment
...     L[i] += 1
...     i += 1
>>> L
[12, 22, 32, 42, 52]
```

The `range` solution may not be ideal either. A list comprehension likely runs faster today, and it does similar work. It does not change the original list in place, though. You could assign its new list back to `L`, but that would not update other references to the original list.

```
>>> [x + 1 for x in L]
[13, 23, 33, 43, 53]
```

Comprehensions get a full treatment later in this handbook.

### Parallel traversals with zip

The `range` function lets a `for` walk sequences without covering all of them. The built-in `zip` function lets a `for` visit multiple sequences in parallel. The sequences are not visited at the same moment. They are walked during the same loop. `zip` takes one or more sequences or other iterables. It returns tuples that pair up the items at the same positions.

Suppose you have two lists of data that pair up by position.

```
>>> L1 = [1, 2, 3, 4]
>>> L2 = [5, 6, 7, 8]
```

`zip` is also an iterable, so you must wrap it in `list` to collect and display all of its results at once.

```
>>> zip(L1, L2)                              # An iterable that generates pairs
<zip object at 0x026523C8>
>>> list(zip(L1, L2))                        # list() required to see all results
[(1, 5), (2, 6), (3, 7), (4, 8)]
```

Paired with `for`, `zip` supports parallel iteration.

```
>>> for (x, y) in zip(L1, L2):
...     print(f'{x} + {y} => {x + y}')
1 + 5 => 6
2 + 6 => 8
3 + 7 => 10
4 + 8 => 12
```

The loop steps over the pairs that `zip` pulls from the two lists. It uses tuple assignment to unpack each pair. The first time through, it acts like `(x, y) = (1, 5)`, and so on. So the loop scans both `L1` and `L2` at once.

A `while` loop with manual indexing gives the same output. It needs noticeably more code. So it likely runs slower than the `for` and `zip` version.

```
>>> i = -1
>>> while (i := i + 1) < len(L1):
...     print(f'{L1[i]} + {L2[i]} => {L1[i] + L2[i]}')
```

Memory is no better with `while`. `zip` makes just one pair per loop, so it does not consume memory needlessly. The bigger difference is that this `while` version is not truly equivalent to `zip`. The next section explains why.

### More on zip: size and truncation

The `zip` function is more general than the last example suggests. It accepts any iterable object, including `range` results and input files.

```
>>> list(zip(range(4), 'hack'))
[(0, 'h'), (1, 'a'), (2, 'c'), (3, 'k')]
```

`zip` is not limited to pairs, either. It accepts any number of arguments, of any size. This example builds a list of three-item tuples from three arguments. It takes items column by column.

```
>>> T1, T2, T3 = (1, 2, 3), (4, 5, 6), (7, 8, 9)
>>> T3
(7, 8, 9)
>>> list(zip(T1, T2, T3))                    # 3 args of 3 vals => 3 3-item tuples
[(1, 4, 7), (2, 5, 8), (3, 6, 9)]
```

Formally, for N arguments that each contain M items, `zip` gives an M-long series of N-item tuples.

```
>>> list(zip(T1, T2))                        # 2 args of 3 vals => 3 2-item tuples
[(1, 4), (2, 5), (3, 6)]
```

When argument lengths differ, `zip` truncates the results at the length of the shortest sequence. The next example zips two strings to pick out characters in parallel. The result has only as many tuples as the shortest string has items.

```
>>> S1 = 'abc'
>>> S2 = 'xyz123'
>>>
>>> list(zip(S1, S2))                        # Truncates at len(shortest)
[('a', 'x'), ('b', 'y'), ('c', 'z')]
```

Formally, the count is the minimum of the arguments' lengths. To pad the results instead of truncating them, you must write loop code that pads them yourself. A later section shows how, once more iteration concepts are in place.

### More zip roles: dictionaries

Parallel traversals with `zip` also help build dictionaries. You can make a dictionary by calling `dict`, by assigning keys over time, or with a literal.

```
>>> D1 = {'app': 1, 'script': 3, 'program': 5}     # Or dict(key=value,…)
>>> D1
{'app': 1, 'script': 3, 'program': 5}
```

What if your program gets keys and values only at run time? A user, a file, or another dynamic source might supply them.

```
>>> keys = ['app', 'script', 'program']
>>> vals = [1, 3, 5]
```

One way to build a dictionary from these is to `zip` the lists. Then step through them in parallel with a `for` loop.

```
>>> list(zip(keys, vals))
[('app', 1), ('script', 3), ('program', 5)]
>>> D2 = {}
>>> for (k, v) in zip(keys, vals): D2[k] = v
>>> D2
{'app': 1, 'script': 3, 'program': 5}
```

You can skip the `for` loop in this case. Pass the zipped keys and values to the built-in `dict` constructor.

```
>>> D3 = dict(zip(keys, vals))
>>> D3
{'app': 1, 'script': 3, 'program': 5}
```

The name `dict` is really a type name. Calling it constructs a dictionary, and here it also converts the pairs into one. Dictionary comprehensions are another option for zipped key and value pairs. They are an alternative to both the `for` statement and `dict`.

```
>>> {k: v for (k, v) in zip(keys, vals)}
{'app': 1, 'script': 3, 'program': 5}
```

### Offsets and items with enumerate

The `range` function gives offsets, not the items at those offsets. Sometimes you need both. You need the item to use, plus its offset as you go. You can code this with a `for` loop that keeps a counter of the current offset.

```
>>> S = 'hack'
>>> offset = 0
>>> for item in S:
...     print(item, 'appears at offset', offset)
...     offset += 1
h appears at offset 0
a appears at offset 1
c appears at offset 2
k appears at offset 3
```

This works, but Python has a built-in named `enumerate` that does the job for you. It gives a loop a counter for free. You keep the simplicity of automatic iteration.

```
>>> S = 'hack'
>>> for (offset, item) in enumerate(S):
...     print(item, 'appears at offset', offset)
h appears at offset 0
a appears at offset 1
c appears at offset 2
k appears at offset 3
```

The result of `enumerate` is an iterable. It supports the iteration protocol, which is covered later. In short, it has a method that the `next` built-in calls. Each call returns an `(index, value)` tuple. The `for` loop steps through these tuples and unpacks them, just as it did with `zip`.

```
>>> E = enumerate(S)
>>> E
<enumerate object at 0x10ebd7880>
>>> next(E)
(0, 'h')
>>> next(E)
(1, 'a')
>>> next(E)
(2, 'c')
```

You rarely see this machinery, because every iteration context runs the protocol automatically. That includes list comprehensions.

```
>>> [c * i for (i, c) in enumerate(S)]
['', 'a', 'cc', 'kkk']
>>> for (ix, line) in enumerate(open('data.txt')):
...     print(f'{ix}) {line.rstrip()}')
0) Testing file IO
1) Learning Python, 6E
2) Python 3.12
```

To fully understand `enumerate` and comprehensions, you need the deeper look that comes later.

## Why you will care: file scanners

Loops show up wherever a job has to run again and again. Text files hold many characters and lines, so they suit loops well. When a file is small enough for memory, the file object's `read` method can pull the whole thing in at once.

```
file = open('data.txt')       # Read contents into a string all at once
print(file.read())
```

For more granular access, scan by characters. The second option below does not load the whole file. It also uses the `:=` named assignment from earlier.

```
for char in open('data.txt').read():
    print(char, end='')
file = open('data.txt')
while char := file.read(1):   # Read by character, empty means end-of-file
    print(char, end='')       # Don't add a \n after each character
```

To read by lines or blocks instead, use `while` loops like these. Binary data is often read by blocks in binary mode, `'rb'`. Text should use text mode, so character bytes are not split.

```
file = open('data.txt')
while line := file.readline():     # Read line by line
    print(line.rstrip())           # Line already has a \n newline
file = open('data.txt')
while chunk := file.read(10):      # Read block by block: up to 10 characters
    print(chunk, end='')           # Keep but don't add newlines
```

To read text files by line, though, the `for` loop is usually easiest to write. It may also run fastest.

```
for line in open('data.txt').readlines():
    print(line.rstrip())
for line in open('data.txt'):      # Use iterators: best for text input (maybe)
    print(line.rstrip())
```

The first version calls the file `readlines` method. It loads the whole file into a list of line strings. The second relies on file iterators, which read one line on each pass. The second version is generally best for text. It is simple, and it works for very large files, because it never loads the entire file into memory. Speed can vary by Python release, so time your code if it matters.

The `readlines` call still has uses. To reverse a file's lines, for example, the file's contents must fit in memory. The `reversed` built-in works on sequences. It does not accept iterables that generate values. `sorted` does accept them. So it can order all the lines in a file without loading the whole file.

```
for line in reversed(open('data.txt').readlines()):
    print(line.rstrip())
for line in sorted(open('data.txt')):
    print(line.rstrip())
```

Python's documentation covers the file calls used here. It also covers `os.popen`. By default, that returns a file object connected to a shell command's output, and that file object supports the same kind of loops.

## The iteration protocol

The `for` loop does not care what kind of collection it steps through. It works on any iterable object. That idea reaches well beyond loops. Comprehensions, `in` membership tests, and the `zip`, `enumerate`, and `map` built-in functions all scan objects from left to right in the same way. Even dictionaries work, although they are not sequences.

```python
>>> for k in dict(a=1, b=2, c=3): print(k, end=' ')
a b c
```

An iterable is a generalization of a sequence. An object counts as iterable if it is a stored sequence. It also counts if it produces one result at a time during an iteration. Those results can be computed on demand. This saves memory and avoids delays, because nothing is built all at once.

Virtual iterables are not true sequences, though. They do not support every operation that lists and tuples do. They only hand out values over time, when something asks for them. Whether an object is physical or virtual, it announces iteration support by implementing the iteration protocol. That protocol is a set of callable methods that all iteration tools use.

### Iterables and iterators

Python sometimes uses the words iterable and iterator interchangeably. That can be confusing. In this handbook, an iterable is an object with the `__iter__` method at the top of the protocol. An iterator is an object with the `__next__` method that produces results. An iterable returns an iterator, and the iterator advances on each `next` call.

The phrase iteration tool means any language feature that runs an iteration. A `for` loop and a `zip` call are both iteration tools.

### Reading a file one line at a time

Files show the protocol clearly. Suppose `data.txt` holds three lines of text. The `readline` method reads one line on each call. At the end of the file, it returns an empty string. An empty string is false, so a loop can stop on it.

```python
>>> f = open('data.txt')
>>> f.readline()
'Testing file IO\n'
>>> f.readline()
'Learning Python, 6E\n'
>>> f.readline()
'Python 3.12\n'
>>> f.readline()
''
```

Files also have a `__next__` method that does nearly the same job. The one difference is what happens at the end. Instead of returning an empty string, `__next__` raises a `StopIteration` exception.

```python
>>> f = open('data.txt')
>>> f.__next__()
'Testing file IO\n'
>>> f.__next__()
'Learning Python, 6E\n'
>>> f.__next__()
'Python 3.12\n'
>>> f.__next__()
Traceback (most recent call last):
StopIteration
```

Any object with a `__next__` method that raises `StopIteration` at the end counts as an iterator. Every iteration tool calls `__next__` on each pass. It catches `StopIteration` to learn when to stop. A file is its own iterator, so the initial `iter` step is optional for files.

### Letting the for loop read the file

The best way to read a text file line by line is to skip explicit reads. Let the `for` loop call `__next__` for you. The file iterator loads one line at a time, so the code stays short and efficient.

```python
>>> for line in open('data.txt'):
...     print(line.upper(), end='')
TESTING FILE IO
LEARNING PYTHON, 6E
PYTHON 3.12
```

The `end=''` argument stops `print` from adding another newline. Each line string already ends with `\n`. Without `end=''`, the output would be double-spaced.

Older code often loads every line first with the `readlines` method. That still runs, but it is not the best practice now. It loads the whole file into memory at once. A file larger than available memory will fail that way. The iterator version reads one line at a time, so memory use stays low.

A `while` loop can also read line by line, using the `:=` named assignment.

```python
>>> f = open('data.txt')
>>> while line := f.readline():
...     print(line.upper(), end='')
TESTING FILE IO
LEARNING PYTHON, 6E
PYTHON 3.12
```

This version usually runs slower than the iterator. File iterators run at C-language speed inside standard CPython. The `while` version runs Python bytecode through the Python virtual machine. Trading Python code for C code tends to raise speed. Speed is not an absolute rule, though, so measure before you decide.

Timing results from CPython 3.12 on macOS show the order. The test used `min(timeit.repeat(code, repeat=50, number=10))` on a 9k-line file, with `pass` as each loop body. The iterator took 0.0073 seconds. The `readlines` version took 0.0077 seconds. The `while` loop took 0.0102 seconds. Without `:=`, the `while` loop took 0.0104 seconds. Your numbers will vary, and memory use matters too. A gap of 0.0029 seconds may not matter in many programs.

### The iter and next built-ins

To simplify manual iteration, Python provides a built-in function named `next`. The call `next(X)` does the same thing as `X.__next__()`. It is simpler to type and read. It also runs slightly faster in CPython 3.12 for the cases tested.

```python
>>> f = open('data.txt')
>>> f.__next__()
'Testing file IO\n'
>>> next(f)
'Learning Python, 6E\n'
>>> next(f)
'Python 3.12\n'
```

The `for` loop also needs an iterator first. It calls the iterable's `__iter__` method to get one. The `iter` built-in runs the same step for you. The returned object then supplies `__next__`.

```python
>>> f = open('data.txt')
>>> I = iter(f)
>>> next(I)
'Testing file IO\n'
>>> next(I)
'Learning Python, 6E\n'
```

### The full iteration protocol

The full protocol involves two objects, used in two steps. The first is the iterable being scanned. Calling its `__iter__` method returns an iterator, just as `iter` does. The second is the iterator. Calling its `__next__` method produces results. It raises `StopIteration` when no results remain, just as `next` does.

Iteration tools run these steps automatically. In some cases a single object plays both roles, as with files, which support just one scan. The iterator is often a temporary object that the tool creates and uses internally.

For a list, the steps are visible when you call them yourself.

```python
>>> L = [1, 2]
>>> I = iter(L)
>>> next(I)
1
>>> next(I)
2
>>> next(I)
StopIteration
```

Some objects are both an iteration tool and an iterable. The `enumerate` and `zip` built-ins are examples. They already avoid building result lists in memory. Applying them to other iterables saves even more space. No work happens until an iteration tool asks for results.

Files are their own iterators, while lists are not. You can check this with `is`, which tests object identity.

```python
>>> f = open('data.txt')
>>> iter(f) is f
True
>>> iter(f) is f.__iter__()
True
>>> L = [1, 2, 3]
>>> iter(L) is L
False
>>> next(L)
TypeError: 'list' object is not an iterator
```

Lists and many other built-in objects support multiple open scans at once. Nested loops may each sit at a different position in the same list. For such objects, call `iter` to start a manual scan.

### Manual iteration

Python iteration tools call these functions for you. You can also apply the protocol yourself when needed. The next example shows that a `for` loop and a manual loop give the same result.

```python
L = [1, 2, 3]
for X in L:
    print(X ** 2, end=' ')

I = iter(L)
while True:
    try:
        X = next(I)
    except StopIteration:
        break
    print(X ** 2, end=' ')
```

Both loops print `1 4 9`. The second loop does by hand what the `for` loop does automatically. It gets an iterator with `iter`, calls `next` on each pass, and catches the stop signal.

A `try` statement runs an action and catches any exception raised while it runs. Exceptions get a fuller treatment later in the book. The `for` loop runs the internal equivalent of `__next__`, not `next`, but the effect is the same.

For user-defined classes, a `for` loop may index the object repeatedly instead of running the protocol. It prefers the protocol when the object supports it. The later chapter on operator overloading returns to this story.

### next with a default value

The `next` built-in takes an optional second argument. If you pass one, Python returns that value at the end instead of raising a stop exception.

```python
>>> L = [1]
>>> I = iter(L)
>>> next(I, 'end of list')
1
>>> next(I, 'end of list')
'end of list'
```

Combined with `:=`, this default shortens manual loops. The catch is that it fails if the default can also be a real value. The following example assumes that `None` is safe to use.

```python
>>> I = iter(L)
>>> while (X := next(I, None)) != None:
...     print(X ** 2, end=' ')
```

The `iter` built-in can also take a second argument, a sentinel value. The call then reads from a function until the function returns the sentinel. This is a tricky way to read a file in blocks with a `for` loop. It needs `lambda`, which you will meet later.

```python
>>> f = open('data.txt')
>>> I = iter(lambda: f.read(5), '')
>>> for block in I: print(block, end='')
```

Python's documentation covers more modes of `next` and `iter`.

## Other built-in iterables

### Dictionaries, range, enumerate, and zip

A `for` loop is the usual way to step through a dictionary's keys. Dictionaries are implicitly iterable. Their iterator returns one key at a time.

```python
>>> D = dict(a=1, b=2)
>>> for key in D:
...     print(key, D[key])
a 1
b 2
>>> I = iter(D)
>>> next(I)
'a'
>>> next(I)
'b'
```

The iteration protocol also explains why `range` results need a `list` call before you can see their values in a REPL. A `range` object produces values one at a time.

```python
>>> R = range(5)
>>> R
range(0, 5)
>>> I = iter(R)
>>> next(I)
0
>>> next(I)
1
>>> list(range(5))
[0, 1, 2, 3, 4]
```

The `list` call is not needed inside a `for` loop, where iteration happens automatically. Avoid it there. Use it when you want to display all values at once, or when you need list behavior or several scans.

The `enumerate` built-in is also an iterable. Its result is its own iterator, like a file. That means `iter` is optional, and it supports just one scan per call.

```python
>>> E = enumerate('text')
>>> iter(E) is E
True
>>> next(E)
(0, 't')
>>> list(enumerate('text'))
[(0, 't'), (1, 'e'), (2, 'x'), (3, 't')]
```

The `zip` built-in works the same way. Like `enumerate`, `zip` is its own iterator. Call it again to iterate again.

```python
>>> Z = zip((1, 2, 3), (10, 20, 30))
>>> I = iter(Z)
>>> next(I)
(1, 10)
>>> next(I)
(2, 20)
>>> I is Z
True
>>> list(Z)
[(3, 30)]
>>> list(zip((1, 2, 3), (10, 20, 30)))
[(1, 10), (2, 20), (3, 30)]
```

### Iterator nesting

The `zip` built-in is both an iteration tool and an iterable. It consumes results from its arguments. It also returns an iterable with an iterator for its own results. In the next example, `zip` receives results from two `range` objects. Its own results come on demand too.

```python
>>> Z = zip(range(1, 4), range(10, 40))
>>> next(Z)
(1, 10)
>>> next(Z)
(2, 11)
>>> next(Z)
(3, 12)
>>> list(zip(range(1, 4), range(10, 40)))
[(1, 10), (2, 11), (3, 12)]
```

Iterators can nest as deep as needed. Because `enumerate` is both a tool and an object, `range`, `enumerate`, and `zip` can all produce results on demand. The `list` call starts the whole chain.

```python
>>> list(enumerate(range(1, 4)))
[(0, 1), (1, 2), (2, 3)]
>>> list(zip(enumerate(range(1, 4)), enumerate(range(5, 8))))
[((0, 1), (0, 5)), ((1, 2), (1, 6)), ((2, 3), (2, 7))]
```

The following example enumerates the zipped results of two ranges. It runs only when a `for` loop asks for results.

```python
>>> for x in enumerate(zip(range(1, 4), range(5, 8))): print(x)
(0, (1, 5))
(1, (2, 6))
(2, (3, 7))
```

Three levels of iterables defer their results here. Nothing happens until a tool such as `list` or `for` asks at the top. Each level then returns one result at a time. This keeps memory needs low and avoids long pauses.

### Functional iterables: map and filter

The `map` and `filter` built-ins also produce results one at a time. Like `enumerate` and `zip`, they are both iteration tools and iterable objects. They scan other iterables and make their own results on demand.

The `map` built-in calls a function for each item in an iterable. It returns the results as another iterable. In the next example, `map` applies the `ord` built-in to collect character code points.

```python
>>> ord('p')
112
>>> M = map(ord, 'py3')
>>> M
<map object at 0x101227550>
>>> next(M)
112
>>> next(M)
121
>>> next(M)
51
```

The `map` object supports no sequence operations, such as indexing with `[i]`. Call `list` if you need a real list. Call `map` again to scan again. A `for` loop calls `next` for you.

```python
>>> list(map(ord, 'py3'))
[112, 121, 51]
>>> M = map(ord, 'py3')
>>> for x in M: print(x, end=' ')
112 121 51
```

The `filter` built-in is similar. It returns the items for which a function returns `True`. A value is true if it is nonempty or nonzero. The `bool` built-in returns the truth value of one object. The `isdigit` method of `str` is true for all-digit text.

```python
>>> filter(bool, ['lp6e', '', 2024])
<filter object at 0x101227850>
>>> list(filter(bool, ['lp6e', '', 2024]))
['lp6e', 2024]
>>> list(filter(str.isdigit, ['lp6e', '2024']))
['2024']
```

Both tools call functions instead of evaluating expressions. Their full story waits until you learn functions. Their basic behavior is clear already. Both can be emulated roughly with list comprehensions, and more closely with generator expressions. Comprehensions come next.

```python
>>> [ord(x) for x in 'py3']
[112, 121, 51]
>>> [x for x in ['lp6e', '2024'] if x.isdigit()]
['2024']
```

### Multiple-pass versus single-pass iterables

Some iterables allow many scans. Others allow only one. The difference changes how you use them.

The `range` object, dictionaries, and lists are not their own iterators. You must make one with `iter` when you iterate manually. These objects support multiple iterators, and each iterator remembers its own position.

```python
>>> R = range(3)
>>> next(R)
TypeError: range object is not an iterator
>>> I1 = iter(R)
>>> next(I1)
0
>>> next(I1)
1
>>> I2 = iter(R)
>>> next(I2)
0
>>> next(I1)
2
```

The results of `enumerate`, `zip`, `map`, and `filter` are their own iterators. Files work the same way. None of these supports multiple active iterations on one result. The `iter` call is optional for them, though harmless. To start a fresh scan, call the tool again.

```python
>>> Z = zip((1, 2, 3), (10, 11, 12))
>>> I1 = iter(Z)
>>> I2 = iter(Z)
>>> next(I1)
(1, 10)
>>> next(I1)
(2, 11)
>>> next(I2)
(3, 12)
>>> M = map(ord, 'py3')
>>> I1, I2 = iter(M), iter(M)
>>> next(I1), next(I1)
(112, 121)
>>> next(I2)
51
>>> L = [0, 1, 2]
>>> I1, I2 = iter(L), iter(L)
>>> next(I1), next(I1)
(0, 1)
>>> next(I2)
0
```

Here the list supports several active scans at once, as `range` does. The `zip` and `map` objects share one position between their iterators. Classes you write later usually return a new object from `iter`, so each scan gets its own position. A single iterator usually returns itself and supports `next` directly. Generator functions and generator expressions behave like `map` and `zip` in this regard. They support just one active scan. Code that treats such single-pass iterators as lists may fail unless you convert them with `list` first.

### Standard-library iterables

Python's standard library adds more iterables. Shelves give access to stored objects by key. The results of `os.popen`, which reads the output of a shell command, are iterable too. You can process both with the full set of iteration tools. The `os.walk` directory walker is iterable as well. The details of that tool wait for the book's coverage of generators.

All of these implement the same `iter` and `next` interface. Loops run that machinery for you, so you rarely see it.

## Comprehensions

Comprehensions and `for` loops are the most common places the iteration protocol appears. Earlier, you changed a list with `range` and an index.

```python
>>> L = [1, 2, 3, 4, 5]
>>> for i in range(len(L)):
...     L[i] += 10
>>> L
[11, 12, 13, 14, 15]
```

This works, but it is not the best approach in Python. A list comprehension replaces this pattern with one expression that builds the result list.

```python
>>> L = [x + 10 for x in L]
>>> L
[21, 22, 23, 24, 25]
```

The result is similar, and the code is shorter. It is often twice as fast as the loop, as tested in CPython 3.12. A comprehension makes a new list object. That can matter if several names refer to the original list. For most code, the difference does not matter.

### List comprehension basics

List comprehensions appeared earlier in the handbook. Their syntax comes from set-theory notation, which applies an operation to each item in a set. You do not need set theory to use them. Most people read a list comprehension as a backward `for` loop.

Take the earlier example apart. The square brackets mean the result is a new list. The expression on the left is one you write. It uses a loop variable you name, such as `x + 10`. The part on the right is a `for` header. It names the loop variable and the iterable, as in `for x in L`.

Python runs the iteration across `L` inside the interpreter. It assigns `x` to each item in turn. It collects the result of the expression for each item. The result is a new list with `x + 10` for every `x` in `L`.

Comprehensions are never strictly required. You can always build the result list with a `for` loop and `append`.

```python
>>> res = []
>>> for x in L:
...     res.append(x + 10)
>>> res
[31, 32, 33, 34, 35]
```

A comprehension does exactly this internally, using internal equivalents. The comprehension is more concise, though. Building result lists is so common that the shorter form earns its place.

Comprehensions can also run faster than manual loops. Their iterations run at the speed of optimized, usually compiled, code inside the interpreter. Manual loops run as Python code. For larger data sets, this speed advantage can matter a great deal.

### List comprehensions and files

The `readlines` method loads a file into a list of line strings all at once. Each line keeps its newline character at the end.

```python
>>> f = open('data.txt')
>>> lines = f.readlines()
>>> lines
['Testing file IO\n', 'Learning Python, 6E\n', 'Python 3.12\n']
```

For many programs, the newline gets in the way. It causes double-spacing when you print. The `rstrip` method removes whitespace from the right side of a string. A `line[:-1]` slice also works, but only if every line ends with `\n`. That may not hold for the last line in a file.

```python
>>> lines = [line.rstrip() for line in lines]
>>> lines
['Testing file IO', 'Learning Python, 6E', 'Python 3.12']
```

A comprehension is an iteration tool, so you do not need to open the file ahead of time. Open it inside the expression. The comprehension reads one line at a time by calling the file's `__next__` handler. It runs each line through `rstrip` and adds the result to the list.

```python
>>> lines = [line.rstrip() for line in open('data.txt')]
>>> lines
['Testing file IO', 'Learning Python, 6E', 'Python 3.12']
```

This expression does a lot for you. Python scans the file line by line and builds the list of results. Most of the work runs inside the interpreter, so it is often faster than an equivalent `for` statement. It also uses the file iterator, so it never loads the whole file at once. For large files, that matters a lot.

You can run any string operation on each line. The following examples show the uppercase version from earlier, plus a few other operations.

```python
>>> [line.upper() for line in open('data.txt')]
['TESTING FILE IO\n', 'LEARNING PYTHON, 6E\n', 'PYTHON 3.12\n']
>>> [line.rstrip().upper() for line in open('data.txt')]
['TESTING FILE IO', 'LEARNING PYTHON, 6E', 'PYTHON 3.12']
>>> [line.split() for line in open('data.txt')]
[['Testing', 'file', 'IO'], ['Learning', 'Python,', '6E'], ['Python', '3.12']]
>>> [line.replace('\n', '!') for line in open('data.txt')]
['Testing file IO!', 'Learning Python, 6E!', 'Python 3.12!']
>>> [('Py' in line, line.split()[0]) for line in open('data.txt')]
[(False, 'Testing'), (True, 'Learning'), (True, 'Python')]
```

Method chaining works in the second example. String methods return new strings, so you can call another string method on the result. The last example collects several results for each line. It wraps them in a tuple.

In CPython, a file object closes itself when it is garbage-collected while still open. So these comprehensions close their temporary file once the expression finishes. Outside CPython, the file may stay open longer. If the code runs in a loop, open the file before the comprehension and close it after. Review the earlier file material for the close call.

### Extended list comprehension syntax

Comprehensions can do more than map one expression across items. They can filter items and nest loops. Together, these features form a small iteration mini-language.

#### Filter clauses: if

A comprehension's `for` part can have an `if` clause. The clause checks each item. If the test is false, the item is left out of the result. Strictly speaking, the clause filters items in. The result is the same.

Suppose you want only the lines that begin with the letter L or P. Imagine the first character is an action code. An `if` clause does the job.

```python
>>> lines = [line.rstrip() for line in open('data.txt') if line[0] in 'LP']
>>> lines
['Learning Python, 6E', 'Python 3.12']
```

The `if` checks the first character of each line. If it does not match, the line is skipped, and iteration continues. The equivalent `for` statement is longer, but easier to follow.

```python
>>> res = []
>>> for line in open('data.txt'):
...     if line[0] in 'LP':
...         res.append(line.rstrip())
>>> res
['Learning Python, 6E', 'Python 3.12']
```

Any list comprehension translates to a `for` statement by appending as you go. Indent each successive part one more level. The reverse is not always true. `for` statements handle roles that comprehensions do not address. Results collection is the common task comprehensions handle best.

A comprehension can also hold more logic. The next example keeps only lines that end in a digit. It uses `[-1:]` instead of `[-1]`, so blank lines do not cause an error after `rstrip`.

```python
>>> [line.rstrip() for line in open('data.txt') if line.rstrip()[-1:].isdigit()]
['Python 3.12']
```

Another `if` example counts lines. The first result gives the total number of lines in a text file. The second strips whitespace from both ends, so blank lines are left out of the count.

```python
>>> fname = 'data-blank-lines.txt'
>>> len(open(fname).readlines())
5
>>> len([line for line in open(fname) if line.strip() != ''])
3
```

#### Nested loops: for

A comprehension can have nested loops. Each `for` clause can have an optional `if` clause. The following example combines every character in one string with every character in another.

```python
>>> [x + y for x in 'abc' for y in '123']
['a1', 'a2', 'a3', 'b1', 'b2', 'b3', 'c1', 'c2', 'c3']
```

The statement form is easier to read, but it is slower. It builds the same list.

```python
>>> res = []
>>> for x in 'abc':
...     for y in '123':
...         res.append(x + y)
>>> res
['a1', 'a2', 'a3', 'b1', 'b2', 'b3', 'c1', 'c2', 'c3']
```

Past a certain point, a comprehension becomes too compact to be useful. Comprehensions suit simple iterations. For more involved work, a plain `for` statement is easier to understand and change. If a comprehension is hard for you to read, a `for` statement is probably the better choice.

### Comprehensions and the other forms

Comprehensions continue in the book's later chapter on functions, where their syntax is defined more formally. They are as closely related to functions as they are to loops. Several related forms share the same syntax. They differ in how they are written and what they produce.

```python
[x + 10 for x in L if x > 0]      # List comprehension
{x + 10 for x in L if x > 0}      # Set comprehension
{x: x + 10 for x in L if x > 0}   # Dictionary comprehension
(x + 10 for x in L if x > 0)      # Generator expression
```

The generator expression produces items on request, instead of building a list. The last three forms are used on files in the sections that follow.

Speed results vary. List comprehensions were consistently about twice as fast as corresponding `for` loops on most tests through CPython 3.12. Some tests show only a small gain. With `if` filter clauses, a comprehension may even be slower. Time your own code before you trust a speed claim.

## Iteration tools

Later in the book, you will see how user-defined classes can implement the iteration protocol too. Any tool that uses the protocol works on any built-in type or user-defined class that provides it. This section summarizes the tools that do.

So far, iterators have appeared mostly in `for` loops. But every built-in tool that scans collections from left to right uses the protocol. The `for` loop is one example.

```python
>>> for line in open('data.txt'):
...     print(line.upper(), end='')
TESTING FILE IO
LEARNING PYTHON, 6E
PYTHON 3.12
```

List comprehensions and the `map` built-in use the same protocol. When applied to a file, both use the file's iterator. They fetch an iterator with `__iter__` and call `__next__` each time through.

```python
>>> uppers = [line.upper() for line in open('data.txt')]
>>> uppers
['TESTING FILE IO\n', 'LEARNING PYTHON, 6E\n', 'PYTHON 3.12\n']
>>> list(map(str.upper, open('data.txt')))
['TESTING FILE IO\n', 'LEARNING PYTHON, 6E\n', 'PYTHON 3.12\n']
```

The `map` built-in applies a function call to each item in an iterable. It is like a list comprehension, but it requires a function instead of an arbitrary expression. It returns an iterable, so wrap it in `list` to get all values at once.

Other built-ins process iterables too. The `zip` built-in combines items from iterables. The `enumerate` built-in pairs each item with its position. The `filter` built-in selects items for which a function is true. The `sorted` built-in sorts items. The `functools.reduce` function runs pairs of items through a function. All of them accept iterables.

```python
>>> import functools, operator
>>> sorted(open('data.txt'))
['Learning Python, 6E\n', 'Python 3.12\n', 'Testing file IO\n']
>>> list(zip(range(99), open('data.txt')))
[(0, 'Testing file IO\n'), (1, 'Learning Python, 6E\n'), (2, 'Python 3.12\n')]
>>> list(enumerate(open('data.txt')))
[(0, 'Testing file IO\n'), (1, 'Learning Python, 6E\n'), (2, 'Python 3.12\n')]
>>> list(filter(bool, open('data.txt')))
['Testing file IO\n', 'Learning Python, 6E\n', 'Python 3.12\n']
>>> functools.reduce(operator.add, open('data.txt'))
'Testing file IO\nLearning Python, 6E\nPython 3.12\n'
```

The `filter` and `reduce` tools belong to functional programming, so their details wait. The point here is that they use the iteration protocol on files.

The `sorted` built-in returns a real list, not an iterable. It works like the `sort` method on lists. It returns a new sorted list, and it accepts any iterable. The `reversed` built-in returns an iterable, but it does not run the iteration protocol.

Nearly everything in the built-in toolset that scans objects uses the protocol. That includes the `list` and `tuple` built-ins, which build new objects from iterables. It also includes the string `join` method, which places a substring between the strings in an iterable.

```python
>>> list(open('data.txt'))
['Testing file IO\n', 'Learning Python, 6E\n', 'Python 3.12\n']
>>> tuple(open('data.txt'))
('Testing file IO\n', 'Learning Python, 6E\n', 'Python 3.12\n')
>>> '&&'.join(open('data.txt'))
'Testing file IO\n&&Learning Python, 6E\n&&Python 3.12\n'
```

Some syntax you might not expect also scans iterables. Sequence assignment, starred assignment, the `in` membership test, slice assignment, the list `extend` method, and single-star literal unpacking all use the protocol. Each one reads the file line by line.

```python
>>> a, b, c = open('data.txt')
>>> b, c
('Learning Python, 6E\n', 'Python 3.12\n')
>>> a, *b = open('data.txt')
>>> a, b
('Testing file IO\n', ['Learning Python, 6E\n', 'Python 3.12\n'])
>>> 'Python 2.7\n' in open('data.txt')
False
>>> 'Python 3.12\n' in open('data.txt')
True
>>> L = [11, 22, 33, 44]
>>> L[1:3] = open('data.txt')
>>> L
[11, 'Testing file IO\n', 'Learning Python, 6E\n', 'Python 3.12\n', 44]
>>> L = [11]
>>> L.extend(open('data.txt'))
>>> L
[11, 'Testing file IO\n', 'Learning Python, 6E\n', 'Python 3.12\n']
>>> L = [11, *open('data.txt'), 44]
>>> L
[11, 'Testing file IO\n', 'Learning Python, 6E\n', 'Python 3.12\n', 44]
```

The `extend` method iterates automatically, but `append` does not. Use `append` when you want to add an iterable as one item and iterate over it later.

```python
>>> L = [11]
>>> L.append(open('data.txt'))
>>> list(L[-1])
['Testing file IO\n', 'Learning Python, 6E\n', 'Python 3.12\n']
```

The `dict` built-in accepts a `zip` result, as shown earlier. The `set` built-in does too. So do the set and dictionary comprehensions.

```python
>>> set(open('data.txt'))
{'Python 3.12\n', 'Learning Python, 6E\n', 'Testing file IO\n'}
>>> {line for line in open('data.txt')}
{'Python 3.12\n', 'Learning Python, 6E\n', 'Testing file IO\n'}
>>> {ix: line for ix, line in enumerate(open('data.txt'))}
{0: 'Testing file IO\n', 1: 'Learning Python, 6E\n', 2: 'Python 3.12\n'}
```

Set and dictionary comprehensions also accept `if` tests. Both scan the file line by line and keep only the lines that begin with L or P. The comprehension syntax and the file iterator do most of the work.

```python
>>> {line for line in open('data.txt') if line[0] in 'LP'}
{'Python 3.12\n', 'Learning Python, 6E\n'}
>>> {ix: line for (ix, line) in enumerate(open('data.txt')) if line[0] in 'LP'}
{1: 'Learning Python, 6E\n', 2: 'Python 3.12\n'}
```

A generator expression uses the same syntax, and it works on iterables too. It is iterable itself, so `list` can collect its results.

```python
>>> list(line.upper() for line in open('data.txt'))
['TESTING FILE IO\n', 'LEARNING PYTHON, 6E\n', 'PYTHON 3.12\n']
```

Other built-in functions use the protocol as well, though they are harder to show with files. The `sum` call adds all the numbers in an iterable. The `any` and `all` built-ins return `True` if any or all items are true. The `max` and `min` built-ins return the largest and smallest items. Each one scans its argument and returns a single result.

```python
>>> sum(range(5))
10
>>> any(open('data.txt'))
True
>>> all(open('data.txt'))
True
>>> max(open('data.txt'))
'Testing file IO\n'
>>> min(open('data.txt'))
'Learning Python, 6E\n'
```

A starred argument in a function call unpacks an iterable into separate arguments. It works like the starred form in list literals. You will see calls like this again in the book's functions material. It accepts any iterable.

```python
>>> def f(a, b, c):
...     print(a, b, c, sep='&')
>>> f(*open('data.txt'))
Testing file IO
&Learning Python, 6E
&Python 3.12
```

Because starred calls accept iterables, `zip` can unzip zipped tuples. Pass a `zip` result as the argument list of another `zip` call. The result is hard to read, so use this pattern with care.

```python
>>> X, Y = (1, 2), (3, 4)
>>> list(zip(X, Y))
[(1, 3), (2, 4)]
>>> A, B = zip(*zip(X, Y))
>>> A, B
((1, 2), (3, 4))
```

The list of iteration tools is not complete. The pattern is clear, though. Any object that supports the protocol works with all of them.

### Other iteration topics

The book returns to iteration in two later places. User-defined functions can become generator functions, using `yield` statements. Comprehensions in parentheses become generator expressions. User-defined classes can become iterable through `__iter__` or `__getitem__` in operator overloading. Once a class supports one of these, it works with every iteration tool in this section.

### Iteration chapter summary

The iteration protocol lets nonsequence objects take part in loops. Comprehensions apply an expression to every item in any iterable. A list comprehension is an expression similar to a `for` loop. Many built-in tools in Python use the same protocol. Use a `for` loop with a file iterator when you need to read a text file line by line.

## Checkpoint questions

<details>
<summary>1. Name three ways to assign three variables to the same value.</summary>

You can use multiple-target assignment (`A = B = C = 0`), sequence assignment (`A, B, C = 0, 0, 0`), or three separate assignment statements (`A = 0`, `B = 0`, and `C = 0`). The separate statements can also share one line if you separate them with semicolons (`A = 0; B = 0; C = 0`).
</details>

<details>
<summary>2. What is dangerous about assigning three variables to a mutable object?</summary>

If you assign them this way, `A = B = C = []`, all three names reference the same object. Changing it in place through one name, such as `A.append(99)`, affects the other two. This risk applies only to in-place changes of mutable objects like lists and dictionaries. Immutable objects such as numbers and strings cannot change in place, so the issue does not arise for them.
</details>

<details>
<summary>3. What is wrong with saying `L = L.sort()`?</summary>

The list `sort` method changes the list in place. Like `append`, it returns `None`, not the list it changed. The assignment sets `L` to `None`. A newer built-in, `sorted`, sorts any sequence and returns a new list. Because it does not change anything in place, its result can be assigned safely.
</details>

<details>
<summary>4. Which two approaches send printed text to an external file?</summary>

For a single `print`, use the `print(X, file=F)` form. Or assign `sys.stdout` to an opened file before the `print`, and restore the original stream afterward if needed. Redirecting all of a program's printed text through special shell syntax, such as `> file`, is outside Python's scope.
</details>

<details>
<summary>5. Why does `a, b = seq` raise an error when `seq` has four items, and how can a starred target fix it?</summary>

Sequence assignment normally needs exactly as many targets as items, so two targets for four items raises a `ValueError`. A starred target such as `a, *b = seq` removes the need for matching lengths. The starred name collects the unassigned items into a list.
</details>

<details>
<summary>6. Why is `(python := 3.12) + 0.01` valid, but `(python[0] := 3.12) + 0.01` a syntax error?</summary>

Named assignment expressions accept only a simple name on the left. A subscript such as `python[0]` is a data structure component, and named assignment does not allow it. The expression `(python := 3.12) + 0.01` assigns the name and returns the value for the addition.
</details>

<details>
<summary>7. How might you code a multiple-choice branch in Python?</summary>

An `if` statement with several `elif` clauses is often the most straightforward way. It is not always the most concise or flexible. Dictionary indexing can get the same result, especially when the dictionary holds functions written with `def` or `lambda`. Since Python 3.10, the `match` statement gives explicit syntax for multiple-choice selection. It works well for basic roles. It cannot handle logic as general as an `if` statement can.
</details>

<details>
<summary>8. How can you code an `if`/`else` statement as an expression?</summary>

The expression `Y if X else Z` returns `Y` when `X` is true, and `Z` otherwise. It does the same job as a four-line `if` statement. It works well in limited contexts, but it cannot hold actions as rich as a full `if` statement, and it can produce code that is hard to read. The `and`/`or` combination, `((X and Y) or Z)`, works too. It is more obscure, and it requires that `Y` be true.
</details>

<details>
<summary>9. How can you make a single statement span many lines?</summary>

Wrap part of the statement in an open pair, `()`, `[]`, or `{}`. The statement continues until Python reaches the closing half of the pair. Lines after the first can start at any indentation level. Backslash continuations also work, but they are broadly discouraged.
</details>

<details>
<summary>10. What do the words `True` and `False` mean?</summary>

`True` and `False` are custom versions of the integers `1` and `0`. They stand for Boolean true and false values. You can use them in truth tests and variable initialization. Python prints them for expression results at the interactive prompt. They are a more readable alternative to `1` and `0` in these roles.
</details>

<details>
<summary>11. What does "short-circuiting" mean, and where does it crop up?</summary>

Short-circuiting happens when Python stops evaluating an expression early, because the result is already known. It comes up in `and` and `or` expressions. Those run their right side only if the left side does not settle the result. It also comes up in the `if`/`else` ternary expression, which runs only its true part or its false part, depending on the test.
</details>

<details>
<summary>12. What are the main functional differences between `while` and `for` loops?</summary>

The `while` loop is a general looping statement. It repeats as long as a test stays true. The `for` loop is built to step automatically through the items of a sequence or other iterable. A `while` loop can imitate a counter-based `for`, but that takes more code and may run more slowly.
</details>

<details>
<summary>13. What is the difference between `break` and `continue`?</summary>

The `break` statement exits the loop immediately, so control moves to the code below the whole loop statement. The `continue` statement jumps back to the top of the loop. In a `while` loop, control then goes to the test. In a `for` loop, control moves on to fetch the next item.
</details>

<details>
<summary>14. When is a loop's `else` clause executed?</summary>

The `else` clause runs once as the loop exits, but only if the loop ends normally. That happens when a `while` test turns false, or when a `for` loop runs out of items. If a `break` ends the loop, the `else` is skipped.
</details>

<details>
<summary>15. How can you code a counter-based loop in Python?</summary>

You can keep a counter by hand in a `while` loop, or use a `for` loop with `range` to generate successive integer offsets. Neither is the preferred style when you only need to visit each item in a sequence. Use a simple `for` loop without `range` or a counter whenever possible. It is easier to write and usually quicker to run.
</details>

<details>
<summary>16. What can a `range` be used for in a `for` loop?</summary>

A `range` can repeat an action a fixed number of times, scan by offsets instead of items, and skip successive items as you go. It can also let you change a list while you step across it. None of these roles strictly requires `range`. Scanning items directly, three-limit slices, and list comprehensions are often better choices today.
</details>

<details>
<summary>17. How are `for` loops and iterable objects related?</summary>

The `for` loop normally uses the iteration protocol to step through an iterable. It gets an iterator by calling the iterable's `__iter__` method. Then it calls the iterator's `__next__` method on each pass. It catches `StopIteration` to know when to stop. Any object that supports this model works in a `for` loop and in other iteration tools.
</details>

<details>
<summary>18. How are `for` loops and list comprehensions related?</summary>

Both are iteration tools. A list comprehension is a concise, often efficient way to collect the results of applying an expression to every item in an iterable. Its syntax resembles the header of a `for` loop. Any list comprehension can be translated into a `for` loop. The `for` loop also covers looping roles that comprehensions do not.
</details>

<details>
<summary>19. Name four iteration tools in the Python language.</summary>

The `for` loop, list comprehensions, the `map` built-in, and the `in` membership test are all iteration tools. So are the built-ins `sorted`, `sum`, `any`, and `all`. The `list` and `tuple` built-ins, the string `join` method, and sequence assignments also use the protocol. Any four of these answer the question.
</details>

<details>
<summary>20. What is the best way to read line by line from a text file today?</summary>

Do not read the file explicitly. Open it inside an iteration tool, such as a `for` loop or a list comprehension. The tool then scans one line at a time by calling the file's `__next__` method on each pass. This approach is generally the simplest to code. It uses little memory, and it is often fast.
</details>

## Sources and review notes

- Source: *Learning Python*, 6th edition (`learning-python-6th-edition`). Chapters used are listed in each section.
- Chapter used: Chapter 11, "Assignments, Expressions, and Prints" (`learning-python-6th-edition`).
- Chapter used: Chapter 12, "if and match Selections" (`learning-python-6th-edition`).
- Chapter used: Chapter 13, "while and for Loops" (`learning-python-6th-edition`).
- Chapter used: Chapter 14, "Iterations and Comprehensions" (`learning-python-6th-edition`).
