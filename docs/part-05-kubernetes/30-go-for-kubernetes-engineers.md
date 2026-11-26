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

Suppose a controller pod crashes, and its logs end with a Go stack trace. If you can read Go, that trace leads you straight into the source code, and you can see which line failed and why. If you cannot read Go, the trace is noise. Kubernetes and most of its ecosystem are written in Go. That includes containerd, etcd, Prometheus, Terraform providers, the NVIDIA GPU Operator, device plugins, CSI drivers, Kueue, Argo and Cilium. So a large share of the software you will operate on a GPU platform is Go code, whether or not you ever write any yourself.

Platform engineers who read Go can debug operator behaviour from source. When the documentation is silent, the source code is the final word on what a component does. They can also patch or extend components when a fix has not shipped yet. And they can write small controllers and CLI tools of their own, such as a node-health remediator, a quota reporter or an admission webhook. Those tools are often where an AI platform team gets the most value, because they fit the platform exactly.

You do not need to be a Go expert to get value from this chapter. You do need fluency with the language subset and the client libraries that Kubernetes tooling uses. This chapter teaches that subset with Kubernetes examples, so each new Go idea arrives with a reason you can see. It also sets up 5.31 (operators with controller-runtime), 5.32 (a GPU node health operator) and 5.33 (reading the GPU and Network Operator source).

## Prerequisites and outcomes

You need programming experience before you start. Part 3 covers Python, and that is enough to follow the ideas here, because Go and Python share most of the same concepts. You should also have read 5.3 to 5.6, which cover the API server, the object model and controllers. Those chapters explain what the Go code is trying to do, so the code is easier to read once you know the goal.

The list below is a self-check. Each line asks a question that you should be able to answer when you finish. Read them now to see where you are starting, and read them again at the end to see how far you have come.

- Can you set up a Go module and use the toolchain (`go build/test/vet/fmt/mod`, `gopls`, `golangci-lint`)? Can you find your way around a large Go repository?
- Can you use Go's core features correctly? That covers types, structs, methods, interfaces that a type satisfies without declaring it, embedding, pointers versus values, slices and maps, and errors with wrapping, `errors.Is/As`. It also covers `defer`, `panic/recover` and generics.
- Can you write concurrent programs with goroutines, channels, `sync` primitives and `context`? Can you avoid leaks and races, and can you use the race detector to check your work?
- Can you handle JSON, YAML and Kubernetes types, including struct tags, `metav1.ObjectMeta`, `runtime.Object` and `unstructured`?
- Can you use client-go to build a client from a kubeconfig or from inside a cluster? Can you list, get, create, patch and delete objects? Can you watch them with informers, listers, work queues, leader election, the dynamic client and discovery? Do you know the best practices for rate limits and retries?
- Can you write table-driven tests and fake clients, use `envtest`, structure a CLI with cobra, and produce small static container images?

## 1. Toolchain and project layout

Start with the toolchain and a module before you write any Go code. Think of a Go module as the folder that holds one project's name, its dependencies and its version rules. The commands below create a project called `nodectl`, add the Kubernetes libraries, and run the checks you will repeat on every change. You will type these commands often, so it helps to know what each one is for.

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

The client-go version has to follow your Kubernetes minor version, so client-go v0.N pairs with Kubernetes 1.N. The first version line in the block is a reminder to check your Go version against the `go` line in `go.mod`. The last build line produces a static binary for scratch or distroless images. A static binary carries its own libraries, so it can run in a nearly empty container.

The standard repository shape, the one kubebuilder projects use, looks like this. Read it as a map of where things go, so that you know where to put a new file before you create it.

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

Keep `cmd/nodectl/main.go` thin, so it only parses flags and wires dependencies. Wiring means connecting the parts together, such as passing the client into the code that needs it. Put the domain logic in `internal/health/`, where it stays pure and easy to test. Pure here means the functions take inputs and return outputs, without reaching out to the network or the clock. A pure function is the easiest kind to test.

Modules bring a few rules of their own. Semantic import versioning uses a `/v2` suffix, so a new major version of a library gets a new import path. Use `replace` for a local fork, `go.work` for multi-module work, and `go mod vendor` if you choose vendoring, which is optional. Vendoring copies your dependencies into the project, so a build does not need the network.

The Kubernetes libraries are tightly coupled. client-go, apimachinery, api and controller-runtime must be compatible with one another, so check the compatibility matrix before you upgrade any of them. Upgrading one library while the others stay behind is a common way to get confusing compile errors. `go.sum` verifies the hashes of your dependencies, so you can tell that the code you downloaded is the code you tested.

For private modules, configure `GOPROXY` and `GOFLAGS` together with `GOPRIVATE`. `GOPROXY` says where modules are downloaded from, and `GOPRIVATE` tells Go which modules should skip the public proxy.

## 2. Language essentials (the subset Kubernetes code uses)

You do not need all of Go to read Kubernetes code. You need a small set of features that appear again and again. This section covers that set, and it introduces each feature through a small example from a GPU health tool.

### Types, structs, methods

Most Kubernetes controllers rely on the same handful of language features. The example below models a GPU error event as a struct and maps its error code to a severity. A struct is a named bundle of fields, a bit like a form with labelled boxes. Here the form records which node, which GPU, which code and when.

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

Read the example from the top. The first block declares a struct named `XIDEvent`. Its fields are the node name, the GPU index, the error code and the time it was seen. The `Severity` type is an integer with three named values, and `iota` is a counter that gives each name the next number, starting from zero. The `String` method turns a severity into a readable word, so that printing it shows `critical` instead of a bare number. The `Classify` method at the end looks up the code in a `switch` and returns a severity. Notice that the mapping lives in one place, which makes it easy to review.

Go decides what other packages can see from the first letter of each name. An exported identifier starts with a capital letter, so `Classify` is visible to other packages and `classify` would not be. Packages are the unit of encapsulation, and Go has no classes and no inheritance. Methods take a receiver, which can be a value or a pointer. Use a pointer receiver when the method changes the struct, when the struct is large, or for consistency. Do not mix the two on one type, because mixing them makes the rules for when a value satisfies an interface harder to remember.

Zero values are useful. `var s []int` is a nil slice that you can append to, and `var mu sync.Mutex` is ready to use without setup. Go gives every variable a default value, so you rarely need a constructor just to get a usable object.

Struct tags control marshalling. Marshalling means turning a struct into bytes, such as JSON, and back again. Kubernetes types use `json` tags, and some also carry `protobuf` tags. YAML is handled by `sigs.k8s.io/yaml`, which converts YAML to JSON and then into the struct. That means only `json` tags matter, as in `json:"name,omitempty"`. The `omitempty` part tells the encoder to leave the field out when it holds its zero value.

Composition works through embedding. A struct such as `type Node struct { metav1.TypeMeta; metav1.ObjectMeta; Spec NodeSpec; Status NodeStatus }` picks up the fields and methods of its embedded types. That is how every Kubernetes object gets `GetName()` and `GetLabels()`. Embedding is not inheritance. The outer struct does not become the inner type. It simply gets the inner type's fields and methods as a convenience.

### Interfaces (implicit) and polymorphism

An interface is a list of method names. Any type that has all of those methods satisfies the interface. The next example defines one for node remediation, which means fixing a node that has gone bad.

```go
type Remediator interface {
	Cordon(ctx context.Context, node string) error
	Drain(ctx context.Context, node string) error
}

type kubeRemediator struct{ cs kubernetes.Interface }       // *kubeRemediator satisfies Remediator implicitly

var _ Remediator = (*kubeRemediator)(nil)                   // compile-time assertion
```

Go satisfies interfaces implicitly, so a type never declares that it implements one. This is different from Java or C#, where a class names the interfaces it implements. In Go, the compiler checks the method set when a value is used where the interface is expected. The line `var _ Remediator = (*kubeRemediator)(nil)` is a compile-time check. It costs nothing at run time, and it fails the build if the type ever stops matching the interface.

The common idiom is to accept interfaces and return structs. Define small interfaces at the consumer, which means the code that uses the interface defines it, so it asks for only the methods it needs. For example, `kubernetes.Interface` lets you pass `fake.NewSimpleClientset()` in tests. A fake is a stand-in client that keeps its data in memory, so a test does not need a live cluster.

`any` is an alias for `interface{}`, and it holds a value of any type. You recover the concrete type with a type assertion, `v, ok := x.(T)`, or with a type switch, `switch t := x.(type)`. The `ok` in a type assertion tells you whether the guess was right, so you can handle the wrong case without a crash. Kubernetes uses `runtime.Object` as the common supertype of API objects. It is an interface with `GetObjectKind()` and `DeepCopyObject()`, so any API object can be handled through it. controller-runtime also has `client.Object`, which is a similar interface for the controller framework.

### Errors

Errors are ordinary values in Go. There is no exception that jumps over your code. A function that can fail returns an error as its last result, and the caller checks it. The example below shows the usual pattern for cordoning a node, which is marking it so that no new pods land on it.

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

