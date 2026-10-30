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

This chapter goes deeper into material that chapter 3.1 only introduces. You will meet it again whenever you read or write the Python behind schedulers, operators, exporters and training launchers.

## Python scope basics

### Names live in namespaces

Once you write your own functions, you need a clear idea of what a name means. When your code uses a name, Python creates it, changes it, or looks it up in a namespace. A namespace is simply a place where names live. In relation to code, each namespace corresponds to a scope, which is the part of the program where a name is visible.

### Assignment decides the scope

Almost everything about names in Python happens at assignment time. A name springs into existence when you first assign it a value, and you must assign it before you use it. Python does not ask you to declare names ahead of time. The place where you assign a name in your source code decides which namespace it binds to, and so where it can be seen.

Functions add an extra namespace layer. By default, every name assigned inside a function belongs to that function and no other. That gives you three practical rules:

- A name assigned inside a `def` can be seen only by the code inside that `def`. You cannot refer to it from outside the function.
- A name assigned inside a `def` does not clash with a variable of the same name outside it. A name `X` in another `def`, or at the top level of a module file, is a different variable.
- A name assigned in a `lambda` works the same way. Assignment inside a `lambda` is limited to its arguments and `:=` named assignments, and it is much less common than inside a `def`.

The scope of a variable depends only on where you assign it in the source code. Which functions call which has no effect on it. Python calls this lexical scoping, so you can settle most scope questions by reading the code without running it. A variable can be assigned in three places, and each place gives it a different scope:

- If a variable is assigned inside a `def` or `lambda`, it is local to that function.
- If a variable is assigned in an enclosing `def` or `lambda`, it is nonlocal to the functions nested inside it.
- If a variable is assigned outside all `def`s and `lambda`s, it is global to the whole file.

For example, this module file holds two different variables named `X`:

```python
X = 99 # Global (module) scope X
def func():
    X = 88 # Local (function) scope X: a different variable
```

Even though both names are `X`, their scopes keep them apart. Function scopes prevent name clashes, and they make each function more self-contained. Its code does not need to know about names used elsewhere.

### Scopes overview

Before you wrote functions, none of your code sat inside a `def`. The names you used lived in a module, or they were built-ins such as `open` and `zip`. Code typed at the interactive prompt counts too. Technically, the prompt is a module named `__main__` that prints results and does not match a real file. Otherwise it behaves like the top level of a module file.

Functions give you nested namespaces, so names inside a function do not clash with names in a module or in another function. Two kinds of scope matter here:

- Each module is a global scope. Variables assigned at the top level of a module live in its namespace. After an import, they become attributes of the module object, but inside the file you use them as plain variables.
- Each function call creates a new local scope. The names created inside the function live there, unless a `global` or `nonlocal` statement says otherwise.

The global scope spans a single file only. A name at the top level of one file is global only to code in that file. Python has no all-encompassing global scope for your own code. Names are split across modules, and you must import a module before you can use the names its file defines. When you hear "global" in Python, think "module."

Names assigned inside a function are local unless you declare them `global` or `nonlocal`. To change a name at the top level of the enclosing module, use a `global` statement inside the function. To change a name in an enclosing `def`, use a `nonlocal` statement. Because a `lambda` body holds only one expression, these two statements belong to `def` alone.

Names that a function does not assign are looked up elsewhere. Python treats them as locals of a physically enclosing function, as globals of the enclosing module, or as built-ins. An enclosing scope can come from any `def` or `lambda` combination. You cannot write a `def` inside a `lambda`, though.

Each call creates a new local scope. A `def` statement or a `lambda` expression defines a local scope, but the scope is really tied to each call of the function. That detail matters for recursion and closures.

Per-call scopes matter for recursion. Recursion is a technique where a function calls itself to loop, and each active call needs its own copy of the function's local variables. Recursion is useful when you process a structure whose shape you cannot predict ahead of time. Closures need per-call scopes too, because each call gets a fresh set of locals that can remember state for later.

Three subtleties are worth knowing. First, code at the interactive prompt lives in a module and follows the normal scope rules. Names assigned there are global and visible across the whole session. Second, any kind of assignment decides whether a name is local or global, based on where the assignment appears. That includes `=` statements, `:=` expressions, `import` names, `def` names, function arguments, and names in a `class`. Third, changing an object in place does not make a name local. Only a real assignment does.

