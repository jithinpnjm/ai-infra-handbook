---
id: "c17-14"
title: "17.14 Disaster recovery and data resilience"
sidebar_label: "17.14 Disaster recovery and data resilience"
sidebar_position: 14
description: "Disaster recovery and data resilience for AI infrastructure: the RTO/RPO targets, the backup strategy, the multi-region replication, the ransomware defence, the data lineage for recovery, and the disaster recovery drills that keep the recovery muscle sharp."
status: "drafted"
tier: "2"
level: "A"
lab_venue: "GCP / GKE"
---

# 17.14 Disaster recovery and data resilience

| Field | Value |
|---|---|
| Level | Advanced |
| Priority tier | 2 |
| Lab venue | GCP / GKE |
| Part | Part 17: Observability, performance and operations |
| Cross-references | Chapter 17.11 (Incident response); Chapter 17.13 (Reliability engineering); Chapter 17.6 (Alerting and SLOs); Chapter 13 (AI storage) |
| Coverage file | `planning/coverage/chapters/17-14.md` |
| Claim & number ledger | `planning/ledgers/17-14.md` |

## Disaster recovery at a glance

Imagine the primary region goes dark on a Tuesday afternoon. Your inference service still has to answer requests.

```mermaid
flowchart LR
    subgraph Primary["Primary region"]
        P1[Object storage]
        P2[Model registry]
        P3[Inference service]
    end

    subgraph Secondary["Secondary region"]
        S1[Object storage<br/>replicated]
        S2[Model registry<br/>replicated]
        S3[Inference service<br/>pre-warmed]
    end

    subgraph AirGap["Air-gapped"]
        AG[Immutable backups<br/>object-lock]
    end

    LB[Global load balancer]

    P1 -.replicate.-> S1
    P2 -.replicate.-> S2
    P3 -.replicate.-> S3
    LB --> P3
    LB --> S3
    P1 --> AG
```

Normally the primary region serves all traffic. The secondary region stays pre-warmed, ready to take over, and the air-gapped backup is the last resort.

## Why this matters for AI infrastructure

Chapter 17.13 teaches you how to prevent incidents. This chapter starts where that work stops, when prevention fails and something has to be brought back. Disaster recovery is the discipline that lets a team restore service within a time it agreed on in advance, with a known amount of lost data. For example, a team might aim to be back within 1 hour and lose at most 1 minute of data. Those figures are examples you choose for your own platform, not industry standards.

A disaster is any event that takes the cluster down beyond what the normal recovery steps can handle. It might be a regional outage, a ransomware attack, or a hardware failure that takes out a whole zone. When that happens, the disaster recovery plan is what your team follows, because the usual playbook no longer works.

```text
Why disaster recovery is on the critical path (background reading: NVIDIA Zero-to-Hero volume 19; Production Kubernetes; the figures below are examples, not quotations):
- A typical mature AI platform commits to a 1-hour RTO and a 1-minute RPO for
  critical workloads, and a 4-hour RTO and a 1-hour RPO for standard workloads. The RTO is the recovery time objective; the RPO is the
  recovery point objective. The RTO/RPO are what the business commits to.
- A typical disaster recovery drill catches 1-3 latent failures that would
  have caused an extended outage. Each caught failure is worth 10-100x the
  cost of the drill.
- The data resilience is the foundation of the disaster recovery. Without
  immutable, replicated, encrypted data, the disaster recovery is impossible.
  The data resilience is what makes the recovery possible.
```

The figures in that block are example values too. The claim that a drill catches failures worth 10 to 100 times its cost has no source in this chapter's references. Treat it as a guess until your own drills measure it.

Three things make this a platform-team concern, not only a data-science concern. Each one is work that someone has to own.

1. **The disaster recovery plan is a platform-team deliverable.** The plan sets the time and data targets, names the backup and replication design, and writes the recovery steps. If the platform team does not own it, the plan goes stale.
2. **Data resilience is a platform-team discipline.** Each data store in the cluster needs a backup, a second copy in another place, and encryption. Without all three, the recovery plan has nothing reliable to restore from.
3. **The disaster recovery drill is a platform-team drill.** A drill tests the plan, the backups, and the recovery steps together. Until a drill has run, the plan is only a hypothesis.

**Before a team can claim its AI factory is disaster-resilient, it needs a plan, data resilience, and drills.** A plan without drills is untested. Drills without resilient data have nothing to recover.

