---
id: "c17-12"
title: "17.12 Capacity planning and cost optimisation"
sidebar_label: "17.12 Capacity planning and cost"
sidebar_position: 12
description: "Capacity planning and cost optimisation for AI infrastructure: the forecasting model, the FinOps dashboard, the cost-vs-latency trade-off, the right-sizing exercise, the reserved-instance strategy, and the operational patterns that turn the GPU bill into a predictable operating expense."
status: "drafted"
tier: "2"
level: "A"
lab_venue: "GCP / GKE"
---

# 17.12 Capacity planning and cost optimisation

| Field | Value |
|---|---|
| Level | Advanced |
| Priority tier | 2 |
| Lab venue | GCP / GKE |
| Part | Part 17: Observability, performance and operations |
| Cross-references | Chapter 16.14 (Platform design: FinOps); Chapter 17.8 (Performance engineering); Chapter 17.11 (Incident response); Chapter 11 (GPU Kubernetes) |
| Coverage file | `planning/coverage/chapters/17-12.md` |
| Claim & number ledger | `planning/ledgers/17-12.md` |

## Capacity and cost at a glance

Picture two meetings on the same Monday. In one, a manager asks how many GPUs the team will need next quarter. In the other, finance asks why last month's bill was higher than anyone expected. The two questions look different, but they draw on the same numbers, and the diagram below shows how the answers connect.

```mermaid
flowchart LR
    subgraph Forward["Forward-looking"]
        CP[Capacity planning<br/>forecast + buffer]
        RI[Reserved instances<br/>commitment]
    end

    subgraph Backward["Backward-looking"]
        FN[FinOps dashboard<br/>per-team cost]
        RS[Right-sizing<br/>exercises]
    end

    subgraph Output["Procurement"]
        ORD[Procurement order<br/>CFO signature]
    end

    CP --> ORD
    FN --> RS
    RI --> ORD
    RS --> ORD
```

Read the diagram as two views that meet at the procurement order. The capacity plan and the reserved-instance commitments look forward. The FinOps dashboard and right-sizing look back at what you already spent, and right-sizing feeds the order too. The arrows matter as much as the boxes. A purchase decision that ignores the backward view repeats last quarter's mistakes, and a backward view that never reaches the order changes nothing.

## Why this matters for AI infrastructure

Picture a platform team that has just bought a rack of GPUs. A few months later, finance asks why the GPU bill keeps rising, and nobody can explain it. Part 17 so far has taught you to keep the cluster running. This chapter teaches you to pay for it on purpose. The rack is the easy part. The hard part is knowing, every month, what the rack is worth and whether it is still the right size.

Capacity planning and cost optimisation are two views of one problem. Capacity planning looks forward and asks how many GPUs the team will need next quarter. Cost optimisation looks back and asks how many GPUs the team used, and what they cost. Both views meet in the FinOps dashboard, which is the platform team's picture of the cluster's economics. FinOps is the practice of managing cloud and infrastructure spend with finance and engineering working from the same numbers.

The block below shows the stakes with example values. Replace them with your own figures before you put any of them in a budget.

```text
Why capacity planning and cost optimisation are on the critical path (background reading: NVIDIA Zero-to-Hero volume 19; AI Factory; Scalable Kubernetes Infrastructure for AI Platforms; NVIDIA Zero-to-Hero volume 8; the figures below are examples, not quotations):
- A typical mature AI platform spends millions of dollars per year on GPUs.
  A 10% capacity planning error is hundreds of thousands of dollars per year.
  The cost of being wrong is significant.
- A typical workload uses 60-80% of the GPU's compute capacity. A right-sizing
  exercise that closes the gap from 60% to 80% saves 25% of the GPU spend.
  The savings are millions of dollars per year.
- The FinOps dashboard is the source of truth for the cost. The dashboard
  shows the per-team, per-model, per-month cost. The dashboard drives the
  capacity planning and the cost optimisation.
```

Those figures are examples, but the shape of the argument holds. A small percentage error in a large bill is a large sum of money, so a planning method that is roughly right is not good enough on its own. The method needs a feedback loop that catches the error.

Production-scale teams also measure goodput, which is useful work completed per unit of time, rather than raw busy time. A GPU can show as busy while it waits on data or on the other GPUs, and that waiting time is not useful work. AI Systems Performance Engineering, chapter 1, uses Meta's "Revisiting Reliability" paper as its case. A cluster that looked fully utilised still lost 70 to 75 percent of its compute to communication delays, slow data supply, and failure recovery.

Three habits make this a platform-team job rather than a data-science job.

1. The platform team owns the GPU bill. A team that cannot see its own cost has little reason to give GPUs back.
2. Right-sizing is a platform discipline too. Without it, a workload keeps the GPUs it was given long after it needs them.
3. Reserved commitments are a platform decision. The procurement team signs the contract, but the platform team owns the trade-off between flexibility and discount.

**Before a team runs its first workload, make sure it has both a capacity model and a FinOps dashboard.** Capacity planning tells you what to order, and FinOps tells you what you actually spent. The procurement order is where the two meet. Without the first, you buy blind. Without the second, you cannot tell whether the purchase was worth it.

