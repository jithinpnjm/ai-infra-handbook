# network-programmability-and-automation-2nd-edition


<!-- file: ch01.xhtml -->

## Chapter 1. Network Industry Trends

## The Rise of Software-Defined Networking
- The Advent of OpenFlow

## History of Programmable Networks
- Why OpenFlow?

## What Is Software-Defined Networking?
- Opening Up the Data Plane
- Network Functions Virtualization
- Virtual Switching
- Network Virtualization
- Device APIs
- Network Automation
- Bare-Metal Switching
- Data Center Network Fabrics
- SD-WAN
- Controller Networking
- Cloud Native Networking

## Summary

<!-- file: ch02.xhtml -->

## Chapter 2. Network Automation

## Why Network Automation?
- Simplified Architectures
- Deterministic Outcomes
- Business Agility
- Enhanced Security and Risk Reduction

## Types of Network Automation
- Device Provisioning
- Data Collection and Enrichment
- Migrations
- Configuration Management

## Lessons Learned from a Network Automation Outage
- Configuration Compliance
- State Validation
- Reporting
- Troubleshooting

## Evolving the Management Plane from SNMP to APIs
- Application Programming Interfaces
  - SNMP
  - SSH/Telnet and the CLI
  - NETCONF
  - RESTful APIs
  - gNMI
- Impact of Open Networking

## Network Automation in the SDN Era

## Summary

<!-- file: ch03.xhtml -->

## Chapter 3. Linux

## Examining Linux in a Network Automation Context

## Exploring a Brief History of Linux

## Understanding Linux Distributions
- Red Hat Enterprise Linux, Fedora, CentOS, and Amazon Linux
- Debian, Ubuntu, and Other Derivatives
- Other Linux Distributions

## Interacting with Linux
- Navigating the Filesystem
- Manipulating Files and Directories
  - Creating files and directories
  - Deleting files and directories
  - Moving, copying, and renaming files and directories
  - Changing permissions
- Running Programs
- Working with Daemons
  - Starting, stopping, and restarting background services
  - Checking the status or configuration of a background service
  - Other daemon-related commands

## Networking in Linux
- Working with Interfaces
  - Interface configuration via the command line
    - Listing interfaces
    - Enabling/disabling an interface
    - Setting the MTU of an interface
    - Assigning an IP address to an interface
  - Interface configuration via configuration files
  - Using VLAN interfaces
    - Creating, configuring, and deleting VLAN interfaces
    - Use cases for VLAN interfaces
- Routing as an End Host
- Routing as a Router
- Bridging (Switching)
  - Practical use case for bridging
  - Creating and configuring Linux bridges

## Automating Linux with bash Scripting

## Evolving the Linux Kernel with eBPF and XDP

## Summary

<!-- file: ch04.xhtml -->

## Chapter 4. Cloud

## Brief Definition of Cloud Computing

## Networking Fundamentals in the Cloud
- Cloud Networking Building Blocks
- Cloud Network Topologies
  - A small cloud network topology
  - A medium cloud network topology
  - A large cloud network topology
  - A hybrid cloud network topology
- Network Automation in the Cloud
  - Using the cloud provider’s APIs
  - Using the cloud provider’s CLI tool
  - Using a tool purpose-built for automating the cloud

## Containers
- What Do Containers Have to Do with the Cloud?
- What Do Containers Have to Do with Networking?
- Extending Linux Networking for Containers
  - Linux network namespaces
  - Virtual Ethernet interfaces
  - IP masquerading

## Kubernetes
- Key Kubernetes Concepts
- Building Blocks of Networking in Kubernetes
  - Pods
  - Services
  - Ingresses
  - Other networking constructs
  - Container Network Interface
- Service Mesh

## Summary

<!-- file: ch05.xhtml -->

## Chapter 5. Network Developer Environments

## Text Editors
- Syntax Highlighting
- Customization
- Intelligent Code Analysis
- Text Editors Versus Integrated Development Environments

## Development Tools
- Virtualenv
- Make
- Docker
- dyff

## Emulation/Simulation Tools
- VirtualBox
- Vagrant
- Containerlab
- Other Tools

## Summary

<!-- file: ch06.xhtml -->

## Chapter 6. Python

## Should Network Engineers Learn to Code?

## Using the Python Interactive Interpreter

## Understanding Python Data Types
- Strings
  - Using built-in methods of strings

## Navigate the Code with type(), dir(), and help()
    - Using the upper() and lower() methods
    - Using the startswith() and endswith() methods
    - Using the strip() method
    - Using the isdigit() method
    - Using the count() method
    - Using the format() method
    - Using the join() and split() methods
