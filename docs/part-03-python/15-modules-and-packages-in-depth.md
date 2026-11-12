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

Sooner or later a job fails for a reason that has nothing to do with GPUs: Python cannot find one of its own files. Everything in this chapter builds on material that chapter 3.1 only introduces. You will meet it again the first time you open the Python behind a scheduler, an operator, an exporter or a training launcher.

## Module essentials

Open any scheduler, operator or exporter and the first thing you see is a wall of imports. Before you can read the rest of the file, you need to know what those lines really do. Most of the time a module is simply one Python source file. Any file of code becomes a module by existing; nothing declares it. Modules import other modules so they can use the names those modules define. A module can also stand for an extension written in C, Java or C#, or for a whole directory in a package import. Three tools handle modules in all of these forms.

| Tool | What it does |
|---|---|
| `import` | Lets a client (importer) fetch a module as a whole |
| `from` | Allows clients to fetch particular names from a module |
| `importlib.reload` | Provides a way to reload a module's code without stopping Python |

You have already used imports to load standard-library modules and code files in your current directory. The statement looks simple enough. Underneath it sits a richer model, and this chapter walks you through that model one piece at a time.

### Why use modules

A module organizes code into self-contained packages of variables called namespaces. Every name defined at the top level of a module file becomes an attribute of the imported module object. Until another file imports them, those names stay hidden, so they do not clash with names in other files.

This ties back to scopes, which you studied earlier in this course. Imports give access to names in a module's global scope. The file around a function is that function's own global scope. An import lets one file see another file's global names as attributes. Once imported, the module file's global scope becomes the module object's attribute namespace.

Modules are how you link separate files into one larger program. They bring three main benefits.

**Code reuse.** Modules make code permanent. The code lives in a file, so you can run it many times and use it in many programs. Code you type at the REPL disappears the moment you exit Python. Code in a module file stays available.

**Minimizing redundancy.** When several files need the same code, you write it once in a module and import it everywhere. In an earlier benchmarking example, test scripts imported shared timer and test-runner functions rather than repeating them. Like functions, modules keep you out of copy-and-paste programming. Changing common code then takes less work.

**Namespace partitioning.** Modules are the highest-level namespace in a Python program. A name in another file is invisible unless you import that file explicitly. This works much like the local scope of a function, and it prevents name clashes across programs. You cannot opt out of the feature, because everything you run and create lives in a module. Modules group components by their nature.

## Python program architecture

Have you ever split a script into two files and then wondered which one Python actually runs? That question sits at the centre of this section. Most programs are more than one file. Even a small program often pulls in files that someone else wrote. Python encourages a modular structure, where code is grouped into coherent and reusable units. This section shows how the pieces link together.

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

A `def` statement creates the function. Later you can run it by passing values in parentheses after its name. The function is simple on purpose, so we can keep our eyes on how modules work.

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

Python ships with a large collection of utility modules called the standard library. The library holds hundreds of modules. It covers operating system interfaces, object persistence, text pattern matching, network scripting, GUI construction, multithreading and much more. None of these tools belong to the Python language itself. You get them by importing the right modules on any standard Python installation.

Because they are standard-library modules, you can expect them to be present. They also work on most platforms. Earlier examples used `time`, `timeit`, `sys` and `os`. That is only a small part of the library. The standard-library reference manual is free online and covers the rest. The PyDoc tool also lists every importable module.

Browsing is the best way to learn what the library offers. As of Python 3.10, `sys.stdlib_module_names` gives a simple list of all standard-library modules, whether or not they can be imported:

```
$ python3
>>> len(sys.stdlib_module_names) # That's a lot of modules
300
```

## How imports work

You import a module, and a print statement from inside that file fires in the middle of your program's output. Or a module you edited an hour ago refuses to change its behaviour. Both surprises come from the same machinery. The import operation is easy to use and just as easy to misunderstand. Some C programmers compare it to `#include`. That comparison misleads. Python does not paste one file's text into another. An import is a runtime operation. The first time a program imports a file, it performs three steps:

1. Find the module's file.
2. Compile it to bytecode, if needed.
3. Run the module's code to build the objects it defines.

All three steps happen only the first time a module is imported during a program's run. Later imports skip them and reuse the module already in memory.

### Loaded modules are cached

Here is a question that puzzles many newcomers. You import a module, change its file, and import it again. Nothing happens. The answer is that Python keeps a registry. It stores loaded modules in a normal dictionary named `sys.modules`. At the start of each import, Python checks this dictionary for the module's name. The entry `sys.modules['name']` means the same thing as `name` after `import name`. The keys of `sys.modules` list every module loaded so far.

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

A program still runs when bytecode cannot be saved. The compiled code is then created in memory and discarded on exit. The `-B` command-line switch turns off bytecode saves, though you rarely need it. When saved, bytecode files go in a subdirectory named `__pycache__`, next to their source files. This keeps your source folders clean. It also avoids contention and repeated recompiles when several Pythons are installed. Here is what happens when one module file is imported by three different Pythons. On Windows, use `dir` and `py` instead of `ls` and the Python commands.

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

After Python compiles or loads the bytecode, it runs the module's code. Statements run from top to bottom, one at a time. Each name assigned along the way becomes an attribute of the module object, and that is how the tools in a module come into being. A `def` statement runs at import time and creates a function. The function is then available to any file that imports the module.

Because this step runs real code, top-level work in a module shows up at import time. A top-level `print` displays its output when the file is imported. A `def` statement only creates an object for later use. A `class` statement does the same for classes.

Import operations involve real work. They search for files, may run a compiler, and execute code. For that reason, Python imports each module only once per process by default. Later imports reuse the loaded module, as the `sys.modules` check shows. If you need to load a file again, for example to apply dynamic customizations, you can call `importlib.reload`. The next chapter covers that tool.

Most programmers never notice these mechanics, except for faster startups from skipped compile steps. Of the three steps, the search step is the one that often matters.

## The module search path

Two files on the machine share the name `utils.py`. Which one does your import pick, and why? Most programmers must care about the first step, which finds the file to import. You need to know where Python looks. The module search path is the list of directories it searches. You can extend that list for folders of your own.

Built-in modules such as `sys` are coded in C and linked into Python. Frozen modules such as `os` are optimized for faster startup, starting in Python 3.11. Python checks these two groups first, before it scans the search path, so they take precedence. There are only a few of them, so you can mostly ignore them. `sys.builtin_module_names` lists the first group. Counting the names that do not start with an underscore gives 11:

```
>>> sum(1 for m in sys.builtin_module_names if m[0] != '_') # Count non _X
11
```

### Search-path components

Often you never need to configure the search path. If you want to import your own files across directory boundaries, you must customize it. Python builds the search path from five components. Some are set for you. Others you can change to tell Python where to look. Here they are, piece by piece.

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

When an import puzzles you, start here. To see the real search path on your machine, print the built-in `sys.path` list. It holds the directory names that Python searches on each import, and the order of that list matters. Python checks each directory from left to right. It uses the first matching file it finds.

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

Some programs really do need to change `sys.path`, and the case is worth seeing once. A script running on a web server often runs as a limited user such as `nobody`, to restrict machine access. That user cannot rely on `PYTHONPATH` being set in any particular way. Such a script can add the source directories it needs before it runs its imports. An `append`, an `insert` or another list operation does the job for one run:

```
>>> sys.path.append('/Users/me/pycode4') # Extend search path for this run
>>> import module # All imports search the new dir last
```

You can change `sys.path` in code to influence future imports, and this also works in a REPL. Be careful, though. Removing a folder can cut off access to important tools. Your changes disappear when the program or REPL ends. To make path changes last across scripts and sessions, use the lasting techniques above.

## Module file selection

You write `import b`, and Python may load a source file, a bytecode file, a compiled extension or a folder. You never said which one you wanted. Folders are not the only thing that matters during an import. File types matter too. Import statements leave off extensions such as `.py`. Python picks the first file on the search path that matches the imported name. That file need not be a `.py` source file. It might be a `.pyc` bytecode file or something else.

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

Most items on this list go beyond simple files. Here is the reassuring part. To the importer, the type of the loaded file does not matter. Both `import b` and `b.attr` work the same way. `b.attr` might fetch a Python variable or a C function that is linked in. Some standard-library modules are written in C rather than Python. They look like Python modules to their clients, so clients do not need to care.

### Selection priorities

With so many options, conflicts are possible, and they are worth understanding before they bite. Python always loads the matching item found in the first, leftmost directory on the search path. But what happens when one directory holds several matching items? Python then follows a standard picking order. That order is not guaranteed to stay the same over time or across implementations.

One practical rule follows from that. Do not depend on which file type Python picks within one directory. Make your module names distinct. Or configure the search path so your preferences are explicit.

### Path outliers: standalones and packages

Some tools bend these rules. Standalone executables usually embed bytecode in the runnable file. They run without path settings, so module search paths do not apply to them. That is a delivery option outside this chapter's scope.

Package imports also differ. An import statement cannot include path or extension details. Package imports can name a file with part of its directory path, as a set of period-separated names. Even so, package imports still use the normal search path to find the leftmost directory. They also cannot use platform-specific path syntax in import statements. Packages can use `.` syntax to narrow the import search. Package imports are covered separately.

## Chapter summary

This chapter covered the basics of modules and the operation of `import` statements. Here is the whole picture in a few sentences, in case you want to check your understanding before the details that follow. An import finds the designated file on the module search path. It compiles the file to bytecode and runs all its statements to build the module's contents. You can configure the search path to import from directories other than the home and standard-library directories. The main tool is the `PYTHONPATH` setting.

Modules and imports sit at the heart of Python's program architecture. Larger programs split into multiple files. Imports link those files at runtime. Imports use the module search path to find files, and modules define attributes for outside use. Together, these divide a program's logic into reusable, self-contained software components.

## Module files and names

Save a file called `module1.py` with one function inside it, and you have written a module. There is nothing else to do. A module is any text file of Python code saved with a `.py` extension. You write the code in a plain text editor. Python needs no special syntax to treat the file as a module. Every name assigned at the top level becomes an attribute that other files can use.

For example, a file named `module1.py` can hold one function called `printer`. Importing that file gives you a module object with one attribute, `printer`. That attribute refers to the function.

Module filenames should end in `.py` if you plan to import them. The suffix is optional only for a top-level script that you run and never import. Adding it everywhere makes file types obvious. Some editors and file explorers also turn on Python features for `.py` files.

A module name also becomes a variable name inside your program. It must follow the same rules as any variable name. A file called `if.py` can exist, but `import if` gives a syntax error, because `if` is a reserved word. Module filenames and package directory names may contain only letters, digits and underscores. Package directory names also cannot contain spaces.

When Python imports a module called `M`, it searches the module search path. It adds a directory to the front of the name and an extension to the end. So `M` maps to a file such as `directory/M.extension`, which holds the module's code.

### Extension modules

Modules can also be written in other languages, such as C or C++. In the Jython version of Python, they can be written in Java. These are called extension modules. They are often used to wrap external libraries or to speed up part of a program. Clients import them with the same `import` statement, and they provide functions as attributes. Their details are beyond this chapter, so check Python's standard manuals for more.

## Import and from statements

Two lines of code can load the same module and leave your file looking quite different. One leaves you holding a module object. The other leaves you with bare names. Clients use a module by running an `import` or a `from` statement. Both statements find and compile the module file if it is not loaded yet. Both then run its code. The main difference is how much they copy. An `import` fetches the module as a whole, so you must qualify each name with the module name. A `from` copies specific names out of the module, so you can use them directly.

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

The copied name lands in the scope where the `from` statement appears. So you can call `printer` without typing the module name first. You have to do it that way, because `from` does not assign the module's own name. After this statement, `module1` is undefined.

Think of `from` as an extension of `import`. It loads the file in the usual way, then copies names out of it. Only names are copied, not objects. The whole file still loads, but you get direct access to the parts you need.

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

Picture a session like this. You import a module, see its message once, import it again, and nothing happens. Many new users ask why their imports stop working at that point. The first import worked, but later imports in the same session seem to do nothing. This is by design, not a fault. A module's code runs on the first `import` or `from` only. Importing is an expensive operation, so Python does it once per file, per process. Later imports fetch the module object that is already loaded.

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