Read the example as a story of one function. It asks the API server for the node. If the node does not exist, it wraps a named error with the node's name, so a caller can recognize the case later. If the request fails for any other reason, it wraps the error with a short description of the step. If the node is already cordoned, it returns nil, which in Go means "no error." Otherwise it sends a patch that sets `unschedulable` to true. The last two lines show the caller's side. The caller checks the wrapped error with `errors.Is` or pulls out the typed error with `errors.As`.

Errors are ordinary values, returned as the last result of a function. Check them right away with `if err != nil`. Wrap each one with context using `fmt.Errorf("...: %w", err)`, so the caller can still reach the original cause. The `%w` verb is the piece that makes wrapping work. A plain `%v` would print the message but lose the link to the original error. Compare with `errors.Is/As`, and pull out a typed error with `errors.As`. Kubernetes API errors come with helpers such as `apierrors.IsNotFound/IsConflict/IsAlreadyExists/IsForbidden/IsTimeout/IsServerTimeout`. Never ignore an error silently, because the `errcheck` linter flags it, and a silent failure is hard to find later.

Reserve `panic` for programmer errors and initialisation. A panic stops the program unless something recovers it, so it is for bugs that should never happen, not for expected failures such as a missing node. Use `defer` for cleanup, as in `defer resp.Body.Close()`, `defer cancel()` and `defer mu.Unlock()`. A `defer` runs when the function returns, so cleanup sits next to the code that needs it. `recover` is rare and mostly appears in HTTP servers. When several errors belong together, combine them with `errors.Join`, or with the aggregate helper `utilerrors.NewAggregate` from apimachinery.

### Slices, maps, strings, generics

Most people first trip over a map. Writing to a nil map panics, so a program that writes into a map nobody created stops on the first write. A nil map is one that was declared but never made, and it can be read but not written. Build the collections your code needs with `make` and the standard `slices` and `maps` packages, as the example below shows. The example collects the names of nodes that advertise a GPU, counts pods per node, and includes a small generic filter.

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

Walk through the first part slowly, because it shows a common pattern. The code starts with an empty slice that has room for as many names as there are nodes. The loop checks each node's allocatable resources for a GPU count that is not zero. When it finds one, it appends the node's name. The `ok` check in the `if` tells you whether the key exists in the map, so a missing key does not look like a zero count. Then the names are sorted, and a binary search finds one name quickly. The second part counts pods per node with a map. A map's iteration order is random, which is why the example sorts the keys before it prints them. The `Filter` function at the end uses a type parameter, `T`, so one function works for any element type.

A few gotchas are worth knowing. Slices share backing arrays, so `append` may or may not reallocate. That means two slices can quietly share memory, and a change through one can show up in the other. Since Go 1.22, each loop iteration has its own loop variable, which changed how closures capture it. Before that change, a closure created inside a loop often saw only the last value. Iterating over a string yields runes, which are Unicode code points, not bytes. Know the difference between `copy` and plain assignment, because assignment copies the slice header and not the elements. `for range n` arrived in Go 1.22, and range-over-func iterators arrived in Go 1.23. For building strings, use `strings.Builder` or `bytes.Buffer`, which avoid making a new string for every piece you add. Use `fmt.Sprintf` with verbs such as `%v`, `%+v`, `%#v`, `%T`, `%w` and `%q`. Each verb controls how a value is printed, and `%+v` in particular shows field names, which helps when you are debugging a struct.

### Pointers and values

Go passes everything by value, which means it copies. Pointers are how you share. A pointer holds the address of a value, so changing through the pointer changes the original. Kubernetes API types use pointers for optional fields, such as `*int32 Replicas`, so a program can tell an unset field from a zero value. Zero is a real number, so if the field were a plain integer, you could not tell "set to zero" from "not set at all." The `k8s.io/utils/ptr` helpers make this easier. `ptr.To(int32(3))` builds a pointer to the value 3, and `ptr.Deref(p, default)` reads one safely, returning the default when the pointer is nil.

Objects returned from listers are shared cache objects, so never mutate them. A lister is a read-only view of a local cache, and other code may be reading the same object at the same moment. Call `DeepCopy()` before you change anything. A deep copy gives you a fresh object that you can change without affecting the cache. Struct comparison with `==` works only when every field is comparable, so use `reflect.DeepEqual` or apimachinery's `equality.Semantic.DeepEqual` instead. The Semantic version handles `resource.Quantity` and `metav1.Time` correctly, because those types can hold the same value in more than one form.

### Packages, visibility, init, build tags

One directory holds one package, and `internal/` restricts which packages can import it. Think of `internal/` as a private drawer. Code outside your module cannot open it. Avoid side effects in `init()`, because it runs whenever the package is imported, and that makes the program's behaviour harder to predict. Kubernetes API groups register their types through explicit `AddToScheme` functions, so the registration happens where you can see it. Build constraints such as `//go:build linux` decide which files compile for which platform. `go:embed` handles static assets, such as a template file that you want inside the binary. `go:generate` runs code generators such as deepcopy-gen, controller-gen and mockgen, so generated code is produced from a single command.

When you read the controller code in the next sections, keep two rules in mind. Wrap errors with `%w`, and call `DeepCopy()` before you mutate anything that came from a lister. Most of the bugs in Kubernetes controllers come from breaking one of those two rules.

## 3. Concurrency

Go makes concurrency cheap enough to use everywhere, and that is both its strength and its trap. A goroutine is a function that runs alongside other code. You start one with the word `go`. The examples in this section show how to run work in parallel without losing control of it.

### Goroutines, channels, sync

Suppose you must probe every node in a large cluster. Probing one node takes a moment, so doing them one at a time would be slow. The example below runs the probes concurrently, limits how many run at once, and stops the whole run when a context timeout expires.

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

Read the example in the order its work happens. The function sets a 30-second deadline with a context, and it makes a channel to collect results. A channel is a typed pipe that one goroutine can send into and another can read from. The `sem` channel acts as a counting gate. Each probe must put a value in before it starts and take it out when it ends, so no more than 16 probes run at once. Each probe is a goroutine. It runs its check, then sends its result, unless the context has already ended. The `WaitGroup` counts running goroutines, and a separate goroutine closes the results channel after they all finish. The loop at the bottom reads results until the channel closes, and it fills in a map. Notice the `select` in the probe. It lets the goroutine give up cleanly if the deadline passes while it is trying to send.

Goroutines are cheap, but every goroutine needs a clear way to exit, such as a context cancel or a channel close. A goroutine that never exits is a leak, and leaks add up in a long-running controller. The Go proverb says, "don't communicate by sharing memory; share memory by communicating." It means that passing values through channels is often clearer than locking shared data. When the state is simple, a mutex is the better tool, using `sync.Mutex/RWMutex`. A mutex is a lock that only one goroutine can hold at a time. An RWMutex allows many readers or one writer.

The rest of the `sync` family covers the other cases. `sync.WaitGroup` waits for a set of goroutines, `sync.Once` runs something exactly once, and `sync/atomic` handles single values. `sync.Map` is rare. `errgroup.Group` from `golang.org/x/sync/errgroup` combines waiting, the first error, context cancellation and `SetLimit`. `SetLimit` is the same idea as the semaphore in the example, built into the group.

Channels come in two forms. An unbuffered channel makes the sender and receiver meet, so each send waits for a receive. A buffered channel holds values until someone takes them. Only the sender should close a channel, because a send on a closed channel panics. Receiving from a closed channel yields zero values, so a loop that reads from one needs to know when the channel closed.

Use `select` to wait on several channel operations at once. A `default` case makes the wait non-blocking, so the code moves on if nothing is ready. A timeout or `ctx.Done()` case stops the wait when time runs out. Avoid `time.After` inside loops, because it leaked timers before Go 1.23. Use `time.NewTimer` instead, and stop the timer when you no longer need it.

Two failures are common. A goroutine that waits on a send or receive with no reader is leaked. A data race is undefined behaviour, which means the program may do anything, so run your tests with `-race`. A deadlock shows up as `all goroutines are asleep`, which means every goroutine is waiting and none can make progress. Kubernetes code uses `wait.Until`, `wait.PollUntilContextTimeout` (from apimachinery/util/wait) and rate-limited work queues in controllers, rather than raw goroutines. Those helpers already handle stopping and retrying. Check that every goroutine you start has a way to stop.

### context.Context

A context carries cancellation, deadlines and request-scoped values across API boundaries. Think of it as a note that travels with a request, saying "give up after this time" or "the user has left, stop working." By convention it is the first parameter, written `ctx context.Context`. Derive a child with `WithCancel/WithTimeout/WithDeadline/WithValue`, and always `defer cancel()` after you derive one. The `cancel` function releases resources even when the work finishes early, so skipping it leaks memory.

