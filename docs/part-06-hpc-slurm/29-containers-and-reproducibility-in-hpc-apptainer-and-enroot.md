---
id: "c06-29"
title: "6.29 Containers and reproducibility in HPC: Apptainer and enroot"
sidebar_label: "6.29 Containers and reproducibility in HPC: Apptainer and enroot"
sidebar_position: 29
description: "Running containers on HPC and GPU clusters reproducibly: Apptainer/Singularity (SIF, definition files, build, GPU --nv, MPI hybrid and bind models, cache, signing), Charliecloud, enroot compared, security models, and a reproducibility discipline (pinning by digest, lock files, labels, tests, SBOMs) backed by a tested definition-file and Dockerfile linter"
status: "drafted"
tier: "2"
level: "I"
lab_venue: "GCP / GKE"
---

# 6.29 Containers and reproducibility in HPC: Apptainer and enroot

| | |
|---|---|
| Level | Intermediate |
| Priority tier | 2 |
| Lab venue | Linux host with Apptainer; Slurm for the MPI parts |
| Part | Part 6: HPC and Slurm |
| Status | Drafted. Apptainer statements come from the Apptainer user documentation (apptainer/apptainer-userdocs commit `69efb83`, 2026-10-23: definition files, GPU, MPI, build environment); enroot/pyxis from 6.13. `code/part06/container_lint.py` was run on a bad and a good definition file (output shown). **Apptainer itself was not run** (Linux only), nor any container build. Security-model statements are from general knowledge. Labs **untested** |

## Why this matters for AI infrastructure

6.13 showed how NVIDIA's enroot and pyxis run containers inside Slurm. Many clusters, including most academic and national-lab systems, use **Apptainer** (formerly Singularity), and many scientific groups publish their software as Apptainer/Singularity images. Whichever runtime you use, the harder problem is **reproducibility**: can you rebuild the same environment next year, prove which libraries produced a result, and run it on a different cluster? AI makes this sharper: CUDA, cuDNN, NCCL, PyTorch, drivers and Python wheels interact, and a one-line drift changes performance or numerics. This chapter compares the runtimes and gives a discipline that makes container images trustworthy.

## Prerequisites and outcomes

Needs 6.6, 6.13, 6.4/6.12 (MPI, NCCL). After this chapter you can:

- Explain what a container is mechanically (cgroups, namespaces, chroot) and why HPC runtimes differ from Docker.
- Build, run and share Apptainer images (SIF, definition files, `build`, `exec`, `--nv`, binds), and explain the host-MPI hybrid and bind models.
- Compare Apptainer, Charliecloud and enroot/pyxis along security, GPU, MPI, image format and Slurm integration.
- Apply a reproducibility discipline and lint definition files and Dockerfiles for violations.
- Manage caches, signing, and image distribution.

## 1. What a container is, and why HPC needed new runtimes

The SCL book (chapter 16) defines a container as "an isolated set of processes" with limited access to the other processes, the network, the file system and devices: similar to a virtual machine but with no emulation, since all processes are real and visible from the host. It is built from three kernel facilities: **cgroups** (limits on memory, CPU, devices), **namespaces** (PID, user, mount, network, IPC isolation, so processes can have "virtual" numbers) and **chroot** (change root directory). Docker packaged these with a root daemon and a layered image format. HPC clusters need different properties:

| Requirement | Docker daemon model | HPC runtimes |
|---|---|---|
| No root daemon, no privilege escalation by users | Root daemon; docker group = root | Unprivileged execution (setuid helper or user namespaces) |
| Same user identity and file permissions inside | Often root inside; UID remapping | Run as the invoking user (shared file systems demand it) |
| Scheduler owns the processes | Containers are children of the daemon | The container is the Slurm task (cgroups, accounting, signals) |
| Direct access to the fabric and GPUs | Needs plumbing | Host devices and driver libraries bound in |
| Shared file systems and home mounted | Explicit volumes | Home, scratch and project mounted by default |
| One portable file | Layered store | Single image file (SIF, squashfs) |
| MPI across nodes | Network namespaces get in the way | Host network, host or hybrid MPI |

