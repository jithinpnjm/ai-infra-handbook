---
id: "c00-02"
title: "0.2 How to use this book and set up your labs (Mac, GCP/GKE, Nebius)"
sidebar_label: "0.2 How to use this book and set up your labs (Mac, GCP/GKE, Nebius)"
sidebar_position: 2
description: "How to read this book, the chapter structure, and how to set up Mac, GCP/GKE and Nebius lab environments."
status: "drafted"
tier: "2"
level: "B"
lab_venue: "Mac"
---

# 0.2 How to use this book and set up your labs (Mac, GCP/GKE, Nebius)

## How chapters are built

Each chapter goes basics, then intermediate, then advanced. Most contain: a mental-model diagram, the commands and configurations that matter, a "how it fails" section (symptom, diagnosis, fix), a lab, checkpoint questions with answers and sources. Output shown as *illustrative* or *untested here* was not captured from live hardware; verify it on your own system before relying on it.

Hardware-specific numbers (bandwidths, power, part names) change between generations. Treat them as a snapshot and check the vendor's current documentation before sizing anything.

## Three lab venues

| Venue | Cost | Good for | Not good for |
|---|---|---|---|
| **Mac (local)** | Free | Python, shell, Git, Ansible, Terraform plan, Docker or kind, reading code | Linux kernel features, GPUs, RDMA |
| **GCP VM / GKE** | Pay per hour | Real Linux, namespaces and cgroups, Kubernetes, small GPU nodes | Multi-node InfiniBand |
| **Nebius (or similar GPU cloud)** | Highest | CUDA, `nvidia-smi`, DCGM, NCCL on real GPUs, vLLM | Anything that needs bare-metal BMC access |

Each chapter states its venue in the front matter (`lab_venue`).

## Minimum setup

1. **Mac:** install Homebrew, then Git, Python 3, Docker Desktop (or Colima), `kubectl`, `helm`, Terraform and Ansible.
2. **GCP:** create a project, set a billing budget alert **first**, install the `gcloud` CLI, and enable the Compute and Kubernetes APIs.
3. **Nebius:** create an account and a project, install its CLI, and start with the smallest GPU instance that satisfies the lab.

```bash
# Mac sanity check
git --version && python3 --version && docker --version && kubectl version --client
# GCP sanity check
gcloud config list && gcloud compute instances list
```

## Keep cloud labs cheap and safe

- Set a budget alert before creating anything.
- Tag or label every resource with the chapter number so you can find leftovers.
- Create with Terraform where possible (Part 4) so teardown is one command.
- Delete GPU instances and GKE node pools the moment the lab ends; stopped GPU VMs may still incur disk and IP charges.
- Never put credentials in Git. Use environment variables, a secrets manager or workload identity.

## How it fails

- **Surprise bill:** a forgotten GPU node. Fix: budget alerts and an end-of-day `list` command habit.
- **Quota denied:** new projects often have zero GPU quota. Request it early; approval can take time.
- **Lab differs from the book:** driver, CUDA or image versions drift. Pin versions as the lab states and compare before debugging.

## Checkpoint questions

1. Which venue can you use for namespaces and cgroups labs? *A GCP VM (real Linux), not macOS.*
2. What should you configure before creating cloud resources? *A billing budget alert.*
3. What does "untested here" on an output block mean? *It was not captured on live hardware; verify yourself.*
