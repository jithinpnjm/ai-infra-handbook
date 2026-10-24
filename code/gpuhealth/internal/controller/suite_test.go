package controller

import (
	"context"
	"path/filepath"
	"testing"
	"time"

	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/types"
	"k8s.io/apimachinery/pkg/util/intstr"
	clientgoscheme "k8s.io/client-go/kubernetes/scheme"
	"k8s.io/client-go/rest"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/envtest"
	metricsserver "sigs.k8s.io/controller-runtime/pkg/metrics/server"

	v1alpha1 "example.com/gpuhealth/api/v1alpha1"
)

var (
	cfg *rest.Config
	k   client.Client
)

func TestMain(m *testing.M) {
	env := &envtest.Environment{CRDDirectoryPaths: []string{filepath.Join("..", "..", "config", "crd")}, ErrorIfCRDPathMissing: true}
	var err error
	if cfg, err = env.Start(); err != nil {
		panic(err)
	}
	sch := runtime.NewScheme()
	_ = clientgoscheme.AddToScheme(sch)
	_ = v1alpha1.AddToScheme(sch)
	k, _ = client.New(cfg, client.Options{Scheme: sch})
	mgr, err := ctrl.NewManager(cfg, ctrl.Options{Scheme: sch, Metrics: metricsserver.Options{BindAddress: "0"}})
	if err != nil {
		panic(err)
	}
	r := &GPUHealthPolicyReconciler{Client: mgr.GetClient(), Recorder: mgr.GetEventRecorderFor("test")}
	if err := r.SetupWithManager(mgr); err != nil {
		panic(err)
	}
	ctx, cancel := context.WithCancel(context.Background())
	go func() { _ = mgr.Start(ctx) }()
	code := m.Run()
	cancel()
	_ = env.Stop()
	if code != 0 {
		panic("tests failed")
	}
}

func mkNode(t *testing.T, name string, healthy bool, since time.Duration) {
	t.Helper()
	n := &corev1.Node{ObjectMeta: metav1.ObjectMeta{Name: name, Labels: map[string]string{"pool": t.Name()}}}
	if err := k.Create(context.Background(), n); err != nil {
		t.Fatal(err)
	}
	setCond(t, name, healthy, since)
}

func setCond(t *testing.T, name string, healthy bool, since time.Duration) {
	t.Helper()
	var n corev1.Node
	if err := k.Get(context.Background(), types.NamespacedName{Name: name}, &n); err != nil {
		t.Fatal(err)
	}
	st := corev1.ConditionTrue
	if !healthy {
		st = corev1.ConditionFalse
	}
	n.Status.Conditions = []corev1.NodeCondition{{Type: "GPUHealthy", Status: st, Reason: "test",
		LastTransitionTime: metav1.NewTime(time.Now().Add(-since)), LastHeartbeatTime: metav1.Now()}}
	if err := k.Status().Update(context.Background(), &n); err != nil {
		t.Fatal(err)
	}
}

func mkPolicy(t *testing.T, name string, max *intstr.IntOrString, dry bool) {
	t.Helper()
	p := &v1alpha1.GPUHealthPolicy{ObjectMeta: metav1.ObjectMeta{Name: name},
		Spec: v1alpha1.GPUHealthPolicySpec{NodeSelector: map[string]string{"pool": t.Name()},
			UnhealthyFor: metav1.Duration{Duration: 2 * time.Second}, HealthyFor: metav1.Duration{Duration: 2 * time.Second},
			Action: v1alpha1.ActionCordon, MaxUnavailableNodes: max, DryRun: dry}}
	if err := k.Create(context.Background(), p); err != nil {
		t.Fatal(err)
	}
}

func eventually(t *testing.T, what string, f func() bool) {
	t.Helper()
	deadline := time.Now().Add(20 * time.Second)
	for time.Now().Before(deadline) {
		if f() {
			return
		}
		time.Sleep(200 * time.Millisecond)
	}
	t.Fatalf("timed out waiting for: %s", what)
}

func cordoned(name string) bool {
	var n corev1.Node
	if err := k.Get(context.Background(), types.NamespacedName{Name: name}, &n); err != nil {
		return false
	}
	return n.Spec.Unschedulable
}

