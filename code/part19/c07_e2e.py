#!/usr/bin/env python3
"""End-to-end acceptance test for the observability capstone (Chapter 19.7).

Needs Docker. Standard library only. It starts, on a throwaway Docker network:
  Prometheus 3.16.0   with the platform rules and the Part 20 SLO rules
  Alertmanager 0.35.0 with the real route tree and inhibit rule from
                      c07_alertmanager.yaml (receivers swapped for webhooks)
  Grafana 13.3.0      with the dashboard JSON provisioned from a file
a synthetic exporter and a webhook sink (both in python:3.13-slim containers). It then injects
faults and checks that each one reaches the right receiver.

No GPU, cluster or real receiver is involved. Containers get no privileges, no
Docker socket and no home mount: only the generated config files, read-only.

Usage: python3 c07_e2e.py        (a few minutes)
"""
import copy
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from dataclasses import dataclass

import yaml

import c07_cardinality_budget
import c07_dashboard_check

HERE = pathlib.Path(__file__).resolve().parent
PROM_IMAGE = "prom/prometheus:v3.16.0"
AM_IMAGE = "prom/alertmanager:v0.35.0"
GRAFANA_IMAGE = "grafana/grafana:13.3.0"
PY_IMAGE = "python:3.13-slim"


@dataclass
class Result:
    name: str
    ok: bool
    detail: str = ""


def sh(*args, check=True):
    r = subprocess.run(args, capture_output=True, text=True)
    if check and r.returncode:
        raise RuntimeError(f"{' '.join(args)}: {r.stderr.strip()}")
    return r.stdout.strip()


def http(method, url, body=None, timeout=10):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Content-Type": "application/json"} if data else {})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
        return json.loads(raw) if raw else None


def wait_for(fn, timeout, every=3):
    end = time.time() + timeout
    last = None
    while time.time() < end:
        try:
            last = fn()
            if last:
                return last
        except Exception as e:       # service not up yet
            last = None
            _ = e
        time.sleep(every)
    return last


class Sink:
    """Reads the webhook sink container over its loopback-published port."""
    def __init__(self):
        self.url = None

    def alerts(self, receiver):
        data = http("GET", self.url + "/dump")
        return [a for p in data.get(receiver, []) for a in p.get("alerts", [])]


def am_config_for_test(path):
    """Load the real file and swap every receiver for one webhook at the sink.
    Route tree, inhibit rules and timings stay exactly as written."""
    cfg = yaml.safe_load(pathlib.Path(path).read_text())
    out = copy.deepcopy(cfg)
    out["receivers"] = [{"name": r["name"],
                        "webhook_configs": [{"url": f"http://sink:9200/{r['name']}",
                                             "send_resolved": False}]}
                       for r in cfg["receivers"]]
    return out


def prometheus_yml():
    return {
        "global": {"scrape_interval": "5s", "evaluation_interval": "5s"},
        "rule_files": ["/etc/prometheus/rules/*.yaml"],
        "alerting": {"alertmanagers": [{"static_configs": [{"targets": ["alertmanager:9093"]}]}]},
        "scrape_configs": [
            {"job_name": "synthetic",
             "static_configs": [{"targets": ["synth:9100"],
                                 "labels": {"namespace": "monitoring"}}]},
            {"job_name": "prometheus", "static_configs": [{"targets": ["localhost:9090"]}]},
        ],
    }


def grafana_provisioning(root, dashboard_src):
    (root / "datasources").mkdir(parents=True)
    (root / "dashboards").mkdir()
    (root / "dash").mkdir()
    (root / "datasources" / "ds.yaml").write_text(yaml.safe_dump({
        "apiVersion": 1,
        "datasources": [
            {"name": "Prometheus", "uid": "prometheus", "type": "prometheus",
             "access": "proxy", "url": "http://prometheus:9090", "isDefault": True},
            {"name": "Loki", "uid": "loki", "type": "loki",
             "access": "proxy", "url": "http://loki:3100"},
        ]}))
    (root / "dashboards" / "provider.yaml").write_text(yaml.safe_dump({
        "apiVersion": 1,
        "providers": [{"name": "capstone", "type": "file", "options": {"path": "/var/lib/dash"}}]}))
    shutil.copy(dashboard_src, root / "dash" / "gpu-platform.json")


