---
id: "c05-12"
title: "5.12 Ingress, load balancers and the Gateway API"
sidebar_label: "5.12 Ingress, load balancers and the Gateway API"
sidebar_position: 12
description: "Getting traffic into a cluster: L4 and L7 load balancing, Ingress resources and controllers, the Gateway API (GatewayClass, Gateway, HTTPRoute, GRPCRoute), TLS and cert-manager, bare-metal load balancers, timeouts/streaming for LLM traffic, rate limiting, auth, and operating the edge for inference services"
status: "drafted"
tier: "0"
level: "I"
lab_venue: "GCP / GKE"
---

# 5.12 Ingress, load balancers and the Gateway API

| | |
|---|---|
| Level | Intermediate |
| Priority tier | 1 |
| Lab venue | Cluster with a LoadBalancer implementation (cloud or MetalLB); Helm; curl/hey/fortio |
| Part | Part 5: Kubernetes |
| Status | Drafted, labs **untested** |

## Why this matters for AI infrastructure

Suppose your team has just put a model behind an endpoint, and users report that long answers stop halfway through. The cause often sits at the edge, the point where traffic first enters the cluster. Inference endpoints, notebooks, experiment trackers, dashboards, model registries and internal tools all need a controlled entry point. That entry point handles TLS and authentication. It routes requests by hostname, path or header, for example by model name or tenant.

It also splits traffic between model versions for canary and A/B tests. Long-running answers need long timeouts and streaming. Token streaming can use Server-Sent Events, WebSockets or gRPC. The edge also applies rate limiting per API key and exposes metrics.

The edge is also where AI-specific problems appear. A default 60-second proxy timeout can kill a long generation. Request buffering can break token streaming. Body size limits can reject large prompts or image batches. HTTP/2 connection reuse can produce uneven load. Cache-/KV-aware routing needs go beyond what classic L7 balancers can meet.

This chapter covers the Kubernetes mechanisms, Ingress and the newer Gateway API, along with the controllers behind them. It also covers TLS automation and the operational design of an edge for inference traffic.

## Prerequisites and outcomes

You will need 5.10, 5.11, and the HTTP/TLS fundamentals in 2.10 and 2.20 before you start. After this chapter, you will be able to:

- Contrast L4 and L7 load balancing, and place Service types, Ingress, the Gateway API and external load balancers in the right layer.
- Write Ingress resources with hosts, paths, TLS, annotations and IngressClass, and operate popular controllers such as ingress-nginx, Traefik, HAProxy, Envoy-based controllers and cloud controllers.
- Use the Gateway API, including its roles, GatewayClass, Gateway, HTTPRoute, GRPCRoute, TLSRoute and ReferenceGrant, along with traffic splitting, header matching and filters. You will also compare it with Ingress.
- Automate TLS with cert-manager, using ACME or an internal CA, and secure the edge with mTLS, OAuth/OIDC auth, a WAF, rate limiting and control over network exposure.
- Provide bare-metal load balancing with MetalLB in L2 or BGP mode, kube-vip or Cilium LB IPAM, and understand how cloud load balancers integrate.
- Tune for LLM and streaming workloads, covering timeouts, buffering, HTTP/2, connection draining, body size and retries. You will also know when to use AI-aware gateways.
- Diagnose edge failures, including 502/503/504 errors, TLS errors and wrong routing.

## 1. Layers of load balancing

A request passes through several layers before it reaches your model. Each layer makes a different kind of decision, so knowing which layer acted tells you where to look. The diagram shows that path.

```mermaid
flowchart LR
  C["Clients (Internet / corp / apps)"] --> EDGE["Edge: DNS → external L4 LB or anycast/VIP\n(cloud NLB, MetalLB, hardware LB)"]
  EDGE --> GW["L7 gateway pods in cluster\n(ingress-nginx / Envoy / Traefik / Cilium Gateway)"]
  GW -->|"route by host/path/header,\nTLS termination, auth, rate limit"| SVC["Service (ClusterIP / headless)"]
  SVC --> P1["Pod A (model v1)"]
  SVC --> P2["Pod B (model v1)"]
  GW -.->|"canary 5%"| SVC2["Service model-v2"]
```

Notice that the 5% canary branch leaves the gateway for a separate Service, model-v2.

L4 (TCP/UDP) balancing spreads connections without looking at the protocol. Services covered in 5.10, `type: LoadBalancer`, cloud NLBs, MetalLB and IPVS all work this way. It is fast and protocol-agnostic. However, it cannot route by URL or retry a single request, and long-lived connections stick.

L7 (HTTP and gRPC) balancing terminates the protocol and makes a decision for each request. It can route by host, path or header, retry, set timeouts, apply circuit breaking, rate limit, authenticate and rewrite. It can even balance individual requests over HTTP/2.

A typical stack has three parts. An external L4 load balancer gives you one stable IP. Behind it sits an L7 gateway Deployment or DaemonSet, which forwards to Services and then to pods. Cloud L7 load balancers, such as ALB or the GCP HTTP(S) LB, can skip the node hops by routing straight to pods with NEG/IP targets.

When traffic goes wrong, decide first whether the L4 layer or the L7 layer made the decision.

## 2. Ingress

Suppose one hostname has to reach a chat model while a second hostname reaches a different service. Something must read each request's host and path, then pick the right backend. In Kubernetes, that job belongs to an Ingress.

An **Ingress** declares L7 routing rules, and its API group and version is `networking.k8s.io/v1`. An **Ingress controller** does the actual work. It is a separate deployment that you install. The controller watches Ingress objects and configures a proxy from them. Kubernetes ships no controller by default. `IngressClass` selects which controller handles an Ingress, through `spec.ingressClassName`.

Read the example below as a whole. The annotations tune timeouts, body size and rate limits, and the `tls` block points at a Secret that cert-manager creates and renews.

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: llm-api
  namespace: serving
  annotations:                                   # controller-specific behaviour (ingress-nginx examples)
    nginx.ingress.kubernetes.io/proxy-read-timeout: "600"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "600"
    nginx.ingress.kubernetes.io/proxy-body-size: "64m"
    nginx.ingress.kubernetes.io/proxy-buffering: "off"          # token streaming (SSE)
    nginx.ingress.kubernetes.io/limit-rps: "20"
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  ingressClassName: nginx
  tls:
    - hosts: [llm.example.com]
      secretName: llm-example-tls                # cert-manager creates and renews this Secret
  rules:
    - host: llm.example.com
      http:
        paths:
          - path: /v1/chat
            pathType: Prefix                      # Exact | Prefix | ImplementationSpecific
            backend:
              service: { name: vllm, port: { number: 80 } }
          - path: /v1/embeddings
            pathType: Prefix
            backend:
              service: { name: embeddings, port: { name: http } }
