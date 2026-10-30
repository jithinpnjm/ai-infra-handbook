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

## Sources and review notes

- Source: *Learning Python*, 6th edition (`learning-python-6th-edition`). Chapters used are listed in each section.
- Chapter used: Chapter 11, "Assignments, Expressions, and Prints" (`learning-python-6th-edition`).
