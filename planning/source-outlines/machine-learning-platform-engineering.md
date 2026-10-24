# machine-learning-platform-engineering


<!-- file: about-the-authors.xhtml -->

## about the authors

<!-- file: about-the-cover-illustration.xhtml -->

## about the cover illustration

<!-- file: about-this-book.xhtml -->

## about this book
- Who should read this book?
- What you’ll build
- How this book is organized: A road map
- About the code
- liveBook discussion forum

<!-- file: acknowledgments.xhtml -->

## acknowledgments

<!-- file: appendix-a.xhtml -->

## appendix A Installation and setup
- A.1 Local installation of command-line tools (Mac and Linux)
  - A.1.1 The yq YAML processor
  - A.1.2 Kustomize
  - A.1.3 Kubectl
  - A.1.4 K8s distribution
  - A.1.5 K3s installation
  - A.1.6 MicroK8s installation
  - A.1.7 Argo CD
  - A.1.8 Kubeflow
  - A.1.9 Cloud provider K8s setup
  - A.1.10 MLflow setup
    - Setting up Postgres
    - Building the MLflow Docker image
- A.2 Deploy MLflow
  - A.2.1 Redis online store setup
  - A.2.2 BentoML and Yatai setup
  - A.2.3 Evidently UI setup

<!-- file: appendix-b.xhtml -->

## appendix B Basics of YAML
- B.1 Basic YAML files
  - B.1.1 Comments
  - B.1.2 Scalar values
  - B.1.3 Lists
  - B.1.4 Nested structures (maps)
  - B.1.5 Quoted strings
  - B.1.6 Multiline strings
  - B.1.7 Data types in YAML
    - Boolean
    - Null
    - Integers and floats
- B.2 Aliases and anchors
  - B.2.1 References (merging and reusing data)
  - B.2.2 Complex data types
    - Mapping inside a list
    - Lists inside a map
  - B.2.3 Custom data types
  - B.2.4 Block style vs. flow style
    - Block style
    - Flow style
  - B.2.5 Key sorting and case sensitivity
  - B.2.6 Best practices

<!-- file: chapter-1.xhtml -->

## 1 Getting started with MLOps and ML engineering
  - This chapter covers
- 1.1 The ML life cycle
  - 1.1.1 Experimentation phase
    - Problem formulation
    - Data collection and preparation
    - Data versioning
    - Model training
    - Model evaluation
    - Model validation
  - 1.1.2 Development/staging/production phase
    - Model deployment
    - Model monitoring
    - Model retraining
- 1.2 Skills needed for MLOps
  - 1.2.1 Required skills for ML engineers
  - 1.2.2 Prerequisites
- 1.3 Building an ML platform
  - 1.3.1 Build vs. buy
  - 1.3.2 Looking ahead: From MLOps to LLMOps
  - 1.3.3 Tools used in this book
    - ML pipeline automation
    - Feature store
    - Model registry
    - Model deployment
- 1.4 Building ML systems
  - 1.4.1 Introducing the ML projects
  - 1.4.2 ML projects
    - Project 1: Building an OCR system
    - Project 2: Movie recommender
    - Project 3: A documentation assistant powered by Retrieval-Augmented Generation
- Summary

<!-- file: chapter-10.xhtml -->

## 10 Model inference and serving
  - This chapter covers
- 10.1 Model deployment is hard
- 10.2 BentoML: Simplifying model deployment
- 10.3 A whirlwind tour of BentoML
  - 10.3.1 BentoML Service and Runners
- 10.4 Executing a BentoML Service locally
  - 10.4.1 Loading a model with BentoML Runner
    - Why is the await keyword needed?
    - Multiple BentoML Runners
    - Implementing the /render endpoint
    - Observability endpoints: Ensuring service health and reliability
- 10.5 Building Bentos: Packaging your service for deployment
  - 10.5.1 Bento tags: Versioning and managing your Bentos
- 10.6 BentoML and MLflow inference
- 10.7 Using only MLflow to create an inference service
- 10.8 KServe: An alternative to BentoML
- Summary

<!-- file: chapter-11.xhtml -->

## 11 Monitoring and explainability
  - This chapter covers
- 11.1 Monitoring
  - 11.1.1 Basic monitoring
  - 11.1.2 Custom metrics
  - 11.1.3 Logging
  - 11.1.4 Alerting
- 11.2 Data drift detection
  - 11.2.1 Object detection
  - 11.2.2 Movie recommender