Do not store a context in a struct for long-lived use. A context belongs to one request or one operation, and a struct that outlives that request would keep an expired context. Pass `ctx` to every client-go call, as in `Get(ctx, name, opts)`, and check `ctx.Err()` inside loops. That way, a cancelled run stops at the next check instead of finishing a long job for nobody. controller-runtime passes a context into each reconcile, so your reconcile code can honour cancellation without extra setup.

## 4. JSON, YAML and Kubernetes types

Suppose you need to build a test pod in code and print it as YAML. Kubernetes types make that a short job, and the example below does exactly that. It creates a pod with one GPU limit, writes it out as YAML, and reads the YAML back into a typed object. This round trip is a useful check that your types and your YAML agree.

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

The program builds a pod in memory, marshals it to YAML, and then reads the YAML back into a typed object. The `sigs.k8s.io/yaml` package goes from struct to JSON to YAML, so the same struct works in both directions. Notice how the pod is built from nested structs. The `Pod` holds an `ObjectMeta` for its name and labels, and a `PodSpec` for what runs. The `Containers` field is a list of containers, and each container has its own resource requirements. Once you can read that nesting, you can read almost any Kubernetes object in Go.

Several helper types appear again and again. `resource.Quantity` holds CPU, memory and GPU counts. Build one with `resource.MustParse("100Mi")`, then read it with `.Value()`, `.MilliValue()` or `.Cmp()`. `.Cmp()` compares two quantities, which is safer than comparing the raw numbers yourself. `metav1.Time` and `metav1.Duration` cover timestamps and durations. `intstr.IntOrString` holds an integer or a string. To turn a `metav1.LabelSelector` into a `labels.Selector`, use `metav1.LabelSelectorAsSelector`.

Sometimes you have no Go type at all, for example a CRD without generated types. Then `unstructured.Unstructured` wraps a `map[string]interface{}`. A map of this kind holds any fields in any shape, so you lose the compile-time checks. Helpers such as `unstructured.NestedString/NestedSlice/SetNestedField` read and write fields, and they tell you when a field is missing. `runtime.DefaultUnstructuredConverter.FromUnstructured` converts the object into a typed one, once you have a type to convert into.

The scheme tells Kubernetes how Go types map to kinds. A kind is the name of an API type, such as `Pod`. `runtime.Scheme` maps Go types to GroupVersionKind values, and `scheme.AddToScheme` registers types. Serializers decode and encode the data. Use `client-go/kubernetes/scheme` for built-in types, and remember that custom types need their group's `AddToScheme`. If a custom type is not registered, the client does not know how to read or write it, and the error can be confusing. Metadata helpers handle ownership and selectors: `metav1.NewControllerRef`, `controllerutil.SetControllerReference`, `metav1.IsControlledBy`, `labels.Set` and `fields.OneTermEqualSelector("spec.nodeName", n)`. An owner reference is the link that tells the garbage collector who owns a child object.

Generated `DeepCopy()` methods exist for the API types. Never share an object and mutate it, so call `DeepCopy()` first. The copy costs little next to the bugs that a shared, changed object causes.

Two books explain the inner mechanics of `apimachinery` and Go type conventions. *Kubernetes Programming with Go*, Chapters 4 and 5, covers the types and the scheme. *Network Programmability and Automation*, Chapter 7, covers Go's core features in a network setting. Three of those mechanics are worth knowing.

The first is quantities and `intstr.IntOrString` (*Kubernetes Programming with Go*, Chapter 4). `resource.Quantity` lives in `k8s.io/apimachinery/pkg/api/resource`. It stores numbers as exact fixed-point values, so you never get floating-point rounding errors such as `0.1 + 0.2` not equalling `0.3`. Floating-point numbers store values in binary, which cannot represent many decimal fractions exactly. A quantity can be written in two suffix families. Read the table as a choice of units, the way you might write one gigabyte as 1 GB or as 1024 MiB, depending on which tool you are reading.

| Family | Step size | Suffixes | Example |
|---|---|---|---|
| `BinarySI` | powers of 1024 | `Ki`, `Mi`, `Gi`, `Ti`, `Pi`, `Ei` | `1Ki` is 1024 |
| `DecimalSI` | powers of 1000 | `n`, `u`, `m`, `k`, `M`, `G`, `T`, `P`, `E` | `1k` is 1000, and `2500m` is 2.5 |

`intstr.IntOrString`, from `k8s.io/apimachinery/pkg/util/intstr`, appears in `ServicePort.TargetPort`, `RollingUpdateDeployment.MaxSurge`/`MaxUnavailable` and `PodDisruptionBudget`. It holds either an `IntVal` or a `StrVal`, such as `"25%"`. A value like `"25%"` depends on the total number of replicas, so it has to be worked out at run time. You evaluate it with `intstr.GetScaledValueFromIntOrPercent(&intOrStr, totalReplicas, roundUp)`. The `roundUp` flag decides how a fraction turns into a whole number of pods. This behaviour is modeled in `code/part05/client_go_mechanics_sim.py`.

The second is the scheme and the `RESTMapper` (*Kubernetes Programming with Go*, Chapter 5). `runtime.Scheme` is an in-memory registry. It maps Go `reflect.Type` structs to a `schema.GroupVersionKind` (`GVK`, via `AddKnownTypes`, `ObjectKinds`, `New`). It also performs defaulting (`Default`) and version conversion (`Convert`). In plain words, the scheme knows that a Go type called `Deployment` belongs to a group, a version and a kind, and it knows how to turn one version into another.

Go code names an object type by its group, version and kind, written `GVK`, such as `apps/v1, Kind=Deployment`. The HTTP API names the same thing by group, version and resource, written `GVR`, such as `/apis/apps/v1/namespaces/{ns}/deployments`. The kind is the name a human uses, and the resource is the name in the URL. A `RESTMapper` converts between the two. It also tells you whether the resource lives inside a namespace or at cluster level. Without that conversion, a client could not find the URL for a kind it has only seen in a YAML file.

| Piece | What it does |
|---|---|
| `RESTMapping` | Gives the full mapping for one kind |
| `KindFor` and `ResourceFor` | Convert one name into the other |
| `meta.DefaultRESTMapper` | A mapper you fill in yourself |
| `restmapper.NewDeferredDiscoveryRESTMapper` | Asks the API server at run time through `/apis` and caches the answers in memory |

The deferred form is built with `NewDeferredDiscoveryRESTMapper(memory.NewMemCacheClient(discoveryClient))`. The deferred mapper asks the API server when it first needs an answer, using the discovery endpoint `/apis`, and it keeps the answers in memory after that. That means it knows about custom resources installed after your program started, as long as they are installed before the question is asked.

Serializers live in `k8s.io/apimachinery/pkg/runtime/serializer`. A serializer turns objects into bytes and back. `json.NewSerializerWithOptions` handles both JSON and YAML. `protobuf.NewSerializer` uses `application/vnd.kubernetes.protobuf`, which suits high-throughput native core types. Protobuf is a compact binary format, and it is faster to parse than JSON, which is why it suits busy core types.

The third is pointer versus value receivers, and `net/netip` (*Network Programmability and Automation*, Chapter 7). A type `T` with a pointer receiver method, `func (r *Router) Trim()`, satisfies an interface only when you pass a pointer, `*Router`. Pass a plain `Router` and the compiler stops you with `Router does not implement Trimmable (method has pointer receiver)`. The fix is almost always to pass the address of the value, or to change the receiver. For IP and CIDR work in Kubernetes network controllers, Go 1.18 and later offer `net/netip`, with `netip.ParseAddr` and `netip.ParsePrefix`. It is an immutable, comparable, allocation-free value type that replaces the legacy `net.IP` slices. Immutable means a value cannot change after it is made, which makes it safe to share.

![JSON, YAML and Kubernetes types](./img/m5-30-1.svg)

*Figure 5.30.1. JSON, YAML and Kubernetes types, as a diagram.*

Read the diagram from left to right. The reflector feeds the queue, and the work queue carries `namespace/name` keys rather than whole objects. The reflector is the part that lists and watches the API server. The queue holds the work to do, and the indexer is the local store that the lister reads from. Keep the picture in mind when the informer code appears in section 5, because each piece in that code matches a box here.

## 5. client-go

client-go is the official Go library for talking to the Kubernetes API. It has a typed client for each group, a dynamic client for anything untyped, and the informer machinery that controllers depend on. This section shows how to build a client, change objects safely, watch for changes and write a controller loop.

### Building clients

Your tool may run inside a pod one day and on a laptop the next. The function below works in both places. It tries the in-cluster config first, then falls back to a kubeconfig found through `KUBECONFIG` or `~/.kube/config`. The in-cluster config is the one a pod uses with its own service account, and a kubeconfig is the file a person uses from a workstation.

