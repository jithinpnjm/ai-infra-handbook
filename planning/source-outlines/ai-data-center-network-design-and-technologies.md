# ai-data-center-network-design-and-technologies


<!-- file: appa.xhtml -->
- Appendix A
- Questions and Answers
  - Chapter 1: Wonders in the Workload
    - Questions
    - Answers
  - Chapter 2: “The Common-Man View” of AI Data Center Fabrics
    - Questions
    - Answers
  - Chapter 3: Network Design Considerations
    - Questions
    - Answers
  - Chapter 4: Optics and Cable Management
    - Questions
    - Answers
  - Chapter 5: Thermal and Power Efficiency Considerations
    - Questions
    - Answers
  - Chapter 6: Efficient Load Balancing
    - Questions
    - Answers
  - Chapter 7: RoCEv2 Transport and Congestion Management
    - Questions
    - Answers
  - Chapter 8: IP Routing for AI/ML Fabrics
    - Questions
    - Answers
  - Chapter 9: Storage Network Design and Technologies
    - Questions
    - Answers
  - Chapter 10: AI Network Performance KPIs
    - Questions
    - Answers
  - Chapter 11: Monitoring and Telemetry
    - Questions
    - Answers
  - Chapter 12: Ultra Ethernet Consortium (UEC)
    - Questions
    - Answers

<!-- file: appb.xhtml -->
- Appendix B
- Acronyms

<!-- file: ch01.xhtml -->
- 1
- Wonders in the Workload
  - What’s New in AI Data Center Workloads
  - The Life Cycle of an AI Model
  - Training an AI Model
  - Parallelism
    - Data Parallelism
    - Model Parallelism
  - Job Completion Time (JCT)
  - Tail Latency
    - Understanding Traffic and RDMA
    - RDMA Transport Types
    - RoCEv2
  - Summary
  - Test Your Knowledge
    - Chapter Review
    - Questions
    - Answers

<!-- file: ch02.xhtml -->
- 2
- “The Common-Man View” of AI Data Center Fabrics
  - Training vs. Inference AI Data Centers
    - AI Training Data Centers
    - AI Inference Data Centers
  - InfiniBand vs. Ethernet for AI Training Data Centers
    - Advantages of InfiniBand in AI Training Clusters
    - Advantages of Ethernet in AI Training Clusters
  - Ethernet Hardware Switches and Advanced Software Features
  - Handling Elephant Flows
  - Load-Balancing Techniques
  - Congestion Management and Mitigation Techniques
  - Summary
  - Test Your Knowledge
    - Chapter Review
    - Questions
    - Answers

<!-- file: ch03.xhtml -->
- 3
- Network Design Considerations
  - Background Introduction
  - Training Data Center Architecture
  - Rail-Optimized Design (ROD)
  - Rail-Unified Design (RUD)
  - Rack Design
    - Top-of-Rack
    - Middle-of-Row
    - End-of-Row
    - Design Comparison
  - Scheduled Fabric
  - Topologies
    - Dragonfly Topology
    - Torus Topology
  - Inference Data Center Architecture
  - Multi-Planar Scale-Out Architectures
  - Summary
  - Test Your Knowledge
    - Chapter Review
    - Questions
    - Answers
  - References

<!-- file: ch04.xhtml -->
- 4
- Optics and Cable Management
  - Scaling Optics for AI Clusters
  - Challenges in Optical Innovation
  - Packet Flow
    - Demultiplexers and Multiplexers
    - Digital Signal Processors (DSPs)
  - Transmission Modes
    - Multi-Mode Fiber (MMF)
    - Single-Mode Fiber (SMF)
    - Dense Wavelength Division Multiplexing (DWDM)
    - AI Server Connectivity Options
  - Transceiver Types
  - Cable and Connector Types
  - Standards
    - High-Bandwidth Optics
  - Further Innovations in Optics
  - Summary
  - Test Your Knowledge
    - Questions
    - Answers
  - References

