---
id: "c03-12"
title: "3.12 Objects, types and data structures in depth"
sidebar_label: "3.12 Objects, types and data structures in depth"
sidebar_position: 12
description: "Numbers, strings, lists, dictionaries, tuples and files, and how Python's dynamic typing really works, taught from first principles for infrastructure scripting."
status: "drafted"
tier: "2"
level: "I"
lab_venue: "Mac"
---

# 3.12 Objects, types and data structures in depth

This chapter goes deeper into material that chapter 3.1 only introduces. You will meet it again whenever you read or write the Python behind schedulers, operators, exporters and training launchers.

## Where objects fit in a Python program

Python programs are built in layers. Programs are made of modules, modules contain statements, statements contain expressions, and expressions create and process objects. Chapter 3 introduced the top layer, modules. This part of the book starts at the bottom, with built-in objects and the expressions that create and use them.

Statements mostly exist to manage the objects you meet here. Later, classes let you define new object types by using and extending the types you learn now. That is why built-in objects are the starting point for every Python program.

### A note on terms

Many introductions to programming describe three building blocks: sequence (do this, then that), selection (do this only when a condition holds) and repetition (do this again and again). Python offers tools in each group, and these labels can help you sort ideas early on. They are still artificial, though, and they can confuse you. Comprehensions, for example, count as both repetition and selection.

In Python, the more unifying idea is objects and what you can do with them.

## Why use built-in objects?

If you have used a lower-level language, much of your work centers on building objects, also called data structures, for the parts of your problem. You may need to lay out memory, manage allocation, and write search routines. These chores are tedious and error-prone, and they pull attention away from your real goal.

In a typical Python program, most of that work goes away. Python provides powerful object types as part of the language, so you rarely need to write your own before you start solving problems. Unless you need special processing that built-in objects cannot offer, a built-in is almost always the better choice.

### Built-in objects make programs easy to write

For simple tasks, built-in objects often describe the structure of a problem well enough. Lists give you collections and dictionaries give you search tables, and both come for free. You can get a lot of work done with the built-in types alone.

### Built-in objects are building blocks for extensions

For bigger tasks, you may write your own objects with classes or with C-language interfaces. Those objects are often built on top of lists and dictionaries. A stack, for example, can be a class that manages or customizes a built-in list.

### Built-in objects are often faster

Python's built-in objects use algorithms that are already optimized. Many are implemented in a lower-level language like C for speed. You can write similar types yourself, but you will usually struggle to match their performance.

### Built-in objects are a standard part of the language

Some languages rely on built-in tools, such as Lisp, while others expect you to supply your own, such as C++. Python can do either, but you do not need to write new object types just to get started. Built-ins are also always the same, while proprietary toolkits tend to differ from site to site.

Built-in object types make programming easier, and they are often more powerful than what you could build from scratch. Whether or not you add new types, built-in objects form the core of every Python program.

## Python's core object types

Table 4-1 previews Python's built-in objects and the syntax used to write their literals, which are the expressions that create them. Numbers and strings represent numeric and text values, and file objects give you an interface to real files on your computer. Some of these types will look familiar if you have used other languages.

Lists and dictionaries are more flexible than you may be used to. Lists keep ordered collections of other objects, and dictionaries store objects by key. Both handle memory automatically, nest freely, grow and shrink on demand, and can hold objects of any kind.

### Table 4-1: Python built-in (core) objects

| Object type | Example literals/creation |
| --- | --- |
| Numbers | `1234`, `3.1415`, `0b111`, `1_234`, `3+4j`, `Decimal`, `Fraction` |
| Strings | `'code'`, `"app's"`, `b'a\x01c'`, `'h\u00c4ck'`, `'hÄck'` |
| Lists | `[1, [2, 'three'], 4.5]`, `list(range(10))` |
| Dictionaries | `{'job': 'dev', 'years': 40}`, `dict(hours=10)` |
| Tuples | `(1, 'app', 4, 'U')`, `tuple('hack')`, `namedtuple` |
| Files | `open('docs.txt')`, `open(r'C:\data.bin', 'wb')` |
| Sets | `set('abc')`, `{'a', 'b', 'c'}` |
| Other core objects | Booleans, types, `None` |
| Program-unit objects | Functions, modules, classes (Parts IV, V, and VI) |
| Implementation objects | Compiled code, stack tracebacks (Parts IV and VII) |

### Program-unit and implementation objects

Functions, modules and classes are also objects. You create them with statements and expressions such as `def`, `class`, `import` and `lambda`. You can pass them around, store them inside other objects, and so on.

Python also has implementation objects, such as compiled code. These matter more to tool builders than to application developers, so we will cover them more briefly later.

### Table 4-1 is not the whole list

Table 4-1 is not complete, because everything you process in Python is some kind of object. Pattern-matching work creates pattern objects, and network scripts create socket objects. These usually come from importing functions in standard or add-on library modules. Patterns and sockets, for example, come from the `re` and `socket` modules.

We call the table's objects core object types because the language itself has specific syntax for most of them. Running this line in a REPL creates a new string object:

```
>>> 'Python'
```

The quotes make it a literal expression. A square-bracket expression makes a list, and curly braces make a dictionary or a set. Python does not need type declarations. The syntax you write decides which types you get.

### Dynamic and strong typing

Once you create an object, its set of operations is fixed. You can run string operations on a string and list operations on a list. Formally, Python is dynamically typed, because it tracks object types for you without declaration code. It is also strongly typed, because you can only perform operations that are valid for an object's type.

We will study each core type in detail in later chapters. This chapter gives you a quick look at them in action.

## Numbers

Numbers are the most familiar core type. Python includes integers, floating-point numbers, complex numbers with imaginary parts, decimals with flexible precision, rationals with a numerator and denominator, and sets. Built-in numbers handle most everyday quantities. Vectors and matrices are available as third-party add-ons.

### Basic arithmetic

Python's basic numbers support the usual math. The plus sign adds, the star multiplies, and two stars raise a number to a power. Here is a short session in a REPL, the interactive prompt you started in Chapter 3:

```
$ python3 # Start up a REPL
>>> 123 + 222 # Integer addition
345
>>> 1.5 * 4 # Floating-point multiplication
6.0
>>> 1_234_567, 0x15, bin(21) # Separators, hex, binary
(1234567, 21, '0b10101')
>>> 2 ** 100 # 2 to the power 100, again
1267650600228229401496703205376
```

