# ansible-up-and-running-3rd-edition


<!-- file: bibliography01.xhtml -->

## Bibliography

<!-- file: ch01.xhtml -->

## Chapter 1. Introduction

## A Note About Versions

## What’s with the Name Ansible?

## Ansible: What Is It Good For?

## How Ansible Works

## What’s So Great About Ansible?
- Simple
  - Easy-to-read syntax
  - Easy to audit
  - Little to nothing to install on the remote hosts
  - Ansible scales down
  - Easy to share
  - System abstraction
  - Top to bottom tasks
- Powerful
  - Batteries included
  - Push-based
  - Multitier orchestration
  - Masterless
  - Pluggable and embeddable
  - Works with lots of stuff
  - Really scalable
- Secure
  - Codified knowledge
  - Reproducible systems
  - Equivalent environments
  - Encrypted variables
  - Secure transport
  - Idempotency
  - No daemons

## What Is Ansible, Inc.’s Relationship to Ansible?

## Is Ansible Too Simple?

## What Do I Need to Know?

## What Isn’t Covered

## Moving Forward

<!-- file: ch02.xhtml -->

## Chapter 2. Installation and Setup

## Installing Ansible
- Loose Dependencies
- Running Ansible in Containers
- Ansible Development

## Setting Up a Server for Testing
- Using Vagrant to Set Up a Test Server
- Telling Ansible About Your Servers
- Simplifying with the ansible.cfg File

## Where Should I Put My ansible.cfg File?

## Ansible and Version Control
- Kill Your Darlings

## Convenient Vagrant Configuration Options
- Port Forwarding and Private IP Addresses
- Enabling Agent Forwarding

## The Docker Provisioner

## The Ansible Local Provisioner

## When the Provisioner Runs

## Vagrant Plug-ins
- Hostmanager
- VBGuest

## VirtualBox Customization

## Vagrantfile Is Ruby

## Production Setup

## Conclusion

<!-- file: ch03.xhtml -->

## Chapter 3. Playbooks: A Beginning

## Preliminaries

## A Very Simple Playbook
- Specifying an NGINX Config File
- Creating a Web Page
- Creating a Group

## Running the Playbook

## Cowsay

## Playbooks Are YAML
- Start of Document
- End of File
- Comments
- Indentation and Whitespace
- Strings
- Booleans

## Why Don’t You Use True in One Place and Yes in Another?
- Lists
- Dictionaries
- Multiline Strings
- Pure YAML Instead of String Arguments

## Anatomy of a Playbook

## Plays
- Tasks
- Modules
- Viewing Ansible Module Documentation
- Putting It All Together

## Did Anything Change? Tracking Host State

## Getting Fancier: TLS Support

## TLS versus SSL
- Generating a TLS Certificate
- Variables
- Quoting in Ansible Strings
- Generating the NGINX Configuration Template
- Loop
- Handlers
- A Few Things to Keep in Mind About Handlers
- Testing
- Validation
- The Playbook
- Running the Playbook

## Shebang

## Conclusion

<!-- file: ch04.xhtml -->

## Chapter 4. Inventory: Describing Your Servers

## Inventory/Hosts Files
- Preliminaries: Multiple Vagrant Machines

## Behavioral Inventory Parameters
- Changing Behavioral Parameter Defaults

## Groups and Groups and Groups
- Example: Deploying a Django App
- Aliases and Ports
- Groups of Groups
- Numbered Hosts (Pets Versus Cattle)

## Hosts and Group Variables: Inside the Inventory

## Host and Group Variables: In Their Own Files

## Dynamic Inventory
- Inventory Plug-ins
- Amazon EC2
- Azure Resource Manager
- The Interface for a Dynamic Inventory Script
  - Showing host details
  - Listing groups
- Writing a Dynamic Inventory Script

## Breaking the Inventory into Multiple Files

## Adding Entries at Runtime with add_host and group_by
- add_host
- group_by

## Conclusion

<!-- file: ch05.xhtml -->

## Chapter 5. Variables and Facts

## Defining Variables in Playbooks
- Defining Variables in Separate Files
- Directory Layout

