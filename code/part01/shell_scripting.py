"""Chapter 1.9 model: Shell parameter expansion (${var#}, ${var##}, ${var%}, ${var%%},
${var:-}, ${var:=}, ${var:?}), quoting and "$@" vs $@ / "$*" word splitting,
set -euo pipefail suppression contexts, subshell vs current-shell variable scoping,
and exponential backoff retry timing.

Sources modeled:
- Brian Ward, How Linux Works, 3rd ed. (how-linux-works-3rd-edition), Chapter 11
  ("Introduction to Shell Scripts": limitations, quoting, $1/$#/$@/$0/$$/$?, shift,
  exit codes, if/elif/test, case, for/while loops, mktemp + trap INT/EXIT, here
  documents, basename/awk/sed/xargs/expr/exec, subshells, sourcing, read, and
  Kochan & Wood / Kernighan & Pike references).
- Sergey Zhumatiy, Supercomputers for Linux SysAdmins (SCL), Chapter 28 (staged
  UPS shutdown scripts) and Chapter 29 ("Shell Scripts – Basics and Common Mistakes":
  shebang and BOM, test/[ ], quoting, getopts, functions and local, parameter
  expansion shortcuts).
"""
import fnmatch
from typing import Dict, List, Optional


def evaluate_parameter_expansion(op: str, value: Optional[str], arg: str = "") -> str:
    """Simulate POSIX/bash parameter expansion operators without forking external tools."""
    if op == ":-":
        return value if (value is not None and value != "") else arg
    if op == ":=":
        return value if (value is not None and value != "") else arg
    if op == ":?":
        if value is None or value == "":
            raise ValueError(f"parameter null or not set: {arg}")
        return value
    if op == ":+":
        return arg if (value is not None and value != "") else ""
    if value is None:
        value = ""
    if op == "len":
        return str(len(value))
    if op == "##*/":
        return value.rsplit("/", 1)[-1]
    if op == "%/*":
        return value.rsplit("/", 1)[0] if "/" in value else value
    if op == "%.*":
        return value.rsplit(".", 1)[0] if "." in value else value
    if op == "##*.":
        return value.rsplit(".", 1)[-1] if "." in value else ""
    raise ValueError(f"Unsupported expansion operator: {op}")


def expand_positional_args(args: List[str], form: str) -> List[str]:
    """Compare "$@" (preserves each element), $@ (splits on whitespace), and "$*" (single joined string)."""
    if form == '"$@"':
        return list(args)
    if form == "$@":
        out: List[str] = []
        for a in args:
            out.extend(a.split())
        return out
    if form == '"$*"':
        return [" ".join(args)] if args else []
    raise ValueError(f"Unknown positional form: {form}")


def does_errexit_abort(
    cmd_exit_code: int,
    in_if_or_while_condition: bool = False,
    in_and_or_left_operand: bool = False,
    is_negated_with_bang: bool = False,
    in_function_called_in_condition: bool = False,
) -> bool:
    """Determine whether 'set -e' (errexit) aborts the script on a non-zero command exit."""
    if cmd_exit_code == 0:
        return False
    if (
        in_if_or_while_condition
        or in_and_or_left_operand
        or is_negated_with_bang
        or in_function_called_in_condition
    ):
        return False
    return True


def simulate_variable_scope(initial: int, new_val: int, construct: str) -> int:
    """Return outer shell variable value after running construct: 'subshell_parens', 'pipe_while', 'brace_group', or 'proc_subst_while'."""
    if construct in {"subshell_parens", "pipe_while"}:
        return initial
    if construct in {"brace_group", "proc_subst_while", "redirect_while"}:
        return new_val
    raise ValueError(f"Unknown shell construct: {construct}")


def compute_exponential_backoff_schedule(attempts: int, initial_delay_sec: int) -> Dict[str, object]:
    """Compute sleep schedule for the retry(attempts, initial_delay) function in Section 8."""
    if attempts < 1 or initial_delay_sec < 0:
        raise ValueError("attempts must be >= 1 and initial_delay_sec >= 0")
    delays: List[int] = []
    d = initial_delay_sec
    for _ in range(1, attempts):
        delays.append(d)
        d *= 2
    return {"attempts": attempts, "sleep_delays_sec": delays, "total_sleep_sec": sum(delays)}