## Prerequisites and outcomes

Before you start, make sure the foundations from earlier chapters are in place. This chapter builds directly on them. Each prerequisite supplies a piece you will use in the drills and failover sections, so read any unfamiliar one first.

### Prerequisites

- Chapter 17.11, Incident response, covers the post-mortem and the blameless culture.
- Chapter 17.13, Reliability engineering, covers SLOs and the error budget patterns.
- Chapter 17.6, Alerting and SLOs, covers the alerting stack.
- Chapter 13, AI storage, covers the storage primitives.

### Outcomes

After completing this chapter you will be able to:

1. Set RTO and RPO targets for critical, standard, and development workloads.
2. Build a backup strategy with full backups, incremental backups, and point-in-time recovery.
3. Set up multi-region replication for object storage, the distributed filesystem, and the model registry.
4. Defend against ransomware with immutable backups, object lock, and an audit log.
5. Run a disaster recovery drill from scenario to post-mortem.
6. Operate disaster recovery on GKE with reliable backups, tested replication, and verified drills.

---

## 1. The RTO/RPO targets

### 1.1 The recovery time objective (RTO)

Picture an inference service that stops answering at 2 p.m. on a weekday. Every minute it stays down, customers see errors. The RTO answers one question: how long is the team allowed to take to bring the service back?

The recovery time objective is the longest the service may stay down after a disaster. It is a commitment between the platform team and the business, and it should be written down before a disaster happens.

| Workload tier | RTO | Use case |
|---|---|---|
| Critical (customer-facing) | 1 hour | Inference serving; online learning |
| Standard (internal) | 4 hours | Training pipelines; batch inference |
| Development (experimentation) | 24 hours | Notebooks; experimental workloads |

The table gives example values, not fixed rules. Each tier gets the tightest target its business value justifies. A short RTO costs more, because critical workloads usually need a second region that is already running.

### 1.2 The recovery point objective (RPO)

The RTO is about time. The RPO is about data: how much recent work can you afford to lose? If your newest good copy is an hour old, the data you lost is that hour of writes.

The recovery point objective is the longest window of data that may be lost. Like the RTO, it is a commitment, and it sets how often you must back up or replicate.

| Workload tier | RPO | Use case |
|---|---|---|
| Critical (customer-facing) | 1 minute | Transactional data; inference logs |
| Standard (internal) | 1 hour | Training data; experiment results |
| Development (experimentation) | 24 hours | Notebooks; experimental data |

These values are examples too. An RPO of 1 minute means the copy has to be refreshed about every minute, which a nightly job cannot do.

### 1.3 The RTO/RPO matrix

Put the two targets side by side, and the deployment pattern usually becomes clear. A tight RTO with a tight RPO points toward a multi-region setup. A loose RTO and a loose RPO can often run from a single region with cold backups.

| | RPO 1 minute | RPO 1 hour | RPO 24 hours |
|---|---|---|---|
| **RTO 1 hour** | Critical (multi-region) | Critical (single-region) | N/A |
| **RTO 4 hours** | Critical (warm standby) | Standard (warm backup) | N/A |
| **RTO 24 hours** | Critical (cold standby) | Standard (cold backup) | Development (best effort) |

The N/A cells mark combinations the matrix does not support. Use the matrix to decide which deployment pattern each workload gets, and show the result to the business before you build anything.

---

## 2. The backup strategy

### 2.1 The backup types

A backup you have never restored is only a hope. Start by choosing which kind of backup each dataset needs.

The strategy uses three types. A full backup copies everything, an incremental backup copies only what changed since the last backup, and point-in-time recovery rewinds the data to one chosen moment.

| Backup type | What it captures | When to use |
|---|---|---|
| **Full backup** | The entire dataset | Weekly. The foundation for other backups |
| **Incremental backup** | The changes since the last backup | Daily. The supplement to the full backup |
| **Point-in-time recovery** | The state at a specific timestamp | As needed. The recovery from accidental deletion |

The cadence in this table is an example. Choose your own from the RPO you committed to, because a daily backup cannot protect data you need back within an hour.

### 2.2 The backup targets

Think about what the cluster stores. Model files and datasets live in object storage, the cluster's own state lives in etcd and Kubernetes secrets, and MLflow and Feast keep their records in PostgreSQL. Each target needs a backup method that fits it.

