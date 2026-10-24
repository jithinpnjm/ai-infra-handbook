# llm-engineers-handbook


<!-- file: Appendix.xhtml -->

## Appendix

## MLOps Principles

## 1. Automation or operationalization

## 2. Versioning

## 3. Experiment tracking

## 4. Testing
- Test types
- What do we test?
- Test examples

## 5. Monitoring
- Logs
- Metrics
  - System metrics
  - Model metrics
  - Drifts
    - Data drift
    - Target drift
    - Concept drift
    - How to detect and measure drifts
  - Monitoring vs. observability
  - Alerts

## 6. Reproducibility
    - Unlock this book’s exclusive benefits now

<!-- file: Chapter_01.xhtml -->

## 1

## Understanding the LLM Twin Concept and Architecture

## Understanding the LLM Twin concept
- What is an LLM Twin?
- Why building an LLM Twin matters
- Why not use ChatGPT (or another similar chatbot)?

## Planning the MVP of the LLM Twin product
- What is an MVP?
- Defining the LLM Twin MVP

## Building ML systems with feature/training/inference pipelines
- The problem with building ML systems
- The issue with previous solutions
- The solution – ML pipelines for ML systems
  - The feature pipeline
  - The training pipeline
  - The inference pipeline
- Benefits of the FTI architecture

## Designing the system architecture of the LLM Twin
- Listing the technical details of the LLM Twin architecture
- How to design the LLM Twin architecture using the FTI pipeline design
  - Data collection pipeline
  - Feature pipeline
  - Training pipeline
  - Inference pipeline
- Final thoughts on the FTI design and the LLM Twin architecture

## Summary

## References
    - Unlock this book’s exclusive benefits now

<!-- file: Chapter_02.xhtml -->

## 2

## Tooling and Installation

## Python ecosystem and project installation
- Poetry: dependency and virtual environment management
- Poe the Poet: task execution tool

## MLOps and LLMOps tooling
- Hugging Face: model registry
- ZenML: orchestrator, artifacts, and metadata
  - Orchestrator
  - Artifacts and metadata
  - How to run and configure a ZenML pipeline
- Comet ML: experiment tracker
- Opik: prompt monitoring

## Databases for storing unstructured and vector data
- MongoDB: NoSQL database
- Qdrant: vector database

## Preparing for AWS
- Setting up an AWS account, an access key, and the CLI
- SageMaker: training and inference compute
  - Why AWS SageMaker?

## Summary

## References

## Join our book’s Discord space

<!-- file: Chapter_03.xhtml -->

## 3

## Data Engineering

## Designing the LLM Twin’s data collection pipeline
- Implementing the LLM Twin’s data collection pipeline
- ZenML pipeline and steps
- The dispatcher: How do you instantiate the right crawler?
- The crawlers
  - Base classes
  - GitHubCrawler class
  - CustomArticleCrawler class
  - MediumCrawler class
- The NoSQL data warehouse documents
  - The ORM and ODM software patterns
  - Implementing the ODM class
  - Data categories and user document classes

## Gathering raw data into the data warehouse
- Troubleshooting
  - Selenium issues
  - Import our backed-up data

## Summary

## References
    - Unlock this book’s exclusive benefits now

<!-- file: Chapter_04.xhtml -->

## 4

## RAG Feature Pipeline

## Understanding RAG
- Why use RAG?
  - Hallucinations
  - Old information
- The vanilla RAG framework
  - Ingestion pipeline
  - Retrieval pipeline
  - Generation pipeline
- What are embeddings?
  - Why embeddings are so powerful
  - How are embeddings created?
  - Applications of embeddings
- More on vector DBs
  - How does a vector DB work?
  - Algorithms for creating the vector index
  - DB operations

## An overview of advanced RAG
- Pre-retrieval
- Retrieval
- Post-retrieval

## Exploring the LLM Twin’s RAG feature pipeline architecture
- The problem we are solving
- The feature store
- Where does the raw data come from?
- Designing the architecture of the RAG feature pipeline
  - Batch pipelines
  - Batch versus streaming pipelines
  - Core steps
  - Change data capture: syncing the data warehouse and feature store
  - Why is the data stored in two snapshots?
  - Orchestration

## Implementing the LLM Twin’s RAG feature pipeline
- Settings
- ZenML pipeline and steps
  - Querying the data warehouse
  - Cleaning the documents
  - Chunk and embed the cleaned documents
  - Loading the documents to the vector DB
- Pydantic domain entities
  - OVM
- The dispatcher layer
- The handlers
  - The cleaning handlers
  - The chunking handlers
  - The embedding handlers

## Summary

## References

## Join our book’s Discord space

<!-- file: Chapter_05.xhtml -->

## 5

## Supervised Fine-Tuning

## Creating an instruction dataset
- General framework
  - Data quantity
- Data curation
- Rule-based filtering
- Data deduplication
- Data decontamination
- Data quality evaluation
- Data exploration
- Data generation
- Data augmentation

## Creating our own instruction dataset

## Exploring SFT and its techniques
- When to fine-tune
- Instruction dataset formats
- Chat templates
- Parameter-efficient fine-tuning techniques
  - Full fine-tuning
  - LoRA
  - QLoRA
- Training parameters
  - Learning rate and scheduler
  - Batch size
  - Maximum length and packing
  - Number of epochs
  - Optimizers
  - Weight decay
  - Gradient checkpointing

