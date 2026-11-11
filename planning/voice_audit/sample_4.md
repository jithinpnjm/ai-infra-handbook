# Voice sample 4: parts part-03-python, part-10-gpu-cuda, part-19-capstone

## FILE docs/part-03-python/01-python-core-types-control-flow-functions.md

Ahead-of-time compilers, such as Nuitka and Shed Skin, turn Python programs into machine code. As Chapter 2 noted, they work much as C and C++ compilers do. You run the compiler on your file first, and then run the result like any other executable. These systems can boost speed, but they add development steps that slow you down. They also cut into what makes Python appealing. Beginners should learn the language with REPLs, IDEs and command lines first.

---

Installing Python is not required for every part of this book. You do need a Python to work through the examples and the end-of-part exercises, though, and running code makes the concepts concrete. The book uses Python 3.12, so a version close to that is best. You may not be able to choose a version in some contexts, and that is fine.

---

In a sense, Python is WYSIWYG: what you see is what you get. The way the code looks is the way it runs, no matter who wrote it. Some companies enforce consistent indentation in C even though C does not require it. Their tools check indentation when code is checked in, and an inconsistent check-in can trigger an automated email to the author and perhaps to the manager.

---

A function is an **object** (first class): it can be assigned, stored in data structures, passed to and returned from other functions. `def` executes at definition time (creates the function object and binds the name). A function without `return` returns `None`; `return a, b` returns a tuple. A function should do one thing, have a clear name (verb phrase), and a docstring describing arguments, return value, side effects and exceptions.

---

## FILE docs/part-03-python/02-modules-packages-virtual-environments-and-packaging.md

Importing a root package does not load its submodules. A folder's module object does not check the file system when you read an attribute. So `import dir1`, followed by `dir1.dir2.mod.var`, raises `AttributeError: module 'dir1' has no attribute 'dir2'`. You need the full dotted import, `import dir1.dir2.mod`. On the first import, that runs `dir1/__init__.py`, then `dir1/dir2/__init__.py`, then `dir1/dir2/mod.py`.

---

Each `__init__.py` plays four roles. First, it runs as an initialization hook the first time Python imports through that directory. Second, it fills the namespace of the directory's module object. That is why `dir1.var == 'Python'` and `dir1.dir2.var == 3.12`. It can also hold `__version__` or re-export public names. Third, its presence marks a regular package. That gives the directory priority over same-named directories later on `sys.path`. Fourth, `__all__ = ['mod']` controls `from package import *`. It names the submodules that a star import should load. Package `__init__.py` files are unrelated to the `__init__` constructor methods of classes.

---

Now reverse the order. Restart Python and run `import recur2` first. Or run `python3 recur1.py` as a script. In that case `recur1` is `__main__`, not `sys.modules['recur1']`, so `recur2` is the first module imported. `recur1` then runs from top to bottom during `from recur1 import X`. It finishes `X = 1`. It treats `import recur2` as a no-op, because `recur2` is already in `sys.modules`. It finishes `Y = 2` as well. Only then does `from recur1 import Y` run, and it succeeds.

---

Using `--extra-index-url` with private package names invites dependency confusion. Downloading and running unpinned packages on production hosts is risky too. Installing at runtime, in containers and jobs, brings network flakiness, drift and security risk. Forgetting aarch64 and glibc compatibility also leads to failures.

---

## FILE docs/part-03-python/03-idiomatic-python-the-data-model-comprehensions-generators.md

Most of the data in a script sits in sequences, so the choice of sequence type affects both memory and speed. This section starts with the two families of sequences, then shows the everyday tools for slicing, unpacking and sorting.

---

Watch out for `list.insert(0, x)` and `list.pop(0)`. Both are O(n), because every remaining item has to move. Use `collections.deque` instead. It supports `appendleft`, `popleft` and a `maxlen=N` ring buffer, which is ideal for keeping the most recent N metrics or log lines.

---

UTF-8 is the default for new work. ASCII is a subset of it. Latin-1 maps bytes one to one onto code points 0 to 255, which helps when you need to carry arbitrary bytes through text APIs. The `errors` argument decides what happens on failure. You can choose `"replace"`, `"ignore"`, `"surrogateescape"`, `"backslashreplace"` or `"strict"`. The result of `locale.getpreferredencoding()` changes with the environment, and containers that set `LANG=C` often surprise people. Always pass `encoding="utf-8"` to `open()`.

---

Unicode has its own traps. The same visible text can use different code point sequences, for example `é` as one code point or as `e` plus a combining accent. Normalise both strings with `unicodedata.normalize("NFC", s)` before you compare them. Use `str.casefold()` for caseless matching. `len()` counts code points, not bytes or visual characters, which are called graphemes. Sorting follows code point order, so use `locale.strxfrm` or ICU when you need order that people expect.

---

## FILE docs/part-03-python/04-classes-dataclasses-typing-and-protocols.md

Every dot expression starts a search through a tree of linked objects. Picture a tree with two instances, `I1` and `I2`, a class `C1` that both were made from, and two superclasses, `C2` and `C3`, above `C1`. Each object carries its own names. When you ask for `I2.w`, Python checks `I2`, then `C1`, then `C2`, then `C3`. It stops at the first `w` it finds. If no object in the tree has the name, Python raises an error.

---

In this tree, only `C3` defines `w`. So `I2.w` resolves to `C3.w`, and `I2` inherits `w` from `C3`. Other lookups take shorter paths. Both instances find `x` in `C1` and stop there, because `C1` sits lower in the tree and redefines `x`. A name stored on the instance itself, such as `I2.name`, is found without any climbing.

---

Suppose you want your own object to respond to `+` or to `print`. Python lets a class intercept built-in operations. Operations such as addition, slicing, printing and attribute access route to methods that the class provides. Modules cannot do this for expressions. They can only provide function calls.

---

Lutz's Learning Python Chapter 29 (`Example 29-1 specialize.py`) names four ways a subclass can interface with a superclass called `Super`. In the first, `Inheritor(Super)` inherits the methods unchanged, using `pass`. In the second, `Replacer(Super)` overrides `method(self)` completely. In the third, `Extender(Super)` overrides `method(self)` and calls back into `Super.method(self)`. Learning Python Chapter 28 shows this with `Manager.giveRaise(self, percent, bonus=.10)`, which calls `Person.giveRaise(self, percent + bonus)` in `person_14.py`. That example can also be stored by key in a `shelve.open('persondb')` DBM database through `makedb.py` and `updatedb.py`. In the fourth, `Provider(Super)` implements the abstract `action(self)` hook that `Super.delegate(self)` expects. This is the Template Method pattern.

---

## FILE docs/part-03-python/05-errors-files-text-and-bytes-subprocess-and-system-scripting.md

Infrastructure code lives at the edge of a messy world. Files may not exist, or they may be half-written. Commands fail with partial output. Hosts disagree on encodings, signals arrive in the middle of an operation, and under cron or systemd there may be no terminal at all. A script that runs fine on a laptop can still corrupt a checkpoint directory at 3 a.m. The fault usually lies in one of these places.

---

Prefer `pathlib` over string manipulation and `os.path`. Most standard functions accept `Path` objects directly, because they implement `os.PathLike`. `os.scandir` is the fast, low-level directory iterator behind `os.walk`, and it returns file type information without extra `stat` calls. When you work with millions of files on a parallel file system, minimise metadata operations. Avoid a `stat` per file where you can, batch the work, or use the file system's own tools.

---

Binary protocols use `struct`. For example, `struct.pack(">i4sh", 7, b"code", 8)` produces `b'\x00\x00\x00\x07code\x00\x08'`, as Learning Python, chapter 37, shows. `struct.unpack(">i4sh", B)` returns `(7, b'code', 8)`. Other tools include `struct.pack("<IHB", 1, 2, 3)`, `struct.unpack_from`, `int.from_bytes(b, "big")`, `.to_bytes(4, "little")`, `memoryview` and `bytearray`. Endianness matters. Network order is big-endian, which you write as `!` or `>`. For C structures, use `ctypes` or `cffi`, and for complex formats, `construct` and `kaitai` help.

---

Choose each format for its purpose. Use JSON for machine interchange. Use YAML for configs that people edit by hand, and if you must keep comments when you edit them, `ruamel.yaml` preserves them. Use TOML for tool settings, and CSV for tabular exports. When CSV data gets big, switch to pandas, as chapter 3.10 explains. For large datasets, use JSON Lines or Parquet.

---

## FILE docs/part-03-python/06-concurrency-threads-processes-and-asyncio.md

The threaded spinner, `spinner_thread.py`, starts `spinner = Thread(target=spin, args=('thinking!', done))`, where `done = threading.Event()`. The `spin` function loops over `for char in itertools.cycle(r'\|/-'):` and checks `if done.wait(.1): break`, printing `f'\r{char} {msg}'` with `flush=True`. The main code runs `slow()`, then calls `done.set(); spinner.join()`. If `slow()` runs a CPU-bound `is_prime(5_000_111_000_222_021)` check instead of `time.sleep(3)`, the spinner keeps animating. CPython suspends the `is_prime` thread every `5 ms` (`sys.getswitchinterval()`), which is just long enough for `spin` to print a frame and go back to sleep in `done.wait(.1)`.

---

Arguments and return values cross process boundaries through pickle. Lambdas, nested functions, open files, sockets and locks cannot be pickled, so use top-level functions and plain data. Large objects get copied, which is slow. Pass file paths or indices instead, or use shared memory.

---

An asynchronous generator combines `async def` with `yield`. In *Fluent Python*, Chapter 21 (`Example 21-18`, `domainlib.py`), the function starts with `async def multi_probe(names: Iterable[str]) -> AsyncIterator[Result]:`. It launches `coros = [probe(name, loop) for name in names]`, where `await loop.getaddrinfo( domain, None)` queries DNS asynchronously. It then iterates over `for coro in asyncio.as_completed(coros): result = await coro; yield result`.

---

Most concurrency bugs show up as a symptom first. Start from the symptom you see, then read across the row to its likely cause and remedy. If your service hangs, for instance, begin with the rows about timeouts and blocked loops.

---

## FILE docs/part-03-python/07-building-apis-and-microservices-with-fastapi.md

To use several cores, run uvicorn directly, as in `uvicorn app.main:app --host 0.0.0.0 --port 8000`. You can also run gunicorn with uvicorn workers, as in `gunicorn -k uvicorn.workers.UvicornWorker -w 4`. Each worker is a separate process with its own event loop and memory. State is not shared between workers, so a model loaded in each worker multiplies memory use. That is why GPU services typically run one worker per GPU. In production, several flags matter: `--workers`, `--limit-concurrency`, `--timeout-keep-alive`, `--proxy-headers` for use behind a proxy, `--log-config`, and `--timeout-graceful-shutdown` for graceful shutdown.

---