Here is the third point in action. Suppose `L` is a list at the top level of a module. A statement `L = X` inside a function makes `L` local to that function. But `L.append(X)` changes the list that `L` refers to, not the name `L` itself. So Python finds `L` in the global scope and changes it without a `global` declaration. Keep the difference clear: changing an object is not the same as assigning a name.

## Name resolution: the LEGB rule

### The three rules inside a def

If the previous section sounds complicated, it comes down to three simple rules. Inside a `def`:

- Assigning a name creates or changes a local name by default.
- Referencing a name searches at most four scopes: local, then enclosing functions, then global, then built-in.
- Names declared in `global` and `nonlocal` statements map assignments to the module scope and the enclosing function scope, respectively.

The same rules apply to `lambda`, except for the last one, because a `lambda` cannot contain statements.

Functions can use names assigned in enclosing functions and in the global scope. To change those names, however, they must declare them as `nonlocal` or `global`.

Python calls this lookup order the LEGB rule, after the four scopes it searches:

- L is the local scope of the function itself.
- E is the local scopes of any enclosing `def`s and `lambda`s.
- G is the global scope of the surrounding module.
- B is the built-in scope.

When you use an unqualified name inside a function, Python checks these scopes in order and stops at the first match. If the name is not found anywhere, Python reports an error. When you assign a name inside a function, Python creates or changes it in the local scope, unless the name is declared `global` or `nonlocal`. When you assign a name at the top level of a module or at the interactive prompt, the local and global scopes are the same module namespace.

Because names must be assigned before they are used, there are no hidden steps in this model. Assignments always determine scopes. The E layer can hold more than one level, and it comes into play only when you nest functions. The `nonlocal` statement is what lets you change names in that layer.

> Note: this lookup rule was called the "LGB rule" in the first edition of the book. The E layer was added later, so that you did not have to pass enclosing names in with default arguments. Because `nonlocal` now handles that layer, the rule might have been named "LNGB," but backward compatibility matters. The acronym also ignores the newer comprehension and exception scopes, though acronyms longer than four letters tend to defeat their purpose.

These rules apply only to simple names, such as `name`. Qualified attribute names, such as `object.name`, follow a different lookup. Those names search objects, not scopes, and they can involve inheritance in object-oriented code.

### Other short-lived scopes

There are three more scopes in Python, and they matter less at this stage. They cover loop variables in comprehensions, exception variables in `try` handlers, and the bodies of `class` statements. Most statement blocks do not localize the names they use. A loop variable in a `for` statement, for example, stays visible after the loop ends. The `:=` operator also follows the normal scope rules.

Comprehension loop variables are the first special case. In `[X for X in I]`, the variable `X` refers to the current item. It is local to the expression itself in every comprehension form: list, dictionary, set, and generator. A `for` statement does not do this for its loop variable, even though the syntax looks similar. Names assigned with `:=` inside a comprehension do leak out to the enclosing scope.

Exception variables are the second case. In `except E as X`, the variable `X` refers to the raised exception. It is local to that `except` block, and Python removes it from the containing scope when the block exits. Even if you used the name earlier in your code, it is removed. This design avoids keeping the exception alive, which could delay memory recovery.

Named assignments in a `lambda` are the third case. In `X := Y` inside a `lambda`, the name `X` works much like an unnested `=` statement. A `lambda` creates a new local scope, just like a `def`. Any name assigned with `:=` inside it can be used only within the `lambda` body and is not available outside it. This pattern is rare and adds complexity, so most code will not need it.

Most of these contexts augment the LEGB rule instead of replacing it. A comprehension's loop variable is bound to one more nested, special-case local scope. Every other name in the expression follows the usual LEGB lookup.

A `class` statement also creates a local scope for the names assigned at the top level of its block. Those names do not clash with names elsewhere, and the `class` block acts as the L level of the lookup. After the `class` statement ends, these names become attributes of the class object. Unlike a function, a class does not create new names on each call. Calling a class creates instances, which inherit the names assigned in the class and keep per-object state as their own attributes.

Python uses LEGB to resolve names in a class body and in the methods nested inside it. However, class scopes are skipped when a method looks up a name. Python searches enclosing functions, but not enclosing classes. Names in a class must be fetched as object attributes, so the LEGB picture still applies to object-oriented code.

## Scope examples

### A module with one function

Suppose you save this code in a module file named `scopes101.py`:

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

