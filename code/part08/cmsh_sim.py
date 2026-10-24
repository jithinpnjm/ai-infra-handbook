#!/usr/bin/env python3
"""A small simulator of cmsh behaviour, built ONLY from what the BCM 11 Administrator Manual (section 2.5) shows.

Not cmsh. It exists so you can practise the habits that matter (commit, refresh, modified, asterisks, node lists, foreach, clone,
rename) on a laptop and test your understanding against the manual's own sessions.

Parts:
  expand_nodelist / format_nodelist   node list syntax (2.5.5) and groupingsyntax output
  rename_targets                      the rename command (2.5.5)
  format_table                        the 'format' column width rules (2.5.3)
  Session                             objects, modes, prompt with asterisks, add/use/set/get/clear/commit/refresh/modified/remove/clone/foreach
"""
import re

class CmshError(ValueError):
    pass

# ---- node lists --------------------------------------------------------------------------------------------------
def _split_top(s):
    parts, depth, cur = [], 0, ""
    for ch in s:
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
        if ch in ", " and depth == 0:
            if cur:
                parts.append(cur)
            cur = ""
        else:
            cur += ch
    if cur:
        parts.append(cur)
    return parts

def _expand_group(body):
    """Contents of one [...]: comma separated items, each 'a', 'a-b', 'a..b', optionally ':stride'."""
    out = []
    for item in body.split(","):
        stride = 1
        if ":" in item:
            item, st = item.rsplit(":", 1)
            stride = int(st)
        m = re.fullmatch(r"(\d+)(?:-|\.\.)(\d+)", item)
        if m:
            a, b = m.group(1), m.group(2)
            w = len(a) if a.startswith("0") or len(a) == len(b) else 0
            out += [str(n).zfill(w) for n in range(int(a), int(b) + 1, stride)]
        elif re.fullmatch(r"\d+", item):
            out.append(item)
        else:
            raise CmshError(f"cannot read '{item}' inside brackets")
    return out

def _expand_brackets(item):
    m = re.search(r"\[([^\]]*)\]", item)
    if not m:
        return [item]
    pre, post = item[:m.start()], item[m.end():]
    return [r for g in _expand_group(m.group(1)) for r in _expand_brackets(pre + g + post)]

def _expand_dots(item):
    left, right = item.split("..", 1)
    ml, mr = re.search(r"(\d+)$", left), re.search(r"(\d+)$", right)
    if not ml or not mr:
        raise CmshError(f"cannot read range '{item}'")
    prefix, a, b = left[:ml.start()], ml.group(1), mr.group(1)
    w = len(a)
    return [prefix + str(n).zfill(w) for n in range(int(a), int(b) + 1)]

def expand_nodelist(spec, read_file=None):
    """The manual's node list forms: adhoc, sequential (.. or [a-b]), extended brackets, rack-based, exclusion with a leading '-',
    stride with ':', mixed, and '^/path' to read a file. Order is kept; duplicates are dropped."""
    result = []
    for item in _split_top(spec):
        if item.startswith("^"):
            if read_file is None:
                raise CmshError("a ^file list needs a file reader")
            result += expand_nodelist(read_file(item[1:]), read_file)
            continue
        neg = item.startswith("-")
        body = item[1:] if neg else item
        if "[" in body and ".." in re.sub(r"\[[^\]]*\]", "", body):
            raise CmshError("square brackets and two dots cannot be mixed in one argument")
        names = _expand_brackets(body) if "[" in body else (_expand_dots(body) if ".." in body else [body])
        if neg:
            result = [n for n in result if n not in set(names)]
        else:
            result += names
    seen, out = set(), []
    for n in result:
        if n not in seen:
            seen.add(n); out.append(n)
    return out

