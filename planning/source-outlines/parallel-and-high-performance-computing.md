# parallel-and-high-performance-computing


<!-- file: A.htm -->

## appendix A References
- A.1 Chapter 1: Why parallel computing?
- A.2 Chapter 2: Planning for parallelism
- A.3 Chapter 3: Performance limits and profiling
- A.4 Chapter 4: Data design and performance models
- A.5 Chapter 5: Parallel algorithms and patterns
- A.6 Chapter 8: MPI: The parallel backbone
- A.7 Chapter 9: GPU architectures and concepts
- A.8 Chapter 10: GPU programming model
- A.9 Chapter 12: GPU languages: Getting down to basics
- A.10 Chapter 13: GPU profiling and tools
- A.11 Chapter 14: Affinity: Truce with the kernel
- A.12 Chapter 16: File operations for a parallel world
- A.13 Chapter 17: Tools and resources for better code

<!-- file: B.htm -->

## appendix B Solutions to exercises
- B.1 Chapter 1: Why parallel computing?
- B.2 Chapter 2: Planning for parallelism
- B.3 Chapter 3: Performance limits and profiling
- B.4 Chapter 4: Data design and performance models
- B.5 Chapter 5: Parallel algorithms and patterns
- B.6 Chapter 6: Vectorization: FLOPs for free
- B.7 Chapter 7: OpenMP that performs
- B.8 Chapter 8: MPI: The parallel backbone
- B.9 Chapter 9: GPU architectures and concepts
- B.10 Chapter 10: GPU programming model
- B.11 Chapter 11: Directive-based GPU programming
- B.12 Chapter 12: GPU languages: Getting down to basics
- B.13 Chapter 13: GPU profiling and tools
- B.14 Chapter 14: Affinity: Truce with the kernel
- B.15 Chapter 15: Batch schedulers: Bringing order to chaos
- B.16 Chapter 16: File operations for a parallel world
- B.17 Chapter 17: Tools and resources for better code

<!-- file: C.htm -->

## appendix C Glossary

<!-- file: FM.htm -->

## front matter
- foreword
  - Yulie Zamora, University of Chicago, Illinois
- How we came to write this book
- acknowledgments
- about this book
- Who should read this book
- How this book is organized: A roadmap
- About the code
- Software/hardware requirements
- liveBook discussion forum
- Other online resources
- About the cover illustration
- about the authors

<!-- file: PO-01_Robey.htm -->

## Part 1 Introduction to parallel computing

<!-- file: PO-02_Robey.htm -->

## Part 2 CPU: The parallel workhorse

<!-- file: PO-03_Robey.htm -->

## Part 3 GPUs: Built to accelerate

<!-- file: PO-04_Robey.htm -->

## Part 4 High performance computing ecosystems

<!-- file: Robey_BookIX.htm -->

## index

<!-- file: Robey_BookTOC.htm -->

## contents

<!-- file: ch01_Robey.htm -->

## 1 Why parallel computing?
- 1.1 Why should you learn about parallel computing?
  - 1.1.1 What are the potential benefits of parallel computing?
  - 1.1.2 Parallel computing cautions
- 1.2 The fundamental laws of parallel computing
  - 1.2.1 The limit to parallel computing: Amdahl’s Law
  - 1.2.2 Breaking through the parallel limit: Gustafson-Barsis’s Law
- 1.3 How does parallel computing work?
  - 1.3.1 Walking through a sample application
  - 1.3.2 A hardware model for today’s heterogeneous parallel systems
  - 1.3.3 The application/software model for today’s heterogeneous parallel systems
- 1.4 Categorizing parallel approaches
- 1.5 Parallel strategies
- 1.6 Parallel speedup versus comparative speedups: Two different measures
- 1.7 What will you learn in this book?
  - 1.7.1 Additional reading
  - 1.7.2 Exercises
- Summary

<!-- file: ch02_Robey.htm -->

