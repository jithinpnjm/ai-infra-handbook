---
id: "c20-25"
title: "20.25 PromQL, Grafana and tracing: the traps interviewers test"
sidebar_label: "20.25 PromQL, Grafana, tracing traps"
sidebar_position: 25
description: "Fifteen PromQL, alerting, dashboard and tracing traps for an inference platform, each with a fix. Rules and unit tests that pass promtool, an Alertmanager config that passes amtool, and a PromQL pitfall linter with pytest."
status: "drafted"
tier: "1"
level: "I"
lab_venue: "Laptop / Docker"
---

# 20.25 PromQL, Grafana and tracing: the traps interviewers test

## What the interviewer is testing

The interviewer shares a screen. A dashboard shows a flat, healthy p99 while the customer channel is full of complaints. They ask: "Here is the query behind this panel. What is wrong with it?" You have about two minutes to find the bug, say why, and write the fix.

Notice the mismatch first. The picture on the screen is calm and the people writing in the channel are not. That gap is the whole reason the interviewer picked this panel. Either the query is hiding something, or the data is, and your job is to work out which one before you say anything about the fix.

The job posting asks for deep experience with Prometheus and Grafana. Nebius has not published how its own monitoring is built. So the interviewer cannot test your memory of internals. They test whether you know how the query language fails quietly, because a query that fails quietly is the one that wakes nobody up.

This chapter serves two rounds. In the Linux and incident rounds you read dashboards under pressure. In the system design round you justify how you would alert and trace a streaming request. Chapter 20.19 owns SLO maths and burn-rate alerts. Chapter 20.15 owns pipeline architecture. This chapter owns the query, the alert rule, the dashboard and the trace.

A realistic question: "Your p99 TTFT panel uses `avg` across pods and the alert flaps every night. Walk me through what is wrong and how you would prove it."

## The core ideas

Picture a dashboard review where every panel on the wall hides one trap in its query. The ideas below are the traps, in the order you are likely to meet them while you read a screen out loud.

### 1. Counters, resets and what rate really computes

![Chart of a counter that resets to zero, with a subtraction over ten minutes giving minus ten and increase giving 88.9](./img/x25-counter-reset-compare.svg)

*Figure 20.25.1. Counter reset: subtracting two counter values gives a negative number after a restart, while increase repairs the reset and reports the real work done.*

Picture a deploy that goes out in the middle of the afternoon. The gateway pods restart, and the request counter on each one falls back to zero. A dashboard that subtracts this morning's counter from this evening's counter now shows a negative number of requests, and no user caused that.

A counter only goes up, except when a process restarts and it falls back to zero. Dashboards that subtract two counter values break at that moment, because the subtraction has no idea a restart happened. The Prometheus docs say `rate` adjusts automatically for breaks in monotonicity, such as counter resets after target restarts. Monotonicity is the plain word for only going up. So the function spots the drop and repairs it, and you do not have to write that repair yourself.

The `rate` function gives the per-second average increase over the range you pass. The docs say it extrapolates to the ends of that range. Think of the range as a ruler laid over the graph. `rate` draws a straight line through the samples inside the ruler and reads its slope, then stretches that line to reach both edges of the ruler. `increase` is the same maths multiplied by the number of seconds in the window. That is why `increase` over ten minutes often returns 1.11 for a counter that went up by exactly one. The stretching is a feature, and an equality check against a whole number will never match.

The exercise test in this chapter shows both sides. A counter that climbs by ten a minute and restarts at zero gives minus ten when you subtract it from its value ten minutes earlier. The same counter through `increase` gives 88.9, which is the real work done once the reset is repaired. Read that pair slowly. The subtraction gets the sign wrong, and the `increase` answer is the work the service really did. Nothing in the data changed between the two queries. Only the function did.

**Never subtract counters yourself. Use `rate` or `increase`, and never compare the result with a whole number.**

### 2. rate versus irate, and the range-selector trap

![A scrape timeline showing a 30 second range holding one sample and a 2 minute range holding four, with the irate trap.](./img/p3-2025-range-and-irate.svg)

*Figure 20.25.2. Use a range of at least four scrape intervals and keep irate for graphs.*

Imagine you have just added a panel for the gateway, and it shows nothing at all while traffic is flowing. You write `rate(gateway_requests_total[30s])` and the panel is empty. Nothing is broken in the service. The range is too short.

A range selector is the part inside the square brackets. It covers the interval from the evaluation time back by its length, so each time the panel refreshes, the query looks only at the samples that fall inside that window. The docs say it is left-open and right-closed. In plain words, a sample sitting exactly on the old edge of the window is left out. With a scrape every 30 seconds, a 30-second range holds one sample. One sample cannot make a slope, so the result is empty.

Two samples is the bare minimum, and it is still too thin for a stable answer. Grafana has a variable built for this, `$__rate_interval`, and it is designed to capture at least four scrape samples. Its formula takes the larger of the dashboard interval plus the scrape interval, and four times the scrape interval. The docs warn about one mismatch in particular. If the data source is set to 15 seconds while the real scrape is 60 seconds, the window becomes too small and rate can return no data. Treat four scrape intervals as your floor.

`irate` is different, and it is easy to pick by accident. The docs say it uses only the last two data points. That suits a fast-moving counter on a graph, where you want to see every wiggle. In an alert it is a trap. One quiet pair of samples at the end hides a burst that happened a minute ago, so the alert sees calm when the service had a problem. The exercise test feeds a counter that jumps by 100 and then stays flat. At the end `irate` says zero. `rate` over five minutes still reports the 0.33 per second that the burst left behind, and that is the number an alert should look at.

**Pick a range of at least four scrape intervals, use `rate` in alerts, and keep `irate` for graphs of fast counters.**

### 3. Aggregate after rate, never before

![A wrong averaged ratio of 0.25 against the correct summed ratio of 0.002 with the recording rules that build it.](./img/p3-2025-ratio-trap.svg)

*Figure 20.25.3. Aggregate numerator and denominator separately, then divide.*

