---
id: "c03-17"
title: "3.17 Exceptions, Unicode, managed attributes and decorators"
sidebar_label: "3.17 Exceptions, Unicode, managed attributes and decorators"
sidebar_position: 17
description: "Exception coding details and odds, Unicode and byte strings, managed attributes and decorators, the advanced language tools used by real infrastructure libraries."
status: "drafted"
tier: "2"
level: "I"
lab_venue: "Mac"
---

# 3.17 Exceptions, Unicode, managed attributes and decorators

This chapter goes deeper into material that chapter 3.1 only introduces. You will meet it again whenever you read or write the Python behind schedulers, operators, exporters and training launchers.

## The try statement

The `try` statement is how your code catches exceptions. If an exception happens while the main block runs, Python jumps to one of the handlers and carries on from there. Those handlers can be `except`, `else`, `finally`, and `except*` clauses nested under the `try`. Each clause has its own job and its own rules for how it may be combined.

Because of that, we will learn the common roles of `try` one at a time. We will put the pieces together at the end of this section. Python once used separate statements for these jobs, so the combined form is easier to read once the parts are clear.

We will also defer the `except*` clause to the next chapter. It works with exception objects, and it is rarely needed in everyday code. For now, the fundamentals matter most.

### try statement clauses

A `try` statement can have several clauses after its header. Table 34-1 lists every form. It works as both a reference and a preview of what follows.

| Clause form | Interpretation |
| --- | --- |
| `except:` | Catch all (or all other) exception types |
| `name:` | Catch a specific exception only |
| `name` as `var`: | Catch the listed exception and assign its instance |
| `(name1, name2):` | Catch any of the exceptions listed in a tuple |
| `(name1, name2)` as `var`: | Catch any listed exception and assign its instance |
| `else:` | Run if no exceptions are raised in the `try` block |
| `finally:` | Always perform this block on exit, exception or not |
| `nonempty except forms`… | Catch multiple exceptions in a group (Chapter 35) |

A `try` must use at least one of these clauses. It can have any number of `except` clauses. You can code an `else` only when at least one `except` exists, and there can be only one `else` and one `finally`. A `finally` may appear alongside `except` and `else`, and its ordering rules come later in this chapter.

We will look at the `as var` form when we reach the `raise` statement. It gives you access to the object that was raised.

### The except and else clauses

Syntactically, the `try` is a compound statement with several parts. It starts with a `try` header line, followed by an indented block of statements. After that come clauses that each name a condition and give a block of code to handle it. In its most common form, you write one or more `except` clauses and an optional `else` at the end. Line up `try`, `except`, and `else` at the same indentation level:

```python
try:
    statements # Run this main action first
except name1:
    statements # Run if name1 is raised during the try block
except (name2, name3):
    statements # Run if name2 or name3 occur in the try
except name4 as var:
    statements # Run if name4 is raised, and assign it to var
except:
    statements # Run for all other exceptions raised
else:
    statements # Run if no exception was raised in the try block
```

The block under the `try` header is the main action. It is the code you want to run, wrapped in handlers. The `except` clauses handle exceptions raised during that block. The optional `else` clause runs only when the `try` block finishes without an exception.

Each `except` names the exceptions it catches. A single name catches just that exception. A tuple catches any exception in the tuple. An `except` with no name matches all exceptions, or all the ones not caught above it. A nonempty `except` can also name a variable after `as`. Python assigns the exception object to that variable.

### How try statements run

When Python enters a `try`, it records where it is so it can return if something goes wrong. It runs the statements under the `try` header first. What happens next depends on two questions. Was an exception raised? And does that exception match one the `try` is watching for?

- **Exception and match.** An exception occurs in the `try` block, and one of the `except` clauses names it. Python jumps back to the topmost matching `except` clause. It assigns the exception object to the `as` variable, if one is given. After the handler runs, control continues below the whole `try` statement. If the handler raises another exception, the search starts again from that point.
- **Exception and no match.** An exception occurs, but no clause names it. The exception moves up to the next `try` that was entered earlier and that matches it. If no matching `try` exists, Python prints a default error message and ends the program. The REPL is the exception to that last part.
- **No exception.** The `try` block finishes cleanly. Python runs the `else` clause if one exists, then continues below the whole `try` statement. If the `else` block raises an exception, the propagation process starts again.

In short, `except` clauses catch matching exceptions raised while the `try` block runs. The `else` clause runs only when that block raises nothing. Exceptions match `except` clauses through class relationships. A subclass matches its superclass, and the empty `except` matches any exception. We will explore those class rules in the next chapter.

An `except` is a focused handler. It catches only exceptions that happen inside its `try` block. The block may call functions defined elsewhere, though, so the source of an exception may sit outside the `try` statement itself. A `try` block can call large amounts of code, including code with `try` statements of its own. Those inner `try` statements are searched first. Where an exception goes depends on what ran before it. Chapter 36 of the book explores this more.

If you add a `finally` clause, its block runs in all three cases above. We will see that shortly. First, let us look at some common variations of exception-catching clauses.

### Catching many exceptions with a tuple

An `except` clause can list several exceptions in a parenthesized tuple. It catches any one of them. Python checks `except` clauses from top to bottom. So a tuple has the same effect as one `except` clause per exception. The difference is that you write the shared handler body only once.

```python
try:
    …
except NameError:
    …
except IndexError:
    …
except (AttributeError, TypeError, SyntaxError):
    …
```

If an exception is raised while this `try` block runs, Python returns to the `try` and looks for the first `except` that names it. It checks clauses from top to bottom, and left to right within a tuple. It runs the first clause that matches. If none match, the exception moves past this `try`.

Parentheses are required around the tuple. Adding `as` to this form lets you check which exception occurred:

```python
try:
    …
except (AttributeError, TypeError, SyntaxError) as What:
    …and check What…
```

### Catching all exceptions with empty except and Exception

An `except` clause with no exception name catches every exception not listed above it. It works as a catchall. If you want a general handler that runs when no other clause matches, an empty `except` does the job.

```python
try:
    …
except NameError:
    … # Handle NameError
except IndexError:
    … # Handle IndexError
except:
    … # Handle all other exceptions
else:
    … # Handle the no-exception case (preview)
```

The empty `except` acts as a wildcard. Because it catches everything, your handlers can be as general or as specific as you need. It is handy when you work interactively in a REPL, or when code must recover no matter what occurs. The following catches everything by naming nothing:

```python
try:
    …
except:
    … # Catch all possible exceptions
```

The empty `except` has costs, though. It can catch unexpected exceptions and intercept events that another handler needs. Even system exit calls and Ctrl+C interrupts work by raising exceptions. You usually want those to pass through.

It can also hide real programming mistakes. You may never see a bug until a user reports it, which is too late. We will come back to this as a gotcha at the end of this part of the book. For now, use it with care.

Python offers a safer alternative. Catching the built-in `Exception` has nearly the same effect as an empty `except`. The difference is that it will not catch exceptions related to system exits and Ctrl+C.

```python
try:
    …
except Exception:
    … # Catch all possible exceptions - except exits
```

This works because an exception matches a clause when it is a subclass of the named class. `Exception` is the superclass of nearly every exception you should catch this way. This form keeps most of the convenience of the empty `except`. It avoids catching exit events, and it lets you inspect the exception with `as`. It still has some of the same risks, though. It can mask programming errors and ignore them silently.

### Catching the no-exception case with else

The `else` keyword appears in three places in Python: in `if` selections, in `for` and `while` loops, and in `try` handlers. In a `try`, `else` runs when no exception occurs. It does not run for exceptions that go unmatched. That is the job of the empty `except` from the previous section. The role looks different from the other two, but the context is different too.

New Python users often miss why this clause matters. Without it, you cannot tell whether control passed a `try` because nothing went wrong, or because an error was handled. Either way, you land after the `try`:

```python
try:
    …run code…
except IndexError:
    …handle exception…
# Did we get here because the try failed or not?
```

You could set a Boolean flag and check it later, but that adds admin code. In a loop, `else` makes the exit cause clear when there is no `break`. The `else` clause does the same job in a `try`. It makes the outcome clear with very little extra code:

```python
try:
    …run code…
except IndexError:
    …handle exception…
else:
    …no exception occurred…
```

You can almost copy an `else` clause by moving its code into the `try` block:

```python
try:
    …run code…
    …no exception occurred…
except IndexError:
    …handle exception…
```

This approach can misclassify errors, though. If the "no exception occurred" action raises an `IndexError` itself, it counts as a failure of the `try` block. It then wrongly triggers the handler below. That is unlikely, but it can happen. An explicit `else` clause makes the logic clear. Its `except` handlers run only for real failures in the wrapped code. They do not run for failures in the no-exception action.

### Example: default behavior

Python's control flow can be easier to see in real code than in English. So let us run a few simple examples in files. Exceptions that no `try` catches move up to the top of the Python process. Python then runs its default logic. It ends the program and prints a standard error message.

The module `crashware.py` in Example 34-1 raises a divide-by-zero exception on purpose:

```python
def gobad(x, y):
    return x / y
def gosouth(x):
    print(gobad(x, 0))
if __name__ == '__main__': gosouth(1)
```

The program does not catch the exception, so Python stops it and prints a message. The paths below are shortened, and some code-pointer lines are removed to save space:

```text
$ python3 crashware.py
Traceback (most recent call last):
  File "/…/LP6E/Chapter34/crashware.py", line 7, in <module>
    if __name__ == '__main__': gosouth(1)
  File "/…/LP6E/Chapter34/crashware.py", line 5, in gosouth
    print(gobad(x, 0))
  File "/…/LP6E/Chapter34/crashware.py", line 2, in gobad
    return x / y
ZeroDivisionError: division by zero
```

The message has two parts. The first is a stack trace, which starts with "Traceback." The second names the exception and gives its details. The trace lists every active line when the error occurred, from oldest to newest. Here, the bad divide happens on the last entry: line 2 of `crashware.py`, a `return` statement.

Python reports every error by raising an exception, so exceptions sit at the heart of error handling and debugging. Even typos often produce a `SyntaxError` or another exception. That happens when a file is imported or run, because the compiler runs then.

By default, programming errors produce a useful display like the one above, and it helps you track down the problem. Some interfaces now add pointers to the bad expression. They also add "Did you?" tips. Those tips are worth weighing for yourself as you gain experience:

```text
$ python3
>>> import crashware
>>> crashware.gobad(1, 0)
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/…/LP6E/Chapter34/crashware.py", line 2, in gobad
    return x / y
    ~~^~~
ZeroDivisionError: division by zero
```

Often, this standard message is all you need. For harder debugging, you can catch exceptions with `try`. You can also use debugging tools such as the `pdb` standard-library module, introduced in Chapter 3 of the book.

### Example: catching built-in exceptions

Python's default error handling is often exactly what you want. In a top-level script, an error should usually stop the program right away. Many programs need nothing more specific than that.

Sometimes, though, you want to recover from an error instead. If you do not want Python to end your program, wrap the logic in a `try`. This matters for network servers, which must keep running. The file `kaboom.py` in Example 34-2 catches and recovers from a `TypeError`. Python raises it when you join a list and a string with `+`. That operator expects the same sequence type on both sides.

```python
def kaboom(x, y):
    print(x + y) # Trigger TypeError
def serve(n=2): # Simulate long-running task
    for i in range(n):
        try:
            kaboom([1, 2], 'hack')
        except TypeError: # Catch and recover here
            print('Hello world!')
        print('Resuming here...') # Continue here if exception or not
if __name__ == '__main__': serve()
```

When the exception occurs inside `kaboom`, control jumps to the `except` clause, which prints a message. A caught exception is finished, so the program continues below the `try` instead of stopping. Your script recovers from the error:

```text
$ python3 kaboom.py
Hello world!
Resuming here...
Hello world!
Resuming here...
```

Once you catch an error, control resumes where you caught it, after the `try`. There is no direct way to go back to the spot where the exception happened, here inside `kaboom`. An exception acts more like a simple jump than a function call. There is no way to return to the scene of the problem.

### The finally clause

The other main form of `try` handles cleanup, also called finalization or termination. This job is only loosely related to exceptions. If a `finally` clause is part of a `try`, Python always runs its block on the way out. That holds whether an exception occurred or not. The `finally` does not catch exceptions. It works around them.

In its simplest form, the statement looks like this:

```python
try:
    statements # Run this action first
finally:
    statements # Always run this code on the way out
```

Python starts by running the `try` block. What happens next depends on whether an exception occurs, and on which other clauses are present.

- **Exception and match.** An `except` clause catches the exception. Python runs that `except` block, then the `finally` block. The program then resumes below the whole `try`. The `finally` also runs if the `except` raises a new exception.
- **Exception and no match.** No `except` catches the exception. Python still runs the `finally` block. It then keeps propagating the exception to an earlier `try` or to the top-level handler. The `finally` does not stop the exception. It keeps being raised after the `finally` block finishes.
- **No exception.** The `try` block finishes cleanly. Python runs the `else` block if one exists, then the `finally` block. The program resumes below the whole `try`. The `finally` also runs if the `else` raises a new exception.

The `try`/`finally` form is useful when an action must always happen after some code, no matter what. It can guarantee cleanup such as closing a file or disconnecting from a server.

`finally` can appear in the same statement as `except` and `else`. So there is really one `try` statement with several optional clauses. Its ordering rules set it apart, so many people treat `finally` as a separate tool. Either way, its job is the same: specify cleanup that always runs, regardless of exceptions.

The `with` statement covers the same exit work with an object-based approach. It also supports entry actions. It works only with objects that implement the context-manager protocol, though. We will meet it later in this chapter.

### Example: coding termination actions with try/finally

We wrote a few simple `try`/`finally` examples in the last chapter. The following example shows a typical use. The file `closer.py` in Example 34-3 defines an exception and a function that raises it. The main code opens a file and calls the function inside a `try`:

```python
class MyError(Exception): pass
def stuff(file):
    file.write('Hello?') # May be delayed in file buffer
    raise MyError() # <= Enable or disable me with a #
if __name__ == '__main__':
    file = open('temp.txt', 'w') # Open an output file (this can fail too)
    try:
        stuff(file) # Raises exception
    finally:
        file.close() # Always close file to flush output buffers
    print('Am I reached?') # Continue here only if no exception
```

When the function raises its exception, control jumps back and runs the `finally` block. That block closes the file. The exception then moves on to another `try` or to the top-level handler, which prints the standard message and stops the program. So the `print` after the `try` never runs:

```text
$ python3 closer.py
Traceback (most recent call last):
  File "/…/LP6E/Chapter34/closer.py", line 10, in <module>
    stuff(file) # Raises exception
  File "/…/LP6E/Chapter34/closer.py", line 5, in stuff
    raise MyError() # <= Enable or disable me with a #
MyError
```

If the function does not raise, the `finally` still closes the file. Then the program continues below the whole `try` statement. To see this, disable the `raise` line by adding a `#` in front of it:

```text
$ python3 closer.py
Am I reached?
```

Here, the `try` with `finally` makes sure the file closes whether the function raises or not. Later code can then trust that the output buffer has reached the disk. The same structure can close server connections, GUI windows, and similar resources.

This example's function is not very useful, since it always raises. Still, wrapping calls in `try`/`finally` is a good habit for cleanup that must always run. Nothing helps if Python itself crashes, but that is rare. Python detects errors while it runs, so hard crashes usually come from linked-in C extension code.

Notice that the user-defined exception here is a class. Exceptions must be class instances. We will see the reasons in the next chapter.

CPython closes file objects automatically when they are garbage collected. That is handy for temporary files you never assign to a variable. Still, you cannot always predict when garbage collection runs. This is especially true in large programs and in other Python implementations, which use different policies. The `try` statement makes the close explicit. It closes the file when the block exits, with or without an exception.

### Combined try clauses

For about the first fifteen years of Python, the `try` came in two flavors. They were two separate statements. One used `finally` to guarantee cleanup code ran. The other used `except` blocks to catch and recover from specific exceptions, and could end with an `else` for the no-exception case.

So `finally` could not be mixed with `except` and `else`. That was partly due to implementation issues. It was also because mixing them seemed confusing. Catching and recovering from errors seemed unrelated to cleanup.

Over time, the two statements merged. Today you can mix `finally`, `except`, and `else` in one statement. Java had a similar feature, and Python borrowed the idea. The most complete form of `try` looks like this:

```text
try: # Combined try statement
    main-action
except Exception1: # Catch specific exceptions
    handler1
except Exception2:
    handler2
except: # Catch all (other) exceptions
    handler3
else: # No-exception handler
    handler4
finally: # The finally encloses all
    finally-block
```

The `main-action` block runs first, as usual. If it raises an exception, Python tests each `except` block in turn for a match. `handler1` runs for `Exception1`, `handler2` for `Exception2`, and `handler3` for all others. If no exception is raised, `handler4` runs.

The `finally-block` runs once, after the main action and any handler have finished. That holds even when an error or `raise` in an `except` or `else` block causes a new exception.

Even in this mixed form, `finally` does not end the exception. If an exception is still active when the `finally-block` runs, it keeps propagating after the block. Control then jumps to an earlier `try` or to the top-level handler. If no exception is active, control resumes after the whole `try` statement.

So `finally` always runs. That is true when an exception happened and was handled, when one happened and was not handled, when none happened, and when a new exception came from a handler.

### Combined-clause syntax rules

When the clauses are combined, the `try` must have either an `except` or a `finally`. The parts must appear in this order, where "->" means "is followed by":

```text
try -> except -> else -> finally
```

The `else` and `finally` are optional. You can have zero or more `except` clauses. But an `else` requires at least one `except`. The `try` statement really has two parts: the `except` clauses with an optional `else`, and the `finally`.

More precisely, the combined statement has two formats. In the formats below, square brackets mark optional parts, and a star means any number of the item before it:

```text
try: # Format 1
    statements
except [type [as value]]:
    statements
[except [type [as value]]:
    statements]*
[else:
    statements]
[finally:
    statements]
```

```text
try: # Format 2
    statements
finally:
    statements
```

Because of these rules, an `else` needs at least one `except`. You can always mix `except` with `finally`, with or without an `else`. You can mix `finally` with `else` only if an `except` also appears. An `except` can leave out the exception name to catch everything. It can then run a `raise` statement to reraise the current exception. If you break any of these ordering rules, Python raises a syntax error before your code runs.

### Combining finally and except by nesting

You can get the same effect by nesting. Put a `try`/`except` inside the `try` block of a `try`/`finally`. Chapter 36 of the book explores nesting more fully. The nested form below behaves like the combined form shown above:

```text
try: # Nested equivalent to combined form
    try:
        main-action
    except Exception1:
        handler1
    except Exception2:
        handler2
    except:
        handler3
    else:
        handler4
    finally:
        finally-block
```

The `finally` block still runs on the way out, whatever the main action did. It runs regardless of the handlers inside the nested `try`. Trace the four cases from the previous section to see that this holds. Because an `else` always needs an `except`, the nested form follows the same mixing rules as the combined one.

The nested version can look more obscure to some people. It also takes more code. The combined form costs just one extra line of `finally:` plus extra indentation. Mixing `finally` into the same statement often makes code easier to write and read. Opinions differ on that, so choose what your team finds clear.

### Combined-clauses example

To show how `finally` mixes with other `try` clauses, Example 34-4 runs four common cases. The script `trycombos.py` prints a message for each one:

```python
sep = '-' * 45 + '\n'
print(sep + 'EXCEPTION RAISED AND CAUGHT')
try:
    x = 'hack'[99]
except IndexError:
    print('except run')
finally:
    print('finally run')
print('after run')
print(sep + 'EXCEPTION NOT RAISED')
try:
    x = 'hack'[3]
except IndexError:
    print('except run')
finally:
    print('finally run')
print('after run')
print(sep + 'EXCEPTION NOT RAISED, WITH ELSE')
try:
    x = 'hack'[3]
except IndexError:
    print('except run')
else:
    print('else run')
finally:
    print('finally run')
print('after run')
print(sep + 'EXCEPTION RAISED BUT NOT CAUGHT')
try:
    x = 1 / 0
except IndexError:
    print('except run')
finally:
    print('finally run')
print('after run')
```

Running it produces this output. Trace the code yourself to see how each of the four tests reaches its result:

```text
$ python3 trycombos.py
---------------------------------------------
EXCEPTION RAISED AND CAUGHT
except run
finally run
after run
---------------------------------------------
EXCEPTION NOT RAISED
finally run
after run
---------------------------------------------
EXCEPTION NOT RAISED, WITH ELSE
else run
finally run
after run
---------------------------------------------
EXCEPTION RAISED BUT NOT CAUGHT
finally run
Traceback (most recent call last):
  File "/…/LP6E/Chapter34/trycombos.py", line 38, in <module>
    x = 1 / 0
ZeroDivisionError: division by zero
```

This example uses built-in operations to trigger exceptions, or to avoid them. It depends on Python checking for errors while code runs. The next section shows how to raise exceptions yourself.

## The raise statement

To trigger an exception on purpose, write a `raise` statement. Its general form is simple. It is the word `raise`, optionally followed by a class or an instance of one:

```text
raise instance # Raise an instance of a class
raise class # Make and raise an instance of a class
raise # Reraise the most recent exception
```

Exceptions are always class instances now. So the first form is the most common. You give an instance directly, created before the `raise` or inside the statement. If you pass a class instead, Python calls it with no constructor arguments. That form is the same as adding parentheses after the class name. The last form reraises the most recent exception. Handlers use it to pass along an exception they have caught.

> Note: Before Python 2.6, exceptions could be plain strings, with an optional data item in `raise`. Classes replaced strings to add features and categories. Strings were simpler, though. They spared newcomers from learning classes before they could handle errors.

### Raising exceptions

Two forms of `raise` with a built-in exception are equivalent. Both raise an instance of the named class. The first creates the instance implicitly:

```python
raise IndexError # Class (instance created)
raise IndexError() # Instance (created in statement)
```

You can also create the instance ahead of time. `raise` accepts any object reference, so these both raise `IndexError`:

```python
exc = IndexError() # Create instance ahead of time
raise exc
excs = [IndexError, TypeError]
raise excs[0]
```

The instance you raise can also be reached inside the `try` that catches it, as the next section shows.

### The except as hook

When an exception is raised, Python sends the raised instance along with it. If an `except` clause has an `as` name, that name receives the instance that `raise` or Python produced:

```python
try:
    …
except IndexError as X: # X assigned the raised instance object
    …
```

The `as` part is optional. Without it, the instance is simply not stored in a name. Including it lets the handler read data from the instance and call methods on its class.

This works for your own exceptions too. Pass constructor arguments to the exception class. The handler can then read them through the instance:

```python
class MyExc(Exception): pass
try:
    raise MyExc('oops') # Exception class with constructor args
except MyExc as X: # Instance attributes available in handler
    print(X.args) # Prints ('oops',)
```

We will save the details for the next chapter, since they belong to exception classes.

Whatever raised it, an exception is always a class instance. At most one is active at a time, leaving aside the `except*` groups of Chapter 35. Once an `except` clause catches an exception, that exception ends. It does not propagate to another `try`. The only exception is when another `raise` or error reraises it.

### Scopes and except as

Chapter 17 of the book introduced a scope issue. Now that we have seen the `as` name in action, we can settle it. The name used in an `except` clause's `as` is local to that `except` block. It is not available after the block exits. This works much like a loop variable in a comprehension:

```python
$ python3
>>> try:
...     1 / 0
... except Exception as X: # The "as" localizes names to except block
...     print(X)
...
division by zero
>>> X
NameError: name 'X' is not defined
```

Comprehension loop variables are different in one way. The `as` name is also removed after the `except` block exits. Python does this because the name would otherwise keep a reference to the call stack. That reference would delay garbage collection and hold on to memory. The removal happens even if the name was used for something else in the surrounding scope. It is a stronger rule than the one used for comprehensions:

```python
>>> X = 99
>>> {X for X in 'hack'} # Comprehensions localize but don't remove
{'a', 'c', 'k', 'h'}
>>> X
99
>>> X = 99
>>> try:
...     1 / 0
... except Exception as X: # But "as" localizes _and_ removes on exit!
...     print(X)
...
division by zero
>>> X # Where did my X go? – an odd boundary case
NameError: name 'X' is not defined
```

So use unique names in your `except` clauses, even though they are scoped. If you need the exception after the `try`, assign it to another name that Python will not remove:

```python
>>> try:
...     1 / 0
... except Exception as X: # Python removes this reference
...     print(X)
...     saveit = X # Assign exc to retain exc if needed
...
division by zero
>>> X
NameError: name 'X' is not defined
>>> saveit
ZeroDivisionError('division by zero',)
```

### Propagating exceptions with raise

A `raise` with no exception named is more useful than it looks. It reraises the exception that is currently active. You use this when you need to catch an exception, do something, and still let it continue:

```python
>>> try:
...     raise IndexError('code') # Exceptions remember arguments
... except IndexError:
...     print('propagating')
...     raise # Reraise most recent exception
...
propagating
Traceback (most recent call last):
  File "<stdin>", line 2, in <module>
IndexError: code
```

The reraised exception moves up to a higher handler. If none exists, the top-level default handler stops the program with a standard message. The argument you passed to the exception class appears in that message. You will learn why in the next chapter.

### Exception chaining with raise from

Sometimes one exception is raised because of another. That can be deliberate, or it can come from a new program error. To show the full picture, `raise` accepts an optional `from` clause:

```python
raise newexception from otherexception
```

The expression after `from` names another exception class or instance. Python attaches it to the new exception's `__cause__` attribute. If the new exception goes uncaught, Python prints both exceptions in the standard message:

```python
>>> try:
...     1 / 0
... except Exception as E:
...     raise TypeError('Bad') from E # Explicitly chained exceptions
...
Traceback (most recent call last):
  File "<stdin>", line 2, in <module>
ZeroDivisionError: division by zero
The above exception was the direct cause of the following exception:
Traceback (most recent call last):
  File "<stdin>", line 4, in <module>
TypeError: Bad
```

An error inside an exception handler causes a similar chain automatically. Python attaches the earlier exception to the new one's `__context__` attribute. It shows that exception in the message too, if the new one goes uncaught:

```python
>>> try:
...     1 / 0
... except:
...     badname # Implicitly chained exceptions
...
Traceback (most recent call last):
  File "<stdin>", line 2, in <module>
ZeroDivisionError: division by zero
During handling of the above exception, another exception occurred:
Traceback (most recent call last):
  File "<stdin>", line 4, in <module>
NameError: name 'badname' is not defined
```

Attached exceptions can have causes of their own. So a chain can be any length, and the message displays all of it. Explicit and implicit chaining both let you see every exception involved. Here is a chain of three:

```python
>>> try:
...     try:
...         raise IndexError()
...     except Exception as E:
...         raise TypeError() from E
... except Exception as E:
...     raise SyntaxError() from E
...
Traceback (most recent call last):
  File "<stdin>", line 3, in <module>
IndexError
The above exception was the direct cause of the following exception:
Traceback (most recent call last):
  File "<stdin>", line 5, in <module>
TypeError
The above exception was the direct cause of the following exception:
Traceback (most recent call last):
  File "<stdin>", line 7, in <module>
SyntaxError: None
```

Code like this shows three exceptions too. Here the chain comes from errors in the handlers. The separator lines read "During handling of the above exception…" instead of "The above exception was the direct cause…":

```python
try:
    try:
        1 / 0
    except:
        badname
except:
    open('nonesuch')
```

Chains change the error display. They do not change how exceptions are named and caught. The chain is stored in the exception object's attributes. You can inspect those attributes when needed.

Chaining is common in other languages too, including Java and C#. It is unclear which one influenced Python. In Python, chains often appear in error messages. Creating them yourself with `raise` is less common, so the Python manuals cover the details.

One more tool stops chaining. `raise from None` hides the chained context in the display. Use it in applications that convert one exception type into another. It keeps error messages less cluttered.

## The assert statement

Python's `assert` statement is a debugging aid. It is mostly shorthand for a common `raise` pattern. You can think of an `assert` as a conditional `raise`. The form is:

```python
assert test, data # The data part is optional
```

It works like this code:

```python
if __debug__:
    if not test:
        raise AssertionError(data)
```

If `test` is false, Python raises an exception. The `data` item, if given, becomes the exception's constructor argument. The built-in `AssertionError` ends your program unless a `try` catches it. The `data` text appears in the standard message:

```python
>>> language = 'Java'
>>> assert language.startswith('Py'), "You're using the wrong language!"
AssertionError: You're using the wrong language!
```

There is one extra feature. Python removes `assert` statements from compiled bytecode when you run with the `-O` flag. Then they never run. The built-in name `__debug__` is `True` by default. It is `False` under `-O`. Any code that depends on it being `True` is removed, including asserts.

To disable and omit asserts, run your code with `python3 -O file.py`. You can also produce optimized bytecode before a run, using the `compileall` standard-library module or the `compile` built-in function. The Python manuals explain both.

### Trapping constraints, not errors

Assertions are for checking conditions while you develop. Their messages include the source line and the value in the `assert` statement. The file `asserter.py` in Example 34-5 shows this:

```python
def f(x):
    assert x < 0, 'x must be negative'
    return x ** 2
```

Normally, a positive number triggers the assertion. Under `-O`, the check disappears:

```text
$ python3
>>> import asserter
>>> asserter.f(-3)
9
>>> asserter.f(3)
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/…/LP6E/Chapter34/asserter.py", line 2, in f
    assert x < 0, 'x must be negative'
AssertionError: x must be negative
$ python3 -O
>>> import asserter
>>> asserter.f(3)
9
```

Keep in mind that `assert` is mainly for user-defined constraints. It is not for catching real programming errors. Python already traps those errors, such as bad indexes, type mismatches, and zero divides. So you rarely need an `assert` for them:

```python
def reciprocal(x):
    assert x != 0 # A generally useless assert!
    return 1 / x # Python checks for zero automatically
```

Asserts like that are superfluous. Python raises exceptions on errors without help, so let it do the work. As a rule, you do not need to check for errors yourself in your own code.

There are exceptions to every rule. If a function must do long-running or unrecoverable work before an error would be raised, a test may be worth it. Even then, keep your tests from being too specific or restrictive. Otherwise you limit how useful your code is.

Chapter 29 of the book shows another common use. There, `assert` makes calls to undefined methods in an abstract superclass fail with a message. It is a rare but useful tool.

## The with statement and context managers

Python includes one more exception tool, the `with` statement. It hands exception-related work to an object. The `with` statement works with context manager objects that follow a method-based protocol. The idea is similar to how `for` uses the iteration protocol.

The `with` statement is much like the "using" statement in C#. It is a more advanced tool, and it was once a candidate for the next part of this book. Context managers are light and useful enough that they fit with the exception tools here.

In short, `with` is an alternative to a common `try`/`finally` pattern. Like `try`/`finally`, it mostly handles cleanup that must run whether or not an exception occurs in the block.

`with` is based on method calls around a block. That makes it less general than `try`/`finally`. It is redundant for cleanup alone, and it requires a class for objects that do not support the protocol. On the other hand, `with` also handles entry actions. It can reduce code size where it is supported. It lets you manage code contexts with full object-oriented design.

Python adds context managers to some built-in tools. Files close themselves, and thread locks lock and unlock themselves. Async tools await results automatically, as Chapter 20 of the book covers. You can also write your own context managers with classes. Let us look at the statement and its protocol.

### Basic with usage

The basic form of `with` looks like this. The part in square brackets is optional:

```text
with expression [as variable]:
    with-block
```

The statements in the `with-block` are the main action. The `expression` must return an object that supports the context-management protocol. That object can return a value, which is assigned to `variable` when an `as` clause is present.

The variable does not always receive the expression's result. The result is the context-manager object itself. The `variable` may receive something else meant for use inside the block. The object can run startup code before the block starts. It can also run termination code after the block ends, whether or not the block raised an exception.

Some built-in objects already support this protocol. File objects from Chapter 9 of the book have a context manager. It closes the file after the `with` block, whether or not an exception occurs. It does this no matter if or when the Python version would have closed the file automatically:

```python
with open('somefile.txt') as myfile:
    for line in myfile:
        print(line)
```

Here, `open` returns a file object that is assigned to `myfile`. You use `myfile` with the usual file tools. In this case, the file iterator reads one line at a time in the `for` loop.

The result of `open` also supports the context-management protocol. After the `with` statement finishes, the file is closed automatically. That holds even if the `for` loop raised an exception while processing the file.