- Numbers
- Booleans

## Empty Objects
- Lists
  - Using built-in methods of Python lists
    - Using the append() method
    - Using the insert() method
    - Using the count() method
    - Using the pop() and index() methods
    - Using the sort() method
- Python Dictionaries
  - Using built-in methods of Python dictionaries
    - Using the get() method
    - Using the keys() and values() methods
    - Using the pop() method
    - Using the update() method
    - Using the items() method
- Sets and Tuples

## Adding Conditional Logic to Your Code

## Understanding Containment

## Using Loops in Python
- The while Loop
- The for Loop
  - Using the enumerate() function
  - Flow control within loops

## Using Python Functions

## Working with Files
- Reading from a File
- Writing to a File

## Creating Python Programs
- Creating a Basic Python Script
- Using Comments in Python
  - Understanding the shebang
- Migrating Code from the Python Interpreter to a Python Script

## Working with Python Modules
- Documenting Functions

## Passing Arguments into a Python Script

## Using pip and Installing Python Packages
- Isolating Your Dependencies with Virtualenv

## Understanding Python Classes
- Using Classes
- Building Your Own Classes

## Embracing Failure with try/except

## Parallelizing Your Python Programs

## Summary

<!-- file: ch07.xhtml -->

## Chapter 7. Go

## Why Go?
- Is Go Faster Than Python?
- Is Go Harder than Python?

## Fundamental Go Concepts
- Types and Variables
  - Variables in Go
  - Static versus dynamic type systems
- Flow Control
- Collection Types
- Functions
- Structs
- Methods
- Interfaces

## Advanced Concepts
- Concurrency
- Generics

## Packages and Modules
- Standard Library Packages
  - strings
  - strconv
  - regexp
  - encoding
  - net
  - time
  - os
- Third-Party Modules and Packages

## Summary

<!-- file: ch08.xhtml -->

## Chapter 8. Data Formats and Models

## Benefits and Fundamentals of Structured Data Formats
- When Structured Data Isn’t Available: Screen Scraping
- Types of Data
- Documents Versus Data
- Categories of Data Formats

## Text-Based Data Formats
- YAML
  - Working with YAML in Python
- XML
  - Working with XML in Python
- JSON
  - Working with JSON in Python

## Binary Data Formats
- Protocol Buffers
  - Protobuf definitions
  - Protobuf tooling and code generation
- Other Binary Data Formats

## Data Modeling
- YANG
- JSON Schema
- XML Schema Definition
- Modeling and Validating Protocol Buffers

## Summary

<!-- file: ch09.xhtml -->

## Chapter 9. Templates

## The Rise of Modern Template Languages
- Using Templates for Web Development
- Expanding On the Use of Templates

## The Value of Templates in Network Automation

## Jinja
- Rendering a Jinja Template File in Python
- Using Conditionals and Loops
  - Using conditional logic to create a switchport configuration
  - Using a loop to create many switchport configurations
  - Using a loop and conditionals to create switchport configurations
  - Iterating over a dictionary to generate configurations
  - Generating interface configurations from a list of dictionaries
- Using Jinja Filters
  - Using the upper Jinja filter
  - Chaining Jinja filters
  - Creating custom Jinja filters
- Template Inheritance in Jinja
- Variable Creation in Jinja

## Extensible Stylesheet Language Transformations

## Go Templates

## Summary

<!-- file: ch10.xhtml -->

## Chapter 10. Working with Network APIs

## Understanding Network APIs
- Getting Familiar with HTTP-Based APIs
  - Understanding RESTful APIs
    - Understanding HTTP request types
    - Understanding HTTP response codes
  - Exploring HTTP-based APIs with cURL
    - Using the HTTP GET method to retrieve information
    - Using the HTTP POST method to create a new resource
  - Understanding non-RESTful HTTP-based APIs
- Using NETCONF
  - Learning the NETCONF protocol stack
    - Transport
    - Messages
    - Operations
    - Content
  - Exploring NETCONF
    - NETCONF with Junos
    - NETCONF with Cisco IOS XE
- Using RESTCONF
  - Exploring RESTCONF in Cisco IOS XE
    - Updating configuration via RESTCONF
    - Understanding the YANG PATCH HTTP operation
    - Discovering RESTCONF operations
- Using gRPC and gNMI
  - Understanding gRPC
  - A gRPC example
    - Running a gRPC server in Go
    - Running a gRPC client in Python
  - Understanding the gNMI interface
  - Exploring gNMI with gNMIc
    - gNMI GetRequest
    - gNMI SetRequest
    - gNMI Subscribe