## Prerequisites and outcomes

Before you start, review the chapters below. Chapter 16.14 gives you the cost attribution model that this chapter reuses, so that one is the most important to read first.

### Prerequisites

- Chapter 16.14 (Platform design: FinOps) for the FinOps dashboard and the cost attribution model.
- Chapter 17.8 (Performance engineering methodology) for the cost-versus-latency trade-off.
- Chapter 17.11 (Incident response) for the change management context.
- Chapter 11 (GPU Kubernetes) for the GPU pool management.

### Outcomes

Many teams buy GPUs first and only later ask what they will need, so this chapter walks the loop in order. It starts with a capacity planning model that combines a forecast, a buffer and a procurement order. It then builds a FinOps dashboard that shows cost per team and cost per model, along with the trade-off between cost and latency. Next comes a right-sizing exercise that finds over-provisioned workloads, cuts their GPU count and measures the savings. After that the chapter sets up a reserved-instance strategy with a commitment level, a utilisation target and a renewal calendar. The last part runs the whole process on GKE, so that forecasts, costs and procurement stay predictable.

---

## 1. The capacity planning model

### 1.1 The forecasting model

Imagine your team runs 100 GPUs today, and its GPU count grew by 20 percent over the last quarter. How many GPUs should you order for next quarter? The capacity planning model answers that. It starts from the current GPU count, applies the growth rate and a buffer for spikes, and produces a forecast. The forecast is a single target number, and the order is the difference between that target and what you already own.

The block below lists the inputs, including historical utilisation. The forecast formula itself uses only the current count, the growth rate, and the buffer. Historical utilisation is a check you run before you trust the number, not a term in the formula. If utilisation has been low, the growth figure may be overstating real demand, so look at the utilisation before you accept the growth.

```text
Capacity planning model:
- Historical usage: avg GPU pool utilisation over the last 90 days = 80%
- Growth rate: GPU count growth over the last 90 days = 20% per quarter
- Buffer: 30% for spikes (cost of not having enough GPUs vs cost of over-provisioning)
- Forecast: current GPU count * (1 + growth rate) * (1 + buffer)
```

Work the arithmetic by hand once: 100 × 1.20 × 1.30 = 156. The 30 percent buffer is an example value, so choose your own after you study the workload's spikes. Multiplying by the growth rate first and the buffer second means the buffer sits on top of the grown fleet, not on the old one. That is the point of a buffer: it protects the demand you expect, not the demand you already had.

### 1.2 The buffer calculation

Picture a launch day when traffic jumps for an afternoon, and every GPU you bought last quarter is busy. The buffer is the room you keep above the forecast, so a spike like that does not leave the service short. A buffer that is too small risks missing service targets. A buffer that is too large means paying for GPUs that sit idle. The table shows how that trade-off moves, using example values rather than measured ones.

| Buffer | Trade-off |
|---|---|
| 10% | Low waste; high SLO breach risk |
| 20% | Moderate waste; moderate SLO breach risk |
| 30% | Balanced, and the platform team's default |
| 50% | High waste; low SLO breach risk |
| 100% | Doubled GPU spend; no SLO breach risk |

This chapter starts at 30 percent, and that is only a starting point. Review the buffer each quarter against the workload's spike pattern. A workload with sharp, predictable peaks may need less buffer than one whose demand is spread out but hard to predict.

### 1.3 The procurement order

Picture the procurement form landing on the CFO's desk with one number on it. The model produces two numbers: the target fleet for next quarter, and the order, which is how many GPUs to add to reach it. The script below prints both and writes them to a file. A person should read the script and its output before anyone signs the order.

```bash
# Compute the Q+1 GPU order
python code/part17/capacity_plan.py \
  --current-gpu-count 100 \
  --growth-rate 0.20 \
  --buffer 0.30 \
  --output procurement_order.md
# expected: target fleet 156 GPUs (order 56 more)
```

Before you trust the output, check the current GPU count you fed in. A wrong input produces a confident, wrong order. The script does not know your fleet. It only multiplies the numbers you give it, so the first check is always the input. Keep the printed file with the request, so the person who signs can see the inputs that produced the order.

---

## 2. The FinOps dashboard

### 2.1 The cost model

Picture a finance analyst asking what a single GPU-hour really costs your team. The honest answer is a sum of several lines, not one price. A GPU workload has four cost lines: compute, storage, network egress, and licensing. Network egress is the charge for data that leaves the cloud, and licensing is the fee for the software that runs on the GPUs. Each line works the same way. You multiply how much you used by what it costs, so the model is only as good as the usage numbers and prices you feed it. Use the prices you actually pay, because they differ by GPU class.

```text
Cost model (background reading: NVIDIA Zero-to-Hero volume 19; AI Factory; the figures below are examples, not quotations):
- GPU compute: GPU-hours * GPU price per hour (varies by GPU class)
- Storage: GB-month * storage price per GB-month
- Network egress: GB * network egress price per GB
- Licensing (NVAIE): GPU-hours * license price per GPU-hour
```

