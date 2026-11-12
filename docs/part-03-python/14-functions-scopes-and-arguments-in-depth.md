---
id: "c03-14"
title: "3.14 Functions, scopes and arguments in depth"
sidebar_label: "3.14 Functions, scopes and arguments in depth"
sidebar_position: 14
description: "Scopes and the LEGB rule, argument passing, advanced function topics, comprehensions and generator expressions, and how to benchmark alternatives."
status: "drafted"
tier: "2"
level: "I"
lab_venue: "Mac"
---

# 3.14 Functions, scopes and arguments in depth

Chapter 3.1 introduces functions in a hurry. This chapter slows down and walks the same ground properly: how names find their values, how arguments travel into a function, and what a closure really holds on to. You will meet all of it again whenever you read or write the Python behind schedulers, operators, exporters and training launchers.

## Python scope basics

### Names live in namespaces

Sooner or later you write a function, and a name inside it surprises you. It points at a value you did not expect, or it raises an error for something that looks defined. To read such code calmly, you need a clear idea of what a name means in Python. When your code uses a name, Python creates it, changes it, or looks it up in a namespace. A namespace is simply a place where names live. In relation to code, each namespace corresponds to a scope, which is the part of the program where a name is visible.

### Assignment decides the scope

Here is the sentence that unlocks most of this chapter: almost everything about names in Python happens at assignment time. A name springs into existence when you first assign it a value, and you must assign it before you use it. Python does not ask you to declare names ahead of time. The place where you assign a name in your source code decides which namespace it binds to, and so where it can be seen.

Functions add one more layer of namespaces. By default, every name assigned inside a function belongs to that function and no other. That gives you three practical rules:

- A name assigned inside a `def` can be seen only by the code inside that `def`. You cannot refer to it from outside the function.
- A name assigned inside a `def` does not clash with a variable of the same name outside it. A name `X` in another `def`, or at the top level of a module file, is a different variable.
- A name assigned in a `lambda` works the same way. Assignment inside a `lambda` is limited to its arguments and `:=` named assignments, and it is much less common than inside a `def`.

The scope of a variable depends only on where you assign it in the source code. Which function calls which has no effect on it at all. Python calls this lexical scoping, and that is good news: you can settle most scope questions by reading the code, without running it. A variable can be assigned in three places, and each place gives it a different scope:

- If a variable is assigned inside a `def` or `lambda`, it is local to that function.
- If a variable is assigned in an enclosing `def` or `lambda`, it is nonlocal to the functions nested inside it.
- If a variable is assigned outside all `def`s and `lambda`s, it is global to the whole file.

For example, this module file holds two different variables named `X`:

```python
X = 99 # Global (module) scope X
def func():
    X = 88 # Local (function) scope X: a different variable
```

Even though both names are `X`, their scopes keep them apart. This is the quiet service a function scope does for you. It prevents name clashes, and it makes each function more self-contained. Code inside it does not need to know about the names used elsewhere.

### Scopes overview

Before you wrote functions, none of your code sat inside a `def`. The names you used lived in a module, or they were built-ins such as `open` and `zip`. Code typed at the interactive prompt counts too. Technically, the prompt is a module named `__main__` that prints results and does not match a real file. In every other way it behaves like the top level of a module file.

Functions give you nested namespaces, so a name inside a function does not clash with a name in a module or in another function. Two kinds of scope matter here:

- Each module is a global scope. Variables assigned at the top level of a module live in its namespace. After an import, they become attributes of the module object, but inside the file you use them as plain variables.
- Each function call creates a new local scope. The names created inside the function live there, unless a `global` or `nonlocal` statement says otherwise.

The global scope spans a single file only. A name at the top level of one file is global only to code in that file. Python has no all-encompassing global scope for your own code. Names are split across modules, and you must import a module before you can use the names its file defines. A useful habit: when you hear "global" in Python, think "module."

Names assigned inside a function are local unless you declare them `global` or `nonlocal`. To change a name at the top level of the enclosing module, use a `global` statement inside the function. To change a name in an enclosing `def`, use a `nonlocal` statement. A `lambda` body holds only one expression, so these two statements belong to `def` alone.

Names that a function does not assign are looked up elsewhere. Python treats them as locals of a physically enclosing function, as globals of the enclosing module, or as built-ins. An enclosing scope can come from any `def` or `lambda` combination. One limit to remember: you cannot write a `def` inside a `lambda`.

Each call creates a new local scope. A `def` statement or a `lambda` expression defines a local scope, but the scope is really tied to each call of the function. That detail looks small now, and it matters a great deal for recursion and closures. Hold on to it.

Per-call scopes matter for recursion. Recursion is a technique where a function calls itself to loop, and each active call needs its own copy of the function's local variables. That is what makes recursion useful when you process a structure whose shape you cannot predict ahead of time. Closures need per-call scopes too, because each call gets a fresh set of locals that can remember state for later.

Three subtleties are worth knowing before you move on. First, code at the interactive prompt lives in a module and follows the normal scope rules, so names assigned there are global and visible across the whole session. Second, any kind of assignment decides whether a name is local or global, based on where the assignment appears. That includes `=` statements, `:=` expressions, `import` names, `def` names, function arguments, and names in a `class`. Third, changing an object in place does not make a name local. Only a real assignment does.

Here is the third point in action. Suppose `L` is a list at the top level of a module. A statement `L = X` inside a function makes `L` local to that function. But `L.append(X)` changes the list that `L` refers to, not the name `L` itself. So Python finds `L` in the global scope and changes it without a `global` declaration. Keep the difference clear: changing an object is not the same thing as assigning a name.

## Name resolution: the LEGB rule

Read any function and you will find three kinds of name: one that belongs to the call itself, one borrowed from the code around it, and one that Python simply provides. The LEGB rule is the order Python uses to tell them apart.

### The three rules inside a def

If the previous section sounds complicated, take heart. It comes down to three simple rules. Inside a `def`:

- Assigning a name creates or changes a local name by default.
- Referencing a name searches at most four scopes: local, then enclosing functions, then global, then built-in.
- Names declared in `global` and `nonlocal` statements map assignments to the module scope and the enclosing function scope, respectively.

The same rules apply to `lambda`, except for the last one, because a `lambda` cannot contain statements.

Functions can use names assigned in enclosing functions and in the global scope. To change those names, however, a function must declare them as `nonlocal` or `global`. Reading is free, writing needs a declaration.

Python calls this lookup order the LEGB rule, after the four scopes it searches:

- L is the local scope of the function itself.
- E is the local scopes of any enclosing `def`s and `lambda`s.
- G is the global scope of the surrounding module.
- B is the built-in scope.

When you use an unqualified name inside a function, Python checks these scopes in order and stops at the first match. If the name is not found anywhere, Python reports an error. When you assign a name inside a function, Python creates or changes it in the local scope, unless the name is declared `global` or `nonlocal`. When you assign a name at the top level of a module or at the interactive prompt, the local and global scopes are the same module namespace. That single fact explains many odd-looking results.

Because names must be assigned before they are used, there are no hidden steps in this model. Assignments always determine scopes. The E layer can hold more than one level, and it comes into play only when you nest functions. The `nonlocal` statement is what lets you change names in that layer.

> Note: this lookup rule was once called the "LGB rule". The E layer was added later, so that you did not have to pass enclosing names in with default arguments. Because `nonlocal` now handles that layer, the rule might have been named "LNGB," but backward compatibility matters. The acronym also ignores the newer comprehension and exception scopes, though acronyms longer than four letters tend to defeat their purpose.

These rules apply only to simple names, such as `name`. Qualified attribute names, such as `object.name`, follow a different lookup. Those names search objects, not scopes, and they can involve inheritance in object-oriented code. Keep the two ideas apart and most of the confusion goes away.

### Other short-lived scopes

Three more scopes exist in Python, and they matter less at this stage. They cover loop variables in comprehensions, exception variables in `try` handlers, and the bodies of `class` statements. Most statement blocks do not localize the names they use. A loop variable in a `for` statement, for example, stays visible after the loop ends. The `:=` operator also follows the normal scope rules.

Comprehension loop variables are the first special case. In `[X for X in I]`, the variable `X` refers to the current item. It is local to the expression itself in every comprehension form: list, dictionary, set, and generator. A `for` statement does not do this for its loop variable, even though the syntax looks similar. Names assigned with `:=` inside a comprehension do leak out to the enclosing scope.

Exception variables are the second case. In `except E as X`, the variable `X` refers to the raised exception. It is local to that `except` block, and Python removes it from the containing scope when the block exits. Even if you used the name earlier in your code, it is removed. This design avoids keeping the exception alive, which could delay memory recovery.

Named assignments in a `lambda` are the third case. In `X := Y` inside a `lambda`, the name `X` works much like an unnested `=` statement. A `lambda` creates a new local scope, just like a `def`. Any name assigned with `:=` inside it can be used only within the `lambda` body and is not available outside it. This pattern is rare and adds complexity, so most code will never need it.

Most of these contexts augment the LEGB rule instead of replacing it. A comprehension's loop variable is bound to one more nested, special-case local scope. Every other name in the expression follows the usual LEGB lookup.

A `class` statement also creates a local scope for the names assigned at the top level of its block. Those names do not clash with names elsewhere, and the `class` block acts as the L level of the lookup. After the `class` statement ends, these names become attributes of the class object. Unlike a function, a class does not create new names on each call. Calling a class creates instances, which inherit the names assigned in the class and keep per-object state as their own attributes.

Python uses LEGB to resolve names in a class body and in the methods nested inside it. There is one twist worth remembering. Class scopes are skipped when a method looks up a name, so Python searches enclosing functions but not enclosing classes. Names in a class must be fetched as object attributes, so the LEGB picture still applies to object-oriented code.

## Scope examples

### A module with one function

Let us watch the rules work on a small file. Suppose you save this code in a module file named `scopes101.py`:

```python
# Global scope
X = 99 # X and func assigned in module: global
def func(Y): # Y and Z assigned in function: locals
    # Local scope
    Z = X + Y # X is a global when referenced here
    return Z
func(1) # func in module: result=100 (not printed)
```

To see the result, import the module and call its function. The `func` name is a module attribute once another file imports it. Run this from the same folder as the file so the import works:

```
>>> import scopes101
>>> scopes101.func(1)
100
```

The module and its function use several names. Python's scope rules classify them as follows, and it is worth reading the list slowly.

Global names are `X` and `func`. `X` is global because it is assigned at the top level of the module file. The function can refer to it as a simple name without declaring it `global`. `func` is global for the same reason, since the `def` statement assigns a function object to that name at the top level.

Local names are `Y` and `Z`. Both are assigned while the function runs. `Z` is assigned by the `=` statement, and `Y` is assigned because arguments are always passed by assignment. Both exist only during a call to the function.

The reason for this separation is simple. Local variables are temporary names you need only while a function runs. The argument `Y` and the result `Z` exist only inside the function, so they do not disturb the module's namespace or any other function. When the call exits, its local variables are removed from memory. Objects they refer to can then be garbage-collected, if nothing else refers to them. This step happens automatically, and it keeps memory use low.

Local names also make functions easier to read and debug. Most names a function uses appear in the function itself, not in some distant part of the module. And no remote function can change a local name by accident. In the code below, neither `X` can be changed or even seen from the other function:

```python
def func1():
    X = 'hack' # This X...
    def func2():
        X = 'code' # ...is not the same as this X
```

This keeps each function a self-contained unit of software, which is the goal you are aiming at.

### The built-in scope

The built-in scope sounds abstract, but it is simpler than it seems. It is really a built-in module named `builtins`. You have to import `builtins` to inspect it, because the name `builtins` is not itself a built-in name. Run `dir` on it to see which names are predefined. The list can vary between Python versions, so check it on your own machine:

```
>>> import builtins
>>> dir(builtins)
['ArithmeticError', 'AssertionError', 'AttributeError', 'BaseException',
'BaseExceptionGroup', 'BlockingIOError', 'BrokenPipeError', 'BufferError',
…many more names omitted: 158 total in 3.12…
'ord', 'pow', 'print', 'property', 'quit', 'range', 'repr', 'reversed',
'round', 'set', 'setattr', 'slice', 'sorted', 'staticmethod', 'str', 'sum',
'super', 'tuple', 'type', 'vars', 'zip']
```

These names form the built-in scope. Roughly the first half are built-in exceptions, and the second half are built-in functions. The list also includes `None`, `True`, `False`, and `Ellipsis`. Python searches this module last in the LEGB lookup, so you can use these names without any import.

There are two ways to reach a built-in function. You can rely on the LEGB rule, or you can import `builtins` and use the name directly. The second way takes more typing, but it is useful for customizations, which the section on customizing `open` covers:

```
>>> zip # The normal way, per LEGB's B
<class 'zip'>
>>> import builtins # The hard way: for customizations
>>> builtins.zip
<class 'zip'>
>>> zip is builtins.zip # Same object, different lookup routes
True
```

Python's `__builtins__` name is also preset in most global scopes, including the interactive session. It refers to the `builtins` module, so you can often use `__builtins__` without an import. You cannot import `__builtins__` itself, though, because it is a preset variable and not a module name. After you import `builtins`, `builtins is __builtins__` is `True`. For real work and customization, use `builtins`.

### Redefining built-in names

Because the LEGB lookup takes the first match it finds, local names can hide names with the same spelling in the global and built-in scopes. Global names can hide built-ins too. A function can create a local variable called `open` simply by assigning to it:

```python
def hider():
    open = 'text' # Local variable, hides built-in here (L before B)
    ...
    open('data.txt') # Error: this no longer opens files in this scope!
```

Inside the function, the local `open` hides the built-in `open`. The name now refers to a string, not the file opener. This is sometimes called shadowing a built-in. It is harmless if you never open a file in that function. It causes an error the moment you try.

The same thing can happen at the interactive prompt, which acts as a global scope:

```
>>> open = 99 # Assign in global scope, hides built-in here too
```

There is nothing wrong with using a built-in name for your own variable, as long as you do not need the original in that scope. If these names were off limits, you would have to memorize the whole list and treat every name as reserved. In Python 3.12, the `builtins` module has 158 names, and 150 of them do not start with double underscores:

```
>>> len(dir(builtins)), len([x for x in dir(builtins) if not x.startswith('__')])
(158, 150)
```

Sometimes you really do want to replace a built-in name, such as writing a custom `open` that adds access checks. The `None`, `True`, and `False` names are the exception. They are treated as reserved words now, so you can no longer reassign them. All other built-in names are fair game.

Still, redefining a built-in name is often a bug, and a difficult one to find later. Python does not warn you when you do it. Some tools can flag such mistakes, but your best defense is knowledge. Do not redefine a built-in name you need. If you do it by accident at the interactive prompt, restart the session, or run a `del name` statement to remove the redefinition. Then the original built-in is restored, exactly as the LEGB rule expects.

Functions can also hide global variables of the same name with locals. This is much of the point of local scopes. Because local names minimize clashes, your functions become self-contained namespaces:

```python
X = 88 # Global X
def func():
    X = 99 # Local X: hides global, but we want this here
func()
print(X) # Prints 88: unchanged
```

The assignment inside the function creates a local `X`, which is a different variable from the global `X`. As a result, you cannot change a name outside a function unless the `def` includes a `global` or `nonlocal` declaration. The next section covers the `global` statement.

### The global statement

The `global` and `nonlocal` statements are the only declaration statements in Python that the language itself uses. They are not type or size declarations. They are namespace declarations. A `global` statement tells Python that a function plans to change one or more global names, which are names in the enclosing module's scope.

Here is a short summary of how globals behave:

- Global names are variables assigned at the top level of the enclosing module file.
- Global names must be declared only if they are assigned inside a function.
- Global names can be referenced inside a function without a declaration, under the LEGB rule.

The `global` statement works only inside `def`, not `lambda`. It consists of the word `global` followed by one or more names separated by commas. Each listed name maps to the module's scope when the function assigns or references it. The following example is a variation on the earlier one:

```python
X = 88 # Global X
def func():
    global X
    X = 99 # Global X: outside def
func()
print(X) # Prints 99
```

Because of the `global` declaration, the `X` inside the function refers to the `X` outside it. They are the same variable, so changing one changes the other. Here is a slightly larger example:

```python
y, z = 1, 2 # Global variables in module
def all_global():
    global x # Declare globals assigned
    x = y + z # No need to declare y or z: LEGB rule
```

Here `x`, `y`, and `z` are all globals inside `all_global`. `y` and `z` are global because the function does not assign them. `x` is global because the `global` statement maps it explicitly to the module's scope. Without that statement, the assignment would make `x` local.

Notice that `y` and `z` need no declaration. The LEGB lookup finds them in the module automatically. Also notice that `x` does not exist in the module before the function runs. The first assignment inside the function creates it. This works when you need it. Still, avoid using globals this way whenever possible, as the next section explains.

### Minimize global variables

Functions and global variables raise bigger design questions. How should functions communicate with each other? You will see more answers as you write larger programs, but a few guidelines now can save you trouble later. In general, functions should rely on arguments and return values instead of globals. Newcomers often do not expect this advice, and it is worth taking on trust for a while.

Names assigned in functions are local by default. If you want to change names outside a function, you must write extra code, such as a `global` statement. That is deliberate. You have to say more to do the potentially risky thing. Globals are useful at times, and sometimes required. Still, local-by-default is the better policy most of the time.

Changing globals leads to well-known software problems. The value of a global depends on the order in which distant functions are called. Such programs can be hard to debug or to understand at all. Consider this module file, which another part of a program probably imports:

```python
X = 99
def func1():
    global X # Change global X when called
    X = 88
def func2():
    global X # But so does this, and when?
    X = 77
```

Suppose you must modify or reuse this code. What is the value of `X`? That question has no answer until you give it a point in time. The value depends on which function ran last, and this file alone cannot tell you that. To understand the code, you have to trace the flow of control through the whole program. You cannot use one of these functions without the other, because they are coupled through the global variable.

That is the core problem with globals. They make code harder to understand and reuse than self-contained functions that rely on locals.

Globals still matter for one job. Short of using nested closures or classes, a global is the simplest way to keep shared state. State is information a function must remember for its next call. Local variables disappear when a function returns, but globals do not. Other techniques can do this too, and they can keep several separate copies. Those techniques are more complex, though. For simple cases, a value stored in the global scope is often enough.

Some programs designate a single module to collect shared globals. As long as everyone expects that layout, it causes less harm. Programs that use multithreading for parallel work also often depend on globals. The global scope becomes shared memory between functions running in parallel threads, so it acts as a communication channel.

> Note: multithreading runs function calls in parallel with the rest of a program. Python's standard-library modules `_thread`, `threading`, and `queue` support it. Threaded functions share one process, so global scopes often serve as one form of shared memory. Threading is common for long-running tasks in GUIs, for nonblocking IO, and for using CPU capacity. It is beyond the scope of this book, as are `async` functions.

For now, especially if you are new to programming, avoid globals when you can. They make programs harder to understand and reuse. They also fail when you need more than one copy of saved data. That is why globals are not the default in Python. Pass values in with arguments and return results instead. Six months from now, you and your teammates will be glad you did.

### Minimize cross-file changes

Another design note relates to globals. You can change a global variable in another file directly, but you usually should not. Consider two module files:

```python
# first.py
X = 99 # This code doesn't know about second.py
```

```python
# second.py
import first
print(first.X) # OK: references a name in another file
first.X = 88 # But changing it can be too subtle and implicit
```

The first file defines `X`. The second file imports it, prints the value, and then assigns a new value. The second file must import the first to reach its variable at all. Each module is a self-contained namespace, so you import a module to see inside it. That is the main purpose of modules. They keep variables for each file separate, which prevents name collisions across files. This works much like local variables prevent clashes across functions.

Once a module is imported, its global scope becomes the attribute namespace of the module object. Importers can access all of its global variables that way.

Printing `first.X` is fine, since modules are linked together this way all the time. The assignment to `first.X` is the problem. Whoever maintains the first module probably does not know that a module far down the import chain can change `X` while the program runs. The second file might even sit in a different folder, where it is hard to notice.

Cross-file changes are always possible in Python, but they are usually more subtle than you want. They couple two components tightly. Because both files depend on the value of `X`, neither is easy to understand or reuse alone. Hidden dependencies like this lead to inflexible code at best and surprising bugs at worst.

Generally, communicate across file boundaries by calling functions. Pass in arguments and get back return values. In this case, a function that manages the change is the better option:

```python
# first.py
X = 99
def setX(new): # Accessors make external changes explicit
    global X # And can manage access in a single place
    X = new
```

```python
# second.py
import first
first.setX(88) # Call the function instead of changing directly
```

This needs more code, and it may look like a small change. Still, it helps readability and maintenance a lot. Someone reading the first module sees a function and knows it is an interface point. That person will expect `X` to change through it. This removes surprise, which is rarely welcome in software projects. You cannot always prevent cross-file changes, but you should minimize them unless the whole program knows about them.

### Other ways to reach globals

Because global-scope variables become attributes of a loaded module, you can also change a global without the `global` statement. You import the enclosing module and assign to its attributes. The file below does this in three ways. It also uses `sys.modules`, the dictionary that records every loaded module:

```python
"Change a global three ways"
var = 99 # Global variable == module attribute
def local():
    var = 0 # Change local var
def glob1():
    global var # Declare global (normal)
    var += 1 # Change global var
def glob2():
    var = 0 # Change local var
    import thismod # Import myself
    thismod.var += 1 # Change global var
def glob3():
    var = 0 # Change local var
    import sys # Import system table
    thismod = sys.modules['thismod'] # Get module object (or use __name__)
    thismod.var += 1 # Change global var
def test():
    print(var)
    local(); glob1(); glob2(); glob3()
    print(var)
```

When you import this module and call `test`, it adds 3 to the global `var`. Only `local` leaves the global unchanged:

```
>>> import thismod
>>> thismod.test()
99
102
>>> thismod.var
102
```

All of these techniques work, and they show that the global scope is equivalent to module attributes. They take more work than a `global` statement, though. The `global` statement makes your intent clear, so use it when you need to change a global.

The `nonlocal` statement is a close relative of `global`. It can change names in enclosing functions, not just in the module. To see why that helps, we first need to look at nested functions.

## Nested functions and closures

A function defined inside another function is where the scope story gets interesting. The inner function can see the outer function's names, long after the outer call has returned, and that small fact is the seed of closures.

### Nested scope lookups

So far, this chapter has left out one part of Python's scope rules on purpose. It is uncommon in practice, and it needs a little room to explain. Now it is time to look at layer E of the LEGB rule. Python 2.x added this layer. It consists of the local scopes of every enclosing function. Enclosing scopes are sometimes called statically nested scopes. The nesting is lexical, which means it follows the physical nesting of code in the source text.

With nested function scopes, lookups become a bit more involved. Inside a function:

- A name reference looks for the name first in the current local scope. Then it checks the local scopes of lexically enclosing functions, from inner to outer. Next it checks the current global scope, which is the module file. Finally it checks the built-in scope. A `global` declaration makes the search begin in the module scope instead.
- A name assignment creates or changes the name in the current local scope by default. If the name is declared `global`, the assignment changes the module scope instead. If the name is declared `nonlocal`, the assignment changes the closest enclosing function that assigns the same name.

A `global` declaration still maps names to the module. Enclosing function variables can be referenced without declaration, but changing them requires `nonlocal`. Unlike `global`, a `nonlocal` declaration does not create a name in an enclosing `def` that never assigns it. `nonlocal` makes sense only when an enclosing `def` assigns the name. Otherwise it is an error.

Here is what an enclosing function scope looks like. You can type this into a script file or the interactive prompt:

```python
X = 99 # Global scope name: not used
def f1():
    X = 88 # Enclosing def local
    def f2():
        print(X + 1) # Reference made in nested def
    f2()
f1() # Prints 89: enclosing def local + 1
```

This is legal Python. A `def` is an executable statement, so it can appear anywhere another statement can, including inside another `def`. While `f1` runs, the nested `def` creates a function and assigns it to the name `f2` inside `f1`. The `f2` function is temporary. It lives only while `f1` runs, and only code inside `f1` can see it. That is one good reason to nest it: the name cannot clash with anything else in the program.

When `f2` uses `X`, it refers to the `X` in the enclosing `f1` scope. Functions can access names in every physically enclosing function. So the LEGB rule maps `X` in `f2` to `X` in `f1`, through the E level. Read that mapping slowly, because the rest of this section builds on it.

Here is the part that surprises people. This enclosing lookup still works after the enclosing call has finished. The next example defines a function that makes and returns another function:

```python
def f1():
    X = 88
    def f2():
        print(X + 1) # Remembers X in enclosing def scope
    return f2 # Return f2 but don't call it
action = f1() # Make, return function
action() # Call it now: prints 89
```

The call to `action` runs the function we named `f2` when `f1` ran. This works because functions are objects, like everything else in Python. They can be passed back as return values. `f2` remembers the `X` from `f1` even though `f1` is no longer active when `f2` runs. That memory is one of the main reasons to nest functions, and the next section looks at it closely.

### Closures and factory functions

The behavior in the last example has two names. Some people call it a closure, which is a functional programming technique. Others call it a factory function, which is a design pattern. A factory function creates and returns a function that carries a closure of state. The two terms overlap a lot, so do not worry about choosing between them yet.

Either way, the function object remembers values from enclosing scopes, even when those scopes are no longer active. Think of it as carrying packets of memory with it, and each new nested function gets its own packet. That is why closures often serve as a simple alternative to classes for this job.

Closures are useful when a program must create event handlers at runtime. Imagine a GUI that must define actions based on user input. That input cannot be predicted when the GUI is built, and each action differs. You need a function that creates and returns another function. Each function it makes carries its own state.

Here is a simple demonstration. Type this at the interactive prompt and watch what comes back:

```
>>> def maker(N):
...     def action(X): # Make and return action
...         return X ** N # action retains N from enclosing scope
...     return action
```

The outer function makes the nested function, then returns it without calling it. Calling the outer function gives you back the nested function:

```
>>> f = maker(2) # Pass 2 to argument N
>>> f
<function maker.<locals>.action at 0x101ae7ba0>
```

Now call the function you got back:

```
>>> f(3) # Pass 3 to action's X
9 # And maker's N remembers 2: 3 ** 2
>>> f(4) # Pass 4 to X, N is still 2: 4 ** 2
16
```

The nested function remembers `2`, the value of `N` in `maker`. `maker` has already returned and exited, but `N` lives on as state attached to `action`. That is why calling `f` squares its argument.

If you call the outer function again, you get a new nested function with different state:

```
>>> g = maker(3) # g remembers 3, f remembers 2
>>> g(4) # 4 ** 3
64
>>> f(4) # 4 ** 2
16
```

The name `g` now cubes its argument, while `f` still squares. Each call to a factory like this gets its own state. Here, `g` remembers 3 and `f` remembers 2, because each has its own `N`. In a GUI, that `N` might be a username, an email address, or other data for one specific action.

All of this is real Python behavior, not a teaching simplification. Each nested function has a closure storage area for the enclosing names it uses. You can see it as the `__closure__` attribute of the function. You do not need those internals to use closures, though.

Closures are an advanced technique. You may see them more often in code written by people with functional programming backgrounds. Enclosing scopes also appear in `lambda` expressions from the previous chapter. A `lambda` is an expression, so it is almost always nested inside a `def`. A `lambda` can stand in for a `def` here, and it also keeps state through enclosing references, such as `N` below:

```
>>> def maker(N):
...     return lambda X: X * N # lambda functions retain state too
>>> h, i = maker(2), maker(3) # Make two closure functions
>>> h('Py'), i('Py') # Run lambdas: ('Py' * 2) and ('Py' * 3)
('PyPy', 'PyPyPy')
```

### Customizing open with a closure

Here is a practical example of a closure at work. Imagine you want to replace the built-in `open` with a custom version, as the built-in scope section suggested. If the custom version needs to call the original, it must save the original before replacing it. It must also keep that original for later. That is a classic state-retention job, and a closure fits it neatly.

Globals are not a good fit. If you want to customize `open` more than once, a global would hold only one value. Each customizer needs its own state. The file below, `makeopen.py`, uses a nested closure to remember a value without using globals. It also avoids writing a full class, which would be more code than this job needs:

```python
import builtins
def makeopen(id):
    original = builtins.open
    def custom(*pargs, **kargs):
        print(f'Custom open call {id}' , pargs, kargs)
        return original(*pargs, **kargs)
    builtins.open = custom
```

This code changes `open` for every module in the process. It replaces the built-in version with a custom function, which was defined with a nested `def`. Before the replacement, it saves the original in the enclosing scope, so the custom version can call it later. The code uses starred arguments to collect and pass along any positional and keyword arguments meant for `open`. Those are covered in the next chapter. The main idea here is the closure. The custom `open` found by the LEGB rule keeps a reference to the original:

```
>>> file = '../Chapter14/data.txt'
>>> F = open(file) # Call built-in open in builtins
>>> F.read()
'Testing file IO\nLearning Python, 6E\nPython 3.12\n'
>>> from makeopen import makeopen # Import open resetter function
>>> makeopen('MOD1') # Custom open calls built-in open
>>> F = open(file) # Call custom open in builtins
Custom open call MOD1 ('../Chapter14/data.txt',) {}
>>> F.read()
'Testing file IO\nLearning Python, 6E\nPython 3.12\n'
```

Closures can also nest in ways that globals cannot support. Each call to `makeopen` remembers its own `id` and `original`, so you can stack several customizations on top of each other:

```
>>> makeopen('MOD2') # Nested customizers work too
>>> F = open(file) # Because each retains its own state
Custom open call MOD2 ('../Chapter14/data.txt',) {}
Custom open call MOD1 ('../Chapter14/data.txt',) {}
>>> F.read()
'Testing file IO\nLearning Python, 6E\nPython 3.12\n'
```

As written, this code adds call tracing to a built-in function. The general technique has other uses as well. A class-based version would work too, but it would need more code, because it must store `id` and `original` in object attributes. Classes come later.

### Arbitrary scope nesting

Scopes can nest to any depth. Only enclosing functions are searched when a name is referenced, though. Classes are not. Here is a deeper example:

```
>>> def f1():
...     x = 99
...     def f2():
...         def f3():
...             print(x) # Found in f1's local scope!
...         f3()
...     f2()
>>> f1()
99
```

This does work. Python searches the local scopes of all enclosing `def`s, from inner to outer. It does this after the function's own local scope and before the module's global scope or the built-ins. Code like this is rare, though. The coding saying "flat is better than nested" still holds, even with closures available. Except in limited cases, you will have an easier time if you limit nesting in function definitions.

## The nonlocal statement

Sooner or later a nested function must change a name it can see but does not own. Without help, Python treats that assignment as local, and the result surprises you. The `nonlocal` statement is the help.

### nonlocal basics

Earlier you saw that a nested function can reference a variable in an enclosing function, even after that function has returned. You can also change such a variable, as long as you declare it `nonlocal`. With this statement, a nested function gets both read and write access to names in enclosing functions. That makes closures more useful, because their state can change.

The `nonlocal` statement works inside a `def` but not inside a `lambda`. It is similar in form and role to `global`. Both declare that a name will be changed in a scope outside the current function. The difference is the scope. `global` points at the module, while `nonlocal` points at an enclosing function. Also, `nonlocal` names must already exist in an enclosing function. They cannot be created by a first assignment inside the nested `def`.

Put simply, `nonlocal` allows assignment to names in enclosing function scopes, and it limits the lookup for those names to enclosing functions. The result is a direct and reliable way to keep changeable state. This works well when you need state but do not want a class or another stateful tool.

`nonlocal` appears only inside a function, and using it anywhere else is an error. It works only when a `def` is nested inside another `def`. A `lambda` body holds one expression, so it cannot use `nonlocal` or contain a nested `def`.

Within a `def`, the `nonlocal` statement decides where lookups start. Like `global`, it makes the search for the listed names begin in the enclosing `def` scopes, not in the local scope. In other words, `nonlocal` also means skip my local scope. The names in a `nonlocal` statement must be assigned in an enclosing `def`. They never refer to names in the global or built-in scopes.

The `nonlocal` statement does not change the general lookup rules. Names are still found by LEGB. `nonlocal` only lets you change enclosing names, rather than just read them. For the names it lists, `global` and `nonlocal` tighten the lookup:

- `global` makes the lookup begin in the module scope and allows names there to be assigned. If the name is not in the module, the lookup continues to the built-in scope. Assignments to global names always create or change them in the module scope.
- `nonlocal` limits the lookup to enclosing `def`s, requires the names to exist there, and allows them to be reassigned. The lookup never continues to the global or built-in scopes.

### nonlocal in action

Simple references to enclosing `def` scopes work as you have already seen. In the example below, `outer` builds and returns `inner`. The `state` name inside `inner` maps to the local scope of `outer` through the normal LEGB rules:

```
>>> def outer(start):
...     state = start # Referencing nonlocals works normally
...     def inner(label):
...         print(label, state) # Remembers state in enclosing scope
...     return inner
>>> F = outer(0)
>>> F('code') # State is the same on every inner run
code 0
>>> F('hack')
hack 0
```

Changing a name in an enclosing scope is not allowed by default, though. This is the error that sends beginners looking for answers:

```
>>> def outer(start):
...     state = start
...     def inner(label):
...         state += 1 # Cannot change by default
...         print(label, state)
...     return inner
>>> F = outer(0)
>>> F('code')
UnboundLocalError: cannot access local variable 'state' …
```

If you declare `state` as `nonlocal` inside `inner`, you can both read and change it. This works even though `outer` has returned by the time you call `F`:

