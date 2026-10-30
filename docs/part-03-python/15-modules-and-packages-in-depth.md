---
id: "c03-15"
title: "3.15 Modules and packages in depth"
sidebar_label: "3.15 Modules and packages in depth"
sidebar_position: 15
description: "Module coding basics, module packages, advanced module topics and how Python finds and loads code, for building reusable infrastructure tooling."
status: "drafted"
tier: "2"
level: "I"
lab_venue: "Mac"
---

# 3.15 Modules and packages in depth

This chapter goes deeper into material that chapter 3.1 only introduces. You will meet it again whenever you read or write the Python behind schedulers, operators, exporters and training launchers.

## Module essentials

A module usually matches one Python source file. Every file of code is a module automatically. Modules import other modules to use the names those modules define. A module can also stand for an extension written in C, Java or C#, or for a whole directory in a package import. Three tools handle modules in all of these forms.

| Tool | What it does |
|---|---|
| `import` | Lets a client (importer) fetch a module as a whole |
| `from` | Allows clients to fetch particular names from a module |
| `importlib.reload` | Provides a way to reload a module's code without stopping Python |

You have already used imports to load standard-library modules and code files in your current directory. The statement looks simple. Underneath it sits a richer model, and this chapter walks through it.

### Why use modules

A module organizes code into self-contained packages of variables called namespaces. Every name defined at the top level of a module file becomes an attribute of the imported module object. Those names stay hidden until another file imports them, so they do not clash with names in other files.

This ties back to scopes, which you studied earlier in this course. Imports give access to names in a module's global scope. The file around a function is that function's own global scope. An import lets one file see another file's global names as attributes. Once imported, the module file's global scope becomes the module object's attribute namespace.

Modules help you link separate files into one larger program. They bring three main benefits.

**Code reuse.** Modules make code permanent. A module's code lives in a file, so you can run it many times and use it in many programs. Code you type at the REPL disappears when you exit Python. Code in a module file stays available.

**Minimizing redundancy.** When several files need the same code, write it once in a module and import it everywhere. In an earlier benchmarking example, test scripts imported shared timer and test-runner functions instead of repeating them. Like functions, modules keep you from copy-and-paste programming. Changing common code then takes less work.

**Namespace partitioning.** Modules are the highest-level namespace in a Python program. A name in another file is invisible unless you import that file explicitly. This works much like the local scope of a function, and it prevents name clashes across programs. You cannot avoid this feature, because everything you run and create lives in a module. Modules group components by their nature.

## Python program architecture

Most programs are more than one file. Even a small program often pulls in files that someone else wrote. Python encourages a modular structure, where code is grouped into coherent and reusable units. This section shows how the pieces link together.

### How to structure a program

A Python program is a set of text files that contain Python statements. It has one main top-level file and zero or more supporting module files. The top-level file, also called a script, holds the main flow of control. It is the file you run to start your application.

Module files are libraries of tools. The top-level file uses tools defined in module files, and modules can use tools defined in other modules. Module files usually do nothing when you run them directly. They define tools for other files to use. A file imports a module to reach its attributes, which are the variable names attached to objects such as functions.

### Imports and attributes

Picture a program of three files: `a.py`, `b.py` and `c.py`. The file `a.py` is the top-level script. It runs from top to bottom when launched. The files `b.py` and `c.py` are modules. They are plain text files of statements too, but you normally import them rather than run them.

Suppose `b.py` defines a function for other files to use:

```
def job(tool):
    print(tool, 'coder')
```

A `def` statement creates the function. You can run it later by passing values in parentheses after its name. This function is simple on purpose. It lets us focus on how modules work.

Now suppose `a.py` wants to use `job`. It can contain these statements:

```
import b
b.job('Python')
```

The `import` statement gives `a.py` access to everything defined by top-level code in `b.py`. Top-level code means code not nested inside a function or class. The line `import b` roughly means: load `b.py` unless it is already loaded, and give me its attributes through the name `b`.

Imports run at runtime. Cross-file links are not resolved until the `import` statement executes. Each import assigns a module name, such as `b`, to the loaded module object. The name serves two purposes. It identifies the file to load, and it becomes a variable that holds the module.

Importing also runs the target file's statements one at a time. Every name assigned at the top level of the file becomes an attribute of the module. The `def` in `b.py` runs during the import and creates `job`. The expression `b.job` means: fetch the value of the name `job` that lives inside the object `b`. Since `job` is a function, we can pass it a string in parentheses. Running `a.py` prints `Python coder`.

Any file can import tools from any other file. Import chains can go as deep as you need. Module `a` can import `b`, which can import `c`, which can import `b` again. In the benchmarking code from earlier, test scripts imported runner modules, and those imported timer modules.

Modules are the top level of code reuse in Python. If `b.job` proves useful, you can use it in a different program. Import `b` again from that program, and the code works without copying.

### Standard-library modules

Python ships with a large collection of utility modules called the standard library. The library holds hundreds of modules. It covers operating system interfaces, object persistence, text pattern matching, network scripting, GUI construction, multithreading and much more. These tools are not part of the Python language itself. You get them by importing the right modules on any standard Python installation.

Because they are standard-library modules, you can expect them to be present. They also work on most platforms. Earlier examples used `time`, `timeit`, `sys` and `os`. That is only a small part of the library. The standard-library reference manual is free online and covers the rest. The PyDoc tool also lists every importable module.