Keep this model per team, per model, and per month. The dashboard in the next section reads from it. A total that is only per month cannot tell you which team caused a rise, and a total that is only per team cannot tell you which model is expensive to run.

### 2.2 The FinOps dashboard

Picture a team lead opening the dashboard and seeing a cost much higher than they expected for their own model. A team can only act on a cost it can see, so start the dashboard with cost per team. The JSON below defines five panels: cost per team, cost per model, GPU hours per team, a 90-day cost trend, and a table that sets cost beside p99 latency for each model. Latency at p99 is the response time that nearly all requests beat, with only the slowest tail of requests above it.

```yaml
# code/part17/finops_dashboard.json
{
  "dashboard": {
    "title": "AI Factory - FinOps",
    "panels": [
      {"title": "Cost per team this month", "type": "bargauge", "targets": [{"expr": "sum by (team) (kubecost_team_cost_monthly)"}]},
      {"title": "Cost per model this month", "type": "bargauge", "targets": [{"expr": "sum by (model) (kubecost_model_cost_monthly)"}]},
      {"title": "GPU hours per team this month", "type": "stat", "targets": [{"expr": "sum by (team) (kubecost_team_gpu_hours_monthly)"}]},
      {"title": "Cost trend over the last 90 days", "type": "timeseries", "targets": [{"expr": "sum(kubecost_team_cost_daily)"}]},
      {"title": "Cost vs latency trade-off", "type": "table", "targets": [{"expr": "sum by (model) (kubecost_model_cost_monthly)", "refId": "A"}, {"expr": "histogram_quantile(0.99, sum by (model, le) (rate(inference_request_duration_seconds_bucket[5m])))", "refId": "B"}]}
    ]
  }
}
```

The last panel is the one that matters most for decisions. A model that is cheap per hour but slow to answer may cost more in lost users than it saves in GPUs. Putting cost and latency in one table makes that trade-off visible, instead of leaving each team to argue from its own panel. A team that sees its own latency next to its own cost can start a useful conversation about what a faster model would be worth.

### 2.3 The chargeback integration

Picture finance calling to ask why one team's line is bigger than last month. Chargeback moves these costs into the business's billing system, so each team pays for what it uses. The SQL query below sums each team's cost by month, and the finance system reads the result. Check one month's totals by hand before you trust the chargeback. A chargeback that finance cannot reconcile will be disputed, and a disputed chargeback costs more time than the numbers themselves.

AI Systems Performance Engineering, chapter 2, describes a model where internal teams pay per GPU-hour from their own budgets. That chapter argues that such a charge also covers electricity and depreciation, and that it makes people value the hardware.

```sql
-- code/part17/chargeback_query.sql
SELECT
    team,
    DATE_TRUNC('month', timestamp) AS month,
    SUM(gpu_hours * gpu_price) AS compute_cost,
    SUM(storage_gb_month * storage_price) AS storage_cost,
    SUM(network_egress_gb * network_price) AS network_cost,
    SUM(license_hours * license_price) AS license_cost,
    SUM(compute_cost + storage_cost + network_cost + license_cost) AS total_cost
FROM cost_metrics
GROUP BY team, month
```

---

## 3. Right-sizing

### 3.1 The right-sizing exercise

Picture a cluster with three workloads. Workload A holds 8 GPUs and uses 60 percent of them. Workload B holds 16 GPUs and stays busy. Workload C holds 4 GPUs and uses 40 percent. Right-sizing asks whether A and C can give GPUs back without slowing down. Workload B is the control in this picture. It shows what a healthy, busy workload looks like, so you can judge the other two against it.

The block below works the example through. The $3.20 price is an assumed rate for illustration, not a quote from any provider.

```text
Right-sizing exercise:
- Workload A: 8 GPUs, 60% utilisation -> reduce to 5 GPUs (target 96% utilisation)
- Workload B: 16 GPUs, 80% utilisation -> no change
- Workload C: 4 GPUs, 40% utilisation -> reduce to 2 GPUs (target 80% utilisation)
- Savings: 8 - 5 + 4 - 2 = 5 GPUs * 24 hours * 30 days = 3600 GPU-hours
- Cost savings: 3600 * $3.20 = $11,520 per month
```

Workloads A and C free up 5 GPUs, or 3,600 GPU-hours over 30 days. Recompute the dollar figure with your own rate. The savings come from the hours, not from a single moment. Freeing GPUs for an hour a day is worth less than freeing them around the clock, so the hours figure is the one to check first.

### 3.2 The right-sizing metrics

Read these four metrics together. Low GPU use with full memory can still mean a workload needs its GPUs. A model that holds a large cache in memory may look idle on the compute graph while it keeps its users waiting if you take the memory away. The targets in the table are examples, so choose your own once you see how your workloads behave.