You can mount sub-apps and static files, as in `app.mount("/static", StaticFiles(...))`. For server-side HTML, chapter 4 of the book uses `Jinja2Templates(directory="templates/")`. It renders pages with `templates.TemplateResponse("todo.html", {"request": request, "todos": todo_list})`. Jinja2 gives you filters such as `default`, `escape`, `int`, `float`, `join` and `length`. It also gives you `{% if %}` and `{% for %}` blocks, `{% macro %}` for reusable components, and `{% extends "home.html" %}` with `{% block content %}` for template inheritance. That inheritance suits simple status dashboards.

---

The liveness probe at `/healthz` checks that the process and its event loop still respond. Keep it cheap, and keep it independent of external dependencies. Otherwise, a database blip restarts every pod. The readiness probe at `/readyz` checks that the pod can serve traffic now. That means the model is loaded, the database is reachable and the pod is not draining, so it flips to not-ready during shutdown. Use a startup probe for slow model loads.

---

Liveness probes that depend on external services can restart healthy pods. Readiness that never flips during shutdown, and grace periods that do not line up, drop requests during a deploy. Running migrations from every replica at startup causes conflicts. Connection pool exhaustion follows when `workers × pool` goes over the database limits.

---

## FILE docs/part-03-python/08-building-clis-agents-and-exporters-prometheus-exporters-redfish-client.md

Store files as YAML or TOML. The `tomllib` module is in the standard library from 3.11 onward. Load YAML with `yaml.safe_load`, and never with `yaml.load`. Validate what you load with pydantic, and merge the sources in the precedence order from principle 8 above. Support XDG paths such as `~/.config/fleet/config.toml`, add a `--config` override, and give users a `config show` command that prints the effective configuration with secrets redacted.

---

A DGX or HGX host that will not power on can leave you with no shell to work from. Redfish gives you a second route, through the BMC on the management network. Redfish is the DMTF RESTful API for that out-of-band management, and it replaces IPMI. BMCs on DGX, HGX and OEM servers expose it over HTTPS with JSON. Part 7 covers Redfish and BMCs in depth. Here we build a client skeleton.

---

Keep state small, and write it under `/var/lib/<agent>` using atomic writes. On startup, reconcile the desired state against the actual state rather than assuming a clean slate. The broker or the hardware is the source of truth, so the agent should read it.

---

Run the agent as a dedicated unprivileged user, and grant only the capabilities it needs. For privileged actions, use a narrow sudo rule or a small helper. Authenticate to the control plane with per-node credentials, such as mTLS or short-lived tokens. Validate every command the agent receives. An agent that runs arbitrary remote commands is a route for fleet-wide compromise.

---

## FILE docs/part-03-python/09-testing-quality-and-ci-for-python-tooling.md

In the test, `FakeKube` returns pod lists from a fixed sequence, and the fake clock moves forward in steps of 5. The test runs instantly, because the injected sleep does nothing. Injecting the clock and sleep makes time-dependent logic testable without waiting.

---

Reproducibility matters just as much. Use lock files, pinned base images, `--require-hashes` and hermetic builds, and record tool versions in the logs. GPU tests need self-hosted runners. Label those runners `gpu`, use ephemeral or containerised jobs, limit who can trigger them, and clean up state between jobs. NVIDIA publishes GPU-enabled container images and the container toolkit for this purpose.

---

For Kubernetes manifests and Helm, validate the manifests against schemas with `kubeconform` or `kubeval`. Run `helm lint`, and pipe `helm template` into `kubeconform`. Add `kube-linter` and `conftest` policies, plus `kind` smoke deploys. For declarative operator tests, use `chainsaw` or `kuttl`.

---

Interviewers often ask how you would test code that depends on hardware or a platform. A good answer starts with a pure core. It then uses recorded payloads and fakes at the boundaries, adds containers or kind for integration, and keeps a small hardware tier on labelled runners.

---

## FILE docs/part-03-python/10-python-for-data-and-ml-infrastructure-numpy-pandas-pytorch-essentials.md

Memory order decides which loops run fast. C order (row-major) and Fortran order (column-major) lay out elements in different sequences, so iterating along the contiguous axis is far faster. A non-contiguous array often has to be copied before you pass it to a C library or to `torch.from_numpy`.

---

RAPIDS cuDF offers a pandas-like API on the GPU. The `cudf.pandas` accelerator mode can run unmodified pandas code on the GPU where that is supported. It helps with large joins and groupbys, when the data already lives near the GPU. Check support and speedups for each workload.

---

Determinism costs speed. Use it for debugging and regression tests, and not necessarily for production training. Record the exact versions of your stack with each run, including `pip freeze`, CUDA, the driver, NCCL and the container digest. Bitwise reproducibility across different GPU counts is generally not achievable.

---

1. NumPy memory layout, views and broadcasting, with BLAS oversubscription. Use `compute_ndarray_strides()` and `broadcast_shapes()` in `code/part03/python_data_ml_infra.py` to explain three things. First, why `a = np.arange(12, dtype=np.float32).reshape(3, 4)` has strides `(16, 4)`, while `b = a.T` is a zero-copy view with strides `(4, 16)` and `C_CONTIGUOUS == False`. Second, how right-aligned broadcasting stretches `(1000, 1) + (1, 64)` to `(1000, 64)`, and why adding `(N,)` to `(N, 1)` silently builds an `(N, N)` matrix. Third, why `DataLoader(num_workers=8)` with the default `OMP_NUM_THREADS` causes severe CPU oversubscription.
2. Tabular data at scale, from Designing Machine Learning Systems, chapter 3. Use `compare_row_vs_columnar_io()` to explain three things. (a) How narrow dtypes (`int8`, `float32`, `category`, `string[pyarrow]`) and `usecols` cut DataFrame RAM by 2x to 5x. (b) Why reading 3 of 50 columns across 1M rows scans 400 MB in row-major CSV, but only 6 MB in 4x-compressed columnar Parquet. (c) How look-ahead leakage appears when you resample or normalise time-series features before splitting by time.
3. PyTorch tensors, asynchronous CUDA, pinned memory and autograd leaks. (a) Explain why timing `y = xg @ xg` on a CUDA tensor without `torch.cuda.synchronize()` only measures host kernel-launch overhead. Explain also why calling `loss.item()` on every step stalls the GPU pipeline. (b) Explain why `pin_memory=True` together with `to(dev, non_blocking=True)` is required to overlap host-to-device DMA transfers with compute. Then explain why appending `loss` to a history list, rather than `loss.item()` or `loss.detach()`, causes an out-of-memory crash.
4. Training and inference memory accounting, the caching allocator, and AMP (`bf16` versus `fp16`), from AI Engineering, chapters 2, 7 and 9. Use `estimate_adam_mixed_precision_memory_gb()` to calculate the exact weight, gradient and FP32 Adam optimizer state memory for a 7B parameter model (`14 + 14 + 84 = 112 GB`). Explain why `nvidia-smi` (`memory_reserved()`) stays high after you free tensors, and how `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` relates to that. Then explain why `bfloat16` does not need `GradScaler`, while `float16` does.
5. DataLoader starvation, `/dev/shm` bus errors and copy-on-access in forked workers. Use `diagnose_dataloader_vs_gpu_bottleneck()` to compute the effective GPU utilisation when per-sample CPU decoding takes 20 ms (`batch_size=64`, `gpu_compute_ms=100`) at `num_workers=0` (`7.8%`), and at `num_workers=16` (`100%`). Explain why Docker and Kubernetes containers default to a 64 MB `/dev/shm`, which kills DataLoader workers with `Bus error`. Explain also why a huge Python `list` of dataset metadata triggers copy-on-write page faults across forked workers.
6. Atomic checkpointing, `weights_only=True` versus `safetensors`, reproducibility and profiling. (a) Explain why checkpoints must be written to a temp file and then atomically renamed with `os.replace`. Explain why `torch.load(..., weights_only=True)` or `safetensors` (with `mmap`) is mandatory for untrusted weights. (b) List the settings that deterministic PyTorch runs need: `seed_everything`, `use_deterministic_algorithms`, `cudnn.benchmark = False` and `CUBLAS_WORKSPACE_CONFIG=:4096:8`. Then explain how `torch.profiler` with `schedule(wait=1, warmup=1, active=3)`, and `nsys`, reveal data-loader gaps and stragglers.

---

## FILE docs/part-03-python/11-python-under-the-hood-decorators-descriptors-and-metaprogramming-how-f.md

Several decorators ship with the standard library, and you will meet them often. `functools.lru_cache` and `cache` memoise results for hashable arguments. An unbounded `cache` leaks memory, and it is not safe on methods that hold `self` forever. `cached_property` caches a property on the instance, and `singledispatch` overloads a function on the type of its first argument. `total_ordering` fills in the missing comparison methods, while `partial` and `wraps` help with wrapping. `contextlib.contextmanager` turns a generator into a context manager. `dataclasses.dataclass`, `typing.overload` and `typing.final` shape classes and type hints. `abc.abstractmethod` marks methods that subclasses must implement. `property`, `classmethod` and `staticmethod` cover the common method kinds, and `atexit.register` runs a function when the interpreter exits.

---

Normal superclass inheritance can supply the call interceptor too. The superclass plays the role type plays in the other examples. The next variant shows that the dispatch model works the same way. It is atypical code, but it makes the mechanism visible:

---

Metaclass attributes are visible to classes, but not to the nonclass instances those classes make. A metaclass declaration sets up an instance relationship, and that relationship is not the same as superclass inheritance. Behavior defined in a metaclass applies to the classes made from it. It does not apply to those classes' own instances.

---

Two notes apply. Python runs at most one MRO search for an instance, or two for a class, for each name lookup. The first appearance of a name in a given MRO wins, whatever its kind. The implied object superclass sits at the end of every MRO. The methods `__getattr__` and `__getattribute__` add more rules, and Chapter 38 covers them.

---

## FILE docs/part-03-python/12-objects-types-and-data-structures-in-depth.md

This nested call works from the inside out. Python computes the power first, converts it to a string with `str`, and then measures the string with `len`. Both `str` and `len` work on many object types, and you will see them again.

---

A `for` loop needs a variable name and an iterable. For each item, it assigns the item to the variable and runs the indented block. The `for` loop is one of Python's main repetition tools. The others are comprehensions and the `while` loop, which you will meet later.

---

Dictionary usage has a few more rules. A dictionary is a mapping, not a sequence. Concatenation and slicing do not apply to it, and Python raises an error if you try them. You can create a key with a literal or by assigning to a new key. The end result is the same.

---

The parentheses around a tuple can often be left out, as shown here. Where commas do not have another meaning, the commas are what build the tuple. That is also why the REPL shows results in parentheses when you enter several comma-separated items.

---

## FILE docs/part-03-python/13-statements-iteration-and-control-flow-in-depth.md

Deprecation policies are not always followed. Major releases such as 3.0 broke existing code widely. Some newer changes were also made without the full process, because their promoters judged them justifiable or harmless. A steering committee is meant to enforce the policies, but it has done little to stop the flood of change.

---

Earlier chapters met other Boolean uses. Every object is inherently true or false. So it is easier to test an object directly, as in `if X:`, than to compare it to an empty value, as in `if X != '':`. For a string, the two tests are equivalent. `True` and `False` are the same as `1` and `0`. They are useful for initializing variables (`X = False`), for loop tests (`while True:`), and for showing results at the interactive prompt.

