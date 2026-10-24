# terraform-up-and-running-3rd-edition


<!-- file: app01.xhtml -->

## Appendix A. Recommended Reading

## Books

## Blogs

## Talks

## Newsletters

## Online Forums

<!-- file: ch01.xhtml -->

## Chapter 1. Why Terraform

## What Is DevOps?

## What Is Infrastructure as Code?
- Ad Hoc Scripts
- Configuration Management Tools
- Server Templating Tools
- Orchestration Tools
- Provisioning Tools

## What Are the Benefits of Infrastructure as Code?

## How Does Terraform Work?

## Transparent Portability Between Cloud Providers

## How Does Terraform Compare to Other IaC Tools?
- Configuration Management Versus Provisioning
- Mutable Infrastructure Versus Immutable Infrastructure
- Procedural Language Versus Declarative Language
- General-Purpose Language Versus Domain-Specific Language
- Master Versus Masterless
- Agent Versus Agentless
- Paid Versus Free Offering
- Large Community Versus Small Community
- Mature Versus Cutting Edge
- Use of Multiple Tools Together
  - Provisioning plus configuration management
  - Provisioning plus server templating
  - Provisioning plus server templating plus orchestration

## Conclusion

<!-- file: ch02.xhtml -->

## Chapter 2. Getting Started with Terraform

## Example Code

## Setting Up Your AWS Account

## A Note on Default Virtual Private Clouds

## Installing Terraform

## Other AWS Authentication Options

## Deploying a Single Server

## Use the Docs!

## Deploying a Single Web Server

## Port Numbers

## Deploying a Configurable Web Server

## Deploying a Cluster of Web Servers

## Deploying a Load Balancer

## Cleanup

## Conclusion

<!-- file: ch03.xhtml -->

## Chapter 3. How to Manage Terraform State

## Example Code

## What Is Terraform State?

## The State File Is a Private API

## Shared Storage for State Files

## Limitations with Terraform’s Backends

## State File Isolation
- Isolation via Workspaces
- Isolation via File Layout

## The terraform_remote_state Data Source

## Conclusion

<!-- file: ch04.xhtml -->

## Chapter 4. How to Create Reusable Infrastructure with Terraform Modules

## Example Code

## Module Basics

## Module Inputs

## Module Locals

## Module Outputs

## Module Gotchas
- File Paths
- Inline Blocks

## Module Versioning

## Private Git Repos

## Developing Modules

## Conclusion

<!-- file: ch05.xhtml -->

## Chapter 5. Terraform Tips and Tricks: Loops, If-Statements, Deployment, and Gotchas

## Example Code

## Loops
- Loops with the count Parameter
- Loops with for_each Expressions
- Loops with for Expressions
- Loops with the for String Directive

## Conditionals
- Conditionals with the count Parameter
  - If-statements with the count parameter
  - If-else-statements with the count parameter
- Conditionals with for_each and for Expressions
- Conditionals with the if String Directive

## Zero-Downtime Deployment

## Terraform Gotchas
- count and for_each Have Limitations
- Zero-Downtime Deployment Has Limitations
- Valid Plans Can Fail
- Refactoring Can Be Tricky

## Conclusion

<!-- file: ch06.xhtml -->

## Chapter 6. Managing Secrets with Terraform

## Secret Management Basics

## Secret Management Tools
- The Types of Secrets You Store
- The Way You Store Secrets
- The Interface You Use to Access Secrets
- A Comparison of Secret Management Tools

## Secret Management Tools with Terraform
- Providers
  - Human users
  - Machine users

## Warning: Simplified Examples
    - CircleCI as a CI server, with stored secrets
    - EC2 Instance running Jenkins as a CI server, with IAM roles
    - GitHub Actions as a CI server, with OIDC
- Resources and Data Sources
  - Environment variables
  - Encrypted files
  - Secret stores
- State Files and Plan Files
  - State files
  - Plan files