| Metric | What it measures | Target |
|---|---|---|
| GPU utilisation per workload | The fraction of GPU in use | 80-95% |
| Memory utilisation per workload | The fraction of HBM in use | 80-95% |
| GPU hours per request | The GPU hours consumed per request | As low as possible |
| Cost per inference | The dollar cost per inference | As low as possible |

HBM is the high-bandwidth memory that sits on the GPU itself. Read the first two rows as a pair. If compute is low and memory is full, the workload is not idle, and the right move is to investigate before you shrink it.

### 3.3 The right-sizing recommendations

Picture a recommendations file with a long list of workloads on it, each with a suggested GPU count. Run the script below against your production cluster. It lists each workload with its GPU count, its utilisation, and a recommended count. Review each recommendation before you act, because a low average can hide a workload that peaks at certain hours. A good review asks what the workload does at its busiest hour, and whether the reduced count still covers that hour.

```bash
# Generate the right-sizing recommendations
python code/part17/right_size.py \
  --cluster gke-prod-us-central1 \
  --output right_sizing_recommendations.md
# expected: a list of workloads with their GPU count, utilisation, and recommended GPU count
```

---

## 4. Reserved instances

### 4.1 The reserved-instance strategy

Picture a steady inference service that has run at the same load for a year. Paying the on-demand price for it every hour feels wasteful, because you already know it will be there. A commitment trades flexibility for a lower price. You agree to pay for a set number of GPUs over a set period, whether or not you use them all. The table lists four options. The discounts are example ranges, so check them against your provider's price list before you decide.

| Commitment | Discount | Use case |
|---|---|---|
| On-demand | 0% | Spike capacity; unpredictable workloads |
| 1-year reserved | 30-40% | Steady-state workloads |
| 3-year reserved | 50-60% | Long-term workloads |
| Spot | 50-70% | Preemptible workloads; training jobs |

Spot capacity is the cheapest option, but the provider can take it back at any time. That makes spot a good fit for training jobs that checkpoint often, and a poor fit for anything that must answer a user right now.

### 4.2 The utilisation target

A commitment only pays off if you use it. The utilisation target is the lowest use that justifies a commitment. Work out the break-even point first. If the discount is 30 percent, you pay 70 percent of the on-demand price for every committed hour, so you must use 70 percent of those hours to break even.

The block below sets example targets. Replace them with figures from your own price sheet. Read each target against its own contract, because the commitment length changes what the target is measuring.

```text
Reserved-instance utilisation target:
- 1-year reserved: minimum 80% utilisation
- 3-year reserved: minimum 70% utilisation
- Spot: minimum 0% utilisation (spot can be preempted at any time)
```

### 4.3 The renewal calendar

Picture a commitment that quietly renews at the old price on a day when nobody was watching. A commitment that expires without notice either renews by default or lapses, and both can cost you. A renewal calendar lists each commitment, its expiry date, and the decision that is due. The script below builds that calendar. Many teams review it once a quarter, but choose the cadence that fits your contracts. The point is that the decision happens before the date, not on it. Put the calendar where both the finance team and the platform team see it, so the decision has a shared owner who will notice the date.

```bash
# Schedule the renewal calendar
python code/part17/renewal_calendar.py \
  --cluster gke-prod-us-central1 \
  --output renewal_calendar.md
# expected: a calendar of upcoming renewals with the commitment level and the expiry date
```

---

## 5. Operating capacity planning and cost optimisation on GKE

### 5.1 The components

Picture a finance review in which the cost numbers come from three different tools, and each tool disagrees with the others. Running the process on one stack avoids that. Four components make up the stack. Kubecost or OpenCost collects the cost data, Grafana draws the dashboards, and BigQuery answers the chargeback query. The table lists where each one runs and the latency target it should meet. The targets are examples, so measure your own system first and then set targets that match what your team needs.

| Component | Where it runs | Backing store | SLO |
|---|---|---|---|
| Kubecost (or OpenCost) | Kubernetes Deployment | Prometheus + object storage | Cost aggregation latency p99 < 1 hour |
| Capacity planning dashboard | Grafana | Prometheus + Kubecost | Dashboard load p99 < 5 s |
| FinOps dashboard | Grafana | Prometheus + Kubecost | Dashboard load p99 < 5 s |
| Chargeback query | BigQuery | (BigQuery) | Query latency p99 < 30 s |

Cost also depends on how traffic enters the cluster. Production Kubernetes, chapter 6, explains that a LoadBalancer Service in a cloud cluster gets its own external load balancer, and that this adds up. An Ingress controller routes many services through one entry point, which keeps that cost down. A quiet cost like this is easy to miss, because no single service looks expensive on its own.

### 5.2 IAM and the cost optimisation

Cost data is sensitive, so the stack gets its own access roles. Picture an engineer who can edit a chargeback they should only read. IAM stands for identity and access management, the system that decides who may read or change what. The table shows one way to split them, and you should adjust it to match your organisation. Teams can read the dashboard. The platform team can change the model and the dashboard. Only the CFO's office approves orders and chargebacks.