```
>>> def outer(start):
...     state = start # Each call gets its own state
...     def inner(label):
...         nonlocal state # <= Remembers state in enclosing scope
...         state += 1 # Allowed to change it if nonlocal
...         print(label, state)
...     return inner
>>> F = outer(0)
>>> F('code') # Increments state on each call
code 1
>>> F('hack')
hack 2
```

You can call the `outer` factory several times to get several copies of its state. Each call creates a new `state` object, attached to the new `inner` function. Updating one function's state does not affect the other. Here the interaction continues:

```
>>> G = outer(24) # Make a new outer that starts at 24
>>> G('code')
code 25
>>> G('hack') # G's state information updated to 26
hack 26
>>> F('more') # But F's state is where it left off: at 2
more 3 # Each call has different state information
```

Python's nonlocals are more capable than the "static" function locals in some other languages. In a closure, a nonlocal holds data that is per call, and you can make as many copies of it as you have calls.

### nonlocal boundary cases

`nonlocal` has a few subtleties, and each one has caught someone. First, unlike `global`, a `nonlocal` name must already be assigned in an enclosing `def`. You cannot create it by assigning it in a nested function. The enclosing function's assignment can come before or after the nested function. If the assignment is missing, you get an error. Python checks for it when the nested function is defined, before either function is called:

```
>>> def outer(start):
...     def inner(label):
...         nonlocal state # Nonlocals must exist in an enclosing def
...         state = 0
...         print(label, state)
...     return inner
SyntaxError: no binding for nonlocal 'state' found
>>> def outer(start):
...     def inner(label):
...         global state # But globals don't have to exist when declared
...         state = 0
...         print(label, state)
...     return inner
>>> F = outer(0)
>>> F('glob')
glob 0
>>> state # Created by the assignment in nested inner
0
```

Second, `nonlocal` limits lookup to enclosing `def`s. It never looks in the module's global scope or the built-in scope, even if the name exists there:

```
>>> state = 0
>>> def outer():
...     def inner():
...         nonlocal state # Must be located in a def, not the module
...         state += 1 # Use global for globals, not nonlocal
...     return inner
SyntaxError: no binding for nonlocal 'state' found
>>> def outer():
...     def inner():
...         nonlocal ord # Ditto for built-ins (and immediate calls)
...         print(ord)
...     inner()
SyntaxError: no binding for nonlocal 'ord' found
```

These limits make sense once you see the problem. Python would not know which enclosing scope should get a brand-new name. In the first listing above, should `state` be assigned in `outer` or in the module? That is ambiguous. So Python resolves `nonlocal` names when the function is created, not when it is called.

Third, a `nonlocal` name can appear anywhere in the chain of enclosing functions, not only one level up. The closest match is used. This can matter in deeply nested code. Such code is rare, so the earlier section on arbitrary nesting covers the idea.

## State-retention options

Many problems come down to one question: where should a function keep a value between calls? Python offers four answers, and each one trades a little clarity for a little power.

Nested functions add complexity, so you may wonder why they are worth it. State matters in many programs, even though it is hard to see in small examples. A function can return results, but its local variables will not keep values between calls. Many applications also need those values to differ for each context of use. That combination is what pushes you toward one of the options below.

Python offers several ways to retain state between calls. You have already met two of them: globals and enclosing scope references. The others are class-instance attributes and function attributes. This section compares them, so you can pick with your eyes open.

### Nonlocals

Here is a recap of the `nonlocal` example from the previous section, repeated so you can compare the options:

```
>>> def outer(start):
...     state = start # Each call gets its own state
...     def inner(label):
...         nonlocal state # Remembers state in enclosing scope
...         state += 1 # Allowed to change it if nonlocal
...         print(label, state)
...     return inner
>>> F = outer(0) # State to be saved in enclosing scope
>>> F('nonlocal1') # State visible within closure only
nonlocal1 1
>>> F('nonlocal2')
nonlocal2 2
>>> F.state
AttributeError: 'function' object has no attribute 'state'
```

Each call to `outer` makes a self-contained package of changeable data. Its names do not clash with anything else in the program. You need `nonlocal` only for names that must change. Other enclosing names are kept automatically under LEGB. Also, nonlocal names are not visible outside the enclosing function.

### Globals

A common idea is to skip `nonlocal` and move the saved information into the global scope:

```
>>> def outer(start):
...     global state # Move it out to the module to change it
...     state = start # global allows changes in module scope
...     def inner(label):
...         global state
...         state += 1
...         print(label, state)
...     return inner
>>> F = outer(0)
>>> F('global1') # Each call increments shared global state
global1 1
>>> F('global2')
global2 2
>>> state # State accessible as global outside defs
2
```

This works in this case. It needs `global` declarations in both functions, though. It also risks name collisions, since `state` might already be used for something else in the module. A bigger problem is that the global scope holds only one copy of the state. If you call `outer` again, you reset the module's `state` variable, and earlier calls see their state overwritten:

```
>>> G = outer(24) # Resets state's single copy in global scope
>>> G('global3')
global3 25
>>> F('global4') # But F's counter has been overwritten!
global4 26
```

With `nonlocal` and nested closures, each call to `outer` keeps its own copy of `state`. Globals simply do not fit when each call needs its own data.

### Function attributes

You can often get the same effect as `nonlocal` with function attributes. A function attribute is a user-defined name attached to a function object. Factory functions create a new nested function on each call, so attributes on those functions work as per-call, multiple-copy, changeable state. Python's own internal names will not clash with your attribute names. Like `nonlocal`, you need an attribute only for state that must change. Other scope references keep working normally.

Factory functions already create a new function on each call, so attributes add no extra objects. Each function's attributes are per-call state, much like nonlocals. The difference is access. A nonlocal is visible only inside the nested `def`. A function attribute can be read from outside the function with a simple attribute lookup.

Here is the earlier example rewritten to use an attribute instead of `nonlocal`. Each `inner` changes `inner.state` and reads it back. You must initialize the state after the nested `def`:

```
>>> def outer(start):
...     def inner(label):
...         inner.state += 1 # Change object attr, not inner itself
...         print(label, inner.state) # inner is in the enclosing scope
...     inner.state = start # Initialize state after inner defined
...     return inner
>>> F = outer(0)
>>> F('attr1') # F is an inner with state attached
attr1 1
>>> F('attr2')
attr2 2
>>> F.state # Can access state outside defs too
2
```

This approach may look odd at first. You access the state through the function's name instead of as a plain variable. It also needs initialization after the nested `def`. In return, state can be read from outside, the `nonlocal` declaration is gone, and the state use is more explicit.

Each call to `outer` creates a new nested function object. So this scheme gives you multiple, changeable copies of data, just like nonlocal closures. Global variables cannot offer that:

```
>>> G = outer(24) # G has own state, doesn't overwrite F's
>>> G('attr3')
attr3 25
>>> F('attr4') # F's state varies
attr4 3
>>> F.state # State is accessible and per-call
3
>>> G.state
25
>>> F is G # Different function objects
False
```

Some fine points apply. This code depends on `inner` being a local name in the enclosing `outer` scope. That lets `inner` refer to itself through the E level. The code also depends on the fact that changing an object in place is not an assignment to a name. When it increments `inner.state`, it changes part of the object that `inner` refers to. It does not assign the name `inner`. So no `nonlocal` declaration is needed.

Function attributes predate `nonlocal` and offer similar value. In some roles, that makes `nonlocal` technically redundant. Python's naming conventions keep your attribute names from clashing with internal names, so the function's namespace works like a user scope.

> Note: a list in an enclosing scope can also be changed without declaring it `nonlocal`. The version below keeps changeable per-call state, and it mostly works like the earlier one. It does not let you read the state from outside the functions.

### Mutable objects in an enclosing scope

Here is the list version:

```python
def outer(start):
    def inner(label):
        state[0] += 1 # Clever hack or dark magic?
        print(label, state[0]) # Leverage in-place mutable change
    state = [start]
    return inner
```

This trick relies on the mutability of lists. Like function attributes, it depends on the fact that changing an object in place does not make a name local. It is more obscure than either function attributes or `nonlocal`, though. It is an older technique, and it sits somewhere between an arcane hack and an outdated workaround. Function attributes with names are usually a better choice than a list with numeric offsets. You cannot control what other people write, however, so you may still meet this pattern.

### Classes

Another standard way to keep changeable state is a class with attributes. Like function attributes, a class makes state access explicit instead of relying on scope lookup rules. Each instance gets a fresh copy of the state as a natural part of Python's object model. Classes also support inheritance and multiple behaviors, which go beyond what functions offer.

Here is a rough sketch of two stateful instances of a class:

```python
class Book:
    ...code to define method functions that manage and use state...
lp6e = Book() # Make an instance of the class
lp6e.year = 2024 # Access instance state via attributes
lp6e.python = 3.12
lp5e = Book() # Make another instance of the class
lp5e.year = 2013 # Each instance has its own attributes/state
lp5e.python = 3.3
```

Classes need more code than closures, but they suit larger jobs better. This section does not cover classes in detail. Their multiple-copy state comes later, in the object-oriented chapters.

### Which option to choose

All four options can change state between calls: globals, nonlocals, function attributes, and classes. Globals support only one shared copy. Nonlocals, function attributes, and classes all support multiple copies. Nonlocals use an implicit LEGB lookup. Function attributes are manual, but they are explicit, and you can read the state from outside the function. Classes are a larger tool that brings the complexity of object-oriented design.

The right tool depends on your program's goals. `nonlocal` gives changeable state to nested functions through a dedicated statement. It suits simple state needs where globals do not apply and classes are not worth it. Function attributes can often do the same job with less hidden behavior.

Decorators are a realistic case that needs multilevel state, and the same options apply to them. Performance is another factor in choosing, and this section leaves it aside. Timing code comes up later. For now, it is time to look at one more technique. It both bends the LEGB rule and leads to the next chapter.

## Scopes and argument defaults

### Defaults as an older workaround

Early Python versions did not handle enclosing scopes well. A nested function could not see an enclosing function's variables through LEGB. A reference to such a variable searched only the local, global, and built-in scopes, and failed. Programmers worked around this with default argument values. They passed in the enclosing value and kept it as a default:

```python
def f1():
    X = 88
    def f2(X=X): # Remember enclosing scope X with defaults
        print(X + 1)
    f2()
f1() # Prints 89
```

The same pattern works in a `lambda`, which creates a nested function scope in the normal way:

```python
def f1():
    X = 88
    f2 = lambda X=X: print(X + 1)
    f2()
```

Both examples work in every Python release, and both rely on argument defaults. The syntax `arg=val` in a function header means `arg` takes the value `val` when a call does not pass a real value. Here that default holds the enclosing scope's state.

The `X=X` default works because the right side is evaluated before Python enters the nested function. At that moment, the `X` on the right still refers to `X` in `f1`. So each `f2` remembers the value `88` from its enclosing `f1`.

This technique is subtle, and it depends on when default values are evaluated. It is also incidental. It works only if no real value is passed in to overwrite the default. The nested scope lookup was added to Python partly to make defaults unnecessary for this job. Today Python remembers the values a nested `def` or `lambda` needs from its enclosing scope automatically. The earlier example works the same way without defaults:

```python
def f1():
    X = 88
    def f2(): # Remember enclosing scope X per LEGB rule
        print(X + 1) # And likewise for lambda
    f2()
```

Flat is generally better than nested. Nesting functions in code like this can make programs more complex than they need to be. An equivalent that avoids nesting entirely looks like this. The call to `f2` inside `f1` is a forward reference. It is fine to call a function defined after the caller, as long as the second `def` runs before the caller is actually called. Code inside a function body is not evaluated until that function is called:

```python
def f1():
    X = 88 # Pass x along instead of nesting
    f2(X) # Forward reference OK
def f2(X):
    print(X + 1) # Flat is still often better than nested
```

If you avoid nesting this way, you can almost forget about nested scopes. Nested functions still help in one case, though. They avoid name clashes by hiding functions that are used nowhere else. Nesting is also the basis of closures, which give you stateful callable objects for many jobs. When functions are nested for those reasons, LEGB almost makes defaults unnecessary for saving enclosing state. The exception is covered next.

### Loops require defaults, not scopes

Why learn an outdated scope-reference scheme at all? Because one common case still needs it. Suppose a `lambda` or `def` sits inside a loop, and it references an enclosing variable that the loop changes. Then every function created in the loop ends up with the same value, the value the variable had in the last iteration. In that case you must use defaults to save the current value. This is the classic late-binding trap, so read it twice.

This can come up more often than you might think. It is common in code that creates event-handler functions for many widgets in a GUI. Click handlers for all the buttons in a panel are a typical example. If you create them in a loop, which is common, save their state with defaults. Otherwise every button may end up doing the same thing.

Here is the problem in simple code. The following tries to build a list of functions, each remembering the current `i` from the enclosing scope:

```
>>> def makeActions():
...     acts = []
...     for i in range(5): # Try to remember each i in 0..4
...         acts.append(lambda x: i ** x) # But all remember same last i!
...     return acts
>>> acts = makeActions()
>>> acts[0]
<function makeActions.<locals>.<lambda> at 0x101ae7ec0>
```

The same idea can be written as a list comprehension, with a `lambda` as the element. The comprehension acts as a local scope for its loop variable:

```
>>> acts = [(lambda x: i ** x) for i in range(5)]
>>> acts[0]
<function <lambda> at 0x10de6bce0>
```

Neither version works as intended. Python looks up the enclosing variable `i` when the nested functions run, not when they are created. So they all see the value the loop variable had on its last iteration. In the calls below, each function gets the same result, because `i` is 4 in all of them:

```
>>> acts[0](2) # All are 4 ** 2, 4=last i
16
>>> acts[1](2) # This should be 1 ** 2 (1)
16
>>> acts[2](2) # This should be 2 ** 2 (4)
16
>>> acts[4](2) # Only this should be 4 ** 2 (16)
16
```

To fix this, pass the current value of `i` in as a default argument rather than relying on the enclosing reference. Here are the required changes for both the `def` version and the comprehension version:

```
>>> def makeActions():
...     acts = []
...     for i in range(5): # Use defaults instead
...         acts.append(lambda x, i=i: i ** x) # Remember _current_ i
...     return acts
>>> acts = [(lambda x, i=i: i ** x) for i in range(5)]
```

Defaults are evaluated when the nested function is created, not when it is later called. So each function keeps its own value of `i`:

```
>>> acts = makeActions()
>>> acts[0](2) # 0 ** 2
0
>>> acts[1](2) # 1 ** 2
1
>>> acts[2](2) # 2 ** 2
4
>>> acts[4](2) # 4 ** 2
16
```

Function attributes do not fix this problem either. A function's own name is an enclosing variable that the loop changes too. So each function may refer to the last function made in the loop. The details are involved, but keep the rule in mind. Any enclosing reference changed by a loop may need a default.

This may look like an odd special case. It reflects how Python implements variable scopes, and you will meet it more often as your programs grow. The case is rooted in both scopes and argument defaults. To understand defaults fully, you need the next chapter.

### Mutable defaults keep state

Mutable argument defaults, such as lists and dictionaries, can also retain state. For example, `def f(a=[])` works this way. Python attaches defaults to the function when it is created. So a mutable default keeps its value from call to call. It is not rebuilt on each call. A default can also hold a mutable object from an enclosing function's scope, which gives you changeable per-call state.

Whether this is a useful feature or a dangerous corner of the language depends on whom you ask. Many programmers expect a default written as `[]` to be created fresh on every call. They are surprised when it keeps the values from earlier calls. The "Function Gotchas" discussion covers this in more detail.

## Chapter summary

This chapter covered scopes, one of the two key ideas about functions. Scopes decide how a variable is looked up when you use it. A variable is local to the function where it is assigned, unless it is declared `global` or `nonlocal`. You also saw advanced scope ideas, including nested function scopes and function attributes. Finally, you saw design guidelines, such as keeping globals and cross-file changes to a minimum.

The next chapter continues with the second key idea: argument passing. Arguments pass into a function by assignment. Python also offers tools that make functions flexible about how values are passed, including the defaults previewed here.

## Argument passing basics

The earlier sections showed where names live. This part asks a different question: how do values get into a function in the first place? When you call a function, each value you pass fills one name in the function header. Those names are the function's arguments, also called parameters. Python fills them in a simple way, and that simplicity has effects which surprise newcomers. Read this part slowly, because almost every confusing function bug traces back to it.

Python passes every argument by assignment. When the call starts, each name in the header is assigned the object the caller sent. Nothing is copied on the way in. The caller and the function can therefore share the same object. The earlier section on object references applies here too. The only difference is that Python does the assignment for you.

Three points sum up the model:

- Each argument name becomes a local name. It points at the caller's object, and that object is shared, not copied.
- Assigning a new object to an argument name changes only the local name. The caller's variable keeps its original object.
- Changing a mutable object in place is visible to the caller, because both names point at the same object. A mutable argument can work as both input and output.

Readers who know C or C++ may find this familiar. Python's model is not the same as C++ reference parameters. In practice, though, it behaves much like passing pointers in C. Immutable objects, such as integers and strings, act as if they were passed by value. The function can never change them in place. Mutable objects, such as lists and dictionaries, act as if they were passed by pointer. You do not need C to use Python. The model is simply assignment of references to names.

### Arguments and shared references

Start with a small test. Assigning a new object to an argument name inside a function does not change the caller's variable:

```
>>> def f(a): # a is assigned a reference to the passed object
...     a = 99 # Changes local variable a only
>>> b = 88
>>> f(b) # a and b both reference same 88 initially
>>> b # But b is not changed by assignment to a in f
88
```

The name `a` starts out pointing at the same `88` that `b` points at. Then the assignment inside the function points `a` at `99`. The name `b` keeps `88`. The name `a` only borrowed that object, and the borrowing ends as soon as `a` is reassigned. The argument name does not alias the caller's variable, so `a = 99` does not reach `b`.

Mutable objects behave differently. Changes made in place to a list or dictionary can outlive the function call. Here is an example with both kinds of argument:

```
>>> def changer(a, b): # Arguments assigned references to objects
...     a = 2 # Changes local name's value only
...     b[0] = 'mod' # Changes shared object in place: outlives call
>>> X = 1
>>> L = [1, 2] # Caller:
>>> changer(X, L) # Pass immutable and mutable objects
>>> X, L # X is unchanged, but L is different!
(1, ['mod', 2])
```

The first assignment, to `a`, only changes the local name. The caller's `X` is safe. The second assignment, to `b[0]`, changes the list that both `b` and `L` point at. Here `b` does not change at all. Only the object it refers to changes. The name `L` also stays the same. Its value looks different after the call, because the object it refers to was modified inside the function. In effect, `L` works as both input and output.

Just after the call starts, two objects are shared by four names. A diagram of this moment would show the caller's names and the function's local names sharing those two objects. The automatic assignment behaves like a series of plain assignment statements. The first argument has no effect on the caller:

```
>>> X = 1
>>> a = X # They share the same object
>>> a = 2 # Name change resets 'a' only, 'X' is still 1
>>> X
1
```

The second argument does affect the caller, because the change happens inside a shared object:

```
>>> L = [1, 2]
>>> b = L # They share the same object
>>> b[0] = 'mod' # In-place change from 'b': 'L' sees the change too
>>> L
['mod', 2]
```

Changing a mutable object in place can affect every other reference to it. Earlier chapters on shared mutable objects showed this effect in other settings. With arguments, the effect makes one argument work as both input and output.

### Avoiding mutable argument changes

In-place changes to mutable arguments are not a bug. They are simply how argument passing works in Python, and they are useful in practice. Passing objects by reference means large objects travel through a program without copies. The function can update them as it goes. Python's class model depends on this as well. A method changes its `self` argument in place to update an object's state. The object-oriented chapters explain that model.

Sometimes you do not want a function to change your data. In that case, pass a copy. For a list, you can copy at the point of the call with `list`, `list.copy`, or an empty slice. Dictionaries have similar copy tools:

```
L = [1, 2]
changer(X, L[:]) # Pass a copy, so our 'L' does not change
```

You can also copy inside the function. This protects the caller no matter how the function is called:

```
def changer(a, b):
    b = b.copy() # Copy input list so we don't impact caller
    a = 2
    b[0] = 'mod' # Changes our list copy only
```

Copies stop the changes from reaching the caller. They do not stop the function from changing its own copy. To block changes completely, pass an immutable object. A tuple raises an error when you try to change an item:

```
L = [1, 2]
changer(X, tuple(L)) # Pass a tuple, so changes are errors
TypeError: 'tuple' object does not support item assignment
```

The built-in `tuple` function builds a new tuple from the items of any sequence or iterable. This approach is extreme, though. The function must never change its arguments, which may limit it more than you need. The function also loses list-specific methods. Tuples have adopted `count` and `index` from lists, but not `copy`. Use this technique only when you have a strong reason.

The main point is that a function may update mutable objects you pass in. That is often useful, and the change is often part of a function's intended interface. Do not break that interface by copying. You do need to know about the behavior, though. If an object changes unexpectedly, check whether a called function changed it. Then make copies where the caller needs protection.

### Simulating output parameters and multiple results

Python does not support call by reference, but you can get a similar result with `return`. A function can return any object, including a tuple of several values. The caller then assigns those values back to its own names. This pattern simulates output parameters:

```
>>> def multiple(x, y):
...     x = 2 # Changes local names only
...     y = [3, 4]
...     return x, y # Return multiple new values in a tuple
>>> X = 1
>>> L = [1, 2]
>>> X, L = multiple(X, L) # Assign results to caller's names
>>> X, L
(2, [3, 4])
```

It looks as if the function returns two values, but it returns one two-item tuple. The parentheses are optional here, so they are left out. After the call, tuple unpacking splits the parts into `X` and `L`. The names change only because the caller's assignment says so. Lists work too, but tuples without parentheses are shorter to type, so people use them more often.

## Special argument-matching modes

Assignment is always the passing mechanism. The tools in this section change how the values in a call are matched to the names in a `def` or `lambda` header, before the assignment happens. All of these tools are optional. Libraries you read will use them often, though, so you should know them. By default, Python matches arguments by position, from left to right. You must pass exactly as many values as the header has names. The tools below relax that rule.

### Argument matching overview

These modes only decide which object goes to which name. The assignment still happens after the matching. Some tools are meant more for library authors than for application code. You may still meet them in code you did not write. Here is the full list:

- **Positionals:** values are matched to names from left to right. This is the normal case.
- **Keywords:** the caller names the argument with `name=value`, so the match uses the name.
- **Defaults:** the function gives an argument a value to use when the caller does not pass one.
- **Starred collectors:** a `*` or `**` in the header collects any extra positional or keyword arguments. C programmers call this varargs. In Python, the collected arguments go into a normal object.
- **Starred unpackers:** a `*` or `**` in the call unpacks a collection into separate arguments. This is the opposite of a collector.
- **Keyword-only arguments:** a bare `*` in the header means the names after it must be passed by keyword.
- **Positional-only arguments:** as of Python 3.8, a `/` in the header means the names before it must be passed by position.

### Argument matching syntax

The table below is a quick lookup. It shows each form, where it appears, and what it means:

| Syntax | Location | Interpretation |
| --- | --- | --- |
| `func(value)` | Caller | Normal argument: matched by position |
| `func(name=value)` | Caller | Keyword argument: matched by name |
| `func(*iterable)` | Caller | Pass all objects in `iterable` as individual positional arguments |
| `func(**dict)` | Caller | Pass all key/value pairs in `dict` as individual keyword arguments |
| `def func(name)` | Function | Normal argument: matches any passed value by position or name |
| `def func(name=value)` | Function | Default argument value, if not passed in the call |
| `def func(*name)` | Function | Matches and collects remaining positional arguments in a tuple |
| `def func(**name)` | Function | Matches and collects remaining keyword arguments in a dictionary |
| `def func(*name, name)` | Function | Arguments that must be passed by keyword only in calls |
| `def func(*, name)` | Function | Arguments that must be passed by keyword only in calls |
| `def func(name, /)` | Function | Arguments that must be passed by position only in calls |

In a call, the first four rows matter. Plain values match by position. The `name=value` form matches by name, and these are keyword arguments. You can use any number of `*iterable` and `**dict` forms in one call. Python unpacks them into separate arguments when it passes them to the function.

In a definition, a plain `name` matches by position or by name, depending on how the caller passes it. The `name=value` form gives a default. The `*name` form collects extra positional arguments in a tuple, and `**name` collects extra keyword arguments in a dictionary. Names after a `*name` or a bare `*` are keyword-only. Names before a `/` are positional-only.

Keywords and defaults are the two most common tools in Python code. You have already used keywords with `print`. Keywords label each value, which makes a call easier to read. Defaults make an argument optional. Together, they let a caller override only the defaults they care about.

Argument names in a `def` can also carry annotations, written `name:annot`. Annotations add syntax but do not change the ordering rules. A function can have a return annotation too, written with `->`. Annotations are covered in a later chapter.

### Argument passing details

Python's ordering rules apply when you combine these tools. The rules for calls differ from the rules for definitions. In short, positionals must come before keywords in a call. In a definition, a positional-only argument comes first, and the `**name` collector comes last. The formal rules appear later in this chapter.

If you mix the arguments in another order, Python raises a syntax error, because the combination would be ambiguous. Python matches arguments in roughly these steps:

1. Unpack all `*args` at the call into nonkeyword arguments.
2. Unpack all `**args` at the call into keyword arguments.
3. Assign nonkeyword arguments by position.
4. Assign keyword arguments by matching names.
5. Collect extra nonkeyword arguments in the `*name` tuple.
6. Collect extra keyword arguments in the `**name` dictionary.
7. Assign default values to unassigned arguments.

After matching, Python checks that each argument received only one value. If one did not, it raises an error. Otherwise it assigns the names and runs the function body. The real algorithm is a little more complex. The Python language reference describes it exactly. Reading it helps when you meet a tangled case with mixed modes.

## Keyword and default examples

Argument passing is simpler in code than the rules above may suggest. Without special syntax, Python matches names by position from left to right. A function that requires three arguments must be called with three arguments:

```
>>> def f(a, b, c): print(a, b, c)
>>> f(1, 2, 3)
1 2 3
```

Here `a` matches `1`, `b` matches `2`, and `c` matches `3`. This works the way it does in most languages, so your habits carry over.

### Keywords

Keyword arguments let you match by name instead of by position:

```
>>> f(c=3, b=2, a=1)
1 2 3
```

The `c=3` in this call sends `3` to the argument named `c`. Because the match uses names, the left-to-right order no longer matters. You can also mix the two forms. Positionals match first, from left to right. Then keywords match by name:

```
>>> f(1, c=3, b=2) # a gets 1 by position, b and c passed by name
1 2 3
```

Keywords do two jobs. First, they make calls self-documenting, as long as you choose good argument names. A call like this one tells you what each value means:

```
func(title='Learning Python', edition=6, year=2024, python=3.12)
```

A call with four bare values is harder to read, especially in a large program. The keywords act as labels for the data.

### Defaults

Defaults make selected arguments optional. If the caller does not pass a value, Python assigns the default before the function runs. This function requires one argument and gives defaults to two others:

```
>>> def f(a, b=2, c=3): print(a, b, c) # a required, b and c optional
```

In this function, you must provide `a`, either by position or by keyword. The values for `b` and `c` are optional. Without them, they become `2` and `3`:

```
>>> f(1) # Use defaults
1 2 3
>>> f(a=1)
1 2 3
```

Pass two values, and only `c` keeps its default. Pass three, and no defaults are used:

```
>>> f(1, 4) # Override defaults
1 4 3
>>> f(1, 4, 5)
1 4 5
```

Keywords and defaults work well together. A keyword skips past the positional order, so you can leave out a middle argument:

```
>>> f(1, c=6) # Choose defaults: b in the middle
1 2 6
```

Here `a` gets `1` by position, `c` gets `6` by keyword, and `b` keeps its default of `2`.

Be careful with the `name=value` syntax. In a call, it means a keyword argument. In a definition, it means a default. Neither one is an assignment statement, even though it looks like one.

### Combining keywords and defaults

This larger example shows keywords and defaults at work. The caller must pass at least two arguments, which match `code` and `hack`. The other two are optional. If they are omitted, Python uses the defaults in the header:

```
def func(code, hack, script=0, app=0): # First 2 required
    print((code, hack, script, app))
func(1, 2) # Output: (1, 2, 0, 0)
func(1, app=1, hack=0) # Output: (1, 0, 0, 1)
func(code=1, hack=0) # Output: (1, 0, 0, 0)
func(script=1, hack=2, code=3) # Output: (3, 2, 1, 0)
func(1, 2, 3, 4) # Output: (1, 2, 3, 4)
```

When the call uses keywords, the order of the arguments in the call does not matter. Python matches by name. The caller must supply `code` and `hack`, but can give them by position or by name.

All of this special syntax works in `lambda` too. Most examples here use `def`, but a `lambda` returns its result implicitly:

```
>>> func = lambda code, hack, script=0, app=0: (code, hack, script, app)
>>> func(1, 2)
(1, 2, 0, 0)
>>> func(script=1, hack=2, code=3)
(3, 2, 1, 0)
```

Mutable defaults deserve one more warning. A default such as `def f(a=[])` is built once, and every call reuses it. Changes made inside the function survive into later calls. The earlier section on mutable defaults goes deeper into this trap. To reset the value on each call, create the object inside the function body instead.

## Arbitrary arguments examples

The `*` and `**` forms let a function accept any number of arguments. Both can appear in a definition or in a call, and they have related but different jobs in each place.

### Collecting arguments in definitions

In a definition, the single star collects unmatched positional arguments into a tuple:

```
>>> def f(*args): print(args)
```

Python collects all positional arguments into a new tuple and assigns it to `args`. Because it is a normal tuple, you can index it or step through it with a `for` loop:

```
>>> f()
()
>>> f(1)
(1,)
>>> f(1, 2, 3, 4)
(1, 2, 3, 4)
```

The double star works the same way for keyword arguments. It collects them into a new dictionary, which you can process with the usual dictionary tools. In effect, `**` turns keywords into a dictionary. The `dict` call does something similar when you pass it keywords, but it returns the new dictionary directly:

```
>>> def f(**args): print(args)
>>> f()
{}
>>> f(a=1, b=2)
{'a': 1, 'b': 2}
```

A definition can combine normal arguments, `*`, and `**` to build a flexible signature. In this example, `1` goes to `a` by position. The values `2` and `3` go into the `pargs` tuple. The keywords `x` and `y` end up in the `kargs` dictionary:

```
>>> def f(a, *pargs, **kargs): print(a, pargs, kargs)
>>> f(1, 2, 3, x=1, y=2)
1 (2, 3) {'x': 1, 'y': 2}
```

Since Python 3.6, the keys in the `**` collector keep the order in which the keywords were passed. This follows from the insertion order of dictionary keys in general. Functions that use both `*` and `**` are rare. You will see them in functions that must support several call patterns, often for backward compatibility.

### Calls: unpacking arguments

In a call, the single star has the opposite meaning. It unpacks a collection into separate arguments. Here, four values in a tuple become four positional arguments:

```
>>> def func(a, b, c, d): print(a, b, c, d)
>>> args = (1, 2)
>>> args += (3, 4)
>>> func(*args) # Same as func(1, 2, 3, 4)
1 2 3 4
```

The double star in a call unpacks a dictionary into keyword arguments:

```
>>> args = {'a': 1, 'b': 2, 'c': 3}
>>> args['d'] = 4
>>> func(**args) # Same as func(a=1, b=2, c=3, d=4)
1 2 3 4
```

You can unpack other iterables and mappings too. You can also mix stars, positionals, and keywords in one call:

```
>>> func(*(1, 2), **{'d': 4, 'c': 3}) # Same as func(1, 2, d=4, c=3)
1 2 3 4
>>> func(1, *[2, 3], **dict(d=4)) # Same as func(1, 2, 3, d=4)
1 2 3 4
>>> func(1, c=3, *[2], **{'d': 4}) # Same as func(1, 2, c=3, d=4)
1 2 3 4
>>> func(1, *(2, 3), d=4) # Same as func(1, 2, 3, d=4)
1 2 3 4
>>> func(1, *[2], c=3, **dict(d=4)) # Same as func(1, 2, c=3, d=4)
1 2 3 4
```

These examples use literals to show the options. Real code usually builds the argument collections first and unpacks them by name:

```
>>> pargs, kargs = (1, 2), dict(d=4, c=3)
>>> func(*pargs, **kargs)
1 2 3 4
```

Unpacking helps when you cannot know the number of arguments until the program runs. You can build the collection at runtime and call the function generically. Remember that the star means different things in the two places. In a definition, one star collects positionals and two stars collect keywords. In a call, one star unpacks positionals and two stars unpack keywords.

Since Python 3.5, a call can contain several `*` and `**` items. Each one unpacks another iterable or mapping. Single stars must still come before double stars. This example uses literals too:

```
>>> def func(a, b, c, d): print(a, b, c, d)
>>> func(*[1], *(2,), **dict(c=3), **{'d': 4}) # *Positionals + **keywords
1 2 3 4
>>> func(*[1], *(2,), *[3, 4]) # All *positionals
1 2 3 4
>>> func(**dict(a=1, b=2), **dict(c=3), **{'d': 4}) # All **keywords
1 2 3 4
>>> func(*[1], 2, **dict(c=3), d=4) # All call modes at once!
1 2 3 4
>>> func(*[1], **dict(b=2, c=3), *[4])
SyntaxError: iterable argument unpacking follows keyword argument unpacking
```

