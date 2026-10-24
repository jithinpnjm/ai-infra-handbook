---
id: "c03-02"
title: "3.2 Modules, packages, virtual environments and packaging"
sidebar_label: "3.2 Modules, packages, virtual environments and packaging"
sidebar_position: 2
description: "The import system, modules and packages, virtual environments, dependency management with pip/uv/pip-tools/poetry, pyproject.toml, wheels, entry points, reproducible builds and GPU/ML packaging issues"
status: "drafted"
tier: "2"
level: "B"
lab_venue: "Mac"
---

# 3.2 Modules, packages, virtual environments and packaging

| | |
|---|---|
| Level | Beginner to intermediate |
| Priority tier | 0 |
| Lab venue | Any machine with Python 3.11 or newer, internet access for PyPI (or a mirror) |
| Part | Part 3: Python for infrastructure |
| Status | Drafted, labs **untested** |

## Why this matters for AI infrastructure

Most "it works on my machine" failures in ML and infrastructure code are packaging failures: a different NumPy ABI, a PyTorch wheel built for CUDA 12.1 on a node with a 12.4 driver, a transitive dependency that moved overnight, a system Python that a distribution upgrade changed underneath a cron job. Reproducible environments are also a security and compliance topic (what exactly runs in production?) and a performance topic (container image size, import time, cold start). This chapter covers how Python finds and runs code (modules, packages, the import system), how to isolate and reproduce environments (venv, pip, uv, pip-tools, Poetry, conda), how to structure and ship your own tools (pyproject.toml, wheels, entry points, private indexes), and the specific problems of Python on GPU machines and in containers.

## Prerequisites and outcomes

You should know the core language (chapter 3.1) and basic shell and Git.

After this chapter you can:

- Explain what a module, package, namespace package and script are; how `import` searches and caches (`sys.path`, `sys.modules`, finders/loaders, `.pyc`), absolute vs relative imports, `__init__.py`, `__all__`, `__main__`, circular imports and how to avoid them.
- Design a project layout (src layout), write `pyproject.toml`, define dependencies, optional extras, console-script entry points and plugin entry points.
- Create and use virtual environments; use `pip`, `pip-tools`, `uv`, Poetry/PDM/Hatch, pipx and conda appropriately; pin and lock dependencies, verify hashes, audit vulnerabilities.
- Build and publish wheels and sdists; use private indexes and mirrors; version with SemVer/CalVer; understand platform tags (manylinux, CUDA local versions).
- Deal with system Python (PEP 668 "externally managed"), multiple Python versions (pyenv, uv python, deadsnakes), containers, and the ABI/CUDA problems of ML packages.
- Debug import errors, dependency conflicts and "wrong interpreter" problems.

## 1. Modules

A **module** is a single Python file (or a built-in/extension module) providing a namespace of names. Importing it **executes its top-level code once** and caches the resulting module object. Modules are the unit of code reuse and of namespace separation.

```python
# util.py
import math
PI_APPROX = 3.14159
def circle_area(r): return math.pi * r * r
print("util loaded")       # side effects at import time: avoid in libraries
```

```python
import util                       # binds the name util to the module object
from util import circle_area      # binds the function name directly
from util import circle_area as area
import util as u
import os.path as osp
```