Garbage collection can close files too, but it is not always clear when. This matters more on other Python implementations. The `with` statement lets you be sure the close happens right after a specific block.

You can get the same effect with `try`/`finally`. That takes three more lines of admin code here, four lines instead of one:

```python
myfile = open('somefile.txt')
try:
    for line in myfile:
        print(line)
finally:
    myfile.close()
```

You could skip both forms. But the file may stay open if an exception is raised during the `for` loop. That can matter in long-running programs. Chapter 36 of the book revisits these trade-offs.

Threading locks offer another example. The book does not cover multithreading modules, but their lock and condition objects support the protocol. So `with` adds entry and exit actions around a block. After importing `threading`:

```python
lock = threading.Lock()
with lock:
    …access shared resources…
```

The context manager acquires the lock before the block runs. It releases the lock when the block finishes, whatever the exception outcome.

The `decimal` module, introduced in Chapter 5 of the book, uses context managers too. They save and restore the current decimal context. That context sets the precision and rounding rules for calculations:

```python
with decimal.localcontext() as ctx:
    ctx.prec = 2
    x = decimal.Decimal('1.00') / decimal.Decimal('3.00')
```

After the statement runs, the thread's context returns to what it was before the block. To do the same with `try`/`finally`, you would save the context first and restore it by hand afterward.

### The context-management protocol

Some built-in types come with context managers. You can also write your own. To do that, a class defines special methods, which fall under operator overloading. These methods hook into the `with` statement. The interface is somewhat complex. Most programmers only need to use existing context managers. Tool builders who write their own should know the details.

Here is how `with` works:

1. The expression is evaluated. The result is a context manager, an object that must have `__enter__` and `__exit__` methods.
2. The context manager's `__enter__` method is called. Its return value is assigned to the `as` variable, if present. Otherwise, the value is discarded.
3. The code in the nested `with` block runs.
4. If the block raises an exception, the `__exit__(type, value, traceback)` method is called with its details. These three values match what `sys.exc_info` returns. If `__exit__` returns a false value, the exception is reraised. Otherwise, the exception ends there. The exception should normally be reraised, so it propagates outside the `with` after `__exit__` returns.
5. If the block raises no exception, `__exit__` still runs. Its `type`, `value`, and `traceback` arguments are all `None`. Its return value is ignored.

The file `withas.py` in Example 34-6 shows the protocol. It defines a context manager that traces entry and exit of any `with` block that uses it:

```python
"A context manager that traces entry and exit of any with statement's block"
class TraceBlock:
    def message(self, arg):
        print('running ' + arg)
    def __enter__(self):
        print('[starting with block]')
        return self
    def __exit__(self, exc_type, exc_value, exc_tb):
        if exc_type is None:
            print('[exited normally]\n')
        else:
            print(f'[propagating exception: {exc_type}]')
        return False
if __name__ == '__main__':
    with TraceBlock() as action:
        action.message('test 1')
        print('reached')
    with TraceBlock() as action:
        action.message('test 2')
        raise TypeError
        print('not reached')
```

This `__exit__` returns `False`, so the exception propagates. Deleting the `return` line would have the same effect. A function that returns nothing returns `None`, which counts as false. Still, an explicit `return False` is clearer. The `__enter__` method returns `self`, which is assigned to `action`. In other designs, it could return a different object.

Running the self-test traces two `with` blocks. The `__enter__` and `__exit__` methods run automatically:

```text
$ python3 withas.py
[starting with block]
running test 1
reached
[exited normally]
[starting with block]
running test 2
[propagating exception: <class 'TypeError'>]
Traceback (most recent call last):
  File "/…/LP6E/Chapter34/withas.py", line 25, in <module>
    raise TypeError
TypeError
```

Context managers can use object-oriented state and inheritance. They are an advanced tool for tool builders, so this chapter skips those details. The Python manuals cover the full story, including the `contextlib` standard module. That module has more tools for writing context managers.

The `try`/`finally` form also handles termination. It is often enough when a class is not worth the effort of supporting the `with` protocol.

### Multiple context managers

The `with` statement can take several context managers, separated by commas. In the next snippet, both files close when the block exits. That happens whatever the exception outcome:

```python
with open('lines.txt') as input, open('matches.txt', 'w') as output:
    for line in input:
        if 'somekey' in line:
            output.write(line)
```

You can list any number of context-manager items. Several items behave the same as nested `with` statements. So this code:

```python
with A() as a, B() as b:
    statements
```

is equivalent to, and possibly simpler than, this code:

```python
with A() as a:
    with B() as b:
        statements
```

Each manager's entry and exit methods run in turn, on entry and on exit. Exceptions in the block are caught automatically. The outermost manager's exit method decides whether to reraise them. Several file managers open all their files on entry and close them on exit, with or without an exception.

### Termination handlers compared

The Python docs cover context managers in more depth. Here we will look at this feature in action and weigh its role. Using a newer and more redundant tool like `with` does not prove you are clever. You need to understand the trade-offs.

The first example scans two files for matching lines. It uses `with` to open both files at once. Then it zips their next lines together on each pass of a `for` loop. The file objects handle closing, so you need not catch exceptions or close files yourself:

```python
>>> with open('lines1.txt') as file1, open('lines2.txt') as file2:
...     for pair in zip(file1, file2):
...         print(pair)
('hack\n', 'HACK\n')
('code\n', 'GOOD\n')
('well\n', 'CODE\n')
```

You can use the same structure to compare two text files. This version swaps the `print` for an `if` comparison. It also adds `enumerate` for line numbers:

```python
>>> with open('lines1.txt') as file1, open('lines2.txt') as file2:
...     for (linenum, (line1, line2)) in enumerate(zip(file1, file2)):
...         if line1.lower() != line2.lower():
...             print(f'{linenum} => {line1!r} != {line2!r}')
1 => 'code\n' != 'GOOD\n'
2 => 'well\n' != 'CODE\n'
```

In CPython, though, `with` adds little here. Input files need no buffer flush. CPython closes files automatically when they are garbage collected. Exceptions in the block still propagate out of the statement if you do not catch them. So the simpler version below behaves the same:

```python
for pair in zip(open('lines1.txt'), open('lines2.txt')): # Same if auto close
    print(pair) # Ditto for != test
```

Some alternative Pythons from Chapter 2 of the book use different garbage collectors. They may need direct closes to save system resources. Output files may also need closes, so buffered content reaches the disk before later code opens them.

The following code handles both concerns. It closes files on statement exit, with or without an exception. It uses parentheses and line splits after `with`, which are available from Python 3.10. Write counts are omitted for brevity:

```python
>>> with (open('lines1.txt') as input,
...       open('uppers.txt', 'w') as output):
...     for line in input:
...         output.write(line.upper())
>>> print(open('uppers.txt').read()) # File content is available here
HACK
CODE
WELL
```

In simple scripts, you can often open files in separate statements. Close them when processing ends. Catching an exception there gains little. If an error stops your program, there is no point in recovering. Closing matters only to flush output buffers, or when a later step reopens the file. That step may never run after an exception:

```python
input = open('lines1.txt')
output = open('uppers.txt', 'w')
for line in input: # Same effect if files auto close,
    output.write(line.upper()) # and file is not reopened ahead
```

Some programs must continue after an exception and also close output files for later use in the same run. Here `with` avoids an equivalent `try`/`finally`. That version is more obvious to some readers. It also needs more code: eight lines instead of four:

```python
input = open('lines1.txt')
output = open('uppers.txt', 'w')
try: # Same but explicit close on errors
    for line in input:
        output.write(line.upper())
finally:
    input.close() # Ensure output file is complete
    output.close() # Whether exception occurs or not
```

Still, `try`/`finally` is a single tool that covers every cleanup case, and it keeps the steps explicit. The `with` statement can be more concise for context-manager users. It works only with objects that implement its protocol. It also relies on implicit behavior that can hide meaning. Learning it adds to what a programmer must know. Weigh these trade-offs for yourself.

## Chapter summary

The `try` statement catches exceptions and recovers from them. It names a block of code and one or more handlers for exceptions raised while it runs. The two common variations are `try`/`except`/`else` for catching exceptions, and `try`/`finally` for cleanup that must happen whether an exception is raised or not. The two forms can be mixed in one statement. Even when mixed, `finally` runs on the way out of the `try`. The combined form is equivalent to nesting a `try`/`except`/`else` inside a `try`/`finally`.

The `raise` statement triggers an exception. Python raises built-in exceptions itself when errors occur. Your scripts can raise built-in or user-defined exceptions with `raise`.

The `assert` statement raises an `AssertionError` when a condition is false. It works like a conditional `raise` inside an `if` statement. You can disable it with the `-O` command-line switch.

The `with` statement automates startup and termination work around a block of code. It is roughly like `try`/`finally`, since its exit actions run whether or not an exception occurred. It uses an object-based protocol for entry and exit actions, which can shrink code for context-manager users. It is less general, though. It applies only to objects that support its protocol. `try` with `finally` covers more cases.

The next chapter shows how exception objects are built. It explains how you can create new exceptions for your own programs with classes.

## Exception objects

So far, this part of the handbook has been somewhat vague about what an exception actually is. This section clears up the mystery by disclosing the facts behind exception objects, both built-in and user-defined. An exception is a class instance object. Python raises that object, passes it along, and matches it against the `except` clauses in `try` statements. To define your own exception, you write a class.

That means you need some object-oriented programming. The effort pays off, though. Class-based exceptions give you three things. You get flexible categories, so adding a new subclass does not force changes to existing `try` statements. You get state and behavior, because attributes and methods live on the raised instance. You also get reuse by inheritance, so error displays can share one look.

Every built-in exception is a class too. Python arranges them in one inheritance tree. Your own exceptions join that tree, and they inherit useful defaults from it.

### Exception classes and superclass matching

A raised exception matches an `except` clause when the clause names its class or any superclass of that class. In plain terms, an `except` catches the class it lists and all of that class's subclasses. Superclasses act as category names. Subclasses act as specific kinds of errors inside a category.

Naming a general superclass therefore catches a whole category. Here is a small file called `categoric.py`:

```python
class General(Exception): pass
class Specific1(General): pass
class Specific2(General): pass
def raiser0():
    X = General() # Raise superclass instance
    raise X
def raiser1():
    X = Specific1() # Raise subclass instance
    raise X
def raiser2():
    X = Specific2() # Raise different subclass instance
    raise X
for func in (raiser0, raiser1, raiser2):
    try:
        func()
    except General: # Match General or any subclass of it
        import sys
        print('caught:', sys.exc_info()[0])
```

The `try` statement catches and reports instances of all three classes. The `except` names their common superclass, so every member of the category matches:

```text
$ python3 categoric.py
caught: <class '__main__.General'>
caught: <class '__main__.Specific1'>
caught: <class '__main__.Specific2'>
```

Three points are worth noticing in this code. The category classes are nearly empty. Their bodies hold only `pass`, because the category is the whole point. The top class also inherits from the built-in `Exception` class, and that is required. A class that does not inherit from a built-in exception class will not work in most exception contexts.

`Exception` is the root for nonexit exceptions. `BaseException` is the root for all exceptions, and it may also serve as the parent. Inheriting from `Exception` is the usual choice, and it gives you helpful behavior that you will meet later.

The second point is about raising. The code calls the classes to make instances for the `raise` statements, so the parentheses matter. If you list a class name without parentheses in a `raise`, Python calls it with no constructor arguments. You can create the instance before the `raise`, as this file does, or inside the `raise` statement.

The third point is about the handler. `sys.exc_info` returns a tuple. Its first item is the class of the exception raised, and its second item is the instance. In a general `except` that catches a whole category, that call tells you exactly what happened. The next chapter covers `sys.exc_info` and the related tools, including tracebacks, in more detail.

When an `except` catches an exception, the instance belongs to the listed class or to one of its subclasses. So the specific kind is always available. You can read it through `type(X)` or through the `__class__` attribute. The variant `categoric2.py` shows this with the `as` form:

```python
class General(Exception): pass
class Specific1(General): pass
class Specific2(General): pass
def raiser0(): raise General()
def raiser1(): raise Specific1()
def raiser2(): raise Specific2()
for func in (raiser0, raiser1, raiser2):
    try:
        func()
    except General as X: # X is the raised instance
        print('caught:', type(X)) # Same as sys.exc_info()[0], X.__class__
```

The `as` name gives you the instance directly. That makes `sys.exc_info` most useful in empty `except` clauses that have no other way to reach the instance or its class. Well-designed programs should rarely need to know which specific exception happened. Calling a method on the instance should run behavior that suits that exception.

### Why exception hierarchies?

A tuple of names works well for small code. It is one way to catch several exceptions at once, and it is easy to read. For large programs with many exceptions, though, catching a category is easier than listing every member. A class hierarchy also keeps working as the set grows.

Suppose you write a numeric library for many people to use. You find two things that can go wrong, division by zero and numeric overflow. You document them as two standalone exceptions:

```python
# mathlib.py
class Divzero(Exception): pass
class Oflow(Exception): pass
def func():
    ...
    raise Divzero()
    ...and so on...
```

Users wrap calls in a `try` that catches both exceptions. Otherwise, your exceptions would stop their code:

```python
# client.py
import mathlib
try:
    mathlib.func()
except (mathlib.Divzero, mathlib.Oflow):
    ...handle and recover...
```

Six months later, you add a new error for underflow. Every client that listed the names must now edit each `try` statement to include `mathlib.Uflow`. That is a maintenance problem for your users. If you use the library only in-house, you can make those edits yourself. If many people depend on it, that is not a polite upgrade.

Some users might avoid this with an empty `except`. That catches every error, but it also catches memory exhaustion, Ctrl+C, system exits, and typos in the `try` block itself. Those should pass through. Catching the `Exception` superclass is better, but it can still hide program errors. Users really want to catch only the exceptions your library documents. Any other exception is probably a bug in the library.

A class tree solves this. Put your exceptions under one common superclass that stands for the whole category:

```python
# mathlib.py
class NumErr(Exception): pass
class Divzero(NumErr): pass
class Oflow(NumErr): pass
def func():
    ...
    raise Divzero()
    ...and so on...
```

Clients now name only the superclass to catch every library exception, both now and later:

```python
# client.py
import mathlib
try:
    mathlib.func()
except mathlib.NumErr:
    ...handle and recover...
```

When you add an underflow error later, make it a new subclass of the same superclass:

```python
# mathlib.py
...
class Uflow(NumErr): pass
```

Client code that catches `NumErr` keeps working without change. As long as clients name the superclass and it stays in place, you can add, remove, or change the subclasses freely. Class hierarchies handle this maintenance problem better than a tuple of names does.

### Built-in exception classes

The built-in exceptions follow the same pattern. Every exception Python raises on its own is a predefined class. Names such as `SyntaxError` are really classes that live in the `builtins` module. Python groups them into a shallow hierarchy, with general categories above specific types.

| Class | Role |
| --- | --- |
| `BaseException` | Topmost root. Provides default printing and state retention. Your classes should not inherit from it directly. |
| `Exception` | Root of user-defined exceptions. Nearly all of your classes should inherit from it. |
| `ArithmeticError` | Root of numeric errors. Its subclasses are `OverflowError`, `ZeroDivisionError`, and `FloatingPointError`. |
| `LookupError` | Root of indexing errors for sequences and mappings. Its subclasses are `IndexError` and `KeyError`. |
| `OSError` | Root of I/O and other system-function errors. It has attributes such as `errno`, `strerror`, and `filename`. |

`Exception` is the superclass of every built-in exception except the system exit classes. Those are `SystemExit`, `KeyboardInterrupt`, and `GeneratorExit`. The set of built-in exceptions changes over time, so the Python documentation has the complete list.

### Built-in exception categories

The built-in tree lets you choose how specific a handler should be. `ArithmeticError` is the superclass of numeric errors such as `OverflowError` and `ZeroDivisionError`. Listing `ArithmeticError` in a `try` catches any numeric error. Listing `ZeroDivisionError` catches only that one kind.

`Exception` works as a broad catchall for application-level exceptions. It behaves much like an empty `except`, but system exit exceptions pass through as they should:

```python
try:
    ...
except Exception: # Exits not caught here
    ...handle all application exceptions...
else:
    ...handle no-exception case...
```

This technique is reliable, because Python requires all classes to derive from built-in exceptions. It still shares the pitfalls of the empty `except` from the previous section. It can catch exceptions meant for other code, and it can hide real programming errors. The next chapter returns to this as a gotcha.

### Default printing and state

Built-in exceptions also provide printing and state retention by default. In many cases, that is all a user-defined class needs. Unless you redefine the constructor, any arguments you pass are saved in the instance's `args` tuple. The same arguments appear when the instance is printed.

An empty `args` tuple and display string are used when no arguments are passed. A single argument displays as itself, not as a tuple, and it serves as the message details. Here is how that looks at the interactive prompt:

```text
>>> raise IndexError # Same as IndexError(): no arguments
Traceback (most recent call last):
File "<stdin>", line 1, in <module>
IndexError
>>> raise IndexError('bad') # Constructor argument attached, printed
Traceback (most recent call last):
File "<stdin>", line 1, in <module>
IndexError: bad
>>> i = IndexError('bad', 'stuff') # Available in object attribute "args"
>>> i.args
('bad', 'stuff')
>>> print(i) # Displays args when printed manually
('bad', 'stuff')
>>> i # Uses repr for echo, str for print
IndexError('bad', 'stuff')
```

User-defined exceptions behave the same way, because they inherit these methods from their built-in superclass:

```text
>>> class E(Exception): pass
>>> raise E
Traceback (most recent call last):
File "<stdin>", line 1, in <module>
E
>>> raise E('bad')
Traceback (most recent call last):
File "<stdin>", line 1, in <module>
E: bad
>>> i = E('bad', 'stuff')
>>> i.args
('bad', 'stuff')
>>> print(i)
('bad', 'stuff')
>>> i
E('bad', 'stuff')
```

A `try` statement gives you the instance, so you can read both the original arguments and the display text:

```text
>>> try:
...     raise E('bad') # Displays + saves constructor args
... except E as X:
...     print(f'{X} - {X.args} - {X!r}')
...
bad - ('bad',) - E('bad')
>>> try:
...     raise E('bad', 'stuff') # Multiple args save/display a tuple
... except E as X:
...     print(f'{X} - {X.args} - {X!r}')
...
('bad', 'stuff') - ('bad', 'stuff') - E('bad', 'stuff')
```

An exception instance is not a string itself. It uses the `__str__` and `__repr__` methods to provide display text. To join it with real strings, convert it first, with `str(X)`, `'%s' % X`, or `f'{X}'`. If you need more control over display or stored state, you can redefine methods such as `__str__` and `__init__` in your subclasses.

### Custom print displays

By default, an instance shows the value you passed to its constructor when you catch and print it:

```text
>>> class MyBad(Exception): pass
>>> try:
...     raise MyBad('Sorry--my mistake!')
... except MyBad as X:
...     print(X)
...
Sorry--my mistake!
```

The same default text appears in an error message when the exception is not caught:

```text
>>> raise MyBad('Sorry--my mistake!')
Traceback (most recent call last):
File "<stdin>", line 1, in <module>
MyBad: Sorry--my mistake!
```

For a custom display, define `__repr__` or `__str__` in your class. The string the method returns is shown when the exception is printed or reaches the default handler:

```text
>>> class MyBad(Exception):
...     def __str__(self):
...         return 'Stuff happens...'
>>> try:
...     raise MyBad()
... except MyBad as X:
...     print(X)
...
Stuff happens...
>>> raise MyBad()
Traceback (most recent call last):
File "<stdin>", line 1, in <module>
MyBad: Stuff happens...
```

The method can return a fixed string, as it does here. It can also process text and use state stored on the instance.

You usually must redefine `__str__`, not `__repr__`. The built-in superclasses already have a `__str__` method. In some contexts, including error messages, `__str__` is preferred over `__repr__`. If you define only `__repr__`, the printed message still uses the built-in `__str__`:

```text
>>> class Oops(Exception):
...     def __repr__(self): return 'Custom display not used'
>>> raise Oops("Nobody's perfect")
...
Oops: Nobody's perfect
```

A custom `__str__` takes effect:

```text
>>> class Oops(Exception):
...     def __str__(self): return 'Custom display used'
>>> raise Oops("Nobody's perfect")
...
Oops: Custom display used
```

### Custom state and behavior

Exception classes can store extra state as instance attributes. The built-in constructor saves its arguments in the `args` tuple, which is enough for many cases. For more specific needs, you can write your own constructor. A class can also define methods that handlers call to run exception-specific logic.

### Providing exception details

An exception may cross file boundaries. The `raise` can live in one module, and the `try` that catches it can live in another. Global variables are a poor place for extra details, because the `try` may not know which file holds them. Storing details on the exception itself gives the handler a reliable path to that data.

Classes make this almost automatic. Python passes the raised instance along with the exception. The `as` name in an `except` clause gives your handler access to it. Here, a parser reports a formatting error with a line number and a file name:

```text
>>> class FormatError(Exception):
...     def __init__(self, line, file): # Custom constructor
...         self.line = line
...         self.file = file
>>> def parser(file): # Parse the file first
...     raise FormatError(62, file=file) # When an error is found
>>> try:
...     parser('code.py')
... except FormatError as X:
...     print(f'Error at: {X.file} #{X.line}') # Custom state info
...
Error at: code.py #62
```

The default constructor can do a simpler version of the same job. It stores the values as positional arguments in `args`. Keyword arguments are not allowed with that default:

```text
>>> class FormatError(Exception): pass # Inherited constructor
>>> def parser(file):
...     raise FormatError(file, 62) # No keywords allowed!
>>> try:
...     parser('code.py')
... except FormatError as X:
...     print(f'Error at: {X.args[0]} #{X.args[1]}') # Generic state info
...
Error at: code.py #62
```

### Providing exception methods

Classes can also add behavior to exception objects. An exception class can define its own methods, and handlers can call them. The file `parsely.py` adds a method that uses the stored state to log errors to a file:

```python
from time import asctime
class FormatError(Exception):
    logfile = 'parser-errors.txt'
    def __init__(self, line, file):
        self.line = line
        self.file = file
    def logerror(self):
        with open(self.logfile, 'a') as log:
            print(f'Error at: {self.file} #{self.line} [{asctime()}]', file=log)
def parser(file):
    # Parse a file here...
    raise FormatError(line=62, file=file)
if __name__ == '__main__':
    try:
        parser('code.py')
    except FormatError as exc:
        exc.logerror()
```

Each run appends one message to the log file. On Windows, use `type` instead of `cat` to see the file:

```text
$ python3 parsely.py
$ python3 parsely.py
$ cat parser-errors.txt
Error at: code.py #62 [Sat Jul 13 12:22:19 2024]
Error at: code.py #62 [Sat Jul 13 12:22:25 2024]
```

Methods such as `logerror` can be inherited from a superclass. The attributes `line` and `file` keep state for later method calls. A subclass can also change the behavior. The method below replaces the parent's `logerror` for its own instances:

```python
class CustomFormatError(FormatError):
    def logerror(self):
        ...something unique here...
...
raise CustomFormatError(...)
...
try:
    ...
except FormatError as exc:
    exc.logerror() # Runs the raised class's version
```

Because these classes are ordinary classes, the object-oriented ideas from earlier parts of the handbook apply to exceptions as well.

Two more notes apply here. The instance bound to `exc` is also the second item from `sys.exc_info()`. You can use that call when your `except` clause has no name but you still need the exception. The `logerror` method writes a custom message. It could instead produce Python's standard error message with a stack trace, using the `traceback` standard-library module.

## Exception groups

Python 3.11 added exception groups and the `except*` clause. Most learners can treat this as an optional topic. It is useful to know that the feature exists, even if you rarely write it.

A normal `try` statement runs at most one matching handler, plus an optional `finally`:

```text
>>> try:
...     raise IndexError()
... except IndexError:
...     print('Got IE')
... except (SyntaxError, TypeError):
...     print('Got SE')
...
Got IE
```

Python 3.11 can run several matching handlers in one `try`. You wrap the exceptions in an exception group and catch them with `except*` clauses:

```text
>>> try:
...     raise ExceptionGroup('Many', [IndexError(), SyntaxError()])
... except* IndexError:
...     print('Got IE')
... except* (SyntaxError, TypeError):
...     print('Got SE')
...
Got IE
Got SE
```

Each `except*` clause can process one exception, or one batch of them, from the group. Here the first clause handles `IndexError`, and the second handles `SyntaxError`. A tuple still means "any of these." The group is an exception object made by calling the built-in `ExceptionGroup` class. It takes a label for displays and a sequence of exceptions to match.

Some syntax rules apply, and they are stricter than the rules for a plain `try`. An empty `except*` is not allowed. A basic `except` cannot be mixed with `except*`. An `else` and a `finally` can be used with it. A `break`, `continue`, or `return` cannot appear inside an `except*` clause, although a basic `except` allows them.

The matching rules are also specific. Each `except*` clause runs at most once. It consumes all matching exceptions in the group. Each exception is handled by only one clause, the topmost clause that matches it. Any unmatched exceptions are raised again after the `try` finishes matching. The `as` name receives a group, and the `exceptions` attribute exposes its contents:

```text
>>> excs = ExceptionGroup('Many', [IndexError(), SyntaxError(), TypeError()])
>>> try:
...     raise excs
... except* IndexError as E:
...     print(f'Got IE: {E} => {E.exceptions}')
... except* SyntaxError as E:
...     print(f'Got SE: {E} => {E.exceptions}')
...
Got IE: Many (1 sub-exception) => (IndexError(),)
Got SE: Many (1 sub-exception) => (SyntaxError(),)
  + Exception Group Traceback (most recent call last):
  | File "<stdin>", line 2, in <module>
  | ExceptionGroup: Many (1 sub-exception)
  +-+---------------- 1 ----------------
    | TypeError
    +------------------------------------
```

When a group holds several exceptions of the same type, one matching `except*` consumes them all. You can then loop over them in ordinary code. Spaces around the `*` are allowed and ignored:

```text
>>> try:
...     raise ExceptionGroup('Dups', [IndexError(), TypeError(1), TypeError(2)])
... except *IndexError:
...     print('Got IE')
... except *TypeError as E:
...     print(f'Got TE: {E} => {E.exceptions}')
...
Got IE
Got TE: Dups (2 sub-exceptions) => (TypeError(1), TypeError(2))
```

Matching follows the same class rules as before. A clause matches its named class or any superclass. Because the first match wins and removes exceptions from the group, clause order matters. In the next example, the first clause takes `IndexError` through its `LookupError` superclass, along with both `TypeError` values:

```text
>>> try:
...     raise ExceptionGroup('Dups', [IndexError(), TypeError(1), TypeError(2)])
... except* (TypeError, LookupError) as E:
...     print('Got1:', E)
... except* IndexError as E:
...     print('Got2:', E)
...
Got1: Dups (3 sub-exceptions)
```

Reversing the two clauses would handle `IndexError` separately.

An `except*` can also match a single exception. Python wraps it in a group so the handler can use group-based code:

```text
>>> try:
...     raise IndexError
... except* IndexError as E:
...     print(f'Got IE: {E} => {E.exceptions}')
...
Got IE: (1 sub-exception) => (IndexError(),)
```

A basic `except` can catch a whole group and process it by hand. An `except*` cannot catch a group, because that would be ambiguous:

```text
>>> try:
...     raise ExceptionGroup('Lots', [IndexError(), SyntaxError()])
... except ExceptionGroup as E:
...     print(f'Got group: {E} => {E.exceptions}')
...     for exc in E.exceptions:
...         print('With exc:', type(exc))
...
Got group: Lots (2 sub-exceptions) => (IndexError(), SyntaxError())
With exc: <class 'IndexError'>
With exc: <class 'SyntaxError'>
```

A catchall works in both models. There is no real reason to use `except*` for a single exception, though:

```text
>>> try:
...     raise ExceptionGroup('Dups', [IndexError()])
... except* Exception as E:
...     print(type(E.exceptions[0]))
...
<class 'IndexError'>
>>> try:
...     raise IndexError()
... except Exception as E:
...     print(type(E))
...
<class 'IndexError'>
```

The next chapter shows how groups pass through nested handlers. Groups propagate until they are empty, then they behave like single exceptions. Many programmers find the extra syntax hard to justify. Groups are rarely needed, and a normal exception object with normal iteration can often carry a batch of errors. Decide for yourself whether a project needs them.

Exception groups are an obscure tool with narrow roles. The Python documentation covers this `try` extension in more detail. The special cases above also make `except*` feel like a separate statement form. Adding it to `try` makes that statement a mix of related but different jobs.

## Exception objects summary

Exceptions are implemented as class instance objects. Exception classes support hierarchies that ease maintenance. They let you attach data and behavior to exceptions as instance attributes and methods. They can also inherit tools from superclasses, as usual in object-oriented programming.

A `try` statement that catches a superclass also catches every subclass below it. Superclasses act as exception category names, and subclasses act as more specific exception types within those categories. The built-in superclasses you must inherit from provide usable printing and state retention. You can override those defaults when you need to.

Exception groups and `except*` let one `try` run several handlers. We questioned whether this extension's convolution of `try` statements is justified by its roles. Whether that extra complexity is justified is a question you must answer for your own code. It is a lot to ask of most Python users, so learn the basic exception classes first.

## Unicode and byte strings

Earlier in this part, the string story was kept simple on purpose, so you could get started quickly. This section widens it to full Unicode text and to binary data. Python handles both with its string types, and the difference matters as soon as your data leaves the simple ASCII world.

How much of this you need depends on your work. If you handle non-ASCII text, such as internet content, internationalized applications, XML parsers, or some GUIs, Python's `str` type and its Unicode-aware text files support you directly. If you handle binary data, such as image or audio files, network transfers, or packed data shared with lower-level tools, you need the `bytes` type and a clear line between text and binary.

If you need neither, you can keep using strings as before. Python still encodes and decodes your text with your platform's default, and you will rarely notice. You will notice when content or a machine uses a different default. Plain ASCII text is the easy case, because ASCII is a subset of many common encodings.

### Character representations

Most programmers picture a string as a series of characters. Underneath, each character is stored as an integer code. Unicode keeps that picture, but the way characters are stored in memory and files depends on which characters you use and how you record them.

For many programmers in the US, ASCII shaped their first idea of text. ASCII defines codes 0 to 127, so each character fits in one 8-bit byte, even though only 7 bits are used. The character `a` maps to 97, which is `0x61` in hex. Three built-in functions show these values:

```text
$ python3 # Or py -3 on Windows
>>> ord('a') # Character => code
97
>>> chr(97) # Code => character
'a'
>>> hex(97) # Byte value: fits 8 bits
'0x61'
>>> 0b0111_1111 # Limit of ASCII's 7-bit range
127
```

The function `ord` returns a character's code, `chr` returns the character for a code, and `hex` shows the code as two hex digits. Each hex digit covers a 4-bit "nibble," so two digits fit in one byte. ASCII makes text simple because each character maps directly to one byte.

ASCII has a limit, though. Accented characters and special symbols fall outside codes 0 to 127. Some older standards used all 256 values of one byte and assigned codes 128 to 255 to extra characters. Latin-1 is one of them, and it is widely used in Western Europe. Its code 196, which is byte value `0xc4`, is the accented character `Ä`:

```text
>>> chr(196) # Too big for ASCII
'Ä'
>>> ord('Ä') # Okay for Latin-1
196
>>> hex(ord('Ä')) # Byte value in Latin-1
'0xc4'
>>> bin(ord('Ä')) # Latin-1 uses all 8 bits
'0b11000100'
```

Some alphabets and symbol sets define far more characters than one byte can hold. The character `☞` has the code 9758, which is `0x261e` in hex, and that is too big for one byte. Emoji follow the same rule and need more than two bytes of code space. Unicode provides codes for almost every natural language, plus many symbols and emoji:

```text
>>> ord('☞')
9758
>>> hex(ord('☞')) # Too big for one byte
'0x261e'
>>> [hex(ord(c)) for c in '\U0001f642\U0001f64a\U0001f44d'] # Emojis: > two bytes
['0x1f642', '0x1f64a', '0x1f44d']
```

In Unicode terms, these integer codes are called code points. The code points for `a`, `Ä`, and the smiling emoji `\U0001f642` are 97, 196, and 128578. In hex, they are `0x61`, `0xc4`, and `0x1f642`. Unicode is sometimes called a wide-character model, because one character code may need several bytes.

Inside computer memory, a wide character can span as many bytes as its code point needs. Once text leaves your program, storage and networks need a tighter format. Unicode defines standard ways to map code points to bytes and back. These mappings are called encodings, and they are the subject of the next part.