The last line fails, and the reason is worth pausing on. Once a double star has unpacked keywords, a single star cannot follow it in the same call. The rules further down explain why the language settled on that.

The star on the call side is more generous than you might expect. It accepts any iterable, not only tuples and lists, so objects such as `range` and `zip` unpack into individual arguments. A file object reads its lines and passes them on:

```
func(*range(4)) # Same as func(0, 1, 2, 3)
func(*open('filename')) # Read+pass lines as arguments
```

Stars are a little inconsistent, though, and this is where people slip. The generality holds only in calls. In a definition, a star always collects extra arguments into a tuple. The extended unpacking in assignments, such as `x, *y = z`, uses the same syntax, and that form always creates a list, not a tuple. So the same symbol means three slightly different things depending on where you write it.

### Why arbitrary arguments?

These patterns may look academic at first. In real programs they turn up more often than you might expect. Some programs must call functions generically, without hardcoding their names or argument lists. The real power of starred calls is that you do not need to know the argument count before you write the script.

Suppose the program picks a function and its arguments with `if` logic. It then calls whichever one it chose:

```
if sometest:
    action, args = func1, (1,) # Call func1 with one arg in this case
else:
    action, args = func2, (1, 2, 3) # Call func2 with three args instead
…
action(*args) # Dispatch generically
```

This works because functions are objects. You can store one in a variable and call it through that variable. If a user picks a function from a menu, you may not know which one to call. Build the argument list with sequence operations, then unpack it with a star:

```
args = (2,3)
args += (4,)
…
func3(*args)
```

The argument list is a tuple here, so the program can build it at runtime. The same pattern is common in functions that test or time other functions. The next example passes along whatever arguments it receives:

```
def tracer(func, *pargs, **kargs): # Accept arbitrary arguments
    print('calling:', func.__name__)
    return func(*pargs, **kargs) # Pass along arbitrary arguments
def func(a, b, c, d):
    return a + b + c + d
print(tracer(func, 1, 2, c=3, d=4))
```

The code uses the `__name__` attribute that every function has. It holds the function's name as a string. The stars collect the arguments meant for the traced function, then pass them along with call-side unpacking. When you run it, the tracer intercepts the arguments and forwards them untouched:

```
$ python3 tracer0.py
calling: func
10
```

The customizing `open` example earlier in this chapter used the same idea. Later chapters on generators and decorators use this technique too. It is a common pattern in general-purpose tools, worth recognising on sight.

## Keyword-only arguments

Sometimes a function wants to take any number of positional values and also a handful of named switches. A stray positional value must never land on a switch by accident. To make that safe, a function definition can require that some arguments be passed by keyword only. A positional value never fills them. This feature is called keyword-only arguments. It is useful when a function takes any number of positional values and also accepts optional configuration options.

In the header, keyword-only arguments appear after `*name`. Every such argument must be passed by keyword in the call. In this example, `a` can be passed by name or position, `b` collects extra positionals, and `c` must be passed by keyword:

```
>>> def kwonly(a, *b, c): print(a, b, c)
>>> kwonly(1, 2, c=3)
1 (2,) 3
>>> kwonly(a=1, c=3)
1 () 3
>>> kwonly(1, 2, 3)
TypeError: kwonly() missing 1 required keyword-only argument: 'c'
```

If you do not need to collect extra positionals, use a bare `*` by itself. It says the function accepts no extra positionals, but everything after the star must be a keyword. In the next function, `a` can be positional or keyword. `b` and `c` must be keywords, and no extra positionals are allowed:

```
>>> def kwonly(a, *, b, c): print(a, b, c)
>>> kwonly(1, c=3, b=2)
1 2 3
>>> kwonly(c=3, b=2, a=1)
1 2 3
>>> kwonly(1, 2, 3)
TypeError: kwonly() takes 1 positional argument but 3 were given
>>> kwonly(1)
TypeError: kwonly() missing 2 required keyword-only arguments: 'b' and 'c'
```

Keyword-only arguments can have defaults. In the next example, `a` can be passed by name or position. `b` and `c` are optional, but a caller must use keywords for them:

```
>>> def kwonly(a, *, b='code', c='app'): print(a, b, c)
>>> kwonly(1)
1 code app
>>> kwonly(1, c='hack')
1 code hack
>>> kwonly(a='py')
py code app
>>> kwonly(c=3, b=2, a=1)
1 2 3
>>> kwonly(1, 2)
TypeError: kwonly() takes 1 positional argument but 2 were given
```

A keyword-only argument without a default is effectively a required keyword. In this function, `b` must be passed, and `c` is optional:

```
>>> def kwonly(a, *, b, c='hack'): print(a, b, c)
>>> kwonly(1, b='code')
1 code hack
>>> kwonly(1, c='code')
TypeError: kwonly() missing 1 required keyword-only argument: 'b'
>>> kwonly(1, 2)
TypeError: kwonly() takes 1 positional argument but 2 were given
```

Here is a rule that catches people out. Unlike the arguments before the star, keyword-only arguments can mix defaults and non-defaults in any order. This is an exception to the normal rule, and the reason is covered in the ordering section below:

```
>>> def kwonly(a, *, b=2, c, d=4): print(a, b, c, d)
>>> kwonly(1, c=3)
1 2 3 4
>>> kwonly(1, c=5, b=6)
1 6 5 4
>>> kwonly(1)
TypeError: kwonly() missing 1 required keyword-only argument: 'c'
>>> kwonly(1, 2, 3)
TypeError: kwonly() takes 1 positional argument but 3 were given
>>> def badmix(b=2, c, d=5): …
SyntaxError: parameter without a default follows parameter with a default
```

Keyword-only arguments must come after a single star, not a double star. Nothing can follow the `**args` collector, and a `**` cannot stand alone in the header. Keyword-only arguments go between the `*` and the optional `**`. An argument before the `*` is an ordinary argument. It can be matched by position or keyword, so it is not keyword-only:

```
>>> def kwonly(a, **kargs, b, c):
SyntaxError: arguments cannot follow var-keyword argument
>>> def kwonly(a, **, b, c):
SyntaxError: invalid syntax
>>> def mixed(a, *b, **d, c=6):
SyntaxError: arguments cannot follow var-keyword argument
```

These errors make more sense after the formal ordering rules below. The examples may seem artificial, but they can show up in real code. They matter most to people who write libraries for other programmers.

### Why keyword-only arguments?

Keyword-only arguments let a function accept many positional values and also accept configuration options by keyword. You can do this without them, but the code gets longer. You must supply defaults for each option yourself, and you must check that no unexpected keywords were passed.

Picture a function that processes objects and also takes a tracing flag:

```
process(X, Y, Z) # Use flag's default
process(X, Y, notify=True) # Override flag default
```

Without keyword-only arguments, you need both `*args` and `**args`, and you must inspect the keywords by hand. With keyword-only arguments, the code is shorter. The following header makes sure no positional value can be matched to `notify`. The flag must be passed by keyword:

```
def process(*args, notify=False): …
```

The section on the print emulator below shows a realistic version of this idea.

## Positional-only arguments

Starting with Python 3.8, a function definition can include a `/` in its argument list. Every argument to the left of the slash must be passed by position. Keyword names are not allowed for them. Some built-in functions have worked this way for a long time, and their documentation shows the notation. Python made it available to function authors so library writers can hide argument names from callers.

This function requires `a` and `b` by position, but `c` can be passed either way:

```
>>> def mostlypos(a, b, /, c): print(a, b, c)
>>> mostlypos(1, 2, 3)
1 2 3
>>> mostlypos(1, 2, c=3)
1 2 3
```

Passing either of the first two arguments by keyword raises an error. That is the point of the slash: it closes the door on names for those arguments:

```
>>> mostlypos(1, b=2, c=3)
TypeError: mostlypos() got some positional-only arguments passed as keyword arguments: 'b'
>>> mostlypos(c=3, b=2, a=1)
TypeError: mostlypos() got some positional-only arguments passed as keyword arguments: 'a, b'
```

To accept only positional arguments, put the slash at the end of the list:

```
>>> def allpos(a, b, c, /): print(a, b, c)
>>> allpos(1, 2, 3)
1 2 3
>>> allpos(1, 2, c=3)
TypeError: mostlypos() got some positional-only arguments passed as keyword …
```

A `lambda` accepts the slash in the same way:

```
>>> f = lambda a, b, /, c: print(a, b, c)
>>> f(1, 2, c=3)
1 2 3
>>> f(1, b=2, c=3)
TypeError: <lambda>() got some positional-only arguments passed as keyword …
```

You can combine positional-only and keyword-only arguments to make a signature as strict as you want:

```
>>> def combo(a, b, /, *, c, d): print(a, b, c, d)
>>> combo(1, 2, c=3, d=4)
1 2 3 4
>>> combo(1, 2, 3, 4)
TypeError: combo() takes 2 positional arguments but 4 were given
>>> combo(a=1, b=2, c=3, d=4)
TypeError: combo() got some positional-only arguments passed as keyword …
```

Whether this syntax is worth its complexity is up to you. Python developers managed without it for decades. Some library authors find it useful for avoiding name clashes. The Python language reference documents the rationale and the usage in detail.

## Argument ordering: the gritty details

So far we have been loose about the rules for argument matching. In simple code those rules rarely matter. In more advanced code you need them exactly, so this section writes them down. Definitions and calls share similar syntax, but their rules differ because their roles differ.

### Definition ordering

In a definition, the argument list sits in parentheses after `def`. In a `lambda`, it sits before the colon. The list has four optional parts, and they must appear in this order. Here, position means a simple value in a call, and keyword means a `name=value` pair:

1. One or more arguments that must be passed by position only, followed by a single `/`.
2. Any number of arguments that can be passed by either position or keyword.
3. A single `*` by itself, or a single `*name` positional collector, optionally followed by any number of keyword-only arguments.
4. A single `**name` keyword collector.

Individual parts, including a bare `/` or `*`, are separated by commas. Any argument that is not starred can have a `name=expression` default. After the first default, every name must have a default up to the `*`. Keyword-only names after a star can mix defaults and non-defaults freely.

This ordering has some consequences. Positional-only arguments come first. A `*name` ends the run of positional arguments and collects the extra ones. A `**name` ends the whole list and collects the unmatched keywords. Its keys keep the order in which the keywords were passed.

The formal form is shorter:

```
def name(arguments-list): statements
lambda arguments-list: expression
arguments-list =
[positional-only-arguments, /]
[positional-or-keyword-arguments]
[* -or- *positional-collector, [keyword-only-arguments]]
[**keyword-collector]
```

In this notation, `-or-` is a choice and square brackets mark an optional part. You do not type either one. The next example uses every part:

```
>>> def f(a, /, b, c=3, *ps, e=4, **ks):
...     print(f'{a=}, {b=}, {c=}, {ps=}, {e=}, {ks=}')
>>> f(0, 1, 2, 3, 4, e=5, f=6, g=7)
a=0, b=1, c=2, ps=(3, 4), e=5, ks={'f': 6, 'g': 7}
```

Some boundary cases show the rules at work. The `/` must come before a star, and the double-star collector must come last:

```
>>> def f(a, *ps, /, b): pass
SyntaxError: / must be ahead of *
>>> def f(a, **ks, b): pass
SyntaxError: arguments cannot follow var-keyword argument
```

Python enforces another rule separately. Once a default appears, every later argument must have a default too, including arguments after the `/`:

```
>>> def f(a, b, c=3, d, e): pass
SyntaxError: parameter without a default follows parameter with a default
>>> def f(a, b=2, /, c): pass
SyntaxError: parameter without a default follows parameter with a default
```

This rule applies only to arguments before a `*` or `*name`. Defaults and non-defaults can mix freely among keyword-only arguments. That looks inconsistent. It makes some sense, though, because keyword-only arguments never match by position. That removes the ambiguity:

```
>>> def f(a, *, x=1, y): ... # OK: x and y must be keywords
>>> def f(a=1, b, *, x=1): ... # Not OK: a and b may be positional
SyntaxError: parameter without a default follows parameter with a default
```

A decorator can precede a `def`, and annotations can follow its arguments. Neither one changes argument ordering or matching. Neither works in a `lambda`, because its syntax is limited.

### Calls ordering

Calls follow a similar syntax, but the rules differ. In a call, all positional arguments must come before all keyword arguments. You can mix starred unpackings with single values. One star unpacks into several positional arguments. Two stars unpack into keywords. All positionals and single-star unpackings must come before any double-star unpacking.

A call has three optional parts, in this order:

1. One or more positional expressions, and `*expression` iterable unpackings that become positional arguments.
2. One or more `name=expression` keyword arguments, and `*expression` iterable unpackings that become positional arguments.
3. One or more `name=expression` keyword arguments, and `**expression` mapping unpackings that become keyword arguments.

All the arguments, starred or not, are separated by commas. The formal form is:

```
function([positional-values -or- *iterable-positional-unpackings]
[keyword-arguments -or- *iterable-positional-unpackings]
[keyword-arguments -or- **mapping-keyword-unpackings])
```

Here `function` is any expression that evaluates to a callable object. This example mixes positional, keyword, and unpacking arguments. Read it as a demonstration, not as a style to copy:

```
>>> def f(a, b, c, d, e, f, g, h, i):
...     print(a, b, c, d, e, f, g, h, i)
>>> f(*[1], 2, *[3], 4, f=6, *[5], **dict(g=7), h=8, **{'i': 9})
1 2 3 4 5 6 7 8 9
```

Once you use a keyword argument, you cannot use a plain positional argument. Every later argument must be a keyword or a star unpacking:

```
>>> f(1, 2, c=3, 4)
SyntaxError: positional argument follows keyword argument unpacking
```

This resembles defaults in definitions, but the rules are not identical. Try not to mix up definitions and calls. They share syntax but play different roles. In a call, `*` and `=` unpack and label. In a definition, they collect and set defaults.

After a double star, positional arguments and single stars are also not allowed. This can seem inconsistent. A single star can mix freely with keywords, because a double star unpacks into keywords. But keywords cannot be mixed with positionals:

```
>>> f(1, 2, **{'d': 3}, 4)
SyntaxError: positional argument follows keyword argument unpacking
>>> f(1, 2, **{'d': 3}, *[4])
SyntaxError: iterable argument unpacking follows keyword argument unpacking
>>> f(1, 2, d=3, *[4]) # OK, but why? – like first error above
>>> f(1, 2, d=3, 4) # Not OK, but why? – like preceding line
SyntaxError: positional argument follows keyword argument
```

### Perspective

If these rules make your head spin, take that as a sign to simplify. Python's argument-matching rules grew over time, and they now have many special cases. The first rule of programming applies here too. Keep it simple unless the problem demands complexity. If you must work hard to understand a call's argument order, consider rewriting it.

## Example: the min wakeup call

Now a more realistic exercise. Suppose you must write a function that returns the minimum of any set of arguments. The arguments can be any kind of object: numbers, strings, lists, lists of lists, files, or even `None`. The function should accept zero or more arguments. You do not need to support dictionaries or mixed nonnumeric types. Those types do not support direct comparisons.

The `*` collector handles the first requirement. Collect the arguments in a tuple and step through it with a `for` loop. Most object types support comparison, so you do not need a separate version for each type. Python picks the right comparison for the objects it receives.

The following file, `mins.py`, shows four ways to write this operation. Some of them came from students in a class exercise:

```
"Find minimum value among all passed arguments of comparable types"
def min1(*args):
    res = args[0]
    for arg in args[1:]:
        if arg < res:
            res = arg
    return res
def min2(first, *rest):
    for arg in rest:
        if arg < first:
            first = arg
    return first
def min3(*args):
    tmp = list(args)
    tmp.sort()
    return tmp[0]
def min4(*args):
    return sorted(args)[0]
for func in (min1, min2, min3, min4): # Test all 4 functions
    print(func.__name__ + '...')
    print(func(3, 4.0, 1, 2)) # Mixed numerics
    print(func('bb', 'aa')) # Strings: code points
    print(func([2, 2], [1, 1], [3, 3])) # Lists: recursive
    print(func(*'hack')) # Unpacked characters
```

The first version takes the first argument out of `args` and scans the rest by slicing off the first item. There is no reason to compare the first object with itself, especially when that object is a large structure. The second version lets Python split off the first argument and the rest. That avoids an index and a slice. The code is simpler, and it may be faster, though you would need many calls to notice. The third version converts the tuple to a list and calls the list's `sort` method. After an ascending sort, the first item is the lowest. The fourth version sorts too, but with the `sorted` built-in. It skips the list conversion and saves two lines.

The testing code uses the `__name__` attribute and a `for` loop to call each function in turn. Functions are objects, so they can sit in a tuple without any fuss. All four versions give the same results. The output below shows only the first one:

```
$ python3 mins.py
min1...
1
aa
[1, 1]
a
…and the same for others…
```

None of these versions checks for zero arguments, and that is deliberate. Python raises an exception by itself when no arguments are passed. The first version fails when it fetches item `0`. The second fails when it detects a mismatch in the argument list. The third and fourth fail when they try to return item `0` after sorting. That is the behavior you want. Since the functions accept any object, including `None`, no value could signal an error. Letting Python raise the exception is the cleanest option. Assume that the arguments will work, and let Python report the problems.

Sorting carries a performance note too. CPython's sort is written in C, and it can take advantage of partial order in the items. The other versions do one linear scan, from left to right. Sorting may therefore be faster when the arguments are partly ordered, and slower otherwise. Python changes over time, so time the alternatives yourself with the `time` or `timeit` modules. In CPython, the non-sort versions are faster for random arguments, but slower for ordered ones.

### Bonus points

You can turn these functions into maximum finders. The first two versions need only `<` changed to `>`. The last two need item `[-1]` instead of `[0]`. Rename the functions to `max` too, if you want the extra credit.

You can also write one function that handles both minimum and maximum. One route is `eval` with a comparison string. A cleaner route is to pass in a comparison function. This example uses the second approach:

```
"Find minimum -or- maximum value of arguments"
def minmax(test, *args):
    res = args[0]
    for arg in args[1:]:
        if test(arg, res):
            res = arg
    return res
def lessthan(x, y): return x < y # See also: lambda, eval
def grtrthan(x, y): return x > y
print(minmax(lessthan, 4, 2, 1, 5, 6, 3)) # Self-test code
print(minmax(grtrthan, 4, 2, 1, 5, 6, 3))
```

The script prints the minimum and the maximum:

```
$ python3 minmax.py
1
6
```

Functions are objects, so you can pass them into other functions. To make a maximum function, pass the right test function to `minmax`. Generalizing this way saves work later. You change one version instead of cutting and pasting the code.

### The punch line

This was only a coding exercise, and it is worth saying so plainly. Python already has `min` and `max` as built-ins. The built-ins work almost the same way as these functions. They are written in C for speed, and they accept either one iterable or several arguments. The general pattern here can still be useful in other places.

## Example: generalized set functions

The next example uses argument-matching modes too. Here the goal is to find items that appear in every argument. An earlier chapter wrote a two-argument version. The new version accepts one or more arguments. It uses `*args` to collect them into a tuple. A `for` loop then processes each one. This example also includes a `union` function. It collects items from any of its arguments.

```
"""
Implement intersection and union for one or more arguments.
Inputs may be any sort of iterable that supports multiple in
tests, and results are always lists. This intersect avoids
duplicates in results by in test, but may be slow: improve me.
"""
def intersect(*args):
    res = []
    for x in args[0]: # Scan first sequence
        if x in res: continue # Skip duplicates in [0]
        for other in args[1:]: # For all other args
            if x not in other: break # Item in each one?
        else: # No: break out of loop
            res.append(x) # Yes: add items to end
    return res
def union(*args):
    res = []
    for seq in args: # For all args
        for x in seq: # For all in this arg
            if not x in res:
                res.append(x) # Add new items to result
    return res
```

Store these functions in a module file named `inter2.py`, since they are worth reusing. Launch the REPL from the same folder, so the import can find the file. Both functions work on any kind of sequence. Here they process strings, mixed types, and more than two sequences:

```
$ python3
>>> from inter2 import intersect, union
>>> s1, s2, s3 = 'HACKK', 'CODE', 'CASH'
>>> intersect(s1, s2), union(s1, s3) # Two operands
(['C'], ['H', 'A', 'C', 'K', 'S'])
>>> intersect([1, 2, 3, 4], (1, 4)) # Mixed types
[1, 4]
>>> intersect(s1, s2, s3) # Three operands
['C']
>>> union(s1, s2, s3)
['H', 'A', 'C', 'K', 'O', 'D', 'E', 'S']
```

To test the functions more thoroughly, the next session uses a shuffling helper. It moves the first argument to the end on each pass. It unpacks the arguments with `*` and sorts the results so they compare easily. The `trace` option is keyword-only:

```
>>> def tester(func, items, *, trace=True):
...     for i in range(len(items)):
...         items = items[1:] + items[:1] # Move front item to back
...         if trace: print(items)
...         print(sorted(func(*items))) # Test with reordered items
>>> tester(intersect, (s1, s2, s3)) # Use strings from prior listing
('CODE', 'CASH', 'HACKK')
['C']
('CASH', 'HACKK', 'CODE')
['C']
('HACKK', 'CODE', 'CASH')
['C']
>>> tester(union, (s1, s2, s3), trace=False)
['A', 'C', 'D', 'E', 'H', 'K', 'O', 'S']
['A', 'C', 'D', 'E', 'H', 'K', 'O', 'S']
['A', 'C', 'D', 'E', 'H', 'K', 'O', 'S']
>>> tester(intersect, (s1, s2, s3), trace=False)
['C']
['C']
['C']
```

Two notes apply here. First, these functions produce no duplicates, so they act like set operations. They may be slower than real sets, though. The set type covers intersection and union with `&` and `|`, and its methods accept several operands. Improving this demo is left as an exercise. Second, the shuffle does not try every possible argument order. A full set of orders for three arguments would need six orderings. The shuffle is enough to check whether argument order changes the results. A later chapter on generators shows a cleaner tester that delegates the shuffling to a reusable function.

## Example: rolling your own print

The last example uses `*` and `**` collectors, plus keyword-only arguments, to imitate most of Python's `print` function. Python already has `print`, so there is no urgent need for this code. Still, it teaches argument matching clearly, because everything you have just read appears in one small function. It can also be a base for custom versions of built-in tools.

The module below does roughly what `print` does, in a small amount of code. It builds the output string from the configuration arguments and routes it to the right file:

```
r"""
Emulate most of the Python 3.X print function as customizable code.
Call signature: print3(*args, sep=' ', end='\n', file=sys.stdout).
"""
import sys
def print3(*args, **kargs):
    sep = kargs.get('sep', ' ') # Keyword arg defaults
    end = kargs.get('end', '\n')
    file = kargs.get('file', sys.stdout)
    output = '' # Build+print a string
    first = True
    for arg in args:
        output += ('' if first else sep) + str(arg)
        first = False
    file.write(output + end)
```

The docstring uses a raw string, so the backslash stays visible in `help` output. The function does not need the name `print3`. `print` is a built-in, but not a reserved word. The different name still avoids hiding the built-in. To test the module, import it from another file or the REPL and use it like `print`:

```
from print3 import print3
print3(1, 2, 3) # Defaults
print3(1, 2, 3, sep='') # Suppress separator
print3(1, 2, 3, sep='...') # Custom separator
print3(1, [2], (3,), sep='...') # Various object types
print3(4, 5, 6, sep='', end='') # Suppress newline
print3(7, 8, 9) # Finish line
print3() # Blank line
import sys
print3(1, 2, 3, sep='?', end='.\n', file=sys.stderr) # Redirect to stream
print3('LP6E was here', file=open('log.txt', 'w')) # Redirect to a file
print3(open('log.txt').read())
```

Running the test script gives the same results as `print`. By default, `sys.stderr` writes to the console. A dash in a script's name is fine, because you run the script rather than import it. The output looks like this:

```
$ python3 test-print3.py
1 2 3
123
1...2...3
1...[2]...(3,)
4567 8 9
1?2?3.
LP6E was here
```

The same argument-matching tools work in Python code as they do in Python's own implementation.

### Using keyword-only arguments

The emulator has a flaw, and it is the kind of flaw that costs an afternoon. It treats every keyword as an option, and it ignores unknown ones. A call with a typo in an option name fails silently:

```
$ python3
>>> from print3 import print3
>>> print3(3.12, 'py', sap='@')
3.12 py
```

You can catch unknown keywords by hand. Use `dict.pop()` to remove the keywords you expect. If anything is left when you finish, raise an error. The version below does this. It is equivalent to the first one, but it raises a `TypeError` for unexpected keywords. Exceptions and `raise` get a full treatment later:

```
"Use keyword-collector arguments with deletion and defaults"
import sys
def print3(*args, **kargs):
    sep = kargs.pop('sep', ' ')
    end = kargs.pop('end', '\n')
    file = kargs.pop('file', sys.stdout)
    if kargs: raise TypeError(f'extra keywords: {kargs}')
    output = ''
    first = True
    for arg in args:
        output += ('' if first else sep) + str(arg)
        first = False
    file.write(output + end)
```

This file uses an underscore in its name, not a dash. A module that will be imported must follow the rules for variable names. The new version works as before, and now it catches extra keywords:

```
>>> from print3_pops import print3
>>> print3(3.12, 'py', sep='@')
3.12@py
>>> print3(3.12, 'py', sap='@')
TypeError: extra keywords: {'sap': '@'}
```

Importing `print3` from a different file replaces the earlier version, the same way any reassigned name does. The keyword-only version does the same validation with less code:

```
"Use keyword-only arguments to emulate print"
import sys
def print3(*args, sep=' ', end='\n', file=sys.stdout):
    output = ''
    first = True
    for arg in args:
        output += ('' if first else sep) + str(arg)
        first = False
    file.write(output + end)
```

Valid calls work the same way. Invalid keywords are caught by the keyword-only arguments rather than by manual code:

```
>>> from print3_kwonly import print3
>>> print3(3.12, 'py', sep='@')
3.12@py
>>> print3(3.12, 'py', sap='@')
TypeError: print3() got an unexpected keyword argument 'sap'
```

This version has four fewer lines than the one before it. Keyword-only arguments can simplify any function that takes both values and options. Positional-only arguments could help in a similar way, but that case is less common.

You can also assign the emulator to `builtins.print`, which replaces the built-in everywhere in a program. There is no reason to do that for an identical copy. The technique is useful for a replacement that changes or extends `print`, for example by adding logging.

## Argument passing summary

Arguments are passed to a function by assignment. Each argument name refers to the caller's object, so mutable objects can change in place and affect the caller. Python offers tools that generalize argument matching. These include defaults, keywords, collectors and unpackers for any number of arguments, and keyword-only and positional-only arguments. The examples in this section showed how these tools handle real tasks, such as finding a minimum, intersecting sequences, and emulating `print`.

## Why keyword arguments matter

You can get by with simple positional matching, and that is a good place to start. Many Python tools rely on the advanced modes, though, so it helps to recognize them. Keyword arguments play a central role in `tkinter`, the standard GUI library for Python. Keywords set configuration options when a GUI component is built:

```
from tkinter import Button
widget = Button(text='Press me', command=someFunction)
```

This call creates a button. The `text` keyword sets the label, and `command` sets the function that runs on a press. A widget can have many options, so keywords let you choose only the ones you need. Without keywords, you would have to list every option by position, or design a fixed positional protocol for every combination.

Many built-in functions also expect keywords for options. The `sorted` built-in takes an iterable, plus two optional keyword arguments. These are `key`, which transforms each value before comparison, and `reverse`, which flips the order. Their defaults are `None` and `False`:

```
sorted(iterable, key=None, reverse=False)
```

Usually you skip these options and let the defaults apply. The `dict` call, the `str.format` method, and `print` also accept keywords. Earlier chapters used them before this chapter explained how argument passing works.

## Function design concepts

Writing one function is easy. Writing many that work well together takes more thought. Two ideas guide that work. Cohesion describes how well the steps inside one function belong together. Coupling describes how much a function depends on other code, or on the world outside it. Good designs keep cohesion high and coupling low. These ideas come from structured design, and they apply to Python as they do to any language. Keep the pair in mind and the guidelines below will feel obvious rather than arbitrary.

Here are some guidelines for newcomers:

- **Coupling: use arguments for inputs and `return` for outputs.** A function should be as independent of the outside world as it can be. Arguments and `return` statements keep outside dependencies in a few known places.
- **Coupling: use global variables only when truly necessary.** Globals are usually a poor way for functions to communicate. They create hidden dependencies and timing issues that make programs hard to debug, change, and reuse.
- **Coupling: change mutable arguments only when the caller expects it.** A function can alter a mutable object it receives. As with globals, that ties the caller and the function tightly together, and it can make the function too specific to reuse.
- **Cohesion: give each function a single, unified purpose.** You should be able to describe a good function in one plain sentence. If the sentence is very broad, or it joins several jobs with "and," split the function. Otherwise you cannot reuse its steps on their own.
- **Size: keep each function relatively small.** If a function spans several screens, it is probably time to split it. A long or deeply nested function is often a sign of a design problem.
- **Coupling: avoid changing variables in another module directly.** Changing names across file boundaries couples modules, much as globals couple functions. Use accessor functions instead of direct assignment.

Functions can talk to the outside world in several ways. Inputs can come from arguments, globals, and other sources. Results can leave through `return` statements, changed mutable arguments, global names, and other channels. Whenever possible, prefer arguments for inputs and `return` for outputs.

There are plenty of exceptions. Python classes depend on changing a mutable object. Their methods set attributes on `self`, which Python passes in automatically, as in `self.edition = 6`. Without classes, a global can hold one shared copy of state for the functions in a module. Side effects are usually a problem only when nobody expects them.

In general, reduce external dependencies. The more self-contained a function is, the easier it is to understand, reuse, and change. That matters most when functions call themselves, as the next section shows.

## Recursive functions

A recursive function calls itself, directly or indirectly, to repeat its work. You met the idea while studying scope rules. Here you will see what it looks like in code.

Recursion is an advanced topic, and it is less common in Python than in some other languages. Python offers simple loops, which are usually easier to read. Still, recursion lets a program walk structures with arbitrary shapes and depths. Planning travel routes, analyzing language, and crawling links on the web are examples. Recursion can replace a simple loop too, though it is not always the simplest or fastest choice.

### Summation with recursion

You can add a list of numbers with the built-in `sum`, or with your own function. The recursive version below adds the first item to the sum of the rest of the list:

```python
def mysum(L):
    if not L:
        return 0
    else:
        return L[0] + mysum(L[1:])  # Call myself recursively
```

Import the file as a module to try it at the REPL:

```
>>> from mysum import mysum
>>> mysum([1, 2, 3, 4, 5])
15
```

Each call makes a new call for the rest of the list. When the list is empty, the function returns zero, and the recursion stops. The sums then add up as the calls return. Each open call has its own local scope on the call stack, so `L` holds a different slice at each level. This is the per-call scope idea from earlier, now doing real work.

To see this happen, add a `print` of `L`:

```python
def mysum(L):
    print(L)  # Trace recursive levels
    if not L:  # L shorter at each level
        return 0
    else:
        return L[0] + mysum(L[1:])
```

```
>>> mysum([1, 2, 3, 4, 5])
[1, 2, 3, 4, 5]
[2, 3, 4, 5]
[3, 4, 5]
[4, 5]
[5]
[]
15
```

The list gets shorter at each level until it is empty. That empty list ends the recursion. If the trace is hard to follow, run it with your own lists and watch the pattern.

### Coding alternatives

You can shorten this code. A ternary expression puts the test on one line. Extended unpacking can split the first item from the rest. The variants below also work with any type that supports `+`:

```python
# Variant 1: ternary expression
def mysum(L):
    return 0 if not L else L[0] + mysum(L[1:])

# Variant 2: any type, assumes at least one item
def mysum(L):
    return L[0] if len(L) == 1 else L[0] + mysum(L[1:])

# Variant 3: extended unpacking
def mysum(L):
    first, *rest = L
    return first if not rest else first + mysum(rest)
```

All three handle numbers the same way:

```
>>> mysum([1, 2, 3, 4, 5])
15
```

The last two fail on an empty list, such as `mysum([])`. They do handle sequences of other types that support `+`:

```
>>> mysum(('h', 'a', 'c', 'k'))
'hack'
>>> mysum(['hack', 'app', 'code'])
'hackappcode'
```

For strings, the result is similar to joining them with `''.join(L)`. Two more details are worth knowing. The last two variants also accept a single string, such as `mysum('hack')`. Strings are sequences of one-character strings, so the result is the same string. The third variant also accepts any iterable, including an open file, as in `mysum(open(name))`. The other two rely on indexing, which fails on non-sequences.

The unpacking line looks like a `*` parameter, so you might rewrite it that way. That version expects separate arguments, not one iterable. You must star both the top-level call and the recursive call:

```python
def mysum(first, *rest):
    return first if not rest else first + mysum(*rest)
```

```
>>> mysum(*[1, 2, 3, 4, 5])
15
>>> mysum(*'hack')
'hack'
```

This version solves a different problem than the earlier ones and the built-in `sum`, because it sums separate arguments.

Recursion can also be indirect. In that case, one function calls a second function, which calls back to the first. The net effect is the same, though each level makes two calls instead of one:

```python
def mysum(L):
    if not L: return 0
    return nonempty(L)  # Call a function that calls me

def nonempty(L):
    return L[0] + mysum(L[1:])  # Indirectly recursive
```

```
>>> mysum([1.1, 2.2, 3.3, 4.4])
11.0
```

### Loop statements versus recursion

Recursion works for summing, but it is probably more machinery than this job needs. Python favours simple statements such as loops. A `while` loop makes the work concrete, and it needs no function definition at all:

