# kubernetes-up-and-running-3rd-edition


<!-- file: app01.xhtml -->

## Appendix. Building Your Own Kubernetes Cluster

## Parts List

## Flashing Images

## First Boot
- Setting Up Networking
- Installing a Container Runtime
- Installing Kubernetes
- Setting Up the Cluster
- Setting Up Cluster Networking

## Summary

<!-- file: ch01.xhtml -->

## Chapter 1. Introduction

## Velocity
- The Value of Immutability
- Declarative Configuration
- Self-Healing Systems

## Scaling Your Service and Your Teams
- Decoupling
- Easy Scaling for Applications and Clusters
- Scaling Development Teams with Microservices
- Separation of Concerns for Consistency and Scaling

## Abstracting Your Infrastructure

## Efficiency

## Cloud Native Ecosystem

## Summary

<!-- file: ch02.xhtml -->

## Chapter 2. Creating and Running Containers

## Container Images

## Building Application Images with Docker
- Dockerfiles
- Optimizing Image Sizes
- Image Security

## Multistage Image Builds

## Storing Images in a Remote Registry

## The Container Runtime Interface
- Running Containers with Docker
- Exploring the kuard Application
- Limiting Resource Usage
  - Limiting memory resources
  - Limiting CPU resources

## Cleanup

## Summary

<!-- file: ch03.xhtml -->

## Chapter 3. Deploying a Kubernetes Cluster

## Installing Kubernetes on a Public Cloud Provider
- Installing Kubernetes with Google Kubernetes Engine
- Installing Kubernetes with Azure Kubernetes Service
- Installing Kubernetes on Amazon Web Services

## Installing Kubernetes Locally Using minikube

## Running Kubernetes in Docker

## The Kubernetes Client
- Checking Cluster Status
- Listing Kubernetes Nodes

## Cluster Components
- Kubernetes Proxy
- Kubernetes DNS
- Kubernetes UI

## Summary

<!-- file: ch04.xhtml -->

## Chapter 4. Common kubectl Commands

## Namespaces

## Contexts

## Viewing Kubernetes API Objects

## Creating, Updating, and Destroying Kubernetes Objects

## Labeling and Annotating Objects

## Debugging Commands

## Cluster Management

## Command Autocompletion

## Alternative Ways of Viewing Your Cluster

## Summary

<!-- file: ch05.xhtml -->

## Chapter 5. Pods

## Pods in Kubernetes

## Thinking with Pods

## The Pod Manifest
- Creating a Pod
- Creating a Pod Manifest

## Running Pods
- Listing Pods
- Pod Details
- Deleting a Pod

## Accessing Your Pod
- Getting More Information with Logs
- Running Commands in Your Container with exec
- Copying Files to and from Containers

## Health Checks
- Liveness Probe
- Readiness Probe
- Startup Probe
- Advanced Probe Configuration
- Other Types of Health Checks

## Resource Management
- Resource Requests: Minimum Required Resources
- Capping Resource Usage with Limits

## Persisting Data with Volumes
- Using Volumes with Pods
- Different Ways of Using Volumes with Pods

## Putting It All Together

## Summary

<!-- file: ch06.xhtml -->

## Chapter 6. Labels and Annotations

## Labels
- Applying Labels
- Modifying Labels
- Label Selectors
- Label Selectors in API Objects
- Labels in the Kubernetes Architecture

## Annotations

## Cleanup

## Summary

<!-- file: ch07.xhtml -->

## Chapter 7. Service Discovery

## What Is Service Discovery?

## The Service Object
- Service DNS
- Readiness Checks

## Looking Beyond the Cluster

## Load Balancer Integration

## Advanced Details
- Endpoints
- Manual Service Discovery
- kube-proxy and Cluster IPs
- Cluster IP Environment Variables

## Connecting with Other Environments
- Connecting to Resources Outside of a Cluster
- Connecting External Resources to Services Inside a Cluster

## Cleanup

## Summary