The integer type stretches to hold large numbers automatically. You can compute 2 to the power 12,345 as an integer. The result has nearly 4,000 digits, so it is a lot to read directly. You can ask how long it is instead:

```
>>> len(str(2 ** 12345)) # How many digits in a really BIG number
3717
```

This nested call works from the inside out. Python computes the power first, converts it to a string with `str`, and then measures the string with `len`. Both `str` and `len` work on many object types, and you will see them again.

### Numeric modules

Python ships with numeric modules you can import. A module is a package of extra tools that you load with `import`. The `math` module provides advanced functions and constants:

```
>>> import math
>>> math.pi
3.141592653589793
>>> math.sqrt(85)
9.219544457292887
```

The `random` module generates random numbers and makes random choices. Here it picks from a list written in square brackets:

```
>>> import random
>>> random.random()
0.7082048489415967
>>> random.choice([1, 2, 3, 4])
2
```

Python also has more specialized numeric objects, including complex, fixed-precision and rational numbers, along with sets and Booleans. The third-party open source ecosystem adds more, such as matrices, vectors and extended-precision numbers.

### Very large integers

Python integers can grow as large as your computer's memory allows. Python 3.11 and later need extra steps to convert very large numbers to decimal strings, for example for `str` or display. This protects against rare denial-of-service attacks. The default limit is 4,300 digits.

You can lift that limit with `set_int_max_str_digits` from the `sys` module. Use it to count digits in larger numbers, and check Python's documentation for the full details.

Python's calculator-style use is only the start. Next, we will look at strings, which are a richer kind of object.

## Strings

Strings record text, such as a name, and they can also hold any collection of bytes, such as the contents of an image file. Strings are our first example of a sequence. A sequence keeps its items in a left-to-right order, and you fetch items by their positions. A string is technically a sequence of one-character strings.

### Sequence operations

Suppose you have a four-character string in quotes. Single and double quotes mean the same thing, though single quotes are more common. You can check its length with `len` and fetch characters with indexes:

```
>>> S = 'Code' # Make a 4-character string, and assign it to a name
>>> len(S) # Length: number characters
4
>>> S[0] # The first item in S, indexing by zero-based position
'C'
>>> S[1] # The second item from the left
'o'
```

Indexes count from zero, so the first item is at index 0. Python variables do not need declarations. A variable comes into existence when you assign it a value, and it can hold any type of object. It must be assigned before you use it.

Positive indexes count forward from the left. Negative indexes count backward from the right:

```
>>> S[-1] # The last item from the end in S
'e'
>>> S[-2] # The second-to-last item from the end
'd'
```

A negative index is added to the length to get a positive offset. These two lines do the same thing, though the first is easier to write and harder to get wrong:

```
>>> S[-1] # The last item in S
'e'
>>> S[len(S)-1] # Negative indexing, the hard way
'e'
```

You can put any expression inside the square brackets. A literal, a variable, or a computed value all work.

### Slicing

Slicing extracts a whole section in one step. Think of it as taking a column out of a string. The general form `X[I:J]` means everything in `X` from offset `I` up to, but not including, offset `J`:

```
>>> S # A 4-character string
'Code'
>>> S[1:3] # Slice of S from offsets 1 through 2 (not 3)
'od'
```

The result is a new object. If the left bound is missing, it defaults to zero. If the right bound is missing, it defaults to the length:

```
>>> S[1:] # Everything past the first (1:len(S))
'ode'
>>> S # S itself hasn't changed
'Code'
>>> S[0:3] # Everything but the last
'Cod'
>>> S[:3] # Same as S[0:3]
'Cod'
>>> S[:-1] # Everything but the last again, but simpler (0:-1)
'Cod'
>>> S[:] # All of S as a top-level copy (0:len(S))
'Code'
```

Negative offsets work as slice bounds too. The last form copies the whole string. There is rarely a reason to copy a string, but the same form can be useful for lists.

### Concatenation and repetition

Strings also support concatenation with the plus sign, which joins two strings into a new one. They also support repetition with the star, which repeats a string:

```
>>> S
'Code'
>>> S + 'xyz' # Concatenation
'Codexyz'
>>> S # S is unchanged
'Code'
>>> S * 8 # Repetition
'CodeCodeCodeCodeCodeCodeCodeCode'
```

The plus sign means addition for numbers and concatenation for strings. Python calls this polymorphism, which means an operation's meaning depends on the objects it works on. Polymorphism makes Python code short and flexible. Code can often work on many types as long as they support a compatible operation.

### Immutability

None of the string operations so far changed the original string. Every string operation produces a new string, because strings are immutable. Once created, they cannot be changed in place.

You cannot overwrite part of an immutable object. You can, however, build a new object and assign it to the same name. Python cleans up old objects as you go, so this is not as wasteful as it sounds:

```
>>> S
'Code'
>>> S[0] = 'z' # Immutable objects cannot be changed
…error text omitted…
TypeError: 'str' object does not support item assignment
>>> S = 'Z' + S[1:] # But we can run expressions to make new objects
>>> S
'Zode'
```

Every object is either immutable or mutable. Numbers, strings and tuples are immutable. Lists, dictionaries and sets are mutable, so you can change them freely. Most new objects you write with classes are mutable too. This distinction matters a lot. Immutability can guarantee that a value stays constant. A mutable value can change at any time and place, whether your code expects it or not.

You can change text in place in two ways. One is to expand the string into a list of characters, change the list, and join it back together with nothing between the pieces:

```
>>> S = 'Python'
>>> L = list(S) # Expand to a list: […]
>>> L
['P', 'y', 't', 'h', 'o', 'n']
>>> L[0] = 'C' # Change it in place
>>> ''.join(L) # Join with empty delimiter
'Cython'
```

The other is the special `bytearray` object:

```
>>> B = bytearray(b'app') # A bytes/list hybrid (ahead)
>>> B.extend(b'lication') # 'b' means bytes string
>>> B # B[i] = ord(x) works here too
bytearray(b'application')
>>> B.decode() # Translate to normal string
'application'
```

A `bytearray` can change text in place only when every character fits in 8 bits, as ASCII does. Other strings stay immutable. A `bytearray` mixes immutable bytes strings with mutable lists. You will understand both fully once you learn more about bytes and Unicode.