## 2. Apptainer

Apptainer (the Linux Foundation project formerly known as Singularity; "Singularity" is also the name of SylabsInc's separate commercial line) runs a container from a single **SIF** (Singularity Image Format) file, a squashfs-based immutable image that can also carry signatures, definition files and extra data partitions.

### Core commands

```bash
apptainer pull docker://ubuntu:24.04                        # create a SIF from an OCI image (cached)
apptainer build myenv.sif myenv.def                          # build from a definition file
apptainer build --fakeroot myenv.sif myenv.def               # unprivileged build using user-namespace fake root
apptainer exec --nv -B /scratch:/scratch myenv.sif python train.py     # run a command with NVIDIA GPU support and a bind mount
apptainer shell myenv.sif ; apptainer run myenv.sif          # interactive shell / run the %runscript
apptainer inspect myenv.sif ; apptainer sign myenv.sif ; apptainer verify myenv.sif
```

(Command set from the user documentation; flags such as `--fakeroot`, `--nv`, `-B/--bind` appear there.)

### Definition files

From the documentation: a definition ("def") file is "a set of blueprints explaining how to build a custom container". It has a **header** (`Bootstrap:` first, which selects the *bootstrap agent*; for the `docker` agent `From:` names the base image; other agents include `oras`, `localimage`, `scratch`, `library`, `shub`, `yum`/`dnf`, `debootstrap`) and **sections** introduced by `%`: `%files` (copy from host), `%post` (build-time commands), `%environment`, `%runscript`, `%startscript`, `%test` (run at build end), `%labels`, `%help`, `%setup`, `%arguments`. Build-time sections run under `/bin/sh`.

```text
Bootstrap: docker
From: nvcr.io/nvidia/pytorch@sha256:<digest>

%labels
    Version 2026.10
    Maintainer hpc-team@example.org

%post
    pip install --no-cache-dir -r /opt/requirements.lock

%test
    python -c "import torch; print(torch.__version__)"
```

### Cache

Apptainer caches SIF images generated from remote sources and OCI/docker layers, by default under `$HOME/.apptainer/cache`; set `APPTAINER_CACHEDIR` to move it (use `sudo -E` to carry the variable through a root build). On clusters point the cache and `APPTAINER_TMPDIR` to node-local or scratch storage, not a small, quota-limited home or a metadata-sensitive shared mount, and clean it periodically (`apptainer cache clean`). The SCL book's "Caching" section makes the same point about image and layer caches for the HPC runtimes it covers.

### GPUs

`--nv` sets up the container for NVIDIA GPUs by binding the host driver libraries and device nodes into the container (documentation: "natively supports ... NVIDIA's CUDA ..., AMD's ROCm ..., and Intel's Gaudi", plus OCI **CDI** (Container Device Interface) as a generic method, and experimental `--nvccli` to use `nvidia-container-cli`). The documentation warns about one practical failure: because libraries are bound from the host, the **libc versions in the container and on the host must not be too far apart**, or you get libc mismatch errors (the error happens when the container's libc is older than the host's, and sometimes when it is much newer). The CUDA toolkit in the image must also be compatible with the host driver (Part 10). Check with `apptainer exec --nv img.sif nvidia-smi` and a small CUDA test.

### MPI

Two documented models for MPI applications:

- **Hybrid model**: the host provides `mpirun`/`srun` and its MPI; the container also contains an MPI; the launcher starts the container per rank and the MPI inside connects back through PMI (for Open MPI, `orted` launches Apptainer, which starts the application, which connects back through PMI). Needs the container's MPI to be ABI/PMI-compatible with the host's (same implementation and a close version). Advantage: the application is self-contained.
- **Bind model**: the container has no MPI; the host's MPI libraries are bind-mounted in. Needs administrators to allow user-specified bind mounts.

In Slurm: `srun --mpi=pmix apptainer exec ... ./app` (6.12). For AI jobs NCCL ships with the framework in the image, uses the host's IB devices and driver, and needs host networking.

### Security model (general knowledge, verify)

Apptainer can run with a small setuid-root helper (to mount SIFs and set up namespaces) or entirely in **unprivileged mode using user namespaces** (and the `--fakeroot` feature maps your user to root inside the build). The design principle: privilege escalation inside the container is impossible because the user stays the same user (there is no `sudo` inside). Security controls include signed SIF images (PGP keys by default: `apptainer sign` / `verify`, with a key server), image encryption, and restricting which images may run (`limit container` settings in `apptainer.conf`: allowed paths/owners/groups, signed-only). Distributions that restrict unprivileged user namespaces (some Ubuntu configurations) need the administrators to allow it or use the setuid mode.

## 3. Charliecloud, enroot and the comparison

- **Charliecloud** (from Los Alamos): minimal, unprivileged containers using only user namespaces; images are directory trees or squashfs; `ch-image` builds, `ch-run` runs; its small code size is a selling point for security reviews. The SCL book covers it together with Singularity.
- **enroot + pyxis** (6.13): NVIDIA's pair; converts OCI images to squashfs, runs unprivileged, hooks for GPU/IB/PMIx, Slurm integration via the pyxis SPANK plugin with `srun --container-*` options.
- **Podman rootless** and **Docker rootless**: OCI-compliant tools that can run in user namespaces; more features, heavier, less HPC-tuned (can work on workstations and some clusters).

| | Apptainer | Charliecloud | enroot + pyxis | Podman rootless |
|---|---|---|---|---|
| Image | SIF (squashfs-based, signable) | dir/squashfs/tar | squashfs (import from OCI) | OCI layers |
| Build on cluster | `apptainer build` (fakeroot), def files | `ch-image build` (Dockerfile) | `enroot import` + modify; usually build elsewhere | `podman build` |
| Privilege | setuid helper or userns | userns only | userns/setuid-less | userns |
| GPU | `--nv`, `--rocm`, CDI | bind/hooks | hooks (libnvidia-container) | CDI/nvidia-container-toolkit |
| Slurm integration | `srun apptainer ...` (scripts) | `srun ch-run ...` | pyxis (native options) | scripts |
| MPI | host-MPI hybrid/bind | host MPI | PMIx hooks | host network |
| Ecosystem | Widest in academic HPC; OCI compat | Smaller | Strong in NVIDIA clusters (NGC) | Dev workflows |

Interoperability: all can consume OCI/Docker images; build once with a standard tool and deploy to whichever runtime a cluster uses, but test each, because the runtimes differ in environment handling, home mounting and PID/network namespace choices.

## 4. Reproducibility discipline

Reproducibility has levels: *rerun* the same image (immutability), *rebuild* the same image (determinism of the build), *reuse* the environment on another system (portability), and *understand* it (provenance and metadata).

1. **Pin the base by digest** (`From: image@sha256:...`) not by tag; tags are mutable (`latest`, even `24.04` moves with patch updates). Record the digest in the lab notebook, job log and image labels.
2. **Pin every dependency** with a lock file that includes hashes: `pip install --require-hashes -r requirements.lock`, `conda-lock`, `uv.lock`; pin system packages (`apt-get install pkg=version`) or, more practically, pin the **repository snapshot** (a dated mirror such as snapshot.debian.org or an internal Artifactory/Nexus mirror) so rebuilds see the same packages.
3. **No floating network fetches** in `%post`: verify checksums (`sha256sum -c`) or GPG signatures; avoid `curl | sh`; clone Git repositories at a tag **and** verify the commit hash.
4. **Do not upgrade the system in the build** (`apt-get upgrade`) because the result depends on the build date.
5. **Record metadata**: `%labels` (version, git commit of the recipe, build date, base digest, maintainer), keep the definition file and lock files in Git next to code, and embed or attach a software bill of materials (SBOM, via `syft` or similar) and record vulnerability scan output.
6. **Build in CI**, not on someone's laptop; build in a clean environment; tag images with the recipe's commit; store in a registry (OCI registry with Apptainer `oras` support, or a shared directory of SIFs on the parallel file system with checksums).
7. **Test at build time** (`%test`) and before promotion: import the framework, run a tiny GPU kernel, run a short NCCL test, compare numerics to a reference.
8. **Sign and verify** images used for production runs (`apptainer sign/verify`, or cosign for OCI images; 5.22).
9. **Separate base from application**: a slow-moving base image (CUDA + framework) and a fast-moving application layer; rebuild the application layer often.
10. **Record the runtime environment at run time**: image digest, host driver, kernel, GPU model, and environment variables in the job log (a few lines in your job prologue).
11. **Floating-point and hardware caveats**: bitwise reproducibility across GPU architectures and library versions is not guaranteed (6.5 on fast-math and reductions, 6.12 on NCCL algorithms); fix seeds and use deterministic modes when you need identical results, accept statistical equivalence otherwise.
12. **Retention**: keep images for the life of the publication or project; the registry's garbage collection must not delete referenced digests.

### A linter (tested)

`code/part06/container_lint.py` checks an Apptainer definition file or Dockerfile for the violations above: floating base tags (`:latest`, missing tag, tag without digest), `upgrade` steps, unpinned `apt`/`pip` installs, `curl | sh`, downloads without checksum, `git clone` without a pinned ref, missing labels and tests. On a deliberately poor file:

```text
ERROR line 2: base image 'ubuntu:latest' is not pinned (use a version tag, better a digest @sha256:...)
warn  line 5: system upgrade/update step makes the image depend on the build date
warn  line 6: system upgrade/update step makes the image depend on the build date
warn  line 7: apt install without version pins (acceptable if the base image and repo snapshot are pinned)
ERROR line 8: pipes a download into a shell: unverifiable and non-reproducible
warn  line 8: download without a following checksum/signature check
warn  line 9: download without a following checksum/signature check
warn  line 11: git clone without pinning a tag/commit
warn  line 12: pip install without version pins (use a lock file with hashes)
info  line 12: pip install without --no-cache-dir inflates the image
info  no %labels section ...
info  no %test section ...
```

and a good file (digest-pinned base, lock-file pip install with `--no-cache-dir`, checksum-verified download, labels and a test) produced "no findings". The first version of the linter had two bugs that the test files exposed: it missed `apt-get -y upgrade` (flags before the verb) and it flagged `... | sha256sum -c -` as "pipes into a shell" because the pattern `| sh` matched the start of `sha256sum`. Both were fixed with word-boundary and optional-flag patterns, a reminder to test linters on both good and bad inputs. It is a heuristic text check: it does not parse multi-line continuations or build stages.

## 5. Distribution and operations

- **Where images live**: a registry (Harbor, Artifactory, GHCR, NGC private registry) for OCI images; a controlled directory of SIFs on the parallel file system (`/shared/containers/<name>/<version>.sif` with `sha256` file) for Apptainer. Squashfs is one file: ideal for Lustre/GPFS (6.18) and for staging to node-local NVMe.
- **Start-up at scale**: thousands of ranks pulling or mounting the same image: stage to local disk or rely on page-cache sharing; do not pull from a registry in the job; avoid per-rank unpacking.
- **Bind policy**: default binds home, `/tmp`, `/proc`, `/sys`, `/dev` (Apptainer defaults; verify) can leak host state into containers and break reproducibility (`~/.local` Python packages silently override container packages: use `--no-home`, `--cleanenv`, `--containall` where needed, or set `PYTHONNOUSERSITE=1`). Prefer explicit, minimal binds for datasets and outputs.
- **Environment leakage**: Apptainer passes the host environment by default; `--cleanenv` (`-e`) starts clean. Combine with Slurm's `--export` choices (6.11).
- **Quotas and cleanup**: image caches and build directories grow; automate cleanup in prolog/epilog or cron.
- **Support matrix**: publish which base images, CUDA versions, MPI/PMIx versions, and runtimes are supported on which partitions (6.6), and a test job users can run to verify an image.
- **Kubernetes parity**: the same OCI image should run under Kubernetes (Part 11) and Slurm (enroot, Apptainer); keep the image runtime-agnostic and put runtime-specific settings in launch scripts.

## 6. Lab

Tested: 1) run `container_lint.py` on a Dockerfile and a def file of yours; fix every ERROR and warn; add one new check (for example an `ADD http://` instruction in a Dockerfile) with a test. 2) Create the `bad.def`/`good.def` pair from section 4 and reproduce the output.