## Conclusion

<!-- file: ch07.xhtml -->

## Chapter 7. Working with Multiple Providers

## Working with One Provider
- What Is a Provider?
- How Do You Install Providers?

## Always Include required_providers
- How Do You Use Providers?

## Working with Multiple Copies of the Same Provider
- Working with Multiple AWS Regions
- Working with Multiple AWS Accounts
- Creating Modules That Can Work with Multiple Providers

## Working with Multiple Different Providers
- A Crash Course on Docker

## Cleaning Up Containers
- A Crash Course on Kubernetes
- Deploying Docker Containers in AWS Using Elastic Kubernetes Service

## Conclusion

<!-- file: ch08.xhtml -->

## Chapter 8. Production-Grade Terraform Code

## Example Code

## Why It Takes So Long to Build Production-Grade Infrastructure

## The Production-Grade Infrastructure Checklist

## Production-Grade Infrastructure Modules
- Small Modules
- Composable Modules
- Testable Modules
  - Validations
  - Preconditions and postconditions
  - When to use validations, preconditions, and postconditions
- Versioned Modules

## tfenv on Apple Silicon (M1, M2)

## Lock Files with Multiple Operating Systems
- Beyond Terraform Modules
  - Provisioners
  - Provisioners with null_resource
  - External data source

## Conclusion

<!-- file: ch09.xhtml -->

## Chapter 9. How to Test Terraform Code

## Example Code

## Manual Tests
- Manual Testing Basics

## Validating Infrastructure
- Cleaning Up After Tests

## Warning: Lots of Coding Ahead

## Automated Tests
- Unit Tests
  - Unit testing Terraform code

## Terratest Version
  - Dependency injection
  - Running tests in parallel

## Running Tests in Parallel in the Same Folder
- Integration Tests
  - Test stages
  - Retries
- End-to-End Tests
- Other Testing Approaches
  - Static analysis
  - Plan testing
  - Server testing

## Conclusion

## This Book Has Tests, Too!

<!-- file: ch10.xhtml -->

## Chapter 10. How to Use Terraform as a Team

## Example Code

## Adopting IaC in Your Team
- Convince Your Boss
- Work Incrementally
- Give Your Team the Time to Learn

## A Workflow for Deploying Application Code
- Use Version Control
- Run the Code Locally
- Make Code Changes
- Submit Changes for Review
- Run Automated Tests
- Merge and Release
- Deploy
  - Deployment tooling
  - Deployment strategies
  - Deployment server
  - Promotion across environments

## A Workflow for Deploying Infrastructure Code
- Use Version Control
  - Live repo and modules repo
  - The Golden Rule of Terraform
  - The trouble with branches
- Run the Code Locally
- Make Code Changes
- Submit Changes for Review
  - Documentation
  - Automated tests
  - File layout
  - Style guide
- Run Automated Tests
- Merge and Release
- Deploy
  - Deployment tooling
  - Deployment strategies
  - Deployment server
  - Promote artifacts across environments

## Putting It All Together

## Conclusion

<!-- file: colophon01.xhtml -->

## About the Author

<!-- file: colophon02.xhtml -->

## Colophon

<!-- file: copyright-page01.xhtml -->

## Terraform: Up & Running

## Revision History for the Third Edition

<!-- file: dedication01.xhtml -->

## Dedication

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
  - Y
  - Z

<!-- file: preface01.xhtml -->

## Preface

## Who Should Read This Book

## Why I Wrote This Book

## What You Will Find in This Book

## Changes from the Second Edition to the Third Edition

## Changes from the First Edition to the Second Edition

## What You Won’t Find in This Book

## Open Source Code Examples

## Using the Code Examples

## Conventions Used in This Book

## O’Reilly Online Learning

## How to Contact O’Reilly Media

## Acknowledgments

<!-- file: titlepage01.xhtml -->

## Terraform: Up & Running
