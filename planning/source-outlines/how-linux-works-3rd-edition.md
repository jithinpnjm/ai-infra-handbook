# how-linux-works-3rd-edition


<!-- file: b01.xhtml -->

## Bibliography

<!-- file: b02.xhtml -->

## Index

<!-- file: c01.xhtml -->

## 1 The Big Picture
- 1.1 Levels and Layers of Abstraction in a Linux System
- NOTE
- 1.2 Hardware: Understanding Main Memory
- NOTE
- 1.3 The Kernel
- NOTE
  - 1.3.1 Process Management
  - 1.3.2 Memory Management
- NOTE
  - 1.3.3 Device Drivers and Management
  - 1.3.4 System Calls and Support
- NOTE
- NOTE
- 1.4 User Space
- 1.5 Users
- NOTE
- 1.6 Looking Forward

<!-- file: c02.xhtml -->

## 2 Basic Commands and Directory Hierarchy
- NOTE
- 2.1 The Bourne Shell: /bin/sh
- NOTE
- 2.2 Using the Shell
  - 2.2.1 The Shell Window
- NOTE
  - 2.2.2 cat
  - 2.2.3 Standard Input and Standard Output
- NOTE
- 2.3 Basic Commands
  - 2.3.1 ls
  - 2.3.2 cp
  - 2.3.3 mv
  - 2.3.4 touch
  - 2.3.5 rm
  - 2.3.6 echo
- 2.4 Navigating Directories
  - 2.4.1 cd
- NOTE
  - 2.4.2 mkdir
  - 2.4.3 rmdir
  - 2.4.4 Shell Globbing (“Wildcards”)
- NOTE
- NOTE
- 2.5 Intermediate Commands
  - 2.5.1 grep
- NOTE
  - 2.5.2 less
- NOTE
  - 2.5.3 pwd
  - 2.5.4 diff
  - 2.5.5 file
  - 2.5.6 find and locate
  - 2.5.7 head and tail
  - 2.5.8 sort
- 2.6 Changing Your Password and Shell
- 2.7 Dot Files
- NOTE
- 2.8 Environment and Shell Variables
- NOTE
- 2.9 The Command Path
- NOTE
- 2.10 Special Characters
- NOTE
- 2.11 Command-Line Editing
- 2.12 Text Editors
- NOTE
- 2.13 Getting Online Help
- NOTE
- 2.14 Shell Input and Output
  - 2.14.1 Standard Error
  - 2.14.2 Standard Input Redirection
- 2.15 Understanding Error Messages
  - 2.15.1 Anatomy of a Unix Error Message
- NOTE
  - 2.15.2 Common Errors
    - No such file or directory
- NOTE
    - File exists
    - Not a directory, Is a directory
    - No space left on device
    - Permission denied
    - Operation not permitted
    - Segmentation fault, Bus error
- 2.16 Listing and Manipulating Processes
- NOTE
  - 2.16.1 ps Command Options
  - 2.16.2 Process Termination
- NOTE
  - 2.16.3 Job Control
- NOTE
  - 2.16.4 Background Processes
- NOTE
- 2.17 File Modes and Permissions
- NOTE
  - 2.17.1 Modifying Permissions
- NOTE
  - 2.17.2 Working with Symbolic Links
- WARNING
- 2.18 Archiving and Compressing Files
  - 2.18.1 gzip
  - 2.18.2 tar
    - Unpacking .tar Files
- NOTE
    - Using Table-of-Contents Mode
  - 2.18.3 Compressed Archives (.tar.gz)
  - 2.18.4 zcat
- NOTE
  - 2.18.5 Other Compression Utilities
- 2.19 Linux Directory Hierarchy Essentials
  - 2.19.1 Other Root Subdirectories
  - 2.19.2 The /usr Directory
  - 2.19.3 Kernel Location
- 2.20 Running Commands as the Superuser
  - 2.20.1 sudo
  - 2.20.2 /etc/sudoers
- NOTE
  - 2.20.3 sudo Logs
- 2.21 Looking Forward

<!-- file: c03.xhtml -->