---

The final example builds a list as it goes, for later use. It collects the common items in two sequences. This is nearly an intersection, unless the sequences contain duplicate values. After the loop, `res` refers to a list of every item found in both `seq1` and `seq2`.

---

Past a certain point, a comprehension becomes too compact to be useful. Comprehensions suit simple iterations. For more involved work, a plain `for` statement is easier to understand and change. If a comprehension is hard for you to read, a `for` statement is probably the better choice.

---

## FILE docs/part-03-python/14-functions-scopes-and-arguments-in-depth.md

Each call to `outer` makes a self-contained package of changeable data. Its names do not clash with anything else in the program. You need `nonlocal` only for names that must change. Other enclosing names are kept automatically under LEGB. Also, nonlocal names are not visible outside the enclosing function.

---

Both functions work on any iterable, because they pass their arguments through the `list` built-in to force results. Files work as arguments too, along with sequences like strings. The code uses the `all` and `any` built-ins. These return `True` when all items, or any item, of an iterable are true, which means nonempty here. The loops stop when all or any of the listified arguments become empty after deletions.

---

Still, `async` functions are not truly optional. They were added to the language as syntax, through the `async` and `await` reserved words. You may have to reuse them, or face them in job interviews. This section gives a brief overview. Python's online resources cover the details.

---

This text does not cover Python's multithreading or multiprocessing tools. Both are valid ways to parallelize tasks, just as async functions are. Async alone received dedicated syntax, which favors one option and raises the bar for newcomers. Your goals may differ. For the full story, read Python's standard manuals before you wade deeper into async. For now, step back from this optional, complicated extension. Return to the fundamentals that nearly every Python program uses.

---

## FILE docs/part-03-python/15-modules-and-packages-in-depth.md

You can change `sys.path` in code to influence future imports, and this also works in a REPL. Be careful, though. Removing a folder can cut off access to important tools. Your changes disappear when the program or REPL ends. To make path changes last across scripts and sessions, use the lasting techniques above.

---

To use the package, load its modules the same way you would load a simple `.py` file. You can do this in a REPL or in another script. Use dots to name the path below the `dir0` folder on the search path. In a REPL, the current directory plays that role:

---

A relative import looks only inside the named package. It does not consult the folders on `sys.path`. It also skips the check for built-in and frozen modules. Relative syntax works only when a file is used as part of a package. It fails in any other use. That has both good and bad effects, as the next sections show.

---

In a script, this statement must come first among the executable statements. A docstring or comment may come before it. It changes how Python compiles that one module. At the interactive prompt, the feature stays on for the rest of the session.

---

## FILE docs/part-03-python/16-classes-and-object-oriented-programming-in-depth.md

Let us make `job` optional. It will default to `None`, which means the person is not currently employed. If `job` defaults to `None`, `pay` should default to `0` for consistency. Python requires this: once one argument has a default, every argument after it must have one too.

---

Testing by hand at the prompt has limits. Retyping test cases each session gets tedious. Most programmers use the prompt for quick one-off checks. For real tests they put code at the bottom of the file that holds the class.

---

Some attributes may not appear in `__dict__`. A class that defines `__slots__` stores attributes differently. The feature is optional, somewhat obscure, and covered in full in Chapter 32. Slots belong to the class, not the instance, and they are rarely used. We can safely ignore them here and focus on the normal `__dict__`.

---

We start with the simple case. The next example lists attributes attached to an instance. The file `listinstance.py` defines a mix-in called `ListInstance`. It overloads `__str__` for every class that includes it in its header. Because it is a class, `ListInstance` works for instances of any client subclass.

---

## FILE docs/part-03-python/17-exceptions-unicode-managed-attributes-and-decorators.md

1. The expression is evaluated. The result is a context manager, an object that must have `__enter__` and `__exit__` methods.
2. The context manager's `__enter__` method is called. Its return value is assigned to the `as` variable, if present. Otherwise, the value is discarded.
3. The code in the nested `with` block runs.
4. If the block raises an exception, the `__exit__(type, value, traceback)` method is called with its details. These three values match what `sys.exc_info` returns. If `__exit__` returns a false value, the exception is reraised. Otherwise, the exception ends there. The exception should normally be reraised, so it propagates outside the `with` after `__exit__` returns.
5. If the block raises no exception, `__exit__` still runs. Its `type`, `value`, and `traceback` arguments are all `None`. Its return value is ignored.

---

When an `except` catches an exception, the instance belongs to the listed class or to one of its subclasses. So the specific kind is always available. You can read it through `type(X)` or through the `__class__` attribute. The variant `categoric2.py` shows this with the `as` form:

---

This version is artificial for such a small case. The generic methods shine in delegation code, where each access is validated and routed to a wrapped object. For a single managed attribute, a property or descriptor may do as well and add no extra calls for unmanaged attributes.

---

For a plain function, only `__call__` runs. For a method, the lookup `pat.giveRaise` triggers `__get__` first. The returned `wrapper` keeps the subject instance. The call expression then runs `wrapper.__call__`, which calls `tracer.__call__`, which finally calls the original method. The `wrapper` object routes control back to the one decorator instance, so every call shares the same counter.

---

## FILE docs/part-10-gpu-cuda/01-why-gpus-cpu-versus-gpu-and-throughput-design.md

Real-world experience shows that even minor tweaks to GPU kernels or memory access patterns can produce outsized gains. FlashAttention is a classic example. It reimplements transformer attention in a hardware-aware way. It tiles GPU computation, which minimizes the reads and writes issued to GPU memory. That change shrinks attention, a major bottleneck, to a fraction of total runtime.

---

Memory is a second major bottleneck. A 100-trillion-parameter model needs about 200 TB of GPU memory just to load FP16 weights. That is 100 trillion parameters times 2 bytes each. The figure is roughly three orders of magnitude above the 180 GB of addressable HBM on one NVIDIA Blackwell B200.

---

Feeding data fast enough to keep such a model busy is also hard. Communication overhead grows as the model is split across 1,000 B200 GPUs or 700 B300 GPUs. One training run can consume millions of GPU-hours and megawatt-hours of energy. That cost is why the era of 100-trillion-parameter AI forces a redesign of system design. Hardware, algorithms, and software must coevolve.

---

The announcement briefly shocked US financial markets. NVIDIA's stock dropped ~17% in a single day, on fears that efficiency gains would need less NVIDIA hardware. That reaction was somewhat overblown, and the stock recovered in later sessions. It still shows how an efficiency breakthrough can move global markets.

---

## FILE docs/part-10-gpu-cuda/02-the-execution-model-threads-warps-blocks-and-sms.md

A compiled CUDA binary can run on a small 2-SM test GPU today and scale across a 132-SM GPU tomorrow without code changes. CUDA achieves that generational scalability by organizing parallel software into a nested hierarchy that maps onto the physical hardware tree.

---

In GPU programming, often called "Me" programming, you replace the outer CPU `for` loop with a grid of threads where each thread computes its own global index. When the host launches `myKernel<<<blocksPerGrid, threadsPerBlock>>>(d_input, N)`, each thread calculates its unique 1D coordinate using three built-in variables: `blockIdx.x`, `blockDim.x`, and `threadIdx.x`.

---

Two physical trade-offs govern multidimensional tile selection. First, align the fastest-changing dimension (`blockDim.x`) to warps and cache lines so adjacent threads in a warp read contiguous memory addresses. Second, balance contiguous width against perimeter halo reloads. In stencil or convolution kernels, each tile loads a border halo of neighbor pixels from adjacent tiles. A flat 64 by 2 tile has a long perimeter that duplicates many HBM halo loads. A square or near-square tile such as 16 by 16 (256 threads) or 16 by 8 (128 threads) minimizes the perimeter-to-area ratio while preserving coalesced row reads. Using C++ lambda wrappers in portability frameworks such as SYCL, Kokkos, and Raja lets teams express these tiled loop bodies once across CPU and GPU backends.

---

1. **SASS (Streaming ASSembler)**. Native machine instructions compiled for one specific GPU architecture, such as `sm_80` for Ampere, `sm_90` for Hopper, or `sm_100` for Blackwell. Family-specific targets like `sm_100f` and `compute_100f` restrict portability to devices within that exact feature family. Native SASS runs only on the architecture family it was built for.
2. **PTX (Parallel Thread Execution)**. NVIDIA's virtual instruction-set intermediate representation. When you ship a fatbinary containing architecture-specific SASS cubins plus virtual PTX, any future GPU driver can Just-In-Time compile the embedded PTX into native machine code at startup.
3. **Pre-flight verification with `CUDA_FORCE_PTX_JIT=1`**. In continuous integration or node qualification tests, run your binary with the environment variable `CUDA_FORCE_PTX_JIT=1`. That flag forces the CUDA driver to ignore embedded SASS and JIT-compile the embedded PTX. If a build script omitted PTX from the fatbinary, the test fails immediately in CI rather than crashing in production on next-generation GPU nodes.

---

## FILE docs/part-10-gpu-cuda/03-the-gpu-memory-hierarchy.md

When an AI workload runs much slower than the GPU's peak math rating, engineers often guess blindly between changing batch sizes, rewriting kernels, or buying faster hardware. Without a clear map of where bytes sit and how many cycles each hop costs, you cannot tell whether threads are starving on off-chip DRAM or fighting over on-chip scratchpad capacity. Every step further away from the SM arithmetic units gives you roughly an order of magnitude more storage capacity at the cost of higher latency and lower per-SM bandwidth.

---

The hardware organizes storage into fast on-chip tiers per SM, a shared GPU-wide L2 cache, off-chip HBM stacks, and the external host interconnect. On-chip levels respond in a few cycles at terabytes to tens of terabytes per second per SM. Off-chip HBM requires hundreds of cycles per round trip.

---

Three practical techniques eliminate shared-memory bank conflicts.
- **Array Padding with `__shared__ float tile[32][33]`:** Adding one unused padding column changes the row stride so column width and bank count are coprime. Column reads map each thread in the warp to a unique bank and eliminate all conflicts.
- **XOR Index Swizzling:** Libraries like CUTLASS transform the column index with a bitwise XOR operation `col_swizzled = col ^ row`. This permutes bank assignments across rows with zero memory overhead.
- **Warp Shuffle Intrinsics (`__shfl_sync` and `__shfl_down_sync`):** When threads only need to exchange or reduce data within a single warp, do not write to shared memory at all. Warp shuffle intrinsics read another lane's register directly across the SM sub-partition in logarithmic butterfly steps. This matches Cooperative Groups `__reduce_sync` performance with zero shared memory and zero barriers.

---

A model can fit comfortably inside GPU memory with plenty of free space and still miss its production latency SLA. Platform engineers also hit mysterious multi-millisecond stalls between kernels when host BIOS settings cap the PCIe aperture or when training loops invoke synchronous OS memory allocators.

---

## FILE docs/part-10-gpu-cuda/04-tensor-cores-and-numerical-precision.md