<!-- file: ch08.xhtml -->

## Chapter 8. HTTP Load Balancing with Ingress

## Ingress Spec Versus Ingress Controllers

## Installing Contour
- Configuring DNS
- Configuring a Local hosts File

## Using Ingress
- Simplest Usage
- Using Hostnames
- Using Paths
- Cleanup

## Advanced Ingress Topics and Gotchas
- Running Multiple Ingress Controllers
- Multiple Ingress Objects
- Ingress and Namespaces
- Path Rewriting
- Serving TLS

## Alternate Ingress Implementations

## The Future of Ingress

## Summary

<!-- file: ch09.xhtml -->

## Chapter 9. ReplicaSets

## Reconciliation Loops

## Relating Pods and ReplicaSets
- Adopting Existing Containers
- Quarantining Containers

## Designing with ReplicaSets

## ReplicaSet Spec
- Pod Templates
- Labels

## Creating a ReplicaSet

## Inspecting a ReplicaSet
- Finding a ReplicaSet from a Pod
- Finding a Set of Pods for a ReplicaSet

## Scaling ReplicaSets
- Imperative Scaling with kubectl scale
- Declaratively Scaling with kubectl apply
- Autoscaling a ReplicaSet

## Deleting ReplicaSets

## Summary

<!-- file: ch10.xhtml -->

## Chapter 10. Deployments

## Your First Deployment

## Creating Deployments

## Managing Deployments

## Updating Deployments
- Scaling a Deployment
- Updating a Container Image
- Rollout History

## Deployment Strategies
- Recreate Strategy
- RollingUpdate Strategy
  - Managing multiple versions of your service
  - Configuring a rolling update
- Slowing Rollouts to Ensure Service Health

## Deleting a Deployment

## Monitoring a Deployment

## Summary

<!-- file: ch11.xhtml -->

## Chapter 11. DaemonSets

## DaemonSet Scheduler

## Creating DaemonSets

## Limiting DaemonSets to Specific Nodes
- Adding Labels to Nodes
- Node Selectors

## Updating a DaemonSet

## Deleting a DaemonSet

## Summary

<!-- file: ch12.xhtml -->

## Chapter 12. Jobs

## The Job Object

## Job Patterns
- One Shot
- Parallelism
- Work Queues
  - Starting a work queue
  - Loading up the queue
  - Creating the consumer job
  - Cleanup

## CronJobs

## Summary

<!-- file: ch13.xhtml -->

## Chapter 13. ConfigMaps and Secrets

## ConfigMaps
- Creating ConfigMaps
- Using a ConfigMap

## Secrets
- Creating Secrets
- Consuming Secrets
- Private Container Registries

## Naming Constraints

## Managing ConfigMaps and Secrets
- Listing
- Creating
- Updating
  - Update from file
  - Re-create and update
  - Edit current version
  - Live updates

## Summary

<!-- file: ch14.xhtml -->

## Chapter 14. Role-Based Access Control for Kubernetes

## Role-Based Access Control
- Identity in Kubernetes
- Understanding Roles and Role Bindings
- Roles and Role Bindings in Kubernetes
  - Verbs for Kubernetes roles
  - Using built-in roles
  - Auto-reconciliation of built-in roles

## Techniques for Managing RBAC
- Testing Authorization with can-i
- Managing RBAC in Source Control

## Advanced Topics
- Aggregating ClusterRoles
- Using Groups for Bindings

## Summary

<!-- file: ch15.xhtml -->

## Chapter 15. Service Meshes

## Encryption and Authentication with Mutal TLS

## Traffic Shaping

## Introspection

## Do You Really Need a Service Mesh?

## Introspecting a Service Mesh Implementation

## Service Mesh Landscape

## Summary

<!-- file: ch16.xhtml -->

## Chapter 16. Integrating Storage Solutions and Kubernetes

## Importing External Services
- Services Without Selectors
- Limitations of External Services: Health Checking

