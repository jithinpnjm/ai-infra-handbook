---
id: "c07-12"
title: "7.12 Automating Redfish with Python, Ansible and Go"
sidebar_label: "7.12 Automating Redfish with Python, Ansible and Go"
sidebar_position: 12
description: "How to automate Redfish for real: a careful Python client, the DMTF python-redfish library, Ansible with the uri module and the community.general redfish modules, Go with gofish, TLS with a lab certificate authority, and a fleet runner with retries, timeouts and failure handling that is tested against broken BMCs"
status: "drafted"
tier: "1b"
level: "A"
lab_venue: "GCP / GKE"
---

# 7.12 Automating Redfish with Python, Ansible and Go

| | |
|---|---|
| Level | Intermediate |
| Priority tier | 1 |
| Lab venue | Laptop |
| Part | Part 7: Redfish and BMC |
| Status | Drafted (`fleet_lab.py`: 14 checks pass over HTTPS mock; **untested** on live BMC) |

## Why this matters for AI infrastructure

With one server you can click in a web page. With 1,000 you need code, and code that touches BMCs must be careful: a bad retry loop can lock accounts, an unbounded loop can overload management switches, and a script that dies on the first failed host leaves half a fleet changed. This chapter shows the same few operations in three languages, then the rules that make any of them safe at scale.

## Prerequisites and outcomes

You need chapters 7.2 to 7.5 and basic Python (Part 3), Ansible (Part 4) and some Go. After this chapter you can:

- set up HTTPS with a lab certificate authority and verify certificates in your clients
- write a safe Redfish call in Python, Ansible and Go
- choose between the `uri` module and the Redfish modules in Ansible
- run a task on many BMCs with timeouts, retries, backoff and failure isolation
- test your automation against broken BMCs

## 1. First, TLS: stop using `-k`

Real BMCs use HTTPS. The mock now does too (`redfish_mock.py --tls CERT KEY`, TLS 1.2 or newer, as the spec requires). `tls_setup.py` makes a throw-away certificate authority (CA) and a server certificate for `127.0.0.1`:

```bash
python3 tls_setup.py /tmp/pki
python3 redfish_mock.py --port 8443 --tls /tmp/pki/server.pem /tmp/pki/server.key
```

I checked three behaviours with `curl`:

```text
curl --cacert /tmp/pki/ca.pem https://127.0.0.1:8443/redfish/v1/   -> 200
curl https://127.0.0.1:8443/redfish/v1/                            -> exit 60 (certificate not trusted)
curl -k https://127.0.0.1:8443/redfish/v1/                         -> 200 (no checking at all)
```

The second line is the safe default: the client does not trust a certificate that no known authority signed. The third works but would accept a fake BMC. My Python tools follow the same rule:

- by default the certificate is **verified** against the system store;
- `REDFISH_CA=/tmp/pki/ca.pem` adds your own CA;
- only `REDFISH_INSECURE=1` turns verification off, and then the tool prints a warning on every run.

For real fleets the point is to put one internal CA on all BMCs (chapter 7.4 and 7.15) and trust that CA in your automation, not to hand-disable checks.

## 2. Python

### 2.1 The client I used in all labs

`redfish_crawl.py` has a small standard-library client. Things it does that a quick script does not:

- logs in with a **session** and always logs out;
- sets a **timeout** on every request;
- **renews** the session once if it times out (a 401 while holding a token) and repeats the request;
- raises `LoginError` with the status code, so callers can tell a wrong password (401) from a busy BMC (503);
- verifies TLS unless you explicitly say otherwise.

### 2.2 The DMTF `redfish` library

DMTF publishes a Python library (`pip install redfish`, version 3.4.2 when I tested). The basic use:

```python
import redfish
c = redfish.redfish_client(base_url="https://<bmc>", username="admin", password="...",
                           default_prefix="/redfish/v1")
c.login(auth="session")
r = c.get("/redfish/v1/Systems/System_0")
print(r.status, r.dict["PowerState"])
c.post("/redfish/v1/Systems/System_0/Actions/ComputerSystem.Reset", body={"ResetType": "ForceOff"})
c.logout()
```

I ran this against the mock with `SSL_CERT_FILE=/tmp/pki/ca.pem` and it printed `200 On`, `200` and then `Off`. It handles sessions and gives you `.dict`. It does not decide retries, concurrency or discovery for you.

