---
id: "c03-05"
title: "3.5 Errors, files, text and bytes, subprocess and system scripting"
sidebar_label: "3.5 Errors, files, text and bytes, subprocess and system scripting"
sidebar_position: 5
description: "Exceptions, context managers and else/finally, files and pathlib, text/bytes/Unicode, JSON/YAML/CSV, subprocess, signals, logging, and robust system scripting for Linux operations"
status: "drafted"
tier: "2"
level: "I"
lab_venue: "Mac"
---

# 3.5 Errors, files, text and bytes, subprocess and system scripting

| | |
|---|---|
| Level | Intermediate |
| Priority tier | 0 |
| Lab venue | Linux VM (root for some exercises), Python 3.11+ |
| Part | Part 3: Python for infrastructure |
| Status | Drafted, labs **untested** |

## Why this matters for AI infrastructure

Infrastructure code lives at the boundary with the messy world: files that don't exist or are half-written, commands that fail with partial output, encodings that differ between hosts, signals that arrive mid-operation, terminals that aren't there under cron or systemd. A script that works on a laptop and corrupts a checkpoint directory at 3 a.m. usually failed in one of these places. This chapter covers the discipline of failure (exceptions, cleanup, retries, exit codes, logging), file and path handling (`pathlib`, atomic writes, permissions, temporary files, locking), text versus bytes and serialisation formats (JSON, YAML, CSV, TOML, struct), running external programs safely (`subprocess`), interacting with the OS (environment, signals, processes, `psutil`, `/proc`, `/sys`), and a template for robust operational scripts.

## Prerequisites and outcomes

You should know functions and collections (3.1), idioms (3.3) and classes (3.4); Linux fundamentals from Part 1 help.

After this chapter you can:

- Use `try`/`except`/`else`/`finally`, raise and chain exceptions, define exception hierarchies, use `with`, `ExceptionGroup`/`except*`, and design error handling (what to catch, where, how to report), including exit codes.
- Use `logging` correctly (levels, handlers, formatters, structured logs), and `warnings`.
- Read and write files safely: modes, encodings, buffering, atomic replace, permissions, temp files, file locks, `pathlib`, `shutil`, `os`, globbing, directory walks, `os.scandir`, `mmap`.
- Convert between text and bytes; handle encodings and errors; use `struct`, `base64`, `hashlib`, `zlib`/`gzip`/`tarfile`/`zipfile`.
- Parse and emit JSON, YAML, TOML, CSV and INI safely; handle large and malformed data.
- Run subprocesses safely (`subprocess.run`, `Popen`, pipes, timeouts, env, cwd, streaming output, process groups), avoid shell injection, and wrap CLI tools robustly.
- Handle signals and graceful shutdown; inspect processes and system state (`psutil`, `/proc`, `/sys`, `os`, `platform`, `socket`, `ipaddress`).
- Write production-grade operational scripts: idempotent, observable, safe to re-run, with dry-run mode and clear exit codes.

## 1. Exceptions

### Mechanics

An **exception** is an object representing an error or unusual condition; raising it unwinds the call stack until a matching handler is found; if none exists the program prints a traceback and exits with status 1.

```python
try:
    value = int(text)
    result = 100 / value
except ValueError as exc:                 # specific exception first
    print(f"not a number: {exc}")
except ZeroDivisionError:
    result = float("inf")
except (KeyError, IndexError) as exc:     # multiple types
    raise                                  # bare raise re-raises the current exception with its traceback
else:                                      # runs only if no exception occurred in try
    print("ok", result)
finally:                                   # ALWAYS runs: cleanup
    print("done")
```

- Handlers are matched **in order** by `isinstance`; put specific before general. The exception hierarchy: `BaseException` → `Exception` → (`OSError` → `FileNotFoundError`, `PermissionError`, `TimeoutError`, `ConnectionError`...; `ValueError`; `TypeError`; `KeyError`/`IndexError` (`LookupError`); `RuntimeError`; `AttributeError`; `ImportError`; `StopIteration`...). `KeyboardInterrupt` and `SystemExit` derive from `BaseException`, deliberately not from `Exception`, so `except Exception` doesn't swallow Ctrl-C or `sys.exit()`.
- **Never use a bare `except:`** (it catches `KeyboardInterrupt`/`SystemExit` too) and avoid `except Exception: pass`: silent failure is how data loss hides. Catch the narrowest exceptions you can *handle*; let others propagate to a boundary that logs and exits.
- `else` keeps the `try` body minimal (only the code that may raise what you catch), preventing accidental catching of unrelated errors from the success path.
- `finally` and `with` guarantee cleanup; a `return` inside `finally` swallows exceptions (avoid).
- **Raising**: `raise ValueError("bad value")`; instantiate with context (`raise ConfigError(f"missing key {key!r} in {path}")`). **Chaining**: `raise NewError("...") from exc` sets `__cause__` (explicit translation of low-level errors into domain errors); implicit chaining shows "During handling of the above exception, another exception occurred"; `raise ... from None` suppresses context when the original is noise.
- **Exception objects**: `exc.args`, `str(exc)`, `repr(exc)`, `exc.__traceback__`, `exc.add_note("hint")` (3.11), `traceback.format_exc()`, `logging.exception()` (logs message + traceback inside handlers).
- **`except Exc as var:` scope and reference-cleanup rule**: the variable bound after `as` in an `except` clause is local to that `except` block and is **automatically unbound (`del var`) when the `except` block exits**—even if `var` was previously assigned a value in the surrounding scope. Python removes this binding on exit because the caught exception's `__traceback__` attribute holds references to the runtime call stack frames (and their local variables), so keeping `var` alive would create a reference cycle that delays garbage collection and retains memory. If you need the exception object after the `try` statement finishes, assign it to a separate variable inside the handler:

```python
# In the book's examples (untested here):
X = 99
try:
    1 / 0
except Exception as X:
    print(X)               # division by zero
    saveit = X             # assign to another name if you need the exception after the block
# Here X is unbound (raises NameError: name 'X' is not defined), whereas saveit is ZeroDivisionError('division by zero')
```

- **Custom exceptions**: derive from `Exception` (or an application base), name them for the condition (`NodeUnreachable`), carry data as attributes, keep a shallow hierarchy.

```python
class OpsError(Exception):
    """Base class for errors in this tool."""
class ConfigError(OpsError): ...
class RemoteError(OpsError):
    def __init__(self, host, status, body=""):
        super().__init__(f"{host}: HTTP {status}")
        self.host, self.status, self.body = host, status, body

def load_config(path):
    try:
        text = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ConfigError(f"config file not found: {path}") from exc
    ...
```

- **Assertions** (`assert cond, "message"`) check programmer assumptions in tests and internal invariants; they are removed with `python -O`, so never use them for input validation or security checks.
- **Warnings** (`warnings.warn("x is deprecated", DeprecationWarning, stacklevel=2)`), controlled by `-W` flags and filters; tests can turn them into errors.
- **Exception groups (3.11)**: `ExceptionGroup("batch failed", [e1, e2])` and `except* ValueError:` handle multiple simultaneous errors (used by `asyncio.TaskGroup`, chapter 3.6).
- **Context managers** interplay: `__exit__` receives the exception; returning True suppresses it; `contextlib.suppress(FileNotFoundError)` for expected cases.

### Error-handling strategy for tools and services

1. **Fail fast on programmer errors and invalid input** at the boundary (validate config/arguments immediately, with clear messages).
2. **Handle expected operational failures** (network timeouts, missing files, 404s, lock contention) where you can do something sensible: retry with backoff, skip with a log, fall back, or translate to a domain error.
3. **Don't catch what you can't handle**; let unexpected exceptions bubble to one top-level handler that logs the traceback and exits non-zero.
4. **Preserve information**: chain exceptions, include identifiers (host, path, request id) in messages, log tracebacks once (not at every level).
5. **Make cleanup unconditional** (`with`, `finally`) and **idempotent**.
6. **Be explicit about partial failure**: when processing 500 hosts, collect results per host and report a summary and non-zero exit if any failed, rather than aborting at the first error or hiding failures.
7. **Retries**: only for transient errors and idempotent operations; exponential backoff with jitter and a cap; limit attempts and total time; log each attempt. Libraries: `tenacity`, `backoff`, or a small helper (chapter 3.1).
8. **Timeouts everywhere** on network and subprocess calls (the default is often "forever").

```python
import sys, logging
log = logging.getLogger("myops")

def main(argv=None) -> int:
    try:
        args = parse_args(argv)
        results = run(args)
    except OpsError as exc:
        log.error("%s", exc)                  # expected, user-facing errors: message only
        return 2
    except KeyboardInterrupt:
        log.warning("interrupted"); return 130
    except Exception:
        log.exception("unexpected failure")   # bug: full traceback
        return 1
    failed = [r for r in results if not r.ok]
    for r in failed: log.error("%s failed: %s", r.host, r.error)
    return 1 if failed else 0

if __name__ == "__main__":
    raise SystemExit(main())
```

Conventional exit codes: `0` success, `1` general error, `2` usage/argument error (argparse uses 2), `126/127` command not executable/not found (shell), `128+N` killed by signal N (130 = SIGINT, 143 = SIGTERM). Use documented codes when callers (CI, systemd, schedulers) distinguish them (for example, EX_TEMPFAIL 75 to request retry).

## 2. Logging

`print` is for program output; **`logging`** is for diagnostics, with levels, destinations and structure.

```python
import logging, sys

def setup_logging(verbosity=0, json_logs=False):
    level = {0: logging.WARNING, 1: logging.INFO}.get(verbosity, logging.DEBUG)
    handler = logging.StreamHandler(sys.stderr)                  # logs to stderr; stdout stays clean for data
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)-8s %(name)s: %(message)s", "%Y-%m-%dT%H:%M:%S%z"))
    root = logging.getLogger(); root.setLevel(level); root.handlers[:] = [handler]

log = logging.getLogger(__name__)         # one logger per module; never configure handlers in library code
log.debug("polling %s", host)             # lazy formatting: args formatted only if the record is emitted
log.info("started job %s on %d nodes", job_id, len(nodes))
log.warning("retrying %s in %.1fs", host, delay)
log.error("failed to reach %s", host, exc_info=True)       # attaches the current traceback
log.exception("unexpected")               # error + traceback (use inside except)
log.critical("out of disk")
```