The module and its function use several names. Python's scope rules classify them as follows.

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

This keeps each function a self-contained unit of software, which is the goal.

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

Inside the function, the local `open` hides the built-in `open`. The name now refers to a string, not the file opener. This is sometimes called shadowing a built-in. It is harmless if you never open a file in that function. It causes an error if you try.

The same thing can happen at the interactive prompt, which acts as a global scope:

```
>>> open = 99 # Assign in global scope, hides built-in here too
```

There is nothing wrong with using a built-in name for your own variable, as long as you do not need the original. If these names were off limits, you would have to memorize the whole list and treat every name as reserved. In Python 3.12, the `builtins` module has 158 names, and 150 of them do not start with double underscores:

```
>>> len(dir(builtins)), len([x for x in dir(builtins) if not x.startswith('__')])
(158, 150)
```

Sometimes you really do want to replace a built-in name, such as writing a custom `open` that adds access checks. The `None`, `True`, and `False` names are the exception. They are treated as reserved words now, so you can no longer reassign them. All other built-in names are fair game.

Still, redefining a built-in name is often a bug, and a difficult one to find. Python does not warn you when you do it. Some tools can flag such mistakes, but your best defense is knowledge. Do not redefine a built-in name you need. If you do it by accident at the interactive prompt, restart the session, or run a `del name` statement to remove the redefinition. Then the original built-in is restored, as the LEGB rule expects.

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

Functions and global variables raise bigger design questions. How should functions communicate with each other? You will see more answers as you write larger programs, but a few guidelines now can save you trouble later. In general, functions should rely on arguments and return values instead of globals. Newcomers often do not expect this.

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

### Nested scope lookups

So far, this chapter has left out one part of Python's scope rules on purpose. It is uncommon in practice. Now it is time to look at layer E of the LEGB rule. Python 2.x added this layer. It consists of the local scopes of every enclosing function. Enclosing scopes are sometimes called statically nested scopes. The nesting is lexical, which means it follows the physical nesting of code in the source text.

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

This is legal Python. A `def` is an executable statement, so it can appear anywhere another statement can, including inside another `def`. While `f1` runs, the nested `def` creates a function and assigns it to the name `f2` inside `f1`. The `f2` function is temporary. It lives only while `f1` runs, and only code inside `f1` can see it. That is one reason to nest it, since the name cannot clash with anything else in the program.

When `f2` uses `X`, it refers to the `X` in the enclosing `f1` scope. Functions can access names in every physically enclosing function. So the LEGB rule maps `X` in `f2` to `X` in `f1`, through the E level.

This enclosing lookup still works after the enclosing call has finished. The next example defines a function that makes and returns another function:

```python
def f1():
    X = 88
    def f2():
        print(X + 1) # Remembers X in enclosing def scope
    return f2 # Return f2 but don't call it
action = f1() # Make, return function
action() # Call it now: prints 89
```

The call to `action` runs the function we named `f2` when `f1` ran. This works because functions are objects, like everything else in Python. They can be passed back as return values. `f2` remembers the `X` from `f1` even though `f1` is no longer active when `f2` runs. This memory is one of the main reasons to nest functions, and the next section looks at it closely.

### Closures and factory functions

The behavior in the last example has two names. Some people call it a closure, which is a functional programming technique. Others call it a factory function, which is a design pattern. A factory function creates and returns a function that carries a closure of state. The two terms overlap a lot.

Either way, the function object remembers values from enclosing scopes, even when those scopes are no longer active. It carries packets of memory with it, and each new nested function gets its own packet. Closures often serve as a simple alternative to classes for this job.

Closures are useful when a program must create event handlers at runtime. Imagine a GUI that must define actions based on user input. That input cannot be predicted when the GUI is built, and each action differs. You need a function that creates and returns another function. Each function it makes carries its own state.

Here is a simple demonstration. Type this at the interactive prompt:

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

All of this is real Python behavior. Each nested function has a closure storage area for the enclosing names it uses. You can see it as the `__closure__` attribute of the function. You do not need those internals to use closures, though.

Closures are an advanced technique. You may see them more often in code written by people with functional programming backgrounds. Enclosing scopes also appear in `lambda` expressions from the previous chapter. A `lambda` is an expression, so it is almost always nested inside a `def`. A `lambda` can stand in for a `def` here, and it also keeps state through enclosing references, such as `N` below:

```
>>> def maker(N):
...     return lambda X: X * N # lambda functions retain state too
>>> h, i = maker(2), maker(3) # Make two closure functions
>>> h('Py'), i('Py') # Run lambdas: ('Py' * 2) and ('Py' * 3)
('PyPy', 'PyPyPy')
```

### Customizing open with a closure

Here is a practical example of a closure at work. Imagine you want to replace the built-in `open` with a custom version, as the built-in scope section suggested. If the custom version needs to call the original, it must save the original before replacing it. It must also keep that original for later. That is a classic state-retention job.

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

Closures can also nest in ways that globals cannot support. Each call to `makeopen` remembers its own `id` and `original`, so you can stack several customizations:

```
>>> makeopen('MOD2') # Nested customizers work too
>>> F = open(file) # Because each retains its own state
Custom open call MOD2 ('../Chapter14/data.txt',) {}
Custom open call MOD1 ('../Chapter14/data.txt',) {}
>>> F.read()
'Testing file IO\nLearning Python, 6E\nPython 3.12\n'
```

As written, this code adds call tracing to a built-in function. The general technique has other uses as well. A class-based version would work too, but it would need more code, because it must store `id` and `original` in object attributes. Classes come later in the book.

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

Changing a name in an enclosing scope is not allowed by default, though:

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

Python's nonlocals are more capable than the "static" function locals in some other languages. In a closure, a nonlocal holds data that is per call, and you can make many copies of it.

### nonlocal boundary cases

`nonlocal` has a few subtleties. First, unlike `global`, a `nonlocal` name must already be assigned in an enclosing `def`. You cannot create it by assigning it in a nested function. The enclosing function's assignment can come before or after the nested function. If the assignment is missing, you get an error. Python checks for it when the nested function is defined, before either function is called:

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

Nested functions add complexity, so you may wonder why they are worth it. State matters in many programs, even though it is hard to see in small examples. A function can return results, but its local variables will not keep values between calls. Many applications also need those values to differ for each context of use.

Python offers several ways to retain state between calls. You have already met two of them: globals and enclosing scope references. The others are class-instance attributes and function attributes. This section compares them.

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

With `nonlocal` and nested closures, each call to `outer` keeps its own copy of `state`. Globals do not fit when each call needs its own data.

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

Decorators are a realistic case that needs multilevel state, and the same options apply to them. Performance is another factor in choosing, and this section leaves it aside. Timing code comes up later in the book. For now, it is time to look at one more technique. It both bends the LEGB rule and leads to the next chapter.

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

Why learn an outdated scope-reference scheme at all? Because one common case still needs it. Suppose a `lambda` or `def` sits inside a loop, and it references an enclosing variable that the loop changes. Then every function created in the loop ends up with the same value, the value the variable had in the last iteration. In that case you must use defaults to save the current value.

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

## Check your understanding

Work through these questions to review the scope ideas in this chapter.

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

Answers:

1. The output is `Hack`. The function references a global variable in the enclosing module. Because the function does not assign `X`, Python treats it as a global.
2. The output is `Hack` again. Assigning `X` inside the function makes it a local, which hides the global of the same name. The `print` statement finds the global, which is unchanged.
3. It prints `Py!` on one line and `Hack` on the next. The reference inside the function finds the assigned local. The `print` in the last line finds the global.
4. This time it prints only `Py!`. The `global` declaration makes the assignment inside the function refer to the module-level `X`, so the global itself changes.
5. The output is `Py!` on one line and `Hack` on the next. The `print` inside the nested function finds the name in the enclosing function's local scope. The final `print` finds the global variable.
6. This example prints `Hack`. The `nonlocal` statement makes the assignment to `X` inside the nested function change `X` in the enclosing function's scope. Without it, the assignment would make `X` local to the nested function, a different variable. The code would then print `Py!`.
7. Even though local variables disappear when a function returns, you can keep state with shared global variables, with `nonlocal` references in nested functions, or with default argument values. Function attributes attach state to the function itself, instead of looking it up in a scope. Classes and OOP often retain state better than scope-based techniques, because the attribute assignments are explicit. Changing mutable objects in scopes and defaults also works, but some local coding standards may not allow it.

## Sources and review notes

- Source: *Learning Python*, 6th edition (`learning-python-6th-edition`). Chapters used are listed in each section.
- Chapter used: "17. Scopes" from *Learning Python*, 6th edition (`learning-python-6th-edition`).
