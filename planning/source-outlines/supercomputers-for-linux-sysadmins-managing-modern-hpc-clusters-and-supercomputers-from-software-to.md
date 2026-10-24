# supercomputers-for-linux-sysadmins-managing-modern-hpc-clusters-and-supercomputers-from-software-to


<!-- file: 979-8-8688-1600-0_10_Chapter.xhtml -->

## 10. Remote Management
- ssh and Parallel ssh
  - Forwarding Environment Variables
  - Port Forwarding
  - X Connection Forwarding
  - File Transfer
  - SSH Agent
  - Configuring the ssh Server
  - Configuring the ssh Client
  - Host-Based Authentication
- pdsh
- Cluster Shell
- Screen and tmux
- IPMI
- Conman
- iKVM
- Brief Summary
- Search Keywords

<!-- file: 979-8-8688-1600-0_11_Chapter.xhtml -->

## 11. Users – Accounting Management
- Account Synchronization
- Classic Approach
- NIS/NIS+
- LDAP
- Brief Summary
- Search Keywords

<!-- file: 979-8-8688-1600-0_12_Chapter.xhtml -->

## 12. Users – Quotas and Access Rights
- File System Quotas
- ulimits
- UNIX Groups, ACLs
- Restrict User Access
- Brief Summary
- Search Keywords

<!-- file: 979-8-8688-1600-0_13_Chapter.xhtml -->

## 13. Job Management Systems
- Principles of Operation and Capabilities
- Kubernetes, etc.
- Access Problem
- Brief Summary
- Search Keywords

<!-- file: 979-8-8688-1600-0_14_Chapter.xhtml -->

## 14. OpenPBS and Torque
- Installing Torque
- Setting Up Torque
- Configuring the MOM Server on Compute Nodes
- Customizing the Scheduler
- Using Torque
- Job Control Commands
- Brief Summary
- Search Keywords

<!-- file: 979-8-8688-1600-0_15_Chapter.xhtml -->

## 15. Slurm
- Slurm Installation
- Accounting
- Accounting Setup
- Basic Setup and Usage
- Partitions
- Nodes
- Generic and Trackable Resources
- Backfill and Preemption
- QoS and Limits
- Priorities and FairShare
- User Levels
- Topology
- Reservations
- User Experience
- Job Life Cycle
- scontrol
- Accounting and Statistics
- Troubleshooting
- Advanced Parameters for slurm.conf
- Brief Summary
- Search Keywords

<!-- file: 979-8-8688-1600-0_16_Chapter.xhtml -->

## 16. Containers
- Singularity
- Apptainer
- CharlieCloud
- Pyxis + Enroot
- Caching
- Brief Summary
- Search Keywords

<!-- file: 979-8-8688-1600-0_17_Chapter.xhtml -->

## 17. Clouds
- Brief Summary
- Search Keywords

<!-- file: 979-8-8688-1600-0_18_Chapter.xhtml -->

## 18. Remote User Access
- SSH
- FTP and WWW
- X-Window
- Alternatives for X11
- Brief Summary
- Search Keywords

<!-- file: 979-8-8688-1600-0_19_Chapter.xhtml -->

## 19. Cluster Status Monitoring Systems
- SNMP
- Ganglia
- Nagios
- Zabbix
- Modern Approach
- XDMoD
- Lm_sensors/Hwmon
- IPMI
- APCUPS
- NUT
- Healthchecks
- Security Scans
- Brief Summary
- Search Keywords

<!-- file: 979-8-8688-1600-0_1_Chapter.xhtml -->

## 1. Introduction
- Conventions and Notations Adopted in the Book

<!-- file: 979-8-8688-1600-0_20_Chapter.xhtml -->

## 20. Backup
- Tar
- Bacula
- Rsync and Others
- Brief Summary
- Search Keywords

<!-- file: 979-8-8688-1600-0_21_Chapter.xhtml -->

## 21. Compilers and Environments, for Parallel Technologies
- gcc/gfortran
- Intel and NVIDIA HPC Compilers
- PMIx
- mpich
- OpenMPI
- Mvapich/Mvapich2
- Proprietary MPI: Spectrum MPI and IntelMPI
- SHMEM Library, OpenSHMEM Standard
- CUDA
- UCX and NCCL
- OpenCL
- OpenACC
- Environment Modules and LMOD
- Build Systems
- Brief Summary
- Search Keywords

<!-- file: 979-8-8688-1600-0_22_Chapter.xhtml -->

## 22. Parallel Computing Support Libraries
- ScaLAPACK
- PETSc
- FFT/FFTW
- TBB
- Debuggers and Profilers
- Brief Summary
- Search Keywords

<!-- file: 979-8-8688-1600-0_23_Chapter.xhtml -->

## 23. Booting and Init
- Booting from Hard Disk
- INIT in SystemV Style
- Systemd
- Network Booting
- DHCP
- TFTP, PXE, and NFS-Root
- Brief Summary
- Search Keywords

<!-- file: 979-8-8688-1600-0_24_Chapter.xhtml -->

## 24. Node Setup and Software Installation
- Network and Hardware Drivers
- Configuring the Control and Compute Nodes
- Installation and Configuration of the Login Node
- NFS Server Configuration
- Configuring the Communication Software
- Installing Compilers and Libraries
- Customizing the Job Management System
- Installation and Configuration of the Cluster Compute Node
- Brief Summary
- Search Keywords