```
>>> L = [1, 2, 3, 4, 5]
>>> tot = 0
>>> while L:
...     tot += L[0]
...     L = L[1:]
>>> tot
15
```

A `for` loop iterates automatically, so recursion is often unnecessary:

```
>>> L = [1, 2, 3, 4, 5]
>>> tot = 0
>>> for x in L: tot += x
>>> tot
15
```

Recursion is often less efficient, in both memory and execution time. A loop does not need a fresh local scope on the call stack for each pass. It also avoids the cost of calling a function at every step. You can time the alternatives yourself to compare them, and the next section shows how.

### Handling arbitrary structures

Loops are not always enough, though. Consider a list that holds numbers and nested sublists:

```
[1, [2, [3, 4], 5], 6, [7, 8]]
```

A single loop cannot handle this, because the data is not a flat sequence. Nested loops fail too. Sublists can nest to any depth and in any pattern, so you cannot know in advance how many loops to write. Recursion solves that neatly. The function below steps into each sublist it finds:

```python
def sumtree(L, trace=False):
    tot = 0
    for x in L:  # For each item at this level
        if not isinstance(x, list):
            tot += x  # Add numbers directly
            if trace: print(x, end=', ')
        else:
            tot += sumtree(x, trace)  # Recur for sublists
    return tot
```

Each recursive level runs a `for` loop. It adds numbers directly, or it recurses into sublists to open new levels. The `isinstance` check compares object types, so it detects nested sublists. If `trace` is true, the function also prints each item as it is added. The scan runs across each level and down into nested ones, so it moves both horizontally and vertically:

```
>>> from sumtree import sumtree
>>> sumtree([1, [2, [3, 4], 5], 6, [7, 8]])
36
>>> sumtree([1, [2, [3, 4], 5], 6, [7, 8]], trace=True)
1, 2, 3, 4, 5, 6, 7, 8, 36
```

Typing each test by hand gets tedious. A separate tester script runs several canned tests on any summer function. It can also check other summers you write later:

```python
tests = (
    [1, [2, [3, 4], 5], 6, [7, 8]],  # Mixed nesting => 36
    [1, [2, [3, [4, [5]]]]],  # Right-heavy nesting => 15
    [[[[[1], 2], 3], 4], 5])  # Left-heavy nesting => 15

def tester(sumtree, trace=True):
    for test in tests:
        print(sumtree(test, trace))
```

Import both files and pass the summer to the tester:

```
>>> from sumtree import sumtree
>>> from sumtree_tester import tester
>>> tester(sumtree)
1, 2, 3, 4, 5, 6, 7, 8, 36
1, 2, 3, 4, 5, 15
1, 2, 3, 4, 5, 15
```

Inside `tester`, the name `sumtree` refers to whichever function you pass in. Functions are objects, so you can pass them around this way. That keeps the code flexible, and it lets one tester serve every version you write.

### Recursion versus queues and stacks

Python implements recursion by pushing information onto a call stack at each recursive call. The stack remembers where each call must return and continue. You are not forced to use it, though. An explicit stack or queue of your own can track the remaining steps. The item at the front of the list is always the next one to process.

This queue version computes the same sums, but it schedules the work in a list:

```python
def sumtree(L, trace=False):  # Breadth-first, explicit queue
    tot = 0
    items = list(L)  # Start with copy of top level
    while items:
        front = items.pop(0)  # Fetch/delete front item
        if not isinstance(front, list):
            tot += front  # Add numbers directly
            if trace: print(front, end=', ')
        else:
            items.extend(front)  # <== Append all in nested list
    return tot
```

Nested contents go to the end of the list, so the list works as a first-in-first-out queue. That makes a breadth-first traversal, which covers each level across before going down. Each summer lives in its own file, so importing it gives you the function under the name `sumtree`. The most recent import wins. Run the tester to see the new order:

```
>>> from sumtree_queue import sumtree
>>> sumtree([1, [2, [3, 4], 5], 6, [7, 8]])
36
>>> from sumtree_tester import tester
>>> tester(sumtree)
1, 6, 2, 5, 7, 8, 3, 4, 36
1, 2, 3, 4, 5, 15
5, 4, 3, 2, 1, 15
```

The order differs from the recursive version because of the breadth-first queue. Trace the tester's tests by hand to see why.

To follow the recursive order more closely, use a depth-first traversal instead. Add the nested items to the front of the list, which makes a last-in-first-out stack. Only one line differs from the queue version:

```python
def sumtree(L, trace=False):  # Depth-first, explicit stack
    tot = 0
    items = list(L)  # Start with copy of top level
    while items:
        front = items.pop(0)  # Fetch/delete front item
        if not isinstance(front, list):
            tot += front  # Add numbers directly
            if trace: print(front, end=', ')
        else:
            items[:0] = front  # <== Prepend all in nested list
    return tot
```

```
>>> from sumtree_stack import sumtree
>>> sumtree([1, [2, [3, 4], 5], 6, [7, 8]])
36
>>> from sumtree_tester import tester
>>> tester(sumtree)
1, 2, 3, 4, 5, 6, 7, 8, 36
1, 2, 3, 4, 5, 15
1, 2, 3, 4, 5, 15
```

Recursive calls are often more natural than the explicit lists they replace. They are usually preferred unless you need a special traversal order. Some programs need a best-first search, which uses a queue ordered by relevance or another score. Picture a web crawler that scores each site it visits by its content. That is where an explicit queue earns its place.

### Cycles, paths, and stack limits

These demos work, but larger recursive programs need more support. They may need to avoid cycles or repeats, record the paths they take, and manage stack space when they recurse deeply. Each of those needs is worth knowing before you meet it in someone else's code.

The examples so far do not avoid cycles, which means visiting a location twice. That is fine here, because they walk strictly hierarchical trees of lists. Cyclic data breaks them. The recursive version falls into an infinite recursion, and the queue and stack versions loop forever, adding the same items again. A short demo shows the problem:

```
>>> L = [1, 2]
>>> L.append(L)  # Make a cyclic object: L references itself
>>> L
[1, 2, [...]]
>>> from sumtree import sumtree
>>> sumtree(L)
RecursionError: maximum recursion depth exceeded
>>> from sumtree_queue import sumtree
>>> sumtree(L)
...hang or crash, and ditto for stack...
```

A recursive traversal can avoid repeats by passing along a mutable set, dictionary, or list of states it has seen. It checks each state before going further:

```python
if state not in visited:
    visited.add(state)  # x.add(state), x[state]=True, or x.append(state)
    ...proceed...
```

A nonrecursive version can use the same idea. Mark a state as visited when you take it from the list, and add only unvisited states. With object cycles, the comparison may need `is` rather than `in`. Checking only the items already on the list stops duplicates from waiting in the list. It does not stop a revisit of a state that was already removed from it:

```python
visited.add(front)
...proceed...
items.extend([x for x in front if x not in visited])
```

This model does not quite fit the number-adding example, but other programs can spot repeated states easily. A previously visited web page address is one example. The later examples in this section use these techniques to avoid cycles and repeats.

Some programs must record the full path to each state, so they can report a solution at the end. In that case, each item on the stack or queue can be a full path list. The list records every state visited so far. Its next item to explore sits at one end.

Python also limits the depth of its call stack. That limit catches infinite recursion before it exhausts memory. To allow deeper calls, use the `sys` module:

```
>>> import sys
>>> sys.getrecursionlimit()  # 1000 calls deep default
1000
>>> sys.setrecursionlimit(10000)  # Allow deeper nesting
>>> help(sys.setrecursionlimit)  # Read more about it
```

The highest setting you can use varies by platform. Programs that use explicit stacks or queues do not need a higher limit. They also lose the automatic catch for infinite recursion, so they may run forever instead.

### More recursion examples

The sum example is artificial, but its shape is common. Inheritance trees and module import chains have similar, general structures. Tools such as permutations can need arbitrarily many nested loops. The book uses recursion again in a permutation tool, a module import chain tool, class inheritance tree tools, and some end-of-part exercises that count down and compute factorials.

Several of these later examples detect states they have already visited, so they avoid cycles and repeats. Simple loops are still preferred for linear work. Recursion becomes essential for structures like these.

Unintended recursion is a risk too. Some operator-overloading methods, such as `__setattr__`, `__getattribute__`, and `__repr__`, can loop back on themselves when written badly. Recursion is powerful. It works best when you understand it and expect it.

## Function tools: introspection, attributes, and annotations

Functions are full objects, not just code for the compiler. They can be passed around, stored, and called indirectly. They also support operations that have little to do with calling them, such as attributes and annotations. This section looks at both sides of that picture.

### The first-class object model

Because functions are objects, you can treat them like any other value. A `def` statement assigns a function object to a name in the current scope. You can reassign that object to other names and call it through any of them:

```
>>> def exclaim(message):  # Name exclaim assigned to function object
...     print(message + '!')
>>> exclaim('Direct call')  # Call object through original name
Direct call!
>>> x = exclaim  # Now x references the function too
>>> x('Indirect call')  # Call object through name x by adding ()
Indirect call!
```

Arguments are passed by assignment, so you can pass a function to another function just as easily. The callee calls the passed-in function by adding parentheses:

```
>>> def generic(func, arg):
...     func(arg)  # Call the passed-in object by adding ()
>>> generic(exclaim, 'Argument call')
Argument call!
```

You can also store function objects in data structures, such as a list of tuples that works as an action table:

```
>>> schedule = [(exclaim, 'Hack'), (exclaim, 'Code')]
>>> for (func, arg) in schedule:
...     func(arg)  # Call functions embedded in containers
Hack!
Code!
```

Functions can also be created and returned for later use. The function made this way keeps state from its enclosing scope:

```
>>> def implore(verb):  # Make a function but don't call it
...     def exclaim(noun):
...         print(f'{verb} {noun}!')
...     return exclaim
>>> I = implore('Hack')  # Label in enclosing scope is retained
>>> I('Code')  # Call the function that make returned
Hack Code!
>>> I('App')
Hack App!
```

Python's first-class object model and its lack of type constraints make the language very flexible. The same few ideas keep coming back: a name, an object, and a call.

### Function introspection

Since functions are objects, you can inspect them with ordinary object tools. You already know that you can call a function. You can also look at its attributes:

```
>>> def func(a):
...     b = 'Hack'
...     return b * a
>>> func(8)
'HackHackHackHackHackHackHackHackHack'
>>> func.__name__
'func'
>>> dir(func)
'__annotations__', '__builtins__', '__call__', '__class__', '__closure__',
…more omitted: 38 total…
'__setattr__', '__sizeof__', '__str__', '__subclasshook__', '__type_params__']
```

Introspection gives you access to internals. Functions have attached code objects, which describe details such as local variables and arguments:

```
>>> func.__code__
<code object func at 0x103ef3910, file "<stdin>", line 1>
>>> func.__code__.co_varnames
('a', 'b')
>>> func.__code__.co_argcount
1
```

Tool writers use this information to manage functions. Decorators can use it to check arguments, which is shown later. Whether you write such tools or only use them, object introspection makes functions more useful.

### Attaching your own attributes

You can also attach your own attributes to a function. You create them with simple assignments, as you would with any object:

```
>>> def func(): pass
>>> func.count = 0
>>> func.count += 1
>>> func.count
1
>>> func.handles = 'Button-Press'
>>> func.handles
'Button-Press'
```

Python's own data on functions uses names that begin and end with double underscores, as in `__X__`. That convention keeps your names from clashing with Python's. You can check it:

```
>>> len(dir(func))
40
>>> [x for x in dir(func) if not x.startswith('__')]
['count', 'handles']
```

If you avoid Python's naming pattern, you can use a function's namespace as though it were your own scope. The same works for functions made with `lambda`:

```
>>> F = lambda: None
>>> len(dir(F))
38
>>> F.book = 'LP6E'
>>> F.book
'LP6E'
```

As the state-retention section showed, attributes can hold state directly on a function. Unlike nonlocal names, these attributes are reachable from anywhere the function is, even from outside its code. In a sense, they also emulate "static locals" from other languages. Those are variables local to a function whose values survive after it exits. An attribute belongs to the object, not to a scope, so the code must reach it through the function's name. The net effect is similar.

When factory functions create new function objects, each function gets its own attributes. That gives you multiple, changeable copies of state. It is a useful alternative to closures and class attributes.

### Function annotations

Annotations are arbitrary information about a function's arguments and result. They augment the function without changing how it runs. Python provides the syntax, but it does nothing with the annotations itself. They are attached to the function object as its `__annotations__` attribute, for other tools to read.

Third-party tools might use annotations for error checking or API directives. Type hinting also uses annotations. Type hints are optional, and Python does not enforce them.

Annotations are written only in `def` headers. For an argument, the annotation follows a colon after the name. For the return value, it follows a `->` after the closing parenthesis of the argument list:

```
>>> def func(a: 'hack', b: (1, 10), c: float) -> int:
...     return a + b + c
>>> func(1, 2, 3)
6
>>> func.__annotations__
{'a': 'hack', 'b': (1, 10), 'c': <class 'float'>, 'return': <class 'int'>}
```

Python stores these annotations in a dictionary. Argument names become keys. A return annotation uses the key `return`, which works because `return` cannot be an argument name. Each value is the result of its annotation expression.

Annotations are ordinary Python objects, so you can process them. This example annotates only two of three arguments, then loops over the results:

```
>>> def func(a: 'python', b, c: 3.12):
...     return a + b + c
>>> func(1, 2, 3)
6
>>> func.__annotations__
{'a': 'python', 'c': 3.12}
>>> for arg in func.__annotations__:
...     print(arg, '=>', func.__annotations__[arg])
a => python
c => 3.12
```

Defaults still work with annotations. The annotation and its colon come before the default and its equals sign:

```
>>> def func(a: 'hack' = 4, b: (1, 10) = 5, c: float = 6) -> int:
...     return a + b + c
>>> func(1, 2, 3)  # No defaults used
6
>>> func()  # a=4 + b=5 + c=6 (all defaults)
15
>>> func(1, c=10)  # 1 + b=5 + 10 (keywords work normally)
16
```

The spaces in a header are optional. You can write the same function without them, though that may hurt readability for some people:

```
>>> def func(a:'hack'=4, b:(1,10)=5, c:float=6)->int:
...     return a + b + c
>>> func(1, 2)  # 1 + 2 + c=6
9
```

Annotations are optional and uncommon. They can state constraints for types or values. Larger APIs might also use them to register information about a function's interface. Decorators offer a more general way to add that kind of information, outside the header. A short preview follows.

### Function decorators: a preview

Decorators augment other functions. The book covers them in full later, so this is only a preview. A decorator is applied with an `@` prefix placed above a `def`. The prefix rebinds the function's name to whatever the decorator returns:

```
@decorator
def func(args): ...
```

The syntax above is equivalent to this code, where `decorator` is a one-argument callable:

```
def func(args): ...
func = decorator(func)  # Rebind func to decorator's result
```

A decorator can wrap a function in an extra layer of code. This example adds a message before each call:

```python
def echo(F):
    def proxy(*args):
        print('calling', F.__name__)  # Add actions here
        return F(*args)  # Run decorated function
    return proxy

@echo
def func(x, y):  # Rebinds func = echo(func)
    print('I am running...', x, y)  # func is run by the proxy closure
```

```
>>> func(1, 2)  # Runs a proxy, which runs func
calling func
I am running... 1 2
```

Decorators can also take arguments, such as `@echo(args)`. Their use can overlap with annotations, because argument information can go to the decorator instead of the header. Decorators can also apply to classes, which is covered later.

Compared with annotations, decorators do not add syntax to function headers. They also support more than one role. Annotations often serve a single role, and optional type hinting already claims that role in programs that use it. Some type-hinting advocates have tried to remove other uses of annotations. Decorators face no such pressure, so they may be the safer bet. Both tools are limited mainly by your imagination.

Annotations and decorators work on `def` statements, but not on `lambda` expressions. The `lambda` form is limited by design, and the next section covers it.

## Anonymous functions with lambda

You met the `lambda` expression earlier. This section reviews the basics and goes a little deeper. Like `def`, a `lambda` creates a function to call later. The difference is that it returns the function object instead of assigning it to a name. That is why people call `lambda` an anonymous function. In practice, it inlines a small function definition or defers some code until later.

> Note: the name "lambda" intimidates people. It comes from the Lisp language, which took it from lambda calculus, a form of symbolic logic. In Python, `lambda` is just a keyword that starts an expression. That expression is an alternative way to write a function, but it has no statements, decorators, or annotations.

### lambda basics

The general form has the keyword `lambda`, zero or more arguments, and an expression after a colon:

```
lambda argument1, argument2,… argumentN : expression-using-arguments
```

The arguments follow the same rules as the arguments in a `def` header, without annotations. Parentheses are not allowed around the arguments. They are usually optional around the whole `lambda`, though some contexts need them. Functions made with `lambda` work the same as those made with `def`. The difference is in how they are written, and that difference makes `lambda` useful in special cases:

- A `lambda` is an expression, not a statement. It can appear where a `def` is not allowed, such as inside a list literal or a function call's arguments. It returns a function object, which you can assign to a name or use right where it appears.
- A `lambda` body is a single expression, not a block of statements. It works like the expression you would put in a `return` statement, without writing `return`. That makes `lambda` less general than `def`. This is by design, since `lambda` suits simple functions and `def` handles larger tasks.

Apart from those differences, `def` and `lambda` do the same work. A `def` makes a function like this:

```
>>> def func(x, y, z): return x + y + z
>>> func(2, 3, 4)
9
```

A `lambda` can do the same job if you assign its result to a name:

```
>>> func = lambda x, y, z: x + y + z
>>> func(2, 3, 4)
9
```

Here you assign the function object yourself, where a `def` would do that assignment automatically. Defaults and other argument-matching forms work in a `lambda` too:

```
>>> x = (lambda a='hack', b='python', c='code': a + b + c)
>>> x('write')
'writepythoncode'
```

A `lambda` body follows the same scope lookup rules as a `def`. It creates a local scope, and it can see names in enclosing functions, the module, and the built-in scope through the LEGB rule:

```
>>> def editions(title):  # title in enclosing scope
...     return (lambda e: title + ', ' + e)  # Return a function object
>>> labeler = editions('Learning Python')  # Make+save nested function
>>> labeler('6E')  # '6E' passed to e in lambda
'Learning Python, 6E'
```

### Why use lambda?

A `lambda` is a shorthand that lets you embed a function definition where it is used. It is entirely optional. You can always write a `def` instead, and you should when the function needs the power of full statements. A `lambda` fits when you only need a small piece of code inline, right where it will be used.

Callback handlers are a common example. They are often written as inline `lambda` expressions inside a registration call, rather than defined elsewhere and referred to by name. A GUI example appears later in this section.

A `lambda` is also common in jump tables. A jump table is a list or dictionary of actions to run on demand. Here is a list of three small functions:

```python
L = [lambda x: x * 2,  # Inline function definition
     lambda x: x ** 2,
     lambda x: x // 2]  # A list of three callable functions
for f in L:
    print(f(5))  # Prints 10, 25, and 2
print(L[1](5))  # Prints 25
```

This works because a `lambda` is an expression, so it fits inside a list literal. A `def` cannot go there, since it is a statement. The `def` version needs temporary names, which might clash with others. Its functions also sit apart from the place where they are used, sometimes hundreds of lines away:

```python
def f1(x): return x * 2
def f2(x): return x ** 2  # Define named functions
def f3(x): return x // 4  # Separate from their place of use
L = [f1, f2, f3]  # Reference by name
for f in L:
    print(f(2))  # Also prints 10, 25, and 2
```

### Multiway branches with dictionaries

You can do the same thing with dictionaries. A dictionary of `lambda` values builds an action table with a key for each branch:

```
>>> key = 'loop'
>>> {'hack': lambda s: s.upper(),
...  'code': lambda s: s.lower(),
...  'loop': lambda s: f'{s * 4}!'}[key]('Py')
'PyPyPyPy!'
```

Python builds the temporary dictionary first. Each nested `lambda` creates a function and leaves it there for later. Indexing by key fetches one function, and the parentheses call it. This pattern makes a dictionary a general multiway branch.

Without `lambda`, you would define three `def` statements elsewhere in the file and refer to them by name:

```
>>> def f1(s): return s.upper()
>>> def f2(s): return s.lower()
>>> def f3(s): return f'{s * 4}!'
>>> key = 'loop'
>>> {'hack': f1, 'code': f2, 'loop': f3}[key]('Py')
'PyPyPyPy!'
```

That also works, but the `def` statements may sit far away, even for tiny pieces of code. If the functions serve only one purpose, embedding them as `lambda` values keeps them close to their use. The `def` form also forces you to invent names that might clash with others.

The `match` statement gives similar results today. It can take even more code than the `def` version, and you would need to nest it inside a function to support an argument such as `s`. The earlier chapter on `if` statements has more detail.

> Note: you could skip the dispatch table when each function name matches its string key. Then `eval(key)(arg)` would start the call. That is sometimes useful, but `eval` is relatively slow, because it must compile and run code. It is also insecure, because you must trust the source of the string. Jump tables are usually replaced by polymorphic method dispatch in Python. Calling a method does the right thing based on the type of the object, with no switching logic needed.

### How (not) to obfuscate your Python code

A `lambda` body must be one expression, which seems to limit how much logic you can pack into it. If you know what you are doing, though, you can express most statements as expressions.

To print from a `lambda`, use `print` or `sys.stdout.write`. To run several actions, put them in a tuple, which evaluates its expressions from left to right. Tuples need parentheses in this context:

```
>>> series = lambda a, b: (print(a.upper()), print(b.lower()))  # > 1 actions
>>> ignore = series('Hack', 'Code')
HACK
code
```

To nest logic, use the `if`/`else` ternary expression, or the `and`/`or` combination. Here, the statement `if a: b else: c` can be written as either of these expressions. The second is only roughly the same:

```
b if a else c
((a and b) or c)
```

The ternary works inside a `lambda` too. This `lambda` picks the smaller of two values:

```
>>> lower = (lambda x, y: x if x < y else y)  # Ifs in lambda: ternary
>>> lower('bb', 'aa')
'aa'
>>> lower('aa', 'bb')
'aa'
```

To loop inside a `lambda`, use a list comprehension or `map`. Both are tools from earlier chapters:

```
>>> showall = lambda x: [print(y) for y in x]  # Loops in lambda: list comp
>>> t = showall(['lp5e', 'lp6e'])
lp5e
lp6e
>>> showall = lambda x: list(map(print, x))  # Loops in lambda: maps
>>> t = showall(('py3.3', 'py3.12'))
py3.3
py3.12
>>> showall = lambda x: print(*x, sep='', end='')  # Another option: *unpacking
```

Assignment is limited to the local scope of the function that the `lambda` makes. The `:=` named-assignment expression still works inside one, though the name does not persist after the call:

```
>>> namer = lambda x: (res := x + 1) + res  # Assignment in lambda: :=
>>> namer(2)
6
>>> res  # But it doesn't persist
NameError: name 'res' is not defined
```

Emulating statements with expressions has limits. You cannot assign nonlocal names this way. Tools such as the `setattr` built-in, the `__dict__` of a namespace, and methods that change mutable objects in place can sometimes stand in. They can also lead you into hard-to-read code quickly.

Use these tricks only as a last resort. Without care, they produce obfuscated code that is hard to read. Simple is better than complex, and explicit is better than implicit. Full statements are better than arcane expressions. That is why `lambda` is limited to expressions in the first place. If your logic is larger, use `def`. Keep `lambda` for small pieces of inline code. In moderation, these techniques can still be useful.

### Scopes in nested lambdas

As the scope section explained, `lambda` depends on enclosing-function lookup, the E layer of LEGB. A `lambda` inside a `def` can read the value that a name had in the enclosing function's call:

```
>>> def action(x):
...     return (lambda y: x + y)  # Make function, remember x
>>> act = action(99)
>>> act(2)  # Call what action returned
101
```

A `lambda` can also see names in an enclosing `lambda`. To see that, rewrite the example with `lambda` alone:

```
>>> action = (lambda x: (lambda y: x + y))  # lambda scopes nest too
>>> act = action(99)
>>> act(3)
102
>>> ((lambda x: (lambda y: x + y))(99))(4)  # Even if you don't save them
103
```

The nested `lambda` structure makes a function that makes a function when called. Both versions can read `x` from the enclosing scope. This works, but it is convoluted. For readability, nested `lambda` expressions are best avoided. A `def` cannot be nested inside a `lambda`, because the body must be an expression. That limit is a good thing.

### lambda callbacks in GUIs

A common use of `lambda` is an inline callback for Python's `tkinter` GUI library. The example below creates a button that prints a message when pressed. It assumes `tkinter` is available in your Python, which is the default on most PCs:

```python
from tkinter import Button, mainloop
x = Button(
    text='Press me',
    command=lambda: print('Tapped!'))
x.pack()
mainloop()  # This may be optional in some REPLs
```

The button's `command` argument receives a function made with `lambda`. The advantage over `def` is that the handler sits right inside the button-creation call. The `lambda` defers the work until the event occurs. The `print` runs on each press, not when the button is created. It effectively knows the string to write when the event happens. Real GUIs rarely print to a console, but the pattern is the same.

Nested function scope rules apply to `lambda` too. A `lambda` sees names in the functions it is coded in, so it rarely needs passed-in defaults. Loop variables are the exception. This also helps with the `self` argument in class methods. Here is a preview of that case, which belongs to the object-oriented part:

```python
class MyGui:
    def makewidgets(self):
        Button(command=lambda: self.onPress('Tapped!'))
    def onPress(self, message):
        ...use message...
```

Objects with `__call__` and bound methods also serve as callbacks. The same ideas apply to other GUI toolkits for Python, including Kivy, Toga, PyQt, and wxPython. `tkinter` gets the spotlight only because it ships with Python's standard library.

## Functional programming tools

Python supports several programming styles. Procedural code uses basic statements, object-oriented code uses classes, and functional code applies functions to data. The criteria for functional style are loose. By most measures, Python's functional toolbox includes first-class functions, closures, and anonymous `lambda` expressions. It also includes generators and comprehensions, which the next chapter expands on, and decorators.

The toolbox also has built-ins that apply functions to iterables for you. `map` calls a function on each item. `filter` selects items with a test function. `reduce` combines items pairwise with running results. The sections below survey these three.

### Mapping functions over iterables with map

Programs often apply one operation to each item in a sequence and collect the results. A `for` loop can do that. Here is a loop that adds 10 to each counter:

```
>>> counters = [1, 2, 3, 4]
>>> updated = []
>>> for x in counters:
...     updated.append(x + 10)  # Add 10 to each item
>>> updated, counters
([11, 12, 13, 14], [1, 2, 3, 4])
```

Because the pattern is so common, Python provides `map`. It applies a function to each item in an iterable and returns the results. Here, `map` calls a user-defined `inc` on each item:

```
>>> def inc(x): return x + 10  # Function to be run
>>> list(map(inc, counters))  # Collect call results
[11, 12, 13, 14]
```

The `map` function is an iterable that produces results on demand. A `list` call forces all of them to appear. `map` often appears with `lambda`, since the function passed in is usually small:

```
>>> list(map((lambda x: x + 3), counters))  # Function expression
[4, 5, 6, 7]
```

Each `map` call is equivalent to a `for` loop. You can write a general version yourself, though the built-in is always available and works the same way:

```
>>> def mymap(func, iter):
...     res = []
...     for x in iter: res.append(func(x))
...     return res
>>> list(map(inc, [1, 2, 3]))  # Built-in is an iterable
[11, 12, 13]
>>> mymap(inc, [1, 2, 3])  # Ours builds a list (see generators)
[11, 12, 13]
```

The built-in can do more. Given several sequences, it sends the items from each sequence in parallel, as separate arguments. The function must accept one argument per sequence:

```
>>> pow(3, 4)  # 3**4
81
>>> list(map(pow, [1, 2, 3], [2, 3, 4]))  # 1**2, 2**3, 3**4
[1, 8, 81]
```

A list comprehension can do the same work as `map`:

```
>>> list(map(inc, [1, 2, 3, 4]))
[11, 12, 13, 14]
>>> [inc(x) for x in [1, 2, 3, 4]]
[11, 12, 13, 14]
```

In some cases, `map` runs faster than a `for` loop, and it can need less code. However, `map` applies a function call to each item, which is less general than an arbitrary expression. It often needs a helper function or a `lambda`. Wrapping a comprehension in parentheses instead of square brackets creates a generator. That object produces values on request, which saves memory, much like `map` does.

### Selecting items with filter

`filter` works with a test function. It keeps the items for which the function returns a true result. Like `range`, it returns an iterable, so a `list` call shows all its results:

```
>>> list(range(-5, 5))
[-5, -4, -3, -2, -1, 0, 1, 2, 3, 4]
>>> list(filter((lambda x: x > 0), range(-5, 5)))
[1, 2, 3, 4]
```

`filter` is roughly equivalent to a `for` loop with an `if` test. It is built in, concise, and often fast:

```
>>> res = []
>>> for x in range(-5, 5):  # The statement equivalent of filter
...     if x > 0:  # Simple but slower today, probably
...         res.append(x)
>>> res
[1, 2, 3, 4]
```

A list comprehension with an `if` clause often gives simpler code. It also avoids creating a new function. A generator expression, written with parentheses, delays the results the same way. The next chapter covers generators in detail:

```
>>> [x for x in range(-5, 5) if x > 0]
[1, 2, 3, 4]
```

### Combining items with reduce

`reduce` is more complex. It takes an iterable, but it is not one itself. It returns a single value that combines the items. In modern Python, `reduce` lives in the `functools` module. These two calls compute the sum and the product of a list:

```
>>> from functools import reduce
>>> reduce((lambda x, y: x + y), [1, 2, 3, 4])
10
>>> reduce((lambda x, y: x * y), [1, 2, 3, 4])
24
```

At each step, `reduce` passes the running result and the next item to the function. By default, the first item in the sequence starts the running result. The `for` loop below does the same as the first call, with the addition built in:

```
>>> L = [1, 2, 3, 4]
>>> res = L[0]
>>> for x in L[1:]:
...     res += x
>>> res
10
```

You can write your own version of `reduce`. The function below copies most of the built-in's behavior, which helps show how it works:

```
>>> def myreduce(function, sequence):
...     tally = sequence[0]
...     for next in sequence[1:]:
...         tally = function(tally, next)
...     return tally
>>> myreduce((lambda x, y: x + y), [1, 2, 3, 4])
10
>>> myreduce((lambda x, y: x * y), [1, 2, 3, 4])
24
```

The built-in `reduce` also accepts an optional third argument. It serves as the starting value, and as the result when the sequence is empty. Try adding that to `myreduce` as an exercise.

The `operator` standard-library module offers functions that match Python's built-in expressions. It is handy with these tools:

```
>>> import operator, functools
>>> functools.reduce(operator.add, [2, 4, 6])  # Function-based +
12
>>> functools.reduce((lambda x, y: x + y), [2, 4, 6])
12
```

Taken together, `map`, `filter`, and `reduce` open up a powerful functional style. Many people also count nested closures, `lambda` expressions, generators, and comprehensions as part of that toolset.

## Chapter wrap-up

This part of the chapter covered function design guidelines, recursive functions, function attributes, annotations, and decorators. It also covered `lambda` expressions and the `map`, `filter`, and `reduce` built-ins. Some of these tools are advanced, but many are common in Python programs. Comprehensions and generators build on these functional tools next, so nothing here was a detour.

## Comprehensions: the final act

This part of the chapter finishes the story of comprehensions and iteration. The main subjects are generator functions and generator expressions. Both produce results on demand, the same way many built-in tools do. Generators follow the iteration protocol, and generator expressions reuse comprehension syntax, so this material extends the iteration ideas covered earlier. The chapter also gives a short start on `async` coroutines, which build on generators.

Python supports procedural, object-oriented, and functional programming. Its functional tools include closures, generators, `lambda`, comprehensions, `map`, decorators, and function objects. These tools apply and combine functions in flexible ways, and they often retain state in place of a class.

### A quick review of list comprehensions

Suppose you want the code points of every character in a string. The built-in `ord` function returns the integer code point of one character. A `for` loop can collect the results into a list:

```python
>>> res = []
>>> for x in 'text':
...     res.append(ord(x))  # Manual results collection
>>> res
[116, 101, 120, 116]
```

The `map` built-in can do the same job in one call, so you never manage the list yourself:

```python
>>> res = list(map(ord, 'text'))  # Apply function to iterable
>>> res
[116, 101, 120, 116]
```

A list comprehension gives the same results. While `map` maps a function over an iterable, a list comprehension maps an expression. The comprehension collects the value of the expression for each item and returns them in a new list:

```python
>>> res = [ord(x) for x in 'text']  # Apply expression to iterable
>>> res
[116, 101, 120, 116]
```

The square brackets remind you that the result is a list. Inside them, you write an expression that uses a variable, followed by a `for` header that names the same variable. You get one result for each pass of the implied loop.

Comprehensions are most convenient when you want an arbitrary expression instead of a function. Squaring the numbers from 0 to 9 is one example:

```python
>>> [x ** 2 for x in range(10)]  # Squares of numbers 0 to 9
[0, 1, 4, 9, 16, 25, 36, 49, 64, 81]
```

A `map` call needs a small function for the same job. You would usually write that function inline with `lambda`:

```python
>>> list(map((lambda x: x ** 2), range(10)))
[0, 1, 4, 9, 16, 25, 36, 49, 64, 81]
```