## 2 Planning for parallelization
- 2.1 Approaching a new project: The preparation
  - 2.1.1 Version control: Creating a safety vault for your parallel code
  - 2.1.2 Test suites: The first step to creating a robust, reliable application
  - 2.1.3 Finding and fixing memory issues
  - 2.1.4 Improving code portability
- 2.2 Profiling: Probing the gap between system capabilities and application performance
- 2.3 Planning: A foundation for success
  - 2.3.1 Exploring with benchmarks and mini-apps
  - 2.3.2 Design of the core data structures and code modularity
  - 2.3.3 Algorithms: Redesign for parallel
- 2.4 Implementation: Where it all happens
- 2.5 Commit: Wrapping it up with quality
- 2.6 Further explorations
  - 2.6.1 Additional reading
  - 2.6.2 Exercises
- Summary

<!-- file: ch03_Robey.htm -->

## 3 Performance limits and profiling
- 3.1 Know your application’s potential performance limits
- 3.2 Determine your hardware capabilities: Benchmarking
  - 3.2.1 Tools for gathering system characteristics
  - 3.2.2 Calculating theoretical maximum flops
  - 3.2.3 The memory hierarchy and theoretical memory bandwidth
  - 3.2.4 Empirical measurement of bandwidth and flops
  - 3.2.5 Calculating the machine balance between flops and bandwidth
- 3.3 Characterizing your application: Profiling
  - 3.3.1 Profiling tools
  - 3.3.2 Empirical measurement of processor clock frequency and energy consumption
  - 3.3.3 Tracking memory during run time
- 3.4 Further explorations
  - 3.4.1 Additional reading
  - 3.4.2 Exercises
- Summary

<!-- file: ch04_Robey.htm -->

## 4 Data design and performance models
- 4.1 Performance data structures: Data-oriented design
  - 4.1.1 Multidimensional arrays
  - 4.1.2 Array of Structures (AoS) versus Structures of Arrays (SoA)
- 4.2 Three Cs of cache misses: Compulsory, capacity, conflict
- 4.3 Simple performance models: A case study
  - 4.3.2 Compressed sparse storage representations
- 4.4 Advanced performance models
- 4.5 Network messages
- 4.6 Further explorations
- Summary

<!-- file: ch05_Robey.htm -->

## 5 Parallel algorithms and patterns
- 5.1 Algorithm analysis for parallel computing applications
- 5.2 Performance models versus algorithmic complexity
- 5.3 Parallel algorithms: What are they?
- 5.4 What is a hash function?
- 5.5 Spatial hashing: A highly-parallel algorithm
  - 5.5.1 Using perfect hashing for spatial mesh operations
  - 5.5.2 Using compact hashing for spatial mesh operations
- 5.6 Prefix sum (scan) pattern and its importance in parallel computing
  - 5.6.1 Step-efficient parallel scan operation
  - 5.6.2 Work-efficient parallel scan operation
  - 5.6.3 Parallel scan operations for large arrays
- 5.7 Parallel global sum: Addressing the problem of associativity
- 5.8 Future of parallel algorithm research
- 5.9 Further explorations
  - 5.9.1 Additional reading
  - 5.9.2 Exercises
- Summary

<!-- file: ch06_Robey.htm -->

## 6 Vectorization: FLOPs for free
- 6.1 Vectorization and single instruction, multiple data (SIMD) overview
- 6.2 Hardware trends for vectorization
- 6.3 Vectorization methods
  - 6.3.1 Optimized libraries provide performance for little effort
  - 6.3.2 Auto-vectorization: The easy way to vectorization speedup (most of the time1)
  - 6.3.3 Teaching the compiler through hints: Pragmas and directives
  - 6.3.4 Crappy loops, we got them: Use vector intrinsics
  - 6.3.5 Not for the faint of heart: Using assembler code for vectorization
- 6.4 Programming style for better vectorization
- 6.5 Compiler flags relevant for vectorization for various compilers
- 6.6 OpenMP SIMD directives for better portability
- 6.7 Further explorations
  - 6.7.1 Additional reading
  - 6.7.2 Exercises
