"""Chapter 3.2 model: Python module namespaces (__dict__, vars, dir),
import vs from reference copying and reload() semantics, four-step import
search algorithm (regular package vs simple module vs PEP 420 namespace
package), module-level __getattr__ and __dir__ hooks (Python 3.7+),
__import__ vs importlib.import_module on dotted package paths, and
recursive vs explicit-stack transitive module reloaders.

Sources modeled:
- Mark Lutz, Learning Python, 6th ed. (learning-python-6th-edition, LP),
  Chapters 22-25:
  * Chapter 22 ("Modules: The Big Picture"): 3-step import execution (find,
    compile to .pyc in __pycache__, run top-level code), sys.modules cache,
    5-part module search path (home dir, PYTHONPATH, stdlib, site-packages,
    .pth files), timestamp-based vs hash-based .pyc files, and module sources.
  * Chapter 23 ("Module Coding Basics"): import vs from vs from *, runtime
    assignments, shared mutable objects (share.py), module __dict__ / vars() /
    dir(), lexical scoping across files (lex1.py/lex2.py), downward attribute
    qualification paths (nest1.py -> nest2.py -> nest3.py), and reload() in-place
    namespace updates (changer.py).
  * Chapter 24 ("Module Packages"): dotted package imports (dir0/dir1/dir2/mod.py),
    __init__.py 4 roles, __main__.py bundle execution vs python3 -m, package-relative
    vs absolute imports, and PEP 420 namespace packages (__path__ virtual
    concatenation across ns/part1/sub and ns/part2/sub) with the 4-step search order.
  * Chapter 25 ("Module Odds and Ends"): _X and __all__ data hiding (unders.py,
    alls.py), module __getattr__ and __dir__ (gamod.py), __future__,
    __name__ == '__main__' (dualmode.py, minmax.py), import/from as, module
    introspection (mydir.py), dynamic imports (exec, __import__,
    importlib.import_module), transitive reloaders (reloadall.py, reloadall2.py,
    reloadall3.py), and circular import order traps (recur1.py, recur2.py).
"""
import importlib
import sys
import types
from typing import Dict, List, Sequence, Set, Tuple


def simulate_import_vs_from_and_reload() -> Dict[str, object]:
    """Model LP Ch. 23 share.py & changer.py: how `from` copies references while
    `import` qualifies through the module object, and how in-place `reload`
    updates `mod.x` without rebinding stale `from`-copied variables.
    """
    share = types.ModuleType("share")
    share.x = 1
    share.y = [1, 2]

    # Equivalent to: from share import x, y
    copied_x = share.x
    copied_y = share.y

    # Local rebinding of copied_x does not alter share.x,
    # whereas in-place mutation of copied_y mutates share.y
    copied_x = "hack"
    copied_y[0] = "hack"
    after_local_edits = (share.x, list(share.y), copied_x, list(copied_y))

    # Simulate in-place reload(share) resetting top-level assignments
    share.__dict__["x"] = "After editing"
    share.__dict__["y"] = [10, 20]

    return {
        "share_x_before_reload": after_local_edits[0],
        "share_y_before_reload": after_local_edits[1],
        "copied_x_stale_after_reload": copied_x,
        "qualified_x_after_reload": share.x,
        "qualified_y_after_reload": share.y,
    }