```go
func newClient() (kubernetes.Interface, *rest.Config, error) {
	// precedence: in-cluster → kubeconfig (KUBECONFIG, ~/.kube/config)
	cfg, err := rest.InClusterConfig()
	if err != nil {
		loading := clientcmd.NewDefaultClientConfigLoadingRules()
		cfg, err = clientcmd.NewNonInteractiveDeferredLoadingClientConfig(loading, &clientcmd.ConfigOverrides{}).ClientConfig()
		if err != nil { return nil, nil, fmt.Errorf("load kubeconfig: %w", err) }
	}
	cfg.QPS, cfg.Burst = 50, 100            // default 5/10 is far too low for controllers; see 5.5 about API Priority and Fairness
	cfg.UserAgent = "nodectl/0.1"
	cs, err := kubernetes.NewForConfig(cfg)
	return cs, cfg, err
}
```

The default 5/10 is far too low for controllers. Those numbers are the request rate and the burst size, and a controller that makes many calls will hit them quickly. Raising them lets the controller keep up, but the API server still limits requests with its own fairness rules. See 5.5 for API Priority and Fairness, the server-side limit on request rates.

The typed clientset, `kubernetes.Interface`, exposes `CoreV1()`, `AppsV1()`, `BatchV1()`, `RbacV1()` and more. Each method returns the client for one API group, so you pick the group first and the resource second. The dynamic client, created with `dynamic.NewForConfig`, returns unstructured objects through `Resource(gvr).Namespace(ns).List(...)`, which suits CRDs without generated types. The discovery client lists API groups and resources, and the REST client is low-level. The metadata client returns `PartialObjectMetadata` cheaply, which is useful when you only need names and labels. The scale client and generated clientsets (`client-gen`) complete the set. controller-runtime's `client.Client` adds a cache, as chapter 5.31 covers.

### CRUD, patch, apply

CRUD stands for create, read, update and delete. Those four operations cover most of what a controller does, but the update step is where most of the trouble starts. Two controllers may change the same node at once. If each one reads, changes and writes the whole node, the second write can silently undo the first. The example below shows the safer ways to make the same change.

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

The first block pages through a filtered node list with `Limit` and `opts.Continue`. Paging means the server returns the list in chunks, and `Continue` is the token that asks for the next chunk. Get-modify-update is a common trap. A full `Update` fails with a conflict when your copy is stale, which means someone else wrote the object after you read it. So wrap the read and write in `retry.RetryOnConflict` and read again on each attempt. A merge patch needs no read, because you send only the part you want to change. Server-side apply, with typed apply configurations, records field ownership and is idempotent. Idempotent means that applying the same change twice gives the same result as applying it once.

Eviction is the preferred way to drain a pod, because it respects PDBs. A PDB, or PodDisruptionBudget, is a rule that limits how many pods of an app may be down at once. `EvictV1` returns 429 when a PDB disallows the eviction, so retry later. A 429 is the server's way of saying "not now," so the right response is to wait and try again.

Prefer patch or apply over get-modify-update. Use `Update` only when you handle `resourceVersion` and retry. The resource version is a version marker the server attaches to each object. Treat it as an opaque value, and refuse to guess at its meaning. An update that carries an old marker is refused. For deletes, `DeleteOptions{PropagationPolicy: &fg, GracePeriodSeconds: &g}` sets the propagation, which controls what happens to the children of the deleted object, and the grace period, which gives the object time to shut down cleanly. `Create` returns `AlreadyExists` when the object exists, and `DryRun: []string{metav1.DryRunAll}` validates a request without changing anything. A dry run is a good first step before a risky change.

### Watching

Watching is how a program hears about changes without asking over and over. The loop below handles added, modified, deleted and error events. Each event has a type, and the switch decides what to do with it.

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

Read the loop as a list of cases. A new or changed node arrives as an `Added` or `Modified` event, and the code casts the object back to a `Node` pointer. A `Deleted` event means the node is gone. An `Error` event can carry the status 410 Gone. That status means the resource version the watch started from is too old, so the server no longer remembers the changes. The only fix is to relist and start a fresh watch.

A `watch.Error` with 410 Gone means you must relist. Raw watches also need reconnection, bookmark and resource version handling, and backoff. Bookmarks are periodic markers that let the watch remember its position without a real change. Backoff means waiting longer after each failed attempt. For most code, use `watchtools.NewRetryWatcher` or, almost always, informers. Informers do the relisting and reconnecting for you, which is why most controllers use them.

### Informers, listers and work queues

Suppose a controller must react to every GPU node that joins, leaves or changes. Doing that with raw watches would mean writing the reconnection logic yourself. An informer does that work and keeps a local copy of the objects. The example below sets up an informer, a lister that reads from the local copy, and a work queue that feeds a few worker goroutines.

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

Think of the informer as a local notebook. It copies every GPU node into the notebook when it starts, then keeps the copy up to date from the watch. The lister is the page you read from, so reading a node costs nothing on the network. The work queue is an inbox of keys. The event handlers only put a key into the inbox, and the workers take keys out and do the real work. That separation keeps the handlers fast.

The lister reads from the local cache and serves `Get(name)` and `List(selector)`. The work queue holds keys, and its rate limiter spaces out retries. The event handlers only add keys. Each `DeletedFinalStateUnknown` tombstone needs handling, because a delete can arrive without the final object. A tombstone is a marker that says "this object was deleted, and here is the last state we knew." The `DeletionHandlingMetaNamespaceKeyFunc` unwraps it so the key can still be built.

The code waits for cache sync before the workers start. Cache sync means the notebook has finished its first full copy. Each worker runs `processNext` in a loop. On an error, the key goes back in the queue with `AddRateLimited`, which applies backoff. On success, `Forget` resets the backoff. Backoff here means the wait before a retry grows after repeated failures, so a broken object does not get retried in a tight loop.

Wait for cache sync, read from the lister and write through the client. Never mutate cached objects, so call `DeepCopy()` first. Enqueue keys, not objects. The resync period is a safety net, and one worker handles a given key at a time. A resync is a periodic pass that re-delivers every object, in case an event was lost. Call `Forget` on success, and shut down cleanly on SIGTERM. SIGTERM is the signal Kubernetes sends before it stops a container, so the program has a chance to finish its work.

With several resource types, create one factory for all of them. Add indexers, such as `cache.Indexers{"byNode": func(...)}`, for efficient lookups like pods by node. An indexer builds a second lookup table inside the cache, so a question such as "which pods run on this node" does not have to scan every pod.

### Leader election

Only one replica should act, so the replicas take turns holding a lease. If two replicas both acted on the same nodes, they could cordon the same node twice or fight over the same change. A lease is a small object that records which replica currently holds the job.

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

The lock is a Lease in the `platform` namespace, and each replica identifies itself with its hostname. `RunOrDie` runs the work only while this replica holds the lease. `ReleaseOnCancel` lets the replica give the lease up when its context is cancelled, so a standby can take over quickly. If the replica loses leadership, it logs the event and exits, so a restart can rejoin the election cleanly. Exiting is a deliberate choice here. A replica that lost the lease should not keep acting, and a fresh start is the simplest way to be sure it does not.

### Dynamic client for CRDs

A CRD may have no generated Go types, yet you still need its spec. The dynamic client works from a GroupVersionResource alone. A GroupVersionResource, or GVR, is the three-part address of a resource: its group, its version and its plural name. You do not need a compiled type for it.

```go
gvr := schema.GroupVersionResource{Group: "kueue.x-k8s.io", Version: "v1beta1", Resource: "clusterqueues"}
dc, _ := dynamic.NewForConfig(cfg)
list, err := dc.Resource(gvr).List(ctx, metav1.ListOptions{})
for _, item := range list.Items {
	nominal, found, _ := unstructured.NestedSlice(item.Object, "spec", "resourceGroups")
	_, _ = nominal, found
}
```

The code lists `clusterqueues` through the dynamic client, then reads each item's `spec.resourceGroups` slice with `unstructured.NestedSlice`. The second return value tells you whether the field was found, and the example ignores it, which is fine only for a sketch. In production code, check that flag, so a missing field becomes a clear error and not a silent empty result.

### Logging, metrics, flags

Kubernetes code logs with `klog`, which supports `-v` levels and structured calls such as `klog.InfoS("msg", "key", val)`. A `-v` level sets how much detail is printed, so you can turn on more logs when you need them. Structured calls put key and value pairs in the log line, which makes the logs easier to search. The standard library's `log/slog` is the other option. controller-runtime uses `logr`, typically through `ctrl.Log.WithName`, which gives each controller its own name in the log. Metrics come from `prometheus/client_golang`, which provides counters, gauges and histograms. Keep label values bounded, because every new value of a label creates a new time series.

Flags use `flag`, `pflag` or cobra. Health endpoints use `net/http`, and graceful shutdown uses `signal.NotifyContext`. Graceful shutdown means stopping new work, finishing what is in progress, and then exiting. For anything long-running, prefer informers over raw watches. The informer pattern already handles the hard parts, and writing it yourself is a common source of bugs.

## 6. A small CLI: cordon nodes on XID events (walkthrough)