Production Kubernetes, chapter 2, takes the same view of cluster state. It recommends direct etcd snapshots together with Velero backups taken through the Kubernetes API. Production Kubernetes, chapter 4, adds that Velero supports backup and restore hooks, such as flushing a database before a backup runs.

| Target | Backup method | Retention |
|---|---|---|
| Object storage | Object versioning + cross-region replication | 90 days |
| Distributed filesystem | Snapshot + cross-region replication | 30 days |
| Kubernetes etcd | etcd snapshot | 30 days |
| Kubernetes secrets | Backup + encryption | 30 days |
| MLflow database | PostgreSQL backup | 30 days |
| Feast database | PostgreSQL backup | 30 days |

The retention periods are starting points. Regulators and your own audit rules decide the real numbers, so check them before you copy these values.

### 2.3 The backup verification

Verification is what proves a backup works. Restore it into staging, compare the result with the original, and measure how long the restore took.

```bash
# Restore the backup to staging
python code/part17/restore_backup.py \
  --backup backup-2024-03-15 \
  --target staging

# Verify the backup
python code/part17/verify_backup.py \
  --backup backup-2024-03-15 \
  --expected-rto 4h \
  --expected-rpo 1h
# expected: the backup restores within the RTO; the backup's data loss is within the RPO
```

The expected line is a pass condition, not a report. After each restore, ask whether the team could meet the RTO with this exact procedure.

---

## 3. Multi-region replication

### 3.1 Object storage replication

Suppose a bucket in the primary region receives new model artifacts every hour. If that region fails, those artifacts are stranded. Replication copies each new object to a second region without anyone starting a job.

The copy runs asynchronously, so it can trail the original. That delay is the replication lag, and it counts against your RPO.

```bash
# Copy the primary bucket to a second region every hour with Storage Transfer Service
# (gsutil has no replication command; a dual-region or multi-region bucket replicates by itself)
gcloud transfer jobs create gs://primary-bucket gs://secondary-bucket --schedule-repeats-every=1h
# expected: a transfer job that copies new objects each hour; the interval sets the worst-case lag
```

The lag here is bounded by the schedule you choose. A dual-region bucket replicates continuously instead, so measure the lag you actually get and compare it with your RPO.

### 3.2 Distributed filesystem replication

Synchronous replication waits for the second copy before it confirms a write. Asynchronous replication confirms first and copies later. Asynchronous mode is faster, but it can lose the newest writes if the primary fails.

```bash
# Lustre has no single replication command. Common options are changelog-driven copy
# (the lustre_rsync tool) or an HSM archive tier. Check your Lustre version's manual for the exact syntax.
# expected: the secondary filesystem trails the primary; measure that lag against your RPO
```

The expected line says the lag is under five minutes. Measure that on your own filesystem before you rely on it.

### 3.3 Kubernetes state replication

Etcd copies its data between control-plane members, so one failed member is survivable. A bad command is copied to every member too, so a snapshot is still needed.

Multi-region Kubernetes state needs more setup, such as KubeFed or cluster API federation.

```bash
# Configure etcd snapshot
etcdctl snapshot save /backup/etcd-snapshot.db
# expected: the etcd snapshot is saved
```

---

## 4. Ransomware defence

### 4.1 Immutable backups

Picture an attacker with admin rights who wants to erase your backups before encrypting the data. An immutable backup defends against exactly that. Once written, it cannot be changed or deleted until its retention period ends.

The storage service enforces that rule, not your scripts. S3 Object Lock and GCS Bucket Lock are two examples of this mechanism.

```bash
# Configure object lock on the audit log bucket
gsutil retention set 90d gs://audit-log-bucket
# expected: the bucket has a 90-day retention; the objects cannot be deleted before 90 days
```

The expected line says the bucket keeps objects for 90 days. Choose the period from your recovery needs and retention rules, not from this example.

### 4.2 Air-gapped backups

An air gap is a boundary the attacker cannot cross from the cluster. A bucket that the cluster's own account can write to is not truly air-gapped, because the same credentials may reach it. The example below copies a backup, but that step alone does not create the gap.

```bash
# Copy the backup to an air-gapped bucket
gsutil cp /backup/2024-03-15.tar.gz gs://air-gap-bucket/
# expected: the backup is in the air-gapped bucket; the air-gapped bucket is not connected to the cluster
```

