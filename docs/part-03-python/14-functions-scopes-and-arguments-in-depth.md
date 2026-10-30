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

## Argument passing basics

The earlier sections showed where names live. This part asks how values get into a function. When you call a function, each value you pass fills one name in the function header. Those names are the function's arguments, also called parameters. Python fills them in a simple way, and the result has some effects that surprise newcomers.

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

Table 18-1 is a quick lookup. It shows each form, where it appears, and what it means:

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

Here `a` matches `1`, `b` matches `2`, and `c` matches `3`. This works the way it does in most languages.

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

The last line fails because a single star cannot follow a double star in a call. The rules below explain why.

The call-side star accepts any iterable, not only tuples and lists. Iterables such as `range` and `zip` unpack into individual arguments. A file object reads its lines and passes them on:

```
func(*range(4)) # Same as func(0, 1, 2, 3)
func(*open('filename')) # Read+pass lines as arguments
```

Stars are a little inconsistent, though. The generality holds only in calls. In a definition, a star always collects extra arguments into a tuple. The extended unpacking in assignments, such as `x, *y = z`, uses the same syntax. That form always creates a list, not a tuple. The rules differ between tools even when the syntax looks the same.

### Why arbitrary arguments?

These patterns may look academic at first. They are used more often than you might expect. Some programs must call functions generically, without hardcoding their names or argument lists. The real power of starred calls is that you do not need to know the argument count before you write the script.

For example, you might choose a function and its arguments with `if` logic. Then you call whichever one you chose:

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

The argument list is a tuple here, so the program can build it at runtime. This pattern is also common in functions that test or time other functions. The next example passes along whatever arguments it receives:

```
def tracer(func, *pargs, **kargs): # Accept arbitrary arguments
    print('calling:', func.__name__)
    return func(*pargs, **kargs) # Pass along arbitrary arguments
def func(a, b, c, d):
    return a + b + c + d
print(tracer(func, 1, 2, c=3, d=4))
```

The code uses the `__name__` attribute that every function has. It holds the function's name as a string. The stars collect the arguments meant for the traced function, then pass them along with call-side unpacking. When you run it, the tracer intercepts the arguments and forwards them:

```
$ python3 tracer0.py
calling: func
10
```

The customizing `open` example earlier in this chapter used the same idea. Later chapters on generators and decorators use this technique too. It is a common pattern in general-purpose tools.

## Keyword-only arguments

Function definitions can also require that some arguments be passed by keyword only. A positional value never fills them. This feature is called keyword-only arguments. It is useful when a function takes any number of positional values and also accepts optional configuration options.

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

Unlike the arguments before the star, keyword-only arguments can mix defaults and non-defaults in any order. This is an exception to the normal rule, and the reason is covered in the ordering section below:

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

Imagine a function that processes objects and takes a tracing flag:

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

Passing either of the first two arguments by keyword raises an error:

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

So far, we have been loose about the rules for argument matching. Those rules rarely matter in simple code. In more advanced code, you need to know them exactly. Definitions and calls share similar syntax, but their rules differ because their roles differ.

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

Here `function` is any expression that evaluates to a callable object. This example mixes positional, keyword, and unpacking arguments. It is a demonstration, not a style to copy:

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

If these rules make your head spin, that is a sign to simplify. Python's argument-matching rules grew over time, and they now have many special cases. The first rule of programming applies here too. Keep it simple unless the problem demands complexity. If you must work hard to understand a call's argument order, consider rewriting it.

## Example: the min wakeup call

Now a more realistic exercise. Suppose you must write a function that returns the minimum of any set of arguments. The arguments can be any kind of object: numbers, strings, lists, lists of lists, files, or even `None`. The function should accept zero or more arguments. You do not need to support dictionaries or mixed nonnumeric types. Those types do not support direct comparisons.

The `*` collector handles the first requirement. Collect the arguments in a tuple and step through it with a `for` loop. Most object types support comparison, so you do not need a separate version for each type. Python picks the right comparison for the objects it receives.

The following file, `mins.py`, shows four ways to write this operation. Some came from students in a class exercise:

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