### Type-specific methods

Sequence operations work on other sequences too, such as lists and tuples. Strings also have their own operations, called methods. A method is a function attached to an object and called with parentheses.

The `find` method returns the offset of a substring, or `-1` if it is missing. The `replace` method swaps every match for new text. Both act on the string you call them on:

```
>>> S = 'Code'
>>> S.find('od') # Find the offset of a substring in S
1
>>> S
'Code'
>>> S.replace('od', 'abl') # Replace all substrings 'od' in S with 'abl'
'Cable'
>>> S
'Code'
```

Again, these methods return new strings and leave the original alone. Other string methods split text on a delimiter, which is a simple way to parse data. They convert case, test the content for digits or letters, and strip whitespace from the ends:

```
>>> line = 'aaa,bbb,ccccc,dd'
>>> line.split(',') # Split on a delimiter into a list of substrings
['aaa', 'bbb', 'ccccc', 'dd']
>>> S = 'code'
>>> S.upper() # Upper- and lowercase conversions
'CODE'
>>> S.isalpha() # Content tests: isalpha, isdigit, etc.
True
>>> line = 'aaa,bbb,ccccc,dd\n'
>>> line.rstrip() # Remove whitespace characters on the right side
'aaa,bbb,ccccc,dd'
>>> line.rstrip().split(',') # Combine two operations, run left to right
['aaa', 'bbb', 'ccccc', 'dd']
```

Python runs chained calls from left to right. In the last line, the strip happens before the split. You can chain calls this way as long as each call returns an object that has the next method.

Formatting is another string job. It fills in placeholders with values and builds a new string. Python offers three forms. The original is the format expression, the newer one is the format method, and the newest is the f-string literal. All three resolve their values when they run:

```
>>> tool = 'Python'
>>> major = 3
>>> minor = 3
>>> 'Using %s version %s.%s' % (tool, major, minor + 9) # Format expression
'Using Python version 3.12'
>>> 'Using {} version {}.{}'.format(tool, major, minor + 9) # Format method
'Using Python version 3.12'
>>> f'Using {tool} version {major}.{minor + 9}' # Format literal
'Using Python version 3.12'
```

All three are valid, and you will see each in code you read. You can pick one for your own work. Each has many options for controlling output, which matter most for readable reports with numbers:

```
>>> '%.2f | %+05d' % (3.14159, -62) # Digits, signs, padding
'3.14 | −0062'
>>> '{1:,.2f} | {0}'.format('sapp'[1:], 296999.256) # Commas, decimal digits
'296,999.26 | app'
>>> f'{296999.256:,.2f} | {'sapp'[1:]}' # Ditto, with Python 3.12+ nested quotes
'296,999.26 | app'
```

Sequence operations are generic, but methods are not. String methods generally work only on strings. Python's tools are layered. Generic operations that span types appear as built-in functions or expressions, such as `len(X)` and `X[0]`. Type-specific operations are method calls, such as `aString.upper()`.

### Getting help with dir and help

The methods above are only a small sample of what string objects offer. The built-in `dir` function lists the attributes of any object you pass to it. Methods are callable attributes, so they appear in that list. Here are the attributes of `S`, with the middle cut short:

```
>>> dir(S)
['__add__', '__class__', '__contains__', '__delattr__', '__dir__', '__doc__',
'__eq__', '__format__', '__ge__', '__getattribute__', '__getitem__',
…etc…
'rindex', 'rjust', 'rpartition', 'rsplit', 'rstrip', 'split', 'splitlines',
'startswith', 'strip', 'swapcase', 'title', 'translate', 'upper', 'zfill']
```

Run `dir` yourself for the full list, since strings have 81 attributes today. Names without underscores are the callable methods. Names with double underscores support the object's internal implementation and customization. You will study them when you learn operator overloading in classes.

The `__add__` method is how concatenation works internally. Python maps the first form below to the second. You should not usually write the second form yourself, because it is less intuitive and may run slower:

```
>>> S + 'head!'
'Codehead!'
>>> S .__add__('head!')
'Codehead!'
```

The `dir` function gives you names only. To learn what a method does, pass it to `help`:

```
>>> help(S.replace) # Or help(str.replace)
Help on built-in function replace:
replace(old, new, count=-1, /) method of builtins.str instance
Return a copy with all occurrences of substring old replaced by new.
…etc…
```

Press the `Q` key to leave a `help` display in most console windows. The `help` function is one way into Pydoc, a tool that extracts documentation from objects. Pydoc can also render its reports as HTML for a web browser.

Calling `help(S)` on a string instance may not give you what you want, because it shows the string's value instead. To get help on the type, use `help(str)` or `help(type(S))`. Those describe every method, so `help` is most useful on one specific method at a time. For the full reference, you can also read Python's standard-library manual. For quick answers in a REPL, `dir` and `help` come first.

### Other ways to code strings

Special characters use backslash escapes. Python displays nonprintable characters as `\xNN` hexadecimal escapes, unless they stand for printable characters:

```
>>> S = 'A\nB\tC' # Escapes: \n is newline, \t is tab
>>> len(S) # Each stands for just one character
5
>>> S = 'A\0B\0C' # \0, a binary zero byte, does not terminate string
>>> len(S)
5
>>> S # Nonprintables are displayed as \xNN hex escapes
'A\x00B\x00C'
```

You can enclose strings in single or double quotes. They mean the same thing, and using the other kind lets you embed a quote without an escape. Most programmers prefer single quotes for less clutter. You can also write multiline strings in triple quotes. Every line is joined together, and newline characters appear where the line breaks were:

```
>>> msg = """
... aaaaaaaaaaaa
... bbb'''bbb""bbb
... cccccccc
... """
>>> msg
'\naaaaaaaaaaaa\nbbb\'\'\'bbb""bbb\ncccccccc\n'
```

Triple-quoted strings are handy for embedding multiline HTML, YAML or JSON in a script. You can also use them to stub out lines of code temporarily by wrapping those lines in three quotes.

A raw string literal turns off backslash escapes. You write it with a leading `r`. Raw strings suit regular-expression patterns and Windows directory paths, because you do not need doubled backslashes:

```
>>> r'C:\Users\you\code'
```

### Unicode strings

