---
id: "c01-04"
title: "1.4 Text-processing essentials: grep, sed, awk, find, xargs, sort"
sidebar_label: "1.4 Text-processing essentials: grep, sed, awk, find, xargs, sort"
sidebar_position: 4
description: "The line-oriented toolbox: regular expressions, grep, sort, uniq, cut, tr, sed, awk, xargs, diff and jq, with recipes for logs, GPU metrics, Slurm and Kubernetes output."
status: "drafted"
tier: "0"
level: "B"
lab_venue: "GCP VM"
---

# 1.4 Text-processing essentials: grep, sed, awk, find, xargs, sort

**Level:** basics → intermediate · **Tier 0 (foundations)** · **Lab venue:** a small Ubuntu VM (GNU tools; Mac differences are listed in section 9) · **Status:** drafted, labs untested

## Why this matters for AI infrastructure

Infrastructure produces text: logs, `nvidia-smi` tables, `squeue` and `sinfo` listings, `dmesg`, `journalctl`, `kubectl` output, configuration files, CSV exports of metrics, and JSON from every API. When a 256-GPU job misbehaves at 3 a.m. you will not open a dashboard first; you will pull out the right ten lines from ten gigabytes of logs and count, group and compare them. The tools in this chapter are old, small and ubiquitous, and they are installed on every node you will ever log into, including the ones where you cannot install anything. Fluency here turns a half-hour investigation into a one-line pipeline, and it is the foundation for the shell scripts of chapter 1.9.

## Prerequisites and outcomes

You need chapter 1.2 (pipes, redirection, quoting). After this chapter you will be able to:

- explain the "text stream of lines" model and choose the right tool for a task;
- read and write regular expressions (basic and extended), and know when to avoid them;
- search with `grep`, extract with `cut`, `tr` and `awk`, transform with `sed`, order and group with `sort` and `uniq`, and build the standard "top N" and "count by key" pipelines;
- run commands over many files safely with `find` and `xargs`, including in parallel;
- compare files with `diff` and `comm`;
- query JSON with `jq` and use `kubectl -o jsonpath`/`custom-columns` and `nvidia-smi --query-gpu` for machine-readable output;
- apply a dozen ready recipes to GPU, Slurm, Kubernetes and training-log data;
- avoid seven classic pitfalls (locale, Mac versus GNU, uniq on unsorted data, spaces and newlines in names, and more).

## 1. The model: lines of text flowing through small tools

Most Unix text tools share one design: read **lines** from files or standard input, do one small thing to each, and write lines to standard output. Because every tool consumes and produces the same thing (plain text lines), you can connect them with pipes (chapter 1.2) into a pipeline that does something none of them can do alone. This is the "Unix philosophy": small sharp tools, composed.

A useful map for choosing:

| Task | Tool | Mnemonic |
|---|---|---|
| Keep only lines that match (or do not match) a pattern | `grep` | **filter** lines |
| Select columns / fields | `cut`, `awk` | **slice** columns |
| Replace or delete text, edit streams | `sed`, `tr` | **rewrite** text |
| Compute: sums, averages, counts, reformat, conditions on fields | `awk` | **calculate** |
| Order lines | `sort` | **order** |
| Collapse and count duplicate adjacent lines | `uniq` | **group** |
| First or last lines, count lines | `head`, `tail`, `wc` | **sample** |
| Glue files or columns | `paste`, `join`, `column` | **combine** |
| Compare two files or lists | `diff`, `comm`, `cmp` | **compare** |
| Run a command once per item or batch | `xargs`, `find -exec` | **fan out** |
| Query structured JSON | `jq` | **JSON-aware** |

A habit worth building immediately: **build pipelines incrementally.** Run the first command and look at the output; add the next stage; look again. Do not write a six-stage pipeline blind.

```mermaid
flowchart LR
  A["Source<br/>file, command, journalctl"] --> B["grep<br/>keep the lines you care about"]
  B --> C["cut / awk<br/>pick the fields"]
  C --> D["sed / tr<br/>clean and normalise"]
  D --> E["sort<br/>bring equal keys together"]
  E --> F["uniq -c<br/>count each group"]
  F --> G["sort -rn | head<br/>the top N"]
```

## 2. Regular expressions from scratch