### 2.3 Rules for a Python Redfish script

1. **Discover**, do not hard-code (chapter 7.2). Use `rf_inventory.py` as a pattern.
2. **Timeouts everywhere.** A BMC that hangs must not freeze your whole run.
3. **Sessions, and logout in `finally`.**
4. **Check status and body** (chapter 7.3), including `@Message.ExtendedInfo` on a 200.
5. **Handle 202** with a task loop (chapter 7.5) and a time limit that ends in "unknown", not "success".
6. **Keep secrets out of code and logs** (chapter 7.4).
7. **Be idempotent:** read the current state first, change only if needed, verify afterwards.
8. **Dry run by default** for anything that changes state (my `rf_firmware.py update` and `rf_logs.py clear` do this).

## 3. Ansible

Ansible is good for "do this on all hosts, in batches, and show me what changed". There are two ways to talk to Redfish.

### 3.1 The `uri` module (generic HTTP)

This is what the user's notes show: log in, take the token, call an action. The pattern I tested, with a `block` and `always` so the logout runs even if something fails (`code/part07/ansible/uri_session.yml`):

```yaml
- name: Redfish session with the uri module, always logged out
  block:
    - name: Log in
      ansible.builtin.uri:
        url: "{{ bmc }}/redfish/v1/SessionService/Sessions"
        method: POST
        body_format: json
        body: { UserName: admin, Password: adminpass }
        ca_path: "{{ ca }}"
        status_code: 201
      register: login
      no_log: true
    - name: Read the system
      ansible.builtin.uri:
        url: "{{ bmc }}/redfish/v1/Systems/System_0"
        headers: { X-Auth-Token: "{{ login.x_auth_token }}" }
        ca_path: "{{ ca }}"
      register: sysinfo
  always:
    - name: Log out
      ansible.builtin.uri:
        url: "{{ login.location }}"
        method: DELETE
        headers: { X-Auth-Token: "{{ login.x_auth_token }}" }
        ca_path: "{{ ca }}"
        status_code: 204
```

What I learned by running it:

- The module turns response headers into variables with underscores: `login.x_auth_token` and `login.location`. The notes' use of `session_login.x_auth_token` is right.
- **`login.location` is already the full URL** (`https://host:port/redfish/v1/SessionService/Sessions/1`). My first logout task glued the base URL in front of it and failed with a name resolution error. Use it as is.
- `no_log: true` keeps the password and token out of the Ansible output.
- The notes' example used `validate_certs: false`. Use `ca_path` (or the system store) instead.
- `status_code: 201` and `204` make the task fail on any other answer. Without it only connection errors fail.

### 3.2 The `community.general` Redfish modules

The collection has three modules: `redfish_info` (read), `redfish_command` (act) and `redfish_config` (change settings). They hide the URI walking. I installed `community.general` 13.5.0 and ran (`ansible/inventory_and_restart.yml`):

| Task | Module and command | Result on the mock |
|---|---|---|
| firmware inventory | `redfish_info`, category `Update`, command `GetFirmwareInventory` | 34 entries with names, versions, `Updateable` |
| system inventory | `redfish_info`, category `Systems`, `GetSystemInventory` | model, serial, memory, processors |
| health | `redfish_info`, `GetHealthReport` | per-chassis health |
| restart | `redfish_command`, category `Systems`, command `PowerGracefulRestart`, `resource_id: System_0` | `changed`, "Action was successful" |

Other commands in the module help include `GetFanInventory`, `GetPsuInventory`, `GetBiosAttributes`, `GetBootOrder` and others, plus `redfish_command` commands for power (`PowerOn`, `PowerForceOff`, `PowerReboot`), boot override (`SetOneTimeBoot`, `EnableContinuousBootOverride`) and firmware (`SimpleUpdate`, `MultipartHTTPPushUpdate`). I tested only the ones in the table.

Facts worth knowing:

- Passing the credentials: `baseuri` (host and port, **no scheme**), `username`, `password`, and `ca_path` or `validate_certs`.
- The modules build the address as `https://<baseuri>`, so they work only with HTTPS. That is why I added TLS to the mock.
- On the mock `GetFanInventory` returned no entries, because my mock has no fan resources. Modules ask for specific resources and return what they find; they do not know your BMC's quirks.
- The module's results are reported as facts, so a playbook can compare them with a baseline.