When two workloads run on the exact same NVIDIA GPU, both can report 91% utilization in `nvidia-smi`, yet one finishes in 10 milliseconds while the other takes 500 milliseconds. The physical GPU is not one generic calculator. Each Streaming Multiprocessor contains multiple distinct execution engines: CUDA Cores, Tensor Cores, Special Function Units, Load/Store Units, and on graphics or universal SKUs, RT Cores. The top-level `nvidia-smi` utilization metric only reports that some engine was active during the sampling interval.

---

On a modern data center GPU such as Hopper H100 or Blackwell B200, the vast majority of the chip's mathematical horsepower lives inside its Tensor Cores. Unlocking those matrix pipelines requires satisfying a strict joint contract between hardware and software.
- On a Blackwell B200, standard scalar FP32 compute peaks at a tiny fraction of what dense NVFP4 Tensor Core compute delivers on the exact same silicon.
- Lowering precision does not just speed up matrix math. It shrinks every weight tensor in HBM and multiplies the number of weights carried inside every cache line.
- Yet a single unaligned matrix dimension or a missing PyTorch configuration flag (`torch.set_float32_matmul_precision('high')`) can cause the software stack to bypass the Tensor Cores silently. The workload then falls back to general arithmetic pipelines with zero error messages.

---

This chapter dissects the execution engines inside an SM and maps the exact bit layouts and dynamic-range trade-offs of every AI numerical format. It covers FP64, FP32, TF32, FP16, BF16, FP8, INT8, and NVFP4. It then explains how the Transformer Engine, structured sparsity, Blackwell Tensor Memory with TMA, and NVIDIA CUTLASS keep Tensor Cores running near peak utilization.

---

This is not a fully automatic decision for every layer in every framework. Check which layers run in which precision, and compare accuracy before you trust a faster run. Reduced precision is only a gain when the model still gives the same answers.

---

## FILE docs/part-10-gpu-cuda/05-the-roofline-model-and-performance-modelling.md

Think of a restaurant kitchen to visualize how compute and memory interact. Compute is the chef's chopping speed at the cutting board. Memory bandwidth is the waiter's running speed bringing ingredients from the pantry. Arithmetic Intensity is the recipe's ratio of chopping work to ingredients fetched.

---

Elementwise kernels such as vector addition, activation functions, and bias adds often surprise engineers by utilizing less than 1% of a GPU's peak compute. Reproducing the worked analysis from *AI Systems Performance Engineering* shows why `C[i] = A[i] + B[i]` in FP32 is starving for memory bandwidth on a Blackwell B200 GPU. Each thread loads two floats, performs one addition, and writes back one float.

---

A single GPU kernel's Roofline is only one piece of a production AI service. When an inference endpoint misses its latency objective or a distributed training job slows down, `nvidia-smi` GPU utilization alone cannot tell you why. The GPU could be thermally throttled, starving for host input, waiting on an uncoalesced memory stall, or blocked on a slow peer rank. An end-to-end workload falls into one of six distinct system bottleneck regimes.

---

1. Writing out the symbolic matrix multiplication arithmetic-intensity formula `I(B, K, N, b) = (2 * B * K * N) / ((B*K + K*N + B*N) * b) ≈ (2 * B) / b` in Section 2.2 and `calc_gemm_arithmetic_intensity` in `code/part10/roofline_model.py` is my inference. It links the single-stream scenarios in the notes to the H100 ridge point.
2. Encoding the elimination workflow from the notes into the deterministic Python classifier `classify_gpu_workload_bottleneck` in `code/part10/roofline_model.py` and Section 4 is my inference.

---

## FILE docs/part-10-gpu-cuda/06-gpu-interconnects-pcie-nvlink-nvswitch-and-nvlink-c2c.md

Consider a concrete production incident from the cited notes. A team launches a four-GPU training job on a healthy dual-socket server. Two-GPU runs scale well, but four-GPU runs barely beat two GPUs even though every device passes health checks. When the engineer runs `nvidia-smi topo -m`, the physical wiring explains the stall.

---

The Peripheral Component Interconnect Express bus is the standard internal highway of a server motherboard. It connects CPUs, GPUs, network adapters, and NVMe SSDs. High-speed accelerators and 400G or 800G NICs plug into 16-lane x16 slots, whose generational bandwidths are listed below.

---

Why couldn't hardware designers simply add more PCIe lanes to solve intra-node GPU communication? Tensor Parallelism, Expert Parallelism for Mixture-of-Experts models, and high-frequency gradient synchronization require bandwidth within the same order of magnitude as HBM. They need hundreds to thousands of gigabytes per second with microsecond latency, which standard motherboard PCIe traces cannot deliver.

---

On Kubernetes nodes where a subset of GPUs and a high-speed NIC share a NUMA socket, configure the kubelet Topology Manager and CPU Manager in `/var/lib/kubelet/config.yaml`. The kubelet queries `nvidia-device-plugin` and `sriov-network-device-plugin` for NUMA hints and rejects unaligned placements at pod admission time.

---

## FILE docs/part-10-gpu-cuda/07-gpu-generations-and-product-line-ampere-hopper-blackwell-pcie-versus-s.md

Enterprises that install GeForce drivers in commercial data centers to serve APIs or train commercial models violate this license agreement. NVIDIA audits commercial deployments, exposing violators to legal liability and forced shutdowns. Senior infrastructure architects protect their organizations by deploying only enterprise-licensed RTX Professional or Data Center hardware.

---

Hopper H100 attacked this memory wall by introducing native 8-bit floating-point Tensor Cores paired with a hardware Transformer Engine. Halving weight precision from 16 bits to 8 bits cuts memory bandwidth traffic in half. Because 8-bit floats have a narrow dynamic range, the Transformer Engine tracks tensor statistics in hardware during runtime and dynamically scales layers between FP8 and 16-bit formats to preserve accuracy. Hopper also upgraded the memory subsystem to HBM3, added DPX dynamic programming instructions, and introduced Thread Block Clusters that allow thread blocks across different SMs to share data directly without round-tripping through global HBM.

---

By 2024, semiconductor fabrication hit the optical reticle limit, which caps the maximum area of a single monolithic silicon die that photolithography scanners can print. To keep scaling compute density, NVIDIA moved to a dual-die multichip module architecture with Blackwell B200.

---

Because the PCIe envelope restricts power to half of the SXM budget, NVIDIA runs the silicon at lower voltages and reduced clock frequencies. An H100 PCIe delivers lower compute throughput and uses slower HBM2e memory than its SXM5 counterpart. Furthermore, standard motherboards lack NVSwitch chips. NVIDIA offers physical NVLink Bridge clips that attach across the top edges of adjacent cards, but these bridges only link GPUs in isolated pairs at reduced bandwidth. Traffic between separate pairs must still cross the slow host PCIe bus.

---

## FILE docs/part-10-gpu-cuda/08-operating-gpu-nodes-nvidia-smi-topology-clocks-and-throttling.md

Collecting every counter on a GPU server without a clear mental model overwhelms operators during an outage. If a dashboard only plots one-minute averages, a sub-second thermal spike or a brief PCIe stall vanishes into the average, leaving the team guessing why latency jumped.

---

On a GPU, host operating system queues cannot see hardware saturation. The GPU schedules tens of thousands of threads internally across hardware warp schedulers inside each SM. Meanwhile, CUDA streams push commands into hardware rings managed by GPU firmware. When a host thread submits kernels faster than the GPU can finish them, the CPU thread blocks inside `cudaStreamSynchronize()` or driver calls. That thread then shows up on the host in an asleep `S` state or uninterruptible `D` state. Conversely, if the host launches tiny kernels one by one, the GPU empties its command ring between launches and drops into clock-gated `GPU_IDLE` states. Diagnosing GPU performance therefore requires inspecting internal hardware counters rather than host run queues.

---

When an on-call engineer treats GPU dashboard percentages like CPU metrics, every diagnosis goes wrong. A job that is completely deadlocked can report 100% GPU utilization, and a healthy training run can report 95% memory usage from the first batch. Similarly, a thermally throttled card can look fully utilized while running at reduced speed (`nvidia-devops` V16 Ch 3).

---

Writing a custom monitoring script that shells out to `nvidia-smi` in a tight loop wastes CPU cycles and churns driver handles. Both `nvidia-smi` and NVIDIA Data Center GPU Manager are user-space tools built on top of the NVIDIA Management Library in `libnvidia-ml.so`.

---

## FILE docs/part-10-gpu-cuda/09-the-nvidia-software-stack-driver-cuda-toolkit-container-toolkit-compat.md

To cross from user space into kernel space, the user-mode driver opens Linux character device files and issues `ioctl()` system calls to the Kernel-Mode Driver. The core kernel module `nvidia.ko` handles device initialization, memory allocation, and command submission. Three companion kernel modules provide Unified Virtual Memory paging, display mode-setting, and zero-copy GPUDirect RDMA peer memory registration for InfiniBand and RoCE network adapters.

---

Engineers often wonder why `nvidia-smi` prints a CUDA version in its header even on a bare-metal host where the CUDA Toolkit is not installed. That banner reports the highest CUDA Driver API capability supported by the installed host driver, not which CUDA Runtime library lives inside a container.

---

As documented in Chapter 9 of the BCM 11 installation manual, BCM splits GPU software into local node-image packages and shared head-node packages. The newer open-source driver packages replace the older `cuda-driver` packages and compile the kernel module during package installation rather than at boot. Because kernel module compilation happens when the image is updated, Section 2.3's rule that the kernel module and user-mode driver must match applies to the entire software image at once. Changes to the software image are then pushed to running nodes with `imageupdate` in `cmsh`.

---

When a node reports missing GPUs, walk the stack from the bottom up rather than guessing at container flags. Checking PCI enumeration, `nvidia-smi`, loaded kernel modules, character device nodes, and dynamic linker paths isolates whether the break is in hardware, kernel space, or user space.

---

## FILE docs/part-10-gpu-cuda/10-fabric-manager-nvsm-and-nvlink-domains.md

First, the Fabric Manager package communicates with the kernel NVSwitch driver over a private internal ABI, so its package version must match the NVIDIA driver version exactly. Second, Fabric Manager takes roughly 15 seconds at boot to train 144 NVLink sub-links and program four NVSwitch ASICs, whereas `containerd` and `kubelet` start faster. In systemd, `Wants=` or `Requires=` declares a dependency without enforcing startup order. You must therefore pair `Wants=` with `After=nvidia-fabricmanager.service` on both `containerd` and `kubelet`. Third, when `dmesg` logs Xid 74 for an NVLink error, remember from Chapter 9.3 that each SXM GPU is a bolted Field-Replaceable Unit. The four NVSwitch ASICs, however, are soldered directly onto the HGX baseboard and require a full baseboard RMA if a switch ASIC fails.

---

When an HGX or DGX node reports a degraded NVLink fabric or missing PCIe device, engineers need a single in-band tool to check component health and collect a support archive for NVIDIA Enterprise Support. Whereas the Out-of-Band BMC and Redfish interface monitor the chassis from outside the operating system over a dedicated management network, NVIDIA System Management runs inside Linux. It monitors GPUs, NVSwitches, NVLink-C2C, DIMMs, NVMe drives, fans, and power supplies.

