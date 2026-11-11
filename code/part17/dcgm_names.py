"""Convert PromQL between dcgm-exporter 4.8.x and 4.9.0 metric names.

Mapping data lives in dcgm_exporter_4_9_rename.json. When a metric changes unit,
the converted expression keeps the OLD (or NEW) meaning by scaling the series, so
`DCGM_FI_DEV_GPU_UTIL > 95` becomes `(DCGM_FI_DEV_GPU_UTIL_RATIO * 100) > 95`.
Thresholds are never rewritten. Range-vector metrics are scaled outside the
enclosing rate()/increase()/..._over_time() call.
"""
import json
import re
from pathlib import Path

DATA = json.loads((Path(__file__).with_name("dcgm_exporter_4_9_rename.json")).read_text())
NAME = re.compile(r"\bDCGM_(?:FI|EXP)_[A-Z0-9_]+\b")
RANGE_FUNCS = ("rate", "irate", "increase", "delta", "idelta", "deriv", "avg_over_time", "min_over_time",
               "max_over_time", "sum_over_time", "last_over_time", "quantile_over_time")


class UnitScaleError(ValueError):
    """A metric changes unit but the scale factor is not confirmed, or cannot be applied safely."""


def _entries(include_inferred):
    out = list(DATA["renamed"])
    if include_inferred:
        out += DATA["inferred_optional"]
    return out


def mapping(direction="old_to_new", include_inferred=True):
    """Return {from_name: (to_name, scale_expr_suffix_or_None, entry)}.

    scale suffix is applied to the to_name series so that it has the from_name's unit.
    """
    if direction not in ("old_to_new", "new_to_old"):
        raise ValueError(direction)
    m = {}
    for e in _entries(include_inferred):
        old, new, sc = e["old"], e["new"], e.get("scale")
        if direction == "old_to_new":
            frm, to = old, new
            # new = old op factor  ->  old = new inverse-op factor
            inv = None if not sc else ("/" if sc["op"] == "multiply" else "*")
        else:
            frm, to = new, old
            inv = None if not sc else ("*" if sc["op"] == "multiply" else "/")
        m[frm] = (to, (inv, sc["factor"]) if sc else None, e)
    return m


def _fmt(n):
    return str(int(n))


def _match_paren(s, i):
    """s[i] == '(' -> index of the matching ')'."""
    depth = 0
    for j in range(i, len(s)):
        if s[j] == "(":
            depth += 1
        elif s[j] == ")":
            depth -= 1
            if depth == 0:
                return j
    raise ValueError("unbalanced parentheses")


def _check_scale(e, allow_unverified):
    if e.get("scale_status") == "unverified" and not allow_unverified:
        raise UnitScaleError(f"{e['old']} -> {e['new']}: unit changes ({e['unit_old']} -> {e['unit_new']}) "
                             "but the factor is unverified; pass scale='names_only' to rename without scaling")


def convert(expr, direction="old_to_new", scale="wrap", include_inferred=True):
    """Convert a PromQL expression.

    scale="wrap": keep each series' original unit by scaling; "names_only": rename only.
    """
    if scale not in ("wrap", "names_only"):
        raise ValueError(scale)
    m = mapping(direction, include_inferred)
    # 1. range functions that directly wrap a selector of a scaled metric
    out, i = [], 0
    pat = re.compile(r"\b(" + "|".join(RANGE_FUNCS) + r")\s*\(")
    while True:
        mo = pat.search(expr, i)
        if not mo:
            out.append(expr[i:])
            break
        op = mo.end() - 1
        cl = _match_paren(expr, op)
        inner = expr[op + 1:cl]
        names = NAME.findall(inner)
        scaled = [n for n in names if n in m and m[n][1] is not None]
        if scale == "wrap" and scaled and "[" in inner:
            if len(set(names)) != 1:
                raise UnitScaleError(f"cannot scale {scaled[0]} inside {mo.group(1)}() with other metrics: {inner!r}")
            to, sc, e = m[names[0]]
            _check_scale(e, False)
            new_inner = NAME.sub(lambda x: to, inner)
            out.append(expr[i:mo.start()] + f"({mo.group(1)}({new_inner}) {sc[0]} {_fmt(sc[1])})")
            i = cl + 1
        else:
            out.append(expr[i:op + 1])
            i = op + 1
    expr2 = "".join(out)

    # 2. remaining bare selectors (name plus optional {matchers})
    sel = re.compile(NAME.pattern + r"(\{[^}]*\})?")

    def sub(mo):
        n = NAME.match(mo.group(0)).group(0)
        matchers = mo.group(1) or ""
        if n not in m:
            return mo.group(0)
        to, sc, e = m[n]
        if scale == "names_only":
            return to + matchers
        _check_scale(e, False)
        if sc is None:
            return to + matchers
        if re.match(r"\s*\[", expr2[mo.end():mo.end() + 50]):
            raise UnitScaleError(f"{n} is used in a range selector outside a supported function; scale manually")
        return f"({to}{matchers} {sc[0]} {_fmt(sc[1])})"

    # old and new name sets are disjoint, so names written by step 1 are never re-mapped
    return sel.sub(sub, expr2)


def convert_names_in_text(text, direction="old_to_new"):
    """Rename only (no scaling) every known metric/label name in free text, e.g. a CSV or a label list."""
    m = mapping(direction)
    return NAME.sub(lambda x: m[x.group(0)][0] if x.group(0) in m else x.group(0), text)


def to_dual(expr_new):
    """Return `(new_expr) or (old_expr)` so a rule works on 4.8.x and 4.9.0 exporters."""
    old = convert(expr_new, "new_to_old")
    return expr_new if old == expr_new else f"({expr_new}) or ({old})"


def unit_changes():
    return [e for e in DATA["renamed"] if e.get("scale") or e.get("scale_status")]