## Viewing the Values of Variables
- Variable Interpolation

## Registering Variables

## Facts
- Viewing All Facts Associated with a Server
- Viewing a Subset of Facts
- Any Module Can Return Facts or Info
- Local Facts
- Using set_fact to Define a New Variable

## Built-In Variables
- hostvars

## hostvars Versus host_vars
- inventory_hostname
- groups

## Extra Variables on the Command Line

## Precedence

## Conclusion

<!-- file: ch06.xhtml -->

## Chapter 6. Introducing Mezzanine: Our Test Application

## Why Is Deploying to Production Complicated?

## Postgres: The Database

## Gunicorn: The Application Server

## NGINX: The Web Server

## Supervisor: The Process Manager

## Conclusion

<!-- file: ch07.xhtml -->

## Chapter 7. Deploying Mezzanine with Ansible

## Listing Tasks in a Playbook

## Organization of Deployed Files

## Variables and Secret Variables

## Installing Multiple Packages

## Adding the Become Clause to a Task

## Updating the apt Cache

## Checking Out the Project Using Git

## Installing Mezzanine and Other Packages into a Virtual Environment

## Complex Arguments in Tasks: A Brief Digression

## Configuring the Database

## Generating the local_settings.py File from a Template

## Running django-manage Commands

## Running Custom Python Scripts in the Context of the Application
- Setting Service Configuration Files

## Enabling the NGINX Configuration

## Installing TLS Certificates

## Installing Twitter Cron Job

## The Full Playbook

## Running the Playbook Against a Vagrant Machine

## Troubleshooting
- Cannot Check Out Git Repository
- Cannot Reach 192.168.33.10.nip.io
- Bad Request (400)

## Conclusion

<!-- file: ch08.xhtml -->

## Chapter 8. Debugging Ansible Playbooks

## Humane Error Messages

## Debugging SSH Issues

## Common SSH Challenges
- PasswordAuthentication no
- SSH as a Different User
- Host Key Verification Failed
- Private Networks

## The debug Module

## Playbook Debugger

## The assert Module

## Checking Your Playbook Before Execution
- Syntax Check
- List Hosts
- List Tasks
- Check Mode
- Diff (Show File Changes)
- Tags
- Limits

## Conclusion

<!-- file: ch09.xhtml -->

## Chapter 9. Roles: Scaling Up Your Playbooks

## Basic Structure of a Role

## Example: Deploying Mezzanine with Roles
- Using Roles in Your Playbooks
- Pre-Tasks and Post-Tasks
- A database Role for Deploying the Database
- A mezzanine Role for Deploying Mezzanine

## Creating Role Files and Directories with ansible-galaxy

## Dependent Roles

## Ansible Galaxy
- Web Interface
- Command-Line Interface
  - Installing a role
  - Listing installed roles
  - Uninstalling a role
- Role Requirements in Practice
- Contributing Your Own Role

## Conclusion

<!-- file: ch10.xhtml -->

## Chapter 10. Complex Playbooks

## Dealing with Badly Behaved Commands

## Filters
- The default Filter
- Filters for Registered Variables
- Filters That Apply to Filepaths
- Writing Your Own Filter

## Lookups
- file
- pipe
- env
- password
- template
- csvfile
- dig
- redis
- Writing Your Own Lookup Plug-in

## More Complicated Loops
- With Lookup Plug-in
- with_lines
- with_fileglob
- with_dict
- Looping Constructs as Lookup Plug-ins

## Loop Controls
- Setting the Variable Name
- Labeling the Output

## Imports and Includes
- Dynamic Includes
- Role Includes
- Role Flow Control

## Blocks

## Error Handling with Blocks

## Encrypting Sensitive Data with ansible-vault

## Encryption at Rest
- Multiple Vaults with Different Passwords

## Conclusion

<!-- file: ch11.xhtml -->

## Chapter 11. Customizing Hosts, Runs, and Handlers

## Patterns for Specifying Hosts

## Limiting Which Hosts Run

## Running a Task on the Control Machine