Suppose a GPU reports an unhealthy condition overnight, and you want its node cordoned before more jobs land on it. Cordoning is the step that marks a node as unschedulable, so new pods stop arriving while the existing ones keep running. The small CLI below does that. It is a dry run unless you turn the dry run off, which means it prints what it would do and changes nothing by default.

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

Read the flags first. `--dry-run` defaults to true, so the tool only prints the nodes it would cordon. The tool collects failures as it goes and returns one error at the end, instead of stopping at the first bad node. That way one broken node does not hide the status of the others. The `unhealthy` function checks the node's conditions for a `GPUHealthy` entry, and it treats `False` as unhealthy. The cordon itself is a merge patch that sets `unschedulable` and adds an annotation with the reason, so a person reading the node later can see why it was cordoned.

Two other facts about this program are worth stating. The listing, the informer program of section 5 (with imports `k8s.io/client-go/informers`, `listers/core/v1`, `tools/cache`, `util/workqueue`, `apimachinery/pkg/util/wait`, `k8s.io/klog/v2`) and the `health` package tests of section 7 were compiled, and their unit tests passed, with Go 1.23.2 and client-go, apimachinery and api at v0.31.0. `go vet` was clean and `go test` passed. The CLI follows the principles from 3.8: a dry-run default, explicit exit codes, aggregated errors, selectors and an idempotent patch.

## 7. Testing

Suppose a small edit moves a critical XID code to the warn level. A table-driven test catches that change before it reaches a cluster. A table-driven test lists the inputs and the expected outputs as rows in one table, then runs the same check on every row. The first example checks the classifier with one row per case, and the second checks cordoning against the client-go fake clientset.

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

In the first test, each row is a case with a name, an input and the expected severity. The loop runs each row as a subtest, so a failure names the case that broke. In the second test, the fake clientset stands in for a real API server. The test creates a node, calls `cordon`, then reads the node back to check that it is now unschedulable. The comment at the end points to reactors, which let a test inject an error on purpose. Injecting errors is how you test the failure paths, which are the ones that usually break first.

Table-driven tests use `t.Run`, and you can add `t.Parallel()` and `t.Helper()` where they fit. `t.Parallel()` lets subtests run at the same time, and `t.Helper()` makes a failure point at the caller's line instead of the helper's. Helpers can take `testing.TB`, which covers both tests and benchmarks. `cmp.Diff` from go-cmp compares values, and it prints the difference when they do not match, which is far more useful than a bare "not equal." `testify` with `require` and `assert` is optional. `require` stops the test on the first failure, and `assert` keeps going. Run the suite with `go test -race -cover ./...`. Fuzzing uses `func FuzzParse(f *testing.F)`, which feeds the function random inputs to find crashes, and benchmarks use `func BenchmarkX(b *testing.B)`.

Fakes are not a real server. `k8s.io/client-go/kubernetes/fake` uses an object tracker, which lacks server behaviour such as admission, defaulting, field validation and resourceVersion conflicts. A fake accepts changes that a real server would refuse, so a passing fake test is necessary but not sufficient. The same applies to `dynamic/fake` and controller-runtime's `fake.NewClientBuilder()`. For integration tests, `sigs.k8s.io/controller-runtime/pkg/envtest` runs a real kube-apiserver and etcd binaries, which covers CRDs, webhooks and status subresources. For e2e tests, run on kind with kuttl, chainsaw or Ginkgo. End-to-end tests run the whole system the way a user would, so they are the slowest and the most convincing.

Design the code so it is easy to test. Keep pure domain logic apart from I/O, use small interfaces, and inject clients and clocks through `k8s.io/utils/clock` and `clock/testing`. A clock you can inject lets a test move time forward on purpose, instead of waiting for real seconds to pass.

## 8. Packaging

Once the binary works, it needs a container image. The multi-stage Dockerfile below builds a static binary in one stage and copies only that file into a minimal image. A multi-stage build uses one image to compile and a second, smaller image to run, so the compiler and the source code never reach production.

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

Read the Dockerfile as two stages. The first stage starts from a Go image, downloads the modules, copies the source and builds the binary. The second stage starts from a distroless image, which contains the minimum a program needs and no shell. It copies in only the binary, runs as a non-root user with a fixed numeric ID, and sets the binary as the entry point. Each `RUN` line uses a cache mount, so repeated builds reuse the downloaded modules and the build cache.

`ko` builds images from Go without a Dockerfile, using `ko build ./cmd/nodectl`. GoReleaser creates the releases and the SBOMs and signatures. When you package it, embed the version with `-ldflags -X`. Run the container as non-root, set resource requests, and expose `/healthz` and `/metrics`. Those two endpoints let the kubelet check health and let Prometheus collect metrics, so they are part of running the tool well, not an extra.

## 9. Idioms and pitfalls checklist

An idiom is a Go habit that experienced engineers use without thinking. A pitfall is the mistake that habit prevents. Read each row as a pair. The left column is the habit to build, and the right column is the mistake to avoid.

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

Use this table as a review checklist before you merge code. Pick three rows that match the change in front of you, and check them against the diff. Most controller bugs are on this list, and the most common ones are the cache mutation and the missing retry on conflict.

## 10. Lab

The lab starts with a Python file, which you can run on your own machine. Start with the self-checking Python lab, and run `code/part05/client_go_mechanics_sim_lab.py`. It checks three things. It verifies the `resource.Quantity` rules from *Kubernetes Programming with Go*, Chapter 4, where `BinarySI` (`Ki..Ei`) is compared with `DecimalSI` (`m..T`). It also verifies the `intstr.GetScaledValueFromIntOrPercent` calculator. Then it checks the `DefaultRESTMapper` from Chapter 5, which covers `GVK <-> GVR` pluralization and scope mapping.

The lab also covers Chapters 6 and 7. It checks the `Lister` `DeepCopy()` cache safety guard, and the `fake.NewSimpleClientset` `PrependReactor` and `Actions()` verifier. Each check mirrors a rule from this chapter, so a passing run means the rule is at least consistent with the model.

```bash
python3 code/part05/client_go_mechanics_sim_lab.py
```

Next, with a Go toolchain (`go 1.22+`) and a `kind` cluster, you work through these exercises. The cluster steps below have not been run against live hardware, so treat them as a plan to check against your own cluster. Work through them in order, because the later steps reuse the `nodectl` project from section 1.

1. Install Go, create the module, and add client-go dependencies that match your kind cluster version. Then build and run a program that lists nodes with GPU labels. Use fake labels on the kind nodes, since kind nodes have no real GPUs.
2. Implement `Classify`, a generic `Filter/Map/GroupBy`, and an `errors.Is` and `errors.As` example with a custom error type. Add a bounded-concurrency prober that uses `errgroup`. Finish by running `go vet` and `go test -race`.
3. Write the node informer and work queue example, and log each reconcile. Kill and restart the program. Then observe the resync and cache behaviour. Add an indexer for pods by node, and print the pod counts per node.
4. Write two goroutines that update the same annotations. First use `Update` and observe the conflicts. Then switch to `Patch` or SSA, which shows no conflicts. Inspect field ownership with `--show-managed-fields`.
5. Implement a raw watch, and force a 410 by delaying the restart. Add a `RetryWatcher`. Then compare it with an informer.
6. Implement `cordon` with an eviction loop that respects PDBs, using retries and backoff. Test it against kind with a PDB that blocks evictions. Add `--timeout` and context cancellation.
7. Write a tool that prints Kueue ClusterQueue usage with unstructured access. Then generate typed structs by importing Kueue's API module. Compare the two approaches.
8. Build the `nodectl cordon-unhealthy` command with cobra, and add tests with the fake clientset. Add `--output json`, cross-compile, and package the binary in a distroless image. Run it as a Job with a ServiceAccount and RBAC. Follow least privilege, so the role allows only nodes `get/list/patch`.
9. Run two replicas of an informer program with a Lease. Then kill the leader and measure the failover.
10. Clone `kubernetes/kubernetes` or `kubernetes/sample-controller`. Trace `pkg/controller/replicaset`'s `syncReplicaSet`, and map it to the reconcile pattern in 5.6. Then find where the informers are wired.
11. Write one envtest integration test that installs a CRD and verifies status subresource behaviour.
12. Clean up.

## 11. Interview angles

Go questions in platform interviews usually test whether you understand the mechanisms behind the Kubernetes libraries. Answer with the mechanism and the trade-off, the same way you would for a design question.

- "Why is Go used for Kubernetes? What Go features matter (interfaces, goroutines, static binaries)?"
- "How do informers work and why must you not mutate objects from a lister?"
- "How do you avoid write conflicts when updating Kubernetes objects from code?"
- "How do you structure a controller's work queue and retries?"
- "Explain contexts and goroutine leaks. How do you test for data races?"
- "How do you test code that talks to the Kubernetes API?" (fake clientset, envtest, kind e2e.)
- "How would you write a tool that safely drains nodes at scale?"

## Exercises