## Running Reliable Singletons
- Running a MySQL Singleton
- Dynamic Volume Provisioning

## Kubernetes-Native Storage with StatefulSets
- Properties of StatefulSets
- Manually Replicated MongoDB with StatefulSets
- Automating MongoDB Cluster Creation
- Persistent Volumes and StatefulSets
- One Final Thing: Readiness Probes

## Summary

<!-- file: ch17.xhtml -->

## Chapter 17. Extending Kubernetes

## What It Means to Extend Kubernetes

## Points of Extensibility

## Patterns for Custom Resources
- Just Data
- Compilers
- Operators
- Getting Started

## Summary

<!-- file: ch18.xhtml -->

## Chapter 18. Accessing Kubernetes from Common Programming Languages

## The Kubernetes API: A Client’s Perspective
- OpenAPI and Generated Client Libraries
- But What About kubectl x?

## Programming the Kubernetes API
- Installing the Client Libraries
- Authenticating to the Kubernetes API
- Accessing the Kubernetes API
- Putting It All Together: Listing and Creating Pods in Python, Java, and .NET
- Creating and Patching Objects
- Watching Kubernetes APIs for Changes
- Interacting with Pods
- Summary

<!-- file: ch19.xhtml -->

## Chapter 19. Securing Applications in Kubernetes

## Understanding SecurityContext
- SecurityContext Challenges

## Pod Security
- What Is Pod Security?
- Applying Pod Security Standards

## Service Account Management

## Role-Based Access Control

## RuntimeClass

## Network Policy

## Service Mesh

## Security Benchmark Tools

## Image Security

## Summary

<!-- file: ch20.xhtml -->

## Chapter 20. Policy and Governance for Kubernetes Clusters

## Why Policy and Governance Matter

## Admission Flow

## Policy and Governance with Gatekeeper
- What Is Open Policy Agent?
- Installing Gatekeeper
- Configuring Policies
- Understanding Constraint Templates
- Creating Constraints
- Audit
- Mutation
- Data Replication
- Metrics
- Policy Library

## Summary

<!-- file: ch21.xhtml -->

## Chapter 21. Multicluster Application Deployments

## Before You Even Begin

## Starting at the Top with a Load-Balancing Approach

## Building Applications for Multiple Clusters
- Replicated Silos: The Simplest Cross-Regional Model
- Sharding: Regional Data
- Better Flexibility: Microservice Routing

## Summary

<!-- file: ch22.xhtml -->

## Chapter 22. Organizing Your Application

## Principles to Guide Us
- Filesystems as the Source of Truth
- The Role of Code Review
- Feature Gates

## Managing Your Application in Source Control
- Filesystem Layout
- Managing Periodic Versions
  - Versioning with branches and tags
  - Versioning with directories

## Structuring Your Application for Development, Testing, and Deployment
- Goals
- Progression of a Release
  - Introducing a development tag
  - Mapping stages to revisions

## Parameterizing Your Application with Templates
- Parameterizing with Helm and Templates
- Filesystem Layout for Parameterization

## Deploying Your Application Around the World
- Architectures for Worldwide Deployment
- Implementing Worldwide Deployment
- Dashboards and Monitoring for Worldwide Deployments

## Summary

<!-- file: colophon01.xhtml -->

## About the Authors

<!-- file: colophon02.xhtml -->

## Colophon

<!-- file: copyright-page01.xhtml -->

## Kubernetes: Up and Running

## Revision History for the Third Edition

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
  - J
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
  - Y
  - Z

<!-- file: preface01.xhtml -->

## Preface

## Who Should Read This Book

## Why We Wrote This Book

## Why We Updated This Book

## A Word on Cloud Native Applications Today

## Navigating This Book

## Online Resources

## Conventions Used in This Book

## Using Code Examples

## O’Reilly Online Learning

## How to Contact Us

## Acknowledgments

<!-- file: titlepage01.xhtml -->

## Kubernetes: Up and Running