| Role | Who | What they can do |
|---|---|---|
| `finops.reader` | Every team | Read the FinOps dashboard; query the cost data |
| `finops.writer` | The platform team | Update the cost model; update the FinOps dashboard |
| `finops.admin` | The CFO's office | Approve the procurement order; approve the chargeback |

Cost attribution is the platform team's discipline. Tag every GPU with its team, model, and cost centre. The Kubecost allocation and the FinOps dashboard both read those tags, so an untagged GPU is a cost that nobody owns. A cost centre is the internal account that the finance team uses to collect spending.

### 5.3 Observability

Picture a month in which one team's spending doubles and nobody notices until the invoice arrives. Five signals show whether the process is working. The table pairs each one with the alert it should trigger. The thresholds are examples, so set them from your own budgets and your own history.

| Metric | Why it matters | Alert |
|---|---|---|
| Cost per team per month | FinOps dashboard | > budget for 1 day |
| Cost per model per month | Model economics | > budget for 1 day |
| GPU utilisation per team | Capacity planning | < 30% for 7 days |
| Reserved-instance utilisation | Reserved-instance ROI | < target for 30 days |
| Right-sizing savings | Right-sizing effectiveness | < 10% per quarter |

The right-sizing savings alert matters most. A low savings rate suggests the team has stopped looking for waste, and the bill is growing without a check. The other four signals tell you what happened, but the savings rate tells you whether anyone is still looking.

---

## 6. How it fails

Six failure modes come up again and again. Each one below gives you a symptom to look for, a likely cause, and a fix. The numbers in these examples are illustrations, not measured data. Read each one as a story about a process that drifted, because that is how these failures usually arrive.

### 6.1 "The forecast is wrong"

The forecast said the team would need 156 GPUs next quarter, and the order was placed. When the quarter ended, the actual peak use was still 100 GPUs because the expected growth never arrived. That leaves 56 GPUs bought and idle. Keep the forecast and the actual apart in your head. The forecast is what you predicted, and the actual is what the cluster really used. The 100 in this example is an assumed actual, not a measurement, and the gap between the two is the error to study.

The diagnosis is that the forecast model is off. The growth rate, the buffer, or the history the model learned from may be wrong. The growth rate is the most common culprit, because a single strong quarter can look like a trend. Tune the model and check its history. Add a confidence range to the forecast, so the order shows a likely band rather than one number, and review it each quarter.

### 6.2 "The right-sizing exercise finds nothing"

The team runs the right-sizing exercise every quarter. It finds nothing, and the GPU bill keeps climbing. An exercise that never finds waste is usually not measuring the right thing, or is not looking at the workloads that waste the most.

The diagnosis is that the metrics may be wrong, the exercise may cover too few workloads, or the team may not be looking at all of them. Add the right metrics, widen the exercise to every workload, and train people on the method. A quick check is to pick the largest workload and confirm that its metrics were actually read. If the largest workload has no metric at all, the exercise has been running blind, and that is the first thing to fix.

### 6.3 "The reserved-instance commitment is wasted"

The commitment looks well used, but the bill is higher than on-demand would have been. That can seem impossible, which is why it needs a careful look.

The diagnosis starts with how utilisation is measured. At a 30 percent discount, a commitment only breaks even at about 70 percent use, so a figure of 80 percent should save money. If it does not, the forecast was too optimistic, the spike pattern does not match the commitment, or the team did not adjust it. A high utilisation figure can still hide a bill that rose for another reason, so compare the two prices directly.

The fix is to adjust the commitment level, move spiky work to on-demand or spot, and sell the commitment if your provider allows it.

### 6.4 "The chargeback is wrong"

Team A's chargeback is larger than team B's. The teams dispute it, and the CFO's office escalates. A dispute like this damages trust in the whole process, even when the numbers turn out to be right.

The diagnosis is that the cost attribution, the cost model, or the chargeback query is wrong. Check the attribution and the model. Test the query against spend you already know, and automate a chargeback audit. A known spend is a bill or a figure that finance has already agreed, so the test has something solid to compare against.

### 6.5 "The GPU bill grows without bound"

The GPU bill rises each quarter. Nobody updates the forecast, and nobody caps the orders. Each quarter's growth looks reasonable on its own, and the total becomes a surprise only when it is too late to change.

The diagnosis is that the forecast is stale, the orders have no cap, and right-sizing is not running. The fix is to update the forecast each quarter, cap the orders, and run right-sizing every quarter. A cap on orders is a simple rule that forces a conversation before the bill grows past the agreed limit.

### 6.6 "The cost optimisation is ad-hoc"

Teams cut costs on their own. They skip the right-sizing method and ignore the FinOps dashboard. The savings are real in some places and missing in others, and nobody can say which is which.

The diagnosis is that the process is written down, but nobody enforces it, and the team has not been trained on it. The fix is to train the team, check the process in code review, and add it to the team's quarterly goals. A method that lives only in a document will drift, while one that is checked in review stays close to what was agreed.

---

## 7. Hands-on lab

