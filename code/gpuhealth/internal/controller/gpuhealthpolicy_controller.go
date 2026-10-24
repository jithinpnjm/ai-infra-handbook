package controller

import (
	"context"
	"fmt"
	"sort"
	"time"

	corev1 "k8s.io/api/core/v1"
	policyv1 "k8s.io/api/policy/v1"
	apierrors "k8s.io/apimachinery/pkg/api/errors"
	"k8s.io/apimachinery/pkg/api/meta"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/labels"
	"k8s.io/apimachinery/pkg/types"
	"k8s.io/client-go/tools/record"
	"k8s.io/utils/clock"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/builder"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/controller/controllerutil"
	"sigs.k8s.io/controller-runtime/pkg/event"
	"sigs.k8s.io/controller-runtime/pkg/handler"
	"sigs.k8s.io/controller-runtime/pkg/log"
	"sigs.k8s.io/controller-runtime/pkg/predicate"
	"sigs.k8s.io/controller-runtime/pkg/reconcile"

	v1alpha1 "example.com/gpuhealth/api/v1alpha1"
)

const (
	conditionReady   = "Ready"
	conditionBlocked = "BudgetExhausted"
	podNodeNameIndex = "spec.nodeName"
)

// GPUHealthPolicyReconciler reconciles GPUHealthPolicy objects.
type GPUHealthPolicyReconciler struct {
	client.Client
	Recorder record.EventRecorder
	Clock    clock.Clock
}

// +kubebuilder:rbac:groups=platform.example.com,resources=gpuhealthpolicies,verbs=get;list;watch;update;patch
// +kubebuilder:rbac:groups=platform.example.com,resources=gpuhealthpolicies/status,verbs=get;update;patch
// +kubebuilder:rbac:groups=platform.example.com,resources=gpuhealthpolicies/finalizers,verbs=update
// +kubebuilder:rbac:groups="",resources=nodes,verbs=get;list;watch;patch
// +kubebuilder:rbac:groups="",resources=pods,verbs=get;list;watch
// +kubebuilder:rbac:groups="",resources=pods/eviction,verbs=create
// +kubebuilder:rbac:groups="",resources=events,verbs=create;patch