```

Ingress itself covers virtual hosting by `Host`, path routing with `Exact` and `Prefix` matches, and TLS termination through Secrets that hold `tls.crt` and `tls.key`. It also has a default backend. Everything else, such as rewrites, redirects, auth, rate limits, timeouts, canary, CORS and WAF, is a controller-specific annotation. Annotations are not portable and carry no types. That is the main reason the Gateway API exists. The Ingress API is frozen, so it gets no new features.

Four operational details of Ingress routing matter in practice. *Kubernetes: Up and Running*, Chapter 8, and *Networking and Kubernetes*, Chapters 5 & 6, both describe them.

The first detail is that paths reach the backend unmodified by default. Suppose a client requests `bandicoot.example.com/a/` and that matches the Ingress path rule `path: /a`. The proxy forwards the request with the `/a/` path intact, as `GET /a/ HTTP/1.1`. If the backend expects requests at `/` instead of `/a/`, it returns `404 Not Found`. The fix is path rewriting, set with an Ingress controller annotation such as `nginx.ingress.kubernetes.io/rewrite-target` or a Gateway API `URLRewrite` filter.

The second detail is precedence between path rules. Suppose an Ingress or `HTTPRoute` has a `Prefix` rule for `/v1` and an `Exact` rule for `/v1/health`, and both match a request. The `Exact` match always wins. Among `Prefix` rules, the longest matching prefix wins, as the model in `evaluate_httproute_and_reference_grant()` in `code/part05/gateway_llm_router.py` shows.

The third detail concerns defaults. Marking an `IngressClass` with `ingressclass.kubernetes.io/is-default-class: "true"` makes it handle any Ingress that omits `spec.ingressClassName`. Setting `spec.defaultBackend` handles requests that match no `rules` host or path.

The fourth detail is cloud container-native load balancing. On GKE, Network Endpoint Groups, or NEGs, let the cloud load balancer watch Pod IPs directly. On AWS EKS, the AWS Load Balancer Controller does the same when you set `alb.ingress.kubernetes.io/target-type: ip`. Traffic then runs from the cloud edge straight to Pod IPs, skipping `NodePort` and `kube-proxy` hops. The cloud load balancer also integrates with Google Cloud Armor, Cloud CDN and IAP, or with AWS WAF.

### Why Ingress has no default controller

Ingress works differently from most Kubernetes objects. The object is only a specification, and a separate controller implements it. You can create and change Ingress objects like any other object. By default, though, no code acts on them. So you or your distribution must install and manage a controller. That split is what makes the controller pluggable.

Kubernetes leaves the choice open because no single HTTP load balancer suits every setup. Teams run open source proxies, cloud load balancers such as ELB on AWS, and hardware appliances. The Ingress object also arrived before Kubernetes had its common extension features, which are covered in Chapter 17. It will likely change to use them over time.

### Installing Contour

The examples in this chapter use Contour. It configures Envoy, an open source CNCF load balancer that you can change on the fly through an API. Contour translates Ingress objects into a form Envoy understands. The project began at Heptio with real customers and runs in production today. It is now an independent open source project.

You can install Contour with one line:

```
$ kubectl apply -f https://projectcontour.io/quickstart/contour.yaml
```

Run the install as a user with `cluster-admin` permissions. The single line works for most configurations. It creates a namespace called `projectcontour` and a Deployment with two replicas. It also creates an external-facing Service of `type: LoadBalancer`, sets up permissions through a service account, and installs a CustomResourceDefinition for the extra features covered in "The Future of Ingress."

Because the install is global, it needs wide admin rights on the cluster. When it finishes, look up the external address of Contour:

```
$ kubectl get -n projectcontour service envoy -o wide
NAME CLUSTER-IP EXTERNAL-IP PORT(S) ...
contour 10.106.53.14 a477...amazonaws.com 80:30274/TCP ...
```

Look at the `EXTERNAL-IP` column. On GCP and Azure it holds an IP address, and on AWS it holds a hostname. Other clouds may differ. If your cluster does not support `type: LoadBalancer`, change the Contour YAML to use `type: NodePort`, and send traffic to the cluster machines another way.

With `minikube`, the `EXTERNAL-IP` column will probably stay empty. Open a second terminal and run `minikube tunnel`. The tunnel sets up network routes, so every Service of `type: LoadBalancer` gets its own unique IP address.

### Pointing DNS names at the controller

People reach sites by name, not by IP address, and many hostnames can share one external endpoint. The Ingress controller then uses the hostname to send each request to the right upstream service.

The examples assume a domain called `example.com`. You need two DNS entries, `alpaca.example.com` and `bandicoot.example.com`. If the external load balancer gives you an IP address, create A records. If it gives you a hostname instead, create CNAME records.

ExternalDNS can manage these records for you. It is a cluster add-on that keeps the IP addresses of Kubernetes Service resources in sync with an external DNS provider. It works with traditional domain registrars as well as public cloud providers.

### Testing with a local hosts file

If you have no domain, or you use a local tool such as `minikube`, you can point the names at the controller in your hosts file. Editing that file needs admin or root rights. Its location differs by platform, and the change may need extra steps to take effect. On Windows the file is usually at `C:\Windows\System32\drivers\etc\hosts`. On recent versions of macOS, run `sudo killall -HUP mDNSResponder` after you change it.

Add a line like this one, with the external IP address of Contour:

```
<ip-address> alpaca.example.com bandicoot.example.com
```

If all you have is a hostname, as on AWS, run `host -t a <address>` to get an IP address. That address may change later, so remove the line when you are done.

### Creating three sample services

Before you route anything, you need upstream services to send traffic to. The book calls these backends. The next commands create three Deployments of the same `kuard` app. Each one runs three replicas on port 8080. The images differ only by tag: `blue`, `green` and `purple`. Each Deployment also gets a Service.

```
$ kubectl create deployment be-default \
--image=gcr.io/kuar-demo/kuard-amd64:blue \
--replicas=3 \
--port=8080
$ kubectl expose deployment be-default
$ kubectl create deployment alpaca \
--image=gcr.io/kuar-demo/kuard-amd64:green \
--replicas=3 \
--port=8080
$ kubectl expose deployment alpaca
$ kubectl create deployment bandicoot \
--image=gcr.io/kuar-demo/kuard-amd64:purple \
--replicas=3 \
--port=8080
$ kubectl expose deployment bandicoot
$ kubectl get services -o wide
NAME CLUSTER-IP ... PORT(S) ... SELECTOR
alpaca 10.115.245.13 ... 8080/TCP ... run=alpaca
bandicoot 10.115.242.3 ... 8080/TCP ... run=bandicoot
be-default 10.115.246.6 ... 8080/TCP ... run=be-default
kubernetes 10.115.240.1 ... 443/TCP ... <none>
```

### Simplest Ingress: send everything to one service

The simplest use of Ingress is to pass everything it sees to one upstream service. `kubectl` has only limited commands for Ingress, so you start with a YAML file.

Example 8-1. `simple-ingress.yaml`

```
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
name: simple-ingress
spec:
defaultBackend:
service:
name: alpaca
port:
number: 8080
```

Create it with `kubectl apply`:

```
$ kubectl apply -f simple-ingress.yaml
ingress.extensions/simple-ingress created
```

Check the result with `kubectl get` and `kubectl describe`:

```
$ kubectl get ingress
NAME HOSTS ADDRESS PORTS AGE
simple-ingress * 80 13m
$ kubectl describe ingress simple-ingress
Name: simple-ingress
Namespace: default
Address:
Default backend: alpaca:8080
(172.17.0.6:8080,172.17.0.7:8080,172.17.0.8:8080)
Rules:
Host Path Backends
---- ---- --------
* * alpaca:8080 (172.17.0.6:8080,172.17.0.7:8080,172.17.0.8:8080)
Annotations:
...
Events: <none>
```

With this file, every HTTP request that reaches the controller goes to the `alpaca` service. You can reach it through any of the raw IPs or CNAMEs, which here means either `alpaca.example.com` or `bandicoot.example.com`. On its own, this adds little over a plain Service of `type: LoadBalancer`. The next sections try more complex setups.

### Routing by hostname

Ingress gets useful when it routes on something in the request. The most common case is the HTTP `Host` header, which carries the DNS name from the original URL. Example 8-2 adds a second Ingress that sends traffic for `alpaca.example.com` to the `alpaca` service.

Example 8-2. `host-ingress.yaml`

```
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
name: host-ingress
spec:
defaultBackend:
service:
name: be-default
port:
number: 8080
rules:
- host: alpaca.example.com
http:
paths:
- pathType: Prefix
path: /
backend:
service:
name: alpaca
port:
number: 8080
```

Create it with `kubectl apply`:

```
$ kubectl apply -f host-ingress.yaml
ingress.extensions/host-ingress created
```

Check that it is set up correctly:

```
$ kubectl get ingress
NAME HOSTS ADDRESS PORTS AGE
host-ingress alpaca.example.com 80 54s
simple-ingress * 80 13m
$ kubectl describe ingress host-ingress
Name: host-ingress
Namespace: default
Address:
Default backend: be-default:8080 (<none>)
Rules:
Host Path Backends
---- ---- --------
alpaca.example.com
/ alpaca:8080 (<none>)
Annotations:
...
Events: <none>
```

Two things in this output look odd. The first is the reference to `default-http-backend`. Some Ingress controllers send any request they cannot handle elsewhere to a service with that name in the `kube-system` namespace. `kubectl` simply shows you that convention. The second is that no endpoints appear for the `alpaca` backend. That is a `kubectl` bug, fixed in Kubernetes v1.14.

You should now reach the `alpaca` service at `http://alpaca.example.com`. Reach it by any other method, and you get the default service instead.

### Routing by path

Routing on the path as well as the hostname comes next. You add a `path` to the `paths` entry. Example 8-3 sends everything for `bandicoot.example.com` to the `bandicoot` service, and it sends `bandicoot.example.com/a` to the `alpaca` service. You can use this to host several services on different paths of one domain.

Example 8-3. `path-ingress.yaml`

```
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
name: path-ingress
spec:
rules:
- host: bandicoot.example.com
http:
paths:
- pathType: Prefix
path: "/"
backend:
service:
name: bandicoot
port:
number: 8080
- pathType: Prefix
path: "/a/"
backend:
service:
name: alpaca
port:
number: 8080
```

When several paths on the same host match, the longest prefix wins. Here, traffic that starts with `/a/` goes to the `alpaca` service. All other traffic, which starts with `/`, goes to the `bandicoot` service.

The proxy does not change the path as it forwards the request. A request to `bandicoot.example.com/a/` therefore reaches the upstream server with the same path, so the upstream service must be ready to serve that subpath. The `kuard` app has special test code for this. It answers on the root path, `/`, and on a fixed set of subpaths: `/a/`, `/b/` and `/c/`.

### Cleaning up the sample

To remove the sample objects, run:

```
$ kubectl delete ingress host-ingress path-ingress simple-ingress
$ kubectl delete service alpaca bandicoot be-default
$ kubectl delete deployment alpaca bandicoot be-default
```

### Annotations and gotchas

Ingress supports other advanced features too. How well each one works depends on the controller, and two controllers may implement the same feature in slightly different ways. Many of these features are set through annotations on the Ingress object. Annotations are easy to get wrong and hard to validate, and they apply to the whole object, so they can reach further than you intended. To narrow their scope, split one Ingress object into several. The controller reads them all and merges them together.

When you create more than one Ingress object, the controllers should read them all and merge them into one config. Duplicate or conflicting settings, however, have undefined behavior. Different controllers may handle the same conflict differently. Even one controller may behave differently depending on factors that are not obvious.