Unicode's takeaway is simple. Its code points cover almost every character, and its encodings make text portable. Older schemes such as ASCII fit under the Unicode umbrella without change.

### Character encodings

Code points in memory are integers of any size. Storing and sending text imposes limits on time, space, and compatibility, so text needs an extra formatting step. That step is an encoding.

Two terms describe the translation in both directions. Encoding turns a string of characters into raw bytes, using any encoding broad enough to hold those characters. Decoding turns raw bytes back into a string, using the same encoding that created the bytes. Encoding and decoding are the two halves of one round trip.

Some encodings are trivial. ASCII and Latin-1 map each character to a single byte, so the work is almost nothing. You can see this with the `encode` method, which every Python text string has. The method returns the bytes that represent the string in a chosen encoding:

```text
>>> len('a'.encode('ASCII')) # ASCII 'a' encodes in 1 byte per ASCII
1
```

Other encodings can use several bytes per character. UTF-8 is the most common, because it can represent every Unicode code point with a variable number of bytes. That makes it a de facto standard for text on the internet. In UTF-8, codes below 128 take one byte. Codes from 128 up to `0x7ff` (2047) take two bytes, and larger codes take three or four bytes.

This design keeps simple ASCII text compact. It also avoids zero bytes, which can cause trouble for C libraries and network code. Here is the byte count for three kinds of character:

```text
>>> len('a'.encode('UTF-8')) # ASCII: encodes in 1 byte
1
>>> len('Ä'.encode('UTF-8')) # Non-ASCII: encodes in 2 bytes
2
>>> len('\U0001f642'.encode('UTF-8')) # Emoji: encodes in 4 bytes
4
```

ASCII is a subset of Latin-1 and UTF-8. Both encodings store ASCII characters as the same single byte that ASCII uses. That means ASCII text is also valid Latin-1 text and valid UTF-8 text. The reverse does not hold, because Latin-1 or UTF-8 text with higher code points fails to encode as ASCII.

The mapping is easy to see in Python. ASCII characters produce identical bytes in ASCII, UTF-8, and Latin-1. Non-ASCII characters need more bytes, and some encodings cannot represent them at all:

```text
>>> 'a'.encode('ASCII') # ASCII encodes to the same byte
b'a'
>>> 'a'.encode('UTF-8')
b'a'
>>> 'a'.encode('Latin-1')
b'a'
>>> 'Ä'.encode('UTF-8') # But non-ASCII requires more bytes
b'\xc3\x84'
>>> '\U0001f642'.encode('UTF-8') # And more inclusive encodings
b'\xf0\x9f\x99\x82'
>>> '\U0001f642'.encode('ASCII')
UnicodeEncodeError: 'ascii' codec can't encode character '\U0001f642'...
>>> '\U0001f642'.encode('Latin-1')
UnicodeEncodeError: 'latin-1' codec can't encode character '\U0001f642'...
```

Other encodings take their own approach. UTF-16 uses two bytes per character, and UTF-32 uses four. UTF-16 adds a surrogate-pair scheme for codes that do not fit in two bytes. Some of these encodings also write a byte order mark (BOM) at the start of the encoded text. The BOM can show byte order and encoding type, and Python's text-mode files handle it for you.

Every one of these encodings, including ASCII, Latin-1, and UTF-8, yields the same code points when decoded. The encoding only changes the bytes on disk or on the wire. When text is decoded, its code points may take one, two, or four bytes in memory, depending on the Python version and the content. Once encoded, the bytes follow the standard format for that encoding, no matter which language wrote them.

An encoding is named by a string, such as `'utf-8'` or `'latin-1'`. Python ships with roughly 100 encodings. The `codecs` module in the Python Library Reference lists them, and `help(encodings)` shows many more. Some names are aliases, so `latin-1`, `iso_8859_1`, and `8859` all refer to Latin-1.

### The three string types

Python has three string-like types, and each has a clear job. `str` holds Unicode text as decoded code points. `bytes` holds binary data, including text that has already been encoded. `bytearray` is a mutable version of `bytes`.

The `str` type is an immutable sequence of characters. Its content can be simple ASCII, where one character is one byte once encoded, or richer Unicode text, where one character may need several bytes. In memory, a `str` is just a list of code points. It has no notion of an encoding. Only when it moves to a file or network does Python encode it, using the platform default or a name you give.

The `bytes` type is an immutable sequence of 8-bit integers. It holds raw bytes, which may be image data, packed records, or encoded text with an implied encoding. Most of the operations that `str` supports also work on `bytes`. This includes string methods, sequence operations, and the `re` pattern-matching module. Indexing a `bytes` gives back an integer, and slicing gives back another `bytes`.

When a `bytes` value holds byte values in the ASCII range, Python prints those values as ASCII characters, not as integers. This is a convenience, but it can blur the line between text and binary data. Operations that assume characters, such as `isalpha`, treat the bytes as ASCII-encoded data.

The `bytearray` type is a mutable variant of `bytes`. It supports the string methods and sequence operations of `bytes`, and it also has in-place change methods from lists, such as `append` and `extend`. Use it when you need to change binary data in place without building new copies.

### Text and binary files

File input and output is where encodings matter most. Text is only decoded integer codes while it sits in memory. Encodings come into play when text moves to or from an external source such as a file. Binary data may have nothing to do with encodings or text at all.

Python makes a sharp, platform-independent split between text and binary files. Both are opened with the built-in `open` function, and the mode string decides which kind you get. A text-mode file decodes content when you read it and encodes content when you write it. It uses either the platform default or an `encoding` argument you pass. Text-mode files also handle newline translation and BOMs.

A binary-mode file does none of that. Adding `b` to the mode string makes the file binary. Reads return the raw bytes as a `bytes` object, with no decoding and no newline mapping. Writes accept a `bytes` object, and binary-mode files also accept a `bytearray` object.

The mode decides the object type. Choose `str` and text mode for content that is textual, such as program output, HTML, JSON, CSV, or XML. Choose `bytes` and binary mode for image or audio files, packed data from other programs, and device data streams. For example, the modes `rb`, `wb`, and `rb+` use `bytes`, while `r`, `w+`, and `rt` use `str`. The default mode is `rt`.

### Literals and basic properties

Most string objects come from one of three places: a call to `str` or `bytes`, a file opened with `open`, or a literal in your code. The usual `'…'` and `"…"` forms, and triple-quoted blocks, create a `str`. Adding a `b` or `B` in front creates a `bytes` instead. The `bytes` literal behaves like a raw string in one way, because you can combine the `b` and `r` prefixes to keep backslashes as typed.

```text
>>> B = b'code' # Make a bytes object: 8-bit bytes
>>> S = 'hack' # Make a str object: Unicode characters
>>> type(B), type(S)
(<class 'bytes'>, <class 'str'>)
>>> B # Sequence of ints, prints as ASCII characters
b'code'
>>> S # Sequence of code points, prints as text glyphs
'hack'
>>> B2 = B"""
... xxxx
... yyyy
... """
>>> B2
b'\nxxxx\nyyyy\n'
>>> b'A\nB\rC', br'A\nB\rC', rb'A\nB\rC' # Raw-string combos work too
(b'A\nB\rC', b'A\\nB\\rC', b'A\\nB\\rC')
```

Once you have a string, the usual operations work. Their results depend on the type. Indexing a `bytes` gives an integer, while indexing a `str` gives a character. Both types are immutable, so neither supports item assignment:

```text
>>> B, S
(b'code', 'hack')
>>> B[0], S[0] # Indexing returns an int for bytes, str for str
(99, 'h')
>>> B[1:], S[1:] # Slicing makes another bytes or str
(b'ode', 'ack')
>>> list(B), list(S)
([99, 111, 100, 101], ['h', 'a', 'c', 'k'])
>>> B[0] = 'x' # Both are immutable
TypeError: 'bytes' object does not support item assignment
>>> S[0] = 'x'
TypeError: 'str' object does not support item assignment
```

Python 3 also accepts the Python 2 `u'…'` literal, so older code still runs. In Python 3, that literal is just another spelling of a normal `str`. There is no good reason to write it in new code, but you may see it in older programs.

### String type conversions

The `str` and `bytes` types never mix on their own. They are not converted automatically in expressions or when passed to functions. An operator that expects one type rejects the other, and a function that expects `str` may reject `bytes`.

```text
>>> 'hack' + b'code'
TypeError: can only concatenate str (not "bytes") to str
```

The reason is that a `bytes` value may be encoded text, with an encoding Python cannot know. It may also be binary data, such as an audio file, that has nothing to do with text. Python will not guess, so you must choose a type or convert on purpose. The conversion tools are these:

- `S.encode(encoding?)` and `bytes(S, encoding)` encode a `str` object `S` into a new `bytes` object using `encoding`.
- `B.decode(encoding?)` and `str(B, encoding)` decode a `bytes` object `B` into a new `str` object using `encoding`.

The question mark means the encoding argument is optional for the method form. The method defaults are UTF-8, so `S.encode()` and `B.decode()` use UTF-8 when you leave the name out. The `open` function uses a different default, which comes from the `locale` module and can vary by platform.

```text
>>> S = 'hack'
>>> S.encode() # str to bytes: encode text into raw bytes
b'hack'
>>> bytes(S, encoding='ascii') # str to bytes, alternative
b'hack'
>>> B = b'code'
>>> B.decode() # bytes to str: decode raw bytes into text
'code'
>>> str(B, encoding='ascii') # bytes to str, alternative
'code'
```

With conversions, you can combine the two types on purpose. Encode one side, or decode the other, and the types then match:

```text
>>> S, B
('hack', b'code')
>>> S.encode('ascii') + B # bytes + bytes (encoded)
b'hackcode'
>>> S + B.decode('ascii') # str + str (code points)
'hackcode'
```

Two defaults deserve caution. The `encoding` argument to `bytes` is required, even though it is optional for `S.encode()` and `B.decode()`. The `str` constructor does not require it, but calling `str(B)` without an encoding returns the printed form of the bytes, not the decoded text. That is usually not what you want.

```text
>>> bytes(S)
TypeError: string argument without an encoding
>>> str(B) # str() works without encoding
"b'code'" # But print string, not conversion!
>>> len(str(B))
7
>>> len(str(B, encoding='ascii')) # Pass encoding to convert to str
4
```

Your platform's default encodings are available through the `sys` and `locale` modules. They are less dependable than they look. On a Windows PC, the `open` default is `cp1252`, which is a superset of Latin-1 that adds characters such as curly quotes. On macOS and most Unix systems, the same `open` default is `utf-8`:

```text
$ py -3
>>> import sys, locale
>>> sys.platform # Underlying platform: Windows
'win32'
>>> sys.getdefaultencoding() # Methods default (but not for str()!)
'utf-8'
>>> locale.getpreferredencoding(False) # open() default: a Latin-1 superset
'cp1252'
```

```text
$ python3
>>> import sys, locale
>>> sys.platform # Underlying platform: macOS
'darwin'
>>> sys.getdefaultencoding() # The default for methods is same
'utf-8'
>>> locale.getpreferredencoding(False) # But this differs on Unix: be explicit!
'utf-8'
```

Defaults can also depend on environment variables, command-line arguments, and host settings. Text from other sources may use any encoding at all. For that reason, do not rely on `open` defaults when portability matters. Always pass an explicit encoding to `open` when files must work across hosts.

Encoding and decoding are more than type conversions. They produce different kinds of data. Encoding returns the bytes that represent text under a scheme, and decoding returns the text that those bytes represent. For plain ASCII the mapping looks trivial, but for richer text the difference is real.

### Coding Unicode strings in Python

Encoding and decoding become more useful with non-ASCII text. Some characters are hard to type on a keyboard. Python string literals provide two kinds of escape for those characters:

- `\xNN` hex escapes, where two hex digits give a one-byte (8-bit) code.
- `\uNNNN` and `\UNNNNNNNN` Unicode escapes. The lowercase `\u` form takes four hex digits for a two-byte (16-bit) code, and the uppercase `\U` form takes eight hex digits for a four-byte (32-bit) code.

In a `str`, all three escapes give a code point, not the encoded bytes. In a `bytes` literal, only the hex escapes work, and they give raw byte values. Simple ASCII characters are one byte each in most encodings, which is why ASCII works as a binary-compatible subset.

```text
>>> ord('X') # Character 'X' has code-point value 88
88
>>> chr(88) # Code-point 88 stands for character 'X'
'X'
>>> S = 'XYZ' # str: code points display as their character glyphs
>>> S
'XYZ'
>>> len(S) # 3 characters (not necessarily bytes) long
3
>>> S.encode('ascii') # Values 0…127 in 1 byte each (ASCII shown as chars)
b'XYZ'
>>> S.encode('latin-1') # Values 0…255 in 1 byte each
b'XYZ'
>>> S.encode('utf-8') # Values 0…127 in 1 byte, 128…2047 in 2, others 3~4
b'XYZ'
```

UTF-16 and UTF-32 use two and four bytes for every character, even for plain ASCII. Their data is fast to process, but it takes more space and bandwidth. In the output below, ASCII bytes print as characters, and each result starts with a BOM header of two or four bytes:

```text
>>> S
'XYZ'
>>> S.encode('utf-16') # Always 2 or 4 bytes per character, with BOM header
b'\xff\xfeX\x00Y\x00Z\x00'
>>> S.encode('utf-32')
b'\xff\xfe\x00\x00X\x00\x00\x00Y\x00\x00\x00Z\x00\x00\x00'
```

Non-ASCII characters use escapes in the same way. The hex literals `0xC4` and `0xE8` are code points for two accented characters outside ASCII. A `str` can hold them, because `str` supports all of Unicode:

```text
>>> chr(0xc4) # 0xC4 and 0xE8 are accented characters outside ASCII
'Ä'
>>> chr(0xe8)
'è'
>>> S = '\xc4\xe8' # Hex escapes: code-point values, not encoded bytes
>>> S
'Äè'
>>> S = 'Äè' # Unicode escapes: 16-bits (2-bytes)
>>> S
'Äè'
>>> len(S) # 2 characters long (not number of bytes!)
2
```

Encoding that string shows the byte cost of each encoding. ASCII fails. Latin-1 uses one byte per character, and UTF-8 uses two:

```text
>>> S = 'Äè'
>>> S.encode('ascii')
UnicodeEncodeError: 'ascii' codec can't encode characters in position 0-1:
ordinal not in range(128)
>>> S.encode('latin-1') # 1 byte per character
b'\xc4\xe8'
>>> S.encode('utf-8') # 2 bytes per character
b'\xc3\x84\xc3\xa8'
>>> len(S.encode('latin-1')) # 2 bytes in latin-1, 4 in utf-8
2
>>> len(S.encode('utf-8'))
4
```

The reverse trip works too. You can decode raw bytes to a `str`. You can read the bytes by hand and decode them, but the encoding you pass to `open` does the same decoding for you. That also avoids errors from reading part of a multibyte character when you read in chunks:

```text
>>> B = b'\xc4\xe8'
>>> B
b'\xc4\xe8'
>>> len(B) # 2 raw bytes, 2 characters
2
>>> B.decode('latin-1') # Decode to latin-1 text
'Äè'
>>> B = b'\xc3\x84\xc3\xa8'
>>> len(B) # 4 raw bytes
4
>>> B.decode('utf-8')
'Äè'
>>> len(B.decode('utf-8')) # 2 Unicode characters
2
```

You can also build a `str` piece by piece with `chr`, though that gets tedious for long text. The `\u` and `\U` escapes are usually simpler:

```text
>>> S = 'AÄB\U000000e8C'
>>> S # A, B, C, and 2 non-ASCII characters
'AÄBèC'
>>> len(S) # 5 characters long
5
>>> S.encode('latin-1')
b'A\xc4B\xe8C'
>>> len(S.encode('latin-1')) # 5 bytes in latin-1
5
>>> S.encode('utf-8')
b'A\xc3\x84B\xc3\xa8C'
>>> len(S.encode('utf-8')) # 7 bytes in utf-8
7
>>> S.encode('cp500') # Two other Western European encodings
b'\xc1c\xc2T\xc3'
>>> S.encode('cp850') # 5 bytes each
b'A\x8eB\x8aC'
>>> S = 'code' # ASCII text is the same in most
>>> S.encode('latin-1')
b'code'
>>> S.encode('utf-8')
b'code'
>>> S.encode('cp500') # But not in cp500: IBM ebcdic
b'\x83\x96\x84\x85'
>>> S.encode('cp850')
b'code'
>>> S = 'A' + chr(0xC4) + 'B' + chr(0xE8) + 'C' # str the hard way
>>> S
'AÄBèC'
```

Python gives a warning when you use Unicode escapes in a `bytes` literal. In `bytes`, a `\u` sequence is taken literally, not as an escape. This follows from what `bytes` holds: encoded bytes, not code points. Even when a code point and an encoded byte share a value in some encoding, the two remain different things.

```text
>>> S = 'A\xC4B\xE8C' # str recognizes hex and Unicode escapes
>>> S
'AÄBèC'
>>> S = 'AÄB\U000000E8C' # 4- and 8-digit Unicode escapes (str only)
>>> S
'AÄBèC'
>>> B = b'A\xC4B\xE8C' # bytes recognizes hex escapes, but not Unicode
>>> B
b'A\xc4B\xe8C'
>>> B = b'AÄB\U000000E8C' # Unicode escape sequences taken literally!
<stdin>:1: SyntaxWarning: invalid escape sequence '\u'
>>> B # bytes is encoded bytes, not code points
b'A\\u00C4B\\U000000E8C'
>>> B = b'A\xC4B\xE8C' # Use hex escapes for latin-1 bytes
>>> B # Prints non-ASCII bytes as hex
b'A\xc4B\xe8C'
>>> print(B) # For both interactive and print()
b'A\xc4B\xe8C'
>>> B.decode('latin-1') # Decode to str to interpret as text
'AÄBèC'
```

A `bytes` literal must hold ASCII characters, or use escapes for byte values above 127. A `str` literal can hold any character that the source file's encoding supports. Python reads source code as UTF-8 by default.

```text
>>> S = 'AÄBèC' # Chars from UTF-8 if no encoding declaration
>>> S # Decoded to str when code is read by Py
'AÄBèC'
>>> B = b'AÄBèC'
SyntaxError: bytes can only contain ASCII literal characters.
>>> B = b'A\xC4B\xE8C' # Chars must be ASCII, or hex escapes
>>> B # Non-ASCIIs are latin-1 encoded bytes
b'A\xc4B\xe8C'
>>> B.decode('latin-1')
'AÄBèC'
>>> S.encode() # Source code encoded per UTF-8 by default
b'A\xc3\x84B\xc3\xa8C' # Methods use UTF-8 to encode, unless passed
>>> S.encode('utf-8')
b'A\xc3\x84B\xc3\xa8C'
>>> B.decode() # Raw bytes do not correspond to utf-8
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xc4 in position 1:…
```

Round trips between encodings keep the same code points. Here `cp500` is an IBM EBCDIC encoding. Encoding to it and decoding back returns the same text, and encoding that text to UTF-8 gives the original bytes again:

```text
>>> S = 'AÄBèC'
>>> S.encode() # Method's default utf-8 encoding
b'A\xc3\x84B\xc3\xa8C'
>>> T = S.encode('cp500') # "Convert" to EBCDIC bytes
>>> T
b'\xc1c\xc2T\xc3'
>>> U = T.decode('cp500') # Back to Unicode code points
>>> U
'AÄBèC'
>>> U.encode() # Back to UTF-8 bytes, by default
b'A\xc3\x84B\xc3\xa8C'
```

This pattern looks like a conversion between encodings. In practice, it creates different encoded forms of the same code points. Re-encoding text in a file works the same way: decode it, then encode it in the new encoding. The `open` function usually does this work for you.

Notice that the `str` literal `'AÄBèC'` contains raw Unicode characters, not escapes. That is simpler, as long as your source file and your GUI support the characters.

### Source-file encoding declarations

Escapes work for an occasional character. Coding many accented characters as escapes is tedious. Python reads source files as UTF-8 by default, so you can type the characters directly in string literals and other text in your script.

If you save your script in a different encoding, add a special comment near the top. The comment must be the first or second line. A `#!` line may come before it. The common form names the encoding:

```text
# -*- coding: latin-1 -*-
```

With that comment, Python reads the file's text in the named encoding, and it recognizes characters embedded in string literals. The example below shows the different ways to put non-ASCII text in Python code. Save it in Latin-1 for the comment to match:

```python
# -*- coding: Latin-1 -*-
#----------------------------------------------------------------------------
# Demo all the ways to code non-ASCII text in Python, plus source encodings.
#
# If this file is saved as Latin-1 text, it works as is. But changing the
# coding line above to either ASCII or UTF-8 will then fail because the
# Latin-1 0xc4 and 0xe8 saved in myStr1's value are not valid in either.
#
# A UTF-8 line works if this file is also saved as UTF-8 to make its myStr1
# text match. Because UTF-8 is the default for source, the line above is
# optional if the file is saved as UTF-8 or its text is all UTF-8 compatible
# (e.g., ASCII, which is a subset of both the Latin-1 and UTF-8 encodings).
#----------------------------------------------------------------------------
myStr1 = 'AÄBèC' # Raw, per source encoding
myStr2 = 'A\xc4B\xe8C' # Hex code-point escapes
myStr3 = 'AÄB\U000000e8C' # Unicode short/long escapes
myStr4 = 'A' + chr(0xC4) + 'B' + chr(0xE8) + 'C' # Concatenated code points
import sys, locale
print('Sys hosting platform: ', sys.platform)
print('Sys default encoding: ', sys.getdefaultencoding())
print('Open default encoding:', locale.getpreferredencoding(False))
for aStr in (myStr1, myStr2, myStr3, myStr4):
    print(f'{aStr}, strlen={len(aStr)}', end=', ') # Decoded text+length
    bytes1 = aStr.encode() # Default UTF-8: 2 bytes for accents
    bytes2 = aStr.encode('latin-1') # Explicit Latin-1: 1 byte per char
    #bytes3 = aStr.encode('ascii') # ASCII fails: outside 0...127 range
    print(f'byteslen1={len(bytes1)}, byteslen2={len(bytes2)}') # Encoded length
```

Running this file prints the four strings, their character lengths, and their byte lengths in two encodings that work. The first is the default UTF-8 of `encode`, and the second is an explicit Latin-1. The platform and default-encoding lines vary by host, but the rest of the output does not:

```text
$ python3 source-encoding-latin1.py
Sys hosting platform: darwin
Sys default encoding: utf-8
Open default encoding: UTF-8
AÄBèC, strlen=5, byteslen1=7, byteslen2=5
AÄBèC, strlen=5, byteslen1=7, byteslen2=5
AÄBèC, strlen=5, byteslen1=7, byteslen2=5
AÄBèC, strlen=5, byteslen1=7, byteslen2=5
```

To convert the file to UTF-8, you can read it as Latin-1 and write it back as UTF-8. Then either edit the first line to name UTF-8 or delete that line, since UTF-8 is Python's default for source code. A `diff` shows the two versions differ only in the coding line and the rendered literal:

```text
$ diff source-encoding-latin1.py source-encoding-utf8.py
1c1
< # -*- coding: Latin-1 -*-
---
> # -*- coding: UTF-8 -*-
13c13
< myStr1 = 'A?B?C'
---
> myStr1 = 'AÄBèC'
$ python3 source-encoding-utf8.py # Same output as Latin-1 version above
```

Most programmers use UTF-8 for source files, and that is the safe choice. Python's standard manual covers the less common options, such as Unicode property and character-name escapes.

Source encoding applies to the whole file. Variable names follow stricter rules. Some non-ASCII letters and digits are allowed in names, but symbols and emoji are not. For example, `hÄck` is a valid name, but a name with a symbol is not. The `isidentifier` method of `str` tests a name. Even when a name is valid, non-ASCII names can be hard to type on some keyboards. For that reason, the Python standard library uses ASCII-only names.

### Using byte strings

The `bytes` type and its mutable partner `bytearray` handle binary data. They can hold encoded text too, but their scope is wider. Anything that can be stored as bytes works with them, and that covers all digital data.

As noted earlier, `bytes` supports the sequence operations and most of the methods of `str`. Because you cannot mix `bytes` and `str` without explicit conversions, the usual rule is simple. Use `str` and text files for text, and use `bytes` and binary files for binary data.

#### Methods

Some methods exist on only one of the two types. `decode` and `hex` belong to `bytes`, while `casefold`, `encode`, `format`, and `isidentifier` belong to `str`. Most other methods are shared. You can compare the two lists with `dir`, using `set(X) - set(Y)` to find the items in `X` but not in `Y`:

```text
$ python3
Python 3.12.2 (v3.12.2:6abddd9f6a, Feb 6 2024,…
# Attributes unique to str
>>> sorted(set(dir('abc')) - set(dir(b'abc')))
['casefold', 'encode', 'format', 'format_map', 'isdecimal', 'isidentifier',
'isnumeric', 'isprintable']
# Attributes unique to bytes
>>> sorted(set(dir(b'abc')) - set(dir('abc')))
['__buffer__', '__bytes__', 'decode', 'fromhex', 'hex']
```

The `__mod__` and `__rmod__` methods implement the `%` operator, and both types have them. The `decode` method turns raw bytes into `str`, and `encode` turns `str` into raw bytes. Methods on `bytes` return new `bytes` objects, not `str` objects. Like `str`, `bytes` is immutable:

```text
>>> B = b'code' # b'…' bytes literal
>>> B.find(b'od') # Search for substr offset
1
>>> B.replace(b'od', b'XY') # New bytes with replacement
b'cXYe'
>>> B
b'code'
>>> B[0] = 'x'
TypeError: 'bytes' object does not support item assignment
```

#### Sequence operations

Indexing, slicing, concatenation, and repetition work on both types, as they do on lists. Both are sequences, but their items differ. A `str` is a sequence of code points, and a `bytes` is a sequence of byte-size integers. Indexing a `bytes` returns an integer, while indexing a `str` returns a one-character `str`.

```text
>>> B = b'code' # bytes and str are both sequences
>>> B # Bytes in the 0…127 range display as ASCII
b'code'
>>> B[0], B[-1] # Indexing: returns a byte's integer value
(99, 101)
>>> 'code'[0] # But indexing a str returns a 1-item str
'c'
>>> chr(B[0]) # Unicode character (code point) for byte's value
'c'
>>> list(B) # But it's really integer bytes
[99, 111, 100, 101]
>>> b'A\x42C\xFF\x63' # That happen to display as ASCII if in 0…127
b'ABC\xffc'
>>> chr(0x63), hex(B[0]) # And accept hex escapes for byte values
('c', '0x63')
>>> B[1:], B[:-1] # Slicing: bytes (that display 0…127 as ASCII)
(b'ode', b'cod')
>>> len(B) # Length: number bytes (not necessarily characters)
4
>>> B + b'lmn' # Concatenation: bytes
b'codelmn'
>>> B * 4 # Repetition: bytes
b'codecodecodecode'
```

#### Formatting bytes

One notable exception to the same-operations rule is formatting. The `%` operator works on `bytes` from Python 3.5 onward. The `format` method and f-strings do not work on `bytes`, which is an odd split for a language with several formatting styles:

```text
>>> b'a %s string' % b'fine' # Py 3.5+ formatting for bytes
b'a fine string'
>>> b'a %s string' % bytes([0xFF, 0xFE]) # Non-ASCII bytes work too
b'a \xff\xfe string'
>>> 'a {} string'.format('fine') # But format method only for str
'a fine string'
>>> b'a {} string'.format(b'fine')
AttributeError: 'bytes' object has no attribute 'format'
>>> kind = 'fine'
>>> f'a {kind} string' # But f-strings only for str
'a fine string'
>>> bf'a {kind} string'
SyntaxError: invalid syntax
```

Some reasons for this choice are sound. Raw bytes may hold text in any encoding, or no text at all. Plugging ASCII text into a UTF-16 string or an image makes little sense. Still, the `%` operator is an exception to a rule that the other formatting styles do not follow.

Encoding a formatted string is a different operation. The result depends on the encoding you choose. Encoding fails when the encoding cannot hold every character:

```text
>>> kind = 'fine'
>>> f'a {kind} string'.encode() # Encoding != bytes operations
b'a fine string'
>>> kind = 'AÄBèC' # And narrow encodings may fail
>>> f'a {kind} string'.encode('ascii')
UnicodeEncodeError: 'ascii' codec can't encode character '\xc4' in position 3:…
```

#### Other ways to make bytes

A `bytes` object can come from the `b'…'` literal, from the `bytes` constructor with a `str` and an encoding name, from an iterable of integers, or from encoding a `str` with the default or a passed-in encoding. Decoding goes the other way and produces a `str`:

```text
>>> B = b'abc'
>>> B
b'abc'
>>> B = bytes('abc', 'ascii')
>>> B
b'abc'
>>> ord('a')
97
>>> B = bytes([97, 98, 99])
>>> B
b'abc'
>>> B = 'code'.encode() # Or bytes()
>>> B
b'code'
>>> S = B.decode() # Or str()
>>> S
'code'
```

#### Mixing string types

The `replace` method needs two `bytes` arguments. Passing a `str` fails. Python expects specific string types in some calls and does not convert them for you:

```text
>>> B = b'code'
>>> B.replace('od', 'XY')
TypeError: a bytes-like object is required, not 'str'
>>> B.replace(b'od', b'XY')
b'cXYe'
>>> B.replace(bytes('od'), bytes('XY'))
TypeError: string argument without an encoding
>>> B.replace(bytes('od', 'ascii'), bytes('XY', 'utf-8'))
b'cXYe'
```

Expressions follow the same rule. Keep text and binary data separate. If you must mix them, convert one side first:

```text
>>> b'ab' + 'cd'
TypeError: can't concat str to bytes
>>> b'ab'.decode() + 'cd' # bytes to str
'abcd'
>>> b'ab' + 'cd'.encode() # str to bytes
b'abcd'
>>> b'ab' + bytes('cd', 'ascii') # str to bytes
b'abcd'
```

Conversion is more than a change of type, since encoding and decoding produce different kinds of data. Binary-mode files also return `bytes` objects, so you will often meet `bytes` through files rather than through literals.

### The bytearray object

The `bytearray` type is a mutable sequence of integers from 0 to 255. It supports the same string methods and sequence operations as `bytes`. It also has the in-place change methods of lists.

Call `bytearray` with a `bytes` value, not a `str`, to make one. Then you can change it cell by cell, but each cell must hold an integer:

```text
>>> B = b'code' # A str 'code' does not work: not bytes
>>> C = bytearray(B)
>>> C
bytearray(b'code')
>>> C[0], chr(C[0]) # ASCII code-point integer for 'c'
(99, 'c')
>>> C[0] = 'x'
TypeError: 'str' object cannot be interpreted as an integer
>>> C[0] = b'x'
TypeError: 'bytes' object cannot be interpreted as an integer
>>> C[0] = ord('x')
>>> C
bytearray(b'xode')
>>> C[1] = b'Y'[0]
>>> C
bytearray(b'xYde')
```

The methods of `bytearray` overlap with those of `bytes` and `str`. It also has list-style methods such as `append`, `extend`, `insert`, `pop`, and `remove`:

```text
>>> sorted(set(dir(b'abc')) - set(dir(bytearray(b'abc'))))
{'__bytes__', '__getnewargs__'}
>>> sorted(set(dir(bytearray(b'abc'))) - set(dir(b'abc')))
['__alloc__', '__delitem__', '__iadd__', '__imul__', '__release_buffer__',
'__setitem__', 'append', 'clear', 'copy', 'extend', 'insert', 'pop', 'remove', 'reverse']
>>> C
bytearray(b'xYde')
>>> C.append(b'LMN')
TypeError: 'bytes' object cannot be interpreted as an integer
>>> C.append(b'LMN'[0])
>>> C
bytearray(b'xYdeL')
>>> C.append(ord('M'))
>>> C
bytearray(b'xYdeLM')
>>> C.extend(b'NO')
>>> C
bytearray(b'xYdeLMNO')
```

It also supports the usual sequence operations and string methods:

```text
>>> C + b'!#'
bytearray(b'xYdeLMNO!#')
>>> C[0], chr(C[0])
(120, 'x')
>>> C[1:]
bytearray(b'YdeLMNO')
>>> len(C)
8
>>> C.replace('xY', 'co')
TypeError: a bytes-like object is required, not 'str'
>>> C.replace(b'xY', b'co')
bytearray(b'codeLMNO')
>>> C
bytearray(b'xYamLMNO')
>>> C * 4
bytearray(b'xYdeLMNOxYdeLMNOxYdeLMNOxYdeLMNO')
```

