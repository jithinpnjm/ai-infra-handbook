---
id: "c01-30"
title: "1.30 Network file sharing and remote graphical access: rsync in depth, Samba, SSHFS, NFS clients, cloud storage, X11, VNC and alternatives"
sidebar_label: "1.30 Network file sharing and remote graphical access"
sidebar_position: 30
description: "A reference for moving and sharing files between machines and for giving users remote access: rsync options in depth, quick copies, Samba and CIFS, SSHFS, NFS, cloud storage, why network file sharing is hard, and X11, VNC, x2go and other remote graphics."
status: "drafted"
tier: "0"
level: "I"
lab_venue: "GCP VM"
---

# 1.30 Network file sharing and remote graphical access: rsync in depth, Samba, SSHFS, NFS clients, cloud storage, X11, VNC and alternatives

**Level:** intermediate · **Tier 0 (foundations)** · **Lab venue:** two or three small Ubuntu VMs on GCP · **Status:** drafted, labs untested

Chapter 1.5 introduced `scp`, `rsync` and the idea of shared filesystems. This chapter is the full reference: every way to copy and share files between Linux, Windows and cloud systems, why none of them is a universal answer, and how users reach a cluster remotely, including graphical programs when a command line is not enough.

## Why this matters for AI infrastructure

Data movement is a daily job in AI work: code to nodes, datasets in, checkpoints out, results back to a laptop. The tool choice decides whether a 2 TB transfer takes an hour or a week, whether a deleted directory can be recovered, and whether a home directory is available on 1,000 nodes. Meanwhile the same questions recur for users: how do they log in, copy files, run a visualisation, or open a notebook on a GPU node without exposing services to the internet? Knowing the options, and the performance and security trade-offs behind them, lets you pick the right one instead of the familiar one. This chapter also explains why the "standard" network filesystems are weaker than people expect, which is the background for why AI clusters use parallel filesystems and object storage (Parts 6 and 13).

## Prerequisites and outcomes

You need chapters 1.1 to 1.5 (SSH, `rsync` basics and the filesystem model) and 1.29 (SSH reference). After this chapter you will be able to:

- choose the right tool from a decision table (quick copy, `rsync`, Samba, CIFS, SSHFS, NFS, cloud storage);
- use `rsync` safely in depth: exact copies, trailing slash, excludes and includes, checksums, safeguards, compression, bandwidth limits, in both directions, in dry-run mode;
- explain the performance and security limits of network file sharing, and why they exist;
- set up and use Samba (server and client) and mount CIFS shares;
- use SSHFS and an NFS client, including automounting;
- explain how cloud storage is mounted through FUSE and why it behaves differently from a disk;
- describe how users should be given remote access (SSH, SFTP, why not FTP, how to treat web access);
- explain the X Window System's client/server model, forward X11 safely, and choose an alternative (VNC, x2go, NX, SPICE) when X is too slow;
- diagnose seven common failures.

## 1. Which tool for which job

Many ways exist to distribute and share files; this table summarises the common situations:

| You want to... | Use |
|---|---|
| Make a file or directory on your machine **temporarily available** to others on a trusted network | a one-line web server (`python3 -m http.server`) |
| **Copy files across machines**, especially repeatedly | `rsync` over SSH |
| Share files from Linux **regularly to Windows** machines | Samba (the SMB protocol) |
| **Mount Windows shares** on Linux | the CIFS filesystem (`mount -t cifs`) |
| Small-scale sharing between Linux machines with **minimal setup** | SSHFS |
| Mount **larger filesystems** from a NAS or server on a trusted local network | NFS |
| Mount **cloud storage** | various FUSE-based filesystems (or use the provider's CLI) |

Notice what is missing: **large-scale sharing between many locations and many users.** That is possible, but it takes a good deal of work; sections 6 and 7 explain why, and Parts 6 and 13 cover what clusters do instead.

## 2. A quick copy

If you want to move a file or two to another machine on your own network and do not care about anything fancy, start a web server in the directory:

```bash
python3 -m http.server 8000        # on the machine with the files (older Python 2: python -m SimpleHTTPServer)
# then, on the other machine: open http://10.1.2.4:8000 in a browser, or: curl -O http://10.1.2.4:8000/file
```

It serves the current directory to anyone who can reach port 8000. **Only do this on a network you trust** (it has no authentication and no encryption), bind it to a specific interface where you can (`--bind 10.1.2.4`), and stop it (Ctrl-C) when you are done.

## 3. `rsync` in depth

`scp -r directory user@host:dest` copies a tree but is blunt: if the destination already exists with extra files, those stay, so the result is not an exact copy, and it re-sends everything every time. For regular or automated transfers use **`rsync`**, the standard synchroniser on Linux: it compares source and destination, transfers only what differs, can verify, resume and mirror.

### Getting started

You need `rsync` installed on **both** machines and a way to reach one from the other, normally SSH (current versions assume SSH). It also works between two locations on one machine, for instance between filesystems.

```bash
rsync file1 file2 host:                    # copy files to your home directory on host (same syntax as scp)
rsync file1 file2 user@host:               # if your user name differs
rsync -a dir host:dest_dir                 # a directory tree, with symlinks, permissions, times, devices
rsync -nva dir host:dest_dir               # DRY RUN (-n) with verbose (-v): shows what would be sent, sends nothing
```

Without `-a` (or `-r`), `rsync` copies only plain files and prints `skipping directory dir`. If the remote shell cannot find `rsync` you will see `rsync not found ... connection unexpectedly closed (code 12)`; install it there, or if it exists outside the remote user's command path, point to it with `--rsync-path=/path/to/rsync`.

### Exact copies, and the dangerous option

By default `rsync` ignores what already exists at the destination: copying `d` (containing `a` and `b`) to a machine that already has `d/c` leaves `d/a`, `d/b` and `d/c`. For an **exact replica**, delete what the source does not have:

```bash
rsync -a --delete dir host:dest_dir
```

This is the most dangerous option in the chapter. Always inspect with `-nv` first and read exactly which files it would remove. (If the source is accidentally empty, because a filesystem was not mounted, `--delete` empties the destination.) Safer variants: `--backup --backup-dir=../old` keeps replaced and deleted files in a directory, and a snapshot of the destination makes mistakes recoverable.

### The trailing slash

A trailing `/` on the *source* changes the meaning:

- `rsync -a dir host:dest_dir` creates `dest_dir/dir/...` (the directory itself arrives).
- `rsync -a dir/ host:dest_dir` copies the **contents** of `dir` into `dest_dir` without creating `dir`, like `cp dir/* dest_dir` locally.

Combined with `--delete`, a stray slash can remove unrelated files at the destination. Be wary of **shell tab-completion**, which adds trailing slashes after directory names automatically.

### Excluding and including

```bash
rsync -a --exclude=.git src host:               # excludes every file or directory NAMED .git, anywhere
rsync -a --exclude=/src/.git src host:          # a leading / anchors to the TRANSFER root, not the system root
rsync -a --exclude='*.pyc' --exclude='__pycache__/' src host:
rsync -a --exclude-from=excludes.txt src host:  # patterns in a file, one per line
rsync -a --exclude='item/' src host:            # a trailing slash matches directories named item, not files
rsync -a --include='keep.log' --exclude='*.log' src host:   # include an exception to a broader exclude
```

The pattern is matched against a whole file or directory name component and may use simple globs: `t*s` matches `this` but not `ethers`. Use `--include` when a pattern turns out to be too restrictive; order matters (first match wins), so put includes before the excludes they carve exceptions from.

### How `rsync` decides, and safeguards

To be fast, `rsync` uses a **quick check**: a file is skipped if its **size and modification time** are the same on both sides. The first transfer of a tree sends everything; a second run (`rsync -av ...`) should list nothing, which is a good verification that the copy is consistent. When you need more assurance, or extra protection from overwriting:

| Option | Effect |
|---|---|
| `-c`, `--checksum` | compare content checksums instead of size and time (slower, thorough; use for important data or files that often have identical sizes) |
| `--ignore-existing` | never overwrite files that already exist at the destination |
| `-b`, `--backup` | rename an existing destination file (default suffix `~`) before replacing it; `--suffix=.bak` changes the suffix |
| `-u`, `--update` | skip files that are newer at the destination than at the source |
| `-v`, `-vv` | verbose (the default is silence unless there is a problem); `--stats` prints a summary at the end; `--info=progress2` shows overall progress |
| `-P` | `--partial --progress`: keep partially transferred files so interrupted copies resume |

### Compression and bandwidth

- **`-z`** compresses data in transit. It helps on slow or high-latency links; on a fast LAN the CPU cost of compressing and decompressing can make the transfer *slower*. Skip it for data that is already compressed (most checkpoint formats, images, archives).
- **`--bwlimit=RATE`** caps the transfer rate (the default unit is kibibytes per second; newer versions accept suffixes such as `50m`; see `man rsync`). It keeps a large upload from filling your uplink and starving everything else, because ACK and request traffic competes for the same outgoing bandwidth.

### Pulling files to your machine, and other uses

`rsync -a host:src_dir dest_dir` pulls from the remote side; omit `host:` on both arguments to copy locally. **Batch mode** can replay the same set of changes to several hosts. `rsync --delete` to a mounted cloud or other network storage is a simple, effective **backup**; combined with snapshots or `--link-dest` (hard links to unchanged files from the previous backup) it gives space-efficient daily backups. `rsync --help` and `man rsync` list many more options.

## 4. Why share files over a network at all? Performance and security

Network file sharing is attractive and always compromised, and you should know why before choosing it.

**Why people do it.** Traditionally: **convenience** (log in to any machine and see the same home directory) and **economy** (concentrate storage on a few servers instead of buying disks for every desktop). Clusters still do exactly this for home directories and software.

**Performance.** The one constant disadvantage: *network storage is slow compared with local storage*, and the difference shows with certain access patterns. Streaming a large file sequentially works well, because the server can read ahead and buffer when it knows the client will ask for the next block. But if you do complex manipulation, or touch many different files, the client spends most of its time **waiting on the network**, and the culprit is **latency**: for every new random file access the server must accept and decode the request, then find and load the data, and those first steps are the slowest and happen on almost every new file. The rule that follows: for large amounts of data that do not need frequent random access, network storage is fine; for editing video, compiling a large project, or reading millions of small training files, keep a local copy (or stage data to local NVMe, chapter 13.2).

**Security.** Historically, file-sharing protocols were designed with security as a low priority, and **the easiest options to configure are typically the least secure**. If you cannot trust the networks between the machines, you need both **authentication and authorisation** (only parties with correct credentials get access, and the server is who it claims to be) and **encryption** (so data in transit cannot be read). There are no standardised ways to bolt this on; you combine tools such as `stunnel`, IPsec or VPNs to protect the layers beneath a basic protocol. Treat any file share as reachable by anyone who can reach its network.

## 5. Samba: sharing with Windows (SMB) and CIFS mounts

**SMB (Server Message Block)** is the standard Windows file and printer sharing protocol; macOS can speak it too. **Samba** is the standard suite that implements it on Unix: it lets Windows machines use files and printers on your Linux system, and lets you access Windows shares from Linux. (Over the years the client filesystem has been called **CIFS**, Common Internet File System; on modern systems SMB 3 is used.) Samba is a large topic; here is what you need for a working server and client.

A Samba server needs: a configuration file `smb.conf` (usually `/etc/samba/smb.conf`) with a `[global]` section and one section per share, and the daemons `smbd` (handles share requests) and `nmbd` (a NetBIOS name server). A distribution package starts them with sensible defaults, but it cannot know which directories you want to share.

### The global section and access control

```ini
[global]
   netbios name = fileserver          # server name (default: the Unix host name)
   server string = My server via Samba
   workgroup = MYNETWORK              # Windows workgroup or domain name
   interfaces = 10.23.2.0/255.255.255.0   # listen only on these networks or interfaces
   bind interfaces only = yes         # make 'interfaces' strict
   security = user
   passdb backend = tdbsam            # Samba's own password database (fine for small networks)
   obey pam restrictions = yes        # password changes obey PAM rules
```

Useful access-control options (global or per share): `interfaces` and `bind interfaces only` (limit which networks it listens on), `valid users` (the list of allowed users, for example `valid users = jruser, bill`), `guest ok` (anonymous access; **only on a private network**), and `browseable` (whether the share shows in network browsing; if `no` you must know its exact name).

### Passwords

Unix and Windows store passwords differently, so Samba keeps its own password database (unless you authenticate against a Windows domain with `security = domain`, in which case each domain user still needs a local account with the same name):

```bash
sudo smbpasswd -a alice        # add an existing Linux user to Samba (prompts for the SMB password twice)
sudo smbpasswd -x alice        # delete the user
sudo smbpasswd -d alice        # disable ; -e enables again
sudo smbpasswd alice           # change a user's password as root (users change their own with plain 'smbpasswd')
```

The user must already exist as a Linux account. **Beware `unix password sync = yes`** in `smb.conf`: it changes the user's normal Linux password along with the Samba one, which confuses users who set a different Samba password and then cannot log in to Linux. Some distributions turn it on by default.

### Shares, homes and printers

```ini
[projects]
   path = /srv/projects
   comment = Project files
   guest ok = no
   writable = yes
   printable = no
   veto files = /*.o/bin/            # do not export files matching these patterns

[homes]
   comment = home directories
   browseable = no
   writable = yes
   # path = /u/%S                    # %S is replaced by the user name, if homes live elsewhere

[printers]
   comment = Printers
   browseable = yes
   printing = CUPS                   # needs Samba built with CUPS support
   path = cups
   printable = yes
   writable = no
```

Never combine `guest ok = yes` with `writable = yes`. A directory share must have `printable = no`.

### Starting, diagnosing and the client

Normally systemd starts the daemons (`systemctl status smbd nmbd`; on newer distributions the units are `smb` and `nmb`), and after changing the configuration you reload the service. If started manually: `nmbd -D -s /path/smb.conf` and `smbd -D -s /path/smb.conf` (`-D` daemon mode). Problems during startup print to the terminal; runtime diagnostics go to log files in `/var/log/samba` (`log.smbd`, `log.nmbd`, and one per client). Validate the file with `testparm`.

The client tool **`smbclient`** lists and accesses shares:

```bash
smbclient -L SERVER -U alice                 # list the shares (Disk, Printer; IPC shares are for management)
smbclient //SERVER/sharename -U alice        # an FTP-like prompt: get, put, cd, lcd, pwd, !ls, help
```

To mount a share as a directory you need the CIFS utilities (usually a separate package):

```bash
sudo mount -t cifs //SERVER/sharename /mnt/share -o credentials=/root/.smbcreds,uid=1000
```

Put `username=` and `password=` in a root-only credentials file instead of on the command line, where other users could see them in the process list. (The correct address syntax is `//SERVER/sharename`.)

## 6. SSHFS and NFS: sharing between Linux machines

### SSHFS

**SSHFS** is a user-space filesystem (FUSE) that opens an SSH connection and presents the remote files at a local mount point, which makes it the easiest way to try sharing between Linux machines:

```bash
sshfs alice@host:/data /mnt/data        # mount; omit ':dir' for the remote home directory
fusermount -u /mnt/data                  # unmount as a regular user (fusermount3 on newer systems); root can use umount
```

Advantages: **minimal setup** (the remote side only needs SFTP enabled, which most SSH servers do) and **no special network configuration** (it works anywhere you can open an SSH connection, trusted network or not). Disadvantages: **performance suffers** because of the overhead of encryption, translation and transport (though often not as badly as expected), and **multiuser setups are limited**; mount it as the regular user whose files they are, which also keeps ownership and security consistent. It is well worth trying for modest needs.

### NFS (client side)

**NFS** is the traditional Unix network filesystem. There are several versions (v3 and v4 are common), it can run over TCP or UDP, and it has many authentication and encryption options, very few of which are enabled by default. To mount:

```bash
sudo mount -t nfs server:/export /mnt/nfs         # the -t is optional; mount normally detects it
sudo mount -t nfs4 -o sec=krb5p server:/export /mnt/nfs   # with Kerberos authentication and privacy
```

The security choices are set with the **`sec=`** option: `sys` (trust the client's user IDs, the default), or `krb5`, `krb5i`, `krb5p` (Kerberos authentication, integrity, and encryption). Many administrators on small closed networks use **host-based access control** on the server; stronger methods such as Kerberos require configuration elsewhere. See `man nfs`.

**Automounting.** Once you use network filesystems heavily, mount them only when someone *uses* them, so that boot does not depend on the server being up. The traditional tools were `automount` (autofs) and `amd`; today much of this is provided by **systemd automount units**: in `/etc/fstab`, add `x-systemd.automount` (and optionally `x-systemd.idle-timeout=60`) to the options.

**NFS servers.** Running the server means starting `mountd` and `nfsd` and listing exports in **`/etc/exports`** (then `exportfs -ra`; `showmount -e server` shows what a server offers). That is considerably more involved than the client, and it is often more convenient to buy a **NAS** appliance (many run Linux with NFS built in, and vendors add administration tools for RAID, snapshots and cloud backup). Chapters 6.18 to 6.21 cover NFS limits at cluster scale and the parallel filesystems that replace it.

## 7. Cloud storage, and the state of network file sharing

### Cloud storage

Cloud object stores (AWS S3, Google Cloud Storage) have lower performance than a local network but offer two big advantages: **you never maintain them** and **backups are not your problem**. All providers offer web and programmatic interfaces and command-line tools (`gcloud storage`, `aws s3`, `rclone`), and most can also be **mounted** on Linux through **FUSE** (Filesystem in Userspace): a user-space daemon sits between the data source and the kernel, so no kernel code is involved. For popular services there are several FUSE options. The details are provider-specific; the general behaviour is that listing and small-file access are slow, writes are often whole-object, and consistency and rename semantics differ from a disk, so do not run databases or edit-in-place workloads on them. For AI datasets and checkpoints, use the tools and formats designed for object storage (chapter 13).

### Why there is no standard answer

Network file sharing can feel incomplete because **it is**. The base security level of NFS is low and costly to raise; CIFS is better, since modern software builds in encryption, but performance limits are hard to remove, and a client can behave badly when it temporarily cannot reach its storage (processes hang in uninterruptible sleep, chapter 1.1). Several designs tried to fix this, the most thorough being the **Andrew File System (AFS)**, from the 1980s. Why doesn't everyone use AFS or something like it? Largely because of lack of flexibility: its security depends on **Kerberos**, which is available everywhere but never became a standard part of Unix and takes real effort to set up and run (you need a server for it). Large institutions (universities, banks) manage that happily and are the heartland of AFS; small sites prefer NFS or CIFS shares. Even Windows moved to Kerberos as the default for its server products in Windows 2000, but small networks do not run Windows domains of that kind.

There is also a technical reason: **network filesystem clients have traditionally been kernel code** (NFS especially). Network filesystems are complicated, authentication does not belong in the kernel, and a kernel implementation severely limits the number of developers who can contribute.

Cloud storage changed the picture. Access methods there are built on security mechanisms such as TLS that work **without** a Kerberos-style infrastructure, and the many FUSE clients show that authentication, encryption and file handling can all live in user space. Future designs may well add flexibility in security and in filename translation. For now, in Linux and Unix there is no truly standard network file-sharing system unless you are a large site or willing to do significant work, which is the situation that cluster filesystems (Part 6) and object storage (Part 13) address.

## 8. Giving users remote access

### SSH, for users

SSH is the main way users reach a supercomputer today. Do not be intimidated by their graphical habits: with a few commands, most users are productive, because their daily work is queueing jobs and reading their status; copying and editing is done with a convenient client on their own machine. To ease the start, install **Midnight Commander** (`mc`), a two-panel file manager whose interface resembles Total Commander or Far Manager, on the access node.

Policy recommendations:

- **Passwords:** the classic mode works by default but should not be used for ordinary users. If you must allow it, allow it only from a few administrator workstations and for a few accounts, to resolve emergencies.
- **Keys:** users generate a key pair (or use an existing one) and send you the **public** half; you append it to `~user/.ssh/authorized_keys` (append, never replace). Public keys come in an **OpenSSH** single-line format and an **RFC** multi-line format; convert RFC to OpenSSH with `ssh-keygen -i -f rfc-key.pub >> ~user/.ssh/authorized_keys`. A Linux or macOS user then connects with `ssh -i ~/.ssh/cluster-key cluster`.
- **Windows users:** **PuTTY** (with `puttygen` to create and convert keys, saved in `.ppk` format, and the `putty` client) works well; load the `.ppk` key and enter the cluster address. For file transfer, **WinSCP** (or its plug-in for FAR) and FileZilla (which needs the PuTTY agent loaded with the key, because it does not otherwise support key authentication).
- Linux and macOS users can transfer files with `scp`, `sftp`, `rsync`, the FISH virtual filesystem in Midnight Commander, `sshfs`, or the remote-connection feature of graphical file managers (chapter 1.5).

### FTP and web access

**FTP** was once the dominant way to distribute files and is still built into many browsers and file managers, but its big flaw is that it sends the login and password **unencrypted**. Secure variants exist, but they are not standardised and not universally supported, and even with encryption a password remains a weak credential. FTP is acceptable in exactly one case: **public, anonymous, read-only distribution** of files. For everything else use **SFTP or SCP**, which are standardised, supported by every SSH server, and allow key authentication that largely removes the guessing risk. Their downsides are higher CPU use and often lower speed (encryption overhead, and the way data moves over encrypted channels), and standard clients and servers do not offer "encrypt only the login" modes.

For **web access** (HTTP), you often do not need a web server on the cluster at all: put the information on a separate, ordinary server, and avoid running one on the supercomputer, because any web server becomes vulnerable the moment it serves dynamic content (CGI scripts, application servers) and even static-only servers can be attacked through carelessly enabled modules. When the cluster must publish something (for example queue status), let the external web server obtain the data over SSH or `rsync` with a **restricted key** whose command is limited to one harmless action (chapter 1.29), or configure the server to remove the possibility of compromise: strict `chroot` or, better, run it in a lightweight container or VM (LXC, chapter 1.19 and 1.26). Keep logs, analyse them, and run an **intrusion-detection system**: every unnecessary service reachable from outside is an invitation to break in, even just for fun.

## 9. Remote graphical access: X11 and its alternatives

### The X Window System

Linux graphics is not part of the operating system: the graphical stack is an ordinary set of programs, and a system can run happily with no graphics at all, which is the normal mode for a supercomputer. Occasionally graphical programs are unavoidable (some commercial tools can be configured only graphically or through a browser), and **visualising scientific data** is often best done next to the data, because moving large results to a workstation costs far more than sending screen images.

The **X Window System** (X11, or just X) provides the basics: drawing windows, moving them, and handling mouse and keyboard, but **not** the look of the windows. That is the job of a **window manager** (frames, title bars, placement) and, in full desktop environments, a set of applications and a consistent style (**GNOME**, **KDE**, and others). Wayland is gradually replacing X, though compatibility with X will persist for a long time.

X uses a **client/server architecture, with the names the opposite way round from what you might expect**: the **X server** is the program on *your* machine that owns the screen, keyboard and mouse; the **clients** are the graphical applications, which may run on a *different* machine and talk to your server over the X protocol (version 11) through Unix sockets or network sockets. The server consists of drivers for input and output devices plus the part that talks to applications.

- **Displays.** Each X server serves a **display** with a number; by default `:0`. Applications choose which display to use with the `-display` option (`xclock -display :0`) or the **`DISPLAY`** environment variable (`export DISPLAY=:0`). When forwarded over SSH, `ssh` sets `DISPLAY` for you.
- **Server software and configuration.** The reference implementation is **X.Org**. Modern versions detect hardware automatically and need no configuration; when they guess wrong, create `/etc/X11/xorg.conf` (generate a starting file with `Xorg -configure`, which produces `xorg.conf.new`) or drop-ins in `/etc/X11/xorg.conf.d/`. Server problems are logged in `/var/log/Xorg.0.log` (the 0 is the display number).
- **Starting a session.** Rarely by hand: `startx` starts the server plus a script that starts the clients (a session script in `~/.xsession` or `/etc/X11/Xsession.d/`), and the server stops when that session script ends. Normally the server runs as a service with a **display manager** (`xdm`, `gdm`, `kdm`, `lightdm`) as its only client: it shows a graphical login, offers a choice of language and window manager or desktop, and starts the session after a successful login (`xdm`'s files are in `/etc/X11/xdm/`, `gdm`'s in `/etc/gdm/`).

### Using X from a Windows or Mac workstation

You need an **X server on the machine in front of you**. On Windows there are commercial products and free ones: the popular free choice for years was **Xming** (with an OpenGL variant, plus a launch tool), and its modern relative is **VcXsrv**; typical flags are the display number, `-clipboard` (share the clipboard), `-multiwindow` (each remote window is a local window) and keyboard-layout options. The Windows firewall may ask to open ports for the server; **restrict that rule to the machines that will use it**. On macOS, XQuartz plays this role.

A session: start the X server locally; connect with an SSH client with **X11 forwarding** enabled (`ssh -X host`, or `-Y` for trusted forwarding; in PuTTY, "Connection / SSH / X11 forwarding"); the client sets `DISPLAY` and the authorisation cookie (`XAUTHORITY`) automatically, and any X program you start on the remote host appears on your screen. The remote machine needs **`xauth`** installed. Note that this shows *remote* programs on your local display; you cannot "run your local browser on the remote computer".

**Authorisation.** Without forwarding, you must tell the X server which machines may connect: on Unix `xhost +computer_name` (or, for the Windows servers, an `X0.hosts` file listing allowed names and addresses). **`xhost` is weak and often disabled by default**; avoid it, and use `xauth` cookies, which SSH forwarding sets up for you. If you use `sudo` on the remote host, the `XAUTHORITY` variable must pass through.

### When X is too slow: alternatives

X's weakness is speed: with rich graphics over a narrow or high-latency link, it can become unusable. The alternatives send **images of the screen** (compressed) instead of drawing commands:

| Protocol / tool | Notes |
|---|---|
| **VNC** (TigerVNC, tightvncserver) | very common, many clients; supports scaling and compression; the servers run as X servers so any X application works. Limitation: **not multi-user**: the server runs as one user and everyone who connects sees that user's desktop; dynamic per-user sessions are not available, so it suits a few dedicated uses such as visualisation or administering specific hardware. **Always set a password** (and tunnel it over SSH). |
| **RDP** | Windows' own remote desktop protocol: authentication, simultaneous users, file transfer, usually faster than VNC with better quality; but the protocol is closed and Linux servers for it are rare and not the authors' recommendation. |
| **x2go** | open-source protocol derived from NoMachine's NX; clients and servers for most distributions and for Windows. **No separate server service:** install the package, and the client connects over **SSH** and starts the server program as the user, so authentication is SSH's and the server side is well protected. Speed comparable to VNC, with compression and scaling, and it can show just one program's windows. |
| **NoMachine NX** | the commercial origin of the technology above; the free server allows two simultaneous users; supports password authentication with session saving and reconnection. |
| **SPICE** | another remote display protocol, less widespread. |

For notebooks and web UIs (Jupyter, TensorBoard, the "visualisation" of modern AI work), you rarely need any of these: run the service on the node and **tunnel the port** over SSH (chapter 1.5), which gives the best performance and the smallest attack surface.

### Principle for access design

"The less access, the better", yet users must not feel boxed in. SSH with SCP/SFTP usually suffices. Publish clear instructions for the common tasks, keep the access paths few and well monitored, and treat remote access as the "face" of the system for users, because it is what they will use almost all the time.

## How it fails

### 1. `rsync --delete` removes the wrong files
**Symptom:** destination data vanishes. **Cause:** a trailing slash difference, an empty or unmounted source, or the wrong destination path. **Prevention:** always `-nv` first; check `df` and that the source path is populated; use `--backup-dir` or snapshots; never put `--delete` in a habit alias.

### 2. A transfer is "done" but data differs
**Symptom:** a corrupted or partial dataset after a copy. **Cause:** interrupted copy leaving files with matching size and time, or modification times preserved from a truncated file. **Fix:** `rsync -c` (checksums) or `sha256sum` comparison for critical data, `--partial` and re-run until `rsync -avn` lists nothing.

### 3. Samba users cannot log in, or Linux password suddenly changes
**Symptom:** access denied from Windows, or Linux login breaks after an SMB password change. **Cause:** the user is not in Samba's database (`smbpasswd -a`), the `[global]` security settings are wrong, firewall blocks, or `unix password sync = yes` changed the Unix password too. **Diagnose:** `testparm`, `pdbedit -L`, `/var/log/samba/*`, `smbclient -L localhost -U user`.

### 4. NFS clients hang
**Symptom:** commands touching an NFS path freeze (state `D`); a node that boots with a dead NFS server never finishes booting. **Cause:** hard mounts waiting for an unreachable server, or boot depending on a mount. **Fix:** fix the server or network; use automount (`x-systemd.automount`) so mounts happen on demand; consider `soft` or `intr`-style options only where the application can tolerate errors (they risk data loss); monitor the server.

### 5. SSHFS is "slow" or leaves stale mounts
**Symptom:** very slow listing of large directories; "Transport endpoint is not connected". **Cause:** FUSE overhead and per-file round trips; the SSH connection dropped. **Fix:** use `rsync` or NFS for heavy work; add `-o reconnect,ServerAliveInterval=15`; unmount with `fusermount -u`.

### 6. Remote X programs fail ("cannot open display")
**Symptom:** `Error: Can't open display`. **Cause:** no X server running locally, forwarding not enabled (`-X`), `xauth` missing on the remote host, `DISPLAY` unset or wrong (after `sudo`, the variable and cookie are lost), `X11Forwarding no` on the server, firewall. **Diagnose:** `ssh -vX`, `echo $DISPLAY`, `xauth list`, `xclock`. **Fix:** address the missing piece; for slow graphics use x2go or VNC over a tunnel.

### 7. FTP or open web services expose the cluster
**Symptom:** credential theft, defaced pages, intrusions. **Cause:** plaintext FTP logins, a web server with dynamic content on the cluster, unnecessary services reachable from outside. **Fix:** SFTP/SCP only; web content on a separate server; restricted, command-limited keys for status feeds; containers or chroot; log analysis and intrusion detection.

## Hands-on lab (two or three GCP VMs; untested)

**Part A: quick copy and rsync.**
1. Serve a directory with `python3 -m http.server --bind <internal IP>` and fetch a file from another VM with `curl`; note what protects it (nothing) and stop it.
2. Build a directory with nested folders, a `.git` directory, some `*.pyc` files and a symlink. Run each of `rsync -nva`, then `rsync -a`, with and without the trailing slash; compare the resulting trees. Then `rsync -a --exclude=.git --exclude='*.pyc'` and `--exclude-from`. Use `--include` to keep one `.pyc` that the broader exclude would remove.
3. Safeguards: modify one file at the destination to be newer; compare the effect of the default, `--update`, `--ignore-existing`, `--backup --suffix=.old`, and `-c`. Produce a corrupted-copy scenario (truncate a file but keep its time with `touch -r`) and show that only `-c` catches it.
4. `--delete`: create an extra file at the destination, preview with `-nv --delete`, run it, then show how a wrong trailing slash combined with `--delete` would have behaved (in a scratch directory only).
5. Compression and limits: time a transfer of a large file with and without `-z` (use `dd if=/dev/urandom` for incompressible data and a text file for compressible data) and with `--bwlimit=1000`.

**Part B: Samba.**
6. Install Samba on vm1, create a `[projects]` share with `valid users`, add a Samba user with `smbpasswd -a`, validate with `testparm`, restart the services, and list shares with `smbclient -L localhost`. From vm2 install `cifs-utils` and mount the share with a credentials file; create files from both sides and check ownership. Break it on purpose with `unix password sync = yes` and observe what changes. Clean up.

**Part C: SSHFS and NFS.**
7. Mount a directory from vm1 on vm2 with SSHFS; time `ls` on a directory with 5,000 files compared with local; unmount with `fusermount -u`.
8. Install an NFS server on vm1 (`nfs-kernel-server`), export a directory in `/etc/exports`, run `exportfs -ra`, and mount it on vm2. Create files as users with the **same name but different UIDs** on the two machines and observe the ownership problem (chapter 1.6). Add `x-systemd.automount` to the `fstab` line and stop the server to see that boot and unrelated commands no longer hang.

**Part D: cloud storage.**
9. With `gcloud storage cp` and `rclone` (or `gcsfuse`), copy and list a bucket, then mount it with a FUSE tool; time listing 1,000 small objects versus a local directory, and write a file and read it back immediately; note how it differs from a disk.

**Part E: remote graphics.**
10. On a VM, install a minimal X application (`x11-apps`) and `xauth`, ensure `X11Forwarding yes`, and from your laptop with an X server (XQuartz or VcXsrv) run `ssh -X vm xclock`. Then break it in each way listed in failure mode 6 and fix it. Try `sudo xclock` and see what is lost.
11. Install x2go (or TigerVNC bound to localhost and tunnelled with `-L`) and open a desktop session over a slow link simulated with `tc netem` (chapter 2.23); compare responsiveness with forwarded X for a graphics-heavy program.

## Checkpoint questions

1. Which tool would you use for: a one-off share to a colleague on your LAN; a nightly copy of a project directory; mounting a Windows share; sharing a home directory among 20 Linux machines; mounting a cloud bucket?
2. Why does `scp -r` not give an exact copy, and how does `rsync -a --delete` differ? What is the main risk?
3. Explain the effect of the trailing slash on the rsync source. How can a tab-completion habit be dangerous?
4. How does rsync decide to skip a file? Name four options that add safety or verification.
5. When does `-z` help and when does it hurt? What does `--bwlimit` protect?
6. Why is network storage slow for many small files? What dominates?
7. Name the two reasons classic network file sharing is considered insecure, and ways to harden it.
8. List the steps to make a Linux directory available to Windows users with Samba. Why does Samba need its own password database?
9. What is `unix password sync = yes` and why is it a trap?
10. What are SSHFS's strengths and weaknesses? How do you unmount it?
11. What does the `sec=` NFS option choose? What is an automounter for?
12. Why has no network filesystem become a universal standard (AFS, Kerberos, kernel clients)? How did cloud storage change the approach?
13. Why should ordinary users not use passwords or FTP to reach a cluster? What replaces FTP?
14. Why not run a web server on the cluster itself? How do you publish status safely?
15. In X11, which machine is the "server"? What are `DISPLAY` and `xauth` for? Why is `xhost +` discouraged?
16. Compare VNC, x2go and RDP for remote desktops on a cluster.
17. Why is tunnelling a notebook port over SSH usually better than any remote desktop?

### Answers

1. `python3 -m http.server` on a trusted LAN; `rsync` (cron or a systemd timer); CIFS (`mount -t cifs`); NFS (with automount); a FUSE mount or, better, the provider's CLI (`gcloud storage`, `rclone`).
2. `scp -r` does not remove files at the destination that are not in the source, and recopies everything. `rsync -a --delete` makes the destination an exact mirror by deleting extras, so the risk is deleting data you meant to keep (wrong path, empty source, wrong trailing slash).
3. `src/` copies the contents of `src` into the destination; `src` copies the directory itself into it. With `--delete`, the wrong form can remove unrelated files at the destination. Tab completion adds trailing slashes to directory names automatically.
4. A file is skipped if size and modification time match. Safety options: `-n` dry run, `-c` checksum, `--ignore-existing`, `--backup` (with `--suffix`), `--update`, `--stats`/`-v` for review.
5. `-z` helps on slow or high-latency links with compressible data; it hurts on fast LANs (CPU becomes the limit) or with already-compressed files. `--bwlimit` keeps a transfer from consuming the whole uplink so other traffic is not starved.
6. Latency: every random file access needs a request, a decode, a lookup and a response, and these first steps dominate, whereas sequential streaming can be pre-fetched.
7. Protocols were designed with security as a low priority (weak authentication, no encryption by default) and the easy configurations are the least secure. Harden with strong authentication (Kerberos), encrypted transports (`krb5p`, TLS, IPsec, VPN, `stunnel`), restricted network access and host-based controls.
8. Install Samba; write `smb.conf` with `[global]` (server name, workgroup, security, password backend) and a share section; add users with `smbpasswd -a` (they must exist in Linux); start `smbd` and `nmbd`; validate with `testparm`; connect from Windows. Unix and Windows password hashing differ, so Samba keeps its own database (unless it authenticates against a Windows domain).
9. It makes `smbpasswd` change the user's normal Linux password along with the Samba one, so a user who sets a different Samba password may find they can no longer log in to Linux.
10. Strengths: minimal setup (SFTP only), works over any SSH connection. Weaknesses: slow (encryption and translation overhead), limited multiuser support. Unmount with `fusermount -u mountpoint` (root can use `umount`).
11. `sec=` selects the security flavour (`sys`, `krb5`, `krb5i`, `krb5p`). An automounter mounts filesystems only when used, avoiding boot dependencies on servers.
12. Strong designs such as AFS depend on Kerberos, which never became standard and is costly to run for small sites; kernel-resident clients are complex and limit developers; so simpler NFS/CIFS dominate despite weaknesses. Cloud storage uses TLS and API authentication and user-space FUSE clients, avoiding both problems.
13. Passwords can be guessed and FTP sends them in plaintext. Use SSH keys with SFTP/SCP (standardised, supported by every SSH server).
14. A web server serving dynamic content becomes a target and widens the attack surface. Put web content on a separate server; feed it with restricted, command-limited keys over SSH or rsync; use chroot or containers; monitor logs and use intrusion detection.
15. The machine in front of you running the display is the X server; remote applications are clients. `DISPLAY` says which display to use; `xauth` cookies authorise connections. `xhost +` opens the display to everyone and is unreliable or disabled by default.
16. VNC: widely available, scalable, but single-user sessions; RDP: fast and multiuser but closed with few Linux servers; x2go: open source, SSH-based authentication, no extra server service, per-user sessions, good speed.
17. It sends only the needed traffic, uses SSH's authentication and encryption, adds nothing to expose, and gives native-browser performance, while a remote desktop sends screen images and needs more software.

## Sources and further reading

- Brian Ward, *How Linux Works*, 3rd ed., ch. 12 (the scenario-to-tool list, quick copy, `rsync` including exact copies, the trailing slash, excluding files, checking and safeguards, compression, bandwidth limits, pulling files, file-sharing usage, performance and security, Samba server and client, passwords, shares, homes, printers, CIFS, SSHFS, NFS, cloud storage, and the state of network file sharing, including AFS and Kerberos).
- Sergey Zhumatiy, *Supercomputers for Linux SysAdmins*, ch. 18 (remote user access: SSH for users, key formats and PuTTY, FTP and web access, X Window, X servers for Windows, xauth and xhost, VNC, RDP, x2go, NX and SPICE). Section structure follows these chapters; explanations, corrected command syntax (CIFS address form, Python 3 server), security commentary, failure modes and labs are original.
- Manual pages: `rsync(1)`, `smb.conf(5)`, `smbpasswd(8)`, `smbclient(1)`, `mount.cifs(8)`, `sshfs(1)`, `nfs(5)`, `exports(5)`, `Xorg(1)`, `xauth(1)`, `vncserver(1)`.
- Related chapters: 1.3 (archives and `find`), 1.5 and 1.29 (SSH), 1.6 (UID consistency, NFS ownership), 6.18 to 6.21 (NFS limits, Lustre, parallel I/O), 13 (data path, small files, checkpoints).

*Notes for review:* Samba service names (`smbd`/`nmbd` versus `smb`/`nmb`), SMB protocol versions, `rsync --bwlimit` units, `fusermount` versus `fusermount3`, NFS mount option names and Windows X-server products (Xming, VcXsrv) vary by distribution and version; the "no separate NFS server section" follows the source book's scope. All lab commands are **untested** and must be run on VMs before this chapter moves to `reviewed`.