The `map` version is only a few keystrokes longer, and only slightly harder to read once you know `lambda`. For more advanced roles, comprehensions usually take much less typing.

An `if` clause after the `for` adds selection logic. A comprehension with an `if` clause works like the `filter` built-in, because it skips the items for which the test is false. This example picks the even numbers from 0 to 9, where `x % 2` is zero only for even values:

```python
>>> [x for x in range(10) if x % 2 == 0]
[0, 2, 4, 6, 8]
>>> list(filter((lambda x: x % 2 == 0), range(10)))
[0, 2, 4, 6, 8]
>>> res = []
>>> for x in range(10):
...     if x % 2 == 0:
...         res.append(x)
>>> res
[0, 2, 4, 6, 8]
```

The `filter` call is not much longer than the comprehension, even with its helper function. A comprehension can combine a filter and a map in one expression. This one collects the squares of the even numbers from 0 through 9:

```python
>>> [x ** 2 for x in range(10) if x % 2 == 0]
[0, 4, 16, 36, 64]
```

The `for` loop skips the numbers where the `if` clause is false. The expression on the left computes the squares of the rest. The same result with `map` and `filter` needs one nested expression:

```python
>>> list( map((lambda x: x**2), filter((lambda x: x % 2 == 0), range(10))) )
[0, 4, 16, 36, 64]
```

### Formal comprehension syntax

Comprehensions are more general than these examples show. The simplest form has an accumulation expression and one `for` clause:

```
[ expression for target in iterable ]
```

The other parts are optional. You can add any number of nested `for` clauses, and each can have its own `if` test that filters items. The full structure looks like this:

```
[ expression for target1 in iterable1 if condition1
  for target2 in iterable2 if condition2 ...
  for targetN in iterableN if conditionN ]
```

Set comprehensions and dictionary comprehensions use the same syntax, with curly braces. Generator expressions use it too, with parentheses that are often optional. A dictionary comprehension starts with two expressions separated by a colon, one for the key and one for the value.

When `for` clauses are nested, they work like nested `for` loops. This comprehension combines two lists:

```python
>>> res = [x + y for x in [0, 1, 2] for y in [100, 200, 300]]
>>> res
[100, 200, 300, 101, 201, 301, 102, 202, 302]
```

The statement version is much longer, but it has the same effect:

```python
>>> res = []
>>> for x in [0, 1, 2]:
...     for y in [100, 200, 300]:
...         res.append(x + y)
>>> res
[100, 200, 300, 101, 201, 301, 102, 202, 302]
```

A list comprehension builds a list, but it can loop over any iterable. This one walks over two strings and joins each pair of characters:

```python
>>> [x + y for x in 'orm' for y in 'ORM']  # 3 * 3 results
['oO', 'oR', 'oM', 'rO', 'rR', 'rM', 'mO', 'mR', 'mM']
```

Each `for` clause can have its own `if` filter, however deeply the loops nest. Code like the following becomes hard to picture past this level, so use it with care:

```python
>>> [x + y for x in 'orm' if x in 'ro' for y in 'ORM' if y > 'M']
['oO', 'oR', 'rO', 'rR']
>>> [x + y + z for x in 'hack' if x > 'c'
...            for y in 'CODE' if y in 'OD'
...            for z in '123' if z > '1']
['hO2', 'hO3', 'hD2', 'hD3', 'kO2', 'kO3', 'kD2', 'kD3']
```

The same filtering works on numbers. This comprehension pairs the even numbers from 0 through 4 with the odd numbers from 0 through 4:

```python
>>> [(x, y) for x in range(5) if x % 2 == 0
...         for y in range(5) if y % 2 == 1]
[(0, 1), (0, 3), (2, 1), (2, 3), (4, 1), (4, 3)]
```

The `if` clauses filter each pass of the loops. The statement version is:

```python
>>> res = []
>>> for x in range(5):
...     if x % 2 == 0:
...         for y in range(5):
...             if y % 2 == 1:
...                 res.append((x, y))
>>> res
[(0, 1), (0, 3), (2, 1), (2, 3), (4, 1), (4, 3)]
```

If a complex comprehension confuses you, nest its clauses as statements. Indent each clause one level further to the right. The result is longer, but many readers find its intent clearer at first glance. Writing the `map` and `filter` version of the last example would be deeply nested and hard to follow, so it is left as an exercise for the reader.

### Example: comprehensions and matrixes

Comprehensions are useful on real data too. A basic way to store a matrix in Python is a list of nested lists. These two 3 by 3 matrixes are defined that way:

```python
>>> M = [[1, 2, 3],
...      [4, 5, 6],
...      [7, 8, 9]]
>>> N = [[2, 2, 2],
...      [3, 3, 3],
...      [4, 4, 4]]
```

You can index rows, and items within rows, with normal index operations:

```python
>>> M[1]  # Row 2
[4, 5, 6]
>>> M[1][2]  # Row 2, item 3
6
```

Comprehensions process these structures well because they scan the rows and columns for you. The following collects the second column. The first version iterates over the rows, and the second uses offsets:

```python
>>> [row[1] for row in M]  # Column 2
[2, 5, 8]
>>> [M[row][1] for row in (0, 1, 2)]  # Using offsets
[2, 5, 8]
```

A diagonal is also easy to pull out. The first expression uses the same row and column index, so it picks `M[0][0]`, then `M[1][1]`, and so on. The second scales the column index to fetch `M[0][2]`, `M[1][1]`, and so forth. Both assume the matrix has the same number of rows and columns:

```python
>>> [M[i][i] for i in range(len(M))]  # Diagonals
[1, 5, 9]
>>> [M[i][len(M)-1-i] for i in range(len(M))]
[3, 5, 7]
```

Changing a matrix in place requires assignment to each offset. Use `range` twice when the rows have different lengths:

```python
>>> L = [[1, 2, 3], [4, 5, 6]]
>>> for i in range(len(L)):
...     for j in range(len(L[i])):  # Update in place
...         L[i][j] += 10
>>> L
[[11, 12, 13], [14, 15, 16]]
```

Comprehensions make new lists, so they cannot change a matrix directly. You can still assign their results back to the original name. This applies an operation to every item, giving either a flat vector or a matrix of the same shape:

```python
>>> [col + 10 for row in M for col in row]  # Assign to M to retain new value
[11, 12, 13, 14, 15, 16, 17, 18, 19]
>>> [[col + 10 for col in row] for row in M]
[[11, 12, 13], [14, 15, 16], [17, 18, 19]]
```

To understand these, translate each one to its statement form. Indent the parts further to the right in the expression, as in the first loop. Start a new list when comprehensions are nested on the left, as in the second loop. The second expression works because the row loop is the outer loop. For each row, the inner column loop builds one row of the result:

```python
>>> res = []
>>> for row in M:  # Statement equivalents
...     for col in row:  # Indent parts further right
...         res.append(col + 10)
>>> res
[11, 12, 13, 14, 15, 16, 17, 18, 19]
>>> res = []
>>> for row in M:
...     tmp = []  # Left-nesting starts new list
...     for col in row:
...         tmp.append(col + 10)
...     res.append(tmp)
>>> res
[[11, 12, 13], [14, 15, 16], [17, 18, 19]]
```

With some creativity, comprehensions can also combine values from several matrixes. The first pair of expressions multiplies the matrixes item by item. The first builds a flat list. The second builds the same values as a nested structure:

```python
>>> M
[[1, 2, 3], [4, 5, 6], [7, 8, 9]]
>>> N
[[2, 2, 2], [3, 3, 3], [4, 4, 4]]
>>> [M[row][col] * N[row][col] for row in range(3) for col in range(3)]
[2, 4, 6, 12, 15, 18, 28, 32, 36]
>>> [[M[row][col] * N[row][col] for col in range(3)] for row in range(3)]
[[2, 4, 6], [12, 15, 18], [28, 32, 36]]
```

The nested version works because the row loop is the outer loop again. It is equal to this statement code:

```python
res = []
for row in range(3):
    tmp = []
    for col in range(3):
        tmp.append(M[row][col] * N[row][col])
    res.append(tmp)
```

The `zip` built-in pairs items for multiplication. Both the comprehension and the loop below give the same nested result. Because `zip` produces its items one at a time, this is not as wasteful as it may seem:

```python
[[col1 * col2 for (col1, col2) in zip(row1, row2)] for (row1, row2) in zip(M, N)]
```

```python
res = []
for (row1, row2) in zip(M, N):
    tmp = []
    for (col1, col2) in zip(row1, row2):
        tmp.append(col1 * col2)
    res.append(tmp)
```

Compared with statements, the comprehension versions need only one line. They may run much faster on large matrixes, and they may also make your head spin. That leads to the next topic.

### When not to use comprehensions

Comprehensions are general enough that they can quickly become hard to read, especially when nested. Some tasks are complex by nature, and no syntax can make them simple. The permutations later in this chapter are a good example. Comprehensions are powerful when used wisely, and there is nothing wrong with using them in scripts.

Still, code like the nested examples above can add more complexity than it should. It also tends to attract people who assume that obscure code shows skill. Good software citizenship means keeping code clear for the people who must maintain it.

This book shows advanced comprehensions to teach you how they work. In real programs, though, clarity matters more than cleverness. A tricky comprehension may be a fun puzzle, but it is a poor choice for code that others must understand later.

The old rule KISS still applies: keep it simple. If you must translate a comprehension into simpler statements before you can understand it, the simpler statements should have been written in the first place.

### When to use comprehensions: speed and conciseness

In this case, the extra complexity can buy speed. Tests on current Python show that `map` calls and list comprehensions can be much faster than equivalent `for` loops. The gap varies by use case and Python version. It exists because `map` and comprehensions run at compiled-language speed inside the interpreter. A `for` loop runs its bytecode in the Python virtual machine, which is usually slower.

Comprehensions are also concise. That brevity helps when it does not hide meaning from the next programmer. Many people find that comprehensions give them a powerful tool. Because `map` calls and comprehensions are expressions, they can appear in places that `for` statements cannot, such as inside a `lambda` or an object literal.

Comprehensions and `map` calls are worth using for simple iterations, especially when speed matters. Both of these lines are easy to read and powerful:

```python
[line.rstrip() for line in open('myfile')]
map((lambda line: line.rstrip()), open('myfile'))
```

Matching the memory economy and timing of `map`, though, requires a comprehension coded as a generator expression. That is the next major topic.

## Generator functions and expressions

Python now favours delayed results. It provides tools that produce values only when they are needed, not all at once. Files read lines on request, and functions such as `map` and `zip` produce items on demand. Python programs can also define their own lazy operations. Two constructs delay result creation for user-defined code:

- Generator functions are coded with normal `def` statements, but they use `yield` statements to return results one at a time. They suspend and resume their state between results.
- Generator expressions are similar to the list comprehensions above. They return an object that produces results on demand instead of building a result list.

Neither construct builds a full list in memory. Both save memory and let computation be split across requests. This avoids pauses and allows very large or even infinite results. Both ultimately work by implementing the iteration protocol.

These features have existed since at least Python 2.2, and languages such as Icon explored similar ideas earlier. Generators are common in Python code today. They may seem unusual if you come from simpler models, but they are a powerful tool. They extend the function, comprehension, and iteration topics you have already studied, so you know more about them than you might expect.

### Generator functions: yield versus return

Earlier, you learned to write normal functions that take input parameters and return a single result right away. A function can also send back a value and later resume where it left off. These are generator functions, because they generate a series of values over time instead of stopping after one.

Generator functions look like normal functions, and they are coded with normal `def` statements. Python compiles them specially, though. When you call one, it does not return a final result. It returns a result generator that can appear in any iteration context. The iteration protocol you learned earlier explains how this works.

#### State suspension

Normal functions return a value and exit. Generator functions suspend and resume their execution and state around each value they produce. They are often a useful alternative to computing an entire series up front. They are also an alternative to saving and restoring state by hand in a class.

When a generator is suspended, it keeps its position in the code and its entire local scope. Its local variables keep their values between results. When the function resumes, those values are still available. In other words, the per-call local scope you studied earlier simply waits, intact, between yields.

The main difference between a generator and a normal function is the statement they use. A generator uses `yield` where a normal function uses `return`. The `yield` statement suspends the function and sends a value back to the caller. The function keeps enough state to resume later. When it resumes, it continues right after the last `yield` that ran. The code can then produce a series of values over time, instead of computing them all at once and returning them in a list.

#### Iteration protocol integration

Generator functions are closely tied to the iteration protocol. Iterator objects define a `__next__` method. That method either returns the next item, or raises the `StopIteration` exception to end the iteration. An iterable object gets its iterator with the `__iter__` method. For an object that is its own iterator, this step does nothing.

Python `for` loops and other iteration tools use this protocol to step through a sequence or a generator of values. If the protocol is not supported, iteration falls back on indexing the sequence repeatedly. Any object that supports the protocol works in all the iteration tools. The `iter` and `next` built-ins simplify manual iteration by calling the matching double-underscore method.

A function that contains a `yield` statement is compiled as a generator. It returns an object with the expected iteration methods. Each time you call it, it returns an iterable object. That object has a `__next__` method, which starts or resumes execution.

A generator can also use a `return` statement. Falling off the end of the `def` block works the same way. Both end the generation of values by raising `StopIteration`. A `return` can attach a value to that exception, through its `value` attribute. Iteration tools ignore this value, and few programs use it. From the caller's side, `__next__` runs the function until the next `yield` produces a result, or until `StopIteration` is raised.

In short, a `def` statement that contains `yield` automatically supports the iteration methods. You can use it in any iteration tool to produce results over time. A `yield` in a `def` is enough to make this happen. A `lambda` cannot do this, because it does not allow statements such as `yield`. That is one more reason to prefer `def`.

#### Generator functions in action

Generator functions are easier to see in code than to describe. This function produces the squares of a series of numbers over time:

```python
>>> def gensquares(n):
...     for i in range(n):
...         yield i ** 2  # Resume here later
```

Each time through the loop, the function yields a value and returns to its caller. When it is resumed, its prior state comes back. That includes the last values of `i` and `n`. Control continues right after the `yield` statement. In a `for` loop, the first iteration starts the function and gets its first result. After that, control returns to the function after its `yield` each time:

```python
>>> for i in gensquares(5):  # Resume the function
...     print(i, end=' ')  # Print last yielded value
0 1 4 9 16
```

A function ends the generation of values with a `return` statement. It can also simply reach the end of its body. As noted, `return` can attach a value to the exit exception, but usually does not.

This process can seem implicit at first, almost magical. It is actually concrete. To see what happens inside the `for`, call the generator function directly:

```python
>>> x = gensquares(3)  # Generator of 0..2 squares
>>> x
<generator object gensquares at 0x10dc6d700>
```

The call returns a generator object that supports the iteration protocol. The generator function was compiled to return this object automatically. The object has a `__next__` method. That method starts the function or resumes it from the last `yield`. When the series ends and the function returns, it raises `StopIteration`. The call `next(X)` is a convenience that calls `X.__next__()`:

```python
>>> next(x)  # Run to first yield
0
>>> next(x)  # Resume after yield, run to next yield
1
>>> next(x)  # Resume after yield, run to next yield
4
>>> next(x)  # Resume after yield, exception on return
StopIteration
```

Iteration tools, including `for` loops, work with generators the same way. They call `__next__` again and again until the exit exception is caught. For generators, the yielded values arrive over time.

Generators do not need an `iter` call at the top. A generator is its own iterator, and it supports one active scan. The `iter` method returns the generator itself, and `next` works on it directly. The same is true for the generator expressions covered later:

```python
>>> y = gensquares(5)  # Returns a generator which is its own iterator
>>> iter(y) is y  # iter() is not required: a no-op here
True
>>> next(y)  # Can run next() immediately
0
```

#### Why generator functions?

The simple example here may make you wonder why you would write a generator at all. You could build the full list of squares in one step:

```python
>>> def buildsquares(n):
...     res = []
...     for i in range(n): res.append(i ** 2)
...     return res
>>> for x in buildsquares(5): print(x, end=' ')
0 1 4 9 16
```

You could also use a `for` loop, a `map` call, or a list comprehension:

```python
>>> for x in [n ** 2 for n in range(5)]:
...     print(x, end=' ')
0 1 4 9 16
>>> for x in map((lambda n: n ** 2), range(5)):
...     print(x, end=' ')
0 1 4 9 16
```

Generators can be better for memory use and performance in larger programs. They avoid doing all the work up front. This matters most when result lists are large, or when each value takes a lot of computation. Generators spread the time needed for the values across loop iterations. They can even produce a series with no end, an infinite result.

For more advanced uses, generators can replace manual state saving in class objects. The variables in a function's scopes are saved and restored automatically. You will be able to judge this contrast after the class-based iterables are covered in more detail.

Generator functions are also broader than they look so far. They can operate on and return any type of object. As iterables, they work with every iteration tool, including `tuple` calls, `enumerate`, and dictionary comprehensions:

```python
>>> def ups(line):
...     for sub in line.split(','):  # Substring generator
...         yield sub.upper()
>>> tuple(ups('aaa,bbb,ccc'))  # All iteration contexts
('AAA', 'BBB', 'CCC')
>>> {i: s for (i, s) in enumerate(ups('aaa,bbb,ccc'))}
{0: 'AAA', 1: 'BBB', 2: 'CCC'}
```

Generator expressions offer the same benefits, and you will see them shortly. Generators can also make impractical tasks possible. They produce parts of results that would be far too large to create all at once. First, though, let us look at some advanced generator features.

#### Extended generator protocol: send versus next

Python 2.5 added a `send` method to the generator protocol. The `send` method advances to the next item, just like `__next__`. It also lets the caller send a value into the generator, which can change how the generator runs.

Technically, `yield` is an expression that returns the value passed to `send`. It is usually written as a statement. When you use it as an expression, you must put it in parentheses, unless it is the only item on the right side of an assignment. `X = yield Y` is valid, and so is `X = (yield Y) + Z`.

When you use this protocol, you send a value into generator `G` by calling `G.send(value)`. The generator resumes, and the `yield` expression returns the value that was sent. If you advance with the regular `G.__next__()` method, or with `next(G)`, the `yield` simply returns `None`. Here is an example:

```python
>>> def gen():
...     for i in range(10):
...         X = yield i
...         print('=>', X)
>>> G = gen()
>>> next(G)  # Must call next() first, to start generator
0
>>> G.send(77)  # Advance, and send value to yield expression
=> 77
1
>>> G.send(88)
=> 88
2
>>> next(G)  # next() and X.__next__() send None
=> None
3
```

The `send` method has practical uses. A caller can stop a generator by sending a termination code, or redirect it by passing a new position in the data being processed.

Generators also support a `throw(type)` method. It raises an exception inside the generator at the latest `yield`. The `close` method raises a special `GeneratorExit` exception inside the generator, which ends the iteration. Together with `send`, these advanced features make generators behave more like coroutines. The `async` syntax later took over part of that role. This chapter does not go further. Python's standard manuals cover the details, and exceptions are covered in a later part.

One distinction is easy to miss. `next(X)` is a built-in that calls `X.__next__()` for any iterable. Other generator methods, such as `send`, must be called directly on a generator object, as in `G.send(X)`. Those methods exist only on built-in generator objects. The `__next__` method applies to all iterable objects, including user-defined classes.

#### The yield from extension

Python 3.3 added a `yield from` form. It lets a generator delegate to nested generators, which are called subgenerators. In simple cases, it is equal to a yielding `for` loop. This example uses `list` to force a generator to produce values from two sources:

```python
>>> def both(N):
...     for i in range(N): yield i
...     for i in map(lambda x: x ** 2, range(N)): yield i
>>> list(both(5))
[0, 1, 2, 3, 4, 0, 1, 4, 9, 16]
```

The `yield from` form is shorter and, once you are used to it, more explicit. It supports all the usual generator contexts. In the next example, `both` is the delegating generator. The `range` and `map` built-ins serve as subgenerators. A generator expression with `join` also appears here:

```python
>>> def both(N):
...     yield from range(N)
...     yield from map(lambda x: x ** 2, range(N))
>>> list(both(5))
[0, 1, 2, 3, 4, 0, 1, 4, 9, 16]
>>> ' : '.join(str(i) for i in both(5))
'0 : 1 : 2 : 3 : 4 : 0 : 1 : 4 : 9 : 16'
```

The `yield from` form also supports chains of generators. In this example, two generators delegate to others. The last one in the chain uses `yield` to send results up through the chain:

```python
>>> def c(n):
...     yield n * 8  # The bottom of the "chain"
...     yield n ** 2
>>> def b(n):
...     yield from c(n)  # Delegate to subgenerator
>>> def a(n):
...     yield from b(n)  # Delegate to subgenerator
>>> g = a(4)  # Make top generator, fetch results
>>> g
<generator object a at 0x10bd17940>
>>> next(g)
32
>>> for i in a(4): print(i)  # Force results production
32
16
```

In more advanced cases, a subgenerator can receive sent and thrown values from the caller of the delegating generator. It can also return a final value to the delegating generator, as the result of the `yield from` expression. A generator can be split into subgenerators much like a function is split into subfunctions. The code still behaves as though it were written inline where `yield from` appears.

This is uncommon and beyond the scope of this chapter, so Python's standard manuals are the place for details. An `async def` coroutine is related: its `await` works something like a generator's `yield from`, with a handoff to an event loop. That idea returns later in this chapter.

### Generator expressions: iterables meet comprehensions

Generator functions are useful because they delay evaluation. Later Python versions combined that idea with comprehensions to create generator expressions. Their syntax matches list comprehensions, including `if` filters and nested `for` loops. The difference is the enclosing parentheses instead of square brackets. Like tuples, their parentheses are often optional:

```python
>>> [x ** 2 for x in range(5)]  # List comprehension: build a list
[0, 1, 4, 9, 16]
>>> (x ** 2 for x in range(5))  # Generator expression: make an iterable
<generator object <genexpr> at 0x109607ac0>
```

Wrapping a generator expression in a `list` call forces it to produce all its results in a list at once. That is equal to a list comprehension, in function if not in speed:

```python
>>> list(x ** 2 for x in range(5))  # List comprehension equivalence
[0, 1, 4, 9, 16]
```

The two forms behave very differently in memory. A generator expression does not build the list. It returns a generator object, which is an iterable created automatically. That object yields one item at a time in any iteration tool. It also keeps its state between results, including the variable `x` and its position in the code.

The net effect resembles a generator function, but packed inside a comprehension expression. You get an object that remembers where it left off after each result. Like generator functions, it supports the protocol, and you can inspect that protocol directly. The `iter` call is again optional at the top level:

```python
>>> G = (x ** 2 for x in range(3))
>>> iter(G) is G  # iter(G) optional: __iter__ returns self
True
>>> next(G)  # Generator objects: automatic methods
0
>>> next(G)
1
>>> next(G)
4
>>> next(G)
StopIteration
>>> G
<generator object <genexpr> at 0x109607920>
```

You rarely see the `next` machinery in everyday code. A `for` loop calls `next` for you:

```python
>>> for num in (x ** 2 for x in range(3)):  # Calls next() automatically
...     print(num, num / 2.0, sep=', ')
0, 0.0
1, 0.5
4, 2.0
```

Every iteration tool uses this protocol. That includes `for` loops, the `list` call above, all kinds of comprehensions, the `map` and `filter` functional tools, and the built-ins `sum`, `sorted`, `any`, and `all`. Generator expressions work in all of them, just like sequences and generator-function results.

The `join` method and tuple assignment both iterate. This example uses generator expressions in both. With an empty-string delimiter, `join` concatenates the values its iterable produces:

```python
>>> ''.join(x.upper() for x in 'aaa,bbb,ccc'.split(','))
'AAABBBCCC'
>>> a, b, c = (x + '\n' for x in 'aaa,bbb,ccc'.split(','))
>>> a, c
('aaa\n', 'ccc\n')
```

The `join` call does not need extra parentheses around its generator. When a generator expression is the only argument in a function call, its parentheses can be shared with the call. Other cases need parentheses, even when they look extra. The second `sorted` call below is one of them:

```python
>>> sum(x ** 2 for x in range(3))  # Parens optional
5
>>> sorted(x ** 2 for x in range(3))  # Parens optional
[0, 1, 4]
>>> sorted((x ** 2 for x in range(3)), reverse=True)  # Parens required!
[4, 1, 0]
```

Tuples also use optional parentheses, and there is no widely accepted rule for either. A generator expression has a less clear role than a fixed collection like a tuple. Extra parentheses may seem more pointless here.

### Why generator expressions?

Generator expressions save memory, like generator functions do. They do not build the entire result list before the caller can use it. They also divide the work into smaller time slices. They yield results piece by piece, instead of making the caller wait for the full set.

Generator expressions often run slower than list comprehensions today, though. They are best reserved for very large result sets, or for programs that cannot wait for full results. A firm statement about performance has to wait for the timing scripts in the next chapter.

Generator expressions also offer real coding advantages, and the next sections show them.

#### Generator expressions versus map

It is worth setting generator expressions beside the other functional tools, as we did for list comprehensions. A generator expression often does the same job as a `map` call, because both hand back result items on request. Where the operation is not a function call, the generator expression is simpler, just as a list comprehension is:

```python
>>> list(map(abs, (-1, -2, 3, 4)))  # Map function on tuple
[1, 2, 3, 4]
>>> list(abs(x) for x in (-1, -2, 3, 4))  # Generator expression
[1, 2, 3, 4]
>>> list(map(lambda x: x * 2, (1, 2, 3, 4)))  # Nonfunction case
[2, 4, 6, 8]
>>> list(x * 2 for x in (1, 2, 3, 4))  # Simpler as generator?
[2, 4, 6, 8]
```

Text processing shows the same pattern, as in the `join` call above. A list comprehension builds a temporary list that nobody keeps, which is pure waste here. A `map` call loses its edge in simplicity the moment the operation stops being a function call:

```python
>>> line = 'aaa,bbb,ccc'
>>> ''.join([x.upper() for x in line.split(',')])  # Makes temporary list
'AAABBBCCC'
>>> ''.join(x.upper() for x in line.split(','))  # Generates results
'AAABBBCCC'
>>> ''.join(map(str.upper, line.split(',')))  # Generates results
'AAABBBCCC'
>>> ''.join(x * 2 for x in line.split(','))  # Simpler as generator?
'aaaaaabbbbbbcccccc'
>>> ''.join(map(lambda x: x * 2, line.split(',')))
'aaaaaabbbbbbcccccc'
```

Both `map` and generator expressions can be nested, with a `list` call or another iteration tool setting the chain in motion. The list comprehension below matches the `map` and generator versions that follow it. It builds two physical lists, though. The other two forms generate one integer at a time through nested generators, and the generator form may show its intent more clearly:

```python
>>> [x * 2 for x in [abs(x) for x in (-1, -2, 3, 4)]]  # Nested list comps
[2, 4, 6, 8]
>>> list(map(lambda x: x * 2, map(abs, (-1, -2, 3, 4))))  # Nested maps
[2, 4, 6, 8]
>>> list(x * 2 for x in (abs(x) for x in (-1, -2, 3, 4)))  # Nested generators
[2, 4, 6, 8]
```

All three combine operations, and the generator versions do it without building temporary lists. The next example nests and combines generators. The inner generator expression is driven by `map`, which is driven by `list`:

```python
>>> import math
>>> list(map(math.sqrt, (x ** 2 for x in range(4))))  # Nested combos
[0.0, 1.0, 2.0, 3.0]
```

The `range` on the right is also a generator of values, driven by the generator expression. That gives three levels of value generation. Each level produces values from inner to outer, only when asked. This works because of Python's iteration tools and protocol. Generator nesting can go as deep as you like, though some nestings are more sensible than others:

```python
>>> list(map(abs, map(abs, map(abs, (-1, 0, 1)))))  # Nesting gone bad?
[1, 0, 1]
>>> list(abs(x) for x in (abs(x) for x in (abs(x) for x in (-1, 0, 1))))
[1, 0, 1]
```

These examples are deliberately convoluted, to show how general generators can be. They also show that generator expressions can be abused just as list comprehensions can. Keep them simple unless the problem truly needs complexity.

Used well, generator expressions combine the expressiveness of comprehensions with the memory benefits of other iterables. These unnested versions are simpler, and they still use generators:

```python
>>> list(abs(x) * 2 for x in (-1, -2, 3, 4))  # Same, unnested
[2, 4, 6, 8]
>>> list(math.sqrt(x ** 2) for x in range(4))  # Flat may be better
[0.0, 1.0, 2.0, 3.0]
>>> list(abs(x) for x in (-1, 0, 1))
[1, 0, 1]
```

#### Generator expressions versus filter

Generator expressions support all the usual comprehension syntax, including `if` clauses. An `if` clause works like the `filter` call. `filter` returns its results on request, so a generator expression with an `if` clause does the same job. In the next example, `join` forces all the forms to produce their results:

```python
>>> line = 'aa bbb c'
>>> ''.join(x for x in line.split() if len(x) > 1)  # Generator with if
'aabbb'
>>> ''.join(filter(lambda x: len(x) > 1, line.split()))  # Equivalent filter
'aabbb'
```

The generator is only slightly simpler than the `filter` here. Once you add a processing step, though, `filter` needs a `map` as well. That makes it much more complex:

```python
>>> ''.join(x.upper() for x in line.split() if len(x) > 1)
'AABBB'
>>> ''.join(map(str.upper, filter(lambda x: len(x) > 1, line.split())))
'AABBB'
```

Generator expressions give you general structures that do not rely on functions, and they still delay result production. A generator expression always has a statement equivalent, though that equivalent can take much more code:

```python
>>> res = ''
>>> for x in line.split():  # Statement equivalent?
...     if len(x) > 1:  # This is also a join
...         res += x.upper()
>>> res
'AABBB'
```

This statement form is not quite the same, though. It cannot produce items one at a time, and it builds the whole result at once, much as a `join` does. The true equivalent of a generator expression is a generator function with `yield`, which the next section shows.

#### Generator functions versus generator expressions

Let us recap the ground this section covered. A `def` statement that contains a `yield` becomes a generator function. Calling it returns a new generator object. That object keeps its local scope and its code position. It has an automatically created `__iter__` method, which returns the object itself. It also has an automatically created `__next__` method. That method starts the function or resumes it where it last left off. It raises `StopIteration` when it finishes producing results.

A comprehension in parentheses is a generator expression. When it runs, it returns a new generator object. That object has the same automatic methods and the same state retention as a generator-function call. Its `__iter__` returns itself, and its `__next__` starts or resumes the implied loop. It raises `StopIteration` when the results are done.

The net effect is that both forms produce results on demand, in every iteration tool that uses them. The same iteration can often be coded either way. This generator expression repeats each character in a string four times:

```python
>>> G = (c * 4 for c in 'hack')  # Generator expression
>>> list(G)  # Force generator to produce results
['hhhh', 'aaaa', 'cccc', 'kkkk']
```

The equivalent generator function needs a little more code. Its block of statements can hold more logic and more state. This is much like the earlier trade-off between `lambda` and `def`, where a single expression is concise and a block of statements is more powerful:

```python
>>> def timesfour(S):  # Generator function
...     for c in S:
...         yield c * 4
>>> G = timesfour('hack')
>>> list(G)  # Iterate automatically
['hhhh', 'aaaa', 'cccc', 'kkkk']
```

To their callers, the two forms look much alike. Both support automatic and manual iteration. The `list` call above iterates automatically. The following code iterates manually, first with an expression and then with a function:

```python
>>> G = (c * 4 for c in 'hack')
>>> I = iter(G)  # Iterate manually (expression)
>>> next(I)
'hhhh'
>>> next(I)
'aaaa'
>>> G = timesfour('hack')
>>> I = iter(G)  # Iterate manually (function)
>>> next(I)
'hhhh'
>>> next(I)
'aaaa'
```

Either way, Python creates a generator object. It has the methods the iteration protocol needs, and it keeps state for the variables in its code and for its current position. You need a new generator to iterate again. The next section explains why generators are single-pass iterators.

Before that, here is the statement equivalent of the expression at the end of the last section. It is a function that yields values. The difference does not matter when the code uses a tool such as `join` to produce all the results:

```python
>>> line = 'aa bbb c'
>>> ''.join(x.upper() for x in line.split() if len(x) > 1)  # Expression
'AABBB'
>>> def gensub(line):  # Function
...     for x in line.split():
...         if len(x) > 1:
...             yield x.upper()
>>> ''.join(gensub(line))  # But why generate?
'AABBB'
```

Generators have valid roles. In a case like this, though, a generator is hard to justify over a simple statement. If `join` consumes the results right away, plain loops are enough. Stylistically, four lines of statements compared with one generator expression can still seem worth the change to many programmers.

## Generator odds and ends

The topics that follow are smaller, but they explain behaviour you will meet in the larger examples. Read them with that in mind.

### Generators are single-pass iterables

Generator functions and generator expressions return objects that are their own iterators. They support just one active iteration. Unlike some built-in types, you cannot hold several iterators of one generator at different positions in the stream. A generator's iterator is the generator itself. Calling `iter` on a generator expression or function is therefore an optional no-op:

```python
>>> G = (c * 4 for c in 'hack')
>>> iter(G) is G  # My iterator is myself: G has __next__
True
```

If you iterate over a generator's results manually with several iterators, they all share one position:

```python
>>> G = (c * 4 for c in 'hack')  # Make a new generator
>>> I1 = iter(G)  # Iterate manually
>>> next(I1)
'hhhh'
>>> next(I1)
'aaaa'
>>> I2 = iter(G)  # Second iterator at same position!
>>> next(I2)
'cccc'
```