A **regular expression** (regex) is a compact pattern that describes a set of strings. `grep`, `sed`, `awk`, `less`, `vim`, Prometheus, Python and nearly every tool you use understand some dialect of it. Learn the core once.

Characters that match themselves: letters, digits, spaces. Characters with special meaning (**metacharacters**):

| Pattern | Matches |
|---|---|
| `.` | any single character |
| `*` | zero or more of the preceding item |
| `+` | one or more of the preceding item (extended regex) |
| `?` | zero or one of the preceding item (extended regex) |
| `^` | the start of the line |
| `$` | the end of the line |
| `[abc]`, `[a-z]`, `[0-9]` | any one character from the set or range |
| `[^abc]` | any one character **not** in the set |
| the pipe character (`\|` in table cells), written with a leading backslash in basic regex and plain in extended | alternation: this or that (for example `error` or `fail`) |
| `( )` | grouping and capture |
| `{n,m}` | between n and m repetitions |
| `\.` | a literal dot (a backslash removes a special meaning) |
| `[[:digit:]]`, `[[:space:]]`, `[[:alpha:]]` | named character classes (locale-aware) |

Two dialects matter. **Basic regular expressions (BRE)** are the default in `grep` and `sed`, where `+ ? | ( ) { }` are *literal* unless preceded by a backslash. **Extended regular expressions (ERE)** treat them as operators directly; turn them on with `grep -E` (or `egrep`) and `sed -E` (`awk` already uses ERE). **Use `-E`** unless you have a reason not to; it is easier to read. GNU `grep -P` enables Perl-compatible expressions (lookaheads, `\d`), but it is a GNU extension that macOS `grep` does not provide.

Examples, in words and then as patterns:

- a line that starts with a timestamp like `2026-10-23`: `^[0-9]{4}-[0-9]{2}-[0-9]{2}`
- the word `ERROR` or `FATAL`: `ERROR|FATAL`
- an IPv4-looking address: `([0-9]{1,3}\.){3}[0-9]{1,3}` (a rough match: it also accepts 999)
- a line that is empty or only spaces: `^[[:space:]]*$`
- `step=` followed by digits: `step=[0-9]+`

Important habits: **quote regexes with single quotes** so the shell does not interpret `*`, `$`, `|` or `(`; remember that `.` matches *any* character, so use `\.` or `grep -F` (fixed string) when you mean a literal dot; and remember that regex is greedy (`.*` takes as much as it can). A tiny interactive practice: `echo "step=120 loss=0.43" | grep -oE 'loss=[0-9.]+'` prints just the match.

## 3. `grep`: filter lines

`grep PATTERN [file...]` prints lines that match. Without files it reads standard input, which is why it sits naturally in pipelines. Options you will use constantly:

| Option | Meaning |
|---|---|
| `-i` | ignore case |
| `-v` | invert: lines that do **not** match |
| `-n` | show line numbers |
| `-c` | count matching lines |
| `-l` / `-L` | list names of files that do / do not match |
| `-o` | print only the matched part |
| `-w` | match whole words |
| `-x` | match whole lines |
| `-A n`, `-B n`, `-C n` | n lines of context After, Before, or around each match |
| `-r`, `-R` | recurse into directories (`--include='*.py'`, `--exclude-dir=.git`) |
| `-E` | extended regex |
| `-F` | fixed string (no regex; fast, safe for literals) |
| `-q` | quiet: only set the exit status (0 match, 1 none, 2 error), great in `if` tests |
| `-s` | suppress errors about unreadable files |

```bash
grep -n "ERROR" train.log                        # errors with line numbers
grep -c "ERROR" train.log                        # how many
grep -iE "nccl|timeout" train.log | head         # case-insensitive, either word
grep -C 3 "Xid" <(dmesg -T)                      # three lines around each GPU fault
grep -rn --include='*.yaml' "nvidia.com/gpu" .   # which manifests request GPUs
grep -v '^#' /etc/slurm/slurm.conf | grep -v '^$'   # a config without comments and blank lines
if grep -q "OOM" job.out; then echo "ran out of memory"; fi
```

The comment-stripping idiom in the fifth example is worth memorising: reading a config file without its noise.

## 4. Slicing, ordering and counting: `cut`, `tr`, `sort`, `uniq`, `wc`, `head`, `tail`

**`cut`** extracts fields by position or by a one-character delimiter:

```bash
cut -d: -f1,3 /etc/passwd          # username and UID (fields 1 and 3, colon-separated)
cut -c1-10 file                    # first ten characters of each line
```

`cut` uses a *single* delimiter character, so it fails on text aligned with runs of spaces; use `awk` for that (section 6).

**`tr`** translates or deletes single characters from stdin:

```bash
tr 'a-z' 'A-Z' < file              # upper-case
tr -d '\r' < crlf.txt > lf.txt     # delete carriage returns (Windows line endings)
tr -s ' ' < table.txt              # squeeze runs of spaces to one
tr ':' '\n' <<< "$PATH"            # one PATH entry per line
```

**`sort`** orders lines. By default it compares as text in the current locale; use numeric and key options for real data:

| Option | Meaning |
|---|---|
| `-n` | numeric order (so 9 sorts before 10) |
| `-h` | human-readable numbers (`2K 1M 3G`) |
| `-r` | reverse |
| `-k N` | sort by field N (`-k2,2` limits the key to exactly field 2) |
| `-t C` | field separator character |
| `-u` | unique: drop duplicates |
| `-V` | version order (`1.9` before `1.10`) |
| `-s` | stable sort |

**`uniq`** collapses *adjacent* identical lines. Because "adjacent" is the key word, it almost always follows a `sort`. `uniq -c` prefixes each line with its count, `uniq -d` shows only duplicated lines, `uniq -u` only lines that occur once.

**`wc -l`** counts lines (`-w` words, `-c` bytes). **`head -n N`** and **`tail -n N`** show the first or last N lines; `tail -f` follows a file as it grows, and **`tail -F`** also follows it across log rotation (which replaces the file), the right choice for logs.

### The two pipelines you will write a thousand times

```bash
# 1. Count by key, most frequent first
cat file | cut -d' ' -f1 | sort | uniq -c | sort -rn | head -10

# 2. The biggest things first (sizes in human form)
du -sh * | sort -rh | head -10
```

The first reads: extract the key, **sort so equal keys are adjacent**, count adjacent duplicates, sort by the count, show the top ten. Understanding why each stage is there (and why `uniq` needs the first `sort`) is the whole skill.

### Reading long output: `less`, and a few one-line improvements

`less` is the pager you will use all day: it shows a file or a stream one screen at a time and lets you move both ways without loading everything first. Keys: space (or `f`) forward one screen, `b` back one screen, `/word` search forward and `?word` search backward, `n` next match (`N` previous), `g` and `G` first and last line, `F` follow the end of a growing file (like `tail -f`; Ctrl-C to stop following), `q` quit. Useful options: `-S` do not wrap long lines (essential for wide tables such as `ps` and `nvidia-smi`), `-R` pass colour codes through (so coloured `grep`/`ls` output stays readable), `-F` quit immediately if the whole input fits on one screen, `-N` show line numbers (and `-n` hide them), and `-f` force-open a file that looks binary. A good habit is putting your favourites in the `LESS` environment variable (for example `export LESS='-FRSX'`). `less` is the improved descendant of `more`; on a stripped-down system that lacks it, `more` works. The classic use is a pipeline ending in a pager: `grep ie /usr/share/dict/words | less`.

Three small improvements worth adopting: **`sort -u file`** does what `sort file | uniq` does (unique sorted lines) in one step; **`grep -E`** lets you write `a+bc|xy?z(qwe){1,4}` instead of the backslash-ridden basic form `a\+bc\|xy\?z\(qwe\)\{1,4\}`; and **`tail -n +N file`** prints from line N to the end (for example `tail -n +2 data.csv` skips a header line), while `head -5 file` is a shorthand for the first five lines. `diff` has a default human-readable format, but programmers send `diff -u` (unified format) to each other because tools such as `patch` and code-review systems understand it.

### Combining: `paste`, `join`, `column`, `tee`

`paste a b` puts files side by side line by line; `join` merges two sorted files on a common field like a tiny database join; `column -t` aligns whitespace-separated text into a readable table (`mount | column -t`); `tee` (chapter 1.2) copies a stream to a file and onward.

## 5. `sed`: edit a stream

`sed` (stream editor) applies editing commands to each input line. Its most used command is **substitute**:

```bash
sed 's/old/new/' file        # replace the first match on each line
sed 's/old/new/g' file       # replace all matches on each line
sed -E 's/step=([0-9]+)/STEP:\1/' file     # \1 refers to the first capture group
sed 's|/usr/local|/opt|g' file             # use another delimiter when the text contains /
```

Other commands: `d` deletes lines, `p` prints, `i`/`a` insert and append text, `y` transliterates. **Addresses** limit where a command applies:

```bash
sed -n '10,20p' file          # print only lines 10 to 20 (-n turns off automatic printing)
sed '1d' file                 # delete the first line (header)
sed '/^#/d' file              # delete comment lines
sed '/\[main\]/,/^\[/ s/debug=1/debug=0/' file    # change inside a section only
```

By default `sed` writes to standard output and **does not modify the file**. `sed -i` edits in place: **`sed -i 's/a/b/' file` on GNU/Linux but `sed -i '' 's/a/b/' file` on macOS**, a classic portability trap (section 9). Use `sed -i.bak` to keep a backup. Test the substitution without `-i` first and `diff` the result.

Use `sed` for quick stream edits and simple one-line substitutions. For anything with multiple steps or logic, use `awk`, a script, or a proper parser, and for structured formats (JSON, YAML) never use regex; use `jq` or `yq` (section 8).

## 6. `awk`: the Swiss army knife for columns

`awk` is a tiny programming language built for line-and-field data. Its basic form is **`awk 'PATTERN { ACTION }' file`**. For every input line, awk splits it into **fields** (by default on runs of whitespace), available as `$1`, `$2`, ..., with `$0` the whole line and `NF` the number of fields; `NR` is the current line number. If the PATTERN is true, the ACTION runs.

```bash
awk '{ print $1, $3 }' file                  # fields 1 and 3
awk -F: '{ print $1 }' /etc/passwd           # use ':' as the field separator
awk '$3 > 90' file                           # lines whose third field is greater than 90
awk '/ERROR/ { n++ } END { print n+0 }' f    # count ERROR lines (END runs after the last line)
awk 'NR==1 || /ERROR/' file                  # header plus error lines
awk 'BEGIN { OFS="," } { print $1, $2 }' f   # BEGIN runs first; OFS is the output separator
```

The real power is **variables and associative arrays**, which let you aggregate without `sort | uniq`:

```bash
# sum and average of column 3
awk '{ s += $3 } END { print s, s/NR }' file

# count occurrences of each value in column 1 (a "group by")
awk '{ c[$1]++ } END { for (k in c) print c[k], k }' file | sort -rn

# max of column 3 and the line where it occurred
awk 'NR==1 || $3 > m { m=$3; line=$0 } END { print m, line }' file

# average per key
awk '{ s[$1]+=$2; n[$1]++ } END { for (k in s) printf "%s %.2f\n", k, s[k]/n[k] }' file
```

Two points that save time. First, because awk separates fields on *runs* of whitespace, it parses the aligned output of `ps`, `df`, `nvidia-smi` tables and `squeue` correctly where `cut -d' '` fails. Second, remember that **awk treats a field as a number when it looks like one**; if a field contains units like `120MiB`, strip them first (`sub(/MiB/,"",$3)`), or request machine-readable output from the tool, as in section 8.

## 7. Fan-out: `find`, `xargs`, and parallelism

Many tasks mean "do X to each of these N things": compress every old log, change owner on all files, check every node. `find` (chapter 1.3) produces the list; **`xargs`** turns lines on its standard input into arguments of another command.

```bash
find /data -name '*.tmp' -print0 | xargs -0 rm -f        # safe with spaces and newlines in names
find . -name '*.log' -print0 | xargs -0 -n 50 gzip        # at most 50 files per gzip call
printf '%s\n' gpu01 gpu02 gpu03 | xargs -I{} ssh {} nvidia-smi -L   # one call per host, {} is the item
find . -name '*.png' -print0 | xargs -0 -P 8 -n 20 ./resize.sh      # 8 parallel workers
```