def resolve_four_step_import_search(
    candidate_dirs: Sequence[str],
    fs_entries: Set[str],
    name: str,
) -> Tuple[str, List[str]]:
    """Model LP Ch. 24's four-step import search algorithm across candidate_dirs:
    For each candidate directory:
      1. If <dir>/<name>/__init__.py exists -> return ('regular_package', ['<dir>/<name>/__init__.py'])
      2. If <dir>/<name>.py (or .pyc/.so) exists -> return ('simple_module', ['<dir>/<name>.py'])
      3. If <dir>/<name> is a directory (without __init__.py) -> record it and keep scanning!
      4. Otherwise continue to the next candidate directory.
    If the scan finishes without returning in step 1 or 2 and at least one
    directory was recorded in step 3, return ('namespace_package', recorded_dirs).
    Otherwise raise ModuleNotFoundError.
    """
    recorded_namespace_dirs: List[str] = []
    for d in candidate_dirs:
        pkg_init = f"{d}/{name}/__init__.py"
        if pkg_init in fs_entries:
            return ("regular_package", [pkg_init])
        for ext in (".py", ".pyc", ".so"):
            mod_file = f"{d}/{name}{ext}"
            if mod_file in fs_entries:
                return ("simple_module", [mod_file])
        bare_dir = f"{d}/{name}"
        if bare_dir in fs_entries:
            recorded_namespace_dirs.append(bare_dir)

    if recorded_namespace_dirs:
        return ("namespace_package", recorded_namespace_dirs)
    raise ModuleNotFoundError(f"No module named {name!r}")


def filter_from_star_exports(mod_dict: Dict[str, object]) -> List[str]:
    """Model LP Ch. 25 _X and __all__ precedence rules (unders.py and alls.py)
    for `from module import *`.
    """
    if "__all__" in mod_dict and mod_dict["__all__"] is not None:
        return list(mod_dict["__all__"])  # __all__ takes precedence even over _X
    return [k for k in mod_dict.keys() if not k.startswith("_")]


def build_dynamic_getattr_module() -> types.ModuleType:
    """Build LP Ch. 25 Example 25-3 (gamod.py) with module-level __getattr__ and __dir__."""
    gamod = types.ModuleType("gamod")
    code = """
var = 2

def __getattr__(name):
    match name:
        case 'test':
            return name * var
        case 'hack' | 'code':
            return name.upper()
        case _:
            raise AttributeError(f'{name} is undefined')

def __dir__():
    return ['var', 'test', 'hack', 'code']
"""
    exec(code, gamod.__dict__)
    return gamod


def compare_dunder_import_vs_import_module(dotted_name: str = "email.message") -> Dict[str, str]:
    """Model LP Ch. 25's distinction between __import__('pkg.mod') (returns leftmost
    top-level package) and importlib.import_module('pkg.mod') (returns rightmost target).
    """
    leftmost = __import__(dotted_name)
    rightmost = importlib.import_module(dotted_name)
    return {
        "dunder_import_name": leftmost.__name__,
        "import_module_name": rightmost.__name__,
    }


def list_module_namespace(
    module: types.ModuleType,
    include_dunders: bool = False,
) -> List[Tuple[str, object]]:
    """Model LP Ch. 25 Example 25-6 (mydir.py): inspect sorted(module.__dict__)."""
    items: List[Tuple[str, object]] = []
    for attr in sorted(module.__dict__):
        if attr.startswith("__") and not include_dunders:
            continue
        items.append((attr, getattr(module, attr)))
    return items


def transitive_reload_recursive(root: types.ModuleType) -> List[str]:
    """Model LP Ch. 25 Example 25-8 (reloadall2.py): recursive transitive traversal
    of nested module objects in module.__dict__.values() with a visited set.
    """
    order: List[str] = []
    visited: Set[types.ModuleType] = set()

    def _walk(objects) -> None:
        for obj in objects:
            if isinstance(obj, types.ModuleType) and obj not in visited:
                visited.add(obj)
                order.append(obj.__name__)
                _walk(obj.__dict__.values())

    _walk([root])
    return order


def transitive_reload_stack(root: types.ModuleType) -> List[str]:
    """Model LP Ch. 25 Example 25-9 (reloadall3.py): non-recursive explicit-stack
    transitive traversal using list.pop() and list.extend().
    """
    order: List[str] = []
    visited: Set[types.ModuleType] = set()
    stack: List[object] = [root]
    while stack:
        nxt = stack.pop()
        if isinstance(nxt, types.ModuleType) and nxt not in visited:
            visited.add(nxt)
            order.append(nxt.__name__)
            stack.extend(nxt.__dict__.values())
    return order