Two files can end up pointing at one list. One of them appends to it, and the other sees the change too. That surprises people, but it is ordinary assignment at work. Both `import` and `from` are implicit assignments, so the normal assignment rules apply. A name copied with `from` starts out referring to the same object as the module's name. Reassigning the copied name changes only the importer's name. Changing a shared mutable object through the copied name changes it in the source module too.

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

Which form you choose matters more than it looks at first, and the reason becomes clear once you see what each one expands to. A `from` statement is equivalent to a short sequence of plain statements. This line:

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

You write `X = 1` near the top of a file, and a colleague reaches the same value as `M.X` from their own code. How did that name travel from a line in your file to an attribute on an object? Modules are best understood as packages of names. A module is a place to define names that should be visible to the rest of a system. Usually a module matches a file. Python creates one module object that holds all names assigned in that file. In simple terms, a module is a namespace, and its names are attributes.

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

Here is a trap worth meeting early. A file imports another file and then expects to see that file's variables. It never will, no matter who imports whom. An import never gives a file access to names in another file. You must import the file first. A variable's meaning depends on where it is assigned in the source code. An attribute is always requested from an object by name.

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

You edit a module, save it, and switch back to a Python session that is still running. The session keeps using the old code, and importing again changes nothing. A module's code runs only once per process by default. To run it again, call the `reload` function. The `reload` function is covered briefly in earlier chapters. Here is what happens with imports and reloads:

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

## Package imports

Two tools installed on the same machine both ship a file called `utils.py`, and you need both of them. A single file import cannot give you both, and that is the problem packages solve. So far, each import has loaded a single file. A package is a folder of module files, and it can hold nested folders too. Package imports let you load those files with the statements you already know. The import story gets richer here. This section covers four topics: package imports, packages themselves, package-relative imports, and namespace packages.

A package import turns a folder on your computer into a Python namespace. Its attributes match the module files and subfolders inside. Package imports also resolve cases where several installed programs contain files with the same name.

Packages are an advanced topic. Many readers can leave them until they gain experience with file-based modules. Still, packages avoid same-name conflicts. Many standard-library and third-party tools use them, so a basic understanding helps most Python learners.

### Dotted paths in imports

To load an item inside a package folder, list the folder names in a path, separated by periods. You can use that dotted path wherever you would name a simple file. The dots are doing real work here, and the next few examples show where. This works in an `import` statement:

```
import dir1.dir2.mod
```

The same goes for a `from` statement:

```
from dir1.dir2.mod import var
```

It also applies to modules that are already imported, in `reload` calls:

```
from importlib import reload
reload(dir1.dir2.mod)
```

The dotted path must match a path through the folder hierarchy. In this example, `dir1` holds a subfolder `dir2`, and `dir2` holds a module file `mod.py`. The file might also be a bytecode file, a C extension module, or another item with the base name `mod`. The container folder `dir0` must be on the module search path, just as it would be for a simple module file:

```
dir0/dir1/dir2/mod.py # Or mod.pyc, mod.so, etc.
dir0\dir1\dir2\mod.py # Ditto, on Windows
```

Python treats the dotted path as nested objects. After `import dir1.dir2.mod`, the expression `dir1.dir2.mod` passes through three module objects. The syntax is the same on every platform. It also explains a common error. If you leave off the `.py` extension in an import, Python treats the name as a package import and complains that the file is not a package.

### Packages and the module search path

Package paths use only variable names separated by periods. You cannot use platform-specific path syntax in an import statement. This is where import syntax and shell syntax part company. Forms such as `C:\dir1`, `/Users/me/dir1`, or `../dir1` are not valid there. These lines fail with a syntax error:

```
import C:\Users\me\mycode\dir1\dir2\mod # Error: illegal syntax (Windows)
import /Users/me/mycode/dir1/dir2/mod # Ditto, on Unix
```

Put the platform-specific part in the search path instead. Add the folder that holds your packages to `PYTHONPATH`, to a `.pth` file, or to `sys.path` in code. Then your script can use variable names and periods only:

```
import dir1.dir2.mod # OK: variables and periods
```

Entries on the search path supply the platform-specific prefix. The import statement supplies the rest of the path in a neutral form. The container folder does not need to be added if it is already on the path. The search path includes the home directory, the standard-library folders, and the `site-packages` root. Still, the search path must include every folder that holds a leftmost name in your package imports.

## Creating packages

Suppose you have three helper modules in a folder, and a colleague wants to import them from another project. Turning that folder into a package is the usual answer. To build a package, bundle module files and nested folders into a package folder. The folder can also hold an `__init__.py` file, which runs on the first import. It can hold a `__main__.py` file too, which runs when the whole folder runs as a bundle. The next sections build these pieces one at a time.

### Basic package structure

In its simplest form, a package is a folder of normal module files. It can also contain subfolders of the same kind. This example uses indentation to show the nesting:

```
dir0/ # Container listed on module search path
  dir1/ # Package root folder dir1
    mod.py # Module file dir1.mod in package
    dir2/ # Nested package folder dir1.dir2
      mod.py # Module dir1.dir2.mod in package
```

You can create these folders in a file explorer. On most platforms, these commands work too. On Windows, use backslashes:

```
$ mkdir dir1
$ mkdir dir1/dir2 # Use backward slashes on Windows
```

Package folder names follow the same rules as simple module names. Python turns them into variables when they are imported. Use letters, digits, and underscores, and avoid reserved words. Each module's top-level code runs on first import and creates names as usual.

Next, add the nested module files below. The first one is `dir1/mod.py`:

```
var = 'hack'
print('Loading dir1.mod')
```

The second one is `dir1/dir2/mod.py`:

```
var = 'code'
print('Loading dir1.dir2.mod')
```

### Using the basic package

To use the package, load its modules the same way you would load a simple `.py` file. You can do this in a REPL or in another script. Use dots to name the path below the `dir0` folder on the search path. In a REPL, the current directory plays that role:

```
$ python3
>>> import dir1.mod # Package paths in import
Loading dir1.mod
>>> dir1.mod.var # Module code run on import
'hack'
>>> import dir1.dir2.mod # A further-nested path
Loading dir1.dir2.mod
>>> dir1.dir2.mod.var # Repeat path to get item at end
'code'
```

As with top-level modules, a nested module's code runs only on its first import:

```
>>> import dir1.mod # No-op if already imported
>>> import dir1.dir2.mod
```

This is the first thing that surprises people about packages. You generally must import a nested module before you use its attributes. Folders that become module objects do not go back to the filesystem on attribute fetches. So importing only the root folder is not enough:

```
$ python3
>>> import dir1 # Gets dir1, nothing below it
>>> dir1.dir2.mod.var
AttributeError: module 'dir1' has no attribute 'dir2'
$ python3
>>> import dir1.dir2
>>> dir1.dir2.mod.var
AttributeError: module 'dir1.dir2' has no attribute 'mod'
$ python3
>>> import dir1.dir2.mod # List full path to target
Loading dir1.dir2.mod
>>> dir1.dir2.mod.var
'code'
```

The `from` statement works the same way. It is really `import` with an extra copy of names. You still need to list the folder path in full to reach its contents. Paths in import statements are read literally, not taken from variable values:

```
$ python3
>>> from dir1.mod import var # Package paths in from
Loading dir1.mod
>>> var # Don't repeat path to item
'hack'
>>> from dir1.dir2.mod import var
Loading dir1.dir2.mod
>>> var
'code'
>>> from dir1 import dir2 # Paths taken literally
>>> from dir2 import mod # Not from variable values
ModuleNotFoundError: No module named 'dir2'
```

One advantage of `from` is that you type the package path only once. With `import`, you usually repeat the full path each time you use an item. A `from` statement keeps the path in one place. That helps if the package's folder layout changes later, as software tends to do:

```
>>> import dir1.dir2.mod # import requires paths
>>> dir1.dir2.mod.var
'code'
>>> from dir1.dir2.mod import var # from can shorten paths
>>> var
'code'
>>> from dir1.dir2 import mod # And avoids repeating them
>>> mod.var
'code'
>>> import dir1.dir2.mod as mod # Though "as" can too
>>> mod.var
'code'
```

The `as` form of `import` can shorten a path the same way `from` does. A plain reassignment can also shorten it, and `as` is a tidy way to write that.

### Package __init__.py files

A package often needs a little setup before anything else in it runs. The place for that work is a file named `__init__.py` inside the folder. Python calls this file on the package's first import, whether that happens in a program run or in an interactive session. The name is the only special thing about it. The structure now looks like this:

```
dir0/
  dir1/
    __init__.py # Run on first import of dir1
    mod.py
    dir2/
      __init__.py # Run on first import of dir1.dir2
      mod.py
```

The new `dir1/__init__.py` file contains:

```
var = 'Python'
print('Running dir1.__init__.py')
```

The new `dir1/dir2/__init__.py` file contains:

```
var = 3.12
print('Running dir1.dir2.__init__.py')
```

These files are optional in each folder of a package. When present, they run on the first import through a folder, so they give a natural hook for package-specific setup. Their assignments also fill the namespace of the folder's module object. In plain words, the folder gets a module object of its own, and `__init__.py` is the code that fills it. Names in these files become attributes of the package, as names in a regular file do:

```
$ python3
>>> import dir1.dir2.mod # Runs all __init__.py files
Running dir1.__init__.py
Running dir1.dir2.__init__.py
Loading dir1.dir2.mod
>>> dir1.var # Name in __init__.py's namespace
'Python'
>>> dir1.dir2.var
3.12
>>> dir1.dir2.mod.var # Name in nested mod.py namespace
'code'
```

The `reload` function also works with package paths, once they are imported. Continuing the same session:

```
>>> from importlib import reload
>>> reload(dir1)
Running dir1.__init__.py
<module 'dir1' from '/…/LP6E/Chapter24/dir1/__init__.py'>
>>> reload(dir1.dir2)
Running dir1.dir2.__init__.py
<module 'dir1.dir2' from '/…/LP6E/Chapter24/dir1/dir2/__init__.py'>
>>> reload(dir1.dir2.mod)
Loading dir1.dir2.mod
<module 'dir1.dir2.mod' from '/…/LP6E/Chapter24/dir1/dir2/mod.py'>
```

The initialization prints show that each call reloads only the single module at the end of the path. Reloading a whole package path needs a small helper. That helper loads each item on the path, one at a time, starting from a package root.

Packages with `__init__.py` files are called regular packages. Packages without them are called namespace packages. The single-folder demo above was a namespace package until `__init__.py` made it regular. Regular packages take precedence during the module search. Otherwise, the difference is mostly a leftover from history, and it rarely matters. Namespace packages are covered later in this section.

### Package __main__.py files

To let users run a package as though it were a program or script, add a `__main__.py` file to each folder that should support this mode. Python runs that file automatically whenever its folder is launched like a program. The structure now looks like this:

```
dir0/
  dir1/
    __main__.py # Run whenever dir1 bundle is run
    __init__.py
    mod.py
    dir2/
      __main__.py # Run whenever dir1.dir2 bundle is run
      __init__.py
      mod.py
```

The `dir1/__main__.py` file contains:

```
print('Executing dir1.__main__.py')
```

The `dir1/dir2/__main__.py` file contains:

```
print('Executing dir1.dir2.__main__.py')
```

When present, `__main__.py` runs for several launch options. One is a direct console command line that names the package folder. That folder does not need to be on the module search path in this mode:

```
$ python3 dir1 # Runs __main__.py (not __init__.py)
Executing dir1.__main__.py
$ python3 dir1/dir2
Executing dir1.dir2.__main__.py
$ python3 dir1/dir2/mod.py # Runs nested mod.py
Loading dir1.dir2.mod
```

The `-m` mode also runs `__main__.py`. As you saw earlier, `-m` looks up a module on the search path and runs it as the main program. Unlike direct command lines, `-m` starts the full package import machinery. It runs any `__init__.py` files along the path. The package must be on the search path for this mode:

```
$ python3 -m dir1 # Runs both __init__.py and __main__.py
Running dir1.__init__.py
Executing dir1.__main__.py
$ python3 -m dir1.dir2 # And package must be on search path
Running dir1.__init__.py
Running dir1.dir2.__init__.py
Executing dir1.dir2.__main__.py
$ python3 -m dir1.dir2.mod # Runs mod.py, and parents' __init__.py
Running dir1.__init__.py
Running dir1.dir2.__init__.py
Loading dir1.dir2.mod
```

