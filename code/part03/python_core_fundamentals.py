"""Chapter 3.1 model: Python object reference and mutability/copy semantics,
floor division (//, math.floor) vs truncation (math.trunc, int), string.Template
and str.maketrans/translate, LEGB closure and mutable-default-argument behavior,
and formal parameter/call ordering.

Sources modeled:
- Mark Lutz, Learning Python, 6th ed. (learning-python-6th-edition, LP),
  Chapters 1-19 (running programs -i / import+reload vs exec, object model
  id/type/value, mutability and shallow/deep copy, numbers and floor vs
  truncation, operator precedence, strings and Template/translate, lists/dicts/
  tuples/sets, print and stream redirection, if/match/while/for-else, functions,
  LEGB scopes, closures, and argument ordering).
- Luciano Ramalho, Fluent Python, 2nd ed. (fluent-python-2nd-edition, FP),
  Chapter 6 ("Object References, Mutability, and Recycling").
- Christian Adell et al., Network Programmability and Automation, 2nd ed. (NPA),
  Chapter 6 ("Python").
- volume-02/00-python-fundamentals-for-infrastructure-masterclass.md.
"""
import copy
import math
from string import Template
from typing import Callable, Dict, List


def compare_floor_vs_trunc(numerator: int, denominator: int) -> Dict[str, object]:
    """Compare true division (/), floor division (//, math.floor), and truncation (math.trunc, int)."""
    if denominator == 0:
        raise ZeroDivisionError("denominator must be non-zero")
    true_div = numerator / denominator
    return {
        "true_div": true_div,
        "floor_div_op": numerator // denominator,
        "math_floor": math.floor(true_div),
        "math_trunc": math.trunc(true_div),
        "int_trunc": int(true_div),
    }


def demonstrate_shallow_vs_deep_copy() -> Dict[str, object]:
    """Show how shallow copy shares nested mutable lists while deepcopy isolates them."""
    original = {"rack1": ["gpu01", "gpu02"]}
    alias = original
    shallow = original.copy()
    deep = copy.deepcopy(original)

    original["rack1"].append("gpu03")
    return {
        "alias_len": len(alias["rack1"]),
        "shallow_len": len(shallow["rack1"]),
        "deep_len": len(deep["rack1"]),
        "shallow_shares_inner_list": shallow["rack1"] is original["rack1"],
        "deep_shares_inner_list": deep["rack1"] is original["rack1"],
    }


def sanitize_and_render_host_template(raw_label: str, host: str, gpus: int) -> Dict[str, str]:
    """Use str.maketrans/translate to normalize a label and string.Template to render a summary."""
    table = str.maketrans(":-", "__", " ()")
    normalized = raw_label.translate(table)
    rendered = Template("$host has ${gpus} GPUs").substitute(host=host, gpus=gpus)
    safe_partial = Template("$host has ${gpus} GPUs").safe_substitute(host=host)
    return {
        "normalized_label": normalized,
        "rendered": rendered,
        "safe_partial": safe_partial,
    }


def add_node_safe(ip: str, nodes: List[str] = None) -> List[str]:
    """Safe idiom avoiding the mutable default argument trap."""
    if nodes is None:
        nodes = []
    nodes.append(ip)
    return nodes


def make_nonlocal_counter(start: int = 0) -> Callable[[], int]:
    """Return a closure that increments and returns an enclosing counter using nonlocal."""
    n = start

    def inc() -> int:
        nonlocal n
        n += 1
        return n

    return inc