Picture a quiet afternoon with a non-production cluster, a dashboard and a spreadsheet of last month's bills. This lab takes you through the capacity model, the FinOps dashboard, the right-sizing exercise, and the reserved-instance strategy, in that order. The lab is **untested** in this repository, so treat each step as a plan to verify on your own cluster.

### 7.1 Prerequisites

Check three things before you start. Each one supports a step later in the lab, so a gap here will show up as a failed command there.

- Kubecost (or OpenCost) installed.
- The observability stack from earlier chapters.
- A GKE Autopilot or Standard cluster with at least 4 H100 GPUs.

### 7.2 Step 1: deploy Kubecost

Start by installing Kubecost into its own namespace. Keeping it in its own namespace makes it easy to find, upgrade and remove later. Wait until its pods are running before you move on, because the dashboard in the next step reads from them.

```bash
helm repo add kubecost https://kubecost.github.io/cost-analyzer
helm install kubecost kubecost/cost-analyzer \
  --namespace kubecost --create-namespace \
  --set kubecostToken=$KUBECOST_TOKEN
# expected: Kubecost pods are running; Kubecost is scraping the cluster
```

### 7.3 Step 2: build the FinOps dashboard

Next, load the dashboard into Grafana. The import command below uses Grafana's default admin credentials, so change that password first and never run the command against a shared Grafana. A default password on a shared server is one of the easiest ways for someone else to change your dashboards.

```bash
kubectl -n monitoring create configmap finops-dashboard \
  --from-file=dashboards/finops.json

curl -X POST http://admin:admin@localhost:3000/api/dashboards/import \
  -H "Content-Type: application/json" \
  -d @dashboards/finops_import.json
# expected: the FinOps dashboard is available at /d/finops/ai-factory-finops
```

### 7.4 Step 3: run the capacity planning model

Run the model with your current GPU count. Check the printed number against your own arithmetic before you trust it. Four GPUs, with 20 percent growth and a 30 percent buffer, give 6.24 before any rounding. The script rounds up to a whole GPU, so compare the printed target with 6.24 and not with an unrounded guess.

```bash
python code/part17/capacity_plan.py \
  --current-gpu-count 4 \
  --growth-rate 0.20 \
  --buffer 0.30 \
  --output procurement_order.md
# expected: target fleet 7 GPUs (order 3 more; 6.24 rounded up)
```

### 7.5 Step 4: run the right-sizing exercise

Run the right-sizing script against the cluster, then open the recommendations file. Start with the workloads that show the lowest utilisation, because they have the most room to shrink. Check each one against its memory use before you act on it. A workload with low compute and high memory may still need every GPU it has.

```bash
python code/part17/right_size.py \
  --cluster gke-prod-us-central1 \
  --output right_sizing_recommendations.md
# expected: a list of workloads with their GPU count, utilisation, and recommended GPU count
```

### 7.6 Step 5: query the chargeback

Finally, query the chargeback table in BigQuery. The query returns up to 12 rows, newest first, so you can see each team's recent months. Compare one team's newest row with the figure you expect before you read the rest.

```bash
bq query --use_legacy_sql=false \
  "SELECT team, month, total_cost
   FROM \`${PROJECT_ID}.finops.chargeback\`
   ORDER BY month DESC LIMIT 12"
# expected: the per-team, per-month chargeback
```

### 7.7 What to record

Answer these five questions from the dashboards alone, and time yourself. Answering from the dashboards alone tests whether the dashboards are good enough to use without a person explaining them. The 30-second limit is an example, so set the limit your team actually needs.

1. What is the current cost per team this month?
2. What is the Q+1 GPU order per the capacity planning model?
3. What is the current right-sizing savings rate?
4. What is the current reserved-instance utilisation?
5. What is the next reserved-instance renewal date?

If any answer takes longer than your limit, the stack is not yet a production service. Treat the timings you record as targets to aim for, and note which dashboard slowed you down.

---

## Exercises

These exercises turn the chapter into tools your team can keep and improve. Each one begins with a gap that a platform team usually notices late.

1. **Add a per-model cost dashboard.** Finance keeps asking what each model costs to run, and the answer is spread across several panels. Build a Grafana dashboard that shows what each model costs to run. It should combine the model's cost, its GPU hours, and its inference count. *Solution sketch:* a Grafana dashboard that reads the per-model cost, GPU hours, and inference count from the same data sources the FinOps dashboard uses.
2. **Add a right-sizing recommendation script.** Idle GPUs go unnoticed for months. Build a script that reads the current GPU usage and recommends a smaller count where the GPUs sit idle. *Solution sketch:* a Python script that reads the metrics, computes the right-sized count, and writes the recommendation to a file.
3. **Add a reserved-instance tracking dashboard.** Nobody can say whether the commitments are paying off. Build a Grafana dashboard that shows how much of each commitment is used. It is the view you use to judge whether a commitment is paying off. *Solution sketch:* a Grafana dashboard that plots reserved-instance utilisation against the target you set in section 4.
4. **Add a FinOps alert per team.** A team overspends for weeks before anyone sees it. Configure an alert that fires when a team's monthly cost exceeds its budget. *Solution sketch:* a Prometheus alert on the per-team cost that notifies the team's lead.
5. **Add a capacity planning review process.** The procurement order is often signed without a fresh look at the numbers. Schedule a quarterly review that produces a procurement order and sends it to the CFO's office for approval. *Solution sketch:* a calendar event, a review script, and a signed procurement order.
6. **Add a chargeback audit.** A chargeback total is disputed after finance has already paid it. Run a monthly audit that checks each team's chargeback and flags anomalies. *Solution sketch:* a Python script that reads the chargeback table, recomputes each team's total, and flags any difference.