Browsing is the best way to learn what the library offers. As of Python 3.10, `sys.stdlib_module_names` gives a simple list of all standard-library modules, whether or not they can be imported:

```
$ python3
>>> len(sys.stdlib_module_names) # That's a lot of modules
300
```

## How imports work

The import operation is easy to use but easy to misunderstand. Some C programmers compare it to `#include`. That comparison is misleading. Python does not paste one file's text into another. An import is a runtime operation. The first time a program imports a file, it performs three steps:

1. Find the module's file.
2. Compile it to bytecode, if needed.
3. Run the module's code to build the objects it defines.

All three steps happen only the first time a module is imported during a program's run. Later imports skip them and reuse the module already in memory.

### Loaded modules are cached

Python stores loaded modules in a normal dictionary named `sys.modules`. At the start of each import, Python checks this dictionary for the module's name. The entry `sys.modules['name']` means the same thing as `name` after `import name`. The keys of `sys.modules` list every module loaded so far.

```
>>> import sys, os
>>> sys.modules['os'] is os # Name string => module
True
>>> sorted(sys.modules) # Or sys.modules.keys()
…names of all loaded modules…
```

If the module is not already in `sys.modules`, the three-step process begins.

### Step 1: find it

Python must first locate the file named by the `import` statement. Notice that `import b` does not include a `.py` extension or a directory path. The name is enough. Python uses the module search path and a list of known file types to find the right file. The search path gets its own section below, because it is the part of imports most programmers need to know.

### Step 2: compile it (maybe)

After Python finds a source file, it compiles that file to bytecode if necessary. Bytecode is a lower-level form of your code. The earlier chapter on how Python runs code introduced it, and this is a fuller picture.

The first time you import a module, Python compiles its `.py` source file to bytecode. It saves the bytecode in a file with a `.pyc` extension, if it can. On later runs, Python loads the saved bytecode and skips the compile step. This works only if three conditions hold. The bytecode file must use a compatible format. It must come from the Python that is importing it. And you must not have edited and saved the source since the bytecode file was made.

If you change a module's source, its bytecode file is re-created the next time a program imports it. This keeps the bytecode in sync with the source and with your Python.

Bytecode files come in two flavors. The first is the default. The second arrived in Python 3.7.

- **Timestamp-based** bytecode files are created simply by importing modules. This is the default, original and most common option. Use it when you want fast imports and have no unusual needs.
- **Hash-based** bytecode files are created with the `compileall` or `py_compile` library modules. The command-line switch `--check-hash-based-pycs` controls how they behave. Python's manual describes that flag's three options.

In either model, Python saves enough information to know when a bytecode file must be re-created. A bytecode file embeds a magic number that identifies its format. It also stores either the source file's last-modified timestamp and size, or a hash of the source content. The bytecode file name includes the implementation name and version of the Python that created it.

When a module is imported, Python first checks whether the program already loaded it. If not, it looks for a usable bytecode file. A `.pyc` file is usable only if it has the same base name as the source file, and if it passes three checks. It must use a compatible format, which the magic number confirms. It must be up to date with the source, which the saved timestamp and size or hash confirms. And it must have been created by the running Python, which the implementation and version tags in the filename confirm. If the file passes, Python loads it and skips compiling. If not, Python compiles the source and saves a new bytecode file.

Programs still run when bytecode cannot be saved. The compiled code is then created in memory and discarded on exit. The `-B` command-line switch turns off bytecode saves, though you rarely need it. When saved, bytecode files go in a subdirectory named `__pycache__`, next to their source files. This keeps your source folders clean. It also avoids contention and repeated recompiles when several Pythons are installed. Here is what happens when one module file is imported by three different Pythons. On Windows, use `dir` and `py` instead of `ls` and the Python commands.

```
$ ls
codefile.py
$ python3.12
>>> import codefile
$ python3.8
>>> import codefile
$ pypy3
>>>> import codefile
$ ls
__pycache__ codefile.py
$ ls __pycache__
codefile.cpython-312.pyc codefile.cpython-38.pyc codefile.pypy310.pyc
```

The `__pycache__` subdirectory appeared in Python 3.2. It is not available in earlier versions. This book focuses on Python 3, so you are unlikely to meet an older version.

Bytecode compilation happens during import. A top-level file therefore leaves no `.pyc` file, unless another file imports it. Only imported files leave bytecode behind to speed up future imports. Top-level files are often run directly and never imported. A file can serve both roles, though. The special `__name__` attribute and `__main__` control that behavior.

> **Note: running from bytecode only.** A program can also run when Python finds only bytecode files and no source files. This takes more than deleting the `.py` files. Since Python 3.2, the `.pyc` files must sit where the `.py` files would normally be. You can move and rename them out of `__pycache__`, or create them with the `legacy` option of the `compileall` module (`-b` in command-line mode). The following command makes `.pyc` files from every `.py` file in the current directory, without moves or renames:
>
> ```
> $ python3 -m compileall -b -l .
> ```
>
> Bytecode-only running needs a compatible Python. It does not fully hide your code. Some tools use it to ship programs in standalone form, when the Python version can be included or assured.

### Step 3: run it

After Python compiles or loads the bytecode, it runs the module's code. Statements run from top to bottom. Each name assigned along the way becomes an attribute of the module object. This is how the tools in a module come into being. A `def` statement runs at import time and creates a function. The function is then available to any file that imports the module.

