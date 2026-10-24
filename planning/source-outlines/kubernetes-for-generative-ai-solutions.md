# kubernetes-for-generative-ai-solutions


<!-- file: B31108_01.xhtml -->

## 1

## Generative AI Fundamentals

## Artificial Intelligence versus GenAI

## Evolution of machine learning

## Transformer architecture

## GenAI project life cycle

## GenAI deployment stack

## GenAI use cases

## Summary

## Get This Book's PDF Version and Exclusive Extras

## Appendix 1A – RNNs

## Appendix 1B – Transformer mathematical models for the self-attention mechanism
- Understanding the temperature parameter for GenAI use cases

<!-- file: B31108_02.xhtml -->

## 2

## Kubernetes – Introduction and Integration with GenAI

## Understanding containers
- Container terminology
- Creating a container image
- Why containers for GenAI models?
- Building a GenAI container image

## What is Kubernetes (K8s)?
- Kubernetes architecture
  - Control plane components
  - Data plane components
  - Add-on software components
- Why K8s is a great fit for GenAI models
  - Challenges of running GenAI models
  - K8s advantages

## Summary

## Get This Book's PDF Version and Exclusive Extras
- Appendix

<!-- file: B31108_03.xhtml -->

## 3

## Getting Started with Kubernetes in the Cloud

## Advantages of running K8s in the cloud

## Setting up a K8s cluster in the cloud
- Prerequisites
- Provisioning the Amazon EKS cluster

## Deploying our first GenAI model in the K8s cluster

## Summary

## Get This Book's PDF Version and Exclusive Extras

<!-- file: B31108_04.xhtml -->

## 4

## GenAI Model Optimization for Domain-Specific Use Cases

## Technical requirements

## The need for domain-specific optimization

## LLM model selection

## The LangChain framework

## Understanding RAG
- How RAG works
- Running a query

## Model fine-tuning
- Fine-tuning example

## Summary

## Further reading

## Get This Book's PDF Version and Exclusive Extras

<!-- file: B31108_05.xhtml -->

## 5

## Working with GenAI on K8s: Chatbot Example

## Technical requirements

## GenAI use cases for e-commerce

## Experimentation using JupyterHub

## Fine-tuning Llama 3 in K8s
- Data preparation
- Creating a container image
- Deploying the fine-tuning job

## Deploying the fine-tuned model on K8s

## Deploy a RAG application on K8s

## Deploying a chatbot on K8s

## Summary

## Get This Book's PDF Version and Exclusive Extras

<!-- file: B31108_06.xhtml -->

## 6

## Scaling GenAI Applications on Kubernetes

## Scaling metrics
- Conventional metrics
- Custom metrics

## HorizonalPodAutoscaler (HPA)

## VerticalPodAutoscaler (VPA)
- Combining HPA and VPA

## KEDA

## Cluster Autoscaler (CA)

## Karpenter

## Summary

## Get This Book's PDF Version and Exclusive Extras

<!-- file: B31108_07.xhtml -->

## 7

## Cost Optimization of GenAI Applications on Kubernetes

## Understanding the key cost components
- Kubecost
  - Setting up Kubecost

## Cost optimization techniques
- Compute best practices
  - Right-sizing resources
  - Compute capacity options
- Networking best practices
  - Pod-to-pod communication
  - Load balancer configuration
  - Data transfer and VPC connectivity
  - Optimizing image pulls from Amazon ECR
- Storage best practices
  - Ephemeral storage
  - Object storage
  - EBS volumes

## Summary

## Get This Book's PDF Version and Exclusive Extras

## Join the CloudPro Newsletter with 44000+ Subscribers

<!-- file: B31108_08.xhtml -->

## 8

## Networking Best Practices for Deploying GenAI on K8s

## Understanding the Kubernetes networking model
- Selecting the CNI networking mode for GenAI applications
- Service implementation in K8s
- Service health checks
  - Ingress controller

## Advanced traffic management with a service mesh

## Securing GenAI workloads with Kubernetes’ network policies
- Implementing network policies in a chatbot application
- Service mesh versus K8s network policies

## Optimizing network performance for GenAI
- Kube-Proxy – IPTables versus IPVS
  - IP address exhaustion issues and custom networking
- eBPF and SR-IOV
- CoreDNS
- Network latency and throughput enhancements
  - Amazon EC2 placement groups
  - EFA

## Summary

## Get This Book's PDF Version and Exclusive Extras

<!-- file: B31108_09.xhtml -->

## 9

## Security Best Practices for Deploying GenAI on Kubernetes

## Technical requirements

## Defense in depth

## K8s security considerations
- Supply chain security
  - Build phase
  - Test phase
  - Store phase
  - Encrypt phase
  - Scan phase
- Host security
- Container runtime security
- Network security
- Secrets management

## Additional considerations for GenAI apps
- Data privacy and compliance
  - IAM Roles for Service Accounts
  - Amazon EKS Pod Identity
- Secure model endpoints

## Implementing security best practices in a chatbot app

## Summary

## Get This Book's PDF Version and Exclusive Extras