- `import X` runs the module body the first time; later imports in the same process reuse `sys.modules["X"]` (so a module's global state is a **process-wide singleton**).
- `from X import *` imports all public names (everything in `__all__` if defined): avoid except in `__init__` re-exports; it pollutes namespaces and defeats linters.
- Module attributes: `__name__`, `__file__`, `__doc__`, `__package__`, `__spec__`, `__all__`; inspect with `dir(module)`.
- **Reloading** (`importlib.reload`) re-executes the module in the same namespace; it is a development convenience, not a production update mechanism.
- Keep import-time code cheap and side-effect free: no network calls, no reading config files, no starting threads, no heavy imports at module top level in CLI tools (import inside functions when startup time matters; measure with `python -X importtime`).

### Where Python finds modules

`import X` consults, in order: `sys.modules` (cache), built-in modules, then the **finders** on `sys.meta_path`, which search the directories in `sys.path`:

1. the directory of the script being run (or `''`/current directory for the REPL and `-c`; for `-m`, the current directory),
2. directories in the `PYTHONPATH` environment variable,
3. the standard library,
4. the `site-packages` directory of the active environment (plus `.pth` file entries).

```bash
python3 -c 'import sys; print("\n".join(sys.path))'
python3 -c 'import json, sys; print(json.__file__)'
python3 -m site        # shows sys.path, user site, and whether a venv is active
PYTHONPATH=/opt/mylib python3 app.py        # extend the path (prefer proper installation)
```

**Shadowing trap**: a local file named like a standard or installed module (`json.py`, `random.py`, `requests.py`, `test.py`) shadows the real one because the script directory is first on `sys.path`; the symptom is baffling `AttributeError`s or circular import errors. Name your files carefully and never run Python from inside a directory that contains such files when importing the real ones. (The same advice applies to untrusted download directories: Python executes whatever it imports; use `python -I` for isolated mode.)

### `.pyc` and bytecode caches

Compiled bytecode is cached in `__pycache__/name.cpython-312.pyc`, invalidated by source timestamp or hash. For containers and read-only file systems you can pre-compile (`python -m compileall`), set `PYTHONDONTWRITEBYTECODE=1` to skip writing, or use `PYTHONPYCACHEPREFIX` to relocate caches.

## 2. Packages

A **package** is a directory of modules, importable as a hierarchical namespace.

```text
myops/
├── __init__.py          # makes it a regular package; runs on first import
├── config.py
├── clients/
│   ├── __init__.py
│   ├── redfish.py
│   └── slurm.py
└── cli.py
```

```python
import myops.config
from myops.clients import redfish
from myops.clients.slurm import submit
```

- `__init__.py` may be empty, or define the package's public API by re-exporting (`from .redfish import RedfishClient`), set `__all__`, and hold a `__version__`. Heavy imports there slow every use of the package.
- **Regular packages** have `__init__.py`. **Namespace packages** (PEP 420) have no `__init__.py` and can be split across multiple directories/distributions (`google.cloud.*`, company-wide `acme.*` plugins); they are useful for plugin systems but easy to create by accident when you forget `__init__.py`.
- **Relative imports** inside a package: `from . import config`, `from .clients import slurm`, `from .. import utils`. They only work when the module is imported as part of a package, not when a file inside a package is run directly as a script (use `python -m myops.cli` instead; "attempted relative import with no known parent package" is the telltale error).
- **Absolute imports** (`from myops.clients import slurm`) are preferred by most style guides for clarity; relative imports are fine for intra-package references.
- **`__main__.py`** inside a package makes `python -m myops` run it; combined with entry points it gives a standard CLI.
- **Circular imports** (A imports B imports A) produce partially initialised modules and `ImportError`/`AttributeError`. Fixes: restructure so shared code lives in a third module, import inside functions, import the module (`import pkg.b`) rather than names from it, or use `typing.TYPE_CHECKING` for type-only imports.
- **Lazy imports and plugin discovery**: `importlib.import_module("pkg.plugins." + name)`, `importlib.metadata.entry_points(group="myops.plugins")` allow extension without hard-coded imports (section 6).
- **Data files** inside packages: use `importlib.resources.files("myops") / "templates/x.j2"` instead of paths relative to `__file__`, so zip/wheel installs work.

### Typical project layout (src layout)

```text
myops/
├── pyproject.toml
├── README.md
├── LICENSE
├── src/
│   └── myops/
│       ├── __init__.py
│       ├── __main__.py
│       └── ...
├── tests/
│   └── test_config.py
├── docs/
└── .github/workflows/ci.yml
```

The **src layout** forces you to install the package (`pip install -e .`) to import it in tests, which catches packaging mistakes (missing files, wrong imports) that the flat layout hides because the project root is on `sys.path`.

## 3. Virtual environments

A **virtual environment** is a directory with its own `site-packages` and a `python` executable (symlink or copy) that isolates a project's dependencies from the system and from other projects. Without one, `pip install` modifies shared state and different tools require conflicting versions.

```bash
python3 -m venv .venv                       # create (needs python3-venv package on Debian/Ubuntu)
source .venv/bin/activate                    # sets PATH and VIRTUAL_ENV; 'deactivate' to leave
python -c 'import sys; print(sys.prefix, sys.base_prefix)'     # differ inside a venv
.venv/bin/python -m pip install requests     # no activation needed: call the interpreter directly (best in scripts, cron, systemd)
python -m pip list ; python -m pip freeze > requirements.txt
rm -rf .venv                                 # envs are disposable; never commit them
```

Rules of thumb:

- One environment per project (or per tool); recreate rather than repair.
- Use `python -m pip` (not bare `pip`) so you know which interpreter you install into; `which python` after activation.
- Systemd units, cron jobs and CI should call `/path/to/.venv/bin/python` explicitly; do not rely on activation.
- **Never `sudo pip install`** and avoid installing into the distribution's Python: modern distributions mark it **externally managed** (PEP 668: `error: externally-managed-environment`); use a venv, `pipx` for CLI tools (`pipx install ansible-lint` creates an isolated env per tool), or the distribution package (`apt install python3-yaml`) for system scripts.
- `--system-site-packages` lets a venv see system packages (needed for some distribution-provided bindings like `python3-apt` or GPU vendor packages), at the cost of isolation.
- Environments are tied to the interpreter that created them; upgrading the base Python can break them (rebuild).
- Activate scripts exist for bash/zsh/fish/PowerShell; `direnv` or `uv run` automate activation per directory.

### Managing Python versions

`pyenv` (builds interpreters under `~/.pyenv`), `uv python install 3.12` (downloads standalone builds), Debian/Ubuntu `deadsnakes` PPA, `conda`/`mamba`, or container base images. Pin the minor version in `pyproject.toml` (`requires-python = ">=3.10,<3.13"`), CI matrices and Dockerfiles. The oldest supported Python and deprecation policy of your dependencies (NumPy, PyTorch drop old versions yearly) set your support window.

## 4. Installing and managing dependencies

### pip

```bash
python -m pip install requests                  # latest compatible
python -m pip install "requests>=2.31,<3"       # version specifiers (PEP 440): ==, !=, >=, <=, ~=2.31 (compatible release), *
python -m pip install -r requirements.txt       # from a file
python -m pip install -e .                      # editable install of the current project (dev)
python -m pip install --upgrade pip setuptools wheel
python -m pip install 'torch==2.4.0' --index-url https://download.pytorch.org/whl/cu121   # alternate index (CUDA wheels)
python -m pip install --extra-index-url https://pypi.example.com/simple internal-lib       # additional index: dependency confusion risk!
python -m pip install --require-hashes -r requirements.txt   # integrity-verified install
python -m pip install --no-cache-dir --no-deps pkg           # container tuning / manual resolution
python -m pip check                              # report broken dependency requirements
python -m pip show -f pkg ; python -m pip download pkg -d wheelhouse/ ; python -m pip wheel . -w dist/
python -m pip uninstall pkg ; python -m pip cache purge
```

pip's **resolver** (since 20.3) backtracks to find a consistent set; failures print `ResolutionImpossible` with the conflicting constraints. **Extras**: `pip install "myops[redfish,slurm]"`. **Constraints files** (`-c constraints.txt`) restrict versions without adding requirements. **Environment markers**: `pywin32; sys_platform == "win32"`, `importlib-metadata; python_version < "3.10"`.

### Declaring dependencies: libraries vs applications

- A **library** declares *abstract* compatible ranges (`requests>=2.28,<3`) so it composes with other packages.
- An **application / deployment** needs a *concrete lockfile*: exact versions of everything (including transitive dependencies) with hashes, so every machine installs the same bits.

```bash
# pip-tools: compile abstract requirements into a fully pinned, hashed lock
pip install pip-tools
printf 'requests>=2.31\npyyaml\nprometheus-client\n' > requirements.in
pip-compile --generate-hashes requirements.in -o requirements.txt
pip-sync requirements.txt                       # make the environment match exactly (removes extras)

# uv (Rust, fast pip/pip-tools/venv replacement)
uv venv ; uv pip install -r requirements.txt ; uv pip compile requirements.in -o requirements.txt --generate-hashes
uv init app ; uv add requests ; uv lock ; uv sync ; uv run python main.py ; uv tool install ruff
# Poetry / PDM / Hatch: project managers with lockfiles (poetry.lock, pdm.lock, uv.lock)
poetry init ; poetry add requests ; poetry lock ; poetry install ; poetry run pytest
```

Why locking matters: an unpinned transitive dependency can change between a CI run and a production rollout, and a compromised or yanked release can enter silently. Practices: commit lockfiles, update deliberately (Dependabot/Renovate pull requests with CI), use hashes, install from a vetted mirror (Artifactory/Nexus/devpi) in production, run `pip-audit` / `safety` for known vulnerabilities, generate an SBOM (`cyclonedx-py`, `syft`), and beware of **dependency confusion** (an internal package name published on PyPI by an attacker: use `--index-url` to your index only, or scoped names/namespaces) and **typosquatting**.

### conda / mamba

`conda` (and faster `mamba`/`micromamba`) manage Python itself plus non-Python libraries (CUDA toolkit pieces, MKL, compilers, `ffmpeg`) from channels (`conda-forge`, `nvidia`, `pytorch`); common in data science and on HPC systems where compiled stacks matter. Prefer one tool per environment: mixing `pip` and `conda` installs in the same environment causes subtle breakage; install conda packages first, then pip packages that conda lacks, and never run `pip` as root. Export with `conda env export --from-history` or `conda-lock` for reproducibility.

### Choosing

| Situation | Tool |
|---|---|
| Quick script with a few dependencies | `python -m venv` + `pip` (or `uv`) |
| Application, reproducible deployment | `pip-tools` or `uv pip compile`/`uv lock` + hashes; container image |
| Library you publish | `pyproject.toml` + Hatch/Flit/setuptools; ranges not pins |
| Global CLI tools | `pipx` / `uv tool` |
| Heavy native scientific stack, HPC | conda/mamba, or system modules (Lmod) + venv |
| Multi-version testing | `tox` / `nox` / CI matrix |

## 5. Packaging your own code

### `pyproject.toml`

The standard (PEP 517/518/621) project file declares the build backend and metadata:

```toml
[build-system]
requires = ["hatchling>=1.24"]
build-backend = "hatchling.build"

[project]
name = "myops"
version = "0.3.1"                       # or dynamic = ["version"] from the package or VCS tags
description = "Operations tooling for the GPU cluster"
readme = "README.md"
requires-python = ">=3.10"
license = { text = "Apache-2.0" }
authors = [{ name = "Platform Team", email = "platform@example.com" }]
dependencies = ["requests>=2.31,<3", "pyyaml>=6", "prometheus-client>=0.20"]
classifiers = ["Programming Language :: Python :: 3", "Operating System :: POSIX :: Linux"]

[project.optional-dependencies]
redfish = ["python-redfish-library>=3"]
dev = ["pytest>=8", "ruff", "mypy", "pip-tools"]

[project.scripts]                         # console_scripts entry points: create 'myops' command
myops = "myops.cli:main"

[project.entry-points."myops.plugins"]    # plugin entry points discovered by importlib.metadata
gpu = "myops.plugins.gpu:Plugin"

[tool.hatch.build.targets.wheel]
packages = ["src/myops"]

[tool.ruff]
line-length = 100
[tool.pytest.ini_options]
testpaths = ["tests"]
```

Other backends: `setuptools` (still common; legacy `setup.py`/`setup.cfg` exist), `flit`, `poetry-core`, `pdm-backend`, `maturin` (Rust extensions), `scikit-build-core` (CMake extensions). Tool configuration (ruff, pytest, mypy, black, coverage) lives in `[tool.*]` tables.

### Building, installing, publishing

```bash
python -m pip install build twine
python -m build                       # creates dist/myops-0.3.1.tar.gz (sdist) and dist/myops-0.3.1-py3-none-any.whl (wheel)
python -m twine check dist/*
python -m twine upload --repository-url https://pypi.example.com/ dist/*   # private index; or 'uv publish'
python -m pip install dist/myops-0.3.1-py3-none-any.whl
python -m pip install -e ".[dev]"     # editable + extras for development
```

- **Wheel** (`.whl`): a prebuilt zip installed by unzipping (fast, no build step). Filename tags: `name-version-pythontag-abitag-platformtag`, e.g. `numpy-1.26.4-cp311-cp311-manylinux_2_17_x86_64.whl`. `py3-none-any` is pure Python. **manylinux** wheels run on most Linux distributions with a compatible glibc; **musllinux** wheels target Alpine (musl). If no compatible wheel exists, pip builds from the **sdist**, which needs compilers and headers (the usual reason an install takes 10 minutes or fails in a slim container).
- **Local version labels** (PEP 440 `+cu121`) are used by PyTorch index wheels to mark CUDA builds.
- **Versioning**: SemVer (`MAJOR.MINOR.PATCH`) for libraries, CalVer (`2026.10.1`) for tools; derive from Git tags (`hatch-vcs`, `setuptools-scm`) to avoid forgetting to bump; keep a changelog.
- **Console scripts**: the `[project.scripts]` table makes the installer create a launcher in the environment's `bin/`; this is how `pip`, `black` and `pytest` are exposed. The target function (`main()`) should return an exit code or call `sys.exit`.
- **Zipapps**: `python -m zipapp myapp -m "myops.cli:main"` or `shiv`/`pex` build single-file executables bundling dependencies, handy for shipping tools to servers without internet (Python still required). **PyInstaller**/`Nuitka` create standalone binaries.
- **Private indexes**: run a PyPI-compatible server (devpi, Artifactory, Nexus, GCP Artifact Registry, AWS CodeArtifact, GitLab/GitHub packages); configure clients via `pip.conf` / `PIP_INDEX_URL` / `uv` index settings; authenticate with tokens (keyring helpers), not passwords in files; mirror public packages you rely on.
- **Signing and provenance**: PyPI trusted publishing (OIDC from GitHub Actions, no long-lived tokens), Sigstore attestations, `pip install --require-hashes`.

### Native extensions

Packages with C/C++/Rust/CUDA code (NumPy, PyTorch, cryptography, grpcio) ship compiled `.so` files in wheels; they bind to the Python ABI (`cp311` tags or the stable ABI `abi3`), to the CPU architecture (x86_64, aarch64 for Grace/ARM hosts), to libc, and for GPU packages to CUDA runtime versions and the NVIDIA driver. This is where reproducibility gets hard.

## 6. Plugins and entry points

Entry points let installed distributions advertise components to other programs without imports being hard-coded (pytest plugins, Ansible/Click commands, Prometheus collectors).

```python
from importlib.metadata import entry_points, version, metadata
for ep in entry_points(group="myops.plugins"):       # discover
    plugin_cls = ep.load()                            # imports 'myops.plugins.gpu:Plugin'
    plugin_cls().register(registry)
print(version("myops"), metadata("myops")["Summary"])
```

Design guidance: define a small base class or Protocol (chapter 3.4) for plugins; load lazily; isolate failures (one broken plugin should not crash the host: catch and log); document the entry-point group name as part of the public API.

## 7. Python packaging on GPU and ML systems

- **PyTorch/TensorFlow/JAX wheels are CUDA-specific.** PyTorch publishes separate wheels per CUDA minor version on dedicated indexes (e.g. `https://download.pytorch.org/whl/cu121`); the default PyPI wheel bundles a CUDA runtime via `nvidia-*-cu12` packages (large). The **driver** on the host must be new enough for the CUDA runtime in the wheel (driver forward compatibility: a newer driver runs older CUDA runtimes; the reverse fails with "CUDA driver version is insufficient"). `torch.version.cuda`, `torch.cuda.is_available()`, `nvidia-smi` (driver and max supported CUDA), and `python -c "import torch; print(torch.__file__)"` verify.
- **Do not mix a system CUDA toolkit with wheel-bundled runtimes unintentionally**: `LD_LIBRARY_PATH` pointing to a different CUDA can load the wrong `libcudart`/`libcublas`/`libnccl`. Prefer wheel-bundled libraries or the NGC container's consistent stack.
- **NGC containers** (`nvcr.io/nvidia/pytorch:24.xx-py3`) bundle Python, PyTorch, CUDA, cuDNN, NCCL, Apex, TransformerEngine and tuned builds; use them as base images and add your pure-Python dependencies with a constraints file derived from the image (`pip freeze` inside) so you don't accidentally replace the tuned PyTorch with a PyPI wheel (the classic "pip install broke torch" incident).
- **ABI hazards**: NumPy 2.x changed the C ABI; packages compiled against NumPy 1.x fail with "module compiled using NumPy 1.x cannot be run in NumPy 2.x". Pin consistently; rebuild extensions; use `pip check`.
- **Architectures**: aarch64 (Grace Hopper/Blackwell hosts, Apple silicon) may lack wheels for some packages; sdist builds take long and need toolchains; verify wheel availability early (`pip download --only-binary=:all: --platform manylinux2014_aarch64 ...`).
- **Compilation**: building flash-attn, apex, xformers or custom CUDA extensions requires matching `nvcc`, a compatible GCC, correct `TORCH_CUDA_ARCH_LIST` (e.g. `9.0` for Hopper), enough RAM (`MAX_JOBS`), and takes tens of minutes; cache built wheels (`pip wheel`, `wheelhouse/`, internal index) instead of rebuilding on every node.
- **HPC**: use environment modules (Lmod) for compilers/MPI/CUDA and create venvs/conda envs on shared filesystems carefully (metadata-heavy `import` storms on Lustre/NFS slow startup; copy environments to node-local NVMe, use `python -X importtime`, zipimport, or container images; set `PYTHONDONTWRITEBYTECODE` on read-only paths; keep large packages (torch) in a squashfs/container image).
- **Slurm/Kubernetes**: bake environments into images or shared read-only locations; pin by digest; avoid `pip install` at job start (network dependency, rate limits, non-reproducible).
- **Offline/air-gapped**: build a wheelhouse (`pip download -r requirements.txt -d wheelhouse`), mirror indexes, and install with `--no-index --find-links wheelhouse`.

## 8. Containers and system integration

```dockerfile
FROM python:3.12-slim AS build
ENV PIP_NO_CACHE_DIR=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /src
COPY requirements.txt .
RUN python -m venv /opt/venv && /opt/venv/bin/pip install --require-hashes -r requirements.txt
COPY pyproject.toml ./ ; COPY src/ src/
RUN /opt/venv/bin/pip install --no-deps .

FROM python:3.12-slim
COPY --from=build /opt/venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH PYTHONUNBUFFERED=1
USER 10001
ENTRYPOINT ["myops"]
```

Notes: multi-stage builds keep compilers out of the runtime image; pin base images by digest; run as non-root; `PYTHONUNBUFFERED=1` so logs appear immediately; `PYTHONFAULTHANDLER=1` for crash tracebacks; copy `requirements.txt` before sources to leverage layer caching; slim vs alpine: Alpine uses musl and often lacks wheels (slow builds, subtle differences); distroless images reduce attack surface. For systemd services use a venv path in `ExecStart=/opt/myops/.venv/bin/myops`, `Environment=PYTHONUNBUFFERED=1`, a dedicated user, and `ProtectSystem=` hardening (chapter 1.15).

**System packages vs pip**: for scripts that must run on stock hosts, prefer the distribution's Python and its packaged libraries (`python3-yaml`, `python3-requests`, `python3-psutil`); otherwise ship a venv or zipapp. `ansible` itself uses the system or a venv interpreter (`ansible_python_interpreter`) on targets.

## 9. Troubleshooting imports and environments

| Symptom | Likely cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'x'` | Wrong interpreter/venv; package not installed; typo; running from a different directory | `which python`, `python -m pip show x`, activate venv, install, `python -c 'import sys; print(sys.path)'` |
| `ImportError: cannot import name 'y' from 'x'` | Version mismatch or circular import or shadowing | Check `x.__file__` and version; look for local `x.py`; restructure imports |
| `AttributeError: module 'x' has no attribute ...` | Shadowed module (`random.py`, `requests.py`) or old version | Rename file; remove `__pycache__`; check version |
| `attempted relative import with no known parent package` | Running a package file as a script | `python -m pkg.module` |
| `externally-managed-environment` | PEP 668 on system Python | Use venv/pipx/distribution package |
| `ResolutionImpossible` | Conflicting constraints | Read the chain; relax pins; use `pip install -vv`; upgrade the culprit; separate environments |
| Works in shell, fails in cron/systemd | Different PATH/interpreter/env | Use absolute venv python path; set `Environment=`; log `sys.executable` |
| `GLIBC_2.xx not found` / illegal instruction | Wheel built for newer glibc/CPU | Use matching manylinux tag/container; build from source |
| `CUDA driver version is insufficient` | Wheel CUDA runtime newer than driver | Upgrade driver or use older CUDA wheel (`cu118`) |
| `numpy.core.multiarray failed to import` / ABI error | NumPy 1/2 mismatch | Align versions; rebuild extensions |
| Slow imports / startup | Heavy top-level imports, network filesystem | `-X importtime`, lazy imports, local copy, container |
| Different behaviour on two nodes | Unpinned dependency drift | Lockfile, hashes, image digests, `pip freeze` diff |

Useful commands: `python -m pip debug --verbose` (supported tags), `python -c 'import platform; print(platform.platform(), platform.machine())'`, `ldd $(python -c 'import torch,os;print(os.path.dirname(torch.__file__)+"/lib/libtorch_cuda.so")')`, `pipdeptree` (dependency tree), `pip index versions pkg`, `python -m trace --listfuncs`, `strace -f -e trace=openat python -c 'import x' 2>&1 | grep -v ENOENT` to see where an import comes from.

## 10. Lab: environments and a packaged tool (untested)

1. **Import system**: create `a.py`, `b.py` importing each other (circular) and observe errors; refactor. Create a local `random.py` and see shadowing; remove it. Print `sys.path`, `sys.modules` size and use `-X importtime` on a heavy import.
2. **Packages**: build the `myops` package skeleton above with subpackages, relative and absolute imports, `__all__`, `__main__.py`; run with `python -m myops`; reproduce the relative-import-as-script error and explain it.
3. **Virtual environments**: create two venvs with conflicting versions of a library (for example `requests==2.25.1` and the latest); show isolation; call the interpreter directly without activation; inspect `sys.prefix`; try `sudo pip install` on a throwaway VM and note PEP 668 behaviour; use `pipx` for a CLI tool.
4. **Dependency management**: write `requirements.in` with unpinned deps; compile with `pip-compile --generate-hashes`; sync; remove a package and observe `pip-sync` cleaning; do the same with `uv` and compare speed; run `pip-audit`.
5. **pyproject and wheels**: write `pyproject.toml` (Hatch or setuptools), a console script and an entry-point plugin; build sdist and wheel; unzip the wheel and inspect `METADATA`, `entry_points.txt`, `RECORD`; install in a clean venv; run the command; install editable and modify code live.
6. **Private index**: run `devpi-server` (or a local `pypiserver`) in a container; upload your wheel; install it with `--index-url`; demonstrate dependency confusion risk with `--extra-index-url` and the mitigation.
7. **Reproducibility**: build a Docker image with hashed requirements; rebuild after a transitive release (simulate by editing a pin) and compare `pip freeze`; pin the base image by digest; measure image size and import time; add a multi-stage build.
8. **GPU packaging (needs a GPU VM)**: create a venv with a CUDA-specific PyTorch wheel; verify `torch.cuda.is_available()`; break it deliberately with a mismatched `LD_LIBRARY_PATH`; compare with an NGC container; write the `pip check`/`pip freeze` audit commands you would run on every node.
9. **Systemd/cron**: run the tool as a systemd service with the absolute venv interpreter, a dedicated user and `Environment=PYTHONUNBUFFERED=1`; show the same job failing with bare `python3` and fix it.
10. **Clean up** environments and containers.

Mark tested only after execution.

## 11. Common mistakes

- Installing with `sudo pip`, or into the system Python; using bare `pip` against an unknown interpreter.
- Committing `.venv` or not committing lockfiles; relying on "latest" at deploy time.
- Naming files after standard modules; running scripts from directories with stray `.py` files.
- Heavy work at import time; global state initialised in `__init__.py`.
- Pinning libraries too tightly (breaking downstream users) or applications too loosely (non-reproducible).
- Mixing conda and pip installs carelessly; mixing system CUDA with wheel CUDA.
- Using `--extra-index-url` with private package names; downloading and running unpinned packages on production hosts.
- Installing at runtime in containers and jobs (network flakiness, drift, security).
- Forgetting aarch64 and glibc compatibility; assuming wheels exist.

## 12. Interview angles

- "What happens when you `import x`? Where does Python look?"
- "Difference between a module, a package and a namespace package?"
- "Why use virtual environments? How do you make an environment reproducible?"
- "What is a wheel versus an sdist? What do the tags mean?"
- "How would you deliver a Python tool to 500 servers? To an air-gapped cluster?"
- "A job works on one node and fails on another with the same code. What do you check?" (interpreter, packages, lockfile, CUDA/driver, glibc, CPU, env vars.)
- "How do you avoid dependency confusion and supply-chain risks?"
- "`pip install` of an ML package broke PyTorch in the container; why and how do you prevent it?"
- "How do console scripts and entry points work?"

## 13. Checkpoint questions (35)

1. What is a module? **A:** A file (or built-in) providing a namespace; executed once on import.
2. What is cached in `sys.modules`? **A:** Imported module objects.
3. Import search order? **A:** `sys.modules`, built-ins, then `sys.path` entries.
4. First entry on `sys.path` for a script? **A:** The script's directory.
5. What is shadowing? **A:** A local file hiding an installed/stdlib module of the same name.
6. What does `__init__.py` do? **A:** Marks/initialises a regular package.
7. What is a namespace package? **A:** A package without `__init__.py`, possibly split across directories.
8. When do relative imports fail? **A:** When the file is run as a script, not as part of a package.
9. How to run a package module correctly? **A:** `python -m package.module`.
10. How to break a circular import? **A:** Restructure, import inside functions, or type-check-only imports.
11. How to read package data files? **A:** `importlib.resources`.
12. Why src layout? **A:** Forces testing against the installed package.
13. What is a virtual environment? **A:** Isolated site-packages with its own interpreter link.
14. How to use a venv without activating? **A:** Call `.venv/bin/python` directly.
15. What is PEP 668? **A:** Marks system Python as externally managed to prevent pip breaking it.
16. What is pipx for? **A:** Isolated installs of CLI tools.
17. Library vs application dependency style? **A:** Ranges versus fully pinned lockfile.
18. What does `pip-compile --generate-hashes` produce? **A:** A pinned requirements file with hashes.
19. What does `pip-sync` do? **A:** Makes the environment match the lock exactly.
20. What is `uv`? **A:** A fast Rust-based pip/venv/project manager.
21. Why avoid mixing conda and pip? **A:** Can corrupt dependency consistency.
22. What is dependency confusion? **A:** Public package with a private name wins during install.
23. What is `pyproject.toml`? **A:** Standard build/metadata/tool config file.
24. What is a console script entry point? **A:** Launcher created from `module:function` at install.
25. What is a wheel? **A:** Prebuilt installable zip with compatibility tags.
26. What is `manylinux`? **A:** Tag for broadly compatible Linux wheels.
27. Why might pip build from source? **A:** No compatible wheel exists.
28. What does `+cu121` denote? **A:** A local version label for a CUDA 12.1 build.
29. When does a newer CUDA wheel fail? **A:** When the driver is too old.
30. Why use NGC containers? **A:** Consistent tuned CUDA/NCCL/PyTorch stack.
31. NumPy 2 ABI issue? **A:** Extensions built against 1.x break on 2.x.
32. Why not `pip install` at job start? **A:** Non-reproducible, network-dependent.
33. How to install offline? **A:** Wheelhouse with `--no-index --find-links`.
34. Why set `PYTHONUNBUFFERED=1` in containers? **A:** Logs flush immediately.
35. First debugging step for ModuleNotFoundError? **A:** Check which interpreter and `sys.path`.

## 14. Sources and review notes

**Written in original words.** Principal sources:

- Mark Lutz, *Learning Python*, 6th ed., part V (modules and packages: the big picture, module coding basics, module packages, module odds and ends).
- The author's `nvidia-devops` repository, volume 02 (Python fundamentals and tooling masterclasses) and the volume on GPU/NVIDIA software stacks for the CUDA/driver packaging scenarios.
- Packaging standards (PEP 440, 517/518, 621, 668, 420, 427, 503/691) and the documentation of pip, uv, pip-tools, Poetry, Hatch, conda and the Python Packaging User Guide informed the details.
- Examples are the author's constructions.

**Flagged for verification before publishing:** all command flags and tool behaviours against current versions (uv, pip, pip-tools, Hatch, PyTorch index URLs and CUDA tags, NGC image tags), PEP 668 behaviour per distribution, and every Dockerfile and `pyproject.toml` snippet; all labs are **untested**.