- Summary

<!-- file: ch07_Robey.htm -->

## 7 OpenMP that performs
- 7.1 OpenMP introduction
  - 7.1.1 OpenMP concepts
  - 7.1.2 A simple OpenMP program
- 7.2 Typical OpenMP use cases: Loop-level, high-level, and MPI plus OpenMP
  - 7.2.1 Loop-level OpenMP for quick parallelization
  - 7.2.2 High-level OpenMP for better parallel performance
  - 7.2.3 MPI plus OpenMP for extreme scalability
- 7.3 Examples of standard loop-level OpenMP
  - 7.3.1 Loop level OpenMP: Vector addition example
  - 7.3.2 Stream triad example
  - 7.3.3 Loop level OpenMP: Stencil example
  - 7.3.4 Performance of loop-level examples
  - 7.3.5 Reduction example of a global sum using OpenMP threading
  - 7.3.6 Potential loop-level OpenMP issues
- 7.4 Variable scope importance for correctness in OpenMP
- 7.5 Function-level OpenMP: Making a whole function thread parallel
- 7.6 Improving parallel scalability with high-level OpenMP
  - 7.6.1 How to implement high-level OpenMP
  - 7.6.2 Example of implementing high-level OpenMP
- 7.7 Hybrid threading and vectorization with OpenMP
- 7.8 Advanced examples using OpenMP
  - 7.8.1 Stencil example with a separate pass for the x and y directions
  - 7.8.2 Kahan summation implementation with OpenMP threading
  - 7.8.3 Threaded implementation of the prefix scan algorithm
- 7.9 Threading tools essential for robust implementations
  - 7.9.1 Using Allinea/ARM MAP to get a quick high-level profile of your application
  - 7.9.2 Finding your thread race conditions with Intel® Inspector
- 7.10 Example of a task-based support algorithm
- 7.11 Further explorations
  - 7.11.1 Additional reading
  - 7.11.2 Exercises
- Summary

<!-- file: ch08_Robey.htm -->

## 8 MPI: The parallel backbone
- 8.1 The basics for an MPI program
  - 8.1.1 Basic MPI function calls for every MPI program
  - 8.1.2 Compiler wrappers for simpler MPI programs
  - 8.1.3 Using parallel startup commands
  - 8.1.4 Minimum working example of an MPI program
- 8.2 The send and receive commands for process-to-process communication
- 8.3 Collective communication: A powerful component of MPI
  - 8.3.1 Using a barrier to synchronize timers
  - 8.3.2 Using the broadcast to handle small file input
  - 8.3.3 Using a reduction to get a single value from across all processes
  - 8.3.4 Using gather to put order in debug printouts
  - 8.3.5 Using scatter and gather to send data out to processes for work
- 8.4 Data parallel examples
  - 8.4.1 Stream triad to measure bandwidth on the node
  - 8.4.2 Ghost cell exchanges in a two-dimensional (2D) mesh
  - 8.4.3 Ghost cell exchanges in a three-dimensional (3D) stencil calculation
- 8.5 Advanced MPI functionality to simplify code and enable optimizations
  - 8.5.1 Using custom MPI data types for performance and code simplification
  - 8.5.2 Cartesian topology support in MPI
  - 8.5.3 Performance tests of ghost cell exchange variants
- 8.6 Hybrid MPI plus OpenMP for extreme scalability
  - 8.6.1 The benefits of hybrid MPI plus OpenMP
  - 8.6.2 MPI plus OpenMP example
- 8.7 Further explorations
  - 8.7.1 Additional reading
  - 8.7.2 Exercises
- Summary

<!-- file: ch09_Robey.htm -->

## 9 GPU architectures and concepts
- 9.1 The CPU-GPU system as an accelerated computational platform
  - 9.1.1 Integrated GPUs: An underused option on commodity-based systems
  - 9.1.2 Dedicated GPUs: The workhorse option