---

Even when every server has healthy NVSwitches, GPUDirect RDMA, and matched ConnectX-7 adapters, the cluster will stall if the top-of-rack and spine switches are oversubscribed or shared with bulk storage traffic. Because all ranks in a synchronous training collective transmit at line rate at the exact same microsecond, traditional data-center oversubscription ratios immediately cause congestion.

---

1. **Systemd ordering for Fabric Manager.** On an eight-GPU HGX H100 server, Table 1.2 shows that Fabric Manager takes roughly 15 seconds at boot while `containerd` and `kubelet` start faster. Explain what happens to the first training pod scheduled after a reboot if `kubelet` starts before Fabric Manager completes. Then write the exact systemd drop-in file for `containerd.service` and `kubelet.service` that prevents the race.
2. **BCM `nvsm` and `nvdebug` incident workflow.** A DGX node logs an NVLink error. Write the BCM `cmsh` device mode commands to inspect active NVSM alerts and verify that the driver and Fabric Manager versions match. Then write the commands to trigger a full health dump and collect an `nvdebug` bundle for the health-check log group.
3. **Kubernetes single-NUMA admission math.** Using Table 4.1, a dual-socket HGX server has 128 CPU cores and 8 GPUs split evenly across two NUMA nodes, with 2 cores reserved by system daemons on NUMA 1. Calculate how many pods requesting 16 integer CPUs and 1 GPU are admitted under the single-NUMA policy. Then state how many free CPU cores and GPUs remain stranded on NUMA 1 and why reducing the pod request to 12 CPUs admits all 8 pods.
4. **Isolating a slow cluster with the 3-step benchmark hierarchy.** Using Table 4.2, diagnose four separate tickets. First, `nvbandwidth` reports half of normal PCIe Gen5 bandwidth. Second, `ibstat` shows physical link up but logical state initializing. Third, `ib_write_bw` reports full line rate while `nccl-tests` prints InfiniBand transport without GPUDirect RDMA at 50 Gbps. Fourth, all three C++ benchmarks pass at full speed while a PyTorch DDP model with tiny layers runs 40% slow. State the root cause and fix for each.
5. **Why ConnectX-7 requires PCIe Gen5 x16.** Using Table 3.3, convert a 400 Gbps ConnectX-7 port and an 800 Gbps ConnectX-8 port into Gigabytes per second. Compare them against the unidirectional bandwidth of PCIe Gen4, Gen5, and Gen6 x16 slots, and explain why pairing each H100 with two 200 Gbps ConnectX-6 cards fails to match a single ConnectX-7 card.
6. **Designing a 128-node non-blocking fat-tree.** Using Table 3.4, given 128 DGX H100 servers and 64-port Quantum-2 NDR switches, calculate how many servers fit in one rail-optimized Leaf Group. Then calculate how many Leaf Groups, total Leaf switches, and 64-port Spine switches are required for a 1:1 non-blocking fabric.

---

## FILE docs/part-10-gpu-cuda/11-cuda-programming-basics-kernels-indexing-and-memory.md

An AI infrastructure engineer rarely writes custom CUDA kernels from scratch every day. Yet production training jobs still crash with illegal memory access faults. Other jobs hang forever on an A100 after passing desktop unit tests, or spend most of their runtime inside memory allocation calls. When these failures wake up the on-call team, the root cause lives inside the fundamental rules of the CUDA execution and memory model.

---

In the CUDA heterogeneous model, the Host consists of the CPU and system DDR5 RAM. It runs `main()`, reads files and network sockets, allocates device buffers, and queues asynchronous work. The Device consists of the GPU and its HBM and on-chip SRAM. It executes parallel kernels queued by the host. You tell `nvcc` where each function executes by placing an execution space specifier on the declaration.

---

When a team ports a CPU loop over an array of length $N$ to CUDA, two classic off-by-one bugs show up whenever $N$ is not a multiple of the block size. If the programmer uses integer division to compute the block count, the kernel finishes without reporting any error while leaving the tail elements at zero. If the programmer switches to ceiling division so the grid covers the tail, but forgets a bounds check inside the kernel, the extra threads in the last block write past the end of the buffer.

---

Teams new to GPU acceleration often port a simple math function to CUDA and measure the GPU kernel alone at under a tenth of a millisecond. They then wonder why their end-to-end service actually got slower. They overlook the time spent moving inputs from CPU system RAM into GPU HBM over the PCIe bus and copying outputs back. When an operation performs only one or two arithmetic operations per element, PCIe data movement completely dominates the runtime.

---

## FILE docs/part-10-gpu-cuda/12-streams-events-asynchronous-copies-and-pinned-memory.md

Look at time window 5 to 7 in the Gantt chart above. All three physical engines work simultaneously. Stream 0 copies Batch 0 outputs back to the host on Copy Engine 1, Stream 1 executes Kernel Batch 1 on the SMs, and Stream 2 copies Batch 2 inputs to the device on Copy Engine 0.

---

Even when a developer creates multiple streams, a single stray logging call, helper kernel, or library call launched without an explicit stream argument can serialize the entire GPU. That surprise happens because CUDA's legacy default stream was originally designed to make single-stream programs safe. It acts as a global barrier across all regular blocking streams.

---

If you create two non-blocking streams and call `cudaMemcpyAsync` on standard C++ vector or `malloc()` host buffers, Nsight Systems shows zero overlap. The second stream waits until the first stream's transfers and kernel completely finish. Worse, your Host-to-Device transfer bandwidth sits at less than a quarter of PCIe capacity. The culprit is standard OS pageable memory, which a GPU DMA engine cannot read directly.

---

In *AI Systems Performance Engineering* Chapter 11, Chris Fregly details the four LLM scenarios where dynamic allocations occur inside active streams.
- Per-batch attention scratch buffers allocate a 16 MB workspace for raw attention scores before softmax and free it immediately after the layer completes.
- Variable-length input sequences occur when Batch $N$ has 512 tokens and Batch $N+1$ jumps to 1,024 tokens, requiring larger intermediate activation buffers on the fly.
- Autoregressive decoding causes KV-cache and activation buffers to grow as new tokens are generated.
- Layerwise model pipelining runs Transformer layers 0 through 5 for Batch $t+1$ on Stream 0 while Stream 1 executes layers 6 through 11 for Batch $t$.

---

## FILE docs/part-10-gpu-cuda/13-memory-access-patterns-and-profiling.md

Second, naive matrix and attention kernels repeatedly read the same inputs directly from off-chip HBM. Staging reusable tiles in fast on-chip shared memory cuts off-chip sector traffic by more than eightfold. Arithmetic intensity rises and compute throughput jumps by more than an order of magnitude.

---

Shared-memory tiling partitions the input matrices into square tiles stored in fast on-chip SRAM arrays. First, all threads in the thread block cooperatively load one float of each input tile from HBM using coalesced warp reads. Second, the block executes `__syncthreads()` to ensure the entire tile is resident in shared memory before any thread reads it.

---

Third, every thread loops across the elements of the cached tile and accumulates products from fast on-chip shared memory instead of slow off-chip HBM. Each global memory load is reused 32 times on chip. Fourth, the block calls `__syncthreads()` a second time before advancing to load the next tile. This second barrier prevents faster threads from overwriting the shared buffer while slower threads are still reading it.

---

1. **Warp sector and cache-line math across strides:** Using `analyze_warp_global_memory_access()`, calculate how many cache lines and sectors a warp touches when reading floats under four patterns. Evaluate an aligned contiguous read, a contiguous read offset by four bytes, a stride of two, and a stride of eight. Report the theoretical Global Memory Load Efficiency for each case.
2. **Vectorized `float4` vs. Blackwell `float8` warp transactions:** For a single warp, calculate the total bytes moved per instruction, the number of cache lines, the number of sectors, and the PTX instruction emitted when using `float4` on Hopper versus `alignas(32) float8` on Blackwell. Then explain why casting an unaligned interior pointer offset fails even though `cudaMalloc` returned a 256-byte-aligned base pointer.
3. **Shared-memory tiling and register residency:** Using the numbers from *AI Systems Performance Engineering* Chapter 7, state the global load sector reduction, arithmetic intensity shift, and GFLOPS speedup achieved by 32 by 32 shared-memory tiling. Next, calculate the shared-memory footprint and total registers per block for a 64 by 64 tile using minimal registers versus double-buffered registers on a Blackwell SM.
4. **Shared-memory bank conflict math:** Prove mathematically using modulo arithmetic why reading down column zero across all lanes causes every thread to hit the first bank when the row stride is 32 floats. Then prove why adding one padding column maps all lanes to distinct banks with about three percent memory overhead.
5. **Warp shuffle vs. shared-memory reduction:** Trace the five butterfly iterations of `__shfl_down_sync` for a warp where each lane starts with its one-based lane number and verify the final sum in the first lane. Explain why this pattern cannot reduce across two different warps without shared memory or cluster barriers.
6. **Read-only cache and TMA double-buffering:** Compare the Nsight Compute metrics from the read-only cache and TMA tables in *AI Systems Performance Engineering* Chapter 7. Then write the four-method `cuda::pipeline` stage sequence (`producer_acquire`, `producer_commit`, `consumer_wait`, `consumer_release`) that overlaps TMA tile prefetching with tile computation.

---

## FILE docs/part-10-gpu-cuda/14-occupancy-warp-efficiency-and-instruction-level-parallelism.md

Work through the regimes in order, then verify each change. After a fix, profile again and confirm that the targeted stall or metric improved. Memory stalls should drop after tiling, and achieved occupancy should rise after you tune the block size. Also watch total runtime, because one bottleneck can hide another.

---

Higher occupancy is not always faster. Very low occupancy, around 10 to 20 percent, hurts performance because too few warps can hide latency. Pushing occupancy to 100 percent does not always help, because memory bandwidth and instruction dependencies can become the limit instead. You should check other hardware counters before you chase a higher number.

---

Divergence is easy to spot in source code. Any per-thread condition, such as a threshold check, a sparse-data loop, or a data-dependent filter, can trigger this serial pattern. To reclaim the lost time, eliminate or flatten the branch. You can make the condition uniform across the warp, pull it out of a tight loop, or replace it with arithmetic or a lookup table.

---

You can also rewrite a condition so it is warp-unanimous, meaning all 32 threads of a warp agree on it. A common trick uses the warp index. Compute `int warpId = threadIdx.x / 32;`, and then let half the warps run task A and the other half run task B. Every warp still evaluates the check, but all its lanes agree, so no warp splits. This works well when you can divide the work into coarse blocks of 32 threads.

---

## FILE docs/part-10-gpu-cuda/15-kernel-efficiency-and-arithmetic-intensity.md

In *AI Systems Performance Engineering* Chapter 9, Blackwell B200 compute throughput jumps by two orders of magnitude across precision formats while memory bandwidth remains finite. Even inside a multi-GPU NVLink rack, kernels with low FLOPs per byte saturate memory and interconnect buses first. Infrastructure engineers must raise arithmetic intensity so each memory transaction feeds dozens of math operations on chip.