<!-- file: ch05.xhtml -->
- 5
- Thermal and Power Efficiency Considerations
  - Thermal Footprints in AI Data Centers
  - Airflow Options
    - Front-to-Back Airflow
    - Back-to-Front Airflow
    - Bidirectional Fans
    - Choosing the Fan Direction
  - Liquid Cooling
    - Immersion Liquid Cooling
    - Cold Plate Liquid Cooling
    - Rear-Door Heat Exchanger Liquid Cooling
    - Sprayed Liquid Cooling
  - Summary
  - Test Your Knowledge
    - Chapter Review
    - Questions
    - Answers
  - References

<!-- file: ch06.xhtml -->
- 6
- Efficient Load Balancing
  - Per-Flow Load Balancing
    - Static Load Balancing
    - Dynamic Load Balancing
    - Global Load Balancing
    - Traffic Engineering–Based Load Balancing
  - Per-Packet Load Balancing
    - Random Spray
    - DLB Per-Packet Mode
    - Selective Packet Spraying
  - Load-Balancing Mechanism Comparison
  - Summary
  - Test Your Knowledge
    - Chapter Review
    - Questions
    - Answers

<!-- file: ch07.xhtml -->
- 7
- RoCEv2 Transport and Congestion Management
  - Congestion Points
  - Explicit Congestion Notification (ECN)
    - Priority Flow Control (PFC)
  - Data Center Quantized Congestion Notification (DCQCN)
  - Source Flow Control (SFC)
  - Congestion Signaling
  - Summary
  - Test Your Knowledge
    - Chapter Review
    - Questions
    - Answers

<!-- file: ch08.xhtml -->
- 8
- IP Routing for AI/ML Fabrics
  - Dynamic IP Routing Options
  - eBGP Underlay for Three-Stage/Five-Stage Fabric for an AI Data Center
    - eBGP Underlay and BGP Unnumbered
    - BGP ASN Allocation
    - BGP Advanced Capabilities
    - BGP DPF for AI Data Center Path Diversity
    - Traffic-to-Fabric Color Mapping
    - Interior Gateway Protocols for AI Data Center Fabric
    - IS-IS for IP Fabric: Flood Reduction and Flex Algo
  - Multi-tenancy for an AI/ML Cluster Data Center Network
    - Network-Level Multi-tenancy
    - Server-Level Multi-tenancy
    - Combining Server- and Network-Level Multi-tenancy for AI/ML Clusters
  - Microsegmentation and Multi-tenancy for an AI/ML Data Center
  - Extending IP Routing to the Server
  - Traffic Engineering in the AI Data Center Fabric
  - Segment Routing and SRv6 for AI/ML Fabrics
    - SRv6-Based Traffic Engineering
    - SRv6 Compressed SID
    - Segment Routing for AI/ML Clusters
  - Summary
  - Test Your Knowledge
    - Chapter Review
    - Questions
    - Answers
  - References

<!-- file: ch09.xhtml -->
- 9
- Storage Network Design and Technologies
  - The AI Data Center Life Cycle and Storage Networks
  - Storage Network Design Types
  - Block, Object, and File Storage Systems
  - NVMe-oF for Block-Level Access
    - NVMe-o-TCP State Machine
  - NVMe-o-RDMA/RoCEv2 State Machine
  - High-Performance File Systems
  - GPUDirect Storage
    - InfiniBand for Storage
    - Typical InfiniBand Designs
    - LID: InfiniBand Addressing and Frame Formats
    - InfiniBand QoS Support
  - Summary
  - Test Your Knowledge
    - Chapter Review
    - Questions
    - Answers
  - References

<!-- file: ch10.xhtml -->
- 10
- AI Network Performance KPIs
  - Significance of Performance Benchmarking
  - MLCommons for AI Data Centers
  - MLCommons Initiatives
  - MLCommons Benchmarking Suites
  - Benchmarking a Data Center for Machine Learning
  - Summary
  - Test Your Knowledge
    - Questions
    - Answers
  - References