Design the isolation as separate work, with separate accounts or projects and separate credentials. The copy step only moves the data.

### 4.3 The audit log as a ransomware defence

When an attack happens, you need to know who deleted what, and when. The audit log answers that question, but only if an attacker cannot edit it, so keep it in locked storage.

```bash
# Query the audit log for suspicious activity
bq query --use_legacy_sql=false \
  "SELECT timestamp, user, action, object
   FROM \`${PROJECT_ID}.audit.events\`
   WHERE action = 'delete' AND object LIKE 'backup/%'
   ORDER BY timestamp DESC LIMIT 100"
# expected: a list of recent backup deletions; the audit log proves what happened
```

Run a query like this on a schedule. Alert when it returns deletions you did not expect, because a burst of backup deletions is an early sign of trouble.

---

## 5. Disaster recovery drills

### 5.1 The drill plan

Think of a drill as a rehearsal with a script. Before anyone starts, you write down the disaster, the event that triggers it, the response you expect, and how you will judge success.

Drills test the plan itself. Each one needs a scenario, such as a regional outage, a ransomware attack, or a hardware failure, plus an injected fault, an expected response, and success criteria.

```markdown
# Disaster Recovery Drill: Regional Outage

## Scenario
The primary region's data center suffers a power outage; all GPUs in the primary region are unavailable.

## Injection
At 14:00 UTC, we will simulate a regional outage by draining all nodes in the primary region.

## Expected response
- 14:00: Alert fires
- 14:05: On-call acknowledges the alert
- 14:10: IC is declared
- 14:15: Failover is initiated
- 14:30: Workloads are running in the secondary region
- 14:45: SLO is met in the secondary region
- 15:00: Drill is complete

## Success criteria
- The RTO is met (1 hour for critical workloads)
- The RPO is met (1 minute for critical workloads)
- The failover is automatic
- The SLO is met in the secondary region
```

The times in this template are examples. Set timings that fit your own on-call rota and change windows.

For the most critical workloads, Production Kubernetes, chapter 2, suggests going further. List the ways things can fail, automate recovery for each one, and then test those recoveries. It also suggests a standby cluster to fail over to, with the failover automated and tested.

### 5.2 The drill execution

On drill day, the team follows the script, and someone records each action with its time. A timeline written during the drill is more accurate than one rebuilt from memory afterwards.

```bash
# Schedule the drill
python code/part17/schedule_drill.py \
  --date "2024-04-15" \
  --time "14:00 UTC" \
  --scenario "Regional Outage"

# Execute the drill
python code/part17/execute_drill.py \
  --scenario "Regional Outage"
```

Keep the drill ID, the scenario name, and the schedule in one place, so the post-mortem can refer to them later.

### 5.3 The drill post-mortem

Every drill ends with a post-mortem. It records what was tested, what worked, what did not, and what the team will change. The post-mortem is where the value of the drill is kept.

```markdown
# Disaster Recovery Drill Post-Mortem: Regional Outage

## What was tested
- Failover from primary region to secondary region
- RTO compliance
- RPO compliance
- SLO compliance in the secondary region

## What worked
- The failover was automatic
- The RTO was met (45 minutes)

## What did not work
- The RPO was missed: 5 minutes of data were lost against a 1-minute target
- The IC was not declared within 15 minutes
- The runbook was missing the failover procedure for the registry

## Action items
- Add the IC declaration to the alerting (Owner: platform-team, Due: 2024-04-30)
- Update the runbook with the registry failover (Owner: platform-team, Due: 2024-04-22)
- Shorten the backup cadence to meet the 1-minute RPO (Owner: platform-team, Due: 2024-05-15)
```

Give each action item one owner and one due date. Without both, an action item tends to stay open with nobody responsible for it.

---

## 6. Operating disaster recovery on GKE

### 6.1 The components

Running disaster recovery on GKE means several pieces must work together. Object storage, replication, the etcd snapshot job, and the verification and drill schedulers each have a job. The table shows what each piece does and what it is expected to achieve.

| Component | Where it runs | Backing store | SLO |
|---|---|---|---|
| Object storage with versioning | Managed (GCS) | Object storage | Versioning enabled |
| Object lock | Managed (GCS) | Object storage | Lock retention 90 days |
| Cross-region replication | Managed (GCS) | Object storage | Replication lag < 1 minute |
| etcd snapshot | Kubernetes Deployment | Object storage | Snapshot frequency 6 hours |
| Backup verification | CronJob | (verifies the backup) | Verification frequency 30 days |
| DR drill scheduler | CronJob | (schedules the drill) | Drill frequency 90 days |