def format_nodelist(names, syntax="auto"):
    """groupingsyntax: 'dot' (and 'auto' for output) gives node001..node003; 'bracket' gives node[001-003]."""
    runs, cur = [], []
    def key(n):
        m = re.search(r"(\d+)$", n)
        return (n[:m.start()], int(m.group(1)), len(m.group(1))) if m else (n, None, 0)
    for n in names:
        k = key(n)
        if cur and k[1] is not None and key(cur[-1])[0] == k[0] and key(cur[-1])[2] == k[2] and key(cur[-1])[1] + 1 == k[1]:
            cur.append(n)
        else:
            if cur:
                runs.append(cur)
            cur = [n]
    if cur:
        runs.append(cur)
    out = []
    for r in runs:
        if len(r) == 1:
            out.append(r[0])
        elif syntax == "bracket":
            k0, k1 = key(r[0]), key(r[-1])
            out.append(f"{k0[0]}[{str(k0[1]).zfill(k0[2])}-{str(k1[1]).zfill(k1[2])}]")
        else:
            out.append(f"{r[0]}..{r[-1]}")
    return ",".join(out)

# ---- rename ------------------------------------------------------------------------------------------------------
def rename_targets(sources, target):
    """2.5.5 rename. `sources` is already expanded (sorted alphabetically as the manual says).
      plain text           prefix + 1..N, digits padded to the size of N      (test1.. or test01..test10)
      text with %04d       printf style, numbering from 1
      list / brackets      exact mapping; the sizes must match"""
    srcs = sorted(sources)
    n = len(srcs)
    if "[" in target or "," in target:
        t = expand_nodelist(target)
        if len(t) != n:
            raise CmshError(f"{n} sources but {len(t)} targets: the sizes must match")
    elif "%" in target:
        t = [target % i for i in range(1, n + 1)]
    else:
        w = len(str(n))
        t = [f"{target}{i:0{w}d}" for i in range(1, n + 1)]
    return list(zip(srcs, t))

# ---- format ------------------------------------------------------------------------------------------------------
def column_width(spec, texts):
    """'10' fixed, '0' widest entry, '[10-14]' between 10 and 14 fitted to the text. Longer text is cut with a '+' as the last character."""
    m = re.fullmatch(r"\[(\d+)-(\d+)\]", spec)
    longest = max([len(t) for t in texts] or [0])
    if m:
        return max(int(m.group(1)), min(int(m.group(2)), longest))
    w = int(spec)
    return longest if w == 0 else w

def fit(text, width):
    return text if len(text) <= width else text[:width - 1] + "+"

# ---- the session -------------------------------------------------------------------------------------------------
BOOL_TRUE, BOOL_FALSE = {"yes", "1", "on", "true"}, {"no", "0", "off", "false"}
BOOL_PROPS = {"datanode", "installbootrecord"}
CLEAR_VALUE = {"mac": "00:00:00:00:00:00"}
DEVICE_TYPES = {"physicalnode", "headnode", "switch", "chassis", "genericdevice", "litenode", "cloudnode", "dpu", "powerdistributionunit", "racksensor", "unmanagednode"}
INHERITED = {"bootloaderprotocol", "installmode", "softwareimage", "excludelistupdate"}