<!-- file: ch11.xhtml -->
- 11
- Monitoring and Telemetry
  - Exploring Monitoring Options
  - Network Monitoring in an AI/ML Data Center Network
  - In-Band Flow Analyzer (IFA)
  - Corrective Actions
  - Summary
  - Reference

<!-- file: ch12.xhtml -->
- 12
- Ultra Ethernet Consortium (UEC)
  - UEC Developments and Working Groups
    - Link Layer Working Group
    - Transport Working Group
    - Software Working Group
    - Other Working Groups
  - UEC Key Terminology
  - The UEC and Network Architectures
    - UEC and the Existing Ethernet
  - A New Protocol Stack
  - Data Plan: Packet Forwarding Options
    - UDP-Based Encapsulation for UET
    - UET over IP: The New Entropy Field
  - Packet Delivery Modes
    - Reliable Ordered Delivery (ROD)
    - Reliable Unordered Delivery (RUD)
    - Reliable Unordered Delivery Idempotent (RUDI)
    - Unreliable Unordered Delivery (UUD)
    - UEC Delivery Modes Comparison
  - Congestion Management (CM) in the UEC Specification
    - Network Signal Congestion Control (NSCC)
    - Receiver Credit Congestion Control (RCCC)
    - Credit-Based Flow Control (CBFC)
  - Packet Trimming and Fast Retransmissions
  - Link Layer Reliability (LLR) Mechanism
  - In-Network Collectives (INC) and xCCL
  - Management and Orchestration
  - Interoperability and Backward Compatibility
  - Compliance and Certification
  - UEC Challenges and Future Directions
  - Comparing UEC to InfiniBand and RoCEv2
  - Summary
  - Test Your Knowledge
    - Chapter Review
    - Questions
    - Answers
  - References

<!-- file: ch13.xhtml -->
- 13
- Scale-Up Systems
  - Key Building Blocks of Scale-Up Systems
  - Scale-Up Ethernet Transport (SUE-T)
  - Ultra Accelerator Link (UALink)
  - Memory Coherence in Scale-Up Systems
  - Scale-Up Systems: Key Differences and Similarities
  - Summary
  - Test Your Knowledge
    - Chapter Review
    - Questions
    - Answers
  - References

<!-- file: ch14.xhtml -->
- 14
- Conclusion
  - DC Network Role for AI
  - Caveats and Challenges
  - Future Developments
  - Final Remarks
  - References

<!-- file: halftitle.xhtml -->

## AI Data Center Network Design and Technologies

<!-- file: index.xhtml -->
- Index
  - Numerics
  - A
  - B
  - C
  - D
  - E
  - F
  - G
  - H
  - I
  - J-K
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
  - X-Y-Z

<!-- file: pref00.xhtml -->
- About This eBook

<!-- file: pref01.xhtml -->
- Foreword

<!-- file: pref02.xhtml -->
- Preface

<!-- file: pref03.xhtml -->
- Acknowledgments

<!-- file: pref04.xhtml -->
- About the Authors

<!-- file: pref05.xhtml -->
- What You’ll Find Inside
    - Chapter 1: Wonders in the Workload
    - Chapter 2: “The Common-Man View” of AI Data Center Fabrics
    - Chapter 3: Network Design Considerations
    - Chapter 4: Optics and Cable Management
    - Chapter 5: Thermal and Power Efficiency Considerations
    - Chapter 6: Efficient Load Balancing
    - Chapter 7: RoCEv2 Transport and Congestion Management
    - Chapter 8: IP Routing for AI/ML Fabrics
    - Chapter 9: Storage Network Design and Technologies
    - Chapter 10: AI Network Performance KPIs
    - Chapter 11: Monitoring and Telemetry
    - Chapter 12: Ultra Ethernet Consortium (UEC)
    - Chapter 13: Scale-Up Systems

<!-- file: pref06.xhtml -->
- Credits

<!-- file: register.xhtml -->
- Where are the companion content files?

<!-- file: title.xhtml -->

## AI Data Center Network Design and Technologies

<!-- file: toc.xhtml -->
- Contents