---

## Checkpoint questions

<details><summary>1. Finance asks why the GPU bill keeps rising and nobody on the platform team can explain it. What should have existed, and what would it show?</summary>
A FinOps dashboard, which is the platform team's picture of the cluster's economics. It shows cost per team, cost per model, and GPU hours per team this month, plus a 90-day cost trend. A team that cannot see its own cost has little reason to give GPUs back.
</details>

<details><summary>2. Team A's chargeback is larger than team B's, the teams dispute it, and the CFO's office escalates. Where do you look?</summary>
The chapter names three suspects, which are the cost attribution, the cost model, and the chargeback query. Test the query against spend you already know, and check the tags on each GPU. Then automate a chargeback audit so the next dispute is caught earlier.
</details>

<details><summary>3. The forecast asked for 156 GPUs, but the team only used 100. What does that leave you with, and what may have gone wrong?</summary>
It leaves 56 GPUs bought and idle. The growth rate, the buffer, or the history the model learned from may be wrong. Tune the model, add a confidence range to the forecast, and review it each quarter.
</details>

<details><summary>4. The team runs right-sizing every quarter, finds nothing, and the GPU bill keeps climbing. What does the chapter say may be wrong?</summary>
The metrics may be wrong, the exercise may cover too few workloads, or the team may not be looking at all of them. Add the right metrics, widen the exercise to every workload, and train people on the method. A right-sizing savings rate below 10 percent per quarter is the alert that should have flagged this.
</details>

<details><summary>5. A 1-year commitment shows 80 percent utilisation, yet the bill is higher than on-demand would have been. What do you check first?</summary>
Check how utilisation is measured. At a 30 percent discount a commitment breaks even at about 70 percent use, so 80 percent should save money. If it does not, the forecast was too optimistic, the spike pattern does not match the commitment, or the team did not adjust it.
</details>

<details><summary>6. Dashboards show the cluster fully busy, yet jobs finish slowly. Which idea from the chapter explains this, and what example supports it?</summary>
Goodput, which is useful work completed per unit of time, is a better measure than raw busy time. The chapter cites Meta's "Revisiting Reliability" paper through AI Systems Performance Engineering, chapter 1. A cluster that looked fully used still lost 70 to 75 percent of its compute to communication delays, slow data supply, and failure recovery.
</details>

<details><summary>7. Why does a 30 percent discount require about 70 percent utilisation to break even?</summary>
With a 30 percent discount you pay 70 percent of the on-demand price for every committed hour, whether you use it or not. Using 70 percent of those hours matches what on-demand would have cost. Below that, the commitment costs more than on-demand.
</details>

<details><summary>8. Why would closing the gap from 60 percent to 80 percent utilisation save 25 percent of GPU spend?</summary>
The same work needs fewer GPUs when each one is busier. At 60 percent use the work needs 60 out of every 80 GPUs it would need at 80 percent, so 60 divided by 80 is 0.75. That is a 25 percent saving. The figures are the chapter's examples.
</details>

<details><summary>9. Why does an untagged GPU hurt the cost process?</summary>
Kubecost allocation and the FinOps dashboard both read the team, model, and cost centre tags. An untagged GPU has no team, so its cost belongs to nobody. It then cannot appear in a chargeback or be reviewed in right-sizing.
</details>

<details><summary>10. Why can a service of type LoadBalancer make cost grow quietly, and what does an Ingress change?</summary>
In a cloud cluster each LoadBalancer Service gets its own external load balancer, and those charges add up. An Ingress controller routes many services through one entry point. That keeps the number of load balancers, and the bill, down.
</details>

<details><summary>11. Why does the chapter say a low right-sizing savings rate is the most important alert?</summary>
A low rate suggests the team has stopped looking for waste. The bill then grows without a check, because nothing is pulling unused GPUs back. The example alert fires when savings fall below 10 percent per quarter.
</details>

<details><summary>12. You must set a buffer. When would you pick 30 percent over 10 percent, and what do you give up?</summary>
Pick 30 percent when missing the SLO during a spike costs more than idle GPUs. You give up some spend, because 10 percent has low waste but a high SLO breach risk. The chapter treats 30 percent as a balanced starting point and asks you to review it each quarter against your spike pattern.
</details>

<details><summary>13. A training workload is steady for three years and another is spiky. When would you choose 3-year reserved, 1-year reserved, on-demand, or spot, and what do you give up with each?</summary>
Use 3-year reserved for long-term steady work, with a 50 to 60 percent discount and the least flexibility. Use 1-year reserved for steady-state work at 30 to 40 percent. Use on-demand for spikes at no discount, and spot for preemptible training jobs at 50 to 70 percent, where you accept being preempted at any time.
</details>