**Which to use.** Use the Redfish modules for the common jobs they cover, because they handle sessions and parsing and report `changed` correctly. Use `uri` when no module covers what you need, or when you want exact control over the request (for example `@Redfish.OperationApplyTime`). In both cases: put BMC credentials in Ansible Vault or your secret manager, use `no_log`, and keep one task per change so the output tells the story.

### 3.3 Scale in Ansible

Ansible runs tasks on hosts in parallel (the `forks` setting) and can run in batches with `serial`. For BMCs:

- keep forks modest so management switches are not flooded (your Part 4 chapters cover these settings);
- use `serial` for risky actions such as firmware updates: a small first batch, then bigger;
- use `max_fail_percentage` or `any_errors_fatal` so one bad batch stops the run;
- do **not** retry login failures in a loop (account lockout, chapter 7.4).

## 4. Go

Go suits long-running tools and operators. The `gofish` library (`github.com/stmcginnis/gofish`) is the usual Redfish client. With version 0.27.0 I ran this program against the mock (`code/part07/go_gofish`):

```go
cfg := gofish.ClientConfig{Endpoint: os.Args[1], Username: "admin", Password: "adminpass", Insecure: true}
c, err := gofish.Connect(cfg)
defer c.Logout()
systems, _ := c.GetService().Systems()
for _, s := range systems { fmt.Println(s.ID, s.PowerState, s.Status.Health) }
if _, err := systems[0].Reset(schemas.GracefulRestartResetType); err == nil { fmt.Println("reset sent") }
```

Output: `System_0 Off OK`, `HGX_Baseboard_0 On OK`, `reset sent`. Notes:

- `Insecure: true` in the demo is for the lab certificate. A real program uses a configured `HTTPClient` with your CA, as in section 1.
- `Reset` returns two values in this version (a task monitor and an error), so check both.
- The library walks links for you (`Systems()`), which fits the discovery rule. API names change between versions, so pin the version.

## 5. Running on a fleet: the runner and its lab

`code/part07/fleet_run.py` runs a read-only task on many BMCs. The rules in code:

| Rule | Why |
|---|---|
| bounded worker pool (`--workers`) | 1,000 BMCs must not all be hit at once |
| timeout per request | a hanging BMC must not freeze the run |
| retry only what can recover: timeouts, connection errors, 502, 503, 504 | those may succeed later |
| **never retry 401, 403, 404** | a wrong password retried five times can lock the account |
| exponential backoff with jitter | avoid hitting a recovering BMC all at the same moment |
| one failure never stops the run | every host ends in exactly one outcome |
| log out in `finally` | do not leak sessions |
| summary by failure kind, non-zero exit code | pipelines can react |

`fleet_lab.py` tests all of this against 15 mock BMCs started on the spot:

| Host | Behaviour | Outcome the lab checks |
|---|---|---|
| 8 healthy | normal | success, first try |
| slow | 0.6 s per request | success within the 1 s timeout |
| flaky | 503 twice, then fine | success on the third try |
| down503 | 503 always | fails after 1 plus 3 retries, kind `http 503` |
| badpw | wrong password | fails after **1** attempt, kind `http 401` |
| hang | never answers | cut off, kind `timeout` |
| closed | nothing listening | kind `connection refused` |
| generic | different resource names | success with no code change |

Result: 15 hosts, 11 succeeded, failures grouped as `http 503`, `http 401`, `timeout`, `connection refused`. A second check shows 8 workers finishing 8 slow hosts in about 1 second against 8 seconds for one worker. And a check that no sessions were left open on the healthy hosts.

Run it on your own list:

```bash
python3 fleet_run.py endpoints.csv --workers 16 --timeout 10 --retries 3 --task health
```

This runner only **reads**. A runner that changes things needs more: batches, a stop-on-failure rule, verification, and a human approval step. Chapter 7.14 builds on it.

## 6. A choice table

