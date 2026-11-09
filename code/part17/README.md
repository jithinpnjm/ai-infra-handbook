# code/part17: what is tested and how

Run everything: `python3 code/part17/operations_lab.py`.

| Kind | How it was checked |
|---|---|
| Operations scripts (capacity, RPO/RTO, backups, checklists, runbooks, game days, notices) | `pytest code/part17/test_part17.py`, including real files for backup/restore and checksum corruption |
| `gpu_alerts.yaml`, `recording_rules.yaml`, `prometheus_scrape.yaml` | `promtool check rules` / `check config` |
| `alertmanager.yaml` | `amtool check-config` |
| Grafana dashboards | JSON parse, and every PromQL expression parsed by promtool |
| DCGM metric names | Compared with the dcgm-exporter source (`DCGM_EXPORTER_SRC`) |
| Kubernetes manifests | kubeconform, strict |
| `snippets/` | Syntax only: need GPUs, PyTorch, Prophet or an OTLP collector |

Notices (announcements, status updates, schedules) are written to a local outbox; nothing is sent to Slack, PagerDuty or email.
Alert rules are syntax-checked, not unit-tested with `promtool test rules`.