- 11.3 Explainability
  - 11.3.1 Object detection
  - 11.3.2 Movie recommendation
- Summary

<!-- file: chapter-12.xhtml -->

## 12 Designing LLM-powered systems
  - This chapter covers
- 12.1 LLMOps: New challenges, familiar principles
  - 12.1.1 What makes LLM applications different
    - Nondeterministic outputs requiring new testing approaches
    - Understanding LLM sampling parameters
    - Token limits and context windows
    - LLM sampling parameters control output variability
    - Multistep reasoning chains vs. single model predictions
    - Prompt engineering as a new discipline
    - Token-based cost models vs. compute-time pricing
  - 12.1.2 Extending our ML platform for LLMs
    - Where traditional MLOps practices still apply
    - LLM deployment metadata: Beyond model weights
    - New components for LLM applications
    - An example integration
  - 12.1.3 Essential tools for LLM applications
    - LLMs and embeddings
    - FAISS: An efficient vector DB
    - LangChain: A framework for building LLM applications
    - Langfuse: An open source LLM engineering platform
    - Promptfoo: Open source LLM security
- 12.2 Building DataKrypt’s DakkaBot: A simple RAG architecture
  - 12.2.1 What you’ll build
  - 12.2.2 Beyond single API calls: Designing for composability
    - The limitations of single LLM calls for complex tasks
    - Why RAG solves these problems
  - 12.2.3 Google’s Gemini LLM and embeddings
    - Getting started with Google Gemini
    - Production considerations
  - 12.2.4 The retrieval component
    - Starting with semantic search using embeddings
    - Retrieval quality factors
    - Production retrieval considerations
    - Building the document index
    - Step 1: Document loading
    - Step 2: Intelligent document chunking
    - Step 3: Creating the vector index
    - Step 4: Persistent storage
    - Step 5: Complete indexing pipeline
  - 12.2.5 The augmentation component
    - From retrieval to context assembly
    - Query processing and document retrieval
  - 12.2.6 The generation component
    - LLM configuration for consistent responses
    - Prompt construction and response generation
    - The complete RAG flow
- 12.3 Giving DakkaBot a UI
    - Installing Chainlit
    - Extracting DakkaBotCore for reusability
    - Enhanced query processing with metadata
    - Streaming support for modern chat experience
    - Simple interface wrappers
    - Building the chat interface with Chainlit
    - Real-time message processing with streaming
    - Running the application
- 12.4 Observability for LLM applications
  - 12.4.1 Set up Langfuse via Docker
  - 12.4.2 Integrating Langfuse with DakkaBot
  - 12.4.3 Enhanced observability in DakkaBotCore
  - 12.4.4 Beyond traditional metrics
    - Why accuracy and latency aren’t enough
    - Tracing multistep reasoning
    - Token consumption monitoring
    - The evolution of the ML infrastructure
- Summary

<!-- file: chapter-13.xhtml -->

## 13 Production LLM system design
  - This chapter covers
- 13.1 Prompt engineering: Code for the generative AI era
  - 13.1.1 Treating prompts as critical infrastructure
    - Version 1.0: The problematic baseline
    - Version 2.0: Production-ready architecture
  - 13.1.2 Langfuse prompt management for DakkaBot
    - Creating prompts in Langfuse
    - Deployment management and configuration
    - Creating boundary prompts for error handling
    - The infrastructure advantage
    - Using managed prompts in DakkaBotCore
    - Integrating Langfuse into DakkaBotCore
    - Runtime prompt resolution and configuration
    - Template compilation and response generation
    - Error handling and graceful degradation
  - 13.1.3 Langfuse prompt management for production
    - Deployment and environment management
    - Collaborative prompt development
    - A/B testing and performance optimization
    - Caching and performance considerations
    - Getting started with Langfuse
- 13.2 Testing LLM applications
  - 13.2.1 Evaluation framework for LLM responses
    - Creating a test helper function
    - Understanding G-Eval: LLM-as-Judge evaluation
    - Testing security boundaries with G-Eval
    - How G-Eval criteria encode security behavior
    - Testing multiple metrics simultaneously
    - G-Eval considerations
  - 13.2.2 Safety and adversarial testing
    - Prompt injection attacks on RAG systems with Promptfoo
    - Setting up Promptfoo for adversarial testing
    - Understanding the test generation results
    - Analyzing Promptfoo test results
