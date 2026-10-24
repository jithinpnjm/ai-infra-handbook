---
id: "c06-06"
title: "6.6 Environment modules, Spack and EasyBuild"
sidebar_label: "6.6 Environment modules, Spack and EasyBuild"
sidebar_position: 6
description: "Managing scientific and AI software on shared clusters: how environment variables select software, Environment Modules and Lmod (modulefiles, hierarchies), Spack (specs, concretisation, environments, externals, build caches, module generation), EasyBuild, containers and conda as alternatives, site layout, GPU toolchains and operational practice"
status: "drafted"
tier: "2"
level: "I"
lab_venue: "GCP / GKE"
---

# 6.6 Environment modules, Spack and EasyBuild

| | |
|---|---|
| Level | Intermediate |
| Priority tier | 1 |
| Lab venue | Linux login node or VM with Environment Modules or Lmod; optional Spack and EasyBuild installs |
| Part | Part 6: HPC and Slurm |
| Status | Drafted. Spack facts were read from the Spack documentation in a shallow clone (commit `29aea8a`, 2026-10-23); I did **not** run Spack, Lmod, Environment Modules or EasyBuild (execution of the cloned Spack setup script was refused by the environment's safety check, and I did not work around it). Module and EasyBuild syntax is from documentation knowledge. All labs are **untested** |

## Why this matters for AI infrastructure

A cluster serves many users who need different compilers, MPI builds, CUDA toolkits, Python stacks and applications, often at conflicting versions. Letting everyone install into their home directory produces slow, inconsistent, unsupportable chaos; installing one global version breaks half the users. Environment modules and the build frameworks that feed them (Spack, EasyBuild) are how HPC sites resolve this. AI platforms face the same problem in a new form: CUDA, cuDNN, NCCL, PyTorch and framework versions must match each other and the driver, and containers or conda environments have taken over part of the job. Understanding both the classical and the modern approaches lets you design a software stack for a GPU cluster and debug "works on login node, fails on compute node".

## Prerequisites and outcomes

Needs 6.2 to 6.5 and Part 1 (Linux, shell, environment variables, shared libraries). After this chapter you can:

- Explain how `PATH`, `LD_LIBRARY_PATH`, `RPATH`/`RUNPATH`, `CPATH` and friends determine which software runs, and how modules manipulate them.
- Use and write Environment Modules (Tcl) and Lmod (Lua) modulefiles; explain hierarchical module trees and why they prevent ABI mismatches.
- Describe Spack's model (specs, variants, concretisation, installs, environments, externals, build caches, generated modules) and EasyBuild's model (easyconfigs, toolchains).
- Lay out a shared software tree for multiple CPU architectures and GPU generations, and publish it read-only across nodes.
- Choose among modules, Spack, EasyBuild, conda/uv, and containers for a given need, and combine them sensibly.
- Troubleshoot typical failures: wrong library picked up, mixed compilers, missing module on compute nodes, stale caches.

## 1. The problem: environment variables choose your software

When you type `python`, the shell searches directories in `PATH`. When a program starts, the dynamic loader finds shared libraries by `RPATH`/`RUNPATH` embedded in the binary, then `LD_LIBRARY_PATH`, then the cache `ld.so.cache`, then default directories. Compilers consult `CPATH`/`C_INCLUDE_PATH`/`LIBRARY_PATH`/`PKG_CONFIG_PATH`. Python uses `PYTHONPATH`. CUDA uses `CUDA_HOME`/`CUDA_PATH`. Selecting a toolchain means setting several of these consistently, and unsetting them cleanly when switching.

Doing this by hand in `.bashrc` fails because: it is fragile (order matters), per-user, not discoverable, and mistakes (an old library earlier in `LD_LIBRARY_PATH`) cause baffling runtime errors. Inspect with `ldd ./binary`, `readelf -d ./binary | grep -i path`, `echo $LD_LIBRARY_PATH | tr : '\n'`, and `LD_DEBUG=libs ./binary` (prints the loader's search).

## 2. Environment Modules and Lmod

A **module** is a small file describing environment changes to apply when loading software and to undo when unloading. One shell function, `module`, does everything. The SCL book introduces it as the standard way to switch compilers, MPI implementations and application environments (Table 21-1 there lists the commands).

| Command | Meaning |
|---|---|
| `module avail` (`ml av`) | List modules visible on `MODULEPATH` |
| `module load gcc/13.2.0 openmpi/5.0.3` | Apply modules (order and dependencies matter) |
| `module unload openmpi` / `module swap gcc gcc/12.3.0` | Remove / replace |
| `module list` | What is loaded |
| `module purge` | Unload everything (put this at the top of job scripts) |
| `module show NAME` (Lmod: `module help`, `module whatis`) | Show what loading would do |
| `module use /path` / `module unuse` | Add or remove a directory from `MODULEPATH` |
| `module save NAME` / `module restore NAME` (Lmod) | Save and restore a loaded set (collections) |
| `module spider NAME` (Lmod) | Search the whole hierarchy, including modules not yet visible |
| `module try-load`, `module is-loaded` | Scripting helpers |

Two implementations: **Environment Modules** (originally Tcl-based, current versions in C with Tcl modulefiles) and **Lmod** (Lua-based, from TACC), which adds hierarchical module awareness, caching (fast `avail` on huge trees), `spider`, collections, sticky and hidden modules, and a richer Lua modulefile language. Lmod can also read Tcl modulefiles. Many sites use Lmod; some use Environment Modules; Spack generates either.

### A modulefile (Tcl) and its Lmod (Lua) equivalent

Tcl (`/opt/modulefiles/openmpi/5.0.3-gcc13`):

```tcl
#%Module1.0
module-whatis "Open MPI 5.0.3 built with GCC 13"
conflict openmpi
prereq gcc/13.2.0
set root /opt/apps/x86-64-v3/openmpi/5.0.3-gcc13
prepend-path PATH            $root/bin
prepend-path LD_LIBRARY_PATH $root/lib
prepend-path MANPATH         $root/share/man
prepend-path CPATH           $root/include
setenv       MPI_HOME        $root
```

Lua (Lmod):

```lua
whatis("Open MPI 5.0.3 built with GCC 13")
family("mpi")
depends_on("gcc/13.2.0")
local root = "/opt/apps/x86-64-v3/openmpi/5.0.3-gcc13"
prepend_path("PATH", pathJoin(root, "bin"))
prepend_path("LD_LIBRARY_PATH", pathJoin(root, "lib"))
setenv("MPI_HOME", root)
```

Good modulefile practice: set only what is needed; declare `conflict`/`family` so two MPIs cannot be loaded; declare prerequisites; use `setenv` for homes such as `CUDA_HOME`; never `source` heavy scripts at load time; make the load idempotent and the unload exact (the module system reverses `prepend-path` automatically); document with `whatis`/`help`; avoid putting `LD_LIBRARY_PATH` of user-space libs ahead of system-critical paths unless required, and prefer `RPATH` at build time.

### Hierarchies

A flat list of `openmpi/5.0.3` leaves ambiguity: built with which compiler? A **hierarchical** layout (Lmod's strength) makes the choice structural: `Core` modules (compilers) are visible first; loading `gcc/13.2.0` reveals `Compiler/gcc/13.2.0` modules (MPI, math libraries); loading an MPI then reveals `MPI/gcc/13.2.0/openmpi/5.0.3` modules (HDF5, PETSc, applications). The effect: you cannot load a library built with a different compiler or MPI than the one you have loaded, because it is simply not visible, and swapping the compiler automatically swaps dependent modules. Costs: more complex trees and user confusion about missing modules (use `module spider`).

### Site conventions that keep users sane

- Name modules `name/version` (`cuda/12.4.1`); encode toolchain in the version suffix or the hierarchy.
- Provide sensible **default versions** but always pin versions in job scripts.
- Mark deprecated modules with a warning message and a removal date.
- Provide `module load` for common bundles (a "PyTorch GPU" module that brings Python, CUDA, cuDNN, NCCL) separately from the individual parts.
- Keep **login and compute node environments identical**; a module that exists only on login nodes causes job failures (use the same shared tree).
- Cache: Lmod's cache (`LMOD_CACHE`) must be refreshed after adding modules; stale caches produce "module not found" for a module that exists.

## 3. Spack

**Spack** is a package manager designed for HPC: it builds software from source with a *recipe* (`package.py`) per package, supports many versions, compilers, build options and targets side by side, and records exactly what was built. Key ideas (all from the Spack documentation):

### Specs

A **spec** is a constraint on what you want, using a compact syntax:

```text
spack install hdf5                    # any version, default variants
spack install hdf5@1.14.3             # a version
spack install hdf5 +mpi ^openmpi@5    # variant, and a constraint on the dependency
spack install hdf5 %gcc@13            # build with a compiler
spack install hdf5 target=x86_64_v3   # micro-architecture
spack install petsc +cuda cuda_arch=90
```

`@` version, `+/~` boolean variants, `name=value` valued variants, `%` compiler, `^` dependency constraint, `target=` and `os=` for platform. `spack spec NAME` shows the fully resolved result without building.

### Concretisation

Spack's solver ("concretizer") takes the abstract specs plus configuration and produces a **concrete spec**: every package, version, variant, compiler and dependency decided. It resolves conflicts between requirements and reuses compatible already-installed packages where allowed. Each concrete spec has a **hash**; the install path includes it (`openmpi/5.0.10-gcc-13.3.0-<hash>` in the documentation's example listing), so many builds coexist without clobbering one another. This is what makes Spack suitable for multi-configuration clusters.

### Environments

Spack environments group specs, config and the resolved result (the documentation walks through this):

```bash
spack env create myenv
spack env activate myenv
spack add curl@8 python py-numpy py-scipy py-matplotlib   # edits spack.yaml
spack concretize                                           # solve
spack install                                              # build everything
spack env deactivate
```

The manifest `spack.yaml` lists `specs`, `view: true` (a merged prefix of symlinks) and `concretizer: unify: true` (all root specs share one consistent set of dependencies; other modes exist). The resolved result is stored in `spack.lock`, which can reproduce the exact build elsewhere. Commit both to Git. This is the Spack analogue of a lock file in `pip`/`uv` and Terraform.

### Configuration: compilers, externals, preferences

- **Compilers** are discovered or declared; in current versions compilers are packages like others (the documentation's ROCm example shows `llvm-amdgpu` declared as an external with `extra_attributes: compilers: c: /opt/rocm-5.3.0/bin/amdclang`).
- **Externals** let Spack use software already on the system instead of building it. In `packages.yaml`, `buildable: false` plus `externals: - spec: ... prefix: ...` pins to the system version. This is how you tell Spack to use the vendor MPI, the system CUDA toolkit, or the driver-matched libraries. The GPU documentation page shows this pattern for ROCm (with `variants: amdgpu_target=gfx90a`); CUDA is configured analogously (`cuda_arch=90` for Hopper, `100` for Blackwell: from knowledge; check the package).
- **Requirements and preferences** (`require:`, `prefer:`) steer the solver site-wide: the microarchitecture, the compiler, the MPI provider.
- **Mirrors and build caches**: `spack buildcache push <path/url/mirror> <spec>` creates binary tarballs and metadata; other installs download them instead of compiling (the documentation example pushes `ninja` to a local directory `./spack-cache`). Build caches signed with GPG, hosted in object storage, are how large sites avoid recompiling for hours.
- **Module generation**: `spack module tcl refresh` or `spack module lmod refresh` produces modulefiles for installed packages; add them with `module use $SPACK_ROOT/share/spack/modules/<arch>`. `modules.yaml` controls naming, hierarchy (core/compiler/MPI), hiding, and which variables are set. The module listing in the documentation shows names like `openmpi/5.0.10-gcc-13.3.0-<hash>`.

Strengths: reproducibility, flexibility, huge package repository, many variants, micro-architecture targeting. Costs: build time, disk, learning curve, and discipline (pin the Spack version, pin the package repository, review the concretised result, test).

## 4. EasyBuild

**EasyBuild** (from the HPC community, Python-based) automates building software from **easyconfig** files (`.eb`), each a declarative description (name, version, toolchain, sources, dependencies, build system, checks). It installs into a configured prefix and generates modules (Lmod or Tcl) with a configurable **module naming scheme** (flat or hierarchical, for example `HierarchicalMNS`). Concepts:

- **Toolchains**: coherent compiler + MPI + math library bundles with a version, such as `foss` (GCC, Open MPI, OpenBLAS, FFTW, ScaLAPACK) or `intel`. Everything in a stack is built with one toolchain, which gives binary compatibility; a new toolchain generation (`foss/2024a`) is a new stack.
- `eb Foo-1.2-foss-2024a.eb --robot` builds the package and all dependencies; `--dry-run`/`-D` shows the plan.
- Large public collections of easyconfigs exist; sites copy and adjust them. The European EESSI project distributes an EasyBuild-built software stack via CernVM-FS for several CPU architectures (from knowledge).

Compared with Spack: EasyBuild's toolchain model is simpler and more prescriptive (fewer combinations, predictable); Spack's model is more flexible and constraint-solving. Many sites use one or the other, a few use both (Spack for flexibility, EasyBuild for the curated base). Neither is a substitute for testing.

## 5. Where containers, conda and pip fit

| Tool | Strength | Weakness for clusters |
|---|---|---|
| **Modules + native builds** | Best performance (tuned to hardware and fabric), small overhead, transparent | Admin effort; per-site |
| **Containers** (Apptainer/Singularity, enroot+pyxis, Docker where permitted) | Whole user-space stack frozen; portable; NGC images for CUDA/PyTorch | Host driver and kernel interplay (GPU libraries mounted from host), MPI/fabric compatibility, image size; need a registry (6.13, 6.29) |
| **conda / mamba / uv + venv** | Python-centric, fast for users, good for AI libraries | Binary compatibility with system MPI/CUDA; large file counts hurt parallel file systems; reproducibility depends on discipline |
| **Spack environments** | Reproducible native builds with exact options | Build time |

In AI clusters the common pattern is: the **driver and CUDA userspace baseline** are managed by the admin (image or modules, matching the driver version), user applications run from **container images** (NGC or site-built) launched through Slurm with pyxis, and Python development uses **uv/conda** on shared storage, with a small number of site modules for compilers, MPI and CUDA toolkits for building extensions. Keep a clear rule about which layer owns which version, because mixing a conda-installed CUDA runtime with the system driver and a module-loaded NCCL is a rich source of failures (Part 10).

Warning for parallel file systems: a conda environment or Python virtual environment holds tens of thousands of tiny files; hundreds of ranks importing it at job start hammer the metadata servers. Mitigations: containers (one large squashfs file), node-local copies, `python -X importtime` awareness, or zipped packaging (6.18, 6.29).

## 6. Designing the shared software tree

A workable layout (the SCL book installs compilers and libraries on a shared NFS tree from the control node; this extends it):

```text
/opt/apps/                       # exported read-only to all nodes
  x86-64-v3/                     # one subtree per CPU baseline (also: neoverse-v2, etc.)
    gcc/13.2.0/
    openmpi/5.0.3-gcc13/
    hdf5/1.14.3-gcc13-openmpi5/
  noarch/                        # python-only or scripts
  cuda/12.4.1/                   # toolkits: arch-independent userspace
/opt/modulefiles/                # modulefiles, or generated from the above
/opt/spack/ or /opt/easybuild/   # the build frameworks and their configs (admin-only write)
```

Principles:

1. **Admins write; users read.** Mount read-only on compute nodes; build as a dedicated, non-root software account, never as root.
2. **One tree per CPU baseline** (and per GPU generation when binaries differ), selected at login by detecting the node (an `lmod` `SitePackage` hook or a module `MODULEPATH` set from `lscpu`), so the same module name loads the right build everywhere (6.5 section 6 on `-march`).
3. **Scalable serving**: NFS is fine for small clusters; at scale use parallel-file-system software volumes, node-local caching, CVMFS, or bake critical pieces into the node image (6.22).
4. **Immutable releases**: never edit an installed version in place; add a new version and deprecate the old one. Keep old toolchains for reproducibility of published results.
5. **Version everything**: the Spack environment lock file, easyconfig set and module tree should live in Git with a changelog.
6. **Test**: for each new stack, a smoke test suite (compile and run hello-MPI, a CUDA sample, a small benchmark) runs on every node type via Slurm before announcement (6.28).
7. **Document** the supported matrix (compiler × MPI × CUDA) and the policy for requests.

## 7. GPU specifics

- **Driver versus toolkit**: the kernel driver is installed on the node (image/BCM) and provides `libcuda.so`; the CUDA toolkit (compiler `nvcc`, libraries) can be a module or in a container and must be **no newer than the driver supports** (the driver's CUDA version in `nvidia-smi` is the maximum; Part 10 explains forward and minor-version compatibility).
- Provide several `cuda/X.Y` modules; set `CUDA_HOME`; ensure `nvcc` matches host compiler support (a GCC version too new for the toolkit breaks builds).
- NCCL, cuDNN, TensorRT and cuBLAS versions must be consistent with the framework build. Frameworks bundled in pip wheels carry their own CUDA runtime libraries and need only the driver; modules and wheels in one process can clash.
- Compute capability: build with the right architecture (`sm_90` for Hopper, `sm_100` for Blackwell; from knowledge) or PTX for forward compatibility; Spack variant `cuda_arch`.
- HPC-X, NVIDIA HPC SDK and NGC provide pre-tuned MPI, compilers and containers; treat them as upstream software to be installed as modules (the SDK ships its own modulefiles).

## 8. Operating the stack

| Task | Practice |
|---|---|
| Request a new package | Ticket with use case; admin builds in a staging prefix, tests, then publishes |
| Update a compiler | New toolchain generation; rebuild the dependent stack; keep the old for a deprecation period |
| Security patch | Rebuild affected packages; list consumers (Spack `spack dependents`); notify users |
| Reproducibility | Users record `module list` and `module save`; jobs `module purge` then load by explicit version; containers pinned by digest |
| Slow logins / `module avail` | Enable the Lmod cache; reduce the tree; check shared-file-system latency |
| Space | Garbage-collect unused Spack installs (`spack gc`), remove deprecated modules after notice, de-duplicate with build caches |
| Audit | Track who installed what, from which recipe, with which hash |

## 9. Failure modes

| Symptom | Likely cause | Check |
|---|---|---|
| `error while loading shared libraries: libfoo.so` | Module not loaded on the compute node, wrong `LD_LIBRARY_PATH`, missing RPATH | `ldd`, `module list` in the job, job script `module load` lines |
| Works on login node, fails in the job | Different environment: login-shell profile vs batch (`sbatch` exports the submit environment by default; `--export=NONE` does not), modules available only on login | Print `env`/`module list` at job start; use `module purge` and explicit loads |
| `Illegal instruction` | Module for a newer CPU baseline than the node | `lscpu` flags; arch-aware `MODULEPATH` |
| Segfault in MPI app | Mixed MPI or compiler between build and run | `ldd`, `module list`, rebuild |
| Module not found | Stale Lmod cache, hierarchy (prerequisite not loaded), `MODULEPATH` | `module spider`, rebuild cache |
| Different results after update | New compiler or library version, FP flags | Compare module lists; strict-FP rebuild (6.5) |
| Slow job start | Python env on parallel FS, metadata storm | Container or node-local copy |
| Spack concretisation takes long or changes | Unpinned repo or config; reuse settings | Pin Spack and repo commit; review `spack.lock` diff |

## 10. Lab (untested)

1. On a machine with Lmod or Environment Modules, write the Tcl and Lua modulefiles in section 2 for a locally installed `/opt/test/foo`, add the directory with `module use`, and exercise `avail`, `load`, `list`, `show`, `unload`, `purge`. Verify `PATH` changes and exact restoration.
2. Build a tiny two-level hierarchy (compiler → library) in Lua with `family()`; confirm that swapping the compiler hides the library, and use `spider` to find it.
3. Install Spack in a scratch prefix (use a release, pin the commit), create an environment with `zlib` and `hdf5 +mpi`, run `spack spec`, `spack concretize`, `spack install`, then `spack module lmod refresh` and load the generated module. Inspect `spack.lock`.
4. Create a local build cache with `spack buildcache push ./cache zlib`, install in a second prefix from it, and compare time.
5. Write a `packages.yaml` fragment marking the system CUDA as an external and requiring `cuda_arch=<your GPU>`; check with `spack spec petsc +cuda`.
6. Install EasyBuild and run `eb --dry-run` on an easyconfig; read the toolchain definition.
7. Design the `/opt/apps` tree for a cluster with two CPU types and two GPU generations; write the `MODULEPATH` selection logic.
8. Write the "new stack release" checklist including smoke tests.

## 11. Interview angles

- How do `PATH`, `LD_LIBRARY_PATH` and `RPATH` interact? How would you debug a wrong-library error?
- Modules versus containers versus conda: when each?
- What is a hierarchical module tree and what mistake does it prevent?
- What does a Spack hash in the install path mean? How does a Spack environment give reproducibility?
- How do you make Spack use the system CUDA or MPI?
- Why must login and compute nodes see the same software tree? How do you serve a tree to 10,000 nodes?
- A job works interactively but not from `sbatch`. What is different?
- How do you handle a cluster with Intel and AMD nodes in one module tree?
- How would you roll out a new compiler generation without breaking users?
- What are the metadata costs of Python environments on Lustre?

## 12. Checkpoint questions (30)

1. How does the dynamic loader find a shared library?
2. What are `RPATH` and `RUNPATH`?
3. Why are `.bashrc` environment hacks a poor solution?
4. What does `module load` change, and how is unload exact?
5. Name four commands you use daily with modules.
6. What does `module purge` belong at the top of?
7. Compare Environment Modules and Lmod.
8. What do `conflict`, `prereq` and `family` do?
9. What is a hierarchical module tree and its main user-facing difficulty?
10. What is `module spider` for?
11. What is the Lmod cache and what happens if it is stale?
12. Why pin versions in job scripts?
13. What is a Spack spec? Explain `@`, `+`, `~`, `%`, `^`.
14. What does concretisation produce?
15. What is in a Spack install path and why?
16. What is `spack.yaml` and `spack.lock`?
17. What does `concretizer: unify: true` mean?
18. How do externals work and why use them for CUDA or MPI?
19. How do build caches speed installs?
20. How does Spack generate modulefiles?
21. What is an EasyBuild easyconfig and a toolchain?
22. Give an example toolchain and its components.
23. Compare Spack and EasyBuild.
24. Where do containers beat modules, and where not?
25. Why are large conda environments a problem on parallel file systems?
26. Why one software subtree per CPU baseline?
27. Why mount the software tree read-only?
28. What does the driver's CUDA version in `nvidia-smi` mean for toolkit choice?
29. Why can a job that works on the login node fail in Slurm?
30. List four checks in a release process for a new software stack.

## 13. Sources and review notes

- Modules concept and commands: *Supercomputers for Linux SysAdmins* chapter 21 (Environment Modules and Lmod; build systems) and chapter 24 (installing compilers and libraries on the shared tree, NFS), and *Parallel and High Performance Computing* section 17.10 (toolchain modules and the caveat that toolchain modules are less tested than vendor distributions). Restated in my words.
- Spack: read from the Spack documentation (`environments_basics`, `module_file_support`, `gpu_configuration`, `binary_caches`, `environments`) in a shallow clone, commit `29aea8a`, 2026-10-23. Command forms in section 3 are from those pages.
- EasyBuild, Lmod hierarchy details, `cuda_arch` values, EESSI, and the site layout are from general knowledge and are not verified here.
- Not done: no module system, Spack or EasyBuild command was executed for this chapter.