Each exercise asks for one Go skill that Kubernetes code needs. Work through them in order, because later exercises assume the earlier ideas. The simulators live in `code/part05/client_go_mechanics_sim.py`.

1. Explain why optional fields in Kubernetes Go structs are pointers. Then show how `ptr.To` and `ptr.Deref` help.
2. Explain why a method with a pointer receiver does not satisfy an interface when you pass the value. Network Programmability and Automation, Chapter 7, shows the case.
3. Wrap an error with `%w`, and test it with `errors.Is`. Then use `apierrors.IsNotFound` and `apierrors.IsConflict` on a Kubernetes API error.
4. Trace the node prober in Section 3, which uses `errgroup` with `g.SetLimit(16)`. Say how context cancellation reaches the other workers when one fails. Then say why concurrent map writes panic.
5. Run `parse_k8s_quantity_milli()` and `get_scaled_value_from_int_or_percent()`. Contrast `1Ki` at 1024 with `1k` at 1000. Then say what `2500m` means. Kubernetes Programming with Go, Chapters 4 and 5, covers the types.
6. Use `DefaultRESTMapperSim` to show how a Go struct maps to a group-version-kind. Then show how that maps to a group-version-resource.
7. Compare `Update` with `RetryOnConflict`, `Patch`, and Server-Side Apply for changing a node label. Then say why draining uses an Eviction and not `Delete`. Kubernetes Programming with Go, Chapter 6, covers the clients.
8. Trace the informer program in Section 5 from the reflector to the worker. Say why handlers enqueue only `namespace/name` keys. Then say why a tombstone must be unwrapped in `DeleteFunc`.
9. Explain why changing an object from a lister without `DeepCopy()` corrupts the shared cache.
10. Use `FakeClientsetWithCacheSim` to inject a 409 Conflict with `cs.PrependReactor("patch", "nodes", ...)`. Check the calls with `cs.Actions()`. Then compare the fake clientset with `envtest`, which Kubernetes Programming with Go, Chapter 7, covers.

## Checkpoint questions (20)

<details>
<summary>1. Why are optional fields in Kubernetes Go API structs (such as `DeploymentSpec.Replicas` or `Container.SecurityContext.RunAsNonRoot`) defined as pointers (`*int32`, `*bool`) rather than plain values (`int32`, `bool`), and how do `ptr.To` and `ptr.Deref` help (Kubernetes Programming with Go, Chapter 4)?</summary>

Every Go value has a zero value, such as `0` for `int32` and `false` for `bool`. If `DeploymentSpec.Replicas` were a plain `int32`, the JSON/YAML serializer (`omitempty`) and `kube-apiserver` could not tell two cases apart. In the first, the user left `replicas` out of their YAML, so it defaults to `1`. In the second, the user set `replicas: 0`, which scales down to zero pods. A pointer adds a third state. `nil` means unspecified, `&0` means `0`, and `&3` means `3`.

- `ptr.To[T](v)`, from `k8s.io/utils/ptr`, returns a pointer to any literal value, as in `Replicas: ptr.To(int32(3))`.
- `ptr.Deref(p, defaultVal)` reads through the pointer safely. If `p == nil`, it returns `defaultVal` without panicking.
</details>

<details>
<summary>2. In *Network Programmability and Automation* Chapter 7, why does passing a value `rtr` of type `Router` fail to compile when a function expects an interface `Trimmable` whose method was defined as `func (r *Router) TrimHostname()`?</summary>

Go's method-set rules decide this. A value of type `Router` carries only the methods declared with a value receiver, such as `func (r Router) ...`. A pointer, `*Router`, carries both pointer-receiver and value-receiver methods. `TrimHostname` changes the struct in place, so it has a pointer receiver, `func (r *Router)`. Only `*Router`, such as `&rtr`, implements `Trimmable`. Passing `rtr` by value triggers `Router does not implement Trimmable (TrimHostname method has pointer receiver)`.

The same rule explains why Kubernetes `runtime.Object` methods such as `GetObjectKind()` and `DeepCopyObject()` sit on pointer receivers of `*corev1.Pod`. That is why you pass `&corev1.Pod{}` as a `runtime.Object` rather than `corev1.Pod{}`.
</details>

<details>
<summary>3. How do you wrap errors in Go (`%w`), check for specific error values or types (`errors.Is`, `errors.As`), and classify Kubernetes API errors (`k8s.io/apimachinery/pkg/api/errors`)?</summary>

Wrap an error with `%w`, as in `return fmt.Errorf("cordon node %s: %w", name, err)`. The wrap keeps the original error chain intact.

To check a standard Go error, use `errors.Is(err, context.DeadlineExceeded)`. It reports whether any error in the chain matches the target value. Use `errors.As(err, &targetErr)` when you need to pull a specific error struct or interface type out of the chain.

Kubernetes API errors arrive as `StatusError` values, and the `apierrors` helpers classify them. `apierrors.IsNotFound(err)` matches `404`. `apierrors.IsAlreadyExists(err)` matches `409`. `apierrors.IsConflict(err)` also matches `409`, for an optimistic concurrency `resourceVersion` conflict. `apierrors.IsForbidden(err)` matches `403`, and `apierrors.IsTooManyRequests(err)` matches `429`, which comes from a PDB or an APF rate limit.
</details>

<details>
<summary>4. Why does `sigs.k8s.io/yaml` work properly with Kubernetes Go structs (`corev1.Pod`), whereas calling `gopkg.in/yaml.v3` directly on a `corev1.Pod` produces broken field names?</summary>

Every official Kubernetes API struct in `k8s.io/api` carries `json:"..."` struct tags and `protobuf:"..."` tags. None of them carry `yaml:"..."` tags. If you pass a `corev1.Pod` straight to `gopkg.in/yaml.v3`, the library ignores the `json:` tags. It writes the Go field names in lowercase, such as `objectmeta` and ` restartpolicy`. It also skips the custom `MarshalJSON` methods on types like `resource.Quantity` and `metav1.Time`.

`sigs.k8s.io/yaml` avoids that problem. It marshals the struct to JSON first, honouring every `json:"..."` tag and every `MarshalJSON` method. Then it converts the JSON to YAML, and reverses the process on `Unmarshal`.
</details>

<details>
<summary>5. In *Kubernetes Programming with Go* Chapter 4, how does `resource.Quantity` avoid floating-point rounding bugs, and what is the difference between `100Mi` and `100M` or `500m`?</summary>

`resource.Quantity` stores every quantity as an exact scaled integer. Internally, that is an `inf.Dec` or an `int64` mantissa, together with a base-2 or base-10 exponent.

BinarySI suffixes are `Ki`, `Mi`, `Gi`, `Ti`, `Pi` and `Ei`. They are powers of `2^10 = 1024`. So `resource.MustParse("100Mi")` equals `100 * 2^20 = 104,857,600` bytes.

DecimalSI suffixes are `n`, `u`, `m`, `k`, `M`, `G`, `T`, `P` and `E`. They are powers of `10^3 = 1000`. So `100M` equals `100 * 10^6 = 100,000,000`, and `500m`, which means millicores, equals `0.5`. Its `q.MilliValue() == 500`.

Compare two quantities with `q1.Cmp(q2)`, which returns `-1`, `0` or `1`, or with `q1.Equal(q2)`. Do not use `q1 == q2`. The strings `"1000m"` and `"1"` have different scale exponents internally, even though they hold the same value.
</details>

<details>
<summary>6. In *Kubernetes Programming with Go* Chapter 4, how does `intstr.GetScaledValueFromIntOrPercent` evaluate a `maxUnavailable` or `maxSurge` field?</summary>

Fields such as `RollingUpdateDeployment.MaxUnavailable` or `PodDisruptionBudgetSpec.MinAvailable` use `intstr.IntOrString`. That type holds either an integer, such as `intstr.FromInt32(2)`, or a percentage string, such as `intstr.FromString("25%")`.

`intstr.GetScaledValueFromIntOrPercent(&val, totalReplicas, roundUp)` returns `val.IntVal` directly when the value is an integer. For a percentage, it computes `totalReplicas * (pct / 100.0)`. When `roundUp == true`, it rounds up with `ceil`. For example, `maxSurge: "25%"` of 10 pods gives $\rightarrow 3$. When `roundUp == false`, it rounds down with `floor`. For example, `maxUnavailable: "25%"` of 10 pods gives $\rightarrow 2$.
</details>

<details>
<summary>7. In *Kubernetes Programming with Go* Chapter 5, what is the difference between `GVK` (`GroupVersionKind`) and `GVR` (`GroupVersionResource`), and what component translates between them?</summary>

A `GVK`, or `schema.GroupVersionKind`, identifies a Go struct or a YAML schema type. For example, `{Group: "apps", Version: "v1", Kind: "Deployment"}` names the Deployment type.

A `GVR`, or `schema.GroupVersionResource`, identifies a REST endpoint collection on `kube-apiserver`. For example, `{Group: "apps", Version: "v1", Resource: "deployments"}` maps to `/apis/apps/v1/namespaces/{ns}/deployments`.