<!-- file: 979-8-8688-1600-0_25_Chapter.xhtml -->

## 25. Out-of-the-Box Stacks and Deployment Systems
- ROCKS
- Parallel Knoppix/PelicanHPC
- Brief Summary
- Search Keywords

<!-- file: 979-8-8688-1600-0_26_Chapter.xhtml -->

## 26. Cluster Management Systems – xCAT and Others
- Installation and Initial Setup
- Architecture and Commands
- Node Management
- Loading and Controlling
- Canonical MaaS
- Foreman
- NVIDIA Base Command Manager
- Brief Summary
- Search Keywords

<!-- file: 979-8-8688-1600-0_27_Chapter.xhtml -->

## 27. Communicating with Users
- Correspondence
- Accounting for Requests from Users
- Actualization
- Education
- Brief Summary
- Search Keywords

<!-- file: 979-8-8688-1600-0_28_Chapter.xhtml -->

## 28. One-Two-Three Instructions
- NTP
- Configuring the NFS Server
- Configuring the NFS Client
- Installing Lustre (No HA)
- NIS+ Server Installation
- Installing the NIS+ Client
- Installing OpenLDAP (Using RH As an Example)
- Customizing Xorg
- APCUPSD
- xCAT
- Brief Summary
- Search Keywords

<!-- file: 979-8-8688-1600-0_29_Chapter.xhtml -->

## 29. Shell Scripts – Basics and Common Mistakes
- Not-a-Mistake
- Brief Summary
- Search Keywords

<!-- file: 979-8-8688-1600-0_2_Chapter.xhtml -->

## 2. What Is “Super”?
- General Concepts of Parallel Processing and Parallel Programs
- Types of Clusters
  - Clusters and Supercomputers – Common and Different
- What “Super” Means to a Supercomputer Administrator
- Centralized Management of the Computer Complex
- Brief Summary
- Search Keywords

<!-- file: 979-8-8688-1600-0_30_Chapter.xhtml -->

## 30. Systemd – A Short Course
- Units
- systemctl Commands
- Journald
- Network Config, Time Sync, and Hostname Resolving
- Analyzing
- Brief Summary
- Search Keywords

<!-- file: 979-8-8688-1600-0_3_Chapter.xhtml -->

## 3. How to Build and Start It?
- Anatomy of a Supercomputer
- Planning
- Documentation
- OK, We Got It, What’s Next?
- What Should I Do Later?
- Short Notes
- Brief Summary
- Search Keywords

<!-- file: 979-8-8688-1600-0_4_Chapter.xhtml -->

## 4. Supercomputer Hardware
- Control Node
- Compute Node
- Login Node
- Service Nodes
- Network Equipment
- Data Storage
- Hardware Architecture Features
- Brief Summary
- Search Keywords

<!-- file: 979-8-8688-1600-0_5_Chapter.xhtml -->

## 5. InfiniBand
- Component Identification and Addressing in InfiniBand Networks
- InfiniBand Subnet Management
- IP Over InfiniBand (IP Over IB, IPoIB)
- Utilities for InfiniBand Network Viewing and Managing
- Alternatives
- Brief Summary
- Search Keywords

<!-- file: 979-8-8688-1600-0_6_Chapter.xhtml -->

## 6. How a Supercomputer Does the Job
- How a Typical User Session Occurs
- Job Life Cycle
- What Is Hidden from the User
- Brief Summary
- Search Keywords

<!-- file: 979-8-8688-1600-0_7_Chapter.xhtml -->

## 7. UNIX and Linux – the Basics
- Processes
- Access Rights
- Concept of Service, Key Services
- Manuals
- File Naming Conventions
- Extension Agreements
- Templates
- Commands for Working with the Directory Tree
  - Commands for Working with Catalogs
- Commands for Working with Files
- Packages
- Network Commands
- “Cluster” Commands
- Brief Summary
- Search Keywords

<!-- file: 979-8-8688-1600-0_8_Chapter.xhtml -->

## 8. UNIX and Linux – Working Techniques
- The Magic of sysctl
- udev Subsystem
- PAM Modules
- Shell Tricks
- Tips for Some Often Used Commands
- Brief Summary
- Search Keywords

<!-- file: 979-8-8688-1600-0_9_Chapter.xhtml -->

## 9. Network File Systems
- NTP
- NFS
- Lustre
  - Architecture
  - Creation of Lustre File System
  - Fault Tolerance in Lustre
  - Striping and PFL
  - Quotas
- PanFS
- GPFS/IBM Storage Scale
- Other File Systems
- Brief Summary
- Search Keywords

<!-- file: Backmatter_001.xhtml -->

## Conclusion

<!-- file: Backmatter_002.xhtml -->

## Index
- A
- B
- C
- D
- E
- F
- G
- H
- I, J
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
- X, Y
- Z

<!-- file: Frontmatter_001.xhtml -->

## Supercomputers for Linux SysAdmins

<!-- file: Frontmatter_003.xhtml -->

## Glossary of Terms
- Glossary of Jargon

<!-- file: Frontmatter_005.xhtml -->

## Acknowledgments

<!-- file: Frontmatter_006.xhtml -->

## Table of Contents

<!-- file: Frontmatter_007.xhtml -->

## About the Author

<!-- file: Frontmatter_008.xhtml -->

## About the Technical Reviewer