- 9.2 The GPU and the thread engine
  - 9.2.1 The compute unit is the streaming multiprocessor (or subslice)
  - 9.2.2 Processing elements are the individual processors
  - 9.2.3 Multiple data operations by each processing element
  - 9.2.4 Calculating the peak theoretical flops for some leading GPUs
- 9.3 Characteristics of GPU memory spaces
  - 9.3.1 Calculating theoretical peak memory bandwidth
  - 9.3.2 Measuring the GPU stream benchmark
  - 9.3.3 Roofline performance model for GPUs
  - 9.3.4 Using the mixbench performance tool to choose the best GPU for a workload
- 9.4 The PCI bus: CPU to GPU data transfer overhead
  - 9.4.1 Theoretical bandwidth of the PCI bus
  - 9.4.2 A benchmark application for PCI bandwidth
- 9.5 Multi-GPU platforms and MPI
  - 9.5.1 Optimizing the data movement between GPUs across the network
  - 9.5.2 A higher performance alternative to the PCI bus
- 9.6 Potential benefits of GPU-accelerated platforms
  - 9.6.1 Reducing time-to-solution
  - 9.6.2 Reducing energy use with GPUs
  - 9.6.3 Reduction in cloud computing costs with GPUs
- 9.7 When to use GPUs
- 9.8 Further explorations
  - 9.8.1 Additional reading
  - 9.8.2 Exercises
- Summary

<!-- file: ch10_Robey.htm -->

## 10 GPU programming model
- 10.1 GPU programming abstractions: A common framework
  - 10.1.1 Massive parallelism
  - 10.1.2 Inability to coordinate among tasks
  - 10.1.3 Terminology for GPU parallelism
  - 10.1.4 Data decomposition into independent units of work: An NDRange or grid
  - 10.1.5 Work groups provide a right-sized chunk of work
  - 10.1.6 Subgroups, warps, or wavefronts execute in lockstep
  - 10.1.7 Work item: The basic unit of operation
  - 10.1.8 SIMD or vector hardware
- 10.2 The code structure for the GPU programming model
  - 10.2.1 “Me” programming: The concept of a parallel kernel
  - 10.2.2 Thread indices: Mapping the local tile to the global world
  - 10.2.3 Index sets
  - 10.2.4 How to address memory resources in your GPU programming model
- 10.3 Optimizing GPU resource usage
  - 10.3.1 How many registers does my kernel use?
  - 10.3.2 Occupancy: Making more work available for work group scheduling
- 10.4 Reduction pattern requires synchronization across work groups
- 10.5 Asynchronous computing through queues (streams)
- 10.6 Developing a plan to parallelize an application for GPUs
  - 10.6.1 Case 1: 3D atmospheric simulation
  - 10.6.2 Case 2: Unstructured mesh application
- 10.7 Further explorations
  - 10.7.1 Additional reading
  - 10.7.2 Exercises
- Summary

<!-- file: ch11_Robey.htm -->

## 11 Directive-based GPU programming
- 11.1 Process to apply directives and pragmas for a GPU implementation
- 11.2 OpenACC: The easiest way to run on your GPU
  - 11.2.1 Compiling OpenACC code
  - 11.2.2 Parallel compute regions in OpenACC for accelerating computations
  - 11.2.3 Using directives to reduce data movement between the CPU and the GPU
  - 11.2.4 Optimizing the GPU kernels
  - 11.2.5 Summary of performance results for the stream triad
  - 11.2.6 Advanced OpenACC techniques
- 11.3 OpenMP: The heavyweight champ enters the world of accelerators
  - 11.3.1 Compiling OpenMP code
  - 11.3.2 Generating parallel work on the GPU with OpenMP
  - 11.3.3 Creating data regions to control data movement to the GPU with OpenMP
  - 11.3.4 Optimizing OpenMP for GPUs
  - 11.3.5 Advanced OpenMP for GPUs
