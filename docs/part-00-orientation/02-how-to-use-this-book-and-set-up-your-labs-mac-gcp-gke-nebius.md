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

You open a chapter and find a diagram, some commands and a section called "how it fails". Here is what each piece is for.

Each chapter moves from basics to intermediate to advanced, so you can stop at the level you need. Most chapters contain a mental-model diagram, a picture of how the parts fit together. They also contain the commands and configurations that matter, a "how it fails" section that walks through a symptom, its diagnosis and its fix, a lab, and checkpoint questions with answers and sources. Output shown as *illustrative* or *untested here* was not captured from live hardware. Read it as an example of the shape of the output, and verify it on your own system before relying on it.

Hardware numbers, such as bandwidths, power draw and part names, change from one generation of chips to the next. Before you size anything for a purchase or a deployment, check the vendor's current documentation.

## Three lab venues

Which lab suits a namespace exercise? The book runs labs in three places, and each one is good at some work and weak at others.

| Venue | Cost | Good for | Not good for |
|---|---|---|---|
| **Mac (local)** | Free | Python, shell, Git, Ansible, Terraform plan, Docker or kind, reading code | Linux kernel features, GPUs, RDMA |
| **GCP VM / GKE** | Pay per hour | Real Linux, namespaces and cgroups, Kubernetes, small GPU nodes | Multi-node InfiniBand |
| **Nebius (or similar GPU cloud)** | Highest | CUDA, `nvidia-smi`, DCGM, NCCL on real GPUs, vLLM | Anything that needs bare-metal BMC access |

Each chapter states its venue in the front matter (`lab_venue`). Check that field before you start, so you set up the right place first.

## Minimum setup

It is your first evening with the book, and you want the tools in place first.

1. **Mac:** install Homebrew, then Git, Python 3, Docker Desktop (or Colima), `kubectl`, `helm`, Terraform and Ansible.
2. **GCP:** create a project, set a billing budget alert **first**, install the `gcloud` CLI, and enable the Compute and Kubernetes APIs.
3. **Nebius:** create an account and a project, install its CLI, and start with the smallest GPU instance that satisfies the lab.

You do not need all three platforms on day one.

```bash
# Mac sanity check
git --version && python3 --version && docker --version && kubectl version --client
# GCP sanity check
gcloud config list && gcloud compute instances list
```

Each check prints a version or a list. If a command is not found, install that tool before you go on.

## Keep cloud labs cheap and safe

A bill arrives with a line for a GPU node nobody remembers creating.

- Set a budget alert before creating anything.
- Tag or label every resource with the chapter number so you can find leftovers.
- Create with Terraform where possible (Part 4) so teardown is one command.
- Delete GPU instances and GKE node pools the moment the lab ends; stopped GPU VMs may still incur disk and IP charges.
- Never put credentials in Git. Use environment variables, a secrets manager or workload identity.

## How it fails

A lab that worked last week fails today.

- **Surprise bill:** a forgotten GPU node. Fix: budget alerts and an end-of-day `list` command habit.
- **Quota denied:** new projects often have zero GPU quota. Request it early; approval can take time.
- **Lab differs from the book:** driver, CUDA or image versions drift. Pin versions as the lab states and compare before debugging.

## Checkpoint questions

Before you move on, these three questions check that the venues and the cost rules have sunk in.

1. Which venue can you use for namespaces and cgroups labs? *A GCP VM (real Linux), not macOS.*
2. What should you configure before creating cloud resources? *A billing budget alert.*
3. What does "untested here" on an output block mean? *It was not captured on live hardware; verify yourself.*
