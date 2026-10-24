---
id: "c05-30"
title: "5.30 Go for Kubernetes engineers"
sidebar_label: "5.30 Go for Kubernetes engineers"
sidebar_position: 30
description: "The Go you need to read and write Kubernetes tooling: toolchain and modules, types, structs, interfaces, errors, slices/maps, goroutines/channels/context, generics, testing, JSON/YAML, building CLIs, and using client-go (clientsets, dynamic client, informers, listers, work queues, patching, watching) with idioms and pitfalls"
status: "drafted"
tier: "2"
level: "I"
lab_venue: "GCP / GKE"
---

# 5.30 Go for Kubernetes engineers

| | |
|---|---|
| Level | Intermediate |
| Priority tier | 2 |
| Lab venue | Go 1.22 or newer, kind cluster, `kubectl`; modules `k8s.io/client-go`, `k8s.io/apimachinery`, `k8s.io/api`, `github.com/spf13/cobra` |
| Part | Part 5: Kubernetes |
| Status | Drafted; key listings compile and unit-test (Go 1.23.2, client-go v0.31.0); live-cluster labs **untested** |

## Why this matters for AI infrastructure

Kubernetes and most of its ecosystem (containerd, etcd, Prometheus, Terraform providers, the NVIDIA GPU Operator, device plugins, CSI drivers, Kueue, Argo, Cilium) are written in Go. Platform engineers who can read Go can debug operator behaviour from source, patch or extend components, write small controllers and CLI tools (a node-health remediator, a quota reporter, an admission webhook), and understand error messages and stack traces that come straight from the codebase. You do not need to be a Go expert, but you need fluency with the language subset and the client libraries that Kubernetes tooling uses. This chapter teaches that subset with Kubernetes examples, and sets up 5.31 (operators with controller-runtime), 5.32 (a GPU node health operator) and 5.33 (reading the GPU and Network Operator source).

## Prerequisites and outcomes

Needs programming experience (Part 3 Python) and 5.3 to 5.6. After this chapter you can:

- Set up a Go module, use the toolchain (`go build/test/vet/fmt/mod`, `gopls`, `golangci-lint`), and navigate a large Go repository.
- Use Go's core features correctly: types, structs, methods, interfaces (implicit satisfaction), embedding, pointers vs values, slices and maps, errors (wrapping, `errors.Is/As`), `defer`, `panic/recover`, generics.
- Write concurrent programs with goroutines, channels, `sync` primitives and `context`, avoiding leaks and races; use the race detector.
- Handle JSON/YAML and Kubernetes types (struct tags, `metav1.ObjectMeta`, `runtime.Object`, `unstructured`).
- Use client-go: build a client from kubeconfig/in-cluster config, list/get/create/patch/delete, watch, informers/listers, work queues, leader election, dynamic client, discovery; apply best practices for rate limits and retries.
- Write table-driven tests, fake clients, and use `envtest`; structure a CLI with cobra; produce small static container images.

## 1. Toolchain and project layout

```bash
go version                                  # 1.22+ recommended; check go.mod 'go' directive and toolchain line
mkdir nodectl && cd nodectl && go mod init example.com/nodectl
go get k8s.io/client-go@v0.31.0 k8s.io/apimachinery@v0.31.0 k8s.io/api@v0.31.0   # match your Kubernetes minor version (client-go v0.N ↔ Kubernetes 1.N)
go mod tidy
go build ./... && go vet ./... && go test ./... -race -count=1
gofmt -s -w . && goimports -w .             # formatting is not negotiable; CI should check
golangci-lint run                           # linters (errcheck, staticcheck, govet, ineffassign, unused, revive ...)
go doc k8s.io/client-go/kubernetes.Clientset
GOFLAGS=-mod=readonly go build -trimpath -ldflags='-s -w' -o bin/nodectl ./cmd/nodectl
CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build ...        # static binary for scratch/distroless images
```

Typical layout (the "standard" repo shape used by kubebuilder projects):

```text
nodectl/
├── go.mod, go.sum
├── cmd/nodectl/main.go          # entry point(s) (thin: parse flags, wire dependencies)
├── internal/                    # private packages (cannot be imported by other modules)
│   ├── kube/                    # client construction, helpers
│   └── health/                  # domain logic (pure, easily tested)
├── pkg/                         # public packages (optional)
├── api/v1alpha1/                # CRD Go types (kubebuilder)
├── Makefile, Dockerfile, .golangci.yml
└── hack/                        # scripts (codegen, tools)
```

Modules: semantic import versioning (`/v2` suffix), `replace` for local forks, `go.work` for multi-module work, vendoring optional (`go mod vendor`); Kubernetes libraries have a tight version coupling (client-go, apimachinery, api, controller-runtime versions must be compatible; check the compatibility matrix); `go.sum` verifies hashes; `GOPROXY`/`GOFLAGS` for private modules (`GOPRIVATE`).

