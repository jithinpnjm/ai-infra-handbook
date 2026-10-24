package v1alpha1

import (
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/util/intstr"
)

// Action is what the controller does with an unhealthy node.
// +kubebuilder:validation:Enum=Ignore;Cordon;CordonAndDrain
type Action string

const (
	ActionIgnore         Action = "Ignore"
	ActionCordon         Action = "Cordon"
	ActionCordonAndDrain Action = "CordonAndDrain"
)

// GPUHealthPolicySpec defines the desired behaviour.
// +kubebuilder:validation:XValidation:rule="self.action != 'CordonAndDrain' || has(self.maxUnavailableNodes)",message="maxUnavailableNodes is required when action is CordonAndDrain"
type GPUHealthPolicySpec struct {
	// NodeSelector selects the nodes covered by this policy (labels).
	// +optional
	NodeSelector map[string]string `json:"nodeSelector,omitempty"`

	// ConditionType is the node condition that reports GPU health; the node is unhealthy when its status is False.
	// +kubebuilder:default=GPUHealthy
	ConditionType string `json:"conditionType,omitempty"`

	// UnhealthyFor is how long the condition must stay False before acting.
	// +kubebuilder:default="2m"
	UnhealthyFor metav1.Duration `json:"unhealthyFor,omitempty"`

	// HealthyFor is how long a node must stay healthy before the controller uncordons a node it cordoned.
	// +kubebuilder:default="5m"
	HealthyFor metav1.Duration `json:"healthyFor,omitempty"`

	// Action to take for unhealthy nodes.
	// +kubebuilder:default=Cordon
	Action Action `json:"action,omitempty"`

	// MaxUnavailableNodes bounds how many nodes this policy may hold cordoned at once (count or percentage of matched nodes).
	// +optional
	MaxUnavailableNodes *intstr.IntOrString `json:"maxUnavailableNodes,omitempty"`

	// DryRun reports what would happen without changing nodes.
	// +optional
	DryRun bool `json:"dryRun,omitempty"`
}

// GPUHealthPolicyStatus defines the observed state.
type GPUHealthPolicyStatus struct {
	// +optional
	ObservedGeneration int64 `json:"observedGeneration,omitempty"`
	// +optional
	MatchedNodes int32 `json:"matchedNodes,omitempty"`
	// +optional
	UnhealthyNodes int32 `json:"unhealthyNodes,omitempty"`
	// +optional
	CordonedNodes []string `json:"cordonedNodes,omitempty"`
	// +optional
	// +listType=map
	// +listMapKey=type
	Conditions []metav1.Condition `json:"conditions,omitempty"`
}

// +kubebuilder:object:root=true
// +kubebuilder:subresource:status
// +kubebuilder:resource:scope=Cluster,shortName=ghp,categories=platform
// +kubebuilder:printcolumn:name="Action",type=string,JSONPath=`.spec.action`
// +kubebuilder:printcolumn:name="Matched",type=integer,JSONPath=`.status.matchedNodes`
// +kubebuilder:printcolumn:name="Unhealthy",type=integer,JSONPath=`.status.unhealthyNodes`
// +kubebuilder:printcolumn:name="Ready",type=string,JSONPath=`.status.conditions[?(@.type=="Ready")].status`
// +kubebuilder:printcolumn:name="Age",type=date,JSONPath=`.metadata.creationTimestamp`

// GPUHealthPolicy is the Schema for the gpuhealthpolicies API.
type GPUHealthPolicy struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`

	Spec   GPUHealthPolicySpec   `json:"spec,omitempty"`
	Status GPUHealthPolicyStatus `json:"status,omitempty"`
}

// +kubebuilder:object:root=true

// GPUHealthPolicyList contains a list of GPUHealthPolicy.
type GPUHealthPolicyList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty"`
	Items           []GPUHealthPolicy `json:"items"`
}

func init() {
	SchemeBuilder.Register(&GPUHealthPolicy{}, &GPUHealthPolicyList{})
}
