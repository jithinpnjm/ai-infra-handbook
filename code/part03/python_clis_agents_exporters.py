"""Chapter 3.8 model: CLI argument parsing (`gpuctl`), CSV dataset linting
(`csv-linter` from Practical MLOps Ch. 11: zero_count_columns, unnamed_columns,
carriage_returns), resilient pagination & circuit breaker, Prometheus custom
collector text exposition, Redfish session/discovery/power client, and
`nvidia-smi` CSV parser + health rule evaluator.

Sources modeled:
- Noah Gift & Alfredo Deza, Practical MLOps (practical-mlops, PM), Chapter 11
  ("Building MLOps Command Line Tools and Microservices"):
  * Click CLI packaging (`setup.py` / `pyproject.toml`, `entry_points` /
    `console_scripts` `csv-linter=csv_linter.main:main`, `editable` `pip install -e .`).
  * `csv-linter` checks on tabular CSV datasets (`wine.csv` / `carriage.csv`):
    `zero_count_columns`, `unnamed_columns` (`Unnamed: 0` when saving pandas DataFrames
    without `index=False`), and `carriage_returns` (`\\r\\n` / `^M` in fields).
  * Cloud CLI (`cloud-translate=trigger:main`) invoking `gcloud auth print-identity-token`
    via `subprocess.Popen` and authenticating with `Authorization: bearer <token>` to
    serverless HTTP Cloud Functions.
- volume-02/03-python-tooling-operations-masterclass.md.
- DMTF Redfish Specification (`redfish-spec`) & Prometheus exporter patterns.
"""
import argparse
from dataclasses import dataclass
from typing import Callable, Dict, Iterator, List, Optional, Sequence, Tuple


# 1. Practical MLOps Ch. 11: csv-linter checks (zero_count_columns, unnamed_columns, carriage_returns)
def zero_count_columns(rows: Sequence[Dict[str, Optional[str]]]) -> List[str]:
    """PM Ch. 11: Return column names where every row is None or empty."""
    if not rows:
        return []
    bad: List[str] = []
    for key in rows[0].keys():
        if all(r.get(key) in (None, "", "NaN") for r in rows):
            bad.append(key)
    return bad


def unnamed_columns(rows: Sequence[Dict[str, Optional[str]]]) -> int:
    """PM Ch. 11: Count columns containing 'Unnamed' (caused by to_csv without index=False)."""
    if not rows:
        return 0
    return sum(1 for key in rows[0].keys() if "Unnamed" in key)


def carriage_returns(rows: Sequence[Dict[str, Optional[str]]]) -> Optional[Tuple[int, str, str]]:
    """PM Ch. 11: Find first (row_index, column_name, truncated_50_char_value) containing '\\r\\n'."""
    for idx, row in enumerate(rows):
        for col, field_val in row.items():
            if isinstance(field_val, str) and "\r\n" in field_val:
                return idx, col, field_val[:50]
    return None


# 2. Section 2.1: gpuctl argparse CLI
def build_gpuctl_parser() -> argparse.ArgumentParser:
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


# 3. Section 3.3 & 3.4: Circuit Breaker and Cursor Paginator
class CircuitBreaker:
    """Three-state circuit breaker (CLOSED -> OPEN -> HALF_OPEN -> CLOSED)."""

    def __init__(self, failure_threshold: int = 3) -> None:
        self.failure_threshold = failure_threshold
        self.failures = 0
        self.state = "CLOSED"

    def call(self, fn: Callable[[], object]) -> object:
        if self.state == "OPEN":
            raise RuntimeError("circuit breaker is OPEN")
        try:
            result = fn()
        except Exception:
            self.failures += 1
            if self.failures >= self.failure_threshold:
                self.state = "OPEN"
            raise
        self.failures = 0
        self.state = "CLOSED"
        return result

    def allow_half_open_probe(self) -> None:
        if self.state == "OPEN":
            self.state = "HALF_OPEN"


def paginate_cursor(fetch_page: Callable[[Optional[str], int], Dict[str, object]], page_size: int = 100) -> Iterator[object]:
    """Section 3.4: Generator yielding all items across cursor-paginated pages."""
    token: Optional[str] = None
    while True:
        body = fetch_page(token, page_size)
        for item in body["items"]:  # type: ignore[index]
            yield item
        token = body.get("next_page_token")  # type: ignore[assignment]
        if not token:
            break


# 4. Section 4.3: Prometheus Custom Collector Exposition
def collect_fleet_prometheus_metrics(
    hosts: Sequence[str],
    read_temps: Callable[[str], Dict[int, float]],
) -> List[str]:
    """Model Section 4.3 FleetCollector: emit gpu_temperature_celsius and fleet_host_up
    without raising when a target host fails.
    """
    lines: List[str] = []
    for h in hosts:
        try:
            temps = read_temps(h)
            for gpu, t in sorted(temps.items()):
                lines.append(f'gpu_temperature_celsius{{host="{h}",gpu="{gpu}"}} {t:.1f}')
            lines.append(f'fleet_host_up{{host="{h}"}} 1')
        except Exception:
            lines.append(f'fleet_host_up{{host="{h}"}} 0')
    return lines