- Levels: DEBUG, INFO, WARNING, ERROR, CRITICAL; set them via config/env, not by editing code.
- Use `%s` args, not f-strings, in log calls (cheaper when disabled; consistent aggregation).
- Libraries get a logger and add `logging.NullHandler()`; applications configure handlers once at startup.
- **Destinations**: stderr (containers/systemd capture it into the journal), `RotatingFileHandler`/`TimedRotatingFileHandler`, `SysLogHandler`, `SocketHandler`, `QueueHandler` for non-blocking logging, `logging.config.dictConfig` for declarative setups.
- **Structured logging** (JSON lines with fields like `host`, `job_id`, `duration_ms`) is far easier to search: `structlog`, `python-json-logger`, or a custom `Formatter`; include a correlation/request id. Redact secrets and personal data.
- Do not log inside tight loops at INFO; log summaries and sampled details; include units.
- In containers log to stdout/stderr and let the platform ship them (chapter on observability).

## 3. Files and paths

### `open()` and modes

```python
with open(path, "r", encoding="utf-8", errors="strict", newline=None) as f: ...
# modes: 'r' read text, 'w' truncate+write, 'a' append, 'x' exclusive create (fails if exists), '+' read/write, 'b' binary
with open("/tmp/x.bin", "rb") as f:
    header = f.read(16); f.seek(0, 2); size = f.tell(); f.seek(0)
for line in f_text: ...        # iterate lazily
data = f.read(); f.readlines(); f.readline(); f.write("text"); f.writelines(items); f.flush(); os.fsync(f.fileno())
```

- Text mode decodes/encodes with the given `encoding` and translates newlines; **always specify the encoding** (`utf-8`) for text. Binary mode returns `bytes`.
- Files are **buffered**; `flush()` pushes Python's buffer to the OS, `os.fsync()` forces data to disk (needed for durability, e.g. before renaming a checkpoint). `buffering=0` (binary only) unbuffered; line buffering with `buffering=1` or `-u`.
- Always use `with` (closes even on exceptions); never leave file handles to the garbage collector.
- Iterate files line by line (`for line in f`) for streaming; `read()` loads everything (fine for small files only).
- **Large files**: chunked reads (`iter(lambda: f.read(1<<20), b"")`), `mmap` for random access without copying (`mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)`), `os.sendfile`, `shutil.copyfileobj`.
- `errors="replace"|"backslashreplace"|"surrogateescape"` for logs and file names that may contain invalid UTF-8 (`surrogateescape` round-trips arbitrary bytes).

### `pathlib`

```python
from pathlib import Path
p = Path("/etc/kubernetes") / "manifests" / "kube-apiserver.yaml"      # '/' joins
p.exists(), p.is_file(), p.is_dir(), p.is_symlink(), p.stat().st_size, p.stat().st_mtime, p.resolve(), p.parent, p.name, p.stem, p.suffix, p.suffixes, p.with_suffix(".bak"), p.relative_to("/etc"), p.expanduser()
p.read_text(encoding="utf-8"); p.write_text("x\n", encoding="utf-8"); p.read_bytes(); p.write_bytes(b"")
p.mkdir(parents=True, exist_ok=True); p.touch(); p.unlink(missing_ok=True); p.rename(q); p.replace(q); p.rmdir()
Path("/var/log").glob("*.log"); Path("/data").rglob("*.parquet"); sorted(Path(".").iterdir())
Path.home(), Path.cwd(), Path(__file__).resolve().parent
p.chmod(0o640); p.owner(); p.group(); os.chown(p, uid, gid)
p.walk()                       # 3.12+: like os.walk
```