- Comparing NETCONF, RESTCONF, and gNMI
  - Network interfaces development lifecycle
  - Understanding model-driven telemetry

## Using Network APIs for Automation
- The Python Requests Library
  - Automating the Meraki API with Requests
  - Consuming eAPI in a Python script
    - Using eAPI to autoconfigure interface descriptions based on LLDP data
  - Using API SDKs
    - Exploring the Meraki API SDK
- The Go net/http Package
  - Using net/http with RESTCONF
  - Updating configuration via RESTCONF with net/http
- The Python ncclient Library
  - Understanding the Manager object
  - Retrieving Juniper vMX device configurations with ncclient
    - Using findall() to retrieve multiple XML objects
  - Making Junos vMX configuration changes with ncclient
    - Performing NETCONF delete/replace operations with the ncclient
  - Using ncclient with Cisco IOS XE
  - Understanding vendor-specific NETCONF operations
- The OpenConfig gNMIc Go Package
  - Using OpenConfig gNMIc to perform a gNMI Get operation
  - Using OpenConfig gNMIc to perform a gNMI Set operation
  - Using OpenConfig gNMIc to subscribe to events
- The Netmiko Python Library
  - Verifying the device prompt
  - Entering configuration mode
  - Sending commands
  - Empowering Netmiko with TextFSM and NTC Templates

## Summary

<!-- file: ch11.xhtml -->

## Chapter 11. Source Control with Git

## Use Cases for Source Control

## Benefits of Source Control
- Change Tracking
- Accountability
- Process and Workflow

## Benefits of Source Control for Networking

## Enter Git
- Brief History of Git
- Git Terminology
- Overview of Git’s Architecture

## Working with Git
- Installing Git
- Creating a Repository
- Adding Files to a Repository
- Committing Changes to a Repository
  - Providing user information to Git
  - Committing changes
  - Recommendations for committing changes
  - Amending commits
- Changing and Committing Tracked Files
- Unstaging Files
- Excluding Files from a Repository
  - Excluding files per repository
  - Excluding files globally
- Viewing More Information About a Repository
  - Viewing basic log information
  - Viewing brief log information
  - Drilling into information on specific commits
- Distilling Differences Between Versions of Files
  - Examining differences between commits
  - Viewing other types of differences
- Tagging Commits in Git

## Branching in Git
- Renaming the Default Branch
- Creating a Branch
- Checking Out a Branch

## Viewing Git Branch Information in the Prompt
- Stashing Uncommitted Changes
- Merging and Deleting Branches
  - Reviewing fast-forward merges
  - Deleting a branch
  - Reviewing merges with a merge commit
  - Rebasing to avoid merge commits

## Collaborating with Git
- Collaborating Between Multiple Systems Running Git
  - Linking repositories with remotes
  - Fetching and merging information from remote repositories
  - Pulling information from remote repositories
  - Cloning repositories
  - Extending our working model across multiple systems
  - Using a shared repository
  - Pushing changes to a shared repository
- Collaborating via Git-Based Online Services
  - Forking repositories
  - Keeping forked repositories in sync
  - Creating pull requests

## Summary

<!-- file: ch12.xhtml -->

## Chapter 12. Automation Tools

## Reviewing Automation Tools

## Using Ansible
- Discovering the Ansible Framework
- Understanding How Ansible Works
  - Automating Linux servers
  - Automating network devices
- Constructing an Inventory File
  - Working with inventory groups
  - Using nested groups in an inventory file
  - Using variables in Ansible
    - Managing group variables
    - Managing host variables
    - Understanding variable priority
    - Getting familiar with the all group
- Executing an Ansible Playbook
  - Getting familiar with Ansible tasks and modules
  - Executing a playbook
- Using Secrets
- Using Variable Files
  - Group-based variable files
  - Host-based variable files
- Writing Ansible Playbooks for Network Automation
  - Breaking down common core network modules
  - Creating and using configuration templates
    - Creating variable files
    - Creating Jinja templates
    - Generating network configuration files
  - Ensuring that a configuration exists
    - Understanding idempotency
    - Using the config module
    - Understanding check mode, verbosity, and limit
  - Filtering tasks with when
  - Gathering and viewing network data
    - Using the core facts modules
    - Using the debug module
  - Issuing show commands and writing data to a file
    - Using the register task attribute
  - Performing compliance checks
  - Generating reports

## Ansible Roles
- Using Third-Party Collections and Modules
  - Getting familiar with NAPALM modules
  - Getting familiar with NTC modules
  - Installing third-party collections and modules
- Ansible Summary

