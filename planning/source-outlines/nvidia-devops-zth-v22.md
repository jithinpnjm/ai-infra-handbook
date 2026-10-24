# nvidia-devops-zth-v22


## Chapter 1: Consulting Methodology for Customer Engagement  (chapter-01-consulting-methodology-for-customer-engagement.md)
- Learning Outcome
- Beginner's Primer: Speaking "Business"
- The Consulting Challenge
- The Discovery Framework: Four Questions
  - 1. **What Is the Business Constraint?**
  - 2. **What Is the Technical Constraint?**
  - 3. **What Is the Deployment Constraint?**
  - 4. **What Is the Success Metric?**
- Success Metrics Table
- Cost Model: From Infrastructure to Customer Quote
  - Typical Cost Components
  - Real Cost Example: Bank Fraud Detection
- Interview Preparation
- Architecture Summary
- Related Chapters

## Chapter 2: Banking and Financial Services  (chapter-02-banking-and-financial-services.md)
- Overview
- Beginner's Primer: AI in Banking
- Use Case 1: Fraud Detection (5,000 TPS)
  - Requirements
  - Architecture: 2 Clusters of 4 L40S GPUs
  - Troubleshooting Decision Tree
- Use Case 2: Risk Modeling (Daily VaR, 4 hours)
  - Architecture: 8 A100s (FP64 optimized)
- Use Case 3: Algorithmic Trading Signals
  - Architecture: Single H100 + ONNX Runtime
- Compliance Considerations
- Interview Preparation
- Architecture Summary
- Related Chapters

## Chapter 3: Generative AI and Large Language Models  (chapter-03-generative-ai-and-large-language-models.md)
- Overview
- Beginner's Primer: The LLM Business Model
- Use Case 1: Fine-Tuning Llama-2 7B
  - Requirements
  - Architecture: Single H100
- Use Case 2: LLM Inference Cluster (1,000 concurrent users)
  - Architecture: 8 A100s + vLLM continuous batching
- Troubleshooting Decision Tree
- Interview Preparation
- Architecture Summary
- Related Chapters

## Chapter 4: Automotive and Autonomous Vehicles  (chapter-04-automotive-and-autonomous-vehicles.md)
- Overview
- Beginner's Primer: AI on the Edge
- Use Case: Edge Deployment on Drive Orin
  - Requirements
  - Architecture: 2× Drive Orin per vehicle (primary + safety)
  - Cost Analysis
- Troubleshooting Scenarios
- Architecture Summary
- Related Chapters

## Chapter 5: Pharmaceuticals and Drug Discovery  (chapter-05-pharmaceuticals-and-drug-discovery.md)
- Overview
- Beginner's Primer: AI for Biology
- Use Case 1: Virtual Screening (10M molecules)
  - Requirements
  - Architecture: 8 A100s
- Use Case 2: Protein Folding (AlphaFold2)
  - Architecture: 4 H100s
- FDA Compliance
- Architecture Summary
- Related Chapters

## Chapter 6: Telecommunications  (chapter-06-telecommunications.md)
- Overview
- Beginner's Primer: The Edge Cloud
- Use Case: Network Optimization (10,000 cell towers)
  - Requirements
  - Architecture: 8 A100s + Kafka streaming
- Cost Justification
- Architecture Summary
- Related Chapters

## Chapter 7: Healthcare and Medical Imaging  (chapter-07-healthcare-and-medical-imaging.md)
- Overview
- Beginner's Primer: AI as a Medical Device
- Use Case: CT Lung Cancer Screening (50,000 patients/year)
  - Requirements
  - Architecture: 4 A100s + HIPAA-compliant gateway
  - Cost Model
- Architecture Summary
- Related Chapters

## Chapter 8: Manufacturing and Predictive Maintenance  (chapter-08-manufacturing-and-predictive-maintenance.md)
- Overview
- Beginner's Primer: Industrial IoT and The Edge
- Use Case: Bearing Failure Prediction (50 production lines, 1,250 bearings)
  - Requirements
  - Architecture: 1 Jetson Orin NX per production line
  - ROI
- Troubleshooting
- Architecture Summary
- Related Chapters