func (r *GPUHealthPolicyReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
	logger := log.FromContext(ctx)

	var policy v1alpha1.GPUHealthPolicy
	if err := r.Get(ctx, req.NamespacedName, &policy); err != nil {
		return ctrl.Result{}, client.IgnoreNotFound(err) // deleted: nothing to do (level-triggered)
	}

	// Deletion: release only the cordons this policy placed, then drop the finalizer.
	if !policy.DeletionTimestamp.IsZero() {
		if controllerutil.ContainsFinalizer(&policy, FinalizerName) {
			if err := r.releaseAll(ctx, &policy); err != nil {
				return ctrl.Result{}, err
			}
			controllerutil.RemoveFinalizer(&policy, FinalizerName)
			if err := r.Update(ctx, &policy); err != nil {
				return ctrl.Result{}, err
			}
		}
		return ctrl.Result{}, nil
	}
	if controllerutil.AddFinalizer(&policy, FinalizerName) {
		if err := r.Update(ctx, &policy); err != nil {
			return ctrl.Result{}, err
		}
	}

	// Observe.
	sel := labels.SelectorFromSet(policy.Spec.NodeSelector)
	var nodes corev1.NodeList
	if err := r.List(ctx, &nodes, client.MatchingLabelsSelector{Selector: sel}); err != nil {
		return ctrl.Result{}, err
	}
	now := r.Clock.Now()
	verdicts := make([]NodeVerdict, 0, len(nodes.Items))
	byName := map[string]*corev1.Node{}
	var requeue time.Duration
	setMin := func(d time.Duration) {
		if d > 0 && (requeue == 0 || d < requeue) {
			requeue = d
		}
	}
	unhealthy := int32(0)
	for i := range nodes.Items {
		n := &nodes.Items[i]
		byName[n.Name] = n
		v := Judge(&policy, n, now)
		verdicts = append(verdicts, v)
		if v.Unhealthy || v.Pending {
			unhealthy++
		}
		setMin(v.WaitFor)
		setMin(v.HealthyWaitFor)
	}

	// Decide.
	budget := Budget(policy.Spec.MaxUnavailableNodes, len(nodes.Items))
	act, blocked := Plan(verdicts, budget)

	// Act (unless Ignore/DryRun).
	var actErrs []error
	if policy.Spec.Action != v1alpha1.ActionIgnore {
		for _, name := range act {
			if policy.Spec.DryRun {
				r.Recorder.Eventf(&policy, corev1.EventTypeNormal, "DryRunCordon", "would cordon node %s", name)
				continue
			}
			if err := r.cordon(ctx, &policy, byName[name]); err != nil {
				actErrs = append(actErrs, fmt.Errorf("cordon %s: %w", name, err))
			}
		}
		if policy.Spec.Action == v1alpha1.ActionCordonAndDrain && !policy.Spec.DryRun {
			for _, v := range verdicts {
				if !v.OwnedByPolicy && !contains(act, v.Name) {
					continue
				}
				if !(v.Unhealthy || contains(act, v.Name)) {
					continue
				}
				remaining, err := r.drain(ctx, &policy, v.Name)
				if err != nil {
					actErrs = append(actErrs, fmt.Errorf("drain %s: %w", v.Name, err))
				}
				if remaining > 0 {
					setMin(15 * time.Second) // pods still terminating or blocked by a PDB: look again soon
				}
			}
		}
		// Recovery: uncordon only nodes WE cordoned, once healthy long enough.
		if !policy.Spec.DryRun {
			for _, v := range verdicts {
				if v.OwnedByPolicy && v.Healthy && v.Unschedulable {
					if err := r.uncordon(ctx, &policy, byName[v.Name]); err != nil {
						actErrs = append(actErrs, fmt.Errorf("uncordon %s: %w", v.Name, err))
					}
				}
			}
		}
	}
	for _, name := range blocked {
		r.Recorder.Eventf(&policy, corev1.EventTypeWarning, "BudgetExhausted",
			"node %s is unhealthy but maxUnavailableNodes=%d is reached; not acting", name, budget)
	}

	// Report.
	if err := r.updateStatus(ctx, &policy, nodes.Items, unhealthy, blocked, actErrs); err != nil {
		return ctrl.Result{}, err
	}
	if len(actErrs) > 0 {
		for _, e := range actErrs {
			logger.Error(e, "action failed")
		}
		return ctrl.Result{}, fmt.Errorf("%d actions failed; first: %w", len(actErrs), actErrs[0])
	}
	if requeue > 0 {
		return ctrl.Result{RequeueAfter: requeue + time.Second}, nil
	}
	return ctrl.Result{}, nil
}

func (r *GPUHealthPolicyReconciler) cordon(ctx context.Context, p *v1alpha1.GPUHealthPolicy, n *corev1.Node) error {
	patch := client.MergeFrom(n.DeepCopy())
	n.Spec.Unschedulable = true
	if n.Annotations == nil {
		n.Annotations = map[string]string{}
	}
	n.Annotations[AnnotationOwner] = p.Name
	n.Annotations[AnnotationReason] = fmt.Sprintf("%s=False", p.Spec.ConditionType)
	n.Annotations[AnnotationSince] = r.Clock.Now().UTC().Format(time.RFC3339)
	if err := r.Patch(ctx, n, patch); err != nil {
		return err
	}
	r.Recorder.Eventf(p, corev1.EventTypeWarning, "Cordoned", "cordoned node %s (%s=False)", n.Name, p.Spec.ConditionType)
	return nil
}

func (r *GPUHealthPolicyReconciler) uncordon(ctx context.Context, p *v1alpha1.GPUHealthPolicy, n *corev1.Node) error {
	patch := client.MergeFrom(n.DeepCopy())
	n.Spec.Unschedulable = false
	delete(n.Annotations, AnnotationOwner)
	delete(n.Annotations, AnnotationReason)
	delete(n.Annotations, AnnotationSince)
	if err := r.Patch(ctx, n, patch); err != nil {
		return err
	}
	r.Recorder.Eventf(p, corev1.EventTypeNormal, "Uncordoned", "node %s healthy again; uncordoned", n.Name)
	return nil
}

