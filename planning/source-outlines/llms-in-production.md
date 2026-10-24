# llms-in-production


<!-- file: about-the-authors.xhtml -->

## about the authors

<!-- file: about-the-book.xhtml -->

## about the book
- Who should read this book
- How this book is organized
- About the code
- liveBook Discussion Forum

<!-- file: about-the-cover-illustration.xhtml -->

## about the cover illustration

<!-- file: acknowledgments.xhtml -->

## acknowledgments

<!-- file: appendix-a.xhtml -->

## appendix A History of linguistics
- A.1 Ancient linguistics
- A.2 Medieval linguistics
- A.3 Renaissance and early modern linguistics
- A.4 Early 20th-century linguistics
- A.5 Mid-20th century and modern linguistics

<!-- file: appendix-b.xhtml -->

## appendix B Reinforcement learning with human feedback

<!-- file: appendix-c.xhtml -->

## appendix C Multimodal latent spaces

<!-- file: chapter-1.xhtml -->

## 1 Words’ awakening: Why large language models have captured attention
  - This chapter covers
- 1.1 Large language models accelerating communication
- 1.2 Navigating the build-and-buy decision with LLMs
  - 1.2.1 Buying: The beaten path
  - 1.2.2 Building: The path less traveled
    - Control
    - Competitive edge
    - Integrate anywhere
    - Costs
    - Security and privacy
    - Wrapping up
  - 1.2.3 A word of warning: Embrace the future now
- 1.3 Debunking myths
- Summary

<!-- file: chapter-10.xhtml -->

## 10 Creating a coding copilot project: This would have helped you earlier
  - This chapter covers
- 10.1 Our model
- 10.2 Data is king
  - 10.2.1 Our VectorDB
  - 10.2.2 Our dataset
  - 10.2.3 Using RAG
- 10.3 Build the VS Code extension
- 10.4 Lessons learned and next steps
- Summary

<!-- file: chapter-11.xhtml -->

## 11 Deploying an LLM on a Raspberry Pi: How low can you go?
  - This chapter covers
- 11.1 Setting up your Raspberry Pi
  - 11.1.1 Pi Imager
  - 11.1.2 Connecting to Pi
  - 11.1.3 Software installations and updates
- 11.2 Preparing the model
- 11.3 Serving the model
- 11.4 Improvements
  - 11.4.1 Using a better interface
  - 11.4.2 Changing quantization
  - 11.4.3 Adding multimodality
    - Updating the model
    - Serving the model
  - 11.4.4 Serving the model on Google Colab
- Summary

<!-- file: chapter-12.xhtml -->

## 12 Production, an ever-changing landscape: Things are just getting started
  - This chapter covers
- 12.1 A thousand-foot view
- 12.2 The future of LLMs
  - 12.2.1 Government and regulation
    - Copyright
    - AI detection
    - Bias and ethics
    - Laws are coming
  - 12.2.2 LLMs are getting bigger
    - Larger context windows
    - The next attention
    - Pushing the boundaries of compression
  - 12.2.3 Multimodal spaces
  - 12.2.4 Datasets
  - 12.2.5 Solving hallucination
    - Better prompt engineering
    - Grounding
    - Knowledge editing
  - 12.2.6 New hardware
  - 12.2.7 Agents will become useful
- 12.3 Final thoughts
- Summary

<!-- file: chapter-2.xhtml -->

## 2 Large language models: A deep dive into language modeling
  - This chapter covers
- 2.1 Language modeling
  - 2.1.1 Linguistic features
    - Phonetics
    - Syntax
    - Semantics
    - Pragmatics
    - Morphology
  - 2.1.2 Semiotics
  - 2.1.3 Multilingual NLP
- 2.2 Language modeling techniques
  - 2.2.1 N-gram and corpus-based techniques
  - 2.2.2 Bayesian techniques
  - 2.2.3 Markov chains
  - 2.2.4 Continuous language modeling
  - 2.2.5 Embeddings
  - 2.2.6 Multilayer perceptrons
  - 2.2.7 Recurrent neural networks and long short-term memory networks
  - 2.2.8 Attention