Key options: **`-0`** pairs with `find -print0` and separates items with the NUL byte, the only byte that cannot appear in a file name, so names with spaces or newlines are handled correctly; **`-n N`** batches N items per invocation; **`-I{}`** runs the command once per item, substituting `{}`; **`-P N`** runs N invocations in parallel (use it for I/O or network fan-out, never blindly for CPU-heavy work on a shared login node); **`-r`** (GNU) skips running the command when the input is empty (otherwise `xargs rm` with no input would run `rm` with no arguments). `find ... -exec cmd {} +` is an alternative that batches arguments without a pipe (chapter 1.3). For larger fan-out jobs, GNU `parallel` is a more featureful relative of `xargs -P`.

## 8. Comparing files and handling structured text

### `diff`, `comm`, `cmp`

```bash
diff -u old.conf new.conf          # unified diff: the format used by patches and code review
diff -r dirA dirB                  # recurse through two directory trees
diff <(sort a.txt) <(sort b.txt)   # compare the sorted output of two commands (process substitution)
comm -12 <(sort a) <(sort b)       # lines present in BOTH sorted files (-1/-2/-3 hide columns)
cmp -l file1 file2 | head          # first differing bytes (for binary files)
sha256sum model.bin                # compare by checksum when files are huge
```

`diff -u` marks removed lines with `-` and added lines with `+`; `patch -p1 < change.diff` applies such a diff to a source tree. Before editing any production config, copy it and `diff -u` the result: it is the cheapest change review there is.

### JSON and friends: use a parser, not regex

Modern tools emit JSON. Parsing it with `grep` and `sed` works until it does not. **`jq`** is `sed` for JSON:

```bash
echo '{"gpu":[{"id":0,"mem":1200},{"id":1,"mem":81000}]}' | jq '.gpu[] | select(.mem>80000) | .id'
kubectl get pods -A -o json | jq -r '.items[] | select(.status.phase!="Running") | [.metadata.namespace,.metadata.name,.status.phase] | @tsv'
curl -s http://prometheus:9090/api/v1/query?query=up | jq -r '.data.result[] | [.metric.instance,.value[1]] | @tsv'
```

Useful pieces: `.field`, `.[]` (iterate an array), `select(condition)`, `map(...)`, `length`, `-r` (raw strings, no quotes), `@tsv`/`@csv` to produce tables, `-e` to set the exit status from the result. For YAML, `yq` plays the same role. For Kubernetes specifically, `kubectl` has built-in extractors that avoid `jq` in simple cases:

```bash
kubectl get nodes -o custom-columns=NAME:.metadata.name,GPUS:.status.allocatable.nvidia\\.com/gpu
kubectl get pod mypod -o jsonpath='{.status.containerStatuses[0].lastState.terminated.exitCode}'
```

### Ask tools for machine-readable output first

Before parsing a pretty table, check whether the tool has a parseable mode:

```bash
nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total,temperature.gpu \
           --format=csv,noheader,nounits                      # one clean CSV line per GPU
nvidia-smi --query-compute-apps=pid,used_memory --format=csv  # processes using the GPUs
squeue -h -o "%u %T"                                           # Slurm: user and state, no header
sinfo -N -h -o "%N %T"                                         # Slurm: node and state
lsblk -J                                                       # block devices as JSON
ip -j addr                                                     # network addresses as JSON
df -P                                                          # POSIX layout, one line per filesystem
```

(Option names such as `-h` and `-o` vary slightly between tools and versions; confirm in the man page of the tool you are using.)

## 9. Portability, locale and other traps

**GNU versus BSD.** Linux servers carry the GNU versions of these tools; macOS carries the BSD versions, which differ in details that break scripts: `sed -i` needs an empty suffix argument on macOS; `grep -P` and some `-o` behaviours are absent; `sort`, `date`, `xargs -r`, `readlink -f`, and some `awk` features differ. For this book use a Linux machine for labs. When a script must run on both, stick to POSIX options, test on both, or install GNU tools on the Mac (`brew install gnu-sed grep coreutils findutils gawk`, which provide `gsed`, `ggrep` and so on).

**Locale.** The language and encoding settings (`LANG`, `LC_ALL`, chapter 1.2) affect sorting order, character classes (`[a-z]`), and speed. In a UTF-8 locale `sort` compares using language rules, so `a` and `B` may interleave; many scripts set **`LC_ALL=C`** in front of `sort`, `grep` and `awk` for plain byte order and, often, a large speed-up: `LC_ALL=C sort file`. When two machines give different sort orders for the same file, locale is the first suspect.