## 3 Devices
- 3.1 Device Files
- NOTE
- 3.2 The sysfs Device Path
- 3.3 dd and Devices
- WARNING
- 3.4 Device Name Summary
  - 3.4.1 Hard Disks: /dev/sd*
  - 3.4.2 Virtual Disks: /dev/xvd*, /dev/vd*
  - 3.4.3 Non-Volatile Memory Devices: /dev/nvme*
  - 3.4.4 Device Mapper: /dev/dm-*, /dev/mapper/*
  - 3.4.5 CD and DVD Drives: /dev/sr*
  - 3.4.6 PATA Hard Disks: /dev/hd*
  - 3.4.7 Terminals: /dev/tty*, /dev/pts/*, and /dev/tty
    - Display Modes and Virtual Consoles
- NOTE
  - 3.4.8 Serial Ports: /dev/ttyS*, /dev/ttyUSB*, /dev/ttyACM*
  - 3.4.9 Parallel Ports: /dev/lp0 and /dev/lp1
  - 3.4.10 Audio Devices: /dev/snd/*, /dev/dsp, /dev/audio, and More
- NOTE
  - 3.4.11 Device File Creation
- 3.5 udev
- NOTE
  - 3.5.1 devtmpfs
- NOTE
  - 3.5.2 udevd Operation and Configuration
  - 3.5.3 udevadm
  - 3.5.4 Device Monitoring
- 3.6 In-Depth: SCSI and the Linux Kernel
- NOTE
  - 3.6.1 USB Storage and SCSI
  - 3.6.2 SCSI and ATA
  - 3.6.3 Generic SCSI Devices
  - 3.6.4 Multiple Access Methods for a Single Device

<!-- file: c04.xhtml -->

## 4 Disks and Filesystems
- NOTE
- 4.1 Partitioning Disk Devices
- NOTE
  - 4.1.1 Viewing a Partition Table
- NOTE
    - MBR Basics
- NOTE
    - LVM Partitions: A Sneak Peek
- NOTE
    - Initial Kernel Read
  - 4.1.2 Modifying Partition Tables
- Forcing a Partition Table Reload
  - 4.1.3 Creating a Partition Table
  - 4.1.4 Navigating Disk and Partition Geometry
- NOTE
- NOTE
- Are Cylinder Boundaries Important?
  - 4.1.5 Reading from Solid-State Disks
- 4.2 Filesystems
  - 4.2.1 Filesystem Types
- Linux Filesystem Evolution
  - 4.2.2 Creating a Filesystem
- WARNING
- What Is mkfs?
  - 4.2.3 Mounting a Filesystem
- NOTE
  - 4.2.4 Filesystem UUID
  - 4.2.5 Disk Buffering, Caching, and Filesystems
  - 4.2.6 Filesystem Mount Options
    - Short General Options
    - Long Options
- NOTE
  - 4.2.7 Remounting a Filesystem
  - 4.2.8 The /etc/fstab Filesystem Table
  - 4.2.9 Alternatives to /etc/fstab
  - 4.2.10 Filesystem Capacity
- NOTE
- Getting a Usage Listing
- NOTE
  - 4.2.11 Checking and Repairing Filesystems
- WARNING
    - Checking ext3 and ext4 Filesystems
    - The Worst Case
  - 4.2.12 Special-Purpose Filesystems
- 4.3 Swap Space
  - 4.3.1 Using a Disk Partition as Swap Space
  - 4.3.2 Using a File as Swap Space
  - 4.3.3 Determining How Much Swap You Need
- NOTE
- 4.4 The Logical Volume Manager
  - 4.4.1 Working with LVM
    - Listing and Understanding Volume Groups
    - Listing Logical Volumes
    - Using Logical Volume Devices
- NOTE
    - Working with Physical Volumes
    - Constructing a Logical Volume System
    - Creating Physical Volumes and a Volume Group
- NOTE
- NOTE
    - Creating Logical Volumes
    - Manipulating Logical Volumes: Creating Partitions
    - Removing Logical Volumes
- WARNING
    - Resizing Logical Volumes and Filesystems
  - 4.4.2 The LVM Implementation
    - LVM Utilities and Scanning for Physical Volumes
- NOTE
    - The Device Mapper
- NOTE
- 4.5 Looking Forward: Disks and User Space
- 4.6 Inside a Traditional Filesystem
- NOTE
  - 4.6.1 Inode Details and the Link Count
  - 4.6.2 Block Allocation
  - 4.6.3 Working with Filesystems in User Space

<!-- file: c05.xhtml -->

## 5 How the Linux Kernel Boots
- 5.1 Startup Messages
- 5.2 Kernel Initialization and Boot Options
- 5.3 Kernel Parameters
- 5.4 Boot Loaders
- NOTE
  - 5.4.1 Boot Loader Tasks
  - 5.4.2 Boot Loader Overview
- 5.5 GRUB Introduction
- NOTE
  - 5.5.1 Exploring Devices and Partitions with the GRUB Command Line
    - Listing Devices
    - File Navigation
- NOTE
  - 5.5.2 GRUB Configuration
    - Reviewing grub.cfg
- NOTE
    - Generating a New Configuration File
- NOTE
  - 5.5.3 GRUB Installation
    - Installing GRUB on Your System
- WARNING
    - Installing GRUB Using MBR on an External Storage Device
    - Installing GRUB with UEFI
- 5.6 UEFI Secure Boot Problems
- 5.7 Chainloading Other Operating Systems
- 5.8 Boot Loader Details
  - 5.8.1 MBR Boot
  - 5.8.2 UEFI Boot
- NOTE
  - 5.8.3 How GRUB Works

<!-- file: c06.xhtml -->

## 6 How User Space Starts
- 6.1 Introduction to init
- 6.2 Identifying Your init
- 6.3 systemd
  - 6.3.1 Units and Unit Types
- NOTE
  - 6.3.2 Booting and Unit Dependency Graphs
- NOTE
  - 6.3.3 systemd Configuration
    - Unit Files
- NOTE
    - Variables
    - Specifiers
  - 6.3.4 systemd Operation
- NOTE
    - How Jobs Relate to Starting, Stopping, and Reloading Units
- NOTE
    - Adding Units to systemd
    - Removing Units from systemd
- NOTE
  - 6.3.5 systemd Process Tracking and Synchronization
  - 6.3.6 systemd Dependencies
    - Ordering
    - Default and Implicit Dependencies
    - Conditional Dependencies
    - The [Install] Section and Enabling Units
- NOTE
  - 6.3.7 systemd On-Demand and Resource-Parallelized Startup
    - An Example Socket Unit and Service
- NOTE
- NOTE
    - Instances and Handoff
- NOTE
    - Boot Optimization with Auxiliary Units
- NOTE
  - 6.3.8 systemd Auxiliary Components
- 6.4 System V Runlevels
- 6.5 System V init
- NOTE
  - 6.5.1 System V init: Startup Command Sequence
- NOTE
  - 6.5.2 The System V init Link Farm
    - Starting and Stopping Services
    - Modifying the Boot Sequence
  - 6.5.3 run-parts
  - 6.5.4 System V init Control
  - 6.5.5 systemd System V Compatibility
- 6.6 Shutting Down Your System
- 6.7 The Initial RAM Filesystem
- NOTE
- 6.8 Emergency Booting and Single-User Mode
- 6.9 Looking Forward

<!-- file: c07.xhtml -->

## 7 System Configuration: Logging, System Time, Batch Jobs, and Users
- 7.1 System Logging
  - 7.1.1 Checking Your Log Setup
  - 7.1.2 Searching and Monitoring Logs
- NOTE
    - Filtering by Time
    - Filtering by Unit
    - Finding Fields
    - Filtering by Text
- NOTE
    - Filtering by Boot
- NOTE
    - Filtering by Severity/Priority
    - Simple Log Monitoring
  - 7.1.3 Logfile Rotation
  - 7.1.4 Journal Maintenance
  - 7.1.5 A Closer Look at System Logging
    - Facility, Severity, and Other Fields
    - The Relationship Between Syslog and journald
    - Final Notes on Logging
- 7.2 The Structure of /etc
- 7.3 User Management Files
  - 7.3.1 The /etc/passwd File
- NOTE
  - 7.3.2 Special Users
  - 7.3.3 The /etc/shadow File
  - 7.3.4 Manipulating Users and Passwords
    - Changing /etc/passwd as the Superuser
  - 7.3.5 Working with Groups
- NOTE
- 7.4 getty and login
- NOTE
- 7.5 Setting the Time
  - 7.5.1 Kernel Time Representation and Time Zones
  - 7.5.2 Network Time
- 7.6 Scheduling Recurring Tasks with cron and Timer Units
- NOTE
  - 7.6.1 Installing Crontab Files
  - 7.6.2 System Crontab Files
- NOTE
  - 7.6.3 Timer Units
- NOTE
- NOTE
  - 7.6.4 cron vs. Timer Units
- 7.7 Scheduling One-Time Tasks with at
  - 7.7.1 Timer Unit Equivalents
- NOTE
- 7.8 Timer Units Running as Regular Users
- 7.9 User Access Topics
  - 7.9.1 User IDs and User Switching
- NOTE
  - 7.9.2 Process Ownership, Effective UID, Real UID, and Saved UID
    - Typical Setuid Program Behavior
- NOTE
    - Security Implications
  - 7.9.3 User Identification, Authentication, and Authorization
  - 7.9.4 Using Libraries for User Information
- 7.10 Pluggable Authentication Modules
  - 7.10.1 PAM Configuration
    - Function Types
    - Control Arguments and Stacked Rules
- NOTE
    - Module Arguments
  - 7.10.2 Tips on PAM Configuration Syntax
  - 7.10.3 PAM and Passwords
- 7.11 Looking Forward

<!-- file: c08.xhtml -->

## 8 A Closer Look at Processes and Resource Utilization
- 8.1 Tracking Processes
- NOTE
- 8.2 Finding Open Files with lsof
  - 8.2.1 Reading the lsof Output
- NOTE
  - 8.2.2 Using lsof
- NOTE
- 8.3 Tracing Program Execution and System Calls
  - 8.3.1 strace
  - 8.3.2 ltrace
- NOTE
- 8.4 Threads
  - 8.4.1 Single-Threaded and Multithreaded Processes
- NOTE
  - 8.4.2 Viewing Threads
- NOTE
- 8.5 Introduction to Resource Monitoring
  - 8.5.1 Measuring CPU Time
  - 8.5.2 Adjusting Process Priorities
  - 8.5.3 Measuring CPU Performance with Load Averages
    - Using uptime
    - Managing High Loads
  - 8.5.4 Monitoring Memory Status
    - How Memory Works
    - Page Faults
  - 8.5.5 Monitoring CPU and Memory Performance with vmstat
  - 8.5.6 I/O Monitoring
- NOTE
    - Using iostat
    - Per-Process I/O Utilization and Monitoring: iotop
  - 8.5.7 Per-Process Monitoring with pidstat
- 8.6 Control Groups (cgroups)
- NOTE
  - 8.6.1 Differentiating Between cgroup Versions
  - 8.6.2 Viewing cgroups
- NOTE
  - 8.6.3 Manipulating and Creating cgroups
  - 8.6.4 Viewing Resource Utilization
- 8.7 Further Topics

<!-- file: c09.xhtml -->

## 9 Understanding Your Network and Its Configuration
- 9.1 Network Basics
- 9.2 Packets
- 9.3 Network Layers
- NOTE
- 9.4 The Internet Layer
- NOTE
  - 9.4.1 Viewing IP Addresses
- NOTE
  - 9.4.2 Subnets
  - 9.4.3 Common Subnet Masks and CIDR Notation
- NOTE
- 9.5 Routes and the Kernel Routing Table
- NOTE
- 9.6 The Default Gateway
- How the Kernel Chooses a Route
- 9.7 IPv6 Addresses and Networks
- NOTE
- NOTE
  - 9.7.1 Viewing IPv6 Configuration on Your System
  - 9.7.2 Configuring Dual-Stack Networks
- 9.8 Basic ICMP and DNS Tools
  - 9.8.1 ping
- NOTE
  - 9.8.2 DNS and host
- 9.9 The Physical Layer and Ethernet
- 9.10 Understanding Kernel Network Interfaces
- 9.11 Introduction to Network Interface Configuration
  - 9.11.1 Manually Configuring Interfaces
  - 9.11.2 Manually Adding and Deleting Routes
- 9.12 Boot-Activated Network Configuration
- 9.13 Problems with Manual and Boot-Activated Network Configuration
- 9.14 Network Configuration Managers
  - 9.14.1 NetworkManager Operation
  - 9.14.2 NetworkManager Interaction
  - 9.14.3 NetworkManager Configuration
    - Unmanaged Interfaces
    - Dispatching
- 9.15 Resolving Hostnames
  - 9.15.1 /etc/hosts
- NOTE
  - 9.15.2 resolv.conf
  - 9.15.3 Caching and Zero-Configuration DNS
  - 9.15.4 /etc/nsswitch.conf
- 9.16 Localhost
- 9.17 The Transport Layer: TCP, UDP, and Services
  - 9.17.1 TCP Ports and Connections
    - Establishing TCP Connections
- NOTE
    - Port Numbers and /etc/services
- NOTE
    - Characteristics of TCP
  - 9.17.2 UDP
- NOTE
- 9.18 Revisiting a Simple Local Network
- 9.19 Understanding DHCP
- NOTE
  - 9.19.1 Linux DHCP Clients
  - 9.19.2 Linux DHCP Servers
- 9.20 Automatic IPv6 Network Configuration
- NOTE
- 9.21 Configuring Linux as a Router
- NOTE
- 9.22 Private Networks (IPv4)
- 9.23 Network Address Translation (IP Masquerading)
- 9.24 Routers and Linux
- 9.25 Firewalls
  - 9.25.1 Linux Firewall Basics
- NOTE
  - 9.25.2 Setting Firewall Rules
- WARNING
  - 9.25.3 Firewall Strategies
- WARNING
- 9.26 Ethernet, IP, ARP, and NDP
- NOTE
- NOTE
- IPv6: NDP
- 9.27 Wireless Ethernet
  - 9.27.1 iw
- NOTE
- NOTE
  - 9.27.2 Wireless Security
- 9.28 Summary

<!-- file: c10.xhtml -->

## 10 Network Applications and Services
- 10.1 The Basics of Services
- NOTE
- NOTE
- 10.2 A Closer Look
- NOTE
- 10.3 Network Servers
  - 10.3.1 Secure Shell
- NOTE
- Public-Key Cryptography
  - 10.3.2 The sshd Server
    - Creating Host Keys
- WARNING
    - Starting the SSH Server
  - 10.3.3 fail2ban
  - 10.3.4 The SSH Client
    - SSH File Transfer Clients
- NOTE
    - SSH Clients for Non-Unix Platforms
- 10.4 Pre-systemd Network Connection Servers: inetd/xinetd
- TCP Wrappers: tcpd, /etc/hosts.allow, and /etc/hosts.deny
- 10.5 Diagnostic Tools
  - 10.5.1 lsof
    - Filtering by Protocol and Port
    - Filtering by Connection Status
  - 10.5.2 tcpdump
- NOTE
    - Primitives
    - Operators
- NOTE
  - 10.5.3 netcat
  - 10.5.4 Port Scanning
- WARNING
- 10.6 Remote Procedure Calls
- 10.7 Network Security
  - 10.7.1 Typical Vulnerabilities
- NOTE
  - 10.7.2 Security Resources
- 10.8 Looking Forward
- 10.9 Network Sockets
- 10.10 Unix Domain Sockets
- NOTE

<!-- file: c11.xhtml -->

## 11 Introduction to Shell Scripts
- 11.1 Shell Script Basics
- NOTE
- NOTE
  - 11.1.1 Limitations of Shell Scripts
- 11.2 Quoting and Literals
  - 11.2.1 Literals
  - 11.2.2 Single Quotes
  - 11.2.3 Double Quotes
- NOTE
  - 11.2.4 Literal Single Quotes
- NOTE
- 11.3 Special Variables
- NOTE
  - 11.3.1 Individual Arguments: $1, $2, and So On
  - 11.3.2 Number of Arguments: $#
  - 11.3.3 All Arguments: $@
- NOTE
  - 11.3.4 Script Name: $0
  - 11.3.5 Process ID: $$
  - 11.3.6 Exit Code: $?
- 11.4 Exit Codes
- 11.5 Conditionals
  - 11.5.1 A Workaround for Empty Parameter Lists
  - 11.5.2 Other Commands for Tests
  - 11.5.3 elif
- NOTE
  - 11.5.4 Logical Constructs
  - 11.5.5 Testing Conditions
- NOTE
    - File Tests
- NOTE
    - String Tests
    - Arithmetic Tests
  - 11.5.6 case
- NOTE
- 11.6 Loops
  - 11.6.1 for Loops
  - 11.6.2 while Loops
- 11.7 Command Substitution
- NOTE
- 11.8 Temporary File Management
- NOTE
- NOTE
- 11.9 Here Documents
- 11.10 Important Shell Script Utilities
  - 11.10.1 basename
  - 11.10.2 awk
  - 11.10.3 sed
  - 11.10.4 xargs
  - 11.10.5 expr
  - 11.10.6 exec
- 11.11 Subshells
- WARNING
- 11.12 Including Other Files in Scripts
- 11.13 Reading User Input
- 11.14 When (Not) to Use Shell Scripts

<!-- file: c12.xhtml -->

## 12 Network File Transfer and Sharing
- 12.1 Quick Copy
- WARNING
- 12.2 rsync
  - 12.2.1 Getting Started with rsync
  - 12.2.2 Making Exact Copies of a Directory Structure
- WARNING
  - 12.2.3 Using the Trailing Slash
- WARNING
  - 12.2.4 Excluding Files and Directories
- NOTE
  - 12.2.5 Checking Transfers, Adding Safeguards, and Using Verbose Mode
  - 12.2.6 Compressing Data
  - 12.2.7 Limiting Bandwidth
  - 12.2.8 Transferring Files to Your Computer
- NOTE
  - 12.2.9 Further rsync Topics
- 12.3 Introduction to File Sharing
  - 12.3.1 File Sharing Usage and Performance
  - 12.3.2 File Sharing Security
- 12.4 Sharing Files with Samba
- NOTE
  - 12.4.1 Server Configuration
  - 12.4.2 Server Access Control
  - 12.4.3 Passwords
- NOTE
    - Adding and Deleting Users
    - Changing Passwords
  - 12.4.4 Manual Server Startup
  - 12.4.5 Diagnostics and Logfiles
  - 12.4.6 File Share Configuration
  - 12.4.7 Home Directories
  - 12.4.8 Printer Sharing
- NOTE
  - 12.4.9 The Samba Client
    - Accessing Files as a Client
    - Using the CIFS Filesystem
- 12.5 SSHFS
- 12.6 NFS
- NFS Servers
- 12.7 Cloud Storage
- 12.8 The State of Network File Sharing

<!-- file: c13.xhtml -->

## 13 User Environments
- 13.1 Guidelines for Creating Startup Files
- 13.2 When to Alter Startup Files
- 13.3 Shell Startup File Elements
  - 13.3.1 The Command Path
- NOTE
- Adding a Dot to the Path
  - 13.3.2 The Manual Page Path
  - 13.3.3 The Prompt
- NOTE
  - 13.3.4 Aliases
  - 13.3.5 The Permissions Mask
- NOTE
- 13.4 Startup File Order and Examples
  - 13.4.1 The bash Shell
    - Login Shells
    - Non-Login Shells
    - The Consequences of Two Kinds of Shells
    - Example .bashrc
    - Checking for Login and Interactive Shells
  - 13.4.2 The tcsh Shell
    - Example .cshrc
- 13.5 Default User Settings
  - 13.5.1 Shell Defaults
- NOTE
  - 13.5.2 Editor
  - 13.5.3 Pager
- 13.6 Startup File Pitfalls
- 13.7 Further Startup Topics

<!-- file: c14.xhtml -->

## 14 A Brief Survey of the Linux Desktop and Printing
- 14.1 Desktop Components
  - 14.1.1 Framebuffers
  - 14.1.2 The X Window System
  - 14.1.3 Wayland
  - 14.1.4 Window Managers
  - 14.1.5 Toolkits
  - 14.1.6 Desktop Environments
  - 14.1.7 Applications
- 14.2 Are You Running Wayland or X?
- 14.3 A Closer Look at Wayland
  - 14.3.1 The Compositing Window Manager
- NOTE
  - 14.3.2 libinput
  - 14.3.3 X Compatibility in Wayland
- 14.4 A Closer Look at the X Window System
- NOTE
  - 14.4.1 Display Managers
  - 14.4.2 Network Transparency
- NOTE
  - 14.4.3 Ways of Exploring X Clients
  - 14.4.4 X Events
  - 14.4.5 X Input and Preference Settings
    - Input Devices (General)
    - Mouse
    - Keyboard
    - Desktop Background
    - xset
- 14.5 D-Bus
  - 14.5.1 System and Session Instances
  - 14.5.2 D-Bus Message Monitoring
- 14.6 Printing
  - 14.6.1 CUPS
  - 14.6.2 Format Conversion and Print Filters
- 14.7 Other Desktop Topics

<!-- file: c15.xhtml -->

## 15 Development Tools
- 15.1 The C Compiler
- NOTE
  - 15.1.1 Compiling Multiple Source Files
- NOTE
  - 15.1.2 Linking with Libraries
- NOTE
- NOTE
  - 15.1.3 Working with Shared Libraries
    - How to List Shared Library Dependencies
    - How ld.so Finds Shared Libraries
- NOTE
    - How to Link Programs Against Shared Libraries
    - How to Avoid Problems with Shared Libraries
  - 15.1.4 Working with Header (Include) Files and Directories
    - Include File Problems
- NOTE
    - The C Preprocessor
- NOTE
- NOTE
- 15.2 make
  - 15.2.1 A Sample Makefile
- NOTE
  - 15.2.2 Built-in Rules
  - 15.2.3 Final Program Build
  - 15.2.4 Dependency Updates
  - 15.2.5 Command-Line Arguments and Options
  - 15.2.6 Standard Macros and Variables
- NOTE
  - 15.2.7 Conventional Targets
  - 15.2.8 Makefile Organization
- NOTE
- 15.3 Lex and Yacc
- 15.4 Scripting Languages
  - 15.4.1 Python
  - 15.4.2 Perl
  - 15.4.3 Other Scripting Languages
- 15.5 Java
- 15.6 Looking Forward: Compiling Packages

<!-- file: c16.xhtml -->

## 16 Introduction to Compiling Software from C Source Code
- 16.1 Software Build Systems
- NOTE
- 16.2 Unpacking C Source Packages
- 16.3 GNU Autoconf
- NOTE
  - 16.3.1 An Autoconf Example
  - 16.3.2 Installation Using a Packaging Tool
  - 16.3.3 configure Script Options
- Using Separate Build Directories
  - 16.3.4 Environment Variables
  - 16.3.5 Autoconf Targets
  - 16.3.6 Autoconf Logfiles
  - 16.3.7 pkg-config
    - How pkg-config Works
- NOTE
    - How to Install pkg-config Files in Nonstandard Locations
- 16.4 Installation Practice
  - 16.4.1 Where to Install
- 16.5 Applying a Patch
- 16.6 Troubleshooting Compiles and Installations
  - 16.6.1 Specific Errors
- 16.7 Looking Forward

<!-- file: c17.xhtml -->

## 17 Virtualization
- 17.1 Virtual Machines
- NOTE
  - 17.1.1 Hypervisors
  - 17.1.2 Hardware in a Virtual Machine
    - Virtual Machine CPU Modes
  - 17.1.3 Common Uses of Virtual Machines
  - 17.1.4 Drawbacks of Virtual Machines
- 17.2 Containers
  - 17.2.1 Docker, Podman, and Privileges
  - 17.2.2 A Docker Example
- NOTE
- NOTE
- NOTE
- NOTE
    - Running Docker Containers
- NOTE
    - Overlay Filesystems
- NOTE
    - Networking
- NOTE
    - Docker Operation
    - Docker Service Process Models
  - 17.2.3 LXC
  - 17.2.4 Kubernetes
  - 17.2.5 Pitfalls of Containers
- 17.3 Runtime-Based Virtualization
- NOTE

<!-- file: f01.xhtml -->

## Reviews for How Linux Works

<!-- file: f02.xhtml -->

## How Linux Works
- What Every Superuser Should Know

<!-- file: f04.xhtml -->
- About the Author
- About the Technical Reviewers

<!-- file: f05.xhtml -->

## Acknowledgments

<!-- file: f06.xhtml -->

## Preface
- Who Should Read This Book?
- Prerequisites
- How to Read This Book
- A Hands-on Approach
- How This Book Is Organized
- What’s New in the Third Edition?
- A Note on Terminology

<!-- file: toc.xhtml -->

## Contents In Detail
- List of Tables
- List of Illustrations
- List of Listings
- Guide
- Pages