def open_perms(root):
    for p in [root, *root.rglob("*")]:
        p.chmod(0o755 if p.is_dir() else 0o644)


def published(container, port):
    out = sh("docker", "port", container, f"{port}/tcp").splitlines()[0]
    return int(out.rsplit(":", 1)[1])


def run_e2e(workdir=None):
    results = []

    def record(name, ok, detail=""):
        results.append(Result(name, bool(ok), detail))
        print(("PASS " if ok else "FAIL ") + name + (f"  [{detail}]" if detail and not ok else ""))

    base = pathlib.Path(tempfile.mkdtemp(prefix="c07e2e-", dir=workdir or os.environ.get("C07_E2E_TMP")))
    net = f"c07e2e-{os.getpid()}"
    names = [f"{net}-prom", f"{net}-am", f"{net}-graf", f"{net}-synth", f"{net}-sink"]
    sink = Sink()
    try:
        # ---- generated config ------------------------------------------------
        rules = base / "rules"
        rules.mkdir()
        for f in ("c07_stack_rules.yaml", "c07_e2e_rules.yaml"):
            shutil.copy(HERE / f, rules / f)
        for f in ("slo_recording_rules.yaml", "slo_engine_rules.yaml",
                  "slo_burn_alerts_availability.yaml", "slo_burn_alerts_ttft.yaml",
                  "slo_cause_alerts.yaml"):
            shutil.copy(HERE.parent / "part20" / f, rules / f)
        (base / "prometheus.yml").write_text(yaml.safe_dump(prometheus_yml()))
        am_cfg = am_config_for_test(HERE / "c07_alertmanager.yaml")
        (base / "alertmanager.yml").write_text(yaml.safe_dump(am_cfg))
        grafana_provisioning(base / "grafana", HERE / "c07_dashboard_gpu_platform.json")
        (base / "app").mkdir()
        for f in ("c07_synth_exporter.py", "c07_webhook_sink.py"):
            shutil.copy(HERE / f, base / "app" / f)
        open_perms(base)

        chk = subprocess.run(["amtool", "check-config", str(base / "alertmanager.yml")],
                             capture_output=True, text=True)
        record("amtool accepts the test Alertmanager config", chk.returncode == 0, chk.stderr)

        # ---- containers --------------------------------------------------------
        sh("docker", "network", "create", net)
        common = ["--network", net, "--rm", "-d",
                  "--cap-drop", "ALL", "--security-opt", "no-new-privileges"]
        for i, (script, alias, port) in enumerate((("c07_synth_exporter.py", "synth", 9100),
                                                   ("c07_webhook_sink.py", "sink", 9200))):
            sh("docker", "run", *common, "--name", names[3 + i], "--network-alias", alias,
               "-p", f"127.0.0.1::{port}", "--read-only",
               "-v", f"{base}/app:/app:ro", "-e", "PYTHONDONTWRITEBYTECODE=1",
               PY_IMAGE, "python", f"/app/{script}", str(port))
        ex = f"http://127.0.0.1:{published(names[3], 9100)}"
        sink.url = f"http://127.0.0.1:{published(names[4], 9200)}"
        sh("docker", "run", *common, "--name", names[0], "--network-alias", "prometheus",
           "-p", "127.0.0.1::9090",
           "-v", f"{base}/prometheus.yml:/etc/prometheus/prometheus.yml:ro",
           "-v", f"{rules}:/etc/prometheus/rules:ro", PROM_IMAGE)
        sh("docker", "run", *common, "--name", names[1], "--network-alias", "alertmanager",
           "-p", "127.0.0.1::9093",
           "-v", f"{base}/alertmanager.yml:/etc/alertmanager/alertmanager.yml:ro", AM_IMAGE)
        sh("docker", "run", *common, "--name", names[2], "--network-alias", "grafana",
           "-p", "127.0.0.1::3000",
           "-e", "GF_AUTH_ANONYMOUS_ENABLED=true", "-e", "GF_AUTH_ANONYMOUS_ORG_ROLE=Admin",
           "-v", f"{base}/grafana/datasources:/etc/grafana/provisioning/datasources:ro",
           "-v", f"{base}/grafana/dashboards:/etc/grafana/provisioning/dashboards:ro",
           "-v", f"{base}/grafana/dash:/var/lib/dash:ro", GRAFANA_IMAGE)
        prom = f"http://127.0.0.1:{published(names[0], 9090)}"
        am = f"http://127.0.0.1:{published(names[1], 9093)}"
        graf = f"http://127.0.0.1:{published(names[2], 3000)}"

        def target_up():
            t = http("GET", prom + "/api/v1/targets")["data"]["activeTargets"]
            return all(x["health"] == "up" for x in t) and len(t) == 2
        record("Prometheus scrapes the synthetic exporter and itself", wait_for(target_up, 90))
        rules_ok = wait_for(lambda: all(g["rules"] for g in
                            http("GET", prom + "/api/v1/rules")["data"]["groups"]
                            if g["file"].endswith("c07_stack_rules.yaml")), 30)
        record("Prometheus loaded the platform rules without error", rules_ok)

        # ---- 1. dead man's switch: Watchdog reaches its receiver ------------------
        record("Watchdog reaches the deadman receiver (no page, no ticket)",
               wait_for(lambda: any(a["labels"]["alertname"] == "Watchdog"
                                    for a in sink.alerts("deadman")), 60, 2)
               and not any(a["labels"]["alertname"] == "Watchdog"
                           for r in ("oncall-page", "ticket-queue") for a in sink.alerts(r)))

        # ---- 2. warm up with healthy traffic, then inject faults -------------------
        time.sleep(60)
        http("POST", ex + "/set",
             {"xid": {"node": "n1", "gpu": 0, "value": 79}, "probe": 1, "error_ratio": 1.0})
        t_inject = time.time()

        # Inhibition test, posted straight to Alertmanager: node n2 is NotReady, so its
        # GPU alert must be inhibited. Node n3 has no such alert, so its alert must pass.
        def post_alert(alertname, **labels):
            now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            end = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() + 600))
            http("POST", am + "/api/v2/alerts", [{
                "labels": {"alertname": alertname, **labels},
                "annotations": {"summary": "injected by c07_e2e"},
                "startsAt": now, "endsAt": end}])
        post_alert("KubeNodeNotReady", node="n2", severity="warning")
        post_alert("GPUXidError", node="n2", gpu="0", area="gpu", severity="ticket")
        post_alert("GPUXidError", node="n3", gpu="0", area="gpu", severity="ticket")

        # ---- 3. wait for each fault to reach its receiver ---------------------------
        def has(receiver, alertname, **labels):
            return any(a["labels"].get("alertname") == alertname
                       and all(a["labels"].get(k) == v for k, v in labels.items())
                       for a in sink.alerts(receiver))
        wait_for(lambda: has("oncall-page", "GatewayAvailabilityBurnFast")
                 and has("oncall-page", "SyntheticProbeFiring")
                 and has("ticket-queue", "GPUXidError", node="n1")
                 and has("ticket-queue", "GPUXidError", node="n3"), 150, 3)
        record("synthetic probe reaches the page receiver", has("oncall-page", "SyntheticProbeFiring"))
        record("injected 100 percent errors fire the fast burn alert at the page receiver",
               has("oncall-page", "GatewayAvailabilityBurnFast", model="m1", severity="page"),
               f"after {time.time() - t_inject:.0f}s")
        record("injected Xid 79 reaches the ticket receiver, not the page receiver",
               has("ticket-queue", "GPUXidError", node="n1", gpu="0")
               and not has("oncall-page", "GPUXidError"))
        record("a GPU alert on a healthy node (n3) passes the inhibit rule",
               has("ticket-queue", "GPUXidError", node="n3"))
        time.sleep(35)            # longer than the ticket group_wait, so n2 would have arrived
        record("a GPU alert on the NotReady node (n2) is inhibited",
               not has("ticket-queue", "GPUXidError", node="n2"))
        al = http("GET", am + "/api/v2/alerts")
        n2 = [a for a in al if a["labels"].get("alertname") == "GPUXidError"
              and a["labels"].get("node") == "n2"]
        record("Alertmanager reports the n2 alert as inhibited by KubeNodeNotReady",
               bool(n2) and n2[0]["status"]["state"] == "suppressed" and n2[0]["status"]["inhibitedBy"])

        # ---- 4. Prometheus alert state agrees -----------------------------------------
        active = {a["labels"]["alertname"] for a in
                  http("GET", prom + "/api/v1/alerts")["data"]["alerts"] if a["state"] == "firing"}
        record("Prometheus shows the injected alerts as firing",
               {"GPUXidError", "SyntheticProbeFiring", "GatewayAvailabilityBurnFast"} <= active,
               str(sorted(active)))

        # ---- 5. dashboard as code, through Grafana --------------------------------------
        record("Grafana is healthy", wait_for(lambda: http("GET", graf + "/api/health")["database"] == "ok", 60))
        d = wait_for(lambda: http("GET", graf + "/api/dashboards/uid/gpu-platform"), 30)
        record("Grafana provisioned the dashboard from the file", bool(d) and d["dashboard"]["title"] == "GPU platform overview")
        dash = c07_dashboard_check.load(HERE / "c07_dashboard_gpu_platform.json")
        empty = []
        for label, expr in c07_dashboard_check.prom_expressions(dash):
            if label.startswith("variable"):
                continue
            q = c07_dashboard_check.VAR_RE.sub(
                lambda m: ".+" if m.group(1) == "model" else m.group(0), expr)
            body = {"queries": [{"refId": "A", "datasource": {"type": "prometheus", "uid": "prometheus"},
                                 "expr": q, "instant": True, "intervalMs": 15000, "maxDataPoints": 100}],
                    "from": "now-10m", "to": "now"}
            try:
                res = http("POST", graf + "/api/ds/query", body)["results"]["A"]
                frames = res.get("frames", [])
                rows = sum(len(f["data"]["values"][0]) if f["data"]["values"] else 0 for f in frames)
                if res.get("error") or rows == 0:
                    empty.append(f"{label}: {res.get('error', 'no data')}")
            except Exception as e:
                empty.append(f"{label}: {e}")
        record("every Prometheus panel expression returns data through Grafana", not empty, "; ".join(empty))

        # ---- 6. cardinality on the live exposition ---------------------------------------
        text = urllib.request.urlopen(ex + "/metrics").read().decode()
        ok, errs = c07_cardinality_budget.check_exposition(text)
        record("live exposition passes the label policy", ok, "; ".join(errs))
        head = http("GET", prom + "/api/v1/query?query=prometheus_tsdb_head_series")["data"]["result"]
        record("Prometheus head series is far below the 1,600,000 alert line",
               bool(head) and float(head[0]["value"][1]) < 1_600_000)
    except Exception as e:
        record("e2e run completed without an exception", False, repr(e))
    finally:
        for n in names:
            subprocess.run(["docker", "rm", "-f", n], capture_output=True)
        subprocess.run(["docker", "network", "rm", net], capture_output=True)
        shutil.rmtree(base, ignore_errors=True)
    return results


def main():
    res = run_e2e()
    bad = [r for r in res if not r.ok]
    print(f"{len(res) - len(bad)} passed, {len(bad)} failed")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