You can make a `bytes` or `bytearray` from any sequence of integers or a generator, not just from text. An integer from 0 to 255 becomes one byte. Passing a single integer creates that many zero bytes, which is a surprise to many new users:

```text
>>> bytes([1, 2, 3, 4]), bytearray([1, 2, 3, 4])
(b'\x01\x02\x03\x04', bytearray(b'\x01\x02\x03\x04'))
>>> bytes([115]) # int => bytes
b's'
>>> bytes([115])[0] # bytes => int
115
>>> bytes([999]) # Too big for a byte
ValueError: bytes must be in range(0, 256)
>>> bytes(115) # Lots of zeroes!
b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00…
>>> bytes(range(97, 104)), bytes(c + 97 for c in range(7)) # Generators too
(b'abcdefg', b'abcdefg')
```

The three types differ in role. Use `str` for decoded text, `bytes` for binary data (including encoded text), and `bytearray` for binary data that you change in place. The `bytearray` type avoids the time and space cost of making a new copy for every change.

```text
>>> B = b'code' # Bytes
>>> list(B)
[99, 111, 100, 101]
>>> C = bytearray(b'code') # Changeable bytes
>>> list(C)
[99, 111, 100, 101]
>>> S = 'code' # Unicode text
>>> list(S)
['c', 'o', 'd', 'e']
```

### Text-file basics

The mode of a file decides how its content is read and which Python type you use. Text mode uses `str` objects. Binary mode uses `bytes` objects. The default mode is `rt`, which means text input, and `r` means the same thing.

The first argument to `open` is the pathname, which can be absolute or relative to the current directory. The second argument is the mode, where `w` means write text. A `write` call returns the number of items it wrote. Those items are characters in text mode and bytes in binary mode.

Here is a basic write and read of one line:

```text
>>> file = open('temp.txt', 'w') # Use default encoding on host, mode w=write
>>> size = file.write('abc\n') # Returns number characters written
>>> file.close() # Manual close to flush output buffer
>>> file = open('temp.txt') # Default mode is "r" == "rt": text input
>>> text = file.read()
>>> text
'abc\n'
```

The `close` call is optional in CPython, which closes files when they are garbage collected. Even so, closing is good practice. It flushes changes and keeps memory from growing. The example above uses the platform default encoding without naming one. That works for plain ASCII text.

### Text and binary modes

Here is the same content read in text mode and in binary mode. Text mode needs a `str` for writing. Binary mode with the `rb` mode returns `bytes`. The output below comes from Windows, where text mode turns `\n` into `\r\n` on disk:

```text
$ py -3 # Run on Windows (no \r on Unix)
>>> open('temp.txt', 'w').write('abc\n') # Text-mode output, provide a str
4
>>> open('temp.txt', 'r').read() # Text-mode input, returns a str
'abc\n'
>>> open('temp.txt', 'rb').read() # Binary-mode input, returns a bytes
b'abc\r\n'
```

Text-mode files map `\n` to and from the platform's newline separator. On Windows that separator is `\r\n`, and on Unix it is just `\n`. Binary mode skips both the newline mapping and the decoding, so it returns the file's raw content.

Binary output works the same way, but it needs a `bytes` object. In this example, the newline stays `\n` even on Windows, because no mapping happens:

```text
>>> open('temp.bin', 'wb').write(b'abc\n') # Binary-mode output, send a bytes
4
>>> open('temp.bin', 'r').read() # Text-mode input, receive a str
'abc\n'
>>> open('temp.bin', 'rb').read() # Binary-mode input, bytes sans mapping
b'abc\n'
```

Binary data can contain zero bytes. A zero byte is the null character in ASCII and in UTF-8. Text mode can still read it as part of a `str`:

```text
>>> open('temp.bin', 'wb').write(b'a\x00c') # Binary data included
3
>>> open('temp.bin', 'r').read() # Text-mode: str with NUL
'a\x00c'
>>> open('temp.bin', 'rb').read() # Binary mode: bytes
b'a\x00c'
```

Binary files always return `bytes` when you read them. They accept either `bytes` or `bytearray` for writing. Most APIs that take `bytes` also take `bytearray`:

```text
>>> BA = bytearray(b'\x01\x02\x03')
>>> open('temp.bin', 'wb').write(BA)
3
>>> open('temp.bin', 'r').read()
'\x01\x02\x03'
>>> open('temp.bin', 'rb').read()
b'\x01\x02\x03'
```

Python will not mix the two kinds of data in a file. Writing a `bytes` value to a text file fails. Writing a `str` value to a binary file also fails. Python cannot guess how you want to read the contents, so it refuses to convert them. Use `str` for text and `bytes` for binary data:

```text
>>> open('temp.txt', 'w').write('abc\n') # Auto encodes str to bytes
4
>>> open('temp.txt', 'w').write(b'abc\n') # But bytes != decoded text
TypeError: write() argument must be str, not bytes
>>> open('temp.bin', 'wb').write(b'abc\n') # Writes raw bytes
4
>>> open('temp.bin', 'wb').write('abc\n') # But str != raw bytes
TypeError: a bytes-like object is required, not 'str'
```

### Unicode-text files

Text files can carry a specific encoding. Pass the name in the `encoding` argument of `open`. Then the file decodes text on reads and encodes text on writes. For a file named by the variable `pathname`, these two calls show the idea:

- `open(pathname, 'r', encoding='utf8')` returns a file object that decodes UTF-8 when it reads.
- `open(pathname, 'w', encoding='latin1')` returns a file object that encodes Latin-1 when it writes.

The next example writes and reads a short string that has three non-ASCII characters. The file is written in UTF-8:

```text
>>> file = open('uni.txt', 'w', encoding='utf8') # Auto encodes to bytes
>>> file.write(' 2 hÄck ')
10
>>> file.close()
>>> text = open('uni.txt', 'r', encoding='utf8').read() # Auto decodes to str
>>> text
' 2 hÄck '
>>> [ord(c) for c in text] # Character code points
[128155, 32, 50, 32, 104, 196, 99, 107, 32, 128013]
>>> raw = open('uni.txt', 'rb').read() # No decoding applied
>>> raw
b'\xf0\x9f\x92\x9b 2 h\xc3\x84ck \xf0\x9f\x90\x8d'
```

The encoding you pass must match the file's data. ASCII cannot hold the accented and emoji characters in this text, so ASCII fails both on reads and on writes:

```text
>>> open('uni.txt', 'r', encoding='ascii').read()
UnicodeDecodeError: 'ascii' codec can't decode byte 0xf0 in position 0:…
>>> open('ascii.txt', 'w', encoding='ascii').write(' 2 hÄck ')
UnicodeEncodeError: 'ascii' codec can't encode character '\U0001f49b'…
>>> hex(ord('\U0001f49b')) # ASCII will always break your heart?
'0x1f49b'
```

UTF-16 handles the same text in full. The stored bytes differ from the UTF-8 bytes, but the code points that come back are the same:

```text
>>> file = open('uni2.txt', 'w', encoding='utf16') # UTF-16 works too
>>> file.write(' 2 hÄck ')
10
>>> file.close()
>>> text = open('uni2.txt', 'r', encoding='utf16').read() # Files encode+decode
>>> text
' 2 hÄck '
>>> [ord(c) for c in text] # Same code points
[128155, 32, 50, 32, 104, 196, 99, 107, 32, 128013]
>>> open('uni2.txt', 'rb').read() # Different encoding
b'\xff\xfe=\xd8\x9b\xdc \x002\x00 \x00h\x00\xc4\x00c\x00k\x00 \x00=\xd8\r\xdc'
```

Encodings cannot be mixed. Reading a UTF-16 file as UTF-8 fails, because the encoded bytes differ. Binary mode and error handlers can help with unknown encodings, but the encoding usually has to match the file:

```text
>>> open('uni.txt', 'r', encoding='utf16').read()
UnicodeDecodeError: 'utf-16-le' codec can't decode byte 0x8d in position 16:…
>>> open('uni2.txt', 'r', encoding='utf8').read()
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff in position 0:…
```

With no `encoding` argument, a text file uses the default for the host and platform. That default is from `locale`. The results can look right when the default and the file agree. Still, relying on the default makes your program depend on where its files were made. Use explicit encodings, especially for web servers that run as generic users with unreliable environment settings.

For a real file, the workflow is usually simple. Open a file with an encoding, read it, change the text, and write it back. Reading a web page or an image is routine once you know the modes. An image uses binary mode with `rb`, and a page uses text mode with an explicit encoding:

```text
>>> text = open('Websites/about-lp5e.html', encoding='utf8').read()
>>> text[:79]
'<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.o'
>>> image = open('Websites/lp5e-large.jpg', mode='rb').read()
>>> image[:20]
b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00'
```

Once content is loaded, all the `str` and `bytes` operations are available. Saving follows the same pattern. Use an encoding for text and binary mode for bytes:

```text
>>> text = text.replace('2013', '2024')
>>> open('Websites/about-lp6e.html', mode='w', encoding='utf8').write(text)
>>> image = some_sort_of_modding(image)
>>> open('Websites/lp6e-large.jpg', mode='wb').write(image)
```

The `open` function takes more arguments. The `newline` argument changes newline mapping. The `errors` argument decides how encoding and decoding errors are handled, and `'surrogateescape'` keeps failing bytes so they can be restored on output. The `buffering` argument changes buffering. The defaults suit most programs, so check the Python standard library manual for these options.

The `codecs` module also has its own `open`, which returns a file that decodes and encodes automatically. It was used for Python 2 compatibility. New code has no clear reason to use it, though legacy code may:

```text
>>> import codecs
>>> f = codecs.open('uni.txt', 'r', encoding='utf8')
>>> f.read()
' 2 hÄck '
```

### Unicode and other string tools

Many standard-library tools follow the same split between `str` and `bytes`. The following sample shows how some of them behave. The rest belong to application topics, and the Python Library Reference covers them in depth.

The `re` pattern-matching module works with `str`, `bytes`, and `bytearray`. The result type follows the type of the string you pass in. The pattern and the text must match in type, and a `bytearray` cannot be a pattern because it is mutable:

```text
>>> import re
>>> S = ' is the fastest way to !'
>>> B = b'Python is the fastest way to pizza!'
>>> re.match('(.*) the (.*) way (.*)', S).groups() # str + str => str
(' is', 'fastest', 'to !')
>>> re.match(b'(.*) the (.*) way (.*)', B).groups() # bytes + bytes => bytes
(b'Python is', b'fastest', b'to pizza!')
>>> re.match(b'(.*) the (.*) way (.*)', bytearray(B)).groups()
(b'Python is', b'fastest', b'to pizza!')
>>> re.match('(.*) the (.*) way (.*)', B).groups()
TypeError: cannot use a string pattern on a bytes-like object
>>> re.match(b'(.*) the (.*) way (.*)', S).groups()
TypeError: cannot use a bytes pattern on a string-like object
>>> re.match(bytearray(b'(.*) the (.*) way (.*)'), bytearray(B)).groups()
TypeError: unhashable type: 'bytearray'
```

The `struct` module packs and unpacks binary data. It works with `bytes` and `bytearray` only, because it is meant for binary data and not for decoded text. A format string such as `'>i4sh'` gives the size and type of each item. The `>` prefix selects big-endian byte order:

```text
>>> import struct
>>> B = struct.pack('>i4sh', 7, b'code', 8) # int , bytes(4s), int(h) => bytes
>>> B
b'\x00\x00\x00\x07code\x00\x08'
>>> vals = struct.unpack('>i4sh', B) # Packed data is bytes, not str
>>> vals
(7, b'code', 8)
>>> vals = struct.unpack('>i4sh', B.decode())
TypeError: a bytes-like object is required, not 'str'
```

Packed data often goes to a binary file, so it survives between program runs. This is useful for saving application settings:

```text
>>> F = open('data.bin', 'wb') # Open binary output file
>>> data = struct.pack('>i4sh', 7, b'code', 8) # Create packed binary data
>>> data # bytes, not str
b'\x00\x00\x00\x07code\x00\x08'
>>> F.write(data) # Write to the file
10
>>> F.close() # Flush changes
>>> F = open('data.bin', 'rb') # Open binary input file
>>> data = F.read() # Read bytes
>>> data
b'\x00\x00\x00\x07code\x00\x08'
>>> values = struct.unpack('>i4sh', data) # Extract packed binary data
>>> values # Back to Python objects
(7, b'code', 8)
```

The `pickle` module saves almost any Python object, not just the values that `struct` packs. Even so, `pickle` always produces a `bytes` object, whatever the protocol. The `dumps` call returns that pickled byte string:

```text
>>> import pickle # dumps() returns pickle string
>>> pickle.dumps(['code', 4, '']) # Default protocol=binary
b'\x80\x04\x95\x15\x00\x00\x00\x00 …etc… \x04\x8c\x04\xf0\x9f\x90\x8d\x94e.'
>>> pickle.dumps(['code', 4, ''], protocol=0) # ASCII protocol 0, still bytes!
b'(lp0\nVcode\np1\naI4\naV\\U0001f40d\np2\na.'
```

Because of that, files for pickled objects must be opened in binary mode. The `dump` call writes bytes to the open file, and text mode rejects bytes. Reading back in text mode can also fail, and on other hosts it may return garbage instead of an error:

```text
>>> pickle.dump(['code', 4, ''], open('temp.pkl', 'w')) # bytes+text mode fail
TypeError: write() argument must be str, not bytes
>>> pickle.dump(['code', 4, ''], open('temp.pkl', 'w'), protocol=0)
TypeError: write() argument must be str, not bytes
>>> pickle.dump(['code', 4, ''], open('temp.pkl', 'wb')) # Always binary mode
>>> open('temp.pkl', 'r').read()
UnicodeDecodeError: 'utf-8' codec can't decode byte 0x80 in position 0:…
```

Pickle data is not text, so use binary mode for both writing and reading. Save with `dump` and load with `load`, both through files opened in `'wb'` and `'rb'`:

```text
>>> pickle.dump(['code', 4, ''], open('temp.pkl', 'wb')) # Save to file
>>> pickle.load(open('temp.pkl', 'rb')) # Load from file
['code', 4, '']
>>> open('temp.pkl', 'rb').read()
b'\x80\x04\x95\x15\x00\x00\x00\x00 …etc… \x04\x8c\x04\xf0\x9f\x90\x8d\x94e.'
```

The `json` module, from Chapter 9, is a related tool. It turns a tree of nested objects into text that you can save. Unlike `pickle`, it does not support arbitrary objects. It supports basic types and built-in containers, and its format is language-neutral, which makes it easier for other programs to read.

The `json` module always produces a `str`, so files for saves and loads should use text mode. JSON files are often written in UTF-8 for portability, but any consistent encoding works:

```text
>>> import json
>>> vals = ['code', {'app': ('', None, 1.23, 99)}]
>>> json.dumps(vals)
'["code", {"app": ["\\ud83d\\ude42", null, 1.23, 99]}]'
>>> text = json.dumps(vals) # Save to/load from str
>>> anew = json.loads(text)
>>> anew
['code', {'app': ['', None, 1.23, 99]}]
>>> file = open('data.txt', 'w', encoding='utf8') # Save/load text-mode file
>>> json.dump(vals, file)
>>> file.close()
>>> file = open('data.txt', 'r', encoding='utf8')
>>> json.load(file)
['code', {'app': ['', None, 1.23, 99]}]
```

File names have a Unicode story too. In short, `str` is the normal type for file pathnames in Python, and it is the recommended choice for portable code. Python's file tools translate `str` names to and from the encoding that the host and device use.

Python's file tools also accept file names as `bytes`, which skips automatic filesystem encoding in some cases. This can help with fine control over file name encodings. It is rarely needed in ordinary programs, and the Python manuals say it matters mainly on some Unix systems with undecodable names.

Here is a demo that makes files with both `str` and `bytes` names. The examples run in a subfolder, and the names include a non-ASCII character:

```text
>>> import sys, os, glob
>>> sys.getfilesystemencoding() # Filesystem default: macOS and Win11
'utf-8'
>>> name1 = 'hÄck1' # str filenames
>>> name2 = 'hÄck2'
>>> name2.encode('utf8') # bytes equivalent for name2 str
b'h\xc3\x84ck\xf0\x9f\x99\x822'
>>> os.listdir() # Make files with str and bytes names
[]
>>> open(name1, mode='w', encoding='utf8').write('text1')
5
>>> open(b'h\xc3\x84ck\xf0\x9f\x99\x822', 'w', encoding='utf8').write('text2')
5
>>> os.listdir() # Both show up on the filesystem
['hÄck1', 'hÄck2']
>>> open('hÄck2').read() # And can be accessed either way
'text2'
>>> open('hÄck2'.encode('utf8')).read()
'text2'
```

On macOS and on Windows since Python 3.6, Python encodes `bytes` names with UTF-8. Windows converts them further to UTF-16 for its API. Linux, and so Android, accepts any bytes as file names. Python still tries UTF-8 when it converts names to and from `str`, and it uses surrogate escapes for encoding errors.

Using `bytes` names only works when the encoding matches what Python or the filesystem expects. The next example passes Latin-1 bytes. It fails on macOS and on Windows:

```text
>>> 'hÄck'.encode('latin-1'), 'hÄck'.encode('utf-8')
(b'h\xc4ck', b'h\xc3\x84ck')
>>> b'h\xc4ck'.decode('utf8')
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xc4 in position 1:…
>>> open(b'h\xc4ck', 'w')
OSError: [Errno 92] Illegal byte sequence: b'h\xc4ck'
# open(b'h\xc4ck'.decode('latin1'), 'w') # Works: convert to str
# open(b'h\xc3\x84ck', 'w') # Works: use UTF-8 encoding
```

On Linux and Android the same call can work. Those systems decode the Latin-1 name with UTF-8 and keep the bad byte as a surrogate-escaped `str`. Even then, the result depends on the filesystem. On a removable exFAT drive, the Latin-1 name fails. So using arbitrary bytes in `open` depends on both the platform and the filesystem. Avoid it.

The `os` module lists directories in the same form you pass in. A `str` path gives `str` names, and a `bytes` path gives `bytes` names. The names can then be used in other file tools:

```text
>>> os.listdir('.') # str gives strs, bytes gives bytes
['hÄck1', 'hÄck2']
>>> os.listdir(b'.')
[b'h\xc3\x84ck\xf0\x9f\x99\x821', b'h\xc3\x84ck\xf0\x9f\x99\x822']
>>> for name in os.listdir('.'):
...     print(name, '=>', open(name).read())
hÄck1 => text1
hÄck2 => text2
>>> for name in os.listdir(b'.'):
...     print(name, '=>', open(name).read())
b'h\xc3\x84ck\xf0\x9f\x99\x821' => text1
b'h\xc3\x84ck\xf0\x9f\x99\x822' => text2
```

The `glob` module expands file name patterns in both forms. The `os.fsdecode` function decodes a name with the host's filesystem encoding:

```text
>>> glob.glob('h*ck*') # str gives str, bytes gives byte
['hÄck1', 'hÄck2']
>>> glob.glob(b'h*ck*')
[b'h\xc3\x84ck\xf0\x9f\x99\x821', b'h\xc3\x84ck\xf0\x9f\x99\x822']
>>> for name in glob.glob(b'h*ck*'):
...     print(name.decode(sys.getfilesystemencoding()), os.fsdecode(name))
hÄck1 hÄck1
hÄck2 hÄck2
```

Tools that make and walk folders also accept both forms. The following demo ran on Windows, so the path separators and the order of the output may differ on your system:

```text
>>> os.mkdir('sub') # Make dirs with str or bytes
>>> os.mkdir('subbytes'.encode('utf8')) # and walk them with both
>>> os.mkdir('subbytes/subsub')
>>> os.listdir()
['hÄck1', 'hÄck2', 'sub', 'subbytes']
>>> os.listdir('subbytes')
['subsub']
>>> for (dirhere, subshere, fileshere) in os.walk('.'):
...     print(dirhere, '=>', subshere, fileshere)
. => ['sub', 'subbytes'] ['hÄck1', 'hÄck2']
.\sub => [] []
.\subbytes => ['subsub'] []
.\subbytes\subsub => [] []
>>>
>>> for (dirhere, subshere, fileshere) in os.walk(b'.'):
...     print(dirhere, '=>', subshere, fileshere)
```

`bytes` names work, but `str` names are almost always the better choice. Python's tools already handle `str` paths with care, and `str` names avoid many portability problems in apps that run on several platforms and devices.

### Unicode defaults and UTF-8 mode

The default encoding is a weirdly tangled topic. Each part of Python uses its own default, so it helps to see them together.

The default for source code and for the `encode` and `decode` methods is always UTF-8. The default for file names comes from `sys.getfilesystemencoding()`. The default for file content read through `open` comes from `locale.getpreferredencoding(False)`.

The `sys.getdefaultencoding()` value cannot be changed, as of Python 3.2. The file-name default is usually UTF-8, including on Windows since Python 3.6. That default rarely matters if your names are always `str`.

The default for `open` is the least consistent. It is not simply the result of `locale.getencoding()` on every platform. It is UTF-8 when UTF-8 mode is on, which Python 3.7 introduced. Otherwise, it is the result of `getencoding()`. On Windows that can be a code-page encoding such as `cp1252`. Unix systems usually use UTF-8, so a bare `open` is not portable for non-ASCII text.

UTF-8 mode fixes this. Turn it on by setting the environment variable `PYTHONUTF8` to `1`, or by starting Python with `-X utf8`. The `getencoding()` function, added in Python 3.11, does not change with UTF-8 mode, but `open` and the older `getpreferredencoding(False)` do.

The `locale` results can also depend on the platform, environment variables, and command-line switches. Android is always UTF-8. On Windows, Python 3.15 is planned to turn UTF-8 mode on by default, so code without explicit encodings will match other platforms.

A few other environment variables change related behavior. `PYTHONIOENCODING` sets the encoding of the standard streams, such as `sys.stdout`, when they are redirected to a file. UTF-8 mode also affects redirected streams, unless `PYTHONIOENCODING` is set too. The other variables cover console streams on Windows, file names on Windows, and forcing Unix encodings to skip UTF-8.

The practical advice is short. Use `str` for file names. Pass an explicit encoding to `open`, and do not rely on the defaults. The Python manuals have the full story when you need it.

### Byte-order marks (BOM)

Some encodings store a special marker at the start of a file. This marker is the byte-order mark, or BOM. It records the byte order of the data, which is its endianness, or it names the encoding in general. Text-mode files in Python skip the marker on input and write it on output when the encoding implies one.

UTF-16 and UTF-32 always carry a BOM that names the encoding and the big- or little-endian layout. A UTF-8 file may have a BOM, but it is not required, and the BOM only says that the file is UTF-8. Python handles both cases with specific encoding names.

- In UTF-16, the general name `utf-16` always processes the BOM. The name `utf-16-le` means little-endian and does not add or remove one.
- In UTF-8, the name `utf-8-sig` skips a BOM on input and writes one on output. The general name `utf-8` does neither.

To see this, save a short file in an editor and read it back in Python. On Windows, Notepad can save a file as plain ANSI text, which has no BOM. Its UTF-8 choice can add a three-byte BOM. Its UTF-16 choices add a two-byte BOM:

```text
$ py -3 # On Windows, post ANSI save in Notepad
>>> import locale
>>> locale.getpreferredencoding(False) # open default: ASCII&Latin-1 superset
'cp1252'
>>> open('code.txt', 'rb').read() # ASCII (and cp1252 and UTF-8) bytes
b'code\r\nCODE\r\n'
>>> open('code.txt', 'r').read() # Text mode also translates newlines
'code\nCODE\n'
>>> open('code.txt', 'r', encoding='utf-8').read()
'code\nCODE\n'
```

After a save as UTF-8 with a BOM, the file starts with the three bytes of the BOM. The default encoding keeps the BOM as a character. The `utf-8-sig` name removes it:

```text
>>> open('code.txt', 'rb').read() # After resaved: UTF-8 with 3-byte BOM
b'\xef\xbb\xbfcode\r\nCODE\r\n'
>>> open('code.txt', 'r').read() # Default+utf8 keep BOM, utf-8-sig drops
'ï»¿code\nCODE\n'
>>> open('code.txt', 'r', encoding='utf-8').read()
'﻿code\nCODE\n'
>>> open('code.txt', 'r', encoding='utf-8-sig').read()
'code\nCODE\n'
```

A UTF-16 big-endian file starts with a two-byte BOM. The name `utf-16` skips that BOM because the encoding implies it. The name `utf-16-be` decodes the big-endian data but keeps the BOM in the result:

```text
>>> open('code.txt', 'rb').read()
b'\xfe\xff\x00c\x00o\x00d\x00e\x00\r\x00\n\x00C\x00O\x00D\x00E\x00\r\x00\n'
>>> open('code.txt', 'r', encoding='utf-16').read()
'code\nCODE\n'
>>> open('code.txt', 'r', encoding='utf-16-be').read()
'﻿code\nCODE\n'
```

Other combinations of save and open show more. Reading with the wrong encoding can print garbage characters, because the bytes do not match the encoding.

Python can write these files too. Python adds a BOM automatically for `utf-16`. For UTF-8, `utf-8` writes no BOM, while `utf-8-sig` writes one. The same rule applies on input. The `utf-8-sig` name works on files with or without a BOM, so it is a safe choice when you do not know:

```text
>>> open('temp.txt', 'w', encoding='utf-8').write('code\nCODE\n')
10
>>> open('temp.txt', 'rb').read() # utf-8: no BOM
b'code\r\nCODE\r\n'
>>> open('temp.txt', 'w', encoding='utf-8-sig').write('code\nCODE\n')
10
>>> open('temp.txt', 'rb').read() # utf-8-sig: adds BOM
b'\xef\xbb\xbfcode\r\nCODE\r\n'
>>> open('temp.txt', 'r').read() # Default: bad BOM
'ï»¿code\nCODE\n'
>>> open('temp.txt', 'r', encoding='utf-8').read() # utf-8: keeps BOM
'﻿code\nCODE\n'
>>> open('temp.txt', 'r', encoding='utf-8-sig').read() # utf-8-sig: drops BOM
'code\nCODE\n'
```

The `utf-16` name writes its BOM in the platform's native byte order and always strips the BOM on input. The `sys.byteorder` value tells you the native order on your host:

```text
>>> import sys
>>> sys.byteorder # Windows host's default endianness
'little'
>>> open('temp.txt', 'w', encoding='utf-16').write('code\nCODE\n')
10
>>> open('temp.txt', 'rb').read()
b'\xff\xfec\x00o\x00d\x00e\x00\r\x00\n\x00C\x00O\x00D\x00E\x00\r\x00\n\x00'
>>> open('temp.txt', 'r', encoding='utf-16').read()
'code\nCODE\n'
```

The names `utf-16-le` and `utf-16-be` set the byte order explicitly. You may need to write or skip the BOM yourself in some cases. The `utf-16-le` name does not write a BOM, and `utf-16` cannot read a file that lacks one:

```text
>>> open('temp.txt', 'r', encoding='utf-16-le').read()
'﻿code\nCODE\n'
>>> open('temp.txt', 'w', encoding='utf-16-be').write('﻿code\nCODE\n')
11
>>> open('temp.txt', 'rb').read()
b'\xfe\xff\x00c\x00o\x00d\x00e\x00\r\x00\n\x00C\x00O\x00D\x00E\x00\r\x00\n'
>>> open('temp.txt', 'r', encoding='utf-16').read()
'code\nCODE\n'
>>> open('temp.txt', 'r', encoding='utf-16-be').read()
'﻿code\nCODE\n'
```

```text
>>> open('temp.txt', 'w', encoding='utf-16-le').write('CODE')
4
>>> open('temp.txt', 'rb').read() # Okay if BOM not present or expected
b'C\x00O\x00D\x00E\x00'
>>> open('temp.txt', 'r', encoding='utf-16-le').read()
'CODE'
>>> open('temp.txt', 'r', encoding='utf-16').read()
UnicodeError: UTF-16 stream does not start with BOM
```

Experiment with these encodings to build intuition. The Python library manuals have more detail on BOMs.

### Unicode normalization

Unicode has one more weakness. The standard does not give one code point to every character. Some characters have more than one valid form. This breaks equality tests, and it can cause trouble for text-processing programs.

The character `ñ` is a good example. It can be one code point, `ñ`, which is an `n` with a tilde. It can also be two code points, `n` and `̃`, which are a plain `n` followed by a combining tilde. The first form is called NFC, or the composed form, because the letter and accent are combined. The second form is called NFD, or the decomposed form, because its parts are split.

The Unicode standard says these two forms are the same character, and programs must treat them that way. Python shows both forms with escapes. Windows users may see different rendering in some terminals, especially for NFD:

```text
>>> L = 'ñ' # NFC form ('\xF1' works too)
>>> M = 'ñ' # NFD form
>>> L, M # The same character
('ñ', 'ñ')
```

Other characters have both forms too. Examples include `Å`, `è`, and `é`, along with a few Greek letters. Each pair looks the same to a reader but has different code points:

```text
>>> 'Å', 'Å' # NFD (1 code point), NFC (2 code points)
('Å', 'Å')
>>> 'è', 'è' # But it's the same character for both
('è', 'è')
>>> 'é', 'é'
('é', 'é')
>>> 'ϔ', 'ϔ'
('ϔ', 'ϔ')
```

The two forms differ in memory as code points. They also differ when encoded, because each encoding stores the code points differently. Decoding the encoded forms gives back the two different code-point sequences:

```text
>>> 'ñ'.encode('utf8'), 'ñ'.encode('utf8')
(b'\xc3\xb1', b'n\xcc\x83')
>>> b'\xc3\xb1'.decode('utf8'), b'n\xcc\x83'.decode('utf8')
('ñ', 'ñ')
```

The result is that equality fails. The `==` operator compares code points, so the two forms of `ñ` look equal on screen but are not equal in Python:

```text
>>> L = 'ñ'
>>> M = 'ñ'
>>> L, M # The same character
('ñ', 'ñ')
>>> L == M # But equality says no!
False
>>> len(L), len(M) # Because their code points differ
(1, 2)
```

Vendors favor different forms. macOS tends to prefer NFD, Windows and many others prefer NFC, and the choice can depend on the filesystem. Tools also differ in how well they accept the form they did not expect. The result is an interoperability problem.

The fix is to convert text to a common form before comparing it. Python's `unicodedata` module has a `normalize` function for this:

```python
from unicodedata import normalize # Python stdlib tool
L = 'ñ'
M = 'ñ'
print(L, M) # Same char, diff code points
print(L == M) # Equality fails
print(normalize('NFC', L) == normalize('NFC', M)) # Common-form equality works
print(normalize('NFD', L) == normalize('NFD', M)) # Either suffices, if the same
```

Running the same normalization on both sides makes them equal, and either NFC or NFD works, as long as you use the same form on both sides. Programs that compare file names from different platforms should normalize first. Otherwise, two names that look the same to users will fail to match, and searches and file syncs can break. The same rule applies to text from web content and other outside sources.

The full story has more detail. Canonical equivalence, which NFC and NFD share, is not the same as compatibility equivalence. Most programs do not need to care about that difference. The Unicode HOWTO in the Python manuals and the `casefold` string method are good next steps.

## Unicode and byte strings summary

Python has three string types. `str` holds Unicode text as code points. `bytes` holds binary data, including encoded text. `bytearray` is a mutable form of `bytes`. The types share most operations, but each has a clear role.

Non-ASCII characters can be coded in a `str` with hex escapes, `\u` escapes, or `\U` escapes, and all of them name code points. In a `bytes`, only hex escapes apply, and they give raw byte values. Source files are read as UTF-8 by default, and a coding comment can name another encoding.

Text-mode files encode and decode automatically, and they handle BOMs and newline translation. Binary-mode files transfer bytes unchanged. Pass an explicit encoding to `open` for text in a different encoding from your platform default. Use `bytes` for binary data, and use `str` for text.

ASCII is a kind of Unicode text. Its values from 0 to 127 are the same in many encodings, including Latin-1 and UTF-8. The BOM is a marker at the start of some encoded text that names the encoding and byte order. Normalization converts code points into one common form so that equal-looking text compares equal.