The first version takes the first argument from `args` and scans the rest by slicing off the first item. There is no reason to compare the first object with itself, especially when it is a large structure. The second version lets Python split off the first argument and the rest. This avoids an index and a slice. The code is simpler, and it may be faster, though you would need many calls to notice. The third version converts the tuple to a list and calls the list `sort` method. The first item is the lowest after an ascending sort. The fourth version also sorts, but it uses the `sorted` built-in. It skips the list conversion and saves two lines.

The testing code uses the `__name__` attribute and a `for` loop to call each function in turn. Functions are objects, so they can sit in a tuple. All four versions give the same results. The output below shows only the first one:

```
$ python3 mins.py
min1...
1
aa
[1, 1]
a
…and the same for others…
```

None of these versions checks for zero arguments. Python raises an exception automatically when no arguments are passed. The first version fails when it fetches item `0`. The second fails when it detects a mismatch in the argument list. The third and fourth fail when they try to return item `0` after sorting. That is the behavior you want. Since the functions accept any object, including `None`, no value could signal an error. Letting Python raise the exception is the cleanest option. Assume that the arguments will work, and let Python report the problems.

Sorting has a performance note too. CPython's sort is written in C, and it can take advantage of partial order in the items. The other versions do one linear scan, from left to right. Sorting may therefore be faster when the arguments are partly ordered, and slower otherwise. Python changes over time, so time the alternatives yourself with the `time` or `timeit` modules. In CPython, the non-sort versions are faster for random arguments, but slower for ordered ones.

### Bonus points

You can turn these functions into maximum finders. The first two versions need only `<` changed to `>`. The last two need item `[-1]` instead of `[0]`. Rename the functions to `max` too, if you want the extra credit.

You can also write one function that handles both minimum and maximum. You could use `eval` with a comparison string. You could also pass in a comparison function. This example uses the second approach:

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

This was only a coding exercise. Python already has `min` and `max` as built-ins. The built-ins work almost the same way as these functions. They are written in C for speed, and they accept either one iterable or several arguments. The general pattern here can still be useful in other places.

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

The last example uses `*` and `**` collectors, plus keyword-only arguments, to imitate most of Python's `print` function. Python already has `print`, so there is no urgent need for this code. Still, it teaches argument matching clearly. It can also be a base for custom versions of built-in tools.

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

The emulator has a flaw. It treats every keyword as an option, and it ignores unknown ones. A call with a typo in an option name fails silently:

```
$ python3
>>> from print3 import print3
>>> print3(3.12, 'py', sap='@')
3.12 py
```

You can catch unknown keywords by hand. Use `dict.pop()` to remove the keywords you expect. If anything is left when you finish, raise an error. The version below does this. It is equivalent to the first one, but it raises a `TypeError` for unexpected keywords. Exceptions and `raise` get a full treatment later in the book:

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

Writing one function is easy. Writing many that work well together takes more thought. Two ideas guide that work. Cohesion describes how well the steps inside one function belong together. Coupling describes how much a function depends on other code, or on the world outside it. Good designs keep cohesion high and coupling low. These ideas come from structured design, and they apply to Python as they do to any language.

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

Each call makes a new call for the rest of the list. When the list is empty, the function returns zero, and the recursion stops. The sums then add up as the calls return. Each open call has its own local scope on the call stack, so `L` holds a different slice at each level.

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

Recursion works for summing, but it is probably more than this job needs. Python favors simple statements such as loops. A `while` loop makes the work concrete, and it needs no function definition:

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

Recursion is often less efficient, in both memory and execution time. A loop does not need a fresh local scope on the call stack for each pass. It also avoids the cost of calling a function at every step. You can time the alternatives yourself to compare them.

### Handling arbitrary structures

Loops are not always enough. Consider a list that holds numbers and nested sublists:

```
[1, [2, [3, 4], 5], 6, [7, 8]]
```

A single loop cannot handle this, because it is not a flat sequence. Nested loops fail too. Sublists can nest to any depth and in any pattern, so you cannot know how many loops to write. Recursion solves this. The function below steps into each sublist it finds:

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

Inside `tester`, the name `sumtree` refers to whichever function you pass in. Functions are objects, so you can pass them around this way. That keeps the code flexible.

