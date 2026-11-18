# Part 1 image plan: chapters 1-10 (plan only, no images generated, no chapter edits)

> **RULE (owner, 2026-11-17): figures go only on actual teaching content. No figures in Hands-on lab, Exercises, Checkpoint questions, Sources, or "How it fails" / problem / troubleshooting sections. Any planned figure anchored under such a heading is DROPPED (ch01-fig6 dropped).**

Conventions used below:
- Figure numbers start at 1.2 in chapter 1 because `ch01-fig1-office-building.jpg` already exists at "## 1. What an operating system is for".
- Existing mermaid blocks are listed per chapter so no figure repeats one.
- Labels are copied from the chapter text. Every figure uses only the labels listed.

## Chapter 1

Existing mermaid blocks (do not duplicate): "## 2. The three layers" (layer stack), "### Job 1: running processes" (timer switch loop), "### What happens when you type a command" (sequence diagram), "## 6. Distributions: Linux is a kernel, not a system" (five distro parts), "## 7. Putting a GPU node on the map" (GPU node stack). Existing image: fig1 office building under "## 1.".

### ch01-fig2-ring-privilege

- id: ch01-fig2-ring-privilege
- anchor: ### Why two modes? Kernel mode and user mode
- technical point: The CPU refuses privileged instructions in ring 3, raises a fault that hands control to the kernel, and the kernel usually kills the offending program.
- labels: Ring 0, Ring 3, Kernel mode, User mode, Privileged instruction, Fault to kernel, Program killed
- scene: Draw two concentric rings. The inner ring, labelled Ring 0 and Kernel mode, holds the kernel and a small set of dangerous instructions. The outer ring, labelled Ring 3 and User mode, holds a program that tries one privileged instruction; an arrow labelled Fault to kernel crosses inward, and the program is shown removed with the label Program killed.
- alt: Two concentric rings show that a user program trying a privileged instruction is stopped by the CPU and handed to the kernel, which usually kills it.
- caption: Figure 1.2. Ring 0 is where the kernel runs, and a privileged instruction tried from ring 3 triggers a fault that the kernel handles.

### ch01-fig3-mmu-page-table

- id: ch01-fig3-mmu-page-table
- anchor: ### Job 2: managing memory
- technical point: The MMU translates each process's virtual addresses to physical RAM through that process's own page table of 4 KiB pages, so one process's pages are not mapped into another's table.
- labels: Virtual address, Page table, MMU, Physical RAM, Process A, Process B, 4 KiB page
- scene: Show two process columns, Process A and Process B, each with its own page table. Both tables pass through a single MMU box into a strip of Physical RAM; Process A's entries point to RAM pages, while Process B's table has no entry that reaches A's pages, drawn as a blocked link.
- alt: Two processes each have a private page table, and the MMU maps their virtual addresses into shared physical RAM with no cross-access.
- caption: Figure 1.3. The MMU translates each process's virtual addresses through its own page table, so one process cannot name another's memory.

### ch01-fig4-devices-as-files

- id: ch01-fig4-devices-as-files
- anchor: ### Job 3: managing devices
- technical point: Linux exposes hardware as special files under /dev, and the kernel routes ordinary file operations to the matching driver.
- labels: Program, /dev/nvidia0, Kernel, Device driver, GPU hardware, Ordinary file operations
- scene: A program on the left performs ordinary file operations on the file /dev/nvidia0. An arrow runs through the Kernel box to the Device driver, which connects to the GPU hardware on the right. Keep the file as the visible entry point so the reader sees a file, not a device API.
- alt: A program uses an ordinary file, /dev/nvidia0, and the kernel forwards its operations through the driver to the GPU hardware.
- caption: Figure 1.4. A device file looks like any other file, and the kernel quietly sends its operations to the driver for the hardware.

### ch01-fig5-syscall-layers

- id: ch01-fig5-syscall-layers
- anchor: ### Job 4: system calls and the services around them
- technical point: Programs usually call a library function such as printf or open, and glibc performs the actual system call on their behalf.
- labels: Your program, glibc, libc.so.6, System call, Kernel
- scene: Draw a vertical stack of four boxes from top to bottom: Your program, glibc (labelled libc.so.6), System call, Kernel. Arrows run downward between them, and a dashed line on the right marks the boundary between user space and the kernel, labelled with the same labels only.
- alt: A program calls glibc, which in turn makes the system call that crosses into the kernel.
- caption: Figure 1.5. A program's library call, through glibc, becomes the system call that enters the kernel.

### ch01-fig6-module-version-mismatch

- id: ch01-fig6-module-version-mismatch
- anchor: ### 1. "I updated the kernel and the GPU disappeared"
- technical point: Kernel modules are tied to one kernel build, so after a kernel update the NVIDIA modules must match the running kernel or the GPU disappears.
- labels: Old kernel, New kernel, nvidia.ko, Module missing, uname -r, DKMS
- scene: Split the image into a before panel and an after panel. In the before panel, a kernel block is joined to a matching nvidia.ko block. In the after panel, the kernel block is newer and the nvidia.ko block is greyed out with the label Module missing, with uname -r shown above the kernel and DKMS shown as the fix path back to a matching module.
- alt: Before the update the nvidia module matches the kernel; after the update the module is missing and must be rebuilt for the new kernel.
- caption: Figure 1.6. A kernel module is built for one kernel, so a kernel update without a matching module leaves the GPU unavailable.

### ch01-fig7-distro-lineage

- id: ch01-fig7-distro-lineage
- anchor: ### 6.1 The Red Hat, Fedora, CentOS, and Amazon Linux branch
- technical point: Fedora is the upstream, CentOS Stream the midstream, and RHEL the commercial release, while Rocky Linux and AlmaLinux are downstream rebuilds from RHEL source.
- labels: Fedora, CentOS Stream, RHEL, Rocky Linux, AlmaLinux, Upstream, Midstream, Downstream
- scene: Draw a river flowing left to right. Fedora sits at the source labelled Upstream, CentOS Stream in the middle labelled Midstream, and RHEL after it. Rocky Linux and AlmaLinux branch off at the mouth labelled Downstream. Use arrows so the flow direction is obvious.
- alt: A river-shaped diagram shows Fedora upstream, CentOS Stream midstream, RHEL, and Rocky Linux and AlmaLinux downstream.
- caption: Figure 1.7. The Red Hat family flows from upstream Fedora through CentOS Stream to RHEL, with Rocky Linux and AlmaLinux as downstream rebuilds.

## Chapter 2

Existing mermaid blocks (do not duplicate): "## 1. Terminal, shell, command: three different things" (terminal to shell to programs), "### What the shell does with a line" (six-step line processing), "## 6. Standard streams, redirection and pipes" (fd 0, 1, 2 flow). No existing images.

### ch02-fig1-word-splitting