- 13.3 Governance and safety in production
  - 13.3.1 Implementing safety guardrails
    - Input sanitization and PII detection
    - Installing essential validators
    - Implementing input guards
    - Exploring the Guardrails AI Hub
    - LLM-specific safety settings
    - Output validation implementation
    - Hallucination testing framework
- 13.4 Cost optimization strategies
  - 13.4.1 Understanding LLM economics
  - 13.4.2 Model selection strategy
  - 13.4.3 Caching strategies
    - Context caching for cost reduction
    - Semantic caching for similar questions
    - Semantic caching implementation with RedisVL
  - 13.4.4 Prompt optimization for efficiency
  - 13.4.5 Production cost monitoring
    - Set up cost alerts and budgets
    - Use Langfuse for cost analysis
  - 13.4.6 From traditional ML to LLMOps
    - The engineering fundamentals remain
    - Your journey forward
- Summary

<!-- file: chapter-2.xhtml -->

## 2 What is MLOps?
  - This chapter covers
- 2.1 The iterative MLOps life cycle
  - 2.1.1 Data collection
  - 2.1.2 Exploratory Data Analysis
  - 2.1.3 Modeling and training
  - 2.1.4 Model evaluation
  - 2.1.5 Deployment
  - 2.1.6 Monitoring
  - 2.1.7 Maintenance, updates, and review
- 2.2 Why is robust MLOps important ?
- 2.3 Role of MLOps in a mature organization
- 2.4 DevOps vs. MLOps
- 2.5 Levels of MLOps maturity
  - 2.5.1 Level 0: Basic
  - 2.5.2 Level 1: Intermediate
  - 2.5.3 Level 2: Advanced
- Summary

<!-- file: chapter-3.xhtml -->

## 3 Building applications on Kubernetes
  - This chapter covers
- 3.1 Containers and tooling
- 3.2 Docker
  - 3.2.1 Write the application code
  - 3.2.2 Write a Dockerfile
  - 3.2.3 Building and pushing a Docker image
- 3.3 Kubernetes
  - 3.3.1 Kubernetes architecture overview
  - 3.3.2 Kubectl
  - 3.3.3 Kubernetes objects
    - Pods
    - ReplicaSets
    - Deployments
  - 3.3.4 Networking and services
    - NodePort
    - ClusterIP
    - LoadBalancer
  - 3.3.5 Other objects
    - Namespaces
    - ConfigMaps
    - Secrets
  - 3.3.6 Helm charts
  - 3.3.7 Conclusion
- 3.4 Continuous integration and deployment
  - 3.4.1 GitLab CI
  - 3.4.2 Argo CD
- 3.5 Prometheus and Grafana
- Summary

<!-- file: chapter-4.xhtml -->

## 4 Designing reliable ML systems
  - This chapter covers
- 4.1 MLflow for experiment tracking
  - 4.1.1 Data exploration
  - 4.1.2 MLflow tracking
  - 4.1.3 MLflow model registry
    - Using the MLflow UI
    - MLflow client
- 4.2 Feast as a feature store
  - 4.2.1 Registering features
  - 4.2.2 Retrieving features
  - 4.2.3 Feature server
  - 4.2.4 Using the Feast UI
- Summary

<!-- file: chapter-5.xhtml -->

## 5 Orchestrating ML pipelines
  - This chapter covers
- 5.1 Kubeflow Pipelines: Task orchestrator
  - 5.1.1 Kubeflow components
    - Read data component
    - Feature retrieval component
    - Inference component
    - Write data component
  - 5.1.2 Income classifier pipeline
- Summary

<!-- file: chapter-6.xhtml -->

## 6 Productionizing ML models
  - This chapter covers
- 6.1 BentoML as a deployment platform
  - 6.1.1 Building a Bento
    - Registering the model
    - Initializing the service and runner
    - Defining the service
    - Defining the bentofile.yaml
  - 6.1.2 Building and pushing the Bento
  - 6.1.3 Deploying a Bento
- 6.2 Evidently for data drift monitoring
  - 6.2.1 Data drift detection report and dashboard
  - 6.2.2 Data drift detection Kubeflow pipeline component
  - 6.2.3 Data drift detection for a model deployed as an API
- Summary

<!-- file: chapter-7.xhtml -->

## 7 Data analysis and preparation
  - This chapter covers
    - Capstone project 1: ID card detection
    - Capstone project 2: Movie recommendations