## Manually Gathering Facts

## Retrieving an IP Address from the Host

## Running on One Host at a Time

## Running on a Batch of Hosts at a Time

## Running Only Once

## Limiting Which Tasks Run
- step
- start-at-task
- Running Tags
- Skipping Tags

## Running Strategies
- Linear
- Free

## Advanced Handlers
- Handlers in Pre- and Post-Tasks
- Flush Handlers
- Meta Commands
- Handlers Notifying Handlers
- Handlers Listen
- The SSL Case for the listen Feature

## Conclusion

<!-- file: ch12.xhtml -->

## Chapter 12. Managing Windows Hosts

## Connection to Windows

## PowerShell

## Windows Modules

## Our Java Development Machine

## Adding a Local User

## Windows Features

## Installing Software with Chocolatey

## Configuration of Java

## Updating Windows

## Conclusion

<!-- file: ch13.xhtml -->

## Chapter 13. Ansible and Containers

## Kubernetes

## Docker Application Life Cycle

## Registries

## Ansible and Docker

## Connecting to the Docker Daemon

## Example Application: Ghost

## Running a Docker Container on Our Local Machine

## Building an Image from a Dockerfile

## Pushing Our Image to the Docker Registry

## Orchestrating Multiple Containers on Our Local Machine

## Querying Local Images

## Deploying the Dockerized Application
- Provisioning MySQL
- Deploying the Ghost Database
- Frontend
- Frontend: Ghost
- Frontend: NGINX
- Cleaning Out Containers

## Conclusion

<!-- file: ch14.xhtml -->

## Chapter 14. Quality Assurance with Molecule

## Installation and Setup

## Configuring Molecule Drivers

## Creating an Ansible Role

## Scenarios
- Desired State
- Configuring Scenarios in Molecule
- Managing Virtual Machines
- Managing Containers

## Molecule Commands

## Linting
- YAMLlint
- ansible-lint
- ansible-later

## Verifiers
- Ansible
- Goss
- TestInfra

## Conclusion

<!-- file: ch15.xhtml -->

## Chapter 15. Collections

## Confession

## Installing Collections

## Listing Collections

## Using Collections in a Playbook

## Developing a Collection

## Conclusion

<!-- file: ch16.xhtml -->

## Chapter 16. Creating Images

## Creating Images with Packer
- Vagrant VirtualBox VM
- Combining Packer and Vagrant
- Cloud Images
- Google Cloud Platform
- Azure
- Amazon EC2
- The Playbook

## Docker Image: GCC 11

## Conclusion

<!-- file: ch17.xhtml -->

## Chapter 17. Cloud Infrastructure

## Terminology
- Instance
- Amazon Machine Image
- Tags

## Specifying Credentials
- Environment Variables
- Configuration Files

## Prerequisite: Boto3 Python Library

## Dynamic Inventory
- Inventory Caching
- Other Configuration Options

## Defining Dynamic Groups with Tags
- Applying Tags to Existing Resources
- Nicer Group Names

## Virtual Private Clouds

## Configuring ansible.cfg for Use with ec2

## Launching New Instances

## EC2 Key Pairs
- Creating a New Key
- Uploading Your Public Key

## Security Groups
- Permitted IP Addresses
- Security Group Ports

## Getting the Latest AMI

## Create a New Instance and Add It to a Group

## Returned Information

## Waiting for the Server to Come Up

## Putting It All Together

## Specifying a Virtual Private Cloud
- Dynamic Inventory and VPC

## Conclusion

<!-- file: ch18.xhtml -->

## Chapter 18. Callback Plug-ins

## Stdout Plug-ins
- ARA
- debug
- default
- dense
- json
- minimal
- null
- oneline

## Notification and Aggregate Plug-ins
- Python Requirements
- foreman
- jabber
- junit
- log_plays
- logentries
- logstash
- mail
- profile_roles
- profile_tasks
- say
- slack
- splunk
- timer

## Conclusion

<!-- file: ch19.xhtml -->

## Chapter 19. Custom Modules