---

Staging a tile in Shared Memory reduces global HBM traffic. However, threads can still bottleneck on Shared Memory bandwidth if every scalar multiply-add reads operands from shared banks. When warps issue back-to-back math instructions, shared memory access latency and bank pressure limit how fast the arithmetic units can run. Adding a register-level staging tier between Shared Memory and the compute units removes this bottleneck.

---

Kernel fusion combines multiple operations into a single launch so intermediate values stay inside registers or Shared Memory. Vertical fusion chains sequential producer-to-consumer operations on the same tensor, while horizontal fusion batches independent parallel projections into one kernel. In the `fusedL2Norm` kernel from *AI Systems Performance Engineering* Chapter 9, a single thread block per row accumulates sums of squares in registers using `fmaf`. It then reduces the row sum in Shared Memory and normalizes the row in place.

---

The copy side matters as much as the buffer count. The book recommends `cuda::memcpy_async` for bulk tensor transfers, because it maps to the Tensor Memory Accelerator (TMA). Reserve `cp.async` for niche cases that TMA cannot express, and those cases are rare. Whichever copy you use, make sure it has completed before you read the data.

---

## FILE docs/part-10-gpu-cuda/16-intra-kernel-pipelining-warp-specialization-and-thread-block-clusters.md

Even the most heavily tuned attention pipelines face physical overlap limits when data movement and online softmax rescaling compete for resources. In practice, FlashAttention-3 achieves roughly seventy-five percent of peak FP16 FLOPS using multi-stage asynchronous pipelining. In the `gemm_tiled_pipeline` kernel below, priming the ring buffer in a prologue loop and stepping through ring-buffer slots in steady state cuts execution time in half compared to naive tiling.

---

A persistent kernel eliminates both launch overhead and tail-wave draining by launching a single long-lived grid that stays resident across all SMs until the entire work queue is empty. On a GPU with 132 SMs, launching one block of 256 threads per SM creates 33,792 persistent worker threads that pull tasks continuously from a device-side atomic counter `atomicAdd(&g_index, 1)`. The host pays the twenty-microsecond launch cost only once, and irregular task durations balance automatically across SMs.

---

During autoregressive LLM decode, generating each token requires executing dozens of small operators across eighty or more Transformer layers. Standard serving engines launch separate kernels for RMSNorm, QKV projections, rotary embeddings, attention, all-reduce communication, and MLP blocks on every layer. At small batch sizes, host launch latency and inter-kernel barrier gaps dominate token generation time.

---

Launching a Thread Block Cluster requires either compile-time `__cluster_dims__` annotations or runtime configuration with `cudaLaunchKernelEx` and `cudaLaunchAttributeClusterDimension`. Inside the kernel, every block in the cluster must declare the exact same dynamic shared memory size and synchronize around remote DSMEM accesses using `cluster.sync()`.

---

## FILE docs/part-10-gpu-cuda/17-inter-kernel-pipelining-synchronization-and-stream-ordered-allocation.md

Dynamic deep learning workloads frequently allocate and free temporary tensors inside the training or inference loop. When a runtime falls back to OS-level blocking allocations, the driver halts every stream on the GPU to update page tables. Even PyTorch's default caching allocator, which is stream-aware on cache hits, synchronizes the entire device whenever a cache miss triggers a fresh allocation from the driver.

---

A single stray CUDA call that omits its stream argument can silently destroy multi-stream concurrency across an entire application. By default, omitting the stream argument sends work to the legacy default stream, which acts as a global bidirectional barrier against every blocking stream on the GPU. Engineers debugging Nsight Systems traces recognize this bug immediately when all active streams stop at a vertical wall before and after a tiny helper kernel.

---

A single pipeline object inside a thread block overlaps global-to-shared loads with compute. But the compute warp and storer warp still contend if they share a single stage barrier. In addition, a single kernel launch still pays host-to-device and device-to-host transfer latency between batches. Combining a dual-pipeline three-role warp-specialized kernel with multiple CUDA Streams solves both bottlenecks at once.

---

Normally, two kernels enqueued into the same CUDA Stream execute strictly back-to-back. The hardware scheduler will not start the secondary kernel on any Streaming Multiprocessor until every thread block of the primary kernel has finished its epilogue and exited. During the tail wave of the primary kernel, most Streaming Multiprocessors sit idle while the secondary kernel waits behind the stream boundary.

---

## FILE docs/part-10-gpu-cuda/18-dynamic-scheduling-cuda-graphs-and-device-initiated-orchestration.md

1. Diagnose L2 atomic contention using Nsight Compute counters atomic_transactions and atomic_transactions_per_request and implement a warp-leader batched atomic work queue using `__activemask()`, `__ffs()`, atomicAdd, and __shfl_sync.
2. Capture, instantiate, warm up, and replay CUDA Graphs in C++ and PyTorch using cudaStreamBeginCapture, cudaGraphInstantiate, cudaGraphLaunch, torch.cuda.CUDAGraph, `torch.cuda.graph_pool_handle()`, and cudaGraphExecUpdate.
3. Launch CUDA Graphs directly from device kernels using cudaGraphInstantiateFlagDeviceLaunch and cudaGraphUpload across cudaStreamGraphFireAndForget, cudaStreamGraphTailLaunch, and cudaStreamGraphFireAndForgetAsSibling, and build Conditional Graph Nodes.
4. Implement Dynamic Parallelism with `-rdc=true` where a parent kernel spawns child kernels on the device, and configure cudaLimitDevRuntimePendingLaunchCount and cudaLimitStackSize.
5. Orchestrate multi-GPU pipelines with NVSHMEM one-sided puts nvshmem_float_p, nvshmem_quiet, nvshmem_int_p, nvshmem_int_wait_until, atomic work stealing nvshmem_int_atomic_inc, nvshmemx_collective_launch, and graph-captured NCCL AllReduce.
6. Apply the Roofline-guided orchestration framework and the Volume 03 three-level production profiling funnel and Lab 04 diagnostics using nsys, ncu, nvidia-smi, and compute-sanitizer.

---

With device-initiated graphs, you must manage dependencies yourself. A tail launch is right when the next kernel consumes the graph's output. A fire-and-forget launch is right when the graph is a side job that the parent does not need to wait on.

---

Scaling from one GPU to many keeps the same goal: hide data movement behind useful work. The host dispatches work to each GPU, and then the GPUs take over. While one stream computes, a second stream can move data peer to peer over NVLink or PCIe, without touching host memory.

---

1. Enforce an identical collective sequence across all ranks. Every rank in the communicator captures and replays the exact same order of ncclAllReduce calls on the same ncclComm_t.
2. Run warmup collectives before capture so NCCL ring and tree channels and RDMA buffers are initialized outside the graph capture window.
3. Preallocate gradient and communication buffers at fixed addresses before capture, and use cudaGraphExecUpdate if pointer addresses or sizes change.

---

## FILE docs/part-10-gpu-cuda/19-triton-language-and-compilers-openai-triton-torch-compile-xla.md

TorchInductor is PyTorch's default compiler backend for NVIDIA GPUs, AMD GPUs, and CPUs. It lowers ATen and PrimTorch nodes into fused loop nests expressed in a Python define-by-run loop-level IR using SymPy index expressions. Because indexing is symbolic, view operations like transposes and slices become pure index math inside the consumer loop without materializing a transposed tensor in high-bandwidth memory.

---

In `plan_triton_kernel_launch`, `BLOCK_SIZE` is a compile-time constant specifying how many data elements each Triton program instance processes. Meanwhile, the actual number of CUDA threads per thread block is controlled separately by `num_warps`. The table below shows how block size, warp count, and thread counts relate on modern GPUs.

---

Wrapping the kernel with `torch.library.triton_op` and `wrap_triton` exposes it as a first-class PyTorch operator. TorchInductor can then inline, reorder, and fuse surrounding elementwise operations across the custom kernel boundary without breaking the FX Graph. For training workloads, attaching a backward pass via `register_autograd` integrates the custom operator seamlessly with AOTAutograd.

---

A naive tiled matrix multiplication kernel (`tiled_gemm_kernel`) stalls on global memory latency and wastes cycles launching thousands of short-lived thread blocks. Even when engineers add software pipelining (`pipelined_matmul`) with multiple pipeline stages, a subtle variable-overwrite mistake inside the loop can allow the compiler to reorder loads past compute instructions and collapse overlap completely. Reaching peak Tensor Core throughput on Hopper and Blackwell requires hardware descriptor loads, warp specialization, and persistent grid scheduling.

---

## FILE docs/part-10-gpu-cuda/20-profiling-tools-nsight-systems-nsight-compute-pytorch-profiler.md

An AI training or inference pipeline can stall at any layer of the hardware and software stack. A job might lose half its speed to Python interpreter dispatch, CPU data loading starvation, or un-overlapped host-to-device memory copies. Another job might stall inside Mixture-of-Experts token routing, memory-bound CUDA kernels, caching-allocator fragmentation, or multi-GPU collective communication stragglers. Guessing where the bottleneck lives wastes days of engineering time and thousands of GPU hours.

---

Nsight Systems solves this by using CUPTI activity records to project every CPU-emitted NVTX range onto the asynchronous GPU streams that executed the kernels launched inside that range. Running the `nvtx_gpu_proj_sum` report or recipe computes the exact GPU start-to-end span of each annotated phase.

---

If you wrap an entire multi-billion-parameter model in a single root FSDP instance or merge all DDP gradients into one giant communication bucket, the compiler sees one monolithic graph with zero intermediate communication boundaries. As a result, all collective communication waits until the end of the pass instead of overlapping with backward computation. Peak memory spikes and GPUs sit idle waiting on network transfers.

---

To prevent performance regressions from merging, run deterministic TorchBench workloads in GitHub Actions CI while checking peak memory allocation and `torch.allclose` numerical accuracy. Following the public PyTorch HUD convention, fail the build when throughput regresses by five percent or more sustained across three consecutive runs.

---

## FILE docs/part-10-gpu-cuda/21-gpu-health-dcgm-ecc-row-remapping-and-xid.md

Tier 2 covers application-recoverable faults such as out-of-bounds kernel pointers or an uncorrectable ECC error that hardware successfully contained to one user process. In these cases, the orchestrator only needs to restart the affected pod. However, if the same physical GPU repeats the same Tier 2 fault across unrelated user workloads, automation must escalate that GPU to Tier 3 hardware suspicion.

---

Second, understand how fields and watches multiplex across clients. A field is a typed numeric identifier, and a watch tells the host engine how often to sample that field. The host engine maintains exactly one collection stream per GPU-field pair and samples at the fastest cadence requested by any subscribed client. Every metric sample carries the timestamp of when DCGM read the driver rather than when Prometheus scraped `/metrics`. In addition, Xid counts are aggregated over a rolling 5-minute window so brief spikes between scrapes are never lost.

---

