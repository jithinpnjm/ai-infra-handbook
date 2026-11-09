# Post-mortem: slow first token on chat-large (FICTIONAL EXAMPLE)

- Owner: Dana Okoye
- Status: reviewed
- Incident date: 2026-03-14
- Severity: SEV2

## Summary

A config change that cut the KV-cache budget reached one of four replica groups. Requests routed there saw slow first tokens for 40 minutes. We removed the group from the gateway and rolled the config back.

## Impact

About 25 percent of chat-large requests had time to first token above 4 s for 40 minutes. No requests failed and no data was lost. The change used about 18 percent of the 30-day latency error budget.

## Detection

The TTFT p99 alert fired 19 minutes after the rollout began. The alert needed five bad minutes to fire and group B carried only a quarter of traffic, so the global p99 moved slowly.

## Timeline

| Time (UTC) | Event | Marker |
|---|---|---|
| 2026-03-14 09:12 | Rollout of config v42 to replica group B begins | started |
| 2026-03-14 09:31 | Pager fires: TTFT p99 above 4 s for 5 minutes | detected |
| 2026-03-14 09:35 | On-call declares SEV2, takes commander role |  |
| 2026-03-14 09:44 | Preemption counter rising only on group B pods |  |
| 2026-03-14 09:52 | Group B set to weight 0 at the gateway, p99 recovers | mitigated |
| 2026-03-14 10:40 | Config v41 restored on group B, traffic ramped back |  |
| 2026-03-14 11:05 | SLO burn back to normal, incident closed | resolved |

- Time to detect: 19 min
- Time to mitigate: 40 min
- Time to resolve: 113 min

## Root cause and trigger

The trigger was config v42, which lowered the cache budget on group B. The root cause was that our rollout tool promotes a group once pods are Ready, and Ready only checks that the process answers. It does not send a test generation under load.

## What went well

The on-call declared the incident within four minutes of the page. The preemption counter pointed at group B quickly. Weight 0 at the gateway was a one-line, reversible mitigation.

## What went poorly

The alert waited five minutes and measured the global p99, which hid a bad quarter of traffic. The canary stage had no latency gate.

## Where we got lucky

Group B was the smallest group and the change rolled out at off-peak traffic. At peak the same fault would have queued requests on all four groups.

## Action items

| Action | Type | Owner | Due | Measure | Tracking |
|---|---|---|---|---|---|
| Add a latency gate to the canary stage that blocks promotion if TTFT p99 exceeds 1.5 s for 3 minutes | prevent | Dana Okoye | 2026-04-11 | Replay of the 2026-03-14 change is blocked in staging | OPS-1201 |
| Add a per-group TTFT p99 alert with a 2 minute window | detect | Luis Ferreira | 2026-04-04 | Detection time for a synthetic fault in one group is under 5 min | OPS-1202 |
| Write the gateway weight-0 step into the runbook for the TTFT alert | mitigate | Mei Tanaka | 2026-03-28 | Runbook drill completed by a new on-call in under 10 min | OPS-1203 |