Prefer `pathlib` over string manipulation and `os.path`; pass `Path` objects to most standard functions (they implement `os.PathLike`). `os.scandir` is the fast low-level directory iterator (used by `os.walk`) and returns file type info without extra `stat` calls; for millions of files on parallel file systems, minimise metadata operations (avoid per-file `stat` when possible, batch, or use the file system's tools).

### Safe writes: atomic replace

Writing a file in place can leave a truncated file if the process crashes or the disk fills; readers may see partial content. The pattern: write to a temporary file **in the same directory** (same file system), flush and fsync, then `os.replace()` (atomic rename).

```python
import os, tempfile
from pathlib import Path

def atomic_write(path, data: str | bytes, mode=0o644):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    binary = isinstance(data, bytes)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb" if binary else "w", **({} if binary else {"encoding": "utf-8"})) as f:
            f.write(data); f.flush(); os.fsync(f.fileno())
        os.chmod(tmp, mode)
        os.replace(tmp, path)                      # atomic on POSIX
        dirfd = os.open(path.parent, os.O_DIRECTORY); os.fsync(dirfd); os.close(dirfd)    # persist the rename
    except BaseException:
        Path(tmp).unlink(missing_ok=True); raise
```

Use this for config files, state files, checkpoints' manifests and anything read by other processes. Beware network file systems (NFS, Lustre): atomic rename semantics hold within a directory on most, but caching and consistency rules differ; test.

### Temporary files and directories

`tempfile.TemporaryDirectory()`, `NamedTemporaryFile(delete=False)`, `mkstemp()` (secure, unique, 0600), `mkdtemp()`. Never construct temp file names yourself in `/tmp` (predictable names enable symlink attacks and collisions). Clean up with context managers; place large scratch data on the right file system (`TMPDIR`).

### Permissions, ownership and umask

`os.chmod`, `os.chown`, `os.umask`, `Path.chmod`, `stat` modes (`stat.S_IRUSR`), `os.access` (beware TOCTOU). Create secret files with restrictive modes from the start (`os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)`), not create-then-chmod. Check `0o` octal literals.

### Locking and races

Concurrent scripts (cron overlap, two operators) can corrupt state. Options: **lock files** with `fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)` (advisory, released on process exit), `os.open(path, O_CREAT | O_EXCL)` exclusive creation, the `filelock` library, `flock` command wrapper, or databases/etcd leases for distributed locks. Avoid **TOCTOU** races: instead of `if not exists: create`, attempt the operation and handle the exception (`open(..., "x")`, `os.mkdir`, `Path.mkdir(exist_ok=True)`).

```python
import fcntl, sys
lock = open("/run/myops.lock", "w")
try:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
except BlockingIOError:
    sys.exit("another instance is running")
```

### `shutil`, archives and compression

`shutil.copy2` (preserves metadata), `copytree(dirs_exist_ok=True)`, `move`, `rmtree` (dangerous: validate the path!), `disk_usage`, `which`, `make_archive`, `unpack_archive`; `tarfile` (beware path traversal when extracting untrusted archives: use `filter="data"` in 3.12+ or validate members), `zipfile`, `gzip`, `bz2`, `lzma`, `zlib`; `hashlib.sha256` streaming digests for integrity of artifacts (`for chunk in iter(lambda: f.read(1<<20), b""): h.update(chunk)`).

## 4. Text, bytes and encodings in practice

- **Rule**: decode at the input boundary, work with `str` internally, encode at the output boundary. `bytes` ↔ `str` only via `.decode()`/`.encode()`.
- **UTF-8** everywhere; set `PYTHONUTF8=1` (or `-X utf8`) to make UTF-8 the default regardless of locale (helps containers with `LANG=C`). Check `sys.getdefaultencoding()`, `locale.getpreferredencoding(False)`, `sys.stdout.encoding`, `sys.getfilesystemencoding()`.
- **Unicode errors**: `UnicodeDecodeError` means bytes aren't valid in the assumed encoding. Diagnose with `file -i`, `chardet`/`charset-normalizer`, `bytes.decode("utf-8", errors="replace")`; for opaque bytes in file names use `os.fsdecode`/`os.fsencode` and `surrogateescape`.
- **Binary protocols**: `struct.pack("<IHB", 1, 2, 3)`, `struct.unpack_from`, `int.from_bytes(b, "big")`, `.to_bytes(4, "little")`, `memoryview`, `bytearray`; endianness (network order is big-endian: `!`); `ctypes`/`cffi` for C structures; `construct`/`kaitai` for complex formats.
- **Encodings of text protocols**: HTTP headers are Latin-1/ASCII; JSON must be UTF-8; YAML UTF-8/16; CSV from spreadsheets may be `utf-8-sig` (BOM) or `cp1252`.
- **Newlines**: `\n` vs `\r\n`; open with `newline=""` for CSV; strip with `rstrip("\n")` or `splitlines()`.
- **Base64/hex**: `base64.b64encode(b).decode("ascii")`, `urlsafe_b64encode`, `bytes.hex()`.
- **Terminal output**: ANSI colours only when `sys.stdout.isatty()`; honour `NO_COLOR`; progress bars to stderr; machine-readable output (JSON lines) when piped.

## 5. Data formats

```python
import json, csv, tomllib, configparser
# JSON
data = json.loads(text); text = json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False, default=str)
with open("x.json", encoding="utf-8") as f: data = json.load(f)
for line in open("events.jsonl", encoding="utf-8"): rec = json.loads(line)          # JSON Lines: stream-friendly
# YAML (PyYAML)
import yaml
cfg = yaml.safe_load(open("cfg.yaml", encoding="utf-8"))             # never yaml.load on untrusted input (arbitrary object construction)
yaml.safe_dump(cfg, sort_keys=False, default_flow_style=False)
docs = list(yaml.safe_load_all(open("k8s.yaml")))                    # multi-document manifests
# TOML (read-only stdlib since 3.11; use tomli-w to write)
cfg = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
# CSV
with open("nodes.csv", newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f): ...
with open("out.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["name", "gpus"]); w.writeheader(); w.writerows(rows)
# INI
cp = configparser.ConfigParser(); cp.read("/etc/app.ini"); cp["db"].getint("port", fallback=5432)
```

Guidance: JSON for machine interchange, YAML for human-edited configs (use `ruamel.yaml` to preserve comments on edit), TOML for tool settings, CSV for tabular exports (use pandas for big data, chapter 3.10), JSON Lines or Parquet for large datasets. Validate parsed data (schema/pydantic, chapters 2.28 and 3.4), handle `JSONDecodeError`/`YAMLError` with file and line context, never `eval` data, and be careful with float precision, large integers, `NaN`, duplicate keys and date formats (ISO 8601 with timezone; use `datetime.fromisoformat`, `zoneinfo`, store UTC).

### Dates and times

`datetime.now(timezone.utc)` (aware datetimes), `time.monotonic()` for durations (immune to clock changes), `time.time()` wall clock, `time.perf_counter()` for benchmarks, `zoneinfo.ZoneInfo("Europe/Berlin")`, `timedelta`, `strftime/strptime`, `datetime.fromisoformat`. Avoid naive datetimes in infrastructure; log in UTC.

## 6. Running external programs: `subprocess`

### Safe defaults

```python
import subprocess, shlex

# Preferred: argument list, no shell, capture output, check status, set a timeout
result = subprocess.run(
    ["kubectl", "get", "nodes", "-o", "json"],
    capture_output=True,         # stdout=PIPE, stderr=PIPE
    text=True, encoding="utf-8", errors="replace",
    check=True,                  # raise CalledProcessError on non-zero exit
    timeout=30,                  # raise TimeoutExpired (and kill the child) if it runs too long
    env={**os.environ, "KUBECONFIG": "/etc/kubernetes/admin.conf"},
    cwd="/tmp",
)
nodes = json.loads(result.stdout)
```

- **Use a list of arguments**, never a single string with `shell=True` when any part comes from outside: shell metacharacters (`;`, `$()`, backticks, `&&`, quotes, globs) in a hostname or file name become command injection. If you must use a shell (pipelines, globbing), quote every dynamic part with `shlex.quote()` or build pipelines in Python with `Popen` pipes.
- `check=True` turns failures into exceptions; handle `CalledProcessError` (has `returncode`, `stdout`, `stderr`, `cmd`), `TimeoutExpired`, and `FileNotFoundError` (command missing) or `PermissionError`.
- `capture_output` buffers all output in memory: for huge outputs stream instead.
- Pass an explicit `env` (copy of `os.environ` plus changes) instead of mutating the global environment; clear secrets you don't need to pass.
- Always set `timeout`; for services and daemons use `Popen` and manage lifecycle.
- Prefer machine-readable output (`-o json`, `--format=json`, `ip -j`, `lsblk -J`, `nvidia-smi --query-gpu=... --format=csv,noheader,nounits`) and parse it; avoid regex-scraping human tables.
- `stdin`: `input="data"` (text) to send data; `stdin=subprocess.DEVNULL` to prevent interactive prompts that would hang a script; `stdout=subprocess.DEVNULL` to discard.
- Encoding: set `text=True` with an explicit `encoding` or keep bytes.
- `universal_newlines` is the old name for `text`.

### Streaming, pipelines and process control

```python
# Stream output line by line (long-running command), still bounded by a deadline
import time
with subprocess.Popen(["ping", "-c", "5", "10.0.0.1"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1) as p:
    deadline = time.monotonic() + 30
    for line in p.stdout:
        handle(line.rstrip())
        if time.monotonic() > deadline:
            p.kill(); break
    rc = p.wait()

# Pipeline without a shell:  dmesg | grep -i error | tail -20
p1 = subprocess.Popen(["dmesg"], stdout=subprocess.PIPE)
p2 = subprocess.Popen(["grep", "-i", "error"], stdin=p1.stdout, stdout=subprocess.PIPE)
p1.stdout.close()                       # allow p1 to receive SIGPIPE if p2 exits
p3 = subprocess.run(["tail", "-20"], stdin=p2.stdout, capture_output=True, text=True)

# Run in a new session/process group so you can kill the whole tree on timeout
p = subprocess.Popen(cmd, start_new_session=True)
os.killpg(os.getpgid(p.pid), signal.SIGTERM)
```

- **Deadlocks**: reading only `stdout` while the child fills the `stderr` pipe buffer blocks both; use `communicate()`, `capture_output=True`, merge `stderr=STDOUT`, or threads/`asyncio.create_subprocess_exec` (chapter 3.6).
- **Zombies**: `wait()`/`communicate()` reap children; unreaped children linger as `<defunct>`.
- **Return codes**: negative `returncode` means killed by that signal (`-9` = SIGKILL).
- **Which program**: `shutil.which("kubectl")` finds an executable on `PATH`; pin absolute paths in privileged scripts; scrub `PATH`.
- **Security**: never run user-controlled executable names; avoid `sudo` in scripts when you can run the whole script with the right capabilities; use `sudo -n` (non-interactive) and restrict with sudoers; don't pass secrets on the command line (visible in `ps`): use environment variables, stdin, or files with 0600.
- **Wrappers**: write a small `run()` helper that logs the command (redacting secrets), enforces timeout/check, supports dry-run, and returns a typed result; libraries like `sh`, `plumbum`, `invoke`/`fabric`, and `pyinfra` provide richer ergonomics; `paramiko`/`asyncssh`/`fabric` run commands over SSH; `ansible-runner` for Ansible.

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class CmdResult:
    cmd: tuple[str, ...]
    rc: int
    out: str
    err: str

def run(cmd: list[str], *, dry_run=False, timeout=60, check=True, **kw) -> CmdResult:
    log.info("exec: %s", shlex.join(cmd))
    if dry_run:
        return CmdResult(tuple(cmd), 0, "", "")
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, **kw)
    except subprocess.TimeoutExpired as exc:
        raise OpsError(f"timeout after {timeout}s: {shlex.join(cmd)}") from exc
    except FileNotFoundError as exc:
        raise OpsError(f"command not found: {cmd[0]}") from exc
    if check and p.returncode != 0:
        raise OpsError(f"{shlex.join(cmd)} exited {p.returncode}: {p.stderr.strip()[:500]}")
    return CmdResult(tuple(cmd), p.returncode, p.stdout, p.stderr)