Python strings support Unicode, which you need for non-ASCII text. That includes non-English languages, symbols and emojis, and it is common in web pages, emails and data. The normal `str` type handles Unicode text, and ASCII is just a simple subset of it. The `bytes` type, and its mutable cousin `bytearray`, handle raw byte values, including encoded text and media:

```
>>> 'hÄck' # Normal str strings are Unicode text
'hÄck'
>>> b'a\x01c' # bytes strings are byte-based data
b'a\x01c'
```

Text strings are sequences of Unicode code points. A code point is a number that identifies a character. Bytes strings are sequences of 8-bit bytes. A code point does not always map to one byte in memory or in a file. Some code points are too large for a byte, and encodings can use characters of any size:

```
>>> 'Code' # Characters may be any size in memory
'Code'
>>> 'Code'.encode('utf-8') # Encoded to 4 bytes in UTF-8 in files
b'Code'
>>> 'Code'.encode('utf-16') # But encoded to 10 bytes in UTF-16
b'\xff\xfeC\x00o\x00d\x00e\x00'
```

Rich text shows this even more clearly. The `ord` function gives a character's code point, and `hex` gives that number as a hexadecimal string:

```
>>> len('hÄck') # One character (code point) each
6
>>> len('hÄck'.encode('utf-8')) # But encoded bytes sizes vary
13
>>> len('hÄck'.encode('utf-16'))
18
```

To put non-ASCII characters into text strings, you have three options. You can use `\x` hexadecimal escapes, short `\u` Unicode escapes, or long `\U` escapes. You can also write the character directly, and Python decodes the source using the encoding declared in the file. The default for source code is UTF-8. Here the letter Ä appears four ways:

```
>>> 'h\xc4\u00c4\U000000c4Äck' # Coding non-ASCII: hex, short, long, raw
'hÄÄÄÄck'
```

In text strings, all these forms give Unicode code points. Byte strings use only `\x` escapes for raw byte values. When a byte string holds text, it holds the encoded form, not the code points. The two match only for simple text and simple encodings:

```
>>> '\u00A3', '\u00A3'.encode('latin1'), b'\xA3'.decode('latin1')
('£', b'\xa3', '£')
```

Most Unicode work comes down to moving text to and from files. Text files encode strings to bytes when they save and decode bytes to characters when they load. After loading, you usually work with decoded strings. Text files accept and return text strings, while binary files deal in `bytes`. The rest of the Unicode story comes later in the book, after you master basic string work.

Python's standard toolset also covers text pattern matching with the `re` module, and parsing of JSON, CSV, XML and HTML.

## Lists

The list is the most general sequence in Python. A list is an ordered collection of objects of any type, and it has no fixed size. Lists are mutable, so you can change them in place by assigning to positions or by calling list methods. That makes them a flexible tool for collections such as files in a folder, employees in a company, or emails in an inbox.

### Sequence operations

Lists support every sequence operation you saw with strings. Most of them return lists instead of strings. Here is a three-item list:

```
>>> L = [123, 'text', 1.23] # A list of three different-type objects
>>> len(L) # Number of items in the list
3
```

You can index and slice it just as you did with strings:

```
>>> L[0] # Indexing by position (offset)
123
>>> L[:-1] # Slicing a list returns a new list
[123, 'text']
>>> L + [4, 5, 6] # Concat/repeat make new lists too
[123, 'text', 1.23, 4, 5, 6]
>>> L * 2
[123, 'text', 1.23, 123, 'text', 1.23]
>>> L # We're not changing the original list
[123, 'text', 1.23]
```

### Type-specific operations

Lists may remind you of arrays in other languages, but they are more powerful. A list has no fixed type. The list above holds an integer, a string and a floating-point number. A list also grows and shrinks on demand, using list-specific operations:

```
>>> L.append('Py') # Growing: add object at end of list
>>> L
[123, 'text', 1.23, 'Py']
>>> L.pop(2) # Shrinking: delete an item in the middle
1.23
>>> L # "del L[2]" deletes from a list too
[123, 'text', 'Py']
```

The `append` method adds an item at the end. The `pop` method removes an item at a given offset. A `del` statement also removes an item. Other methods insert at a position with `insert`, remove by value with `remove`, and add several items at once with `extend`.

Most list methods change the list in place instead of making a new one:

```
>>> M = ['bb', 'aa', 'cc']
>>> M.sort()
>>> M
['aa', 'bb', 'cc']
>>> M.reverse()
>>> M
['cc', 'bb', 'aa']
```

The `sort` method orders the list in ascending order by default. The `reverse` method reverses it. Both change the list directly. Similarly named functions that you will meet later do not.

### Bounds checking

A list has no fixed size, but Python still refuses to reference items that do not exist. Indexing past the end is always a mistake. Assigning past the end is also an error:

```
>>> L
[123, 'text', 'Py']
>>> L[99]
IndexError: list index out of range
>>> L[99] = 1
IndexError: list assignment index out of range
```

This is deliberate. Assigning off the end is usually a bug, and in C it can be a particularly nasty one, because C does less error checking. Python reports the error rather than silently growing the list. To grow a list, call a method such as `append`, or build a new list. Slicing behaves differently, because it adjusts offsets to fit inside the list.

### Nesting

Core object types nest in any combination and to any depth. A list can hold a dictionary, which holds another list, and so on. You can describe real-world structures this way.

A nested list is a common way to build a matrix, which is a grid of numbers. Indentation does not matter inside brackets, and an expression can span several lines if its brackets stay open:

```
>>> M = [[1, 2, 3], # A 3 × 3 matrix, as nested lists
[4, 5, 6], # Code can span lines if bracketed
[7, 8, 9]]
>>> M
[[1, 2, 3], [4, 5, 6], [7, 8, 9]]
```

This list holds three lists, which together form a 3 by 3 grid. You can reach the parts in several ways:

```
>>> M[1] # Get row 2
[4, 5, 6]
>>> M[1][2] # Get row 2, then get item 3 within the row
6
```

The first line fetches the whole second row. The second line fetches the third item inside that row. Chained indexes take you deeper into a nested structure. A nested list works for small jobs. For serious number crunching, the third-party NumPy extension stores and processes large matrices much more efficiently.

### Comprehensions

A list comprehension produces a fresh list. It evaluates an expression for every element of a sequence, moving from left to right. It is written in square brackets, which signal that the result is a list. A comprehension combines an expression with a loop that shares a variable name.

