"""Chapter 3.9 model: Testing, benchmarking (`timer.py` / `pybench.py` from
Learning Python Ch. 21), dependency-injected `Drainer` & `FakeKube`, property
round-trip verification, and Testinfra-style host verification.

Sources modeled:
- Mark Lutz, Learning Python, 6th ed. (learning-python-6th-edition, LP),
  Chapter 21 ("The Benchmarking Interlude"):
  * `timer.py` (`once`, `total`, `bestof`, `bestoftotal` using `time.perf_counter`
    and tuple comparison `min(total(reps2, func, *pargs, **kargs) for i in range(reps1))`).
  * `timer2.py` keyword-only `_reps` / `_reps1` configuration.
  * `timer_tests.py` comparing 5 iteration alternatives (`forLoop`, `listComp`,
    `mapCall`, `genExpr`, `genFunc` on `range(10_000)` with `abs(x)` vs `x + 10`).
  * `timeit.repeat` / `pybench.py` (`-n`, `-r`, `-s` setup) and why `min()` of
    repeated runs filters out OS background noise.
- Abdulazeez Abdulazeez Adeshina, Building Python Web APIs with FastAPI
  (building-python-web-apis-with-fastapi, FA), Chapter 8 ("Testing FastAPI
  Applications"): `conftest.py` fixtures and CRUD/auth test suites.
- Bas Meijer et al., Ansible: Up and Running, 3rd ed. (ansible-up-and-running-3rd-edition,
  AUR), Chapter 14 ("Quality Assurance with Molecule"): `yamllint`, `ansible-lint`,
  `ansible-later`, Molecule lifecycle (`create`, `converge`, `idempotence`, `verify`,
  `destroy`), Goss, and `testinfra` (`host.package`, `host.service`, `host.file`,
  `host.user`).
-Len Bass et al., Engineering AI Systems (engineering-ai-systems-architecture-and-devops-essentials,
  EAS), Chapter 2 ("Software Engineering Background"): VMs vs containers, SOA vs
  microservices (Amazon's 2002 API mandate), REST vs GraphQL, Infrastructure as
  Code idempotency testing, and DevOps vs MLOps continuous testing loops.
- volume-02/03-python-tooling-operations-masterclass.md.
"""
import time
from typing import Callable, Dict, Iterable, List, Sequence, Tuple


# 1. LP Ch. 21 Example 21-2 timer2.py: once, total, bestof, bestoftotal
def timer_once(func: Callable, /, *pargs, **kargs) -> Tuple[float, object]:
    """LP Ch. 21: Time a single call using time.perf_counter()."""
    start = time.perf_counter()
    ret = func(*pargs, **kargs)
    elapsed = time.perf_counter() - start
    return elapsed, ret


def timer_total(func: Callable, /, *pargs, _reps: int = 1000, **kargs) -> Tuple[float, object]:
    """LP Ch. 21: Total time for `_reps` calls."""
    total_elapsed = 0.0
    ret: object = None
    for _ in range(_reps):
        elapsed, ret = timer_once(func, *pargs, **kargs)
        total_elapsed += elapsed
    return total_elapsed, ret


def timer_bestof(func: Callable, /, *pargs, _reps: int = 5, **kargs) -> Tuple[float, object]:
    """LP Ch. 21: Minimum time across `_reps` single calls (filters out OS noise)."""
    return min(timer_once(func, *pargs, **kargs) for _ in range(_reps))


def timer_bestoftotal(
    func: Callable,
    /,
    *pargs,
    _reps1: int = 5,
    _reps: int = 100,
    **kargs,
) -> Tuple[float, object]:
    """LP Ch. 21: Best (min) of `_reps1` totals of `_reps` calls each."""
    return min(timer_total(func, *pargs, _reps=_reps, **kargs) for _ in range(_reps1))


# 2. LP Ch. 21 Example 21-4 timer_tests.py: 5 iteration alternatives
def run_five_iteration_alternatives(n: int = 500) -> Dict[str, List[int]]:
    repslist = list(range(-n // 2, n // 2))

    def forLoop() -> List[int]:
        res = []
        for x in repslist:
            res.append(abs(x))
        return res

    def listComp() -> List[int]:
        return [abs(x) for x in repslist]

    def mapCall() -> List[int]:
        return list(map(abs, repslist))

    def genExpr() -> List[int]:
        return list(abs(x) for x in repslist)

    def genFunc() -> List[int]:
        def gen():
            for x in repslist:
                yield abs(x)

        return list(gen())

    return {
        "forLoop": forLoop(),
        "listComp": listComp(),
        "mapCall": mapCall(),
        "genExpr": genExpr(),
        "genFunc": genFunc(),
    }


# 3. Section 3: Dependency-injected Drainer & FakeKube (no real sleeping)
class FakeKube:
    def __init__(self, pods_sequence: Sequence[Sequence[str]]) -> None:
        self.seq = [list(p) for p in pods_sequence]
        self.cordoned: List[str] = []

    def cordon(self, node: str) -> None:
        self.cordoned.append(node)

    def pods_on(self, node: str) -> List[str]:
        return self.seq.pop(0) if self.seq else []


class Drainer:
    def __init__(
        self,
        kube: FakeKube,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.kube = kube
        self.clock = clock
        self.sleep = sleep

    def drain(self, node: str, timeout: float = 600.0) -> int:
        self.kube.cordon(node)
        deadline = self.clock() + timeout
        polls = 0
        while self.kube.pods_on(node):
            polls += 1
            if self.clock() > deadline:
                raise TimeoutError(f"drain timed out on {node}")
            self.sleep(5.0)
        return polls


# 4. AUR Ch. 14 Example 14-8: Testinfra-style host verifier for SSH/node configuration
class FakeTestinfraHost:
    """AUR Ch. 14 Testinfra host fixture double (`host.package`, `host.service`, `host.file`, `host.user`)."""

    def __init__(self) -> None:
        self._packages = {"openssh-server": True}
        self._services = {"sshd": (True, True)}
        self._files = {
            "/etc/ssh/ssh_host_ed25519_key.pub": ("ssh-ed25519 AAAAC3Nza...", "root", "root", 0o644)
        }
        self._users = {"sshd": True}

    def package(self, name: str):
        installed = self._packages.get(name, False)
        return type("Pkg", (), {"is_installed": installed})()

    def service(self, name: str):
        running, enabled = self._services.get(name, (False, False))
        return type("Svc", (), {"is_running": running, "is_enabled": enabled})()

    def file(self, path: str):
        content, user, group, mode = self._files[path]
        return type(
            "FileObj",
            (),
            {
                "contains": lambda self, pat: pat in content,
                "user": user,
                "group": group,
                "mode": mode,
            },
        )()

    def user(self, name: str):
        exists = self._users.get(name, False)
        return type("Usr", (), {"exists": exists})()


def verify_sshd_host(host: FakeTestinfraHost) -> bool:
    """AUR Ch. 14 Example 14-8 Testinfra verification assertions."""
    assert host.package("openssh-server").is_installed
    service = host.service("sshd")
    assert service.is_running
    assert service.is_enabled
    sshd_key = host.file("/etc/ssh/ssh_host_ed25519_key.pub")
    assert sshd_key.contains("ssh-ed25519 ")
    assert sshd_key.user == "root"
    assert sshd_key.group == "root"
    assert sshd_key.mode == 0o644
    assert host.user("sshd").exists
    return True