### Ingress and namespaces

Ingress interacts with namespaces in a few non-obvious ways. For security reasons, an Ingress object can point only at an upstream service in its own namespace. So one Ingress object cannot send a subpath to a service in another namespace.

Ingress objects in different namespaces can, however, define subpaths for the same host. The controller merges them into one final config. Ingress therefore has to be coordinated across the whole cluster. If one namespace is careless, its Ingress object can cause problems, or undefined behavior, in the others.

By default, the Ingress controller does not restrict which namespaces may claim which hostnames and paths. Advanced users may try to enforce a policy with a custom admission controller. The evolutions of Ingress covered in "The Future of Ingress" also address this problem.

### Path rewriting

Some Ingress controllers can rewrite the path while they proxy a request. You usually set this with an annotation on the Ingress object, and it applies to every request that object handles. With the NGINX Ingress controller, for example, you set `nginx.ingress.kubernetes.io/rewrite-target: /`. Rewriting lets an upstream service work on a subpath, even when the service was not built for one.

Several implementations go further and accept regular expressions in the path. The NGINX controller, for instance, can capture parts of the path and reuse them when it rewrites. How that works, and which regular expression variant it uses, depends on the implementation.

Rewriting is not a silver bullet, though, and it often causes bugs. Many web apps link to themselves with absolute paths. Suppose an app served on `/subpath` receives its requests on `/`, then sends a user to `/app-path`. It is unclear whether that link is internal, and if it is, it should be `/subpath/app-path`. It could also point to a different app. For that reason, avoid subpaths for complicated applications when you can.

### Serving TLS

Secure HTTPS is now the norm for websites. Ingress supports TLS, as do most Ingress controllers. First, you give Ingress a Secret that holds your certificate and private key, and Example 8-4 shows its shape. You can also create the Secret from the command line with `kubectl create secret tls <secret-name> --cert <certificate-pem-file> --key <private-key-pem-file>`.

Example 8-4. `tls-secret.yaml`

```
apiVersion: v1
kind: Secret
metadata:
creationTimestamp: null
name: tls-secret-name
type: kubernetes.io/tls
data:
tls.crt: <base64 encoded certificate>
tls.key: <base64 encoded private key>
```

Once the Secret exists, an Ingress object references it. The Ingress lists each certificate together with the hostnames it should serve, as Example 8-5 shows. If several Ingress objects name certificates for the same hostname, the behavior is undefined.

Example 8-5. `tls-ingress.yaml`

```
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
name: tls-ingress
spec:
tls:
- hosts:
- alpaca.example.com
secretName: tls-secret-name
rules:
- host: alpaca.example.com
http:
paths:
- backend:
serviceName: alpaca
servicePort: 8080
```

Uploading and managing TLS secrets by hand is hard, and certificates can cost a lot. Let's Encrypt helps here. It is a nonprofit that runs a free, API-driven Certificate Authority, so a cluster can fetch and install certificates automatically. Setup is tricky, but it is very simple to use once it works. The missing piece is cert-manager, an open source project created by Jetstack, a UK startup, and since onboarded to the CNCF. The cert-manager.io website and GitHub repository explain how to install it.

### Where Ingress is heading

Ingress is a useful abstraction for configuring L7 load balancers, but it has not grown to cover every feature users want. Various implementations want to offer more. Many Ingress features are underdefined, so each implementation may expose them differently. That lowers the portability of configurations between implementations.

Ingress is also easy to misconfigure. Multiple objects can combine into conflicts, and implementations resolve those conflicts differently. Merging objects across namespaces also breaks the idea of namespace isolation.

Ingress arrived before the service mesh idea, which projects such as Istio and Linkerd made well known. How Ingress and service meshes should fit together is still being worked out. Chapter 15 covers service meshes in more detail.

The future of HTTP load balancing in Kubernetes looks like the Gateway API. The Kubernetes networking special interest group, or SIG, is developing it to provide a more modern API for routing. It focuses on HTTP, but it also includes resources for Layer 4 TCP balancing. The Gateway APIs are still under development, so for now stick to the Ingress and Service resources that exist in Kubernetes today.

### Controllers

The table lists the common controllers and the proxy each one uses.

| Controller | Proxy | Notes |
|---|---|---|
| **ingress-nginx** (Kubernetes community) | NGINX | Most common; huge annotation set; snippet annotations are risky (disable `allow-snippet-annotations`); retired/limited maintenance should be checked for your timeline |
| NGINX Inc. Ingress Controller / NGINX Gateway Fabric | NGINX / NGINX Plus | Commercial option, Gateway API-based fabric |
| **Traefik** | Traefik | Dynamic config, CRDs (IngressRoute), middlewares |
| **HAProxy Ingress** | HAProxy | High performance, rich TCP features |
| **Envoy-based**: Contour, Emissary, Envoy Gateway, Istio ingress gateway, Cilium Gateway/Ingress | Envoy | xDS dynamic config, gRPC/HTTP2 first-class, good observability; foundation for Gateway API implementations and meshes |
| **Cloud**: AWS Load Balancer Controller (ALB/NLB), GKE Ingress/Gateway, AGIC (Azure) | Cloud LB | Managed, integrates with WAF/IAM; may route to pod IPs |
| **Kong, Apache APISIX, Ambassador** | Envoy/NGINX | API gateway features: plugins, auth, rate limiting, developer portals |

Read the notes column before you pick one. It flags risky snippet annotations and maintenance status.

You can run the controller as an autoscaled Deployment, or as a DaemonSet that uses `hostNetwork` or a NodePort with an external load balancer. Give it dedicated nodes when traffic is heavy. Set resource requests, a PDB, anti-affinity, `terminationGracePeriodSeconds` and a lifecycle so the controller drains gracefully. Finally, expose metrics for Prometheus and write access logs as structured JSON to stdout.

### Multi-team Ingress collisions and Contour's `HTTPProxy` root inclusion

In a multi-tenant cluster, the standard `Ingress` API does not stop two teams in different namespaces from claiming the same `host`. The book's example uses `app.bearcanoe.com`. Depending on the controller, overlapping rules are either merged in surprising ways or rejected, and either can cause production outages. As *Production Kubernetes*, Chapter 6, describes, platform teams solve this in one of two ways.

The first way is validating admission control. An Open Policy Agent or Gatekeeper policy, for example, checks existing `Ingress` objects across the cluster and rejects duplicate hostnames.

The second way is delegated routing with a custom resource such as Contour's `HTTPProxy`. Contour replaces flat `Ingress` objects with a root `HTTPProxy` custom resource that uses inclusion, set with `includes`. A platform administrator creates a root `HTTPProxy` in an administrative namespace. That root owns a domain, such as `app1.bearcanoe.com`, and delegates routing for that domain or path prefix by including `HTTPProxy` resources from the `app1` team's namespace. Only the root namespace can define top-level virtual hosts, so teams cannot collide with another team's hostname.

Contour's `HTTPProxy` also supports layer 3/4 TCP proxying through TLS Server Name Indication (`SNI`). The book's example (untested here) looks like this:

```yaml
apiVersion: projectcontour.io/v1
kind: HTTPProxy
metadata:
  name: tcp-proxy
spec:
  virtualhost:
    fqdn: tcp.bearcanoe.com
    tls:
      secretName: secret
  tcpproxy:
    services:
      - name: tcp-app
        port: 8080
```

### Dedicated Ingress node pool and DaemonSet edge pattern

Kubernetes does not isolate network I/O or file descriptors with cgroups. So a noisy application pod can contend with Ingress proxies when both share general worker nodes. *Production Kubernetes*, Chapter 6, recommends reserving a dedicated set of edge nodes for the Ingress tier. It uses four settings together.

The first setting is node labels, taints and a `DaemonSet`. Label and taint the dedicated ingress nodes, then deploy the Ingress controller as a `DaemonSet` with a matching `nodeSelector` and taint `tolerations`. A small, fixed set of edge nodes also simplifies firewall exceptions and static backend pools on hardware load balancers.

The second setting is host networking with `hostNetwork: true` and `ClusterFirstWithHostNet`. Binding the Ingress proxy container directly to the node's network namespace lets incoming packets reach the proxy without traversing the Kubernetes Service `iptables`/`IPVS` fabric. When `hostNetwork: true` is enabled, you must set `dnsPolicy: ClusterFirstWithHostNet`. That lets the proxy still resolve in-cluster `*.svc.cluster.local` Service names through CoreDNS, as in the book's Pod template snippet (untested here):

```yaml
spec:
  containers:
    - image: nginx
      name: nginx
  dnsPolicy: ClusterFirstWithHostNet
  hostNetwork: true
```

The third setting is `externalTrafficPolicy: Local` on the Service. Use it when the Ingress controller is exposed through a `NodePort` or `LoadBalancer` Service rather than direct host ports. External load balancers then send traffic only to nodes that run a local Ingress proxy replica. That avoids an extra cross-node hop, and the client's source IP address is preserved with no SNAT.

The fourth setting is spreading the replicas across failure domains. When you run a `Deployment`, or select nodes across zones, use Pod anti-affinity rules to spread Ingress controller replicas across availability zones or racks.