- 11.4 Further explorations
  - 11.4.1 Additional reading
  - 11.4.2 Exercises
- Summary

<!-- file: ch12_Robey.htm -->

## 12 GPU languages: Getting down to basics
  - Figure 12.1 The interoperability map for the GPU languages shows an increasingly complex situation. Four GPU languages are shown at the top with the various hardware devices at the bottom. The arrows show the code generation pathways from the languages to the hardware. The dashed lines are for hardware that is still in development.
- 12.1 Features of a native GPU programming language
- 12.2 CUDA and HIP GPU languages: The low-level performance option
  - 12.2.1 Writing and building your first CUDA application
  - 12.2.2 A reduction kernel in CUDA: Life gets complicated
  - Figure 12.2 Pair-wise reduction tree for a warp that sums up values in log n steps.
  - 12.2.3 Hipifying the CUDA code
- 12.3 OpenCL for a portable open source GPU language
  - 12.3.1 Writing and building your first OpenCL application
  - 12.3.2 Reductions in OpenCL
  - Figure 12.3 Comparison of OpenCL and CUDA reduction kernels: sum_within_block
  - Figure 12.4 Comparison for the first of two kernel passes for the OpenCL and CUDA reduction kernels
  - Figure 12.5 Comparison of the second pass for the reduction sum
- 12.4 SYCL: An experimental C++ implementation goes mainstream
- 12.5 Higher-level languages for performance portability
  - 12.5.1 Kokkos: A performance portability ecosystem
  - 12.5.2 RAJA for a more adaptable performance portability layer
- 12.6 Further explorations
  - 12.6.1 Additional reading
  - 12.6.2 Exercises
- Summary

<!-- file: ch13_Robey.htm -->

## 13 GPU profiling and tools
- 13.1 An overview of profiling tools
- 13.2 How to select a good workflow
- 13.3 Example problem: Shallow water simulation
- 13.4 A sample of a profiling workflow
  - 13.4.1 Run the shallow water application
  - 13.4.2 Profile the CPU code to develop a plan of action
  - 13.4.3 Add OpenACC compute directives to begin the implementation step
  - 13.4.4 Add data movement directives
  - 13.4.5 Guided analysis can give you some suggested improvements
  - 13.4.6 The NVIDIA Nsight suite of tools can be a powerful development aid
  - 13.4.7 CodeXL for the AMD GPU ecosystem
- 13.5 Don’t get lost in the swamp: Focus on the important metrics
  - 13.5.1 Occupancy: Is there enough work?
  - 13.5.2 Issue efficiency: Are your warps on break too often?
  - 13.5.3 Achieved bandwidth: It always comes down to bandwidth
- 13.6 Containers and virtual machines provide alternate workflows
  - 13.6.1 Docker containers as a workaround
  - 13.6.2 Virtual machines using VirtualBox
- 13.7 Cloud options: A flexible and portable capability
- 13.8 Further explorations
  - 13.8.1 Additional reading
  - 13.8.2 Exercises
- Summary

<!-- file: ch14_Robey.htm -->

## 14 Affinity: Truce with the kernel
- 14.1 Why is affinity important?
- 14.2 Discovering your architecture
- 14.3 Thread affinity with OpenMP
- 14.4 Process affinity with MPI
  - 14.4.1 Default process placement with OpenMPI
  - 14.4.2 Taking control: Basic techniques for specifying process placement in OpenMPI
  - 14.4.3 Affinity is more than just process binding: The full picture
- 14.5 Affinity for MPI plus OpenMP
- 14.6 Controlling affinity from the command line
  - 14.6.1 Using hwloc-bind to assign affinity
  - 14.6.2 Using likwid-pin: An affinity tool in the likwid tool suite
- 14.7 The future: Setting and changing affinity at run time
  - 14.7.1 Setting affinities in your executable
  - 14.7.2 Changing your process affinities during run time
- 14.8 Further explorations
  - 14.8.1 Additional reading
  - 14.8.2 Exercises