For ordinary ASCII scripts, `str` without special handling is usually enough. If you process non-ASCII text, pass encodings to `open`. If you handle binary files, work with `bytes`. If your code must run on many platforms or read content from unknown sources, use explicit encodings for every text file.

## Managed attributes

Most attributes are simple. A `person.name` fetch returns a stored value, and `person.name = value` stores a new one. The attribute usually lives in the object itself or in a class the object inherits from. That plain model handles most programs you will write.

Sometimes requirements change after the code is written. Suppose a `name` attribute must now be validated or transformed whenever it is read or set. The obvious fix is to replace the attribute with get and set methods, as in this sketch. The `valid` and `transform` helpers here are placeholders, not real functions:

```python
class Person:
    def getName(self):
        if not valid():
            raise TypeError('cannot fetch name')
        else:
            return self.name.transform()
    def setName(self, value):
        if not valid(value):
            raise TypeError('cannot change name')
        else:
            self.name = transform(value)
person = Person()
person.getName()
person.setName('value')
```

This fix has a cost. Every place that uses `name` in the program must change from attribute syntax to method calls. Clients also have to know which form to use. A method-based interface from the start keeps clients safe from later changes. Retrofitting one is harder.

This comes up more often than it seems. A cell in a spreadsheet-style program may start as a plain number and later become a calculation. An object's interface should handle that change without breaking code that already uses it. Managed attributes make that possible.

### Inserting code to run on attribute access

Managed attributes let you run code automatically when an attribute is fetched, assigned or deleted. You can add that logic after a class already exists, and existing client code keeps its simple syntax. Managed attributes also support usage modes that go beyond plain storage, such as computed values.

Python offers four accessor techniques for this job:

- The `property` built-in, which routes access to one specific attribute to functions you provide.
- The `__get__` and `__set__` descriptor methods, which handle one specific attribute and form the basis for properties and slots.
- The `__getattr__` and `__setattr__` methods, which handle undefined attribute fetches and every attribute assignment.
- The `__getattribute__` method, which handles every attribute fetch.

You met some of these in chapters 30 and 32 of the book, and some only briefly. All four share goals, and you can often solve one problem with any of them. They differ in complexity and style, though, and you have to see them in action to judge. The first two apply to named attributes. The last two are general enough for proxy classes that route any attribute to a wrapped object.

The chapter is an advanced topic. Most application programmers never need it, because they simply fetch and set attributes. Tool builders, however, use these techniques to design flexible APIs. Understanding the descriptor model also makes slots and properties easier to read when you meet them in code.

## Properties

A property routes get, set and delete operations on one attribute to methods you write. That lets you run code on attribute access, reject deletions, and document an attribute. Properties are created with the `property` built-in and assigned to class attributes, just like method functions. Subclasses and instances inherit them as they inherit other class attributes.

### The basics of properties

You create a property by assigning the result of a built-in call to a class attribute:

```text
attribute = property(fget, fset, fdel, doc)
```

None of the four arguments is required, and each defaults to `None`. A `None` for `fget`, `fset` or `fdel` means that operation is not supported. Trying it raises an `AttributeError` automatically. The `fget` function returns the computed value, while `fset` and `fdel` return nothing. Any of the three can raise an exception to reject an access.

The `doc` argument sets a documentation string for the attribute. If you leave it out, the property copies the docstring from `fget`. Each function receives the instance as its first argument, so it can read and change that instance's data. You can pass any callable here, including a method.

### A first example with properties

The class in Example 38-1 uses a property to trace every access to an attribute named `name`. The real data is stored in `_name`, so it does not clash with the property name:

```python
class Person:
    def __init__(self, name):
        self._name = name
    def getName(self):
        print('fetch...')
        return self._name
    def setName(self, value):
        print('change...')
        self._name = value
    def delName(self):
        print('remove...')
        del self._name
    name = property(getName, setName, delName, 'name property docs')
sue = Person('Sue Jones') # sue has a managed attribute
print(sue.name) # Runs getName
sue.name = 'Susan Jones' # Runs setName
print(sue.name)
del sue.name # Runs delName
print('-'*20)
bob = Person('Bob Smith') # bob inherits property too
print(bob.name)
print(Person.name.__doc__) # Or help(Person.name)
```

This property does little more than trace access, but it shows the protocol. Both instances inherit the property, just as they would any other attribute on their class. Each access to `name` is caught and handled by the methods you provide. Running the script prints this:

```text
$ python3 prop-person.py
fetch...
Sue Jones
change...
fetch...
Susan Jones
remove...
--------------------
fetch...
Bob Smith
name property docs
```

Properties are inherited like any class attribute. If you move the property into a base class named `Super` and let `Person` subclass it, the output stays the same. The subclass gets the property through inheritance, and the instance gets it from the subclass. Because the methods receive `self`, they can use instance state and other methods at any depth of subclassing.

### Computed attributes with properties

Properties often do more than trace access. They can compute a value each time it is fetched. Example 38-2 shows a property that returns the square of a stored value:

```python
class PropSquare:
    def __init__(self, start):
        self.value = start
    def getX(self): # On attr fetch
        return self.value ** 2
    def setX(self, value): # On attr assign
        self.value = value
    X = property(getX, setX) # No delete or docs
P = PropSquare(3) # Two instances of class with property
Q = PropSquare(32) # Each has different state information
print(P.X) # 3 ** 2
P.X = 4
print(P.X) # 4 ** 2
print(Q.X) # 32 ** 2 (1024)
```

The attribute `X` looks like plain data, but each fetch runs code to compute the value. The instance stores the base value, and each fetch returns that value squared. Running the example prints `9`, `16` and `1024`.

Each instance keeps its own base value, because the property methods receive `self`. That means the fetch always squares the subject instance's own data.

### Coding properties with decorators

The `@property` decorator is a shorter way to create a property. A decorator rebinds the function name to the result of the decorator call, so `@property` is equivalent to the manual assignment. You can write the manual form first to see what happens:

```python
class Person:
    def name(self): ...
    name = property(name) # Manual equivalent to @property
```

Property objects also have `getter`, `setter` and `deleter` methods. Each one attaches a matching accessor and returns a copy of the property. You can use them to decorate normal methods for the set and delete operations. The getter and documentation usually fill in automatically when the property is created. Example 38-3 shows the decorator form:

```python
class Person:
    def __init__(self, name):
        self._name = name
    @property
    def name(self): # name = property(name)
        'name property docs'
        print('fetch...')
        return self._name
    @name.setter
    def name(self, value): # name = name.setter(name)
        print('change...')
        self._name = value
    @name.deleter
    def name(self): # name = name.deleter(name)
        print('remove...')
        del self._name
sue = Person('Sue Jones') # sue has a managed attribute
print(sue.name) # Runs name getter (def name 1)
sue.name = 'Susan Jones' # Runs name setter (def name 2)
print(sue.name)
del sue.name # Runs name deleter (def name 3)
print('-'*20)
bob = Person('Bob Smith') # bob inherits property too
print(bob.name)
print(Person.name.__doc__) # Or help(Person.name)
```

This code behaves exactly like Example 38-1, and its output matches. The decorator form adds only three lines. Whether you prefer it is mostly a matter of taste.

## Descriptors

A descriptor is a class that intercepts attribute access for one specific attribute. A property is actually a simple kind of descriptor. The `property` built-in creates a descriptor that calls functions on each access. Descriptors are also the mechanism behind properties and slots.

Descriptors can do more than properties. Because a descriptor is a normal class, it can keep its own state, take part in inheritance, use composition to hold other objects, and hold its own helper methods and documentation. Like a property, though, a descriptor still manages only one attribute.

### The basics of descriptors

You write a descriptor as a separate class. It defines special methods for the access types it handles: `__get__` for fetches, `__set__` for assignments and `__delete__` for deletions. You then assign an instance of that class to an attribute in another class:

```python
class Descriptor:
    "docstring goes here"
    def __get__(self, instance, owner): ... # Return attr value
    def __set__(self, instance, value): ... # Return nothing (None)
    def __delete__(self, instance): ... # Return nothing (None)
```

A class with any of these methods counts as a descriptor. When one of its instances is assigned to another class's attribute, Python calls the matching method on each access. If a method is missing, that kind of access is not supported.

The `__set__` method is worth a closer look. Leaving it out does not make an attribute read-only. Python lets an instance assign that name and store its own copy, which hides the descriptor. To make a descriptor attribute read-only, you define `__set__` and raise an exception inside it.

Descriptors with `__set__` are called data descriptors. They take precedence over names found through normal inheritance, so the descriptor always wins over an instance attribute with the same name. The built-in `__class__` attribute works this way. Chapter 40 of the book covers the full inheritance rules.

### Descriptor method arguments

All three descriptor methods receive the descriptor's own instance as `self`. They also receive the client instance that owns the attribute, named `instance` here. The `__get__` method gets one more argument, `owner`, which is the class that holds the descriptor.

The `instance` argument is `None` when you fetch the attribute through the class instead of an instance. That lets the descriptor return itself for class-level access. This REPL session shows the arguments Python passes:

```text
>>> class Descriptor:
...     def __get__(self, instance, owner):
...         print(self, instance, owner, sep='\n')
>>> class Subject:
...     attr = Descriptor() # Descriptor instance is class attr
>>> X = Subject()
>>> X.attr
<__main__.Descriptor object at 0x104bc9b20>
<__main__.Subject object at 0x104b8a570>
<class '__main__.Subject'>
>>> Subject.attr
<__main__.Descriptor object at 0x104bc9b20>
None
<class '__main__.Subject'>
```

When `X.attr` is fetched, Python acts as if it made this call. The `Subject.attr` lookup itself does not call `__get__` again:

```text
X.attr => Descriptor.__get__(Subject.attr, X, Subject)
```

The descriptor knows it is being accessed directly when its `instance` argument is `None`.

### Read-only descriptors

Omitting `__set__` is not enough to make a descriptor attribute read-only. The assignment still stores a value in the instance and hides the descriptor. This session shows the problem:

```text
>>> class D:
...     def __get__(*args): print('get')
>>> class C:
...     a = D() # Attribute "a" is a descriptor instance
>>> X = C()
>>> X.a # Runs inherited descriptor __get__
get
>>> C.a
get
>>> X.a = 99 # Stored on X, hiding C.a!
>>> X.a
99
>>> list(X.__dict__.keys())
['a']
>>> Y = C()
>>> Y.a # Y still inherits descriptor
get
>>> C.a
get
```

Instance assignment works this way for every attribute, and it lets an instance override a class default. To block it, define `__set__` and raise an exception. Python then sends the assignment to the descriptor instead of the instance:

```text
>>> class D:
...     def __get__(*args): print('get')
...     def __set__(*args): raise AttributeError('cannot set')
>>> class C:
...     a = D()
>>> X = C()
>>> X.a # Routed to C.a.__get__
get
>>> X.a = 99 # Routed to C.a.__set__
AttributeError: cannot set
```

> Note: Do not confuse the descriptor `__delete__` method with `__del__`. The `__delete__` method runs when someone deletes the managed attribute on an instance of the owner class. The `__del__` method is a general destructor that runs when any instance is about to be garbage-collected. `__delete__` is closer to the `__delattr__` method covered below.

### A first example with descriptors

Example 38-4 rebuilds the earlier `name` example with a descriptor. Its methods use the `instance` argument to reach the name stored on the client object:

```python
class Name:
    'name descriptor docs'
    def __get__(self, instance, owner):
        print('fetch...')
        return instance._name
    def __set__(self, instance, value):
        print('change...')
        instance._name = value
    def __delete__(self, instance):
        print('remove...')
        del instance._name
class Person:
    def __init__(self, name):
        self._name = name
    name = Name() # Assign descriptor to attr
sue = Person('Sue Jones') # sue has a managed attribute
print(sue.name) # Runs Name.__get__
sue.name = 'Susan Jones' # Runs Name.__set__
print(sue.name)
del sue.name # Runs Name.__delete__
print('-'*20)
bob = Person('Bob Smith') # bob inherits descriptor too
print(bob.name)
print(Name.__doc__) # Or help(Name)
```

The descriptor must be assigned to a class attribute. It does not work when assigned to an instance attribute with `self`. When `__get__` runs, Python passes three objects. The `self` is the `Name` instance. The `instance` is the `Person` object, and `owner` is the `Person` class.

The output matches the property version exactly. Like the property, the descriptor is inherited by subclasses, and you can move it into a base class without changes. If the descriptor is useful only inside one class, you can nest it inside that class. The nested version works the same, but the docstring lives at a new path:

```python
class Person:
    def __init__(self, name):
        self._name = name
    class Name: # Using a nested class
        'name descriptor docs'
        def __get__(self, instance, owner):
            ...same...
        def __set__(self, instance, value):
            ...same...
        def __delete__(self, instance):
            ...same...
    name = Name()
```

Nesting moves `Name` into the scope of `Person`, so it cannot clash with names outside the class. The test script must fetch the docstring with `print(Person.Name.__doc__)` instead of `print(Name.__doc__)`.

### Computed attributes with descriptors

Descriptors can compute values too. Example 38-5 reworks the squaring example with a descriptor. Each descriptor keeps its own base value:

```python
class DescSquare:
    def __init__(self, start): # Each desc has own state
        self.value = start
    def __get__(self, instance, owner): # On attr fetch
        return self.value ** 2
    def __set__(self, instance, value): # On attr assign
        self.value = value # No delete or docs
class Client1:
    X = DescSquare(3) # Assign descriptor instance to class attr
class Client2:
    X = DescSquare(32) # Another instance in another client class
# Could also code two instances in same class
c1 = Client1()
c2 = Client2()
print(c1.X) # 3 ** 2
c1.X = 4
print(c1.X) # 4 ** 2
print(c2.X) # 32 ** 2 (1024)
```

The output matches the property version: `9`, `16` and `1024`. This time a descriptor object intercepts each access instead of a property.

### Using state in descriptors

The first two descriptor examples keep their data in different places. The name example stores data on the client instance. The squaring example stores data on the descriptor itself, in `self`. A descriptor can use either place, or both.

Descriptor state is per-descriptor data. It can be internal to the descriptor, or it can span all instances. It can vary per attribute appearance, and it is often different for each client class. Instance state is per-client-object data, so it varies from one application object to the next.

Choose carefully. Storing employee names in descriptor state would make every client instance share one copy. Storing descriptor internals in each instance would create many copies that vary. Descriptor state can also avoid name clashes, because the descriptor does not add anything to the instance namespace. Example 38-6 shows a descriptor that keeps its data on itself:

```python
class DescState: # Use descriptor state
    def __init__(self, value):
        self.value = value
    def __get__(self, instance, owner): # On attr fetch
        print('DescState get')
        return self.value * 10
    def __set__(self, instance, value): # On attr assign
        print('DescState set')
        self.value = value
# Client class
class CalcAttrs:
    X = DescState(2) # Descriptor class attr
    Y = 3 # Class attr
    def __init__(self):
        self.Z = 4 # Instance attr
obj = CalcAttrs()
print(obj.X, obj.Y, obj.Z) # X is computed, others are not
obj.X = 5 # X assignment is intercepted
CalcAttrs.Y = 6 # Y reassigned in class
obj.Z = 7 # Z assigned in instance
print(obj.X, obj.Y, obj.Z)
obj2 = CalcAttrs() # But X uses shared data, like Y!
print(obj2.X, obj2.Y, obj2.Z)
```

Only `X` is managed here. Reads and writes to `X` are intercepted, but `Y` and `Z` are not. Because `X` keeps its value on the descriptor, every client instance sees the same value:

```text
$ python3 desc-state-desc.py
DescState get
20 3 4
DescState set
DescState get
50 6 7
DescState get
50 6 4
```

A descriptor can also store data on the client instance. That allows a value that varies per instance. Example 38-7 assumes the client sets an `_X` attribute on each instance, and the descriptor reads it:

```python
class InstState: # Using instance state
    def __get__(self, instance, owner):
        print('InstState get') # Assume set by client class
        return instance._X * 10
    def __set__(self, instance, value):
        print('InstState set')
        instance._X = value
# Client class
class CalcAttrs:
    X = InstState() # Descriptor class attr
    Y = 3 # Class attr
    def __init__(self):
        self._X = 2 # Instance attr
        self.Z = 4 # Instance attr
obj = CalcAttrs()
print(obj.X, obj.Y, obj.Z) # X is computed, others are not
obj.X = 5 # X assignment is intercepted
CalcAttrs.Y = 6 # Y reassigned in class
obj.Z = 7 # Z assigned in instance
print(obj.X, obj.Y, obj.Z)
obj2 = CalcAttrs() # But X differs now, like Z!
print(obj2.X, obj2.Y, obj2.Z)
```

The name `_X` avoids a clash with the descriptor's own name. This time each instance keeps its own value:

```text
$ python3 desc-state-inst.py
InstState get
20 3 4
InstState set
InstState get
50 6 7
InstState get
20 6 4
```

Both kinds of state have a role. Descriptors can keep data internal to themselves without adding it to the client's namespace, and that is a clear advantage over properties. This small class uses both sources. Its `self.data` belongs to the attribute, and `instance.data` varies per client:

```text
>>> class DescBoth:
...     def __init__(self, data):
...         self.data = data
...     def __get__(self, instance, owner):
...         return f'{self.data}, {instance.data}'
...     def __set__(self, instance, value):
...         instance.data = value
>>> class Client:
...     def __init__(self, data):
...         self.data = data
...     managed = DescBoth('hack')
>>> I = Client('code')
>>> I.managed # Show both data sources
'hack, code'
>>> I.managed = 'HACK' # Change instance data
>>> I.managed
'hack, HACK'
```

Properties and descriptors are virtual attributes. They do not appear in the instance's namespace dictionary, yet you can reach them with `getattr`. They do appear in `dir` results, because they live on the class. Whether to read them this way depends on the program, since they may run real computation:

```text
>>> I.__dict__
{'data': 'HACK'}
>>> [x for x in dir(I) if not x.startswith('__')]
['data', 'managed']
>>> getattr(I, 'data')
'HACK'
>>> getattr(I, 'managed')
'hack, HACK'
>>> for attr in (x for x in dir(I) if not x.startswith('__')):
...     print(f'{attr} => {getattr(I, attr)}')
data => HACK
managed => hack, HACK
```

The generic `__getattr__` and `__getattribute__` methods do not have class-level names, so their virtual attributes do not show up in `dir` results. A class can provide a `__dir__` method to fix that, but it is optional and uncommon.

### How properties and descriptors relate

The `property` built-in is a convenient way to create a descriptor. Once you know both tools, you can write a property with a descriptor class. Example 38-8 does that:

```python
class Property:
    def __init__(self, fget=None, fset=None, fdel=None, doc=None):
        self.fget = fget
        self.fset = fset
        self.fdel = fdel # Save unbound methods
        self.__doc__ = doc # or other callables
    def __get__(self, instance, instancetype=None):
        if instance is None:
            return self
        if self.fget is None:
            raise AttributeError("can't get attribute")
        return self.fget(instance) # Pass instance to self
    # in property accessors
    def __set__(self, instance, value):
        if self.fset is None:
            raise AttributeError("can't set attribute")
        self.fset(instance, value)
    def __delete__(self, instance):
        if self.fdel is None:
            raise AttributeError("can't delete attribute")
        self.fdel(instance)
class Person:
    def getName(self):
        print('getName...')
    def setName(self, value):
        print('setName...')
    name = Property(getName, setName) # Use like property()
x = Person()
x.name
x.name = 'Pat'
del x.name
```

This `Property` class routes accesses through the descriptor protocol. It sends them to the methods saved in its state when the class instance is created. The fetch goes from `Person` to `Property.__get__` and then back to `getName`. Running it prints this:

```text
$ python3 prop-desc-equiv.py
getName...
setName...
AttributeError: can't delete attribute
```

This class handles only basic property use. To support `@` decorator syntax for setters and deleters, you would add `setter` and `deleter` methods that save the decorated function and return the property. The built-in `property` already does this, so the book skips that extension.

### Descriptors, slots and other tools

Descriptors also power Python's `__slots__` feature. Instance dictionaries are avoided by creating class-level descriptors. Those descriptors map slot names to fixed storage in the instance. Unlike the explicit `property` call, slot descriptors are created automatically when a `__slots__` attribute appears in the class.

Chapter 32 of the book explains slots, and it explains why they are rarely worth using outside unusual cases. Descriptors also serve other class tools, but the internals are beyond this chapter. Python's manuals and open source code cover them.

## The `__getattr__` and `__getattribute__` methods

The `__getattr__` and `__getattribute__` methods are operator-overloading methods, so they intercept attribute fetches in a more general way. They run automatically when an instance is used in an attribute fetch. Unlike properties and descriptors, they can catch any name. That makes them more flexible, but it can also add extra calls.

Attribute fetch interception comes in two forms. The `__getattr__` method runs only for attributes that are undefined. That means the attribute is not stored on the instance or inherited from its classes. The `__getattribute__` method runs for every attribute. Because it catches everything, it must be used carefully to avoid loops.

These two methods belong to a larger set. Python also has `__setattr__` for every assignment and `__delattr__` for every deletion. The four work together, so this chapter treats them as one topic. You met `__getattr__` and `__setattr__` in chapters 30 and 32 of the book, and `__getattribute__` only briefly.

### The basics of these methods

If a class defines or inherits one of these four methods, Python runs it when an instance takes part in the matching operation:

```python
def __getattr__(self, name): ... # On undefined attribute fetch [obj.name]
def __getattribute__(self, name): ... # On all attribute fetch [obj.name]
def __setattr__(self, name, value): ... # On all attribute assignment [obj.name=value]
def __delattr__(self, name): ... # On all attribute deletion [del obj.name]
```

Here `self` is the instance, `name` is the attribute name as a string, and `value` is the object being assigned. The two fetch methods return a value. The other two return nothing. Each one can raise an exception to block an access.

Using `__getattr__` for fetches and `__setattr__` for assignments catches every access in a small class like this one:

```python
class Catcher:
    def __getattr__(self, name):
        print('Get:', name)
    def __setattr__(self, name, value):
        print('Set:', name, value)
X = Catcher()
X.job # Prints "Get: job"
X.pay # Prints "Get: pay"
X.pay = 'bread' # Prints "Set: pay bread"
```

The `__getattribute__` method works the same here, but it can loop in general, as the next section explains:

```python
class Catcher: # On all attribute fetches
    def __getattribute__(self, name): # Works same as getattr here
        print('Get:', name) # But prone to loops in general
    ...rest unchanged...
```

This structure can implement the delegation pattern from chapter 31 of the book. Because every attribute reaches the interception method, you can validate each one and pass it to an embedded object. This wrapper, a proxy class, traces each fetch made to the object it wraps:

```python
class Wrapper:
    def __init__(self, object):
        self.wrapped = object # Save object
    def __getattr__(self, attrname):
        print('Trace:', attrname) # Trace fetch
        return getattr(self.wrapped, attrname) # Delegate fetch
X = Wrapper([1, 2, 3])
X.append(4) # Prints "Trace: append"
print(X.wrapped) # Prints "[1, 2, 3, 4]"
```

Properties and descriptors have no equivalent for this. You would need an accessor for every attribute of every wrapped object. The generic methods can add calls on assignments, though. The case study at the end of this section shows that trade-off.

### Avoiding loops in these methods

These methods are straightforward, but they can recurse. The main risk is a fetch inside a method that calls the same method again. Because `__getattr__` runs only for undefined attributes, it can fetch other attributes without trouble. The `__getattribute__` and `__setattr__` methods run for every attribute, so their code must be careful.

In a `__getattribute__` method, a fetch like the one below calls `__getattribute__` again. The loop continues until memory runs out:

```python
def __getattribute__(self, name):
    x = self.other # LOOPS!
```

Any `self` attribute reference in the class triggers `__getattribute__`, not only the ones inside it. That is usually the goal, since the method exists to see every fetch. Inside the method itself, though, it almost always loops. To avoid it, send the fetch to a higher superclass. The `object` class is a superclass of every class, so it works well:

```python
def __getattribute__(self, name):
    x = object.__getattribute__(self, 'other') # Force higher to avoid me
```

The same trap exists in `__setattr__`. Any assignment inside the method calls `__setattr__` again:

```python
def __setattr__(self, name, value):
    self.other = value # Recurs (and might LOOP!)
```

You can avoid this by writing into the instance's `__dict__` directly, which skips the assignment hook:

```python
def __setattr__(self, name, value):
    self.__dict__['other'] = value # Use attr dict to avoid me
```

You can also send assignments to a superclass. This works well when the wrapped class uses slots, properties or other virtual attributes that live on the class instead of the instance:

```python
def __setattr__(self, name, value):
    object.__setattr__(self, 'other', value) # Force higher to avoid me
```

The `__dict__` trick does not help in `__getattribute__`. Fetching `__dict__` is itself an attribute fetch, so the method calls itself again and fails quickly:

```python
def __getattribute__(self, name):
    x = self.__dict__['other'] # Loops!
```

The `__delattr__` method is less common, but it runs for every deletion, just as `__setattr__` runs for every assignment. Avoid loops there with the same tools: the `__dict__` or a superclass call.

### A first example with generic methods

The generic methods do not need much code. Example 38-9 repeats the `name` example using these methods. Because they catch so much, the code checks the name to know when to manage an attribute. Other names pass through normally:

```python
class Person:
    def __init__(self, name): # On [Person()]
        self._name = name # Triggers __setattr__!
    def __getattr__(self, attr): # On [obj.undefined]
        print('get: ' + attr)
        if attr == 'name': # Intercept name: not stored
            return self._name # Does not loop: real attr
        else: # Others are errors
            raise AttributeError(attr)
    def __setattr__(self, attr, value): # On [obj.any = value]
        print('set: ' + attr)
        if attr == 'name':
            attr = '_name' # Set internal name
        self.__dict__[attr] = value # Avoid looping here
    def __delattr__(self, attr): # On [del obj.any]
        print('del: ' + attr)
        if attr == 'name':
            attr = '_name' # Avoid looping here too
        del self.__dict__[attr] # but much less common
sue = Person('Sue Jones') # sue has a managed attribute
print(sue.name) # Runs __getattr__
sue.name = 'Susan Jones' # Runs __setattr__
print(sue.name)
del sue.name # Runs __delattr__
print('-'*20)
bob = Person('Bob Smith') # bob's attrs work like sue's
print(bob.name)
#print(Person.name.__doc__) # No direct equivalent here!
```

Running it prints the same results, along with a trace of each generic call:

```text
$ python3 getattr-person.py
set: _name
get: name
Sue Jones
set: name
get: name
Susan Jones
del: name
--------------------
set: _name
get: name
Bob Smith
```

The assignment in `__init__` also triggers `__setattr__`. That method sees every instance assignment, including the `_name` attribute. These methods also cannot hold documentation. A managed attribute here is just code inside the methods, not a separate object.

Using `__getattribute__` gives the same result. Replace `__getattr__` in Example 38-9 with this method, which must route all other names to the superclass:

```python
# Replace just __getattr__ with this
def __getattribute__(self, attr): # On [obj.any]
    print('get: ' + attr)
    if attr == 'name': # Intercept all names
        attr = '_name' # Map to internal name
    return object.__getattribute__(self, attr) # Avoid looping here
```

The output has an extra `get: __dict__` call for each assignment. The `__setattr__` method fetches `__dict__`, and that fetch goes through `__getattribute__` too:

```text
$ python3 getattribute-person.py
set: _name
get: __dict__
get: name
Sue Jones
set: name
get: __dict__
get: name
Susan Jones
del: name
get: __dict__
--------------------
set: _name
get: __dict__
get: name
Bob Smith
```

This version is artificial for such a small case. The generic methods shine in delegation code, where each access is validated and routed to a wrapped object. For a single managed attribute, a property or descriptor may do as well and add no extra calls for unmanaged attributes.

### Computed attributes with generic methods

These methods can compute a value just as properties and descriptors do. Example 38-11 creates a virtual attribute `X` that is calculated on each fetch:

```python
class AttrSquare:
    def __init__(self, start):
        self.value = start # Triggers __setattr__!
    def __getattr__(self, attr): # On undefined attr fetch
        if attr == 'X':
            return self.value ** 2 # value is not undefined
        else:
            raise AttributeError(attr)
    def __setattr__(self, attr, value): # On all attr assignments
        if attr == 'X':
            attr = 'value'
        self.__dict__[attr] = value
A = AttrSquare(3) # 2 instances of class with overloading
B = AttrSquare(32) # Each has different state information
print(A.X) # 3 ** 2
A.X = 4
print(A.X) # 4 ** 2
print(B.X) # 32 ** 2 (1024)
```

The output matches the property and descriptor versions. The mechanics, however, come from generic interception:

```text
$ python3 getattr-computed.py
9
16
1024
```

Example 38-12 makes the same change with `__getattribute__`. It replaces the fetch method and changes assignments to call `object` methods rather than `__dict__` keys:

```python
class AttrSquare:
    def __init__(self, start):
        self.value = start # Triggers __setattr__!
    def __getattribute__(self, attr): # On all attr fetches
        if attr == 'X':
            return self.value ** 2 # Triggers __getattribute__ again!
        else:
            return object.__getattribute__(self, attr)
    def __setattr__(self, attr, value): # On all attr assignments
        if attr == 'X':
            attr = 'value'
        object.__setattr__(self, attr, value)
    ...self-test code same as Example 38-11...
```

The results are the same. Two things happen inside this class, though. The constructor's `self.value = start` triggers `__setattr__`. Also, `self.value` inside `__getattribute__` triggers `__getattribute__` again. That means each fetch of `X` runs the method twice. The `__getattr__` version avoids this because `value` is defined and skips the method.

To avoid the second call, fetch `value` through the superclass as well:

```python
def __getattribute__(self, attr):
    if attr == 'X':
        return object.__getattribute__(self, 'value') ** 2
```

This still calls a superclass method, but it does not start an extra recursive call. If the flow is hard to follow, add `print` calls to each method and trace the order.

### Comparing `__getattr__` and `__getattribute__`

Example 38-13 shows the coding difference between the two methods. Both implement three attributes. `attr1` is a class attribute, `attr2` is an instance attribute, and `attr3` is a virtual attribute computed on fetch:

```python
class GetAttr:
    attr1 = 1
    def __init__(self):
        self.attr2 = 2
    def __getattr__(self, attr): # On undefined attrs only
        print('get:', attr) # Not on attr1: inherited from class
        if attr == 'attr3': # Not on attr2: stored on instance
            return 3
        else:
            raise AttributeError(attr)
X = GetAttr()
print(X.attr1)
print(X.attr2)
print(X.attr3)
print('-'*20)
class GetAttribute:
    attr1 = 1
    def __init__(self):
        self.attr2 = 2
    def __getattribute__(self, attr): # On all attr fetches
        print('get:', attr) # Use superclass to avoid looping here
        if attr == 'attr3':
            return 3
        else:
            return object.__getattribute__(self, attr)
X = GetAttribute()
print(X.attr1)
print(X.attr2)
print(X.attr3)
```

The `__getattr__` version intercepts only `attr3`, since the others are defined. The `__getattribute__` version intercepts every fetch. It must send the ones it does not manage to the superclass to avoid loops:

```text
$ python3 getattr-v-getattribute.py
1
2
get: attr3
3
--------------------
get: attr1
1
get: attr2
2
get: attr3
3
```

The two methods can catch different sets of fetches. In practice, though, they often do the same job. If an attribute is not physically stored, both produce the same result.

### Management techniques compared

A computed attribute makes a useful comparison across all four techniques. Example 38-14 uses properties for `square` and `cube`. The base values begin with an underscore, so they do not clash with the property names:

```python
"Two dynamically computed attributes with properties"
class Powers:
    def __init__(self, square, cube):
        self._square = square # _square is the base value
        self._cube = cube # square is the property name
    def getSquare(self):
        return self._square ** 2
    def setSquare(self, value):
        self._square = value
    square = property(getSquare, setSquare) # Or @property decorator
    def getCube(self):
        return self._cube ** 3
    cube = property(getCube) # Likewise
```

Example 38-15 does the same with descriptors. Each descriptor is a full class. These descriptors keep base values in instance state, so they need leading underscores too. The book notes that storing base values in descriptor state would avoid the rename. That would not suit values that must vary per client instance:

```python
"Same, but with descriptors (per-instance state)"
class DescSquare:
    def __get__(self, instance, owner):
        return instance._square ** 2
    def __set__(self, instance, value):
        instance._square = value
class DescCube:
    def __get__(self, instance, owner):
        return instance._cube ** 3
class Powers:
    square = DescSquare()
    cube = DescCube()
    def __init__(self, square, cube):
        self._square = square # "self.square = square" works too,
        self._cube = cube # because it triggers desc __set__!
```