The SLO column holds example targets. Replace each one with a value you actually measure, and write it down where the team can see it.

### 6.2 IAM and the disaster recovery

The recovery stack needs its own access rules. Backups are only as safe as the people and services that can change them. Give each role only the rights it needs.

| Role | Who | What they can do |
|---|---|---|
| `dr.reader` | Every team | Read the backup status; read the RTO/RPO |
| `dr.writer` | The platform team | Create backups; restore backups |
| `dr.admin` | The platform team lead | Approve the DR plan; approve the failover |

Write down who holds each role, and review that list every quarter. A quarterly review is an example cadence, so choose the one your team can keep.

### 6.3 Observability

Dashboards show whether the plan is still true today. Track the metrics below, and alert when a value leaves its safe range.

| Metric | Why it matters | Alert |
|---|---|---|
| RTO last drill | DR readiness | > RTO target |
| RPO last drill | DR readiness | > RPO target |
| Backup age | DR freshness | > 24 hours |
| Backup verification age | DR readiness | > 30 days |
| Object storage replication lag | DR readiness | > 5 minutes |
| Object lock age | DR readiness | < 30 days remaining |

The two drill metrics matter most. A drill that misses the RTO target has found a gap in the plan. A drill that misses the RPO target has shown data you would have lost.

Put the RTO and RPO from your last drill on the team dashboard first. Everything else in this table is easier to act on once those two numbers are visible.

---

## 7. How it fails

Six failure modes are worth checking for. Each one below gives the symptom you will see, the usual diagnosis, and the fix.

### 7.1 "The backup is corrupted"

**Symptom:** The team tries to restore a backup and finds it corrupted, so recovery stops.

**Diagnosis:** Nobody verified the backup, it lived on a single disk, and its checksum does not match.

**Fix:** Verify backups on a schedule, keep copies on more than one disk, and check the checksum before you restore.

### 7.2 "The RTO is exceeded"

**Symptom:** A real disaster hits, recovery starts, and it takes longer than the RTO allows.

**Diagnosis:** The runbook is out of date, nobody has rehearsed it, and the failover is manual.

**Fix:** Update the runbook, rehearse it on a schedule, and automate the failover where you can.

### 7.3 "The RPO is exceeded"

**Symptom:** Recovery finishes, but the data is older than the RPO allows, so customer records are missing.

**Diagnosis:** Backups run too rarely, replication lags too far behind, or the newest backup is too old.

**Fix:** Run backups more often, reduce the replication lag, and keep enough history to choose a good restore point.

### 7.4 "The ransomware deletes the backups"

**Symptom:** The attack succeeds, the backups are gone, and the team has nothing to restore.

**Diagnosis:** The backups were mutable, they were not air-gapped, and the audit log could be edited.

**Fix:** Turn on object lock for the backup bucket, air-gap the most critical backups, and make the audit log tamper-evident.

### 7.5 "The failover does not work"

**Symptom:** The team starts the failover, it fails partway, and the service stays down.

**Diagnosis:** The failover was never tested, a dependency is missing in the secondary region, and the runbook is wrong.

**Fix:** Test the failover on a schedule, confirm every dependency exists in the secondary region, and correct the runbook after each test.

### 7.6 "The disaster recovery drill is skipped"

**Symptom:** The team has not drilled for 6 months, so nobody is sure what to do first.

**Diagnosis:** No drill schedule exists, the team is busy, and drills are not a priority.

**Fix:** Put drills on a calendar, automate the scheduling, and add drills to the team's objectives.

Pick the failure mode your team is least ready for, and write its runbook step this week.

---

## 8. Hands-on lab

Run this lab in a test project, never in production, and run the steps in order. The lab is **untested** in this repository, so treat each command as a draft until you have run it yourself.

### 8.1 Prerequisites

- A GKE Autopilot or Standard cluster (1.27+) with at least 4 H100 GPU nodes.
- The observability stack from earlier chapters.
- A second GKE cluster in a different region for multi-region testing.

### 8.2 Step 1: configure the backup strategy

