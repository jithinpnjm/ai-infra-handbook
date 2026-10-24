# computer-networking-problems-and-solutions


<!-- file: bk01-toc.xhtml -->
- Contents

<!-- file: ch01.xhtml -->
- Chapter 1Fundamental Concepts
  - Art or Engineering?
  - Circuit Switching
  - Packet Switching
    - Packet Switched Operation
    - Flow Control in Packet Switched Networks
  - Fixed Versus Variable Length Frames
  - Calculating Loop-Free Paths
  - Quality of Service
  - The Revenge of Centralized Control Planes
  - Complexity
    - Why So Complex?
    - Defining Complexity
    - Managing Complexity through the Wasp Waist
  - Final Thoughts
  - Further Reading
  - Review Questions

<!-- file: ch02.xhtml -->
- Chapter 2Data Transport Problems and Solutions
  - Digital Grammars and Marshaling
    - Digital Grammars and Dictionaries
    - Fixed Length Fields
    - Type Length Value
    - Shared Object Dictionaries
  - Errors
    - Error Detection
    - Error Correction
  - Multiplexing
    - Addressing Devices and Applications
    - Multicast
    - Anycast
  - Flow Control
    - Windowing
    - Negotiated Bit Rates
  - Final Thoughts on Transport
  - Further Reading
  - Review Questions

<!-- file: ch02_images.xhtml -->
- Code Snippets

<!-- file: ch03.xhtml -->
- Chapter 3Modeling Network Transport
  - United States Department of Defense (DoD) Model
  - Open Systems Interconnect (OSI) Model
  - Recursive Internet Architecture (RINA) Model
  - Connection Oriented and Connectionless
  - Final Thoughts
  - Further Reading
  - Review Questions

<!-- file: ch04.xhtml -->
- Chapter 4Lower Layer Transports
  - Ethernet
    - Multiplexing
    - Error Control
    - Data Marshaling
    - Flow Control
  - Wireless 802.11
    - Multiplexing
    - Data Marshaling, Error Control, and Flow Control
  - Final Thoughts on Lower Layer Transmission Protocols
  - Further Reading
  - Review Questions

<!-- file: ch05.xhtml -->
- Chapter 5Higher Layer Data Transports
  - The Internet Protocol
    - Transport and Marshaling
    - Multiplexing
  - Transmission Control Protocol
    - Flow Control
    - Error Control
    - TCP Port Numbers
    - TCP Session Setup
  - QUIC
  - ICMP
  - Final Thoughts
  - Further Reading
  - Review Questions

<!-- file: ch06.xhtml -->
- Chapter 6Interlayer Discovery
  - Interlayer Discovery Solutions
    - Well-Known and/or Manually Configured Identifiers
    - Mapping Database and Protocol
    - Advertising Identifier Mappings in a Protocol
    - Calculating One Identifier from the Other
  - Interlayer Discovery Examples
    - The Domain Name System
    - DHCP
    - IPv4 Address Resolution Protocol
    - IPv6 Neighbor Discovery
  - The Default Gateway Problem
  - Final Thoughts
  - Further Reading
  - Review Questions

<!-- file: ch07.xhtml -->
- Chapter 7Packet Switching
  - Physical Media to Memory
  - Processing the Packet
    - Switching
    - Routing
    - Why Route?
    - Equal Cost Multipath
    - Packet Processing Engines
  - Across the Bus
    - Crossbars and Contention
  - Memory to Physical Media
  - Final Thoughts on Packet Switching
  - Further Reading
  - Review Questions

<!-- file: ch08.xhtml -->
- Chapter 8Quality of Service
  - Defining the Problem Space
    - Why Not Just Size Links Large Enough?
  - Classification
    - Preserving Classification
    - The Unmarked Internet
  - Congestion Management
    - Timeliness: Low-Latency Queueing
    - Fairness: Class-Based Weighted Fair Queueing
    - Overcongestion
    - Other QoS Congestion Management Tools
  - Queue Management
    - Managing a Full Buffer: Weighted Random Early Detection
    - Managing Buffer Delay, Bufferbloat, and CoDel
  - Final Thoughts on Quality of Service
  - Further Reading
  - Review Questions