- Summary

<!-- file: ch15_Robey.htm -->

## 15 Batch schedulers:Bringing order to chaos
- 15.1 The chaos of an unmanaged system
- 15.2 How not to be a nuisance when working on a busy cluster
  - 15.2.1 Layout of a batch system for busy clusters
  - 15.2.2 How to be courteous on busy clusters and HPC sites: Common HPC pet peeves
- 15.3 Submitting your first batch script
- 15.4 Automatic restarts for long-running jobs
- 15.5 Specifying dependencies in batch scripts
- 15.6 Further explorations
  - 15.6.1 Additional reading
  - 15.6.2 Exercises
- Summary

<!-- file: ch16_Robey.htm -->

## 16 File operations for a parallel world
- 16.1 The components of a high-performance filesystem
- 16.2 Standard file operations: A parallel-to-serial interface
- 16.3 MPI file operations (MPI-IO) for a more parallel world
- 16.4 HDF5 is self-describing for better data management
- 16.5 Other parallel file software packages
- 16.6 Parallel filesystem: The hardware interface
  - 16.6.1 Everything you wanted to know about your parallel file setup but didn’t know how to ask
  - 16.6.2 General hints that apply to all filesystems
  - 16.6.3 Hints specific to particular filesystems
- 16.7 Further explorations
  - 16.7.1 Additional reading
  - 16.7.2 Exercises
- Summary

<!-- file: ch17_Robey.htm -->

## 17 Tools and resources for better code
- 17.1 Version control systems: It all begins here
  - 17.1.1 Distributed version control fits the more mobile world
  - 17.1.2 Centralized version control for simplicity and code security
- 17.2 Timer routines for tracking code performance
- 17.3 Profilers: You can’t improve what you don’t measure
  - 17.3.1 Simple text-based profilers for everyday use
  - 17.3.2 High-level profilers for quickly identifying bottlenecks
  - 17.3.3 Medium-level profilers to guide your application development
  - 17.3.4 Detailed profilers give the gory details of hardware performance
- 17.4 Benchmarks and mini-apps: A window into system performance
  - 17.4.1 Benchmarks measure system performance characteristics
  - 17.4.2 Mini-apps give the application perspective
- 17.5 Detecting (and fixing) memory errors for a robust application
  - 17.5.1 Valgrind Memcheck: The open source standby
  - 17.5.2 Dr. Memory for your memory ailments
  - 17.5.3 Commercial memory tools for demanding applications
  - 17.5.4 Compiler-based memory tools for convenience
  - 17.5.5 Fence-post checkers detect out-of-bounds memory accesses
  - 17.5.6 GPU memory tools for robust GPU applications
- 17.6 Thread checkers for detecting race conditions
  - 17.6.1 Intel® Inspector: A race condition detection tool with a GUI
  - 17.6.2 Archer: A text-based tool for detecting race conditions
- 17.7 Bug-busters: Debuggers to exterminate those bugs
  - 17.7.1 TotalView debugger is widely available at HPC sites
  - 17.7.2 DDT is another debugger widely available at HPC sites
  - 17.7.3 Linux debuggers: Free alternatives for your local development needs
  - 17.7.4 GPU debuggers can help crush those GPU bugs
- 17.8 Profiling those file operations
- 17.9 Package managers: Your personal system administrator
  - 17.9.1 Package managers for macOS
  - 17.9.2 Package managers for Windows
  - 17.9.3 The Spack package manager: A package manager for high performance computing
- 17.10 Modules: Loading specialized toolchains
  - 17.10.1 TCL modules: The original modules system for loading software toolchains
  - 17.10.2 Lmod: A Lua-based alternative Modules implementation
- 17.11 Reflections and exercises
- Summary

<!-- file: copyright.xhtml -->

## Copyright

<!-- file: dedication_Robey.htm -->

## Dedication

<!-- file: title.xhtml -->

## Parallel and High Performance Computing
