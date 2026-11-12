package controller

import (
	"testing"
	"time"

	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/util/intstr"

	v1alpha1 "example.com/gpuhealth/api/v1alpha1"
)

func policy() *v1alpha1.GPUHealthPolicy {
	return &v1alpha1.GPUHealthPolicy{
		ObjectMeta: metav1.ObjectMeta{Name: "default"},
		Spec: v1alpha1.GPUHealthPolicySpec{
			ConditionType: "GPUHealthy",
			UnhealthyFor:  metav1.Duration{Duration: 2 * time.Minute},
			HealthyFor:    metav1.Duration{Duration: 5 * time.Minute},
		},
	}
}

func node(name string, status corev1.ConditionStatus, since time.Time) *corev1.Node {
	n := &corev1.Node{ObjectMeta: metav1.ObjectMeta{Name: name}}
	if status != "" {
		n.Status.Conditions = []corev1.NodeCondition{{Type: "GPUHealthy", Status: status, LastTransitionTime: metav1.NewTime(since)}}
	}
	return n
}

func TestJudge(t *testing.T) {
	now := time.Date(2026, 10, 24, 12, 0, 0, 0, time.UTC)
	tests := []struct {
		name string
		n    *corev1.Node
		want func(NodeVerdict) bool
	}{
		{"false for 3m is unhealthy", node("a", corev1.ConditionFalse, now.Add(-3*time.Minute)), func(v NodeVerdict) bool { return v.Unhealthy && !v.Pending }},
		{"false for 30s is pending 90s", node("a", corev1.ConditionFalse, now.Add(-30*time.Second)), func(v NodeVerdict) bool { return v.Pending && v.WaitFor == 90*time.Second && !v.Unhealthy }},
		{"true for 10m is healthy", node("a", corev1.ConditionTrue, now.Add(-10*time.Minute)), func(v NodeVerdict) bool { return v.Healthy }},
		{"true for 1m is not yet healthy", node("a", corev1.ConditionTrue, now.Add(-1*time.Minute)), func(v NodeVerdict) bool { return !v.Healthy && v.HealthyWaitFor == 4*time.Minute }},
		{"absent is neither healthy nor unhealthy", node("a", "", now), func(v NodeVerdict) bool { return !v.Healthy && !v.Unhealthy && !v.Pending }},
		{"unknown is neither healthy nor unhealthy", node("a", corev1.ConditionUnknown, now.Add(-time.Hour)), func(v NodeVerdict) bool { return !v.Healthy && !v.Unhealthy && !v.Pending }},
	}
	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			if v := Judge(policy(), tc.n, now); !tc.want(v) {
				t.Fatalf("unexpected verdict: %+v", v)
			}
		})
	}
}

func TestBudgetAndPlan(t *testing.T) {
	two := intstr.FromInt32(2)
	pct := intstr.FromString("25%")
	bad := intstr.FromString("abc")
	if got := Budget(&two, 10); got != 2 {
		t.Fatalf("int budget = %d", got)
	}
	if got := Budget(&pct, 10); got != 3 { // 25% of 10 rounded up
		t.Fatalf("percent budget = %d", got)
	}
	if got := Budget(&bad, 10); got != 0 {
		t.Fatalf("invalid budget must fail safe to 0, got %d", got)
	}
	if got := Budget(nil, 10); got != 10 {
		t.Fatalf("nil budget = %d", got)
	}
	verdicts := []NodeVerdict{
		{Name: "n3", Unhealthy: true},
		{Name: "n1", Unhealthy: true},
		{Name: "n2", Unhealthy: true},
		{Name: "n4", Unschedulable: true}, // already unavailable (e.g. cordoned by a human)
	}
	act, blocked := Plan(verdicts, 3) // budget 3, one already unavailable -> room for 2
	if len(act) != 2 || act[0] != "n1" || act[1] != "n2" || len(blocked) != 1 || blocked[0] != "n3" {
		t.Fatalf("plan act=%v blocked=%v", act, blocked)
	}
}