<!-- file: B31108_10.xhtml -->

## 10

## Optimizing GPU Resources for GenAI Applications in Kubernetes

## Technical requirements

## GPUs and custom accelerators

## Allocating GPU resources in K8s

## Understanding GPU utilization
- NVIDIA Data Center GPU Manager (DCGM)
- GPU utilization challenges

## Techniques for partitioning and sharing GPUs
- NVIDIA MIG
- NVIDIA MPS
- GPU time-slicing

## Scaling and optimization considerations
- NVIDIA NIM
  - GPU availability in the cloud

## Summary

## Get This Book's PDF Version and Exclusive Extras

<!-- file: B31108_11.xhtml -->

## 11

## GenAIOps: Data Management and the GenAI Automation Pipeline

## Technical requirements

## Overview of GenAI pipelines

## GenAIOps on K8s
- KubeFlow
- MLflow
- Argo Workflows
- Ray
- Deploying KubeRay on a K8s cluster
- Comparing KubeFlow, MLFlow, and Ray

## Data privacy, model bias, and drift monitoring
- Methods to test bias and variance
  - Fairness and explainability libraries
  - Model drift monitoring and feedback loops
  - Drift detection and remediation

## Summary

## Join the CloudPro Newsletter with 44000+ Subscribers

<!-- file: B31108_12.xhtml -->

## 12

## Observability – Getting Visibility into GenAI on K8s

## Observability key concepts
- Logs
  - K8s audit logs
- Metrics
- Traces

## Monitoring tools in K8s
- Fluentd and Fluent Bit
- Loki
- OpenTelemetry
- Prometheus
  - Deploying the Prometheus stack
  - Enabling GPU monitoring

## Visualization and debugging
- Grafana
  - Grafana best practices
  - Setting up Grafana dashboards
    - NVIDIA DCGM dashboard
    - Ray Serve dashboard
- LangChain observability
- LangFuse

## Summary

## Get This Book's PDF Version and Exclusive Extras

<!-- file: B31108_13.xhtml -->

## 13

## High Availability and Disaster Recovery for GenAI Applications

## Designing for HA and DR
- Resiliency in K8s

## DR strategies in K8s
- Additional K8s DR considerations

## Summary

## Get This Book's PDF Version and Exclusive Extras

<!-- file: B31108_14.xhtml -->

## 14

## Wrapping Up: GenAI Coding Assistants and Further Reading

## Technical requirements

## GenAI-powered coding assistants

## GenAI-powered observability and optimization

## Amazon Q Developer walk-through with EKS

## References for further reading

## Summary

## Get This Book's PDF Version and Exclusive Extras

## Stay Sharp in Cloud and DevOps – Join 44,000+ Subscribers of CloudPro

<!-- file: B31108_15.xhtml -->

## 15

## Unlock Your Exclusive Benefits

## Unlock this Book’s Free Benefits in 3 Easy Steps
- Step 1
- Step 2
- Step 3

## Need help?

<!-- file: B31108_BM.xhtml -->

## Why subscribe?

## Other Books You May Enjoy

## Packt is searching for authors like you

## Share Your Thoughts

<!-- file: B31108_FM.xhtml -->

## Kubernetes for Generative AI Solutions

<!-- file: B31108_Index.xhtml -->

## Index

<!-- file: B31108_Part_1.xhtml -->

## Part 1:GenAI and Kubernetes Foundation

<!-- file: B31108_Part_2.xhtml -->

## Part 2: Productionalizing GenAI Workloads Using K8s

<!-- file: B31108_Part_3.xhtml -->

## Part 3: Operating GenAI Workloads on K8s

<!-- file: B31108_Preface.xhtml -->

## Preface

## Who this book is for

## What this book covers

## To get the most out of this book

## Download the example code files

## Get in touch

## Share Your Thoughts

## Stay Sharp in Cloud and DevOps – Join 44,000+ Subscribers of CloudPro

## Free Benefits with Your Book

## How to Unlock

<!-- file: B31108_TOC_ePub.xhtml -->

## Table of Contents
- Preface
  - Free Benefits with Your Book
- Part 1: GenAI and Kubernetes Foundation
- 1
- Generative AI Fundamentals
  - Artificial Intelligence versus GenAI
  - Evolution of machine learning
  - Transformer architecture
  - GenAI project life cycle
  - GenAI deployment stack
  - GenAI use cases
  - Summary
  - Appendix 1A – RNNs
  - Appendix 1B – Transformer mathematical models for the self-attention mechanism
  - Understanding the temperature parameter for GenAI use cases
- 2
- Kubernetes – Introduction and Integration with GenAI
  - Understanding containers
  - Container terminology
  - Creating a container image
  - Why containers for GenAI models?
  - Building a GenAI container image
  - What is Kubernetes (K8s)?
  - Kubernetes architecture
  - Why K8s is a great fit for GenAI models
  - Summary
  - Appendix
- 3
- Getting Started with Kubernetes in the Cloud
  - Advantages of running K8s in the cloud
  - Setting up a K8s cluster in the cloud
  - Prerequisites
  - Provisioning the Amazon EKS cluster
  - Deploying our first GenAI model in the K8s cluster
  - Summary