func TestCordonThenUncordon(t *testing.T) {
	mkNode(t, "a1", false, time.Minute) // unhealthy long enough
	mkNode(t, "a2", true, time.Minute)
	mkPolicy(t, "p-a", nil, false)
	eventually(t, "a1 cordoned", func() bool { return cordoned("a1") })
	time.Sleep(time.Second)
	if cordoned("a2") {
		t.Fatal("healthy node must not be cordoned")
	}
	// recover: healthy for long enough -> uncordon
	setCond(t, "a1", true, time.Minute)
	eventually(t, "a1 uncordoned", func() bool { return !cordoned("a1") })
	var n corev1.Node
	_ = k.Get(context.Background(), types.NamespacedName{Name: "a1"}, &n)
	if _, ok := n.Annotations[AnnotationOwner]; ok {
		t.Fatal("ownership annotation should be removed on uncordon")
	}
}

func TestBudgetLimitsCordons(t *testing.T) {
	for _, nm := range []string{"b1", "b2", "b3"} {
		mkNode(t, nm, false, time.Minute)
	}
	one := intstr.FromInt32(1)
	mkPolicy(t, "p-b", &one, false)
	eventually(t, "one cordoned", func() bool { return cordoned("b1") })
	time.Sleep(2 * time.Second)
	if cordoned("b2") || cordoned("b3") {
		t.Fatal("budget=1 must cap cordons at one node")
	}
	eventually(t, "BudgetExhausted condition", func() bool {
		var p v1alpha1.GPUHealthPolicy
		if k.Get(context.Background(), types.NamespacedName{Name: "p-b"}, &p) != nil {
			return false
		}
		for _, c := range p.Status.Conditions {
			if c.Type == "BudgetExhausted" && c.Status == metav1.ConditionTrue {
				return true
			}
		}
		return false
	})
}

func TestDryRunDoesNothing(t *testing.T) {
	mkNode(t, "c1", false, time.Minute)
	mkPolicy(t, "p-c", nil, true)
	eventually(t, "status populated", func() bool {
		var p v1alpha1.GPUHealthPolicy
		return k.Get(context.Background(), types.NamespacedName{Name: "p-c"}, &p) == nil && p.Status.UnhealthyNodes == 1
	})
	time.Sleep(time.Second)
	if cordoned("c1") {
		t.Fatal("dryRun must not cordon")
	}
}

func TestPendingWindowWaits(t *testing.T) {
	mkNode(t, "d1", false, 0) // just turned unhealthy
	mkPolicy(t, "p-d", nil, false)
	time.Sleep(time.Second)
	if cordoned("d1") {
		t.Fatal("must not cordon before unhealthyFor elapses")
	}
	eventually(t, "cordoned after window", func() bool { return cordoned("d1") }) // RequeueAfter fires with no further node event
}

func TestFinalizerReleasesOwnCordonsOnly(t *testing.T) {
	mkNode(t, "e1", false, time.Minute)
	mkNode(t, "e2", true, time.Minute)
	mkPolicy(t, "p-e", nil, false)
	eventually(t, "e1 cordoned", func() bool { return cordoned("e1") })
	// a human cordons e2 by hand
	var n corev1.Node
	_ = k.Get(context.Background(), types.NamespacedName{Name: "e2"}, &n)
	n.Spec.Unschedulable = true
	if err := k.Update(context.Background(), &n); err != nil {
		t.Fatal(err)
	}
	p := &v1alpha1.GPUHealthPolicy{ObjectMeta: metav1.ObjectMeta{Name: "p-e"}}
	if err := k.Delete(context.Background(), p); err != nil {
		t.Fatal(err)
	}
	eventually(t, "policy gone", func() bool {
		return errors.IsNotFound(k.Get(context.Background(), types.NamespacedName{Name: "p-e"}, &v1alpha1.GPUHealthPolicy{}))
	})
	if cordoned("e1") {
		t.Fatal("finalizer should have released the policy's own cordon")
	}
	if !cordoned("e2") {
		t.Fatal("a human's cordon must be left alone")
	}
}