## Automating with Nornir
- Getting Started with Nornir
  - Initializing Nornir
  - Defining the inventory
    - host_file
    - group_file
  - Executing tasks
  - Extending Nornir with plug-ins
- Using NAPALM with Nornir
  - Understanding NAPALM
  - Retrieving operational data with NAPALM
  - Configuration management at scale
- Nornir Summary

## Managing Dynamic Infrastructure with Terraform
- Understanding Terraform Architecture
  - Terraform configuration language
  - Terraform in a nutshell
  - Terraform workflow
- Provisioning Your First Resource with Terraform
  - Setting up an AWS free account
  - Using Terraform providers
  - Validating the Terraform syntax
  - Initializing the Terraform environment
  - Getting insights into Terraform changes
  - Applying the Terraform configuration
  - Understanding Terraform state
  - Remediating Terraform state
  - Cleaning up infrastructure with Terraform
- Extending Terraform Execution
  - Adding resource dependencies
  - Handling data validation
  - Using Terraform functions
  - Creating multiple resources in a loop
- Managing Terraform at Scale
  - Using data sources to get data from nonmanaged infrastructure
  - Using Terraform variables
  - Defining variables programmatically
  - Using workspaces
  - Using modules to improve reusability
- Terraform Out of Its Comfort Zone
  - Using Terraform provisioners
  - Using Terraform to manage network devices
- Terraform Summary

## Summary

<!-- file: ch13.xhtml -->

## Chapter 13. Continuous Integration

## Important Prerequisites
- Simple Is Better
- People, Process, and Technology
- Learn to Code

## Introduction to Continuous Integration
- Basics of Continuous Integration
- Continuous Delivery
- Test-Driven Development
- Why Continuous Integration for Networking?

## A Continuous Integration Pipeline for Networking
- Peer Review
- Build Automation
- Deployment Validation and Testing
- Test/Dev/Staging Environment
- Deployment Tools and Strategies

## Summary

<!-- file: ch14.xhtml -->

## Chapter 14. Network Automation Architecture

## Introducing the Network Automation Architecture

## Overview of the Architecture Components
- User Interactions
  - Graphical user interfaces
    - IT service management
    - Dashboards
    - ChatOps
  - Text-based interactions
  - Documentation and reporting
- Source of Truth
  - Data quality
  - Data use cases
    - Network inventory

## REST API Versus GraphQL
    - Data center infrastructure management
    - IP address management
    - Network properties
    - Configuration templates
  - Data modeling
    - A structured approach
    - Data modeling example
  - Data Persistence
    - Version control systems
    - Databases
    - When to use Git or a database
  - Data population
    - Brownfield environments
    - Greenfield environments
  - Distributed source of truth
- Automation Engine
  - Configuration management
    - Configuration backup
    - Configuration rendering
    - Configuration compliance
    - Configuration deployment
  - Operations
- Telemetry and Observability
  - Operational state data
    - Metrics
    - Logs
    - Traces
    - Flows
    - Packet capture
  - Options to collect network operational data
    - SNMP
    - Syslog and flow exporters
    - CLI
    - Model-driven telemetry
    - REST API
    - Network protocols
    - Synthetic monitoring
  - Telemetry and observability stack
  - Collector
  - SoT enrichment
  - Data distribution and processing
  - Storage
  - Visualization
  - Alerting
- Orchestration
  - Event-driven automation

## Understanding the Architecture with an Example
- Determine the Operation’s Workflow
- Translate the Workflow Steps to Automated Tasks
- Map the Automated Tasks to Architecture Components
- Choose the Tools to Implement Each Component’s Tasks

## Summary

<!-- file: colophon01.xhtml -->

## About the Authors

<!-- file: colophon02.xhtml -->

## Colophon

<!-- file: copyright-page01.xhtml -->

## Network Programmability and Automation

## Revision History for the Second Edition

<!-- file: dedication01.xhtml -->

## Praise for Network Programmability and Automation

<!-- file: dedication02.xhtml -->

## Dedication

<!-- file: ix01.xhtml -->

## Index
  - Symbols
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
  - X
  - Y
  - Z

<!-- file: preface01.xhtml -->

## Preface

## What This Book Covers
- What’s New in This Edition

## How This Book Is Organized

## Who Should Read This Book
- Network Engineers
  - Prerequisites
- Systems Administrators
  - Prerequisites
- Software Developers
  - Prerequisites

## Tools Used in This Book

## Online Resources

## Conventions Used in This Book

## Using Code Examples

## O’Reilly Online Learning

## How to Contact Us

## Acknowledgments

<!-- file: titlepage01.xhtml -->

## Network Programmability and Automation