- 7.1 Data analysis
  - 7.1.1 Launching a notebook server in Kubeflow
  - 7.1.2 Workspace and data volumes
  - 7.1.3 Configurations and affinity/tolerations
  - 7.1.4 Customizing the menu
    - Customizing images shown to the user
    - Affinity and tolerations groups
  - 7.1.5 Creating a custom Kubeflow notebook image
- 7.2 Data passing
  - 7.2.1 Scenario 1: Passing simple values to downstream components
  - 7.2.2 Scenario 2: Passing paths for larger data
  - 7.2.3 Overview of KFP v2 artifact types
    - Dataset type: Represents any form of ML dataset
    - Model type: Represents trained ML models
    - Metrics type: Stores simple key-value metrics
    - ClassificationMetrics type: Specialized metrics for classification tasks
    - HTML type: HTML content for visualization and reporting
    - Markdown type: Markdown formatted documentation and reports
    - Artifact type: Base type for generic artifacts
- 7.3 Data preparation in action
  - 7.3.1 Data preparation: Object detection
    - Background: What YOLO expects
    - MIDV-500 : Dataset used for object detection examples
    - Dataset download component
    - Step 1: Download data from remote locations
    - Step 2: Uncompress the tar file
    - Step 3: Create a MinIO bucket and copy data
    - Step 4: Turning this into a Kubeflow component
    - Bonus step: Using the component in a pipeline
    - Passing data between components
    - Dataset splitting component
    - Step 1: Dataset splitting for YOLO and installing custom packages
    - Step 2: Outputting file contents from input files
    - Full pipeline from components
    - Upload and run pipeline
  - 7.3.2 Data preparation: Movie recommender
    - MovieLens 25M : Dataset used for recommender examples
    - The plan
    - Dataset download
    - Dataset unzip
    - Parquet conversion
    - Data split
    - Data upload
    - Data quality assessment
    - Full pipeline from components
    - Running the pipeline
- Summary

<!-- file: chapter-8.xhtml -->

## 8 Model training and validation: Part 1
  - This chapter covers
- 8.1 Training an object detection model
  - 8.1.1 Training YOLO on a custom dataset
  - 8.1.2 Training the model
    - Why model architecture matters
    - Hyperparameters in YOLO
  - 8.1.3 Container components for system dependencies
    - Step 1: Creating the training script
    - Step 2: Customizing the component using a container component
    - Step 3: Integrating the training script into the component
    - Step 4: Using the component
  - 8.1.4 Creating the validation component
  - 8.1.5 Creating the pipeline
  - 8.1.6 Executing the pipeline
  - 8.1.7 Validating model artifacts
- Summary

<!-- file: chapter-9.xhtml -->

## 9 Model training and validation: Part 2
  - This chapter covers
- 9.1 Storing data with PersistentVolumeClaim
  - 9.1.1 Refactoring the pipeline with a PVC
  - 9.1.2 Efficient dataset management
  - 9.1.3 Creating a VolumeOp
  - 9.1.4 Download Op using PVC
  - 9.1.5 Splitting the dataset directly
  - 9.1.6 Simplifying model training
  - 9.1.7 Simplifying model validation
- 9.2 Tracking training with TensorBoard
  - 9.2.1 Launching a new TensorBoard
  - 9.2.2 Exploring YOLOv8’s default graphs
    - Understanding model complexity
- 9.3 Movie recommender project
  - 9.3.1 Reading data from MinIO and quality assurance
  - 9.3.2 Model training component
  - 9.3.3 Metrics for evaluation
  - 9.3.4 Experiment tracking with MLflow
  - 9.3.5 Model registry with MLflow
  - 9.3.6 Creating a pipeline from components
  - 9.3.7 Local inference in a notebook
- Summary

<!-- file: contents.xhtml -->

## contents

<!-- file: copyright.xhtml -->
- copyright

<!-- file: dedication.xhtml -->

## dedication

<!-- file: index.xhtml -->

## index

<!-- file: part-1.xhtml -->

## Part 1 Laying the MLOps foundation

<!-- file: part-2.xhtml -->

## Part 2 Building core ML platform capabilities

<!-- file: part-3.xhtml -->

## Part 3 Applying MLOps in practice

<!-- file: part-4.xhtml -->

## Part 4 Extending MLOps for large language models

<!-- file: preface.xhtml -->

## preface

<!-- file: title.xhtml -->
- Build a Machine Learning Platform (From Scratch)