<details><summary>14. Should the platform team charge each team per GPU-hour or keep GPUs in one shared budget, and what does each give up?</summary>
A per-GPU-hour charge makes teams see the cost and value the hardware. AI Systems Performance Engineering, chapter 2, adds that it also covers electricity and depreciation. You give up simplicity, because you need tags, a cost model, and a chargeback query that teams will trust. A shared budget is easier but hides who uses what.
</details>

<details><summary>15. The workload's average utilisation looks low. Do you cut its GPUs straight away, or check first, and what do you risk either way?</summary>
Review each recommendation first, because a low average can hide a workload that peaks at certain hours. Cutting immediately saves money but risks missing the SLO at the peak. Checking costs a little time and keeps the savings honest.
</details>

<details><summary>16. A team has 100 GPUs, growth of 20 percent, and a 30 percent buffer. What is the target fleet and the order?</summary>
The forecast is current count times 1.20 times 1.30. That is 100 times 1.20 times 1.30, which is 156 GPUs. The order is 156 minus 100, so 56 more.
</details>

<details><summary>17. A lab cluster has 4 GPUs, 20 percent growth, and a 30 percent buffer. What does the script print, and why?</summary>
The raw result is 4 times 1.20 times 1.30, which is 6.24. You cannot buy a fraction of a GPU, so the target fleet is 7. The order is 7 minus 4, which is 3 more.
</details>

<details><summary>18. In the right-sizing example, A drops from 8 to 5 GPUs and C from 4 to 2. At $3.20 per GPU-hour, what is the monthly saving?</summary>
A frees 3 GPUs and C frees 2, which is 5 GPUs. Over 30 days that is 5 times 24 times 30, which is 3,600 GPU-hours. At $3.20 each the saving is 3,600 times 3.20, which is $11,520. The $3.20 is an assumed rate, so use your own.
</details>

<details><summary>19. The procurement script prints an order that looks far too high. What do you check first, second, and third?</summary>
First check the current GPU count you fed in, because a wrong input gives a confident, wrong order. Second check the growth rate and the buffer against the last 90 days of history. Third work the formula by hand, as in 100 times 1.20 times 1.30, and compare it with the printed number.
</details>

<details><summary>20. A chargeback total for one month looks wrong. In what order do you verify it before finance reads it?</summary>
First check one month's totals by hand against the four cost lines, which are compute, storage, network egress, and licensing. Second check that the cost attribution tags are present on the GPUs involved. Third test the query against spend you already know.
</details>

---

## Sources and review notes

- NVIDIA Zero-to-Hero Volume 19 (`chapter-03-capacity-planning.md`, `chapter-06-cost-optimisation.md`). Source for the capacity planning model, the FinOps dashboard, and the cost optimisation patterns. The wording has been rewritten in the handbook's voice.
- *AI Factory* (`ai-factory`, Chapter 8, on software engineering). Background on the lifecycle only; it has no GPU cost material.
- NVIDIA Zero-to-Hero Volume 21 (AI factory overview). Source for the multi-tenant AI factory economics.
- *Scalable Kubernetes Infrastructure for AI Platforms* (`scalable-kubernetes-infrastructure-for-ai-platforms`, Chapter 2). Source for the Kubernetes cost optimisation patterns.
- NVIDIA Zero-to-Hero Volume 8 (`chapter-02-cost-optimisation.md`). Source for the GPU-specific cost optimisation patterns.

### Cross-references to other handbook chapters

- Chapter 16.14 for the platform design FinOps patterns.
- Chapter 17.8 for the performance engineering methodology.
- Chapter 17.11 for the incident response and change management.
- Chapter 11 for the GPU Kubernetes.

### Migrated from `nvidia-devops`

The capacity planning and cost optimisation patterns draw on Volume 19 chapters 3 and 6, Volume 8 chapter 2, and Volume 21. The wording has been rewritten in the handbook's voice.

### Explicitly labelled inferences

- The buffer calculation (30% default) is a starting point; specific buffers depend on the workload's spike pattern.
- The right-sizing savings targets (10% per quarter) are starting points; specific targets depend on the workload.
- The reserved-instance commitment ratios (1-year: 30-40%; 3-year: 50-60%) are approximate; specific discounts depend on the cloud provider.

### Not verified on live hardware

- The lab in Section 7 is **untested** against a live GKE cluster in this repository.
- The Kubecost version assumed in the lab should be pinned against the current releases before production use.
- The cost numbers in the lab are illustrative; production costs vary by usage pattern, region, and commitment.

corrected 2026-11-11: no quarterly_review.py exists and none is used here; the capacity_plan.py commands use its real flags (--current-gpu-count, --growth-rate, --buffer, --output), and the expected output now matches what the script prints (target fleet and order); source code/part17/capacity_plan.py, run 2026-11-11.