class Session:
    def __init__(self, cluster="basecm11"):
        self.cluster = cluster
        self.db = {"device": {}, "category": {"default": {"softwareimage": "default-image"}}, "network": {}}
        self.pending = {}            # (mode, name) -> ('new'|'mod'|'del', props)
        self.mode = None
        self.obj = None
        self.log = []

    # prompt
    def prompt(self):
        s = f"[{self.cluster}"
        if self.mode:
            star = "*" if any(m == self.mode for (m, _) in self.pending) else ""
            s += f"->{self.mode}{star}"
            if self.obj:
                ostar = "*" if (self.mode, self.obj) in self.pending and self.pending[(self.mode, self.obj)][0] != "del" else ""
                s += f"[{self.obj}{ostar}]"
        return s + "]%"

    def _get(self, mode, name):
        p = self.pending.get((mode, name))
        if p:
            if p[0] == "del":
                return None
            return p[1]
        return self.db[mode].get(name)

    def _touch(self, mode, name):
        if (mode, name) not in self.pending:
            self.pending[(mode, name)] = ("mod", dict(self.db[mode][name]))
        return self.pending[(mode, name)][1]

    def _need_obj(self, name=None):
        n = name or self.obj
        if not self.mode or not n:
            raise CmshError("no current object")
        if self._get(self.mode, n) is None:
            raise CmshError(f"no such {self.mode}: {n}")
        return n

    def _bool(self, prop, v):
        if prop in BOOL_PROPS:
            lv = v.lower()
            if lv in BOOL_TRUE:
                return "yes"
            if lv in BOOL_FALSE:
                return "no"
            raise CmshError(f"{v} is not a Boolean (yes/1/on/true or no/0/off/false)")
        return v

    # commands
    def enter(self, mode):
        if mode not in self.db:
            raise CmshError(f"unknown mode {mode}")
        self.mode, self.obj = mode, None

    def home(self):
        self.mode = self.obj = None

    def exit(self):
        if self.obj:
            self.obj = None
        else:
            self.mode = None

    def add(self, *args):
        if self.mode == "device":
            if not args or args[0] not in DEVICE_TYPES:
                raise CmshError("device mode: add <type> <hostname> [ip]")
            typ, name = args[0], args[1]
            props = {"type": typ, "hostname": name, "category": "default" if typ == "physicalnode" else "", "mac": CLEAR_VALUE["mac"]}
            if len(args) > 2:
                props["ip"] = args[2]
        else:
            name, props = args[0], {}
        if self._get(self.mode, name) is not None:
            raise CmshError(f"{name} already exists")
        self.pending[(self.mode, name)] = ("new", props)
        self.obj = name

    def use(self, name):
        if self._get(self.mode, name) is None:
            raise CmshError(f"no such {self.mode}: {name}")
        self.obj = name

    def set(self, prop, value, name=None):
        n = self._need_obj(name)
        if (self.mode, n) in self.pending:
            props = self.pending[(self.mode, n)][1]
        else:
            props = self._touch(self.mode, n)
        props[prop] = self._bool(prop, value)

    def get(self, prop, name=None):
        n = self._need_obj(name)
        props = self._get(self.mode, n)
        if prop in props:
            return props[prop]
        if self.mode == "device" and prop in INHERITED:
            cat = props.get("category", "default")
            cp = self._get("category", cat) or {}
            if prop in cp:
                return f"{cp[prop]} ({cat})"
        return ""

    def clear(self, prop, name=None):
        n = self._need_obj(name)
        props = self._touch(self.mode, n) if (self.mode, n) not in self.pending else self.pending[(self.mode, n)][1]
        props[prop] = CLEAR_VALUE.get(prop, "")

    def remove(self, name):
        if self._get(self.mode, name) is None:
            raise CmshError(f"no such {self.mode}: {name}")
        state = self.pending.get((self.mode, name))
        if state and state[0] == "new":
            del self.pending[(self.mode, name)]
        else:
            self.pending[(self.mode, name)] = ("del", {})
        if self.obj == name:
            self.obj = None

    def clone(self, src, dst, next_ip=False):
        s = self._get(self.mode, src)
        if s is None:
            raise CmshError(f"no such {self.mode}: {src}")
        if self._get(self.mode, dst) is not None:
            raise CmshError(f"{dst} already exists")
        props = dict(s)
        notes = []
        if self.mode == "device":
            props["hostname"] = dst
            props["mac"] = CLEAR_VALUE["mac"]
            if s.get("ip"):
                bs, bd = re.sub(r"\d+$", "", src), re.sub(r"\d+$", "", dst)
                ns, nd = re.search(r"(\d+)$", src), re.search(r"(\d+)$", dst)
                if next_ip:
                    props["ip"] = self._next_free_ip(s["ip"])
                elif bs == bd and ns and nd and len(ns.group(1)) == len(nd.group(1)):
                    base = s["ip"].split(".")
                    base[3] = str(int(base[3]) + int(nd.group(1)) - int(ns.group(1)))
                    props["ip"] = ".".join(base)
                else:
                    notes.append("Base name mismatch, IP settings will not be modified!")
            notes.append("Warning: The Ethernet switch settings were not cloned, and have to be set manually") if not notes else None
        self.pending[(self.mode, dst)] = ("new", props)
        self.obj = dst
        return notes

    def _next_free_ip(self, like):
        used = {self._get("device", n).get("ip") for n in self._names("device")}
        parts = like.split(".")
        for i in range(1, 255):
            cand = ".".join(parts[:3] + [str(i)])
            if cand not in used:
                return cand
        raise CmshError("no free address")

    def _names(self, mode):
        names = set(self.db[mode]) | {n for (m, n), v in self.pending.items() if m == mode and v[0] == "new"}
        return sorted(n for n in names if self._get(mode, n) is not None)

    def modified(self):
        rows = []
        for (m, n), (st, _) in self.pending.items():
            rows.append(("+" if st == "new" else "-" if st == "del" else "", m, n))
        return sorted(rows, key=lambda r: (r[1], r[2]))

    def refresh(self):
        if self.obj and (self.mode, self.obj) in self.pending:
            del self.pending[(self.mode, self.obj)]
            if self._get(self.mode, self.obj) is None:
                self.obj = None
        else:
            for k in [k for k in self.pending if k[0] == self.mode]:
                del self.pending[k]

    def commit(self):
        n = 0
        for (m, name), (st, props) in list(self.pending.items()):
            if st == "del":
                self.db[m].pop(name, None)
            else:
                self.db[m][name] = props
            n += 1
            del self.pending[(m, name)]
        return n

    def foreach(self, names, commands, clone_from=None, next_ip=False):
        out = []
        for n in names:
            if clone_from:
                out += self.clone(clone_from, n, next_ip)
            else:
                self.use(n)
            for c in commands:
                r = self.run_line(c)
                if r:
                    out.append(r)
        self.obj = None
        return out

    # a tiny interpreter -------------------------------------------------------------------------------------------
    def run_line(self, line):
        line = line.strip()
        if not line:
            return ""
        m = re.match(r"foreach\s+(.*?)\((.*)\)\s*$", line)
        if m:
            opts, body = m.group(1).split(), [c for c in m.group(2).split(";") if c.strip()]
            clone_from, nodes, next_ip = None, [], "--next-ip" in opts
            i = 0
            while i < len(opts):
                if opts[i] in ("--clone", "-o"):
                    clone_from = opts[i + 1]; i += 1
                elif opts[i] in ("-n", "--nodes"):
                    nodes = expand_nodelist(opts[i + 1]); i += 1
                elif opts[i] in ("-c", "--category"):
                    nodes = [n for n in self._names(self.mode) if self._get(self.mode, n).get("category") == opts[i + 1]]; i += 1
                elif opts[i] == "*":
                    nodes = self._names(self.mode)
                i += 1
            return "\n".join(self.foreach(nodes, body, clone_from, next_ip))
        w = line.split()
        cmd, a = w[0], w[1:]
        if cmd in self.db:
            if not a:
                self.enter(cmd)
                return ""
            saved = (self.mode, self.obj)
            self.enter(cmd)
            r = self.run_line(" ".join(a))
            if a[0] not in ("add", "clone"):      # the manual: add drops into the new object; other commands leave the mode as it was
                self.mode, self.obj = saved
            return r
        if cmd == "use": self.use(a[0])
        elif cmd == "add": self.add(*a)
        elif cmd == "set":
            if len(a) >= 3 and self.mode and self._get(self.mode, a[0]) is not None and a[1] not in ("",):
                self.set(a[1], " ".join(a[2:]), a[0])
            else:
                self.set(a[0], " ".join(a[1:]))
        elif cmd == "get":
            return self.get(a[1], a[0]) if len(a) == 2 else self.get(a[0])
        elif cmd == "clear":
            self.clear(a[1], a[0]) if len(a) == 2 else self.clear(a[0])
        elif cmd == "remove": self.remove(a[0])
        elif cmd == "clone": return "\n".join(self.clone(a[0], a[1]))
        elif cmd == "commit":
            self.commit()
        elif cmd == "refresh": self.refresh()
        elif cmd == "exit": self.exit()
        elif cmd == "home": self.home()
        elif cmd == "modified":
            return "\n".join(f"{s:6} {m} {n}" for s, m, n in self.modified()) or f"No modified objects of type {self.mode}"
        elif cmd == "list": return "\n".join(self._names(self.mode))
        else:
            raise CmshError(f"unknown command {cmd}")
        return ""

    def script(self, text):
        """Run '; '-separated commands and return the prompt after each one, like a terminal transcript."""
        out = []
        depth, cur, cmds = 0, "", []
        for ch in text:
            depth += (ch == "(") - (ch == ")")
            if ch in ";\n" and depth == 0:
                cmds.append(cur); cur = ""
            else:
                cur += ch
        cmds.append(cur)
        for c in cmds:
            if c.strip():
                self.run_line(c)
                out.append((c.strip(), self.prompt()))
        return out
