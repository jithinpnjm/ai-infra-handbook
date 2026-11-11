#!/usr/bin/env python3
"""Wrap a plain Prometheus rule file in a PrometheusRule object (Chapter 19.7).

The rule file stays the source of truth: promtool checks and tests it. This
script only moves its `groups` into spec.groups so the Prometheus Operator can
load it. Needs PyYAML.

Usage: python3 c07_prometheusrule.py RULES.yaml NAME [NAMESPACE] > rule.yaml
"""
import sys

import yaml


def wrap(rule_text, name, namespace="monitoring"):
    doc = yaml.safe_load(rule_text)
    if not isinstance(doc, dict) or "groups" not in doc:
        raise ValueError("input is not a Prometheus rule file: no top-level 'groups'")
    return {
        "apiVersion": "monitoring.coreos.com/v1",
        "kind": "PrometheusRule",
        "metadata": {"name": name, "namespace": namespace,
                     "labels": {"app.kubernetes.io/part-of": "gpu-platform-observability"}},
        "spec": {"groups": doc["groups"]},
    }


def main(argv):
    if len(argv) not in (3, 4):
        print(__doc__)
        return 2
    text = open(argv[1]).read()
    obj = wrap(text, argv[2], argv[3] if len(argv) == 4 else "monitoring")
    sys.stdout.write(yaml.safe_dump(obj, sort_keys=False, width=100))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