# 5. Section 5.2: Redfish Client Session Lifecycle & OData Discovery
class MockRedfishTransport:
    """Deterministic in-memory DMTF Redfish BMC simulator."""

    def __init__(self) -> None:
        self.active_sessions: Dict[str, str] = {}
        self.power_state = "On"
        self.last_reset: Optional[str] = None

    def post(self, uri: str, json_body: Dict[str, str], token: Optional[str]) -> Tuple[int, Dict[str, str], Dict[str, object]]:
        if uri == "/redfish/v1/SessionService/Sessions":
            sid = f"/redfish/v1/SessionService/Sessions/{len(self.active_sessions) + 1}"
            tok = f"tok-{len(self.active_sessions) + 1}"
            self.active_sessions[sid] = tok
            return 201, {"X-Auth-Token": tok, "Location": sid}, {"Id": "1"}
        if token not in self.active_sessions.values():
            raise PermissionError("401 Unauthorized")
        if uri == "/redfish/v1/Systems/System.Embedded.1/Actions/ComputerSystem.Reset":
            self.last_reset = json_body["ResetType"]
            return 200, {}, {"TaskState": "Completed"}
        raise KeyError(uri)

    def delete(self, uri: str, token: Optional[str]) -> int:
        if token in self.active_sessions.values() and uri in self.active_sessions:
            del self.active_sessions[uri]
            return 200
        raise PermissionError("401 Unauthorized")

    def get(self, uri: str, token: Optional[str]) -> Dict[str, object]:
        if token not in self.active_sessions.values():
            raise PermissionError("401 Unauthorized")
        routes: Dict[str, Dict[str, object]] = {
            "/redfish/v1/Systems": {
                "Members": [{"@odata.id": "/redfish/v1/Systems/System.Embedded.1"}]
            },
            "/redfish/v1/Systems/System.Embedded.1": {
                "Id": "System.Embedded.1",
                "PowerState": self.power_state,
                "Status": {"Health": "OK"},
                "Model": "DGX-H100",
                "Actions": {
                    "#ComputerSystem.Reset": {
                        "target": "/redfish/v1/Systems/System.Embedded.1/Actions/ComputerSystem.Reset",
                        "ResetType@Redfish.AllowableValues": ["On", "ForceOff", "GracefulRestart", "ForceRestart"],
                    }
                },
            },
        }
        return routes[uri]


class RedfishSessionClient:
    """Section 5.2 Redfish client discovering @odata.id links and cleaning up sessions on __exit__."""

    def __init__(self, transport: MockRedfishTransport, user: str, password: str) -> None:
        self.t = transport
        _, headers, _ = self.t.post(
            "/redfish/v1/SessionService/Sessions",
            {"UserName": user, "Password": password},
            token=None,
        )
        self.token: Optional[str] = headers["X-Auth-Token"]
        self.session_uri = headers["Location"]

    def close(self) -> None:
        if self.token:
            self.t.delete(self.session_uri, self.token)
            self.token = None

    def __enter__(self) -> "RedfishSessionClient":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def system(self) -> Dict[str, object]:
        coll = self.t.get("/redfish/v1/Systems", self.token)
        first_uri = coll["Members"][0]["@odata.id"]  # type: ignore[index]
        return self.t.get(first_uri, self.token)

    def power(self, reset_type: str) -> Dict[str, object]:
        s = self.system()
        act = s["Actions"]["#ComputerSystem.Reset"]  # type: ignore[index]
        allowed = act.get("ResetType@Redfish.AllowableValues", [])
        if allowed and reset_type not in allowed:
            raise ValueError(f"{reset_type} not allowed: {allowed}")
        _, _, body = self.t.post(act["target"], {"ResetType": reset_type}, self.token)
        return body


# 6. Section 10: Worked Capstone GPU Fleet Diagnostics Parser & Rules
@dataclass(frozen=True)
class Gpu:
    index: int
    name: str
    temp_c: int | None
    util_pct: int | None
    mem_used_mib: int | None
    mem_total_mib: int | None
    ecc_uncorrected: int | None


def _int(s: str) -> int | None:
    s = s.strip()
    return None if s in ("", "[N/A]", "[Not Supported]") else int(float(s))


def parse_smi_csv(text: str) -> List[Gpu]:
    gpus: List[Gpu] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        f = [x.strip() for x in line.split(",")]
        if len(f) != 7:
            raise ValueError(f"unexpected nvidia-smi columns: {line!r}")
        gpus.append(Gpu(int(f[0]), f[1], _int(f[2]), _int(f[3]), _int(f[4]), _int(f[5]), _int(f[6])))
    return gpus


def evaluate_gpus(gpus: Sequence[Gpu], expected: int = 8, max_temp: int = 85) -> List[str]:
    problems: List[str] = []
    if len(gpus) != expected:
        problems.append(f"expected {expected} GPUs, found {len(gpus)}")
    for g in gpus:
        if g.temp_c and g.temp_c > max_temp:
            problems.append(f"gpu{g.index} temp {g.temp_c}C")
        if g.ecc_uncorrected:
            problems.append(f"gpu{g.index} uncorrected ECC {g.ecc_uncorrected}")
    return problems