When a specific HBM cell develops a permanent physical defect, correcting the same bit flip millions of times per second wastes memory bandwidth and risks a second bit flip in the same word. The GPU needs a permanent mechanism to retire the damaged memory location so future allocations never touch it. Pre-Ampere GPUs used software-visible Page Retirement, whereas Ampere, Hopper, and Blackwell GPUs use a dedicated Hardware Row Remapper.

---

Before running diagnostics or scraping metrics on a new GPU node, verify that the installed DCGM 4 package matches the CUDA major version reported by the driver. Once the daemon and exporter are running, use `dcgmi` and `nvidia-smi` to inspect live field streams, run active health checks, and audit ECC and Row Remapper state.

---

## FILE docs/part-10-gpu-cuda/22-gpu-troubleshooting-scenarios.md

Second, check for a userspace versus kernel driver version mismatch. If a container image bakes in a stale NVML library or a host upgrade leaves old symlinks behind, NVML fails to initialize when talking to the newer `nvidia.ko` kernel module. Updating the symlink with `ldconfig` or injecting host libraries via the NVIDIA Container Toolkit resolves the mismatch immediately.

---

When a GPU's clock frequency drops in the middle of a training run, throughput can fall by 15% to 40% while every rank in the collective waits on the slowed device. Operators who only inspect temperature, clock speed, and power draw often guess the wrong cause and order a larger power supply for a cooling problem. Lowering clock frequency automatically reduces dynamic power draw. Observing a lower power reading alongside a lower clock never proves that a power limit caused the slowdown.

---

Sometimes a GPU's graphics clock oscillates wildly every half-second even though temperature is a cool 65°C and every hardware throttle bit reads inactive. This clock jitter creates variable iteration times that slow down synchronous all-reduce steps across the entire cluster.

---

During a complex production incident, a single node can simultaneously report ECC or Xid errors, thermal throttling, and NCCL collective timeouts. Investigating those signals in the wrong order wastes hours chasing downstream symptoms or saving a checkpoint whose weights are already corrupted. Always evaluate multi-failure evidence in strict priority order: Data Integrity first, Hardware Performance Cause second, and Downstream Communication Symptom third.

---

## FILE docs/part-19-capstone/01-capstone-a-slurm-gpu-cluster.md

It is 2 a.m. A 24-hour training run has just died, and the on-call engineer is staring at a cluster that, by every individual check, looks healthy. `sinfo` shows every node healthy. The dashboards show GPU allocation near saturation. But fairshare never fired, so one team's 500-job hyperparameter sweep quietly consumed the entire cluster. And two co-scheduled jobs on the same node just corrupted each other's results, because neither was pinned to its own GPUs. Nothing is broken. The pieces are simply not integrated.

---

The answer is five integration surfaces. One is the `slurm.conf` that every node trusts. The second is the accounting database that makes QoS and fairshare real. The third is the health-check loop that turns a dying GPU into a drained node before the scheduler sends it more jobs. The fourth is an upgrade order that never freezes the cluster, and the fifth is a runbook that tells the on-call engineer exactly what to do at 2 a.m. This chapter walks the whole cluster through those five surfaces.

---

The capstone is also the interview anchor. When an interviewer asks how you would build and operate a Slurm GPU cluster, the answer is not a list of daemons; it is this integrated picture, told in the order a real build proceeds. The same picture is what the platform team uses as its reference design and what the on-call engineer uses when the cluster is on fire.

---

This is why the controller node build has two halves: the control plane and the accounting plane. Chapter 6.7 walks the package installation; here we build the accounting plane end to end, because it is the piece that breaks most often.

---

## FILE docs/part-19-capstone/02-capstone-a-kubernetes-gpu-platform-with-kai-and-kueue.md

The capstone is also the interview anchor. When asked how you would build and run a Kubernetes GPU platform, tell this picture in build order: pool, stack, queues, gangs, health, day 2. This chapter says what the topic tests. It does not claim any company asks a particular question.

---

Serving sits at 1000, training at 50 and research at 0. When a pending pod cannot fit, the default scheduler looks for lower-priority pods to evict. Victims get their graceful termination period, which defaults to 30 seconds in the Kubernetes pod lifecycle docs. A training job that cannot checkpoint inside that window loses progress, so checkpoint intervals must be shorter than the window.

---

The nominal quotas now sum to the hardware: 12 for training and 4 for serving, 16 in total. A draft gave training 16 and serving 4. Kueue allows quotas above the hardware, but then the serving reserve is a hope, not a guarantee. Only GPUs are covered. By default Kueue does not account for resources that no ClusterQueue declares. The config key `resources.quotaCheckStrategy: BlockUndeclared` changes that.

---

Page when someone must stop work: lost schedulable capacity, an actionable hardware event, sustained throttling with measured impact, or lost monitoring. Do not page on low utilization. A zero reading is ambiguous until you check the exporter target is alive.

---

## FILE docs/part-19-capstone/03-capstone-inference-on-gke-with-vllm-triton-tensorrt-llm-nim-and-kserve.md

The chapter also fixes several errors from its earlier draft. The old node pool used a machine type that cannot carry an A100. It used a Kubernetes kind that does not exist. It claimed a Triton mode gave zero-downtime reloads when the documentation says otherwise. The verification log at the end lists every correction.

---

Picture a team that adds four GPUs because p95 latency is high. Traffic did not change. Latency stays flat, and the new GPUs idle. The slow part was a tokenizer running on one CPU core in front of the model. More GPUs cannot fix a CPU queue. This is an illustration of a common pattern, not a reported incident.

---

Four facts matter more than the table suggests. First, the book says NIM picks a backend by itself, preferring TensorRT-LLM, then vLLM, then SGLang, based on the model profiles for the detected GPU. You do not choose the engine inside NIM, you choose a profile.

---

The book's own example uses a pod-level metric through an OpenTelemetry sidecar with a value of 4, based on a benchmark. It says a pod metric and an external one are equivalent for pod-local queries, and the pod-level source reacts faster. Choose the external form when you need joins across replicas.

---

## FILE docs/part-19-capstone/04-capstone-multi-node-training-with-fault-tolerance.md

It is 03:10 and a training run that started nine days ago has stopped moving. The loss curve ends in a flat line, GPU utilisation reads zero on every node, and the job is still listed as running. Somebody has to decide whether to wait, restart, or page the network team. Whatever they decide, the last good checkpoint is the only thing that stands between the team and nine days of lost compute.

---

`test_c04_slurm_script.py` runs the real batch script with a fake `srun` and a fake `scontrol`. It does not touch a scheduler. It proves three things. A SIGUSR1 to the batch shell becomes SIGTERM for the step and one `scontrol requeue`. At the restart cap the script stops requeueing. And a normal failure exit code passes through without a requeue.

---

The CRD also offers `failurePolicy.rules`, with actions such as `FailJobSet`, `RestartJobSet` and `RestartJob`, selected by failure reason. That lets you fail fast on an application error and restart on a node loss. The manifest here does not use rules. I did not test rule behaviour on a cluster.

---

1. Read before you restart. A restart destroys the process state that explains a hang. Take the flight recorder dump and the last 200 log lines first.
2. Never delete a checkpoint during an incident. Rename suspicious ones. The resume code already does.
3. Restart from the checkpoint, not by hand-editing state. The manifest tells you which checkpoint is valid.
4. If the job restarts and fails again at the same step, stop the loop. Auto-restart past a deterministic failure only burns restart budget.
5. Write down the cause class from section 1 in the incident record. A pattern across weeks tells you which tool to invest in.

---

## FILE docs/part-19-capstone/05-capstone-an-nccl-tests-fabric-lab.md

A new engineer reads the nccl-tests output and files a ticket against every NIC in the rack. The AllReduce shows 24 GB/s in the algbw column, and the rails are rated at 400 Gbps. That looks like half the line rate. The busbw column on the same row says 45 GB/s, which is the number to compare with the link. The fabric was fine and the ticket was wrong.

---

The derivation for AllReduce is short. Each element needs n-1 additions and n assignments, which is 2(n-1) transfers. With n links of bandwidth B, the best time is `t = S/B * 2(n-1)/n`. Solving for B gives `B = algbw * 2(n-1)/n`. That is where the factor comes from, and the page states that the bottleneck being compared is "NVLink, PCI, QPI, or network".

---

The second is the port state from `ibstat`. *Supercomputers for Linux SysAdmins* (ch. 5) describes `ibstat` as showing the status of all ports, and it also covers `perfquery` for counters and `mlxlink` for deeper detail. Look for `State: Active`, `Physical state: LinkUp` and a `Rate` that matches the port, 400 for NDR. A lower rate means a speed or width downshift. Check cable reach too: the DGX B200 data-center guide gives up to 3 meters for passive copper at 400 Gb and up to 30 meters for active optical cable, so a copper cable that is too long can cause errors by itself.

---

The analyser `c05_nccl_parse.py` reads a saved table, so the judgments do not depend on someone's eyes at 2 a.m. It handles both column layouts: the older one with `error` and no root column, and the newer one with `root` and `#wrong`. It recognises rows by shape and not by header text, so a changed header does not break it.

---

## FILE docs/part-19-capstone/06-capstone-node-health-automation-with-dcgm-and-an-operator.md

First, the thresholds marked "start value" are mine. They are 100 corrected ECC errors per hour, 10 PCIe replays per hour, 1000 NVLink CRC errors in six hours, 60 throttled seconds in 15 minutes and a temperature rise of 2 degrees per minute. No vendor document gives them. The nvidia-devops fan-failure chapter lists a rise of 2 to 3 degrees per minute under load as a symptom of a failing fan, which is where I took the idea. Tune them on your own fleet.

---

For application codes such as 13, 31 and 32, restart the process and watch the count. One restart followed by stability points at the application. Repeats on one GPU across unrelated applications point at hardware, and that is my escalation rule, not catalog text. For self-healing codes such as 63 and 92, take no action in real time. Review the rate weekly. The earlier draft said to escalate at a 3x week-over-week rise. I have no source for that number, so I treat it as a starting idea and not as a rule.

---

Make two nodes unhealthy with a budget of one. Cordon a third node by hand with `kubectl cordon`. Restore the conditions. Expected shape, not run: one operator cordon, one blocked-node warning, and after the recovery window the operator releases only its own node while the hand-cordoned node stays cordoned.

---

What to record: the five answers you should be able to give in five seconds each. Which alerts fired and how long each took? Which nodes did the operator cordon and which limit bound it? Which node did it refuse to release and why? What was in the evidence bundle? What gap did the runbook have?

---

## FILE docs/part-19-capstone/07-capstone-an-observability-platform.md

A team installs the stack with default values. A month later someone adds a ServiceMonitor for the GPU exporter and nothing is scraped. The cause is a selector. By default the Operator only picks up objects that carry the Helm release label. Nobody on the team knew that.

---

Read the file from the top. The `fullnameOverride` of `kps` keeps service names short. The three `NilUsesHelmValues` settings are set to false. In the chart's rendering this turns the service monitor and rule selectors into empty selectors, and a test checks both. An empty selector matches everything in the cluster.

---

