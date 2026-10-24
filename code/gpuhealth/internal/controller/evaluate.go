package controller

import (
	"sort"
	"time"

	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/util/intstr"

	v1alpha1 "example.com/gpuhealth/api/v1alpha1"
)

const (
	// AnnotationOwner records which policy cordoned a node, so the controller only ever
	// uncordons nodes it cordoned itself and never fights a human operator.
	AnnotationOwner  = "platform.example.com/cordoned-by"
	AnnotationReason = "platform.example.com/cordon-reason"
	AnnotationSince  = "platform.example.com/cordoned-at"
	FinalizerName    = "platform.example.com/release-cordons"
)

// NodeVerdict is the pure-function result of looking at one node.
type NodeVerdict struct {
	Name           string
	Unhealthy      bool          // condition False for at least UnhealthyFor
	Pending        bool          // condition False but window not yet elapsed
	WaitFor        time.Duration // time until Pending becomes Unhealthy
	Healthy        bool          // condition True (or absent) for at least HealthyFor
	HealthyWaitFor time.Duration // time until a recovering node counts as healthy
	OwnedByPolicy  bool
	Unschedulable  bool
}

// Judge inspects a node against the policy at time now. It has no side effects.
func Judge(p *v1alpha1.GPUHealthPolicy, n *corev1.Node, now time.Time) NodeVerdict {
	v := NodeVerdict{
		Name:          n.Name,
		Unschedulable: n.Spec.Unschedulable,
		OwnedByPolicy: n.Annotations[AnnotationOwner] == p.Name,
	}
	condType := corev1.NodeConditionType(p.Spec.ConditionType)
	var cond *corev1.NodeCondition
	for i := range n.Status.Conditions {
		if n.Status.Conditions[i].Type == condType {
			cond = &n.Status.Conditions[i]
			break
		}
	}
	unhealthyFor := p.Spec.UnhealthyFor.Duration
	healthyFor := p.Spec.HealthyFor.Duration

	if cond != nil && cond.Status == corev1.ConditionFalse {
		age := now.Sub(cond.LastTransitionTime.Time)
		if age >= unhealthyFor {
			v.Unhealthy = true
		} else {
			v.Pending = true
			v.WaitFor = unhealthyFor - age
		}
		return v
	}
	// True, Unknown or absent: treat absent as healthy (no signal yet), Unknown as "not proven healthy".
	if cond == nil {
		v.Healthy = true
		return v
	}
	if cond.Status == corev1.ConditionTrue {
		age := now.Sub(cond.LastTransitionTime.Time)
		if age >= healthyFor {
			v.Healthy = true
		} else {
			v.HealthyWaitFor = healthyFor - age
		}
	}
	return v
}

// Budget returns the maximum number of matched nodes allowed to be unschedulable.
// A nil maxUnavailable means "no limit" (represented as matched).
func Budget(maxUnavailable *intstr.IntOrString, matched int) int {
	if maxUnavailable == nil {
		return matched
	}
	v, err := intstr.GetScaledValueFromIntOrPercent(maxUnavailable, matched, true)
	if err != nil || v < 0 {
		return 0 // fail safe: invalid budget means do nothing
	}
	if v > matched {
		return matched
	}
	return v
}

// Plan decides which unhealthy nodes to act on, honouring the budget.
// unavailable is the number of matched nodes that are already unschedulable.
// Deterministic ordering (by name) makes reconciles repeatable.
func Plan(verdicts []NodeVerdict, budget int) (act []string, blocked []string) {
	unavailable := 0
	for _, v := range verdicts {
		if v.Unschedulable {
			unavailable++
		}
	}
	var candidates []string
	for _, v := range verdicts {
		if v.Unhealthy && !v.Unschedulable {
			candidates = append(candidates, v.Name)
		}
	}
	sort.Strings(candidates)
	room := budget - unavailable
	for _, name := range candidates {
		if room > 0 {
			act = append(act, name)
			room--
		} else {
			blocked = append(blocked, name)
		}
	}
	return act, blocked
}