The translator is `meta.RESTMapper`. You cannot simply add an `s` to a `Kind`, because English plurals are irregular. `Ingress` becomes `ingresses`, and `NetworkPolicy` becomes `networkpolicies`. CRDs can also define any `spec.names.plural` they like. A `RESTMapper`, such as `restmapper.NewDeferredDiscoveryRESTMapper` backed by the Discovery API, translates `GVK <-> GVR` with `RESTMapping`, `ResourceFor` and `KindFor`. It also tells the client whether the resource is namespaced or cluster-scoped.
</details>

<details>
<summary>8. In *Kubernetes Programming with Go* Chapter 5, what are the four core responsibilities of `runtime.Scheme` (`k8s.io/apimachinery/pkg/runtime`)?</summary>

The scheme has four jobs.

1. Type registration (`AddKnownTypes` / `AddToScheme`) maps Go `reflect.Type` structs, such as `&corev1.Pod{}`, to `schema.GroupVersionKind` values, such as `v1, Kind=Pod`.
2. Object instantiation (`scheme.New(gvk)`) allocates a new Go struct pointer for a `GVK` read from `apiVersion` and `kind` during deserialization.
3. Type lookup (`scheme.ObjectKinds(obj)`) finds the `GVK` or `GVK`s registered for a Go `runtime.Object` pointer.
4. Defaulting and conversion (`scheme.Default(obj)` and `scheme.Convert(in, out, ctx)`) run the registered defaulting functions and the hub-and-spoke version conversion functions.
</details>

<details>
<summary>9. Why are the default `rest.Config` `QPS` (`5.0`) and `Burst` (`10`) settings a major bottleneck for custom controllers and CLI tools (Kubernetes Programming with Go, Chapter 6)?</summary>

By default, `client-go` attaches a client-side token-bucket rate limiter, `flowcontrol.NewTokenBucketRateLimiter`. Its settings are `QPS: 5`, which means 5 requests per second, and `Burst: 10`. Suppose an operator reconciles 100 Pods, or a CLI drains a 64-pod GPU node. `client-go` throttles itself on the client side and logs this line:

`Waited for 1.198s due to client-side throttling, not priority and fairness`

A batch of calls can then take 20+ seconds to complete. For production controllers and administrative CLIs, set `cfg.QPS = 50` and `cfg.Burst = 100` explicitly. You rely on server-side API Priority and Fairness, `APF`, to protect `kube-apiserver`.
</details>

<details>
<summary>10. Compare the four main ways to modify an existing Kubernetes object in `client-go`: (a) `Get` + `Update`, (b) `Get` + `Update` inside `retry.RetryOnConflict`, (c) `Patch` (`MergePatchType` / `StrategicMergePatchType`), and (d) Server-Side `Apply` (`ApplyConfigurations`).</summary>

1. A plain `Get` followed by `Update` is fragile. If another controller, such as the kubelet, the HPA or a status updater, changes the object between your `Get` and `Update`, the `resourceVersion` changes, and the `Update` fails with `409 Conflict`.
2. `retry.RetryOnConflict(retry.DefaultRetry, func() error { Get -> mutate -> Update })` fetches the latest `resourceVersion` and applies your mutation again on a `409 Conflict`. It suits mutations that depend on reading the current fields first.
3. `Patch` with `types.MergePatchType` or `types.StrategicMergePatchType` sends only the diff, such as `{"metadata":{"labels":{"quarantine":"true"}}}`. It needs no earlier `Get` and no `resourceVersion`, and it completes in a single round trip.
4. Server-Side Apply, using `Apply` with `applyconfigurations` and `FieldManager: "nodectl"`, is covered in Kubernetes Programming with Go, Chapter 6. It declares only the fields your controller owns, through type-safe builders such as `applycorev1.Node(name).WithLabels(...)`. `kube-apiserver` tracks per-field ownership in `metadata.managedFields`, and it rejects conflicting edits from other managers unless `Force: true` is set.
</details>

<details>
<summary>11. Why should a node-drain CLI in Go call `cs.CoreV1().Pods(ns).EvictV1(ctx, eviction)` instead of `cs.CoreV1().Pods(ns).Delete(ctx, name, opts)`?</summary>

`Pods().Delete(...)` bypasses `PodDisruptionBudget` (`PDB`) checks. It terminates the Pod right away, even if that takes down the last remaining replica of a critical quorum or inference service.

`Pods().EvictV1(...)` uses the `policy/v1` `Eviction` subresource. It asks `kube-apiserver` to check every matching `PodDisruptionBudget` first. If `disruptionsAllowed == 0`, the API server rejects the eviction with `429 Too Many Requests`. Your drain loop can then sleep and retry with backoff until the replacement replicas become `Ready`.
</details>

<details>
<summary>12. Trace the internal data flow of a `client-go` Shared Informer (`Reflector -> DeltaFIFO -> Indexer/Lister -> ResourceEventHandler -> WorkQueue`, Kubernetes Programming with Go, Chapter 6).</summary>

1. The `Reflector` makes an initial `List`, which records the `resourceVersion`. It then runs a long-lived `Watch` against `kube-apiserver`, and it re-lists automatically on `410 Gone`. It pushes `Added`, `Updated`, `Deleted` and `Sync` deltas into the `DeltaFIFO` queue.
2. The `SharedInformer` and its `Controller` loop pop deltas from the `DeltaFIFO`. They update the thread-safe local in-memory cache, which is the `Indexer` or `Store`. Then they call every registered `ResourceEventHandler`, which means `AddFunc`, `UpdateFunc` and `DeleteFunc`.
3. Each `ResourceEventHandler` extracts the `"namespace/name"` key with `cache.MetaNamespaceKeyFunc(obj)`. It then calls `queue.Add(key)` on the rate-limited `WorkQueue`.
4. Worker goroutines call `queue.Get()` and read the current object from the `Lister`, which is backed by the local `Indexer`. Reading through the `Lister` needs no network round trip. The worker reconciles the desired state, then calls `queue.Done(key)` and `queue.Forget(key)`, or `queue.AddRateLimited(key)` on error.
</details>

<details>
<summary>13. Why must you NEVER mutate an object pointer returned by a `Lister` (`node, _ := nodeLister.Get(name)`) without calling `node = node.DeepCopy()` first (Kubernetes Programming with Go, Chapter 6)?</summary>

For speed and memory efficiency, a `SharedInformer`'s `Lister` returns a direct pointer to the shared object in the in-memory `Indexer` cache. That is the same pointer that every other informer handler and worker goroutine in your process reads at the same time.

Suppose you modify `node.Labels["foo"] = "bar"` without calling `node = node.DeepCopy()` first. Two bad things can follow.

1. You cause a concurrent map or struct data race, and the program fails with `fatal error: concurrent map read and map write` while other goroutines read the cache.
2. If your later `Update()` API call fails, the local informer cache stays corrupted with your unsaved change. Future reconciles then assume the label is already set in `etcd`, even though it is not.
</details>

<details>
<summary>14. What is `cache.DeletedFinalStateUnknown` (a "Tombstone") in an Informer's `DeleteFunc(obj interface{})`, and how do you handle it safely?</summary>

Suppose a watch connection drops briefly, and an object is deleted in `etcd` while the watch is down. When the `Reflector` re-lists, it sees that the object has gone. It never saw the `DELETED` watch event, though, so it does not know the exact final state at the moment of deletion. It wraps the last known cached object in a `cache.DeletedFinalStateUnknown` struct, which is called a tombstone, and passes that to `DeleteFunc`.

Always unwrap the tombstone before you cast or call `MetaNamespaceKeyFunc`. The helper `cache.DeletionHandlingMetaNamespaceKeyFunc` does this for you automatically.

```go
node, ok := obj.(*corev1.Node)
if !ok {
    tombstone, ok := obj.(cache.DeletedFinalStateUnknown)
    if !ok { return }
    node, ok = tombstone.Obj.(*corev1.Node)
    if !ok { return }
}
```
</details>

<details>
<summary>15. In a `client-go` `WorkQueue` (`workqueue.TypedRateLimitingInterface`), what is the difference between `queue.Done(key)` and `queue.Forget(key)`?</summary>

`queue.Done(key)`, usually written `defer queue.Done(key)`, tells the WorkQueue that this worker has finished with `key` for now. While `key` sits between `Get()` and `Done()`, the WorkQueue guarantees that no other worker receives the same `key`. If a new event for `key` arrives while it is in flight, the queue holds it in the `dirty` set until `Done(key)` is called.

`queue.Forget(key)` resets the rate-limiter failure counter for `key` back to `0` after a successful reconcile. Suppose you call `Done(key)` but never `Forget(key)` on success. The next time `key` fails, its exponential backoff picks up from the old high failure count, rather than starting fresh.
</details>