The dashboard has 11 panels. Ten query Prometheus. One queries Loki. Every panel names its datasource by a fixed uid, `prometheus` or `loki`. The uid `prometheus` matches the one the stack chart provisions by default. A variable called `model` is filled from the vLLM waiting-request gauge and feeds four panels.

---

The table follows the methods in Systems Performance. The USE method asks for utilization, saturation and errors for every resource, and the RED method asks for rate, errors and duration for every service. The book says the first suits machine health and the second suits user health. The dashboard shows both. The book also warns that a five-minute average can hide short bursts of saturation, so the burn-rate alerts pair a long window with a short one.

---

## FILE docs/part-19-capstone/08-capstone-mig-multi-tenancy.md

Stranded slices come in two kinds. The first is built into the layout: two 3g profiles always strand one SM slice and seven 1g profiles always strand one memory slice. The second comes from history, because the guide notes that as instances are created and destroyed, fragmentation occurs.

---

Kubernetes isolation is outside MIG. Namespaces, RBAC, network policies and storage credentials keep tenant A from tenant B's secrets. Production Kubernetes chapter 12 separates soft multitenancy, where tenants share some trust, from hard multitenancy, where they are treated as adversaries, and notes that requests and limits are weaker than a hypervisor.

---

Two warnings. Version 4.9.0 names metrics with units, and its repository tells users to update dashboards to the new names, so a panel that goes blank after an upgrade is likely a rename. Power and temperature are per physical GPU, so you cannot bill or alert on power for one tenant, and this chapter invents no per-instance energy figure.

---

What to record: the CRD message, the three failing test names, and the fact that the upstream parser accepted the impossible layout. This step proves that the checks can fail, and it shows why the planner is needed on top of the parser.

---

## FILE docs/part-19-capstone/09-capstone-capacity-planning.md

On a Monday the finance lead asks one question: how many GPUs do we need next year, and should we buy them or rent them? The platform team has three answers in three spreadsheets. Training says 100 GPUs for six weeks every quarter. Inference says its traffic doubled since spring. The research group says "as many as you can give us." Nobody can say what the sum is, how sure they are, or what happens if one of the numbers is wrong.

---

Headroom and spares come from the same chapter. The book *AI Systems Performance Engineering*, chapter 16, advises targeting about 90 percent of peak throughput and keeping extra replicas that sit mostly idle, and it warns that autoscaling takes time to provision resources. The formula is replicas equals ceil of QPS over rate times target, plus spares. At 40 requests per second that gives 9 GPUs, which the tests check against chapter 20.12.

---

The break-even rule tells you whether to own. It does not tell you how much. A commit of 161 GPUs, the peak, would leave most of them idle in the troughs. A commit of zero gives up the discount. The right level is in between, and the model finds it by trying every whole-number commit from 0 to the peak and keeping the cheapest.

---

The same history gives a P90 of 44.2 requests per second one month ahead and 57.5 four months ahead. The longer the lead time, the larger the number you must plan to, and the wider the band around it. This is the real cost of buying hardware. It is not just the price. It is the commitment to a forecast that is four months more uncertain.

---

## FILE docs/part-19-capstone/10-customer-workshops-and-the-consulting-method.md

The only gem-book description of a whole customer engagement is the Fraunhofer case in *Engineering AI Systems*, chapter 12. It splits the project into three phases. A proof of concept proves the approach is feasible. A main project integrates the application on the customer side. Maintenance and operation follow after deployment. The proof of concept ran three months with a break at the halfway point where either partner could stop the project if progress was not significant.

---

The record format, with context, options, decision and consequences, is a widely used convention. I am using it from memory of common practice and I have not verified it against a source, so I do not call it a standard.

---

The Fraunhofer proof of concept had a defined window, a halfway decision point and a goal. The client emphasised precision over recall, so the model had to be certain in its recommendations even if it covered fewer products. The evaluation combined numbers from a held-out test set with a qualitative review by the employees, who also sorted recommendations into incorrect, correct and functionally correct. The bulk of the work went into parsing the input. A simple embedding-based model was enough to convince the client to proceed, and a heavier model came later in the main project.

---

The question is "walk me through how you would run a discovery workshop." The interviewer wants to hear a structure, an awareness of risk and some humility about what you do not know. This chapter's method is built from the gem books and my own practice. It is not how any particular company works, and I would not claim it is.

---

## FILE docs/part-19-capstone/11-system-design-a-training-cluster.md

Do not stop at compute. The training state must also fit in memory. Distributed AI Systems ch. 5 says Adam keeps two FP32 copies at 8 bytes per parameter and a FP32 master copy adds 4 more. With BF16 weights at 2 and gradients at 2, my sum is 16 bytes per parameter, so 1.12 TB for this model. Eight B200 GPUs with 192 GB each could hold that state alone. The script prints 8 as a floor because activations are not counted. At 368 GPUs sharded, state is about 3 GB per GPU. Memory is not the constraint here. Compute is.

---

How long does the write take? It depends on the bandwidth. The DGX GB300 reference architecture gives guidelines for one scalable unit. Table 5 lists 90 GB/s read and 45 GB/s write for a "standard" level and 280 and 140 for "enhanced". It is a different system from the B200 in my example, so I use it only as an order of magnitude. At 45 GB/s the write takes 21.8 seconds. At 10 GB/s it would take 98 seconds.

---

The Young interval for this cluster is 4,616 seconds, about 77 minutes, and the script's inflation model gives 1.0107. If you checkpoint every 30 minutes instead, the cost of writes is 1.21 percent and the expected lost work per failure is 15 minutes plus the 10 minute restart. Both choices are cheap. The shape of the curve is flat near its minimum, so pick a round interval that operations can remember. The DGX GB300 document also describes Mission Control automatically restarting failed ranks from the most recent valid checkpoint, which is the behaviour you want from any scheduler. [19.4](./04-capstone-multi-node-training-with-fault-tolerance.md) builds that loop.

---

Cost closes the answer. The run costs about 2.25 million dollars at the placeholder price. Say what moves it: MFU, price, spare count, and checkpoint stall. Buying instead of renting changes the shape, and [19.9](./09-capstone-capacity-planning.md) has the buy-versus-rent model. Do not quote a purchase price, because I have no sourced one.

---

## FILE docs/part-19-capstone/12-system-design-inference-serving.md

The GPU is an 80 GB H100 SXM. The model sizes come from 20.12. The traffic shapes are also assumed. The assistant peaks in office hours, docsum runs as a batch job in the first five hours of the night, and the analyst peaks around midday.

---

Hands-On LLM Serving and Optimization, chapter 8, gives a method. Write the targets first. Look at the real prompts and note whether they are prefill-heavy or decode-heavy. Compare engines with the same model, precision and batch. Measure start-up time, observability and upgrade effort too. Its closing advice is "workload first, not hype".

---

For this pool I would pick vLLM for all four tiers. The reason is operational, not about speed. One engine means one set of metrics, one probe design and one upgrade path for five models. Chapter [20.22](../part-20-nebius-sre-interview/22-operating-vllm-triton-ray-and-tensorrt-llm.md) has the flags, the metrics and the version-skew rules. I would revisit the choice for the analyst model first, because it uses the most GPUs and would gain most from a faster engine.

---

The big step is the last row. A fixed pool saves $9,720 over three dedicated pools, because the peaks do not coincide. A pool that follows the load saves $40,635, because the night hours are cheap. That saving depends on scaling down safely, which section 6 covers, and on the spare node being a placeholder that other work can use.

---

## FILE docs/part-19-capstone/13-system-design-research-infrastructure.md

A good answer follows this order, in about 45 minutes. Minutes 0 to 5 are requirements and numbers. Minutes 5 to 10 are the platform shape. Minutes 10 to 20 are compute sharing, because that is where the hard trade-offs live. Minutes 20 to 33 are environments, reproducibility, tracking and data. Minutes 33 to 40 are security and cost. The last minutes are growth from 5 to 100 people and what breaks first.

---

Start the interview the same way. Ask who the users are, what they run, and what they cannot tolerate. Then write down the numbers you assume and say that they are assumptions. Everything in the table below is my assumption for a worked example. None of it is a measurement of a real organisation.

---

The design answer is one lock file and one image. A project keeps `pyproject.toml` and `uv.lock`. The image installs exactly the lock file, so a notebook and a batch job get identical packages. I built and ran this on a laptop. The lock resolved 45 packages with uv 0.13.7, and the image imported numpy 2.5.4 and mlflow 3.18.0. The files live in `code/part19/c13_env/`.

---

Expected: the rendered chart has 34 resources, all valid, then 8 valid core objects, then `checked 9 resources, 0 problems` for the Kueue objects. Run here: yes, with Helm v4.2.3, kubeconform and the Kueue v0.20.5 CRDs. What to record: the three summary lines. The pytest schema test is the offline version, using a saved copy of the chart's `values.schema.json` and defaults.

---

## FILE docs/part-19-capstone/14-interview-question-bank-by-topic.md

A good answer has a shape. Say what you think the problem is in one sentence. Give the mechanism in plain words. Name the first measurement you would take, and say what result would change your mind. Close with the trade-off or the fix. The entries in the bank follow this shape, so reading ten of them teaches it.

---

Model answer. The PCIe link may have trained down, for example to a narrower width, because of riser wiring or bifurcation. The slot then caps DMA throughput regardless of the network speed. lspci shows the link capability next to the link status. Reseat or fix the slot and retrain.

---

Model answer. The default shared-memory size of 64 MiB is too small for an 8-GPU node, because NCCL places buffers there. The chapter's worked example needs over a gigabyte. Set a larger shared memory size for the pod, using a memory-backed volume, and check the NCCL buffer settings.

---

`c14_bank.py` checks that every entry has a topic, a level, a chapter link that resolves to a file, a model answer and a follow-up. It also checks that ids are unique, that the count is between 150 and 200, and that no entry claims a company asks the question.

---

## FILE docs/part-19-capstone/15-interview-cheat-sheet.md

The sheet is built to prevent that. Each row is one fact with one source chapter id, such as 20.12 or 19.5. Most rows also carry an anchor: a short string that must appear in the cited chapter. The validator `c15_sheet_validator.py` reads the sheet and fails on four things. A row with no id. An id that matches no chapter file. An id that is not in the form `N.M`. An anchor that is missing from the cited chapter.

---

The checkpoint lines come from chapter 19.4, which scales a published interruption rate to 16,384 GPUs. At that size the Daly interval is 685 seconds and waste is 11.47 percent. Cutting the blocking write from 22.5 s to 2 s with asynchronous staging takes waste to 7.22 percent. The chapter labels the scaling as its own reasoning, so say "about" and "if failures are independent".

---

Do not memorise a row you cannot explain. If you say "Xid 79, restart the node" and are asked why, you need the next sentence. The Xid 79 row is a prompt to say "I would read the live catalog for my driver".

---

For a behavioural question, use the situation, task, action and result form, known as STAR. This is a common interview convention and no handbook source tests it, so it is my advice. Spend most of the time on your own action and a measured result. Chapter 20.28 gives the probe that follows a project story. Prepare one story that survives it.

---