- id: ch02-fig1-word-splitting
- anchor: ## 5. Expansion and quoting: the rules that explain "weird" behaviour
- technical point: An unquoted variable is split on whitespace into several arguments, while a double-quoted variable reaches the program as one argument.
- labels: my report.txt, Unquoted: two words, Quoted: one word, Program arguments
- scene: Show the variable file holding the value my report.txt as a single box. Two rows below show the result: the unquoted row splits the box into two separate pieces that feed into the program arguments as two items, and the quoted row keeps one whole piece with one item.
- alt: The same variable becomes two arguments when unquoted and one argument when double-quoted.
- caption: Figure 2.1. Quoting decides whether a variable with a space reaches a program as one argument or as two.

### ch02-fig2-redirection-order

- id: ch02-fig2-redirection-order
- anchor: ### 3. Errors vanish or appear in the wrong place: redirection order
- technical point: The shell applies redirections from left to right, so writing stderr to the file before or after stdout's redirection decides whether errors land in the file.
- labels: cmd > out 2>&1, cmd 2>&1 > out, stdout to file, stderr to file, stderr on terminal
- scene: Two side-by-side rows, one per command. In the first row, an arrow for stdout points to the file and a second arrow for stderr follows it into the same file. In the second row, stderr is pointed at the terminal first, and only stdout moves to the file, so stderr stays on the terminal.
- alt: With cmd greater-than out 2>&1, both streams reach the file; with the reversed order, stderr stays on the terminal.
- caption: Figure 2.2. Redirections are applied left to right, so the order of 2>&1 and the file target decides where errors go.

### ch02-fig3-env-inheritance

- id: ch02-fig3-env-inheritance
- anchor: ## 8. Environment variables, `PATH` and startup files
- technical point: A plain shell assignment stays inside the shell that made it, while an exported variable is copied into the environment that every child process inherits.
- labels: Shell variable, Environment variable, export, Child process, Inherited
- scene: Draw a parent shell box containing two variables. The one labelled Shell variable stays inside the box with a blocked arrow to the child; the one labelled Environment variable, created by export, has an arrow passing down into a Child process box where it is marked Inherited.
- alt: The exported variable is copied into the child process, but the plain shell variable is not.
- caption: Figure 2.3. Only exported variables are inherited by child processes; a plain assignment stays in the shell.

### ch02-fig4-startup-file-order

- id: ch02-fig4-startup-file-order
- anchor: ### Startup files: where the settings live
- technical point: A bash login shell reads only the first of .bash_profile, .bash_login, or .profile that it finds, while a non-interactive shell reads no startup file by default.
- labels: Login shell, .bash_profile, .bash_login, .profile, Only the first, Non-interactive shell
- scene: Draw a flow from a Login shell box down through /etc/profile into a decision among three file boxes, .bash_profile, .bash_login, and .profile, with a single chosen file highlighted and the other two greyed out labelled Only the first. A separate box on the side, Non-interactive shell, has no arrow to any file.
- alt: A bash login shell uses only the first matching profile file, and a non-interactive shell reads none by default.
- caption: Figure 2.4. A bash login shell reads only the first profile file it finds, and a non-interactive shell reads none of them by default.

### ch02-fig5-exit-code-signals

- id: ch02-fig5-exit-code-signals
- anchor: ### Exit codes you will meet in AI infrastructure
- technical point: A process killed by signal N ends with exit status 128 plus N, so 137 means SIGKILL and 143 means SIGTERM.
- labels: 128 + N, Exit 137, SIGKILL (9), Exit 143, SIGTERM (15), OOMKilled
- scene: Draw a horizontal number line from 128 to 143 with the formula 128 + N above it. Mark 137 with an arrow to SIGKILL (9) and 143 with an arrow to SIGTERM (15), and attach a small note labelled OOMKilled to the 137 marker.
- alt: A number line shows exit status 128 plus the signal number, with 137 pointing to SIGKILL and 143 pointing to SIGTERM.
- caption: Figure 2.5. An exit status above 128 means the process was killed by a signal, so the number after 128 names the signal.

### ch02-fig6-empty-variable-rm