Because this step runs real code, top-level work in a module shows up at import time. A top-level `print` displays its output when the file is imported. A `def` statement only creates an object for later use. A `class` statement does the same for classes.

Import operations involve real work. They search for files, may run a compiler, and execute code. For that reason, Python imports each module only once per process by default. Later imports reuse the loaded module, as the `sys.modules` check shows. If you need to load a file again, for example to apply dynamic customizations, you can call `importlib.reload`. The next chapter covers that tool.

Most programmers never notice these mechanics, except for faster startups from skipped compile steps. The search step is the one that often matters.

## The module search path

Most programmers must care about the first step, which finds the file to import. You need to know where Python looks. The module search path is the list of directories it searches. You can extend that list for folders of your own.

Built-in modules such as `sys` are coded in C and linked into Python. Frozen modules such as `os` are optimized for faster startup, starting in Python 3.11. Python checks these two groups first, before it scans the search path, so they take precedence. There are only a few of them, so you can mostly ignore them. `sys.builtin_module_names` lists the first group. Counting the names that do not start with an underscore gives 11:

```
>>> sum(1 for m in sys.builtin_module_names if m[0] != '_') # Count non _X
11
```

### Search-path components

Often you never need to configure the search path. If you want to import your own files across directory boundaries, you must customize it. Python builds the search path from five components. Some are set for you. Others you can change to tell Python where to look.

1. **Home directory (automatic).** When you run a program, this is the directory that holds the program's top-level script file. When you work in a REPL, it is the directory where you currently are. Code run with the `-c` and `-m` switches uses the current working directory as its home component.
2. **`PYTHONPATH` directories (configurable).** Python searches the directories in your `PYTHONPATH` environment variable from left to right, if you set it. `PYTHONPATH` is a list of directory names that hold Python source or bytecode files. It is not set for you by default.
3. **Standard-library directories (automatic).** Python searches the folders where the standard library is installed. These hold modules written in Python and modules written in C.
4. **The `site-packages` directory (automatic).** Python adds the `site-packages` subdirectory of its standard library. Most third-party extensions install here, often through `pip`. Clients can import these modules without any path settings.
5. **`.pth` path-file directories (configurable).** Directories listed in any `.pth` file are added to the path.

The first, third and fourth components are automatic. The second and fifth let you extend the path with your own source directories. Python combines all five into the built-in `sys.path` list. It searches that list from first to last.

The home directory is searched first. This means a program kept in one folder imports its own files with no setup. The same rule has a catch. A home-directory file overrides a module with the same name elsewhere on the path. Be careful not to hide a standard-library module this way. Later package tools can partly avoid this problem with nested folders.

The home directory only affects the search for imports. It does not change the working directory used for relative filenames. A script that creates a file without a path puts it in the folder returned by `os.getcwd`, not in the script's home folder. Module imports and file access are separate ideas.

`PYTHONPATH` matters only when a file imports from a different directory than its own. Once your programs grow, you may need it. When you are starting out, keep all your module files in your working directory. Your imports will then work with no setting.

Python also searches the standard-library folders automatically, so you rarely add them to `PYTHONPATH`. Third-party packages land in `site-packages`, which is always on the path.

A `.pth` file is a lesser-used alternative to `PYTHONPATH`. It is a plain text file whose name ends in `.pth`. It lists one directory per line. You place it in the `site-packages` folder of an installed Python. Python adds those directories near the end of the search path, after `site-packages`. It drops duplicates and entries that do not exist. Because a `.pth` file is a file rather than a shell setting, it can apply to every user of that Python. The standard `site` module documents where path files belong.

Python's import system can be extended in many ways beyond what this chapter covers. `PYTHONPATH` entries may name ZIP files that act like read-only folders. `PYTHONHOME` can set standard-library locations. A file with a `._pth` suffix can fully override the usual `sys.path` rules. Virtual environments made with the `venv` module keep package versions apart by giving each one its own search path. The relative import syntax in packages also limits the search. For unusual needs, consult Python's manuals.

### Configuring the search path

Both `PYTHONPATH` and path files let you tailor where imports look. How you set them depends on your platform. On macOS and Linux, separate directories with colons. On Windows, separate them with semicolons:

```
/Users/me/pycode/utilities:/Volumes/ssd/pycode/package1 # Unix paths list
C:\Users\me\pycode\utilities;d:\pycode\package1 # Windows paths list
```

On Unix systems, the `export` shell command sets an environment variable for the shell and everything it runs. You can put it in a startup file such as `~/.bash_profile` to make it permanent. The following session on macOS sets the path so you can import modules from two earlier code folders. The `…` marks trimmed text.

```
$ pwd
/Users/me/…/LP6E/Chapter22
$ export PYTHONPATH=/Users/me/…/LP6E/Chapter21:/Users/me/…/LP6E/Chapter20
$ python3
>>> import pybench, permute
>>> pybench
<module 'pybench' from '/Users/me/…/LP6E/Chapter21/pybench.py'>
>>> permute
<module 'permute' from '/Users/me/…/LP6E/Chapter20/permute.py'>
>>> permute.permute1([1, 2, 3, 4])
>>> pybench.runner([(100, 5, '[x ** 2 for x in range(2 ** 16)]')])
```

Path syntax such as `..` for a parent folder also works in `PYTHONPATH`. Python reads it relative to the current working directory. That directory is not always the home directory of a program, if its top-level script lives elsewhere.