## 2. Language essentials (the subset Kubernetes code uses)

### Types, structs, methods

```go
package health

import "time"

// XIDEvent is a GPU error event reported by DCGM or kernel logs.
type XIDEvent struct {
	Node  string
	GPU   int
	Code  int
	Seen  time.Time
}

type Severity int

const (
	SeverityInfo Severity = iota // iota: 0,1,2...
	SeverityWarn
	SeverityCritical
)

func (s Severity) String() string {
	switch s {
	case SeverityInfo:
		return "info"
	case SeverityWarn:
		return "warn"
	case SeverityCritical:
		return "critical"
	default:
		return "unknown"
	}
}

// Classify maps an XID code to a severity (illustrative mapping).
func (e XIDEvent) Classify() Severity {
	switch e.Code {
	case 79, 74, 48: // fallen off bus, NVLink error, double-bit ECC (illustrative; verify against NVIDIA's catalogue)
		return SeverityCritical
	case 13, 31:
		return SeverityWarn
	}
	return SeverityInfo
}
```

- Exported identifiers start with a capital letter; packages are the unit of encapsulation; no classes or inheritance; **methods** have receivers (value or pointer). Use pointer receivers when the method mutates, the struct is large, or for consistency (don't mix on one type). Zero values are useful (`var s []int` is a nil slice, valid to append to; `var mu sync.Mutex` is ready to use).
- **Struct tags** control marshalling: `json:"name,omitempty"`, and Kubernetes types use `json` tags (and `protobuf`); `yaml` handled by `sigs.k8s.io/yaml` converting YAML→JSON→struct (so only `json` tags matter).
- **Composition by embedding**: `type Node struct { metav1.TypeMeta; metav1.ObjectMeta; Spec NodeSpec; Status NodeStatus }` — fields and methods promoted from embedded types (this is how every Kubernetes object gets `GetName()`, `GetLabels()`).

### Interfaces (implicit) and polymorphism

```go
type Remediator interface {
	Cordon(ctx context.Context, node string) error
	Drain(ctx context.Context, node string) error
}

type kubeRemediator struct{ cs kubernetes.Interface }       // *kubeRemediator satisfies Remediator implicitly

var _ Remediator = (*kubeRemediator)(nil)                   // compile-time assertion
```

Interfaces are satisfied implicitly (no `implements`). Idiom: "accept interfaces, return structs"; define small interfaces at the consumer (e.g., `kubernetes.Interface` allows `fake.NewSimpleClientset()` in tests). `any` (alias for `interface{}`) holds any value; type assertions (`v, ok := x.(T)`) and type switches (`switch t := x.(type)`) recover concrete types. Kubernetes uses `runtime.Object` (interface with `GetObjectKind()` and `DeepCopyObject()`) as the common supertype of API objects and `client.Object` in controller-runtime.

### Errors

```go
var ErrNoSuchNode = errors.New("no such node")

func cordon(ctx context.Context, cs kubernetes.Interface, name string) error {
	n, err := cs.CoreV1().Nodes().Get(ctx, name, metav1.GetOptions{})
	if apierrors.IsNotFound(err) {
		return fmt.Errorf("cordon %q: %w", name, ErrNoSuchNode)       // wrap with %w
	}
	if err != nil {
		return fmt.Errorf("get node %q: %w", name, err)
	}
	if n.Spec.Unschedulable {
		return nil
	}
	patch := []byte(`{"spec":{"unschedulable":true}}`)
	_, err = cs.CoreV1().Nodes().Patch(ctx, name, types.StrategicMergePatchType, patch, metav1.PatchOptions{})
	return err
}

if errors.Is(err, ErrNoSuchNode) { ... }                           // unwrap chain
var se *apierrors.StatusError
if errors.As(err, &se) && se.ErrStatus.Code == http.StatusConflict { ... }
```

Errors are values returned as the last result; check them immediately (`if err != nil`); wrap with context (`fmt.Errorf("...: %w", err)`); compare with `errors.Is`, extract with `errors.As`; Kubernetes API errors have helpers (`apierrors.IsNotFound/IsConflict/IsAlreadyExists/IsForbidden/IsTimeout/IsServerTimeout`); never ignore errors silently (`errcheck` lint); `panic` only for programmer errors/initialisation; `defer` for cleanup (`defer resp.Body.Close()`, `defer cancel()`, `defer mu.Unlock()`); `recover` rare (HTTP servers). Use `errors.Join` for multiple errors; aggregate utilities exist in apimachinery (`utilerrors.NewAggregate`).

### Slices, maps, strings, generics

```go
gpuNodes := make([]string, 0, len(nodes))                          // len 0, cap hint
for _, n := range nodes.Items {                                    // range copies values: take &nodes.Items[i] if you need pointers
	if q, ok := n.Status.Allocatable["nvidia.com/gpu"]; ok && !q.IsZero() {
		gpuNodes = append(gpuNodes, n.Name)
	}
}
slices.Sort(gpuNodes)                                              // std lib 'slices' and 'maps' packages (Go 1.21+)
idx, found := slices.BinarySearch(gpuNodes, "node-7")

counts := map[string]int{}                                         // maps: iteration order is random; not safe for concurrent writes
for _, p := range pods { counts[p.Spec.NodeName]++ }
keys := slices.Sorted(maps.Keys(counts))                           // deterministic output (Go 1.23)

func Filter[T any](in []T, keep func(T) bool) []T {                // generics (type parameters)
	out := in[:0:0]
	for _, v := range in { if keep(v) { out = append(out, v) } }
	return out
}
```

Gotchas: slices share backing arrays (append may or may not reallocate); loop variable capture semantics changed in Go 1.22 (each iteration has its own variable); nil map writes panic; string iteration yields runes; `copy` vs assignment; `for range n` (1.22) and range-over-func iterators (1.23). `strings.Builder`, `bytes.Buffer`, `fmt.Sprintf` verbs (`%v %+v %#v %T %w %q`).

### Pointers and values

Go passes everything by value (copies); pointers share. Kubernetes API types use pointers for optional fields (`*int32 Replicas`) to distinguish unset from zero; helpers: `ptr.To(int32(3))` (k8s.io/utils/ptr), `ptr.Deref(p, default)`. Objects from listers are **shared cache objects**: never mutate them; call `DeepCopy()` before modification. Struct comparison with `==` requires comparable fields; use `reflect.DeepEqual`, `equality.Semantic.DeepEqual` (apimachinery; handles resource.Quantity, metav1.Time).

### Packages, visibility, init, build tags

One directory = one package; `internal/` restricts imports; `init()` functions run at import (avoid side effects; Kubernetes API groups register schemes via `AddToScheme` functions explicitly); build constraints (`//go:build linux`); `go:embed` for static assets; `go:generate` for code generation (deepcopy-gen, controller-gen, mockgen).

## 3. Concurrency

### Goroutines, channels, sync

```go
func probeAll(ctx context.Context, nodes []string, probe func(context.Context, string) (bool, error)) map[string]bool {
	type result struct {
		node string
		ok   bool
	}
	ctx, cancel := context.WithTimeout(ctx, 30*time.Second)
	defer cancel()

	results := make(chan result)
	sem := make(chan struct{}, 16)                      // bound concurrency
	var wg sync.WaitGroup
	for _, n := range nodes {
		wg.Add(1)
		go func() {                                      // Go 1.22: n is per-iteration
			defer wg.Done()
			sem <- struct{}{}
			defer func() { <-sem }()
			ok, err := probe(ctx, n)
			if err != nil { ok = false }
			select {
			case results <- result{n, ok}:
			case <-ctx.Done():
			}
		}()
	}
	go func() { wg.Wait(); close(results) }()           // close when all senders are done

	out := make(map[string]bool, len(nodes))
	for r := range results { out[r.node] = r.ok }
	return out
}
```

Principles: goroutines are cheap, but **every goroutine needs a clear exit** (context cancel, channel close); "don't communicate by sharing memory; share memory by communicating" (use mutexes when state is simple: `sync.Mutex/RWMutex`); `sync.WaitGroup`, `sync.Once`, `sync/atomic`, `sync.Map` (rare), `errgroup.Group` (`golang.org/x/sync/errgroup`: wait + first error + context cancel + `SetLimit`); channels: unbuffered (rendezvous) vs buffered; only the sender closes; receiving from a closed channel yields zero values; `select` with `default`, timeouts (`time.After` leaks timers in loops pre-1.23; use `time.NewTimer`), `ctx.Done()`; avoid goroutine leaks (blocked sends/receives with no reader); data races undefined behaviour: run tests with `-race`; deadlocks (`all goroutines are asleep`). Kubernetes code uses `wait.Until`, `wait.PollUntilContextTimeout` (apimachinery/util/wait), rate-limited work queues rather than raw goroutines in controllers.

### context.Context

Carries cancellation, deadlines and request-scoped values across API boundaries; first parameter by convention (`ctx context.Context`); derive with `WithCancel/WithTimeout/WithDeadline/WithValue`; always `defer cancel()`; never store contexts in structs for long-lived use; pass `ctx` to every client-go call (`Get(ctx, name, opts)`); respect `ctx.Err()` in loops; controller-runtime passes a per-reconcile context.

## 4. JSON, YAML and Kubernetes types

```go
import (
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"sigs.k8s.io/yaml"
)

pod := &corev1.Pod{
	ObjectMeta: metav1.ObjectMeta{Name: "gpu-test", Namespace: "default", Labels: map[string]string{"app": "gpu-test"}},
	Spec: corev1.PodSpec{
		RestartPolicy: corev1.RestartPolicyNever,
		Containers: []corev1.Container{{
			Name:    "cuda",
			Image:   "nvcr.io/nvidia/cuda:12.4.1-base-ubuntu22.04",
			Command: []string{"nvidia-smi"},
			Resources: corev1.ResourceRequirements{
				Limits: corev1.ResourceList{"nvidia.com/gpu": resource.MustParse("1")},
			},
		}},
	},
}
b, _ := yaml.Marshal(pod)                      // sigs.k8s.io/yaml: struct → JSON → YAML
var p2 corev1.Pod
_ = yaml.Unmarshal(b, &p2)
```

- `resource.Quantity` (`resource.MustParse("100Mi")`, `.Value()`, `.MilliValue()`, `.Cmp()`) for CPU/memory/GPU counts; `metav1.Time`, `metav1.Duration`; `intstr.IntOrString`; `metav1.LabelSelector` ↔ `labels.Selector` via `metav1.LabelSelectorAsSelector`.
- **Unstructured**: `unstructured.Unstructured` wraps `map[string]interface{}` for objects whose Go types you don't have (CRDs without generated types); helpers `unstructured.NestedString/NestedSlice/SetNestedField`; `runtime.DefaultUnstructuredConverter.FromUnstructured` to convert to typed.
- **Scheme and codecs**: `runtime.Scheme` maps Go types ↔ GroupVersionKind; `scheme.AddToScheme` registers types; serializers decode/encode; `client-go/kubernetes/scheme` for built-ins; custom types need their group's `AddToScheme`.
- **Meta helpers**: `metav1.NewControllerRef`, `controllerutil.SetControllerReference`, `metav1.IsControlledBy`, `labels.Set`, `fields.OneTermEqualSelector("spec.nodeName", n)`.
- **DeepCopy**: generated `DeepCopy()` methods for API types (never share and mutate).

## 5. client-go

### Building clients

```go
func newClient() (kubernetes.Interface, *rest.Config, error) {
	// precedence: in-cluster → kubeconfig (KUBECONFIG, ~/.kube/config)
	cfg, err := rest.InClusterConfig()
	if err != nil {
		loading := clientcmd.NewDefaultClientConfigLoadingRules()
		cfg, err = clientcmd.NewNonInteractiveDeferredLoadingClientConfig(loading, &clientcmd.ConfigOverrides{}).ClientConfig()
		if err != nil { return nil, nil, fmt.Errorf("load kubeconfig: %w", err) }
	}
	cfg.QPS, cfg.Burst = 50, 100            // default 5/10 is far too low for controllers; see 5.5 about APF
	cfg.UserAgent = "nodectl/0.1"
	cs, err := kubernetes.NewForConfig(cfg)
	return cs, cfg, err
}
```

Clients: **typed clientset** (`kubernetes.Interface`: `CoreV1()`, `AppsV1()`, `BatchV1()`, `RbacV1()`...), **dynamic client** (`dynamic.NewForConfig`; `Resource(gvr).Namespace(ns).List(...)` returns unstructured; for CRDs without types), **discovery client** (API groups/resources), **REST client** (low-level), **metadata client** (`PartialObjectMetadata`, cheap), **scale client**, generated clientsets for your CRDs (`client-gen`) or controller-runtime's `client.Client` (a unified typed/unstructured client with cache; 5.31).

### CRUD, patch, apply

```go
ctx := context.Background()
nodes, err := cs.CoreV1().Nodes().List(ctx, metav1.ListOptions{LabelSelector: "nvidia.com/gpu.present=true", Limit: 500})
for nodes.Continue != "" { /* paginate with opts.Continue */ }

pod, err := cs.CoreV1().Pods("training").Get(ctx, "trainer-0", metav1.GetOptions{})
pod.Labels["checked"] = "true"
_, err = cs.CoreV1().Pods("training").Update(ctx, pod, metav1.UpdateOptions{})            // full update; conflict if stale

// Conflict-safe read-modify-write
err = retry.RetryOnConflict(retry.DefaultRetry, func() error {
	n, err := cs.CoreV1().Nodes().Get(ctx, name, metav1.GetOptions{})
	if err != nil { return err }
	n.Annotations["platform.example.com/cordon-reason"] = "xid79"
	_, err = cs.CoreV1().Nodes().Update(ctx, n, metav1.UpdateOptions{})
	return err
})

// JSON merge patch / strategic merge patch (no read needed)
_, err = cs.CoreV1().Nodes().Patch(ctx, name, types.MergePatchType,
	[]byte(`{"metadata":{"labels":{"platform.example.com/quarantine":"true"}}}`), metav1.PatchOptions{})

// Server-side apply with typed apply configurations (field ownership; idempotent)
import applycorev1 "k8s.io/client-go/applyconfigurations/core/v1"
nodeAC := applycorev1.Node(name).WithLabels(map[string]string{"platform.example.com/quarantine": "true"})
_, err = cs.CoreV1().Nodes().Apply(ctx, nodeAC, metav1.ApplyOptions{FieldManager: "nodectl", Force: false})

// Eviction (respects PDBs) — preferred over Delete for draining
ev := &policyv1.Eviction{ObjectMeta: metav1.ObjectMeta{Name: pod.Name, Namespace: pod.Namespace}}
err = cs.CoreV1().Pods(pod.Namespace).EvictV1(ctx, ev)   // returns 429 if a PDB disallows; retry later
```

Prefer **patch/apply** over get-modify-update to avoid conflicts; use `Update` only with `resourceVersion` awareness and retry; use `DeleteOptions{PropagationPolicy: &fg, GracePeriodSeconds: &g}`; `Create` returns `AlreadyExists`; use `DryRun: []string{metav1.DryRunAll}` for validation.

### Watching

```go
w, err := cs.CoreV1().Nodes().Watch(ctx, metav1.ListOptions{ResourceVersion: list.ResourceVersion, AllowWatchBookmarks: true})
defer w.Stop()
for ev := range w.ResultChan() {
	switch ev.Type {
	case watch.Added, watch.Modified: n := ev.Object.(*corev1.Node); _ = n
	case watch.Deleted:
	case watch.Error:                                   // 410 Gone → relist
	}
}
```

Raw watches need reconnection, bookmark/RV handling, backoff: use `watchtools.NewRetryWatcher` or (almost always) **informers**.

### Informers, listers and work queues

```go
factory := informers.NewSharedInformerFactoryWithOptions(cs, 10*time.Hour,
	informers.WithTweakListOptions(func(o *metav1.ListOptions) { o.LabelSelector = "nvidia.com/gpu.present=true" }))
nodeInformer := factory.Core().V1().Nodes()
nodeLister := nodeInformer.Lister()                                   // cache-backed reads: Get(name), List(selector)

queue := workqueue.NewTypedRateLimitingQueue(workqueue.DefaultTypedControllerRateLimiter[string]())
defer queue.ShutDown()

_, _ = nodeInformer.Informer().AddEventHandler(cache.ResourceEventHandlerFuncs{
	AddFunc:    func(obj interface{}) { enqueue(queue, obj) },
	UpdateFunc: func(_, obj interface{}) { enqueue(queue, obj) },
	DeleteFunc: func(obj interface{}) { enqueue(queue, obj) },        // obj may be cache.DeletedFinalStateUnknown
})

func enqueue(q workqueue.TypedRateLimitingInterface[string], obj interface{}) {
	key, err := cache.DeletionHandlingMetaNamespaceKeyFunc(obj)
	if err == nil { q.Add(key) }
}

ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
defer stop()
factory.Start(ctx.Done())
if !cache.WaitForCacheSync(ctx.Done(), nodeInformer.Informer().HasSynced) { return errors.New("cache sync failed") }

for i := 0; i < 2; i++ {                                              // workers
	go wait.UntilWithContext(ctx, func(ctx context.Context) {
		for processNext(ctx, queue, nodeLister) {}
	}, time.Second)
}
<-ctx.Done()

func processNext(ctx context.Context, q workqueue.TypedRateLimitingInterface[string], l listersv1.NodeLister) bool {
	key, shutdown := q.Get()
	if shutdown { return false }
	defer q.Done(key)
	if err := reconcile(ctx, key, l); err != nil {
		q.AddRateLimited(key)                                          // retry with backoff
		return true
	}
	q.Forget(key)                                                      // reset backoff
	return true
}
```

Key rules: wait for cache sync before processing; read from the lister, write via the client; **never mutate cached objects** (DeepCopy); enqueue keys not objects; handle `DeletedFinalStateUnknown` tombstones; resync period = safety net; one worker handles a given key at a time; use `Forget` on success; shut down cleanly on SIGTERM. For multiple resource types create one factory; add indexers (`cache.Indexers{"byNode": func(...)}`) for efficient lookups (pods by node).

### Leader election

```go
lock := &resourcelock.LeaseLock{
	LeaseMeta:  metav1.ObjectMeta{Name: "nodectl-leader", Namespace: "platform"},
	Client:     cs.CoordinationV1(),
	LockConfig: resourcelock.ResourceLockConfig{Identity: hostname},
}
leaderelection.RunOrDie(ctx, leaderelection.LeaderElectionConfig{
	Lock: lock, ReleaseOnCancel: true,
	LeaseDuration: 15 * time.Second, RenewDeadline: 10 * time.Second, RetryPeriod: 2 * time.Second,
	Callbacks: leaderelection.LeaderCallbacks{
		OnStartedLeading: func(ctx context.Context) { run(ctx) },
		OnStoppedLeading: func() { klog.Info("lost leadership; exiting"); os.Exit(1) },     // restart to rejoin cleanly
	},
})
```

### Dynamic client for CRDs

```go
gvr := schema.GroupVersionResource{Group: "kueue.x-k8s.io", Version: "v1beta1", Resource: "clusterqueues"}
dc, _ := dynamic.NewForConfig(cfg)
list, err := dc.Resource(gvr).List(ctx, metav1.ListOptions{})
for _, item := range list.Items {
	nominal, found, _ := unstructured.NestedSlice(item.Object, "spec", "resourceGroups")
	_, _ = nominal, found
}
```

### Logging, metrics, flags

`klog` (Kubernetes' logging; `-v` levels, `klog.InfoS("msg", "key", val)` structured) or `log/slog` (std lib); controller-runtime uses `logr` (`ctrl.Log.WithName`); metrics via `prometheus/client_golang` (counters, gauges, histograms with bounded labels); flags via `flag`/`pflag`/cobra; health endpoints with `net/http`; graceful shutdown with `signal.NotifyContext`.

## 6. A small CLI: cordon nodes on XID events (walkthrough)

```go
// cmd/nodectl/main.go (condensed)
package main

import (
	"context"
	"fmt"
	"os"

	"github.com/spf13/cobra"
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/types"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/tools/clientcmd"
)

func main() {
	var kubeconfig, selector string
	var dryRun bool
	root := &cobra.Command{Use: "nodectl", SilenceUsage: true}
	root.PersistentFlags().StringVar(&kubeconfig, "kubeconfig", os.Getenv("KUBECONFIG"), "path to kubeconfig")

	cordon := &cobra.Command{
		Use:   "cordon-unhealthy",
		Short: "Cordon GPU nodes whose NodeCondition GPUHealthy is False",
		RunE: func(cmd *cobra.Command, _ []string) error {
			cs, err := client(kubeconfig)
			if err != nil { return err }
			ctx := cmd.Context()
			nodes, err := cs.CoreV1().Nodes().List(ctx, metav1.ListOptions{LabelSelector: selector})
			if err != nil { return err }
			var failed int
			for i := range nodes.Items {
				n := &nodes.Items[i]
				if !unhealthy(n) || n.Spec.Unschedulable { continue }
				fmt.Printf("cordon %s\n", n.Name)
				if dryRun { continue }
				patch := []byte(`{"spec":{"unschedulable":true},"metadata":{"annotations":{"platform.example.com/reason":"GPUHealthy=False"}}}`)
				if _, err := cs.CoreV1().Nodes().Patch(ctx, n.Name, types.MergePatchType, patch, metav1.PatchOptions{}); err != nil {
					fmt.Fprintf(os.Stderr, "error: %s: %v\n", n.Name, err); failed++
				}
			}
			if failed > 0 { return fmt.Errorf("%d nodes failed", failed) }
			return nil
		},
	}
	cordon.Flags().StringVar(&selector, "selector", "nvidia.com/gpu.present=true", "node label selector")
	cordon.Flags().BoolVar(&dryRun, "dry-run", true, "only print actions")   // safe by default (4.8 principles)
	root.AddCommand(cordon)
	if err := root.ExecuteContext(context.Background()); err != nil { os.Exit(1) }
}

func unhealthy(n *corev1.Node) bool {
	for _, c := range n.Status.Conditions {
		if c.Type == "GPUHealthy" { return c.Status == corev1.ConditionFalse }
	}
	return false
}

func client(path string) (kubernetes.Interface, error) {
	cfg, err := clientcmd.BuildConfigFromFlags("", path)
	if err != nil { return nil, err }
	return kubernetes.NewForConfig(cfg)
}
```

This listing, the informer program of section 5 (with imports `k8s.io/client-go/informers`, `listers/core/v1`, `tools/cache`, `util/workqueue`, `apimachinery/pkg/util/wait`, `k8s.io/klog/v2`) and the `health` package tests of section 7 were compiled and the unit tests run with Go 1.23.2 and client-go/apimachinery/api v0.31.0 (`go vet` clean, `go test` passing); the live-cluster behaviour was not exercised. It follows CLI principles from 3.8: dry-run default, explicit exit codes, errors aggregated, selectors, idempotent patch.

## 7. Testing

```go
// internal/health/classify_test.go
func TestClassify(t *testing.T) {
	tests := []struct {
		name string
		code int
		want Severity
	}{
		{"fallen off bus", 79, SeverityCritical},
		{"nvlink", 74, SeverityCritical},
		{"app error", 13, SeverityWarn},
		{"unknown", 999, SeverityInfo},
	}
	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			if got := (XIDEvent{Code: tc.code}).Classify(); got != tc.want {
				t.Fatalf("Classify(%d) = %v, want %v", tc.code, got, tc.want)
			}
		})
	}
}

// client-go fake clientset
func TestCordon(t *testing.T) {
	cs := fake.NewSimpleClientset(&corev1.Node{ObjectMeta: metav1.ObjectMeta{Name: "n1"}})
	if err := cordon(context.Background(), cs, "n1"); err != nil { t.Fatal(err) }
	n, _ := cs.CoreV1().Nodes().Get(context.Background(), "n1", metav1.GetOptions{})
	if !n.Spec.Unschedulable { t.Fatal("node not cordoned") }
	// fake clients support reactors to inject errors: cs.PrependReactor("patch", "nodes", ...)
}
```

- **Table-driven tests** with `t.Run`, `t.Parallel()`, `t.Helper()`, `testing.TB`, `cmp.Diff` (go-cmp), `testify` (`require`/`assert`) optionally; `go test -race -cover ./...`; fuzzing (`func FuzzParse(f *testing.F)`); benchmarks (`func BenchmarkX(b *testing.B)`).
- **Fakes**: `k8s.io/client-go/kubernetes/fake` (object tracker; no server semantics like admission/defaulting/field validation/resourceVersion conflicts), `dynamic/fake`, controller-runtime `fake.NewClientBuilder()`; **envtest** (`sigs.k8s.io/controller-runtime/pkg/envtest`) runs a real kube-apiserver and etcd binaries for integration tests (CRDs, webhooks, status subresources); e2e on kind (kuttl, chainsaw, Ginkgo).
- Design for testability: pure domain logic separate from I/O; small interfaces; inject clients and clocks (`k8s.io/utils/clock`, `clock/testing`).

## 8. Packaging

Multi-stage Dockerfile for a static binary:

```dockerfile
FROM golang:1.23 AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN --mount=type=cache,target=/go/pkg/mod go mod download
COPY . .
RUN --mount=type=cache,target=/root/.cache/go-build CGO_ENABLED=0 go build -trimpath -ldflags="-s -w -X main.version=${VERSION}" -o /out/nodectl ./cmd/nodectl

FROM gcr.io/distroless/static:nonroot
COPY --from=build /out/nodectl /nodectl
USER 65532:65532
ENTRYPOINT ["/nodectl"]
```

`ko` builds images from Go without Dockerfiles (`ko build ./cmd/nodectl`), GoReleaser creates releases and SBOMs/signatures; embed version info with `-ldflags -X`; run as non-root; set resource requests; expose `/healthz` and `/metrics`.

## 9. Idioms and pitfalls checklist

| Idiom | Pitfall |
|---|---|
| Wrap errors with `%w` and check with `errors.Is/As` | Comparing error strings; swallowing errors |
| Pass `context.Context` first and honour cancellation | Using `context.Background()` deep in libraries; leaking goroutines |
| Use `DeepCopy()` before mutating objects from informers/listers | Mutating cached objects (corrupts the cache) |
| Use patch/SSA, `RetryOnConflict` | Get-modify-update without retry; overwriting others' fields |
| Bound concurrency (`errgroup.SetLimit`, semaphore) | Spawning thousands of goroutines hitting the API (client-side throttling) |
| Rate-limited work queue per key | Tight retry loops; processing event handlers synchronously in the handler |
| Set client `QPS/Burst` explicitly | Default QPS 5 throttles controllers; unlimited QPS floods API (APF) |
| Prefer informers over polling `List` | Listing the whole cluster repeatedly |
| `defer cancel()` and `defer Close()` | Forgetting; defers in loops (run at function end) |
| Table-driven tests, fakes | Testing against a live cluster only |
| Keep API-type conversions at boundaries | Passing `unstructured` everywhere |
| Run `go vet`, `staticcheck`, `-race` in CI | Data races in shared maps; copying mutexes |
| Small interfaces at the consumer | Large "god" interfaces and mocking everything |
| `internal/` for private code, minimal public API | Exporting everything; import cycles |
| Match client-go and Kubernetes versions | Mixed versions causing type or API mismatches |
| `ptr.To` for optional fields; check nil before dereferencing | Nil pointer panics on optional API fields |

## 10. Lab (untested)

1. **Toolchain**: install Go, create the module, add client-go dependencies matching your kind cluster version, build and run a program that lists nodes with GPU labels (use fake labels on kind nodes).
2. **Language drills**: implement `Classify`, a generic `Filter/Map/GroupBy`, an `errors.Is/As` example with a custom error type, and a bounded-concurrency prober using `errgroup`; run `go vet` and `go test -race`.
3. **Informer program**: write the node informer + work queue example; log reconciles; kill/restart; observe resync and cache behaviour; add an indexer for pods by node and print pod counts per node.
4. **Patch vs update**: write conflicting writers (two goroutines updating annotations) with `Update` (observe conflicts) vs `Patch`/SSA (no conflicts, field ownership via `--show-managed-fields`).
5. **Watch and relist**: implement a raw watch, force a 410 by delaying; add `RetryWatcher`; compare with an informer.
6. **Drain tool**: implement `cordon` + eviction loop respecting PDBs with retries/backoff; test against kind with a PDB that blocks; add `--timeout` and context cancellation.
7. **Dynamic client**: write a tool that prints Kueue ClusterQueue usage using unstructured access; then generate typed structs by importing Kueue's API module and compare.
8. **CLI**: build the `nodectl cordon-unhealthy` command with cobra; add tests with the fake clientset; add `--output json`; cross-compile and package in a distroless image; run it as a Job with a ServiceAccount and RBAC (least privilege: nodes `get/list/patch`).
9. **Leader election**: run two replicas of an informer program with a Lease; kill the leader and measure failover.
10. **Read real code**: clone `kubernetes/kubernetes` or `kubernetes/sample-controller`; trace `pkg/controller/replicaset`'s `syncReplicaSet`; map to the reconcile pattern (5.6); find where informers are wired.
11. **Envtest**: write one integration test using envtest that installs a CRD and verifies status subresource behaviour.
12. **Clean up**.

Mark tested only after execution.

## 11. Interview angles

- "Why is Go used for Kubernetes? What Go features matter (interfaces, goroutines, static binaries)?" 
- "How do informers work and why must you not mutate objects from a lister?" 
- "How do you avoid write conflicts when updating Kubernetes objects from code?" 
- "How do you structure a controller's work queue and retries?" 
- "Explain contexts and goroutine leaks. How do you test for data races?" 
- "How do you test code that talks to the Kubernetes API?" (fake clientset, envtest, kind e2e.)
- "How would you write a tool that safely drains nodes at scale?" 

## 12. Checkpoint questions (35)

1. Go module file? **A:** `go.mod`.
2. Export rule? **A:** Capitalised identifiers.
3. Interface satisfaction? **A:** Implicit.
4. Error wrapping verb? **A:** `%w`.
5. Check wrapped error? **A:** `errors.Is`/`errors.As`.
6. `defer` runs when? **A:** At function return.
7. Slice vs array? **A:** Slice is a view over an array; dynamic.
8. Map concurrency? **A:** Not safe for concurrent writes.
9. Loop var semantics 1.22? **A:** Per-iteration variables.
10. Generics syntax? **A:** `func F[T any](...)`.
11. Goroutine exit requirement? **A:** Clear termination path.
12. Who closes a channel? **A:** The sender.
13. `context` first param? **A:** Convention.
14. errgroup gives? **A:** Wait + first error + limit.
15. Race detector flag? **A:** `-race`.
16. `resource.Quantity` use? **A:** CPU/memory/GPU amounts.
17. Optional API fields type? **A:** Pointers.
18. `ptr.To` does? **A:** Returns pointer to value.
19. Unstructured is? **A:** Map-based generic object.
20. Scheme maps? **A:** Go types ↔ GVK.
21. Typed clientset interface? **A:** `kubernetes.Interface`.
22. Dynamic client for? **A:** CRDs without types.
23. Conflict retry helper? **A:** `retry.RetryOnConflict`.
24. SSA in client-go? **A:** `Apply` with apply configurations + FieldManager.
25. Eviction vs delete? **A:** Eviction respects PDBs.
26. Informer provides? **A:** Cached list/watch with handlers.
27. Lister reads from? **A:** Local cache.
28. Mutate cached objects? **A:** Never; DeepCopy.
29. Work queue enqueues? **A:** Keys.
30. `Forget` does? **A:** Reset rate limiter for key.
31. Tombstone type? **A:** `DeletedFinalStateUnknown`.
32. Leader election lock? **A:** Lease.
33. Fake client limits? **A:** No real API server semantics.
34. envtest provides? **A:** Real kube-apiserver + etcd for tests.
35. Static binary flag? **A:** `CGO_ENABLED=0`.

## 13. Sources and review notes

**Written in original words.** Principal sources:

- Michael Hausenblas and Stefan Schimanski, *Programming Kubernetes* (client-go, informers, work queues, API machinery, custom resources).
- Network programmability material in the study corpus for Go-based tooling context where cross-referenced (NPA chapter 7).
- Go documentation (effective Go, language spec, standard library), client-go, apimachinery and controller-runtime documentation and examples (`kubernetes/sample-controller`).
- Examples are the author's constructions; the CLI, informer program and `health` tests were compiled/tested as noted in section 6.

**Flagged for verification before publishing:** client-go API names and signatures for the version you pin (typed work queues, `WithTweakListOptions`, apply configurations), Go version-specific features (loop variable semantics, `slices`/`maps` helpers, range-over-func), XID code classifications (use NVIDIA's catalogue), and every Go listing not listed as compiled in section 6; the live-cluster labs are **untested**.