If heavy traffic shares nodes with application pods, give the Ingress tier its own nodes first.

## 3. Gateway API

The Gateway API is the successor to Ingress. It is role-oriented, expressive, portable and extensible. It covers L4 and L7 traffic, and it also covers gateways for service meshes, which the project calls GAMMA. Its HTTP features reached GA in v1. The table lists each resource and the person who usually owns it.

| Resource | Owner persona | Purpose |
|---|---|---|
| **GatewayClass** | Infrastructure provider | Names a controller implementation (like StorageClass/IngressClass) |
| **Gateway** | Cluster operator | A deployed listener set: addresses, ports, protocols, TLS, allowed routes (namespaces/selectors) |
| **HTTPRoute / GRPCRoute** | App developer | Hostnames, matches (path, headers, query, method), filters (redirect, rewrite, header modification, mirror, CORS/timeouts in newer releases), backendRefs with weights |
| **TLSRoute / TCPRoute / UDPRoute** | App developer | L4 routing (experimental/standard by release) |
| **ReferenceGrant** | Namespace owner | Permit cross-namespace references (route → Service in another namespace; Gateway → Secret) |
| **BackendTLSPolicy, BackendLBPolicy, policy attachment** | Operator/developer | Backend TLS, load balancing policy, timeouts (via policy attachment pattern; evolving) |

Notice that each resource has a different owner. The infrastructure provider names the controller, the cluster operator defines the Gateway, and the app developer writes the routes. The example below shows how these pieces fit together in a canary split and a redirect.

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: GatewayClass
metadata: { name: envoy }
spec: { controllerName: gateway.envoyproxy.io/gatewayclass-controller }
---
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata: { name: public, namespace: edge }
spec:
  gatewayClassName: envoy
  listeners:
    - name: https
      protocol: HTTPS
      port: 443
      hostname: "*.ai.example.com"
      tls:
        mode: Terminate
        certificateRefs: [ { name: wildcard-ai-example-com } ]
      allowedRoutes:
        namespaces: { from: Selector, selector: { matchLabels: { gateway-access: public } } }
---
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata: { name: chat, namespace: serving }
spec:
  parentRefs: [ { name: public, namespace: edge, sectionName: https } ]
  hostnames: ["chat.ai.example.com"]
  rules:
    - matches:
        - path: { type: PathPrefix, value: /v1 }
          headers: [ { name: x-model, value: llama-70b } ]
      backendRefs:
        - { name: vllm-llama70b-v1, port: 80, weight: 95 }       # canary: 95/5 split
        - { name: vllm-llama70b-v2, port: 80, weight: 5 }
      timeouts: { request: 600s, backendRequest: 600s }
      filters:
        - type: RequestHeaderModifier
          requestHeaderModifier: { add: [ { name: x-served-by, value: gateway } ] }
    - matches: [ { path: { type: PathPrefix, value: /healthz } } ]
      filters:
        - type: RequestRedirect
          requestRedirect: { scheme: https, statusCode: 301 }
```

The Gateway sits in the `edge` namespace and accepts HTTPS for `*.ai.example.com`. The `chat` route in the `serving` namespace attaches to it. It sends `/v1` traffic 95/5 between two model versions, and it adds a header to each request. It also redirects `/healthz` to HTTPS with status 301.

Compared with Ingress, the Gateway API replaces annotations with typed fields. Header matches, weights, redirects, mirroring and timeouts are all fields you can read and check. Roles are separated as well. Cluster operators own Gateways, and teams own Routes under RBAC. Cross-namespace references need a ReferenceGrant, which keeps them safe. Gateways and Routes also report status conditions, `Accepted`, `ResolvedRefs` and `Programmed`, that tell you why a route is not working. The same API runs on many implementations, including Envoy Gateway, Istio, Cilium, Contour, NGINX Gateway Fabric, Traefik, Kong, and the GKE, AWS and Azure offerings.

Migration can start with a tool such as `ingress2gateway`, which converts Ingresses. Run both in parallel during migration, using different IPs or hostnames. Map annotations to filters and policies, and note the features that remain implementation-specific.

The Gateway API Inference Extension adds concepts for LLM serving. An InferencePool groups a set of model-server pods, and InferenceModel and Objective objects describe the models. An endpoint picker routes requests by reading model-server metrics, such as queue depth, KV-cache utilisation, active LoRA adapters and prefix cache, instead of round-robin. This is directly relevant to LLM serving, which Part 15 covers. The project is still evolving, so verify its maturity before you rely on it.

Before you migrate, list the annotations your Ingresses use and map each one to a filter or policy.

## 4. TLS and cert-manager

Suppose a certificate expires on a Friday night and the site goes down. cert-manager prevents that. It automates certificate issuance and renewal through custom resources. An `Issuer` or `ClusterIssuer` says where certificates come from, such as ACME and Let's Encrypt, Vault PKI, an internal CA, Venafi, or self-signed. A `Certificate` describes the certificate you want, and cert-manager stores the result in a Secret. An annotation on an Ingress or Gateway, like `cert-manager.io/cluster-issuer`, creates the Certificate for you.

ACME gives you two ways to prove that you control a domain. HTTP-01 needs public reachability on port 80, works per host, and cannot issue wildcards. DNS-01 needs API credentials for your DNS provider. It supports wildcards and private clusters.

Renewal starts at about 2/3 of the lifetime by default. For 90-day certificates, that means renewal 30 days before expiry.

The example uses a DNS-01 solver with `cloudDNS`.

```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata: { name: letsencrypt-prod }
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: platform@example.com
    privateKeySecretRef: { name: letsencrypt-prod-account }
    solvers:
      - dns01:
          cloudDNS: { project: my-dns-project, serviceAccountSecretRef: { name: clouddns-sa, key: key.json } }   # prefer workload identity