Example 38-16 uses `__getattr__`. Base values keep underscore names, so accesses to the managed names are undefined and reach the method. It also needs `__setattr__` to intercept assignments, and it must avoid looping there:

```python
"Same, but with generic __getattr__ undefined-attribute interception"
class Powers:
    def __init__(self, square, cube):
        self._square = square
        self._cube = cube
    def __getattr__(self, name):
        if name == 'square':
            return self._square ** 2
        elif name == 'cube':
            return self._cube ** 3
        else:
            raise TypeError('unknown attr:' + name)
    def __setattr__(self, name, value):
        if name == 'square':
            self.__dict__['_square'] = value # Or use object
        else:
            self.__dict__[name] = value
```

Example 38-17 uses `__getattribute__`. It catches every fetch, so it must route base-value fetches to a superclass. Fetching `self._square` directly also works, but it adds a second `__getattribute__` call:

```python
"Same, but with generic __getattribute__ all-attribute interception"
class Powers:
    def __init__(self, square, cube):
        self._square = square
        self._cube = cube
    def __getattribute__(self, name):
        if name == 'square':
            return object.__getattribute__(self, '_square') ** 2
        elif name == 'cube':
            return object.__getattribute__(self, '_cube') ** 3
        else:
            return object.__getattribute__(self, name)
    def __setattr__(self, name, value):
        if name == 'square':
            object.__setattr__(self, '_square', value) # Or use __dict__
        else:
            object.__setattr__(self, name , value)
```

All four modules produce the same result. This REPL session imports each module by name, then tests its attributes:

```text
>>> from importlib import import_module
>>> mods = [f'all_four_{M}' for M in ('props', 'desc', 'getattr', 'getattribute')]
>>> for modname in mods:
...     module = import_module(modname) # Import by name string
...     X = module.Powers(3, 4) # This module's class (print to see)
...     print(X.square) # 3 ** 2 = 9
...     print(X.cube) # 4 ** 3 = 64
...     X.square = 5
...     print(X.square) # 5 ** 2 = 25
9
64
25
...repeated four times...
```

### Intercepting built-in operation attributes

The generic methods have a limit that matters for delegation. Attribute fetches for implicit operator-overloading methods never reach `__getattr__` or `__getattribute__`. Printing, `+` and indexing look up methods such as `__str__`, `__add__` and `__getitem__` in the class. They skip the instance and its interceptors.

Explicit fetches differ. `X.__add__` does reach the interceptors, but `X + Y` does not. A wrapper that wants to delegate built-in operations must define those methods itself. That is more work when the wrapped object has many operators, but it is workable. Adding them manually, with tools, or through a shared superclass all work.

Example 38-18 runs the same tests against both classes. It checks an ordinary attribute, a missing attribute and each built-in operation:

```python
class GetAttr:
    cattr = 88 # Attrs stored on class and instance
    def __init__(self): # These skip getattr, but not getattribute
        self.iattr = 77
    def __len__(self): # Redefine for len(): doesn't run getattr
        print('__len__: 66')
        return 66
    def __getattr__(self, attr): # Provide __str__ if asked, else dummy func
        print('getattr:', attr) # Never run for __str__: inherited from object
        if attr == '__str__':
            return lambda *args: '[Getattr str]'
        else:
            return lambda *args: None
class GetAttribute:
    cattr = 88 # Similar, but catch all attributes
    def __init__(self): # Except implicit fetches for built-in ops
        self.iattr = 77
    def __len__(self): # Redefine for len(): doesn't run getattribute
        print('__len__: 66') # But explicit fetches of inherited __str__ do
        return 66
    def __getattribute__(self, attr):
        print('getattribute:', attr)
        if attr == '__str__':
            return lambda *args: '[GetAttribute str]'
        else:
            return lambda *args: None
for Class in GetAttr, GetAttribute:
    print('\n' + Class.__name__.ljust(50, '='))
    X = Class()
    # Defined attributes trigger getattribute but not getattr
    X.cattr # Class attr (defined – skips getattr)
    X.iattr # Instance attr (defined – skips getattr)
    X.other # Missing attr
    len(X) # __len__ defined explicitly: moot
    # Built-in ops do not invoke either getattr or getattribute
    # No defaults are inherited for these from object superclass
    try: X[0] # Tries to invoke __getitem__
    except: print('fail []')
    try: X + 99 # Ditto, __add__
    except: print('fail +')
    try: X() # Ditto, __call__
    except: print('fail ()')
    # But explicit calls invoke both catchers
    X.__getitem__(0)
    X.__add__(99)
    X.__call__()
    # The implied object superclass defines a __str__ that precludes getattr
    # But the absolute getattribute is not called for implicit fetches either
    print(X.__str__()) # __str__: explicit call => only __getattr__ skipped
    print(X) # __str__: implicit via built-in => both skipped
```

The output shows the difference. Neither method runs for the operators, though explicit calls to the same names reach both:

```text
$ python3 getattr-builtins.py
GetAttr===========================================
getattr: other
__len__: 66
fail []
fail +
fail ()
getattr: __getitem__
getattr: __add__
getattr: __call__
<__main__.GetAttr object at 0x10f76f020>
<__main__.GetAttr object at 0x10f76f020>
GetAttribute======================================
getattribute: cattr
getattribute: iattr
getattribute: other
__len__: 66
fail []
fail +
fail ()
getattribute: __getitem__
getattribute: __add__
getattribute: __call__
getattribute: __str__
[GetAttribute str]
<__main__.GetAttribute object at 0x10f74c440>
```

Several points stand out. The `__getattr__` method never sees `__str__`, because `object` supplies a default for it. The `__getattribute__` method catches `__str__` only in the explicit call, since printing skips it. The `__call__` and `__add__` methods are caught by both schemes when fetched explicitly, but built-in operations bypass them. The `__len__` method works because the class defines it, and `len` finds it there.

This affects delegation. A wrapper class that passes printing requests to the wrapped object has to define `__repr__`. The `object` class supplies a default `__repr__`, and built-in operations skip the generic methods, so the wrapper needs its own. Chapter 39 of the book shows fixes for delegating built-ins.

### Attribute validation case study

The closing example is a `CardHolder` class with four attributes. Three of them are managed, and each one validates or transforms its value. The `remain` attribute is read-only and computed on demand. All four versions produce the same output for the same tests, but each uses a different technique. The case is mainly for self-study, though it uses every idea from this section.

#### Validating with properties

Example 38-19 uses properties for three attributes. The attributes `name`, `age` and `acct` are managed, `addr` is a plain attribute, and `remain` is virtual. Properties are a good fit when code already uses attributes, since they add checks without changing callers.

Inside `__init__`, the attribute assignments trigger the property setters too. When the constructor assigns `self.name`, the `setName` method transforms the value and stores it in `__name`. The double underscore is a name-mangling convention that keeps the stored value separate from the property. Properties have no state of their own, so the stored data must live under another name. This class has 39 lines, counting blank lines:

```python
class CardHolder:
    acctlen = 8 # Class data
    retireage = 62.5
    def __init__(self, acct, name, age, addr):
        self.acct = acct # Instance data
        self.name = name # These trigger prop setters too!
        self.age = age # __X mangled to have class name
        self.addr = addr # addr is not managed
        # remain has no data
    def getName(self):
        return self.__name
    def setName(self, value):
        value = value.lower().replace(' ', '_')
        self.__name = value
    name = property(getName, setName) # Or @ decorators for both
    def getAge(self):
        return self.__age
    def setAge(self, value):
        if value < 0 or value > 150:
            raise ValueError('invalid age')
        else:
            self.__age = value
    age = property(getAge, setAge)
    def getAcct(self):
        return self.__acct[:-3] + '***'
    def setAcct(self, value):
        value = value.replace('-', '')
        if len(value) != self.acctlen:
            raise TypeError('invalid acct number')
        else:
            self.__acct = value
    acct = property(getAcct, setAcct)
    def remainGet(self): # Could be a method, not attr
        return self.retireage - self.age # Unless already using as attr
    remain = property(remainGet)
```

The tester in Example 38-20 takes the module name as a command-line argument. It loads the class, creates two instances, and reads and changes their attributes. Operations expected to fail sit inside `try` statements. The same tester runs against all four versions:

```python
def loadclass():
    import sys, importlib
    modulename = sys.argv[1] # Module name in command line
    module = importlib.import_module(modulename) # Import module by name string
    print(f'[Using: {module.CardHolder}]') # No need for getattr() here
    return module.CardHolder
def printholder(who):
    print(who.acct, who.name, who.age, who.remain, who.addr, sep=' / ')
if __name__ == '__main__':
    CardHolder = loadclass()
    bob = CardHolder('1234-5678', 'Bob Smith', 40, '123 main st')
    printholder(bob)
    bob.name = 'Bob Q. Smith'
    bob.age = 50
    bob.acct = '23-45-67-89'
    printholder(bob)
    sue = CardHolder('5678-12-34', 'Sue Jones', 35, '124 main st')
    printholder(sue)
    try:
        sue.age = 200
    except: print('Bad age for Sue')
    try:
        sue.remain = 5
    except: print("Can't set sue.remain")
    try:
        sue.acct = '1234567'
    except: print('Bad acct for Sue')
```

The output shows the managed values. Account numbers are partly hidden, names are standardized, and `remain` is computed when fetched:

```text
$ python3 validate_tester.py validate_properties
[Using: <class 'validate_properties.CardHolder'>]
12345*** / bob_smith / 40 / 22.5 / 123 main st
23456*** / bob_q._smith / 50 / 12.5 / 123 main st
56781*** / sue_jones / 35 / 27.5 / 124 main st
Bad age for Sue
Can't set sue.remain
Bad acct for Sue
```

#### Validating with descriptors

The descriptor version manages the same attributes with classes. Properties are a focused form of descriptor, but descriptors can keep their own state. That flexibility can also cause trouble, as the next two versions show.

In the first version, the constructor's assignments trigger each descriptor's `__set__`. Assigning `self.name` invokes `Name.__set__`, which transforms the value and stores it in the descriptor. The `remain` descriptor must reject assignments. Without that check, assigning `remain` on an instance would quietly create an instance attribute that hides the descriptor. This version has 45 lines of code:

```python
class CardHolder: # Using shared descriptor state
    acctlen = 8 # Class data
    retireage = 62.5
    def __init__(self, acct, name, age, addr):
        self.acct = acct # Instance data
        self.name = name # These trigger __set__ calls too!
        self.age = age # __X not needed: in descriptor
        self.addr = addr # addr is not managed
        # remain has no data
    class Name:
        def __get__(self, instance, owner): # Class names: CardHolder locals
            return self.name
        def __set__(self, instance, value):
            value = value.lower().replace(' ', '_')
            self.name = value
    name = Name()
    class Age:
        def __get__(self, instance, owner):
            return self.age # Use descriptor data
        def __set__(self, instance, value):
            if value < 0 or value > 150:
                raise ValueError('invalid age')
            else:
                self.age = value
    age = Age()
    class Acct:
        def __get__(self, instance, owner):
            return self.acct[:-3] + '***'
        def __set__(self, instance, value):
            value = value.replace('-', '')
            if len(value) != instance.acctlen: # Use instance class data
                raise TypeError('invalid acct number')
            else:
                self.acct = value
    acct = Acct()
    class Remain:
        def __get__(self, instance, owner):
            return instance.retireage - instance.age # Triggers Age.__get__
        def __set__(self, instance, value):
            raise TypeError('cannot set remain') # Else set allowed here
    remain = Remain()
```

When you run this version with the same tester, the output matches the property version, except for the class name in the first line:

```text
$ python3 validate_tester.py validate_descriptors1
[Using: <class 'validate_descriptors1.CardHolder'>]
…rest is same output as properties…
```

The second version fixes a real problem. In the first version, every instance shares one descriptor, so the stored values are shared too. Descriptor state is class-level data, and it cannot vary between instances. Example 38-22 shows the damage with two objects:

```python
from validate_tester import loadclass
CardHolder = loadclass()
bob = CardHolder('1234-5678', 'Bob Smith', 40, '123 main st')
print('bob:', bob.name, bob.acct, bob.age, bob.addr)
sue = CardHolder('5678-12-34', 'Sue Jones', 35, '124 main st')
print('sue:', sue.name, sue.acct, sue.age, sue.addr) # addr differs: client data
print('bob:', bob.name, bob.acct, bob.age, bob.addr) # name,acct,age overwritten?
```

Here `bob` changes into `sue` for every managed attribute, because the two instances share one descriptor:

```text
$ python3 validate_tester_plus.py validate_descriptors1
[Using: <class 'validate_descriptors1.CardHolder'>]
bob: bob_smith 12345*** 40 123 main st
sue: sue_jones 56781*** 35 124 main st
bob: sue_jones 56781*** 35 123 main st
```

Properties do not have this problem, since they hold no state. Descriptor state does have valid uses, such as data that spans all instances. This example used it on purpose to show the effect. In this case, though, the values belong to each client object. The fix is to store them on the instance, using the same `__X` naming as the property version.

Example 38-23 makes that change. The line count stays at 45:

```python
class CardHolder: # Using per-client-instance state
    acctlen = 8 # Class data
    retireage = 62.5
    def __init__(self, acct, name, age, addr):
        self.acct = acct # Client instance data
        self.name = name # These trigger __set__ calls too!
        self.age = age # __X needed: in client instance
        self.addr = addr # addr is not managed
        # remain managed but has no data
    class Name:
        def __get__(self, instance, owner): # Class names: CardHolder locals
            return instance.__name
        def __set__(self, instance, value):
            value = value.lower().replace(' ', '_')
            instance.__name = value
    name = Name() # class.name vs mangled attr
    class Age:
        def __get__(self, instance, owner):
            return instance.__age # Use *instance* data
        def __set__(self, instance, value):
            if value < 0 or value > 150:
                raise ValueError('invalid age')
            else:
                instance.__age = value
    age = Age() # class.age vs mangled attr
    class Acct:
        def __get__(self, instance, owner):
            return instance.__acct[:-3] + '***'
        def __set__(self, instance, value):
            value = value.replace('-', '')
            if len(value) != instance.acctlen: # Use instance class data
                raise TypeError('invalid acct number')
            else:
                instance.__acct = value
    acct = Acct() # class.acct vs mangled name
    class Remain:
        def __get__(self, instance, owner):
            return instance.retireage - instance.age # Triggers Age.__get__
        def __set__(self, instance, value):
            raise TypeError('cannot set remain') # Else set allowed here
    remain = Remain()
```

Now each object keeps its own values, and `bob` stays `bob`:

```text
$ python3 validate_tester_plus.py validate_descriptors2
[Using: <class 'validate_descriptors2.CardHolder'>]
bob: bob_smith 12345*** 40 123 main st
sue: sue_jones 56781*** 35 124 main st
bob: bob_smith 12345*** 40 123 main st
$ python3 validate_tester.py validate_descriptors2
…same output as properties, except class name…
```

This version has one limit. It does not support fetches through the class, because the `instance` argument is `None` there. The mangled name in the error shows the problem:

```text
>>> from validate_descriptors1 import CardHolder
>>> pat = CardHolder('1234-5678', 'Pat Smith', 40, '123 main st')
>>> pat.name
'pat_smith'
>>> CardHolder.name
'pat_smith'
>>> from validate_descriptors2 import CardHolder
>>> pat = CardHolder('1234-5678', 'Pat Smith', 40, '123 main st')
>>> pat.name
'pat_smith'
>>> CardHolder.name
AttributeError: 'NoneType' object has no attribute '_Name__name'
```

You could add code to raise a clearer error. The book suggests it is not worth it. This version keeps data on the client, so the descriptors need a client instance to mean anything, like an ordinary instance method. Choose state policies carefully, since they change how a descriptor behaves.

#### Validating with `__getattr__`

The `__getattr__` version checks the name in each undefined fetch. Attributes stored on the instance never reach the method. This approach is more general than properties or descriptors, but it needs extra work to act like them. The code must check names at runtime, which is a good job for a `match` statement. It also needs a `__setattr__` to validate assignments.

Example 38-24 uses this approach. The constructor's assignments trigger `__setattr__`. Storing `name` on the instance means later fetches skip `__getattr__`. The `acct` value is stored as `_acct`, so fetches of `acct` do reach the method:

```python
class CardHolder:
    acctlen = 8 # Class data
    retireage = 62.5
    def __init__(self, acct, name, age, addr):
        self.acct = acct # Instance data
        self.name = name # These trigger __setattr__ too
        self.age = age # _acct not mangled: name tested
        self.addr = addr # addr is not managed
        # remain has no data
    def __getattr__(self, name):
        match name:
            case 'acct': # On undefined attr fetches
                return self._acct[:-3] + '***' # name, age, addr are defined
            case 'remain':
                return self.retireage - self.age # Doesn't trigger __getattr__
            case _:
                raise AttributeError(name)
    def __setattr__(self, name, value):
        match name:
            case 'name': # On all attr assignments
                value = value.lower().replace(' ', '_') # addr stored directly
            case 'age': # acct mangled to _acct
                if value < 0 or value > 150:
                    raise ValueError('invalid age')
            case 'acct':
                name = '_acct'
                value = value.replace('-', '')
                if len(value) != self.acctlen:
                    raise TypeError('invalid acct number')
            case 'remain':
                raise TypeError('cannot set remain')
        self.__dict__[name] = value # Avoid looping (or object)
```

This class has 34 lines. The `match` statement adds two lines and some indentation. The version has one drawback. Assignments to unmanaged attributes, such as `addr`, now cost an extra call. Fetches of unmanaged attributes cost nothing, since they are defined. The book's view is that generic tools suit delegation, while properties and descriptors suit specific attributes. Running either tester gives the same output as before, with the class name changed:

```text
$ python3 validate_tester.py validate_getattr
…same output as properties, except class name…
$ python3 validate_tester_plus.py validate_getattr
…same output as instance-state descriptors, except class name…
```

#### Validating with `__getattribute__`

The final variant catches every fetch with `__getattribute__`. It tests names to find managed attributes, and it sends the rest to the superclass. It keeps the same `__setattr__` as the previous version, since Python has no matching `__setattribute__` method.

Example 38-25 is that version. Because every fetch goes through `__getattribute__`, the names need no mangling, so `acct` is stored as `acct`. The method must send unmanaged fetches to the superclass to avoid loops and extra calls:

```python
class CardHolder:
    acctlen = 8 # Class data
    retireage = 62.5
    def __init__(self, acct, name, age, addr):
        self.acct = acct # Instance data
        self.name = name # These trigger __setattr__ too
        self.age = age # acct not mangled: name tested
        self.addr = addr # addr is not managed
        # remain has no data
    def __getattribute__(self, name):
        superget = object.__getattribute__ # Don't loop: level up
        match name:
            case 'acct': # On all attr fetches
                return superget(self, 'acct')[:-3] + '***'
            case 'remain':
                return superget(self, 'retireage') - superget(self, 'age')
            case _:
                return superget(self, name) # name, age, addr: stored
    def __setattr__(self, name, value):
        match name:
            case 'name': # On all attr assignments
                value = value.lower().replace(' ', '_') # addr stored directly
            case 'age':
                if value < 0 or value > 150:
                    raise ValueError('invalid age')
            case 'acct':
                value = value.replace('-', '')
                if len(value) != self.acctlen:
                    raise TypeError('invalid acct number')
            case 'remain':
                raise TypeError('cannot set remain')
        self.__dict__[name] = value # Avoid loop, orig names
```

This version also has 34 lines. Its cost is higher than the `__getattr__` version, since it adds calls for both setting and fetching unmanaged attributes. If speed matters most, this version may be the slowest of the four. Both generic versions match the other two in output, and they run the same way under both testers. The book points out that the generic approach can serve other roles too.

Be sure to run this code yourself. It shows more patterns for managed attributes.

## Managed attributes summary

Python gives you four ways to manage attribute access. The `__getattr__` and `__getattribute__` methods are operator-overloading hooks that can catch many attributes. Properties and descriptors manage one named attribute each. The `__getattr__` method runs only for undefined attributes. The `__getattribute__` method runs for every fetch, so it must avoid loops by calling `object` methods.

Properties are a simple form of descriptor, and both attach code to specific attributes. Descriptors are classes, so they can keep their own state, inherit, and use composition. Properties and descriptors handle fetches, assignments and deletions by design. The generic methods handle fetches, but assignments need `__setattr__`. Properties and descriptors also avoid extra calls on unmanaged names and show up in `dir` results. The generic methods are better suited to delegation.

Chapter 39 of the book covers decorators, which run when functions and classes are created instead of when attributes are accessed.

## Decorators

Decorators let you add behavior to a function or class without editing its body. You place one short line above the `def` or `class` statement, and Python applies the extra logic when the definition runs. Most application programmers only use decorators. Decorators now show up often in popular Python frameworks, so knowing the mechanics makes their role less mysterious.

### What a decorator is

A decorator is a callable object, usually a function, that takes another callable and returns a callable. Decoration is a way to attach management or augmentation code to functions and classes. Python supports two related kinds. A function decorator runs at the end of a `def` statement, and a class decorator runs at the end of a `class` statement.

Each kind rebinds a name. A function decorator rebinds the function name, so it can manage the function or the calls later made to it. A class decorator rebinds the class name, so it can manage the class or the instances created from it.

In short, decorators run automatically right after a definition finishes. The `@` line is the signal that tells Python to do this.

### Managing calls and instances

Most decorators wrap something. The wrapper is a proxy object that takes the place of the original name. When the name is used later, the proxy runs first. It can trace, time, check or change the request, and then it usually passes the request on to the original.

A function decorator installs call proxies that intercept later function calls. A class decorator installs interface proxies that intercept instance-creation calls. The proxy often creates the real instance for you.

### Managing functions and classes directly

Decorators can also manage the function or class object itself. A function decorator might register a function with an API or store attributes on it. A class decorator might add methods or data to a class.

If the decorator returns the same object it received, no wrapper is created. The decorator then becomes a simple post-creation step. Class decorators overlap with metaclasses, a more advanced tool, and often offer a lighter-weight option.

### Why use decorators

Decorators are never strictly required. You can always call a helper function or rebind the name by hand. The decorator syntax still earns its place, because it makes intent obvious and removes repeated augmentation code.

The syntax has three practical benefits. The decorator is easy to spot, unlike a helper call far away from the function. It is applied once, when the definition runs, so callers need no extra code. A user of an API is also less likely to forget a required step.

Decorators have drawbacks too. A wrapper can change the type of the object it decorates. It can also add an extra call every time the object is used. Any wrapping technique has the same issues, so weigh them in context.

### Decorators and macros

Some people compare decorators with aspect-oriented programming. That style inserts code that runs before or after a function call, and Python decorators have a similar effect. Their syntax also resembles Java annotations, though Python's model is more flexible and general.

Others call decorators macros, and that comparison can mislead you. A C macro made with `#define` works by text replacement and expansion. A Python decorator is a runtime operation that rebinds a name to a callable object, often a proxy. Comparing the two is like comparing Python's `import` with C's `#include`. One works on objects at runtime, and the other inserts text.

Treat a decorator as a callable that manages another callable. Python code is best understood in Python terms.

## Decorator basics

### Function decorator basics

A function decorator is mostly syntactic sugar. It runs one function through another at the end of a `def` statement, and it rebinds the original name to the result. The line above the `def` starts with `@`, followed by a reference to a decorator. As of Python 3.9, the expression after the `@` can be any expression that returns a decorator, though it is usually a simple name.

This code:

```python
@decorator  # Decorate function
def F(arg):
    ...

F(99)  # Call function
```

works the same as this longer form:

```python
def F(arg):
    ...

F = decorator(F)  # Rebind function name to decorator result
F(99)  # Essentially calls decorator(F)(99)
```

The decorator is a one-argument callable that returns a callable with the same number of arguments as `F`, or `F` itself. It runs only once, when the function is defined. Later calls to `F` run whatever object the decorator returned. That object may be a wrapper that adds logic, or the original function.

The same rebinding explains two built-in decorators you already know. Static methods and properties are declared this way:

```python
class S:
    @staticmethod
    def meth(arg):
        ...  # meth = staticmethod(meth)

class P:
    @property
    def name(self):
        ...  # name = property(name)
```

In both cases the method name is rebound to the result of a built-in decorator. The static method becomes a router, and the property becomes a descriptor. The process is more general than these two cases, as the next part explains.

#### Implementation

A decorator is a callable that returns a callable. The returned object runs when the original name is called later. It may be a wrapper that intercepts the call, or the original function augmented in some way.

To run code right after a function is created, you can return the function unchanged:

```python
def decorator(F):
    # Process function F here
    return F

@decorator
def func():  # func = decorator(func)
    ...
```

Because the original function is assigned back to its name, this adds a post-creation step. You might use it to register a function with an API or to set function attributes.

To intercept later calls, return a different object. The most common pattern is a wrapper that keeps the original function in an enclosing scope:

```python
def decorator(F):  # On @ decoration
    def wrapper(*args):  # On wrapped function call
        # Use F and args
        # F(*args) calls original function
        ...
    return wrapper

@decorator  # func = decorator(func)
def func(x, y):  # func is passed to decorator's F
    ...

func(6, 7)  # 6, 7 are passed to wrapper's *args
```

When `func` is later called, it really invokes `wrapper`. The wrapper can still reach the original function because `F` lives in an enclosing scope. Each decorated function therefore gets a fresh scope for its state.

The same idea works with a class. The decorator stores the function on an instance, and the instance's `__call__` method runs on each call:

```python
class decorator:
    def __init__(self, func):  # On @ decoration
        self.func = func
    def __call__(self, *args):  # On wrapped function call
        # Use self.func and args
        # self.func(*args) calls original function
        ...

@decorator  # func = decorator(func)
def func(x, y):  # func is passed to __init__
    ...

func(6, 7)  # 6, 7 are passed to __call__'s *args
```

Each decorated function now gets its own instance, and each instance keeps its own copy of the original function.

#### Supporting method decoration

The class-based version has a catch. It works for plain functions, but it fails when you decorate a method inside a class:

```python
class decorator:
    def __init__(self, func):  # func is method without instance
        self.func = func
    def __call__(self, *args):  # self is decorator instance
        # self.func(*args) fails! # C instance not in args!
        ...

class C:
    @decorator
    def method(self, x, y):  # method = decorator(method)
        ...  # Rebound to decorator instance
```

Here the decorated method is rebound to an instance of the decorator class. Later, the `self` in `__call__` is the decorator instance. The `C` instance never shows up in `*args`, so the decorator has no object to pass to the original method.

A nested function solves this. The wrapper receives the class instance as its first argument, because the method name is rebound to a simple function:

```python
def decorator(F):  # F is func or method without instance
    def wrapper(*args):  # class instance in args[0] for method
        # F(*args) runs func or method
        ...
    return wrapper

@decorator  # func = decorator(func)
def func(x, y):
    ...

func(6, 7)  # Really calls wrapper(6, 7)

class C:
    @decorator  # method = decorator(method)
    def method(self, x, y):  # Rebound to simple function
        ...

X = C()
X.method(6, 7)  # Really calls wrapper(X, 6, 7)
```

Python creates a bound method only when the attribute refers to a simple function. When it refers to an instance of a callable class, that instance is passed to `self` instead. This subtle difference matters in realistic code. If you want one decorator to work on both functions and methods, the nested function style is the safest choice.

### Class decorator basics

Class decorators use the same syntax as function decorators, and their coding patterns are very similar. They appear just before a `class` statement. Instead of wrapping one function, a class decorator manages the class itself or wraps the instance-creation calls. In the second role it can manage a whole object interface.

This code:

```python
@decorator  # Decorate class
class C:
    ...

x = C(99)  # Make an instance
```

works the same as:

```python
class C:
    ...

C = decorator(C)  # Rebind class name to decorator result
x = C(99)  # Essentially calls decorator(C)(99)
```

Calling the class name later triggers the callable that the decorator returned. That callable may or may not call the original class. To manage the class only, return the class unchanged:

```python
def decorator(C):
    # Process class C here
    return C

@decorator
class C:  # C = decorator(C)
    ...
```

To intercept instance creation, return a different callable. This example inserts an object that intercepts undefined attributes of the instance:

```python
def decorator(cls):  # On @ decoration
    class Wrapper:
        def __init__(self, *args):  # On instance creation
            self.wrapped = cls(*args)
        def __getattr__(self, name):  # On attribute fetch
            return getattr(self.wrapped, name)
    return Wrapper

@decorator
class C:  # C = decorator(C)
    def __init__(self, x, y):  # Run by Wrapper.__init__
        self.attr = 'hack'

x = C(6, 7)  # Really calls Wrapper(6, 7)
print(x.attr)  # Runs Wrapper.__getattr__, prints "hack"
```

The decorator rebinds the class name to another class. That class keeps the original class in an enclosing scope, and it creates and embeds an instance of the original class. Attribute fetches that miss on the wrapper are delegated to the embedded instance. Each decorated class gets its own scope, so each one remembers its own original class.

#### Supporting multiple instances

Some pairings of callable types work better than others. This version looks reasonable, but it is wrong:

```python
class Decorator:
    def __init__(self, C):  # On @ decoration
        self.C = C
    def __call__(self, *args):  # On instance creation
        self.wrapped = self.C(*args)
        return self
    def __getattr__(self, attrname):  # On attribute fetch
        return getattr(self.wrapped, attrname)

@Decorator
class C:  # C = Decorator(C)
    ...

x = C()
y = C()  # Overwrites x!
```

It handles several decorated classes, but each instance creation overwrites the one saved instance. Two patterns support multiple wrapped instances. Each one makes a new wrapper for every instance:

```python
def decorator(C):  # On @ decoration
    class Wrapper:
        def __init__(self, *args):  # On instance creation: new Wrapper
            self.wrapped = C(*args)  # Embed instance in instance
    return Wrapper
```

```python
class Wrapper:
    ...

def decorator(C):  # On @ decoration
    def onCall(*args):  # On instance creation: new Wrapper
        return Wrapper(C(*args))  # Embed instance in instance
    return onCall
```

Choose callable types carefully, and think about how state is kept.

### Decorator nesting

Sometimes one decorator is not enough. Suppose you wrote one function decorator that checks argument types before a call, and another that checks return types after it. You want both on one function. Decorators can be stacked, and each decorator must sit on its own line:

```python
@A
@B
@C
def f(x):
    ...
```

Python treats that stack the same as this form:

```python
def f(x):
    ...

f = A(B(C(f)))
```

The original function passes through three decorators, and the last one written is applied first. If every decorator inserts a wrapper, the calls stack. The innermost wrapper runs closest to the original function. Each layer can augment the call in a different way.

Class decorators stack in the same way:

```python
@hack
@code
class C:
    ...

X = C()
```

This is the same as `C = hack(code(C))` followed by `X = C()`. Each layer can return the original class or a wrapper. With wrappers, a request for an instance passes through both layers in turn.

The following do-nothing decorators simply return the function they receive:

```python
def d1(F): return F
def d2(F): return F
def d3(F): return F

@d1
@d2
@d3
def func():  # func = d1(d2(d3(func)))
    print('hack')

func()  # Prints "hack"
```

When decorators insert wrappers, they can add to the result. Each layer below runs from the inside out:

```python
def d1(F): return lambda: 'X' + F()
def d2(F): return lambda: 'Y' + F()
def d3(F): return lambda: 'Z' + F()

@d1
@d2
@d3
def func():  # func = d1(d2(d3(func)))
    return 'hack'

print(func())  # Prints "XYZhack"
```

Each `lambda` keeps the wrapped function in an enclosing scope. Wrappers can also be functions or callable classes. When you design them well, nesting lets you combine steps in many ways.

### Decorator arguments

Decorators can take arguments too. The arguments are passed to a callable that returns the decorator. That decorator returns the callable that runs on later calls. So decorator arguments usually set up several levels of state. This code:

```python
@decorator(A, B)
def F(arg):
    ...

F(99)
```

is mapped to this form:

```python
def F(arg):
    ...

F = decorator(A, B)(F)  # Rebind F to result of decorator's return value
F(99)  # Essentially calls decorator(A, B)(F)(99)
```

Decorator arguments are resolved before decoration happens. They are usually kept as state for later use. The skeleton looks like this:

```python
def decorator(A, B):  # Save A and B for later
    def actualDecorator(F):  # Save or use function F
        def callable_object(*args):  # Runs later, on calls to F
            ...
        return callable_object
    return actualDecorator
```