![Summing two pods' counters before the rate hides a restart, while taking the rate per series first keeps the reset visible and gives the fleet rate.](./img/p2-2025-sum-before-rate.svg)

*Figure 20.25.4. Summing counters before taking the rate hides a pod restart, so the rate is taken per series first and then summed by the labels kept.*

Your gateway runs as two pods behind one service, and a manager asks for the total request rate across the fleet. The quick answer feels natural. Two pods report a request counter. One restarts. You want the fleet rate. The tempting query sums the counters first and then asks for the rate of the sum.

Summing first throws away the reset. When pod A falls from 100 to 0 while pod B climbs by 100, the sum stays flat. In the sum, the drop in A and the climb in B cancel each other out, so the reset is invisible. The work pod A did before the restart is lost from the total. The docs say to take a `rate` first and then aggregate, so each pod's reset is repaired before anything is added together. In the exercise test the sum-first form reports 1.38 per second and the correct form reports 1.79.

The same order applies to ratios. The Prometheus recording-rule guide says to aggregate numerator and denominator separately and then divide. A ratio of two summed rates is correct. An average of ratios is not, because it gives every pod the same vote even when one pod served most of the traffic. The guide also says never to take the average of a ratio or an average of an average.

**Rate per series, sum by the labels you want to keep, then divide.**

### 4. Histograms: keep le, then take the quantile once

![A busy pod and an idle pod whose averaged p99 of 1.47 seconds differs from the true combined p99 of 0.99 seconds.](./img/p3-2025-average-p99.svg)

*Figure 20.25.5. Merge buckets across pods and take the quantile once.*

![A cumulative latency histogram where summing without the le label breaks the p99, and the right query keeps le in the by clause before taking the quantile once.](./img/p2-2025-le-buckets.svg)

*Figure 20.25.6. A latency histogram stores cumulative buckets by le, and the p99 is correct only when le stays in the by clause before histogram_quantile runs.*

Your p99 panel looks simple, but underneath it sits a set of counters called buckets. Think of a histogram as a row of boxes. Each box has an upper bound, and it counts every request that finished at or under that bound. The boxes are cumulative, so the box for a larger bound also holds everything the smaller boxes hold.

A latency histogram is a set of cumulative bucket counters, one per upper bound, with a label called `le`. The label stands for less than or equal to. The function `histogram_quantile` reads those buckets and interpolates inside the bucket that holds your quantile. Interpolate means estimate a value between the two bounds of that bucket. The function needs the `le` label to do that, because without it the function cannot tell one bucket from another.

Here is the trap in practice. A dashboard author wants a p99 for each model, so they write a sum that keeps the model label and drops everything else. The docs say that when you aggregate classic histograms, `le` has to be in the `by` clause. Write `sum by (le)` or `sum by (model, le)`. If you write plain `sum`, the label is gone and the function returns nothing. If you write `sum by (pod)`, you get nothing too, because `le` is dropped there as well. The exercise test confirms both return an empty result.

![Histograms: keep le, then take the quantile once](./img/m20-25-1.svg)

*Figure 20.25.7. Histograms: keep le, then take the quantile once, as a diagram.*

The next trap is averaging percentiles, and it is the one interviewers like best. A percentile of a pod says nothing about how many requests that pod served. Picture a busy pod next to a nearly idle one. In the test, pod A serves 1,000 requests per step and has a p99 of 0.95 seconds. Pod B serves ten and has a p99 of 1.99 seconds. The average of the two is 1.47. The p99 of all the requests together is 0.99 seconds. The busy pod dominates the truth, because most of the users sat on it. The average gives both pods equal weight, so a nearly idle pod drags the number up by half.

There is also a limit that no query fixes. The docs say the highest bucket must have an upper bound of `+Inf`, which means everything above the last named bound. A histogram with no observations returns `NaN`, which is the not-a-number value. So an empty histogram looks like a broken panel rather than a quiet one. Chapter 20.19 covers choosing bucket boundaries at your SLO limit, and that choice decides how precise the answer can be.

**Sum buckets by le across everything you want in the answer, take the quantile once, and never average quantiles.**

### 5. Gauges, saturation and dashboards that tell the truth

![Three pods where the average cache usage of 0.53 hides one pod at 1, with USE versus RED and gauge function rules.](./img/p3-2025-saturation-panels.svg)

*Figure 20.25.8. Show the worst pod and put saturation beside every utilization panel.*

A panel shows average KV cache usage at 53 percent. It looks comfortable. One of three pods sits at 100 percent and is rejecting work. The average hides it, and the maximum shows it.

Read that panel the way an on-call engineer would. The KV (key-value) cache is the memory where an inference engine keeps the working state of each running request, so a full cache means the engine has no room for more work. A healthy average can sit on top of one pod that is out of room. The question to ask is which pod is full, not what the mean looks like.

*Systems Performance*, in its chapter on methodologies, defines utilization as how busy a resource is and saturation as the degree to which it has queued work it cannot service. The USE method checks errors first, then saturation, because any level of saturation can be an issue. For an inference engine, KV cache usage is utilization. The waiting queue is saturation. The vLLM metrics design page lists both as gauges: `vllm:kv_cache_usage_perc` and `vllm:num_requests_waiting`. Mapping them to utilization and saturation is my reasoning, not a vLLM statement.

The difference matters in practice. A pod that is busy with an empty queue is working as designed. A pod with a queue behind it is in trouble, even when its utilization number looks similar to the busy pod next to it.

A gauge needs gauge functions. A gauge is a value that rises and falls on its own, such as a queue length, so it is not a counter. `rate` over a gauge that holds at 7 returns zero and says the queue is empty, which is wrong, because the queue still has work in it. Use the value itself, `avg_over_time`, `max_over_time`, or `deriv` when you want the trend. `deriv` gives the slope of a gauge, which answers the question of whether the queue is growing.

Grafana's best-practice page names two methods. USE suits hardware resources, such as a GPU or a disk. RED suits services, and it stands for request rate, errors and duration. The page says to alert on symptoms rather than causes, so a user-facing alert should fire on errors or latency, not on one internal number. A good inference dashboard therefore has a RED row for the gateway and a USE row for the engine, with saturation next to every utilization panel. It also says to avoid dashboard sprawl and to use variables and templates for consistency, so one panel can serve every model.

**Every utilization panel needs a saturation panel beside it, and fleet panels should show the worst pod.**

### 6. Staleness, absent and silent alerts

![Three alert checks side by side: up equals zero for unscrapable targets, a count for vanished series, and absent for a total blackout](./img/x25-alert-blind-spots.svg)

*Figure 20.25.9. Silent alerts: pair a no-data risk with a count or an absent check, because absent alone misses the loss of one pod out of several.*

Imagine a Tuesday night when one exporter stops reporting. The error panel goes blank, nobody is paged, and in the morning the team finds the errors were climbing the whole time. An alert never fires because the metric stopped existing. This is the quietest failure in monitoring, and it deserves more attention than the loud ones.

The docs say a series is marked stale when a scrape or rule evaluation no longer returns it, and that queries then return no value for it. Without a stale marker the lookback applies, five minutes by default. So a vanished series does not make a query return zero. It makes it return nothing. An alert on `errors > 0` cannot fire when the errors series is gone, because there is no value left to compare with the threshold.

The function `absent` returns a one-element vector when its argument is empty. The docs say it is useful when no series exists for a metric name and label combination. The trap is scope. `absent(up{job="vllm"})` fires only when every vllm target is gone. In the test, one of two pods disappears and `absent` returns nothing. The fix for partial loss is to count: `count(up{job="vllm"}) < 2`. The test returns 1 for that. The count sees the loss that `absent` cannot see, because `absent` only looks for total silence.

Two layers belong together. `up == 0` catches a target that exists but cannot be scraped. A count catches series that vanished. `absent` catches a total blackout. None of the three covers all the cases alone, so use them together.

**Pair every "no data" risk with a count or an absent alert, and test it by deleting the series.**

### 7. Joins: on, ignoring and group_left

Suppose you want vLLM queue depth shown by node. The node name lives on `kube_pod_info`, not on the vLLM metric. The two series share a pod label, so you join them with `on (pod)`.

Prometheus matches one series to one series by default. If one side has several series per pod, for example one per engine, the join is many-to-one. The query then fails, and the real error from `promtool` is: "multiple matches for labels: many-to-one matching must be explicit (group_left/group_right)". The error is honest. It tells you the matching is ambiguous and asks you to say which side has the many. The fix names the many side. With `group_left (node)` the result keeps every left series and copies the node label from the right.

The safe habit is to know which side is many before you write the join. The side that has more series is the one `group_left` points at. When the right side has duplicate series for one pod, you get the same error from the other direction, and the fix is to fix the data, not the query. A join that needs a hack to run is usually telling you the labels are wrong upstream.

**Name the many side, copy only the labels you need, and check that the one side really is one.**

### 8. Alert rules: for, flapping and keep_firing_for

![A queue depth timeline with two spikes and a plateau and three alert variants showing when each one fires.](./img/p3-2025-for-keepfiring.svg)

*Figure 20.25.10. Use for to ignore blips and keep_firing_for to stop flapping.*

Picture a queue that spikes for a few seconds every time a batch of requests lands. A person who gets paged for every spike will stop trusting the pager. An alert without a `for` clause becomes active on the first evaluation, as the docs say, so one noisy sample pages a person. A `for` clause holds the alert in the pending state until it has been active for the whole duration.

The opposite problem is flapping. When a metric hovers around the threshold, the alert resolves and fires again, and every flip sends a notification. The `keep_firing_for` clause tells Prometheus to keep the alert firing for a stated time after the condition was last met. The docs say it prevents flapping and false resolutions caused by data gaps.

The rules test in this chapter feeds queue depth with two short spikes and a long plateau. The alert without `for` fires at the first spike at minute two. The fixed alert stays quiet through both spikes, fires during the plateau, and keeps firing for three minutes after the queue drains. You can read the difference on the timeline. The first alert is a pager that rings for nothing, and the second one rings for the long problem and then stops cleanly.

A burn-rate alert from chapter 20.19 can skip `for` because its two windows already filter noise. Everything else should have one.

**Use for to ignore blips and keep_firing_for to stop flapping, and say why when you leave either out.**

### 9. Alertmanager: grouping, inhibition and routing

![Alertmanager flow: alerts grouped by cluster and model, routed by severity to a pager or a ticket queue, with inhibition rules that silence symptoms](./img/x25-alertmanager-routing.svg)

*Figure 20.25.11. Alertmanager routing: group by cluster and model, send pages and tickets to separate receivers, and let a cause alert or a page silence its symptoms.*

The pager rings forty times in a minute because one pod failure trips twenty alerts. The fix is not in Prometheus. It is in Alertmanager, the component that receives alerts from Prometheus and decides who hears about them and when.

Alertmanager's docs describe three tools. Grouping puts alerts of similar nature into one notification. Inhibition suppresses certain alerts when others are already firing. Silences mute alerts for a time. A routing tree in the config file sets the grouping, the timing and the receivers.

The configuration reference gives the defaults. `group_wait` is 30 seconds, how long to wait before the first notification for a new group. `group_interval` is 5 minutes, the wait before further notifications for the same group. `repeat_interval` is 4 hours. Group by `[cluster, model]` and a burst of different alert names for one model becomes one page. The grouping key is the set of labels that decide which alerts travel together.

Inhibition needs care. The docs recommend choosing source and target matchers so an alert never matches both sides, which makes rules easier to reason about. The config below says a missing-targets alert silences the symptom alerts for the same cluster, and a page silences tickets for the same model. Read it as two sentences in code. If the first condition is firing, the symptoms in that cluster are quiet. If a page is firing for a model, the tickets for that model are quiet.

```yaml
# code/part20/c25_alertmanager.yml
# Alertmanager config for chapter 20.25. Check: amtool check-config c25_alertmanager.yml
# The webhook URLs are placeholders. Replace them with your real receivers.
route:
  receiver: ticket
  # One notification per model and cluster, however many alertnames fire for it.
  group_by: [cluster, model]
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 12h
  routes:
    - matchers: ['severity="page"']
      receiver: pager
      repeat_interval: 4h
    - matchers: ['severity="ticket"']
      receiver: ticket
inhibit_rules:
  # Scrape failure on the whole job explains the symptom alerts. Source and target
  # alertnames are disjoint so no alert can inhibit itself.
  - source_matchers: ['alertname="VllmTargetsMissing"']
    target_matchers: ['alertname=~"ErrorRatioHigh|KVCacheSaturated|QueueDeep"']
    equal: [cluster]
  # A page for a model silences tickets for the same model.
  - source_matchers: ['severity="page"']
    target_matchers: ['severity="ticket"']
    equal: [cluster, model]
receivers:
  - name: pager
    webhook_configs:
      - url: http://pager-bridge.example.invalid/hook
  - name: ticket
    webhook_configs:
      - url: http://ticket-bridge.example.invalid/hook
```

`amtool check-config` passes this file. The routing test script checks three alerts land in the right receivers. Running it is a cheap way to catch a route that sends pages to a ticket queue before a real night shift discovers it.

```bash
# code/part20/c25_route_check.sh
#!/usr/bin/env bash
# Routing checks for c25_alertmanager.yml. Needs amtool on PATH. Exits 1 on any mismatch.
set -u
cfg="$(dirname "$0")/c25_alertmanager.yml"
fail=0
expect() {  # expect <receiver> <label>...
  want=$1; shift
  got=$(amtool config routes test --config.file="$cfg" "$@" 2>/dev/null)
  if [ "$got" = "$want" ]; then echo "ok   $* -> $got"; else echo "FAIL $* -> $got (want $want)"; fail=1; fi
}
expect pager severity=page model=m1 cluster=c1
expect ticket severity=ticket model=m1
expect ticket alertname=Unlabelled
exit $fail
```

**Group by what a person acts on, inhibit symptoms when a cause is firing, and keep source and target matchers disjoint.**

### 10. Recording rules and naming

![Three layers of recording rules from rates through ratios and quantiles to alerts, with the naming convention.](./img/p3-2025-rule-layers.svg)

*Figure 20.25.12. Record the expensive expression once and build each layer on a clean input.*

A dashboard takes eight seconds to load because every refresh runs a heavy `histogram_quantile` over a week of data. Nobody can wait eight seconds for a p99 during an incident. The fix is to precompute the expensive expression once, on a schedule, and let the dashboard read the result. That is what a recording rule does.

The Prometheus naming guide says rules should be of the general form `level:metric:operations`. The level is the aggregation level and the labels of the output. The metric name stays unchanged except for stripping `_total`. The operations list names what was applied, newest first. It also says always to specify a `without` clause with the labels you aggregate away.

So `model:gateway_errors:rate5m` is a sum by model of the rate over five minutes of `gateway_errors_total`. The name tells a reader what is inside without opening the rule. A name like `errors_ratio` tells nothing, and my linter flags it.

Here is the rule file of correct patterns. It keeps `le` in the bucket rule, divides sums for the ratio, records the worst pod for saturation, and gives every alert a `for`. Read it from the top. The recorded series are built in layers, and each layer is a clean input for the next one.

```yaml
# code/part20/c25_trap_rules.yaml
# Rules that avoid the traps in chapter 20.25. Metric names gateway_* and req_seconds_*
# are this chapter's own design. vllm:* names are from the vLLM metrics design doc.
# Assumes a 30 s scrape interval, so every range is at least 4 scrapes (2m).
groups:
  - name: c25_recording
    interval: 30s
    rules:
      # level:metric:operations. Rate first, then sum. Numerator and denominator
      # are summed separately and then divided.
      - record: model:gateway_requests:rate5m
        expr: sum by (model) (rate(gateway_requests_total[5m]))
      - record: model:gateway_errors:rate5m
        expr: sum by (model) (rate(gateway_errors_total[5m]))
      - record: model:gateway_errors:ratio_rate5m
        expr: model:gateway_errors:rate5m / model:gateway_requests:rate5m
      # Keep le when summing buckets, or histogram_quantile has nothing to read.
      - record: model_le:req_seconds_bucket:rate5m
        expr: sum by (model, le) (rate(req_seconds_bucket[5m]))
      - record: model:req_seconds:p99
        expr: histogram_quantile(0.99, model_le:req_seconds_bucket:rate5m)
      # Saturation: the worst pod, not the average.
      - record: model_name:vllm_kv_cache_usage_perc:max
        expr: max by (model_name) (vllm:kv_cache_usage_perc)
  - name: c25_alerts
    rules:
      - alert: QueueDeep
        expr: gateway_queue_depth > 500
        for: 5m
        keep_firing_for: 3m
        labels: {severity: ticket}
        annotations:
          summary: "{{ $labels.model }} queue deeper than 500 for 5m"
      - alert: ErrorRatioHigh
        expr: model:gateway_errors:ratio_rate5m > 0.05
        for: 5m
        labels: {severity: page}
        annotations:
          summary: "{{ $labels.model }} error ratio above 5%"
      - alert: VllmTargetsMissing
        expr: absent(up{job="vllm"})
        for: 5m
        labels: {severity: page}
        annotations:
          summary: "no vllm targets are being scraped"
      - alert: VllmPodDown
        expr: up{job="vllm"} == 0
        for: 2m
        labels: {severity: ticket}
        annotations:
          summary: "{{ $labels.pod }} is not scrapable"
      - alert: KVCacheSaturated
        expr: |
          model_name:vllm_kv_cache_usage_perc:max > 0.95
          and on (model_name)
          sum by (model_name) (vllm:num_requests_waiting) > 0
        for: 10m
        labels: {severity: page}
        annotations:
          summary: "{{ $labels.model_name }} KV cache full and requests are queueing"
```

`promtool check rules` reports 11 rules found. The test file covers the alerts and one recorded quantile. A passing check tells you the syntax is right. It does not tell you the query means what you intended, which is why the test file exists as a second step.

**Name every rule level:metric:operations, and record the expensive expression once instead of running it in every panel.**

### 11. Offset, subqueries and what they do to time

Week-over-week comparison is a classic panel. Today's p99 sits next to the p99 from the same hour a week ago, so a regression is obvious at a glance. The query needs `offset`, and the position of that word matters.

The docs say `offset` must follow the selector immediately. Writing `rate(x[5m]) offset 1h` is a parse error, and `promtool` says so: "offset modifier must be preceded by an instant vector selector or range vector selector or a subquery". The correct form is `rate(x[5m] offset 1h)`, with the offset inside the bracket that holds the selector. The docs also warn that a negative offset looks ahead of the evaluation time, which means the query reads data that has not happened yet from the point of view of the panel.

A subquery runs an instant query repeatedly over a range, and its resolution defaults to the global evaluation interval. It is useful for functions that need a range, such as the maximum of a rate over an hour. It is also the tool that makes the sum-first trap in idea 3 possible, so treat any `rate(sum(...)[5m:1m])` as suspect. The expression looks harmless, and it hides a reset in exactly the way idea 3 described.

**Put offset on the selector, and use a subquery only when you can say what resolution it samples at.**

### 12. Cardinality: the cost behind every label

A new label named `request_id` ships on a Friday afternoon. By Monday Prometheus is out of memory. Every distinct value makes a new series, and a histogram makes many series per value. The label looked like one extra dimension. In fact it multiplied everything by the number of requests.

*Production Kubernetes*, in its chapter on observability, warns that overusing labels makes resource use untenable and points to the instrumentation guide. The arithmetic is the lesson. A histogram with 10 finite buckets has 13 series per label set, counting `+Inf`, `_sum` and `_count`. With 20 models and 1,000 tenants that is 260,000 series. Those counts are my assumed inputs, not a Nebius figure. A single request ID label multiplies that by the number of requests.

Keep user, request and prompt identifiers out of metric labels. They belong in logs and traces, where one line per request is the normal shape of the data. Chapter 20.15 covers how a pipeline controls cardinality at scale, and chapter 20.19 covers the page-by-model, ticket-by-tenant split.

**Label metrics by things you can count on one hand, and put identifiers in traces.**

### 13. Tracing a streaming request

![The four fields of a traceparent header and a table of gateway, router and engine spans for a streaming request.](./img/p3-2025-traceparent-anatomy.svg)

*Figure 20.25.13. One span per hop, with the gateway span covering the whole stream.*

A user says the answer started late. The gateway shows a healthy p50 and the engine shows a healthy queue. Both dashboards look fine, so neither one explains the complaint. You need to see one slow request end to end, from the moment it entered the gateway to the moment its last token left.

The OpenTelemetry docs define a span as a unit of work or operation. Context propagation, in their words, is the core concept that enables distributed tracing. The W3C Trace Context specification defines the `traceparent` header as version, trace ID, parent ID and trace flags, with fields of 2, 32, 16 and 2 hex characters. The least significant bit of the flags is the sampled bit. Each service reads the header, creates a child span, and passes a new header to the next hop. The header is the thread that ties the spans of one request together.

A streaming request is awkward because the HTTP status is sent early and the work continues for seconds. The 200 goes out before the first token, and the tokens keep coming after it. A design that I think works, and that Nebius has not published, is below. Treat it as my reasoning, except where the table says what vLLM v0.32.0 does.

![Tracing a streaming request](./img/m20-25-2.svg)

*Figure 20.25.14. Tracing a streaming request, as a diagram.*

| Span | Kind | Lives until | Attributes and events |
|---|---|---|---|
| Gateway request | server | last token or abort | model, status, finish reason, token counts, event `first_token` |
| Router decision | internal | replica chosen | replica, retries, queue depth seen |
| Engine request | server | last token | queue wait, prefill and decode times as attributes. vLLM v0.32.0 sets these on one span. It does not emit a preemption event. |

Two rules make this work. The gateway span stays open until the stream ends, and its status is set to Error if the stream fails after a 200 was sent. Without that rule, the trace says success for a request the user saw break in the middle. The OTel docs say status takes one of three values, Unset, Error or Ok. Put the first-token moment on the span as an event, because a span event is a structured log message on a span.

vLLM documents tracing through the flags `--otlp-traces-endpoint` and `--collect-detailed-traces`. This comes from the v0.32.0 source, the version chapter 20.22 pins. The first flag sets the OTLP target, which is the address where the traces are sent. The second takes `model`, `worker` or `all`, needs the first flag, and the source warns it can be costly or blocking. With tracing on, the output processor emits one span named `llm_request` when a request finishes. It has kind SERVER and takes its parent from the incoming trace headers. Its attributes are time to first token, end-to-end time, time in queue, prefill, decode and inference time, token counts, request ID and some sampling parameters. So the engine hop gives you one span with timing attributes, not child spans for queue, prefill and decode. Plan your dashboards around that shape.

**One span per hop, the gateway span covers the whole stream, and failure after the 200 must set span status.**

### 14. Sampling and joining traces to metrics

![Five steps from a red bar on a metrics panel through an exemplar and a trace to the matching log lines using one trace ID](./img/x25-exemplar-join-path.svg)

*Figure 20.25.15. Metrics to traces: an exemplar on a slow bucket links the panel to one trace, and the same trace ID finds the matching log lines.*

At high volume you cannot keep every trace. Storing each one costs money and attention, and most of them show a request that went fine. The question is which traces to keep. The OTel docs split sampling into two approaches, and the choice between them is a trade-off that you need to explain in your own words.

Head sampling decides as early as possible. It is simple and efficient, but it cannot guarantee that a trace containing an error is kept, because the decision was made before the error happened. Tail sampling decides after it sees all or most of the spans and can keep slow or failed traces. The docs call it harder to implement and operate, because it needs stateful components handling large volumes. The Collector includes a Tail Sampling Processor.

The join between metrics and traces is the exemplar. The Prometheus feature-flag page says OpenMetrics lets scrape targets attach exemplars, and a common use is trace IDs. The flag is `--enable-feature=exemplar-storage`. The page says an exemplar with only a trace ID uses roughly 100 bytes in memory, in a fixed-size circular buffer. In Grafana, you add an exemplar link on the Prometheus data source settings. Choose an internal link to a tracing data source, or an external URL, and set the label name that holds the trace ID, often `trace_id` or `traceID`. Then switch on the Exemplars toggle in the query editor. Exemplars do not work with instant queries.

With an exemplar on a slow bucket you go from the panel to one trace. In that trace you find the trace ID, and in logs you search the same ID. Put `trace_id` on every log line from the gateway and the engine. That one habit lets you walk from a red bar on a graph to the exact request that made it red.

**Keep errors and slow traces with tail sampling, attach trace IDs to exemplars and logs, and never put them in labels.**

## How to answer out loud

Picture the end of the round, when the interviewer asks you to walk through each answer again in your own words. Each of these answers is written to be said, not read. Say it once aloud, then listen for the place where you stumbled. That stumble is usually a missing sentence about why.

### Question 1: "What is wrong with a p99 panel that averages across pods?"

Picture the interviewer nodding at the panel and waiting for your first sentence. Start with what the average does, because that is where the bug lives. Percentiles do not add and do not average, because each one hides how many requests stand behind it. Use the example to make it concrete. Two pods, one busy with p99 0.95 s and one idle with p99 1.99 s, give an average of 1.47 s, while the true p99 is 0.99 s. Then give the fix in order: rate the buckets, `sum by (le)`, and take `histogram_quantile` once. Expect the follow-up on bucket resolution, and answer that interpolation is only as good as your bucket boundaries.

### Question 2: "Explain rate versus irate and how you pick a window."

Picture the interviewer asking why your alert and your graph use different functions. Open with the rule: rate for alerts, irate for fast graphs. Explain that irate uses the last two samples, so it reacts to the newest moment and forgets the burst before it. Then give the window: at least four scrape intervals, so a 30-second scrape needs two minutes. Mention that Grafana's `$__rate_interval` does this when the data source scrape setting is right. Expect the follow-up about a wrong default scrape setting in Grafana returning no data.

### Question 3: "The alert never fired during the outage. Why?"

Picture the question a manager asks after an outage: why did nobody get paged? Say you check three things in order, because each check rules out one layer. Did the series disappear and leave the expression empty? Was there a `for` that was longer than the outage? Did Alertmanager inhibit it? Describe the stale marker and the five-minute lookback, since they explain why a vanished series gives nothing rather than zero. Offer the three-layer fix: `up == 0`, a count of expected series, and `absent` for blackout. Expect to be asked how you would test it, and answer with `promtool test rules` and a deleted series.

### Question 4: "Pager noise is too high. What do you change?"

Picture an on-call engineer who was paged over and over for one incident. Start from the person: one page per thing they must act on. Group by cluster and model, inhibit symptoms under a cause alert, add `for` and `keep_firing_for`, and route tickets away from the pager. Quote the defaults, 30 s, 5 m and 4 h. Name the trade-off: a longer `group_wait` delays the first page, so you are choosing a small delay over a flood. Expect a follow-up on how you avoid hiding a real second incident behind an inhibition, and answer that the inhibition only covers the same cluster, and for the page rule the same model.

### Question 5: "How would you trace a streaming request?"

Picture the interviewer sketching three boxes on a whiteboard and asking you to finish the picture. Draw gateway, router, engine. Say the header carries the context from one hop to the next. Say the gateway span covers the whole stream and carries a first-token event. Say tail sampling keeps errors and slow traces, because it decides after it has seen the spans. Say exemplars link a slow bucket to a trace. Label the design as yours, not Nebius's, so the interviewer can tell which parts are published and which are your reasoning.

## Worked scenarios

Picture three pages arriving during the same on-call shift, each one with a symptom that looks simple. Each scenario below is a short case file. It starts with the symptom, walks through the evidence in the order you would check it, and ends with the sentence you would say. The numbers come from the chapter's own tests and runs, so you can check them yourself.

### Scenario 1: The flat p99

A dashboard shows p99 TTFT at 0.4 seconds. Customers say it is slow. The panel query is the average of per-pod quantiles.

The panel is the first suspect, not the users. Start by asking what the panel computes. Here it averages a percentile from each pod, which is the trap from idea 4.

First rerun it as the fleet quantile. Sum the bucket rates by model and le, then apply the quantile once. Then check bucket coverage. If the SLO limit is 1 second and no bucket sits near it, interpolation is coarse. Finally check traffic skew. If one pod gets most requests, the average hides it.

Run the linter on the old query. It reports P003 for averaging a quantile. The answer is the `sum by (le)` form, which the exercise test shows gives 0.99 where the average gave 1.47. The two numbers tell the same story as the busy and idle pods in idea 4, now on a dashboard you can actually see.

### Scenario 2: The silent outage

![Two quiet alerts during a pod loss and the up, count and absent checks that would have caught the shrinking fleet.](./img/p3-2025-silent-outage-count.svg)

*Figure 20.25.16. Count what should be there, because a vanished series returns nothing rather than zero.*

One of four vLLM pods crashes at night. The error ratio alert stays quiet because requests moved to other pods. The `absent` alert is quiet too.

Notice that both alerts are quiet for good reasons. Nothing is wrong with the traffic that is still arriving. The failure is a shrinking fleet, and neither alert was written to notice a shrinking fleet.

The first alert is right: no errors exist. The `absent` alert is quiet because three pods still report. Add `up == 0` for two minutes and a count below four. The test in this chapter deletes one of two pods and shows `absent` empty and the count returning 1. The count is the alert that matches this outage, because it counts what should be there.

Also make the router alert on lost capacity, since the loss shows up as saturation on the survivors. That is chapter 20.18 territory.

### Scenario 3: Forty pages for one cause

A node fails. Scrape targets go away, the error ratio rises, KV cache saturates on the survivors and a queue alert fires.

Count the alerts before you count the pages. Several alerts all come from one cause, the failed node. The goal of the Alertmanager config is to turn that pile into one clear message that tells the on-call person what to look at first.

The Alertmanager config groups by cluster and model, so alerts for one model arrive as one notification. The inhibition rule silences symptom alerts while `VllmTargetsMissing` fires in the same cluster. The page rule silences tickets for the same model. The routing script confirms the pages go to the pager. Run against Alertmanager 0.35.0 in a throwaway container, as the lab describes, the grouping and inhibition behave as described.

## Hands-on lab

Picture a laptop with the rule files open, a clean terminal and no cluster in sight. Everything you need runs locally, so you can break the rules on purpose and watch what the tools say. Each step below uses one of the chapter's files.

All steps run on a laptop with `promtool`, `amtool` and Python. No Docker is needed. Every step below was run on macOS.

1. Check the rules. Before you trust the rule file, ask the syntax checker whether it even parses. Run `promtool check rules code/part20/c25_trap_rules.yaml`. It should print `SUCCESS: 11 rules found`.
2. Run the exercise tests. Next, check that each bad query and its fix still behave as the chapter says. Run `promtool test rules code/part20/c25_exercises_test.yaml`. It should print `SUCCESS`. Change one expected value and read the diff it prints.
3. Run the alert tests. Now test the alerts themselves, not only the queries. Run `promtool test rules code/part20/c25_trap_rules_test.yaml`. It should print `SUCCESS`.
4. Check the Alertmanager config. Move on to routing. Run `amtool check-config code/part20/c25_alertmanager.yml`. It should list 2 inhibit rules and 2 receivers. Then run `code/part20/c25_route_check.sh`, and expect three `ok` lines.
4b. Run the real Alertmanager. This step checks behaviour, not syntax. Start `prom/alertmanager` in Docker with the config. Point both webhooks at a small receiver on the host. Post three alerts for one model and cluster, one for another model, and one `VllmTargetsMissing`. Two ticket alerts for model m1 arrived as one notification listing both. A page alert for model m2 reached the pager, and the ticket alert for the same model was inhibited. In cluster c2, `QueueDeep` with severity page was inhibited while `VllmTargetsMissing` was firing. The API listed the inhibited alerts as suppressed. The timing values were not measured to the second.
5. Lint the good and bad rules. The linter checks patterns, not meaning, so it is a second opinion. Run `python3 code/part20/c25_promql_lint.py code/part20/c25_trap_rules.yaml`, which should report 0 findings. Run the same command on `c25_bad_rules.yaml`. It reports 5 warnings and exits 0. Add `--strict`, and it exits 1.
6. Run the pytest suite. Next, test the linter itself. Run `python3 -m pytest code/part20/test_c25_promql_lint.py`. It should report 38 passed.
7. Break an offset on purpose. A parse error you have seen once is easy to spot later. Write `rate(gateway_requests_total[5m]) offset 1h` into a rule file. Run `promtool check rules` on it. Expect the parse error quoted in idea 11.
8. Break a join on purpose. Build two vLLM series for one pod and one `kube_pod_info` series. Query them without `group_left`. Expect `promtool` to print the many-to-one error quoted in idea 7.

## The 15 exercises: what is wrong with this query

![A table of five query mistakes with their errors and fixes, covering absent, joins, labels, extrapolation and offset.](./img/p3-2025-query-mistakes-alerts.svg)

*Figure 20.25.17. A query that parses can still mean something other than what you intended.*

Picture a pull request that changes one line of a dashboard query and claims the panel is now correct. Each exercise below is that kind of change, with the bad query, the reason it fails and the fix. The status line says how it was checked. "Test" means `promtool test rules` passed with the bad and fixed query asserted. "Lint" means the linter flags the bad one.

| # | Bad query | What is wrong | Fix | Checked |
|---|---|---|---|---|
| 1 | `rate(gateway_requests_total[30s])` | Range holds one scrape at 30 s, so the result is empty | `[2m]` | Test, lint P001 |
| 2 | `irate(gateway_errors_total[5m]) > 1` | Uses the last two samples and misses the burst | `rate(...[5m])` | Test, lint P005 |
| 3 | `x - x offset 10m` | Goes negative after a restart | `increase(x[10m])` | Test |
| 4 | `rate(sum(x)[5m:1m])` | Sum hides one pod's reset, 1.38 versus 1.79 | `sum(rate(x[5m]))` | Test, lint P004 |
| 5 | `histogram_quantile(0.99, sum by (pod) (rate(b[5m])))` | `le` removed, empty result | `sum by (le)` | Test, lint P002 |
| 6 | `avg(histogram_quantile(0.99, sum by (pod, le) ...))` | Average of p99s is 1.47, true p99 is 0.99 | Merge buckets, one quantile | Test, lint P003 |
| 7 | `absent(up{job="vllm"})` | Silent when one of two pods is gone | `count(up{job="vllm"}) < 2` | Test |
| 8 | Alert `queue > 500`, no `for` | Pages on a single spike | `for: 5m`, `keep_firing_for: 3m` | Rules test, lint P008 |
| 9 | `waiting * on (pod) kube_pod_info` | Many-to-one error | add `group_left (node)` | Test, ran the error |
| 10 | `sum(rate(errors[5m])) > 1` with `$labels.model` | Aggregation drops the label the annotation uses | `sum by (model)` | Rules test, lint P010 |
| 11 | `increase(restarts[10m]) == 1` | Extrapolated value is 1.11 | `> 0` | Test |
| 12 | `rate(x[5m]) offset 1h` | Parse error | `rate(x[5m] offset 1h)` | Ran the error |
| 13 | `rate(vllm:num_requests_waiting[5m])` | Rate of a gauge, returns 0 for a steady queue of 7 | `avg_over_time(...)` | Test, lint P006 |
| 14 | `avg(vllm:kv_cache_usage_perc)` | Shows 0.53 while one pod is at 1 | `max(...)` | Test |
| 15 | `avg(errors_rate / requests_rate)` | Averages a ratio, 0.25 versus 0.002 | Sum both, then divide | Test, lint P007 |

The linter is regex-level. It cannot parse PromQL, so it misses nested cases and can misfire on names. The excerpt below shows the histogram rule, which is the one the interviewer most often has in mind. Read it as a rule about the `le` label. If the aggregation inside `histogram_quantile` has a `by` list without `le`, the rule raises an error.

```python
# excerpt from code/part20/c25_promql_lint.py (P002)
m = re.search(AGG + r"\s*(?:(by|without)\s*\(([^)]*)\)\s*)?\(", arg)
if m:
    mode, labels = m.group(1), m.group(2) or ""
    has_le = bool(re.search(r"\ble\b", labels))
    if not mode:
        add("P002", "error", "aggregation with no by() inside histogram_quantile drops the le label")
    elif mode == "by" and not has_le:
        add("P002", "error", "aggregation by() inside histogram_quantile does not keep le")
```

The test data behind the numbers is in the file below. It is longer than 120 lines, so only a group is shown here. Read the group as a small story. The counter climbs, resets to zero, and climbs again, and the test checks what each query says about that story.

```yaml
# excerpt from code/part20/c25_exercises_test.yaml (E3)
  - name: E3 subtracting a counter breaks on a restart
    interval: 1m
    input_series:
      - series: 'queue_processed_total{pod="a"}'
        values: '0+10x10 0+10x10'
    promql_expr_test:
      - expr: queue_processed_total{pod="a"} - queue_processed_total{pod="a"} offset 10m
        eval_time: 15m
        exp_samples:
          - labels: '{pod="a"}'
            value: -10
      - expr: increase(queue_processed_total{pod="a"}[10m])
        eval_time: 15m
        exp_samples:
          - labels: '{pod="a"}'
            value: 88.88888888888889
```

## Drill questions

Picture the interviewer reading the questions one at a time, with no notes in front of you. Answer each one in your own words first, then open the answer and compare.

<details><summary>1. Why does rate over a range equal to one scrape interval return nothing?</summary>

The range holds a single sample, and a slope needs two. The range is left-open, so a sample exactly at its start is excluded. Use at least four scrape intervals.
</details>

<details><summary>2. What does irate use, and when is it a trap?</summary>

It uses the last two data points. It suits graphs of fast counters. In alerts it misses bursts and makes flapping.
</details>

<details><summary>3. Why do you take rate before sum?</summary>

Rate repairs counter resets per series. Summing first hides a reset in the total. In the test the sum-first form gave 1.38 and the correct form 1.79.
</details>

<details><summary>4. What must sum keep before histogram_quantile?</summary>

The `le` label. Write `sum by (le)` or add it to your other labels. Without it the result is empty.
</details>

<details><summary>5. Why is averaging p99 across pods wrong?</summary>

A percentile ignores how many requests stand behind it. Merge the buckets and take one quantile. The example gave 1.47 for the average and 0.99 for the true value.
</details>

<details><summary>6. When does absent fire, and what does it miss?</summary>

It fires when the whole selector returns nothing. It misses the loss of one of several series. Use a count of expected series for that.
</details>

<details><summary>7. What does for do, and what does keep_firing_for do?</summary>

`for` keeps the alert pending until the condition has held that long. `keep_firing_for` keeps it firing for a time after the condition stops. Together they stop one-sample pages and flapping.
</details>

<details><summary>8. What are the Alertmanager defaults for group_wait, group_interval and repeat_interval?</summary>

30 seconds, 5 minutes and 4 hours. They come from the Alertmanager configuration reference.
</details>

<details><summary>9. How do you name a recording rule?</summary>

`level:metric:operations`. The level is the aggregation labels, the metric loses `_total`, and the operations list the newest first.
</details>

<details><summary>10. What does a traceparent header carry, and what does the sampled flag mean?</summary>

Version, trace ID, parent ID and trace flags. The lowest bit says the caller may have recorded trace data.
</details>

## Common mistakes and weak answers

Imagine the interviewer's notes at the end of the round. The same few marks show up on weak answers, and each one has a one-sentence fix that you can practise before the interview.

- Saying "I would average the p99s". Say you would merge buckets and take the quantile once, because an average of percentiles ignores how many requests stand behind each one.
- Using a window of one scrape interval. Say at least four, and name `$__rate_interval`, which does the arithmetic for you when the data source is set right.
- Alerting on `irate`. Say rate, and explain the missed burst that `irate` hides at the end of the window.
- Writing `absent` and calling the outage covered. Say it only covers a total blackout, and add a count for partial loss.
- Showing average KV cache usage alone. Say you show the maximum and the waiting queue beside it.
- Putting a request ID in a metric label. Say it belongs in the trace and the log, where one line per request is the right shape.
- Claiming Nebius uses a given monitoring stack. Say what is public and label the rest as your design.

## Connections to the rest of the handbook

Picture the next place you would go after this chapter, once the query traps feel familiar. Each link below takes one piece of this chapter further, and you can read them in any order.

- Chapter 20.19, [SLIs, SLOs and alerts for token APIs](19-slis-slos-and-alerts-for-token-apis.md), owns burn-rate maths and bucket alignment. This chapter assumes it.
- Chapter 20.15 owns the observability pipeline: collectors, storage and cost at volume. It is written separately, so this chapter does not cover pipeline architecture.
- Chapter 20.18, [How LLM serving fails](18-how-llm-serving-fails.md), explains the queue and KV cache saturation the panels should show.
- Chapter 20.26, [The stress interview](26-the-stress-interview-production-incident-role-play.md), is where you practise reading these dashboards under time pressure.
- Chapter 20.13, [Design: a multi-tenant LLM inference API](13-design-a-multi-tenant-llm-inference-api.md), is where gateway, router and engine spans belong.
- Part 17, [logging and tracing](../part-17-operations/03-logging-with-loki-and-tracing-with-opentelemetry.md), covers the tooling for logs and traces.

## Sources and review notes

Sources, all fetched 2026-11-09 unless stated:

- Prometheus docs, "Query functions", https://prometheus.io/docs/prometheus/latest/querying/functions/. Latest docs, no version number shown. rate, irate, increase, histogram_quantile, absent, resets.
- Prometheus docs, "Querying basics", https://prometheus.io/docs/prometheus/latest/querying/basics/. Staleness, offset, subqueries, range selectors.
- Prometheus docs, "Alerting rules", https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/. `for`, `keep_firing_for`.
- Prometheus Alertmanager docs, overview and configuration pages under https://prometheus.io/docs/alerting/latest/. Grouping, inhibition, silences, defaults.
- Prometheus docs, "Recording rules" practices, https://prometheus.io/docs/practices/rules/. Naming and aggregation guidance.
- Prometheus docs, feature flags, https://prometheus.io/docs/prometheus/latest/feature_flags/. Exemplar storage.
- Grafana docs, dashboard best practices and Prometheus template variables. USE and RED, `$__rate_interval`.
- OpenTelemetry docs, traces and sampling concepts, https://opentelemetry.io/docs/concepts/. Spans, context propagation, status, head and tail sampling.
- W3C Trace Context, https://www.w3.org/TR/trace-context/. traceparent format.
- vLLM docs, metrics design page, https://docs.vllm.ai/en/latest/design/metrics.html. Latest developer docs, no version shown. Metric names and the tracing flags. The vLLM OpenTelemetry example page returned 404.
- vLLM v0.32.0 source from github.com/vllm-project/vllm: `vllm/config/observability.py`, `vllm/engine/arg_utils.py`, `vllm/v1/engine/output_processor.py` and `docs/usage/metrics.md`, fetched 2026-11-09.
- Grafana documentation sources: Prometheus data source configuration and query editor, and template variables, from github.com/grafana/grafana `main`, fetched 2026-11-09.
- Alertmanager 0.35.0 docker image `prom/alertmanager:latest`, pulled 2026-11-09.
- Systems Performance, 2nd edition, Chapter 2 "Methodologies": utilization, saturation, the USE method.
- Production Kubernetes, Chapter 9 "Observability": Prometheus model, label cardinality, Alertmanager.
- LLMs in Production, Chapter 3: streaming and completion length affect latency. Used only as background for per-token metrics.
- AI Factory: I searched it for monitoring and metrics. It covers industrial AI and has nothing on PromQL, Grafana or tracing, so I did not use it for any claim.
- Plan for this volume, section 1, for the job posting wording.

Explicitly labelled inferences:

- The mapping of KV cache usage to utilization and queue depth to saturation.
- The span design for a streaming request, the span table and the choice to hold the gateway span open for the whole stream.
- The cardinality example with 20 models, 1,000 tenants and 13 series per histogram.
- The Alertmanager route layout and inhibition rules.
- The metric names `gateway_*` and `req_seconds_*` are this chapter's own.

Not verified:

- No Prometheus server was run, so real scraping was not exercised. Alertmanager grouping and inhibition were run on 2026-11-09, but group_wait and group_interval timing was not measured. My short-timer test showed notifications earlier than the configured values, and I did not work out why.
- No vLLM server was run, so the `llm_request` span is read from source, not observed.
- Which spans vLLM actually emits, and whether the vLLM docs page shown matches your installed version.
- The linter is regex-level and was tested only on the cases in its test file.

### Verification log

Fact-check pass on 2026-11-09. Eleven claims were checked. Ten are confirmed, one was corrected and none are left unverified except the group timing noted above.

| Claim | Result | Source |
|---|---|---|
| Alertmanager defaults: group_wait 30s, group_interval 5m, repeat_interval 4h | Confirmed | Alertmanager configuration reference, main |
| Grouping by cluster and model merges alerts into one notification | Confirmed by running Alertmanager 0.35.0 | Container run |
| Inhibition rules suppress the target alerts, including a page-severity target | Confirmed by running | Container run |
| Source and target matchers should not match the same alert | Confirmed | Alertmanager configuration reference |
| Lookback delta is 5 minutes | Confirmed | Prometheus querying basics |
| `keep_firing_for` exists | Confirmed | Prometheus alerting rules page |
| Exemplar flag is `--enable-feature=exemplar-storage`, about 100 bytes per exemplar | Confirmed | Prometheus feature flags page, main |
| `$__rate_interval` is the larger of interval plus scrape interval and four scrape intervals | Confirmed | Grafana template variables page |
| Grafana exemplar setting | Resolved: data source exemplar link plus the query toggle | Grafana docs, main |
| vLLM tracing flags exist at v0.32.0 | Confirmed | `observability.py`, `arg_utils.py` |
| The engine emits queue, prefill and decode spans, and a preemption event | Corrected: one `llm_request` span with timing attributes, no preemption event | `output_processor.py` v0.32.0 |