A `__main__.py` file works like an app bundle on macOS or a smartphone. The bundle is really a folder, but you can run it as one item. Keep that picture in mind, because it explains the rest of this section. Authors often use `__main__.py` to give a package a command-line interface. Other programs can import the package to use its tools. Users can also launch the whole package as a standalone program. The file can also host test code for the package.

A `__main__.py` file also runs when it sits in a ZIP file on the search path. Python treats ZIP files like a normal folder during a module search. Python's documentation covers this option in more detail.

One subtlety applies here. Same-package imports inside `__main__.py` may need the package-relative `from .` syntax covered below. That syntax works when the file runs with `-m`, but it fails for direct command-line launches. So choose the launch mode you need to support. Code that must support both package and program use can solve this with full-path imports.

## Why packages?

Packages are optional, and here is the honest answer about them. Early in a coding journey they may seem like overkill, and you can write useful programs without them. Still, they are worth knowing. They help make names unique in large programs and in libraries that others use. Placing your code in a package folder makes it unlikely that its file names clash with other software on the same machine.

The idea is familiar by now. This is the same namespace separation that file-based modules and local function scopes provide. Packages extend it to the filesystem. A reference to your package is qualified by the package folder's name, so same-name collisions are less likely.

Packages can also make imports more descriptive. They make it easier to track down where a variable lives. They can simplify your search path settings. Package imports are strictly required in one case. That case is resolving ambiguity when several installed programs have same-named files. This is mostly an installation issue. It can also come up in everyday work, because developers often pick simple, similar names for module files.

### A tale of two systems

Suppose a programmer writes a program with a common file, `utilities.py`, and a top-level file, `main.py`, that users launch. Every file in the program says `import utilities` to load the shared code. When the program is installed, its files unpack into one folder called `system1`:

```
system1/
  utilities.py # Common utility functions, classes
  main.py # Launch this to start the program
  other.py # Import utilities to load my tools
```

A second programmer writes a different program. It also has files named `utilities.py` and `main.py`, and it uses `import utilities` in the same way. Its files unpack into a new folder called `system2`, so they do not overwrite the first system's files:

```
system2/
  utilities.py # Common utilities
  main.py # Launch this to run
  other.py # Imports utilities
```

Both systems can coexist and run on the same computer. You do not need to configure the search path to use them. Python always searches the home directory first, which holds the top-level file. So imports in each system see that system's own files. Running `system1/main.py` searches `system1` first. Running `system2/main.py` searches `system2` first. Search path settings matter only when an import crosses a directory boundary.

Now suppose you want to use the code in one of the two `utilities.py` files from a third folder of your own:

```
import utilities
utilities.func('hack')
```

The problem starts here. You must add a directory that holds a `utilities.py` to the search path. But which directory goes first, `system1` or `system2`? The search path is a linear list. Python scans it from left to right. It finds one `utilities.py`, from the leftmost directory that has one. The other file stays out of reach.

You could change `sys.path` in your script before each import, but that is extra work and invites mistakes. Changing `PYTHONPATH` before each run is tedious. It also cannot let one file use both versions. By default, you are stuck.

Packages fix this problem. Instead of installing each program in its own folder listed on the search path, install each one as a subfolder of a common root:

```
root/
  system1/
    utilities.py
    main.py
    other.py
  system2/
    utilities.py
    main.py
    other.py
  mycode/ # Here or elsewhere
    myfile.py # Your new code here
```

Add only the common root to your search path. If your imports are relative to this root, you can import either utility file with a package import. The enclosing folder name makes the path unique. You can even import both utility files in the same module, if you repeat the full path each time:

```
import system1.utilities # Import from one package
import system2.utilities # Import from another
system1.utilities.function('hack') # And use names from either
system2.utilities.function('code') # Or both!
```

The folder names make the module references unique. You need `import` instead of `from` only when you must reach the same attribute name through two or more paths. If each function had a different name, `from` statements would avoid repeating the full package path. The `as` form can also give each one a unique synonym.

The `mycode` folder does not have to sit under the root. It only needs to hold the packages you import from. Because you never know when your own modules will be useful elsewhere, placing them under the common root may prevent similar name collisions later.

Path setup stays simple when you unpack every Python system under one common root. You add that root only once. Both original systems keep working unchanged. Their home directories are searched first, so the new root is irrelevant to their code. They can keep saying `import utilities` when run as programs. If they are also used as packages, they may need `from .` package-relative imports, and `main.py` could become `__main__.py`.

Even if you never create packages, you will probably use standard-library and third-party tools that do. A sample of standard-library packages looks like this:

```
from email.message import Message # Email parsing/construction
from tkinter.filedialog import askopenfilename # Portable GUI toolkit
from http.server import CGIHTTPRequestHandler # Web-server utilities (till Python 3.15?)
```

Bundling code in a package keeps such tools self-contained and avoids name conflicts. Whether you do the same for your own code is up to you.

## The roles of __init__.py files

The `__init__.py` files in the opening demo were simple. These files can hold arbitrary Python code, just like normal module files. Their special name makes Python run them automatically the first time a program imports the directory. That makes them a hook for setup steps the package needs. They can also be completely empty, and they sometimes have other roles.

The file serves four roles, and only one of them is the obvious one. It is a hook for package initialization. It creates a module namespace for a directory. It declares a directory as a regular Python package. It also controls what a `from *` statement does for folders in package imports.

### Package initialization

The first time a program imports through a directory, Python runs all the code in that directory's `__init__.py` file. So these files are a natural place to set up the state that other package files need. A package might create required data files, open connections to a database, or do similar work. These files are not meant to be run directly. That job belongs to `__main__.py`. Python runs `__init__.py` automatically when the package is first imported for use elsewhere.

### Module namespace initialization

Directory paths become real nested object paths after an import. In the earlier demo, `dir1.dir2` works and returns a module object. Its namespace holds all the names assigned by `dir2`'s `__init__.py` file. A folder has no module file of its own, so these assignments give it a place to define names. That is the second role, and it is easy to miss.

### Package indicator for search

`__init__.py` files also declare that a directory is a Python package. This role keeps folders with common names from hiding real modules further along the search path. Without it, Python could settle on a folder unrelated to your code. The only reason would be that the folder appears earlier in the search list.

Namespace package rules now cover part of this job. They scan ahead on the search path for later items before settling on a plain folder. Even so, a package with `__init__.py` still gets higher priority than a same-name folder elsewhere on the path.

### The `from *` statement behavior

An advanced feature lets you control `from *` with a list of name strings called `__all__`. You place that list at the top level of an `__init__.py` file. In a package's `__init__.py`, `__all__` names the nested submodules that should be imported automatically when `from *` is used on the package folder itself.

If `__all__` is not set, `from *` does not load submodules nested in the package folder. It loads only the names assigned in the package's `__init__.py` file. That includes any submodules this file imports explicitly. For example, `from submodule import X` in a package's `__init__.py` makes `X` available in that package's namespace, even without `__all__`.

The `__all__` list also declares `from *` exports for simple file-based modules, not only packages. You will see an example of `__all__` later in this section.

**Note:** Package `__init__.py` files are not the same as the `__init__` method of a class. A package's `__init__.py` is a file of code that runs when imports first step through its folder. A class's `__init__` method runs each time an instance is created. Both have initialization roles, and both are optional. Otherwise they differ, despite the shared name.

## Package-relative imports

Up to now, every package import in this chapter has come from outside the package. Files inside a package can import each other the same way, with the full path, and often should. They have a second option as well. A relative import points at the package itself, so the import cannot wander off and load some other file that happens to share the name.

### Relative and absolute imports

Files used as part of a package can use special syntax like this. It works only in package files, and only in `from` statements, not in `import`:

```
from . import module # Import a module in this package (only)
from .module import name # Import a name from a module in this package
from .. import module # Import a module sibling of the parent folder
from ..module import name # Import a name from a parent-sibling module
```

The `import` statement would not fit this form. It binds modules to simple names, not to paths. In a `from` statement, though, the source can begin with dots. An import like this is called relative. It finds an item relative to the folder of the enclosing package.

The name comes from relative filename paths. Those paths point to a file from the current working directory. Here the dots work the same way, except that the base is the package. A single dot means the enclosing package folder. Two dots mean its parent folder. Each extra dot goes one level higher, though that is rare. The effect names an item relative to the importing file's package, not a content file relative to the working directory.

A relative import looks only inside the named package. It does not consult the folders on `sys.path`. It also skips the check for built-in and frozen modules. Relative syntax works only when a file is used as part of a package. It fails in any other use. That has both good and bad effects, as the next sections show.

Files that are part of a package can still write imports without dots:

```
import module # Import a module from a folder in sys.path
from module import name # Import a name from the same
```

An import without leading dots is called absolute. It names an item in a folder listed on `sys.path`. This is normal Python import behavior. The word is a little misleading. These imports are really relative to an entry on the module search path. The terminology has stuck anyway.

Absolute imports within a package do not check the package itself. They skip it and go straight to the folders on `sys.path`. That path may include the package folder anyway, through the working directory, the home folder of the top-level script, or `PYTHONPATH`. On their own, though, absolute imports do not look inside the package.

### Relative-import rationales and trade-offs

So why use the dots? The short answer is self-defence. Relative imports let a package make sure its imports load its own modules. Because they search only the package itself, they will not load a same-named but unrelated module from elsewhere on the host. This makes the package more self-contained. Without relative imports, a stray module of that name could break the package's code. With them, the package depends less on search path settings it cannot predict or control.

The downside is that this model is all or nothing. You basically must choose a mode for your files: package or program. Relative imports see the package itself, but they cannot be used in nonpackage mode. Absolute imports work in nonpackage mode, but they cannot see the package itself. That combination seems like a catch-22 that limits your code.

If you are writing a library of tools, this may not matter. You can use relative imports throughout the package, and add a `__main__.py` file so it can run as a program with the `-m` switch. If you are writing a traditional folder of code that you want to use in any way, your options look limited.

One easy solution is to skip relative imports altogether. Use full, explicit, absolute package-import paths everywhere in your code. Each path names the item from the package's root folder onward:

```
import package.module # Import a module in this package
from package import module # Same as: from . import module
from package.module import name # Same as: from .module import name
```

This works only if the package's root folder sits in a folder listed on `sys.path`. That is the normal case, because clients could not import the package's code any other way. This approach does not directly support `..` parent-sibling imports. Those seem rare. Just one standard-library tool relies on them today.

Because of this, code folders gain flexibility. Direct command lines and the `-m` switch both can run package files as programs. The following section shows how.

### Package-relative imports in action

To demonstrate these points, return to the simple package from the start of this section. Its `__main__.py` runs automatically when the folder runs as a bundle. It also plays the role of any top-level file launched as a script. Its last known state is below, so you do not have to scroll back:

```
# prior dir1/mod.py
var = 'hack'
print('Loading dir1.mod')
# prior dir1/__main__.py
print('Executing dir1.__main__.py')
```

#### The normal-import warm-up

This `__main__.py` worked as expected. Things get harder if a file run as a top-level script imports another module from its own package folder. Here is a rewrite of `dir1/__main__.py` that does that:

```
import mod
print('Executing dir1.__main__.py:', mod.var.upper())
```

Written this way, the file runs with a direct command line, both as a folder and as a script. It does not run with the `-m` switch, which brings the package machinery online. Notice the `__init__.py` output in the `-m` mode:

```
$ python3 dir1 # Launch with a direct command line
Loading dir1.mod
Executing dir1.__main__.py: HACK
$ python3 dir1/__main__.py # As folder bundle or explicit file
Loading dir1.mod
Executing dir1.__main__.py: HACK
$ python3 -m dir1 # Launch with Python -m module switch
Running dir1.__init__.py
ModuleNotFoundError: No module named 'mod'
$ python3 -m dir1.__main__ # As package root or explicit module
Running dir1.__init__.py
ModuleNotFoundError: No module named 'mod'
```

The first two commands work because `__main__.py` runs as a normal, nonpackage program. It finds its sibling through the home entry on `sys.path`, which is the top-level file's own folder. The last two commands fail. They use the file as part of a package. So `import mod` is read as an absolute import, which skips the enclosing package. That is why they fail.

