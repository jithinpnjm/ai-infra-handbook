"""Chapter 3.5 model: Exceptions, files, text/bytes/Unicode, context managers,
and safe subprocess/system scripting.

Sources modeled:
- Mark Lutz, Learning Python, 6th ed. (learning-python-6th-edition, LP),
  Chapters 33-37:
  * Chapter 33 ("Exception Basics"): fetcher(obj, index), default vs try/except
    recovery, raise, and finally termination actions (no backtracking of prior
    mutations).
  * Chapter 34 ("Exception Coding Details"): combined try/except/else/finally
    execution order, raise NewExc from OldExc (__cause__) vs implicit __context__,
    except Exc as var unbinding rule (del var on block exit to break traceback
    frame reference cycles), assert vs python -O, and multiple-context with.
  * Chapter 35 ("Exception Objects"): exception class hierarchies (General,
    Specific1, Specific2; mathlib NumErr -> Divzero/Oflow/Uflow), custom state
    and methods in FormatError(line, file) & exc.args, and ExceptionGroup /
    except* selective group matching.
  * Chapter 36 ("Exception Odds and Ends"): control-flow vs syntactic try
    nesting (action1/action2/action3, except-finally.py), sys.exc_info() vs
    sys.exception() (3.11+), traceback.print_exc / format_exc, and why bare
    except catches sys.exit() (SystemExit) and masks NameError bugs.
  * Chapter 37 ("Unicode and Byte Strings"): str vs bytes vs bytearray,
    encode('utf-8') vs encode('latin-1') on 'AÄBèC' (strlen=5, utf8=7, latin1=5),
    NFC vs NFD ('\\u00E9' vs '\\u0065\\u0301'), struct.pack/unpack ('>i4sh'),
    and text vs binary file I/O.
- Luciano Ramalho, Fluent Python, 2nd ed. (fluent-python-2nd-edition, FP):
  * Chapter 4 ("Unicode Text Versus Bytes"): nfc_equal & fold_equal (NFC/NFKC,
    casefold on 'Straße'/'strasse' and 'µ'), shave_marks & shave_marks_latin,
    str vs bytes regex (r'\\d+' vs rb'\\d+'), and surrogateescape.
  * Chapter 18 ("with, match, and else Blocks"): LookingGlass class and
    @contextmanager looking_glass (handling exceptions in yield), ExitStack, and
    EAFP vs LBYL.
"""
import contextlib
import re
import string
import struct
import sys
import unicodedata
from typing import Dict, List, Tuple


# 1. LP Ch. 35 & 36: Exception hierarchy (NumErr -> Divzero, Oflow, Uflow) and FormatError
class NumErr(Exception):
    """LP Ch. 35 mathlib base exception category."""


class Divzero(NumErr):
    pass


class Oflow(NumErr):
    pass


class Uflow(NumErr):
    pass


class FormatError(Exception):
    """LP Ch. 35 Example 35-3 parsely.py custom exception carrying structured state."""

    def __init__(self, line: int, file: str) -> None:
        super().__init__(line, file)
        self.line = line
        self.file = file

    def format_report(self) -> str:
        return f"Error at: {self.file} #{self.line}"


def trace_try_except_else_finally(mode: str) -> Tuple[List[str], object]:
    """LP Ch. 34 & 36: Trace exact execution order of try/except/else/finally
    and verify `except Exception as X` unbinding on exit plus `sys.exception()`.
    """
    events: List[str] = []
    saved_exc: object = None
    outer_x = "initial"

    try:
        events.append("try:start")
        if mode == "index_error":
            raise IndexError("bad index")
        if mode == "chained":
            try:
                1 / 0
            except ZeroDivisionError as orig:
                raise FormatError(42, "config.yaml") from orig
        events.append("try:ok")
    except IndexError as outer_x:
        # Inside except block, sys.exception() returns the active exception (3.11+)
        active = sys.exception()
        events.append(f"except:IndexError(active={type(active).__name__})")
        saved_exc = outer_x
    except FormatError as outer_x:
        events.append(f"except:FormatError(cause={type(outer_x.__cause__).__name__})")
        saved_exc = outer_x
    else:
        events.append("else:ran")
    finally:
        events.append("finally:ran")

    # Verify outer_x was unbound by `del outer_x` when the except block exited
    try:
        _ = outer_x  # type: ignore[used-before-def]
        x_still_bound = True
    except UnboundLocalError:
        x_still_bound = False

    events.append(f"x_bound_after={x_still_bound}")
    return events, saved_exc


