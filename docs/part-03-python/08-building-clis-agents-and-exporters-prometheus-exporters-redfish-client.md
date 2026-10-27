---
id: "c03-08"
title: "3.8 Building CLIs, agents and exporters"
sidebar_label: "3.8 Building CLIs, agents and exporters"
sidebar_position: 8
description: "Production Python tooling for infrastructure: CLIs (argparse, Click, Typer), resilient API clients, Prometheus exporters, a Redfish client, node agents, packaging and distribution"
status: "drafted"
tier: "2"
level: "I"
lab_venue: "Mac"
---

# 3.8 Building CLIs, agents and exporters

| | |
|---|---|
| Level | Intermediate |
| Priority tier | 0 |
| Lab venue | Python 3.11+, `pip install click typer rich httpx tenacity prometheus-client pyyaml`; Docker for Prometheus |
| Part | Part 3: Python for infrastructure |
| Status | Drafted, labs **untested** |

## Why this matters for AI infrastructure

Fleet operations are mostly small programs that talk to other systems: a CLI that drains a node, a script that collects `nvidia-smi` or DCGM data from 500 machines, an exporter that turns BMC sensors into Prometheus metrics, a Redfish client that sets boot order across a rack, a node agent that reports health to a control plane. These tools are run by humans at 3 a.m. and by automation every minute, so they must be predictable (clear exit codes, idempotent, dry-run), resilient (timeouts, retries, backoff, pagination), observable (structured logs, metrics) and distributable (a pinned version that works on every operator's laptop and every jump host). This chapter covers the engineering patterns behind such tools, with a bias toward GPU fleets, BMCs and Prometheus.

## Prerequisites and outcomes

Needs 3.1 to 3.6 (functions, packaging, typing, subprocess, concurrency) and 2.31 (monitoring). Complements 3.7 (services) and 3.9 (testing).

After this chapter you can:

- Design a CLI with subcommands, options, config files, environment variables, output formats and meaningful exit codes, using argparse, Click or Typer.
- Build resilient HTTP clients with timeouts, retries with exponential backoff and jitter, circuit breakers, pagination and rate-limit handling.
- Write a Prometheus exporter (custom collector) that is safe to scrape, and know the metric type and naming rules.
- Talk to a BMC with the Redfish API (sessions, service root traversal, power, boot, sensors, firmware, events) in Python.
- Fan out work across many hosts with bounded concurrency and per-host error isolation.
- Build a long-running node agent (signals, graceful shutdown, health, systemd unit).
- Package and distribute tools (wheels, `pipx`, zipapps, containers, single binaries).

## 1. Principles for operational tooling

1. **Safe by default.** Read-only commands need no confirmation; mutating commands support `--dry-run`, print what they will do, require `--yes` for destructive scope, and refuse wildcard targets without an explicit flag.
2. **Idempotent.** Running twice gives the same end state (set to desired, do not toggle). Return "already in desired state" as success.
3. **Explicit exit codes.** `0` success, `1` generic failure, `2` usage error (argparse/Click default), distinct codes for "partial failure" (some hosts failed) and "nothing to do" so wrappers and CI can react.
4. **Machine- and human-readable output.** Default to a table for humans, `--output json|yaml|tsv` for pipelines; send data to stdout and logs/progress to stderr so pipes stay clean.
5. **Timeouts everywhere.** Every network call and subprocess has a timeout; no operational tool should be able to hang forever.
6. **Per-target isolation.** One bad host must not abort the batch; collect results and errors, summarise at the end, and set the exit code accordingly.
7. **Structured logging and auditability.** Log who ran what against which targets with a run id; log mutating actions at INFO with before/after state.
8. **Config layering.** Precedence: command-line flags, then environment variables, then config file, then defaults; never put secrets on the command line (they show up in `ps` and shell history); read from env, files or a secret store.
9. **Small, testable core.** Parsing, decision logic and I/O separated: the CLI layer is a thin shell over functions you can unit test (chapter 3.9).

## 2. Command-line interfaces

### 2.1 argparse: the standard library baseline

```python
import argparse, sys

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="gpuctl", description="GPU fleet helper")
    p.add_argument("-v", "--verbose", action="count", default=0)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("status", help="show node GPU status")
    s.add_argument("hosts", nargs="+")
    s.add_argument("--output", choices=["table", "json"], default="table")

    d = sub.add_parser("drain", help="cordon and drain a node")
    d.add_argument("host")
    d.add_argument("--timeout", type=int, default=600)
    d.add_argument("--dry-run", action="store_true")
    return p

def main(argv=None) -> int:
    args = build_parser().parse_args(argv)           # argv injectable for tests
    ...
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

argparse needs no dependency, handles subcommands, types, choices, mutually exclusive groups and automatic `--help`. Its weaknesses are verbosity and weaker composition for large command trees. Always take `argv` as a parameter and return an int so tests call `main([...])` directly.

### 2.2 Click

Click builds CLIs from decorated functions, with nested command groups, automatic help, type conversion, prompts, colour, shell completion and a test runner (`CliRunner`). The context object carries shared state (config, client, output format) to subcommands.

```python
import json, logging, sys
import click

@click.group()
@click.option("--config", type=click.Path(dir_okay=False), envvar="FLEET_CONFIG", help="Config file")
@click.option("-v", "--verbose", count=True)
@click.option("--output", type=click.Choice(["table", "json"]), default="table", show_default=True)
@click.pass_context
def cli(ctx, config, verbose, output):
    """Fleet management CLI."""
    logging.basicConfig(level=[logging.WARNING, logging.INFO, logging.DEBUG][min(verbose, 2)],
                        format="%(asctime)s %(levelname)s %(message)s", stream=sys.stderr)
    ctx.obj = {"config": load_config(config), "output": output}

@cli.command()
@click.argument("hosts", nargs=-1, required=True)
@click.pass_obj
def status(obj, hosts):
    """Show GPU status for HOSTS."""
    rows = [query_host(h, obj["config"]) for h in hosts]
    if obj["output"] == "json":
        click.echo(json.dumps(rows, indent=2))
    else:
        for r in rows:
            click.echo(f"{r['host']:<20} {r['gpus']:>2} GPUs  {r['state']}")

@cli.command()
@click.argument("host")
@click.option("--dry-run", is_flag=True)
@click.option("--yes", is_flag=True, help="Skip confirmation")
def drain(host, dry_run, yes):
    """Cordon and drain HOST."""
    if not (yes or dry_run):
        click.confirm(f"Drain {host}?", abort=True)
    ...

if __name__ == "__main__":
    cli()
```

```mermaid
flowchart LR
  A["argv"] --> B["Group callback\n(logging, config, client)"]
  B --> C["Subcommand\nparse + convert + validate"]
  C --> D["Business function\n(pure, testable)"]
  D --> E["Output formatter\n(table/json)"]
  E --> F["Exit code"]
```

Click essentials: `@click.option` with `envvar=`, `multiple=True`, `required`, `type=click.IntRange(1, 64)`; `click.Path(exists=True)`; `click.File`; `click.prompt`/`confirm`; `click.progressbar`; `click.echo(..., err=True)` for stderr; raising `click.ClickException` or `click.UsageError` for clean error messages and exit codes; `ctx.exit(code)`; `click.testing.CliRunner().invoke(cli, ["status", "h1"])` to test.

### Case study from *Practical MLOps* Chapter 11: `csv-linter` and `cloud-translate` CLIs

In *Practical MLOps* Chapter 11 (*Building MLOps Command Line Tools and Microservices*, modeled in `code/part03/python_clis_agents_exporters.py`), Alfredo Deza walks through two end-to-end Click command-line tools that illustrate why packaging a single-purpose CLI beats ad-hoc notebooks and shell snippets:
1. **Packaging `csv-linter` with `console_scripts` and `pip install -e .`:** When inspecting a 32,770-row `wine.csv` dataset in pandas (`df.describe()`), three silent data-quality bugs surfaced: (a) the `'grape'` column had a count of `0.0` (100% `NaN` values), (b) saving a DataFrame via `df.to_csv("wine.csv")` without `index=False` injected spurious `'Unnamed: 0'` index columns on every round-trip, and (c) Windows carriage returns (`\r\n`, displayed as `^M` in `vim`) inside `'notes'` fields broke downstream parsers (`carriage.csv`). Deza packages three helper functions in `csv_linter/checks.py`—`zero_count_columns(df)` (returning columns where `df[key].count() == 0`), `unnamed_columns(df)` (counting keys containing `"Unnamed"`), and `carriage_returns(df)` (returning the first `(index, column, field)` containing `"\r\n"`, truncated to `field[:50]` on display)—behind a Click command `@click.command() @click.argument('filename', type=click.Path(exists=True)) def main(filename):`, exposed as `csv-linter=csv_linter.main:main` under `entry_points` (`[project.scripts]` in `pyproject.toml`) and installed in editable mode with `pip install -e .` (noting that renaming or moving `csv_linter.py` to `csv_linter/main.py` requires re-running `pip install -e .` to regenerate the entry-point wrapper script).
2. **Wrapping a Cloud ML microservice (`cloud-translate`):** Rather than bundling heavy ML weights inside every CLI binary, `cloud-translate` (`cloud-translate=trigger:main`) deploys a serverless HTTP Cloud Function (`google-cloud-translate==3.0.2`, `translate.TranslationServiceClient()` in `us-central1` translating text to French `target_language_code="fr"`), fetches a short-lived OIDC bearer token via `subprocess.Popen(["gcloud", "auth", "print-identity-token"], stdout=subprocess.PIPE)` (`out.decode("utf-8").strip()`), and posts `requests.post(url, json={"message": text}, headers={"Authorization": f"bearer {token()}"})`—turning a 20-line Click CLI (`@click.command() @click.argument('text')`) into a secure client for a cloud microservice.

### 2.3 Typer and Rich

**Typer** (from the FastAPI author) builds on Click and uses type hints: function parameters become arguments and options, giving less boilerplate and good shell completion.

```python
import typer
from typing import Annotated
app = typer.Typer(no_args_is_help=True, add_completion=True)

@app.command()
def drain(host: str,
          timeout: Annotated[int, typer.Option(min=1, help="Seconds")] = 600,
          dry_run: Annotated[bool, typer.Option("--dry-run")] = False):
    """Drain HOST."""
    ...

if __name__ == "__main__":
    app()
```

**Rich** adds tables, progress bars, syntax-highlighted tracebacks and live displays; **textual** builds full terminal UIs. Keep rich output on a TTY only (`sys.stdout.isatty()`) and plain text when piped.

Choice guide: argparse for tiny scripts and zero dependencies; Click for large command trees and mature plug-in ecosystems; Typer for fast type-hint-driven tools; `fire`/`cyclopts` exist but are less common. In an NVIDIA/Kubernetes world you will also read many Go CLIs (kubectl, helm); borrowing their conventions (`noun verb`, `-o json`, `--dry-run=client`, `--context`) makes tools feel familiar.

### 2.4 Configuration and secrets

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
class Config(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FLEET_", env_file=".env", extra="ignore")
    api_url: str = "https://fleet.example.com"
    token: str | None = None            # from env FLEET_TOKEN, never a CLI flag
    timeout: float = 10.0
```

Use YAML/TOML for files (`tomllib` is in the standard library from 3.11; `yaml.safe_load` never `yaml.load`), validate with pydantic, and merge in the documented precedence order. Support XDG paths (`~/.config/fleet/config.toml`), `--config` override, and print the effective configuration with a `config show` command (redacting secrets).

### 2.5 Interactive and long-running UX

Progress bars for long loops, spinners for waits, `--watch` modes that poll and redraw, `--follow` for streams, `--wait/--timeout` for operations that complete asynchronously (poll the status endpoint with backoff, as kubectl does with `rollout status`). Handle `KeyboardInterrupt` by cleaning up and returning exit code 130.

## 3. Resilient API clients

Network calls fail in many ways: DNS errors, connection refused, TLS problems, timeouts, 429/503 under load, partial responses, pagination that silently truncates. A client library for an internal API should implement these defences once.

### 3.1 Sessions, timeouts and connection reuse

```python
import httpx
client = httpx.Client(base_url="https://api.example.com", timeout=httpx.Timeout(connect=3, read=15, write=15, pool=5),
                      headers={"Authorization": f"Bearer {token}", "User-Agent": "fleetctl/1.4"},
                      limits=httpx.Limits(max_connections=20), verify="/etc/ssl/corp-ca.pem")
```

Reuse one client (connection pooling, keep-alive); always set all four timeouts (a bare `requests.get(url)` has none and can hang forever); pin the CA bundle for private PKI; include a User-Agent with version for server-side debugging. `requests` is ubiquitous and fine for sync scripts; `httpx` offers sync and async APIs and HTTP/2; `aiohttp` is common for high-concurrency async clients.

### 3.2 Retries, backoff and jitter

Retry only operations that are safe to repeat (GET, PUT, DELETE, or POST with an idempotency key) and only on transient failures (connection errors, timeouts, 429, 502, 503, 504). Use **exponential backoff with jitter** so many clients retrying simultaneously do not synchronise into a thundering herd, honour `Retry-After`, and cap both attempts and total time.

```python
from tenacity import retry, stop_after_attempt, stop_after_delay, wait_exponential_jitter, retry_if_exception, before_sleep_log
import httpx, logging
log = logging.getLogger(__name__)

def transient(exc: BaseException) -> bool:
    if isinstance(exc, (httpx.ConnectError, httpx.ReadTimeout, httpx.ConnectTimeout, httpx.RemoteProtocolError)):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in {429, 502, 503, 504}
    return False

@retry(retry=retry_if_exception(transient),
       wait=wait_exponential_jitter(initial=0.5, max=20),      # 0.5, 1, 2, 4 ... capped, with jitter
       stop=(stop_after_attempt(6) | stop_after_delay(60)),
       before_sleep=before_sleep_log(log, logging.WARNING), reraise=True)
def get_json(path: str, **params):
    r = client.get(path, params=params)
    r.raise_for_status()
    return r.json()
```

Without a library the loop is `delay = min(cap, base * 2**attempt); sleep(random.uniform(0, delay))` ("full jitter"). Retrying 4xx errors other than 429 (400, 401, 403, 404, 409) is a bug: the answer will not change.

### 3.3 Circuit breakers and bulkheads

When a dependency is down, retries amplify load. A **circuit breaker** counts consecutive failures, **opens** after a threshold (fail fast, no calls), waits a cool-down, then goes **half-open** allowing a probe call; success **closes** it. Libraries: `pybreaker`, `circuitbreaker`, or a 30-line class. A **bulkhead** limits concurrent calls per dependency (semaphore) so one slow service cannot consume all threads. Combine: timeout, then retry, then breaker, then bulkhead; and surface a clear error ("fleet API unavailable, breaker open for 30 s").

### 3.4 Pagination and completeness

Silent truncation is a classic bug: the API returns 100 items per page and the script processes only the first. Wrap pagination in a generator that hides the mechanics and fails loudly on anomalies.

```python
def paginate(path: str, page_size: int = 200):
    token = None
    seen = 0
    while True:
        params = {"limit": page_size, **({"page_token": token} if token else {})}
        body = get_json(path, **params)
        for item in body["items"]:
            seen += 1
            yield item
        token = body.get("next_page_token")
        if not token:
            break
```

Prefer cursor/token pagination for consistency over offset pagination (offsets shift when items are added). Verify totals if the API provides a count; log how many items were fetched.

### 3.5 Rate limits, concurrency and file operations

Respect `X-RateLimit-*`/`Retry-After`; use a token bucket (`aiolimiter`, `ratelimit`) for outbound limits. For file operations on shared systems avoid time-of-check/time-of-use races: write to a temporary file in the same directory and `os.replace` (atomic on POSIX), use `fcntl.flock` or lock files for mutual exclusion, open with `O_EXCL` for create-if-absent, and prefer `try: open(...)` over `if exists: open(...)`.

## 4. Prometheus exporters

An **exporter** exposes the state of something that does not speak Prometheus natively (a BMC, an InfiniBand fabric, a license server, a vendor CLI) as metrics on an HTTP endpoint that Prometheus scrapes.

### 4.1 Metric model essentials

- **Counter**: monotonically increasing total (`_total` suffix); use `rate()` in queries. **Gauge**: value that goes up and down. **Histogram**: bucketed observations plus `_sum`/`_count` for latency distributions. **Summary**: client-side quantiles (not aggregatable; prefer histograms). **Info**: constant labels about an entity.
- **Naming**: `snake_case`, a unit suffix in base units (`_seconds`, `_bytes`, `_celsius`, `_watts`), prefix with the application (`bmc_temperature_celsius`), no label names in the metric name, no timestamps in the name.
- **Labels**: low and bounded cardinality (host, gpu index, sensor name); never user ids, request ids, timestamps or free text. Each unique label combination is a separate time series, and cardinality explosions are the main way exporters hurt Prometheus.
- Expose `*_up` or `scrape_success` and `scrape_duration_seconds` so failures are visible as data rather than silent gaps.

### 4.2 The simple way: instrument and serve

```python
from prometheus_client import start_http_server, Gauge, Counter, Histogram
import time

TEMP = Gauge("gpu_temperature_celsius", "GPU temperature", ["host", "gpu"])
ERRORS = Counter("exporter_poll_errors_total", "Failed polls", ["host"])
POLL = Histogram("exporter_poll_seconds", "Poll duration")

def poll_forever(hosts, interval=15):
    while True:
        for h in hosts:
            with POLL.time():
                try:
                    for gpu, t in read_temps(h).items():
                        TEMP.labels(h, gpu).set(t)
                except Exception:
                    ERRORS.labels(h).inc()
        time.sleep(interval)

start_http_server(9101)
poll_forever(["gpu01", "gpu02"])
```

This background-polling model decouples collection from scraping, but metrics can be stale if polling stalls, and series for removed hosts linger (call `.remove(...)` or use a collector).

### 4.3 The recommended way: a custom collector

A custom collector runs **at scrape time**, producing a fresh, consistent snapshot every time and avoiding stale series. This is the pattern used by most mature exporters (node_exporter style: the scrape drives the collection).

```python
from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily
from prometheus_client import REGISTRY, start_http_server
import time

class FleetCollector:
    def __init__(self, hosts, timeout=5):
        self.hosts, self.timeout = hosts, timeout

    def collect(self):
        t0 = time.time()
        temp = GaugeMetricFamily("gpu_temperature_celsius", "GPU temperature", labels=["host", "gpu"])
        up = GaugeMetricFamily("fleet_host_up", "1 if the host answered", labels=["host"])
        for h in self.hosts:
            try:
                for gpu, t in read_temps(h, timeout=self.timeout).items():
                    temp.add_metric([h, str(gpu)], t)
                up.add_metric([h], 1)
            except Exception:
                up.add_metric([h], 0)               # failure is data, not an exception
        yield temp
        yield up
        dur = GaugeMetricFamily("fleet_scrape_duration_seconds", "Collection time")
        dur.add_metric([], time.time() - t0)
        yield dur

REGISTRY.register(FleetCollector(["gpu01", "gpu02"]))
start_http_server(9101)
```

Rules: collection must finish well under the scrape timeout (parallelise with a thread pool and per-host timeouts, or cache results for a few seconds); never let one failing target raise out of `collect()`; do not block on slow hardware (BMC queries can take seconds); avoid running expensive commands on every scrape (cache with a TTL); protect the endpoint (bind to an internal interface, TLS and basic auth through `--web.config`-style proxies, or a sidecar).

A **multi-target exporter** (the pattern of `blackbox_exporter` and `snmp_exporter`) takes the target as a URL parameter (`/probe?target=bmc01`), so Prometheus relabelling supplies targets from service discovery and the exporter holds no host list:

```yaml
scrape_configs:
- job_name: bmc
  metrics_path: /probe
  static_configs: [ { targets: [bmc01.mgmt, bmc02.mgmt] } ]
  relabel_configs:
  - source_labels: [__address__]
    target_label: __param_target
  - source_labels: [__param_target]
    target_label: instance
  - target_label: __address__
    replacement: bmc-exporter:9102
```

### 4.4 Real-world GPU and hardware exporters

You rarely need to write these from scratch for GPUs: **DCGM exporter** (NVIDIA Data Center GPU Manager) publishes utilisation, memory, temperature, power, clocks, XID errors, NVLink counters and ECC; **node_exporter** covers the host; the **NVIDIA GPU Operator** deploys DCGM exporter in Kubernetes with a ServiceMonitor; IPMI/Redfish exporters read BMC sensors. You write custom exporters for site-specific gaps: scheduler state (Slurm queue depth and node states from `sinfo`/`squeue --json`), fabric health (UFM or `ibdiagnet` summaries), storage tenant quotas, license counts, job-level GPU accounting joined to Kubernetes or Slurm metadata.

Test an exporter by `curl -s localhost:9101/metrics | head`, lint with `promtool check metrics`, and verify cardinality with `count({__name__=~"gpu_.*"})` in Prometheus.

## 5. Talking to hardware: a Redfish client

**Redfish** is the DMTF RESTful API for out-of-band management (the successor to IPMI): BMCs on DGX, HGX and OEM servers expose it over HTTPS with JSON. Part 7 covers Redfish and BMCs in depth; here we build the client skeleton.

### 5.1 Resource model

A tree rooted at `/redfish/v1/` (the **service root**): `Systems` (the host computer: power state, boot, BIOS, processors, memory), `Chassis` (physical enclosure: thermal, power, sensors, GPUs/PCIe devices), `Managers` (the BMC itself: network, logs, virtual media), `UpdateService` (firmware inventory and update), `AccountService`, `SessionService`, `EventService`, `TelemetryService`. Resources link to each other with `@odata.id` URIs; clients should **discover** members by following links rather than hard-coding vendor paths (`/Systems/1` vs `/Systems/System.Embedded.1` vs `/Systems/Self`). Actions are POSTs to `Actions/...` targets (for example `#ComputerSystem.Reset` with `ResetType` of `On`, `ForceOff`, `GracefulRestart`, `ForceRestart`, `PushPowerButton`).

### 5.2 A small client

```python
import httpx, time, logging
log = logging.getLogger("redfish")

class Redfish:
    def __init__(self, host, user, password, verify=False, timeout=15):
        self.base = f"https://{host}"
        self.c = httpx.Client(base_url=self.base, verify=verify, timeout=timeout)    # BMC certs are often self-signed: pin or manage the CA in production
        self.token = None
        self._login(user, password)

    def _login(self, user, password):
        r = self.c.post("/redfish/v1/SessionService/Sessions", json={"UserName": user, "Password": password})
        r.raise_for_status()
        self.token = r.headers["X-Auth-Token"]
        self.session_uri = r.headers["Location"]                 # needed to log out
        self.c.headers["X-Auth-Token"] = self.token              # session auth avoids sending the password on every call

    def close(self):
        if self.token:
            self.c.delete(self.session_uri)                      # BMCs have a tiny session limit: always log out
        self.c.close()

    def get(self, uri):
        r = self.c.get(uri)
        r.raise_for_status()
        return r.json()

    def members(self, uri):
        for m in self.get(uri).get("Members", []):
            yield self.get(m["@odata.id"])                        # follow links; do not hard-code ids

    def system(self):
        return next(self.members("/redfish/v1/Systems"))

    def power(self, reset_type):
        s = self.system()
        target = s["Actions"]["#ComputerSystem.Reset"]["target"]
        allowed = s["Actions"]["#ComputerSystem.Reset"].get("ResetType@Redfish.AllowableValues", [])
        if allowed and reset_type not in allowed:
            raise ValueError(f"{reset_type} not allowed: {allowed}")
        r = self.c.post(target, json={"ResetType": reset_type})
        r.raise_for_status()
        return r

    def temperatures(self):
        for ch in self.members("/redfish/v1/Chassis"):
            thermal = ch.get("Thermal", {}).get("@odata.id")      # newer schemas use ThermalSubsystem/Sensors
            if thermal:
                for t in self.get(thermal).get("Temperatures", []):
                    yield ch["Id"], t["Name"], t.get("ReadingCelsius")

    def __enter__(self): return self
    def __exit__(self, *exc): self.close()
```

Practical notes:

- **Sessions over basic auth**: create a session, send `X-Auth-Token`, delete the session when done; BMCs allow few concurrent sessions, so leaked sessions lock you out until they time out. Wrap in context managers and `finally`.
- **Long-running actions return a Task**: a `202 Accepted` with a `Location` to a Task monitor; poll until `TaskState` is `Completed`/`Exception`, with a timeout (firmware updates take many minutes and reboot the BMC; expect connection errors in the middle).
- **Vendor variation is the rule**: schemas evolve (Thermal/Power deprecated in favour of ThermalSubsystem/PowerSubsystem/EnvironmentMetrics), OEM extensions live under `Oem`, and some BMCs are slow, rate-sensitive or return 500s under concurrent load. Serialise requests per BMC, retry carefully, cap concurrency across the fleet (BMC management networks are modest), and test against each platform. The DMTF publishes a mockup server and `redfish` Python library (`python-redfish-library`) that handles sessions and OData; NVIDIA tooling (`nvfwupd`, DGX BMC) builds on the same.
- **Security**: BMC credentials are root-equivalent over the machine; keep BMC networks isolated, rotate secrets, use per-user accounts with roles, enable TLS validation with an internal CA, and audit actions. Never log passwords or tokens.
- **Dry-run first**: for power and boot actions, print the target and action without sending; require `--yes`.

### 5.3 Fleet fan-out

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def check(host):
    try:
        with Redfish(host, USER, PASS) as rf:
            s = rf.system()
            return host, {"power": s["PowerState"], "health": s["Status"].get("Health"), "model": s.get("Model")}, None
    except Exception as e:                                         # isolate per host
        return host, None, f"{type(e).__name__}: {e}"

def run(hosts, workers=16):
    ok, bad = {}, {}
    with ThreadPoolExecutor(max_workers=workers) as ex:            # bounded concurrency protects the management network
        for fut in as_completed(ex.submit(check, h) for h in hosts):
            h, res, err = fut.result()
            (bad if err else ok)[h] = err or res
    return ok, bad                                                  # CLI exits non-zero if bad is non-empty
```

For thousands of hosts use asyncio with a semaphore (chapter 3.6), report progress, write results incrementally (so an interrupted run is resumable), and emit a final summary: `412 ok, 3 failed (bmc17: timeout, ...)`.

## 6. Collecting from GPU hosts

Common non-API data sources and how to parse them robustly:

- **`nvidia-smi`**: prefer machine-readable queries over scraping the default table: `nvidia-smi --query-gpu=index,name,temperature.gpu,utilization.gpu,memory.used,memory.total,power.draw,ecc.errors.uncorrected.volatile.total --format=csv,noheader,nounits`. Parse with `csv`; treat `[N/A]` and `[Not Supported]` as missing; use `nvidia-smi -q -x` for XML. Avoid hammering it (each call initialises NVML and can take a second on busy hosts); for continuous monitoring use DCGM or NVML bindings (`pynvml`/`nvidia-ml-py`).
- **NVML/DCGM bindings**: `pynvml.nvmlDeviceGetTemperature`, `nvmlDeviceGetUtilizationRates`, `nvmlDeviceGetMemoryInfo`, `nvmlDeviceGetPowerUsage`, throttling reasons, XID events; DCGM Python bindings for health checks and diagnostics (`dcgmi diag -r 1|2|3` as subprocess).
- **Subprocess hygiene** (chapter 3.5): list arguments, `timeout=`, `check=False` with explicit returncode handling, capture stderr, never `shell=True` with interpolated input, and kill the process group on timeout so no zombie children remain (`subprocess.run(..., timeout=...)` kills the child but not its descendants; use `start_new_session=True` and `os.killpg`). Reap children (`wait()`) in long-running agents.
- **`/proc` and `/sys`**: read directly for cheap, dependency-free metrics (`/proc/meminfo`, `/proc/pressure/*`, `/sys/class/infiniband/*/ports/*/counters/*`, `/sys/class/net/*/statistics/*`); handle files vanishing between listing and reading.

Wrap each source in a function returning a typed result (dataclass) so the CLI, exporter and agent share one collection layer and tests can feed canned outputs.

## 7. Node agents and daemons

A **node agent** runs on every host (as a systemd service or DaemonSet): it gathers health, applies local actions and reports to a control plane. Design points:

- **Lifecycle and signals**: handle `SIGTERM` (graceful stop: finish the current cycle, flush, exit within the grace period), `SIGHUP` (reload config), ignore `SIGPIPE` issues, and exit non-zero on fatal errors so systemd restarts it. In asyncio use `loop.add_signal_handler`; in threads set a `threading.Event` the loop checks.
- **Main loop**: `while not stop.is_set(): do_cycle(); stop.wait(interval + jitter)`. Jitter prevents fleet-wide synchronised spikes. Measure cycle time; log and metric when a cycle overruns.
- **Failure containment**: each check in its own try/except with a timeout; a broken GPU query must not stop network checks. Export per-check success metrics.
- **State and idempotency**: store small state under `/var/lib/<agent>` (atomic writes); on start, reconcile desired vs actual instead of assuming a clean slate (the broker/hardware is the source of truth).
- **Self-observability**: expose `/metrics` and `/healthz` (use `http.server` in a thread or `prometheus_client`), version/build info, last successful cycle timestamp, and queue depths. Alert on staleness of the last-success metric.
- **Resource discipline**: bounded memory (no unbounded caches or retained tracebacks), bounded file descriptors, CPU limits in systemd (`CPUQuota`, `MemoryMax`, `Nice`), low priority so it never competes with training jobs (and pin or limit threads to avoid jitter on GPU hosts).
- **Security**: run as a dedicated unprivileged user; grant only needed capabilities; for privileged actions use narrow sudo rules or a small helper; authenticate to the control plane with per-node credentials (mTLS or short-lived tokens), and validate any command received (an agent that executes arbitrary remote commands is a fleet-wide compromise vector).

Minimal systemd unit:

```ini
[Unit]
Description=Node health agent
After=network-online.target
Wants=network-online.target

[Service]
User=nodeagent
ExecStart=/opt/nodeagent/venv/bin/nodeagent --config /etc/nodeagent.toml
Restart=on-failure
RestartSec=5
TimeoutStopSec=30
MemoryMax=300M
CPUQuota=20%
NoNewPrivileges=yes
ProtectSystem=strict
ReadWritePaths=/var/lib/nodeagent
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

Kubernetes alternative: a DaemonSet with `hostPID`/`hostNetwork` only if truly required, tolerations for all nodes (including tainted GPU nodes), `/sys` and `/dev` mounts read-only where possible, and the Downward API for node name.

## 8. Packaging and distribution of tools

How operators get your tool matters as much as the code.

| Approach | Good for | Notes |
|---|---|---|
| Wheel on an internal index + `pipx install fleetctl` | Developer/operator laptops, jump hosts | Isolated env per tool, easy upgrades; pin Python version |
| `uv tool install` / `uvx` | Fast installs, reproducible | Lockfile support |
| Zipapp (`shiv`, `pex`, `python -m zipapp`) | Single-file deployment to hosts with matching Python | Needs compatible interpreter and wheels for the platform |
| Container image | CI, Kubernetes jobs, consistent runtime | Larger; mount kubeconfig/credentials explicitly |
| PyInstaller / Nuitka single binary | Hosts without Python, air-gapped | Platform-specific builds; larger; slower startup |
| OS packages (deb/rpm via `fpm`) | Fleet-wide config-managed rollout | Fits Ansible/Foreman; versioned and auditable |

Project layout with `pyproject.toml`:

```toml
[project]
name = "fleetctl"
version = "1.4.0"
requires-python = ">=3.10"
dependencies = ["click>=8.1", "httpx>=0.27", "tenacity>=8", "rich>=13"]

[project.scripts]
fleetctl = "fleetctl.cli:cli"          # creates the `fleetctl` executable on install

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

Release practices: semantic versioning and a changelog; `--version` output including git SHA; pinned, hashed lock files for reproducibility (`uv lock`, `pip-compile --generate-hashes`); supply-chain hygiene (scan dependencies with `pip-audit`, generate an SBOM, sign artefacts, publish from CI with trusted publishing); shell completions; man pages or `--help` that documents exit codes; an upgrade check that warns when the tool is older than the server's minimum supported version.

## 9. Profiling and performance of tools

- **CPU**: `python -m cProfile -o out.prof script.py` then `python -m pstats out.prof` (sort by cumulative time) or `snakeviz`; `py-spy top -p PID` / `py-spy record -o flame.svg -p PID` profile a running process without modifying it (needs ptrace permission); `scalene` and `pyinstrument` give line-level and wall-clock views.
- **Memory**: `tracemalloc` (take snapshots, compare, print top allocation sites), `memray`, `objgraph` for reference chains; typical leaks in agents are unbounded dicts/lists, caches without eviction, retained exceptions/tracebacks, and growing label sets in metrics.
- **I/O-bound slowness** is usually serial network calls: add bounded concurrency, connection reuse, and batching; measure first (log timings per phase).
- **Startup time** matters for CLIs invoked in loops: lazy-import heavy modules (`import pandas` inside the function), avoid work at import time, check with `python -X importtime`.

A production latency investigation pattern: confirm the symptom with timings, check dependencies (is the API slow or are we?), profile where time goes (py-spy on the live process), look at resource limits (CPU throttling in containers shows as latency), then fix the specific bottleneck and verify with the same measurement.

## 10. Worked capstone: a GPU fleet diagnostics CLI

Architecture: `cli.py` (Click group, output formatting, exit codes) calls `collect.py` (per-host executor: SSH/agent/Redfish with timeout, bounded concurrency), which calls `parsers.py` (pure functions turning `nvidia-smi` CSV / `dcgmi` output into dataclasses), with `models.py` (dataclasses/pydantic) and `rules.py` (health rules: temperature above threshold, uncorrected ECC non-zero, XID in a set, missing GPUs versus expected count). Output is a table or JSON; exit code 0 when all healthy, 1 on usage/runtime failure, 3 when any GPU is unhealthy, 4 on partial collection failure.

```python
# parsers.py: pure, trivially testable
from dataclasses import dataclass
@dataclass(frozen=True)
class Gpu:
    index: int; name: str; temp_c: int | None; util_pct: int | None; mem_used_mib: int | None
    mem_total_mib: int | None; ecc_uncorrected: int | None

def _int(s):
    s = s.strip()
    return None if s in ("", "[N/A]", "[Not Supported]") else int(float(s))

def parse_smi_csv(text: str) -> list[Gpu]:
    gpus = []
    for line in text.splitlines():
        if not line.strip(): continue
        f = [x.strip() for x in line.split(",")]
        if len(f) != 7: raise ValueError(f"unexpected nvidia-smi columns: {line!r}")
        gpus.append(Gpu(int(f[0]), f[1], _int(f[2]), _int(f[3]), _int(f[4]), _int(f[5]), _int(f[6])))
    return gpus
```

```python
# rules.py
def evaluate(gpus, expected=8, max_temp=85):
    problems = []
    if len(gpus) != expected: problems.append(f"expected {expected} GPUs, found {len(gpus)}")
    for g in gpus:
        if g.temp_c and g.temp_c > max_temp: problems.append(f"gpu{g.index} temp {g.temp_c}C")
        if g.ecc_uncorrected: problems.append(f"gpu{g.index} uncorrected ECC {g.ecc_uncorrected}")
    return problems
```

The test strategy (chapter 3.9) feeds canned CSV (including `[N/A]`, wrong column counts, empty output, and a missing GPU) into `parse_smi_csv` and `evaluate`, runs the Click command with `CliRunner` and a stubbed executor, and asserts exit codes and JSON shape. This separation (parser, rules, executor, CLI) is the pattern to reuse.

## 11. Lab

First, run the self-checking Python lab (`code/part03/python_clis_agents_exporters_lab.py`) locally. It verifies *Practical MLOps* Chapter 11's `csv-linter` checks (`zero_count_columns`, `unnamed_columns`, `carriage_returns`), `gpuctl` `argparse` subcommand parsing, `CircuitBreaker` state transitions (`CLOSED -> OPEN -> HALF_OPEN -> CLOSED`) and cursor pagination (`paginate_cursor`), Prometheus custom collector exposition (`gpu_temperature_celsius` and `fleet_host_up`), `RedfishSessionClient` session login/discovery/logout, and `parse_smi_csv` + `evaluate_gpus` health rules.

```bash
python3 code/part03/python_clis_agents_exporters_lab.py
```

Next, on any machine with Python 3.11+ (all interactive shell steps below are `untested here`), work through these exercises:

1. **argparse to Click**: implement `gpuctl status|drain` with argparse, then port to Click and Typer; compare help output, tests, completion; add `--output json` and verify piping to `jq` works with logs on stderr.
2. **Exit codes and dry-run**: add partial-failure and unhealthy exit codes; write a shell wrapper that reacts to each; verify `--dry-run` never mutates.
3. **Resilient client**: build a client against a flaky local server (FastAPI endpoint that randomly returns 503/429/hangs); implement timeouts, retries with jitter, `Retry-After`, a circuit breaker; log attempts; graph failures vs attempts; prove POST without idempotency key is not retried.
4. **Pagination bug hunt**: write a server returning 150 items at 100 per page; show the naive client misses 50; fix with the generator and a completeness check.
5. **Exporter**: write the collector exporter around `nvidia-smi` (or a fake) with `up`, duration and per-GPU metrics; scrape with Prometheus in Docker; lint with `promtool check metrics`; kill the data source and verify `up` goes to 0 (not a stale value); cause a label-cardinality mistake deliberately and observe series growth.
6. **Multi-target exporter**: implement `/probe?target=` with relabel config; add concurrency and caching with TTL; measure scrape duration with 50 fake targets.
7. **Redfish**: run the DMTF Redfish mockup (or a vendor simulator/BMC if available); implement the client with session login/logout, discovery, power state, temperatures; add task polling for a simulated long action; list sessions and prove a leaked session consumes a slot.
8. **Fan-out**: query 200 simulated BMCs with a thread pool of 16 and then asyncio with a semaphore; inject failures and slow hosts; compare wall time and verify per-host isolation and the summary line.
9. **Agent**: write a node agent with SIGTERM/SIGHUP handling, jittered loop, `/metrics`, a systemd unit with resource limits; kill -TERM mid-cycle and confirm clean exit; run under `systemd-run` to test limits.
10. **Packaging**: build a wheel, install with `pipx`, build a zipapp with `shiv`, build a container; compare size and startup time; add `--version` with git SHA.
11. **Profiling**: introduce a deliberate O(n^2) loop and a memory leak into the tool; find them with py-spy and tracemalloc.
12. **Clean up.**

## 12. Common mistakes

- No timeouts on HTTP calls or subprocesses; hanging scripts in cron and CI.
- Retrying non-idempotent calls or permanent errors; retries without jitter causing thundering herds; unbounded retry loops.
- Secrets in command-line arguments, logs, or exception messages.
- Printing logs and data to the same stream, breaking pipelines.
- Silent pagination truncation; offset pagination over changing data.
- One host's exception aborting the whole fleet run; or the opposite, swallowing all errors and exiting 0.
- Exporters that do slow work in the scrape path without timeouts, emit unbounded label values, expose stale values forever, or raise from `collect()`.
- Leaking BMC sessions; hard-coding Redfish paths; assuming schemas are identical across vendors; ignoring self-signed TLS without a plan (disable verification only in labs).
- Zombie subprocesses and orphaned children after timeouts.
- Agents that execute remote commands without authentication and validation; agents without memory or CPU limits that disturb training jobs.
- Shipping scripts by copying files to hosts with no versioning or dependency control.

## 13. Interview angles

- "Design a CLI to drain GPU nodes safely at scale." (dry-run, idempotency, concurrency limits, health gating, exit codes, audit log.)
- "How do you make an API client resilient?" (timeouts, retry classification, backoff with jitter, breaker, pagination, idempotency keys.)
- "Write or describe a Prometheus exporter. What are the pitfalls?" (collector at scrape time, `up` metrics, cardinality, naming, timeouts.)
- "How do you query hardware health out of band?" (Redfish: sessions, discovery, tasks, vendor differences, security.)
- "Your script hangs on one host. How do you prevent that?" (timeouts, process groups, isolation, bounded pools.)
- "How would you distribute a Python tool to 1,000 hosts?" (wheel + pipx, zipapp, packages via config management, containers; version pinning.)
- "A Python service's memory grows steadily. How do you find the leak?" (tracemalloc/memray, retained references, caches, label growth.)

## Exercises

1. **CLI Design (`argparse`, Click, Typer), Stream Separation, Exit Codes, and `csv-linter` (`PM` Chapter 11):** (a) Using `build_gpuctl_parser()`, `zero_count_columns()`, `unnamed_columns()`, and `carriage_returns()` in `code/part03/python_clis_agents_exporters.py`, explain why `main(argv=None) -> int` accepts an injectable `argv` list, why logs go to `stderr` while `--output json|table` goes to `stdout`, and how `csv-linter` detects empty columns, `Unnamed: 0` index columns, and `\r\n` carriage returns; (b) state the configuration precedence order (CLI flags > env vars > config file > defaults) and why secrets must never be passed as CLI flags.
2. **Resilient HTTP Clients: 4-Part Timeouts, Jittered Retries (`tenacity`), Circuit Breakers, and Cursor Pagination:** Using `CircuitBreaker` and `paginate_cursor()` in `code/part03/python_clis_agents_exporters.py`, explain: (a) which HTTP methods and status codes (`429, 502, 503, 504` vs `400, 401, 403, 404, 409`) are safe to retry with exponential backoff and full jitter; (b) how a circuit breaker transitions across `CLOSED -> OPEN -> HALF_OPEN -> CLOSED`; and (c) why cursor/token pagination beats offset pagination over changing datasets.
3. **Prometheus Exporters: Metric Types, Cardinality Rules, Custom Collectors (`collect()`), and Multi-Target Relabelling:** Using `collect_fleet_prometheus_metrics()`, contrast background polling (`Gauge.set`) with scrape-time custom collectors (`FleetCollector.collect()`), explain why `collect()` must emit `fleet_host_up 0` rather than raising an exception when a target fails, and explain how `/probe?target=bmc01` multi-target relabelling works.
4. **DMTF Redfish BMC Client: Session Lifecycle (`X-Auth-Token`), `@odata.id` Link Discovery, and `AllowableValues`:** Using `RedfishSessionClient` and `MockRedfishTransport` in `code/part03/python_clis_agents_exporters.py`, explain why a Redfish client must authenticate via `/redfish/v1/SessionService/Sessions` and `DELETE` its session on `__exit__`, why it must discover system URIs via `Members[@odata.id]` rather than hardcoding `/Systems/1`, and how it validates `ResetType@Redfish.AllowableValues` and tracks `202 Accepted` Task monitors.
5. **GPU Telemetry Parsing (`nvidia-smi` CSV & NVML/DCGM) and Pure Health Rules (`parse_smi_csv`, `evaluate_gpus`):** Using `parse_smi_csv()` and `evaluate_gpus()` in `code/part03/python_clis_agents_exporters.py`, show how separating pure CSV parsing (handling `[N/A]` and `[Not Supported]`) and health rule evaluation (`expected=8`, `max_temp=85`, `ecc_uncorrected > 0`) from SSH/subprocess execution makes fleet diagnostics trivially unit-testable.
6. **Node Agents (`SIGTERM`, Jittered Loops, `systemd` Hardening), Tool Packaging (`pipx`, Zipapps), and Live Profiling (`py-spy`, `tracemalloc`):** (a) Explain how a systemd node agent bounds its impact on GPU training jobs (`MemoryMax=300M`, `CPUQuota=20%`, `NoNewPrivileges=yes`, `ProtectSystem=strict`, `stop.wait(interval + jitter)`); (b) compare `pipx` / `uv tool`, `zipapp`/`shiv`/`pex`, and containers for distributing CLI tools, and explain how `python -X importtime`, `py-spy`, and `tracemalloc` diagnose slow startups and memory leaks.

## Checkpoint questions (20)

<details>
<summary>1. Why must operational CLIs send data to `stdout` and logs/progress bars to `stderr`, and why should `main(argv=None) -> int` accept `argv`?</summary>

Sending structured output (`--output json`) exclusively to `stdout` and human diagnostics/progress bars to `stderr` (`sys.stderr`, `click.echo(..., err=True)`) ensures pipelines like `gpuctl status gpu01 --output json | jq .` never break on interleaved log lines. Defining `def main(argv=None) -> int:` and calling `parse_args(argv)` lets `pytest` invoke `main(["status", "gpu01"])` directly in-process and assert on the returned integer exit code without spawning a subprocess.
</details>

<details>
<summary>2. Compare `argparse`, `Click`, and `Typer`, and explain how `Click`'s `@click.pass_context` and `CliRunner` work.</summary>

- **`argparse`**: standard-library baseline requiring zero third-party dependencies (`add_subparsers(dest="cmd", required=True)`).
- **`Click`**: decorator-based framework (`@click.group()`, `@click.command()`, `@click.option(..., envvar="...")`) that passes shared state (config, output mode) down subcommand trees via `@click.pass_context` (`ctx.obj = ...`) and `@click.pass_obj`, tested in-process via `click.testing.CliRunner().invoke(cli, [...])`.
- **`Typer`**: builds on Click using Python type annotations (`Annotated[int, typer.Option(min=1)]`) to reduce boilerplate and generate shell completions.
</details>

<details>
<summary>3. In *Practical MLOps* Chapter 11, what three CSV dataset bugs does `csv-linter` catch, and why did moving `csv_linter.py` break the entry point?</summary>

1. **`zero_count_columns(df)`:** Columns where `df[key].count() == 0` (such as `'grape'` in `wine.csv` containing 100% `NaN` values).
2. **`unnamed_columns(df)`:** Spurious `'Unnamed: 0'` columns created when pandas exports `df.to_csv("wine.csv")` without `index=False`.
3. **`carriage_returns(df)`:** Embedded Windows `\r\n` (`^M`) line endings inside text fields (`carriage.csv`), reported with the field preview truncated to 50 characters (`field[:50]`).
Moving `csv_linter.py` into `csv_linter/main.py` broke the installed `csv-linter` command because the `console_scripts` wrapper generated in `venv/bin/csv-linter` still pointed to the old `module:function` path until `entry_points` was updated to `csv-linter=csv_linter.main:main` and `pip install -e .` was re-run.
</details>

<details>
<summary>4. What is the configuration precedence order for operational tools, and why must secrets never be passed on the command line?</summary>

Precedence from highest to lowest: **(1) Explicit command-line flags** (`--timeout 30`) -> **(2) Environment variables** (`FLEET_TIMEOUT`) -> **(3) Configuration file** (`~/.config/fleet/config.toml` or `--config`) -> **(4) Code defaults**. Secrets (API tokens, BMC passwords) must **never** be passed as command-line arguments because every user on the host can read `/proc/<pid>/cmdline` (`ps aux`) and shell history files; load secrets from environment variables (`FLEET_TOKEN`), `0600` credential files, or OS/cloud secret stores (or short-lived `gcloud auth print-identity-token` OIDC tokens as in `PM` Chapter 11).
</details>

<details>
<summary>5. Why is a bare `requests.get(url)` dangerous in automation, and what four timeouts does `httpx.Timeout` configure?</summary>

A bare `requests.get(url)` has `timeout=None` by default, meaning a dropped packet or wedged server causes the script or cron job to **hang forever**. `httpx.Timeout(connect=3, read=15, write=15, pool=5)` bounds: (1) **`connect`** (TCP/TLS handshake time), (2) **`read`** (max wait between response chunks), (3) **`write`** (sending request payload), and (4) **`pool`** (waiting for a free connection from the connection pool).
</details>

<details>
<summary>6. Which HTTP methods and status codes should an API client retry, and how does `tenacity`'s `wait_exponential_jitter` work?</summary>

- **Safe methods to retry:** Idempotent methods (`GET`, `HEAD`, `PUT`, `DELETE`, `OPTIONS`) and `POST` requests carrying an `Idempotency-Key` header.
- **Transient status codes/errors to retry:** Network/connection timeouts (`ConnectError`, `ReadTimeout`) and HTTP **`429 Too Many Requests`** (honoring `Retry-After`), **`502 Bad Gateway`**, **`503 Service Unavailable`**, and **`504 Gateway Timeout`**. Never retry deterministic client errors (`400`, `401`, `403`, `404`, `409`, `422`).
- **`wait_exponential_jitter(initial=0.5, max=20)`** combined with `stop_after_attempt(6) | stop_after_delay(60)` backs off exponentially with random jitter so concurrent clients do not synchronize into a retry storm.
</details>

<details>
<summary>7. How do a Circuit Breaker (`CLOSED`, `OPEN`, `HALF_OPEN`) and a Bulkhead protect infrastructure services?</summary>

- **Circuit Breaker:** Tracks consecutive failures to a downstream dependency. In **`CLOSED`** state, requests pass through normally; once consecutive failures reach `failure_threshold`, the breaker trips to **`OPEN`** and fails fast immediately without making network calls for a cool-down window; after the cool-down, it enters **`HALF_OPEN`** and lets a single probe request through—if the probe succeeds, it resets to `CLOSED`, and if it fails, it re-opens.
- **Bulkhead:** Isolates concurrency per target/dependency (via a separate `Semaphore` or thread pool per rack/service) so one slow BMC or API cannot exhaust all worker threads across the tool.
</details>

<details>
<summary>8. Why is silent pagination truncation a common fleet bug, and why is cursor/token pagination preferred over offset pagination?</summary>

Many APIs return at most 100 or 200 items per call; a script that reads `body["items"]` without looping over `next_page_token` silently ignores the rest of the fleet. Wrapping pagination in a generator (`def paginate(path): while True: ... yield item; token = body.get("next_page_token"); if not token: break`) guarantees completeness. **Cursor/token pagination** is preferred over `offset`/`limit` because if items are inserted or deleted while paginating, `offset` shifts and either duplicates or skips records.
</details>

<details>
<summary>9. Name the four core Prometheus metric types, state the metric naming rules, and explain what causes a cardinality explosion.</summary>

- **Types:** (1) **`Counter`** (monotonically increasing cumulative total, suffix `_total`, queried with `rate()`), (2) **`Gauge`** (value that can go up or down, such as temperature or queue depth), (3) **`Histogram`** (bucketed observations `_bucket{le="..."}` plus `_sum` and `_count`, aggregatable across instances for p99 latency), and (4) **`Summary`** (client-side quantiles, not aggregatable).
- **Naming:** `snake_case`, application prefix, and base unit suffix (`gpu_temperature_celsius`, `fleet_scrape_duration_seconds`, `http_requests_total`).
- **Cardinality explosion:** Every unique combination of key-value labels creates a distinct time series in Prometheus TSDB; putting unbounded values (UUIDs, request IDs, user emails, timestamps, or raw error strings) into labels exhausts Prometheus RAM.
</details>

<details>
<summary>10. Why is a scrape-time Custom Collector (`FleetCollector.collect()`) preferred over a background polling loop (`Gauge.set`), and how should `collect()` handle a dead host?</summary>

In a background polling loop, if the polling thread stalls or a host is decommissioned, the `Gauge` continues serving **stale numbers** to Prometheus forever. A **custom collector (`collect()`)** executes fresh on every Prometheus scrape, yielding `GaugeMetricFamily` / `CounterMetricFamily` snapshots with zero lingering series. When a target host times out or fails during `collect()`, the collector **must catch the exception and emit `fleet_host_up{host="..."} 0`** (plus `fleet_scrape_duration_seconds`) rather than raising out of `collect()` and failing the entire scrape.
</details>

<details>
<summary>11. How does the Multi-Target Exporter pattern (`/probe?target=bmc01`) with Prometheus `relabel_configs` work?</summary>

Instead of hardcoding a static list of 500 BMCs inside the exporter's config file, the exporter exposes `/probe?target=<host>`. In Prometheus's `scrape_configs`, `relabel_configs` copies the discovered target's `__address__` (`bmc01.mgmt`) into the URL query parameter `__param_target`, copies `__param_target` into the `instance` label, and rewrites `__address__` to the exporter's address (`bmc-exporter:9102`)—letting Prometheus service discovery and scrape intervals drive per-target probing.
</details>

<details>
<summary>12. What is DMTF Redfish, what are its main `/redfish/v1/` top-level collections, and why must clients follow `@odata.id` links instead of hardcoding paths?</summary>

**Redfish** is the DMTF standard RESTful JSON-over-HTTPS API for out-of-band server management (replacing IPMI). Its service root `/redfish/v1/` links to:
- **`Systems`**: host computer state (power, boot order, BIOS, CPUs, RAM).
- **`Chassis`**: physical enclosure, power supplies, thermal sensors, PCIe/GPU devices.
- **`Managers`**: the BMC itself (network config, event logs, virtual media).
- **`SessionService`, `AccountService`, `UpdateService`, `TaskService`, `TelemetryService`**.
Different vendors use different member IDs (`/redfish/v1/Systems/1` on Dell/Supermicro vs `/redfish/v1/Systems/System.Embedded.1` or `/Systems/Self` on others), so clients must iterate `Members` and follow **`@odata.id`** URIs dynamically.
</details>

<details>
<summary>13. Why should a Redfish client use Session Authentication (`X-Auth-Token`) inside a context manager instead of HTTP Basic Auth, and how are long-running Redfish actions tracked?</summary>

- **Session lifecycle:** Posting credentials to `/redfish/v1/SessionService/Sessions` returns an **`X-Auth-Token`** header and a session `Location` URI (avoiding slow per-request password hashing). Because hardware BMCs enforce a **strict limit on concurrent active sessions** (often 8 to 64), failing to `DELETE` the session URI on exit leaks session slots and locks operators out of the BMC. Wrapping the client in `__enter__`/`__exit__` guarantees session logout.
- **Long-running actions:** Operations like firmware updates (`UpdateService`) return **`HTTP 202 Accepted`** with a `Location` header pointing to a **Task monitor URI**, which the client polls until `TaskState` reaches `Completed` or `Exception`.
</details>

<details>
<summary>14. How should Python tools query `nvidia-smi` or GPU telemetry, and how does the worked capstone separate parsing, rules, and execution?</summary>

Invoke `nvidia-smi --query-gpu=index,name,temperature.gpu,utilization.gpu,memory.used,memory.total,ecc.errors.uncorrected.volatile.total --format=csv,noheader,nounits` (or use `pynvml` / DCGM bindings for frequent polling so NVML is not re-initialized on every subprocess call). In the capstone:
1. **`parsers.py` (`parse_smi_csv`)** is a pure function converting CSV lines into frozen `Gpu` dataclasses (mapping `""`, `"[N/A]"`, and `"[Not Supported]"` to `None`).
2. **`rules.py` (`evaluate_gpus`)** is a pure function checking count (`len(gpus)` differing from `expected`), thermal (`temp_c > max_temp`), and ECC (`ecc_uncorrected > 0`) invariants.
3. **`collect.py` and `cli.py`** handle bounded fan-out, formatting, and distinct exit codes (`0` healthy, `1` runtime error, `3` unhealthy GPU, `4` partial collection failure).
</details>

<details>
<summary>15. How should a long-running node agent structure its main loop, signal handlers, and `systemd` unit to never disturb GPU training jobs?</summary>

- **Jittered interruptible loop:** Handle `SIGTERM` by setting a `threading.Event` (`stop.set()`) and sleep via `stop.wait(interval + random.uniform(0, jitter))` so 1,000 node agents do not hammer the control plane at the exact same second.
- **Per-check isolation:** Wrap each hardware check in its own `try / except` with a timeout and export per-check success metrics plus a `last_success_timestamp_seconds` gauge.
- **`systemd` resource & security hardening:** Set **`MemoryMax=300M`**, **`CPUQuota=20%`**, `User=nodeagent`, `NoNewPrivileges=yes`, `ProtectSystem=strict`, and `ReadWritePaths=/var/lib/nodeagent` so a runaway agent can never starve training jobs of RAM or CPU cores.
</details>

<details>
<summary>16. Compare the six ways to package and distribute operational Python tools across laptops, jump hosts, and air-gapped clusters.</summary>

1. **Wheel on private index + `pipx install fleetctl` / `uv tool install`:** Creates an isolated virtualenv per CLI tool on operator laptops and jump hosts.
2. **Zipapp (`python -m zipapp`, `shiv`, `pex`):** Bundles the application and dependencies into a single executable `.pyz`/`.pex` file for hosts that already have a compatible Python interpreter.
3. **Container image:** Standard for Kubernetes CronJobs/DaemonSets and CI runners.
4. **PyInstaller / Nuitka standalone binary:** Bundles interpreter + extensions for hosts without Python.
5. **OS packages (`.deb` / `.rpm` via `fpm`):** Integrates directly with Ansible, apt/dnf mirrors, and BCM image layers.
</details>

<details>
<summary>17. How do you profile CPU bottlenecks, memory leaks, and slow CLI startup times in Python?</summary>

- **CPU profiling:** Use `python -m cProfile -o out.prof` + `pstats`/`snakeviz` in dev, or attach **`py-spy top -p <PID>` / `py-spy record -o flame.svg -p <PID>`** to a live production process with zero code changes.
- **Memory leaks:** Use **`tracemalloc`** (comparing snapshots to find the exact file:line growing allocations) or `memray`; check for unbounded caches, retained exception tracebacks, and unbounded Prometheus label sets.
- **CLI startup time:** Run **`python3 -X importtime -c "import fleetctl.cli"`** and move heavy imports (`pandas`, `torch`, ` clicks` plugins) inside the specific subcommand function that needs them.
</details>

<details>
<summary>18. Why must mutating CLI subcommands (`drain`, `power`) support `--dry-run`, require `--yes` (or interactive confirmation), and refuse unguarded wildcards?</summary>

At 3 a.m., a typo in a host list or glob pattern can power off an entire rack of 64-GPU training nodes. Making `--dry-run` print the exact target URIs and payloads without executing them, requiring interactive `click.confirm("Drain host?", abort=True)` unless `--yes` is explicitly passed, and rejecting wildcard targets unless `--all-matching` is set prevents catastrophic operator errors.
</details>

<details>
<summary>19. How do you prevent orphaned child processes when a CLI or agent wraps external commands like `dcgmi diag` or `ipmitool` with a timeout?</summary>

When `subprocess.run(cmd, timeout=30)` times out, Python kills only the direct child process—any grandchildren spawned by a wrapper script keep running as orphans holding GPU device files open. Launch external tools in their own process group via **`subprocess.Popen(cmd, start_new_session=True)`** and, on timeout, send `SIGTERM`/`SIGKILL` to the entire process group with **`os.killpg(os.getpgid(p.pid), signal.SIGKILL)`** followed by `p.wait()`.
</details>

<details>
<summary>20. How do you test a Prometheus exporter and a Redfish CLI before deploying them to a 500-node GPU cluster?</summary>

1. **Unit-test pure parsers and collectors:** Feed canned `nvidia-smi` CSV strings (including `[N/A]`, missing GPUs, high temps, and ECC errors) and mock Redfish responses (`MockRedfishTransport` or the **DMTF Redfish Mockup Server**) into your collector/client and assert on metric families, session logout (`active_sessions == 0`), and CLI exit codes via `CliRunner`.
2. **Validate metric syntax and cardinality:** Scrape `/metrics` locally and pipe the output into **`promtool check metrics`** to catch naming, type, and syntax errors before Prometheus scrapes it in production.
</details>

## Sources and review notes

- **Sources read in full:**
  - `practical-mlops` — Noah Gift & Alfredo Deza, *Practical MLOps*, **Chapter 11: Building MLOps Command Line Tools and Microservices** (read in full: packaging Click CLIs with `setup.py` / `requirements.txt` / `console_scripts` entry points and `pip install -e .`, building `csv-linter` with `zero_count_columns`, `unnamed_columns`, and `carriage_returns` on `wine.csv` and `carriage.csv`, and building `cloud-translate` wrapping a serverless Google Cloud Function authenticated via `gcloud auth print-identity-token` and `Authorization: bearer <token>`).
  - `nvidia-devops` (`volume-02/03-python-tooling-operations-masterclass.md`): CLI design with `argparse` and `Click`, testing infrastructure code, resilient clients with retries and backoff, packaging and CI distribution, profiling with `cProfile` and `tracemalloc`, the GPU fleet diagnostics CLI capstone (`parse_smi_csv`, `evaluate`), pagination, subprocess and file-race scenarios, and circuit breakers.
  - `redfish-spec` — DMTF Redfish Specification (`SessionService`, `@odata.id` resource traversal, `Systems`/`Chassis`/`Managers`, `#ComputerSystem.Reset` and `ResetType@Redfish.AllowableValues`, and `202 Accepted` Task monitors), plus Prometheus client library custom collector and multi-target exporter documentation.
- **Run here:** `python3 code/part03/python_clis_agents_exporters_lab.py` (6 passed, 0 failed).
- **Explicitly labelled inferences:** The `gpuctl` `argparse`/`Click`/`Typer` examples, `FleetCollector`, `Redfish` client class, `nodeagent.service` systemd unit, and Section 10 GPU diagnostics capstone are the author's constructions applying *Practical MLOps* Chapter 11, `volume-02`, and the DMTF Redfish specification to GPU cluster operations (plus original study items 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, and 35).
- **Not verified on live hardware:** Live BMC Redfish calls, `nvidia-smi`, `dcgmi diag`, `prometheus_client.start_http_server(9101)`, `promtool check metrics`, and `systemd` service execution (`500` machines, `9101`, `9102`, `600`s, `412 ok, 3 failed`, `300M`, `20%`, `1.4.0`, `85`C) are marked (`untested here`) where not executed by `python_clis_agents_exporters_lab.py`.