#### The relative-import adventure

A first reaction might be to add a relative import to satisfy the package system:

```
from . import mod
print('Executing dir1.__main__.py:', mod.var.upper())
```

This fixes `-m` usage, but it breaks direct command lines:

```
$ python3 -m dir1
Running dir1.__init__.py
Loading dir1.mod
Executing dir1.__main__.py: HACK
$ python3 -m dir1.__main__
Running dir1.__init__.py
Loading dir1.mod
Executing dir1.__main__.py: HACK
$ python3 dir1
ImportError: attempted relative import with no known parent package
$ python3 dir1/__main__.py
ImportError: attempted relative import with no known parent package
```

The first two commands work because `-m` runs package behavior. That enables the relative `.` import syntax, which searches the package and finds the module. The last two commands fail. Python does not allow relative imports in nonpackage mode. That dooms these runs from the start, whatever the search path says. So it seems we must choose a package role or a nonpackage role for our code.

#### The absolute-import solution

An easy way out is to use normal package imports that spell out the absolute path from the package root. As noted, these paths are still relative to `sys.path`:

```
import dir1.mod
print('Executing dir1.__main__.py:', dir1.mod.var.upper())
```

The package root, `dir1`, normally sits on `sys.path`. Outside code can reach that package only through this root. Callers must begin their imports at `dir1`.

For this demo, add the package root to the search path explicitly, using `.` for the current directory. In real use, this might be an absolute path, or the site-packages root of installed packages. The top-level file's home folder in direct-command mode sits one level below the package root. Both direct-command and `-m` modes need access to the package root, so set it here:

```
$ export PYTHONPATH=. # Or similar outside Unix: see the search path section
$ python3 dir1
Running dir1.__init__.py
Loading dir1.mod
Executing dir1.__main__.py: HACK
$ python3 dir1/__main__.py
Running dir1.__init__.py
Loading dir1.mod
Executing dir1.__main__.py: HACK
$ python3 -m dir1 # Both usage modes work, sans "." imports
Running dir1.__init__.py
Loading dir1.mod
Executing dir1.__main__.py: HACK
$ python3 -m dir1.__main__
Running dir1.__init__.py
Loading dir1.mod
Executing dir1.__main__.py: HACK
```

Now both direct command lines and the `-m` switch work. The code is not limited to one launch mode. This is dual-mode code. It can be used as both a program and a package.

If you would rather not repeat import paths at each use, both launch modes still work with other forms of `__main__.py`. Test them yourself to confirm, since they follow ordinary import rules:

```
import dir1.mod as mod
print('Executing dir1.__main__.py:', mod.var.upper())
```

```
from dir1 import mod
print('Executing dir1.__main__.py:', mod.var.upper())
```

```
from dir1.mod import var
print('Executing dir1.__main__.py:', var.upper())
```

You can also use `from *` in this scheme, if you add an `__all__` list to the package root's `__init__.py` file. The usual cautions about `from *` given earlier in this chapter still apply:

```
# dir1/__init__.py
__all__ = ['mod']
# dir1/__main__.py
from dir1 import *
print('Executing dir1.__main__.py:', mod.var.upper())
```

If you are sure your code will only ever run as part of a package, you can use relative imports in all of its files to reach same-package modules. The absolute-path solution fits files meant to launch as top-level scripts. Other files that are only imported can use package-relative imports.

Relative imports have one clear advantage. A same-named module earlier on `sys.path` cannot accidentally override a crucial module in the package. But they limit a file to package-only roles. If package files must support both launches and imports, relative imports are not the best option.

This section skips some details for space. First, `-m` mode also checks the working directory for absolute imports. So the `PYTHONPATH` setting in the demo is optional for that mode. Second, some sources say relative-import failures in scripts come from the name `'__main__'`. Files run with `-m` have the same name too. They also follow other protocols that are too obscure to cover here. Because package-relative imports change over time and mostly serve programmers who build large libraries, Python's documentation is the best guide for the finer points.

Namespace packages do not add new syntax. They allow a module to span folders. The next section covers them.

## Namespace packages

Imagine two teams ship parts of one library from two different folders on the same machine. Neither folder knows about the other, yet a single import name has to reach both of them. That is what a namespace package does. Namespace packages are the last package topic. They are packages that may be built from one or more folders, located in different parts of the module search path.

Packages split across folders are probably rare in practice. But the import search changes that made them possible also allow packages without `__init__.py` files. Since this revised algorithm is now the import search itself, namespace packages are a side topic. They are still worth understanding.

To see where namespace packages fit, a short history helps.

### Python import models

Python has four import schemes. They are listed below from the original to the newest. The examples are representative, not complete. The `from` statement also allows a `*` wildcard, and `reload` can reload any module passed to it. Those are add-on topics.

Basic modules came first. They import files and their contents, relative to the `sys.path` module search path:

```
import module
from module import name
```

Basic packages came next. They import from folder paths relative to `sys.path`. Each package sits in a single folder that has an `__init__.py` file:

```
import folder.folder.module
from folder.module import name
```

Package-relative imports are the third model. They handle imports within the same package, as covered in the prior section. Relative and absolute lookup rules apply to imports with and without leading dots:

```
from . import module
from .module import name
```

Namespace packages are the newest model. They are still relative to `sys.path`. But they allow packages to span multiple directories, and they remove the requirement that a package must define an `__init__.py` file:

```
import anyfolder.anyfolder.module
from anyfolder import name
```

The first two models are self-contained. The third tightens the search order and extends the syntax for same-package imports. The fourth changes some of the notions and requirements of the prior package model. Python now formally defines two flavors of packages. The first is the original model, now known as regular packages. The second is the alternative model, known as namespace packages.

The two package models are not mutually exclusive. They can be used together in the same program. The namespace model works as a fallback. It only takes effect when no simple module or regular package with that name is found on the search path. Despite the showy title, namespace packages are really a change to import search, as the following sections explain.

### Namespace-package rationales

A namespace package is not fundamentally different from a regular package. It is simply another way to create one. At the top level, a namespace package is still relative to `sys.path`. The leftmost component of its dotted path must be found in an entry on the normal module search path.

Physically, though, regular and namespace packages differ. A regular package has an `__init__.py` file that runs automatically, and it lives in a single directory. A namespace package cannot contain an `__init__.py` file. It may span several directories, collected at import time. Because the presence of `__init__.py` identifies the package type, none of the directories in a namespace package can have that file. The content nested in all of them still forms one composite package.

The reason for namespace packages comes from package installation. That may seem obscure unless you handle such tasks. In short, several `__init__.py` files can collide when package parts are merged. Removing that file avoids the collision. Namespace packages also support packages split across multiple directories, located in multiple `sys.path` entries. That improves install flexibility. It also replaces several incompatible solutions that had appeared to meet the same goal.

For most Python users, the biggest benefit is simpler. Namespace packages no longer require `__init__.py` initialization files. So any directory of code can be used as an importable package. Next, the details of the import search.

### The module search algorithm

To understand how namespace packages change import search, look at how an import operation works. Python resolves an import by checking a group of candidate folders in turn, much like reading a row of mailboxes from left to right. For the first part of a dotted name, the candidates are all the directories on `sys.path`. For components nested in a package import, or named in a relative import, the candidates are just the package itself. A package folder has one instance of a given name. A search path may have many.

For each directory among the candidates, Python tests for matches to the name, in this order:

1. If `directory/name/__init__.py` exists, Python imports and returns a regular package.
2. If `directory/name.py`, `name.pyc`, or another module extension exists, Python imports and returns a simple module.
3. If `directory/name` exists and is a folder, Python records it and continues the scan with the next candidate directory.
4. If none of the above matches, Python continues the scan with the next candidate directory.
5. If the candidate scan finishes without a regular package or module from steps 1 or 2, and step 3 recorded at least one directory, Python creates and returns a namespace package. Otherwise, it reports an error.

The namespace package is created right away. It is not deferred until a lower-level import happens. In other words, a namespace package is a real module object, just one with no home file of its own. It is a module object with no `__file__` attribute. Its `__path__` attribute is set to an iterable of the directory path strings that step 3 recorded during the candidate scan.

Later and deeper accesses use this `__path__` as their set of candidates. Each recorded entry is searched whenever a further-nested item is requested. A regular package searches only its one directory. Viewed another way, the `__path__` of a namespace package plays the same role for lower components that `sys.path` plays at the top. It becomes the parent search path for accessing lower items, using the same four-step procedure.

The net result is that a namespace package is a virtual concatenation of directories found on one or more search candidates. Once it is created, it works like a regular package in every functional way. That includes the package-relative import syntax.

Any single directory without an `__init__.py` file, nested in a search-path folder, is classified as a namespace package by step 3. So any such directory qualifies as a package. The only operational difference from a regular package folder is search precedence. Same-named folders with an `__init__.py` file, and simple modules anywhere on the search path, are chosen first by steps 1 and 2.

So adding an `__init__.py` file, even an empty one, ensures your package is selected instead of a same-named folder later on the search path. It may also speed up imports, since the scan ends at step 1. That benefit happens once, though. Whether to include the file depends on your goals, and on the other roles of `__init__.py` covered earlier.

### Namespace packages in action

The opening demo of this section already made single-folder namespace packages. Its folders had no `__init__.py` files yet. Any folder nested in a search-path folder counts as a package, unless a same-named regular package or simple module elsewhere on the path hides it.

To see the folder-concatenation effect, work through a quick demo. Make two modules in a nested layout. Two folders named `sub` sit in different parent folders, `part1` and `part2`. Indentation shows the nesting:

```
ns/
  part1/
    sub/
      mod1.py
  part2/
    sub/
      mod2.py
```