Untested (Linux with Apptainer): 3) `apptainer pull docker://...`, `build` a def file with `%test`, run with `--nv` on a GPU node; trigger and diagnose a libc mismatch with an old base image. 4) Run an MPI hello with the hybrid model under `srun --mpi=pmix`. 5) Measure start-up latency of a 5 GB SIF on Lustre vs node-local NVMe with 64 ranks. 6) Sign and verify an image; try to run a modified copy. 7) Rebuild the same def file twice a week apart with and without digest and lock-file pinning; compare `pip freeze` and image checksums. 8) Convert one workflow between Apptainer and enroot/pyxis and list differences in environment and mounts. 9) Generate an SBOM and scan the image.

## 7. Interview angles

- How is an HPC container runtime different from Docker?
- Explain `--nv` and the libc mismatch problem.
- Hybrid vs bind MPI model: trade-offs?
- How do you make a container build reproducible?
- Why pin by digest and what does a tag guarantee?
- How would you let researchers build images on a shared cluster safely?
- Compare Apptainer and enroot/pyxis for an NVIDIA GPU cluster.
- What gets leaked from the host into a container by default and how do you control it?
- A job works in the container on cluster A and fails on cluster B: what do you check?

## 8. Checkpoint questions (25)

1. What three kernel features make a container?
2. Why do HPC clusters avoid the Docker daemon?
3. What is a SIF?
4. What is the header of a def file; which keyword comes first?
5. List five def-file sections.
6. What does `%test` do?
7. What does `--fakeroot` provide?
8. What does `--nv` bind in?
9. Describe the libc mismatch failure.
10. What is CDI?
11. Describe the hybrid and bind MPI models.
12. Where is the Apptainer cache and how do you move it?
13. How do you sign and verify an image?
14. What distinguishes Charliecloud?
15. Compare image formats of Apptainer, Charliecloud, enroot.
16. What are the four levels of reproducibility?
17. Why pin by digest?
18. How do you make `pip` installs reproducible?
19. Why avoid `curl | sh`?
20. What metadata should an image carry?
21. What can leak from the host (home, env) and how to stop it?
22. How do you distribute images to thousands of nodes?
23. What does the linter flag, and what bugs did the test reveal?
24. What are the limits of bitwise reproducibility on GPUs?
25. How do you keep one image usable under both Slurm and Kubernetes?

## 9. Sources and review notes

- Container fundamentals, Singularity/Apptainer, Charliecloud, Pyxis + Enroot, caching: *Supercomputers for Linux SysAdmins* chapter 16 ("Containers"), restated in my words.
- Apptainer definition files, GPU support (`--nv`, CDI, libc warning), MPI hybrid/bind models, build-environment cache variable: Apptainer user documentation (apptainer-userdocs commit `69efb83`).
- enroot/pyxis: see 6.13 (sources there).
- Original and run: `container_lint.py` and the good/bad definition files above.
- Unverified: Apptainer security-model specifics (setuid vs userns, `apptainer.conf` limits), default bind list, Charliecloud details, Podman rootless claims, SBOM tool names. No container was built or run.