- 2.3 Attention is all you need
  - 2.3.1 Encoders
  - 2.3.2 Decoders
  - 2.3.3 Transformers
- 2.4 Really big transformers
- Summary

<!-- file: chapter-3.xhtml -->

## 3 Large language model operations: Building a platform for LLMs
  - This chapter covers
- 3.1 Introduction to large language model operations
- 3.2 Operations challenges with large language models
  - 3.2.1 Long download times
  - 3.2.2 Longer deploy times
  - 3.2.3 Latency
  - 3.2.4 Managing GPUs
  - 3.2.5 Peculiarities of text data
  - 3.2.6 Token limits create bottlenecks
  - 3.2.7 Hallucinations cause confusion
  - 3.2.8 Bias and ethical considerations
  - 3.2.9 Security concerns
  - 3.2.10 Controlling costs
- 3.3 LLMOps essentials
  - 3.3.1 Compression
    - Quantizing
    - Pruning
    - Knowledge distillation
    - Low-rank approximation
    - Mixture of experts
  - 3.3.2 Distributed computing
    - Data parallelism
    - Tensor parallelism
    - Pipeline parallelism
    - 3D parallelism
- 3.4 LLM operations infrastructure
  - 3.4.1 Data infrastructure
  - 3.4.2 Experiment trackers
  - 3.4.3 Model registry
  - 3.4.4 Feature stores
  - 3.4.5 Vector databases
  - 3.4.6 Monitoring system
  - 3.4.7 GPU-enabled workstations
  - 3.4.8 Deployment service
- Summary

<!-- file: chapter-4.xhtml -->

## 4 Data engineering for large language models: Setting up for success
  - This chapter covers
- 4.1 Models are the foundation
  - 4.1.1 GPT
  - 4.1.2 BLOOM
  - 4.1.3 LLaMA
  - 4.1.4 Wizard
  - 4.1.5 Falcon
  - 4.1.6 Vicuna
  - 4.1.7 Dolly
  - 4.1.8 OpenChat
- 4.2 Evaluating LLMs
  - 4.2.1 Metrics for evaluating text
    - ROUGE
    - BLEU
    - BPC
  - 4.2.2 Industry benchmarks
    - GLUE
    - SuperGLUE
    - MMLU
  - 4.2.3 Responsible AI benchmarks
  - 4.2.4 Developing your own benchmark
  - 4.2.5 Evaluating code generators
  - 4.2.6 Evaluating model parameters
- 4.3 Data for LLMs
  - 4.3.1 Datasets you should know
    - Wikitext
    - Wiki-40B
    - Europarl
    - Common Crawl
    - OpenWebText
    - The Pile
    - RedPajama
    - OSCAR
    - Summary of datasets
    - Corpora
  - 4.3.2 Data cleaning and preparation
    - Instruct schema
    - Ensuring proficiency with speech acts
    - Annotating the data
- 4.4 Text processors
  - 4.4.1 Tokenization
    - Word-based
    - Character-based
    - Subword-based
  - 4.4.2 Embeddings
- 4.5 Preparing a Slack dataset
- Summary

<!-- file: chapter-5.xhtml -->

## 5 Training large language models: How to generate the generator
  - This chapter covers
- 5.1 Multi-GPU environments
  - 5.1.1 Setting up
    - Google virtual machine
    - SSH through VS Code
  - 5.1.2 Libraries
    - DeepSpeed
    - Accelerate
    - BitsandBytes
    - xFormers
- 5.2 Basic training techniques
  - 5.2.1 From scratch
  - 5.2.2 Transfer learning (finetuning)
    - Finetuning
    - Finetuning OpenAI
  - 5.2.3 Prompting
- 5.3 Advanced training techniques
  - 5.3.1 Prompt tuning
  - 5.3.2 Finetuning with knowledge distillation
  - 5.3.3 Reinforcement learning with human feedback
  - 5.3.4 Mixture of experts
  - 5.3.5 LoRA and PEFT