There are no `__init__.py` files here. As noted earlier, namespace packages cannot use them. That is their main difference from regular single-folder packages. You can create these folders with commands like the following. On Windows, switch `/` to `\` and omit the `-p`:

```
$ mkdir -p ns/part1/sub # Two subdirs of same name in different dirs
$ mkdir -p ns/part2/sub # And similar on Windows
```

The two module files print a line on import, as a trace. The first one, `ns/part1/sub/mod1.py`, contains:

```
print('Loading ns/part1/sub/mod1')
```

The second one, `ns/part2/sub/mod2.py`, contains:

```
print('Loading ns/part2/sub/mod2')
```

Now add both `part1` and `part2` to the module search path. Then `sub` becomes a namespace package that spans both folders. Its two module files are available under one name, even though they live in separate physical directories. This Unix command uses paths relative to the working directory. In practice, you would more likely list two full, absolute paths. On Windows, use `set` instead of `export`:

```
$ export PYTHONPATH=ns/part1:ns/part2
```

When imported directly, the namespace package is the virtual concatenation of its folders. Its nested parts can be reached through its single composite name, with normal imports. The paths below are shortened with `…`, and line breaks were added for fit:

```
$ python3
>>> import sub
>>> sub # Namespace packages: nested search paths
<module 'sub' (namespace) from
['/…/LP6E/Chapter24/ns/part1/sub', '/…/LP6E/Chapter24/ns/part2/sub']>
>>> from sub import mod1
Loading ns/part1/sub/mod1
>>> import sub.mod2 # Content from two different directories
Loading ns/part2/sub/mod2
>>> mod1
<module 'sub.mod1' from '/…/LP6E/Chapter24/ns/part1/sub/mod1.py'>
>>> sub.mod2
<module 'sub.mod2' from '/…/LP6E/Chapter24/ns/part2/sub/mod2.py'>
```

This split-folder package also works if you import through the namespace package name right away. The namespace package forms when it is first reached, so the timing of path additions does not matter:

```
$ python3
>>> import sub.mod1
Loading ns/part1/sub/mod1
>>> import sub.mod2 # One package spanning two directories
Loading ns/part2/sub/mod2
>>> sub.mod1
<module 'sub.mod1' from '/…/LP6E/Chapter24/ns/part1/sub/mod1.py'>
>>> sub.mod2
<module 'sub.mod2' from '/…/LP6E/Chapter24/ns/part2/sub/mod2.py'>
>>> sub
<module 'sub' (namespace) from
['/…/LP6E/Chapter24/ns/part1/sub', '/…/LP6E/Chapter24/ns/part2/sub']>
>>> sub.__path__
_NamespacePath(
['/…/LP6E/Chapter24/ns/part1/sub', '/…/LP6E/Chapter24/ns/part2/sub'])
```

Relative imports also work in namespace packages, if you add one. Here is the modified `ns/part1/sub/mod1.py`:

```
from . import mod2
print('Loading ns/part1/sub/mod1')
```

The added relative import references a file in the package, even though that file lives in a different folder:

```
$ python3
>>> import sub.mod1 # Relative import of mod2 in another dir
Loading ns/part2/sub/mod2
Loading ns/part1/sub/mod1
>>> import sub.mod2 # Already imported by mod1.py: not rerun
>>> sub.mod2
<module 'sub.mod2' from '/…/LP6E/Chapter24/ns/part2/sub/mod2.py'>
```

Namespace packages work like ordinary single-folder packages in every way, except that their storage is split. By the same logic, a folder without `__init__.py` is simply a namespace package with one folder. It has no initialization logic to run.

Namespace packages are a useful tool. Still, most Python learners do better by first mastering packages that map to real folders. Packages spread across a host's folders can come later. Python's documentation covers namespace packages in more depth.

## Module design concepts

Picture two modules that read and write each other's globals. Nothing in Python stops you, and a month later nobody can say which value wins. Modules involve design trade-offs, just as functions do. You decide which functions belong in which module, and how modules communicate. These choices become clearer as systems grow. Four ideas help from the start.

You are always inside a module in Python. There is no place to write code outside one. Even code typed at the interactive prompt, also called the REPL, runs in a built-in module named `__main__`. The prompt differs in two ways. Code runs and is discarded at once, and expression results print automatically.

Keep coupling low. A good module works like a closed box. It should depend as little as possible on global variables defined in other modules. The only things it should share with the outside world are the tools it imports and the tools it defines.

Raise cohesion. Functions work best with one job, and modules do too. When every part of a module serves one general purpose, those parts are less likely to need outside names. A focused module is also easier to reuse.

Leave other modules' variables alone. Reading globals from another module is fine, because that is how clients use services. Changing another module's globals is usually a design problem. Pass results through function arguments and return values instead. Otherwise a global's value depends on the order of assignments in remote files, and the modules become hard to understand.

Here is the environment in which modules operate. Modules hold variables, functions and classes. They import other modules to use the tools those modules define. Functions and classes have local variables of their own. Functions can nest, but every piece of code is ultimately contained by a module at the top.

## Data hiding in modules

A module exports every name assigned at its top level. Python has no syntax for declaring which names are private. Nothing stops a client from changing a name inside a module, either. Data hiding is therefore a convention, not a rule. Some purists argue that this rules out encapsulation. In Python, encapsulation is more about packaging than restriction. Classes follow the same idea in the next part.

### Hiding names from `from *`

Prefix a name with a single underscore, such as `_X`, to keep it out of a `from *` import. This limits namespace pollution. A `from *` copies every name it can, so the importer may get more than it wanted. That can include names that overwrite its own. An underscore does not make a name private, though. `import` and a normal `from` still reach it.

The idea appears in `unders.py`:

```
a, b, _c, _d = 1, 2, 3, 4 # Control from * exports, take 1
```

A session follows. The `from *` form loads `a` and `b`, but not `_c`. The other import forms reach all four names:

```
$ python3
>>> from unders import * # Load non _X names only on from *
>>> a, b
(1, 2)
>>> _c
NameError: name '_c' is not defined. Did you mean: '_'?
>>> from unders import _c # But other importers get every name
>>> _c
3
>>> import unders
>>> unders._d
4
```

You can also list the names to copy in a variable called `__all__`. Assign it a list of name strings at the top level of the module. Python checks for `__all__` first. When it exists, `from *` copies exactly the names listed, even ones with underscores. When it is missing, `from *` copies every name without a leading underscore. In effect, `__all__` says what to copy, while `_X` says what to skip.

`alls.py` uses both tools:

```
__all__ = ['a', '_c'] # Control from * exports, take 2
a, b, _c, _d = 1, 2, 3, 4 # __all__ has precedence over _X
```

Again, `from *` gets only the names in `__all__`. Other importers still get every name:

```
$ python3
>>> from alls import * # Load __all__ names - only
>>> a, _c # Even if they have underscores
(1, 3)
>>> b
NameError: name 'b' is not defined
>>> from alls import a, b, _c, _d # But other importers get every name
>>> a, b, _c, _d
(1, 2, 3, 4)
>>> import alls
>>> alls.a, alls.b, alls._c, alls._d
(1, 2, 3, 4)
```

As with the `_X` convention, `__all__` affects only the `from *` form. It is not a privacy declaration. Module writers can use either technique to build modules that behave well under `from *`. The package `__init__.py` section above uses `__all__` in a related way. There, the list declares nested submodules to load for a `from *` on their container. Packages extend the idea to the contents of a folder.

### Managing attribute access with `__getattr__` and `__dir__`

Python 3.7 added two special functions that can sit at a module's top level. If a module defines `__getattr__`, Python runs it when a requested attribute is not found. If a module defines `__dir__`, that function replaces the normal list fetched by the `dir` built-in. Together they can enforce access rules or build dynamic interfaces.

Their names match same-named methods in classes. They also replace an older, obscure trick. That trick swapped a module's entry in `sys.modules` for a class instance with the same methods. These functions make the idea simpler. They make the most sense after you study classes, which come next.

`gamod.py` shows the basics:

```
var = 2 # Real attribute returned directly
def __getattr__(name): # Undefined attr fetches routed here
    print(f'(virtual {name})', end=' ')
    match name:
        case 'test':
            return name * var
        case 'hack' | 'code':
            return name.upper()
        case _:
            raise AttributeError(f'{name} is undefined')
def __dir__():
    return ['var', 'test', 'hack', 'code']
```

When imported, real attributes work normally, subject to the `_X` and `__all__` rules for `from *`. A missing name goes to `__getattr__`, which can manage the request. It can also raise an exception to flag an invalid request. Exceptions get full coverage later in this course:

```
>>> import gamod
>>> gamod.var # Real: __getattr__ not called
2
>>> gamod.test # Virtual: computed when fetched
(virtual test) 'testtest'
>>> gamod.hack
(virtual hack) 'HACK'
>>> gamod.nonesuch
AttributeError: nonesuch is undefined
>>> dir(gamod)
['code', 'hack', 'test', 'var']
```

The `from` statement calls `__getattr__` too. A `from *` needs the names to appear in `__all__`. You can mostly ignore the stray `__path__` fetch, but `__getattr__` must accept it:

```
>>> from gamod import code
(virtual __path__) (virtual code)
>>> code
'CODE'
>>> from gamod import *
(virtual __path__) (virtual __all__)
>>> var
2
>>> hack
NameError: name 'hack' is not defined
```

Importantly, `__getattr__` does not run for global lookups inside the module itself. Undefined names in the file stay undefined. The hook serves attribute fetches from other modules. It also ignores assignments. For example, this line added to the file fails, and the REPL line that follows creates a real attribute:

```
print(test) # File: does NOT call __getattr__ (raises NameError)
gamod.hack = 'real' # REPL: does NOT call __getattr__ (makes attribute)
```

After the second line, `hack` bypasses `__getattr__` for good. Keep that in mind when you test a module interactively.

This all works as advertised. It is a tool-builder's hook, though, and legitimate uses are narrow. It also mixes modules with classes. Learners do not yet know where these functions come from. This is a common theme in Python. Additions often assume you already know Python well.

A later proposal to add a class-style `__setattr__` for module attribute assignment was rejected by the Python steering committee. Only `__getattr__` and `__dir__` got through. Weigh the complexity of this extension against its real uses.

## Enabling language changes with `__future__`

Open an older Python file and you may find a line that looks like a message from the future. That line is often the first executable statement in the file. Python changes often roll out in stages. Some arrive as optional extensions that stay off by default. Version 3.0 was a glaring exception to that gentle pace. Python 2.X still received support for 12 more years after 3.X came out.

To enable an optional extension in an older Python, use this import form:

```
from __future__ import featurename
```

In a script, this statement must come first among the executable statements. A docstring or comment may come before it. It changes how Python compiles that one module. At the interactive prompt, the feature stays on for the rest of the session.

The prior edition of this book used `__future__` for several 2.X-era features. These included 3.X true division, 3.X `print` calls, and 3.X absolute imports for packages. Earlier editions used the same form to introduce generator functions, which needed `yield` before it was on by default.

This edition goes forward with the present. Older Pythons can still use `__future__` to enable a later change, such as the 3.7 behavior where `StopIteration` bubbles out of generators:

```
from __future__ import generator_stop
```

The Python library manual lists every feature name you can import this way. Those names are never removed, so leaving a `__future__` import in place is safe. Even code run by a Python where the feature is standard can keep the line.

## The `__name__` usage-mode variable

One file can serve two roles, as a library and as a program, and the trick behind it is a single variable. You can import a file as a module, or run it as a standalone script. Python sets a built-in attribute named `__name__` for each module:

- If the file runs as a top-level script, `__name__` is the string `'__main__'`.
- If the file is imported, `__name__` is the module's name as clients know it.

A module can test its own `__name__` to see how it is being used. `dualmode.py` shows the trick:

```
def title():
    print('Learning Python, 6E')
if __name__ == '__main__': # Only when run
    title() # Not when imported
```

Imported, the module only defines a function that clients can call:

```
$ python3
>>> import dualmode
>>> dualmode.title()
Learning Python, 6E
```

Run as a program, the bottom code calls the function automatically:

```
$ python3 dualmode.py
Learning Python, 6E
```

In effect, `__name__` acts as a usage-mode flag. The same code works as an importable library and as a top-level script. You will see this hook in many Python files, both for testing and for dual use.

### Self-test code

The most common use is self-test code. Wrap the tests for a module's exports in a `__name__` check at the bottom of the file. Clients can import the file normally. You can still test its logic by running it from the shell or another launch method.

This is probably the simplest unit-testing protocol in Python. It beats retyping your tests at the interactive prompt each time. The standard-library `unittest` and `doctest` modules offer more advanced testing tools, which you can explore later.

The `__name__` test also suits files that work as both command-line utilities and tool libraries. Suppose you write a file-finder script. Package its logic in functions. Then add a `__name__` test that calls those functions when the file runs standalone. The script's code can then be reused in other programs.

Note: do not confuse the `__main__` check with the `__main__.py` file from the package section above. That file runs an entire package folder as a program. The `__name__` check gives one file two roles. Python often reuses the same names for different purposes, and this is one case.

### Example: unit tests with `__name__`

Earlier examples had self-test code that printed output on every import. Take the `minmax` function that returns the smallest or largest value from a set of arguments. Its original version looks like this:

```
def minmax(test, *args):
    res = args[0]
    for arg in args[1:]:
        if test(arg, res):
            res = arg
    return res
def lessthan(x, y): return x < y
def grtrthan(x, y): return x > y
print(minmax(lessthan, 4, 2, 1, 5, 6, 3)) # Self-test code
print(minmax(grtrthan, 4, 2, 1, 5, 6, 3))
```

The self-test calls are handy. The problem is that their output appears whenever another file imports this module as a tool. Wrap the self-test calls in a `__name__` check, so they run only for a top-level script. The improved module follows:

```
print('I am:', __name__)
def minmax(test, *args):
    res = args[0]
    for arg in args[1:]:
        if test(arg, res):
            res = arg
    return res
def lessthan(x, y): return x < y
def grtrthan(x, y): return x > y
if __name__ == '__main__':
    print(minmax(lessthan, 4, 2, 1, 5, 6, 3)) # Self-test code
    print(minmax(grtrthan, 4, 2, 1, 5, 6, 3))