<details>
<summary>16. How do you restrict a `SharedInformerFactory`'s memory usage when your controller only cares about GPU nodes or a specific label selector (`WithTweakListOptions`)?</summary>

By default, `informers.NewSharedInformerFactory(cs, resync)` caches every object of each watched kind across all namespaces. In a large cluster, that can use gigabytes of RAM, especially for Pods, Secrets or ConfigMaps.

Use `informers.NewSharedInformerFactoryWithOptions` with `informers.WithNamespace(ns)` and `informers.WithTweakListOptions`, as in the code below.

```go
factory := informers.NewSharedInformerFactoryWithOptions(cs, 10*time.Minute,
    informers.WithTweakListOptions(func(opts *metav1.ListOptions) {
        opts.LabelSelector = "nvidia.com/gpu.present=true"
    }),
)
```

You can also register a `cache.TransformFunc` with `informer.SetTransform`. It strips large fields you never use, such as `managedFields` or large annotations, before the objects enter the in-memory cache.
</details>

<details>
<summary>17. When should you use `client-go`'s `dynamic.Interface` (`unstructured.Unstructured`) vs. `metadata.Interface` (`metav1.PartialObjectMetadata`)?</summary>

Use `dynamic.Interface`, from `k8s.io/client-go/dynamic`, when your tool needs to inspect or change custom resources whose compiled Go structs you do not import. It works with `unstructured.Unstructured`, which is a `map[string]interface{}`, and it is addressed by a `schema.GroupVersionResource`, or `GVR`. A generic backup tool, a policy engine or a Kueue CLI fits this case.

Use `metadata.Interface`, from `k8s.io/client-go/metadata`, when you only need object metadata. It sends `Accept: application/vnd.kubernetes.protobuf;as=PartialObjectMetadata`, so `kube-apiserver` returns only `TypeMeta` and `ObjectMeta`. That means `name`, `namespace`, `uid`, `labels`, `annotations`, `ownerReferences` and `finalizers`, without `.spec` or `.status`. It suits garbage collectors, label auditors and finalizer tools that scan tens of thousands of objects, and it uses about 90% less memory and network than full objects.
</details>

<details>
<summary>18. In *Kubernetes Programming with Go* Chapter 7, how do `fake.NewSimpleClientset`, `cs.Actions()`, and `cs.PrependReactor` work in unit tests, and what are the limitations of the fake clientset?</summary>

`fake.NewSimpleClientset(initialObjs...)` creates an in-memory `kubernetes.Interface`, backed by an `ObjectTracker`. Unit tests run in milliseconds without a cluster.

`cs.Actions()` returns the ordered slice of `testing.Action` values, such as `GetAction`, `CreateAction` and `PatchAction`, that your code performed. You can assert the exact verbs, resources and payloads.

`cs.PrependReactor(verb, resource, reactionFunc)`, covered in Chapter 7, runs before the default `ObjectTracker`. That lets a test simulate API server errors, such as `409 Conflict`, `429 Too Many Requests` or `500 Internal Error`, or make custom server-side changes:

  ```go
  cs.PrependReactor("patch", "nodes", func(action ktesting.Action) (bool, runtime.Object, error) {
      return true, nil, apierrors.NewConflict(schema.GroupResource{Resource: "nodes"}, "n1", errors.New("conflict"))
  })
  ```

The fake clientset does not enforce OpenAPI or CRD schema validation, CEL rules, defaulting, real `resourceVersion` optimistic concurrency, `/status` subresource isolation or garbage collection. For integration tests that need real API server behaviour, use `envtest` (`sigs.k8s.io/controller-runtime/pkg/envtest`), which starts real local `kube-apiserver` and `etcd` binaries.
</details>

<details>
<summary>19. How does Leader Election (`leaderelection.RunOrDie` with `resourcelock.LeasesResourceLock`) prevent split-brain when running 2+ HA replicas of a custom controller?</summary>

Every replica tries to acquire and renew a `coordination.k8s.io/v1` `Lease` object in the controller's namespace. The timings are `LeaseDuration: 15s`, `RenewDeadline: 10s` and `RetryPeriod: 2s`.

Only the one replica that holds the Lease starts its `OnStartedLeading` workers, and only that replica writes to the cluster. Standby replicas can keep their read-only informer caches warm, so failover is fast.

`ReleaseOnCancel: true` makes a leader that receives `SIGTERM`, and therefore has its `ctx` cancelled, release the Lease right away. A standby can then take over in less than 2 seconds, rather than waiting 15 seconds for `LeaseDuration` to expire.

`OnStoppedLeading: func() { os.Exit(1) }` covers the case where the leader fails to renew its Lease within `RenewDeadline: 10s`, for example during a network partition. The replica must then abort its in-flight contexts and exit, so two replicas never reconcile at the same time.
</details>

<details>
<summary>20. Explain the flags used in Section 8's multi-stage Dockerfile (`CGO_ENABLED=0 go build -trimpath -ldflags="-s -w -X main.version=${VERSION}"`) and why `gcr.io/distroless/static:nonroot` is used as the runtime base.</summary>

`CGO_ENABLED=0` turns off cgo. The result is a pure-Go, statically linked binary with no dependency on `libc.so`, whether `glibc` or `musl`. That lets the binary run in an empty `scratch` or `distroless/static` image.

`-trimpath` removes local build-machine paths, such as `/Users/alice/go/src/...`, from stack traces in the binary. That keeps builds reproducible.

`-ldflags="-s -w -X main.version=${VERSION}"` does two things. `-s` and `-w` strip the symbol table and the DWARF debug headers, which shrinks the binary by about 30%. `-X main.version=...` injects the Git tag or commit version into the `var version string` variable at link time.

`FROM gcr.io/distroless/static:nonroot`, with `USER 65532:65532`, gives you a base image that holds only CA certificates, `/etc/passwd` with the `nonroot` user, and tzdata. It has no shell (`/bin/sh`), no package manager and no root privileges. That keeps the image small, about 2 MB plus the binary, and limits the CVE surface.
</details>

## Sources and review notes

- **Sources read in full:**
  - `kubernetes-programming-with-go-programming-kubernetes-clients-and-operators-using-go-and-the-kuberne` — Philippe Martin / Stefan Schimanski & Michael Hausenblas, *Kubernetes Programming with Go* / *Programming Kubernetes*, **Chapter 4: Using Common Types** (`pointer`/`ptr`, `resource.Quantity` `BinarySI` vs `DecimalSI`, `intstr.IntOrString` and `GetScaledValueFromIntOrPercent`, `metav1.Time`), **Chapter 5: The API Machinery** (`GVK` vs `GVR`, `runtime.Scheme`, `DefaultRESTMapper` & `DeferredDiscoveryRESTMapper`, JSON/YAML/Protobuf serializers), **Chapter 6: The Client-go Library** (`rest.Config` `QPS`/`Burst`, typed/dynamic/discovery clients, `labels.NewRequirement`, `fields`, `ApplyConfigurations`, `SharedInformerFactory`, `Lister` `DeepCopy()`, and `workqueue`), and **Chapter 7: Testing Applications Using Client-go** (`fake.NewSimpleClientset`, `Actions()`, `PrependReactor`, and `fakediscovery.FakeDiscovery`).
  - `network-programmability-and-automation-2nd-edition` — Jason Edelman, Scott S. Lowe & Matt Oswalt, *Network Programmability and Automation*, 2nd ed., **Chapter 7: Go** (read in full: Go compilation and execution, types, slices/maps, pointer vs value method receivers on interfaces, structs, goroutines/channels, `context`, `encoding/json`, `net/netip` `ParsePrefix`, and testing).
- **Run here:** `python3 code/part05/client_go_mechanics_sim_lab.py` (3 passed, 0 failed); Go listings in Section 6 compiled and unit-tested with Go 1.23.2 / `client-go v0.31.0`.
- **Explicitly labelled inferences:** The `parse_k8s_quantity_milli`, `get_scaled_value_from_int_or_percent`, `DefaultRESTMapperSim`, and `FakeClientsetWithCacheSim` models in `code/part05/client_go_mechanics_sim.py` and the `nodectl`, `XIDEvent`, and informer+workqueue Go programs are the author's constructions synthesizing *Kubernetes Programming with Go* Chapters 4–7 and *Network Programmability and Automation* Chapter 7 (plus original study items 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, and 35).
- **Not verified on live hardware:** Live cluster executions of `nodectl` (`go 1.22` / `1.23.2`, `client-go v0.31.0`, XIDs `79`/`74`/`13`/`999`, `g.SetLimit(16)`, `cuda:12.4.1-base-ubuntu22.04`, `100Mi`, `QPS: 50, Burst: 100` vs `5/10`, `Limit: 500`, `410 Gone`, `maxRetries = 5`, `LeaseDuration: 15s, RenewDeadline: 10s, RetryPeriod: 2s`, `USER 65532:65532`) are marked (not run against live hardware here) where not executed by `client_go_mechanics_sim_lab.py`.