<!-- file: ch09.xhtml -->
- Chapter 9Network Virtualization
  - Understanding Virtual Networks
    - Providing Ethernet Services over an IP Network
    - Virtual Private Access to a Corporate Network
    - A Summary of Virtualization Problems and Solutions
  - Segment Routing
    - Segment Routing with Multiprotocol Label Switching
    - Segment Routing with IPv6
    - Signaling Segment Routing Labels
  - Software-Defined Wide Area Networks
  - Complexity and Virtualization
    - Interaction Surfaces and Shared Risk Link Groups
    - Interaction Surfaces and Overlaid Control Planes
  - Final Thoughts on Network Virtualization
  - Further Reading
  - Review Questions

<!-- file: ch10.xhtml -->
- Chapter 10Transport Security
  - The Problem Space
    - Validating Data
    - Protecting Data from Being Examined
    - Protecting User Privacy
  - The Solution Space
    - Encryption
    - Key Exchange
    - Cryptographic Hashes
    - Obscuring User Information
  - Transport Layer Security
  - Final Thoughts on Transport Security
  - Further Reading
  - Review Questions

<!-- file: ch11.xhtml -->
- Chapter 11Topology Discovery
  - Nodes, Edges, and Reachable Destinations
    - Node
    - Edge
    - Reachable Destination
    - Topology
  - Learning about the Topology
    - Detecting Other Network Devices
    - Detecting Two-Way Connectivity
    - Detecting the Maximum Transmission Unit
  - Learning about Reachable Destinations
    - Learning Reactively
    - Learning Proactively
  - Advertising Reachability and Topology
    - Deciding When to Advertise Reachability and Topology
    - Reactive Distribution of Reachability
    - Proactive Distribution of Reachability
  - Redistribution between Control Planes
    - Redistribution and Metrics
    - Redistribution and Routing Loops
  - Final Thoughts on Topology Discovery
  - Further Reading
  - Review Questions

<!-- file: ch12.xhtml -->
- Chapter 12Unicast Loop-Free Paths (1)
  - Which Path Is Loop Free?
  - Trees
  - Alternate Loop-Free Paths
    - Waterfall (or Continental Divide) Model
    - P/Q Space
    - Remote Loop-Free Alternates
  - Bellman-Ford Loop-Free Path Calculation
  - Garcia’s Diffusing Update Algorithm
  - Final Thoughts
  - Further Reading
  - Review Questions

<!-- file: ch13.xhtml -->
- Chapter 13Unicast Loop-Free Paths (2)
  - Dijkstra’s Shortest Path First
    - Partial and Incremental SPF
    - Calculating LFAs and rLFAs
  - Path Vector
  - Disjoint Path Algorithms
    - Two-Connected Networks
    - Suurballe’s Disjoint Path Algorithm
    - Maximally Redundant Trees
  - Two-Way Connectivity
  - Final Thoughts
  - Further Reading
  - Review Questions

<!-- file: ch14.xhtml -->
- Chapter 14Reacting to Topology Changes
  - Detecting Topology Changes
    - Polling to Detect Failures
    - Event-Driven Failure Detection
    - Comparing Event-Driven and Polling-Based Detection
    - An Example: Bidirectional Forwarding Detection
  - Change Distribution
    - Flooding
    - Hop by Hop
    - A Centralized Store
  - Consistency, Accessibility, and Partitionability
  - Final Thoughts
  - Further Reading
  - Review Questions

<!-- file: ch15.xhtml -->
- Chapter 15Distance Vector Control Planes
  - Control Plane Classification
  - Spanning Tree Protocol
    - Building a Loop-Free Tree
    - Learning about Reachable Destinations
    - Concluding Thoughts on the Spanning Tree Protocol
  - The Routing Information Protocol
    - Tying Bellman-Ford to RIP
    - Reacting to Topology Changes
    - Concluding Thoughts on RIP
  - The Enhanced Interior Gateway Routing Protocol
    - Reacting to a Topology Change
    - Neighbor Discovery and Reliable Transport
    - Concluding Thoughts on EIGRP
  - Further Reading
  - Review Questions

<!-- file: ch16.xhtml -->
- Chapter 16Link State and Path Vector Control Planes
  - A Short History of OSPF and IS-IS
  - The Intermediate System to Intermediate System Protocol
    - OSI Addressing
    - Marshalling Data in IS-IS
    - Neighbor and Topology Discovery
    - Reliable Flooding
    - Concluding Thoughts on IS-IS
  - The Open Shortest Path First Protocol
    - Marshalling Data in OSPF
    - Neighbor and Topology Discovery
    - Reliable Flooding
    - Concluding Thoughts on OSPF
  - Common Elements of OSPF and IS-IS
    - Multiaccess Links
    - Conceptualizing Links, Nodes, and Reachability in Link State Protocols
    - Validating Two-Way Connectivity in SPF
  - Border Gateway Protocol
    - BGP Peering
    - The BGP Best Path Decision Process
    - BGP Advertisement Rules
    - Concluding Thoughts on BGP
  - Final Thoughts
  - Further Reading
  - Review Questions