- Part 2: Productionalizing GenAI Workloads Using K8s
- 4
- GenAI Model Optimization for Domain-Specific Use Cases
  - Technical requirements
  - The need for domain-specific optimization
  - LLM model selection
  - The LangChain framework
  - Understanding RAG
  - How RAG works
  - Running a query
  - Model fine-tuning
  - Fine-tuning example
  - Summary
  - Further reading
- 5
- Working with GenAI on K8s: Chatbot Example
  - Technical requirements
  - GenAI use cases for e-commerce
  - Experimentation using JupyterHub
  - Fine-tuning Llama 3 in K8s
  - Data preparation
  - Creating a container image
  - Deploying the fine-tuning job
  - Deploying the fine-tuned model on K8s
  - Deploy a RAG application on K8s
  - Deploying a chatbot on K8s
  - Summary
- 6
- Scaling GenAI Applications on Kubernetes
  - Scaling metrics
  - Conventional metrics
  - Custom metrics
  - HorizonalPodAutoscaler (HPA)
  - VerticalPodAutoscaler (VPA)
  - Combining HPA and VPA
  - KEDA
  - Cluster Autoscaler (CA)
  - Karpenter
  - Summary
- 7
- Cost Optimization of GenAI Applications on Kubernetes
  - Understanding the key cost components
  - Kubecost
  - Cost optimization techniques
  - Compute best practices
  - Networking best practices
  - Storage best practices
  - Summary
  - Join the CloudPro Newsletter with 44000+ Subscribers
- 8
- Networking Best Practices for Deploying GenAI on K8s
  - Understanding the Kubernetes networking model
  - Selecting the CNI networking mode for GenAI applications
  - Service implementation in K8s
  - Service health checks
  - Advanced traffic management with a service mesh
  - Securing GenAI workloads with Kubernetes’ network policies
  - Implementing network policies in a chatbot application
  - Service mesh versus K8s network policies
  - Optimizing network performance for GenAI
  - Kube-Proxy – IPTables versus IPVS
  - eBPF and SR-IOV
  - CoreDNS
  - Network latency and throughput enhancements
  - Summary
- 9
- Security Best Practices for Deploying GenAI on Kubernetes
  - Technical requirements
  - Defense in depth
  - K8s security considerations
  - Supply chain security
  - Host security
  - Container runtime security
  - Network security
  - Secrets management
  - Additional considerations for GenAI apps
  - Data privacy and compliance
  - Secure model endpoints
  - Implementing security best practices in a chatbot app
  - Summary
- 10
- Optimizing GPU Resources for GenAI Applications in Kubernetes
  - Technical requirements
  - GPUs and custom accelerators
  - Allocating GPU resources in K8s
  - Understanding GPU utilization
  - NVIDIA Data Center GPU Manager (DCGM)
  - GPU utilization challenges
  - Techniques for partitioning and sharing GPUs
  - NVIDIA MIG
  - NVIDIA MPS
  - GPU time-slicing
  - Scaling and optimization considerations
  - NVIDIA NIM
  - Summary
- Part 3: Operating GenAI Workloads on K8s
- 11
- GenAIOps: Data Management and the GenAI Automation Pipeline
  - Technical requirements
  - Overview of GenAI pipelines
  - GenAIOps on K8s
  - KubeFlow
  - MLflow
  - Argo Workflows
  - Ray
  - Deploying KubeRay on a K8s cluster
  - Comparing KubeFlow, MLFlow, and Ray
  - Data privacy, model bias, and drift monitoring
  - Methods to test bias and variance
  - Summary
  - Join the CloudPro Newsletter with 44000+ Subscribers
- 12
- Observability – Getting Visibility into GenAI on K8s
  - Observability key concepts
  - Logs
  - Metrics
  - Traces
  - Monitoring tools in K8s
  - Fluentd and Fluent Bit
  - Loki
  - OpenTelemetry
  - Prometheus
  - Visualization and debugging
  - Grafana
  - LangChain observability
  - LangFuse
  - Summary
- 13
- High Availability and Disaster Recovery for GenAI Applications
  - Designing for HA and DR
  - Resiliency in K8s
  - DR strategies in K8s
  - Additional K8s DR considerations
  - Summary
- 14
- Wrapping Up: GenAI Coding Assistants and Further Reading
  - Technical requirements
  - GenAI-powered coding assistants
  - GenAI-powered observability and optimization
  - Amazon Q Developer walk-through with EKS
  - References for further reading
  - Summary
  - Stay Sharp in Cloud and DevOps – Join 44,000+ Subscribers of CloudPro
- 15
- Unlock Your Exclusive Benefits
- Index
- Other Books You May Enjoy

<!-- file: Section0002.xhtml -->

## Foreword

<!-- file: Section0003.xhtml -->

## Contributors

## About the authors

<!-- file: Section0004.xhtml -->

## About the reviewers

<!-- file: toc.xhtml -->
- Contents
- Landmarks