Suppose you want the second column of the matrix. The matrix is stored by rows, so rows are easy to grab. Columns take a comprehension, but it is still short:

```
>>> col2 = [row[1] for row in M] # Collect the items in column 2
>>> col2
[2, 5, 8]
>>> M # The matrix is unchanged
[[1, 2, 3], [4, 5, 6], [7, 8, 9]]
```

Read the comprehension as: give me `row[1]` for each row in `M`, in a new list. Comprehensions can also do more work. One adds 1 to each item as it is collected. Another uses an `if` clause to keep only the even items, with `%` returning the remainder of a division:

```
>>> [row[1] + 1 for row in M] # Add 1 to each item in column 2
[3, 6, 9]
>>> [row[1] for row in M if row[1] % 2 == 0] # Filter out odd items (pick evens)
[2, 8]
```

Comprehensions work over any iterable object. An iterable is either a physical sequence or a virtual one that makes its items on request. Here a comprehension steps over a list of coordinates, and then over a string:

```
>>> diag = [M[i][i] for i in [0, 1, 2]] # Collect a diagonal from matrix
>>> diag
[1, 5, 9]
>>> doubles = [c * 2 for c in 'hack'] # Repeat characters in a string
>>> doubles
['hh', 'aa', 'cc', 'kk']
```

To collect several values per item, wrap them in a nested collection. The `range` built-in generates successive integers. Wrap it in `list` so the REPL shows every value:

```
>>> list(range(4)) # Integers 0..(N-1)
[0, 1, 2, 3]
>>> list(range(−6, 7, 2)) # −6 to +6 by 2
[−6, −4, −2, 0, 2, 4, 6]
>>> [[x ** 2, x ** 3] for x in range(4)] # Multiple values, "if" filters
[[0, 0], [1, 1], [4, 8], [9, 27]]
>>> [[x, x // 2, x * 2] for x in range(-6, 7, 2) if x > 0]
[[2, 1, 4], [4, 2, 8], [6, 3, 12]]
```

Comprehensions are optional, but they are useful and often run faster. Python has both simple and advanced tools, and you will choose between them as you go.

Parentheses turn a comprehension into a generator. A generator produces results on demand, following Python's iteration protocol. This example sums each row with `sum`, one row per call to `next`:

```
>>> M
[[1, 2, 3], [4, 5, 6], [7, 8, 9]]
>>> G = (sum(row) for row in M) # Make a generator of row sums
>>> next(G) # Run the iteration protocol (ahead)
6
>>> next(G) # A new row sum on each call
15
>>> next(G) # Row 3: 7 + 8 + 9
24
```

Curly braces turn a comprehension into a set or a dictionary:

```
>>> {sum(row) for row in M} # Makes an unordered set of row sums
{24, 6, 15}
>>> {i: sum(M[i]) for i in range(3)} # Makes key:value table of row sums
{0: 6, 1: 15, 2: 24}
```

## Dictionaries

Dictionaries are not sequences. They are the only core mapping type. A mapping stores objects by key rather than by position. Dictionaries keep insertion order, which has been true since Python 3.7, but their main job is still mapping keys to values. Like lists, they are mutable, grow and shrink on demand, and can hold any kind of object. Their named keys suit records with labeled fields, such as the fields of a database row.

### Mapping operations

Dictionaries are written in curly braces as a series of key-value pairs. Use them whenever you need to associate values with keys, such as the properties of one thing. This dictionary records three attributes of a made-up worker, with keys for name, job and age:

```
>>> D = {'name': 'Pat', 'job': 'dev', 'age': 40}
```

Indexing a dictionary uses the same square-bracket syntax as a sequence. The item in the brackets is a key, not a position. You can fetch a value by key, or change it:

```
>>> D['name'] # Fetch value of key 'name'
'Pat'
>>> D['job'] = 'mgr' # Change Pat's job description
>>> D
{'name': 'Pat', 'job': 'mgr', 'age': 40}
```

Dictionaries are often built up over time, not written out in full, since you rarely know all your data before the program runs. This code starts with an empty dictionary and adds one key at a time. Assigning to a new key creates it. That differs from lists, where assigning past the end is forbidden:

```
>>> D = {}
>>> D['name'] = 'Pat' # Create keys by assignment
>>> D['job'] = 'dev'
>>> D['age'] = 40
>>> D
{'name': 'Pat', 'job': 'dev', 'age': 40}
```

Here the keys act as field names for a record describing an imaginary person. Dictionaries can also replace searches. Indexing by key is often the fastest way to search in Python.

You can also build a dictionary by passing keyword arguments to `dict`, written as `name=value`. Or you can pass the result of zipping together a list of keys and a list of values. Both forms below match the literal form. The keyword form needs string keys and is shorter. The `zip` form works well with values read at runtime, such as from a file:

```
>>> pat1 = dict(name='Pat', job='dev', age=40) # Keywords
>>> pat1
{'name': 'Pat', 'job': 'dev', 'age': 40}
>>> pat2 = dict(zip(['name', 'job', 'age'], ['Pat', 'dev', 40])) # Zipping
>>> pat2
{'name': 'Pat', 'job': 'dev', 'age': 40}
```

Keys keep the order in which you added them, even after changes. Before Python 3.7, key order was not guaranteed, and you sometimes needed a separate ordering step. The newer behavior is more intuitive, and this book assumes it. It gives dictionaries a sequence-like flavor that other non-sequences lack.

### Nesting revisited

Suppose the record needs more detail, such as a first name, a last name, and several job titles. A nested structure handles that well. This dictionary is written all at once as a literal:

```
>>> rec = {'name': {'first': 'Pat', 'last': 'Smith'},
'jobs': ['dev', 'mgr'],
'age': 40.5}
```

The top level still has three keys. The `name` value is now a nested dictionary, and the `jobs` value is a nested list. You reach the parts the same way you reached the matrix. Most indexes here are keys, not list offsets:

```
>>> rec['name'] # 'name' is a nested dictionary
{'first': 'Pat', 'last': 'Smith'}
>>> rec['name']['last'] # Index the nested dictionary
'Smith'
>>> rec['jobs'] # 'jobs' is a nested list
['dev', 'mgr']
>>> rec['jobs'][-1] # Index the nested list
'mgr'
>>> rec['jobs'].append('janitor') # Expand Pat's job description in place
>>> rec
{'name': {'first': 'Pat', 'last': 'Smith'}, 'jobs': ['dev', 'mgr', 'janitor'], 'age': 40.5}
```