Windows consoles use similar commands. Use `set` in place of `export`, or `setx` to make the setting permanent. Most Windows users set environment variables in the Settings app, using the environment-variables dialog.

Instead of `PYTHONPATH`, or in addition to it, you can create a text file in your Python's `site-packages` folder with a `.pth` extension. Here is an example on macOS:

```
/Users/me/pycode/utilities # Unix .pth paths file
/Volumes/ssd/pycode/package1 # One path per line
```

These settings work the same way on every platform, though the details differ too much to cover fully here. When you start out, `PYTHONPATH` is often the better choice, and only when you must import across directories. Path files are used more often by third-party libraries installed in `site-packages`.

To see how your Python configures the path, print `sys.path`. The next section shows how.

### The `sys.path` list

To see the real search path on your machine, print the built-in `sys.path` list. It holds the directory names that Python searches on each import. Python checks each directory from left to right. It uses the first matching file it finds.

Python builds `sys.path` at startup by merging the components above. Inspecting it is useful for two reasons. First, it confirms that your settings took effect. If your settings do not appear after you restart Python, recheck your work. Suppose on macOS you set `PYTHONPATH` to `/Users/me/pycode1:/Users/me/pycode2`. Suppose a `mypath.pth` file in `site-packages` lists `/Users/me/pycode3`. The REPL output looks like this:

```
>>> import sys
>>> sys.path
['', '/Users/me/pycode1', '/Users/me/pycode2',
'/Library/Frameworks/Python.framework/Versions/3.12/lib/python312.zip',
'/Library/Frameworks/Python.framework/Versions/3.12/lib/python3.12',
'/Library/Frameworks/Python.framework/Versions/3.12/lib/python3.12/lib-dynload',
'/Library/Frameworks/Python.framework/Versions/3.12/lib/python3.12/site-packages',
'/Users/me/pycode3']
```

The empty string at the front stands for the current directory. Your two custom settings come next, in the order given earlier. The remaining entries are standard-library folders and the `site-packages` home for third-party extensions.

### Changing the search path

Scripts can also change `sys.path` at runtime. Changes to the program-wide list affect every future import made during the run. The change lasts only for that run. `PYTHONPATH` and `.pth` files are the lasting options. `PYTHONPATH` applies per user, and a `.pth` file applies per installed Python.

Some programs really do need to change `sys.path`. A script running on a web server often runs as a limited user such as `nobody`, to restrict machine access. That user cannot rely on `PYTHONPATH` being set in any particular way. Such a script can add the source directories it needs before it runs its imports. An `append`, an `insert` or another list operation does the job for one run:

```
>>> sys.path.append('/Users/me/pycode4') # Extend search path for this run
>>> import module # All imports search the new dir last
```

You can change `sys.path` in code to influence future imports, and this also works in a REPL. Be careful, though. Removing a folder can cut off access to important tools. Your changes disappear when the program or REPL ends. To make path changes last across scripts and sessions, use the lasting techniques above.

## Module file selection

Folders are not the only thing that matters during an import. File types matter too. Import statements leave off extensions such as `.py`. Python picks the first file on the search path that matches the imported name. That file need not be a `.py` source file. It might be a `.pyc` bytecode file or something else.

### Module sources

Imports are the interface to many kinds of external components. These include source code, bytecode, compiled extensions, ZIP files, Java classes and more. Python picks up any type that matches the module's name. A statement such as `import b` might resolve to any of these:

- A source code file named `b.py`.
- A bytecode file in `__pycache__`, named `b.cpython-312.pyc` or something similar.
- A bytecode file named `b.pyc`, if no `b.py` source file was found.
- A directory named `b`, for package imports.
- A compiled built-in module, written in C and linked into Python when it is built.
- A compiled extension module, such as `b.so` or `b.pyd`, written in C and linked in on import.
- A source or bytecode file stored in a ZIP file, extracted automatically on import.
- An in-memory image of a module, for frozen standalone executables.
- A Java class, in the Jython version of Python.
- A .NET component, in the IronPython version of Python.

Most items on this list go beyond simple files. To the importer, the type of the loaded file does not matter. Both `import b` and `b.attr` work the same way. `b.attr` might fetch a Python variable or a C function that is linked in. Some standard-library modules are written in C rather than Python. They look like Python modules to their clients, so clients do not need to care.

### Selection priorities

With so many options, conflicts are possible. Python always loads the matching item found in the first, leftmost directory on the search path. But what happens when one directory holds several matching items? Python then follows a standard picking order. That order is not guaranteed to stay the same over time or across implementations.

Do not depend on which file type Python picks within one directory. Make your module names distinct. Or configure the search path so your preferences are explicit.

### Path outliers: standalones and packages

Some tools bend these rules. Standalone executables usually embed bytecode in the runnable file. They run without path settings, so module search paths do not apply to them. That is a delivery option outside this chapter's scope.

Package imports also differ. An import statement cannot include path or extension details. Package imports can name a file with part of its directory path, as a set of period-separated names. Even so, package imports still use the normal search path to find the leftmost directory. They also cannot use platform-specific path syntax in import statements. Packages can use `.` syntax to narrow the import search. Package imports are covered separately.

## Chapter summary

This chapter covered the basics of modules and the operation of `import` statements. An import finds the designated file on the module search path. It compiles the file to bytecode and runs all its statements to build the module's contents. You can configure the search path to import from directories other than the home and standard-library directories. The main tool is the `PYTHONPATH` setting.