## Example: Checking That You Can Reach a Remote Server
- Using the Script Module Instead of Writing Your Own
- can_reach as a Module

## Should You Develop a Module?

## Where to Put Your Custom Modules

## How Ansible Invokes Modules
- Generate a Standalone Python Script with the Arguments (Python Only)
- Copy the Module to the Host
- Create an Arguments File on the Host (Non-Python Only)
- Invoke the Module

## Expected Outputs
- Output Variables That Ansible Expects
  - changed
  - failed
  - msg

## Implementing Modules in Python
- Parsing Arguments
- Accessing Parameters
- Importing the AnsibleModule Helper Class
- Argument Options
  - required
  - default
  - choices
  - aliases
  - type
- AnsibleModule Initializer Parameters
  - argument_spec
  - no_log
  - check_invalid_arguments
  - mutually_exclusive
  - required_one_of
  - add_file_common_args
  - bypass_checks
- Returning Success or Failure
- Invoking External Commands
- Check Mode (Dry Run)

## Documenting Your Module

## Debugging Your Module

## Implementing the Module in Bash

## Specifying an Alternative Location for Bash

## Conclusion

<!-- file: ch20.xhtml -->

## Chapter 20. Making Ansible Go Even Faster

## SSH Multiplexing and ControlPersist
- Manually Enabling SSH Multiplexing
- SSH Multiplexing Options in Ansible

## More SSH Tuning
- Algorithm Recommendations

## Pipelining
- Enabling Pipelining
- Configuring Hosts for Pipelining

## Mitogen for Ansible

## Fact Caching
- JSON File Fact-Caching Backend
- Redis Fact-Caching Backend
- Memcached Fact-Caching Backend

## Parallelism

## Concurrent Tasks with Async

## Conclusion

<!-- file: ch21.xhtml -->

## Chapter 21. Networking and Security

## Network Management
- Supported Vendors
- Ansible Connection for Network Automation
- Privileged Mode
- Network Inventory
- Network Automation Use Cases

## Security
- Comply with Compliance?
- Secured, but Not Secure
- Shadow IT
- Sunshine IT
- Zero Trust

## Conclusion

<!-- file: ch22.xhtml -->

## Chapter 22. CI/CD and Ansible

## Continuous Integration
- Elements in a CI System
  - Artifact repository
  - Gitea
  - Code quality
  - CI server
  - Jenkins
- Jenkins and Ansible
  - Jenkins configuration as code
  - Jenkins job configurations as code
- Running CI for Ansible Roles

## Staging

## Ansible Plug-in

## Ansible Tower Plug-in

## Conclusion

<!-- file: ch23.xhtml -->

## Chapter 23. Ansible Automation Platform

## Subscription Models
- Ansible Automation Platform Trial

## What Ansible Automation Platform Solves
- Access Control
- Projects
- Inventory Management
- Run Jobs by Job Templates

## RESTful API

## AWX.AWX
- Installation
- Create an Organization
- Create an Inventory
- Running a Playbook with a Job Template

## Using Containers to Run Ansible
- Creating Execution Environments

## Conclusion

<!-- file: ch24.xhtml -->

## Chapter 24. Best Practices

## Simplicity, Modularity, and Composability

## Organize Content

## Decouple Inventories from Projects

## Decouple Roles and Collections

## Playbooks

## Code Style

## Tag and Test All the Things

## Desired State

## Deliver Continuously

## Security

## Deployment

## Performance Indicators

## Benchmark Evidence

## Final Words

<!-- file: colophon01.xhtml -->

## About the Authors

<!-- file: colophon02.xhtml -->

## Colophon

<!-- file: copyright-page01.xhtml -->

## Ansible: Up and Running

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
  - Q
  - R
  - S
  - T
  - U
  - V
  - W
  - Y
  - Z

<!-- file: preface01.xhtml -->

## Preface to the Third Edition

## Conventions Used in This Book

## Using Code Examples

## O’Reilly Online Learning

## How to Contact Us

## Acknowledgments
- From Lorin
- From René
- From Bas

<!-- file: titlepage01.xhtml -->

## Ansible: Up and Running