The `jobs` list is a separate object from the dictionary that holds it. That is why it can grow and shrink freely. The `pop` method is one way to shrink it. This may seem unusual if you come from a stricter language, but in Python it feels natural.

Building the same structure in a low-level language like C would take much more code. You would declare structures and arrays, fill in values, and link everything together. In Python, running the expression creates the whole nested structure. Saving time like this is one of the main benefits of scripting languages.

Memory works the same way. In lower-level languages, you allocate memory ahead of time and release it yourself. In Python, memory is allocated as needed and freed when you lose the last reference to an object. Assigning the variable to something else is one way to lose that reference:

```
>>> rec = 0 # Now the prior object's space is reclaimed
```

Python uses garbage collection to reclaim unused memory while your program runs. In standard CPython, reference counts do most of the work, with a supplemental collector for cycles. You can use objects freely while Python manages their memory.

This record shape appears again in later chapters, where lists, dictionaries, tuples, named tuples and classes are compared. You can also save a structure like this to a file. The `pickle` module does that, and JSON is a language-neutral format that looks very much like a Python dictionary.

### Missing keys and if tests

Dictionaries support key access and the operations shown above. They also have methods for common jobs. The `copy` method copies a dictionary. The `update` method merges one dictionary into another in place. The `|` operator does the same merge, but it builds a new dictionary as its result. That is simply a copy plus an update.

Assigning to a new key grows a dictionary. Fetching a missing key is still an error:

```
>>> D = {'a': 1, 'b': 2, 'c': 3}
>>> D['d'] = 4 # Assigning new keys grows dictionaries
>>> D
{'a': 1, 'b': 2, 'c': 3, 'd': 4}
>>> D['e'] # Referencing a nonexistent key is an error
…error text omitted…
KeyError: 'e'
```

That behavior is usually what you want, because fetching a missing key is often a programming error. In general programs, though, you cannot always know which keys will exist. One answer is to test first. The `in` expression checks whether a key exists, and an `if` statement branches on the result:

```
>>> 'e' in D # Boolean result: True or False
False
>>> if not 'e' in D: # Python's main selection statement
print('missing key!')
missing key!
```

The `if` statement is Python's main tool for choices. Its header is the word `if`, then an expression that is true or false, then a block of code to run when the expression is true. An `else` branch covers the false case, and any number of `elif` branches add more tests. The ternary `if`/`else` expression is a shorter form, and the `if` filter in comprehensions is a close relative. The newer `match` statement handles multiple selections, and you will meet it later.

Blocks are marked by indentation, not braces. If a block has several statements, indent them all the same amount. Every multiline statement follows this pattern: a header line ending in a colon, then the indented block. You do not need semicolons after statements. Forgetting the colon is the most common beginner mistake:

```
>>> if not 'e' in D:
print('missing') # Statement blocks are indented
print('no, really...') # (Unless they're simple: see ahead)
missing
no, really...
```

Other ways avoid nonexistent keys too. The `get` method is a conditional index with a default value. The ternary expression is a compact `if`. The `try` statement catches and recovers from errors, and you will meet it later:

```
>>> D.get('a', 'missing') # Like D['a'] but with a default
1
>>> D.get('e', 'missing') # Default returned if absent
'missing'
>>> D['e'] if 'e' in D else 0 # if/else ternary expression form
0
```

### Item iteration with for loops

Dictionaries hold much of your data, so you often need to process their items one at a time. Dictionaries have methods for this. The `keys`, `values` and `items` methods return keys, values, and key-value pairs:

```
>>> D = dict(a=1, b=2, c=3)
>>> D
{'a': 1, 'b': 2, 'c': 3}
>>> list(D.keys()) # Keys, values, and key/value pairs
['a', 'b', 'c']
>>> list(D.values()) # list forces results generation
[1, 2, 3]
>>> list(D.items())
[('a', 1), ('b', 2), ('c', 3)]
```

These methods return objects that produce one result at a time. That is why the examples wrap them in `list`, just as with `range`. This is Python's iteration protocol. An iterable object has an iterator, and the iterator answers `next` calls with one item at a time:

```
>>> D.keys() # Get an iterable object
dict_keys(['a', 'b', 'c'])
>>> I = iter(D.keys()) # Get an iterator from an iterable
>>> next(I) # Get one result at a time from iterator
'a'
>>> next(I) # This is most of the iteration protocol
'b'
```

Generators skip the `iter` step. A generator does not support multiple scans, so it is its own iterator, and `iter` does nothing to it.

The protocol saves memory and reduces delays. Results are made one at a time, not all at once. You rarely need to call `next` yourself. The `for` loop runs the protocol for you, stepping through items one by one. It works on strings, lists, and virtual sequences such as generators, `range`, and `keys`:

```
>>> for key in D.keys(): # Auto run the iteration protocol
print(key, '=>', D[key]) # Display multiple items, space between
a => 1
b => 2
c => 3
```

A `for` loop needs a variable name and an iterable. For each item, it assigns the item to the variable and runs the indented block. The `for` loop is one of Python's main repetition tools. The others are comprehensions and the `while` loop, which you will meet later.

Because iterating over a dictionary is so common, a `for` loop can also step through its keys implicitly. It can step through key-value pairs too. These two loops give the same output as the first. The choice is partly a matter of taste, but explicit code is usually better:

```
>>> for key in D: # Implicit keys() iteration
print(key, '=>', D[key])
>>> for (key, value) in D.items(): # Key/value-pair tuples iteration
print(key, '=>', value)
```

The second loop uses tuple assignment, which unpacks each pair into two variables. To understand what `items` returns, you need to know about tuples first.

## Tuples

A tuple is roughly a list that cannot change. Tuples are sequences like lists, but they are immutable like strings. Tuples represent fixed collections, such as the parts of a specific calendar date. They are written in parentheses instead of square brackets. They support any object type, any nesting, and the usual sequence operations:

```
>>> T = (1, 2, 3, 4) # A 4-item tuple
>>> len(T) # Length
4
>>> T + (5, 6) # Concatenation: a new tuple
(1, 2, 3, 4, 5, 6)
>>> T[0], T[1:] # Indexing, slicing, and more
(1, (2, 3, 4))
```