func (r *GPUHealthPolicyReconciler) releaseAll(ctx context.Context, p *v1alpha1.GPUHealthPolicy) error {
	var nodes corev1.NodeList
	if err := r.List(ctx, &nodes); err != nil {
		return err
	}
	for i := range nodes.Items {
		n := &nodes.Items[i]
		if n.Annotations[AnnotationOwner] == p.Name {
			if err := r.uncordon(ctx, p, n); err != nil {
				return err
			}
		}
	}
	return nil
}

// drain evicts evictable pods (respecting PDBs). It returns how many pods remain.
func (r *GPUHealthPolicyReconciler) drain(ctx context.Context, p *v1alpha1.GPUHealthPolicy, node string) (int, error) {
	var pods corev1.PodList
	if err := r.List(ctx, &pods, client.MatchingFields{podNodeNameIndex: node}); err != nil {
		return 0, err
	}
	remaining := 0
	var firstErr error
	for i := range pods.Items {
		pod := &pods.Items[i]
		if !evictable(pod) {
			continue
		}
		remaining++
		if !pod.DeletionTimestamp.IsZero() {
			continue // already terminating
		}
		ev := &policyv1.Eviction{ObjectMeta: metav1.ObjectMeta{Name: pod.Name, Namespace: pod.Namespace}}
		err := r.SubResource("eviction").Create(ctx, pod, ev)
		switch {
		case err == nil || apierrors.IsNotFound(err):
		case apierrors.IsTooManyRequests(err): // PDB disallows right now: expected, retry later
			r.Recorder.Eventf(p, corev1.EventTypeNormal, "EvictionBlocked", "eviction of %s/%s blocked by a PodDisruptionBudget", pod.Namespace, pod.Name)
		default:
			if firstErr == nil {
				firstErr = err
			}
		}
	}
	return remaining, firstErr
}

func evictable(pod *corev1.Pod) bool {
	if pod.Status.Phase == corev1.PodSucceeded || pod.Status.Phase == corev1.PodFailed {
		return false
	}
	if _, mirror := pod.Annotations[corev1.MirrorPodAnnotationKey]; mirror {
		return false
	}
	for _, o := range pod.OwnerReferences {
		if o.Kind == "DaemonSet" && o.Controller != nil && *o.Controller {
			return false
		}
	}
	return true
}

func (r *GPUHealthPolicyReconciler) updateStatus(ctx context.Context, p *v1alpha1.GPUHealthPolicy, nodes []corev1.Node,
	unhealthy int32, blocked []string, actErrs []error) error {
	var cordoned []string
	for _, n := range nodes {
		if n.Annotations[AnnotationOwner] == p.Name && n.Spec.Unschedulable {
			cordoned = append(cordoned, n.Name)
		}
	}
	sort.Strings(cordoned)

	orig := p.DeepCopy()
	p.Status.ObservedGeneration = p.Generation
	p.Status.MatchedNodes = int32(len(nodes))
	p.Status.UnhealthyNodes = unhealthy
	p.Status.CordonedNodes = cordoned

	ready := metav1.Condition{Type: conditionReady, Status: metav1.ConditionTrue, Reason: "Reconciled",
		Message: fmt.Sprintf("%d nodes matched, %d unhealthy, %d cordoned", len(nodes), unhealthy, len(cordoned)), ObservedGeneration: p.Generation}
	if len(actErrs) > 0 {
		ready.Status, ready.Reason, ready.Message = metav1.ConditionFalse, "ActionFailed", actErrs[0].Error()
	}
	meta.SetStatusCondition(&p.Status.Conditions, ready)

	bud := metav1.Condition{Type: conditionBlocked, Status: metav1.ConditionFalse, Reason: "WithinBudget", ObservedGeneration: p.Generation}
	if len(blocked) > 0 {
		bud.Status, bud.Reason = metav1.ConditionTrue, "BudgetExhausted"
		bud.Message = fmt.Sprintf("not acting on %v", blocked)
	}
	meta.SetStatusCondition(&p.Status.Conditions, bud)

	if equalStatus(orig.Status, p.Status) {
		return nil // avoid write churn / reconcile loops
	}
	return r.Status().Patch(ctx, p, client.MergeFrom(orig))
}