### Recursion versus queues and stacks

Python implements recursion by pushing information onto a call stack at each recursive call. The stack remembers where each call must return and continue. You can also avoid recursive calls. An explicit stack or queue of your own can track the remaining steps. The item at the front of the list is always the next one to process.

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

These demos work, but larger recursive programs need more support. They may need to avoid cycles or repeats, record the paths they take, and manage stack space when they recurse deeply.

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

Functions are full objects, not just code for the compiler. They can be passed around, stored, and called indirectly. They also support operations that have little to do with calling them, such as attributes and annotations.

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

Python's first-class object model and its lack of type constraints make the language very flexible.

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

Tool writers use this information to manage functions. Decorators can use it to check arguments, which the book shows in a later chapter. Whether you write such tools or only use them, object introspection makes functions more useful.

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

Decorators can also take arguments, such as `@echo(args)`. Their use can overlap with annotations, because argument information can go to the decorator instead of the header. Decorators can also apply to classes, which the book covers later.

Compared with annotations, decorators do not add syntax to function headers. They also support more than one role. Annotations often serve a single role, and optional type hinting already claims that role in programs that use it. Some type-hinting advocates have tried to remove other uses of annotations. Decorators face no such pressure, so they may be the safer bet. Both tools are limited mainly by your imagination.

Annotations and decorators work on `def` statements, but not on `lambda` expressions. The `lambda` form is limited by design, and the next section covers it.

## Anonymous functions with lambda

You met the `lambda` expression earlier. This section reviews the basics and goes deeper. Like `def`, a `lambda` creates a function to call later. Instead of assigning the function to a name, it returns the function object. That is why people call `lambda` an anonymous function. In practice, it inlines a small function definition or defers some code until later.

> Note: the name "lambda" intimidates people. It comes from the Lisp language, which took it from lambda calculus, a form of symbolic logic. In Python, `lambda` is just a keyword that starts an expression. That expression is an alternative way to write a function, but it has no statements, decorators, or annotations.

### lambda basics

The general form has the keyword `lambda`, zero or more arguments, and an expression after a colon:

```
lambda argument1, argument2,… argumentN : expression-using-arguments
```

The arguments follow the same rules as the arguments in a `def` header, without annotations. Parentheses are not allowed around the arguments. They are usually optional around the whole `lambda`, though some contexts need them. Functions made with `lambda` work the same as those made with `def`. The difference is in how they are written, and that makes `lambda` useful in special cases:

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

Here you assign the function object yourself. A `def` does this assignment automatically. Defaults and other argument-matching forms also work in a `lambda`:

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

A `lambda` is a shorthand that lets you embed a function definition where it is used. It is entirely optional. You can always write a `def` instead, and you should when the function needs the power of full statements. A `lambda` fits when you only need a small piece of code inline, where it will be used.

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

A `lambda` body must be one expression. That seems to limit how much logic you can pack into one. If you know what you are doing, you can express most statements as expressions.

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

As covered in the scope section, `lambda` depends on enclosing-function lookup, the E layer of LEGB. A `lambda` inside a `def` can read the value that a name had in the enclosing function's call:

```
>>> def action(x):
...     return (lambda y: x + y)  # Make function, remember x
>>> act = action(99)
>>> act(2)  # Call what action returned
101
```

A `lambda` can also see names in an enclosing `lambda`. To see it, rewrite the example with `lambda` alone:

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

Nested function scope rules apply to `lambda` too. A `lambda` sees names in the functions it is coded in, so it rarely needs passed-in defaults. Loop variables are the exception. This also helps with the `self` argument in class methods. Here is a preview of that case, which the book covers in its object-oriented part:

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

Together, `map`, `filter`, and `reduce` support powerful functional techniques. Many people also count nested closures, `lambda` expressions, generators, and comprehensions as part of that toolset.

## Chapter wrap-up

This part of the chapter covered function design guidelines, recursive functions, function attributes, annotations, and decorators. It also covered `lambda` expressions and the `map`, `filter`, and `reduce` built-ins. Some of these tools are advanced, but many are common in Python programs. Comprehensions and generators build on these functional tools next.

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

Answers:

1. The output is `Hack`. The function references a global variable in the enclosing module. Because the function does not assign `X`, Python treats it as a global.
2. The output is `Hack` again. Assigning `X` inside the function makes it a local, which hides the global of the same name. The `print` statement finds the global, which is unchanged.
3. It prints `Py!` on one line and `Hack` on the next. The reference inside the function finds the assigned local. The `print` in the last line finds the global.
4. This time it prints only `Py!`. The `global` declaration makes the assignment inside the function refer to the module-level `X`, so the global itself changes.
5. The output is `Py!` on one line and `Hack` on the next. The `print` inside the nested function finds the name in the enclosing function's local scope. The final `print` finds the global variable.
6. This example prints `Hack`. The `nonlocal` statement makes the assignment to `X` inside the nested function change `X` in the enclosing function's scope. Without it, the assignment would make `X` local to the nested function, a different variable. The code would then print `Py!`.
7. Even though local variables disappear when a function returns, you can keep state with shared global variables, with `nonlocal` references in nested functions, or with default argument values. Function attributes attach state to the function itself, instead of looking it up in a scope. Classes and OOP often retain state better than scope-based techniques, because the attribute assignments are explicit. Changing mutable objects in scopes and defaults also works, but some local coding standards may not allow it.

8. The output is `1 2 5`, because `1` and `2` match `a` and `b` by position, and `c` is left out, so it defaults to `5`.
9. The output is `1 2 3`, because `1` matches `a` by position, and `b` and `c` match `2` and `3` by name. Order does not matter with keywords.
10. The output is `1 (2, 3)`, because `1` matches `a`, and `*pargs` collects the remaining positional arguments into a tuple.
11. The output is `1 {'c': 3, 'b': 2}`, because `1` matches `a` by name, and `**kargs` collects the remaining keywords into a dictionary. Its keys keep the order in which they were passed.
12. The output is `1 5 6 4`, because `1` matches `a`, `5` and `6` unpack into `b` and `c`, and `d` keeps its default of `4`.
13. The output is `(1, ['x'], {'a': 'y'})`. The first assignment inside the function does not reach the caller. The next two change passed-in mutable objects in place, so the caller sees them.
14. Both create function objects to call later. A `lambda` is an expression, so it returns a function object instead of assigning a name, and it fits where a `def` cannot. Its body is a single expression, so it suits small functions, not large ones.
15. A `lambda` lets you inline a small piece of code, defer it, and give it state through defaults and enclosing variables. You never need one, because a `def` always works. It helps for small handlers used in one place, such as GUI callbacks, and it pairs well with `map` and `filter`.
16. All three apply a function to the items of an iterable. `map` collects each call's result. `filter` keeps the items for which the function returns a true value. `reduce` combines the items into a single value by applying the function to a running result and the next item. `reduce` lives in `functools`, not the built-in scope.
17. Annotations are syntax attached to a function's arguments and result. Python collects them in `__annotations__` and gives them no meaning. Other tools can read them, for example for type hints or error checking.
18. Recursive functions call themselves, directly or indirectly, to repeat work. They can traverse structures of arbitrary shape and depth. They can also iterate in general, though a loop is usually simpler and more efficient. Explicit stacks or queues can simulate or replace recursion.
19. Keep functions small and self-contained, with one unified purpose. Communicate through arguments and return values. Change mutable arguments only when the caller expects it. Some programs need other communication mechanisms, but these basics keep code easy to reuse.
20. Functions can send results back with `return` statements, by changing passed-in mutable arguments, and by setting global variables. Globals are generally discouraged because they make code harder to understand, except in special cases such as multithreaded programs. Functions can also communicate through files and sockets, which this chapter does not cover.

## Sources and review notes

- Source: *Learning Python*, 6th edition (`learning-python-6th-edition`). Chapters used are listed in each section.
- Chapter used: "17. Scopes" from *Learning Python*, 6th edition (`learning-python-6th-edition`).
- Chapter used: "18. Arguments" from *Learning Python*, 6th edition (`learning-python-6th-edition`).
- Chapter used: "19. Function Odds and Ends" from *Learning Python*, 6th edition (`learning-python-6th-edition`).