```

The first line prints `__name__` to trace its value. You would not do that in a real library module. Python sets this variable as soon as it starts loading a file. Run as a top-level script, the name is `__main__`, so the self-test code starts on its own:

```
$ python3 minmax.py
I am: __main__
1
6
```

Import the file, and the name is not `__main__`. You must call the function yourself:

```
$ python3
>>> import minmax
I am: minmax
>>> minmax.minmax(minmax.lessthan, *'hack')
'a'
```

Either way, the code serves two roles. It works as a library of tools or as an executable program. It is a buy-one-get-one-free arrangement.

You will also see programs route program-mode runs into a function named `main`:

```
def main():
...
if __name__ == '__main__':
main()
```

This works, but it adds extra code. Python gives no special meaning to a function named `main`, unlike some other languages that may have inspired this pattern.

## The `as` extension for `import` and `from`

The `as` clause is a small convenience for both `import` and `from`. It renames a name that your script imports. This extends the name-collision idea from earlier in this course. An `import` with `as` looks like this:

```
import modulename as name # And use name, not modulename
```

That line is equal to three statements. The module gets a new name in the importer's scope only. Other files still know it by its original name. The original name is dropped from the importer's scope:

```
import modulename # Run a normal import
name = modulename # Rename the module - here
del modulename # Discard the original name - here
```

After an `import` with `as`, you must use the name after `as` to reach the module. The longer form works because modules are first-class objects. You can pass them around like functions.

The `as` clause also works with `from`. It assigns a name imported from a file to a different name in the importer's scope. You get only the new name:

```
from modulename import attrname as name # And use name, not attrname
```

That is the same as these three statements:

```
from modulename import attrname
name = attrname
del attrname
```

Programmers use `as` for two main jobs. One is a shorter synonym for a long name. The other is avoiding a clash when a normal import would overwrite a name you already use:

```
import reallylongmodulename as name # Use shorter nickname
name.func() # Rename to make shorter
from module1 import utility as util1 # Can have only one "utility"
from module2 import utility as util2 # Rename to make unique
util1(); util2()
```

The `as` clause also gives a short name to a long directory path. That helps when you use the package imports from the package section:

```
import dir1.dir2.mod as mod # Only list full path once
mod.func() # Only one change if path changes
from dir1.dir2.mod import func as modfunc # Rename to make unique if needed
modfunc() # Allow func to be something else
```

Finally, `as` hedges against library changes. If a new release renames a module your code uses heavily, rename it back on import. Your code keeps working while you update it at your own pace:

```
import newname as oldname
from library import newname as oldname
...and keep happily using oldname until you have time to update all your code...
```

That said, software changes are rarely just name changes.

## Module introspection

How does a tool list every name in a module it has never seen? Modules expose most of their useful properties as built-in attributes. That makes it easy to write programs that manage other programs. Tools like this are called metaprograms, because their subject is other programs. The field is called introspection, since programs can see and process object internals. It is an advanced feature, but it helps you build programming tools.

To fetch a module's attribute value, you can qualify the name. You can also index the module's attribute dictionary through the built-in `__dict__` attribute. Python's `vars` built-in is another way to reach `__dict__`. The `sys.modules` dictionary records all loaded modules by their import-name string. The `getattr` built-in fetches an attribute from a string name at runtime.

All of these expressions reach the same object, the attribute `name` in module `M`, after importing `M` and `sys`:

```
M.name # Qualify object by attribute
M.__dict__['name'] # Index namespace dictionary manually
vars(M)['name'] # Namespace dictionary alternative
sys.modules['M'].name # Index loaded-modules table manually
getattr(M, 'name') # Call built-in fetch function
sys.modules['M'].__dict__['name'] # Module and attribute name strings
```

A demo with `minmax` uses chained comparisons. Each side reaches the same function:

```
>>> import minmax, sys
>>> (minmax.lessthan
is minmax.__dict__['lessthan'] is vars(minmax)['lessthan']
is sys.modules['minmax'].lessthan is getattr(minmax, 'lessthan')
is sys.modules['minmax'].__dict__['lessthan'])
True
```

The first form is the easiest to read and type. The others support generic access, which matters for tools.

### Example: listing modules with `__dict__`

Python's internals make it possible to build programs about programs. `mydir.py` uses these ideas. The module offers a customized and expanded version of the built-in `dir` function. Its `listing` function takes a module object. It prints a formatted view of the module's namespace, sorted by attribute name.

```
"""
mydir.py: a module that lists the namespaces of other modules.
Import this module's listing and pass an imported module, or
run this file as a script to perform its self-test code.
"""
sepchr = '-'
seplen = 60
def listing(module, verbose=True, unders=True):
    """
    List module: just attributes if verbose=False,
    hide built-in __X__ attributes if unders=False.
    """
    sepline = sepchr * seplen
    if verbose:
        print(sepline)
        print(f'name: {module.__name__}\nfile: {module.__file__}')
        print(sepline)
    # Scan namespace keys
    for (count, attr) in enumerate(sorted(module.__dict__)):
        prefix = f'{count + 1:02d}) {attr}'
        if attr.startswith('__'):
            if unders:
                print(prefix, '<built-in name>') # Skip __file__, etc.
        else:
            print(prefix, getattr(module, attr)) # Or module.__dict__[attr]
    if verbose:
        print(sepline)
        print(f'{module.__name__} has {count + 1} names')
        print(sepline)
if __name__ == '__main__':
    import mydir
    listing(mydir) # Self-test code: list myself
```

The docstrings matter here. Because this is a general tool, its docstrings give help text through `help` and the PyDoc browser. Those tools use the same introspection methods. The bottom of the file imports and lists itself. Run it as a script to see the output:

```
$ python3 mydir.py
------------------------------------------------------------
name: mydir
file: /Users/me/…/LP6E/Chapter25/mydir.py
------------------------------------------------------------
01) __builtins__ <built-in name>
02) __cached__ <built-in name>
03) __doc__ <built-in name>
04) __file__ <built-in name>
05) __loader__ <built-in name>
06) __name__ <built-in name>
07) __package__ <built-in name>
08) __spec__ <built-in name>
09) listing <function listing at 0x1077758a0>
10) sepchr -
11) seplen 60
------------------------------------------------------------
mydir has 11 names
------------------------------------------------------------
```

To list other modules, pass them to the function as objects. The function works with any object that has `__name__`, `__file__` and `__dict__` attributes. Here it lists itself, then the `tkinter` GUI module from the standard library:

```
>>> from mydir import listing
>>> import mydir, tkinter
>>> listing(mydir, unders=False, verbose=False)
09) listing <function listing at 0x10800fba0>
10) sepchr -
11) seplen 60
>>> listing(tkinter, unders=False)
------------------------------------------------------------
name: tkinter
file: /…/lib/python3.12/tkinter/__init__.py
------------------------------------------------------------
01) ACTIVE active
02) ALL all
03) ANCHOR anchor
04) ARC arc
...more names omitted...
166) re <module 're' from '/…/lib/python3.12/re/__init__.py'>
167) sys <module 'sys' (built-in)>
168) types <module 'types' from '/…/lib/python3.12/types.py'>
169) wantobjects 1
------------------------------------------------------------
tkinter has 169 names
------------------------------------------------------------
```

You will meet `getattr` and its relatives again later. The main point is that `mydir` is a program that browses other programs. Because Python exposes its internals, you can process objects in a generic way.

Note: you can preload tools such as `mydir.listing`, or a reloader you write, into the REPL. Import them in a file named by the `PYTHONSTARTUP` environment variable. Code in that startup file runs in the interactive namespace, so common imports save typing.

## Importing modules by name string

Type a module name at a prompt and pass it to `import`, and Python refuses. The statement wants a name it can read, not a string it has to evaluate. That is the awkward corner this section handles. Often a program gets a module name as a string at runtime. The string might come from a user's menu choice, or from parsing an XML document. You cannot pass such a string to an `import` statement directly. Python expects a variable name that it reads literally, not an evaluated string or expression:

```
>>> import 'string'
SyntaxError: invalid syntax
```

Assigning the string to a variable does not help either:

```
>>> x = 'string'
>>> import x
ModuleNotFoundError: No module named 'x'
```

Here Python tries to import a file named `x.py`, not the `string` module. In an `import` statement, the name both identifies the file and becomes the variable that holds the module.

### Running code strings

To load a module from a string built at runtime, use a tool that runs code. The most general approach builds an `import` statement as a string and passes it to the `exec` built-in function:

```
>>> modname = 'string'
>>> exec('import ' + modname) # Run a string of code
>>> string # Imported in this namespace
<module 'string' from '/…/lib/python3.12/string.py'>
```

You have seen `exec` and its expression cousin `eval` before. The `exec` function compiles a string of code and hands it to the interpreter. The bytecode compiler is available at runtime, so programs can build and run other programs. By default, `exec` runs the code in the current scope, as if you had pasted it there. You can pass namespace dictionaries to control the scope. `exec` also carries security risks. Those risks matter less when you build the code string yourself.

### Direct calls: two options

The main drawback of `exec` is that it compiles the `import` statement each time it runs. Compiling can be slow. The `compile` built-in can precompile a string that runs many times. In most cases, though, the `__import__` built-in is simpler and often faster. It imports from a name string and returns the module object. Assign the result to a name to keep it:

```
>>> modname = 'string'
>>> string = __import__(modname)
>>> string
<module 'string' from '/…/lib/python3.12/string.py'>
```

Imports work by invoking `__import__`, so this loads the named module normally.

The standard-library `importlib.import_module` call does the same job. Python's documentation describes it as a simpler wrapper around `__import__` for everyday use:

```
>>> import importlib
>>> modname = 'string'
>>> string = importlib.import_module(modname)
>>> string
<module 'string' from '/…/lib/python3.12/string.py'>
```

Both calls work the same way in their basic roles. Read the Python manuals for their advanced arguments. Python's docs seem to prefer the `importlib` call for name strings. Either call works, and the import system changes often.

Both calls also work with package paths. They differ in what they return. `__import__` returns the leftmost component of a package path. `importlib.import_module` returns the last one. This is their most important difference:

```
>>> import importlib
>>> __import__('email.message')
<module 'email' from '/…/lib/python3.12/email/__init__.py'>
>>> importlib.import_module('email.message')
<module 'email.message' from '/…/lib/python3.12/email/message.py'>
```

The `importlib` call also handles a package-relative import string with leading dots. You must pass the package path that the import resolves from as a second string. Package imports come from the package section above.

## Transitive module reloads

This section builds a larger tool that combines several topics from this chapter. A reload picks up code changes without a restart. Earlier, you saw that a reload updates only the module you pass in. It does not reload the modules that module imports.

Suppose you reload module `A`, and `A` imports `B` and `C`. The reload applies only to `A`, not to `B` and `C`. The import statements inside `A` run again. They fetch the already loaded `B` and `C` objects, so they do nothing new. In abstract code, `A.py` looks like this:

```
# A.py
import B # Not reloaded when A is!
import C # Just imports of already loaded modules: no-ops
$ python3
>>> …import and use A…
>>> from importlib import reload
>>> reload(A)
```

By default, you cannot depend on reloads to update every module in a program. You must call `reload` on each subcomponent. Large systems make this slow to test interactively. You can add `reload` calls in parent modules such as `A`, but that makes the code more complex.

### A recursive reloader

A better approach is a general tool that reloads transitively. It scans a module's `__dict__` attributes and checks each value's `type`. When it finds a nested module, it reloads that module too. The tool calls itself recursively to walk import chains of any depth. The pieces come from earlier topics. The `__dict__` attribute holds a module's namespace. Recursion comes from the functions section. The `type` call checks an object's kind.

The module `reloadall.py` defines `reload_all`. It reloads a module, every module it imports, and so on down each chain. It keeps a dictionary of reloaded modules. Recursion walks the import chains. The standard library's `types` module predefines type results for built-in types such as modules. The `visited` dictionary avoids repeats when imports are recursive or redundant. Module objects can serve as dictionary keys. A set would work too.

```
"""
reloadall.py: transitively reload nested modules.
Call reload_all with one or more imported modules as arguments.
These modules, and all the modules they import, are reloaded.
"""
import types
from importlib import reload
def status(module):
    print('reloading', module.__name__)
def tryreload(module):
    try:
        reload(module) # Imports might fail
    except:
        print('FAILED:', module)
def transitive_reload(module, visited):
    if not module in visited: # Trap cycles, duplicates
        status(module) # Reload this module
        tryreload(module) # And visit children
        visited[module] = True
        for attrobj in module.__dict__.values(): # For all attrs in mod
            if type(attrobj) == types.ModuleType: # Recur if nested module
                transitive_reload(attrobj, visited)
def reload_all(*args):
    visited = {} # Main entry point
    for arg in args: # For all passed in
        if type(arg) == types.ModuleType:
            transitive_reload(arg, visited)
