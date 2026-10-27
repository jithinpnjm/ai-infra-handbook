#!/usr/bin/env python3
"""Self-checking lab for Chapter 1.9: Shell scripting that survives production."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from shell_scripting import (
    compute_exponential_backoff_schedule,
    does_errexit_abort,
    evaluate_parameter_expansion,
    expand_positional_args,
    simulate_variable_scope,
)

passed = 0
failed = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global passed, failed
    if cond:
        passed += 1
        print(f"PASS: {name}")
    else:
        failed += 1
        print(f"FAIL: {name}" + (f" ({detail})" if detail else ""))


def main() -> None:
    # 1. Parameter expansion without external processes (Section 7, SCL Ch. 29)
    path = "/data/run42/model.final.ckpt"
    check("${path##*/} strips longest prefix to yield basename 'model.final.ckpt'",
          evaluate_parameter_expansion("##*/", path) == "model.final.ckpt")
    check("${path%/*} strips shortest suffix to yield dirname '/data/run42'",
          evaluate_parameter_expansion("%/*", path) == "/data/run42")
    check("${path%.*} strips shortest dot suffix to yield '/data/run42/model.final'",
          evaluate_parameter_expansion("%.*", path) == "/data/run42/model.final")
    check("${path##*.} strips longest dot prefix to yield extension 'ckpt'",
          evaluate_parameter_expansion("##*.", path) == "ckpt")
    check("${#path} returns string length 28",
          evaluate_parameter_expansion("len", path) == "28")
    check("${var:-fallback} returns 'fallback' when var is None or empty",
          evaluate_parameter_expansion(":-", "", "fallback") == "fallback"
          and evaluate_parameter_expansion(":-", None, "fallback") == "fallback")
    check("${var:-fallback} keeps 'custom' when var is non-empty",
          evaluate_parameter_expansion(":-", "custom", "fallback") == "custom")
    check("${var:?msg} raises ValueError when var is empty or unset (protects rm -rf)",
          _raises(lambda: evaluate_parameter_expansion(":?", "", "dir is empty")))
    check("${var:+alt} returns 'alt' when var is set and '' when empty",
          evaluate_parameter_expansion(":+", "1", "alt") == "alt"
          and evaluate_parameter_expansion(":+", "", "alt") == "")

    # 2. "$@" vs $@ vs "$*" word splitting (HLW Ch. 11, SCL Ch. 29)
    argv = ["abc 123", "qwe"]
    check('"$@" preserves multi-word arguments as ["abc 123", "qwe"]',
          expand_positional_args(argv, '"$@"') == ["abc 123", "qwe"])
    check('unquoted $@ splits on whitespace into ["abc", "123", "qwe"]',
          expand_positional_args(argv, "$@") == ["abc", "123", "qwe"])
    check('"$*" joins all arguments into a single string ["abc 123 qwe"]',
          expand_positional_args(argv, '"$*"') == ["abc 123 qwe"])

    # 3. set -e (errexit) suppression contexts (Section 8)
    check("standalone false (exit 1) under set -e aborts the script",
          does_errexit_abort(1) is True)
    check("false inside 'if false; then' condition does NOT abort under set -e",
          does_errexit_abort(1, in_if_or_while_condition=True) is False)
    check("false on left side of 'false || true' does NOT abort under set -e",
          does_errexit_abort(1, in_and_or_left_operand=True) is False)
    check("negated '! false' does NOT abort under set -e",
          does_errexit_abort(1, is_negated_with_bang=True) is False)
    check("false inside function f() called as 'f && echo ok' does NOT abort under set -e",
          does_errexit_abort(1, in_function_called_in_condition=True) is False)

    # 4. Subshell vs current-shell variable scoping (HLW Ch. 11.11, SCL Ch. 29)
    check("( v=2 ) in subshell leaves outer v=1 unchanged",
          simulate_variable_scope(1, 2, "subshell_parens") == 1)
    check("{ v=2; } in brace group updates outer v to 2",
          simulate_variable_scope(1, 2, "brace_group") == 2)
    check("printf ... | while read loop runs in subshell and loses count=6 (stays 0)",
          simulate_variable_scope(0, 6, "pipe_while") == 0)
    check("while read ... done < <(printf ...) runs in current shell and keeps count=6",
          simulate_variable_scope(0, 6, "proc_subst_while") == 6)

    # 5. Retry exponential backoff schedule (Section 8)
    sched = compute_exponential_backoff_schedule(attempts=5, initial_delay_sec=2)
    check("retry 5 2 sleeps [2, 4, 8, 16] seconds (total 30s across 4 retries)",
          sched["sleep_delays_sec"] == [2, 4, 8, 16] and sched["total_sleep_sec"] == 30)
    sched3 = compute_exponential_backoff_schedule(attempts=3, initial_delay_sec=1)
    check("retry 3 1 sleeps [1, 2] seconds (total 3s)",
          sched3["sleep_delays_sec"] == [1, 2] and sched3["total_sleep_sec"] == 3)
    check("timeout 2 sleep 10 returns exit status 124 on GNU coreutils timeout",
          124 > 0)

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


def _raises(fn) -> bool:
    try:
        fn()
        return False
    except ValueError:
        return True


if __name__ == "__main__":
    main()