Once any iteration runs to completion, all of them are exhausted. You need a new generator to start again:

```python
>>> list(I1)  # Collect the rest of I1's items
['kkkk']
>>> next(I2)  # Other iterators exhausted too
StopIteration
>>> I3 = iter(G)  # Ditto for new iterators
>>> next(I3)
StopIteration
>>> I3 = iter(c * 4 for c in 'hack')  # New generator to start over
>>> next(I3)
'hhhh'
```

Generator functions behave the same way. The `def` version below supports one active iterator, and it is used up after a single pass:

```python
>>> def timesfour(S):
...     for c in S:
...         yield c * 4
>>> G = timesfour('hack')  # Generator functions work the same way
>>> iter(G) is G  # One scan per generator (call)
True
>>> I1, I2 = iter(G), iter(G)
>>> next(I1)
'hhhh'
>>> next(I1)
'aaaa'
>>> next(I2)  # I2 at same position as I1
'cccc'
```

Built-in objects such as lists behave differently. A list supports multiple iterators and multiple passes. Its in-place changes also show up in active iterators:

```python
>>> L = [1, 2, 3, 4]
>>> I1, I2 = iter(L), iter(L)
>>> next(I1)
1
>>> next(I1)
2
>>> next(I2)  # Lists support multiple iterators
1
>>> del L[2:]  # Changes reflected in iterators
>>> next(I1)
StopIteration
```

These simple examples hide why this matters. If you need to scan a generator's values more than once, you must do one of two things. You can create a new generator for each scan, or build a list that you can rescan. A generator's values are used up after a single pass, and no amount of rewinding brings them back.

Class-based iterables also decide how many scans they support. Objects that allow multiple scans return a separate helper object from `iter`, instead of returning themselves.

### Generation in built-ins and classes

Many built-in types generate values too. You have already seen that dictionaries and files do. Looping over a dictionary yields its keys, and looping over a file yields its lines:

```python
for key in dictionary: ...
for line in file: ...
```

Many standard-library tools also generate values. The directory walker `os.walk` is one example. At each level of a folder tree, it yields a tuple. The tuple holds the current directory, its subdirectories, and its files. This loop finds the `.py` files in the parent directory and below:

```python
>>> import os
>>> for (root, subs, files) in os.walk('..'):  # Directory-walk generator
...     for name in files:  # A Python 'find' operation
...         if name.endswith('.py'):  # Also os.path.join(root, name)
...             print(root, name)
../Chapter02 script0.py
../Chapter03 myfile.py
../Chapter03 script1.py
...
```

The current Python version of `os.walk` uses `yield` to return results. It is therefore a normal generator function. It is iterable and produces a three-item tuple on each iteration:

```python
>>> G = os.walk('..')  # A single-scan iterator: iter(G) optional
>>> next(G)
('..', ['Chapter02', 'Chapter03', 'Chapter04', ...etc... 'Chapter37'], [])
>>> next(G)
('../Chapter02', ['__pycache__'], ['script0.py'])
```

The walker yields results as it goes, so callers do not wait for an entire tree to be scanned. Python's manuals cover this tool in more depth.

You can also write your own generator objects with classes that follow the iteration protocol. Such a class defines `__iter__` and `__next__` methods, which support the protocol:

```python
class SomeIterable:
    def __iter__(self):
        return self  # On iter(): return self or supplemental object

    def __next__(self):
        ...  # On next(): coded here, or in another class
```

A class like this usually returns itself for single-pass behaviour. For multiple scans, it returns a supplemental object that holds scan-specific state. Alternatively, a class's `__iter__` can use `yield` to turn itself into a generator. A `__getitem__` indexing method is also available as a fallback for iteration, with trade-offs covered later. Class-based iterables are a later topic, so the full iterator and generator story waits until the chapters on classes.

### Comprehensions versus type calls and generators

This chapter has focused on list comprehensions and generators. Two other comprehension forms exist: set comprehensions and dictionary comprehensions. Here is a summary of all the comprehension forms:

```python
>>> [x * x for x in range(10)]  # List comprehension: builds list
[0, 1, 4, 9, 16, 25, 36, 49, 64, 81]  # Fixed order, made all at once
>>> (x * x for x in range(10))  # Generator expression: yields items
<generator object <genexpr> at 0x100a1f920>
>>> {x * x for x in range(10)}  # Set comprehension: builds set
{0, 1, 64, 4, 36, 9, 16, 49, 81, 25}  # Random order, no duplicates
>>> {x: x * x for x in range(10)}  # Dict comprehension: insert order
{0: 0, 1: 1, 2: 4, 3: 9, 4: 16, 5: 25, 6: 36, 7: 49, 8: 64, 9: 81}
```

All of these forms use the same comprehension syntax. Their delimiters, and the key for dictionaries, show their different roles. List, set, and dictionary comprehensions are shorthand for passing a generator expression to a type name. Each of those types accepts any iterable, so a generator works there too:

```python
>>> list(x ** 2 for x in range(10))  # Generator plus type name
[0, 1, 4, 9, 16, 25, 36, 49, 64, 81]
>>> set(x * x for x in range(10))  # Similar to a set comprehension
{0, 1, 64, 4, 36, 9, 16, 49, 81, 25}
>>> dict((x, x * x) for x in range(10))
{0: 0, 1: 1, 2: 4, 3: 9, 4: 16, 5: 25, 6: 36, 7: 49, 8: 64, 9: 81}
```

Do not read too much into these equivalences. Implementations can vary, so collect performance data before you adopt an alternative. Generators are slower than the equivalent list comprehension today, and the next chapter proves it. Programs that run many of them may need to care.

### Scopes and comprehension variables

The loop variable in a comprehension is local to the expression. The chapter on scopes described this. The loop variable does not clash with names outside the comprehension, and it is not visible outside. A `for` statement behaves differently and does not localize its variable:

```python
>>> X = 99
>>> [X for X in range(5)]  # All comprehensions localize loop variables
[0, 1, 2, 3, 4]
>>> X  # Enclosing-scope X was not changed
99
>>> for X in range(5): pass  # But loop statements do not localize!
>>> X
4
```

A loop variable in a comprehension lives in a further nested scope of its own. Other names inside the expression still follow the usual LEGB lookup rules. In this generator, `Z` is local to the comprehension. `Y` comes from the enclosing function, and `X` comes from the global scope:

```python
>>> X = 'aaa'
>>> def func():
...     Y = 'bbb'
...     print('-'.join(Z for Z in X + Y))  # Z=comprehension, Y=local, X=global
>>> func()
a-a-a-b-b-b
```

There is one exception, and it is easy to miss. Names assigned with the `:=` expression inside a comprehension do leak out. They behave as though they were assigned in the scope that contains the comprehension:

```python
>>> S = 'hack'
>>> [(temp := S[i]) + temp.upper() for i in range(len(S))]
['hH', 'aA', 'cC', 'kK']
>>> temp
'k'
>>> i
NameError: name 'i' is not defined. Did you mean: 'id'?
```

This lets comprehensions both reuse and export values. Be careful, though, because it can be less clear than a simple assignment. A `lambda` body has its own local scope, which plugs this leak. In the next example, `temp` lives only inside the `lambda`:

```python
>>> del temp
>>> f = lambda: [(temp := S[i]) + temp.upper() for i in range(len(S))]
>>> f()
['hH', 'aA', 'cC', 'kK']
>>> temp
NameError: name 'temp' is not defined
```

A later example uses this `:=` nesting in a sequence scrambler. Chapter 11 has more background on `:=` named assignment.

### Generating "infinite" results

Generators can produce "infinite" results, which lists cannot. The phrase sounds more impressive than the reality. A generator keeps yielding values from the local variables in its retained state. It continues until its caller stops asking:

```python
>>> def squares(n):
...     while True:  # Generate results "forever"
...         yield n ** 2  # Or until no more next calls...
...         n += 1
>>> G = squares(2)
>>> next(G)
4
>>> next(G)
9
>>> for i in range(10): print(next(G), end=' ')
16 25 36 49 64 81 100 121 144 169
```

Narrow roles suit this pattern, such as generating test parameters. A list comprehension cannot compete here, because it must collect all its results at once. In practice generators are finite: they stop when the caller does. Next, some code that is more concrete.

## Generator examples: shuffling and permuting sequences

These examples put iteration and generation to work. Earlier, a testing function scrambled the order of the arguments used to check the intersection and union functions. That testing function could itself be a generator of values. Now that generators are understood, this becomes a practical application.

One caution before we start. The examples slice and concatenate objects, so they work only on sequences such as strings and lists. They do not work on arbitrary iterables such as files, `map` objects, or other generators. Some examples are generators themselves, yet they cannot take generators as input. If you need to pass in a generator, wrap it in a `list` call first.

### Scrambling sequences

First, a review. Earlier we reordered a sequence by slicing and concatenation. Each loop moved the front item to the end. Slicing, rather than indexing, lets `+` work on any sequence type:

```python
>>> L, S = [1, 2, 3], 'code'
>>> for i in range(len(S)):  # Coding 1: for repeat counts 0..3
...     S = S[1:] + S[:1]  # Move front item to the end
...     print(S, end=' ')
odec deco ecod code
>>> for i in range(len(L)):
...     L = L[1:] + L[:1]  # Slice so any sequence type works
...     print(L, end=' ')
[2, 3, 1] [3, 1, 2] [1, 2, 3]
```

You can get the same results another way. Move an entire front section to the end. The order of the results varies slightly:

```python
>>> for i in range(len(S)):  # Coding 2: for positions 0..3
...     X = S[i:] + S[:i]  # Rear part + front part (same effect)
...     print(X, end=' ')
code odec deco ecod
```

Trace this code to see how it works. Each version produces `N` results for an `N`-item sequence.

### Simple functions

This code works on specific named variables and only prints its results. You can generalise it into a normal function, one that works on any argument and returns its result for other uses. The first version below is the classic list comprehension pattern. The second version uses a comprehension, which saves some work:

```python
>>> def scramble(seq):
...     res = []
...     for i in range(len(seq)):
...         res.append(seq[i:] + seq[:i])
...     return res
>>> scramble('code')
['code', 'odec', 'deco', 'ecod']
>>> def scramble(seq):
...     return [seq[i:] + seq[:i] for i in range(len(seq))]
>>> scramble('code')
['code', 'odec', 'deco', 'ecod']
>>> for x in scramble((1, 2, 3)):
...     print(x, end=' ')
(1, 2, 3) (2, 3, 1) (3, 1, 2)
```

Recursion could also work here, but it would be overkill for this fixed and linear task.

### Generator functions for scrambling

The simple approach works, but it has two costs. It builds the whole result list in memory, which is a problem for massive results. It also makes the caller wait until the whole list is finished, which feels slow when the work is expensive. You can do better on both counts. Translate the function into a generator that yields one result at a time. Either coding scheme works:

```python
>>> def scramble(seq):
...     for i in range(len(seq)):
...         seq = seq[1:] + seq[:1]  # Generator function, coding 1
...         yield seq  # Assignments work here
>>> def scramble(seq):
...     for i in range(len(seq)):  # Generator function, coding 2
...         yield seq[i:] + seq[:i]  # Yield one item per iteration
```

Both versions produce values for tools such as `list` and `for`. The results of the second version arrive in a slightly different order. That should not matter to future callers:

```python
>>> list(scramble('code'))  # list() generates all results
['code', 'odec', 'deco', 'ecod']
>>> list(scramble((1, 2, 3)))  # Any sequence type works
[(1, 2, 3), (2, 3, 1), (3, 1, 2)]
>>> for x in scramble((1, 2, 3)):  # for loops generate results
...     print(x, end=' ')
(1, 2, 3) (2, 3, 1) (3, 1, 2)
```

Both generator functions keep their local state, `seq` and `i`, while they are active. They use less memory and divide the work into shorter time slices. They are also very general, since they are full functions. Because iteration tools behave the same way with a list or a generator, the function can switch codings or strategies later without affecting its callers.

### Generator expressions for scrambling

Generator expressions, which are comprehensions in parentheses, also produce values on request and keep their local state. They are not as flexible as full functions. Because they yield values automatically, they can be far more concise for a specific case like this one:

```python
>>> S = 'code'
>>> G = (S[i:] + S[:i] for i in range(len(S)))  # Generator expr, coding 2
>>> list(G)
['code', 'odec', 'deco', 'ecod']
```

A generator expression cannot use the `seq` assignment from the first generator-function coding. It can reach the same effect by nesting the `:=` named assignment expression from earlier. The `:=` operator changes the name in the containing scope, and it also returns the assigned value, so that value appears in the results:

```python
>>> S = 'code'
>>> G = (S:=(S[1:] + S[:1]) for i in range(len(S)))  # Generator expr, coding 1
>>> list(G)
['odec', 'deco', 'ecod', 'code']
```

These versions still work on one specific variable, `S`. To generalise a generator expression, wrap it in a simple `lambda` that takes an argument and returns a generator. In the second version below, `seq` is not local to the generator. It is local to the `lambda` that encloses it:

```python
>>> F = lambda seq: (seq[i:] + seq[:i] for i in range(len(seq)))
>>> list(F(S))
['code', 'odec', 'deco', 'ecod']
>>> F = lambda seq: (seq:=(seq[1:] + seq[:1]) for i in range(len(seq)))
>>> list(F(S))
['odec', 'deco', 'ecod', 'code']
>>> list(F([1, 2, 3]))
[[2, 3, 1], [3, 1, 2], [1, 2, 3]]
>>> F(S)
<generator object <lambda>.<locals>.<genexpr> at 0x100b23300>
>>> for x in F((1, 2, 3)): print(x, end=' ')
(2, 3, 1) (3, 1, 2) (1, 2, 3)
```

### Tester client

You can use either the generator function or its expression equivalent in a tester. The tester feeds scrambled arguments to the functions under test. Once the scramblers live in a module, they become reusable tools. The next example shows that module:

```python
"Generate shuffles of a sequence, by function or expression"
def scramble1(seq):
    for i in range(len(seq)):
        yield seq[i:] + seq[:i]  # Yield one shuffle per iteration

scramble2 = lambda seq: (seq[i:] + seq[:i] for i in range(len(seq)))
```

Moving value generation into this external module makes the testing function simpler. You need a little page flipping to see how it fits together. The tester takes a function, a sequence of items, and a trace flag. Here is an example session:

```python
>>> from scramble import scramble1  # Choose your scrambler
>>> from inter2 import intersect, union  # Functions to be tested
>>> def tester(func, items, trace=True):
...     for args in scramble1(items):  # Use either generator
...         if trace: print(args)
...         print(sorted(func(*args)))  # Test for this scramble
>>> tester(intersect, ('aab', 'abcde', 'ababab'), False)
['a', 'b']
['a', 'b']
['a', 'b']
```

To run this yourself, all the imported files must be in the current directory. You can copy `inter2.py` from the earlier folder into this one. Or you can copy `scramble.py` into the earlier folder and work there. The examples package already does the first. You can also change the module search path with the `PYTHONPATH` setting to include any folder. Modules are covered in full in a later chapter.

### Permutating sequences

Generators have many real-world uses. You might parse attachments in an email message, or compute points to plot in a GUI. Other kinds of sequence scrambles matter in searches and mathematics too. The scrambler above is a simple reordering. Some programs need every possible ordering, which is a permutation. The next example has two permutation functions. One builds a list and the other is a generator. They are recursive:

```python
"Permute sequences: as a list or generator of values"
def permute1(seq):
    if not seq:  # Shuffle any sequence: list
        return [seq]  # Empty sequence
    else:
        res = []
        for i in range(len(seq)):
            rest = seq[:i] + seq[i+1:]  # Delete current node
            for x in permute1(rest):  # Permute the others
                res.append(seq[i:i+1] + x)  # Add node at front
        return res

def permute2(seq):
    if not seq:  # Shuffle any sequence: generator
        yield seq  # Empty sequence
    else:
        for i in range(len(seq)):
            rest = seq[:i] + seq[i+1:]  # Delete current node
            for x in permute2(rest):  # Permute the others
                yield seq[i:i+1] + x  # Add node at front
```

Both functions produce the same results. The second defers most of its work until a result is requested. This code is advanced, especially the second function. Some newcomers find it painful to read. Still, generator approaches are sometimes essential, as you will see.

Study and test this code to learn more. Add print statements to trace it if that helps. If it still seems mysterious, start with the first version. Remember that generator functions return objects whose `next` methods run at each level of the loops. They produce no results until they are iterated. Trace some of the examples below to see how the code handles them.

Permutations produce more orderings than the simple scrambler. For `N` items, you get `N!` results, not `N`. For 4 items, that is 24 (4 * 3 * 2 * 1). Recursion is needed because the number of nested loops depends on the sequence length. Here is a demo of both shufflers:

```python
>>> from scramble import scramble1
>>> from permute import permute1, permute2
>>> list(scramble1('abc'))  # Simple scrambles: N = 3
['abc', 'bca', 'cab']
>>> permute1('abc')  # Permutations larger: N! = 6
['abc', 'acb', 'bac', 'bca', 'cab', 'cba']
>>> list(permute2('abc'))  # Generate all ordered combos
['abc', 'acb', 'bac', 'bca', 'cab', 'cba']
>>> G = permute2('abc')  # Iterate: iter() not needed
>>> next(G)
'abc'
>>> next(G)
'acb'
>>> for x in permute2('abc'): print(x)  # Automatic iteration
...prints six lines...
```

The list and generator versions give the same results. The generator uses less memory, and results arrive sooner. For larger inputs, the set of all permutations is much bigger than the simple scrambler's output:

```python
>>> permute1('hack') == list(permute2('hack'))
True
>>> len(list(permute2('hack'))), len(list(scramble1('hack')))
(24, 4)
>>> list(scramble1('hack'))
['hack', 'ackh', 'ckha', 'khac']
>>> list(permute2('hack'))
['hack', 'hakc', 'hcak', 'hcka', 'hkac', 'hkca', 'ahck', 'ahkc', 'achk', 'ackh',
'akhc', 'akch', 'chak', 'chka', 'cahk', 'cakh', 'ckha', 'ckah', 'khac', 'khca',
'kahc', 'kach', 'kcha', 'kcah']
```

Chapter 19 described nonrecursive options, which use explicit stacks or queues. Other orderings are common too. Fixed-size subsets and combinations can filter out duplicates that differ only in order. Those need extensions that this chapter does not cover. Experiment on your own to learn more.

### Why generators here: space, time, and more

Generators are an advanced tool, and they might be treated as optional except for one fact: they appear everywhere in Python. Built-in tools such as `range`, `map`, dictionary `keys`, and files are generators now. You must know the concept even if you never write a generator yourself. User-defined generators also appear in code you will read, including the Python standard library.

The guideline for comprehensions applies to generators too. Do not add user-defined generators unless they are warranted. Smaller programs and data sets may not need them. A simple list of results may be easier to understand, and it is garbage-collected automatically. It may also be produced faster, as the next chapter shows. Advanced tools that rely on implicit "magic" can be fun to experiment with, but when they are optional they may be a poor choice.

Some use cases do suit generators well. Generators can reduce memory use, reduce delays, and occasionally make the impossible possible. Take a program that must produce every permutation of a long sequence. The number of permutations is a factorial, which grows explosively. The recursive list builder `permute1` would either cause a long pause or fail on memory.

The recursive generator `permute2` returns each result quickly, and it handles very large result sets. The difference shows up even at 10 items, as Python's `math` module shows:

```python
>>> import math
>>> f'{math.factorial(10):,}'  # 10 * 9 * 8 * 7 * 6 * 5 * 4 * 3 * 2 * 1
'3,628,800'
>>> from permute import permute1, permute2
>>> seq = list(range(10))
>>> p1 = permute1(seq)  # ~17 seconds on a 2.3GHz i9 macOS host
>>> len(p1)  # Creates a list of 3.6M numbers
3628800
>>> p1[0], p1[-1]
([0, 1, 2, 3, 4, 5, 6, 7, 8, 9], [9, 8, 7, 6, 5, 4, 3, 2, 1, 0])
```

Here, `permute1` pauses for about 17 seconds to build a list of 3.6 million items. The generator starts returning single results right away. Neither `permute2` nor any `next` call pauses:

```python
>>> p2 = permute2(seq)  # Returns generator immediately
>>> next(p2)  # Returns each result quickly on demand
[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
>>> next(p2)
[0, 1, 2, 3, 4, 5, 6, 7, 9, 8]
```

Collecting every result from the generator is still slow. It is faster than the list builder, but that is not the intended use:

```python
>>> p2 = list(permute2(seq))  # About 10 seconds, though still impractical
>>> p1 == p2  # Same set of results generated
True
```

You could optimize the list builder, for example with an explicit stack instead of recursion. For larger sequences, though, the list builder is not an option at all. At just 50 items, the number of permutations rules out building a list. It would also take far too long. Larger values also overflow the recursion depth limit covered earlier. The generator still works, since it can produce single results right away despite the huge total:

```python
>>> math.factorial(50)
30414093201713378043612608166064768844377641568960512000000000000
>>> p3 = permute2(list(range(50)))  # permute1 is not an option here!
>>> next(p3)
[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22,
23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43,
44, 45, 46, 47, 48, 49]
```

For variety, you can shuffle the input randomly before permuting. The `random` module, covered in an earlier chapter, provides `random.shuffle`. Each `permute2` and `next` call returns right away and permutes a random sequence. The `permute1` call would hang, and it would eventually run out of memory if left running:

```python
>>> seq = list(range(20))
>>> print(f'{math.factorial(20):,}')  # permute1 is not an option here
2,432,902,008,176,640,000
>>> import random
>>> random.shuffle(seq)  # Shuffle sequence randomly first
>>> p = permute2(seq)
>>> next(p)
[10, 19, 5, 6, 2, 13, 1, 8, 11, 7, 14, 16, 4, 3, 0, 18, 9, 12, 17, 15]
>>> next(p)
[10, 19, 5, 6, 2, 13, 1, 8, 11, 7, 14, 16, 4, 3, 0, 18, 9, 12, 15, 17]
>>> random.shuffle(seq)
>>> p = permute2(seq)
>>> next(p)
[17, 15, 14, 7, 10, 8, 2, 6, 18, 19, 13, 4, 1, 12, 5, 0, 3, 9, 16, 11]
>>> next(p)
[17, 15, 14, 7, 10, 8, 2, 6, 18, 19, 13, 4, 1, 12, 5, 0, 3, 9, 11, 16]
```

You might use the random shuffler in place of manual shuffles in some cases. That works only if you can assume it will not repeat shuffles while you consume them. Otherwise you must test its results against earlier shuffles. When full coverage matters, manual shuffles give you more control.

The main point is that generators can produce results from large solution sets when list builders cannot. Still, such use cases may be uncommon, and they do not justify the implicit style of generator functions and expressions everywhere. Class-based iterables can produce items on request too, and they are more explicit than the magic objects and methods behind generator functions and expressions.

Part of programming is finding a balance among trade-offs, and there are no absolute rules here. The benefits of generators can justify their use, but maintainability counts too. Comprehensions and generators offer expressiveness and code economy that is hard to resist once you understand them. Weigh that against the frustration of coworkers who may not share your comfort with them.

### Example: emulating zip and map

This example shows how expressive generators can be. Once you know comprehensions, generators, and other iteration tools, you can emulate many of Python's functional built-ins. The emulations are instructive, and they can also be useful for custom roles.

The `zip` and `map` built-ins combine several iterables. `zip` pairs items from its iterables. `map` applies a function across items taken from each iterable, much as `zip` combines them. Both stop at the length of the shortest iterable:

```python
>>> list(zip('abc', 'xyz123'))  # zip combines items from iterables
[('a', 'x'), ('b', 'y'), ('c', 'z')]
>>> list(zip([1, 2, 3], [2, 3, 4, 5]))  # N M-ary iterables: M N-ary tuples
[(1, 2), (2, 3), (3, 4)]
>>> list(zip([-2, -1, 0, 1, 2]))  # 1 5-ary iterable: 5 1-ary tuples
[(-2,), (-1,), (0,), (1,), (2,)]
>>> list(map(abs, [-2, -1, 0, 1, 2]))  # Single iterable: 1-ary function
[2, 1, 0, 1, 2]
>>> list(map(pow, [1, 2, 3], [2, 3, 4, 5]))  # N iterables: N-ary function
[1, 8, 81]
```

Both built-ins work on any iterable, including files that read lines automatically. They serve different purposes. Still, if you study these examples, you may notice a link between `zip` results and `map` function arguments. The next example uses that link.

### Coding your own map

The `map` and `zip` built-ins are fast and convenient, yet you can still implement them in your own code. The chapter on functions wrote a function that emulated `map` for a single iterable. The next example extends it to accept several iterables, as the built-in does:

```python
"Emulate map: support multiple arguments, build a list result"
def mymap(func, *seqs):
    res = []
    for args in zip(*seqs):
        res.append(func(*args))
    return res

print(mymap(abs, [-2, -1, 0, 1, 2]))
print(mymap(pow, [1, 2, 3], [2, 3, 4, 5]))
```

This version uses `*` argument syntax in three places. It collects several iterable arguments, unpacks them as arguments to `zip`, and then unpacks the combined results as arguments to the passed-in function. Zipping is essentially a nested step in mapping. The test code applies the function to one and to two sequences, and it gives the same results as the built-in `map`:

```
$ python3 mymap-list.py
[2, 1, 0, 1, 2]
[1, 8, 81]
```

This code follows the classic list comprehension pattern. It builds a list of results inside a `for` loop. You can rewrite the mapper as a one-line equivalent list comprehension:

```python
def mymap(func, *seqs):
    return [func(*args) for args in zip(*seqs)]
```

The output is the same, and the code is shorter. It might also run faster, and the next chapter covers performance. Both `mymap` versions build their result lists all at once, which can waste memory with large lists. Now that you know generator functions and expressions, you can recode both as generators that produce results on demand. The next example does this:

```python
"Emulate map: support multiple arguments, generate results on request"
def mymap_func(func, *seqs):
    for args in zip(*seqs):
        yield func(*args)

def mymap_expr(func, *seqs):
    return (func(*args) for args in zip(*seqs))

for mymap in (mymap_func, mymap_expr):
    print(list(mymap(abs, [-2, -1, 0, 1, 2])))
    print(list(mymap(pow, [1, 2, 3], [2, 3, 4, 5])))
```

Both new versions give the same results. The first yields one result at a time explicitly. The second returns a generator expression, which does the same thing implicitly. Each is a generator, so you must wrap it in a `list` call to force all its values out at once:

```
$ python3 mymap-generate.py
[2, 1, 0, 1, 2]
[1, 8, 81]
[2, 1, 0, 1, 2]
[1, 8, 81]
```

No real work happens until the `list` calls activate the iteration protocol. Those `list` calls exist only to display results during testing, and you rarely want them elsewhere. The generators returned here, and the generators that `zip` returns, produce results only on demand. That is the whole point of generators. Delaying results saves memory and spares callers a wait for the full set.

### Coding your own zip and Python 2 map

The `zip` built-in combines arguments from several iterables, and the examples so far depend on it. You can also write your own version. One version emulates the truncating behaviour of today's `zip`. Another emulates the padding behaviour of `map` in Python 2 when it receives `None` as its function. Padding `map` has no use in Python 3, but custom code can still provide it. The next example shows that `zip` and padding `map` are related in purpose and nearly the same in code:

```python
# Emulate zip and padding map: build lists
def myzip(*seqs):
    seqs = [list(S) for S in seqs]
    res = []
    while all(seqs):
        res.append(tuple(S.pop(0) for S in seqs))
    return res

def mymapPad(*seqs, pad=None):
    seqs = [list(S) for S in seqs]
    res = []
    while any(seqs):
        res.append(tuple((S.pop(0) if S else pad) for S in seqs))
    return res

S1, S2 = 'abc', 'xyz123'
print(myzip(S1, S2))
print(mymapPad(S1, S2))
print(mymapPad(S1, S2, pad=99))
```

Both functions work on any iterable, because they pass their arguments through the `list` built-in to force results. Files work as arguments too, along with sequences like strings. The code uses the `all` and `any` built-ins. These return `True` when all items, or any item, of an iterable are true, which here means nonempty. The loops stop when all or any of the listified arguments become empty after deletions.

The `pad` argument is keyword-only. Unlike the Python 2 `map`, this version accepts any pad object. Running the file prints one `zip` result and two padded `map` results:

```
$ python3 myfptools-list.py
[('a', 'x'), ('b', 'y'), ('c', 'z')]
[('a', 'x'), ('b', 'y'), ('c', 'z'), (None, '1'), (None, '2'), (None, '3')]
[('a', 'x'), ('b', 'y'), ('c', 'z'), (99, '1'), (99, '2'), (99, '3')]
```

These functions do not translate well into comprehensions, because their loops are too specific. Still, these `zip` and `map` workalikes can become generators. Use `yield` in place of building lists, so each hands back one piece of its result at a time. The next example shows how:

```python
# Emulate zip and padding map: generate results
def myzip(*seqs):
    seqs = [list(S) for S in seqs]
    while all(seqs):
        yield tuple(S.pop(0) for S in seqs)

def mymapPad(*seqs, pad=None):
    seqs = [list(S) for S in seqs]
    while any(seqs):
        yield tuple((S.pop(0) if S else pad) for S in seqs)
```

The results match the earlier ones. This file has no self-test code, because it assumes it will be used or tested elsewhere. In the REPL, you still need `list` to force the generators to yield values for display:

```python
$ python3
>>> from myfptools_generate import myzip, mymapPad
>>> list(myzip('abc', 'xyz123'))
[('a', 'x'), ('b', 'y'), ('c', 'z')]
>>> list(mymapPad('abc', 'xyz123', pad=99))
[('a', 'x'), ('b', 'y'), ('c', 'z'), (99, '1'), (99, '2'), (99, '3')]
```

Another version avoids the `pop` method entirely. It computes the minimum and maximum argument lengths. With those lengths, nested comprehensions can step through the index ranges:

```python
def myzip(*seqs):
    minlen = min(len(S) for S in seqs)
    return [tuple(S[i] for S in seqs) for i in range(minlen)]

def mymapPad(*seqs, pad=None):
    maxlen = max(len(S) for S in seqs)
    index = range(maxlen)
    return [tuple((S[i] if len(S) > i else pad) for S in seqs) for i in index]
```

These versions use `len` and indexing. They assume the arguments are sequences or similar, not arbitrary iterables. The outer comprehensions step through the index range. The inner comprehensions, passed to `tuple`, pull items from each sequence in parallel. The results match the earlier ones.

Generators and iterators are everywhere in this example. The arguments to `min` and `max` are generator expressions. They run to completion before the nested comprehensions begin. The nested comprehensions also have two levels of delayed evaluation. The `range` built-in is an iterable, and so is the generator expression passed to `tuple`.

No results appear until the square brackets of the list comprehensions ask for values for the result list. That request forces all the comprehensions and generators to run. To make these functions generators themselves, use parentheses instead of square brackets. Here is the `zip` version:

```python
def myzip(*seqs):
    minlen = min(len(S) for S in seqs)
    return (tuple(S[i] for S in seqs) for i in range(minlen))

S1, S2 = 'abc', 'xyz123'
print(list(myzip(S1, S2)))  # Go!... [('a', 'x'), ('b', 'y'), ('c', 'z')]
```

Here, a `list` call is needed to activate the generators and the other iterables. Experiment with these yourself. Developing more coding alternatives is left as an exercise. The sidebar "Iteration Versus Python Morph" below explores one such option.

## Asynchronous functions: the short story

Python 3.5 added asynchronous functions, usually shortened to `async` functions. They can pause their own execution while they wait for a result. That pause lets other such functions run in the meantime, which is the whole trick.

Other languages, such as JavaScript, have similar tools, and they helped inspire Python's version. Many Python features, such as `match`, `:=`, f-strings, and type hints, come from the same language design race.

The main use case for `async` is input and output. A function can pause until an I/O transfer finishes, and other parts of the program run during the wait. Threads can solve this problem too. Some developers find `async` functions the lighter-weight option.

There are downsides. The `async` design has changed almost constantly since its first versions in Python 3.4. That makes it hard to document in a book, which lasts longer than a web page. It is also all or nothing, because async code needs other async code to call it.

Async functions also belong to parallel programming. That field includes multiprocessing and multithreading. Async is a heavyweight subject for most Python users, and a lot to ask of newcomers. Given how complex Python already is, it can reasonably be an optional add-on topic.

Still, `async` functions are not truly optional. They were added to the language as syntax, through the `async` and `await` reserved words. You may have to reuse them, or face them in job interviews. This section gives a brief overview, and Python's online resources cover the details.

### Async basics

Async functions allow cooperative, nonpreemptive multitasking. The trade-offs resemble those of asynchronous network servers. Tasks must be short-lived, or one will monopolize the processor. Python 3.5 made this model part of the language. It added the `async def` statement, the `await` expression, the `async for` iterator, and the `async with` context manager.

Async tools and syntax work only inside functions defined with `async def`. Like `yield` and `yield from`, `async def` compiles a function specially. When you call it, the body does not run. Instead, you get an awaitable object that supports a method-based protocol.

To run that object, you `await` its results, or use `async for` or `async with`, which await implicitly. An event loop must also run the whole program. The event loop runs one task at a time, so tasks are not truly parallel. When a task awaits a result that is not ready, the event loop can switch to another task.

#### Running serial tasks with normal blocking calls

Code is often easier to follow than prose, so the examples below lean on code. Their snippets come from a file named `all_async_demos.py` in the examples package. The next example shows its preamble. You can paste the snippets from it, run the whole file, or run it with some parts disabled. Every example assumes the preamble has run:

