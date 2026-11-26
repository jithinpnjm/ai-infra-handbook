#!/usr/bin/env python3
import re

expected_labels = [
    "resourceVersion versus generation versus observedGeneration",
    "metadata.resourceVersion",
    "metadata.generation",
    "status.observedGeneration",
    "resourceVersion changes on every write (metadata, spec or status)",
    "generation increments only when spec changes",
    "observedGeneration is written by the controller to record the generation it last reconciled",
    "spec edit",
    "label edit",
    "status write by controller",
    "controller finishes reconcile",
    "controller has not caught up",
    "status reflects the latest spec",
    "resourceVersion is opaque, compare only for equality, derived from the etcd mod_revision",
    "uid identifies one instance; a recreated object gets a new uid",
    "kubectl rollout status uses this"
]

step_numbers = {"1", "2", "3", "4"}

print(f"Total expected labels: {len(expected_labels)}")
print(f"Step numbers: {len(step_numbers)}")
print(f"Total expected text elements: {len(expected_labels) + len(step_numbers)}")