```

The solver reads a service account key from a Secret, and the comment prefers workload identity.

To operate this, monitor `certmanager_certificate_expiration_timestamp_seconds` and alert on issuance failures. When something fails, run `kubectl describe certificate/order/challenge` to see why. Watch public CA rate limits, and secure the issuer credentials. For private and internal domains, including mTLS between services, use an internal CA such as Vault, step-ca or the cert-manager CA issuer.

At the edge, accept TLS 1.2 or newer, and prefer 1.3. Use modern cipher suites, HSTS, OCSP stapling and an HTTP-to-HTTPS redirect. Keep separate certificates for each environment, rotate secrets on a schedule, and restrict who can read TLS Secrets with RBAC.

You can terminate at the L4 load balancer for passthrough, or at the gateway. End-to-end encryption to pods with mTLS in a mesh is covered in 5.28. SNI routing with TLS passthrough suits backends that must keep their own certificates.

Choose HTTP-01 or DNS-01 for each domain before creating the issuer.

## 5. Bare-metal and GPU-cloud load balancers

Without a cloud provider, a `type: LoadBalancer` Service stays `<pending>` until you install a controller.

MetalLB assigns IP addresses from pools you configure. In L2 mode, one node answers ARP or NDP for the IP. Failover takes seconds, but that single node is a bandwidth bottleneck, and all nodes must share one L2 domain. If you run kube-proxy in IPVS mode, set `strictARP`. In BGP mode, the speakers peer with the ToR switches or routers and advertise /32 routes. Traffic then spreads across nodes with ECMP, which helps at scale. BGP needs router configuration, and it fits the leaf-spine fabrics covered in 2.15 to 2.16. You configure MetalLB with the `IPAddressPool`, `L2Advertisement`, `BGPPeer` and `BGPAdvertisement` CRDs. Service annotations such as `metallb.universe.tf/address-pool` and `loadBalancerIPs` select the pool and the address.

kube-vip provides a VIP for the control plane and for Services, using ARP or BGP, and it is lightweight. Cilium LB IPAM, with its BGP Control Plane or with L2 announcements, is integrated with the CNI. It can use Maglev hashing and DSR with an eBPF datapath. Calico advertises Service and cluster IPs through BGP.

Hardware and virtual appliances fill the same role. Examples include F5, A10, NetScaler, HAProxy with keepalived pairs, and NVIDIA or Cumulus anycast designs. Anycast also gives you one entry point across multiple sites.

Cloud providers offer a Network LB at L4 and an Application LB at L7. Use annotations to configure internal LBs, health check paths, target types (instance or IP) and idle timeouts. Idle timeouts need attention. The AWS NLB default is 350 s, the ALB default is 60 s, and the GCP backend timeout default is 30 s. Raise these for streaming and LLM endpoints.

Raise the idle timeouts on any load balancer that fronts streaming endpoints before you send it real traffic.

## 6. Designing the edge for AI/LLM traffic

An LLM edge fails in different ways from a web edge. Generations run for minutes, prompts can be large, and one slow backend can hold many requests. The table covers each concern, and you can read the guidance on the same row.

| Concern | Guidance |
|---|---|
| **Timeouts** | Generation can take minutes; set gateway read/idle/request timeouts (e.g., 300-900 s) and cloud LB idle timeouts accordingly; use heartbeats/keepalive comments in SSE streams; client libraries must match |
| **Streaming** | Disable response buffering for SSE/chunked token streams (`proxy_buffering off`, Envoy default is streaming); avoid gzip on streams; HTTP/2 end-to-end if possible; watch idle connection reaping in intermediate NAT/LB |
| **Request size** | Raise body size limits for long prompts, multimodal inputs (images/audio), batch inference (`proxy-body-size`); consider presigned object store uploads for large files instead of proxying through the gateway |
| **Connection handling** | HTTP/2 multiplexing and keep-alive pin to backends; L7 per-request balancing (Envoy `least_request`, `ring_hash`/`maglev` for consistent hashing by session/user for prefix-cache locality); limit max connection age to rebalance |
| **Retries and idempotency** | Do not auto-retry non-idempotent POSTs that already started generating; configure retry budgets and timeouts; use idempotency keys |
| **Backpressure and queues** | Gateways need concurrency limits and queueing per model (max pending requests); return 429/503 with `Retry-After` rather than piling latency; surface queue depth; integrate with autoscaling signals (5.23) |
| **Rate limiting** | Per API key/tenant limits in requests and tokens per minute: gateway-level (Envoy global rate limit service, Kong/APISIX plugins, NGINX `limit_req`), or an LLM gateway (LiteLLM, Portkey, Kong AI Gateway, custom) for token accounting |
| **Authentication** | OIDC (oauth2-proxy, Envoy ext_authz), API keys/JWT validation at the gateway, mTLS for service clients; propagate identity headers; never expose model-serving ports directly |
| **Routing by model/version** | Host/path/header matches; weights for canary (5% → 25% → 100%) with metrics gates (Argo Rollouts/Flagger integrate with Gateway API) (4.26) |
| **Cache-/load-aware routing** | Use endpoint-picker approaches (Gateway API Inference Extension, vLLM production-stack router, llm-d) that use KV-cache and queue metrics, prefix-cache hit probability, LoRA locality — beats round-robin for LLMs (Part 15) |
| **Observability** | Access logs with request id, model, tenant, status, latency, upstream time, tokens; RED metrics per route; distributed tracing (W3C `traceparent`); correlate with model-server metrics |
| **Security** | WAF/rate limiting, request validation (schema), max prompt size, prompt-injection filtering is application-level; isolate public and internal gateways; network policies from gateway namespace to backends only; TLS everywhere |
| **Availability** | ≥3 gateway replicas across zones, PDB, anti-affinity, HPA on connections/CPU, graceful shutdown (drain connections, `lameduck`), multiple LB IPs, DNS failover, health checks that reflect model readiness |
| **Cost/egress** | Keep gateways in the same zone/region as model servers; avoid hairpinning through the Internet; compress responses where not streaming |

Start with timeouts and streaming, because the first rows decide whether a long answer reaches your users at all. The rows after them handle load, security and cost.

### Example: nginx-ingress tuned for streaming inference (annotations)

The first example applies the streaming settings to ingress-nginx.

```yaml
metadata:
  annotations:
    nginx.ingress.kubernetes.io/proxy-connect-timeout: "10"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "900"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "900"
    nginx.ingress.kubernetes.io/proxy-buffering: "off"
    nginx.ingress.kubernetes.io/proxy-request-buffering: "off"
    nginx.ingress.kubernetes.io/proxy-body-size: "100m"
    nginx.ingress.kubernetes.io/backend-protocol: "HTTP"
    nginx.ingress.kubernetes.io/upstream-hash-by: "$http_x_session_id"      # consistent hashing for prefix-cache locality
    nginx.ingress.kubernetes.io/limit-connections: "50"
```

### Example: Envoy Gateway policies (Gateway API attachments)

The second example applies the same ideas as a Gateway API policy in Envoy Gateway.

```yaml
apiVersion: gateway.envoyproxy.io/v1alpha1
kind: BackendTrafficPolicy
metadata: { name: llm-policy, namespace: serving }
spec:
  targetRefs: [ { group: gateway.networking.k8s.io, kind: HTTPRoute, name: chat } ]
  loadBalancer: { type: LeastRequest }
  timeout: { http: { requestTimeout: 900s } }
  retry: { numRetries: 0 }                      # no blind retries of generation requests
  circuitBreaker: { maxPendingRequests: 200, maxParallelRequests: 400 }
