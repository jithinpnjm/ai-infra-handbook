---
id: "c01-07"
title: "1.7 Packages, repositories and software installation"
sidebar_label: "1.7 Packages, repositories and software installation"
sidebar_position: 7
description: "Packages, repositories and software installation"
status: "drafted"
tier: "0"
level: "B"
lab_venue: "GCP / GKE"
---

# 1.7 Packages, repositories and software installation

| | |
|---|---|
| Level | Basics |
| Priority tier | 0 |
| Lab venue | GCP / GKE (one Ubuntu VM and, optionally, one Rocky/Alma VM) |
| Part | Part 1: Linux, from the command line to the kernel and performance |
| Status | Drafted, labs **untested** |

## Why this matters for AI infrastructure

Almost everything you will operate arrives on a node as software somebody else built: the NVIDIA driver, the CUDA toolkit, the container runtime, `nvidia-container-toolkit`, the Slurm daemons, the InfiniBand stack (OFED or the distribution's inbox drivers), monitoring agents. Three kinds of incident in GPU fleets come from getting this layer wrong:

1. **Version drift.** One node is auto-upgraded and ends up with a kernel that the installed driver does not support, so the GPUs vanish after the next reboot. Another node has a different CUDA minor version, and a job that worked on the first fails on the second.
2. **Unknown provenance.** A library copied into `/usr/local/lib` years ago shadows the one the package manager installed, and nobody can say where it came from.
3. **Broken dependency resolution.** An engineer forces an install with `--nodeps` or `--force` to get past an error, and the node's package database no longer describes what is on disk.

This chapter gives you the vocabulary and the mechanics to avoid all three. It covers what a package is, how the two package families (deb and rpm) work, how repositories and signatures protect you, how to inspect and verify what is installed, how to hold versions, how software is built from source when no package exists (and how to do that without damaging the system), how shared libraries are found at run time (the cause of many "works on my machine" bugs), and how a whole cluster node is assembled in practice. It also introduces `make`, because you will constantly read other people's build instructions, Dockerfiles and driver installers that call it.

## Prerequisites and outcomes

You should be comfortable with the shell (1.2), the directory layout (1.3) and users and `sudo` (1.6).

After this chapter you can:

- Explain what a package contains, what metadata it carries, and why dependency metadata makes installation tractable.
- Install, remove, query, verify and hold packages with `apt`/`dpkg` on Debian-family systems and `dnf`/`rpm` on Red Hat-family systems, and translate between the two.
- Add a third-party repository safely, and say how signature checking works and why `--nogpgcheck` is a smell.
- Find which package owns a file, and which package would provide a missing file or header.
- Build and install software from source with `./configure`, `make` and `make install` into a private prefix, read the build log, and turn the result into a real package.
- Diagnose "cannot open shared object file" and "undefined reference" errors with `ldd`, `ldconfig`, `rpath` and `LD_LIBRARY_PATH`, and explain why `LD_LIBRARY_PATH` should not be exported globally.
- Read a simple `Makefile` and apply a source patch.
- Describe the order of operations for building a small HPC cluster node, including NFS, OFED, kickstart, cloning pitfalls and diskless booting.

## 1. What a package is

A **package** is one file (usually a compressed archive) that holds a tree of files belonging to one piece of software, plus **metadata** describing it. A web server, a single encryption module, a documentation set: each is a package. The files are what gets copied to disk; the metadata is what lets a tool reason about them.

The most useful metadata fields are:

| Metadata | What it enables |
|---|---|
| Name, version, architecture, description | Searching, comparing versions, refusing to install an x86-64 package on arm64 |
| **Dependencies** | The tool can compute and install everything else that is needed |
| **File checksums** | Later verification that nothing has been altered |
| **Marked configuration files** | Upgrades do not overwrite your edits |
| Maintainer scripts (pre/post install and remove) | Creating a system user, enabling a service, rebuilding a cache |
| Signature | Proof that the package came from the repository owner |

The set of fields differs between package systems, and so do their capabilities. The common families are:

| Family | Package file | Used by | Low-level tool | High-level manager |
|---|---|---|---|---|
| **deb** | `.deb` | Debian, Ubuntu, Mint | `dpkg` | `apt`, `apt-get`, `aptitude` |
| **rpm** | `.rpm` | Red Hat Enterprise Linux and clones (Rocky, Alma, CentOS Stream), Fedora, SUSE | `rpm` | `dnf` (older: `yum`), `zypper` on SUSE |
| Source-oriented ports | build recipes | Arch (pacman, with a ports-like build system), Gentoo (ebuild), Slackware | | |

For AI infrastructure you will meet deb on Ubuntu (the default for most GPU cloud images and NVIDIA's DGX OS) and rpm on RHEL-family systems (common in HPC and enterprise). Know both.

### Two layers, and why they exist

Every package system splits into two layers, and keeping them apart in your head resolves most confusion:

- The **low-level tool** (`dpkg`, `rpm`) works on **one package file**. It unpacks files, runs maintainer scripts and records the result in a local database. It does **not** fetch anything and, with a few exceptions, it does not solve dependencies: if a dependency is missing it complains.
- The **high-level manager** (`apt`, `dnf`) talks to **repositories**, works out the full set of packages that must be installed, removed or upgraded, downloads them, and then calls the low-level tool to do the unpacking.

```mermaid
flowchart LR
  subgraph Internet_or_Local["Repositories"]
    R1["Distribution repo\n(base, updates, security)"]
    R2["Third-party repo\n(EPEL, NVIDIA, Docker, vendor)"]
    R3["Local mirror\n(air-gapped cluster)"]
  end
  HM["High-level manager\napt / dnf\nresolve dependencies, download,\nverify signatures"]
  LL["Low-level tool\ndpkg / rpm\nunpack files, run scripts"]
  DB[("Local package database\n/var/lib/dpkg or /var/lib/rpm")]
  FS["Files on disk\n/usr /etc /lib ..."]
  R1 --> HM
  R2 --> HM
  R3 --> HM
  HM -->|"package files"| LL
  LL --> FS
  LL --> DB
  DB -.->|"queries: owns? version? verify?"| HM
```

### The package database is precious

The low-level tool records every installed package, its files and its checksums in a local database. If that database is damaged, the system no longer knows what is installed and repairing it is difficult. One concrete cause is installing or removing packages on a **filesystem that is 100% full**, because the tool can fail halfway while writing its own records. So before a big install on a node, check `df -h /` and `df -i /` (chapter 1.3 explains inodes); a full `/var` is just as bad as a full `/`.

Two related habits:

- Never use the "force" switches (`--force`, `--nodeps`, `dpkg --force-all`) as a way to get unblocked. They produce a system whose database disagrees with the disk.
- Do not mix installation methods for the same software. If the distribution already ships `foo`, installing a second `foo` into `/usr/local` or via a tarball creates two copies and the one that runs depends on `$PATH` order (chapter 1.2).

### Configuration files and upgrades

Packages mark certain files as **configuration**. When you upgrade, the manager must not discard your edits and also must not ignore the packager's improvements. The conventions are:

- On **rpm**, if you changed a config file and the new package also changed it, your file is kept and the new default is written next to it with the suffix `.rpmnew` (or, if the packager decided the old file must be replaced, your version is saved as `.rpmsave`).
- On **deb**, `dpkg` asks you interactively whether to keep your version or take the package's, and offers to show the difference. In scripts and automation you set an option so the choice is made without a prompt (for example `-o Dpkg::Options::="--force-confold"`, which keeps your files).
- When you **remove** a package, its configuration files normally stay behind so a later reinstall finds your settings. To remove them too, use `apt purge` (deb) or remove the leftover files (rpm, where the files are usually already gone but `.rpmsave` files may linger).

After any large upgrade, search for the leftovers and compare them:

```bash
sudo find /etc -name '*.rpmnew' -o -name '*.rpmsave' -o -name '*.dpkg-dist' -o -name '*.dpkg-old'
```

### Dependencies, and how the two families express them

A dependency says "package A needs package B (possibly at a given version) to work". The managers read these and compute the full closure, which is what turns "install this driver" into a list of forty packages.

The deb format has a richer vocabulary than rpm. A deb package can say a dependency is **required** (`Depends`), **strongly recommended** (`Recommends`, installed by default by `apt`), **merely suggested** (`Suggests`, typically documentation or examples), or **in conflict** (`Conflicts`, `Breaks`). A smart interactive manager can choose the set of optional packages that fits what you want. On the rpm side, installing one package has historically sometimes pulled in a dozen more that are not strictly needed, because there are fewer gradations; modern `dnf` has `--setopt=install_weak_deps=False` to skip "weak" dependencies, which is useful for small compute node images.

A dependency can also name a **capability** instead of a package: "any package that provides an `smtp-server`", or "a library providing `libcuda.so.1`". This is why you can ask the manager which package provides a file you are missing (section 5).

### Integrity: checksums

Because the package system stores a checksum for every file, you can later ask "has anything the package installed been changed?" This is a cheap integrity check, useful after a suspected compromise, after a disk problem, and when a node behaves differently from its siblings:

```bash
# rpm: verify one package, or everything
rpm -V openssh-server
rpm -Va                      # all packages; output lines show what differs

# deb: debsums is a separate package; dpkg has a built-in verifier too
sudo apt install debsums
sudo debsums -s              # show only files that fail
dpkg --verify openssh-server
```

An `rpm -V` line looks like `S.5....T.  c /etc/ssh/sshd_config`, where each letter flags what differs (S size, 5 digest, T modification time, and so on) and the trailing `c` marks a config file. Differences in config files are normal; differences in `/usr/bin` or `/usr/lib` binaries deserve an explanation. Only files that belong to packages are checked: a file that was dropped in by hand is invisible to this method.

## 2. Repositories: where packages come from

A **repository** is an indexed directory of packages, served over HTTP(S), from local disk, or from an optical medium. The index lets the manager find a package and its dependencies without downloading them. When you install an operating system, a repository (the installation medium, or a network mirror) is configured for you. After installation the main network repositories are added, normally including separate channels for the base release, bug-fix updates and security updates.

Beyond the distribution's own repositories there are three more kinds you will configure:

- **Third-party repositories.** The standard Red Hat repositories, for example, omit many packages, so people enable **EPEL** (Extra Packages for Enterprise Linux), a trusted community repository for the RHEL family. NVIDIA, Docker, Kubernetes and others publish their own repositories for their own software.
- **Vendor mini-repositories.** Some projects, like the InfiniBand OFED distribution, publish their own small repositories just for their software.
- **Local mirrors and internal repositories.** For machines without Internet access (typical for HPC clusters on a private network) or for reproducibility, you copy the packages you need to a server on your network and point nodes at it. That also lets you freeze a known-good set of versions and roll the whole fleet forward on your schedule.

### Signatures and trust

A repository signs its metadata (and, for rpm, usually each package). The manager checks the signature against a key you have **explicitly trusted**. This is the mechanism that stops someone who can intercept your download from substituting a malicious package. Consequences:

- **Adding a repository is a trust decision**, because its packages run as root during installation (maintainer scripts) and then run on your node. Only add repositories from the real owner, over HTTPS, and verify the key fingerprint against the vendor's documentation.
- Switches that disable the check (`dnf --nogpgcheck`, `gpgcheck=0` in a repo file, apt's `--allow-unauthenticated` or `[trusted=yes]`) are for emergencies and for your own internal test repositories; do not leave them in configuration.

### Debian-family configuration

- **Sources**: `/etc/apt/sources.list` and files in `/etc/apt/sources.list.d/`. Older entries are one line each (`deb [signed-by=/etc/apt/keyrings/vendor.gpg] https://repo.example.com/apt stable main`). Newer Ubuntu and Debian releases are moving to a multi-line "deb822" format in files ending `.sources`; both formats work, but check which your release uses. *(Review note: confirm the default format on the release you run.)*
- **Keys**: the modern practice is a key file in `/etc/apt/keyrings/` (or `/usr/share/keyrings/`) referenced from the entry with `signed-by=`, so each repository's key is trusted for that repository only. The old global keyring managed by `apt-key` is deprecated; guides that tell you to run `apt-key add` are out of date.
- **Update the index** before installing: `sudo apt update` downloads the package lists (it does not install anything). Forgetting this, or running it on a node whose repository has moved, is the usual reason for "Unable to locate package" or "404 Not Found".

### Red Hat-family configuration

- **Repository definitions**: files ending `.repo` in `/etc/yum.repos.d/`. Each section has a `baseurl` or `mirrorlist`/`metalink`, `enabled=1`, `gpgcheck=1` and a `gpgkey=` URL.
- **Keys**: imported once with `sudo rpm --import <key-url-or-file>` or fetched automatically when you first install from a repository that provides `gpgkey=` (you are asked to accept it).
- **Temporary control** without editing files: `--enablerepo=NAME`, `--disablerepo=NAME` and `--disablerepo='*' --enablerepo=NAME` on the command line.
- Newer RHEL-family releases split content into **BaseOS** and **AppStream** repositories and add *modules* (streams of software versions such as multiple Python or Node.js versions). Modules and streams are an extra layer you only need to know exist; check your distribution's current documentation.

### Verbs you need on both sides

| Task | Debian family | Red Hat family |
|---|---|---|
| Refresh repository metadata | `sudo apt update` | `sudo dnf makecache` (done automatically on most commands) |
| Install | `sudo apt install pkg1 pkg2` | `sudo dnf install pkg1 pkg2` |
| Install a local package file with dependencies | `sudo apt install ./pkg.deb` | `sudo dnf install ./pkg.rpm` |
| Remove | `sudo apt remove pkg` | `sudo dnf remove pkg` |
| Remove and delete config files | `sudo apt purge pkg` | (config files marked as such are saved as `.rpmsave`) |
| Remove packages nobody needs any more | `sudo apt autoremove` | `sudo dnf autoremove` |
| Upgrade installed packages | `sudo apt upgrade` (never removes packages); `sudo apt full-upgrade` (may install/remove to resolve) | `sudo dnf upgrade` |
| Check what has updates | `apt list --upgradable` | `dnf check-update` |
| Reinstall | `sudo apt install --reinstall pkg` | `sudo dnf reinstall pkg` |
| Download without installing | `apt download pkg` or `apt-get install --download-only pkg` | `dnf download pkg` or `--downloadonly` (with `--downloaddir=DIR`) |
| Search by name or description | `apt search word` | `dnf search word` |
| Show details and dependencies | `apt show pkg` ; `apt depends pkg` | `dnf info pkg` ; `dnf repoquery --requires pkg` |
| Which repository / version would be used | `apt policy pkg` | `dnf list --showduplicates pkg` |
| Package groups | `tasksel`, meta-packages | `sudo dnf group install "Development Tools"` |
| Transaction history and undo | `/var/log/apt/history.log` | `dnf history`, `dnf history undo N` |

A few details that surprise people:

- `yum` is the older name; on current RHEL-family releases `yum` is a compatibility alias for `dnf`. The option tables you find in older books and on forums still work.
- `apt` is the friendly front end with progress bars and sensible defaults for humans; **`apt-get`** and `apt-cache` have stable output and behaviour and are what you should use in scripts, Dockerfiles and automation. (`apt` warns you that its interface is not stable for scripting.)
- Add `-y` (assume yes) in automation, and `DEBIAN_FRONTEND=noninteractive` so debconf does not stop to ask questions.
- `--skip-broken` (dnf/yum) installs what it can and skips what has dependency problems. Use it only when you are certain you understand what is being skipped.

## 3. The low-level tools

You use `dpkg` and `rpm` directly for three jobs: installing a single package file, interrogating the database, and verifying.

### `rpm`: modes and selectors

`rpm` has **modes** (what to do) and **selectors** (which packages):

| Mode | Meaning | Selector | Meaning |
|---|---|---|---|
| `-q` | Query | `-a` | All installed packages |
| `-i` | Install | `-f /path` | The package that owns this file or directory |
| `-U` | Upgrade (or install if absent) | `-p file.rpm` | A package **file** (not yet installed) |
| `-e` | Erase | | |
| `-V` | Verify | | |

Combined, they answer nearly every question:

```bash
rpm -qa | grep -i cuda          # which CUDA-related packages are installed
rpm -qi openssh-server          # description, version, vendor, build date
rpm -ql openssh-server          # every file the package installed
rpm -qc openssh-server          # only its configuration files
rpm -qf /usr/bin/ssh            # who owns this file?
rpm -qpl downloaded.rpm         # contents of a package file before installing it
rpm -qR somepackage             # its dependencies (what it requires)
rpm -q --whatprovides libcuda.so.1   # which installed package provides this
```

Use `rpm -i` and `-U` only for a package file whose dependencies are already satisfied. Switches such as `--nodeps` (skip dependency check) and `--force` (overwrite files owned by another package, or install an older version) exist for repair work. Treat them as dangerous tools.

### `dpkg`: the equivalents

```bash
dpkg -l | grep -i cuda          # installed packages (name, version, status)
dpkg -s openssh-server          # status and metadata of one installed package
dpkg -L openssh-server          # files installed by it
dpkg -S /usr/bin/ssh            # which package owns this file?
dpkg -c pkg.deb                 # contents of a package file
dpkg -I pkg.deb                 # metadata of a package file
sudo dpkg -i pkg.deb            # install (does not fetch dependencies)
sudo apt -f install             # then let apt fix up missing dependencies
```

In `dpkg -l` output the first two columns are a state code. `ii` means installed and correctly configured; `rc` means removed but configuration remains; `iU` or `iF` mean half-installed or failed configuration (usually fixed with `sudo dpkg --configure -a`).

### Translation table

| Question | rpm | dpkg |
|---|---|---|
| Is it installed, which version? | `rpm -q pkg` | `dpkg -s pkg` or `dpkg -l pkg` |
| List installed packages | `rpm -qa` | `dpkg -l` |
| Files in an installed package | `rpm -ql pkg` | `dpkg -L pkg` |
| Which package owns this file? | `rpm -qf path` | `dpkg -S path` |
| Contents of a package file | `rpm -qpl f.rpm` | `dpkg -c f.deb` |
| Verify installed files | `rpm -V pkg` | `dpkg --verify pkg` / `debsums` |
| Which package could provide a file I do not have? | `dnf provides '*/name.h'` | `apt-file search name.h` (after `sudo apt install apt-file && sudo apt-file update`) |

## 4. Holding, pinning and reproducibility

On GPU nodes the point of package management is not "always newest". It is "exactly the versions we validated". Tools for that:

- **Hold a package** so routine upgrades skip it: `sudo apt-mark hold nvidia-driver-XXX linux-image-generic` (and `unhold`); on RHEL-family, the `dnf versionlock` plugin (`sudo dnf install python3-dnf-plugin-versionlock`, then `sudo dnf versionlock add pkg`). *(Review note: package names for the plugin differ by release.)*
- **Install an exact version**: `sudo apt install pkg=1.2.3-1` ; `sudo dnf install pkg-1.2.3-1.el9`. Use `apt policy pkg` or `dnf list --showduplicates pkg` to see what versions your repositories offer.
- **Apt pinning** (`/etc/apt/preferences.d/`) assigns priorities to repositories or versions, so a third-party repository cannot silently replace a base package. It is powerful and easy to get wrong; reach for `apt-mark hold` first.
- **Freeze the whole repository.** The strongest approach for a fleet is to mirror the repositories you depend on at a point in time (or use a snapshot service) and have nodes install only from that snapshot. Two nodes built a month apart then get identical packages.
- **Unattended upgrades** (`unattended-upgrades` on Ubuntu, `dnf-automatic` on RHEL-family) are valuable for security patches on servers, but on a GPU node they can replace the kernel without rebuilding the driver. Restrict them to security updates for packages outside the driver/kernel set, or disable them on compute nodes and patch via a controlled process.

The failure this prevents is concrete and common:

```mermaid
sequenceDiagram
  participant Admin as Routine upgrade (cron or unattended)
  participant Pkg as apt / dnf
  participant Kern as Kernel package
  participant DKMS as DKMS (driver module)
  participant Node as GPU node
  Admin->>Pkg: apt upgrade
  Pkg->>Kern: install new kernel 6.x
  Pkg->>DKMS: rebuild nvidia module for 6.x
  alt build succeeds (headers present, driver supports kernel)
    DKMS-->>Node: module ready
    Note over Node: next reboot: GPUs fine
  else build fails (no headers / driver too old for kernel)
    DKMS-->>Node: no module for 6.x
    Note over Node: next reboot boots 6.x: nvidia-smi says no driver
  end
```

Chapter 1.22 develops DKMS and kernel modules. The package-layer fix is: hold kernel and driver packages together, upgrade them in a controlled step, and test a rebooted canary node before rolling out.

## 5. Finding the package you need

Three questions come up daily.

**"Which package does this file belong to?"** Use `rpm -qf`, `dpkg -S`.

**"I need a file I do not have (a header, a library, a command). Which package provides it?"** On deb: `apt-file search pkg.h`. On rpm: `dnf provides '*/pkg.h'` (the older spelling `yum provides` works). The usual cases:

- A compiler error `fatal error: foo.h: No such file or directory` means the **development package** for the library is missing. Libraries are packaged in two flavours: the runtime package (`libfoo1` on Debian, `foo` on Red Hat) with the shared library, and the development package (`libfoo-dev`, `foo-devel`) with the headers and `.pc` files. The same distinction explains why `openssl.pc` is absent until you install `libssl-dev`/`openssl-devel`.
- A runtime error `error while loading shared libraries: libfoo.so.1: cannot open shared object file` means the runtime package is missing, or the library is installed in a location the dynamic linker does not search (section 8).

**"What would this install do?"** Simulate first: `apt install -s pkg` (or `apt-get -s`), `dnf install --assumeno pkg`, and read the list of packages that will be removed. A line that says an unrelated meta-package such as `ubuntu-desktop` or a driver will be **removed** is a reason to stop.

## 6. Installing from source

Packages exist because most open-source software is distributed as **source code**: Unix and Linux come in so many flavours and architectures that distributing binaries for every combination is impractical. Source distribution also lets users fix bugs and add features, which is the point of open source. Nearly everything on a Linux system, from the kernel to the libraries, can be obtained as source.

You should not replace your distribution's packages with source builds wholesale. Distributions fix security problems quickly, keep dependencies consistent, and let you upgrade with one command. But there are good reasons to build from source yourself:

- **Control of options**, for example building an MPI library with exactly the network backends your cluster has, or a Slurm with specific plugins.
- **Control of the version**, when the distribution's is too old or too new (particularly for add-ons such as language libraries).
- **Install location**, including keeping several versions of the same software side by side.
- **Understanding** how the software works and what it depends on.

The costs are real: it takes time; custom installs **do not update themselves** (a security issue for anything network-facing); you may overwrite files the distribution owns; and a typo in an option can leave a half-working build. So the rule is: *prefer the package; build from source into an isolated prefix when you need control; turn the result into a package if you will deploy it to more than one machine*.

### The standard sequence

Most C and C++ projects built with the GNU autotools follow four steps, and the pattern transfers to other build systems (CMake, Meson, SCons):

```mermaid
flowchart LR
  A["1. Unpack\ntar xf pkg-1.23.tar.xz"] --> B["2. Configure\n./configure --prefix=..."]
  B --> C["3. Build\nmake"]
  C --> D["4. Test\nmake check"]
  D --> E["5. Dry run\nmake -n install"]
  E --> F["6. Install\nmake install\n(or package it)"]
  B -.->|"fails?"| L["read config.log:\nmissing -dev package,\nwrong CPPFLAGS/LDFLAGS"]
  C -.->|"fails?"| M["find the first real error,\nnot the make[N] cascade"]
```

**Unpack carefully.** Source archives come as `.tar.gz`, `.tar.bz2` or `.tar.xz` (chapter 1.3 covered `tar`). *Before* extracting, list the contents with `tar tvf` or `tar ztvf`, for two reasons:

- A well-formed archive has everything under one top directory (`package-1.23/...`). Some archives instead spill files directly into the current directory; if the listing shows bare names such as `Makefile` and `main.c`, extract into a new, empty directory so you do not make a mess.
- Never unpack an archive that contains **absolute paths** such as `/etc/passwd` or `/etc/inetd.conf`. That is almost certainly a booby trap, and extracting as root would overwrite system files. Delete such an archive. (Modern `tar` strips leading slashes by default, but do not rely on that.)

**Read the documentation in the tree first.** Open `README`, then `INSTALL` if there is one, before doing anything else; they often state special options, prerequisites and supported platforms. Then get a feel for the files by their role:

- Build-system files: `Makefile`, `Makefile.in`, `configure`, `CMakeLists.txt`, `meson.build`. Very old packages ship a plain `Makefile` you edit by hand; most use a configuration script or file that generates the `Makefile` for your system.
- Source files: `.c`, `.h` for C; `.cc`, `.cxx`, `.C` for C++.
- Object files (`.o`) or binaries should not be in a source archive. If you find them, run `make clean` so you get a fresh compile.

**Configure.** GNU autoconf-based packages ship a `configure` script and template files ending in `.in` (`Makefile.in`, `config.h.in`). Running `./configure` probes your system (which compiler, which headers and libraries exist, which functions are available) and substitutes the results into the templates to produce the real `Makefile` and a `config.h` header. It also writes `config.cache` and a detailed log, `config.log`. The output is long and tells you what is being checked; a successful configure does not guarantee a successful build, but the odds are good.

You need the build tools installed first. On Debian and Ubuntu the quick way is `sudo apt install build-essential`; on RHEL-family, `sudo dnf group install "Development Tools"`. If some tool is absent, search for `gcc` or "C compiler".

### Safe first install: a private prefix

The key option is `--prefix`. By default an autoconf package installs under `/usr/local` (programs in `/usr/local/bin`, libraries in `/usr/local/lib`, and so on). To experiment safely, install into a directory you own:

```bash
mkdir -p ~/src && cd ~/src
tar xf coreutils-9.5.tar.xz            # example archive; the version will differ
cd coreutils-9.5
./configure --prefix=$HOME/mycoreutils
make -j"$(nproc)"                      # -j builds in parallel
make check                             # runs the package's tests (can take a while)
make -n install                        # DRY RUN: print what install would do
make install
$HOME/mycoreutils/bin/ls --version
```

Everything lands under `~/mycoreutils`, independent of the rest of the system, so you can delete that directory and nothing else is affected. Always do the dry run (`make -n install`) and read it: the `install` target of a `Makefile` can copy files anywhere the author thought appropriate, and the dry run shows you the commands without executing them. If anything is installed outside your prefix, stop.

**Other useful `configure` options:**

| Option | Meaning |
|---|---|
| `--prefix=DIR` | Root of the installation tree |
| `--bindir=DIR`, `--sbindir=DIR`, `--libdir=DIR` | Override where executables, system executables and libraries go |
| `--disable-shared` | Do not build shared libraries (can avoid run-time library hassles for obscure libraries) |
| `--with-pkg=DIR` | Tell the build where a dependency lives, when it is in a nonstandard place. Not every script supports this and the exact spelling varies. |
| `--help` | Lists all options (long; search it) |

**Separate build directory.** If you want to try several option sets, or build for several configurations from one source tree, create a new empty directory anywhere and run the `configure` script by its path from there (`mkdir build && cd build && ../pkg-1.23/configure ...`). The source tree is not modified; the build directory gets generated files and links back. Many maintainers prefer this ("out-of-tree" build).

**Environment variables.** `configure` reads `CPPFLAGS` (preprocessor options, such as `-I` include paths and `-D` macro definitions), `CFLAGS` (compiler options), `LDFLAGS` (linker options such as `-L` paths) and `CC`. Set them in front of the command or as arguments:

```bash
CPPFLAGS=-DDEBUG ./configure
./configure CPPFLAGS="-I$HOME/opt/zlib/include" LDFLAGS="-L$HOME/opt/zlib/lib -Wl,-rpath=$HOME/opt/zlib/lib"
```

Use `CPPFLAGS`, not `CFLAGS`, for include directories, because `configure` often runs the preprocessor on its own. Be exact: a missing dash (`CPPFLAGS=Iinclude`) makes the compiler treat the argument as a file name and `configure` aborts with "C compiler cannot create executables".

**Reading `config.log`.** When `configure` fails and the cause is not obvious, the answer is in `config.log`, which is huge because it also dumps the whole environment at the end. The efficient technique: open it in `less`, press `G` to jump to the end, and search **backward** (`?`) for a phrase from the failing message (for example `for more details`, or the name of the check that failed). The error is usually a few lines above the match, showing the exact compiler command that failed and its error message.

**Targets in an autoconf `Makefile`.** Besides `all` (default) and `install`: `clean` (remove built objects), `distclean` (remove everything generated, including `Makefile` and `config.h`, returning the tree to its freshly unpacked state), `check` (run tests) and `install-strip` (install with debug symbols stripped, saving space).

### `pkg-config`: how builds find libraries

When libraries are scattered across prefixes, a build must be told where each one's headers and libraries are and which link flags it needs. Most libraries solve this with a small text file ending `.pc`, read by the `pkg-config` program:

```bash
pkg-config --cflags --libs zlib      # prints e.g. "-lz" (flags vary by system)
pkg-config --modversion openssl      # installed version
pkg-config --list-all | less         # everything it knows
```

A `.pc` file contains variables (`prefix`, `libdir`, `includedir`), the name, version, dependencies (`Requires`), and the flags to compile and link (`Cflags`, `Libs`). By default `pkg-config` looks only in the `lib/pkgconfig` directory of its **own** installation prefix (and `share/pkgconfig`). Files elsewhere (say `/opt/openssl/lib/pkgconfig/openssl.pc`) are invisible unless you either symlink them into the central directory, or set **`PKG_CONFIG_PATH`** to include the extra directory. The environment-variable approach works per build and badly system-wide. You will not see `.pc` files for most libraries until you install their development packages.

### Turning a source build into a package

Installing with plain `make install` leaves files with no record in any package database, so you cannot cleanly remove, upgrade or inventory them. If you are going to install the build on more than one machine, make a real package:

- On Debian family, **`checkinstall`** wraps `make install`, tracks the files it installs, and produces a `.deb` you install and remove with `dpkg`:
  ```bash
  sudo checkinstall make install
  ```
- On RPM family, create a build tree with `rpmdev-setuptree` (from `rpmdevtools`) and write a `.spec` file that describes the build; then `rpmbuild -ba name.spec` produces the package. This is more work; follow a tutorial for your release, and consider `mock` (clean-chroot builds) for repeatable results.
- On a build server, use **`DESTDIR`**: `make install DESTDIR=/tmp/stage` installs into a staging directory without touching the live system, and you pack that directory (with `tar`, `fpm` or your packaging tool). This is the foundation of every packaging workflow.

If you do install by hand into `/usr/local`, remember that operating system upgrades leave `/usr/local` alone. That is convenient, but it also means lots of unrecorded files accumulate and nobody remembers their origin. When it becomes unmanageable, package them.

For large numbers of nodes, an even better answer is to put software in a **shared, versioned location** (a network filesystem mount with per-version directories) selected by *environment modules* (section 10), or to bake it into a container image (chapter 7).

### Applying a patch

A **patch** (or diff) is a text file, produced by `diff -u`, that describes changes to source files. Developers also distribute fixes as patches. The header of each file section looks like:

```text
--- src/file.c.orig   2015-07-17 14:29:12 +0100
+++ src/file.c        2015-09-18 10:22:17 +0100
@@ -2,16 +2,12 @@
```

Search the patch for lines starting with `---` to see which files it changes, and read the paths. The **working directory matters**: the path `src/file.c` means you must run `patch` from the directory that *contains* `src`, not from `src` itself.

```bash
patch -p0 < fix.patch        # paths are used as written
patch -p1 < fix.patch        # strip one leading path component (typical for patches made from git)
patch -p1 --dry-run < fix.patch   # test without changing anything
```

If a path in the patch begins with a directory such as `package-3.42/src/file.c` and your directory is named differently, `-p1` removes the first component so the rest matches. If `patch` asks "File to patch:", you are probably in the wrong directory or the source does not match the version the patch was made against; stop rather than guess, because a partly applied patch leaves source that will not build. With git you can also use `git apply --check` and `git apply`.

### Where to go next with builds

Once the autotools routine is comfortable, three directions are worth knowing about: other build systems (**CMake**, **Meson**, **SCons**, and language-specific ones such as `cargo` or `go build`), each with its own configure-then-build-then-install shape; the **Linux kernel build**, which has its own configuration system (`make menuconfig`, `make modules_install`) and which you should only attempt while keeping the previous kernel bootable as a fallback (chapters 1.14 and 1.22); and **distribution source packages**, which carry the distribution's own patches and build recipes and let you rebuild or patch a packaged program the supported way (`debuild`/`dpkg-buildpackage` on Debian family, `rpmbuild` and `mock` on RPM family). Rebuilding a distribution source package, rather than compiling a tarball by hand, usually gives you a proper package at the end.

### Troubleshooting builds

First learn to read `make` output:

- `make: *** [target] Error 1` is a real failure. A line with `Error 1 (ignored)` is a failure the author expected and tolerates; ignore it.
- GNU `make` calls itself recursively, and each level is labelled `make[N]`. When something fails deep inside, you see a cascade: the compiler error, then `make[3]: *** [file.o] Error 1`, then `make[2]`, `make[1]` and finally `make`. **The first error is the one that matters**; the cascade is only the unwinding. Scroll up to the first compiler message and the directory it names (`Leaving directory ...` tells you where).

Common failures and what they mean:

| Message | Meaning and fix |
|---|---|
| `conflicting types for 'item'` / `previous declaration` | The source declares something twice; remove or guard the offending line (comment, `#ifdef`). Often a sign you are building on a system the package does not support. |
| `'time_t' undeclared` (or any unknown type or function) | A header is missing from the source. Look up the function's manual page (`man 2 time` / `man 3 time`): its `SYNOPSIS` shows the header to `#include`. |
| `pkg.h: No such file or directory` | Development package missing, or the header is in a nonstandard place: add `-I` to `CPPFLAGS` (and probably a matching `-L` to `LDFLAGS`). Find the package with `apt-file search pkg.h` or `dnf provides '*/pkg.h'`. If nothing looks missing, you may be building for an OS the source does not support: read the `README`. |
| `undefined reference to 'initscr'` (linker) | A library was not linked, or one of your own object files was left off the link line. Search for the function name to find which library (here, curses) and add `-lcurses` (and `-L` if it is in a nonstandard place). |
| `make: prog: Command not found` | Build tool missing (`cc`, `gcc`, `ld`: install the toolchain). If you are sure it is installed, a badly written `Makefile` may assume `.` is in your `$PATH`; use `./prog` in the `Makefile`, or temporarily put `.` on your path. |
| `Makefile:7: *** missing separator. Stop.` | A recipe line starts with spaces instead of a **tab**. |

## 7. The build toolchain: compiler, linker, headers and `make`

You do not need to write C to operate a cluster, but you will constantly read build logs, fix `Makefile` variables and chase library errors, so you need the model of how a program is built.

### From source to executable

```mermaid
flowchart LR
  S1["main.c"] -->|"preprocessor (cpp)\nexpands #include, #define, #ifdef"| P1["expanded source"]
  P1 -->|"compiler (cc -c)"| O1["main.o\nobject file"]
  S2["aux.c"] --> O2["aux.o"]
  O1 --> L["linker (ld)\nresolves symbols"]
  O2 --> L
  LIB1["static library\nlibfoo.a\n(code copied in)"] --> L
  LIB2["shared library\nlibbar.so\n(only a reference is recorded)"] -.-> L
  L --> EXE["executable\nmyprog (ELF)"]
  EXE -->|"at run time:\nld.so finds libbar.so"| RUN["running process"]
  LIB2 -.-> RUN
```

The vocabulary:

- **Source code** is the human-written text (`.c`, `.cc`). A compiler translates it into **object files** (`.o`), binary code with loose ends: references to functions defined elsewhere and no information the operating system needs to start it.
- The **linker** (`ld`) combines object files and libraries into an **executable** and resolves each reference. People rarely run `ld` directly: the compiler driver (`cc`, `gcc`, `g++`, `clang`) calls it for you. `cc` is the traditional name for the system's C compiler; on Linux it is usually GNU `gcc`, and `clang` (from the LLVM project) is the common alternative.
- A **library** is a bundle of compiled components (essentially object files plus header files that declare them). There is a standard C library (`libc`) that is always linked in unless you say otherwise, a math library, and thousands of others.

A minimal two-file example to see the steps (my own, small enough to retype):

```bash
mkdir -p ~/lab/build && cd ~/lab/build
cat > greet.h <<'EOF'
void greet(const char *who);
EOF
cat > greet.c <<'EOF'
#include <stdio.h>
#include "greet.h"
void greet(const char *who) { printf("hello, %s\n", who); }
EOF
cat > main.c <<'EOF'
#include "greet.h"
int main(void) { greet("cluster"); return 0; }
EOF

cc -c greet.c            # produces greet.o
cc -c main.c             # produces main.o
cc -o hello main.o greet.o   # links them into 'hello'
./hello
```

If you omit `-o`, the compiler writes an executable called `a.out`; always name your output. To see the intermediate stages: `cc -E main.c` (preprocessor only), `cc -S main.c` (assembly), `file main.o hello` (object vs executable).

### Linking against libraries

Libraries matter at **link time**. If a program calls a function and you do not link the library that defines it, the linker stops with:

```text
badobject.o: undefined reference to 'initscr'
```

The important part is the function name. A web search for it (or `man initscr`) tells you which library provides it (here, curses). Note that "undefined reference" does **not** always mean a missing library: one of your own object files may be missing from the link command; it is usually easy to tell, because you will recognise your own functions.

To link, name the library with **`-l`** (the filename minus the `lib` prefix and the suffix) and, if it is not in a default directory, tell the linker where with **`-L`**:

```bash
cc -o badobject badobject.o -lcurses                       # in a default directory
cc -o badobject badobject.o -lcurses -L/usr/junk/lib -lcrud   # extra library in a custom directory
```

The default library directories are `/lib`, `/usr/lib` and, on modern multiarch distributions, architecture-specific subdirectories such as `/usr/lib/x86_64-linux-gnu`. To find which library defines a function: `nm --defined-only libcurses.a | grep initscr` (static) or `nm -D --defined-only /usr/lib/.../libncurses.so.6 | grep initscr` (shared).

### Static and shared libraries

| | Static library (`libfoo.a`) | Shared library (`libfoo.so.N`) |
|---|---|---|
| At link time | Needed code is **copied** into the executable | Executable records only the library's **name** |
| At run time | The library file is not needed; the executable behaves identically forever | The dynamic loader `ld.so` finds and maps the library; many processes **share** the same copy in memory |
| Updating the library | Requires **relinking every executable** | Fix the library once; programs pick it up (usually without recompiling) |
| Cost | Larger binaries, more disk and RAM; a security fix means finding and rebuilding every user | Management complexity: the right version must be found at run time |

Shared libraries are why a library security update from your package manager protects every program that uses it, and why the update tool sometimes asks you to reboot or restart services (so running processes drop the old library). They are also the source of the most common run-time failures, which section 8 covers.

### Headers, the preprocessor and include paths

**Header files** (`.h`) contain declarations (types and function signatures) for libraries. The compiler never looks for them itself: a separate program, the **C preprocessor** (`cpp`, or `cc -E`), runs first and rewrites the source. Preprocessor commands, **directives**, begin with `#`, and there are three kinds:

- `#include <stdio.h>` inserts a file. Angle brackets mean "search the system include directories"; double quotes (`#include "greet.h"`) mean "look next to this source file first". If you hit a problem with a double-quoted include, you probably have incomplete source.
- `#define NAME value` defines a **macro**: every occurrence of `NAME` is replaced by `value`. You can also define one without touching source: `cc -DNAME=value`.
- `#ifdef MACRO` / `#if cond` ... `#endif` includes or skips a block depending on a macro. This is how one code base supports different platforms or a debug mode.

The preprocessor knows nothing about C syntax; it only manipulates text. Many a confusing build error comes from a macro substituting something unexpected.

The default system include directory is `/usr/include` (plus architecture-specific subdirectories). If a header lives elsewhere, add `-I/path/to/include` to the compile command:

```text
badinclude.c:1:22: fatal error: notfound.h: No such file or directory
```

```bash
cc -c -I/usr/junk/include badinclude.c
```

When the compiler cannot find a header, look for it with `locate`, `find`, or the package tools from section 5; there can be several with the same name in different places, so confirm you are using the right one.

### `make`

Compiling a handful of files by hand does not scale, so Unix has **`make`**, which reads a file named `Makefile` (or `makefile`) and rebuilds only what is out of date. The model has three ideas:

- A **target** is something to produce: a file (`main.o`, `myprog`) or a label (`all`, `clean`).
- A target has **dependencies**: other targets that must exist, and be at least as new, first.
- A **rule** is the recipe, the shell commands that build the target from its dependencies.

Using the example files above:

```make
# Makefile  (the indented lines MUST start with a TAB character, not spaces)
OBJS = main.o greet.o

all: hello

hello: $(OBJS)
	$(CC) -o hello $(OBJS)

clean:
	rm -f $(OBJS) hello
```

Points to notice:

- `OBJS = ...` defines a **macro** (variable), used as `$(OBJS)`. `CC` is predefined (default `cc`).
- The **first target** in the file (`all` here) is the default when you run `make` with no arguments.
- You wrote no rule for `main.o` or `greet.o`; `make` has **built-in rules** that know how to get a `.o` from a `.c` using `$(CC) -c` and the standard flag variables.
- The recipe lines start with a tab. Spaces cause `*** missing separator. Stop.`

`make` brings targets up to date and does the minimum: run it twice and the second says `make: 'hello' is up to date` (or `Nothing to be done`). Run `touch greet.c` and `make` again: it recompiles only `greet.o` and relinks `hello`, because `greet.o` became older than its source and `hello` older than `greet.o`. That chain reaction, driven purely by file timestamps, is the whole idea.

**Commands you will use daily:**

```bash
make                     # build the default target
make hello               # build one target
make -n                  # print what would run, run nothing (dry run)
make -f other.mk         # use a different file
make -j8                 # run up to 8 jobs in parallel (builds go much faster)
make CC=clang            # override a macro from the command line
make CFLAGS="-O2 -g"    # likewise
```

You do not even need a `Makefile` for tiny programs: `make blah` with a `blah.c` in the directory uses built-in rules to compile it. This is a handy trick with unfamiliar languages (Fortran, lex, yacc), because `make` may figure out the right commands, and even its failure message hints at the tool you need.

**Standard macros** (set in the `Makefile`, an environment variable, or the command line):

| Macro | Meaning |
|---|---|
| `CC` | C compiler (default `cc`) |
| `CFLAGS` | Compiler options (optimisation, warnings, `-g`) |
| `CPPFLAGS` | Preprocessor options (`-I`, `-D`) |
| `CXXFLAGS` | Flags for the C++ compiler (GNU `make`) |
| `LDFLAGS` | Linker options (`-L`, `-Wl,-rpath=...`) |
| `LDLIBS` | Libraries to link (`-lm`, `-lcurses`), when you want to keep them separate from search paths |

**Automatic variables** inside a rule: `$@` is the current target, `$<` the first dependency, `$*` the stem of the target name (for `blah.o`, `blah`). A pattern like `.c.o:` in older Makefiles defines how to produce a `.o` from a `.c`.

**Conventional targets** found in nearly every project:

| Target | Purpose |
|---|---|
| `all` | Build everything (usually the first target) |
| `clean` | Remove object files and executables |
| `distclean` | Remove everything not in the original distribution, including generated Makefiles |
| `install` | Copy built files to their destination. **Dangerous**; always `make -n install` first |
| `test` / `check` | Run the test suite |
| `depend` | Regenerate header dependencies (an older practice) |

**Organisation tips.** Real Makefiles group `-I` and `-L` flags by package in macros at the top, group object files per executable, and keep one rule per executable. Combining two executables into one rule is a trap: each executable would depend on both sources and `make` would rebuild both whenever either changes. If you need a special rule for an object file, put it just above the executable rule that uses it.

GNU `make` has many extensions that other implementations (BSD, Solaris) lack; this is fine on Linux and is the reason portable projects layer autotools or CMake on top. For more depth, read the GNU `make` manual (`info make`).

**Lex and Yacc**, briefly: you may see `flex` (a lexer: tokenises text) and `bison -y` (a parser generator) in builds of programs that read configuration languages. They may require link flags such as `-lfl` and `-ly`. You rarely need more.

## 8. Shared libraries at run time

A dynamically linked executable knows only the **names** of the libraries it needs. A small program, the **dynamic linker/loader** (`ld.so`, shown as `ld-linux-x86-64.so.2` on x86-64), runs first when you start the program, finds those libraries and maps them into the process.

List what a program needs with `ldd`:

```bash
ldd /bin/bash
#   linux-vdso.so.1 (0x00007ffd...)
#   libtinfo.so.6 => /lib/x86_64-linux-gnu/libtinfo.so.6 (0x00007f...)
#   libc.so.6 => /lib/x86_64-linux-gnu/libc.so.6 (0x00007f...)
#   /lib64/ld-linux-x86-64.so.2 (0x00007f...)
```

The name on the left of `=>` is what the executable asked for; the path on the right is where `ld.so` found it. A line reading `libfoo.so.1 => not found` is your problem. (On untrusted binaries, do not run `ldd`; some implementations execute the program. Use `readelf -d prog | grep NEEDED` instead.)

### The search order

`ld.so` looks in this order (details in `ld.so(8)`):

1. The executable's embedded **`RPATH`/`RUNPATH`**, if the program was linked with one.
2. The **`LD_LIBRARY_PATH`** environment variable, if set. (For the classic `RPATH` the order is `RPATH`, then `LD_LIBRARY_PATH`; for `RUNPATH` it is `LD_LIBRARY_PATH` first. Check `ld.so(8)` for your system.)
3. The **cache** `/etc/ld.so.cache`, a fast index of libraries found in the directories listed in `/etc/ld.so.conf` (which usually includes files from `/etc/ld.so.conf.d/`).
4. The **default directories** `/lib` and `/usr/lib` (and their architecture variants), which are implicit.

The cache is rebuilt by **`sudo ldconfig`** (add `-v` for details). Whenever you add a library to a directory in the cache's path, or change `ld.so.conf`, run `ldconfig`, or the loader will not know. Useful: `ldconfig -p | grep libcuda` lists what the cache knows.

### Do not add directories carelessly to `/etc/ld.so.conf`

It is tempting to put every unusual library directory in `ld.so.conf`. Resist: you should know what is in the system cache, and a cache stuffed with odd directories causes conflicts and a disorganised system. The better ways to find a library in a nonstandard place are:

**Link with an `rpath`** (build time). Say `libweird.so.1` lives in `/opt/obscure/lib`:

```bash
cc -o myprog myprog.o -Wl,-rpath=/opt/obscure/lib -L/opt/obscure/lib -lweird
```

`-Wl,-rpath=...` passes `-rpath` to the linker and embeds the directory into the executable. You still need `-L` for the link step. To change the `rpath` of a binary you cannot rebuild, use **`patchelf`** (`patchelf --set-rpath /opt/obscure/lib myprog`), but compile-time is better. Inspect with `readelf -d myprog | grep -E 'RPATH|RUNPATH'`. A relative form, `-Wl,-rpath='$ORIGIN/../lib'`, makes a relocatable tree whose libraries sit beside the program; this is how many vendors ship software that works wherever it is unpacked.

### The danger of `LD_LIBRARY_PATH`

`LD_LIBRARY_PATH` is a colon-separated list of directories searched **before** the normal places. It is the number-one cause of shared-library trouble, because it is a cheap way to make a program run when you do not have the source and cannot use `patchelf`. You get what you pay for:

- **Performance.** The loader may scan each listed directory for every library of every program started with the variable set.
- **Wrong libraries.** If you export it in your shell startup files, every program you run, including system tools, searches those directories first and can pick up an incompatible library. This produces baffling crashes and "symbol lookup error" messages far from the real cause.
- **Invisible state.** Two users with different values see different behaviour from the same binary.

So: **never set `LD_LIBRARY_PATH` in global shell startup files, and never compile software with it set.** If you must use it for one program, use a **wrapper script** that sets it only for that command:

```bash
#!/bin/sh
LD_LIBRARY_PATH=/opt/crummy/lib
export LD_LIBRARY_PATH
exec /opt/crummy/bin/crummy.bin "$@"
```

(The `exec` replaces the shell with the program; `"$@"` passes your arguments through preserving spaces. Quote it; the unquoted form from older scripts breaks on arguments with spaces.) Cluster **environment modules** (section 10) do something similar, on purpose and per job, which is the acceptable form of the same idea.

A second problem appears with developers: a library's API changes slightly between minor versions and breaks installed software. The preventive solutions are to install each library version consistently under its own prefix and link with `rpath`, or to link obscure libraries statically.

### Quick diagnosis

```bash
ldd ./prog | grep 'not found'          # which names are unresolved
ldconfig -p | grep libname             # does the cache know it?
find / -name 'libname.so*' 2>/dev/null # where is it, if anywhere?
readelf -d ./prog | grep -E 'NEEDED|RPATH|RUNPATH'
LD_DEBUG=libs ./prog 2>&1 | head -50   # trace the loader's search (debugging only)
strace -e trace=openat ./prog 2>&1 | grep -E 'ENOENT|\.so'   # chapter 1.11
```

Chapter 1.11 returns to ELF, the loader and `strace` in depth.

## 9. Interpreters, shebang lines and scripting languages

A script is a text file run by an interpreter. If the file is executable and its first line begins with `#!` (the **shebang**), the kernel runs the program named after it and feeds it the file:

```bash
#!/usr/bin/env python3
print("hello")
```

- `#!/usr/bin/python3` hard-codes a path. `#!/usr/bin/env python3` finds the first `python3` on your `$PATH`, which is better when interpreters live in different places or in virtual environments, at the cost of depending on `$PATH`.
- The most common failure: `bash: ./myscript: /usr/bin/tail: bad interpreter: No such file or directory`. The path after `#!` does not exist on this system (for example the program is in `/bin`, not `/usr/bin`). Another common one is a script saved on Windows with CRLF line endings, so the interpreter name ends with an invisible `\r`; fix with `dos2unix` or `sed -i 's/\r$//'`.
- Do not rely on more than one argument on the shebang line; different systems treat the rest of the line as one argument. Keep it to the interpreter plus at most one option.

Languages you will meet: **Python** (everywhere in ML and ops; the interpreter is `python3`), **Perl** (older admin and text-processing tools), **Ruby**, **PHP**, **JavaScript** via `node`, **R**, and **MATLAB/Octave** in some HPC groups. Treat the system Python as part of the operating system: many distribution tools depend on it, so do not `pip install` into it as root. Use a virtual environment (`python3 -m venv .venv`, then `.venv/bin/pip install ...`), or a project manager such as `uv`, or a container (chapter 7), so you do not break the OS or collide with a neighbouring project.

A shared principle links packages, libraries and interpreters: **every language has its own packaging ecosystem** (`pip`, `conda`, `npm`, `cargo`, `go install`) in addition to the distribution's, and mixing them without isolation is how nodes become unreproducible. For GPU Python stacks, which depend on CUDA-matched wheels or conda packages, isolation (a venv, a conda environment or a container image) is not optional.

## 10. Software installation on a cluster

A cluster is a different problem from one machine: the same software must be present, identical and quickly reachable on hundreds of nodes. This section follows the practical order in which a small cluster is built, which also explains what each service is for.

### Drivers, InfiniBand and RAID

- **Network drivers** for most Ethernet cards ship in the Linux kernel. Some vendors' cards need a separate driver; check the list of supported operating systems and the warranty terms before choosing one. Also check how the *switch* is managed: some management interfaces require a browser plug-in or Java applet that does not work on every OS version, which is a reason to prefer devices with a command-line or web interface that needs nothing special.
- **InfiniBand** has an in-kernel stack ("inbox" drivers), but for HPC performance and complete tooling the usual practice is the vendor's package set: the **OFED** (OpenFabrics Enterprise Distribution) package, or the NVIDIA-supplied equivalent (MLNX_OFED/DOCA-OFED; confirm current names in the vendor documentation). It contains the drivers for most cards, the user-space libraries (`libibverbs` and friends), subnet-management and diagnostic tools (`ibstat`, `ibv_devinfo`, the `perftest` suite), IP-over-InfiniBand support, and sometimes bundled MPI builds. Rules of thumb:
  - OFED is **strict about kernel and C library versions**. Prefer the vendor's prebuilt packages for your exact OS release, or run the installer, which compiles packages for the running system.
  - **Back up the existing packages first.** The installer removes previously installed OFED packages before it builds; if the build fails you are left without InfiniBand.
  - Some packages in the build output are mutually exclusive, so not all get installed. If your hardware vendor supplies its own stack for its equipment, try that first.
  - MPI libraries bundled with OFED are built with preset options; for tuned production use, build your own with exactly the options you need.
  - Remember `/etc/security/limits.conf` (or a file in `limits.d`): InfiniBand needs unlimited locked memory, e.g. `* soft memlock unlimited` and `* hard memlock unlimited` (chapter 1.8 explains limits, and under systemd the service-level equivalent is `LimitMEMLOCK=infinity`).
  - If the network is used through **IPoIB** (IP over InfiniBand), a scheduler that generates the Ethernet node names will start jobs that talk over Ethernet, not InfiniBand. You then need a way to map node names to their IB addresses, for example separate hostnames such as `node01-ib`.
- **RAID.** Hardware RAID protects against disk failure, not against a failed controller or motherboard or multiple disks lost in a power event. Keep backups regardless. Where you can choose, mirroring is the safest; adding striping (RAID 0) for speed is better done in the Linux software layer (chapter 1.13), where it costs little CPU and often recovers more gracefully.

### A sensible build order

Building a cluster in an order that lets you test early prevents cloning mistakes into fifty nodes. A small cluster is typically built like this:

1. Install the **control (management) server**.
2. Set up the **network file system** if you use one.
3. Install **one compute node**.
4. Install the **communication software** (OFED).
5. Install the **second compute node**, forming a *mini-cluster* of one control and two compute nodes.
6. Install **compilers and test packages**.
7. **Test** the communication hardware (bandwidth and latency against the manufacturer's numbers).
8. Install the **job scheduler** (Slurm, chapter 6.7).
9. Test **job completion** end to end.
10. Only then **clone** the compute node (or build a network-boot image) and add the rest of the nodes.

The principle: reach maximum readiness and test it fully *before* you replicate, so you do not clone a defect hundreds of times. Check network bandwidth and node performance against what the vendors claim. A mini-cluster will not reveal everything (response time as request rate grows, reliability of network services under load), but it finds most issues early. And when the cluster is ready to run jobs there is strong pressure to open it to users at once; resist until **monitoring and backups are in place**, otherwise there will be almost no time to build them later.

### The login node

The login node is where users connect and where compute nodes send certain requests. It needs two network interfaces, **external** and **internal**; internal services must not be reachable from outside, so configure a **firewall** on the external interface. On small clusters it often doubles as the management node, but a separate management node is safer: you keep control when users do something destructive on the login node. If the cluster has a high-speed fabric, connect the management node to it too, which simplifies network management and statistics. If this node stores user data and exports it to the compute nodes, its disk subsystem must be fast and large; for big clusters use a dedicated file server or a distributed filesystem.

### NFS server and client

Exporting a directory over NFS, on the server (package and service names differ between distributions):

1. Install the NFS server package and enable the service: `sudo systemctl enable --now nfs-server`.
2. If the internal interface has a firewall, open the RPC/NFS services there.
3. List the exports in `/etc/exports`, each with the directory, the clients allowed to mount it and the options, for example `/export  10.0.0.0/24(rw,sync,no_subtree_check)`.
4. Re-read the configuration with `sudo exportfs -ra` (and `exportfs -v` to display it).

On each client, add one line to `/etc/fstab`:

```text
myserver:/export  /export  nfs  defaults  0  0
```

The six fields are: the source (server and exported directory), the mount point, the filesystem type, the mount options, the `dump` flag (0 means not included in backups) and the `fsck` pass number (0 means not checked at boot). Chapters 1.12 and 5 and the parallel-file-system chapters in Part 6 cover options such as `hard`, `vers=`, `nconnect` and tuning.

### Compilers and libraries on nodes

Compilers are usually installed once, on the network filesystem, so compute nodes see them and the libraries the compiled programs need. Make the libraries visible to the dynamic linker in one of two ways: set `LD_LIBRARY_PATH` **per job through environment modules**, or list the directories in `ld.so.conf` and run `ldconfig`. In the second case, remember to update the file and rerun `ldconfig` on **every node** whenever the compiler version (and thus the library path) changes.

**Environment modules** (Environment Modules or Lmod) are the standard answer: `module load gcc/13 openmpi/5` edits `PATH`, `LD_LIBRARY_PATH`, `MANPATH` and similar variables for the current shell or job only, and `module purge` undoes it. Several versions of the same software can coexist on the shared filesystem and users pick one. This is also the clean answer to the earlier rule about not exporting `LD_LIBRARY_PATH` globally. Chapter 6.20 covers modules in depth.

### The compute node

A compute node exists to run user work. Design points:

- **Disk.** It can run diskless, but this increases load on a network that is already busy and consumes RAM. Network filesystems can bottleneck on programs that create many temporary files, even parallel filesystems. Keep a **local `/tmp`** as scratch space and encourage users to use it (container runtimes such as `enroot` also unpack images there by default).
- **Layout** if the OS is local: a 50 to 100 GB partition for the system; a small **swap** (it is only a small reserve for RAM; a job that needs lots of swap spends its time waiting for pages); and **all the remaining space for `/tmp`**. With two disks, put swap on each and combine the `/tmp` partitions as software RAID-1 if you want resilience, or stripe them if you want speed and can afford to lose scratch.
- **Network.** Provide fast fabric (InfiniBand or RoCE) for inter-process traffic and Ethernet for control. Heavy NFS traffic often justifies a **separate network for storage**.
- **Fewer services.** Disable everything the node does not need: mail server, print server, desktop services, and cron-scheduled jobs that update the manual page index or the `locate` database. Every daemon steals CPU time and adds jitter to synchronous parallel jobs.
- **Compilers** are not needed at run time but are needed when building the communications stack, so either do a full install on the node or reach the compilers through NFS.
- Finally install the **scheduler's client** (for Slurm, `slurmd` and munge, chapter 6.7).

### Getting an operating system onto many nodes

| Method | How | Notes |
|---|---|---|
| **Manual install** from media or virtual media over IPMI/BMC | Good for the first (reference) node | Remember to remove the installation media from the repository list afterwards |
| **Automated network install** (PXE + kickstart/preseed/autoinstall) | An answer file describes disk layout, network, package list | Scales to hundreds; the answer file can be edited and reused |
| **Cloning** a disk image | Copy a prepared node to others | Needs preparation, see below |
| **Diskless/network-root** (NFS-root or an image loaded into RAM) | Nodes boot from the network; one image to maintain | Reduces drift; costs RAM for RAM-based images |
| **Image-based provisioning** (BCM, xCAT, Warewulf, MAAS and similar) | A tool manages images, node identity and updates | The modern default for clusters (chapter 6.x and the BCM part) |

**Kickstart** (Red Hat family) works like this. An interactive install writes `/root/anaconda-ks.cfg`, a record of every choice you made (partitioning, network, package list). Edit that file, place it on a USB stick named `ks.cfg`, or serve it over the network, and any number of nodes can install unattended. For network installs the DHCP server points installing nodes to the file, for example in an ISC DHCP configuration:

```text
filename "/opt/ks.cfg";
next-server server.cluster.myorg;
```

If the returned filename ends in `/`, the client mounts that directory over NFS and looks for a file named `<IP-address>-kickstart`, so a node with address `10.0.0.2` reads `10.0.0.2-kickstart`; this lets different nodes get different installations. With no file or directory given, the client tries `/kickstart` on the NFS server. (Debian and Ubuntu have their equivalents: preseed and Ubuntu autoinstall/cloud-init.) *(Review note: the exact DHCP and installer parameters differ by release and by DHCP software; confirm against current documentation.)*

**Cloning pitfalls.** If you copy a disk image with `dd if=/dev/sda of=/dev/sdb`, or with a tool such as Clonezilla, the clone may not boot unless you prepared the prototype first:

- Many systems record disks by **factory identifiers** in the bootloader and mount configuration, for example `root=/dev/disk/by-id/ata-WDC_...-part1`. On a different disk that name is wrong. Replace such entries in `/boot/grub/grub.cfg` (generated, so change the source settings and regenerate) and in `/etc/fstab` with something portable such as `UUID=` for per-filesystem identity set at clone time, or with plain device names, before taking the image.
- If the OS **binds network interface names to MAC addresses** (historically in `/etc/udev/rules.d/70-persistent-net.rules` or similar), clones will have the wrong names or no network. Correct or remove the binding. Also remove host-specific state such as SSH host keys and `/etc/machine-id` (regenerated at first boot) or you will have many machines with the same identity.
- Watch the first boot of the clone carefully.

**NFS-root** is safer and faster in this respect: build a minimal image, export it read-write to install and configure packages, set up DHCP, TFTP, PXE boot and an initial ramdisk (chapter 1.14), boot the node, install software, and then switch the export to **read-only**. Do not put the node's name in configuration files in the image (it must come from DHCP). Update software later by `chroot` into the image on the NFS server. During the first install, set up passwordless SSH for root, which rescues you when the home-directory partition is not mounted.

**Final acceptance test** before you add the remaining nodes:

1. Passwordless remote commands work for the superuser.
2. A regular user exists and has passwordless remote commands.
3. The user's environment is set up for each installed MPI.
4. A test program from the communications package is submitted as a script.
5. It starts, runs and writes its result into the working directory.

If that whole chain works, connect the rest.

## 11. AI-infrastructure patterns

**The GPU stack is a chain of version constraints.** Kernel, driver, CUDA toolkit, user-space libraries (cuDNN, NCCL), container runtime and framework must match. A package manager is the tool that expresses and enforces these constraints, and holds them steady:

| Layer | Typical package source | Pin how |
|---|---|---|
| Kernel and headers | Distribution | `apt-mark hold` / `versionlock` the kernel and headers, upgrade in a controlled step |
| NVIDIA driver (kernel module) | Distribution or NVIDIA repository; DKMS or precompiled modules | Choose one install method and keep it (mixing the `.run` installer with packages is a classic mess) |
| CUDA toolkit | NVIDIA repository (installed through the `cuda-keyring` package on Debian family); can be several versions side by side under `/usr/local/cuda-X.Y` | Install a specific versioned meta-package, not the unversioned one |
| `nvidia-container-toolkit` | NVIDIA repository | Pin with the driver; restart the container runtime after changes |
| Python and ML libraries | `pip`/`conda` inside a venv or container | Lock files; image digest |
| Cluster software (Slurm, OFED) | Distribution, vendor or your own build | Mirror or build once, package, deploy the same artefact everywhere |

*(Review note: repository URLs, key-installation commands, and package names for NVIDIA software change over time; always use the instructions in NVIDIA's current installation guide rather than copying commands from an old page.)*

**Be wary of installers that bypass the package manager.** A vendor `.run` file that copies files into `/usr` produces exactly the unrecorded state this chapter warns about. If you must use one, record what you did in your node build automation, and prefer the packaged route.

**Reproduce nodes from automation, not memory.** The goal is that any node can be rebuilt from a script (Ansible, chapter 4.x; cloud-init; BCM image) plus a pinned package set. Terraform builds machines; configuration management installs and configures packages on them; the package manager is the engine underneath. Ansible's `apt`, `dnf`, `package`, `yum_repository` and `apt_key`/`deb822_repository` modules express everything in sections 2 to 4 as idempotent tasks.

**Containers move the problem, they do not remove it.** Inside a container image you still run `apt-get install` or `dnf install`, so the same rules apply: pin versions, install only what you need (`--no-install-recommends`), clean the package cache in the same layer (`rm -rf /var/lib/apt/lists/*`), and build from a base image whose digest you control. The NVIDIA driver, however, is **not** inside the image; the host's driver plus `nvidia-container-toolkit` provide it (chapter 7).

**Supply chain.** Anyone who can publish into a repository you trust can run code as root on your nodes. Mirror from the real source, verify signatures, restrict who can add repositories to nodes, and record which packages are installed (`dpkg -l`, `rpm -qa`) in your build logs so you can answer "which nodes ran the vulnerable version?" quickly.

## How it fails

1. **`apt update` errors: "404 Not Found", "NO_PUBKEY", "The repository ... does not have a Release file".** The repository moved, the release reached end of life, or the signing key is missing or rotated. Check the URL in the sources file, the `signed-by` key and the release codename; for end-of-life Ubuntu or CentOS releases the repository is moved to an archive server.
2. **"E: Unable to locate package".** Forgot `apt update`; wrong release; the repository (for example `universe`) is not enabled.
3. **Dependency conflict or "held broken packages".** A third-party repository offers a newer library than the distribution's, or a package is held. Read the list of what would change; do not force.
4. **The driver disappears after a reboot.** An unattended kernel upgrade rebuilt nothing, or DKMS failed (no headers, driver too old for the kernel). Diagnose with `dkms status`, `journalctl -b -u nvidia-*`, `dmesg | grep -i nvidia`; prevention is section 4.
5. **dpkg interrupted: "dpkg was interrupted, you must manually run `dpkg --configure -a`".** An install was killed (full disk, lost SSH). Run it; if the disk is full, free space first. Using `tmux` for long upgrades prevents a dropped session from killing the install (chapter 1.5).
6. **`/var` or `/` is 100% full during an upgrade.** Can corrupt the package database. Check `df -h`, `df -i`; clean caches (`apt clean`, `dnf clean all`), and free space *before* retrying.
7. **A "fixed" dependency problem with `--nodeps` or `--force`.** The package database now lies. Later upgrades fail strangely or silently break the forced package. Remove, reinstall properly.
8. **"cannot open shared object file".** Library missing, not in the cache (run `ldconfig`), or not on the search path (use `rpath`, a module, or fix the install). Not `LD_LIBRARY_PATH` in `.bashrc`.
9. **Two versions of a library, the wrong one loads.** A source build into `/usr/local/lib` shadows the packaged one, or a stale `LD_LIBRARY_PATH` redirects everything. Use `ldd`, `ldconfig -p` and `LD_DEBUG=libs` to see which file is used; remove the stray copy.
10. **`./configure` fails on a missing library.** The runtime package is installed but the **development** package (`-dev`, `-devel`) is not. Install it and re-run; read `config.log` (backward search from the end) for the exact failing probe.
11. **The program builds, but `make install` scatters files over `/usr/local` and later nobody knows where they came from.** Use `--prefix` with a dedicated directory, or `checkinstall`/`DESTDIR` packaging.
12. **A `Makefile` fails with `missing separator`.** Spaces instead of tabs; your editor converted tabs to spaces.
13. **Cloned node boots but has no network, or two nodes share an identity.** Persistent MAC-to-name rules, the same `machine-id`, or the same SSH host keys; prepare the image before cloning.
14. **Upgrade overwrote or ignored an edited configuration file.** You answered the prompt incorrectly in an unattended run; find `.rpmnew`/`.dpkg-dist` files and merge by hand.

## Hands-on lab (a GCP Ubuntu VM, plus optionally a Rocky/Alma VM; untested)

Use a throwaway VM with `sudo`. These commands have **not** been run; run them on a disposable machine before relying on them.

**A. Inspect the package database (Ubuntu).**

```bash
dpkg -l | wc -l                         # how many packages are installed?
dpkg -S /usr/bin/ssh                    # which package owns ssh? (openssh-client)
dpkg -L openssh-client | head -20       # what did it install?
apt show openssh-client | head -30      # metadata and dependencies
apt depends openssh-client              # its dependency list
apt policy openssh-client               # which repository and version
sudo apt install -s tree                # simulate installing 'tree' (-s = simulate)
sudo apt install -y tree && tree -L 1 /etc | head
dpkg -S "$(which tree)"
sudo apt remove -y tree
sudo apt purge -y tree
```

Write down what changed between `remove` and `purge` (look in `/var/lib/dpkg/info` and `dpkg -l tree`: `rc` versus gone).

**B. Verify integrity.**

```bash
sudo apt install -y debsums
sudo debsums -s                       # should be quiet on a fresh VM
sudo cp /bin/ls /tmp/ls.bak
echo x | sudo tee -a /bin/ls >/dev/null     # corrupt a packaged binary (on a throwaway VM only)
sudo debsums coreutils | grep -v OK         # detects the change
sudo cp /tmp/ls.bak /bin/ls
```

**C. Holds.**

```bash
sudo apt-mark hold tree 2>/dev/null || sudo apt install -y tree && sudo apt-mark hold tree
apt-mark showhold
sudo apt-mark unhold tree
```

**D. Find which package provides a header.**

```bash
sudo apt install -y apt-file build-essential
sudo apt-file update
apt-file search zlib.h | head
echo '#include <zlib.h>
int main(void){return 0;}' > z.c
cc z.c -o z          # fails: header missing
sudo apt install -y zlib1g-dev
cc z.c -o z && echo built
pkg-config --cflags --libs zlib
```

**E. Build from source in a private prefix.**

```bash
mkdir -p ~/src && cd ~/src
# any small autotools project works; use a release tarball of GNU hello or similar
curl -LO https://ftp.gnu.org/gnu/hello/hello-2.12.1.tar.gz
tar tzf hello-2.12.1.tar.gz | head          # list BEFORE extracting; check for absolute paths
tar xzf hello-2.12.1.tar.gz && cd hello-2.12.1
less README INSTALL | head -5
./configure --prefix=$HOME/opt/hello-2.12.1
make -j"$(nproc)" && make check
make -n install | head -20
make install
$HOME/opt/hello-2.12.1/bin/hello
ldd $HOME/opt/hello-2.12.1/bin/hello
make distclean
```

Write down which `configure` option you would need to move the install to `/opt/tools/hello`, and what `DESTDIR` would let you do.

**F. Break and fix the linker, by hand.**

```bash
cd ~/lab/build           # the greet/main example from section 7
cc -o hello main.o       # undefined reference to 'greet'
cc -o hello main.o greet.o && ./hello
# make a shared library
cc -fPIC -shared -o libgreet.so greet.c
cc -o hello2 main.c -L. -lgreet
./hello2                 # fails: cannot open shared object file
ldd ./hello2 | grep greet
LD_LIBRARY_PATH=. ./hello2          # works, for this command only
cc -o hello3 main.c -L. -lgreet -Wl,-rpath='$ORIGIN'
./hello3                 # works with no environment variable
readelf -d hello3 | grep -E 'RPATH|RUNPATH'
```

**G. A Makefile.**

```bash
cat > Makefile <<'EOF'
OBJS = main.o greet.o
all: hello
hello: $(OBJS)
	$(CC) -o $@ $(OBJS)
clean:
	rm -f $(OBJS) hello
EOF
make && make          # second run: nothing to do
touch greet.c && make # only greet.o and hello rebuild
make -n clean
```

Break it on purpose: replace the tab before `$(CC)` with spaces and note the error.

**H. A patch.**

```bash
mkdir -p ~/lab/patch && cd ~/lab/patch
printf 'one\ntwo\nthree\n' > a.txt
cp a.txt b.txt && sed -i 's/two/TWO/' b.txt
diff -u a.txt b.txt > fix.patch
patch -p0 --dry-run < fix.patch     # (a.txt, as named in the patch)
patch -p0 < fix.patch && cat a.txt
```

**I. (Optional, Rocky/Alma) rpm and dnf.** Repeat A and B with `rpm -qa | wc -l`, `rpm -qf /usr/bin/ssh`, `rpm -ql openssh-clients | head`, `sudo dnf install -y tree`, `dnf history`, `rpm -V openssh-server`, `dnf provides '*/zlib.h'`.

## Checkpoint questions

1. What does a package contain besides files? Name four metadata items and what each enables.
2. What is the difference between `dpkg`/`rpm` and `apt`/`dnf`? Which one resolves dependencies and fetches from repositories?
3. Why is it dangerous to install or remove packages when the filesystem is 100% full?
4. Name the commands that tell you (a) which package owns `/usr/bin/ssh` on Ubuntu and on Rocky; (b) which package would provide the header `zlib.h`.
5. What is the difference between `apt remove` and `apt purge`? What are `.rpmnew` and `.rpmsave` files?
6. What does a repository signature protect against, and why is `--nogpgcheck` risky? What changed about key handling for apt in recent years?
7. A GPU node's `nvidia-smi` fails after an automatic update and reboot. Describe the likely sequence and two ways to prevent it.
8. Why use `apt-get` rather than `apt` in scripts? What does `DEBIAN_FRONTEND=noninteractive` do?
9. List the four to six steps of building an autotools package from source, and say which one you should always precede with a dry run, and how.
10. What does `./configure --prefix=$HOME/opt/x` do, and why is it a good practice for a first install?
11. Why do you list a source tarball with `tar tf` before extracting it? What would an archive with absolute paths indicate?
12. How do you diagnose a failing `./configure`? Where in `config.log` do you look?
13. What does `pkg-config` do, and how do you make it see a `.pc` file in `/opt/foo/lib/pkgconfig`?
14. Explain `-I`, `-L` and `-l`. Which stage uses each (preprocessor, compiler, linker)?
15. What is the difference between static and shared libraries? Give an advantage of each.
16. In what order does the dynamic linker search for a library? What does `ldconfig` do and when must you run it?
17. Why is exporting `LD_LIBRARY_PATH` in `.bashrc` considered harmful, and what do you do instead (two options)?
18. What is an `rpath`, how do you set one at link time, and how can you inspect it?
19. A recipe line in a Makefile fails with `*** missing separator`. What is wrong?
20. `make` run twice in a row prints "Nothing to be done" the second time. Explain how it knows, and what `touch aux.c` followed by `make` will do.
21. In a failed parallel build you see `make[3]: *** [file.o] Error 1`, then `make[2]`, `make[1]` errors. Which message do you act on?
22. Patch header paths start with `src/file.c`. From which directory do you run `patch -p0`, and what does `-p1` change?
23. List five reasons to build software from source, and five reasons not to.
24. Why is a source build installed with plain `make install` hard to maintain, and what are two ways to make it manageable?
25. Give the recommended build order for a small cluster and the reason for cloning only after a mini-cluster is tested.
26. What must you do to a prototype node before cloning its disk with `dd` or Clonezilla? Name three items.
27. In an OFED installation, which two precautions about existing packages and kernel versions apply, and which `limits.conf` entries does InfiniBand need?
28. What goes in `/etc/exports`, and which command makes the server re-read it? What do the six fields in an `/etc/fstab` NFS line mean?
29. Describe a policy that keeps a fleet of GPU nodes on identical package versions, using at least three mechanisms from this chapter.
30. Why should you not `pip install` into the system Python as root, and what do you use instead?

### Answers

1. Metadata: name/version/architecture (identify and compare), dependencies (compute everything needed), file checksums (later integrity verification), marked configuration files (preserve your edits on upgrade), maintainer scripts (create users, enable services), signature (authenticity).
2. `dpkg`/`rpm` handle one package file and the local database and do not fetch or fully resolve dependencies; `apt`/`dnf` talk to repositories, resolve dependencies, download and call the low-level tool. The high-level managers.
3. The tool may fail partway while writing its database, corrupting the record of what is installed, which is hard to repair.
4. (a) `dpkg -S /usr/bin/ssh` on Ubuntu; `rpm -qf /usr/bin/ssh` on Rocky. (b) `apt-file search zlib.h` (Debian family, after installing and updating `apt-file`); `dnf provides '*/zlib.h'` (Red Hat family).
5. `remove` uninstalls the files but keeps configuration files; `purge` removes configuration too. `.rpmnew` is the new default config written beside your edited file; `.rpmsave` is your old file saved when the package replaces it.
6. It proves the packages come from the repository owner and were not altered or substituted in transit; disabling the check lets an attacker who can intercept or compromise a mirror run code as root on your nodes. Apt moved from a single global keyring (`apt-key`) to per-repository key files referenced with `signed-by`.
7. An unattended upgrade installed a new kernel; DKMS could not build the NVIDIA module for it (headers missing or driver too old), so the next reboot boots the new kernel without the module. Prevent with `apt-mark hold` (or `versionlock`) on kernel and driver packages and controlled upgrades tested on a canary node; or restrict unattended upgrades to security updates outside those packages.
8. `apt` output is for humans and not stable; `apt-get`'s is stable for scripts. `DEBIAN_FRONTEND=noninteractive` makes debconf use defaults instead of asking questions.
9. Unpack, configure, make, (make check), make install; precede `make install` with `make -n install`, which prints what it would do without doing it.
10. It sets the installation root to a directory you own, so files land in `~/opt/x` and can be deleted without affecting the system; no root needed, no clash with distribution packages.
11. To see whether the archive has a top-level directory (otherwise extract into an empty directory) and to catch absolute paths; an archive with absolute paths such as `/etc/passwd` is likely malicious and should be deleted.
12. Read `config.log`: press `G` to go to the end in `less`, then search backward (`?`) for a phrase from the failure; the failing compiler command and its error are just above.
13. It reports compile and link flags and versions from `.pc` files. Make the file visible by symlinking it into the central directory or by adding its directory to `PKG_CONFIG_PATH`.
14. `-I dir`: add a header search directory (preprocessor stage, compile step). `-L dir`: add a library search directory (linker). `-lname`: link the library `libname` (linker).
15. Static: code copied into the executable; no run-time dependency and unchanged behaviour. Shared: one copy shared in memory and on disk; a library fix applies to all users without relinking.
16. `RPATH`/`RUNPATH` of the executable and `LD_LIBRARY_PATH` (their relative order depends on which kind of rpath), then `/etc/ld.so.cache`, then default directories. `ldconfig` rebuilds the cache from `ld.so.conf`; run it after adding libraries or changing the configuration.
17. It makes every program on the system search those directories first, slowing the loader and loading wrong or mismatched libraries. Use an `rpath` at build time, a wrapper script that sets it for one program, or environment modules (per job).
18. An embedded run-time library search directory in the executable. Set it with `-Wl,-rpath=/dir` at link time (or `patchelf --set-rpath`). Inspect with `readelf -d prog | grep -E 'RPATH|RUNPATH'`.
19. The recipe line begins with spaces instead of a tab.
20. `make` compares file modification times of targets and dependencies; nothing is newer, so it does nothing. After `touch aux.c`, `aux.o` is out of date and is recompiled, then the executable is relinked.
21. The first one, the compiler error and the `make[3]` line in the directory it names; the later `make[2]`/`make[1]` messages are only the unwinding.
22. From the directory that contains `src` (not inside `src`). `-p1` strips one leading path component from file names in the patch (useful when the patch has a directory like `package-3.42/` that your tree names differently).
23. For: control of options, control of the version, choice of install location (multiple versions), understanding, features missing in the distribution. Against: takes time, no automatic security updates, risk of overwriting distribution files, misconfiguration risk, not worthwhile if you do not use it.
24. No package database entry, so you cannot cleanly remove, upgrade or inventory it. Use `checkinstall`/`rpmbuild` or install into `DESTDIR` and package; or use an isolated prefix with environment modules.
25. Control server, network filesystem, one compute node, OFED, second compute node (mini-cluster), compilers and tests, communication tests, scheduler, job test, then clone/add nodes. So defects are found and fixed before being replicated.
26. Replace disk-identity references (`/dev/disk/by-id/...`) in `fstab` and the bootloader configuration with portable names or UUIDs; remove MAC-bound network interface naming rules; remove per-host state (SSH host keys, `machine-id`) so each clone gets its own.
27. Back up existing OFED packages (the installer removes them first, and a failed build leaves no InfiniBand) and match kernel/C library versions to the OFED release; set `memlock` to `unlimited` (soft and hard) in `limits.conf`.
28. Exported directories with the clients allowed and options; `exportfs -ra` (or `-av`) re-reads it. Fields: server:path, mount point, type, options, dump flag, fsck pass.
29. Example: mirror/snapshot repositories (one source of truth); `apt-mark hold`/`versionlock` for kernel, driver and toolkit; automation (Ansible) installing exact versions; unattended upgrades limited or disabled on GPU nodes; canary node testing; record `dpkg -l`/`rpm -qa` in build logs.
30. The system Python is part of the OS and tools depend on it; installing packages as root can break them. Use a virtual environment (`python3 -m venv`), a project tool such as `uv`, conda, or a container.

## Sources and further reading

- Brian Ward, *How Linux Works*, 3rd ed.: ch. 15 (development tools: the C compiler, compiling several source files, linking with libraries, static and shared libraries, `ldd`, how `ld.so` finds libraries, `rpath`, `LD_LIBRARY_PATH` and its dangers, header files and the preprocessor, `make`: a sample Makefile, built-in rules, dependency updates, command-line options, standard macros and variables, conventional targets, Makefile organisation; Lex and Yacc; scripting languages and shebang lines) and ch. 16 (compiling software from C source: unpacking source archives, GNU autoconf, an example installation, packaging a source build, `configure` options and environment variables, autoconf targets and log files, `pkg-config`, installation practice and where to install, applying a patch, troubleshooting compiles). Sections 6 to 9 follow these chapters; the explanations, tables, labs and the package-manager material (sections 1 to 5) are written independently.
- Sergey Zhumatiy, *Supercomputers for Linux SysAdmins*: ch. 7 (the package section: package metadata, dependencies, checksums, configuration files, repositories, `yum`/`dnf` and `rpm` options) and ch. 24 (node setup and software installation: network and hardware drivers, InfiniBand/OFED, RAID, the build order for a mini-cluster, login node, NFS server and client, communication software, compilers and libraries, the job scheduler, compute-node design and installation methods, kickstart, cloning and NFS-root, final testing). Sections 1 to 3 and 10 draw on these chapters.
- Manual pages: `dpkg(1)`, `apt(8)`, `apt-get(8)`, `apt-mark(8)`, `apt_preferences(5)`, `sources.list(5)`, `rpm(8)`, `dnf(8)`, `yum.conf(5)`, `ld.so(8)`, `ldconfig(8)`, `ldd(1)`, `readelf(1)`, `patchelf(1)`, `make(1)`, `pkg-config(1)`, `patch(1)`, `gcc(1)`, `tar(1)`.
- Related chapters: 1.3 (tar, links, inodes), 1.6 (users, `sudo`), 1.8 (limits and processes), 1.11 (ELF, libraries, `strace`), 1.14 (boot and initramfs), 1.22 (DKMS), 4.x (Ansible package modules), 6.7 (Slurm installation), 6.20 (environment modules), 7 (containers).

*Notes for review:* package-manager commands and file locations are those of current mainstream releases (Ubuntu LTS and RHEL-family 9); newer releases change defaults (deb822 `.sources` files, DNF versions, module streams). The NVIDIA repository, `cuda-keyring`, OFED/MLNX_OFED/DOCA-OFED and `nvidia-container-toolkit` details must be checked against NVIDIA's current documentation. The `ld.so` search order relative to `RPATH` and `RUNPATH` should be confirmed in `ld.so(8)` on your distribution. Kickstart and DHCP parameters are given as in the source and vary by DHCP server and installer release. All lab commands are **untested**; run them on a disposable VM before this chapter moves to `reviewed`.