Modules and imports sit at the heart of Python's program architecture. Larger programs split into multiple files. Imports link those files at runtime. Imports use the module search path to find files, and modules define attributes for outside use. Together, these divide a program's logic into reusable, self-contained software components.

## Module files and names

A module is any text file of Python code saved with a `.py` extension. You write the code in a plain text editor. Python needs no special syntax to treat the file as a module. Every name assigned at the top level becomes an attribute that other files can use.

For example, a file named `module1.py` can hold one function called `printer`. Importing that file gives you a module object with one attribute, `printer`. That attribute refers to the function.

Module filenames should end in `.py` if you plan to import them. The suffix is optional only for a top-level script that you run and never import. Adding it everywhere makes file types obvious. Some editors and file explorers also turn on Python features for `.py` files.

A module name also becomes a variable name inside your program. It must follow the same rules as any variable name. A file called `if.py` can exist, but `import if` gives a syntax error, because `if` is a reserved word. Module filenames and package directory names may contain only letters, digits and underscores. Package directory names also cannot contain spaces.

When Python imports a module called `M`, it searches the module search path. It adds a directory to the front of the name and an extension to the end. So `M` maps to a file such as `directory/M.extension`, which holds the module's code.

### Extension modules

Modules can also be written in other languages, such as C or C++. In the Jython version of Python, they can be written in Java. These are called extension modules. They are often used to wrap external libraries or to speed up part of a program. Clients import them with the same `import` statement, and they provide functions as attributes. Their details are beyond this chapter, so check Python's standard manuals for more.

## Import and from statements

Clients use a module by running an `import` or a `from` statement. Both statements find and compile the module file if it is not loaded yet. Both then run its code. The main difference is how much they copy. An `import` fetches the module as a whole, so you must qualify each name with the module name. A `from` copies specific names out of the module, so you can use them directly.

### The import statement

This example uses a module named `module1`:

```
>>> import module1
>>> module1.printer('Hello world!')
Hello world!
```

The `import` statement names one or more modules, separated by commas. In this example, `module1` plays two roles. It identifies the file to load, and it becomes a variable that refers to the module object. Because the name refers to the whole module, you go through it to reach `module1.printer`.

### The from statement

The `from` statement copies one or more names out of the module, separated by commas:

```
>>> from module1 import printer
>>> printer('Hello world!')
Hello world!
```

The copied name lands in the scope where the `from` statement appears. So you can call `printer` without typing the module name. You must do it this way, because `from` does not assign the module's own name. After this statement, `module1` is undefined.

The `from` statement is an extension of `import`. It loads the file in the usual way, then copies names out of it. Only names are copied, not objects. The whole file still loads, but you get direct access to the parts you need.

### The from * statement

A `*` in place of names copies every top-level name in the module:

```
>>> from module1 import *
>>> printer('Hello world!')
Hello world!
```

Both `import` and `from` run the same import operation. The `from *` form adds a step that copies all names into the importing scope. This merges one module's namespace into another. It saves typing, but it gives up the separation between names.

Only a single `*` works here. You cannot select names with a pattern. You could loop over a module's `__dict__` to pick names, but that takes much more work. The `*` also may not copy every name. A module can use `_X` naming, or an `__all__` list, to hide some of its names from this form.

The `*` form works only at the top level of a module file. Inside a function, it gives a syntax error. Python could not detect local variables before the function runs. Imports inside functions are rare. Best practice is to list all imports at the top of a module file. It is not required, but imports are then easier to spot. It also avoids a speed penalty from re-importing a module on every function call.

## Imports run once and at runtime

Many new users ask why their imports stop working. The first import works, but later imports in the same session seem to do nothing. This is by design. A module's code runs on the first `import` or `from` only. Importing is an expensive operation, so Python does it once per file, per process. Later imports fetch the module object that is already loaded.

Because top-level code runs only once, you can use it to set up names. The name's value can then change later. Consider a file called `init.py` with two lines:

```
print('hello')
flag = 1
```

The first import runs the file, and the `print` and assignment both happen:

```
$ python3
>>> import init
hello
>>> init.flag
1
```

Changing the attribute and importing again does not rerun the file. The second import only fetches the existing module object:

```
>>> init.flag = 2
>>> import init
>>> init.flag
2
```

Forcing a rerun needs the `reload` function. It is covered later in this chapter.

### Imports are runtime statements

The `def`, `import` and `from` statements are executable. They are not compile-time declarations. You can place them inside an `if` test to choose between module versions. You can place them inside a function, so they load only when the function is called. You can place them in a `try` statement, to supply a default when an import fails:

```
if sometest:
    from moduleA import name
else:
    from moduleB import name
```

Python does not resolve or run an import until it reaches that line. So an imported module or name is not available until its statement runs.

## Shared objects and cross-file changes

Both `import` and `from` are implicit assignments. The normal assignment rules therefore apply. A name copied with `from` starts out referring to the same object as the module's name. Reassigning the copied name changes only the importer's name. Changing a shared mutable object through the copied name changes it in the source module too.

Consider a file called `share.py`:

```
x = 1
y = [1, 2]
```

In a REPL, copy both names with `from` and change them:

```
>>> from share import x, y
>>> x = 'hack'
>>> y[0] = 'hack'
>>> x, y
('hack', ['hack', 2])
```

