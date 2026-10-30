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

## Sources and review notes

- Source: *Learning Python*, 6th edition (`learning-python-6th-edition`). Chapters used are listed in each section.
- Source: *Learning Python*, 6th edition (`learning-python-6th-edition`), Chapter 34, "Exception Coding Details". Used for the `try`, `raise`, `assert` and `with` sections.