**Line endings and encodings.** Files from Windows have `\r\n` line endings (strip with `tr -d '\r'`); files can be in encodings other than UTF-8 (`file -i name`, `iconv`). `grep` may report `Binary file matches` for files containing NUL bytes; use `-a` to treat them as text.

**Large files.** These tools stream, so a 50 GB log does not need 50 GB of memory, but `sort` of a huge file spills to temporary disk (`TMPDIR`, `-T`) and `awk` arrays grow with the number of keys. Filter early (`grep` first) and use `head` only after the expensive part, remembering that a pipeline stops early when a downstream `head` closes (the upstream process receives SIGPIPE).

## 10. Recipes for AI and HPC work

Each recipe is a pattern you will adapt. Run the first stage alone to see the data before trusting the pipeline.

```bash
# 1. GPUs above 90 percent utilisation right now
nvidia-smi --query-gpu=index,utilization.gpu --format=csv,noheader,nounits | awk -F', ' '$2>90 {print "GPU", $1, $2"%"}'

# 2. Total GPU memory in use across the node (MiB)
nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | awk '{s+=$1} END {print s " MiB"}'

# 3. Who has the most jobs queued in Slurm
squeue -h -t PD -o %u | sort | uniq -c | sort -rn | head

# 4. How many nodes in each Slurm state
sinfo -N -h -o "%T" | sort | uniq -c

# 5. Kernel messages about GPU faults, with timestamps, last 20
dmesg -T | grep -iE "xid|nvrm" | tail -20

# 6. The ten largest files under a directory (human readable)
find /data -xdev -type f -printf '%s %p\n' | sort -rn | head -10 | awk '{printf "%.1f GiB %s\n", $1/2^30, $2}'

# 7. Distinct error messages in a log, ranked, with ids and numbers masked
grep -i error train.log | sed -E 's/[0-9]+/N/g' | sort | uniq -c | sort -rn | head

# 8. Mean tokens per second from a training log with lines like "... tokens_per_sec=94211 ..."
grep -oE 'tokens_per_sec=[0-9]+' train.log | cut -d= -f2 | awk '{s+=$1} END {print s/NR}'

# 9. Pods that are not Running, across the cluster
kubectl get pods -A --no-headers | awk '$4!="Running" && $4!="Completed" {print $1, $2, $4}'

# 10. Which hosts differ in kernel version (compare outputs collected into files)
for h in gpu01 gpu02 gpu03; do ssh $h uname -r | sed "s/^/$h /"; done | sort -k2 | uniq -f1 -c
```

## How it fails

### 1. Different sort order or "wrong" results on two machines: locale
**Symptom:** the same pipeline gives a different order or different matches on two hosts; ranges like `[a-z]` behave oddly. **Cause:** different `LANG` or `LC_ALL`. **Diagnose:** `locale`, `echo $LC_ALL`. **Fix:** set `LC_ALL=C` for byte order in scripts, or the same explicit UTF-8 locale everywhere.

### 2. `uniq -c` shows duplicates: input was not sorted
**Symptom:** the same key appears several times with small counts. **Cause:** `uniq` only collapses adjacent lines. **Fix:** `sort | uniq -c`, or count with `awk '{c[$1]++}'`.

### 3. The `sed -i` that works on the laptop and fails on the server (or the reverse)
**Symptom:** `sed: 1: "file": extra characters at the end of d command` on macOS, or a stray backup file named `file''` on Linux. **Cause:** GNU versus BSD syntax for `-i`. **Fix:** use `sed -i.bak` (valid on both) and delete the backup, install GNU sed, or avoid in-place editing in portable scripts (write to a temp file and `mv`).

### 4. Files with spaces or newlines in names break an `xargs` pipeline
**Symptom:** `xargs rm` complains about non-existent half-names. **Cause:** plain `xargs` splits on whitespace. **Fix:** `find ... -print0 | xargs -0 ...`.

### 5. A regex that matches too much: unescaped dots, greedy stars
**Symptom:** `grep 10.0.0.1` also matches `10.0.0.100` and `10x0y0z1`. **Cause:** `.` matches any character, and there is no word boundary. **Fix:** `grep -F`, escape dots (`10\.0\.0\.1`), anchor or use `-w`: `grep -wF 10.0.0.1`.