- 5.4 Training tips and tricks
  - 5.4.1 Training data size notes
  - 5.4.2 Efficient training
  - 5.4.3 Local minima traps
  - 5.4.4 Hyperparameter tuning tips
  - 5.4.5 A note on operating systems
  - 5.4.6 Activation function advice
- Summary

<!-- file: chapter-6.xhtml -->

## 6 Large language model services: A practical guide
  - This chapter covers
- 6.1 Creating an LLM service
  - 6.1.1 Model compilation
    - Kernel tuning
    - Tensor fusion
    - Graph optimization
    - TensorRT
    - ONNX Runtime
  - 6.1.2 LLM storage strategies
    - Fusing
    - Baking the model
    - Mounted volume
    - Hybrid: Intermediary mounted volume
  - 6.1.3 Adaptive request batching
  - 6.1.4 Flow control
  - 6.1.5 Streaming responses
  - 6.1.6 Feature store
  - 6.1.7 Retrieval-augmented generation
  - 6.1.8 LLM service libraries
- 6.2 Setting up infrastructure
  - 6.2.1 Provisioning clusters
  - 6.2.2 Autoscaling
    - Target parameter
    - Target threshold
    - Minimum pod replicas
    - Maximum pod replicas
    - Scaling policies
  - 6.2.3 Rolling updates
  - 6.2.4 Inference graphs
  - 6.2.5 Monitoring
- 6.3 Production challenges
  - 6.3.1 Model updates and retraining
  - 6.3.2 Load testing
  - 6.3.3 Troubleshooting poor latency
  - 6.3.4 Resource management
  - 6.3.5 Cost engineering
  - 6.3.6 Security
- 6.4 Deploying to the edge
- Summary

<!-- file: chapter-7.xhtml -->

## 7 Prompt engineering: Becoming an LLM whisperer
  - This chapter covers
- 7.1 Prompting your model
  - 7.1.1 Few-shot prompting
  - 7.1.2 One-shot prompting
  - 7.1.3 Zero-shot prompting
- 7.2 Prompt engineering basics
  - 7.2.1 Anatomy of a prompt
  - 7.2.2 Prompting hyperparameters
  - 7.2.3 Scrounging the training data
- 7.3 Prompt engineering tooling
  - 7.3.1 LangChain
  - 7.3.2 Guidance
  - 7.3.3 DSPy
  - 7.3.4 Other tooling is available but …
- 7.4 Advanced prompt engineering techniques
  - 7.4.1 Giving LLMs tools
  - 7.4.2 ReAct
- Summary

<!-- file: chapter-8.xhtml -->

## 8 Large language model applications: Building an interactive experience
  - This chapter covers
- 8.1 Building an application
  - 8.1.1 Streaming on the frontend
  - 8.1.2 Keeping a history
  - 8.1.3 Chatbot interaction features
  - 8.1.4 Token counting
  - 8.1.5 RAG applied
- 8.2 Edge applications
- 8.3 LLM agents
- Summary

<!-- file: chapter-9.xhtml -->

## 9 Creating an LLM project: Reimplementing Llama 3
  - This chapter covers
- 9.1 Implementing Meta’s Llama
  - 9.1.1 Tokenization and configuration
  - 9.1.2 Dataset, data loading, evaluation, and generation
  - 9.1.3 Network architecture
- 9.2 Simple Llama
- 9.3 Making it better
  - 9.3.1 Quantization
  - 9.3.2 LoRA
  - 9.3.3 Fully sharded data parallel–quantized LoRA
- 9.4 Deploy to a Hugging Face Hub Space
- Summary

<!-- file: contents.xhtml -->

## contents

<!-- file: copyright.xhtml -->

## copyright

## LLMs in Production

<!-- file: dedication.xhtml -->

## dedication

<!-- file: foreword.xhtml -->

## foreword

<!-- file: index.xhtml -->

## index

<!-- file: preface.xhtml -->

## preface

<!-- file: title.xhtml -->

## LLMs in Production