- id: ch02-fig6-empty-variable-rm
- anchor: ### 2. `rm -rf "$DIR"/*` with an empty `DIR`
- technical point: With DIR empty, the pattern "$DIR"/* turns into /*, while the ${DIR:?} form makes the shell abort with an error instead.
- labels: DIR is empty, Expands to /*, ${DIR:?} aborts, Shell aborts with error
- scene: Show two rows. In the top row, a variable box labelled DIR is empty flows into the pattern "$DIR"/* which becomes /*, pointing at the root directory icon. In the bottom row, the same empty variable flows into ${DIR:?} and a stop sign labelled Shell aborts with error.
- alt: An empty DIR turns the rm pattern into the root directory, while the guarded form stops the shell with an error.
- caption: Figure 2.6. An empty variable can turn a destructive glob into the root directory, which the guarded ${DIR:?} form prevents.

## Chapter 3

Existing mermaid blocks (do not duplicate): "## 1. Paths: how you name a file" (directory tree), "## 4. Inodes: what a file really is" (directory table to inode to data blocks). Existing table compares hard and symbolic links, so the figures below show the mechanism, not the table.

### ch03-fig1-absolute-relative-path

- id: ch03-fig1-absolute-relative-path
- anchor: ## 1. Paths: how you name a file
- technical point: An absolute path starts at the root and means the same thing everywhere, while a relative path is read from the process's current working directory.
- labels: Absolute path, Relative path, Working directory, Same everywhere
- scene: Draw two rooms side by side, each with a desk and a file. Both people say "the file on my desk," and an arrow from each reads "relative path" from its own room, showing different files. Above the rooms, a single arrow labelled "absolute path" points from the root to one fixed file, which both rooms can reach.
- alt: Two people in different rooms each say "the file on my desk," which means different files, while an absolute path always names the same file.
- caption: Figure 3.1. An absolute path always names the same file, while a relative path depends on the working directory it is read from.

### ch03-fig2-hard-link-same-inode

- id: ch03-fig2-hard-link-same-inode
- anchor: ### Hard links
- technical point: A hard link is a second directory entry pointing at the same inode, so deleting one name leaves the data intact under the other.
- labels: a.txt, b.txt, Same inode, Link count 2, Data blocks
- scene: Show two name labels, a.txt and b.txt, each with an arrow converging on one shared inode box marked Same inode and Link count 2. Below the inode, a Data blocks box holds the contents. Add a small crossed-out arrow to a.txt with a note that b.txt still reaches the data.
- alt: Two file names point to one inode and its data, so removing one name leaves the file reachable through the other.
- caption: Figure 3.2. A hard link is a second name for the same inode, so the data survives while any name still points at it.

### ch03-fig3-symlink-dangling

- id: ch03-fig3-symlink-dangling
- anchor: ### Symbolic (soft) links
- technical point: A symbolic link stores a path rather than the data, so deleting its target leaves a dangling link, while a hard link to the same data still works.
- labels: Symbolic link, Target path, Target deleted, Dangling link, No such file
- scene: Draw two panels. In the left panel, a symbolic link box holds a target path arrow to a file that exists. In the right panel, the target file is removed, the arrow remains pointing at an empty spot, and the link is marked Dangling link with the message No such file or directory beside it.
- alt: A symbolic link that points at a deleted file is left pointing at nothing and is marked as dangling.
- caption: Figure 3.3. A symbolic link holds only a path, so when its target is deleted the link is left dangling.

### ch03-fig4-atomic-latest-swap

- id: ch03-fig4-atomic-latest-swap
- anchor: ### The atomic "latest" pattern
- technical point: Creating a new link under a temporary name and renaming it over latest switches readers from the old target to the new one in one atomic step, with no moment when the path is missing.
- labels: latest.tmp, mv -T, latest, Old target, New target, Atomic rename
- scene: Show three steps left to right. First, latest points to Old target and latest.tmp points to New target. Second, an arrow labelled mv -T and Atomic rename moves latest.tmp over latest. Third, latest now points to New target and latest.tmp is gone.
- alt: A temporary link is renamed over the latest link in one step, so readers switch from the old target to the new one without the path disappearing.
- caption: Figure 3.4. Renaming a new link over latest is atomic, so readers see either the old or the new target and never a missing path.

### ch03-fig5-inodes-vs-bytes

- id: ch03-fig5-inodes-vs-bytes
- anchor: ### 1. "No space left on device" but `df -h` shows free space
- technical point: A filesystem has two independent capacities, data bytes and inodes, so the inodes can run out while plenty of bytes remain free.
- labels: Data bytes, Inodes, Bytes free, Inodes used up, No space left
- scene: Draw two gauge bars side by side. The Data bytes gauge is mostly empty and labelled Bytes free. The Inodes gauge is full and labelled Inodes used up. A write arrow hits the Inodes gauge and is stamped No space left on device.
- alt: Two gauges show plenty of free bytes but a full inode table, which causes a no-space error on a disk that looks half empty.
- caption: Figure 3.5. Bytes and inodes are separate limits, so a full inode table can cause a no-space error while the disk still has free bytes.

### ch03-fig6-deleted-but-open

- id: ch03-fig6-deleted-but-open
- anchor: ### 4. The disk is full, but `du` cannot find the files: deleted but still open
- technical point: Deleting a file removes only its name, and the data is freed only when the link count reaches zero and no process still has the file open.
- labels: Name removed, Link count 0, Process still open, Data kept, Data freed
- scene: Draw a timeline of three boxes. Box one shows a file with a name and a process holding it open. Box two shows the name removed with the label Name removed, while the process still holds the data marked Process still open and Data kept. Box three shows the process closed and the data marked Data freed with Link count 0.
- alt: A deleted file keeps its data on disk while a process still has it open, and the space is freed only after the process closes it.
- caption: Figure 3.6. A deleted file's space is reclaimed only after its last link is gone and the last process holding it open has closed it.

## Chapter 4

Existing mermaid blocks (do not duplicate): "## 1. The model: lines of text flowing through small tools" (pipeline stages grep, cut/awk, sed/tr, sort, uniq -c). No existing images.

### ch04-fig1-bre-vs-ere

- id: ch04-fig1-bre-vs-ere
- anchor: ## 2. Regular expressions from scratch
- technical point: In basic regular expressions the characters + ? | () {} are literal text unless escaped, while in extended regular expressions (grep -E) they are operators by default.
- labels: BRE (default), ERE (grep -E), + is literal, + is operator, Backslash needed in BRE
- scene: Draw two columns. The left column, labelled BRE (default), shows the symbols + ? | with a padlock-like backslash marker and the note + is literal. The right column, labelled ERE (grep -E), shows the same symbols as active operator badges with the note + is operator.
- alt: Two side-by-side columns show that plus, question mark and pipe are plain text in basic regex but operators in extended regex.
- caption: Figure 4.1. Basic regex treats + ? | as plain characters, while grep -E turns them into operators.

### ch04-fig2-cut-vs-awk-spaces

- id: ch04-fig2-cut-vs-awk-spaces
- anchor: ### 6. Parsing a pretty table with `cut -d' '`
- technical point: cut uses one delimiter character at a time, so a run of spaces produces empty fields, while awk splits on runs of whitespace and gets the right columns.
- labels: cut -d' ', awk default, Runs of whitespace, Empty fields, Correct columns
- scene: Show one aligned table row with columns separated by wide runs of spaces. The top path splits each single space into its own slot, producing blank boxes labelled Empty fields under the label cut -d' '. The bottom path, labelled awk default, groups each run of whitespace into one separator and yields clean boxes labelled Correct columns.
- alt: With cut and a single space delimiter, aligned spaces produce empty fields, while awk's default splitting returns the correct columns.
- caption: Figure 4.2. cut treats every single space as a separator and so breaks on aligned tables, while awk groups runs of whitespace together.

### ch04-fig3-uniq-adjacent-only

- id: ch04-fig3-uniq-adjacent-only
- anchor: ### 2. `uniq -c` shows duplicates: input was not sorted
- technical point: uniq collapses only adjacent identical lines, so unsorted input leaves the same key in several separate groups and the counts come out wrong.
- labels: Unsorted input, Sorted input, Adjacent lines only, Key A, Key B, Counts combined
- scene: Draw two rows of stacked line blocks. The top row, labelled Unsorted input, alternates Key A and Key B blocks so the same key is split into several groups under the label Adjacent lines only. The bottom row, labelled Sorted input, puts all Key A blocks together and all Key B blocks together, so each key becomes one group with Counts combined.
- alt: Unsorted input splits the same key into several uniq groups, while sorted input puts equal keys next to each other so each key is counted once.
- caption: Figure 4.3. uniq only merges adjacent lines, so the same key must be sorted next to itself before uniq -c can count it correctly.

### ch04-fig4-greedy-star

- id: ch04-fig4-greedy-star
- anchor: ### 5. A regex that matches too much: unescaped dots, greedy stars
- technical point: The dot matches any single character and the star is greedy, so a pattern can take far more text than intended, and a literal dot needs a backslash.
- labels: Dot matches any, Greedy star, Takes too much, Escape the dot, Literal dot
- scene: Draw a single line of text with a marked start and end. Show the pattern .* as a long bracket that stretches as far right as it can, labelled Greedy star and Takes too much. Below it, show a second, shorter bracket for the escaped form labelled Escape the dot and Literal dot, stopping at the intended character.
- alt: A greedy dot-star pattern stretches across more text than intended, while an escaped literal dot matches only the dot itself.
- caption: Figure 4.4. A greedy star keeps matching as far as it can, and an unescaped dot matches any character, so patterns can grab too much text.

### ch04-fig5-xargs-nul-separator

- id: ch04-fig5-xargs-nul-separator
- anchor: ## 7. Fan-out: `find`, `xargs`, and parallelism
- technical point: find -print0 with xargs -0 separates names with the NUL byte, the only byte that cannot appear in a file name, so names with spaces or newlines stay intact.
- labels: NUL byte, find -print0, xargs -0, Spaces safe, Newlines safe
- scene: Show a list of three file-name boxes, one containing a space and one containing a newline, joined by separator markers. Above the list, a find -print0 box emits the markers labelled NUL byte, and an xargs -0 box on the right receives each name whole, tagged Spaces safe and Newlines safe.
- alt: File names with spaces or newlines pass through find and xargs intact when the NUL byte separates them.
- caption: Figure 4.5. The NUL byte is the one character that cannot appear in a file name, so find -print0 with xargs -0 keeps every name whole.

### ch04-fig6-locale-sort

- id: ch04-fig6-locale-sort
- anchor: ### 1. Different sort order or "wrong" results on two machines: locale
- technical point: A UTF-8 locale sorts by language rules so letters of different case can interleave, while LC_ALL=C gives plain byte order.
- labels: UTF-8 locale, LC_ALL=C, Language rules, Byte order, Letters interleave
- scene: Show the same set of letter tiles in two rows. The top row, labelled UTF-8 locale and Language rules, interleaves upper and lower case tiles so they mix. The bottom row, labelled LC_ALL=C and Byte order, groups the tiles in a fixed byte sequence, with the Letters interleave label on the first row only.
- alt: Under a UTF-8 locale letters of different case can interleave in sorted output, while LC_ALL=C sorts by plain byte order.
- caption: Figure 4.6. The same file can sort differently under a language-aware locale and under LC_ALL=C, which uses byte order.

## Chapter 5

Existing mermaid blocks (do not duplicate): "## 1. How SSH works" (sequence: host key, known_hosts, key exchange, user auth). No existing images.

### ch05-fig1-local-forward-tunnel

- id: ch05-fig1-local-forward-tunnel
- anchor: ### Port forwarding (tunnels)
- technical point: A local forward (-L) listens on a port on your machine and delivers the traffic through the server to a destination, so TensorBoard on gpu01 becomes reachable at localhost.
- labels: Your laptop, Port 6006, gpu01, TensorBoard, Local forward -L
- scene: Draw a laptop on the left with a port labelled Port 6006 on its side. A tunnel line runs from that port through a server box labelled gpu01 to a TensorBoard box on the far right. Label the tunnel as Local forward -L and make clear that the listening end is on the laptop.
- alt: A tunnel listens on a port on the laptop and carries traffic through gpu01 to the TensorBoard service.
- caption: Figure 5.1. A local forward listens on your machine and carries traffic through the server to the destination service.

### ch05-fig2-rsync-trailing-slash

- id: ch05-fig2-rsync-trailing-slash
- anchor: ### `rsync` properly
- technical point: A trailing slash on the source makes rsync copy the contents of src into dest, while no trailing slash copies the directory itself so that dest/src is created.
- labels: src/ to dest/, src to dest/, Contents copied, dest/src created, Trailing slash
- scene: Show two rows. The top row, labelled src/ to dest/ with the note Trailing slash, shows the contents of a src folder flowing into a dest folder. The bottom row, labelled src to dest/, shows the whole src folder placed inside dest, producing a nested dest/src folder.
- alt: With a trailing slash rsync copies the contents of the source folder into the destination, and without it rsync nests the source folder inside the destination.
- caption: Figure 5.2. The trailing slash on the rsync source decides whether the contents or the directory itself land in the destination.

### ch05-fig3-tmux-detach-reattach

- id: ch05-fig3-tmux-detach-reattach
- anchor: ## 5. Sessions that survive: `tmux`
- technical point: A tmux session keeps running on the server independently of your connection, so detaching or losing the SSH link leaves the work running and reattaching resumes it.
- labels: Laptop, Server, tmux session, Detach, Reattach
- scene: Draw a laptop connected to a server box containing a tmux session that keeps running. Show the connection line from the laptop being cut, with the session still active on the server. A second laptop arrow labelled Reattach connects back to the same session.
- alt: A tmux session keeps running on the server after the laptop disconnects, and a later connection can reattach to it.
- caption: Figure 5.3. A tmux session lives on the server, so the work continues after your connection drops and can be reattached later.

### ch05-fig4-proxyjump-bastion

- id: ch05-fig4-proxyjump-bastion
- anchor: ### The config file: `~/.ssh/config`
- technical point: ProxyJump routes a connection through the bastion to the final host, and the connection to that final host stays end-to-end encrypted.
- labels: Laptop, Bastion, gpu01, ProxyJump, End-to-end encrypted
- scene: Draw three boxes in a row: Laptop, Bastion, and gpu01. The arrow from Laptop to gpu01 passes through the Bastion box and is labelled ProxyJump. A lock symbol and the label End-to-end encrypted span the full path from Laptop to gpu01, so the bastion carries the traffic without reading it.
- alt: A laptop reaches gpu01 through the bastion with ProxyJump, and the encryption runs all the way to gpu01.
- caption: Figure 5.4. ProxyJump passes your connection through the bastion, which still leaves the path to the final host encrypted end to end.

### ch05-fig5-host-key-changed

- id: ch05-fig5-host-key-changed
- anchor: ### 2. `WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED`
- technical point: The client saves each server's host key in known_hosts and refuses a connection when the server presents a different key, so a changed key must be verified before the old entry is removed.
- labels: Host key, known_hosts, Key matches, Key changed, Verify out of band
- scene: Draw a two-branch decision flow. The server presents a Host key that is compared with an entry in known_hosts. The Key matches branch leads to a green connection. The Key changed branch leads to a warning and a box labelled Verify out of band before any removal of the old entry.
- alt: The client compares the server's host key with its saved entry and, when the key has changed, stops and asks for out-of-band verification.
- caption: Figure 5.5. The client compares a server's host key with its saved entry, and a changed key must be verified before the old entry is removed.

### ch05-fig6-agent-forwarding-exposure

- id: ch05-fig6-agent-forwarding-exposure
- anchor: ### 6. Agent forwarding exposes you, and keys leak
- technical point: With agent forwarding, anyone with root on the remote host can use your local agent's identity while you are connected.
- labels: Laptop, ssh-agent, Remote host, Root on remote, Forward only to trusted
- scene: Draw a laptop with an ssh-agent box connected to a Remote host box. An arrow labelled Root on remote, drawn in a different colour, points from the remote host back to the agent, showing that a root user there can reach the agent. A shield labelled Forward only to trusted sits on the link.
- alt: Agent forwarding links the laptop's agent to the remote host, where a root user can reach it while the connection is open.
- caption: Figure 5.6. Agent forwarding lets a root user on the remote host reach your local agent while you are connected.

## Chapter 6

Existing mermaid blocks (do not duplicate): "## 1. Users and groups: names for numbers" (kernel numbers vs user-space names via C library), "## 6. Shell startup files: the user environment" under "### Which file is read when (bash)" (bash startup decision tree). No existing images.

### ch06-fig1-names-vs-numbers

- id: ch06-fig1-names-vs-numbers
- anchor: ## 1. Users and groups: names for numbers
- technical point: The kernel knows only numeric UIDs, so two nodes that map alice to different numbers disagree about who owns her files.
- labels: alice, UID 1042, UID 1043, Same name, Owner mismatch
- scene: Draw two cluster node boxes side by side. Each has a name tag alice attached to a different number, UID 1042 on the left and UID 1043 on the right. A shared file box sits between them with an arrow from each node, and the mismatch is marked Owner mismatch. Add the label Same name, different number across the top.
- alt: Two nodes map the same name alice to different UIDs, so the same file appears owned by different users on each.
- caption: Figure 6.1. The kernel compares numbers, so the same username with different UIDs on two nodes means different owners for the same files.

### ch06-fig2-permission-triple-order

- id: ch06-fig2-permission-triple-order
- anchor: ## 3. File permissions: read, write, execute
- technical point: The kernel checks the owner triple first, then the group triple, then the other triple, and stops at the first match, so an owner with no bits is denied even when the group has full access.
- labels: Owner triple, Group triple, Other triple, First match wins, Owner denied
- scene: Draw a three-step flow from left to right with boxes Owner triple, Group triple, and Other triple. The check enters at the Owner triple, which is shown as --- and stops the flow with the label Owner denied, while a rwx group box beside it is shown unused with a label First match wins.
- alt: The kernel stops at the first matching triple, so an owner with no permission bits is denied even if the group has full access.
- caption: Figure 6.2. The kernel stops at the first matching triple, so the owner's bits can deny access even when the group's bits would allow it.

### ch06-fig3-setgid-shared-directory

- id: ch06-fig3-setgid-shared-directory
- anchor: ### A recipe: a safe shared project directory
- technical point: With the setgid bit on a directory, new files inherit the directory's group instead of the creator's primary group, and with umask 002 they are group-writable.
- labels: chmod 2770, projx group, New file, Inherits group, umask 002
- scene: Show two panels. In the left panel, a directory with no setgid bit creates a new file tagged with the creator's own group, shown in a different colour. In the right panel, the directory is labelled chmod 2770 and the new file is shown with the projx group inherited and a group-write mark labelled umask 002.
- alt: Without setgid a new file takes the creator's group, while with setgid on a directory it inherits the directory's projx group.
- caption: Figure 6.3. The setgid bit on a shared directory makes new files inherit its group, so team members can share them without extra steps.

### ch06-fig4-real-vs-effective-uid

- id: ch06-fig4-real-vs-effective-uid
- anchor: ### Real, effective, saved (and filesystem) IDs
- technical point: When a setuid program runs, its effective UID becomes the file owner's while the real UID stays with the user who started it.
- labels: Real UID, Effective UID, Saved UID, Started by, Permission checks
- scene: Draw a process box with three ID tags. The Real UID tag points back to the user who started the program, labelled Started by. The Effective UID tag points to the file owner and is labelled Permission checks, since it is the identity used for checks. A small Saved UID tag sits beside them as the stored ID to switch back to.
- alt: A setuid process carries the starter's real UID and the file owner's effective UID, which is the one used for permission checks.
- caption: Figure 6.4. A setuid program checks permissions with its effective UID, while its real UID still records who started it.

### ch06-fig5-sudo-env-reset

- id: ch06-fig5-sudo-env-reset
- anchor: ### `sudo`: administrative power with a trail
- technical point: sudo resets the environment, so an exported variable such as CUDA_VISIBLE_DEVICES does not reach the command unless the policy keeps it, for example through sudo -E or env_keep.
- labels: Your shell, CUDA_VISIBLE_DEVICES, sudo env_reset, Command under sudo, sudo -E
- scene: Draw your shell on the left with an exported variable box labelled CUDA_VISIBLE_DEVICES. An arrow to a sudo box labelled sudo env_reset stops, with the variable dropped, and the command under sudo box on the right receives no variable. A second, dashed path marked sudo -E carries the variable through to the command.
- alt: The exported variable is dropped by sudo's environment reset unless sudo -E or env_keep passes it through.
- caption: Figure 6.5. sudo resets the environment by default, so a variable set in your shell can vanish unless the policy keeps it.

### ch06-fig6-nss-lookup-chain

- id: ch06-fig6-nss-lookup-chain
- anchor: ### 8.5 How a program finds a user: the Name Service Switch (NSS)
- technical point: C library user lookups consult the sources listed in nsswitch.conf from left to right, with local files first, then systemd, then sss.
- labels: passwd: files systemd sss, files, systemd, sss (SSSD), getpwnam
- scene: Draw a horizontal chain of three source boxes in order: files, then systemd, then sss (SSSD). A program box labelled getpwnam sits on the left and sends its query into the first box. Arrows show the lookup moving rightward through the chain, and the top line reads passwd: files systemd sss.
- alt: A user lookup passes through the nsswitch sources in order, starting with local files and then systemd and sssd.
- caption: Figure 6.6. Programs look up users through the sources in nsswitch.conf, checked from left to right.

## Chapter 7

Existing mermaid blocks (do not duplicate): "### Two layers, and why they exist" (repositories, apt/dnf, dpkg/rpm, database, files), "### Installing from source" section "### The standard sequence" (unpack, configure, build, test, dry run, install), "## 4. Holding, pinning and reproducibility" (sequence: routine upgrade and DKMS), "### From source to executable" (preprocessor, compiler, linker, run). Figures below avoid those four.

### ch07-fig1-static-vs-shared-library

- id: ch07-fig1-static-vs-shared-library
- anchor: ### Static and shared libraries
- technical point: A static library's code is copied into each executable, so every program must be relinked for a fix, while a shared library is loaded at run time, so one update protects every program that uses it.
- labels: Static libfoo.a, Shared libfoo.so, Copied into program, Relink every program, Fix once
- scene: Draw two panels. In the static panel, libfoo.a code is shown being copied into three separate program boxes, with a note Relink every program. In the shared panel, one libfoo.so box is shown with arrows from three programs pointing to it, labelled Fix once.
- alt: Static libraries are copied into each program and need relinking, while one shared library file serves every program that loads it.
- caption: Figure 7.1. A static library is copied into each program, while a shared library is loaded at run time, so a single fix reaches every program.

### ch07-fig2-link-flags-undefined-reference

- id: ch07-fig2-link-flags-undefined-reference
- anchor: ### Linking against libraries
- technical point: An undefined reference means the linker found no definition for a function, and -l names the library that provides it while -L adds a directory to search.
- labels: badobject.o, initscr, -lcurses, -L directory, Undefined reference
- scene: Show a badobject.o box feeding into a linker box. An error tag labelled Undefined reference names the function initscr. A library box labelled -lcurses is added to the linker input, and an extra path arrow labelled -L directory points at the folder that holds the library.
- alt: The linker reports an undefined reference to initscr until the curses library is named with -l and its folder is given with -L.
- caption: Figure 7.2. An undefined reference is fixed by naming the library with -l and, when needed, its folder with -L.

### ch07-fig3-include-search-paths

- id: ch07-fig3-include-search-paths
- anchor: ### Headers, the preprocessor and include paths
- technical point: Angle brackets make the preprocessor search the system include directories, double quotes look next to the source file first, and -I adds an extra directory to search.
- labels: Angle brackets, Double quotes, Source directory, System include dirs, -I path
- scene: Draw a source file box at the centre with two search arrows. An angle-bracket arrow goes to a System include dirs box, and a double-quote arrow goes first to a Source directory box next to the file. A third arrow labelled -I path adds an extra folder to the search.
- alt: The preprocessor searches the source directory first for quoted includes, the system include directories for angle-bracket includes, and any folder added with -I.
- caption: Figure 7.3. Angle brackets, double quotes, and the -I option each control where the preprocessor looks for a header file.

### ch07-fig4-make-timestamp-rebuild

- id: ch07-fig4-make-timestamp-rebuild
- anchor: ### `make`
- technical point: make rebuilds only the targets that are older than their dependencies, so touching greet.c recompiles greet.o and then relinks hello.
- labels: greet.c, greet.o, hello, touch greet.c, Rebuild stale targets
- scene: Draw a chain of three file boxes in a row: greet.c, greet.o, and hello, linked by arrows showing dependency. Above the chain, a touch greet.c label starts the chain. A glowing marker shows greet.c as newer, and the next two boxes are highlighted with the label Rebuild stale targets, while unchanged boxes stay plain.
- alt: Touching the source file makes make rebuild the object file and then relink the program, since each target is now older than what it depends on.
- caption: Figure 7.4. make compares file timestamps, so changing one source file rebuilds only the chain of targets that depend on it.

### ch07-fig5-pkg-config-search-path

- id: ch07-fig5-pkg-config-search-path
- anchor: ### `pkg-config`: how builds find libraries
- technical point: pkg-config reads .pc files only from its own installation prefix by default, so a .pc file stored elsewhere stays invisible until PKG_CONFIG_PATH or a link makes it visible.
- labels: .pc file, Own prefix, lib/pkgconfig, PKG_CONFIG_PATH, Invisible by default
- scene: Draw a pkg-config box with a home area labelled Own prefix containing lib/pkgconfig, which is visible. A separate folder outside, holding a .pc file, is greyed out with the label Invisible by default. A dashed path from PKG_CONFIG_PATH reaches into that outside folder, making it visible.
- alt: pkg-config searches its own prefix by default, and a .pc file outside that prefix only becomes visible when PKG_CONFIG_PATH points to it.
- caption: Figure 7.5. pkg-config finds .pc files in its own prefix by default, so files stored elsewhere need PKG_CONFIG_PATH or a link.

### ch07-fig6-make-error-cascade

- id: ch07-fig6-make-error-cascade
- anchor: ### Troubleshooting builds
- technical point: GNU make calls itself recursively, so a deep compiler error is followed by a cascade of make[N] failures, and only the first error is the real cause.
- labels: First compiler error, make[3] Error 1, make[2], make[1], Read the first error
- scene: Draw a stack of error lines descending from top to bottom. The top line, marked First compiler error, is highlighted as the cause. Below it, the lines make[3] Error 1, make[2], make[1] and make appear in grey, labelled as unwinding, and a bracket on the side says Read the first error.
- alt: A deep compiler error is followed by a stack of make failures, and only the top-most error explains the failure.
- caption: Figure 7.6. In a recursive make build, the first compiler error is the cause, and the make[N] lines below it are only the unwinding.

## Chapter 8

Existing mermaid blocks (do not duplicate): "### The operating system in one picture" (user/kernel layers), "### Where processes come from: fork and exec" (fork/exec sequence), "### Process states" (state diagram R, S, D, T, Z). No existing images. Body read through "### Creating and changing cgroups" and section 10 start; the final "## How it fails" entries were not reviewed in full.

### ch08-fig1-signal-escalation

- id: ch08-fig1-signal-escalation
- anchor: ### Sending signals
- technical point: Send SIGTERM first so the program can clean up, and reserve SIGKILL for a program that does not respond, because SIGKILL gives it no chance to clean up.
- labels: SIGTERM (15), Clean up, SIGKILL (9), No cleanup, Escalate in order
- scene: Draw a two-step ladder labelled Escalate in order. The lower step is SIGTERM (15) with a note Clean up showing buffers flushed and a lock file removed. The higher step, reached only if the program does not respond, is SIGKILL (9) with the note No cleanup and a process vanishing.
- alt: A ladder shows SIGTERM as the first step, which allows cleanup, and SIGKILL as the last resort, which stops the process without cleanup.
- caption: Figure 8.1. Escalate from SIGTERM to SIGKILL, because SIGKILL ends the process immediately and gives it no chance to clean up.

### ch08-fig2-uncatchable-signals

- id: ch08-fig2-uncatchable-signals
- anchor: ### Stopping, continuing and processes that resist
- technical point: SIGKILL and SIGSTOP cannot be caught, ignored, or blocked, so the kernel acts on them directly, while other signals can run a handler the process installed.
- labels: SIGKILL (9), SIGSTOP (19), Cannot be caught, Handler runs, Default action
- scene: Draw a signal arrow aimed at a process box with a shield in the middle. Two signals, SIGKILL (9) and SIGSTOP (19), pass straight through the shield with the label Cannot be caught. A second arrow, labelled Handler runs, is stopped by the shield and bounced into a small handler function inside the process.
- alt: SIGKILL and SIGSTOP go straight to the kernel, while other signals can be intercepted by a handler the program installed.
- caption: Figure 8.2. SIGKILL and SIGSTOP bypass the process entirely, while other signals can be caught by a handler.

### ch08-fig3-hangup-and-job-remedies

- id: ch08-fig3-hangup-and-job-remedies
- anchor: ## 5. Shell job control
- technical point: Closing the terminal sends SIGHUP to the shell, which passes it to its jobs, so nohup, setsid, or disown protect a job from that signal.
- labels: Terminal closed, SIGHUP, Shell job, nohup or setsid, disown
- scene: Draw a terminal box that closes, sending a SIGHUP arrow down to a shell box and then to a job box, where the job is marked as terminated. Show three protective shields labelled nohup or setsid and disown that block the arrow before it reaches the job.
- alt: Closing the terminal sends a hangup signal through the shell to its jobs, and nohup, setsid, or disown can stop the job from receiving it.
- caption: Figure 8.3. Closing a terminal sends SIGHUP to the shell and its jobs, which is why nohup, setsid, or disown are used to protect a long job.

### ch08-fig4-zombie-orphan

- id: ch08-fig4-zombie-orphan
- anchor: ### Zombies and orphans
- technical point: An exited child stays a zombie until its parent calls wait, and when a parent exits first, its children are re-parented to PID 1, which must reap them.
- labels: Exited child, Zombie (Z), Parent calls wait(), Orphan, PID 1 adopts
- scene: Draw two small scenes. In the first, an exited child box is stuck in a Zombie (Z) state until a Parent calls wait() arrow removes it. In the second, a Parent box exits, and its child becomes an Orphan that is adopted by a PID 1 box, which reaps it.
- alt: A zombie stays until its parent calls wait, and an orphan is adopted by PID 1, which collects it.
- caption: Figure 8.4. A zombie waits for its parent to call wait, and an orphan is adopted by PID 1, which must reap it.

### ch08-fig5-load-average-counts

- id: ch08-fig5-load-average-counts
- anchor: ### The run queue and the load average
- technical point: On Linux the load average counts running and runnable tasks plus tasks in uninterruptible sleep, so a high load with idle CPUs means tasks are waiting for I/O.
- labels: Running (R), Runnable queue, Uninterruptible (D), Load average, Idle CPUs
- scene: Draw a bar of CPU cores that are mostly idle and marked Idle CPUs. Next to it, a queue of waiting tasks is shown, with a subset stamped Uninterruptible (D) and waiting on a disk icon. A gauge labelled Load average rises high because the D tasks are counted, even though the cores are not busy.
- alt: A high load average can come from tasks stuck in uninterruptible sleep, even when the CPU cores are idle.
- caption: Figure 8.5. The load average counts tasks in uninterruptible sleep as well as runnable ones, so a high value with idle CPUs points to waiting on I/O.

### ch08-fig6-pid1-exec-entrypoint

- id: ch08-fig6-pid1-exec-entrypoint
- anchor: ## 10. AI-infrastructure patterns
- technical point: A shell entrypoint that starts Python as a child does not forward SIGTERM, so ending the script with exec makes Python itself PID 1 and receive the signal.
- labels: Shell script, Python child, SIGTERM, exec python, Python as PID 1
- scene: Draw two container scenes side by side. On the left, a shell script is PID 1 with a Python child, and a SIGTERM arrow stops at the shell and never reaches Python. On the right, the label exec python shows Python replacing the shell as PID 1, with the SIGTERM arrow landing directly on it.
- alt: In the first container the shell swallows SIGTERM and Python never receives it, while with exec the Python process is PID 1 and gets the signal directly.
- caption: Figure 8.6. Ending a container entrypoint with exec makes the real program PID 1, so it receives SIGTERM directly.

## Chapter 9

Existing mermaid blocks (do not duplicate): "## 2. Quoting and expansion: the heart of shell" under "### ... ", the six-step expansion order (brace, tilde, parameter, word splitting, globbing, quote removal). No existing images. Full body read; "## How it fails" entries 1-6 read, the rest of that list not reviewed.

### ch09-fig1-run-vs-source

- id: ch09-fig1-run-vs-source
- anchor: ### Run, source, or exec
- technical point: A script run as a child process cannot change its parent's variables, while sourcing reads and executes the commands in the current shell, so the variables survive.
- labels: ./script.sh, source script.sh, Child process, Current shell, Variables survive
- scene: Draw two paths from a parent shell box. The ./script.sh path forks a Child process box that holds its variables, and an arrow back to the parent is crossed out with the label Variables do not return. The source script.sh path runs the commands directly inside the Current shell box, labelled Variables survive.
- alt: Running a script creates a child that cannot change the parent's variables, while sourcing runs the commands in the current shell so the variables remain.
- caption: Figure 9.1. A child script cannot change the variables of its parent, but a sourced script runs in the current shell and its variables remain.

### ch09-fig2-dollar-at-vs-star

- id: ch09-fig2-dollar-at-vs-star
- anchor: ### `$@` versus `$*`
- technical point: "$@" passes each argument as its own correctly quoted word, while "$*" joins all arguments into one string.
- labels: "$@" separate words, "$*" one word, [abc 123], [qwe], [abc 123 qwe]
- scene: Show the three arguments abc 123 and qwe as input tiles. The top row, labelled "$@" separate words, shows two output boxes, [abc 123] and [qwe]. The bottom row, labelled "$*" one word, shows a single merged box [abc 123 qwe].
- alt: With the quoted at-sign form each argument stays a separate word, while the quoted star form merges all arguments into one.
- caption: Figure 9.2. "$@" keeps each argument as its own word, while "$*" joins them into a single string.

### ch09-fig3-subshell-vs-braces

- id: ch09-fig3-subshell-vs-braces
- anchor: ### Grouping and subshells
- technical point: Commands in parentheses run in a subshell whose variable changes vanish when it ends, while commands in braces run in the current shell and keep their changes.
- labels: ( ) subshell, { } current shell, myvar=20 lost, myvar=30 kept, Changes vanish
- scene: Draw two boxes. The left box, labelled ( ) subshell, contains myvar=20 inside a dashed bubble that fades out with the label Changes vanish when it closes. The right box, labelled { } current shell, sets myvar=30, which stays visible after the box closes, with the label myvar=30 kept.
- alt: A subshell in parentheses drops its variable change when it ends, while a group in braces keeps the change in the current shell.
- caption: Figure 9.3. Parentheses start a subshell whose variable changes are discarded, while braces change the current shell.

### ch09-fig4-trap-exit-paths

- id: ch09-fig4-trap-exit-paths
- anchor: ### Cleanup with `trap`
- technical point: An EXIT trap runs on normal exits, error exits, and signal-driven exits, so cleanup in one place covers all of them, but SIGKILL cannot be trapped at all.
- labels: EXIT trap, Normal exit, Error exit, Signal exit, SIGKILL not trappable
- scene: Draw a central EXIT trap box with arrows coming in from three exit types: Normal exit, Error exit, and Signal exit. The cleanup step runs at the centre. A separate arrow from SIGKILL is shown bypassing the trap entirely and marked SIGKILL not trappable.
- alt: The EXIT trap is reached from normal, error, and signal exits, while SIGKILL skips it entirely.
- caption: Figure 9.4. A cleanup trap on EXIT catches normal, error, and signal exits, but nothing in user space can catch SIGKILL.

### ch09-fig5-flock-second-copy

- id: ch09-fig5-flock-second-copy
- anchor: ### Locking: only one copy at a time
- technical point: flock -n lets a second copy of a script exit at once while the first copy holds the lock, and the kernel releases the lock when the holding process dies.
- labels: First run, Second run, flock -n, already running, Lock released on exit
- scene: Draw two script run boxes stacked vertically. The First run box holds a padlock labelled flock -n. The Second run box tries to acquire the same lock, is refused, and shows the message already running and exits. A final note at the bottom says the lock is released when the first process exits.
- alt: A second copy of a script finds the lock held by the first copy, prints already running, and exits.
- caption: Figure 9.5. A second copy that cannot take the flock lock exits at once, and the lock frees itself when the first process ends.

### ch09-fig6-retry-backoff

- id: ch09-fig6-retry-backoff
- anchor: ### Retries and timeouts
- technical point: The retry helper doubles the delay after each failed attempt and gives up with an error after the set number of attempts.
- labels: Attempt n failed, Delay doubles, Wait then retry, Failed after n attempts, timeout 30
- scene: Draw a timeline of attempt boxes, each one ending in a red cross labelled Attempt n failed. Between attempts, the gap grows, with a bracket labelled Delay doubles. The last box ends in a stop sign with Failed after n attempts. A small clock tag beside the attempt boxes is labelled timeout 30.
- alt: Each failed attempt is followed by a longer wait, and after the final allowed attempt the helper stops with an error.
- caption: Figure 9.6. The retry helper doubles its wait after each failure and stops with an error after the last attempt.

## Chapter 10

Existing mermaid blocks (do not duplicate): "## 4. sysfs: the kernel's device model as a tree" (sysfs tree), "## 6. udev: from hardware events to device files" under "### The problem and the design" (udev uevent sequence). No existing images. Full body read; the "## How it fails" list (line 643 onward) was not reviewed in full.

### ch10-fig1-major-minor-numbers

- id: ch10-fig1-major-minor-numbers
- anchor: ### Types and numbers
- technical point: The kernel finds a device through its major number, which selects the driver, and its minor number, which selects the instance within that driver, so the file name itself does not identify the device.
- labels: Major number, Minor number, Driver, Instance in driver, Device file
- scene: Draw a device file in /dev as a labelled pointer on the left. An arrow carries two numbers, Major number and Minor number, into a building-shaped driver box labelled Driver, and a room inside it labelled Instance in driver. The pointer itself is tagged Device file to show it is only a label.
- alt: A device file points to a driver through its major number and to one instance inside that driver through its minor number.
- caption: Figure 10.1. A device file is a labelled pointer; the major number picks the driver and the minor number picks the instance inside it.

### ch10-fig2-sdb-sdc-swap

- id: ch10-fig2-sdb-sdc-swap
- anchor: ### Naming: why enumeration order is a trap
- technical point: Kernel names such as sdb follow driver discovery order, which can change between boots, so a fixed sdX name in fstab can mount the wrong disk while a UUID keeps pointing at the right one.
- labels: Before reboot, After reboot, sdb, sdc, UUID=
- scene: Draw two timelines of the same three disks. Before reboot, the failed-disk slot is shown with names sda, sdb and sdc. After reboot, the old sdc now appears as sdb, with a warning that an fstab entry for /dev/sdb mounts the wrong disk. A separate UUID= tag stays attached to the same physical disk in both timelines.
- alt: After a reboot a disk that was sdc becomes sdb, so a fixed name in fstab points at the wrong disk, while a UUID stays attached to the same disk.
- caption: Figure 10.2. Kernel device names follow discovery order and can change after a reboot, so persistent configuration should use a UUID instead.

### ch10-fig3-udev-rules-all-matched

- id: ch10-fig3-udev-rules-all-matched
- anchor: ### Rules
- technical point: udev processes rule files in lexical order and checks each event against every rule, without stopping at the first match, unless a rule uses GOTO.
- labels: 60-persistent-storage, 70-uaccess, 99-local, Lexical order, All rules checked
- scene: Draw three rule files stacked in order, labelled 60-persistent-storage, 70-uaccess, and 99-local, with an arrow labelled Lexical order running down them. A single event passes through all three boxes, each one marked with a tick under All rules checked, and a dashed bypass arrow labelled GOTO is shown as optional.
- alt: A device event is checked against every rule file in lexical order, so each matching rule can add to the result.
- caption: Figure 10.3. udev reads rules in lexical order and checks every rule against the event, so a later match can add to what an earlier rule set.

### ch10-fig4-storage-stack

- id: ch10-fig4-storage-stack
- anchor: ## 7. How storage devices fit together in the kernel (*How Linux Works* Section 3.6)
- technical point: Disks from USB, SATA, and SAS all appear as sd devices because the top class driver sd sends SCSI commands through the SCSI core to a host-adapter driver, with libata and usb-storage translating for SATA and USB.
- labels: sd (disks), SCSI core, libata, usb-storage, Host adapter driver
- scene: Draw a three-layer stack from top to bottom. The top layer shows sd (disks) with sr and st beside it. The middle layer is the SCSI core. The bottom layer shows host-adapter drivers, with libata under a SATA disk and usb-storage under a USB stick, both feeding into the SCSI core. Arrows show that every path leads to sd.
- alt: USB and SATA disks both reach the SCSI core through translators and appear as sd devices at the top layer.
- caption: Figure 10.4. The sd driver sees every disk through the SCSI core, and libata or usb-storage translate the SATA or USB hardware into SCSI commands.

### ch10-fig5-topo-link-ladder

- id: ch10-fig5-topo-link-ladder
- anchor: ## 8. Hardware inventory: PCI, USB, CPU, memory, firmware
- technical point: The nvidia-smi topo -m matrix ranks GPU and NIC paths from NV# over NVLink, the fastest, down through PIX, PXB, PHB and NODE to SYS across the inter-socket link, the slowest.
- labels: NV# NVLink, PIX, PXB, PHB, NODE, SYS, Fastest, Slowest
- scene: Draw a vertical ladder of six rungs from top to bottom: NV# NVLink, PIX, PXB, PHB, NODE, and SYS. The top rung is marked Fastest and the bottom rung is marked Slowest. Each rung has a short line drawn between two small GPU or NIC boxes, with the number of bridges or the link type shown by the rung's line style.
- alt: A ladder of connection types runs from NVLink as the fastest path down to SYS across the socket link as the slowest.
- caption: Figure 10.5. The nvidia-smi topology matrix ranks GPU and NIC paths from NVLink, the fastest, to SYS across sockets, the slowest.

### ch10-fig6-sysctl-persistence

- id: ch10-fig6-sysctl-persistence
- anchor: ### `/proc/sys` and `sysctl`
- technical point: A runtime write to a sysctl value is lost at reboot, while a file in /etc/sysctl.d is read at boot by systemd-sysctl and so persists.
- labels: Live value, Lost at reboot, /etc/sysctl.d, systemd-sysctl, Applied at boot
- scene: Draw two paths from a central kernel value box. The upper path, labelled Live value, goes through a sudo sysctl -w arrow into a reboot gate marked Lost at reboot. The lower path goes through a file box labelled /etc/sysctl.d, which passes a systemd-sysctl gate marked Applied at boot and re-sets the value after the reboot.
- alt: A live sysctl write disappears at reboot, while a file under /etc/sysctl.d is applied again at every boot.
- caption: Figure 10.6. A live sysctl change is lost at reboot, while a setting kept in /etc/sysctl.d is reapplied at every boot.

## Plan summary

- Chapters 1-10 done. Figure ids and captions are consecutive per chapter. Chapter 1 starts at Figure 1.2 because `ch01-fig1-office-building.jpg` already exists.
- Chapter 1 fig2-fig7, chapter 2 fig1-fig6, chapter 3 fig1-fig6, chapter 4 fig1-fig6, chapter 5 fig1-fig6, chapter 6 fig1-fig6, chapter 7 fig1-fig6, chapter 8 fig1-fig6, chapter 9 fig1-fig6, chapter 10 fig1-fig6.