def tester(reloader, modname): # Self-test: cmd or passed
    import importlib, sys # Imports for tests only
    if len(sys.argv) > 1: # Command-line argument?
        modname = sys.argv[1]
    module = importlib.import_module(modname) # Import by name string
    reloader(module) # Test passed-in reloader
if __name__ == '__main__':
    tester(reload_all, 'reloadall') # Test: reload self or arg
```

The module uses several tools you have seen. The `__name__` test runs self-test code only for a top-level script. The `tester` function reads `sys.argv` for command-line arguments. It uses `importlib` to import a module by name string.

The `tryreload` function wraps `reload` in a `try` statement. Reloads can fail for many reasons, so defensive code is wise with system interfaces. For example, a `monitoring` module added to `sys` in Python 3.12 cannot be reloaded. Without the `try`, that module would crash the reloader. The `try` statement was previewed earlier and is covered in full later in the course.

### Testing recursive reloads

To use the module normally, import `reload_all` and pass in an already loaded module object. That works just like the built-in `reload`. Pass a module from a top-level `import`. Modules that you reach only through `from` do not apply. The `sys.modules` lookups work too.

To test it standalone, run the file. Its `tester` function runs a reloader on a module imported by name string. The name comes from a command-line argument if one is present. Otherwise it uses the default name. With no arguments, the module reloads itself and the standard `types` module:

```
$ python3 reloadall.py
reloading reloadall
reloading types
```

With a command-line argument, the tester reloads the named module. The next run reloads a benchmark module kept in another folder of example code, which must be on `PYTHONPATH`. Copying files is poor practice, and running from that other folder does not help, because this script's folder is home. Pass a module name, not a filename. The script imports the module through the search path, so the `.py` extension is omitted:

```
$ pwd # In Chapter 25's code folder
/Users/me/…/LP6E/Chapter25
$ export PYTHONPATH=../Chapter21 # Extend path: your shell may vary
$ python3 reloadall.py pybench # Import+reload Chapter 21 module
reloading pybench
reloading sys
reloading sys.monitoring
FAILED: <module 'sys.monitoring'>
reloading os
reloading abc
reloading stat
reloading posixpath
reloading genericpath
reloading time
reloading timeit
reloading gc
reloading itertools
```

The reloader is most useful in the REPL. It works like `reload`, but it adds recursive reloads for each module passed in. Here it reloads standard-library modules:

```
$ python3
>>> from reloadall import reload_all # Reload stdlib modules in REPL mode
>>> import os, tkinter
>>> reload_all(os)
reloading os
reloading abc
reloading sys
reloading sys.monitoring
FAILED: <module 'sys.monitoring'>
reloading stat
reloading posixpath
reloading genericpath
>>> reload_all(tkinter)
reloading tkinter
reloading collections
reloading collections.abc
…etc…
reloading _sre
reloading functools
reloading copyreg
```

The reloader also works on packages, in either mode. Here it reloads the standard library's `email` package:

```
$ python3 reloadall.py email.message # Import+reload a stdlib package
reloading email.message
reloading binascii
reloading re
…etc…
$ python3
>>> from reloadall import reload_all # Same, but in REPL mode
>>> import email.message
>>> reload_all(email.message)
reloading email.message
reloading binascii
reloading re
…etc…
```

The next example runs the reloader on the `dir1.dir2.mod` path from the basic package section. Every item on the path is reloaded from the package root. The `sys.path` change gives the REPL access to another chapter's code folder, much like `PYTHONPATH`:

```
>>> import sys
>>> sys.path.append('../Chapter24') # Extend the search path manually
>>> import dir1.dir2.mod # A package in Chapter 24's folder
Running dir1.__init__.py
Running dir1.dir2.__init__.py
Loading dir1.dir2.mod
>>> reload_all(dir1) # Reloads all on path: mods in mods
reloading dir1
Running dir1.__init__.py
reloading dir1.dir2
Running dir1.dir2.__init__.py
reloading dir1.dir2.mod
Loading dir1.dir2.mod
```

A simple session shows the difference between a normal reload and a transitive one. Three files import each other in a chain:

```
# File ra.py
import rb
X = 1
# File rb.py
import rc
Y = 2
# File rc.py
Z = 3
$ python3
>>> import ra
>>> ra.X, ra.rb.Y, ra.rb.rc.Z # Three-level import chain
(1, 2, 3)
```

Now change all three files' values without stopping Python, save them, and reload in the REPL:

```
>>> from importlib import reload
>>> reload(ra) # Built-in reload is top-level only
<module 'ra' from '/…/LP6E/Chapter25/ra.py>
>>> ra.X, ra.rb.Y, ra.rb.rc.Z
(111, 2, 3)
>>> from reloadall import reload_all
>>> reload_all(ra) # Normal usage mode
reloading ra
reloading rb
reloading rc
>>> ra.X, ra.rb.Y, ra.rb.rc.Z # Reloads all nested modules too
(111, 222, 333)
```

The built-in `reload` changed only `ra`. The transitive reloader updated the nested modules too. Study the reloader's code and its results to see how it works.

### Alternative codings

Some readers prefer recursion, and the next module shows a recursive alternative. `reloadall2.py` uses a set instead of a dictionary to detect repeats and cycles. It is slightly more direct because it drops the top-level loop. It also shows recursive coding in general. This module extends the original and replaces only the parts that vary. It imports `tester` from the original and passes in its own `reload_all`. That makes sure this reloader runs in standalone mode.

```
"""
reloadall2.py: transitively reload nested modules.
Alternative coding: recursive, refactored.
"""
import types
from reloadall import status, tryreload, tester
def transitive_reload(objects, visited):
    for obj in objects:
        if type(obj) == types.ModuleType and obj not in visited:
            status(obj)
            tryreload(obj) # Reload this, recur to attrs
            visited.add(obj)
            transitive_reload(obj.__dict__.values(), visited)
def reload_all(*args):
    transitive_reload(args, set())
if __name__ == '__main__':
    tester(reload_all, 'reloadall2') # Test: reload myself or arg
```

The functions section covered recursive functions. An explicit stack or queue can replace recursion, which sometimes suits a context better. `reloadall3.py` is a nonrecursive transitive reloader. It uses a stack instead of recursion, and a set to skip repeats and cycles. For each module, it pushes all attribute values onto the end of the `objects` stack. Those values are filtered later. The loop repeats until no candidates remain. A generator expression could filter out nonmodules in the `extend` call, but that would be more complex.

```
"""
reloadall3.py: transitively reload nested modules.
Alternative coding: nonrecursive, explicit stack.
"""
import types
from reloadall import status, tryreload, tester
def transitive_reload(objects, visited):
    while objects:
        next = objects.pop() # Delete next item at end
        if (type(next) == types.ModuleType # Is it a module object?
            and next not in visited): # Not already reloaded?
            status(next) # Reload this, push attrs
            tryreload(next)
            visited.add(next)
            objects.extend(next.__dict__.values())
def reload_all(*args):
    transitive_reload(list(args), set())
if __name__ == '__main__':
    tester(reload_all, 'reloadall3') # Test: reload myself or arg
```

This version pops and pushes items at the end of its list, so it is stack-based. The order of pushes and dictionary values sets the order of reloads. It visits submodules in namespace dictionaries from right to left. The recursive versions go left to right. You could reverse `values` to match. Reload order does not matter here.

### Testing reload variants

To prove the two alternatives match the original, test all three. Each module shares a common `tester` function. Run each with no arguments to reload itself, or with a module name to reload that module:

```
$ python3 reloadall.py
reloading reloadall
reloading types
$ python3 reloadall2.py
reloading reloadall2
reloading types
$ python3 reloadall3.py
reloading reloadall3
reloading types
```

Each run tests a different reloader, though the output looks alike. Each test passes the `reload_all` from its own file to the shared tester. Here the variants reload the `tkinter` GUI module and every module it reaches. The third variant's order differs:

```
$ python3 reloadall.py tkinter
reloading tkinter
reloading collections
reloading collections.abc
…etc…
$ python3 reloadall2.py tkinter
reloading tkinter
reloading collections
reloading collections.abc
…etc…
$ python3 reloadall3.py tkinter
reloading tkinter
reloading re
reloading copyreg
…etc…
```

You can test interactively too. Import the reloaders and call either the main entry point with a module object, or the tester with a reloader and a module name string:

```
$ python3
>>> import reloadall, reloadall2, reloadall3
>>> import tkinter
>>> reloadall.reload_all(tkinter) # Normal use case
reloading tkinter
reloading collections
reloading collections.abc
…etc…
>>> reloadall.tester(reloadall2.reload_all, 'tkinter') # Testing utility
reloading tkinter
reloading collections
reloading collections.abc
…etc…
>>> reloadall.tester(reloadall3.reload_all, 'reloadall3') # Mimic self-test code
reloading reloadall3
reloading types
```

The third reloader's order can vary. Reload order depends on namespace dictionary ordering. Dictionaries keep keys in insertion order. The stack version also depends on the order that items enter its stack. To check that all three reload the same modules in any order, compare their messages as sets or sorted lists. This session runs the scripts with `os.popen`:

```
>>> import os
>>> res1 = os.popen('python3 reloadall.py tkinter').readlines()
>>> res2 = os.popen('python3 reloadall2.py tkinter').readlines()
>>> res3 = os.popen('python3 reloadall3.py tkinter').readlines()
>>> res1[:3]
['reloading tkinter\n', 'reloading collections\n', 'reloading collections.abc\n']
>>> res3[:3]
['reloading tkinter\n', 'reloading re\n', 'reloading copyreg\n']
>>> res1 == res2, res2 == res3
(True, False)
>>> set(res2) == set(res3) # Order-neutral equality
True
>>> sorted(res2) == sorted(res3) # Ditto
True
```

Run these scripts, study them, and experiment. They are the kind of importable tools you might keep in your own code library. The class tree listers in a later chapter use a similar testing technique.

### Caveats of transitive reloads

All the transitive reloaders depend on how `reload` works. A reload updates the module object in place. Every reference to that module sees the new version, so a transitive reload works. A `from` importer copies names out, though. Those copies do not update after a reload, transitive or not. Modules imported only through `from` also miss out. They never appear in an importer's namespace, so the scan cannot find them. Fixing that may require source-code analysis or import customization.

This is another reason to prefer `import` over `from`. The next section covers the common gotchas for this topic.

## Module gotchas

The import bugs that hurt most are usually not deep. A name clash, or an import that ran before a name existed, is enough to end the afternoon. This section covers the boundary cases that trip up Python learners. Some repeat earlier points. A few are so obscure that good examples are hard to find. Most show something important about the language.

### Module name clashes

If two modules share a name, you may be able to import only one. By default, Python picks the one in the leftmost directory on `sys.path`. Your top-level script's folder is always first, so a module there wins automatically. Across directories, the linear search path means same-named files can clash.

The fix is to avoid same-named files. If you truly need both, use the package imports from the package section. Put each file in a subdirectory, so the package directory names make each reference unique. As long as the enclosing package names differ, you can reach either or both modules.

A similar problem happens when your own module shares a name with a standard-library module you need. Your local module in the home directory, or in another early folder on the path, can hide the library module. Avoid reusing standard-library names. Or store your modules in a package and use package-relative imports. In that model, normal imports skip the package folder and reach the library's version. Special dotted imports can still select the local one.

### Statement order matters in top-level code

When Python first imports a module, or later reloads it, it runs the statements one by one from top to bottom. That has some subtle effects on forward references:

- Top-level code, which is not nested in a function, runs as soon as Python reaches it during an import. It cannot reference names assigned lower in the file.
- Code inside a function body does not run until the function is called. Names inside a function resolve only when the function runs. They can usually refer to names anywhere in the file.

Forward references matter mainly for top-level code that runs right away. Functions can reference names at any point. This file shows the dos and don'ts:

```
func1() # Error: func1 not yet assigned
def func1():
    print(func2()) # OK: func2 looked up later
func1() # Error: func2 not yet assigned
def func2():
    return "Hello"