Tuples have a few methods, though far fewer than lists:

```
>>> T.index(4) # Tuple methods: 4 appears at offset 3
3
>>> T.count(4) # 4 appears once
1
```

The main difference is that a tuple cannot change after creation. It is an immutable sequence. A one-item tuple needs a trailing comma, or it looks like a plain expression in parentheses:

```
>>> T[0] = 2 # Tuples are immutable
TypeError: 'tuple' object does not support item assignment
>>> T = (2,) + T[1:] # Make a new tuple for a new value
>>> T
(2, 2, 3, 4)
```

Tuples support mixed types and nesting, but they do not grow or shrink:

```
>>> T = 'hack', 3.0, [11, 22, 33]
>>> T
('hack', 3.0, [11, 22, 33])
>>> T[1]
3.0
>>> T[2][1]
22
>>> T.append(4)
AttributeError: 'tuple' object has no attribute 'append'
```

The parentheses around a tuple can often be left out, as shown here. Where commas do not have another meaning, the commas are what build the tuple. That is also why the REPL shows results in parentheses when you enter several comma-separated items.

### Why use tuples?

Tuples are less common than lists in practice, and they offer fewer operations. Their immutability is the point. A list passed around a program can be changed anywhere. A tuple cannot. That gives you a kind of integrity constraint, which helps in larger programs. Later in the book you will meet named tuples, an extension built on top of tuples.

## Files

File objects are how Python code reads and writes the content of files on your computer. You can use them for text notes, audio, spreadsheets, saved emails, and anything else stored on your device. Files are core objects, but they have no literal syntax. You create one by calling the built-in `open` function with a filename and any options you need.

To create a text output file, pass the name and the `'w'` mode string. Python writes the newline character `\n` in a portable way when it moves text to and from files:

```
>>> f = open('data.txt', 'w') # Open a new file in text-output mode
>>> f.write('Hello\n') # Write strings of characters to it
6
>>> f.write('world!\n') # Return number of items written
7
>>> f.close() # Close to flush output buffers to disk
```

The filename can be a full path if the file lives elsewhere. To read the file back, reopen it in `'r'` mode. Reading is also the default if you leave the mode out. Read the content into a string. A file's content is always a string in your script, whatever kind of data the file holds:

```
>>> f = open('data.txt') # Open an existing file in text-input mode
>>> text = f.read() # Read entire file into a string
>>> text
'Hello\nworld!\n'
>>> print(text) # print interprets control characters
Hello
world!
>>> text.split() # File content is always a string
['Hello', 'world!']
```

File objects have more methods. The `read` method accepts an optional size limit. The `readline` method reads one line at a time. The `seek` method moves to a new position in the file. The best way to read a text file is often not to read it directly. Files support iteration, so a `for` loop reads them line by line:

```
>>> for line in open('data.txt'): # Display lines in a file
print(line.rstrip()) # Single spaced (sans \n)
```

To explore the full set of file methods, run `dir` on an open file, then run `help` on the names that come back.

### Unicode and byte files

The examples above depend on the platform's default Unicode encoding. Text files always encode strings when they write and decode them when they read. For plain ASCII text, this rarely matters, because the bytes map to and from the text unchanged. Richer data can behave differently depending on the file interface.

Python separates text from binary data in files. Text files represent content as normal `str` strings and handle encoding and decoding automatically. Binary files represent content as `bytes` and give you the raw content unchanged. Binary files suit media, data written by C programs, and similar content. What you send and receive is the literal content, whether it is encoded text or a JPEG image.

To open a file in binary mode, add a `b` to the mode. On Windows, the line ending becomes `\r\n` instead of `\n`, because Windows newlines differ from Unix:

```
>>> bf = open('data.bin', 'wb')
>>> bf.write(b'h\xFFa\xEEc\xDDk\n') # Write binary data in a bytes
8
>>> bf.close()
>>> open('data.bin', 'rb').read() # Read binary data to a bytes
b'h\xffa\xeec\xddk\n'
```

For text files, you should also ask which encoding the file uses. A text file can use any Unicode encoding. This is more likely when the file came from another system or from the web. For portable programs, state the encoding explicitly. Pass an `encoding` name to `open` to force one:

```
>>> tf = open('unidata.txt', 'w', encoding='utf-8')
>>> tf.write('h\u00c4ck') # Encodes to UTF-8
6
>>> tf.close()
```

Reading with the same encoding, or a compatible one, returns the same characters you wrote. The file itself stores UTF-8 bytes, but your code usually does not need to care:

```
>>> open('unidata.txt', 'r', encoding='utf-8').read() # Decodes from UTF-8
'hÄck'
>>> open('unidata.txt', 'rb').read() # Raw encoded text
b'\xf0\x9f\x90\x8dh\xc3\x84ck\xf0\x9f\x91\x8f'
```

Sometimes text arrives from another source, such as an email or a network connection. Then you encode or decode it yourself:

```
>>> 'hÄck'.encode('utf-8')
b'h\xc3\x84ck'
>>> b'h\xc3\x84ck'.decode('utf-8')
'hÄck'
```

Python also supports non-ASCII file names, and that mostly happens automatically.

### Other file-like tools

The `open` function handles most file work. For advanced jobs, Python offers more file-like tools, including pipes, FIFOs, sockets, keyed-access files, persistent object shelves, descriptor-based files, and database interfaces. This book does not cover most of them. You will find them useful once you program Python seriously.

## Other object types

Some core objects get less attention than the others, but they are still useful for their roles. The rest of this section covers them.

### Sets

Sets are neither mappings nor sequences. A set is an unordered collection of hashable, or immutable, objects, and each object is stored only once. You create a set with the `set` function on a sequence or other iterable, or with a set literal. Sets support the usual mathematical operations:

```
>>> X = set('hack') # Sequence => set
>>> Y = {'a', 'p', 'p'} # Set literal
>>> X, Y
({'c', 'k', 'a', 'h'}, {'p', 'a'})
>>> X & Y, X | Y # Intersection, union
({'a'}, {'p', 'c', 'k', 'h', 'a'})
>>> X - Y, X > Y # Difference, superset
({'c', 'k', 'h'}, False)
```

Sets are handy even for programmers who are not mathematical. They filter out duplicates, find differences, and test equality without sorting:

```
>>> list(set([3, 1, 2, 1, 3, 1])) # Duplicates removal
[1, 2, 3]
>>> set('code') - set('hack') # Collection difference
{'d', 'o', 'e'}
>>> set('code') == set('deoc') # Order-neutral equality
True
```

A set is mutable, so you can change it with methods such as `remove` and `add`. The items inside a set must be immutable.

### Booleans and None

Python has two Boolean objects, `True` and `False`. They are essentially the integers 1 and 0 with custom display. Python also has `None`, a placeholder that often initializes names and objects. It also marks a function result that is absent:

```
>>> 1 > 2, 1 < 2 # Booleans
(False, True)
>>> bool('hack') # All objects have a Boolean value
True # Nonempty means True
>>> X = None # None placeholder
>>> print(X) # But None is a thing
None
>>> L = [None] * 100 # Initialize a list of 100 Nones
>>> L
[None, None, None, None, None, None, None, None, None, None, None, None,
None, None, None, None, None, None, None, None, …etc: a list of 100 Nones…]
```

### Types

The `type` built-in returns the type of an object, and that result is itself an object. Here is what it returns for a list:

```
>>> L = [1, 2, 3]
>>> type(L) # The type of a list object
<class 'list'>
>>> type(type(L)) # Even types are objects!
<class 'type'>
```

Code can use `type` to check the types of the objects it handles. There are at least three ways to do it in a script:

```
>>> type(L) == type([]) # Type testing, if you must…
True # Using a real object
>>> type(L) == list # Using a type name
True
>>> isinstance(L, list) # The object-oriented way
True
```

Type checking is almost always the wrong move in Python. It restricts your code to one type. Code without such checks can often work across a whole range of types. This is the polymorphism described earlier. Python does not use type declarations, so you code to object interfaces, which are the operations an object supports. You care what an object does, not what it is.

Checking types is supported, and rare cases do need it. Still, programmers coming from stricter languages often check types out of habit, and that habit works against Python's style. Polymorphism is the key to writing Python well.

### Type hinting

Python has also added a type-declaration feature called type hinting. It grew out of function annotations and was inspired by the TypeScript dialect of JavaScript. Syntax and module extensions let you name expected types for function arguments and results, class attributes, and simple variables. External type checkers such as mypy can read these hints:

```
>>> x: int = 1 # Optional hint: x might be an integer
>>> x = 'anything' # But it doesn't have to be!
```

Type hints are for documentation and third-party tools. The Python language does not require them and does not use them itself. Hints are close to comments in value. They also sit a little against Python's core ideas. For beginners, type hinting is an optional topic that is best left until you are comfortable with dynamic typing. This book covers it only briefly.

Type hinting does not make Python statically typed. A statically typed Python would not be Python. Some programmers add hints out of habit, but good Python code relies on polymorphism instead.

### User-defined objects

Classes let you define new object types. Suppose you want an object that models workers in a company. No core type does that, so a user-defined class fits. The `class` statement is covered later in the book. Here is the outline of such a class:

```
>>> class Worker:
…stay tuned for Part VI…
```

A class like this would define attributes, such as `name` and `pay`, and behavior in custom methods. Calling the class creates instances of the new type. The class's methods then process those instances:

```
>>> sue = Worker('Sue Jones', 60000) # Make two new objects
>>> bob = Worker('Bob Smith', 50000) # Each has a name and pay
>>> sue.lastName() # Call a method to process sue
'Jones'
>>> bob.lastName() # Call a method to process bob
'Smith'
>>> sue.giveRaise(.10) # Update sue's pay
>>> sue.pay # Display sue's pay
66000.0
```

This style is called object-oriented, because each function in a class has an implied subject. Class-based objects use built-in objects internally. You could describe workers with dictionaries and lists instead. Classes give operations meaningful names and add structure. They also support inheritance, which lets you extend software by writing new classes rather than changing code that already works.

### Everything else

Everything you process in Python is an object. Not everything is part of the core toolset, though. Functions, modules, classes and compiled code relate to program execution. Other objects come from imported modules rather than language syntax. These often have application-specific roles, such as text patterns, database interfaces and network connections.

Core objects are the workhorses of nearly every Python script. They are also the basis for many larger, non-core objects. Keep in mind that these objects are not all object-oriented. That idea requires the `class` statement, which comes later.

## Chapter summary

This chapter previewed Python's core object types and the operations you can run on them. You met generic operations that work on many types, such as indexing and slicing. You also met type-specific methods, such as string `split` and list `append`. Key terms include immutability, sequence and polymorphism.

Python's core types are more flexible than what lower-level languages offer. Lists and dictionaries nest, grow and shrink, and hold objects of any type. Their memory is created and cleaned up as you go. Strings and files work together for binary and text data. The iteration protocol, the object-oriented style, and the risks of type hinting also appeared. The `if` and `for` statements come up again in the next chapters.

This chapter skipped many details to give you a first tour. Do not worry if not everything made sense yet. The next chapters go deeper, with a second pass over each core type.

## Checkpoint questions

1. Name four of Python's core object types.

<details><summary>Answer</summary>

Numbers, strings, lists, dictionaries, tuples, files and sets. Any four of these are correct.

</details>

2. What does immutable mean, and which three core types are immutable?

<details><summary>Answer</summary>

An immutable object cannot be changed after it is created. Numbers, strings and tuples are immutable.

</details>

3. For `S = 'Code'`, what does `S[1:3]` return?

<details><summary>Answer</summary>

It returns `'od'`. A slice runs from offset 1 up to, but not including, offset 3.

</details>

4. What is the difference between a sequence and a mapping?

<details><summary>Answer</summary>

A sequence keeps its items in a left-to-right order and fetches them by position. A mapping stores values by key. Python's dictionary is the only mapping among the core types.

</details>

5. Why is checking types with `type(L) == list` usually the wrong approach?

<details><summary>Answer</summary>

It limits your code to one type. Code that depends only on what an object can do, which is polymorphism, works with many more types.

</details>

6. What happens if you assign `L[99] = 1` to a three-item list?

<details><summary>Answer</summary>

Python raises an `IndexError` with the message "list assignment index out of range." To grow a list, use a method such as `append`.

</details>

## Sources and review notes

- Source: *Learning Python*, 6th edition (`learning-python-6th-edition`). Chapters used are listed in each section.
- Source: `learning-python-6th-edition`, chapter 4, "Introducing Python Objects."