## Fine-tuning in practice

## Summary

## References
    - Unlock this book’s exclusive benefits now

<!-- file: Chapter_06.xhtml -->

## 6

## Fine-Tuning with Preference Alignment

## Understanding preference datasets
- Preference data
  - Data quantity
- Data generation and evaluation
  - Generating preferences
  - Tips for data generation
  - Evaluating preferences

## Creating our own preference dataset

## Preference alignment
- Reinforcement Learning from Human Feedback
- Direct Preference Optimization

## Implementing DPO

## Summary

## References

## Join our book’s Discord space

<!-- file: Chapter_07.xhtml -->

## 7

## Evaluating LLMs

## Model evaluation
- Comparing ML and LLM evaluation
- General-purpose LLM evaluations
- Domain-specific LLM evaluations
- Task-specific LLM evaluations

## RAG evaluation
- Ragas
- ARES

## Evaluating TwinLlama-3.1-8B
- Generating answers
- Evaluating answers
- Analyzing results

## Summary

## References
    - Unlock this book’s exclusive benefits now

<!-- file: Chapter_08.xhtml -->

## 8

## Inference Optimization

## Model optimization strategies
- KV cache
- Continuous batching
- Speculative decoding
- Optimized attention mechanisms

## Model parallelism
- Data parallelism
- Pipeline parallelism
- Tensor parallelism
- Combining approaches

## Model quantization
- Introduction to quantization
- Quantization with GGUF and llama.cpp
- Quantization with GPTQ and EXL2
- Other quantization techniques

## Summary

## References

## Join our book’s Discord space

<!-- file: Chapter_09.xhtml -->

## 9

## RAG Inference Pipeline

## Understanding the LLM Twin’s RAG inference pipeline

## Exploring the LLM Twin’s advanced RAG techniques
- Advanced RAG pre-retrieval optimizations: query expansion and self-querying
  - Query expansion
  - Self-querying
- Advanced RAG retrieval optimization: filtered vector search
- Advanced RAG post-retrieval optimization: reranking

## Implementing the LLM Twin’s RAG inference pipeline
- Implementing the retrieval module
- Bringing everything together into the RAG inference pipeline

## Summary

## References
    - Unlock this book’s exclusive benefits now

<!-- file: Chapter_10.xhtml -->

## 10

## Inference Pipeline Deployment

## Criteria for choosing deployment types
- Throughput and latency
- Data

## Understanding inference deployment types
- Online real-time inference
- Asynchronous inference
- Offline batch transform

## Monolithic versus microservices architecture in model serving
- Monolithic architecture
- Microservices architecture
- Choosing between monolithic and microservices architectures

## Exploring the LLM Twin’s inference pipeline deployment strategy
- The training versus the inference pipeline

## Deploying the LLM Twin service
- Implementing the LLM microservice using AWS SageMaker
  - What are Hugging Face’s DLCs?
  - Configuring SageMaker roles
  - Deploying the LLM Twin model to AWS SageMaker
  - Calling the AWS SageMaker Inference endpoint
- Building the business microservice using FastAPI

## Autoscaling capabilities to handle spikes in usage
- Registering a scalable target
- Creating a scalable policy
- Minimum and maximum scaling limits
  - Cooldown period

## Summary

## References

## Join our book’s Discord space

<!-- file: Chapter_11.xhtml -->

## 11

## MLOps and LLMOps

## The path to LLMOps: Understanding its roots in DevOps and MLOps
- DevOps
  - The DevOps lifecycle
  - The core DevOps concepts
- MLOps
  - MLOps core components
  - MLOps principles
  - ML vs. MLOps engineering
- LLMOps
  - Human feedback
  - Guardrails
  - Prompt monitoring

## Deploying the LLM Twin’s pipelines to the cloud
- Understanding the infrastructure
- Setting up MongoDB
- Setting up Qdrant
- Setting up the ZenML cloud
  - Containerize the code using Docker
  - Run the pipelines on AWS
  - Troubleshooting the ResourceLimitExceeded error after running a ZenML pipeline on SageMaker

## Adding LLMOps to the LLM Twin
- LLM Twin’s CI/CD pipeline flow
  - More on formatting errors
  - More on linting errors
- Quick overview of GitHub Actions
- The CI pipeline
  - GitHub Actions CI YAML file
- The CD pipeline
- Test out the CI/CD pipeline
- The CT pipeline
  - Initial triggers
  - Trigger downstream pipelines
- Prompt monitoring
- Alerting

## Summary

## References
    - Unlock this book’s exclusive benefits now

<!-- file: Index.xhtml -->

## Index

<!-- file: Other_Books_You_May_Enjoy.xhtml -->

## Why subscribe?

## Other Books You May Enjoy

## Packt is searching for authors like you

## Share your thoughts

<!-- file: Preface.xhtml -->

## Preface

## Who this book is for

## What this book covers

## To get the most out of this book
- Download the example code files
- Download the color images
- Conventions used

## Get in touch

## Share your thoughts

## Making the Most Out of This Book – Get to Know Your Free Benefits

## Unlock Your Book’s Exclusive Benefits

## How to unlock these benefits in three easy steps
- Step 1
- Step 2
- Step 3

## Need help?

<!-- file: Title_Page.xhtml -->

## Forewords

## Contributors

## About the authors

## About the reviewer

## Join our book’s Discord space

<!-- file: toc.xhtml -->
- Contents

## Landmarks