func1() # OK: func1 and func2 assigned
```

When this file is imported or run as a program, Python runs it from top to bottom. The first call to `func1` fails, because its `def` has not run yet. The call to `func2` inside `func1` works once `func2`'s `def` has run. At the second top-level call, it has not. The last call works because both functions are assigned.

Mixing `def` statements with immediate code is hard to read, and it depends on statement order. As a rule of thumb, put your `def` statements at the top of the file. Put top-level code at the bottom. Then every function is defined before the code that uses it.

### `from` copies names but does not link

The `from` statement assigns names in the importer's scope. It copies names rather than aliasing them. That matters most for names that live in different files. Consider the simple module `nested.py`:

```
X = 99
def printer(): print(X)
```

If another module, or the REPL, imports these names with `from`, it gets copies. Changing a name in the importer resets only the local copy. The name in `nested.py` does not change:

```
>>> from nested import X, printer # Copy names out
>>> X = 88 # Changes my X only!
>>> printer() # nested1's X is still 99
99
```

If you use `import` instead and assign to a qualified name, you change the module's loaded image. The attribute qualifier points at the name in the module object, not in the importer:

```
>>> import nested # Get module as a whole
>>> nested.X = 88 # Change nested1's X
>>> nested.printer()
88
```

The takeaway: changing a name obtained with `from` affects no other module. Changing a mutable object shared through a `from` copy can affect other modules, though. Only the name rebinding stays local.

### `from *` can obscure the meaning of variables

The `from *` form does not list the names it imports. It can silently overwrite names already in your scope. It also hides where a variable came from. This gets worse when `from *` is used on more than one module:

```
>>> from module1 import * # May overwrite names silently
>>> from module2 import * # No way to tell what we get
>>> from module3 import * # No way to see name origins
>>> func() # Huh?
```

With three modules, you cannot tell what `func` means without searching all three files. Those files may live in other directories.

The fix is simple. List the names you want in most `from` statements. Use at most one `from *` per file. Then any undefined name must come from the one module named in that `from *`. You can avoid the problem entirely by using `import` everywhere. That advice is too strict. `from` is handy when used wisely. Collecting names into one well-known module for convenience is acceptable.

### `reload` may not affect `from` imports

`from` copies names when it runs. It keeps no link back to the source module. An imported name simply refers to the object that the source name referenced at that time. So reloading the source module does nothing for clients that imported the name with `from`:

```
from module import X # X may not reflect any module reloads
…
from importlib import reload
reload(module) # Changes module, but not my names
X # Still references old object!
```

Use `import` and name qualification to fix this. A qualified name always goes back to the module. After a reload, it finds the new bindings that the reload updated in place:

```
import module # Get module, not names
…
from importlib import reload
reload(module) # Changes module in place
module.X # Get current X: reflects module reloads
```

This is why the transitive reloader above does not update names fetched with `from`, only those fetched with `import`. If you plan to reload, use `import`.

### `reload`, `from`, and interactive testing

The problem is more subtle than it looks. Earlier in this course, you saw that launching programs through imports and reloads is often a bad idea. The complexity grows when `from` joins in. Beginners often hit these issues while testing in an interactive session. Imagine you open a module in a text editor. You then load it with `from` in a session to test it:

```
from module import function
function(1, 2, 3)
```

You find a bug and edit the file. Then you try to reload the module that way:

```
from importlib import reload
reload(module)
```

That fails. The `from` statement bound only the name `function`, not `module`. To reload, you must first bind the module name with an `import` at least once:

```
from importlib import reload
import module
reload(module)
function(1, 2, 3)
```

This still does not work. `reload` updates the module object in place. But names copied out earlier, such as `function`, still point to the old objects. `function` is still the original version. To use the new function, refer to `module.function` after the reload. Or rerun the `from`:

```
from importlib import reload
import module
reload(module)
from module import function # Or give up and use module.function()!
function(1, 2, 3)
```

The new function finally runs. Getting there takes a lot of work, though. You must remember to reload after imports, and to rerun your `from` statements after reloads. In Python 3, you must also import `reload` itself. That is complex enough to trip up experts now and then.

The short story: do not expect `reload` and `from` to work together. Avoid combining them. Use `reload` with `import`. Or launch your programs another way. Options include IDLE's menu commands, clicking a file icon, the system command line, the `exec` built-in, or other methods from the early chapters.

### Recursive `from` imports may not work

This is the most bizarre gotcha, and luckily an obscure one. Imports run a file's statements from top to bottom. Be careful when modules import each other. People call this a recursive import, but the recursion does not really happen. A circular import is a better name. Such imports do not loop forever. A module's statements may not all have run when it imports another module, though. So some of its names may not exist yet.

If you use `import` to fetch the whole module, this usually does not matter. You access its names later, and by then the module is complete. If you use `from` to fetch specific names, only names already assigned at that point are available during a recursive import.

Consider `recur1` and `recur2` in Examples 25-11 and 25-12:

```
X = 1
import recur2 # Run recur2 now if it doesn't exist
Y = 2
```

```
from recur1 import X # OK: X already assigned
from recur1 import Y # Error: Y not yet assigned
```

Module `recur1` assigns `X`, then imports `recur2`, then assigns `Y`. The `recur2` module can fetch `recur1` as a whole with `import`. The module is already in the `sys.modules` table, so the import works and does not loop. But `recur2` uses `from`. It can see only `X`. The name `Y` is assigned below the import, so it does not exist yet:

```
$ python3
>>> import recur1
ImportError: cannot import name 'Y' from partially initialized module 'recur1'
(most likely due to a circular import) (/…/LP6E/Chapter25/recur1.py)
```

Python avoids rerunning `recur1`'s statements during the recursive import. Otherwise the imports would loop forever. But `recur1`'s namespace is incomplete when `recur2` imports it.

The solution: avoid `from` in recursive imports. Python will not get stuck in a cycle with `from`, but your program will depend on the order of statements. There are two ways out of this gotcha:

- Eliminate import cycles with careful design. Maximize cohesion and minimize coupling, as described at the start of this chapter.
- If you cannot break the cycles, delay name access. Use `import` with attribute qualification instead of `from` with direct names. Or place your `from` statements inside functions, or near the bottom of the file.

### Recap of advanced module topics

This chapter covered data hiding, the `__future__` module, the `__name__` usage-mode variable, transitive reloads, and importing by name string. It also covered module design and common mistakes. Those mistakes are worth knowing so you can avoid them. Classes come next. They live in modules and are namespaces too. They add one more step to attribute lookup, called inheritance search.

## Practice exercises

These exercises build on this chapter. Try them in a scratch folder.

1. **Import basics.** Write a module called `mymod.py` that counts lines and characters in a file, much like part of the Unix `wc` command. It should export three top-level names:
   - A `countLines(name)` function that reads the file named by `name` and counts its lines. Hint: `file.readlines` does most of the work, and `len` finishes the job. A `for` loop over the file works better for very large files.
   - A `countChars(name)` function that counts characters in the file. Hint: `file.read` returns one string, which you can measure.
   - A `test(name)` function that calls both counting functions on a given filename. The filename might be passed in, hardcoded, typed by a user with `input`, or read from `sys.argv`. For now, assume a passed-in argument.

   Each function should take a filename string. If your functions run more than two or three lines each, you are working too hard. Use the hints.

2. **Test interactively.** Import `mymod` and use attribute references to reach its exports. Does `PYTHONPATH` need the folder that holds `mymod.py`? Run the module on itself with `test('mymod.py')`. The `test` function opens the file twice. To improve that, pass an open file object to both counters. Hint: `file.seek(0)` rewinds a file.

3. **`from` and `from *`.** Test `mymod` interactively. Use `from` to load its exports by name first. Then use `from *` to fetch everything.

4. **`__main__`.** Add a line to `mymod` that calls `test` only when the module runs as a script. Test the value of `__name__` for `'__main__'`. Run the module from the command line, then import it and test its functions interactively. Does it work in both modes?

5. **Nested imports.** Write a second module, `myclient.py`, that imports `mymod` and tests its functions. Run `myclient` from the command line. If `myclient` uses `from` to fetch from `mymod`, can you reach `mymod`'s functions at the top level of `myclient`? What if it uses `import`? Try both versions. Then import `myclient` and inspect its `__dict__`.

6. **Package imports.** Create a subdirectory called `mypkg` inside a folder on your import search path. Move or copy `mymod.py` into it. Import it with a package import of the form `import mypkg.mymod`, then call its functions. Try fetching the counter functions with `from` too. This works on all platforms, which is part of why Python uses `.` as a path separator. If the package folder sits in your working directory, the home directory finds it, and you need no path settings. An `__init__.py` file is optional here. Add one with basic `print` calls to see whether it runs on each import or reload. Then copy `mymod.py` to the folder's `__main__.py` and run the folder. Does that make sense here? Can you still run the nested `mymod.py` itself?

7. **Reloads.** Repeat the reload experiment with `changer.py` from the reload example earlier in this chapter. Change the function's message or behavior several times without stopping the REPL. You can edit `changer` in another window. Or suspend the interpreter and edit in the same window. On Unix, `Ctrl+Z` suspends a process, and `fg` resumes it.

8. **Circular imports.** Earlier, importing `recur1` raised an error. Restart Python and import `recur2` interactively. The error does not occur. Why does importing `recur2` work, but not `recur1`? Hint: Python records a new module before it runs the module's code. Later imports fetch the module first, whether or not it is complete. Next, run `recur1` as a top-level script with `python3 recur1.py`. Do you get the same error as before? Why? Hint: a script is not imported, so this case matches importing `recur2` first. What happens when you run `recur2` as a script? Circular imports are uncommon in practice. Understanding why they cause trouble, though, teaches you a lot about import semantics.

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
11. **What is the purpose of an `__init__.py` file in a package directory?** It declares and initializes a regular package. Python runs its code the first time a program imports through the folder. Its assigned variables become attributes of the folder's module object. The file is optional, but it gives the folder search precedence over same-named folders that lack it.
12. **How can you avoid repeating a package's full path each time you use its contents?** Use `from` to copy names out of the package directly. Or pair `as` with `import` to give the path a shorter alias. Either way, the full path appears just once.
13. **Which directories require `__init__.py` files?** None strictly. Earlier Python versions required them. Namespace packages made them optional. They still have valid roles, such as raising a folder's search precedence.
14. **When must you use `import` instead of `from` with packages?** Only when you need the same name from more than one path. With `import`, the path keeps each reference unique. A `from` statement allows just one version of a given name, unless you rename it with `as`.
15. **What is the difference between `from pkg import name` and `from . import name`?** The first is an absolute import. It skips the enclosing package and searches the folders on `sys.path`. The second is a relative import. It looks up `name` only within the package that contains the statement.
16. **What is a namespace package?** It is one or more folders that have no `__init__.py` file. When an import search finds no simple module or regular package first, Python builds a namespace package. It is the virtual concatenation of all found folders with the requested name. Further nested parts are looked up in all of its folders.

17. **What is significant about top-level module variables whose names begin with a single underscore?** They are not copied out when a client uses `from *`. The `import` and normal `from` forms can still reach them. The `__all__` list works in the opposite direction, naming the only names that `from *` copies.
18. **What does it mean when a module's `__name__` is `'__main__'`?** The file runs as a top-level script, not as an import. It works as a program rather than a library, so its dual-mode code runs.
19. **How can you step through all the attributes of a module with a loop?** Loop over the module's `__dict__` attribute. Attribute values can also be fetched by string name, using indexing or the `getattr` built-in.
20. **If a user types the name of a module at a prompt, how can your code import it?** Build an import statement as a string and run it with `exec`. Or pass the string to the `__import__` built-in or to `importlib.import_module`.
21. **Can you import from the past in Python?** No. The `__future__` module only enables features that are coming. You can install an older Python, but the latest Python is generally the best choice.

## Sources and review notes

- Source: *Learning Python*, 6th edition (`learning-python-6th-edition`). Chapters used are listed in each section.
- Chapter used: 22, *Modules: The Big Picture* (book folder `learning-python-6th-edition`, chapter prefix "22. ").
- Chapter used: 23, *Module Coding Basics* (book folder `learning-python-6th-edition`, chapter prefix "23. ").
- Chapter used: 24, *Module Packages* (book folder `learning-python-6th-edition`, chapter prefix "24. ").
- Chapter used: 25, *Module Odds and Ends* (book folder `learning-python-6th-edition`, chapter prefix "25. ").