```

Resource kinds and fields vary by implementation and version. This example illustrates the attachment pattern.

Set the timeouts and body size on the edge before you tune anything else.

## 7. Operating and debugging

When an on-call page says users see errors, start with the status code. Each code points at a different layer of the request path. A request travels from DNS to an LB IP, through a node or load balancer, into a gateway pod, then to a Service and its endpoints, and finally to an app pod.

The table maps each status to its likely meaning and to the first thing you should check.

| Status | Meaning | Check |
|---|---|---|
| **404 from the gateway** | No matching host/path/route; default backend | Ingress/HTTPRoute `Accepted`/`ResolvedRefs`, hostname/Host header, path type, IngressClass, namespace allowed by Gateway |
| **502 Bad Gateway** | Backend reset connection / protocol mismatch / bad upstream TLS | Backend pod logs, `backend-protocol`, port, HTTP/1.1 vs HTTP/2, upstream TLS settings, pod crash during rollout |
| **503 Service Unavailable** | No healthy endpoints / overloaded / circuit breaker | EndpointSlices, readiness, outlier detection, `maxPendingRequests` |
| **504 Gateway Timeout** | Upstream took longer than timeout | Raise timeouts, check model latency/queue, LB idle timeouts, retries |
| **413 Request Entity Too Large** | Body limit | Raise size, use presigned uploads |
| **TLS handshake errors** | SNI mismatch, expired/missing cert, wrong secret namespace | `openssl s_client -connect ip:443 -servername host`, cert-manager status, Secret exists in right namespace (Ingress) / ReferenceGrant (Gateway) |
| **429** | Rate limit | Policy, client behaviour, `Retry-After` |
| **Connection resets mid-stream** | Idle/maximum duration timeouts, buffer limits, pod termination | LB idle timeout, `proxy_read_timeout`, SSE heartbeats, rolling update drain |
| **Wrong client IP** | SNAT / `externalTrafficPolicy: Cluster` / proxy protocol missing | `Local` policy, PROXY protocol, `X-Forwarded-For` handling and trusted proxies |
| **Uneven load** | HTTP/2 connection pinning, L4 balancing, sticky hash | Per-request L7 balancing, max connection age |

The commands below let you check each layer in turn, from the Ingress and Gateway objects down to the logs and the TLS certificate.

```bash
kubectl get ingressclass,ingress -A
kubectl describe ingress llm-api -n serving                     # events, backends, TLS
kubectl get gatewayclass,gateway,httproute -A
kubectl describe gateway public -n edge | sed -n '/Conditions/,$p'
kubectl describe httproute chat -n serving | sed -n '/Status/,$p'
kubectl -n ingress-nginx logs deploy/ingress-nginx-controller --tail=100
kubectl -n ingress-nginx exec deploy/ingress-nginx-controller -- cat /etc/nginx/nginx.conf | grep -A5 "server_name llm.example.com"
curl -vk --resolve llm.example.com:443:<LB-IP> https://llm.example.com/v1/models
curl -N -H 'Accept: text/event-stream' https://llm.example.com/v1/chat   # check streaming with -N (no buffering)
openssl s_client -connect <LB-IP>:443 -servername llm.example.com </dev/null | openssl x509 -noout -dates -subject -issuer
kubectl get certificate,certificaterequest,order,challenge -A
```

For a 504, check the timeouts and the model's latency before you change anything else.

## 8. Lab

Start with the self-checking Python lab. You can run it locally before you touch a cluster. It checks the Gateway API `HTTPRoute` matcher, `evaluate_httproute_and_reference_grant`, covering `Exact` versus `PathPrefix` precedence, `x-model` header matching and cross-namespace `ReferenceGrant` enforcement. It also checks the LLM streaming gateway validator, `validate_llm_streaming_gateway_config`, and the KV-cache and queue-aware `InferencePool` endpoint picker, `pick_llm_inference_endpoint`.

```bash
python3 code/part05/gateway_llm_router_lab.py
```

Next, move to a cluster that has a LoadBalancer implementation and Helm. All interactive shell steps below are `untested here`. You work through these exercises in order.

1. Install ingress-nginx and MetalLB, or a cloud LB. Deploy two echo services and create an Ingress with host and path rules. Test it with `curl --resolve`, observe the generated nginx config, and add TLS first with a self-signed cert, then with cert-manager and an internal CA.
2. Deploy a mock SSE server that emits a token every 200 ms for 5 minutes. Observe the buffering effects with the defaults, then set timeouts and `proxy-buffering: off`. Verify with `curl -N`, test through a cloud or LB idle timeout, for example 60 s, and add keepalive comments.
3. Install Envoy Gateway, or Cilium or Istio, along with the Gateway API CRDs. Create a GatewayClass, a Gateway and an HTTPRoute. Set a weight-based canary of 90/10 between two Services, and add header-based routing. Then read the status conditions after you introduce mistakes, such as a missing ReferenceGrant or a wrong parentRef.
4. Convert the Ingress from step 1 with `ingress2gateway`, and compare the two. Run both, and document the unsupported annotations and their equivalents.
5. Send gRPC echo traffic over a single client connection through a Service, then through ingress-nginx, then through Envoy with `LeastRequest`. Graph the per-backend counts. Add `maglev` or `ring_hash` keyed by a header, and observe the stickiness and its effect on prefix-cache hit rate. Simulate the cache with an LRU cache in the backend.
6. Add per-key rate limiting with the Envoy rate limit service or NGINX, and add OIDC through oauth2-proxy or JWT validation. Test the 401, 403 and 429 behaviour, and check the logs.
7. Issue a certificate with ACME DNS-01 against the staging CA, or against an internal CA. Force a renewal. Then simulate a failure by revoking the DNS credentials, and use `describe` to read the error. Finally, add expiry alerts.
8. Configure MetalLB in L2 mode, and find the announcing node with `kubectl get events` and `arping`. Kill that node and measure the failover. Switch to BGP with FRR, observe ECMP across nodes, and test `externalTrafficPolicy: Local` health checks.
9. Drain a gateway node, and roll the gateway Deployment both with and without graceful drain. Count the dropped requests. Scale backend pods to 0 to produce 503s, set a tiny body limit to produce 413s, and shorten the timeouts to produce 504s.
10. This step is optional. Deploy two mock or real vLLM replicas, plus a router or endpoint picker, such as the vLLM router or the Gateway API Inference Extension if it is available. Compare tail latency with round-robin under a skewed workload.
11. Turn on JSON access logs and Prometheus metrics, and build a dashboard of request rate, errors and duration by route. Add tracing headers, then view a trace through the gateway and the backend.
12. Clean up.

## 9. Common mistakes

Default proxy timeouts of 60 s and default buffering kill long generations and token streams. Relying on controller-specific annotations is another trap. An annotation can silently do nothing under another controller or version, and nothing validates it. Enabling snippet annotations for untrusted tenants is a related risk.

Exposing model server ports through a NodePort or an LB, without auth and rate limiting, leaves the model open. Using `externalTrafficPolicy: Cluster` means you may later wonder where client IPs went. Setting `Local` with too few pods creates its own gaps.

Running one gateway replica, or running without a PDB, leaves you no graceful drain. DNS TTLs that are too long also slow failover. Not allowing the gateway namespace in NetworkPolicies, or not restricting backends to gateway-only ingress, is another gap.

Ignoring certificate expiry monitoring is risky. So are ACME rate limits, and HTTP-01 challenges behind a firewall. Assuming L7 gateways balance HTTP/2 evenly without configuration is a mistake. Round-robin is also a poor fit for LLM traffic when load- and cache-aware routing matters.

Retrying non-idempotent generation requests is dangerous. Running Ingress and Gateway controllers that both claim the same class or hosts causes conflicts.

Check your edge against this list before the next rollout.

## 10. Interview angles

- Explain the difference between a Service of type LoadBalancer, an Ingress and the Gateway API.
- Why was the Gateway API created, and what do GatewayClass, Gateway, HTTPRoute and ReferenceGrant each do?
- How would you expose an LLM inference endpoint securely and reliably? Which timeouts and buffering settings matter most?
- How do you run canary releases for a model version at the gateway?
- How does cert-manager work, and when do you pick HTTP-01 over DNS-01?
- How do you provide LoadBalancer Services on bare metal? Mention MetalLB's L2 and BGP modes.
- A client gets a 504 after 60 seconds on a long generation. Where do you look?
- Why might round-robin load balancing be a poor choice for LLM serving?

## Exercises

1. Contrast L4 load balancing, as in `Service type: LoadBalancer`, with L7 load balancing through `Ingress` and `Gateway API`. Explain why `bandicoot.example.com/a/` reaches the backend as `/a/` unless it is rewritten, as Kubernetes: Up and Running, Chapter 8, describes. Show how you prevent multi-team hostname collisions with OPA or Contour `HTTPProxy` root `includes`, as Production Kubernetes, Chapter 6, explains. Finally, isolate an Ingress `DaemonSet` on dedicated edge nodes using `hostNetwork: true`, `dnsPolicy: ClusterFirstWithHostNet` and `externalTrafficPolicy: Local`.
2. Work with the Gateway API resources: GatewayClass, Gateway, HTTPRoute, GRPCRoute and ReferenceGrant. Using `evaluate_httproute_and_reference_grant()` in `code/part05/gateway_llm_router.py`, map the three Gateway API personas: Infrastructure Provider, Cluster Operator and Application Developer. Trace how an `HTTPRoute` matches on `PathPrefix` and `headers: [{name: x-model, value: llama-70b}]` with a `95/5` canary split. Then explain why cross-namespace backend references fail with `RefNotPermitted` without a `ReferenceGrant`.
3. Trace `ClusterIssuer/letsencrypt-prod` in Section 4. Compare ACME `HTTP-01` and `DNS-01` for wildcard certificates and for private, air-gapped or VPC clusters. Explain how cert-manager renews certificates at 2/3 of their lifetime.
4. Compare MetalLB Layer 2, which uses an `L2Advertisement` with an ARP or NDP single-node leader, with BGP, which uses `BGPAdvertisement` and ECMP across ToR switches. Place kube-vip and Cilium LB IPAM in the same comparison. Then explain how GKE Container-Native Load Balancing, with NEGs, and AWS ALB IP target mode route directly to Pod IPs. Networking and Kubernetes, Chapter 6, covers the cloud side.
5. Using `validate_llm_streaming_gateway_config()` in `code/part05/gateway_llm_router.py`, explain why default NGINX, Envoy and cloud LB settings break LLM serving. Cover a `60s` read or idle timeout that returns a `504`, `proxy-buffering: on` that stalls SSE tokens, a `1m` body size that returns a `413`, and automatic POST retries that multiply GPU load. Then show both the `ingress-nginx` annotation block and the Envoy Gateway `BackendTrafficPolicy` that you would use.
6. Work with `InferencePool` from the Gateway API Inference Extension. Using `pick_llm_inference_endpoint()` in `code/part05/gateway_llm_router.py`, explain why round-robin and plain least-connections perform poorly for long-context LLM prompts and LoRA adapters. Compare them with KV-prefix-cache and queue-depth routing. Then state the root cause and the diagnostic command you would run for each HTTP status at the gateway: `404`, `413`, `429`, `502`, `503` and `504`.

## Checkpoint questions (20)

<details>
<summary>1. Compare `Service type: LoadBalancer`, `Ingress`, and the `Gateway API`: what layer does each operate at, and how many external IP addresses do 20 HTTP microservices need under each?</summary>

- `Service type: LoadBalancer` works at Layer 4, for TCP and UDP. It provisions a dedicated external load balancer for each Service. Exposing 20 microservices that way creates 20 separate cloud load balancers and 20 billable public IPs, and it offers no URL path or header routing.
- `Ingress` works at Layer 7, for HTTP and HTTPS. One shared reverse proxy, such as `ingress-nginx`, Envoy or ALB, sits behind a single external IP. It routes to all 20 internal `ClusterIP` Services by `Host` header and URL path. Advanced features depend on controller annotations, which are not portable.
- The `Gateway API` works at Layer 4 and Layer 7, covering HTTP, gRPC, TLS, TCP and UDP. It is a role-oriented, strongly typed successor to `Ingress`, built from `GatewayClass`, `Gateway`, `HTTPRoute`, `GRPCRoute` and `ReferenceGrant`. It can share one or more managed Gateway listeners across teams without untyped annotations.
</details>

<details>
<summary>2. In *Kubernetes: Up and Running* Chapter 8, what happens if you create an `Ingress` object in a cluster that has no Ingress controller installed?</summary>

Nothing happens. A `Deployment` or `ReplicaSet` has its controller built into `kube-controller-manager`, but Kubernetes does not include a built-in Ingress controller. `kube-apiserver` stores the `Ingress` YAML in `etcd`, and `kubectl get ingress` shows an empty `ADDRESS` column forever. No traffic is routed until you install an Ingress controller that matches `spec.ingressClassName`, such as `ingress-nginx`, Contour, Cilium, Traefik or a cloud controller.
</details>

<details>
<summary>3. In Kubernetes: Up and Running, Chapter 8, if an Ingress rule matches `host: bandicoot.example.com` and `path: /a` (`pathType: Prefix`) and forwards to Service `bandicoot:8080`, what URL path does the `bandicoot` container receive?</summary>

By default, Ingress does not strip or rewrite the matched path prefix. A client request for `http://bandicoot.example.com/a/status` reaches the `bandicoot` container as `GET /a/status HTTP/1.1`. If the application listens at `/status` instead of `/a/status`, it returns `404 Not Found`. Path rewriting fixes that, through an annotation such as `nginx.ingress.kubernetes.io/rewrite-target` or a Gateway API `URLRewrite` `ReplacePrefixMatch` filter.
</details>

<details>
<summary>4. In Networking and Kubernetes, Chapter 5, if an `Ingress` or `HTTPRoute` contains both a `Prefix` rule for `/v1` and an `Exact` rule for `/v1/models`, which rule wins for a request to `/v1/models`?</summary>