```python
import time, asyncio

def now():
    return time.strftime('[%H:%M:%S]')  # Local time, as hour:minute:second

# ...all examples here...
```

The examples use a few standard-library tools. Some come from the `asyncio` module. Times are shown with `time.strftime`. Sleep calls in both `time` and `asyncio` simulate a long-running task. Python's library manual covers the fine print, which is skipped here.

Start with ordinary code. A `main` function calls `producer`, which pauses for two seconds with `time.sleep` before it returns a result. The sleep stands in for a real blocking operation, such as an I/O call, a network transfer, or a user interaction. `main` waits for each `producer` to finish before it moves on:

```python
def producer(label):
    time.sleep(2)  # Pause for two seconds: blocking
    return f'All done, {label}, {now()}'  # And return a result

def main():
    print('Start =>', now())
    print(producer(f'serial task 1'))  # Run three steps in sequence
    print(producer(f'serial task 2'))  # Waiting for each one to finish
    print(producer(f'serial task 3'))  # Before doing anything else
    print('Stop =>', now())

main()
```

The results are ordinary. Each `producer` runs its two-second sleep before the next one starts. The total time is six seconds, two for each call that `main` runs in series:

```
Start => [19:00:28]
All done, serial task 1, [19:00:30]
All done, serial task 2, [19:00:32]
All done, serial task 3, [19:00:34]
Stop => [19:00:34]
```

#### Running concurrent tasks with await and async def

Now do the same work with async functions. The `producer` is defined with `async def`, so Python compiles it as a coroutine. When you call it, it does not produce its result. It returns an object that supports the coroutine protocol. That protocol includes a method named `__await__`, which returns an iterator. That iterator produces coroutine results through `__next__`. Async generators use `__anext__` instead. You can safely ignore these details for now.

The `async def` syntax is required for any function that uses `await`, `async for`, or `async with`. Because `async def` is required both to use and to define awaitable coroutines, it spreads through code like a virus. Some libraries now ship in two forms, asynchronous and not.

In the next listing, `producer` uses `await` to pause itself until the sleep expires. `await` is similar to `yield from`. The event loop can pause the coroutine that runs the `await` and resume another coroutine if the awaited result is not ready. In `producer`, `await` works as a statement. It is also an expression that returns the awaited result, as it does in `main`:

```python
async def producer(label):  # await requires async
    await asyncio.sleep(2)  # Call nonblocking/awaitable sleep
    return f'All done, {label}, {now()}'  # Result of await expression

async def main():
    print('Start =>', now())
    task1 = asyncio.create_task(producer(f'async task 1'))
    task2 = asyncio.create_task(producer(f'async task 2'))
    task3 = asyncio.create_task(producer(f'async task 3'))
    print(await task1)
    print(await task2)
    print(await task3)  # Wait for tasks to finish
    print('Stop =>', now())

asyncio.run(main())  # Start event-loop schedule
```

The `asyncio.sleep` call is awaitable and nonblocking. It is like `time.sleep`, but it uses the event loop's API, so the caller does not pause. It can be paused with `async def` until its timeout elapses. Operations at the end of an `await` chain must generally follow this model.

`main` uses `asyncio.create_task` to wrap each `producer` in a task. A task is an object that the event loop runs. It suspends the coroutine it wraps while that coroutine waits on a future. When awaited, it returns the wrapped coroutine's result. Futures signal progress in ways too low-level for this overview. It is enough to know that each task suspends itself while its coroutine sleeps.

Because the tasks overlap in time, they run concurrently. All three tasks finish at the same moment. The whole program takes two seconds instead of six:

```
Start => [19:00:34]
All done, async task 1, [19:00:36]
All done, async task 2, [19:00:36]
All done, async task 3, [19:00:36]
Stop => [19:00:36]
```

You can automate the steps with loops. This version behaves the same way. It takes two total seconds, with two seconds for each overlapped task:

```python
async def producer(label):
    await asyncio.sleep(2)
    return f'All done, {label}, {now()}'

async def main():
    print('Start =>', now())
    tasks = []
    for i in range(3):
        tasks.append(asyncio.create_task(producer(f'async task {i+1}')))
    for task in tasks:
        print(await task)
    print('Stop at', now())

asyncio.run(main())
```

In both `producer` and `main`, `await` suspends the coroutine that runs it. It does this until the awaited object returns its result, much like `yield from`. Together, the event loop and the tasks interleave the code.

#### How not to use async functions

Some incorrect codings show what the working example really needs. The `await` expressions, the tasks, and the event loop are all essential. Without them, the code will not work. Calling `main` directly, without the event loop, fails at once with a warning. The call creates an awaitable but does nothing with it. The following snippets show only the differing code, followed by its results:

```python
async def main():
    print(producer('xxx'))

main()
# Result...
# ...all_async_blunders.py:12: RuntimeWarning: coroutine 'main' was never awaited
```

Calling `producer` directly, without awaiting it, fails for the same reason. Like generators, calling a coroutine returns an awaitable and does not run it. You must `await` the awaitable to make it run, just as you call `next` to get results from a generator:

```python
async def main():
    print(producer('xxx'))

asyncio.run(main())
# Result...
# <coroutine object producer at 0x10142e740>
# ...all_async_blunders.py:22: RuntimeWarning: coroutine 'producer' was never awaited
```

Tasks are the key to concurrency. If `main` awaits each `producer` directly, it pauses for each sleep. In the next miscoding, both coroutines wait for their sleeps to end, one after the other. The program takes four seconds instead of two:

```python
async def main():
    print('Start =>', now())
    print(await producer('xxx'))
    print(await producer('yyy'))
    print('Stop =>', now())

asyncio.run(main())
# Result...
# Start => [18:41:56]
# All done, xxx, [18:41:58]
# All done, yyy, [18:42:00]
# Stop => [18:42:00]
```

Deferring the awaits with assignments does not help. `main` keeps running after it creates the `producer` coroutines. It still waits at each later `await`, which runs the coroutine's code. There is no concurrency:

```python
async def main():
    print('Start =>', now())
    p1 = producer('xxx')
    p2 = producer('yyy')
    print('Await =>', now())
    print(await p1)
    print(await p2)
    print('Stop =>', now())

asyncio.run(main())
# Result...
# Start => [18:42:00]
# Await => [18:42:00]
# All done, xxx, [18:42:02]
# All done, yyy, [18:42:04]
# Stop => [18:42:04]
```

That is why tasks are needed in the working example. Tasks let the event loop pause and run coroutines, so their execution overlaps. This is how concurrency happens. Alternatives appear in the next section.

#### Running concurrent tasks with as_completed and gather

Besides creating tasks, you can use the `gather` function to wait for all coroutines at once. You can also use `as_completed` to handle results as they finish. `as_completed` works in an ordinary `for` loop, so you can watch the completions arrive:

```python
async def producer(label):
    await asyncio.sleep(2)
    return f'All done, {label}, {now()}'

async def main():
    print('Start =>', now())
    coros = [producer(f'async task {i+1}') for i in range(3)]
    for nextdone in asyncio.as_completed(coros):
        print(await nextdone)
    print('Stop at', now())

asyncio.run(main())
```

This version also finishes in two seconds. Results can arrive in any order, though. The `as_completed` function also works with `async for`, which the next subsection covers. Python's manuals describe those details:

```
Start => [19:00:38]
All done, async task 2, [19:00:40]
All done, async task 3, [19:00:40]
All done, async task 1, [19:00:40]
Stop at [19:00:40]
```

The `gather` call behaves differently. It schedules tasks for the coroutines and awaits all of its arguments. When they all finish, it returns a list of their results, and that list keeps the same order as the arguments:

```python
async def producer(label):
    await asyncio.sleep(2)
    return f'All done, {label}, {now()}'

async def main():
    print('Start =>', now())
    coro1 = producer(f'async task 1')
    coro2 = producer(f'async task 2')
    coro3 = producer(f'async task 3')
    results = await asyncio.gather(coro1, coro2, coro3)
    print(results)
    print('Stop at', now())

asyncio.run(main())
```

The results come back in a list, formatted here for display. The whole job still takes just two seconds:

```
Start => [19:00:40]
['All done, async task 1, [19:00:42]',
'All done, async task 2, [19:00:42]',
'All done, async task 3, [19:00:42]']
Stop at [19:00:42]
```

A starred list comprehension can build the awaitables for `gather` more briefly. It gives the same two-second result:

```python
async def producer(label):
    await asyncio.sleep(2)
    return f'All done, {label}, {now()}'

async def main():
    print('Start =>', now())
    print(await asyncio.gather(*[producer(f'async task {i+1}') for i in range(3)]))
    print('Stop at', now())

asyncio.run(main())
```

This code works. Python's manuals now recommend `TaskGroup` over `gather`, because `TaskGroup` handles exceptions better. To follow that advice, read the next section.

#### Running concurrent tasks with async with and async for

Another concurrency option combines the `async with` statement with a manager object. The manager handles both protocols and exceptions, and it waits for tasks to finish. The `async with` statement awaits the awaitables returned by its subject's `__aenter__` and `__aexit__` methods. A normal `with` statement calls the context-manager methods `__enter__` and `__exit__` instead.

Normal `with` statements and their protocols are covered in a later part, since they need classes. For now, it is enough to know how this code behaves. A `TaskGroup` used as an asynchronous context manager, with `async with`, waits for all of its tasks before the statement exits. It also handles some difficult exception cases:

```python
async def producer(label):
    await asyncio.sleep(2)
    return f'All done, {label}, {now()}'

async def main():
    print('Start =>', now())
    async with asyncio.TaskGroup() as tg:
        tasks = [tg.create_task(producer(f'async task {i+1}')) for i in range(3)]
    for task in tasks:
        print(task.result())
    print('Stop at', now())

asyncio.run(main())
```

The three `producer` calls run concurrently and finish in two seconds:

```
Start => [19:00:44]
All done, async task 1, [19:00:46]
All done, async task 2, [19:00:46]
All done, async task 3, [19:00:46]
Stop at [19:00:46]
```

A function written with `async def` that also uses `yield` is an asynchronous generator. Calling it returns an asynchronous iterable. That iterable uses the `__anext__` method, and you can loop over it with an `async for` statement. Only `with` and `for` have `async` variants so far. There are no `async` versions of `while` or `if`.

Internally, `async for` uses `__aiter__` and `__anext__`. These are the async versions of `__iter__` and `__next__`, which you learned about earlier. `__anext__` returns an awaitable that produces the next value. When the values end, it raises `StopAsyncIteration` instead of `StopIteration`. `async for` gets each value by awaiting a call to `__anext__`, then runs the loop body for it. This goes deeper into classes, which later chapters cover. Statement users can usually ignore the details.

Be careful here. `async for` awaits the next item in the iterable it scans. That is not the same as awaiting something inside the body of an ordinary `for` loop. Also, `async for` does not run anything in parallel. It works like a normal `for` loop, but it adds an `await` before each item. That lets other ready tasks run between loop passes. It does not help much otherwise:

```python
async def producer(label):
    for i in range(3):
        await asyncio.sleep(2)
        yield f'All done, {label} {i+1}, {now()}'

async def main():
    print('Start =>', now())
    async for reply in producer('async task'):
        print(reply)
    print('Stop at', now())

asyncio.run(main())
```

In this form, the result matches the six-second serial version. Nothing else runs during the sleeps in this simple demo:

```
Start => [19:00:46]
All done, async task 1, [19:00:48]
All done, async task 2, [19:00:50]
All done, async task 3, [19:00:52]
Stop at [19:00:52]
```

Within an `async def` function, you can also use `await` and `async for` inside a comprehension. That topic is beyond this overview. The book leaves it for another time.

#### The async wrap-up

That covers all the time and space this topic deserves. Python's async functions may be more useful than type hints, which are rarely used and seem to clash with Python's core ideas. A full survey of either topic could fill chapters or books, and only some Python users would need it.

This text does not cover Python's multithreading or multiprocessing tools. Both are valid ways to parallelize tasks, just as async functions are. Async alone received dedicated syntax, which favours one option and raises the bar for newcomers. Your goals may differ. For the full story, read Python's standard manuals before you wade deeper into async. For now, step back from this optional, complicated extension and return to the fundamentals that nearly every Python program uses.

## Comprehensions and generators: summary

This part of the chapter covered the built-in comprehension and iteration tools. It explained list comprehensions as functional tools. It also presented generator functions and generator expressions as more tools for the iteration protocol. The larger examples showed iterations, comprehensions, and generators in action. The async extension was introduced briefly, to whet your appetite for further study. Iteration will come up again when you write user-defined iterable classes.

The next chapter continues this theme. It times the performance of these tools in a case study, which is also a realistic example at the midpoint of this book.

### Iteration versus Python morph

Earlier in this part, we noted that some built-ins, such as `map`, support only a single traversal. After that, they are empty. This section shows why that matters in practice, and how a Python change can quietly break your code.

In earlier editions of this book, a clever `zip` emulation worked. It was adapted from Python's documentation at the time. It worked because `map` returned a physical list, not a generator of values:

```python
def myzip(*args):  # Before 3.0...
    iters = map(iter, args)
    while iters:  # Guarantee >=1, force looping
        res = [next(i) for i in iters]  # Any empty? StopIteration=return
        yield tuple(res)  # Else return res, suspend state
    # Exit=return=StopIteration

>>> list(myzip('ab', 'lmn'))
KeyboardInterrupt
```

This broke in Python 3.0. The code relied on `map` supporting several scans. In 3.0, `map` became a single-scan generator. Once the list comprehension scanned `iters` one time, the generator was used up. It still tested as true, though. Later list comprehensions returned `[]`, and the loop ran until a Ctrl+C stopped it.

The earlier edition fixed this by wrapping `map` in `list`, which made it reiterable:

```python
def myzip(*args):  # Before 3.7...
    iters = list(map(iter, args))  # <== Make iters reiterable, 3.0+
    while iters:  # map() is a one-scan generator
        res = [next(i) for i in iters]
        yield tuple(res)

>>> list(myzip('ab', 'lmn'))
RuntimeError: generator raised StopIteration
```

This version broke in Python 3.7. The code had relied on an uncaught `StopIteration` from any iterable in `iters`. That exception passed through the function and ended its generation of values. Python 3.7 stopped this propagation, so a generator now raises a `RuntimeError` instead. The workaround is to catch `StopIteration` explicitly and `return`. A `return` in a generator raises `StopIteration` anyway:

```python
def myzip(*args):  # After 3.7, and before ?...
    iters = list(map(iter, args))
    while iters:
        try:  # <== Catch StopIteration, 3.7+
            res = [next(i) for i in iters]  # StopIteration won't propagate
        except StopIteration:
            return  # How generators should exit
        yield tuple(res)  # But exit=return=StopIteration!

>>> list(myzip('ab', 'lmn'))
[('a', 'l'), ('b', 'm')]
```

The `try` statement is covered in a later part. In rare generators that relied on the old bubbling behaviour, you may need to translate exceptions into returns this way. This final version works today, but its future is uncertain.

The lessons are clear. Wrapping `map` calls in `list` calls is not just for display. Generators no longer pass exit exceptions out of the code they run. Python changes can break code, both subtly and repeatedly.

## Benchmarking interlude

Now that you have worked through function coding and the iteration tools, this short detour puts both to use. It closes the functions part with a larger case study. The case study times the iteration tools we have met so far, in standard Python and in one of its alternatives.

Along the way, you will survey Python's code-timing tools and learn general benchmarking techniques. You will also write timing code that is more realistic than most examples so far. Whether the speeds you measure matter depends on what your programs are for.

Because this is the last chapter in the part, the section ends with common gotchas. First, though, let us time some real code.

## Benchmarking with homegrown tools

We have met quite a few iteration alternatives. Each one is a trade-off between expressiveness and speed. Picking the right tool is part of an engineer's job, and speed is only one factor in that choice.

Earlier sections said that list comprehensions and `map` calls sometimes beat `for` loop statements for speed. They also said that sort speed depends on how the input is ordered. Generator functions and expressions tend to be slower than the other options. They do save memory, though, and they do not delay the caller when there are many results to produce.

That holds in common use today, but benchmarking still comes with big caveats. Code structure and host hardware can change speed in ways that are hard to predict. Python's speed also shifts over time, because its internals keep being optimized. Alternative Pythons can differ from CPython by a wide margin.

In short, if you want to verify speed for yourself, time your code on your own device. Use the Python versions you plan to run, and measure them now. That list of qualifiers is long, yet benchmarking is at heart a hands-on, measure-it-yourself task.

### Timer module: take 1

Python makes timing easy, which can be deceptive. To get the total time for several calls to a function with positional arguments, a small module like this is a fair first draft.

timer0.py

```python
"Simplistic timing function"
import time
def timer(func, *args): # Any positional arguments (only)
    start = time.perf_counter()
    for i in range(100_000): # Hardcoded reps, range() timed
        func(*args)
    return time.perf_counter() - start # Total elapsed time in seconds
```

The function reads the clock from the standard-library `time` module. It runs the passed-in function with the passed-in arguments 100,000 times. Then it subtracts the start time from the stop time.

`time.perf_counter` is a portable clock with the best resolution for short durations. The difference between two calls is the usual way to measure performance. That difference includes time spent sleeping, and it counts system-wide time. `time.process_time` reports per-process CPU time instead, which is useful in some roles. The older `time.clock` was deprecated and later dropped, so older examples may break.

Apart from those `time` calls, the code uses tools you already know. On a macOS machine with CPython 3.12, the REPL results look like this:

```
>>> from timer0 import timer
>>> timer(pow, 2, 1000) # Time to call pow(2, 1000) 100k times
0.08591239107772708
>>> timer(str.upper, 'hack' * 100) # Time to call 'hack...'.upper() 100k times
0.04990812297910452
```

This timer works, but it is limited. It shows several classic mistakes in function design and benchmarking:

- It hardcodes the repetition count at 100,000.
- It charges the cost of `range` to the tested function's time.
- It does not accept keyword arguments for the tested function.
- It gives the caller no way to check that the tested function worked.
- It reports only total time, which can fluctuate on a busy machine.

In other words, timing code is more complex than it looks.

### Timer module: take 2

The second version is more general and more accurate. It defines small timing utilities in a module file, so any program can import them. Its docstrings give usage details that `help` and PyDoc can display.

timer.py

```python
"""
Homegrown timing tools for arbitrary function calls.
Times one call, total of N, best of N, and best of totals of N.
Pass any number of positional and keyword arguments for each func.
"""
import time
timer = time.perf_counter # See also time.process_time()
def once(func, *pargs, **kargs): # Collect arguments for func
    """
    Time to run func(...) one time.
    Returns (time, result).
    """
    start = timer()
    result = func(*pargs, **kargs) # Unpack arguments for func
    elapsed = timer() - start
    return (elapsed, result) # Return result to verify
def total(reps, func, *pargs, **kargs): # Collect arguments for func
    """
    Total time to run func(...) reps times.
    Returns (total-time, last-result).
    """
    total = 0 # Don't charge range() time
    for i in range(reps):
        time, result = once(func, *pargs, **kargs)
        total += time
    return (total, result) # Return last result to verify
def bestof(reps, func, *pargs, **kargs):
    """
    Best time among reps runs of func(...).
    Returns (best-time, best-time-result).
    """
    return min(once(func, *pargs, **kargs) for i in range(reps))
def bestoftotal(reps1, reps2, func, *pargs, **kargs):
    """
    Best total time among reps1 runs of [reps2 runs of func(...)].
    Returns (best-total-time, best-total-time-last-result).
    """
    return min(total(reps2, func, *pargs, **kargs) for i in range(reps1))
```

The module times four ways: one call, a total over many calls, the best single time, and the best total. Each mode accepts any positional and keyword arguments for the function under test. Here is how this version fixes the problems of the first one:

- The repetition count is now a required argument, so each call can choose its own count.
- The cost of `range` is no longer charged to the timed function. The `once` function times only the function it receives.
- Positional and keyword arguments are collected and unpacked with starred syntax. Callers pass them individually, not in a sequence or a dictionary.
- Every function returns the timed function's return value with the time, so callers can verify the result.
- The best-of modes return the minimum time, which filters out fluctuations on the host.

Each function serves a different use case. `once` times a single call. `total` runs many calls, so very short functions accumulate measurable time. `bestof` returns the minimum among single calls, which filters out other activity on the host. `bestoftotal` takes the minimum of nested total-time runs, which combines both ideas.

The `min` calls in the best-of variants work because Python compares tuples from left to right. Each result tuple begins with the time, so the time decides the comparison:

```
>>> min(tup for tup in [(2.0, 3), (3.0, 3), (1.0, 3), (0.0, 3), (4.0, 3)])
(0.0, 3)
```

Because the functions live in a module, you can import them anywhere. Import the module and call one of its functions. The results match the first version, but they are more robust:

```
>>> import timer # Import file in this directory
>>> help(timer) # Display module's docs nicely
>>> reps, text = 100_000, 'hack' * 100
>>> timer.once(pow, 2, 1000)[0] # Not useful for fast calls
6.182119250297546e-06
>>> timer.once(str.upper, text) # (time, result)
(3.363005816936493e-06, 'HACKHACKHACK…etc…')
>>> timer.total(reps, pow, 2, 1000)[0] # Compare to timer0 results
0.08979405369609594
>>> timer.total(reps, str.upper, text)[0] # (time, last call's result)
0.050884191412478685
>>> timer.bestof(50, pow, 2, 1000)[0] # Not useful for fast calls
1.6265548765659332e-06
>>> timer.bestof(50, str.upper, text)[0] # (best time, best time result)
8.619390428066254e-07
>>> timer.bestoftotal(50, reps, pow, 2, 1000)[0]
0.07521858718246222
>>> timer.bestoftotal(50, reps, str.upper, text)[0]
0.03947464330121875
```

The last two calls compute best-of-totals times. Each is the lowest of 50 runs, and each run totals 100,000 calls. These roughly match the `total` times above, but the minimum filters out host noise. `bestoftotal` wraps `total` for better accuracy, and this is a common timing mode.

You could nest `total` inside `bestof` instead, like this:

```
>>> timer.bestof(50, timer.total, reps, str.upper, text)
(0.07037258706986904, (0.039281503297388554, 'HACKHACKHACK…etc…'))
```

That is not quite the same. The result is nested tuples, and the timed work now includes the `total` function itself, not only the function it runs. That adds admin overhead, which pushes the best-of time up. The nested result ends up larger than the best total shown inside it. Taking `min` of `total` directly avoids that skew. The point is subtle, but it is true.

### Timing runner and script

To time iteration tools, write a script that defines test functions and hands them to the timer. The next example defines a utility module named `timer_runner`. Its `runner` function accepts any number of test functions. It passes each one to `bestoftotal` from the timer module.

timer_runner.py

```python
"Run passed-in test functions with the timer.py module"
import timer, sys
def runner(*tests):
    results = []
    print('Python', sys.version.split()[0], 'on', sys.platform)
    # Time
    for test in tests:
        besttime, result = timer.bestoftotal(10, 1000, test)
        results.append(result)
        print(f'{test.__name__:<9}: '
              f'{besttime:.5f} => [{result[0]}…{result[-1]}]')
    # Verify
    print('Results differ!'
          if any(result != results[0] for result in results[1:])
          else 'All results same.')
```

The `runner` function prints the Python version and platform. It steps through the tests, printing each function's `__name__` and its best time. It keeps the results, so it can check at the end that they all match. That check keeps the comparison fair, because every test must build the same data.

The next example defines the actual tests and passes them to the runner. Run this file as a top-level script to time the iteration styles from this part.

timer_tests.py

```python
"Test the relative speed of iteration coding alternatives."
from timer_runner import runner
repslist = list(range(10_000))
def forLoop():
    res = []
    for x in repslist:
        res.append(abs(x))
    return res
def listComp():
    return [abs(x) for x in repslist]
def mapCall():
    return list(map(abs, repslist)) # Use list() to force results
def genExpr():
    return list(abs(x) for x in repslist) # Use list() to force results
def genFunc():
    def gen():
        for x in repslist:
            yield abs(x)
    return list(gen()) # Use list() to force results
runner(forLoop, listComp, mapCall, genExpr, genFunc)
```

This script compares five ways to build a list of results. The reported times reflect about 100 million steps for each function. Each one builds a 10,000-item list 1,000 times. The process repeats 10 times to get the best-of time. Across all five functions, the script runs roughly 500 million steps.

Notice that the generator expression and the generator function go through `list`. Without that call, they would only produce generators that never do any real work. The `map` result needs `list` too, because it is an on-demand iterable.

The `range` result is created once at the top of the module, and it is wrapped in `list`. That keeps construction and traversal costs out of the timed loops. Removing the `list` wrapper inflates the times by some 25 percent.

### Iteration results

When the script runs under CPython 3.12 on the same macOS host, it prints these total times in seconds:

```
$ python3 timer_tests.py
Python 3.12.2 on darwin
forLoop : 0.26035 => [0...9999]
listComp : 0.20781 => [0...9999]
mapCall : 0.14399 => [0...9999]
genExpr : 0.41133 => [0...9999]
genFunc : 0.41203 => [0...9999]
All results same.
```

In short, `map` calls beat list comprehensions here, and list comprehensions beat `for` loops. Generator expressions and generator functions come last, roughly tied for slowest. Generator expressions are much slower than list comprehensions today, which is surprising. The difference shows up clearly in two lines:

```
return [abs(x) for x in repslist] # 0.20 seconds
return list(abs(x) for x in repslist) # 0.41 seconds: differs internally
```

The generator test also times the `list` call, but that does not seem to hurt `map`, so the effect is probably minor. The exact cause would need deeper analysis. A plausible reason is that a generator expression must save and restore its state while it produces each value. A list comprehension does not, so it runs quicker here and in the tests ahead.

### Other Pythons' results

For comparison, here are the same tests run under PyPy. PyPy is the optimized Python implementation covered earlier in this handbook. Its 7.3 release implements the Python 3.10 language. PyPy runs roughly 5 times faster than CPython here, and up to 10 times faster. Its timings can vary widely until its JIT has compiled the code fully.

```
$ pypy3 timer_tests.py
Python 3.10.14 on darwin
forLoop : 0.04329 => [0...9999]
listComp : 0.01876 => [0...9999]
mapCall : 0.04132 => [0...9999]
genExpr : 0.08744 => [0...9999]
genFunc : 0.08726 => [0...9999]
All results same.
```

On PyPy alone, list comprehensions win this test, but generators still lose badly. The bigger point is how much faster all of PyPy's results are today. On CPython, `map` is still the quickest so far.

These results differ from an older run in the prior edition. That run used CPython 3.3 on Windows, and there generators sat in the middle of the pack. The `for` loops fared much worse than they do today. The script also had a different name back then:

```
C:\code> c:\python33\python timeseqs.py
3.3.0 (v3.3.0:bd8afb90ebf2, Sep 29 2012, 10:57:17) [MSC v.1600 64 bit (AMD64)]
forLoop : 1.33290 => [0...9999]
listComp : 0.69658 => [0...9999]
mapCall : 0.56483 => [0...9999]
genExpr : 1.08457 => [0...9999]
genFunc : 1.07623 => [0...9999]
```

The absolute times reflect older, slower machines. The relative performance of these tools has clearly changed over about 12 years. It will probably change again in another dozen.

### For more good times: function calls and map

Now swap the `abs` calls for an inline `+` in each test, and watch the results shift in surprising ways. Only the code inside the test functions differs, and the shared runner treats every test the same. The next example shows the change.

timer_tests2.py

```python
from timer_runner import runner
repslist = list(range(10_000))
def forLoop():
    res = []
    for x in repslist:
        res.append(x + 10)
    return res
def listComp():
    return [x + 10 for x in repslist]
def mapCall():
    return list(map((lambda x: x + 10), repslist))
def genExpr():
    return list(x + 10 for x in repslist)
def genFunc():
    def gen():
        for x in repslist:
            yield x + 10
    return list(gen())
runner(forLoop, listComp, mapCall, genExpr, genFunc)
```

Now `map` is slower than the `for` loop statements, even though the loop version has more code. Either the need to call a user-defined function slows `map`, or the lack of function calls speeds up the others. On CPython 3.12 on the same host, the results are these:

```
$ python3 timer_tests2.py
Python 3.12.2 on darwin
forLoop : 0.28682 => [10...10009]
listComp : 0.24389 => [10...10009]
mapCall : 0.49622 => [10...10009]
genExpr : 0.44047 => [10...10009]
genFunc : 0.44476 => [10...10009]
All results same.
```

The earlier edition's Python 3.3 results, on a slower machine, look similar once you allow for machine differences. The interpreter optimizes so much internally that analysing performance like this is tricky. Without numbers, it is nearly impossible to guess which method is fastest. The best you can do is time your code with your own test parameters.

On this Python, a user-defined `lambda` inside `map` seems to slow it down out of proportion. The `+` operator is also slower than a trivial `abs` call across the board. List comprehensions run quickest in this case, though `map` wins in some others. List comprehensions look consistently faster than `for` loops, but even that needs qualifiers. Extra syntax such as `if` filters can change the relative speed. So can later Python changes, and usage modes this test did not cover.

The next example applies a simple user-defined function in all five iteration tests. Again, only the test functions' bodies change.

timer_tests3.py

```python
from timer_runner import runner
repslist = list(range(10_000))
def F(x): return x
def forLoop():
    res = []
    for x in repslist:
        res.append(F(x))
    return res
def listComp():
    return [F(x) for x in repslist]
def mapCall():
    return list(map(F, repslist))
def genExpr():
    return list(F(x) for x in repslist)
def genFunc():
    def gen():
        for x in repslist:
            yield F(x)
    return list(gen())
runner(forLoop, listComp, mapCall, genExpr, genFunc)
```

With this change, CPython 3.12 on the same host gives these results:

```
$ python3 timer_tests3.py
Python 3.12.2 on darwin
forLoop : 0.36206 => [0...9999]
listComp : 0.31181 => [0...9999]
mapCall : 0.35479 => [0...9999]
genExpr : 0.50531 => [0...9999]
genFunc : 0.50290 => [0...9999]
All results same.
```

Now `map` improves its relative standing. It comes second, between list comprehensions and `for` loops, instead of last as it did with `+`. That suggests `map` may be slower simply because it must call functions, and function calls are relatively slow in general. The other tools can win when they use plain expressions instead.

That hypothesis cannot explain the good showing for `map` in the first `abs` test, though. Calling a built-in function may be a special, fast case for `map` in CPython. The comparison with `ord` at the end of this chapter supports that theory.

Performance should not be your main concern when you write Python. The first step in optimizing Python code is to avoid optimizing too early. Write for readability and simplicity first. Optimize later, and only if you need to. Any of the five iteration styles may be quick enough for the data your program processes. If so, clarity should be the chief goal.

### More module mods

The `timer.py` module works as designed, but it could be friendlier. Its functions require repetition counts as their first arguments, with no defaults. That is a minor point, yet it is less than ideal in a general-purpose tool. A better design accepts repetition counts as keyword arguments with defaults, much as the print emulators in an earlier chapter did.

The repetition names must differ from the names in the timed function. That is why `_reps` replaces `reps`. The function object should also be positional-only, so the name `func` cannot clash with a keyword argument of the same name in the timed code. The next example makes these changes. Its docstrings are left out for space. The argument-matching sections earlier in this part give more insight.

timer2.py

```python
"Use keyword-only arguments with defaults for reps, and positional-only for func."
import time
timer = time.perf_counter
def once(func, /, *pargs, **kargs):
    start = timer()
    result = func(*pargs, **kargs)
    elapsed = timer() - start
    return (elapsed, result)
def total(func, /, *pargs, _reps=100_000, **kargs):
    total = 0
    for i in range(_reps):
        time, result = once(func, *pargs, **kargs)
        total += time
    return (total, result)
def bestof(func, /, *pargs, _reps=5, **kargs):
    return min(once(func, *pargs, **kargs) for i in range(_reps))
def bestoftotal(func, /, *pargs, _reps1=50, **kargs):
    return min(total(func, *pargs, **kargs) for i in range(_reps1)) # _reps => **
```

Because the names changed, this module is not a drop-in replacement. The repetition arguments follow a new naming scheme. That means the `timer_runner` module needs a small edit to use it. Otherwise it works the same way. Compare its output on the same host with the results of `timer.py`:

```
$ python3
>>> import timer2
>>> timer2.total(pow, 2, 1000, _reps=100_000)[0]
0.0865794476121664
>>> timer2.total(str.upper, 'hack' * 100, _reps=100_000)[0]
0.04620114527642727
>>> timer2.bestoftotal(pow, 2, 1000, _reps1=50, _reps=100_000)[0]
0.07179990829899907
>>> timer2.bestoftotal(str.upper, 'hack' * 100, _reps1=50, _reps=100_000)[0]
0.0393348871730268
```

This time, the repetition defaults can apply or not:

```
>>> timer2.total(str.upper, 'hack' * 100)[0]
0.047992002684623
>>> timer2.bestoftotal(str.upper, 'hack' * 100)[0]
0.03935634717345238
>>> timer2.bestoftotal(str.upper, 'hack' * 100, _reps=10_000)[0]
0.00393257150426507
```

A `_reps` argument passed to `bestoftotal` travels along in `**kargs`, because nothing else matches it. For a closer look, time user-defined functions with richer argument headers:

```
>>> def f(a, b, c=88, d=99): return(a, b, c, d)
>>> f(1, 2)
(1, 2, 88, 99)
>>> timer2.bestoftotal(f, 1, 2, _reps1=50, _reps=100_000)
(0.014080120716243982, (1, 2, 88, 99))
>>> timer2.bestoftotal(f, 1, 2, c=66, d=77, _reps1=50, _reps=100_000)
(0.021575820166617632, (1, 2, 66, 77))
>>> timer2.bestoftotal(f, 1, 2, c=66, d=77, _reps1=50)
(0.021694606635719538, (1, 2, 66, 77))
>>> timer2.bestoftotal(f, 1, 2, c=66, d=77, _reps=100_000)
(0.021556788589805365, (1, 2, 66, 77))
>>> def f(a, *b, c=88, **d): return(a, b, c, d)
>>> f(1, 2, 3, c=66, d=77, e=88)
(1, (2, 3), 66, {'d': 77, 'e': 88})
>>> timer2.bestoftotal(f, 1, 2, 3, c=66, d=77, e=88)
(0.030859854072332382, (1, (2, 3), 66, {'d': 77, 'e': 88}))
>>> timer2.bestoftotal(f, 1, 2, 3, c=66, d=77, e=88, _reps1=10)
(0.030802161898463964, (1, (2, 3), 66, {'d': 77, 'e': 88}))
>>> timer2.bestoftotal(f, 1, 2, 3, c=66, d=77, e=88, _reps=10_000)
(0.0030745575204491615, (1, (2, 3), 66, {'d': 77, 'e': 88}))
```

Passing keyword arguments to a timed function adds a small unpacking cost. The original `timer.py` has the same overhead. That cost is irrelevant when you compare relative times.

Beyond this, custom benchmarking is fun but open-ended. You could time set and dictionary comprehensions against their `for` loop equivalents. You could explore the `profile` and `cProfile` modules, which build full-program profiles instead of focused benchmarks. Or you could explore `timeit`, which works much like this chapter's homegrown code and offers extra options.

> Note: Decorator timers preview. Here we pass functions into the timers by hand. A decorator-based timer lets callers invoke functions normally, but it adds `@` syntax where the function is defined. Decorators suit instrumenting functions inside a larger system. They do not fit the test-call patterns used here as easily. Every call to a decorated function runs the timing logic, which can help or hurt depending on your goals.

## Benchmarking with timeit

The earlier section used custom timing functions. The standard library also ships a module named `timeit`. It works in similar ways, but it offers more flexibility. It times code strings as well as functions, and it has a command-line mode.

Python's "batteries included" approach means a precoded option exists for most goals. You still need the ideas behind those options to choose and use them well. The `timeit` module shows this clearly. Newcomers have misused it when they did not understand those ideas. Now that the basics are clear, let us move to a tool that automates much of this work.

### Basic timeit usage

With `timeit`, tests are specified either as callable objects or as statement strings. A string can hold several statements, separated by `;` or by `\n` line breaks. It can indent nested blocks with spaces or tabs, as in `\n\t`. Tests may also include setup actions. You can launch them from the command line or from API calls, and from scripts or the REPL.

### API-calls mode

The `repeat` call returns a list of total times. It runs a test `number` times for each of the `repeat` runs. The `min` of that list gives the best time among the runs. That filters out system load fluctuations, which can otherwise skew results high. Pass the code to the `stmt` keyword, or as the first positional argument. It can be a string or a no-argument function.

The next example times a list comprehension on CPython 3.12 and on PyPy, using REPLs on macOS. Each result is the best total time among 5 runs. Each run executes the code string 1,000 times. The string builds a 1,000-item list of integers on every pass. `timeit` has default repeat counts, but being explicit keeps the runs comparable.

```
$ python3
>>> import timeit
>>> min(timeit.repeat(stmt='[x ** 2 for x in range(1000)]', number=1000, repeat=5))
0.05187674192711711
$ pypy3
>>>> import timeit
>>>> min(timeit.repeat(stmt='[x ** 2 for x in range(1000)]', number=1000, repeat=5))
0.00252467580139637
```

PyPy comes in about 20 times faster than CPython 3.12 here. This is a small, artificial benchmark, but the gap is striking. It fits a relative speed ranking seen elsewhere in this book. CPython still beats PyPy on some kinds of code, though, and a future JIT may change the picture. This test also measures integer math, which is everywhere in Python. PyPy's lead is even larger for non-integer code. Try squaring a float to see for yourself.

These results differ from the earlier PyPy ratio of about 10 times for list comprehensions. The different code shape is one reason. Another is that `timeit` builds and runs a generated `def` statement around the test string. That avoids a function call on every inner loop. This does not matter for relative speed, because times from the same tool are comparable with each other.

Code to be timed is a string here. Multiline code in some modes needs manual line breaks and indentation. All such code must follow Python's rules for string literals, quotes, and escapes. A code string cannot contain the same quote that encloses it unless you escape it. You can avoid that trouble by timing callables, though those take no arguments.

### Command-line mode

The `timeit` module also runs as a script from the command line. Use the `-m` switch, which finds `timeit` on the module search path. Or give the file path explicitly. Quote or escape the Python code according to your shell's rules. Double quotes are generally portable, but quoting is still a potential weak spot.

In this mode, `timeit` reports the average time for one loop, and `-n` sets the loop count. It uses units such as usec (microseconds), msec (milliseconds), sec (seconds), and nsec (nanoseconds). To compare with API totals, multiply by the loop count. For example, a loop time of 51 usec, over 1,000 loops, totals 51 msec. That is 0.051 seconds. For CPython 3.12 on macOS:

```
$ python3 -m timeit -n 1000 "[x ** 2 for x in range(1000)]"
1000 loops, best of 5: 51.9 usec per loop
$ python3 -m timeit -n 1000 -r 50 "[x ** 2 for x in range(1000)]"
1000 loops, best of 50: 51.8 usec per loop
```

The command line can also verify that the choice of timer does not change these comparisons. `timeit` uses `time.perf_counter` by default. Its `-p` flag switches it to `time.process_time`. As tested, there is no discernible difference:

```
$ python3 -m timeit -p -n 1000 -r 50 "[x ** 2 for x in range(1000)]"
1000 loops, best of 50: 51.8 usec per loop
```

PyPy's command-line `timeit` gives a surprise:

```
$ pypy3 -m timeit -n 1000 -r 50 "[x ** 2 for x in range(1000)]"
WARNING: timeit is a very unreliable tool. use pyperf or something
else for real measurements
pypy3 -m pip install pyperf
pypy3 -m pyperf timeit -n '1000' -r '50' '[x ** 2 for x in range(1000)]'
------------------------------------------------------------
1000 loops, average of 50: 1.54 +- 0.568 usec per loop (using standard deviation)
```

PyPy has customized its command-line `timeit`. It prints a warning that suggests another timer, and it shows averages instead of minimums. Both changes are opinionated, and both were made since the prior edition. They are understandable for a tool so sensitive to benchmark results. The `pyperf` package is not part of the standard library. It needs a separate install, but it may offer more advanced timing options that suit some goals.

### Handling multiline statements

API-call mode has no shell to worry about. To time larger blocks, load the code from a file, use a triple-quoted string, or use newlines and indentation that satisfy Python's syntax. Because you pass Python strings to a Python function, watch nested quotes. Use escapes or mixed quotes when needed. The example below times the loop alternatives from an earlier chapter on CPython 3.12. The same pattern works for the file-reading alternatives too.

```
$ python3
>>> import timeit
>>> min(timeit.repeat(number=100_000, repeat=5,
stmt='L = [1, 2, 3, 4, 5]\nfor i in range(len(L)): L[i] += 1'))
0.028153221122920513
>>> min(timeit.repeat(number=100_000, repeat=5,
stmt='L = [1, 2, 3, 4, 5]\ni=0\nwhile i < len(L):\n\tL[i] += 1\n\ti += 1'))
0.03337613819167018
>>> min(timeit.repeat(number=100_000, repeat=5,
stmt='L = [1, 2, 3, 4, 5]\nM = [x + 1 for x in L]'))
0.021507765166461468
```

To run multiline statements from the command line, pass each statement line as a separate argument. Use spaces for indentation. `timeit` joins the lines with newlines and re-indents them as needed. Spaces usually work better than tabs in this mode, because shells vary. Quote the code arguments if your shell requires it. The first command below is split across two lines here to fit the page. In some shells, you must type it on one line.

```
$ python3 -m timeit -n 100000 -r 5 "L = [1,2,3,4,5]" "i=0" "while i < len(L):"
" L[i] += 1" " i += 1"
100000 loops, best of 5: 332 nsec per loop
$ python3 -m timeit -n 100000 -r 5 "L = [1,2,3,4,5]" "M = [x + 1 for x in L]"
100000 loops, best of 5: 218 nsec per loop
```

### Other timeit usage modes

The `timeit` module also accepts setup code. Setup runs in the same scope as the main statement, but its time is not charged to the main statement's total. Use it for work you want to exclude, such as imports and building test data. Names created by setup code are available to the test statement. Names defined in the interactive shell generally are not.

To give setup code from the command line, use `-s`. Repeat it for multiline setups. In API calls, use a `setup` string argument. The next pair of commands splits list creation into setup, so the second command times only the iteration:

```
$ python3 -m timeit -n 100000 -r 5 "L = [1,2,3,4,5]" "M = [x + 1 for x in L]"
100000 loops, best of 5: 211 nsec per loop
$ python3 -m timeit -n 100000 -r 5 -s "L = [1,2,3,4,5]" "M = [x + 1 for x in L]"
100000 loops, best of 5: 175 nsec per loop
```

As a general rule, the more code a test statement includes, the closer its results match realistic code. Setup splitting focuses a test sharply, but it can also drift from real use.

### Timing sort speed

To demo setup code in API-call mode, the next example times a sort-based option from the minimum-value example earlier in this part. Here is the function, which lives in `mins.py`:

```python
def min4(*args):
    return sorted(args)[0]
```

The results show that sequences sort much faster when they are already ordered. Run this from the folder that holds `mins.py` to see it for yourself:

```
>>> from timeit import repeat # Standard-library module
>>> min(repeat(number=1000, repeat=5, # Sort an ordered list in min4
setup='from mins import min4\n' # Adjacent strings concatenated
'vals=list(range(1000))', # Code within () spans lines
stmt= 'min4(*vals)')) # First import prints output
0.011066518723964691
>>> min(repeat(number=1000, repeat=5, # Sort a randomly ordered list
setup='from mins import min4\n'
'import random\n'
'vals=[random.random() for i in range(1000)]',
stmt= 'min4(*vals)'))
0.068130933213979
```

The randomly ordered list takes far longer to sort. See Python's manuals for more on the `random` module used here. `timeit` can also report only total time, time callable objects instead of strings, and use a class-based API. Its command line accepts more switches, and its API calls accept more arguments. Those details are beyond this chapter. The following section builds a small helper around `timeit`, so you no longer type each command by hand.

## Automating timeit benchmarking

Rather than more `timeit` details, study a program that uses it to time coding alternatives and Python versions. It lets you define a set of tests in a separate file. It also collects data from several Pythons, both one at a time and grouped together. Grouped mode has limits today, as you will see.

### Benchmark module

The module `pybench.py` times a sequence of statements. Scripts that import it supply the statements. It runs them either on the Python executing the script or on every Python version in a list. It relies on a few standard-library tools, such as `os.popen`.

Because it mostly applies ideas you have already seen, and because it is well documented, treat this file as self-study material. It is also a good exercise in reading Python code.

pybench.py

```python
r"""
Time the speed of one or more Pythons on multiple code-string
benchmarks with timeit. This is a function, to allow timed tests
to vary. It times all code strings in a passed list, in either:
1) The Python running this script, by timeit API calls
2) Multiple Pythons whose paths are passed in a list, by reading
   the output of timeit command lines run by os.popen that use
   Python's -m switch to find timeit on the module search path
In command-line mode (2) only, this replaces all " in timed code
with ', to avoid clashes with argument quoting; splits multiline
statements into one quoted argument per line so all will be run;
and replaces all \t in indentation with 4 spaces for uniformity.
Caveats:
- Command-line mode (only) uses naive quoting and MAY FAIL if code
  embeds and requires double quotes; quoted code is incompatible
  with the host shell; or command length exceeds shell limits.
- PyPy is largely unusable in command-line mode (2) today, as its
  modified timeit output in this mode is jarring in the report.
- This does not (yet?) support a setup statement in any mode: the
  time of all code in the test stmt is charged to its total time.
As fallbacks on fails, use either this module's API-call mode to
test one Python at a time, or the homegrown timer.py module.
"""
import sys, os, time, timeit
defnum, defrep = 1000, 5 # May vary per stmt
def show_context():
    """
    Show run's context using an arguably gratuitous f-string
    that fails on 3.10 PyPy without "..." for nested ' quotes.
    """
    print(f"Python {'.'.join(str(x) for x in sys.version_info[:3])}"
          f' on {sys.platform}'
          f" at {time.strftime('%b-%d-%Y, %H:%M:%S')}")
def runner(stmts, pythons=None, tracecmd=False):
    """
    Main logic: run tests per input lists which determine usage modes.
    stmts: [(number?, repeat?, stmt-string)]
    pythons: None=host python only, or [python-executable-paths]
    """
    show_context()
    for (number, repeat, stmt) in stmts:
        number = number or defnum
        repeat = repeat or defrep # 0=default
        if not pythons:
            # Run stmt on this python: API call
            # No need to split lines or quote here
            best = min(timeit.repeat(stmt=stmt, number=number, repeat=repeat))
            print(f'{best:.4f} {stmt[:70]!r}')
        else:
            # Run stmt on all pythons: command line
            # Split lines into quoted arguments
            print('-' * 80)
            print(repr(stmt)) # show quotes
            for python in pythons:
                stmt = stmt.replace('"', "'") # all " => '
                stmt = stmt.replace('\t', ' ' * 4) # tab => 4 spaces
                lines = stmt.split('\n') # line => arg
                args = ' '.join(f'"{line}"' for line in lines) # arg => "arg"
                oscmd = f'{python} -m timeit -n {number} -r {repeat} {args}'
                print(oscmd if tracecmd else python)
                print('\t' + os.popen(oscmd).read().rstrip())
```

### Benchmark script

This module is only half the picture. Test scripts pass concrete lists of statements and Pythons into its function. The script below uses command-line arguments to choose its mode. The `-a` switch tests all the listed Pythons instead of just one. The `-t` switch traces the command lines it builds, so you can see how quotes, multiline statements, and tabs are handled.

pybench_tests.py

```python
"""
Run pybench.py to time one or more Pythons on multiple code strings.
Use command-line arguments (which appear in sys.argv) to select modes:
<python> pybench_tests.py
    times just the hosting Python on all code listed in stmts below
python3 pybench_tests.py -a
    times all stmts in all pythons whose paths are listed below
python3 pybench_tests.py -a -t
    same as -a, but also traces command lines in full
Edit stmts below to change tested code, and edit pythons below to give
paths of Python executables to be tested in -a mode. To find a Python's
path, start its REPL, run "import sys", and inspect "sys.executable".
"""
import pybench, sys
pythons = [
    '/Library/Frameworks/Python.framework/Versions/3.12/bin/python3',
    '/Users/me/Downloads/pypy3.10-v7.3.16-macos_x86_64/bin/pypy3',
]
stmts = [
    # Iterations
    (0, 0, '[x ** 2 for x in range(1000)]'), # (num,rpt,stmt)
    (0, 0, 'res=[]\nfor x in range(1000): res.append(x ** 2)'), # \n=multistmt
    (0, 0, 'list(map(lambda x: x ** 2, range(1000)))'), # \n\t=indent
    (0, 0, 'list(x ** 2 for x in range(1000))'),
    # String ops
    (0, 0, "s = 'hack' * 2500\nx = [s[i] for i in range(10_000)]"),
    (0, 0, "s = '?'\nfor i in range(10_000): s += '?'"), # A PyPy loss!
]
tracecmd = '-t' in sys.argv # -t: trace command lines?
pythons = pythons if '-a' in sys.argv else None # -a: all in list, else one?
pybench.runner(stmts, pythons, tracecmd) # Time pythons on all stmts
```

### Timing individual Pythons

The next output comes from running the script to test the Python that runs it. This mode makes direct `timeit` API calls, not command lines. Total time appears in the left column, and the tested statement appears quoted on the right. A context line at the top comes from the `sys` and `time` modules. These two runs use CPython 3.12 and PyPy 7.3, which implements Python 3.10, on the same host:

```
$ python3 pybench_tests.py
Python 3.12.2 on darwin at Jun-27-2024, 15:21:02
0.0533 '[x ** 2 for x in range(1000)]'
0.0605 'res=[]\nfor x in range(1000): res.append(x ** 2)'
0.0804 'list(map(lambda x: x ** 2, range(1000)))'
0.0759 'list(x ** 2 for x in range(1000))'
0.4042 "s = 'hack' * 2500\nx = [s[i] for i in range(10_000)]"
0.8061 "s = '?'\nfor i in range(10_000): s += '?'"
$ pypy3 pybench_tests.py
Python 3.10.14 on darwin at Jun-27-2024, 15:22:14
0.0020 '[x ** 2 for x in range(1000)]'
0.0040 'res=[]\nfor x in range(1000): res.append(x ** 2)'
0.0030 'list(map(lambda x: x ** 2, range(1000)))'
0.0077 'list(x ** 2 for x in range(1000))'
0.0529 "s = 'hack' * 2500\nx = [s[i] for i in range(10_000)]"
1.2942 "s = '?'\nfor i in range(10_000): s += '?'"
```

Drawing conclusions from this is left as an exercise. Notice, though, that PyPy loses to CPython on the very last test. Performance varies by code, and absolute numbers in benchmarking are perilous at best.

### Timing multiple Pythons

Adding `-a` makes the script test each statement on several Pythons. The script itself runs under CPython 3.12. It launches shell command lines that start the other Pythons, and those run the `timeit` module on the statement strings. To make this work, the script must split, format, and quote multiline statements for both `timeit` and the shell.

This mode relies on the `-m` switch to find `timeit` and run it as a script. It uses `os.popen` to run shell commands, and `sys.argv` to read the command-line arguments. Add `-t` to trace the commands. Here is the result:

```
$ python3 pybench_tests.py -a
Python 3.12.2 on darwin at Jun-27-2024, 16:12:39
--------------------------------------------------------------------------------
'[x ** 2 for x in range(1000)]'
/Library/Frameworks/Python.framework/Versions/3.12/bin/python3
1000 loops, best of 5: 52.7 usec per loop
/Users/me/Downloads/pypy3.10-v7.3.16-macos_x86_64/bin/pypy3
WARNING: timeit is a very unreliable tool. use pyperf or something
else for real measurements
pypy3 -m pip install pyperf
pypy3 -m pyperf timeit -n '1000' -r '5' '[x ** 2 for x in range(1000)]'
------------------------------------------------------------
1000 loops, average of 5: 2.66 +- 1.55 usec per loop (using standard deviation)
…more output clipped…
```

Regrettably, this all-Pythons mode is nearly unusable today. PyPy's inserted changes make its command-line output look very different from the norm, and hard to read. There is no switch to turn them off. The only fix is copying CPython's `timeit.py` into PyPy's library folder, which is too much for this demo. So the `-a` mode still works in this edition. It is best used with Pythons that do not modify a widely used standard-library module like `timeit`.

### Timing set and dictionary iterations

Single-Python mode is still useful for scripting a batch of benchmarks, and it works on PyPy too. The next script runs set and dictionary tests through the driver module `pybench.py`. It shows how each construction style compares.

pybench_tests2.py

```python
import pybench
stmts = [
    # Sets
    (0, 0, '{x ** 2 for x in range(1000)}'),
    (0, 0, 'set(x ** 2 for x in range(1000))'),
    (0, 0, 's=set()\nfor x in range(1000): s.add(x ** 2)'),
    # Dicts
    (0, 0, '{x: x ** 2 for x in range(1000)}'),
    (0, 0, 'dict((x, x ** 2) for x in range(1000))'),
    (0, 0, 'd={}\nfor x in range(1000): d[x] = x ** 2'),
]
pybench.runner(stmts, None, False) # No -a mode in this script
```

Earlier, we noted that handing a generator to a type name, such as `set`, costs extra time. This output on CPython 3.12 and on PyPy 7.3, which implements Python 3.10, confirms it:

```
$ python3 pybench_tests2.py
Python 3.12.2 on darwin at Jun-27-2024, 16:20:19
0.0746 '{x ** 2 for x in range(1000)}'
0.0947 'set(x ** 2 for x in range(1000))'
0.0834 's=set()\nfor x in range(1000): s.add(x ** 2)'
0.0745 '{x: x ** 2 for x in range(1000)}'
0.1174 'dict((x, x ** 2) for x in range(1000))'
0.0754 'd={}\nfor x in range(1000): d[x] = x ** 2'
$ pypy3 pybench_tests2.py
Python 3.10.14 on darwin at Jun-27-2024, 16:22:18
0.0191 '{x ** 2 for x in range(1000)}'
0.0222 'set(x ** 2 for x in range(1000))'
0.0186 's=set()\nfor x in range(1000): s.add(x ** 2)'
0.0188 '{x: x ** 2 for x in range(1000)}'
0.0398 'dict((x, x ** 2) for x in range(1000))'
0.0185 'd={}\nfor x in range(1000): d[x] = x ** 2'
```

### Conclusion: comparing tools

A third script, `pybench_tests3.py`, checks that the `timeit` tools give results similar to the homegrown timer. Its findings generally match the iteration results shown earlier in this chapter, although they arrive at them by a very different route:

```
$ python3 pybench_tests3.py
Python 3.12.2 on darwin at Jun-27-2024, 16:26:44
0.2766 "res=[]\nfor x in 'hack' * 2500: res.append(ord(x))"
0.2173 "[ord(x) for x in 'hack' * 2500]"
0.1430 "list(map(ord, 'hack' * 2500))"
0.4172 "list(ord(x) for x in 'hack' * 2500)"
```

If you want a closer look, dig into this chapter's code and write more tests of your own. Exploring benchmarks is enjoyable, and the remaining experiments are left to you as practice. Results change with every Python release and every machine, so retest with your own Pythons and devices before you trust any number here.

## Function gotchas

Now that the function story is complete, here are some common pitfalls. Functions have a few jagged edges you might not expect. They are obscure, and a few have started to fall away from the language in recent releases. Still, most of them have tripped up new users.

### Hiding built-ins by assignment

You saw earlier that you can reassign a built-in name in a closer local or global scope. The reassignment hides the built-in and replaces it for the rest of that scope. You can no longer reach the original built-in value there. If you do not need the original, this is harmless, because many names are built in and can be reused freely.

If your code relies on a built-in name that you reassign, however, you will have problems. So avoid doing that unless you really mean it. The built-ins you use often will soon become second nature. Python's error trapping also tends to flag these mistakes early in testing, when a name is not what you expect.

### Wrapping up the case study

This case study measured the iteration alternatives from this part and other tools from earlier chapters. It also measured one alternative Python implementation. It used both custom timer code and `timeit`, with a helper that runs code in several modes. It also reviewed common function mistakes that cause trouble.

This concludes the functions part. The next topic is modules, the files that group functions into reusable units. After that comes classes, which are largely packages of functions with special first arguments. Before moving on, work through the questions below to practise what you learned about functions here.

## Check your understanding

Work through these questions to review the scope ideas in this chapter. Try to answer each one before you read the answer key, then come back to any that surprised you.

1. What is the output of the following code, and why?

```
>>> X = 'Hack'
>>> def func():
...     print(X)
>>> func()
```

2. What is the output of this code, and why?

```
>>> X = 'Hack'
>>> def func():
...     X = 'Py!'
>>> func()
>>> print(X)
```

3. What does this code print, and why?

```
>>> X = 'Hack'
>>> def func():
...     X = 'Py!'
...     print(X)
>>> func()
>>> print(X)
```

4. What output does this code produce, and why?

```
>>> X = 'Hack'
>>> def func():
...     global X
...     X = 'Py!'
>>> func()
>>> print(X)
```

5. What about this code? What is the output, and why?

```
>>> X = 'Hack'
>>> def func():
...     X = 'Py!'
...     def nested():
...         print(X)
...     nested()
>>> func()
>>> print(X)
```

6. How about this example? What is its output, and why?

```
>>> def func():
...     X = 'Py!'
...     def nested():
...         nonlocal X
...         X = 'Hack'
...     nested()
...     print(X)
>>> func()
```

7. Name three or more ways to retain state information across calls in a Python function.
8. What is the output of the following code, and why?

```
>>> def func(a, b=4, c=5):
...     print(a, b, c)
>>> func(1, 2)
```

9. What is the output of this code, and why?

```
>>> def func(a, b, c=5):
...     print(a, b, c)
>>> func(1, c=3, b=2)
```

10. How about this code: what is its output, and why?

```
>>> def func(a, *pargs):
...     print(a, pargs)
>>> func(1, 2, 3)
```

11. What does this code print, and why?

```
>>> def func(a, **kargs):
...     print(a, kargs)
>>> func(a=1, c=3, b=2)
```

12. What gets printed by this, and why?

```
>>> def func(a, b, c=3, d=4): print(a, b, c, d)
>>> func(1, *(5, 6))
```

13. One last time: what is the output of this code, and why?

```
>>> def func(a, b, c):
...     a = 2; b[0] = 'x'; c['a'] = 'y'
>>> L=1; M=[1]; N={'a': 0}
>>> func(L, M, N)
>>> L, M, N
```

14. How are `lambda` expressions and `def` statements related?
15. What is the point of using `lambda`?
16. Compare and contrast `map`, `filter`, and `reduce`.
17. What are function annotations, and how are they used?
18. What are recursive functions, and how are they used?
19. What are some general design guidelines for coding functions?
20. Name three or more ways that functions can communicate results to a caller.
21. What is the difference between enclosing a list comprehension in square brackets and parentheses?
22. How are generators and iterators related?
23. How can you tell if a function is a generator function?
24. What does a `yield` statement do?
25. How are `map` calls and list comprehensions related? Compare and contrast the two.
26. What do `async def` and `await` mean in a Python script?

Answers:

1. The output is `Hack`. The function references a global variable in the enclosing module. Because the function does not assign `X`, Python treats `X` as a global.
2. The output is `Hack` again. Assigning `X` inside the function makes it a local, and that local hides the global of the same name. The `print` statement finds the global, which is unchanged.
3. It prints `Py!` on one line and `Hack` on the next. The reference inside the function finds the assigned local. The `print` on the last line finds the global.
4. This time it prints only `Py!`. The `global` declaration makes the assignment inside the function refer to the module-level `X`, so the global itself changes.
5. The output is `Py!` on one line and `Hack` on the next. The `print` inside the nested function finds the name in the enclosing function's local scope, through the E layer. The final `print` finds the global variable.
6. This example prints `Hack`. The `nonlocal` statement makes the assignment to `X` inside the nested function change `X` in the enclosing function's scope. Without it, the assignment would make `X` local to the nested function, a different variable, and the code would print `Py!`.
7. Even though local variables disappear when a function returns, you can keep state with shared global variables, with `nonlocal` references in nested functions, or with default argument values. Function attributes attach state to the function itself, instead of looking it up in a scope. Classes and OOP often retain state better than scope-based techniques, because the attribute assignments are explicit. Changing mutable objects in scopes and defaults also works, but some local coding standards may not allow it.

8. The output is `1 2 5`. The values `1` and `2` match `a` and `b` by position, and `c` is left out, so it defaults to `5`.
9. The output is `1 2 3`. The value `1` matches `a` by position, and `b` and `c` match `2` and `3` by name. Order does not matter with keywords.
10. The output is `1 (2, 3)`. The value `1` matches `a`, and `*pargs` collects the remaining positional arguments into a tuple.
11. The output is `1 {'c': 3, 'b': 2}`. The value `1` matches `a` by name, and `**kargs` collects the remaining keywords into a dictionary. Its keys keep the order in which they were passed.
12. The output is `1 5 6 4`. The value `1` matches `a`, `5` and `6` unpack into `b` and `c`, and `d` keeps its default of `4`.
13. The output is `(1, ['x'], {'a': 'y'})`. The first assignment inside the function does not reach the caller. The next two change passed-in mutable objects in place, so the caller sees them.
14. Both create function objects to call later. A `lambda` is an expression, so it returns a function object instead of assigning a name, and it fits where a `def` cannot. Its body is a single expression, so it suits small functions, not large ones.
15. A `lambda` lets you inline a small piece of code, defer it, and give it state through defaults and enclosing variables. You never need one, because a `def` always works. It helps for small handlers used in one place, such as GUI callbacks, and it pairs well with `map` and `filter`.
16. All three apply a function to the items of an iterable. `map` collects each call's result. `filter` keeps the items for which the function returns a true value. `reduce` combines the items into a single value by applying the function to a running result and the next item. `reduce` lives in `functools`, not in the built-in scope.
17. Annotations are syntax attached to a function's arguments and result. Python collects them in `__annotations__` and gives them no meaning of its own. Other tools can read them, for example for type hints or error checking.
18. Recursive functions call themselves, directly or indirectly, to repeat work. They can traverse structures of arbitrary shape and depth. They can also iterate in general, though a loop is usually simpler and more efficient. Explicit stacks or queues can simulate or replace recursion.
19. Keep functions small and self-contained, with one unified purpose. Communicate through arguments and return values. Change mutable arguments only when the caller expects it. Some programs need other communication mechanisms, but these basics keep code easy to reuse.
20. Functions can send results back with `return` statements, by changing passed-in mutable arguments, and by setting global variables. Globals are generally discouraged because they make code harder to understand, except in special cases such as multithreaded programs. Functions can also communicate through files and sockets, which this chapter does not cover.

21. A list comprehension in square brackets builds the whole result list in memory at once. In parentheses, it becomes a generator expression. The internal syntax is the same and the meaning is similar, but it does not build the list. It returns a generator object that yields one item at a time, whenever an iteration tool or `next` asks.
22. Generators are iterable objects that follow the iteration protocol automatically. Each has an iterator with a `__next__` method, which `next` runs. That method advances one item at a time and raises an exception at the end. Python has three ways to make one: generator functions with `def` and `yield`, generator expressions with parenthesized comprehensions, and classes that define `__iter__`.
23. A generator function contains a `yield` statement, with or without its `from` extension. Otherwise it is written like a normal function. Python compiles it specially, so calling it returns a generator object that keeps its state between values. Deleting the `yield` turns it into a normal function, but deleting code can cause other problems.
24. The `yield` statement sends a result back to the caller and suspends the function's state. The function resumes after that `yield` when `next` or `__next__` is called again. The generator `send` method also resumes it, and it can pass a value that becomes the value of the `yield` expression. A `return` statement ends the generator and can attach a value to the `StopIteration` exception.
25. Both produce a series of values by applying an operation to each item of an iterable, one item at a time. `map` applies a function call to each item. A list comprehension applies any expression. Comprehensions can also nest `for` loops and use `if` clauses, which cover the work of `filter`. `map` produces a generator of values, while a list comprehension builds the whole result list in memory, which can matter for large lists.
26. `async def` defines an asynchronous function, usually called a coroutine. `await` waits for another asynchronous object to produce its value. While it waits, it can give control back to an event loop, so other code can run. `async def` is required to use `await`, `async for`, and `async with`. Concurrency in this model generally needs an event loop and scheduling calls from the `asyncio` module.

27. Which iteration tools were quickest and slowest on CPython 3.12 in this chapter's timer tests? Why should you not treat those results as final for your own code?
28. Why does the `timer` module take the `min` of the best-of results instead of an average? Explain what the time-first tuples have to do with it.
29. What does the `-p` flag change in `timeit` command-line mode, and did it change the results in this chapter?
30. In `timer2.py`, why are the repetition arguments named `_reps` and `_reps1` instead of `reps`?
31. Timing tools exercise: Which of `math.sqrt(X)`, `X ** .5`, and `pow(X, .5)` runs fastest on your device? Time each one with `bestoftotal` from `timer2.py`. How would you time dictionary comprehensions against `for` loops?
32. Keywords exercise: Write `adder(red, green, blue)` with a default for each argument. Does the call `adder(blue=1, red=2)` work, and why? Then generalize it to accept any number of keyword arguments.
33. Primes revisited: Package the prime-checking loop as a function that takes `num` as an argument. What goes wrong when you replace `//` with `/`, and how should negative numbers, `0`, and `1` be handled?
34. Iterations and comprehensions exercise: Build a list of the square roots of `[2, 4, 9, 16, 25]` with a `for` loop, a `map` call, a list comprehension, and a generator expression. Which approach do you like best?
35. Argument matching: Define `f5(a, b=2, c=3)` and `f6(a, b=2, *c)`. Predict the results of `f5(1, c=4)` and `f6(1, *[3, 4])`, then test them.
36. Function gotchas: After you assign `open = 99` at the top level of a module, what happens to a later `open('data.txt')` call in that module? How can you restore the built-in?

## Sources and review notes

- Source: *Learning Python*, 6th edition (`learning-python-6th-edition`). Chapters used are listed in each section.
- Chapter used: "17. Scopes" from *Learning Python*, 6th edition (`learning-python-6th-edition`).
- Chapter used: "18. Arguments" from *Learning Python*, 6th edition (`learning-python-6th-edition`).
- Chapter used: "19. Function Odds and Ends" from *Learning Python*, 6th edition (`learning-python-6th-edition`).
- Chapter used: "20. Comprehensions and Generations" from *Learning Python*, 6th edition (`learning-python-6th-edition`).
- Chapter used: "21. The Benchmarking Interlude" from *Learning Python*, 6th edition (`learning-python-6th-edition`).