### 6. Parsing a pretty table with `cut -d' '`
**Symptom:** columns come out empty or shifted. **Cause:** aligned tables use runs of spaces; `cut` takes a single space as the delimiter. **Fix:** `awk '{print $2}'`, or better, ask the tool for CSV or JSON.

### 7. Parsing JSON or YAML with regex
**Symptom:** it works for a month, then a field order change or a value containing a quote breaks it silently. **Cause:** regex does not understand nesting or escaping. **Fix:** `jq` or `yq`.

## Hands-on lab (a GCP Ubuntu VM; untested)

**Part A: build a realistic dataset.** Create a synthetic training log and a GPU metrics CSV so everything below has data (no cluster needed):

```bash
mkdir -p ~/lab/text && cd ~/lab/text
awk 'BEGIN{srand(42); for(i=1;i<=2000;i++){loss=2.5/(1+i/200)+rand()*0.05;
 printf "2026-10-23T10:%02d:%02d step=%d loss=%.4f tokens_per_sec=%d gpu=%d\n", int(i/60)%60, i%60, i, loss, 90000+int(rand()*10000), i%8}}' > train.log
printf '%s\n' "2026-10-23T10:20:01 ERROR NCCL timeout on rank 3" "2026-10-23T10:21:44 WARN loss spike at step 1300" \
  "2026-10-23T10:31:09 ERROR NCCL timeout on rank 5" "2026-10-23T10:40:00 ERROR CUDA out of memory on gpu=2" >> train.log
awk 'BEGIN{srand(7); print "index,name,util,mem_used,mem_total,temp"; for(g=0;g<8;g++) printf "%d,NVIDIA H100,%d,%d,81559,%d\n", g, int(rand()*100), 1000+int(rand()*79000), 40+int(rand()*40)}' > gpus.csv
wc -l train.log gpus.csv; head -3 train.log; head -3 gpus.csv
```

**Part B: grep.** (1) Count error lines, warning lines and all non-training lines (those without `step=`). (2) Show each ERROR with two lines of context. (3) List only the distinct error messages after masking numbers with `sed` (recipe 7). (4) Use `grep -q` in an `if` to print "found OOM" or "no OOM".

**Part C: slicing and counting.** (5) Extract the `gpu=` value of every training line and count how many lines each GPU produced (`sort | uniq -c`). Are they equal? (6) Using `cut` and `tr`, extract the `loss` values to a file. (7) Find the line with the smallest loss with `sort -t= -k3 -n` (work out which `-t` and `-k` values are right) and then again with `awk`.

**Part D: awk.** (8) Compute the mean and the maximum of `tokens_per_sec`. (9) Print the mean loss per block of 500 steps (a "group by" using `int(step/500)`). (10) From `gpus.csv` print the GPUs whose utilisation is above 80 and temperature above 60, as a nicely formatted table with `column -t`. (11) Compute total memory used as a percentage of total.

**Part E: sed.** (12) Replace `loss=` with `L=` in a copy and show the diff with `diff -u`. (13) Print lines 100 to 105 only. (14) Remove the header of `gpus.csv` with `sed '1d'`. (15) Create a copy of `/etc/ssh/sshd_config` (do not edit the original), disable a setting with `sed -i.bak`, and show the change with `diff -u`.

**Part F: find and xargs.** (16) Create 1000 empty files, some with spaces in the names, in a directory; remove them first with a naive `ls | xargs rm` and watch it fail, then do it correctly with `-print0`. (17) Compress them with `xargs -P 4`.

**Part G: JSON.** (18) Install `jq` (`sudo apt-get install -y jq`) and process `ip -j addr` to print each interface name with its first IPv4 address. (19) Use `jq` to pick two fields out of a JSON file you write by hand.

**Part H: traps.** (20) Make a file with mixed-case words and show how `sort` and `LC_ALL=C sort` order them differently. (21) Demonstrate the `uniq` without `sort` pitfall. (22) Create a CRLF file and show that `grep '^ERROR$'` fails on it, then fix with `tr -d '\r'`.

## Checkpoint questions