Turn on versioning first, so an overwritten object keeps its earlier copy. Then lock the backup bucket and set up replication from the cluster's artifact bucket.

```bash
# Enable object versioning on the cluster's object storage bucket
gsutil versioning set on gs://cluster-artifacts

# Configure object lock on the backup bucket
gsutil retention set 90d gs://backup-bucket

# Enable cross-region copy (Storage Transfer Service; gsutil has no replication command)
gcloud transfer jobs create gs://cluster-artifacts gs://backup-bucket --schedule-repeats-every=1h
```

This is the same Storage Transfer Service approach as in section 3, with the same lag caveat.

### 8.3 Step 2: schedule regular backups

Scheduling is what turns these commands into a backup strategy. The first command copies the bucket once, into a folder dated today. The etcd CronJob then runs the snapshot on its own schedule.

```bash
# Schedule a daily backup
gsutil cp -r gs://cluster-artifacts gs://backup-bucket/daily/$(date +%Y-%m-%d)/

# Schedule etcd snapshots
kubectl apply -f code/part17/etcd_snapshot_cronjob.yaml
```

Without a scheduler, these commands run only when someone remembers to run them.

### 8.4 Step 3: verify the backup

Restore the backup to a separate staging bucket, then verify the restored copy. A backup that restores but fails verification cannot be used for recovery.

```bash
# Restore the backup to staging
gsutil -m cp -r gs://backup-bucket/daily/2024-03-15/ gs://staging-restore/

# Verify the backup
python code/part17/verify_backup.py \
  --backup daily-2024-03-15 \
  --expected-rto 4h \
  --expected-rpo 1h
```

### 8.5 Step 4: simulate a regional outage

This step simulates a regional outage by draining all nodes in the primary region. Watch the Pods during the drill, and confirm where the workloads run.

```bash
# Draining all nodes in the primary region (cordon alone does not move running Pods)
for node in $(kubectl get nodes -l topology.kubernetes.io/region=us-central1 -o name); do
  kubectl drain $node --ignore-daemonsets --delete-emptydir-data
done

# Observing the failover
kubectl get pods -n mlops -w
# expected: the workloads are rescheduled to the secondary region
```

### 8.6 Step 5: measure the RTO and RPO

Measure the RTO and RPO from timestamps, not from memory. The second command misses its target, and that is the point of the example.

```bash
# Measure the RTO
python code/part17/measure_rto.py \
  --incident-start "2024-03-15T14:00:00Z" \
  --incident-end "2024-03-15T14:45:00Z"
# expected: RTO is 45 minutes; RTO is within the 1-hour target

# Measure the RPO
python code/part17/measure_rpo.py \
  --last-backup "2024-03-15T13:55:00Z" \
  --disaster-time "2024-03-15T14:00:00Z"
# expected: RPO is 5m; OUTSIDE the 1m target (exit code 1), so the backup cadence must improve
```

A 5-minute gap is larger than a 1-minute target, so the RPO was missed. The backup cadence has to improve before the target can be met. The post-mortem in Section 5.3 records the miss in the same way.

### 8.7 Step 6: write the drill post-mortem

Turn the timeline into a post-mortem with the generator below. It writes a draft from the drill ID, and you complete the lessons yourself.

```bash
python code/part17/generate_dr_post_mortem.py \
  --drill-id DR-2024-03-15 \
  --output dr_post_mortem.md
```

### 8.8 What to record

Finish the lab by answering five questions.

1. What is the current RTO target per workload tier?
2. What is the current RPO target per workload tier?
3. When was the last backup verification?
4. What was the RTO and RPO in the last disaster recovery drill?
5. What is the object-lock retention on the backup bucket?

The 30-second limit is a choice for your team, not a standard. Still, an answer that takes longer usually means the information lives in someone's head instead of in a document. The lab is **untested** against a live GKE cluster.

---

## Exercises