The `Exact` rule always takes precedence over `Prefix` rules, whatever order the rules appear in the YAML file. When several `Prefix` rules match, such as `/v1` and `/v1/chat`, the longest matching prefix wins. In that case, `/v1/chat` wins.
</details>

<details>
<summary>5. In *Production Kubernetes* Chapter 6, what is the \"Multi-Team Hostname Collision\" problem with standard `Ingress`, and how do Contour's `HTTPProxy` and the Gateway API solve it?</summary>

With standard `Ingress`, any developer who can create an `Ingress` in their own namespace, such as `team-b`, can declare `host: chat.ai.example.com`. They can do that accidentally or maliciously, and it hijacks or corrupts production routes that `team-a` owns.
- Contour's `HTTPProxy` handles this with root `HTTPProxy` inclusion, set through `includes`. Only a locked-down admin namespace can define top-level virtual hosts, such as `fqdn: chat.ai.example.com`. That namespace delegates path prefixes, such as `/v1/embeddings`, to child `HTTPProxy` objects in `team-b`'s namespace. Production Kubernetes, Chapter 6, describes this pattern.
- The Gateway API separates the `Gateway`, owned by cluster operators in the `edge` namespace, from the `HTTPRoute`s owned by application teams. The `Gateway` defines the allowed `hostname: "*.ai.example.com"` and the `allowedRoutes` namespace selector.
</details>

<details>
<summary>6. Why does Production Kubernetes, Chapter 6, recommend running high-throughput Ingress/Gateway proxies on dedicated edge nodes with `hostNetwork: true` and `dnsPolicy: ClusterFirstWithHostNet`?</summary>

It recommends three settings that you use together.
1. Dedicated edge nodes, labeled and tainted, run the proxy as a `DaemonSet`. This isolates proxy CPU, NIC bandwidth, file descriptors and `conntrack` tables from noisy application and training pods. It also gives external hardware load balancers or BGP routers a small, fixed set of edge node IPs.
2. `hostNetwork: true` binds the proxy directly to host ports `80` and `443` in the root network namespace. That bypasses the `NodePort` `iptables`/`IPVS` DNAT overhead and preserves client source IPs.
3. `dnsPolicy: ClusterFirstWithHostNet` is needed because `hostNetwork: true` otherwise makes Kubernetes default to the host's external `/etc/resolv.conf`. That breaks resolution of in-cluster `*.svc.cluster.local` backend names. This policy restores CoreDNS resolution for the host-networked proxy.
</details>

<details>
<summary>7. What are the four core resource kinds in the Gateway API (`gateway.networking.k8s.io/v1`) and which persona manages each?</summary>

1. `GatewayClass`, owned by the infrastructure provider, defines the controller implementation class. Examples include `gateway.envoyproxy.io/gatewayclass-controller`, `io.cilium/gateway-controller` and `gke-l7-global-external-managed`.
2. `Gateway`, owned by the cluster or platform operator, declares the load-balancing entry point. It holds listeners, ports such as `443`, protocols such as `HTTPS`, TLS certificates, and the namespaces allowed to attach routes through `allowedRoutes`.
3. `HTTPRoute`, `GRPCRoute` and `TLSRoute`, owned by application or ML developers, attach to a parent `Gateway` through `parentRefs`. They define hostnames, path and header matches, filters, timeouts and weighted `backendRefs`.
4. `ReferenceGrant`, owned by the target namespace owner, explicitly authorizes cross-namespace references. For example, it can allow an `HTTPRoute` in `edge` to route to a `Service` in `serving`, or a `Gateway` in `edge` to read a TLS `Secret` in `security`.
</details>

<details>
<summary>8. If an `HTTPRoute` in namespace `serving` tries to attach to a `Gateway` in namespace `edge` (or reference a `Service` in namespace `ops`) and traffic is not flowing, what `status` conditions on the `HTTPRoute` tell you why?</summary>

Run `kubectl describe httproute <name> -n serving` and inspect `status.parents[].conditions`. Two conditions can explain the problem you see.
- `Accepted: False`, with `Reason: NotAllowedByListeners` or `NoMatchingListenerHostname`, means the `Gateway` in `edge` does not allow routes from `serving` through `allowedRoutes.namespaces`. It can also mean the route's `hostnames` do not match the listener's hostname wildcard.
- `ResolvedRefs: False`, with `Reason: RefNotPermitted` or `BackendNotFound`, means the `HTTPRoute` references a `Service` in another namespace, `ops`, and there is no `ReferenceGrant` in `ops` that permits `HTTPRoute`s from `serving` to target it.
</details>

<details>
<summary>9. Why should `allow-snippet-annotations` be disabled on `ingress-nginx` in multi-tenant clusters?</summary>

`nginx.ingress.kubernetes.io/configuration-snippet` and `server-snippet` let any user who can create an `Ingress` inject arbitrary raw `nginx.conf` directives into the shared `ingress-nginx-controller` Pod. Those directives can include Lua code or file reads. That Pod has cluster-wide permission to read every TLS `Secret` and ServiceAccount token. Snippet injection has been the source of critical CVEs, such as `CVE-2021-25742` and `CVE-2023-5044`, which let tenants steal all cluster Secrets. Always set `allow-snippet-annotations: "false"`, or migrate to the typed Gateway API.
</details>

<details>
<summary>10. Compare `cert-manager` ACME `HTTP-01` vs. `DNS-01` challenges: when must you use `DNS-01`?</summary>

- The `HTTP-01` challenge: Let's Encrypt makes an inbound HTTP request from the public internet to `http://<your-domain>/.well-known/acme-challenge/<token>` on port 80. `cert-manager` temporarily spawns a solver Pod and an Ingress rule to answer it. The method is simple and needs no DNS API credentials. However, it fails if port 80 is blocked from the public internet, as with private or VPC-internal endpoints. It also cannot issue wildcard certificates such as `*.ai.example.com`.
- The `DNS-01` challenge: `cert-manager` uses a cloud DNS API, such as Cloud DNS, Route53 or Cloudflare, to create a temporary `_acme-challenge.<domain>` `TXT` record. It works for private or internal clusters without public inbound port 80, and it supports wildcard certificates such as `*.ai.example.com`.
</details>

<details>
<summary>11. What four gateway settings break Server-Sent Events (`SSE`) token streaming on LLM inference endpoints (`/v1/chat/completions` with `"stream": true`) if left at their defaults?</summary>

1. Response buffering, set with `proxy-buffering: "on"` in NGINX, holds generated tokens in proxy memory until the buffer fills or generation completes. The user then sees nothing for 40 seconds and receives the whole answer in one burst, instead of smooth real-time token streaming. Set `nginx.ingress.kubernetes.io/proxy-buffering: "off"`, and disable gzip compression on `text/event-stream`.
2. Short proxy read and send timeouts, with a `60s` default, cause trouble. A reasoning model such as `DeepSeek-R1` or an `o1`-style model, or a long 8,192-token generation, can take 2–10 minutes. A 60s timeout kills the connection mid-stream, which shows up as `504 Gateway Timeout` or a premature EOF. Raise `proxy-read-timeout` or `requestTimeout` to `600s`–`900s`.
3. Cloud load balancer idle timeouts, `60s` on AWS ALB and `30s` on GCP BackendService, can drop the connection even when the L7 Ingress timeout is 900s. A reasoning model that thinks for 65 seconds before its first token triggers that. Raise the outer LB idle timeout, and send periodic SSE comment heartbeats, such as `: ping\n\n`, every 15s during prefill or thinking.
4. Small request body limits, `1m` by default in NGINX, are easily exceeded by multimodal prompts with base64 images or 128k-token context windows. Those prompts can exceed 1 MB and return `413 Request Entity Too Large`. Raise `proxy-body-size` to `64m`–`100m`.
</details>

<details>
<summary>12. Why must automatic HTTP retries on `POST /v1/chat/completions` be disabled (`numRetries: 0`) at the L7 gateway?</summary>

Generating 4,000 tokens for one prompt uses tens of seconds of expensive GPU compute across 4–8 H100 GPUs. Suppose a gateway automatically retries a `POST` on a timeout or transient reset, with `retries: 3`. One slow prompt then triggers 4 concurrent 4,000-token generations. That quadruples GPU queue depth and can cause a cascading latency collapse, or retry storm, across the inference pool. Retry only fast connect failures, before any bytes are sent, using `retryOn: connect-failure`. Never retry full `POST` generation timeouts.
</details>

<details>
<summary>13. Why is naive Round-Robin load balancing suboptimal for LLM inference servers (`vLLM`, `TRT-LLM`, `SGLang`), and what does the Gateway API Inference Extension (`InferencePool`) do instead?</summary>

In LLM serving, requests differ in cost by $1,000\times$, from a 10-token prompt to a 64,000-token prompt. Pods also keep stateful GPU KV-caches, which include prefix caches of shared system prompts or RAG documents, and loaded LoRA adapters. Round-robin sends a 64k-token prompt to a pod whose GPU KV-cache is already 95% full, which triggers KV-cache preemption and recomputation. It can also send a multi-turn chat turn to a pod that does not hold the conversation's prefix in its KV-cache.