The name `x` refers to a number, which is not mutable. Assigning to it changes only the local name. The name `y` refers to a list, which is mutable. Changing it in place affects every name that shares that list. Now import the module by name:

```
>>> import share
>>> share.x
1
>>> share.y
['hack', 2]
```

The module's `x` is still `1`. Its `y` shows the change, because both names share one list.

### Cross-file name changes

A name copied with `from` has no link back to the module it came from. To change a global name in another file, use `import` and assign to the attribute:

```
>>> from share import x, y
>>> x = 23
>>> import share
>>> share.x = 23
```

The first assignment changes only your local `x`. The assignment to `share.x` changes the `x` inside the other module. Changing names in other modules this way is a common source of confusion. It is often a weak design choice. Changing an object through `y[0]` is different. It changes the shared object, not a name. That can also be a weak design, unless every client expects it.

## Choosing import or from

A `from` statement is equivalent to a short sequence of plain statements. This line:

```
from module import name1, name2
```

behaves like this:

```
import module
name1 = module.name1
name2 = module.name2
del module
```

The `from` statement creates new variables in the importer. They start out referring to the objects that have the same names in the imported file. The module name itself is not copied. The `from *` form does the same, but it copies every top-level name.

The first step of a `from` is a normal `import`. So a `from` loads the entire module into memory the first time, no matter how many names it copies. You cannot load part of a module file, such as one function. Because modules are compiled to bytecode, the performance effect is usually small.

### Pitfalls of the from statement

The `from` statement can make a variable's meaning less clear. The name `name` tells the reader less than `module.name` does. The reader may need to search for the `from` line that loaded it. For this reason, some Python users recommend `import` most of the time.

Still, `from` is common and widely used. It is also convenient, especially in the REPL, because you skip typing the module name. There is a real risk, though. A `from` import silently overwrites any variable in your scope that has the same name. The `import` form avoids this, because `module.attr` never clashes with a variable named `attr`.

The `from` statement also has trouble with `reload`. Names copied before a reload may refer to older versions of objects. The `from *` form is worse. It can corrupt a namespace in many ways. When it imports from more than one file, you cannot tell which module a name came from without searching. It merges one namespace into another, which defeats the purpose of modules.

The practical advice is simple. For simple modules, prefer `import`. In most `from` statements, list the names you want. Limit the `from *` form to one per file, or to throwaway REPL code.

### When import is required

You must use `import` when two modules define the same name differently. Suppose one file `M.py` defines `func`, and another file `N.py` also defines `func`. A `from` statement cannot keep both:

```
# O.py
from M import func
from N import func
func()    # Calls N.func only!
```

The second line overwrites the first. An `import` keeps both names apart, because the module names make them unique:

```
# O.py
import M, N
M.func()
N.func()
```

This case is rare. If you do meet it, the `as` extension is another way out. It renames each import:

```
# O.py
from M import func as mfunc
from N import func as nfunc
mfunc(); nfunc()
```

The `as` extension works in both `import` and `from`. In `import`, it can also give a shorter name to a long module name.

## Module namespaces

Modules are best understood as packages of names. A module is a place to define names that should be visible to the rest of a system. Usually a module matches a file. Python creates one module object that holds all names assigned in that file. In simple terms, a module is a namespace, and its names are attributes.

Given `X = 1` at the top level of a file `M.py`, the name `X` becomes an attribute of `M`. Outside the module, you refer to it as `M.X`. Inside `M.py`, `X` is also a global variable. Four ideas explain how this works.

- **Statements run on the first import.** The first time a module is imported, Python creates an empty module object. It then runs the file's statements from top to bottom.
- **Top-level assignments create attributes.** Assignments such as `=` and `def`, when they are not nested in a function or class, create module attributes. An `import` inside the file also creates one, by assigning a module object to a name.
- **Namespaces are dictionaries.** You can reach a module's namespace through its `__dict__` attribute. The built-in `dir` function on a module gives the same result as the sorted keys of `__dict__`.
- **Module scope is one scope.** Inside a module, the local and global scopes are the same. The LEGB lookup rule applies, without the local and enclosing layers.

Module scopes also outlive the import. A function's local scope exists only while the call runs. A module's global scope stays alive after the import. That gives importers a source of tools.

Consider a file called `spaces.py`:

```
print('starting to load...')
import sys
var = 23
def func(): pass
class klass: pass
print('done loading.')
```

The first import runs the file from top to bottom. The two `print` statements run during the import:

```
>>> import spaces
starting to load...
done loading.
```

After the import, the names are attributes of the module object:

```
>>> spaces.sys
<module 'sys' (built-in)>
>>> spaces.var
23
>>> spaces.func
<function func at 0x101ce7b00>
>>> spaces.klass
<class 'spaces.klass'>
```

The name `sys` is an attribute, because an `import` assigns a module object to a name. Any assignment at the top level creates a module attribute.

### Namespace dictionaries

Internally, a module's namespace is a dictionary. You can reach it through `__dict__`. This is useful for tools that list a module's contents in general terms:

```
>>> spaces.__dict__.keys()
dict_keys(['__name__', '__doc__', '__package__', '__loader__', '__spec__',
'__file__', '__cached__', '__builtins__', 'sys', 'var', 'func', 'klass'])
```

The names you assigned appear as keys. Both forms give the same value for `var`:

```
>>> spaces.var, spaces.__dict__['var']
(23, 23)
```

Python also adds useful names to the namespace. The `__file__` name gives the file the module was loaded from. You can use it to find resources bundled with the code. The `__name__` name gives the module's name as importers know it. It has no `.py` extension and no directory path:

```
>>> spaces.__name__, spaces.__file__
('spaces', '/Users/me/…/spaces.py')
```

To see only the names your code assigned, filter out names that start with a double underscore:

```
>>> list(name for name in spaces.__dict__ if not name.startswith('__'))
['sys', 'var', 'func', 'klass']
>>> dir(spaces) == sorted(spaces.__dict__)
True
```

The built-in `vars` function is a less common option. It returns the `__dict__` of the module you pass in:

```
>>> vars(spaces) == spaces.__dict__
True
>>> dir(spaces) == sorted(vars(spaces))
True
```

### Attribute name qualification

Qualification means the `object.attribute` syntax. You can use it on any object that has attributes. The expression `spaces.sys` fetches the value assigned to `sys` in `spaces`. The same idea works on a list. If `L` is a list, `L.append` returns its `append` method.

Qualification is separate from the scope rules. When you qualify a name, you give Python an explicit object to search. The LEGB rule applies only to bare names. It can apply to the leftmost name in a path. The names after each dot are searched in that specific object, not in the scopes.

Here are the full rules for name resolution:

- `X` searches the current scopes, using the LEGB rule.
- `X.Y` finds `X` in the current scopes, then searches for attribute `Y` in the object `X`.
- `X.Y.Z` looks up `Y` in the object `X`, then looks up `Z` in the object `X.Y`.

Qualification works on modules, classes and other objects with attributes. Classes add one more step: inheritance happens during attribute fetch.

## Imports and scopes

An import never gives a file access to names in another file. You must import the file first. A variable's meaning depends on where it is assigned in the source code. An attribute is always requested from an object by name.

Consider two modules. The first, `lex1.py`, defines `X` and a function that changes it:

```
X = 88
def f():
    global X
    X = 99
```

The second, `lex2.py`, defines its own `X`. It imports the first module and calls its function:

```
X = 11
import lex1
lex1.f()
print(X, lex1.X)
```

Running the second file prints this:

```
$ python3 lex2.py
11 99
```

The function `lex1.f` changes the `X` in `lex1`, not the `X` in `lex2`. The global scope of a function is the file that encloses it. That is true no matter which module calls the function. In short, an imported file cannot see names in the file that imports it. A function can see names only in its physical enclosing scope. A module can see names in another module only if it imports that module explicitly.

Python uses lexical scoping. The scopes around a piece of code depend on where the code sits in the file. Function calls and imports do not change them. Some languages use dynamic scoping, where calls can change scopes at runtime. That makes code harder to follow, because a variable's meaning can change over time. In Python, scopes match the text of the program.

### Namespace nesting

Imports do not nest namespaces upward. They do nest downward, though. An imported module cannot see the names in its importer. But a qualification path can reach into nested modules.

Consider three files. The first, `nest3.py`, defines one name:

```
X = 3
```

The second, `nest2.py`, defines its own `X`. It imports `nest3` and reads that module's attribute:

```
X = 2
import nest3
print(X, end=' ')
print(nest3.X)
```

The third, `nest1.py`, defines its own `X`. It imports `nest2` and reads attributes in both files:

```
X = 1
import nest2
print(X, end=' ')
print(nest2.X, end=' ')
print(nest2.nest3.X)
```

When `nest1` imports `nest2`, Python builds a two-level namespace. The path `nest2.nest3.X` descends into `nest3`, which is nested inside `nest2`. So `nest1` can see the `X` names in all three files:

```
$ python3 nest1.py
2 3
1 2 3
```

The reverse is not true. `nest3` cannot see names in `nest2`, and `nest2` cannot see names in `nest1`. It helps to think in terms of objects instead. In `nest1`, `nest2` is a name for an object. Some attributes of that object refer to other objects. Python evaluates a path like `nest2.nest3.X` from left to right, fetching attributes along the way.

The statement `import nest2.nest3` is not the same as `import nest2`. It uses the package import syntax, which follows directory trees rather than file chains. Package imports are covered in the next chapter.

## Reloading modules

A module's code runs only once per process by default. To run it again, call the `reload` function. The `reload` function is covered briefly in earlier chapters. Here is what happens with imports and reloads:

- Both `import` and `from` load and run a module's code only the first time it is imported in a process.
- Later imports use the loaded module object. They do not rerun the file, even if you saved a new version of its source during the run.
- The `reload` function reruns the module's code. Assignments in the new code change the existing module object in place.

Reloads are mainly useful for REPL testing and customization. Restarting the REPL after each change costs time. Reloading a module you changed in another window is faster.

Reloads also support dynamic customization. Parts of a program can change without stopping the whole program. You see the effect of a change at once. Take a database program that connects to a server on startup. After a reload, you can test changes without reconnecting each time. Long-running servers can update themselves this way too.

Python already skips the compile and link steps of a C program. Modules load when a running program imports them. Reloading adds a further benefit. It lets you change parts of a running program without stopping it. This book's use of `reload` covers only modules written in Python. Compiled extension modules can also load at runtime, but they are beyond this chapter.

### reload basics

The `reload` function differs from the `import` and `from` statements in three ways:

- `reload` is a function, not a statement.
- `reload` takes an existing module object, not a string name.
- `reload` lives in the `importlib` standard-library module, so you must import it first.

The module must have been imported successfully before you can reload it. If the first import failed with a syntax error, you may need to import it again. Because `reload` is a function, it needs parentheses. An `import` statement does not. The usual pattern looks like this:

```
import module
...use module.attributes...
...change the module file...
from importlib import reload
reload(module)
...use module.attributes...
```

You import a module, edit its source, and then reload it. You can do this in an interactive session. Larger programs can also reload modules on a schedule.

When you call `reload`, Python rereads the source and reruns its top-level statements. The module object changes in place. Python does not delete it and create a new one. So every reference to the module in your program sees the change. In detail:

- `reload` runs the new code in the module's current namespace. It overwrites the existing namespace rather than deleting it.
- Top-level assignments replace old names with new values. Rerunning a `def` replaces the function in the namespace.
- Clients that use `import` see new values after a reload, because they fetch attributes from the module object.
- Clients that used `from` keep their old references. A reload does not change them.
- A reload affects one module only. You must reload each module you want to update, unless you use tools that reload related modules too.

### A reload example

Create a file called `changer.py` with this content:

```
message = 'First version'
def printer():
    print(message)
```

Start a REPL, import the module, and call the function:

```
$ python3
>>> import changer
>>> changer.printer()
First version
```

Keep the REPL open. Edit and save the file in another window, so it reads:

```
message = 'After editing'
def printer():
    print('reloaded:', message)
```

Back in the REPL, importing again has no effect. You still see the original message. Only a reload fetches the new code:

```
>>> import changer
>>> changer.printer()
First version
>>> from importlib import reload
>>> reload(changer)
<module 'changer' from '/…/changer.py'>
>>> changer.printer()
reloaded: After editing
```

The `reload` function returns the module object. Usually you ignore that result. The REPL prints it because it displays every expression result.

You can also reload a module by its string name. The `sys.modules` dictionary holds every loaded module:

```
>>> import sys
>>> reload(sys.modules['changer'])
```

If you already have a variable for the module, `import changer` is simpler. The `sys.modules` approach helps programs that reload modules in a general way. Deleting a module from `sys.modules` also forces a reload. That approach is discouraged, so use `reload` instead.

### Reload notes

Pair `reload` with `import` instead of `from`. Names copied with `from` do not update after a reload. They stay in an odd state that is hard to reason about.

By itself, `reload` updates one module. You can write a function that applies it to related modules. That pattern is useful in larger programs.

Some development tools, such as Jupyter notebooks, offer an auto-reload mode. It can replace manual `reload` calls. It works only in those tools, though, and it does not cover customization.

The `reload` function has moved over time. It began as a built-in function, then moved to the `imp` module, and now lives in `importlib`. It may move again. Check the current standard-library documentation when you use it.

## Checkpoint questions

1. **How does a module source file become a module object?** When the module is imported, its source file becomes a module object automatically. Python runs the source one statement at a time. Each name assigned along the way becomes an attribute of the module object.
2. **Why might you have to set the `PYTHONPATH` environment variable?** You need it only to import from directories other than the standard library and the home directory. The home directory is the current directory in interactive work, or the folder that holds your program's top-level file. Nontrivial programs that use libraries of tools may need this setting.
3. **Name the five major components of the module search path.** They are the home directory of the top-level script, the directories in `PYTHONPATH`, the standard-library directories, the `site-packages` directory for third-party installs, and the directories listed in `.pth` files in standard places. Programmers can customize `PYTHONPATH` and `.pth` files.
4. **Name four file types that Python might load in response to an import.** Python might load a source file (`.py`), a bytecode file (`.pyc`), a C extension module, or a directory of the same name for package imports. Imports can also load more unusual items, such as ZIP file components, Java classes under Jython, .NET components under IronPython, and statically linked C modules with no file present at all.
5. **What is a module namespace, and what does it contain?** A module namespace is a self-contained package of variables. Those variables are the attributes of the module object. It holds every name assigned by code at the top level of the module file, not nested in a `def` or `class` statement. The module's global scope becomes its attribute namespace. Other files that import the module can change that namespace, but this is generally frowned upon.

6. **How does a `from` statement differ from an `import` statement?** An `import` gives you the module object, and you qualify names through it. A `from` copies named attributes into the importing scope, so you use them directly. Both load the module the same way.
7. **Why can't a second `import` change a module's values?** Python runs a module's code only on the first import in a process. Later imports fetch the loaded module object without rerunning its code.
8. **What makes `reload` different from another `import`?** `reload` reruns the module's code and updates the existing module object in place. A plain `import` only fetches the object that is already loaded.
9. **Why is the `from *` form risky in more than one file?** It merges every top-level name into the importer's scope. You then cannot tell which module a name came from without searching the files.
10. **How do you use two same-named functions from different modules?** Use `import` for both modules, then call each function through its module name, such as `M.func()` and `N.func()`. You can also use `from ... import ... as` to rename each one.

## Sources and review notes

- Source: *Learning Python*, 6th edition (`learning-python-6th-edition`). Chapters used are listed in each section.
- Chapter used: 22, *Modules: The Big Picture* (book folder `learning-python-6th-edition`, chapter prefix "22. ").
- Chapter used: 23, *Module Coding Basics* (book folder `learning-python-6th-edition`, chapter prefix "23. ").