## Chapter 9: Scientific Research and Simulation  (chapter-09-scientific-research-and-simulation.md)
- Overview
- Beginner's Primer: HPC vs AI
- Use Case: Climate Modeling (100-year forecast)
  - Requirements
  - Architecture: 32 A100s + NVMe burst buffer
- Failure Recovery
- Architecture Summary
- Related Chapters

## Volume 22 — Customer Workshops: Industry-Specific AI Solutions  (index.md)
- Overview
- Chapters
  - Chapter 1: Consulting Methodology for Customer Engagement
  - Chapter 2: Banking and Financial Services
  - Chapter 3: Generative AI and Large Language Models
  - Chapter 4: Automotive and Autonomous Vehicles
  - Chapter 5: Pharmaceuticals and Drug Discovery
  - Chapter 6: Telecommunications
  - Chapter 7: Healthcare and Medical Imaging
  - Chapter 8: Manufacturing and Predictive Maintenance
  - Chapter 9: Scientific Research and Simulation
- Labs
- How to Use
- Cross-References

## Lab 01: Banking Use Case Workshop  (labs/lab-01-banking-use-case-workshop.md)
- 1. Objective
- 2. Target Audience
- 3. Prerequisites
- 4. Architecture Diagram
- 5. Environment Setup
- 6. Step 1: Prepare Fraud Detection Model
- 7. Step 2: Deploy Inference Server (Triton)
- 8. Step 3: Create Fraud Detection Client
- 9. Step 4: Measure Performance
- 10. Step 5: Load Test (5,000 TPS Sustained)
- 11. Validation Against SLA
- 12. Troubleshooting Scenarios
  - Scenario 1: Latency spikes during load test
  - Scenario 2: One GPU underutilized
- 13. Common Failures
- 14. Recovery Steps
- 15. Knowledge Check
- 16. Validation Checklist
- 17. Additional References

## Lab 02: LLM Serving Design  (labs/lab-02-llm-serving-design.md)
- 1. Objective
- 2. Target Audience
- 3. Prerequisites
- 4. Architecture Diagram
- 5. Environment Setup
- 6. Step 1: Download and Convert Llama-2 13B
- 7. Step 2: Launch vLLM Inference Server
- 8. Step 3: Create Concurrent User Workload
- 9. Step 4: Measure Per-Token Latency During Generation
- 10. Validation Against SLA
- 11. Step 5: Model Optimization
- 12. Troubleshooting Scenarios
  - Scenario 1: TTFT degradation over time
  - Scenario 2: Uneven load between GPUs
- 13. Knowledge Check
- 14. Validation Checklist
- 15. Additional References

## Lab 03: Edge Deployment  (labs/lab-03-edge-deployment.md)
- 1. Objective
- 2. Target Audience
- 3. Prerequisites
- 4. Architecture Diagram
- 5. Environment Setup
- 6. Step 1: Download YOLOv8 Model
- 7. Step 2: Benchmark Inference on Jetson Orin
- 8. Step 3: Deploy with Live Camera Feed
- 9. Step 4: Export Detection Events
- 10. Validation Against SLA
- 11. Troubleshooting Scenarios
  - Scenario 1: Latency spikes during heavy detection
  - Scenario 2: Thermal throttling during sustained operation
- 12. Knowledge Check
- 13. Validation Checklist
- 14. Advanced: Deploy Multiple Models
- 15. Additional References

## Lab 04: Medical Imaging Pipeline  (labs/lab-04-medical-imaging-pipeline.md)
- 1. Objective
- 2. Target Audience
- 3. Prerequisites
- 4. Architecture Diagram
- 5. Environment Setup
- 6. Step 1: Prepare DICOM Data (de-identified)
- 7. Step 2: Load and Normalize CT Volume
- 8. Step 3: Load Pretrained Model
- 9. Step 4: Inference and Risk Scoring
- 10. Step 5: Implement HIPAA Compliance
- 11. Step 6: Benchmark Throughput (50K studies/year)
- 12. Validation Against SLA
- 13. Troubleshooting Scenarios
  - Scenario 1: Inference latency varies (5ms to 50ms)
  - Scenario 2: Audit log file grows too large
- 14. Knowledge Check
- 15. Validation Checklist
- 16. Advanced: Multi-Study Batch Processing
- 17. Additional References
