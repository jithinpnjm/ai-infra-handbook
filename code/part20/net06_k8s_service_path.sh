#!/usr/bin/env bash
# Read-only walk down the Service path. Usage: net06_k8s_service_path.sh NAMESPACE SERVICE
# Order follows kubernetes.io "Debug Services": DNS, Service, EndpointSlices, Pods.
set -u
ns=${1:?namespace}; svc=${2:?service}
echo "== 1 service exists";      kubectl -n "$ns" get svc "$svc" -o wide
echo "== 2 endpoint slices (ENDPOINTS <none> means selector matches no ready pod)"
kubectl -n "$ns" get endpointslices -l "kubernetes.io/service-name=$svc"
echo "== 3 backing pods";        kubectl -n "$ns" get pods -o wide
echo "== 4 service ports vs targetPort"
kubectl -n "$ns" get svc "$svc" -o jsonpath='{range .spec.ports[*]}{.port}{" -> "}{.targetPort}{"\n"}{end}'
echo "== 5 CoreDNS pods";        kubectl -n kube-system get pods -l k8s-app=kube-dns
echo "== 6 kube-proxy pods";     kubectl -n kube-system get pods -l k8s-app=kube-proxy
echo "Next, from inside a pod: nslookup $svc.$ns ; then curl the ClusterIP ; then curl a pod IP."