```

### Avoid shelling out when Python can do it

Use libraries instead of parsing command output: `socket`, `ipaddress`, `psutil` (processes, CPU, memory, disks, network counters), `os.statvfs`/`shutil.disk_usage`, `platform`, `pwd/grp`, `pyudev`, `netifaces`/`pyroute2` (netlink), `docker`/`kubernetes` clients, `boto3`, `paramiko`, NVML bindings (`pynvml`/`nvidia-ml-py`) instead of scraping `nvidia-smi` (chapter 3.8 for exporters).

## 7. Interacting with the operating system

### Environment, arguments, process info

```python
import os, sys, platform, socket, getpass, pwd, resource
os.environ.get("HOME"); os.environ["X"] = "1"; os.getenv("X", "default"); os.environ.copy()
sys.argv; sys.executable; sys.platform; platform.node(); platform.machine(); platform.release()
os.getpid(); os.getppid(); os.getuid(); os.geteuid(); os.cpu_count(); len(os.sched_getaffinity(0))      # usable CPUs (respects cgroups/affinity better than cpu_count)
socket.gethostname(); socket.getfqdn(); pwd.getpwuid(os.getuid()).pw_name
resource.getrlimit(resource.RLIMIT_NOFILE); resource.setrlimit(resource.RLIMIT_NOFILE, (65536, 65536))
os.nice(5); os.sched_setaffinity(0, {0, 1}); os.setsid()      # Linux process control
```

Command-line arguments: use `argparse` (chapter 3.8 covers CLIs fully), not hand parsing of `sys.argv`. Environment variables for configuration and secrets (injected by systemd/Kubernetes); never log them wholesale.

### `/proc`, `/sys`, `psutil`

```python
import psutil
psutil.cpu_percent(interval=1, percpu=True); psutil.virtual_memory()._asdict(); psutil.disk_usage("/"); psutil.net_io_counters(pernic=True)
for p in psutil.process_iter(["pid", "name", "cmdline", "cpu_percent", "memory_info"]): ...
psutil.Process(pid).children(recursive=True); psutil.Process(pid).terminate()
psutil.sensors_temperatures(); psutil.boot_time()
open("/proc/meminfo").read(); Path("/sys/class/net/eth0/speed").read_text(); Path("/proc/loadavg").read_text().split()
```

Reading `/proc` and `/sys` directly is cheap and dependency-free; values are text; handle files that vanish (processes exit) with `FileNotFoundError`/`ProcessLookupError`. Containers see namespaced and cgroup-limited views (`/sys/fs/cgroup/...`): `psutil` totals may show the host, not the limit.

### Signals and graceful shutdown

```python
import signal, threading