1. **Add a backup verification cron job.** Configure a CronJob that verifies the backup monthly. *Solution sketch:* Use a Kubernetes CronJob that restores the backup to staging, measures the RTO and RPO, and reports the results.
2. **Add a multi-region failover drill.** Schedule a quarterly drill that tests the multi-region failover. *Solution sketch:* Write a Chaos Mesh experiment that cordons all nodes in the primary region. The drill measures the failover latency and produces a post-mortem.
3. **Add a ransomware defence drill.** Schedule a quarterly drill that tests the ransomware defence. *Solution sketch:* Use a Chaos Mesh experiment that simulates a ransomware attack. The drill checks that the immutable backups are untouched, then produces a post-mortem.
4. **Add an air-gapped backup bucket.** Configure a bucket in a separate network, and copy the most critical backups into it. *Solution sketch:* Create a separate GCP project with its own VPC, then copy the backup into the air-gapped bucket there.
5. **Add a backup age alert.** Configure an alert that fires when the newest backup is older than 24 hours. *Solution sketch:* Write a Prometheus alert on backup age, and route it to the on-call engineer.
6. **Add a disaster recovery runbook.** Build a runbook for the regional outage scenario, and test it quarterly. *Solution sketch:* Write a Markdown document that describes the scenario, and use it as the default for every drill.

Start with exercise 1. A verification job tells you whether the rest of the plan can be trusted. If you have limited time, do exercise 5 next, because you need to know when your backups stop arriving.

---

## Checkpoint questions

<details><summary>1. The primary region goes dark on a Tuesday afternoon and the inference service must still answer. What should already be in place?</summary>
A secondary region with replicated object storage and model registry, and a pre-warmed inference service. A global load balancer can then send traffic to it. An air-gapped copy of immutable backups sits behind as the last resort.
</details>

<details><summary>2. An attacker with admin rights tries to erase your backups before encrypting the data. Which defences stop that, and what do you check afterwards?</summary>
Immutable backups with object lock cannot be changed or deleted until retention ends, and the storage service enforces that rule. An air-gapped copy sits outside what the cluster's credentials can reach. Afterwards query the audit log for backup deletions, and keep that log in locked storage so it cannot be edited.
</details>

<details><summary>3. During a real recovery you find the backup is corrupted. What does the chapter say went wrong, and what is the fix?</summary>
Nobody verified the backup, it lived on a single disk, and its checksum does not match. Verify backups on a schedule, keep copies on more than one disk, and check the checksum before you restore.
</details>

<details><summary>4. A drill post-mortem says "the RPO was met (5 minutes)" for a critical workload whose RPO is 1 minute. Is that statement correct?</summary>
No. Five minutes of lost data is larger than a 1-minute target, so the RPO was missed. The lab's sample output shows the same 5-minute gap as outside the target, so a post-mortem should list it under what did not work and add an action to shorten the backup cadence.
</details>

<details><summary>5. Recovery finishes but customer records are missing because the data is older than the RPO. What do you look at?</summary>
Backups may run too rarely, replication may lag too far behind, or the newest backup may be too old. Run backups more often, reduce the replication lag, and keep enough history to choose a good restore point.
</details>

<details><summary>6. A failover starts, fails partway, and the service stays down. What does the chapter say usually caused it?</summary>
The failover was never tested, a dependency is missing in the secondary region, and the runbook is wrong. In the example drill the runbook was missing the failover procedure for the registry. Test the failover on a schedule, confirm every dependency exists in the secondary region, and correct the runbook after each test.
</details>

<details><summary>7. Why can a nightly job not meet a 1-minute RPO?</summary>
The RPO sets how often you must back up or replicate. A 1-minute RPO means the copy has to be refreshed about every minute. A nightly job leaves up to a day of changes uncopied.
</details>

<details><summary>8. Why does replication lag count against your RPO?</summary>
Replication runs asynchronously, so the copy can trail the original. If the primary fails, everything written during that lag is missing from the copy. The lag is therefore data you would lose.
</details>

<details><summary>9. Why does the lab drain every node instead of only cordoning them?</summary>
Cordon alone does not move running Pods. Drain evicts the workloads so they are rescheduled, which is what a regional outage forces. A drill that only cordoned would not test the failover.
</details>

<details><summary>10. Why is a bucket the cluster's own account can write to not truly air-gapped?</summary>
An air gap is a boundary the attacker cannot cross from the cluster. If the same credentials reach the bucket, an attacker who controls the cluster may reach it too. The isolation has to be designed separately, with separate accounts or projects and separate credentials.
</details>

<details><summary>11. Why do you still need an etcd snapshot when etcd copies data between control-plane members?</summary>
Replication means one failed member is survivable. A bad command is copied to every member as well, so all copies are damaged. A snapshot gives you a point to restore from.
</details>

