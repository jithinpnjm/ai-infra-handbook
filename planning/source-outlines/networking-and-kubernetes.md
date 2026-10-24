# networking-and-kubernetes


<!-- file: ch01.xhtml -->

## Chapter 1. Networking Introduction

## Networking History

## OSI Model

## TCP/IP
- Application
  - HTTP
- Transport
  - TCP
  - TCP handshake
  - tcpdump
  - TLS
  - UDP
- Network
- Internet Protocol
  - Getting round the network
  - ICMP
- Link Layer
- Revisiting Our Web Server

## Conclusion

<!-- file: ch02.xhtml -->

## Chapter 2. Linux Networking

## Basics

## The Network Interface

## The Bridge Interface

## Packet Handling in the Kernel
- Netfilter
- Conntrack
- Routing

## High-Level Routing
- iptables
  - iptables tables
  - iptables chains
  - Subchains
  - iptables rules
  - Practical iptables
- IPVS
- eBPF

## Network Troubleshooting Tools
- Security Warning
- ping
- traceroute
- dig
- telnet
- nmap
- netstat
- netcat
- Openssl
- cURL

## Conclusion

<!-- file: ch03.xhtml -->

## Chapter 3. Container Networking Basics

## Introduction to Containers
- Applications
- Hypervisor
- Containers
  - OCI
  - LXC
  - runC
  - containerd
  - lmctfy
  - rkt
  - Docker
  - CRI-O

## Container Primitives
- Control Groups
- Namespaces
- Setting Up Namespaces

## Container Network Basics
- Docker Networking Model
- Overlay Networking
- Container Network Interface

## Container Connectivity
- Container to Container
- Container to Container Separate Hosts

## Conclusion

<!-- file: ch04.xhtml -->

## Chapter 4. Kubernetes Networking Introduction

## The Kubernetes Networking Model

## Node and Pod Network Layout
- Isolated Networks
- Flat Networks
- Island Networks
- kube-controller-manager Configuration

## The Kubelet

## Pod Readiness and Probes

## The CNI Specification

## CNI Plugins
- The IPAM Interface
- Popular CNI Plugins

## kube-proxy
- userspace Mode
- iptables Mode
- ipvs Mode
- kernelspace Mode

## NetworkPolicy
- NetworkPolicy Example with Cilium
- Selecting Pods
  - The LabelSelector type
- Rules

## DNS

## IPv4/IPv6 Dual Stack

## Conclusion

<!-- file: ch05.xhtml -->

## Chapter 5. Kubernetes Networking Abstractions

## StatefulSets

## Endpoints

## Endpoint Slices

## Kubernetes Services
- NodePort
- ClusterIP
- Headless
- ExternalName Service
- LoadBalancer
- Services Conclusion

## Ingress

## Ingress Controllers and Rules
  - Deploy ingress rules

## Service Meshes

## Conclusion

<!-- file: ch06.xhtml -->

## Chapter 6. Kubernetes and Cloud Networking

## Amazon Web Services
- AWS Network Services
  - Virtual private cloud
  - Region and availability zones
  - Subnet
  - Routing tables
  - Elastic network interface
  - Elastic IP address
  - Security controls
    - Security groups
    - Network access control lists
  - Network address translation devices
  - Internet gateway
  - Elastic load balancers
- Amazon Elastic Kubernetes Service
  - EKS nodes
  - EKS mode
  - eksctl
  - AWS VPC CNI
  - AWS ALB ingress controller
- Deploying an Application on an AWS EKS Cluster
  - Deploy EKS cluster
  - Deploy test application
  - Verify LoadBalancer services for Golang web server
  - Deploy ALB ingress and verify
  - Cleanup

## Google Compute Cloud (GCP)
- GCP Network Services
  - Regions and zones
  - Virtual private cloud
  - Subnet
  - Routes and firewall rules
  - Cloud load balancing
  - GCE instances
- GKE
  - GCP GKE nodes

## Azure
- Azure Networking Services
  - Azure backbone infrastructure
  - Subnets
  - Route tables
  - Public and private IPs
  - Network security groups
  - Communication outside the virtual network
  - Azure load balancer
- Azure Kubernetes Service
  - Azure CNI
  - Application gateway ingress controller
- Deploying an Application to Azure Kubernetes Service
  - Deploying an Azure Kubernetes Service cluster
  - Connecting to and configuring AKS
  - Deploying the Go web server
  - AKS conclusion

## Conclusion

<!-- file: colophon01.xhtml -->

## About the Authors

<!-- file: colophon02.xhtml -->

## Colophon

<!-- file: copyright-page01.xhtml -->

## Networking and Kubernetes

## Revision History for the First Edition

<!-- file: ix01.xhtml -->

## Index
  - A
  - B
  - C
  - D
  - E
  - F
  - G
  - H
  - I
  - K
  - L
  - M
  - N
  - O
  - P
  - R
  - S
  - T
  - U
  - V
  - W
  - X
  - Y

<!-- file: preface01.xhtml -->

## Preface

## Just Another Packet

## Who This Book Is For

## What You Will Learn

## Conventions Used in This Book

## Using Code Examples

## O’Reilly Online Learning

## How to Contact Us

## Acknowledgments

<!-- file: titlepage01.xhtml -->

## Networking and Kubernetes