def split_exception_group_demo() -> List[str]:
    """LP Ch. 35 ExceptionGroup and except* selective handler execution."""
    handled: List[str] = []
    try:
        raise ExceptionGroup("BatchErrors", [IndexError("idx"), TypeError(1), TypeError(2)])
    except* IndexError as eg:
        handled.append(f"IE:{len(eg.exceptions)}")
    except* TypeError as eg:
        handled.append(f"TE:{len(eg.exceptions)}")
    return handled


# 2. LP Ch. 37 & FP Ch. 4: Unicode encodings, NFC/NFD, casefold, shave_marks_latin, struct
def inspect_unicode_and_struct() -> Dict[str, object]:
    """LP Ch. 37 'AÄBèC' UTF-8 vs Latin-1 lengths, struct.pack('>i4sh'), and
    FP Ch. 4 nfc_equal, fold_equal, shave_marks_latin, and str vs bytes regex.
    """
    s = "AÄBèC"
    utf8_bytes = s.encode("utf-8")
    latin1_bytes = s.encode("latin-1")

    packed = struct.pack(">i4sh", 7, b"code", 8)
    unpacked = struct.unpack(">i4sh", packed)

    # NFC vs NFD ('é' vs 'e\u0301') and casefold ('Straße' vs 'strasse')
    s1 = "caf\u00e9"
    s2 = "cafe\u0301"
    raw_eq = s1 == s2
    nfc_eq = unicodedata.normalize("NFC", s1) == unicodedata.normalize("NFC", s2)
    fold_eq = (
        unicodedata.normalize("NFC", "Straße").casefold()
        == unicodedata.normalize("NFC", "strasse").casefold()
    )

    shaved = shave_marks_latin("São Paulo: Zéphyr & Ελληνικά")

    # FP Ch. 4 Example 4-23 ramanujan.py: str vs bytes \d+ on Tamil digits
    text_str = "1729 \u0be7\u0bed\u0be8\u0bef"
    text_bytes = text_str.encode("utf-8")
    str_digits = re.findall(r"\d+", text_str)
    bytes_digits = re.findall(rb"\d+", text_bytes)

    return {
        "strlen": len(s),
        "utf8_len": len(utf8_bytes),
        "latin1_len": len(latin1_bytes),
        "packed": packed,
        "unpacked": unpacked,
        "raw_eq": raw_eq,
        "nfc_eq": nfc_eq,
        "fold_eq": fold_eq,
        "shaved": shaved,
        "str_digits_count": len(str_digits),
        "bytes_digits_count": len(bytes_digits),
    }


def shave_marks_latin(txt: str) -> str:
    """FP Ch. 4 Example 4-16: Remove all diacritic marks from Latin base characters only."""
    norm_txt = unicodedata.normalize("NFD", txt)
    latin_base = False
    preserve: List[str] = []
    for c in norm_txt:
        if unicodedata.combining(c) and latin_base:
            continue
        preserve.append(c)
        if not unicodedata.combining(c):
            latin_base = c in string.ascii_letters
    shaved = "".join(preserve)
    return unicodedata.normalize("NFC", shaved)


# 3. FP Ch. 18: LookingGlass context manager and @contextmanager looking_glass
class LookingGlass:
    """FP Ch. 18 Example 18-3: Context manager that reverses text and catches ZeroDivisionError."""

    def __init__(self) -> None:
        self.log: List[str] = []

    def write(self, text: str) -> None:
        self.log.append(text[::-1])

    def __enter__(self) -> str:
        return "JABBERWOCKY"

    def __exit__(self, exc_type, exc_value, traceback) -> bool | None:
        if exc_type is ZeroDivisionError:
            self.log.append("Please DO NOT divide by zero!")
            return True
        return None


@contextlib.contextmanager
def safe_looking_glass(sink: List[str]):
    """FP Ch. 18 Example 18-5/18-7: @contextmanager with try/except/finally around yield."""
    sink.append("enter")
    try:
        yield "JABBERWOCKY"
    except ZeroDivisionError:
        sink.append("caught_zero_div")
    finally:
        sink.append("exit_restored")