stop = threading.Event()
def handle(signum, frame):
    log.warning("received %s, shutting down", signal.Signals(signum).name)
    stop.set()
signal.signal(signal.SIGTERM, handle)        # Kubernetes/systemd stop
signal.signal(signal.SIGINT, handle)         # Ctrl-C
signal.signal(signal.SIGHUP, lambda *_: reload_config())       # reload convention
signal.signal(signal.SIGPIPE, signal.SIG_DFL)                  # let 'script | head' end quietly
while not stop.is_set():
    do_work()
    stop.wait(5)                              # interruptible sleep
cleanup()
```

- Handlers run in the main thread between bytecode instructions; keep them tiny (set a flag), do real work in the main loop. You can't handle `SIGKILL`/`SIGSTOP`.
- Kubernetes sends `SIGTERM`, waits `terminationGracePeriodSeconds`, then `SIGKILL`: use the grace period to finish in-flight work and checkpoint.
- Python as PID 1 in containers does not reap zombies or forward signals by default: use `tini`/`--init`, or `exec` the process from a shell wrapper.
- `atexit.register(fn)` runs on normal exit (not on `SIGKILL`/`os._exit`). `faulthandler.enable()` dumps tracebacks on crashes and `kill -SIGUSR1` (with `faulthandler.register`) for diagnosing hangs.

### Network and system helpers

`socket` (TCP/UDP clients/servers, `getaddrinfo`, timeouts: `sock.settimeout(5)`; connect checks `socket.create_connection((host, port), timeout=3)`), `ipaddress` (parse, networks, subnets, containment), `ssl`, `urllib.request` (dependency-free HTTP) or `requests`/`httpx` (chapter 3.7), `select`/`selectors`, `datetime`, `uuid`, `secrets` (tokens), `hashlib`, `hmac`, `getpass`, `crypt`-like password hashing via `bcrypt`/`argon2-cffi`.

## 8. A template for robust operational scripts

```python
#!/usr/bin/env python3
"""drain_nodes: cordon and drain Kubernetes nodes matching a label, safely and idempotently."""
from __future__ import annotations
import argparse, json, logging, shlex, signal, subprocess, sys, threading
from dataclasses import dataclass

log = logging.getLogger("drain_nodes")
stop = threading.Event()

class OpsError(Exception): ...

@dataclass
class Result:
    node: str
    ok: bool
    detail: str = ""

def kubectl(*args, dry_run=False, timeout=120):
    cmd = ["kubectl", *args]
    log.info("exec: %s", shlex.join(cmd))
    if dry_run and args[0] in {"drain", "cordon", "uncordon", "delete"}:
        return ""
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=True)
    except subprocess.CalledProcessError as exc:
        raise OpsError(f"{shlex.join(cmd)}: {exc.stderr.strip()}") from exc
    except subprocess.TimeoutExpired as exc:
        raise OpsError(f"timeout: {shlex.join(cmd)}") from exc
    return p.stdout

def select_nodes(selector):
    out = kubectl("get", "nodes", "-l", selector, "-o", "json")
    return [i["metadata"]["name"] for i in json.loads(out)["items"]]

def drain(node, *, dry_run):
    if stop.is_set(): return Result(node, False, "interrupted")
    try:
        kubectl("cordon", node, dry_run=dry_run)                       # idempotent
        kubectl("drain", node, "--ignore-daemonsets", "--delete-emptydir-data", "--timeout=300s", dry_run=dry_run)
        return Result(node, True)
    except OpsError as exc:
        return Result(node, False, str(exc))