func equalStatus(a, b v1alpha1.GPUHealthPolicyStatus) bool {
	if a.ObservedGeneration != b.ObservedGeneration || a.MatchedNodes != b.MatchedNodes || a.UnhealthyNodes != b.UnhealthyNodes ||
		len(a.CordonedNodes) != len(b.CordonedNodes) || len(a.Conditions) != len(b.Conditions) {
		return false
	}
	for i := range a.CordonedNodes {
		if a.CordonedNodes[i] != b.CordonedNodes[i] {
			return false
		}
	}
	for i := range a.Conditions {
		x, y := a.Conditions[i], b.Conditions[i]
		if x.Type != y.Type || x.Status != y.Status || x.Reason != y.Reason || x.Message != y.Message || x.ObservedGeneration != y.ObservedGeneration {
			return false
		}
	}
	return true
}

func contains(ss []string, s string) bool {
	for _, x := range ss {
		if x == s {
			return true
		}
	}
	return false
}

// policiesForNode maps a Node event to the policies whose selector matches it.
func (r *GPUHealthPolicyReconciler) policiesForNode(ctx context.Context, obj client.Object) []reconcile.Request {
	var list v1alpha1.GPUHealthPolicyList
	if err := r.List(ctx, &list); err != nil {
		return nil
	}
	var reqs []reconcile.Request
	for i := range list.Items {
		p := &list.Items[i]
		if labels.SelectorFromSet(p.Spec.NodeSelector).Matches(labels.Set(obj.GetLabels())) || obj.GetAnnotations()[AnnotationOwner] == p.Name {
			reqs = append(reqs, reconcile.Request{NamespacedName: types.NamespacedName{Name: p.Name}})
		}
	}
	return reqs
}

// nodeChanged filters Node updates down to the ones that can change a decision.
func nodeChanged() predicate.Funcs {
	return predicate.Funcs{
		UpdateFunc: func(e event.UpdateEvent) bool {
			o, ok1 := e.ObjectOld.(*corev1.Node)
			n, ok2 := e.ObjectNew.(*corev1.Node)
			if !ok1 || !ok2 {
				return true
			}
			if o.Spec.Unschedulable != n.Spec.Unschedulable || !equalMap(o.Labels, n.Labels) || !equalMap(o.Annotations, n.Annotations) {
				return true
			}
			return !equalConditions(o.Status.Conditions, n.Status.Conditions)
		},
	}
}

func equalMap(a, b map[string]string) bool {
	if len(a) != len(b) {
		return false
	}
	for k, v := range a {
		if b[k] != v {
			return false
		}
	}
	return true
}

func equalConditions(a, b []corev1.NodeCondition) bool {
	if len(a) != len(b) {
		return false
	}
	for i := range a {
		// ignore heartbeat timestamps; only transitions and status/reason matter
		if a[i].Type != b[i].Type || a[i].Status != b[i].Status || a[i].Reason != b[i].Reason || !a[i].LastTransitionTime.Equal(&b[i].LastTransitionTime) {
			return false
		}
	}
	return true
}

// SetupWithManager wires watches and the pod index.
func (r *GPUHealthPolicyReconciler) SetupWithManager(mgr ctrl.Manager) error {
	if r.Clock == nil {
		r.Clock = clock.RealClock{}
	}
	if err := mgr.GetFieldIndexer().IndexField(context.Background(), &corev1.Pod{}, podNodeNameIndex,
		func(o client.Object) []string { return []string{o.(*corev1.Pod).Spec.NodeName} }); err != nil {
		return err
	}
	return ctrl.NewControllerManagedBy(mgr).
		Named("gpuhealthpolicy").
		For(&v1alpha1.GPUHealthPolicy{}, builder.WithPredicates(predicate.GenerationChangedPredicate{})).
		Watches(&corev1.Node{}, handler.EnqueueRequestsFromMapFunc(r.policiesForNode), builder.WithPredicates(nodeChanged())).
		Complete(r)
}