Decorator arguments therefore imply three levels of callables. The first accepts the arguments, the second is the decorator, and the third handles calls to the original function or class. Each level can be a function or a class, and each can keep state in scopes or attributes. Arguments can supply attribute initial values, trace labels, attribute names to validate, and more.

### Decorators that manage functions and classes too

Much of this chapter focuses on wrapping later calls. The decorator mechanism is more general, though. It is simply a protocol for passing a new function or class through a callable right after it is created:

```python
def decorator(O):
    # Augment function or class O
    return O

@decorator
def F():  # F = decorator(F)
    ...

@decorator
class C:  # C = decorator(C)
    ...
```

If the decorator returns the original object, it manages the function or class itself. This is useful for registering callables with an API or setting attributes when an object is created. The roles are limited only by your needs.

## Coding function decorators

Now for working code. This part shows the function decorator ideas in complete form, and the next part does the same for class decorators. Two larger case studies come at the end. They show typical decorator roles, including attribute privacy and argument range tests.

### Tracing function calls

Start with a call tracer. This `decorator1.py` module counts the calls to a function and prints a trace message for each call:

```python
class tracer:
    def __init__(self, func):  # On @ decoration: save original func
        self.calls = 0
        self.func = func
    def __call__(self, *args):  # On later calls: run original func
        self.calls += 1
        print(f'call {self.calls} to {self.func.__name__}')
        self.func(*args)

@tracer
def hack(a, b, c):  # hack = tracer(hack)
    print(a + b + c)  # Wraps hack in a decorator object
```

Each decorated function gets its own instance, with its own saved function and call counter. The `*args` syntax packs and unpacks any number of positional arguments. This first version does not handle keyword arguments, class methods or return values. Later versions fix those gaps.

In an interactive session, each call prints a trace message, because the class intercepts it:

```text
$ python3
>>> from decorator1 import hack
>>> hack(1, 2, 3)  # Really calls the tracer wrapper object
call 1 to hack
6
>>> hack('a', 'b', 'c')  # Invokes __call__ in class
call 2 to hack
abc
>>> hack.calls  # Number calls in wrapper state information
2
>>> hack
<decorator1.tracer object at 0x10cafc680>
```

The decorated name is now an instance of the `tracer` class. That can matter for code that checks types, but it is usually harmless. The call count lives on the decorated function as an attribute.

The `@` syntax is often more convenient than changing every call site. It also avoids calling the original function by accident. You could write the same tracing without decorators, but it needs extra code wherever the function is called:

```text
>>> calls = 0
>>> def tracer(func, *args):
...     global calls
...     calls += 1
...     print(f'call {calls} to {func.__name__}')
...     func(*args)
>>> def hack(a, b, c):  # Nondecorated function
...     print(a, b, c)
>>> hack(1, 2, 3)  # Normal nontraced call: accidental?
1 2 3
>>> tracer(hack, 1, 2, 3)  # Special traced call without decorators
call 1 to hack
1 2 3
```

This alternative works on any function, but every call must use the special form. Its intent is also less obvious, and nothing guarantees that a normal call goes through the tracer. Decorators are not required, but they are often the most uniform option.

### Decorator state retention options

Decorators must keep state from decoration time for use during later calls. They need to support several decorated objects, each with its own calls. You have four main options: instance attributes, global variables, nonlocal closure variables and function attributes.

#### State with class-instance attributes

This version adds support for keyword arguments and returns the wrapped function's result, so it works in more cases. It keeps state as instance attributes:

```python
class tracer:  # State via instance attributes
    def __init__(self, func):  # On @ decorator
        self.calls = 0  # Save func for later call
        self.func = func
    def __call__(self, *args, **kwargs):  # On call to original function
        self.calls += 1
        print(f'call {self.calls} to {self.func.__name__}')
        return self.func(*args, **kwargs)

@tracer
def hack(a, b, c):  # Same as: hack = tracer(hack)
    print(a + b + c)  # Triggers tracer.__init__

@tracer
def code(x, y):  # Same as: code = tracer(code)
    print(x ** y)  # Wraps code in a tracer object

if __name__ == '__main__':
    hack(1, 2, 3)  # Really calls tracer instance: runs tracer.__call__
    hack(a=4, b=5, c=6)  # hack is an instance attribute
    code(4, 2)  # Really calls tracer instance: self.func is code
    code(2, y=16)  # self.calls is per-decoration here
```

Each decoration gets its own copy of the wrapped function and the counter. Running the script gives this output:

```text
$ python3 decorator_state_classes.py
call 1 to hack
6
call 2 to hack
15
call 1 to code
16
call 2 to code
65536
```

This scheme works well for functions, but it still has problems with methods. The next part explains why.

#### State with global variables

For simpler jobs, a global variable may be enough. This version keeps the call counter in the module's global scope:

```python
calls = 0
def tracer(func):  # State via enclosing scope and global
    def wrapper(*args, **kwargs):  # Instead of class attributes
        global calls  # calls is global, not per-function
        calls += 1
        print(f'call {calls} to {func.__name__}')
        return func(*args, **kwargs)
    return wrapper

@tracer
def hack(a, b, c):  # Same as: hack = tracer(hack)
    print(a + b + c)

@tracer
def code(x, y):  # Same as: code = tracer(code)
    print(x ** y)

if __name__ == '__main__':
    hack(1, 2, 3)  # Really calls wrapper, assigned to hack
    hack(a=4, b=5, c=6)  # wrapper calls hack
    code(4, 2)  # Really calls wrapper, assigned to code
    code(2, y=16)  # Global calls is not per-decoration here!
```

A global counter is shared by every wrapped function. It counts calls across the whole program, not per function. The output shows the problem clearly:

```text
$ python3 decorator_state_globals.py
call 1 to hack
6
call 2 to hack
15
call 3 to code
16
call 4 to code
65536
```

The single shared counter is updated by calls to every decorated function. That is usually not what you want for per-function data.

#### State with enclosing-scope nonlocals

If you want a per-function counter, use a closure with the `nonlocal` statement. It lets the nested function change a variable in the enclosing scope, so each decoration gets its own counter:

```python
def tracer(func):  # State via enclosing scope and nonlocal
    calls = 0  # Instead of class attrs or global
    def wrapper(*args, **kwargs):  # calls is per-function, not global
        nonlocal calls
        calls += 1
        print(f'call {calls} to {func.__name__}')
        return func(*args, **kwargs)
    return wrapper

@tracer
def hack(a, b, c):  # Same as: hack = tracer(hack)
    print(a + b + c)

@tracer
def code(x, y):  # Same as: code = tracer(code)
    print(x ** y)

if __name__ == '__main__':
    hack(1, 2, 3)  # Really calls wrapper, bound to hack
    hack(a=4, b=5, c=6)  # wrapper calls hack
    code(4, 2)  # Really calls wrapper, bound to code
    code(2, y=16)  # Nonlocal calls _is_ per-decoration here
```

Enclosing-scope variables are not program globals, so each wrapped function keeps its own count:

```text
$ python3 decorator_state_nonlocals.py
call 1 to hack
6
call 2 to hack
15
call 1 to code
16
call 2 to code
65536
```

#### State with function attributes

You can also store changeable state as attributes of the wrapper function. A factory function creates a new function on each decoration, so its attributes are per-decoration state. Enclosing-scope references still work as usual:

```python
def tracer(func):  # State via enclosing scope and func attr
    def wrapper(*args, **kwargs):  # calls is per-function, not global
        wrapper.calls += 1
        print(f'call {wrapper.calls} to {func.__name__}')
        return func(*args, **kwargs)
    wrapper.calls = 0
    return wrapper

@tracer
def hack(a, b, c):  # Same as: hack = tracer(hack)
    print(a + b + c)

@tracer
def code(x, y):  # Same as: code = tracer(code)
    print(x ** y)

if __name__ == '__main__':
    hack(1, 2, 3)  # Really calls wrapper, assigned to hack
    hack(a=4, b=5, c=6)  # wrapper calls hack
    code(4, 2)  # Really calls wrapper, assigned to code
    code(2, y=16)  # wrapper.calls _is_ per-decoration here
```

This works because the name `wrapper` lives in the enclosing `tracer` scope. Changing `wrapper.calls` does not rebind `wrapper`, so no `nonlocal` declaration is needed. The output matches the nonlocal version.

This scheme is less common than `nonlocal`, so save it for cases where the other schemes do not help. It has one real advantage, though. Function attributes are visible from outside the decorator, while nonlocals are visible only inside the nested function. Attributes can be read as `hack.calls` from anywhere in your program.

### Class pitfall: decorating methods

The class-based `tracer` from the state section works for plain functions. It was first assumed to work for methods too, with `self` simply included at the front of `*args`. That assumption is wrong, and the reason is not obvious. When the class-based tracer decorates a method, `self` is the decorator instance. The instance of the decorated class is not in `*args` at all.

Here is the class again:

```python
class tracer:  # State via instance attributes
    def __init__(self, func):  # On @ decorator
        self.calls = 0  # Save func for later call
        self.func = func
    def __call__(self, *args, **kwargs):  # On call to original function
        self.calls += 1
        print(f'call {self.calls} to {self.func.__name__}')
        return self.func(*args, **kwargs)
```

It works for plain functions:

```text
>>> from decorator_state_classes import tracer
>>> @tracer
... def hack(a, b, c):  # hack = tracer(hack)
...     print(a + b + c)  # Triggers tracer.__init__
>>> hack(1, 2, 3)  # Runs tracer.__call__
call 1 to hack
6
>>> hack(a=4, b=5, c=6)  # hack saved in an instance attribute
call 2 to hack
15
```

It fails for methods:

```text
>>> class Person:
...     def __init__(self, name, pay):
...         self.name = name
...         self.pay = pay
...     @tracer
...     def giveRaise(self, percent):  # giveRaise = tracer(giveRaise)
...         self.pay *= (1.0 + percent)
>>> pat = Person('Pat Jones', 50_000)  # tracer remembers method funcs
>>> pat.giveRaise(.10)  # Runs tracer.__call__(???, .10)
call 1 to giveRaise
TypeError: Person.giveRaise() missing 1 required positional argument: 'percent'
```

The `self` in `__call__` must be the `tracer` object, because it holds the `calls` and `func` state. The method needs the `Person` instance too, to dispatch the call. Python passes only the `tracer` instance, and the `Person` object is absent. Adding a print of the arguments shows it:

```text
>>> pat.giveRaise(.10)
<__main__.tracer object at 0x108a02c00> (0.10,) {}
```

Python passes the subject instance to `self` only when a method name is bound to a simple function. When the name is bound to an instance of a callable class, that instance is passed instead. The fix is to change the coding style, not the decorator logic.

#### Using nested functions to decorate methods

For a decorator that works on both functions and methods, use nested `def` statements. Then you do not depend on one `self` argument serving two roles. The earlier nonlocal and attribute versions already work this way:

```text
>>> from decorator_state_nonlocals import tracer  # See the nonlocal version
>>> @tracer
... def hack(a, b, c):  # Works for functions
...     print(a + b + c)
>>> hack(1, 2, 3)
call 1 to hack
6
>>> class Person:  # AND works for methods
...     def __init__(self, name, pay):
...         self.name = name
...         self.pay = pay
...     @tracer
...     def giveRaise(self, percent):  # self included in args
...         self.pay *= (1.0 + percent)  # Counter in nonlocals
>>> pat = Person('Pat Jones', 50_000)
>>> pat.giveRaise(.10)
call 1 to giveRaise
>>> pat.giveRaise(.10)
call 2 to giveRaise
>>> f'{pat.pay:,.2f}'
'60,500.00'
```

The attribute version gives the same results. Here the decorated method is a simple function, so Python passes the `Person` object as the first argument. The decorator forwards it inside `*args` to the real method's `self`. Trace this through until the model feels familiar.

#### Using descriptors to decorate methods

Descriptors offer another route. A descriptor is a class attribute with a `__get__` method, which runs whenever that attribute is fetched. The `__get__` method receives both the descriptor instance and the subject instance, so it can keep the decorator's state and still reach the original object:

```python
class Descriptor:
    def __get__(self, instance, owner): ...

class Subject:
    attr = Descriptor()

X = Subject()
X.attr  # Roughly runs Descriptor.__get__(Subject.attr, X, Subject)
```

This version of the tracer is a decorator and a descriptor at once:

```python
class tracer:  # A decorator+descriptor
    def __init__(self, func):  # On @ decorator
        self.calls = 0  # Save func for later call
        self.func = func
    def __call__(self, *args, **kwargs):  # On call to original func/meth
        self.calls += 1
        print(f'call {self.calls} to {self.func.__name__}')
        return self.func(*args, **kwargs)
    def __get__(self, instance, owner):  # On method attribute fetch
        return wrapper(self, instance)

class wrapper:
    def __init__(self, desc, subj):  # Save both instances
        self.desc = desc  # Route calls back to deco/desc
        self.subj = subj
    def __call__(self, *args, **kwargs):
        return self.desc(self.subj, *args, **kwargs)  # Runs tracer.__call__

@tracer
def hack(a, b, c):  # hack = tracer(hack)
    ...  # Uses __call__ only

class Person:
    ...
    @tracer
    def giveRaise(self, percent):  # giveRaise = tracer(giveRaise)
        ...  # Makes giveRaise a descriptor
```

For a plain function, only `__call__` runs. For a method, the lookup `pat.giveRaise` triggers `__get__` first. The returned `wrapper` keeps the subject instance. The call expression then runs `wrapper.__call__`, which calls `tracer.__call__`, which finally calls the original method. The `wrapper` object routes control back to the one decorator instance, so every call shares the same counter.

A nested-function version does the same job with less code:

```python
class tracer:
    def __init__(self, func):  # On @ decorator
        self.calls = 0  # Save func for later call
        self.func = func
    def __call__(self, *args, **kwargs):  # On call to original func
        self.calls += 1
        print(f'call {self.calls} to {self.func.__name__}')
        return self.func(*args, **kwargs)
    def __get__(self, instance, owner):  # On method fetch
        def wrapper(*args, **kwargs):  # Retain both inst
            return self(instance, *args, **kwargs)  # Runs __call__
        return wrapper
```

Both descriptor versions are harder to follow than the nested-function version. They also cost more at runtime. The nested-function style is usually the better second choice.

A simpler descriptor-only version looks tempting, but it only works for methods:

```python
class tracer:  # For methods, but not functions!
    def __init__(self, meth):  # On @ decorator
        self.calls = 0
        self.meth = meth
    def __get__(self, instance, owner):  # On method fetch
        def wrapper(*args, **kwargs):  # On method call: proxy with self+inst
            self.calls += 1
            print(f'call {self.calls} to {self.meth.__name__}')
            return self.meth(instance, *args, **kwargs)
        return wrapper

@tracer  # OK for methods but FAILS for functions
def hack(a, b, c):  # hack = tracer(hack)
    ...  # No attribute fetch occurs on calls!
```

A function call never fetches an attribute, so `__get__` never runs for it. That limit is the reverse of the problem we set out to solve. If you want one decorator for both functions and methods, go with nested functions.

Some decorators do not need the subject instance at all. Python's own `staticmethod` decorator is an example, because its whole purpose is to remove the instance from the call. Those decorators can be classes that still work on plain functions. The simpler rule still holds. If you want a decorator to work on both functions and methods, nested functions are usually the best choice.

### Timing function calls

Another practical use is timing. This decorator measures each call, along with the total time across all calls. In this `timerdeco1.py` module, it times two ways of building a list:

```python
"Caveat: timer won't work on methods as coded (see quiz solution)"
import time, sys
class timer:
    def __init__(self, func):
        self.func = func
        self.alltime = 0
    def __call__(self, *args, **kargs):
        start = time.perf_counter()
        result = self.func(*args, **kargs)
        elapsed = time.perf_counter() - start
        self.alltime += elapsed
        print(f'{self.func.__name__}: {elapsed:.5f}, {self.alltime:.5f}')
        return result

@timer
def listcomp(N):
    return [x * 2 for x in range(N)]

@timer
def mapcall(N):
    return list(map((lambda x: x * 2), range(N)))

if __name__ == '__main__':
    for func in (listcomp, mapcall):
        result = func(5)  # Time for this call, result
        func(50_000)
        func(500_000)
        func(1_000_000)
        print(result)
        print(f'allTime = {func.alltime}\n')  # Total time for all func calls
    print('**map/comp =', round(mapcall.alltime / listcomp.alltime, 3))
```

Run under CPython 3.12 on a macOS host, the self-test prints one line per call. Each line shows the function name, the time for that call and the running total. The output ends with the total for each function and the ratio of the two:

```text
$ python3 timerdeco1.py
listcomp: 0.00000, 0.00000
listcomp: 0.00366, 0.00366
listcomp: 0.03134, 0.03500
listcomp: 0.05213, 0.08713
[0, 2, 4, 6, 8]
allTime = 0.08712841104716063
mapcall: 0.00001, 0.00001
mapcall: 0.00396, 0.00397
mapcall: 0.04082, 0.04479
mapcall: 0.07789, 0.12268
[0, 2, 4, 6, 8]
allTime = 0.12268476499593817
**map/comp = 1.408
```

Your times will differ with the Python version, the machine and other load. The cumulative time is kept as an instance attribute. Here `map` is slower than the list comprehension, because each element costs a function call.

The `timeit` module and the timing helpers from the timing chapter do the same job without a decorator. In a REPL they look like this:

```text
>>> def listcomp(N): [x * 2 for x in range(N)]
>>> import timer  # Timing helper techniques
>>> timer.total(1, listcomp, 1_000_000)
(0.08150088600814342, None)
>>> timer.bestoftotal(5, 1, listcomp, 1_000_000)
(0.059792334999656305, None)
>>> import timeit
>>> timeit.timeit(number=1, stmt=lambda: listcomp(1_000_000))
0.08125517799635418
>>> min(timeit.repeat(repeat=5, number=1, stmt=lambda: listcomp(1_000_000)))
0.06156357398140244
```

A nondecorator approach lets the functions run with or without timing. But the call sites must change every time you want timing. There is also no direct way to make sure every call goes through the timer. Decorators are a good choice when functions are already deployed in a larger system and cannot easily be passed to an analysis function. A nondecorator approach may be better when you want to time only some calls.

### Adding decorator arguments

The timer works, but it would be more useful with settings. A label and an on-off switch for trace messages are the obvious ones. Decorator arguments provide that. Here is the general pattern:

```python
def timer(label=''):
    def decorator(func):
        def onCall(*args):  # Multilevel state retention:
            ...  # args passed to function
            func(*args)  # func retained in enclosing scope
            print(label, ...)  # label retained in enclosing scope
        return onCall
    return decorator  # Returns the actual decorator

@timer('==>')  # Like listcomp = timer('==>')(listcomp)
def listcomp(N):
    ...  # listcomp is rebound to new onCall

listcomp(...)  # Really calls onCall
```

The `timer` function runs before decoration. It returns the decorator, which remembers the label and the function. The label stays in an enclosing scope, so each decoration keeps its own label.

The `timerdeco2.py` module puts that idea into practice. It uses a class for the second level of state:

```python
import time
def timer(label='', trace=True):  # On decorator args: retain args
    class Timer:
        def __init__(self, func):  # On @: retain decorated func
            self.func = func
            self.alltime = 0
        def __call__(self, *args, **kargs):  # On calls: call original
            start = time.perf_counter()
            result = self.func(*args, **kargs)
            elapsed = time.perf_counter() - start
            self.alltime += elapsed
            if trace:
                if label: print(label, end=' ')
                print(f'{self.func.__name__}: {elapsed:.5f}, {self.alltime:.5f}')
            return result
    return Timer
```

The outer `timer` function creates a scope that holds the decorator arguments. It runs before decoration and returns the `Timer` class as the actual decorator. Each decorated function then gets its own `Timer` instance. That instance keeps the function and can also see the arguments.

A client module applies the decorator with different settings for each function:

```python
import sys
from timerdeco2 import timer

@timer(label='[CCC]==>')
def listcomp(N):  # Like listcomp = timer(...)(listcomp)
    return [x * 2 for x in range(N)]  # listcomp(...) triggers Timer.__call__

@timer(trace=True, label='[MMM]==>')
def mapcall(N):
    return list(map((lambda x: x * 2), range(N)))

for func in (listcomp, mapcall):
    result = func(5)  # Time for this call, return value
    func(50_000)
    func(500_000)
    func(1_000_000)
    print(result)
    print(f'allTime = {func.alltime}\n')  # Total time for all calls
print('**map/comp =', round(mapcall.alltime / listcomp.alltime, 3))
```

Each function now has a label of its own. That makes the trace lines easy to find in a larger program's output:

```text
$ python3 testseqs.py
[CCC]==> listcomp: 0.00000, 0.00000
[CCC]==> listcomp: 0.00379, 0.00379
[CCC]==> listcomp: 0.03142, 0.03521
[CCC]==> listcomp: 0.05188, 0.08709
[0, 2, 4, 6, 8]
allTime = 0.08709081003325991
[MMM]==> mapcall: 0.00001, 0.00001
[MMM]==> mapcall: 0.00401, 0.00402
[MMM]==> mapcall: 0.04025, 0.04427
[MMM]==> mapcall: 0.07776, 0.12203
[0, 2, 4, 6, 8]
allTime = 0.12203056103317067
**map/comp = 1.401
```

This timer works on any function, in modules and interactively. It is a general-purpose tool for timing code. Timing methods needs a small rewrite, because the nested `Timer` class cannot handle `self` correctly. That rewrite is a good exercise, and it is covered in the chapter quiz.

## Coding class decorators

Function decorators manage calls to functions. Class decorators can manage a class itself, or they can intercept instance creation to manage the instances. Like function decorators, they are syntactic sugar. They make intent obvious and reduce missed calls.

### Singleton classes

Class decorators can manage all instances of a class. The classic singleton pattern allows at most one instance to exist. This decorator enforces that rule:

```python
instances = {}
def singleton(aClass):  # On @ decoration
    def onCall(*args, **kwargs):  # On instance creation
        if aClass not in instances:  # One dict entry per class
            instances[aClass] = aClass(*args, **kwargs)
        return instances[aClass]
    return onCall
```

Decorate each class that should be a singleton:

```python
from singletons1 import singleton

@singleton  # Person = singleton(Person)
class Person:  # Rebinds Person to onCall
    def __init__(self, name, hours, rate):  # onCall remembers Person
        self.name = name
        self.hours = hours
        self.rate = rate
    def pay(self):
        return self.hours * self.rate

@singleton  # Hack = singleton(Hack)
class Hack:  # Rebinds Hack to onCall
    def __init__(self, val):  # onCall remembers Hack
        self.attr = val

sue = Person('Sue', 50, 20)  # Really calls onCall
print(sue.name, sue.pay())
bob = Person('Bob', 40, 10)  # Same, single object
print(bob.name, bob.pay())
X = Hack(val=42)  # One Person, one Hack
Y = Hack(99)
print(X.attr, Y.attr)
```

Every creation call for a class goes to `onCall`, which returns the one saved instance. Running the script shows that Bob's object is really Sue's:

```text
$ python3 singletons.py
Sue 1000
Sue 1000
42 42
```

Other versions do the same thing. This one keeps one enclosing scope per class, instead of a global table entry per class:

```python
def singleton(aClass):  # On @ decoration
    instance = None
    def onCall(*args, **kwargs):  # On instance creation
        nonlocal instance
        if instance == None:
            instance = aClass(*args, **kwargs)  # One scope per class
        return instance
    return onCall
```

Function attributes can hold the instance too. This version uses one function per decoration:

```python
def singleton(aClass):  # On @ decoration
    def onCall(*args, **kwargs):  # On instance creation
        if onCall.instance == None:
            onCall.instance = aClass(*args, **kwargs)  # One function per class
        return onCall.instance
    onCall.instance = None
    return onCall
```

A class-based version keeps one instance per decoration in an attribute:

```python
class singleton:
    def __init__(self, aClass):  # On @ decoration
        self.aClass = aClass
        self.instance = None
    def __call__(self, *args, **kwargs):  # On instance creation
        if self.instance == None:
            self.instance = self.aClass(*args, **kwargs)  # One instance per class
        return self.instance
```

The class-based version is the most explicit, and it may be easier to extend later. Simple jobs do not need a class, though. Choose the version that fits your team's style, and store it in an importable module.

### Tracing object interfaces

Class decorators can also wrap a whole object interface. That is useful for tracing every attribute of an instance. A simple delegation example shows the idea first.

#### The nondecorator approach

This wrapper intercepts attribute fetches that miss on the wrapper itself, and then it delegates them to the embedded object:

```python
class Wrapper:
    def __init__(self, object):
        self.wrapped = object  # Save object
    def __getattr__(self, attrname):
        print('Trace:', attrname)  # Trace fetch
        return getattr(self.wrapped, attrname)  # Delegate fetch

x = Wrapper([1,2,3])  # Wrap a list object
x.append(4)  # Delegate to list method
```

The wrapper traces attribute accesses made from outside the wrapped object's class. Accesses inside that class's own methods are not caught, and they run normally. This wrapper handles the whole interface, unlike a function decorator that wraps one method.

#### The class-decorator approach

A class decorator can create the wrapped instance for you. Instead of passing a ready-made object into the wrapper, you just decorate the class. This version also accepts keyword arguments and counts the number of accesses:

```python
def Tracer(aClass):  # On @ decorator
    class Wrapper:
        def __init__(self, *args, **kargs):  # On instance creation
            self.fetches = 0
            self.wrapped = aClass(*args, **kargs)  # Use enclosing-scope name
        def __getattr__(self, attrname):
            print('Trace: ' + attrname)  # Catches all but own attrs
            self.fetches += 1
            return getattr(self.wrapped, attrname)  # Delegate to wrapped obj
    return Wrapper

if __name__ == '__main__':
    @Tracer
    class Hack:  # Hack = Tracer(Hack)
        def display(self):  # Hack is rebound to Wrapper
            print('Hack!' * 3)

    @Tracer
    class Person:  # Person = Tracer(Person)
        def __init__(self, name, hours, rate):  # Wrapper remembers Person
            self.name = name
            self.hours = hours
            self.rate = rate
        def pay(self):  # Accesses outside class traced
            return self.hours * self.rate  # In-method accesses not traced

    work = Hack()  # Triggers Wrapper()
    work.display()  # Triggers __getattr__
    print([work.fetches])
    print()

    bob = Person('Bob', 40, 50)  # bob is really a Wrapper
    print(bob.name)  # Wrapper embeds a Person
    print(bob.pay())
    print()

    sue = Person('Sue', rate=100, hours=60)  # sue is a different Wrapper
    print(sue.name)  # With a different Person
    print(sue.pay())
    print()

    print(bob.name)  # bob's state != sue's state
    print(bob.pay())
    print('calls:', [bob.fetches, sue.fetches])  # Wrapper attrs are not traced
```

This is different from the function tracer. It intercepts instance creation, so it traces an entire object interface, meaning any attribute of the instance. The output shows each access as it happens:

```text
$ python3 interfacetracer.py
Trace: display
Hack!Hack!Hack!
[1]
Trace: name
Bob
Trace: pay
2000
Trace: name
Sue
Trace: pay
6000
Trace: name
Bob
Trace: pay
2000
calls: [4, 2]
```

Each decoration creates one `Wrapper` class, and each instance gets its own counter. The `Person` instances are really `Wrapper` objects. The built-in operations are not caught by `__getattr__`, a limit we return to later in this section.

The decorator can also wrap a built-in type, such as a list, as long as you subclass it so the decorator syntax works:

```text
>>> from interfacetracer import Tracer
>>> @Tracer
... class MyList(list): pass  # MyList = Tracer(MyList)
>>> x = MyList([1, 2, 3])  # Triggers Wrapper()
>>> x.append(4)  # Triggers __getattr__, append
Trace: append
>>> x.wrapped
[1, 2, 3, 4]
>>> MyList = Tracer(list)  # Or perform decoration manually
>>> x = MyList([4, 5, 6])  # Else subclass statement required
>>> x.append(7)
Trace: append
>>> x.wrapped
[4, 5, 6, 7]
```

The decorator version moves instance creation into the decorator. Normal creation syntax stays the same, and the augmentation appears only at the class definition. Compare the two styles:

```python
@Tracer  # Decorator approach
class Person: ...

bob = Person('Bob', 40, 50)
sue = Person('Sue', rate=100, hours=60)
```

```python
class Person: ...  # Nondecorator approach

bob = Wrapper(Person('Bob', 40, 50))
sue = Wrapper(Person('Sue', rate=100, hours=60))
```

If you make many instances and want the augmentation on all of them, decorators usually win on code size and maintenance.

### Class pitfall: retaining multiple instances

A class-based version of this decorator looks possible, but it has a serious flaw:

```python
class Tracer:
    def __init__(self, aClass):  # On @decorator
        self.aClass = aClass  # Use instance attribute
    def __call__(self, *args):  # On instance creation
        self.wrapped = self.aClass(*args)  # ONE (LAST) INSTANCE PER CLASS!
        return self
    def __getattr__(self, attrname):
        print('Trace:', attrname)
        return getattr(self.wrapped, attrname)

@Tracer  # Triggers __init__
class Hack:  # Like: Hack = Tracer(Hack)
    def display(self):
        print('Hack!' * 3)

work = Hack()  # Triggers __call__
work.display()  # Triggers __getattr__
```

The `__init__` method runs when the decorator is applied to the class. The `__call__` method runs on each instance creation. Both versions handle several classes. But each new instance overwrites the saved one, so the decorator keeps only the last instance. A second decorated class shows the problem:

```python
@Tracer
class Person:  # Person = Tracer(Person)
    def __init__(self, name):  # Person rebound to a Tracer
        self.name = name

bob = Person('Bob')  # bob is really a Tracer
print(bob.name)  # Tracer embeds a Person
sue = Person('Sue')
print(sue.name)  # sue overwrites bob
print(bob.name)  # OOPS: now bob's name is 'Sue'!
```

The output confirms it. Bob's name changes to Sue after Sue is created:

```text
$ python3 interfacetracer-fail.py
Trace: display
Hack!Hack!Hack!
Trace: name
Bob
Trace: name
Sue
Trace: name
Sue
```

This is bad state retention. The decorator keeps one instance per class, not one per object created from it. The function-based `Tracer` from the previous part works for multiple instances. It returns a class, so each creation call makes a new `Wrapper`. Class-based decorators have this trap, so check which callable type you need.

### Private and public attributes

This case study implements attribute privacy with a class decorator. The `Private` declaration blocks fetches and changes of named attributes from outside the class. Code inside the class's own methods still has full access. The decorator is not identical to the private attributes of C++ or Java. It offers a development-time check where you need one.

Attribute privacy was introduced earlier in this chapter's class material. This version adds checks on fetches too. It uses delegation instead of inheritance. Its interception is still based on the `__getattr__` and `__setattr__` methods. When a private attribute is accessed, it raises a `TypeError` with a message. A `try` statement can catch that exception, or the script can stop.

The first version catches explicit attribute fetches but not implicit operations, which we cover later:

```python
"""
Class decorator with Private attribute declarations.
Privacy for attributes fetched from class instances.
See self-test code at end of file for a usage example.
Rebinding is: Doubler = Private('data', 'size')(Doubler).
Private returns onDecorator, onDecorator returns onInstance,
and each onInstance instance embeds a new Doubler instance.
"""

traceMe = False

def trace(*args):
    if traceMe: print(f'[{" ".join(map(str, args))}]')  # Python 3.12+ f-string

def Private(*privates):  # privates in enclosing scope
    def onDecorator(aClass):  # aClass in enclosing scope
        class onInstance:  # wrapped in instance attribute
            def __init__(self, *args, **kargs):
                self.wrapped = aClass(*args, **kargs)
            def __getattr__(self, attr):  # My attrs don't call getattr
                trace('get:', attr)  # Others assumed in wrapped
                if attr in privates:
                    raise TypeError('private attribute fetch, ' + attr)
                else:
                    return getattr(self.wrapped, attr)
            def __setattr__(self, attr, value):  # Outside accesses
                trace('set:', attr, value)  # Others run normally
                if attr == 'wrapped':  # Allow my attrs
                    self.__dict__[attr] = value  # Avoid looping
                elif attr in privates:
                    raise TypeError('private attribute change, ' + attr)
                else:
                    setattr(self.wrapped, attr, value)  # Wrapped obj attrs
        return onInstance
    return onDecorator

if __name__ == '__main__':
    traceMe = True
    @Private('data', 'size')  # Doubler = Private(...)(Doubler)
    class Doubler:
        def __init__(self, label, start):
            self.label = label  # Accesses inside the subject class
            self.data = start  # Not intercepted: run normally
        def size(self):
            return len(self.data)  # Method bodies run with no checking
        def double(self):  # Because privacy not inherited
            for i in range(self.size()):
                self.data[i] = self.data[i] * 2
        def display(self):
            print(f'{self.label} => {self.data}')

    print('Making instances...')
    X = Doubler('X is', [1, 2, 3])
    Y = Doubler('Y is', [-10, -20, -30])
    # The following all succeed properly
    print('\nExploring X instance...')
    print(X.label)  # Accesses outside subject class
    X.display(); X.double(); X.display()  # Intercepted: validated, delegated
    print('\nExploring Y instance...')
    print(Y.label)
    Y.display(); Y.double()
    Y.label = 'Hack'
    Y.display()
    # The following all fail properly
    """
    print(X.size())  # Prints "TypeError: private attribute fetch, size"
    print(X.data)
    X.data = [1, 1, 1]  # Prints "TypeError: private attribute change, data"
    X.size = lambda S: 0
    print(Y.data)
    print(Y.size())
    """
```