| Tool | Best for | Weak at |
|---|---|---|
| `curl` | one quick look, learning, a shell snippet | loops, errors, JSON handling |
| Python | custom logic, validation, fleets, reports | needs care for sessions and retries |
| `redfish` library | simple scripts with sessions handled | no fleet logic |
| Ansible `uri` | exact requests inside playbooks | verbose, manual session handling |
| Ansible Redfish modules | common read and power tasks, change reporting | limited to what the modules cover |
| Go and gofish | services, operators, high concurrency | more code for small jobs |
| BCM `redfish*` commands | cluster-wide actions in a BCM cluster (chapter 7.2) | tied to BCM |

## 7. Exercises

1. Run `fleet_lab.py` and change the retry rule so a 401 is retried. Which check fails and why is that retry dangerous?
2. Write a playbook with `redfish_info` that prints the BIOS version of every host in an inventory of three mock BMCs on different ports.
3. Change `uri_session.yml` to log out even when reading the system fails. Test by pointing it at a wrong system ID.
4. Port `rf_inventory.py`'s idea to Go with gofish: list each system's GPUs from `Processors`.
5. Add `--task firmware-drift` to `fleet_run.py` using `rf_firmware.drift` and a baseline file.
6. Start the mock with `--tls` and a self-signed certificate (`selfsigned.pem`). Show that a client with the lab CA refuses it.

## 8. Interview angles

- "How do you automate BMC changes safely?" Sessions, TLS verification, idempotent steps, small batches, verification after each change, no blind retries on 401.
- "Why not retry on a 401?" It will not fix itself and it can lock the account for everyone.
- "Ansible module or `uri`?" Module for covered jobs (change reporting, parsing); `uri` for exact control.
- "How do you test automation without hardware?" A mock with fault injection (slow, flaky, down, wrong password, hang), plus validation against the official schemas (chapter 7.6).
- "How do you keep a hung BMC from stopping a fleet run?" Timeouts per request, a bounded pool and per-host failure isolation.

## 9. Checkpoint questions (20)

1. Why is `curl -k` unsafe, and what do you use instead?
2. What does TLS 1.2 or newer mean for a Redfish service?
3. What does the Redfish library handle for you, and what not?
4. Why log out in a `finally` or `always` block?
5. What is the `uri` module's name for the `X-Auth-Token` response header?
6. Why did my logout task fail the first time?
7. What does `no_log: true` do?
8. What do `redfish_info`, `redfish_command` and `redfish_config` do?
9. Why do the Redfish modules need HTTPS?
10. When would you choose `uri` over a Redfish module?
11. Which Ansible settings protect your network when you hit many BMCs?
12. What does `Insecure: true` do in gofish and when is it acceptable?
13. Which statuses should a runner retry? Which never?
14. What is exponential backoff with jitter for?
15. Why must one failing host not stop the run?
16. How do you detect a leaked session?
17. What should a script do when a task times out?
18. How does the mock inject faults?
19. Name three outcomes you test in a fleet lab.
20. Why is the runner read-only, and what must a changing runner add?

## 10. Sources and review notes

- **Redfish Specification DSP0266 v1.21.0:** TLS 1.2 or later and certificate replacement (13.1), HTTP Basic and sessions (13.3), tasks and status codes (7.3, 8.3, 12.2).
- **Tools run here:** `redfish` 3.4.2 (PyPI), `ansible-core` 2.21.5, `community.general` 13.5.0 (modules `redfish_info`, `redfish_command`, `redfish_config`; I read their documentation text in the installed collection), `gofish` v0.27.0, Go 1.23.2, OpenSSL for the lab CA.
- **NVIDIA-DevOps notes (volume 10 chapter 1, sections 3.5 and 3.6):** the Python and Ansible examples. Changes I made: sessions closed, certificates verified instead of disabled, and a corrected note about the `Location` value.
- **Background:** your Part 3 and Part 4 chapters on Python resilience and Ansible; the Ansible book's chapters on `serial`, handlers and speed; the notes' Python masterclass sections on resilient API clients (retries and circuit breakers). I used these as background and did not copy from them.
- **Run here:** `fleet_lab.py` (14 checks); all earlier labs re-run after the TLS and client changes (all pass).
- **Not verified:** any behaviour on a real BMC (rate limits, session limits, response times), the module list on versions other than the ones above, and `MultipartHTTPPushUpdate` and `SimpleUpdate` modules against the mock (I did not run them).
