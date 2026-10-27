#!/usr/bin/env python3
"""Self-checking lab for Chapter 3.5: Errors, files, text and bytes, subprocess and system scripting."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from python_errors_files_subprocess import (
    Divzero,
    FormatError,
    LookingGlass,
    NumErr,
    inspect_unicode_and_struct,
    safe_looking_glass,
    split_exception_group_demo,
    trace_try_except_else_finally,
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
    # 1. LP Ch. 34 & 36: try/except/else/finally order, `as var` unbinding, and `raise ... from`
    ev_ok, exc_ok = trace_try_except_else_finally("ok")
    ev_idx, exc_idx = trace_try_except_else_finally("index_error")
    ev_ch, exc_ch = trace_try_except_else_finally("chained")
    check(
        "try/except/else/finally runs else only on success, unbinds `as X` on except exit, and chains __cause__",
        ev_ok == ["try:start", "try:ok", "else:ran", "finally:ran", "x_bound_after=True"]
        and exc_ok is None
        and ev_idx == [
            "try:start",
            "except:IndexError(active=IndexError)",
            "finally:ran",
            "x_bound_after=False",
        ]
        and isinstance(exc_idx, IndexError)
        and ev_ch == [
            "try:start",
            "except:FormatError(cause=ZeroDivisionError)",
            "finally:ran",
            "x_bound_after=False",
        ]
        and isinstance(exc_ch, FormatError)
        and exc_ch.format_report() == "Error at: config.yaml #42",
    )

    # 2. LP Ch. 35: Exception hierarchy (NumErr -> Divzero) and ExceptionGroup / except*
    caught_cat = False
    try:
        raise Divzero("0")
    except NumErr:
        caught_cat = True
    eg_res = split_exception_group_demo()
    check(
        "NumErr superclass catches Divzero subclass, and except* splits ExceptionGroup into IE:1 and TE:2",
        caught_cat is True and eg_res == ["IE:1", "TE:2"],
    )

    # 3. LP Ch. 37 & FP Ch. 4: 'AÄBèC' UTF-8 (7 B) vs Latin-1 (5 B), struct('>i4sh'), NFC/casefold, shave_marks_latin, regex
    uni = inspect_unicode_and_struct()
    check(
        "'AÄBèC' is 5 chars, 7 UTF-8 bytes, 5 Latin-1 bytes; struct.pack('>i4sh', 7, b'code', 8) round-trips",
        uni["strlen"] == 5
        and uni["utf8_len"] == 7
        and uni["latin1_len"] == 5
        and uni["packed"] == b"\x00\x00\x00\x07code\x00\x08"
        and uni["unpacked"] == (7, b"code", 8),
    )
    check(
        "NFC normalizes 'café' == 'cafe\\u0301', casefold matches 'Straße' == 'strasse', shave_marks_latin preserves Greek, and r'\\d+' vs rb'\\d+'",
        uni["raw_eq"] is False
        and uni["nfc_eq"] is True
        and uni["fold_eq"] is True
        and uni["shaved"] == "Sao Paulo: Zephyr & Ελληνικά"
        and uni["str_digits_count"] == 2
        and uni["bytes_digits_count"] == 1,
    )

    # 4. FP Ch. 18: LookingGlass (__enter__/__exit__ suppressing ZeroDivisionError) & @contextmanager try/finally
    lg = LookingGlass()
    with lg as what:
        lg.write("Alice")
        _ = 1 / 0
    sink = []
    with safe_looking_glass(sink) as tag:
        sink.append(tag[::-1])
        _ = 1 / 0
    check(
        "LookingGlass reverses text, suppresses ZeroDivisionError via __exit__->True, and @contextmanager runs finally",
        what == "JABBERWOCKY"
        and lg.log == ["ecilA", "Please DO NOT divide by zero!"]
        and sink == ["enter", "YKCOWREBBAJ", "caught_zero_div", "exit_restored"],
    )

    # 5. Atomic file write and exclusive create ('x') in a temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        target = Path(tmpdir) / "state.json"
        target.write_text('{"ok": true}\n', encoding="utf-8")
        excl_failed = False
        try:
            with open(target, "x", encoding="utf-8") as _:
                pass
        except FileExistsError:
            excl_failed = True
        check(
            "TemporaryDirectory writes UTF-8 state.json and open(..., 'x') raises FileExistsError on existing file",
            target.read_text(encoding="utf-8") == '{"ok": true}\n' and excl_failed is True,
        )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