<!-- file: ch17.xhtml -->
- Chapter 17Policy in the Control Plane
  - Control Plane Policy Use Cases
    - Routing and Potatoes
    - Resource Segmentation
    - Flow Pinning for Application Optimization
  - Defining Control Plane Policy
  - Control Plane Policy and Complexity
    - Routing and Potatoes
    - Resource Segmentation
    - Flow Pinning for Applications
  - Final Thoughts on Control Plane Policy
  - Further Reading
  - Review Questions

<!-- file: ch18.xhtml -->
- Chapter 18Centralized Control Planes
  - Considering the Definition of Software Defined
    - A Taxonomy of Interfaces
    - Considering the Division of Labor
  - BGP as an SDN
  - Fibbing
  - I2RS
  - PCEP
  - OpenFlow
  - CAP Theorem and Subsidiarity
  - Final Thoughts on Centralized Control Planes
  - Further Reading
  - Review Questions

<!-- file: ch19.xhtml -->
- Chapter 19Failure Domains and Information Hiding
  - The Problem Space
    - Defining Control Plane State Scope
    - Positive Feedback Loops
  - The Solution Space
    - Summarizing Topology Information
    - Aggregating Reachability Information
    - Filtering Reachability Information
    - Layering Control Planes
    - Caching
    - Slowing Down
  - Final Thoughts on Hiding Information
  - Further Reading
  - Review Questions

<!-- file: ch20.xhtml -->
- Chapter 20Examples of Information Hiding
  - Summarizing Topology Information
    - Intermediate System to Intermediate System
    - Open Shortest Path First
  - Aggregation
  - Layering
    - The Border Gateway Protocol as a Reachability Overlay
    - Segment Routing with a Controller Overlay
  - Slowing Down State Velocity
    - Exponential Backoff
    - Link State Flooding Reduction
  - Final Thoughts on Failure Domains
  - Further Reading
  - Review Questions

<!-- file: ch21.xhtml -->
- Chapter 21Security: A Broader Sweep
  - The Scope of the Problem
    - The Biometric Identity Conundrum
    - Definitions
    - The Problem Space
  - The Solution Space
    - Defense in Depth
    - Access Control
    - Data Protection
    - Service Availability Assurance
  - The OODA Loop as a Security Model
    - Observe
    - Orient
    - Decide
    - Act
  - Final Thoughts on Security
  - Further Reading
  - Review Questions

<!-- file: ch22.xhtml -->
- Chapter 22Network Design Patterns
  - The Problem Space
    - Solving Business Problems
    - Translating Business Requirements into Technical
    - What Is a Good Network Design?
  - Hierarchical Design
  - Common Topologies
    - Ring Topologies
    - Mesh Topologies
    - Hub-and-Spoke Topologies
    - Planar, Nonplanar, and Regular
  - Final Thoughts on Network Design Patterns
  - Further Reading
  - Review Questions

<!-- file: ch23.xhtml -->
- Chapter 23Redundant and Resilient
  - The Problem Space: What Failures Look Like to Applications
  - Resilience Defined
    - Other “Measures”
  - Redundancy as a Tool to Create Resilience
    - Shared Risk Link Groups
    - In-Service Software Upgrade and Graceful Restart
    - Dual and Multiplanar Cores
  - Modularity and Resilience
  - Final Thoughts on Resilience
  - Further Reading
  - Review Questions

<!-- file: ch24.xhtml -->
- Chapter 24Troubleshooting
  - What Is the Purpose?
  - What Are the Components?
  - Models and Troubleshooting
    - Build How Models
    - Build What Models
    - Build Accurate Models
    - Shifting between Models
  - Half Split and Move
    - Using Manipulability
    - Simplify before Testing
  - Fixing the Problem
  - Final Thoughts on Troubleshooting
  - Further Reading
  - Review Questions