def parse_args(argv):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selector", required=True, help="label selector, e.g. pool=gpu-a")
    ap.add_argument("--max-failures", type=int, default=0)
    ap.add_argument("--dry-run", action="store_true", help="show what would be done")
    ap.add_argument("-v", "--verbose", action="count", default=0)
    return ap.parse_args(argv)

def main(argv=None):
    args = parse_args(argv)
    logging.basicConfig(level=[logging.WARNING, logging.INFO, logging.DEBUG][min(args.verbose, 2)], format="%(asctime)s %(levelname)s %(message)s", stream=sys.stderr)
    signal.signal(signal.SIGINT, lambda *_: stop.set()); signal.signal(signal.SIGTERM, lambda *_: stop.set())
    try:
        nodes = select_nodes(args.selector)
    except OpsError as exc:
        log.error("%s", exc); return 2
    if not nodes:
        log.warning("no nodes match %r", args.selector); return 0
    results = []
    for n in nodes:                                                    # sequential for safety (rolling): parallelise cautiously
        r = drain(n, dry_run=args.dry_run); results.append(r)
        log.info("%s: %s %s", n, "ok" if r.ok else "FAILED", r.detail)
        if sum(not x.ok for x in results) > args.max_failures: break
    failed = [r for r in results if not r.ok]
    print(json.dumps({"drained": [r.node for r in results if r.ok], "failed": [vars(r) for r in failed]}, indent=2))
    return 1 if failed else 0

if __name__ == "__main__":
    raise SystemExit(main())