<details><summary>12. A workload is customer-facing. Do you give it the 1-hour RTO tier or the 4-hour tier, and what do you give up?</summary>
Give a critical customer-facing workload the 1-hour tier. The cost is that a short RTO usually needs a second region that is already running. Internal training pipelines fit the 4-hour tier and cost less. These values are examples.
</details>

<details><summary>13. Would you choose synchronous or asynchronous replication for the distributed filesystem, and what do you give up?</summary>
Synchronous waits for the second copy before confirming a write, so it loses nothing but is slower. Asynchronous confirms first and copies later, so it is faster but can lose the newest writes if the primary fails. Choose from the RPO you committed to, and measure the lag you actually get.
</details>

<details><summary>14. When would you pick a multi-region setup over a cold standby in the RTO and RPO matrix?</summary>
Pick multi-region when you need an RTO of 1 hour and an RPO of 1 minute. A cold standby suits an RTO of 24 hours with a 1-minute RPO. You give up the running cost of a second region in exchange for speed. Show the matrix result to the business before you build.
</details>

<details><summary>15. For copying a bucket to a second region, would you use an hourly Storage Transfer job or a dual-region bucket?</summary>
An hourly job bounds the lag by its schedule, so the worst case is about an hour. A dual-region bucket replicates continuously. Measure the lag you actually get and compare it with your RPO before you decide.
</details>

<details><summary>16. A drill starts at 14:00 and workloads are healthy at 14:45. The critical RTO target is 1 hour. Was it met, and by how much?</summary>
Yes. From 14:00 to 14:45 is 45 minutes. The target is 60 minutes, so the drill finished 15 minutes inside it.
</details>

<details><summary>17. The last backup was at 13:55 and the disaster at 14:00. The RPO target is 1 minute. By how much was it missed?</summary>
The data loss window is 14:00 minus 13:55, which is 5 minutes. The target is 1 minute. It was missed by 4 minutes.
</details>

<details><summary>18. A transfer job copies a bucket every hour and the RPO is 1 minute. How far off is the worst case?</summary>
Data written just after a copy waits a full hour for the next one. That is 60 minutes against a 1-minute RPO, so 60 times too long. A schedule of this kind cannot meet that target.
</details>

<details><summary>19. You restore a backup into staging. What do you do first, second, and third to know it is usable?</summary>
First restore it into staging. Second compare the result with the original and run the verification script against the expected RTO and RPO. Third measure how long the restore took and ask whether the team could meet the RTO with this exact procedure.
</details>

<details><summary>20. You suspect backups are being deleted. In what order do you investigate?</summary>
First query the audit log for delete actions on backup objects. Second check whether object lock still protects the backup bucket and how many days of retention remain. Third confirm the air-gapped copy is intact, since it is the last resort.
</details>

---

## Sources and review notes

- NVIDIA Zero-to-Hero Volume 19, in the file `chapter-10-disaster-recovery.md`, supplied the disaster recovery patterns and the RTO and RPO framework. The handbook rewrote the wording.
- *Production Kubernetes* (`production-kubernetes`, Chapter 14), supplied the Kubernetes-level disaster recovery patterns.
- *Production Kubernetes*, chapters 2 and 4, supplied the points on backing up cluster state, standby clusters, and Velero hooks used in sections 2 and 5.

### Cross-references to other handbook chapters

- Chapter 17.11 for the incident response.
- Chapter 17.13 for the reliability engineering.
- Chapter 17.6 for the alerting and SLOs.
- Chapter 13 for the AI storage.

### Migrated from `nvidia-devops`

The disaster recovery operational patterns draw on Volume 19 chapter 10. The handbook rewrote the wording in its own voice.

### Explicitly labelled inferences

These values are starting points, not sourced facts. Check each one against your own business and your own rules before you use it.

- The RTO and RPO targets (critical: 1h/1m; standard: 4h/1h; development: 24h/24h) are starting points. The real targets depend on the business.
- The backup retention periods (90 days for object storage, 30 days for etcd) are starting points. The real retention depends on the regulatory regime.
- The drill frequency (quarterly) is a starting point. The real frequency depends on how disciplined the team is.

### Not verified on live hardware

- The lab in Section 8 is **untested** against a live GKE cluster in this repository.
- The cross-region replication patterns in the lab assume a multi-region deployment is available.
- The drill post-mortem template in the lab is illustrative. Production templates are more detailed. Keep these caveats in view when you check the lab against your own environment.