1. What shared property of Unix text tools allows pipelines?
2. Why do we sort before `uniq -c`? What happens without sorting?
3. Write a pipeline that prints the five most common values of the third space-separated column of a file.
4. What is the difference between BRE and ERE? Which option enables ERE in `grep` and `sed`?
5. What does `grep -v '^#'` do? What does `grep -c` count?
6. What is the difference between `grep -F` and plain `grep`, and when do you prefer `-F`?
7. In `awk '{ s += $3 } END { print s/NR }'`, what do `END`, `NR` and `$3` mean?
8. Why does `awk` parse `ps` output correctly while `cut -d' '` often does not?
9. Why use `find ... -print0 | xargs -0` instead of `find ... | xargs`?
10. What does `xargs -P 8` do, and when is it a bad idea?
11. Why should you use `jq` instead of `grep` for JSON?
12. Give two different reasons the same `sort` can give different results on two machines.
13. What does `sed -i` do on GNU and on BSD/macOS, and how do you write a portable form?
14. `tail -f` versus `tail -F`: which should you use for logs and why?
15. How would you list Slurm nodes by state with counts using `sinfo`?

### Answers

1. They read lines of plain text from standard input and write lines of plain text to standard output, so any tool's output can be another's input.
2. `uniq` only compares adjacent lines. Sorting puts equal lines next to each other. Without sorting, the same value appears several times with partial counts.
3. `awk '{print $3}' file | sort | uniq -c | sort -rn | head -5`.
4. In BRE the characters `+ ? | ( ) { }` are literal unless backslash-escaped; in ERE they are operators. `grep -E` and `sed -E` (and `awk` natively) use ERE.
5. It prints the lines that do not begin with `#` (it removes comments). `-c` counts matching lines instead of printing them.
6. `-F` treats the pattern as a literal string, not a regex. Prefer it when searching for text containing special characters such as `.`, `*` or `[`, or for speed.
7. `$3` is the third field of the line; `NR` is the number of the current line (at END, the total number of lines); `END` runs its action after the last line is read. The program prints the mean of column 3.
8. `awk` splits fields on runs of whitespace by default; `cut` uses a single delimiter character, so multiple adjacent spaces create empty fields.
9. File names can contain spaces and newlines, which plain `xargs` would split; `-print0` and `-0` separate with the NUL byte, which cannot occur in a file name.
10. It runs up to eight invocations of the command at the same time. It is a bad idea for CPU-heavy work on a shared machine, for commands that are not safe to run concurrently, or when the target (a network filesystem, an API) cannot handle the load.
11. JSON has nesting, escaping and flexible whitespace; regex does not understand its structure and breaks on harmless formatting changes. `jq` parses it correctly.
12. Different locale settings (collation order) and different tool versions or implementations (GNU versus BSD).
13. It edits files in place. GNU: `sed -i 's/a/b/' f`; macOS/BSD: `sed -i '' 's/a/b/' f`. A portable form is `sed -i.bak 's/a/b/' f` followed by removing the backup, or write to a temporary file and `mv` it.
14. `tail -F`. It keeps following by name and reopens the file after log rotation, whereas `-f` follows the original file descriptor and goes silent after the file is rotated.
15. `sinfo -N -h -o "%T" | sort | uniq -c`.

## Sources and further reading

- Brian Ward, *How Linux Works*, 3rd ed., ch. 2 (grep, diff, head and tail, sort, pipes and redirection), used for the core command set; this chapter's regular-expression treatment, `sed`, `awk`, `xargs`, `jq` sections, recipes, failure modes and lab are original.
- Sergey Zhumatiy, *Supercomputers for Linux SysAdmins*, ch. 8 (shell tricks and tips for often-used commands).
- Man pages: `man grep`, `man 7 regex`, `man sed`, `man awk` (or `gawk`), `man sort`, `man xargs`, `man diff`, `man jq`, `man 3 locale`; the GNU `grep`, `sed`, `awk` and `coreutils` info manuals.
- Related chapters: 1.2 (pipes and redirection), 1.3 (`find`), 1.9 (scripting), 17.3 (logs with Loki), 15.14 and 17.4 (metrics).

*Notes for review:* the Slurm format specifiers (`%u`, `%T`, `%N`), `nvidia-smi` query field names and `kubectl` extractor syntax are stated from current usage and should be confirmed against the versions you run (`man squeue`, `nvidia-smi --help-query-gpu`). The macOS statements describe the stock BSD tools. All lab commands are **untested** and must be run on a Linux VM before this chapter moves to `reviewed`.
