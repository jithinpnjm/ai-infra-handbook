"""Turn the text printed by the 60-second Linux tools into plain Python values.

Standard library only. Every function takes the text a tool printed and
returns dicts or lists. Nothing here runs a command.
"""
import re

NUM = re.compile(r"^-?\d+(\.\d+)?$")


def _floats(tokens):
    return [float(t) for t in tokens]


def parse_uptime(text):
    """Return the 1, 5 and 15 minute load averages from `uptime` text."""
    m = re.search(r"load averages?:\s*([\d.]+),?\s+([\d.]+),?\s+([\d.]+)", text)
    if not m:
        raise ValueError("no load average found")
    one, five, fifteen = (float(x) for x in m.groups())
    return {"load1": one, "load5": five, "load15": fifteen}


def parse_vmstat(text):
    """Return one dict per data row of `vmstat`, keyed by the header names.

    The first data row is marked since_boot=True. In the book it is a
    summary since boot for some columns, so a reader must not trust it.
    """
    header, rows = None, []
    for line in text.splitlines():
        parts = line.split()
        if parts[:3] == ["r", "b", "swpd"]:
            header = parts
        elif header and len(parts) == len(header) and all(NUM.match(p) for p in parts):
            row = dict(zip(header, _floats(parts)))
            row["since_boot"] = not rows
            rows.append(row)
    return rows


def parse_free(text):
    """Return memory and swap figures from `free` text, in the unit printed."""
    mem = swap = None
    cols = []
    for line in text.splitlines():
        parts = line.split()
        if parts and parts[0] == "total":
            cols = parts
        elif parts and parts[0] == "Mem:":
            mem = dict(zip(cols, _floats(parts[1:])))
        elif parts and parts[0] == "Swap:":
            swap = dict(zip(cols, _floats(parts[1:])))
    if mem is None:
        raise ValueError("no Mem: line found")
    return {"mem": mem, "swap": swap}


def parse_iostat(text):
    """Return disk rows and the avg-cpu line from `iostat`, keyed by header.

    Works for the extended and short layouts. Repeated blocks all end up
    in the same list. Each disk row also gets a `block` number.
    """
    disks, cpu, header, block = [], None, None, 0
    lines = text.splitlines()
    for i, line in enumerate(lines):
        parts = line.split()
        if parts and parts[0] == "avg-cpu:" and i + 1 < len(lines):
            names = [p.lstrip("%") for p in parts[1:]]
            cpu = dict(zip(names, _floats(lines[i + 1].split())))
        elif parts and parts[0] in ("Device", "Device:"):
            header, block = parts, block + 1
        elif header and len(parts) == len(header) and all(NUM.match(p) for p in parts[1:]):
            row = dict(zip(header[1:], _floats(parts[1:])))
            row.update(device=parts[0], block=block)
            disks.append(row)
    return {"disks": disks, "cpu": cpu}


def parse_mpstat(text):
    """Return one dict per CPU row of `mpstat`, keyed by the header names.

    A row printed on the Average: line gets average=True.
    """
    header, rows = None, []
    for line in text.splitlines():
        parts = line.split()
        if "CPU" in parts and "%usr" in parts:
            header = parts[parts.index("CPU"):]
        elif header and "CPU" not in parts and len(parts) >= len(header):
            tail = parts[-len(header):]
            if all(NUM.match(p) for p in tail[1:]) and (tail[0] == "all" or tail[0].isdigit()):
                row = dict(zip(header, [tail[0]] + _floats(tail[1:])))
                row["average"] = parts[0] == "Average:"
                rows.append(row)
    return rows


def parse_psi(text):
    """Return {'some': {...}, 'full': {...}} from a /proc/pressure/* file."""
    out = {}
    for line in text.splitlines():
        parts = line.split()
        if parts and parts[0] in ("some", "full"):
            out[parts[0]] = {k: float(v) for k, v in (p.split("=") for p in parts[1:])}
    return out


def find_oom(text):
    """Return the dmesg lines that mention the out-of-memory killer."""
    return [l for l in text.splitlines()
            if "Out of memory" in l or "killed" in l.lower()]