<!-- file: ch25.xhtml -->
- Chapter 25Disaggregation, Hyperconvergence, and the Changing Network
  - Changes in Compute Resources and Applications
    - Converged, Disaggregated, Hyperconverged, and Composable
    - Applications Virtualized and Disaggregated
  - The Impact on Network Design
    - The Rise of East/West Traffic
    - The Rise of Jitter and Delay
  - Packet Switched Fabrics
    - The Special Properties of a Fabric
    - Spine and Leaf
    - Traffic Engineering on a Spine and Leaf
    - A Larger-Scale Spine and Leaf
  - Disaggregation in Networks
  - Final Thoughts on Disaggregation
  - Further Reading
  - Review Questions

<!-- file: ch26.xhtml -->
- Chapter 26The Case for Network Automation
  - Automation Concepts
  - Modern Automation Methods
    - NETCONF
    - RESTCONF
  - Automation with Programmatic Interfaces
  - On-box Automation
  - Network Automation with Infrastructure Automation Tools
  - Network Controllers and Automation
  - Network Automation for Deployment
  - Final Thoughts on the Future of Network Automation: Automation to Automatic
  - Further Reading
  - Review Questions

<!-- file: ch27.xhtml -->
- Chapter 27Virtualized Network Functions
  - Network Design Flexibility
    - Service Chaining
  - Scaling Out
  - Decreased Time to Service through Automation
    - Centralized Policy Management
    - Intent-Based Networking
    - Benefit
  - Compute Advantages and Architecture
    - Improving VNF Throughput
  - Considering Tradeoffs
    - State
    - Optimization
    - Surface
    - Other Tradeoffs to Consider
  - Final Thoughts
  - Further Reading
  - Review Questions

<!-- file: ch28.xhtml -->
- Chapter 28Cloud Computing Concepts and Challenges
  - Public Cloud Business Drivers
    - Shifting from Capital to Operational Expenditure
    - Time-to-Market and Business Agility
  - Nontechnical Public Cloud Tradeoffs
    - Operational Tradeoffs
    - Business Tradeoffs
  - Technical Challenges of Cloud Networking
    - Latency
    - Populating Remote Storage
    - Data Gravity
    - Selecting Among Multiple Paths to the Public Cloud
  - Security in the Cloud
    - Protecting Data over Public Transport
    - Managing Secure Connections
    - The Multitenant Cloud
    - Role-Based Access Controls
  - Monitoring Cloud Networks
  - Final Thoughts
  - Further Reading
  - Review Questions

<!-- file: ch29.xhtml -->
- Chapter 29Internet of Things
  - Introducing IoT
  - IoT Security
    - Securing Insecurable Devices Through Isolation
  - IoT Connectivity
    - Bluetooth Low Energy (BLE)
    - LoRaWAN
    - IPv6 for IoT
  - IoT Data
  - Final Thoughts on the Internet of Things
  - Further Reading
  - Review Questions

<!-- file: ch30.xhtml -->
- Chapter 30Looking Forward
  - Pervasive Open Automation
    - Modeling Languages and Models
    - A Brief Introduction to YANG
    - Looking Forward Toward Pervasive Automation
  - Hyperconverged Networks
  - Intent-Based Networking
  - Machine Learning and Artificial Narrow Intelligence
  - Named Data Networking and Blockchains
    - Named Data Networking Operation
    - Blockchains
  - The Reshaping of the Internet
  - Final Thoughts on the Future of Network Engineering
  - Further Reading
  - Review Questions

<!-- file: index.xhtml -->
- Index
  - Numbers
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
  - X
  - Y–Z

<!-- file: part1.xhtml -->

## PART IThe Data Plane

<!-- file: part2.xhtml -->

## PART IIThe Control Plane

<!-- file: part3.xhtml -->

## PART IIINetwork Design
  - Three Underlying Models
    - The Law of Leaky Abstractions
    - The State/Optimization/Surface (SOS) Triad
    - The Consistency/Accessibility/Partitioning (CAP) Triad

<!-- file: part4.xhtml -->

## PART IVCurrent Topics

<!-- file: pref00.xhtml -->
- About This E-Book

<!-- file: pref01.xhtml -->
- Acknowledgments

<!-- file: pref02.xhtml -->
- About the Authors

<!-- file: pref03.xhtml -->
- Introduction
  - How This Book Is Organized
    - What Is the Problem?
    - What Is the Solution?
    - How Has This Been Implemented?
  - What This Book Does Not Cover
  - On Reading Flow
  - A Beginning
  - Reader Services

<!-- file: title.xhtml -->

## Computer Networking Problems and Solutions