With tracing on, the self-test shows each attribute fetch and assignment that comes from outside the class. Accesses inside the class run quietly:

```text
$ python3 access1.py
Making instances...
[set: wrapped <__main__.Doubler object at 0x1059c7d70>]
[set: wrapped <__main__.Doubler object at 0x1059c7da0>]
Exploring X instance...
[get: label]
X is
[get: display]
X is => [1, 2, 3]
[get: double]
[get: display]
X is => [2, 4, 6]
Exploring Y instance...
[get: label]
Y is
[get: display]
Y is => [-10, -20, -30]
[get: double]
[set: label Hack]
[get: display]
Hack => [-20, -40, -60]
```

Three points help when you study this code. First, delegation makes it easy to tell inside accesses from outside ones. The Chapter 30 version used inheritance, which made that split awkward. Second, the decorator arguments are used before decoration. The `Private` function returns the decorator, and the decorator remembers the names. Third, three levels of state live in enclosing scopes and instance attributes. The arguments, the class and the wrapped instance each have a home.

The `__setattr__` method sets the proxy's own `wrapped` attribute through `__dict__`, which avoids a loop. It sets all other attributes through the built-in `setattr` on the wrapped object. It reads them with `getattr`. Because of this, the decorator works with classes that use `__slots__`, properties and descriptors. Each class gets the storage it needs, and the proxy stays out of the way.

#### Generalizing for public declarations

Once `Private` works, `Public` is only the inverse test. A `Private` declaration blocks outside access to the names it lists. A `Public` declaration allows outside access to the names it lists and blocks everything else. The two are mutually exclusive, so pick one per class.

With `Private`, undeclared names are public. New names can be created from outside. With `Public`, undeclared names are private, and new names cannot be created from outside. The code adds one more level of state: the validation test lives in its own enclosing scope.

```python
"""
Class decorator with Private and Public attribute declarations.
Controls external access to attributes stored on an instance, or
inherited by it from its classes. Private declares attribute names
that cannot be fetched or assigned outside the decorated class,
and Public declares all the names that can. Choose either decorator.
Caveat: as is, this works for explicitly-named attributes only. The
__X__ operator-overloading methods fetched implicitly for built-in
operations do not trigger either __getattr__ or __getattribute__, and
hence won't be delegated to any wrapped objects that define them. If
needed, add __X__ methods to catch and delegate built-ins (per ahead).
"""

traceMe = False

def trace(*args):
    if traceMe: print('[' + ' '.join(map(str, args)) + ']')

def accessControl(failIf):
    def onDecorator(aClass):
        class onInstance:
            def __init__(self, *args, **kargs):
                self.__wrapped = aClass(*args, **kargs)
            def __getattr__(self, attr):
                trace('get:', attr)
                if failIf(attr):
                    raise TypeError('private attribute fetch, ' + attr)
                else:
                    return getattr(self.__wrapped, attr)
            def __setattr__(self, attr, value):
                trace('set:', attr, value)
                if attr == '_onInstance__wrapped':
                    self.__dict__[attr] = value
                elif failIf(attr):
                    raise TypeError('private attribute change, ' + attr)
                else:
                    setattr(self.__wrapped, attr, value)
        return onInstance
    return onDecorator

def Private(*attributes):
    return accessControl(failIf=(lambda attr: attr in attributes))

def Public(*attributes):
    return accessControl(failIf=(lambda attr: attr not in attributes))
```

At the interactive prompt, both decorators behave as advertised. Undeclared names can be read and changed from outside. Declared private names cannot:

```text
>>> from access2 import Private, Public
>>> @Private('age')  # Person = Private('age')(Person)
... class Person:  # Person = onInstance with state
...     def __init__(self, name, age):
...         self.name = name
...         self.age = age  # Inside accesses run normally
>>> X = Person('Pat', 40)
>>> X.name  # Outside accesses validated
'Pat'
>>> X.name = 'Sue'
>>> X.name
'Sue'
>>> X.age
TypeError: private attribute fetch, age
>>> X.age = 'Bob'
TypeError: private attribute change, age
>>> @Public('name')
... class Person:
...     def __init__(self, name, age):
...         self.name = name
...         self.age = age
>>> X = Person('Pat', 40)  # X is an onInstance
>>> X.name  # onInstance embeds Person
'Pat'
>>> X.name = 'Sue'
>>> X.name
'Sue'
>>> X.age
TypeError: private attribute fetch, age
>>> X.age = 'Bob'
TypeError: private attribute change, age
```

#### Implementation details

The `__X` pseudoprivate name mangling feature keeps the wrapped attribute inside the proxy class. Python prefixes the name with the class name, so the attribute becomes `_onInstance__wrapped`. That avoids a clash with a `wrapped` attribute in the real class. Mangling is not true privacy, though. The mangled name is still visible to anyone who uses it. The `__setattr__` method must test for the expanded name string.

Privacy can be broken on purpose. You can fetch the proxy's inner object by its full mangled name, such as `bob._onInstance__wrapped.pay`. This is true in other languages too. Access controls prevent accidents, but they cannot stop a determined programmer. Python is about enabling, not controlling. Use privacy sparingly, if at all.

#### Decorator trade-offs

You could get the same results with helper functions or by rebinding names by hand. The decorator syntax keeps that work consistent and obvious. The main costs of any wrapper-based approach are an extra call per attribute access, and instances that are not really instances of the original class. A check with `X.__class__` or `isinstance(X, C)` reveals the wrapper class.

Unless your program inspects types, the type issue rarely matters. The extra call matters mostly during development. Later in this section you will see a way to remove decorations automatically with the `-O` flag.

#### Delegating built-in operations

Explicit attribute fetches work for the decorators so far. Operator overloading is weaker. Built-in operations such as `print` and `+` skip instance-level lookup. They search the class namespace directly, so a proxy's `__getattr__` never sees them.

A simple class shows normal behavior:

```text
>>> class Tally:
...     def __init__(self):
...         self.sum = 0
...     def __str__(self):
...         return f'Tally: {self.sum}'
...     def __add__(self, add):
...         self.sum += add
>>> X = Tally()
>>> X.sum  # All attributes accessible
0
>>> print(X)  # Same as X.__str__() {sort of}
Tally: 0
>>> X + 5  # Same as X.__add__(5) {ditto}
>>> print(X)
Tally: 5
```

Wrapped in the private proxy, the built-ins break:

```text
>>> from access2 import Private
>>> @Private('sum', '__add__')
... class Tally:
...     # same as before
>>> X = Tally()
>>> X.sum
TypeError: private attribute fetch, sum
>>> X.__add__(5)
TypeError: private attribute fetch, __add__
>>> print(X)
<access2.accessControl.<locals>.onDecorator.<locals>.onInstance object at 0x...etc...>
>>> X + 5
TypeError: unsupported operand type(s) for +: 'onInstance' and 'int'
```

The explicit fetches of `sum` and `__add__` are blocked, as they should be. The implicit `print` and `+` are not caught, so they never reach the wrapped `Tally`. The `print` works only because `object` prints the proxy itself. That is an inconsistency in Python's model.

There are several workarounds. The simplest is to define each operator method on the proxy class. Each one forwards the operation to the wrapped object:

```python
"Inline methods, skip validations"
def accessControl(failIf):
    def onDecorator(aClass):
        class onInstance:
            def __init__(self, *args, **kargs):
                self.__wrapped = aClass(*args, **kargs)
            # Intercept and delegate built-in implicit access specifically
            def __add__(self, other):
                return self.__wrapped + other  # Or getattr(), __getattr__()
            def __str__(self):
                return str(self.__wrapped)  # Or self.__wrapped.__str__()
            def __getitem__(self, index):
                return self.__wrapped[index]
            def __call__(self, *args, **kargs):
                return self.__wrapped(*args, **kargs)
            # Plus any others needed
            # Intercept and delegate explicit attribute access generically
            def __getattr__(self, attr):
                ...  # same as in access2.py
            def __setattr__(self, attr, value):
                ...  # same as in access2.py
        return onInstance
    return onDecorator
```

This works because built-ins find the methods on the proxy class. The new methods call the wrapped object directly, so they skip the access checks in `__getattr__`. That may or may not be what you want. The code is repetitive, though a tool or a shared superclass can generate it.

A common superclass can hold the operator methods instead:

```python
"Inherit methods, skip validations"
class BuiltinsMixin:
    def __add__(self, other):
        return self._wrapped + other  # Assume a _wrapped
    def __str__(self):  # Bypass __getattr__
        return str(self._wrapped)
    def __getitem__(self, index):
        return self._wrapped[index]
    def __call__(self, *args, **kargs):
        return self._wrapped(*args, **kargs)
    # Plus any others needed

def accessControl(failIf):
    def onDecorator(aClass):
        class onInstance(BuiltinsMixin):
            ...  # rest same, but use unmangled _wrapped instead of __wrapped
        return onInstance
    return onDecorator
```

This route requires a `_wrapped` attribute in the proxy. That name can clash with the wrapped class, and it creates a dependency on the subclass. It is still better than the mangled `_onInstance__wrapped` name.

A third mixin sends each operator through `__getattr__`, so the access checks still apply:

```python
"Inherit methods, run validations"
class BuiltinsMixin:
    def __add__(self, other):
        return self.__getattr__('__add__')(other)  # Route to validator
    def __str__(self):  # Finish operations
        return self.__getattr__('__str__')()
    def __getitem__(self, index):
        return self.__getattr__('__getitem__')(index)
    def __call__(self, *args, **kargs):
        return self.__getattr__('__call__')(*args, **kargs)
    # Plus any others needed

def accessControl(failIf):
    def onDecorator(aClass):
        class onInstance(BuiltinsMixin):  # Inherit methods
            ...  # rest unchanged
        return onInstance
    return onDecorator
```

Here the operator names must be non-private or public under the decorator's arguments, or they will not run. Built-ins then get the same checks as explicit names.

The most concise option uses class-level descriptors. Each descriptor intercepts only the attribute fetch that comes before the operation, and it routes that fetch through `__getattr__`:

```python
"Inherit descriptors, run validations"
class BuiltinsMixin:
    class ProxyDesc:  # Define descriptor
        def __init__(self, attrname):
            self.attrname = attrname
        def __get__(self, instance, owner):
            return instance.__getattr__(self.attrname)  # Run validations

    builtins = ['add', 'str', 'getitem', 'call']  # Plus any others
    for attr in builtins:
        exec(f'__{attr}__ = ProxyDesc("__{attr}__")')  # Make descriptors

def accessControl(failIf):
    def onDecorator(aClass):
        class onInstance(BuiltinsMixin):  # Inherit descriptors
            ...  # rest unchanged
        return onInstance
    return onDecorator
```

The `exec` call runs a string of code inside the class body, as if the string were written there. The loop therefore creates `__add__`, `__str__` and the other names as descriptors. This coding is the most compact, but it is also the most implicit. Read it slowly. A simpler model of the same idea looks like this:

```python
class B:
    class D:
        def __get__(s, i, o): return i.meth()
    name = D()

class A(B):
    def meth(self): return 'hack'

I = A()
I.name  # 'hack'
```

With the descriptor approach, the decorator works as intended for the Tally class. Public built-ins are delegated, and private built-ins are blocked:

```text
>>> from access_builtins_mixin_desc import Private
>>> @Private('sum')
... class Tally:
...     def __init__(self):
...         self.sum = 0
...     def __str__(self):
...         return f'Tally: {self.sum}'
...     def __add__(self, add):
...         self.sum += add
>>> X = Tally()
>>> X.sum  # Explicit validated
TypeError: private attribute fetch, sum
>>> X + 10  # Built-in delegated
>>> print(X)  # Built-in delegated
Tally: 10
```

```text
>>> @Private('sum', '__add__')
... class Tally:
...     # same as before
>>> X = Tally()
>>> X.sum  # Explicit validated
TypeError: private attribute fetch, sum
>>> X + 10  # Built-in canceled: private
TypeError: private attribute fetch, __add__
>>> print(X)  # Built-in allowed: public
Tally: 0
>>> @Private('__str__')
... class Tally:
...     # same as before
>>> print(Tally())  # Built-in canceled: private
TypeError: private attribute fetch, __str__
```

## Validating function arguments

Decorators can also check arguments before a function runs. This case study builds a function decorator that tests whether arguments are inside a valid numeric range. It can run during development or in production. You can use it as a template for similar checks, such as argument type tests.

### The goal

In the object-oriented material earlier, a class gave a raise based on a percentage:

```python
class Person:
    ...
    def giveRaise(self, percent):
        self.pay = int(self.pay * (1 + percent))
```

The percentage should be between 0.0 and 1.0. You can check that with an inline `if` or with an `assert`:

```python
class Person:
    def giveRaise(self, percent):  # Validate with inline code
        if percent < 0.0 or percent > 1.0:
            raise TypeError('percent invalid')
        self.pay = int(self.pay * (1 + percent))

class Person:  # Validate with asserts
    def giveRaise(self, percent):
        assert percent >= 0.0 and percent <= 1.0, 'percent invalid'
        self.pay = int(self.pay * (1 + percent))
```

These checks clutter the method, and they are often useful only during development. Complex checks become tedious to inline. If the rule changes, you must find and update every copy. A general decorator solves these problems. You write the rule once, and each method declares the ranges it needs:

```python
class Person:
    @rangetest(percent=(0.0, 1.0))  # Use decorator to validate
    def giveRaise(self, percent):
        self.pay = int(self.pay * (1 + percent))
```

Isolating the validation in a decorator simplifies both the client code and future maintenance. This differs from the attribute validation in the previous section. Here the function's argument values are checked when the call happens. Introspection makes this new task just as easy to code.

### A basic range-testing decorator for positional arguments

Start with a simple version. It handles only positional arguments that always appear in the same position. Keyword names are not supported, because they could break the positions declared in the decorator:

```python
def rangetest(*argchecks):  # Validate positional arg ranges
    def onDecorator(func):
        if not __debug__:  # True if "python -O main.py args..."
            return func  # No-op: call original directly
        else:  # Else wrapper while debugging
            def onCall(*args):
                for (ix, low, high) in argchecks:
                    if args[ix] < low or args[ix] > high:
                        errmsg = f'Argument {ix} not in {low}..{high}'
                        raise TypeError(errmsg)
                return func(*args)
            return onCall
    return onDecorator
```

This code reuses the patterns from earlier: decorator arguments, enclosing scopes for state, and nested `def` statements so it works for methods too. In a method, `onCall` receives the instance in the first item of `*args`. The argument numbers in the decorator therefore start at 1 for methods, to account for `self`.

The code also uses the `__debug__` built-in variable. Python sets it to `True` unless you run with the `-O` flag, as in `python -O main.py`. When `__debug__` is `False`, the decorator returns the original function unchanged. That removes the wrapper and its cost. You do not have to delete the decoration lines to get that result.

Here is how the first version is used:

```python
from rangetest0 import rangetest
print(f'{__debug__=}')  # False if "python -O main.py"

@rangetest((1, 0, 120))  # persinfo = rangetest(...)(persinfo)
def persinfo(name, age):  # age must be in 0..120
    print(f'{name} is {age} years old')

@rangetest([0, 1, 12], [1, 1, 31], [2, 0, 2024])
def birthday(M, D, Y):
    print(f'birthday = {M}/{D}/{Y}')

class Person:
    def __init__(self, name, job, pay):
        self.job = job
        self.pay = pay
    @rangetest([1, 0.0, 1.0])  # giveRaise = rangetest(...)(giveRaise)
    def giveRaise(self, percent):  # Arg 0 is the self instance here
        self.pay = int(self.pay * (1 + percent))

# Comment lines raise TypeError unless "python -O" used on shell command line
persinfo('Bob Smith', 45)  # Really runs onCall(...) with state
#persinfo('Bob Smith', 200)  # Or persinfo if -O cmd line argument
birthday(8, 31, 2024)
#birthday(8, 32, 2024)
sue = Person('Sue Jones', 'dev', 100_000)
sue.giveRaise(.10)  # Really runs onCall(self, .10)
print(sue.pay)  # Or giveRaise(self, .10) if -O
#sue.giveRaise(1.10)
```

Valid calls print normally:

```text
$ python3 rangetest0_test.py
__debug__=True
Bob Smith is 45 years old
birthday = 8/31/2024
110000
```

Uncommenting an invalid call raises a `TypeError`. The message below is shortened:

```text
$ python3 rangetest0_test.py
__debug__=True
Bob Smith is 45 years old
birthday = 8/31/2024
110000
TypeError: Argument 1 not in 0.0..1.0
```

Running Python with the `-O` flag disables the range tests. It also removes the wrapping cost, so the original function runs directly. Assuming the checks are for debugging, that flag lets you ship a faster program. Here the last line still runs, with a print that shows the raise:

```text
$ python3 -O rangetest0_test.py
__debug__=False
Bob Smith is 45 years old
birthday = 8/31/2024
110000
231000
```

### Generalizing for keywords and defaults

The first version handles only positional arguments. It ignores keyword arguments, and it does not know about defaults that a call may omit. That is fine for simple cases, but a general tool needs more.

The next version matches the decorated function's expected arguments against the actual call. It validates arguments passed by position or by keyword name. It skips any default argument that the call omits:

```python
"""
A function decorator that performs range-test validation for
arguments passed to any function or method. Usage synopsis:
@rangetest(percent=(0.0, 1.0), month=(1, 12))
def func-or-method(..., percent, ..., month=5, ...):
    ...
func-or-method(..., value, month=8, ...)
Arguments are specified by keyword to the decorator. In the actual
call, arguments may be passed by position or keyword, and defaults
may be omitted. See rangetest_test.py for example use cases.
"""

trace = True

def rangetest(**argchecks):  # Validate ranges for both+defaults
    def onDecorator(func):  # onCall remembers func and argchecks
        if not __debug__:  # True if "python -O main.py args..."
            return func  # Wrap if debugging; else use original
        else:
            funcname = func.__name__
            funccode = func.__code__
            funcargs = funccode.co_varnames[:funccode.co_argcount]
            def onCall(*pargs, **kargs):
                # All pargs match first N expected args by position
                # The rest must be in kargs or be omitted defaults
                positionals = funcargs[:len(pargs)]
                errormsg = lambda *args: '%s argument "%s" not in %s..%s' % args
                for (argname, (low, high)) in argchecks.items():
                    # For all args to be checked
                    if argname in kargs:
                        # Was passed by name
                        if kargs[argname] < low or kargs[argname] > high:
                            raise TypeError(errormsg(funcname, argname, low, high))
                    elif argname in positionals:
                        # Was passed by position
                        position = positionals.index(argname)
                        if pargs[position] < low or pargs[position] > high:
                            raise TypeError(errormsg(funcname, argname, low, high))
                    else:
                        # Assume not passed: default
                        if trace:
                            print(f'-Argument "{argname}" defaulted')
                return func(*pargs, **kargs)  # OK: run original call
            return onCall
    return onDecorator
```

The test script shows the new decorator in use. Decorator arguments name the checked parameters. At each call you can pass arguments by name or by position, and you can omit defaults that are not checked:

```python
"""
Test the rangetest decorator (usage differs from rangetest0).
Comment lines raise TypeError unless "python -O" or similar in compileall.
"""
from rangetest import rangetest

def announce(what): print(what.center(24, '-'))  # str method

# Test functions, positional and keyword
announce('Functions')
@rangetest(age=(0, 120))  # persinfo = rangetest(...)(persinfo)
def persinfo(name, age):
    print(f'{name} is {age} years old')

@rangetest(M=(1, 12), D=(1, 31), Y=(0, 2024))
def birthday(M, D, Y):
    print(f'birthday = {M}/{D}/{Y}')

persinfo('Pat', 40)
persinfo(age=40, name='Pat')
birthday(8, D=31, Y=2024)
#persinfo('Pat', 150)
#persinfo(age=150, name='Pat')
#birthday(8, Y=2025, D=40)

# Test methods, positional and keyword
announce('Methods')
class Person:
    def __init__(self, name, job, pay):
        self.job = job
        self.pay = pay
    # giveRaise = rangetest(...)(giveRaise)
    @rangetest(percent=(0.0, 1.0))  # percent passed by name or position
    def giveRaise(self, percent):
        self.pay = int(self.pay * (1 + percent))

sue = Person('Sue Jones', 'dev', 100_000)
bob = Person('Bob Smith', 'dev', 100_000)
sue.giveRaise(percent=.20)
bob.giveRaise(.10)
print(f'sue=>{sue.pay}, bob=>{bob.pay}')
#sue.giveRaise(1.20)
#bob.giveRaise(percent=1.20)

# Test omitted defaults: skipped
announce('Defaults')
@rangetest(a=(1, 10), b=(1, 10), c=(1, 10), d=(1, 10))
def omitargs(a, b=7, c=8, d=9):
    print(a, b, c, d)

omitargs(1, 2, 3, 4)  # Positionals
omitargs(1, 2, 3)  # Default d
omitargs(1, 2, 3, d=4)  # Keyword d
omitargs(1, d=4)  # Default b and c
omitargs(d=4, a=1)  # Ditto
omitargs(1, b=2, d=4)  # Default c
omitargs(d=8, c=7, a=1)  # Default b
#omitargs(1, 2, 3, 11)  # Bad d
#omitargs(1, 2, 11)  # Bad c
#omitargs(1, 2, 3, d=11)  # Bad d
#omitargs(11, d=4)  # Bad a
#omitargs(d=4, a=11)  # Bad a
#omitargs(1, b=11, d=4)  # Bad b
#omitargs(d=8, c=7, a=11)  # Bad a
```

Out-of-range values raise an exception, whether they are passed by name or by position. Omitted defaults are not checked. The output shows which defaults were used:

```text
$ python3 rangetest_test.py
-------Functions--------
Pat is 40 years old
Pat is 40 years old
birthday = 8/31/2024
--------Methods---------
sue=>120000, bob=>110000
--------Defaults--------
1 2 3 4
-Argument "d" defaulted
1 2 3 9
1 2 3 4
-Argument "b" defaulted
-Argument "c" defaulted
1 7 8 4
-Argument "b" defaulted
-Argument "c" defaulted
1 7 8 4
-Argument "c" defaulted
1 2 8 4
-Argument "b" defaulted
1 7 7 8
```

The checks run in the order listed in the decorator, because dictionaries keep insertion order. Uncommenting a method line shows the failure:

```text
$ python3 rangetest_test.py
-------Functions--------
Pat is 40 years old
Pat is 40 years old
birthday = 8/31/2024
--------Methods---------
sue=>120000, bob=>110000
TypeError: giveRaise argument "percent" not in 0.0..1.0
$ python3 -O rangetest_test.py
...no error messages or default traces...
```

#### Implementation details

This decorator relies on introspection and on rules of argument passing. Mimicking all of Python's argument matching would be too complex and fragile. A better plan matches the decorator's names against the function's expected names.

Function introspection gives the expected names. The names of the first N local variables on a function's code object are its arguments:

```text
>>> def func(a, b, c, e=True, f=None):  # Args: three required, two defaults
...     x = 1  # Plus two more local variables
...     y = 2
>>> code = func.__code__  # Code object of function object
>>> code.co_nlocals
7
>>> code.co_varnames  # All local variable names
('a', 'b', 'c', 'e', 'f', 'x', 'y')
>>> code.co_varnames[:code.co_argcount]  # <== First N locals are expected args
('a', 'b', 'c', 'e', 'f')
```

Starred names in the wrapper collect any number of arguments. Those are compared with the expected names:

```text
>>> def catcher(*pargs, **kargs): print(f'{pargs}, {kargs}')
>>> catcher(1, 2, 3, 4, 5)
(1, 2, 3, 4, 5), {}
>>> catcher(1, 2, c=3, d=4, e=5)  # Arguments at calls
(1, 2), {'d': 4, 'e': 5, 'c': 3}
```

The matching depends on two rules from Python's argument passing. At a call, positional arguments come before keyword arguments. In a `def`, nondefault arguments come before default arguments. Positional values fill names from left to right, and keywords match by name. Each argument can receive only one value.

The decorator also assumes that the call is valid. If it is not, Python will raise an error when the call finally runs. That is acceptable, because checking validity in advance would mean copying Python's full matching algorithm.

The matching algorithm uses those rules. Let N be the number of positional arguments in `*pargs`. The first N expected names are the ones passed by position. Any other expected name was either passed by keyword or left at its default. For each checked name, the decorator looks in three places. If the name is in `**kargs`, its value is there. If the name is among the first N expected names, its value is in `*pargs` at that position. Otherwise the argument was defaulted, so it needs no check.

#### Open issues

The range tester works as planned, but three caveats remain. It does not detect invalid calls, it does not handle every arbitrary-argument signature, and it does not fully support nesting.

Invalid calls still fail, but only when the wrapper calls the original function. For example, both of these calls are missing the required argument `a`:

```python
omitargs()
omitargs(d=8, c=7, b=6)
```

Trying to catch these earlier would mean imitating Python's argument matching. Letting Python report the error at the call is simpler.

The decorator also does not handle starred names in the definition, such as `*pargs` and `**kargs`. Extra keyword arguments with a name can be tested if the decorator mentions that name. Extra positional arguments cannot be named, so they are skipped. Starred names are locals, but they are not expected arguments:

```text
>>> def func(*pargs, **kargs): pass
>>> code = func.__code__
>>> code.co_nlocals, code.co_varnames
(2, ('pargs', 'kargs'))
>>> code.co_argcount, code.co_varnames[:code.co_argcount]
(0, ())
>>> def func(a, b, *pargs, **kargs): pass
>>> code = func.__code__
>>> code.co_argcount, code.co_varnames[:code.co_argcount]
(2, ('a', 'b'))
```

Starred names in a call are flattened before the function starts, so the decorator never sees them. Nesting is the last caveat. The decorator analyzes names from the function's definition. A nested wrapper has its own call signature, so the names no longer match. In nested use, only the innermost validation runs in full. The outer levels can check only keyword arguments. Proxies change the signatures, so positional checks get lost.

### Decorator arguments versus function annotations

Python's annotations offer another way to state range limits. An annotation is an expression written in the `def` header. Python stores annotations in a dictionary on the function. You could write the limits in the header instead of in decorator arguments:

```python
@rangetest(a=(1, 5), c=(0.0, 1.0))
def func(a, b, c):  # func = rangetest(...)(func)
    print(a + b + c)
```

```python
@rangetest
def func(a:(1, 5), b, c:(0.0, 1.0)):
    print(a + b + c)
```

The annotation version still needs a decorator to wrap the function. It also needs one less level of nesting, because it does not keep decorator arguments as state. Both versions can be seen in this skeleton:

```python
# Using decorator arguments
def rangetest(**argchecks):
    def onDecorator(func):
        def onCall(*pargs, **kargs):
            print(argchecks)
            for check in argchecks:
                pass  # Add validation code here
            return func(*pargs, **kargs)
        return onCall
    return onDecorator

@rangetest(a=(1, 5), c=(0.0, 1.0))
def func(a, b, c):  # func = rangetest(...)(func)
    print(a + b + c)

func(1, 2, c=3)  # Runs onCall, argchecks in scope

# Using function annotations
def rangetest(func):
    def onCall(*pargs, **kargs):
        argchecks = func.__annotations__
        print(argchecks)
        for check in argchecks:
            pass  # Add validation code here
        return func(*pargs, **kargs)
    return onCall

@rangetest
def func(a:(1, 5), b, c:(0.0, 1.0)):  # func = rangetest(func)
    print(a + b + c)

func(1, 2, c=3)  # Runs onCall, annotations on func
```

Both forms see the same test information. The decorator-argument version keeps it in an enclosing scope, and the annotation version keeps it on the function as an attribute:

```text
$ python3 decoargs-vs-annotation.py
{'a': (1, 5), 'c': (0.0, 1.0)}
6
{'a': (1, 5), 'c': (0.0, 1.0)}
6
```

Annotations limit the utility of the tool. Each parameter can carry only one annotation expression, so the function is committed to a single role. Range checks would block other uses, such as type hints. Decorator arguments stay outside the function. They are easier to remove, and nested decorators can apply several steps to one function. The function itself keeps a normal appearance.

If you have a single purpose in mind, the choice is largely a matter of style. One programmer's decoration may be another's syntactic clutter.

## Decorators summary

Decorators insert code that runs when a function or class is defined. When a decorator is used, Python rebinds the name to the callable that the decorator returns. That hook lets you manage functions and classes themselves, or the calls and instances that come later. Wrapper logic catches the later calls, so you can augment both function calls and instance interfaces. Decorators give you an explicit and uniform way to do this.

Class decorators can also manage classes rather than only their instances. Decorator state can live in closures, class attributes or function attributes. Each choice has a cost, so pick the one that fits the job.

## Checkpoint questions

<details>
<summary>Five questions to review unicode and byte strings</summary>

1. What are the names and roles of Python's three string types?
2. How can you code a non-ASCII character in a `str`, and what does each escape give?
3. What is the main difference between text-mode and binary-mode files?
4. How would you read a text file that uses an encoding other than your platform default?
5. What do a BOM and Unicode normalization mean, and when do they matter?

</details>

<details>
<summary>Five questions to review managed attributes</summary>

1. How does a `property` differ from a descriptor, and what extra things can a descriptor do?
2. Why does a descriptor need a `__set__` method to make an attribute read-only?
3. What do the `self`, `instance` and `owner` arguments of a descriptor's `__get__` method give you?
4. How do `__getattr__` and `__getattribute__` differ in which fetches they intercept?
5. Why must an attribute interception method avoid fetching `self` attributes inside itself, and how do you avoid the loop?

</details>

<details>
<summary>Five questions to review decorators</summary>

1. What two steps does `@decorator` above a `def` perform, and what does `F = decorator(F)` show?
2. Why does a class-based decorator fail on methods, and what does a nested function change?
3. How would you rewrite the timer decorator so it works on both functions and methods?
4. How would you make a `Private` class decorator skip all wrapping when Python runs with `-O`?
5. How would you generalize the range tester so one code base handles several kinds of argument checks?

</details>

## Sources and review notes

- Source: *Learning Python*, 6th edition (`learning-python-6th-edition`). Chapters used are listed in each section.
- Source: *Learning Python*, 6th edition (`learning-python-6th-edition`), Chapter 34, "Exception Coding Details". Used for the `try`, `raise`, `assert` and `with` sections.
- Source: *Learning Python*, 6th edition (`learning-python-6th-edition`), Chapter 35, "Exception Objects". Used for the exception objects, built-in exception classes, custom displays and state, and exception groups sections.
- Source: *Learning Python*, 6th edition (`learning-python-6th-edition`), Chapter 37, "Unicode and Byte Strings". Used for the Unicode and byte strings, encodings, text and binary files, Unicode tools, defaults, BOM and normalization sections.
- Source: *Learning Python*, 6th edition (`learning-python-6th-edition`), Chapter 38, "Managed Attributes". Used for the managed attributes, properties, descriptors, `__getattr__` and `__getattribute__`, and attribute validation sections.
- Source: *Learning Python*, 6th edition (`learning-python-6th-edition`), Chapter 39, "Decorators". Used for the decorator basics, function and class decorators, decorator nesting and arguments, state retention, method decoration, timing, singleton, interface tracing, private and public attributes, built-in delegation and argument validation sections.