The Gateway API Inference Extension, through `InferencePool` and the Endpoint Picker, `EPP`, works differently. It scrapes real-time KV-cache utilization, waiting queue depth, active LoRA adapters and prefix-cache hashes from the `vLLM` pods. It then routes each request to the replica with the highest prefix-cache hit and the lowest queue and KV pressure.
</details>

<details>
<summary>14. Why does rate limiting for LLM APIs require both `Requests Per Minute (RPM)` and `Tokens Per Minute (TPM)` controls?</summary>

A classic L7 API gateway, such as `limit-rps: 20`, counts every HTTP request as cost `1`. But a tenant that sends 10 requests per second with 100,000 input tokens each consumes 1,000,000 prefill tokens per second. That saturates a whole H100 cluster while staying well under a `20 RPS` request limit. An AI-aware gateway layer, such as Envoy `ext_proc`, LiteLLM, Kong AI Gateway or APISIX, inspects the prompt token count before it forwards the request. It also records completion token usage from the response stream. That enforces per-tenant Tokens Per Minute (`TPM`) and concurrent-request budgets.
</details>

<details>
<summary>15. In *Networking and Kubernetes* Chapter 6, what is GKE \"Container-Native Load Balancing\" (`NEG`s) / AWS ALB `target-type: ip`, and why is it faster than `NodePort`-based load balancing?</summary>

With traditional cloud load balancing, `target-type: instance`, the external cloud LB sends traffic to a node's `NodePort`, in the range `30000-32767`. `kube-proxy` then uses `iptables` or `IPVS` to DNAT the packet and forward it over a second network hop to the node that runs the Pod.

With GKE Network Endpoint Groups, `NEG`s, set through `cloud.google.com/neg: '{"ingress": true}'`, or with the AWS Load Balancer Controller and `alb.ingress.kubernetes.io/target-type: ip`, the cloud controller programs the cloud L7 load balancer with the actual Pod IPs from `EndpointSlice`s. Traffic then flows directly from the cloud load balancer to the target Pod IP in one hop. Client source IPs are preserved, and the `NodePort` SNAT and `kube-proxy` hops disappear.
</details>

<details>
<summary>16. Distinguish the exact meanings of HTTP `502 Bad Gateway`, `503 Service Unavailable`, and `504 Gateway Timeout` when returned by an Ingress or Gateway proxy.</summary>

- `502 Bad Gateway`: The gateway selected a backend Pod IP and connected, but it received an invalid response or a TCP `RST`. Causes include a backend process that crashed mid-request, a backend that speaks plain HTTP where the gateway expects HTTPS or HTTP/2, or a backend that closed the keep-alive socket just as the gateway sent a request.
- `503 Service Unavailable`: The gateway has zero healthy backend endpoints in the `EndpointSlice`, because every Pod failed its `readinessProbe` or the selector labels do not match. It can also mean the gateway's circuit breaker or pending-request queue limit, `maxPendingRequests`, tripped.
- `504 Gateway Timeout`: The gateway connected and sent the request to the backend Pod, but the backend did not respond within `proxy-read-timeout` or `requestTimeout`.
</details>

<details>
<summary>17. How do you perform a zero-downtime canary rollout (`95% -> 5%`) of a new model version (`vllm-llama70b-v2`) using the Gateway API?</summary>

Deploy `vllm-llama70b-v1` and `vllm-llama70b-v2` as separate `Deployment`s and `Service`s. List both in the `HTTPRoute`'s `backendRefs` with explicit `weight` values:

```yaml
backendRefs:
  - { name: vllm-llama70b-v1, port: 80, weight: 95 }
  - { name: vllm-llama70b-v2, port: 80, weight: 5 }
```

An automated progressive delivery controller, Argo Rollouts or Flagger, covered in Chapter 4.26, can adjust these weights automatically, for example `5 -> 25 -> 50 -> 100`. At each step it checks Prometheus TTFT, ITL and HTTP 5xx error rates.
</details>

<details>
<summary>18. Why can rolling updates of the Ingress/Gateway controller Pods themselves drop active streaming connections, and how do you prevent it?</summary>

External load balancers can take 5–15 seconds to notice that a proxy Pod's health check has failed. Existing LLM token streams through that Pod can take 2–5 minutes to finish. A controller upgrade can therefore drop active streams. Prevent that with two settings you place on the controller Pod.
1. A `lifecycle.preStop` hook, such as `sleep 15` or `/wait-shutdown`. The proxy then fails its LB health check and stops receiving new connections from the external LB for 15 seconds, before NGINX or Envoy begins draining.
2. `terminationGracePeriodSeconds: 600`, matching your maximum LLM streaming timeout, so NGINX worker processes or Envoy can drain existing streams cleanly before exit.
</details>

<details>
<summary>19. How do you test an `Ingress` or `Gateway` route for `https://llm.example.com/v1/models` before updating public DNS records (Kubernetes: Up and Running, Chapter 8)?</summary>

Use `curl --resolve <host>:<port>:<LB-IP>`. It overrides DNS resolution for `llm.example.com` inside `curl`, so the TCP connection, the TLS SNI `ClientHello` extension, and the HTTP `Host: llm.example.com` header all use the real hostname.

```bash
curl -vk --resolve llm.example.com:443:203.0.113.50 https://llm.example.com/v1/models
```

Running `curl -k -H "Host: llm.example.com" https://203.0.113.50/...` sets the HTTP `Host` header, but it fails TLS SNI routing. The TLS `ClientHello` lacks `servername=llm.example.com`. `--resolve` sets both SNI and `Host` correctly.
</details>

<details>
<summary>20. How do you debug a `Certificate` stuck in `Ready: False` in `cert-manager`?</summary>

Follow the `cert-manager` resource chain from top to bottom with `kubectl describe`. The chain runs from `Certificate` to `CertificateRequest`, then to `Order` for ACME, and then to `Challenge`. To list all of them, run `kubectl get certificate,certificaterequest,order,challenge -A`. Then run `kubectl describe challenge <name>` to see the exact ACME failure reason. That can be a firewall blocking Let's Encrypt's HTTP-01 probe to port 80, an Ingress class mismatch on the solver Pod, or missing Cloud DNS IAM permissions for creating the DNS-01 TXT record.
</details>

## Sources and review notes

- **Sources read in full:**
  - `kubernetes-up-and-running-3rd-edition` — Brendan Burns, Joe Beda, Kelsey Hightower & Lachlan Evenson, *Kubernetes: Up and Running*, 3rd ed., **Chapter 8: HTTP Load Balancing with Ingress** (read in full: Ingress spec vs Ingress controller, installing Contour, `/etc/hosts` local testing, `defaultBackend`, host and path rules, unmodified upstream path forwarding vs path rewriting, serving TLS with `kubernetes.io/tls` Secrets, `ingressClassName` and `is-default-class`, and multiple-Ingress merge pitfalls).
  - `production-kubernetes` — Josh Rosso, Rich Lander, Alexander Brand & John Harris, *Production Kubernetes*, **Chapter 6: Service Routing** (read in full: Ingress controller deployment considerations, multi-team hostname collisions, Contour `HTTPProxy` root `includes` and TCP SNI proxying, dedicated Ingress node pools with `DaemonSet` + `hostNetwork: true` + `dnsPolicy: ClusterFirstWithHostNet` + `externalTrafficPolicy: Local`).
  - `networking-and-kubernetes` — James Strong & Vallery Lancey, *Networking and Kubernetes*, **Chapter 5: Kubernetes Networking Abstractions** (`Exact` vs `Prefix` path precedence, NGINX Ingress controller, TLS Secrets) and **Chapter 6: Kubernetes and Cloud Networking** (read in full: AWS VPC/EKS with AWS Load Balancer Controller `v2.2.0` & OIDC IAM service account, GCP VPC-native GKE with Container-Native Load Balancing / NEGs / Cloud Armor / IAP, and Azure VNet/AKS).
- **Run here:** `python3 code/part05/gateway_llm_router_lab.py` (3 passed, 0 failed).
- **Explicitly labelled inferences:** The `evaluate_httproute_and_reference_grant`, `validate_llm_streaming_gateway_config`, and `pick_llm_inference_endpoint` models in `code/part05/gateway_llm_router.py` and the `llm-api` `Ingress`, `chat` `HTTPRoute`, `letsencrypt-prod` `ClusterIssuer`, and `llm-policy` `BackendTrafficPolicy` manifests are the author's constructions synthesizing `KUR` Chapter 8, `PK` Chapter 6, and `NK` Chapters 5 & 6 (plus original study items 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, and 35).
- **Not verified on live hardware:** Live `ingress-nginx`, `Envoy Gateway`, `Contour`, `cert-manager`, and `MetalLB` executions (`60s` / `600s` / `900s` timeouts, `64m` / `100m` body size, `limit-rps: 20`, `limit-connections: 50`, `8080`, `443`, `95/5` and `90/10` canary weights, `301`, `90`-day certs / `30`-day renewal, `350 s` AWS NLB / `60 s` ALB / `30 s` GCP timeouts, `maxPendingRequests: 200, maxParallelRequests: 400`, `404`/`413`/`429`/`502`/`503`/`504`, `200 ms` token interval) are marked (`untested here`) where not executed by `gateway_llm_router_lab.py`.