```

Qualities to copy: single `main()` returning an exit code; `--dry-run`; idempotent steps; per-item error isolation with a failure budget; timeouts on every subprocess; logs to stderr and machine-readable results to stdout; graceful interrupt; no shell; clear error messages with command and stderr; small testable functions.

## 9. Lab (untested)

1. **Exceptions**: write functions that raise and catch `ValueError`, `FileNotFoundError`, a custom `ConfigError` chained with `from`; demonstrate `else`/`finally`, `raise` re-raise, `suppress`, exception groups with `except*`; show what bare `except:` swallows (Ctrl-C) and why that's wrong.
2. **Exit codes and top-level handler**: build the `main()` pattern; verify exit codes in a shell (`echo $?`), under `systemd-run --wait`, and in a Kubernetes Job (or `docker run`).
3. **Logging**: configure console and rotating file handlers, a JSON formatter, a correlation id via `LoggerAdapter` or `contextvars`; compare `%s` args vs f-strings with `timeit` when DEBUG is off.
4. **Files**: implement `atomic_write`; test with a process killed mid-write (`kill -9`) vs naive `open("w")`; add `fsync`; test on a full tmpfs (`mount -t tmpfs -o size=1m`) to see `ENOSPC` handling; create a file with 0600 securely; show a TOCTOU race and its fix; implement a lock file and run two instances.
5. **Large files**: generate a 5 GB file; compare `read()`, line iteration, chunked reads, and `mmap` for memory and time; compute SHA-256 streaming; compress with `gzip` streaming.
6. **Encodings**: create files in UTF-8, UTF-8-BOM, Latin-1 and UTF-16; write a loader that detects and decodes; reproduce `UnicodeDecodeError` and fix with `errors="replace"`; handle undecodable filenames with `surrogateescape`; run with `LANG=C` vs `PYTHONUTF8=1` in a container.
7. **Formats**: round-trip data through JSON, YAML (`safe_load`), TOML, CSV; show the YAML "Norway problem"; show why `yaml.load` is unsafe (construct a harmless object); stream a large JSON Lines file.
8. **Subprocess**: wrap `ip -j addr`, `lsblk -J`, `nvidia-smi --query-gpu=...` (if available) and parse; demonstrate shell injection with `shell=True` and an attacker-controlled string, then fix with an argument list; reproduce a pipe deadlock and fix; implement timeout-and-kill of a process tree with `start_new_session` and `killpg`; build the `run()` helper with dry-run.
9. **Signals**: write a worker that checkpoints on SIGTERM and reloads config on SIGHUP; test with `kill`, `systemctl stop` and in a container (`docker stop`, observing the 10 s grace period); run it as PID 1 without and with `--init` to see zombie/signal behaviour.
10. **System inspection**: write a node-info script using `psutil`, `/proc`, `/sys` (CPU, memory, disks, NICs speed/MTU, load, GPU via `pynvml` if available) producing JSON; compare container vs host views.
11. **Operational script**: implement the `drain_nodes` template against a kind cluster; add unit tests with a fake `kubectl` (a stub executable on `PATH` or monkeypatched `subprocess.run`); run in dry-run and real mode; kill it mid-run and re-run to check idempotency.
12. **Clean up.**

Mark tested only after execution.

## 10. Common mistakes

- Bare `except`/`except Exception: pass`; catching too much around too much code; losing tracebacks; logging the same error at every level.
- Writing files in place (partial writes), not fsyncing before declaring success, relying on exists-then-create checks.
- Default text encoding assumptions; opening files without `encoding=`; mixing bytes and str.
- `shell=True` with interpolated input; no timeouts; ignoring return codes; parsing human-formatted output; secrets in command lines.
- Capturing huge output in memory; pipe deadlocks; unreaped children.
- Using `os.system`, `os.popen`, or the deprecated `commands`.
- Mutating global state (`os.environ`, `os.chdir`) in libraries; assuming the current directory.
- Scripts that are not safe to re-run; no dry-run; no lock against overlapping runs; non-UTC naive timestamps.
- Heavy work in signal handlers; ignoring SIGTERM in containers.
- Extracting untrusted tar/zip archives without path validation; `yaml.load`; `pickle` from the network.

## 11. Interview angles

- "What's the difference between `try/except/else/finally`? When use `else`?"
- "Why shouldn't you use a bare `except`? What does `raise ... from` do?"
- "How do you write a file atomically? Why `os.replace` and why same directory?"
- "How do you run a command safely from Python? What's wrong with `shell=True`?"
- "How would you avoid deadlocks when reading a subprocess's stdout and stderr?"
- "A script works interactively but not under cron/systemd. What could differ?" (PATH, env, cwd, locale, TTY, umask, user, HOME, signals.)
- "How do you handle SIGTERM in a container?"
- "How would you make an operational script safe to re-run, and safe to run concurrently?"
- "Explain text vs bytes and the failure modes of encodings."
- "How would you process a 50 GB file safely?"

## 12. Checkpoint questions (40)

1. When does `else` run in try? **A:** When no exception occurred in try.
2. When does `finally` run? **A:** Always.
3. Why not bare `except:`? **A:** Catches `KeyboardInterrupt`/`SystemExit` and hides bugs.
4. What does `raise` alone do, and what happens to `var` after an `except Exc as var:` block exits? **A:** Bare `raise` re-raises the active exception; Python automatically unbinds (`del var`) the `as var` target when the `except` block exits (even if `var` existed in the surrounding scope) so the exception's `__traceback__` frame references do not keep local variables alive in a reference cycle.
5. What does `raise X from Y` set? **A:** `__cause__` explicit chaining.
6. How to suppress context? **A:** `raise X from None`.
7. Which exception base excludes Ctrl-C from `except Exception`? **A:** `KeyboardInterrupt` derives from `BaseException`.
8. Are assertions reliable validation? **A:** No; removed with `-O`.
9. What is `except*` for? **A:** Handling `ExceptionGroup`s.
10. Exit code for success? **A:** 0.
11. Exit code convention for Ctrl-C? **A:** 130.
12. Why log to stderr? **A:** Keep stdout for data; platforms capture stderr.
13. Why `%s` args in log calls? **A:** Lazy formatting.
14. Where to configure logging? **A:** In the application entry point, not libraries.
15. Which file mode fails if the file exists? **A:** `"x"`.
16. Why specify `encoding`? **A:** Avoid locale-dependent defaults.
17. Flush vs fsync? **A:** Python buffer to OS vs OS to disk.
18. What is atomic replace? **A:** Write temp in same dir, fsync, `os.replace`.
19. Why same directory for temp? **A:** Same file system so rename is atomic.
20. What is TOCTOU? **A:** Check-then-act race condition.
21. How to avoid it? **A:** Attempt the operation and handle failure.
22. How to lock with fcntl? **A:** `flock(fd, LOCK_EX | LOCK_NB)`.
23. Why `mkstemp`? **A:** Secure unique temp files.
24. `pathlib` over `os.path`? **A:** Object-oriented, fewer string bugs.
25. How to stream a big file? **A:** Iterate lines or read chunks; `mmap`.
26. `surrogateescape` use? **A:** Round-trip undecodable bytes.
27. Safe YAML loader? **A:** `yaml.safe_load`.
28. Why `newline=""` for CSV? **A:** Correct newline handling in quoted fields.
29. Which clock for durations? **A:** `time.monotonic()`.
30. Why `subprocess.run` with a list? **A:** Avoid shell injection.
31. What does `check=True` do? **A:** Raises on non-zero exit.
32. What does `timeout` do? **A:** Kills the child and raises `TimeoutExpired`.
33. Pipe deadlock cause? **A:** Child blocks writing a full pipe nobody reads.
34. Avoid secrets in args because? **A:** Visible in `ps`/`/proc`.
35. How to kill a process tree? **A:** `start_new_session` and `os.killpg`.
36. What signal does Kubernetes send first? **A:** SIGTERM.
37. What should a signal handler do? **A:** Set a flag; keep it minimal.
38. Why use `tini`/`--init`? **A:** Reap zombies and forward signals for PID 1.
39. How to count usable CPUs? **A:** `len(os.sched_getaffinity(0))`.
40. What makes a script idempotent? **A:** Re-running yields the same end state without errors.

## 13. Sources and review notes

**Written in original words.** Principal sources:

- Mark Lutz, *Learning Python*, 6th ed. (`learning-python-6th-edition`; part VII: exceptions—with `Chapter 34. Exception Coding Details` read in full for this chapter, covering `try`/`except`/`else`/`finally`, `raise`/`raise from`, `except Exc as var` scope and reference-cleanup rules, `assert`, and `with` context managers—plus chapter 37 on Unicode and byte strings).
- Luciano Ramalho, *Fluent Python*, 2nd ed.: chapter 4 (Unicode text versus bytes) and chapter 18 (`with`, `match`, and `else` blocks).
- The author's `nvidia-devops` repository, volume 02: interacting with the host system (`pathlib`, `subprocess`, `shutil`), error handling, tooling and operations masterclasses.
- Brian Ward, *How Linux Works*, 3rd ed. (signals, processes, `/proc`) for the system-interaction sections.
- Examples are the author's constructions.

**Flagged for verification before publishing:** version-specific behaviour (`tarfile` extraction filters in 3.12, `Path.walk` 3.12, `ExceptionGroup` 3.11, `tomllib` 3.11), library APIs (psutil, pynvml, PyYAML), NFS/Lustre atomicity statements, and every code listing; all labs are **untested**.
