# fluent-python-2nd-edition


<!-- file: afterword01.xhtml -->

## Afterword

## Further Reading

<!-- file: ch01.xhtml -->

## Chapter 1. The Python Data Model

## Magic and Dunder

## What’s New in This Chapter

## A Pythonic Card Deck

## Ellipsis in doctests

## How About Shuffling?

## How Special Methods Are Used
- Emulating Numeric Types
- String Representation
- Boolean Value of a Custom Type
- Collection API

## Overview of Special Methods

## Why len Is Not a Method

## Chapter Summary

## Further Reading

<!-- file: ch02.xhtml -->

## Chapter 2. An Array of Sequences

## What’s New in This Chapter

## Overview of Built-In Sequences

## List Comprehensions and Generator Expressions
- List Comprehensions and Readability

## Syntax Tip
- Listcomps Versus map and filter
- Cartesian Products
- Generator Expressions

## Tuples Are Not Just Immutable Lists
- Tuples as Records
- Tuples as Immutable Lists
- Comparing Tuple and List Methods

## Unpacking Sequences and Iterables
- Using * to Grab Excess Items
- Unpacking with * in Function Calls and Sequence Literals
- Nested Unpacking

## Pattern Matching with Sequences
- Pattern Matching Sequences in an Interpreter
  - Alternative patterns for lambda
  - Shortcut syntax for function definition

## Slicing
- Why Slices and Ranges Exclude the Last Item
- Slice Objects
- Multidimensional Slicing and Ellipsis
- Assigning to Slices

## Using + and * with Sequences
- Building Lists of Lists
- Augmented Assignment with Sequences
- A += Assignment Puzzler

## list.sort Versus the sorted Built-In

## When a List Is Not the Answer
- Arrays
- Memory Views
- NumPy
- Deques and Other Queues

## Chapter Summary

## Further Reading

<!-- file: ch03.xhtml -->

## Chapter 3. Dictionaries and Sets

## What’s New in This Chapter

## Modern dict Syntax
- dict Comprehensions
- Unpacking Mappings
- Merging Mappings with |

## Pattern Matching with Mappings

## Standard API of Mapping Types
- What Is Hashable
- Overview of Common Mapping Methods
- Inserting or Updating Mutable Values

## Automatic Handling of Missing Keys
- defaultdict: Another Take on Missing Keys
- The __missing__ Method
- Inconsistent Usage of __missing__ in the Standard Library

## Variations of dict
- collections.OrderedDict
- collections.ChainMap
- collections.Counter
- shelve.Shelf
- Subclassing UserDict Instead of dict

## Immutable Mappings

## Dictionary Views

## Practical Consequences of How dict Works

## Set Theory
- Set Literals

## Syntax Quirk
- Set Comprehensions

## Practical Consequences of How Sets Work
- Set Operations

## Set Operations on dict Views

## Chapter Summary

## Further Reading

<!-- file: ch04.xhtml -->

## Chapter 4. Unicode Text Versus Bytes

## What’s New in This Chapter

## Character Issues

## Byte Essentials

## Basic Encoders/Decoders

## Understanding Encode/Decode Problems
- Coping with UnicodeEncodeError
- Coping with UnicodeDecodeError
- SyntaxError When Loading Modules with Unexpected Encoding
- How to Discover the Encoding of a Byte Sequence
- BOM: A Useful Gremlin

## Caleb’s Tip about UTF-8-SIG

## Handling Text Files
- Beware of Encoding Defaults

## Normalizing Unicode for Reliable Comparisons
- Case Folding
- Utility Functions for Normalized Text Matching
- Extreme “Normalization”: Taking Out Diacritics

## Sorting Unicode Text
- Sorting with the Unicode Collation Algorithm

## PyICU: Miro’s Recommendation for Unicode Sorting

## The Unicode Database
- Finding Characters by Name
- Numeric Meaning of Characters

## Dual-Mode str and bytes APIs
- str Versus bytes in Regular Expressions
- str Versus bytes in os Functions

## Chapter Summary

## Further Reading

<!-- file: ch05.xhtml -->

## Chapter 5. Data Class Builders

## What’s New in This Chapter

## Overview of Data Class Builders
- Main Features
  - Mutable instances
  - Class statement syntax
  - Construct dict
  - Get field names and default values
  - Get field types
  - New instance with changes
  - New class at runtime

## Classic Named Tuples

## Typed Named Tuples

## Type Hints 101
- No Runtime Effect
- Variable Annotation Syntax
- The Meaning of Variable Annotations
  - Inspecting a typing.NamedTuple
  - Inspecting a class decorated with dataclass

## More About @dataclass
- Field Options
- Post-init Processing
- Typed Class Attributes
- Initialization Variables That Are Not Fields
- @dataclass Example: Dublin Core Resource Record

## Data Class as a Code Smell
- Data Class as Scaffolding
- Data Class as Intermediate Representation

## Pattern Matching Class Instances
- Simple Class Patterns
- Keyword Class Patterns
- Positional Class Patterns

## Chapter Summary

## Further Reading

<!-- file: ch06.xhtml -->

## Chapter 6. Object References, Mutability, and Recycling

## What’s New in This Chapter

## Variables Are Not Boxes

## Identity, Equality, and Aliases
- Choosing Between == and is
- The Relative Immutability of Tuples

## Copies Are Shallow by Default
- Deep and Shallow Copies of Arbitrary Objects

## Function Parameters as References
- Mutable Types as Parameter Defaults: Bad Idea
- Defensive Programming with Mutable Parameters

## del and Garbage Collection

## Tricks Python Plays with Immutables

## Chapter Summary

## Further Reading

<!-- file: ch07.xhtml -->

## Chapter 7. Functions as First-Class Objects

## What’s New in This Chapter

## Treating a Function Like an Object

## Higher-Order Functions
- Modern Replacements for map, filter, and reduce

## Anonymous Functions

## The Nine Flavors of Callable Objects

## User-Defined Callable Types

## From Positional to Keyword-Only Parameters
- Positional-Only Parameters

## Packages for Functional Programming
- The operator Module
- Freezing Arguments with functools.partial

## Chapter Summary

## Further Reading

<!-- file: ch08.xhtml -->

## Chapter 8. Type Hints in Functions

## What’s New in This Chapter

## About Gradual Typing

## Gradual Typing in Practice
- Starting with Mypy
- Making Mypy More Strict
- A Default Parameter Value
- Using None as a Default

## Types Are Defined by Supported Operations

## Types Usable in Annotations
- The Any Type
  - Subtype-of versus consistent-with
- Simple Types and Classes

## int Is Consistent-With complex
- Optional and Union Types

## Better Syntax for Optional and Union in Python 3.10
- Generic Collections
- Tuple Types
  - Tuples as records
  - Tuples as records with named fields
  - Tuples as immutable sequences
- Generic Mappings
- Abstract Base Classes
  - The fall of the numeric tower
- Iterable

## Stub Files and the Typeshed Project

## Explicit TypeAlias in Python 3.10
  - abc.Iterable versus abc.Sequence
- Parameterized Generics and TypeVar

## Why Is TypeVar Needed?
  - Restricted TypeVar
  - Bounded TypeVar
  - The AnyStr predefined type variable
- Static Protocols
- Callable
  - Variance in Callable types
- NoReturn

## Annotating Positional Only and Variadic Parameters

## Imperfect Typing and Strong Testing

## Chapter Summary

## Further Reading

<!-- file: ch09.xhtml -->

## Chapter 9. Decorators and Closures

## What’s New in This Chapter

## Decorators 101

## When Python Executes Decorators

## Registration Decorators

## Variable Scope Rules

## Closures

## The nonlocal Declaration
- Variable Lookup Logic

## Implementing a Simple Decorator
- How It Works

## Decorators in the Standard Library
- Memoization with functools.cache

## Stacked Decorators
- Using lru_cache
- Single Dispatch Generic Functions
  - Function singledispatch

## Parameterized Decorators
- A Parameterized Registration Decorator
- The Parameterized Clock Decorator
- A Class-Based Clock Decorator

## Chapter Summary

## Further Reading

<!-- file: ch10.xhtml -->

## Chapter 10. Design Patterns with First-Class Functions

## What’s New in This Chapter

## Case Study: Refactoring Strategy
- Classic Strategy
- Function-Oriented Strategy

## Why self.promotion(self)?
- Choosing the Best Strategy: Simple Approach
- Finding Strategies in a Module

## Decorator-Enhanced Strategy Pattern

## The Command Pattern

## Chapter Summary

## Further Reading

<!-- file: ch11.xhtml -->

## Chapter 11. A Pythonic Object

## What’s New in This Chapter

## Object Representations

## Vector Class Redux

## An Alternative Constructor

## classmethod Versus staticmethod

## Formatted Displays

## A Hashable Vector2d

## Supporting Positional Pattern Matching

## Complete Listing of Vector2d, Version 3

## Private and “Protected” Attributes in Python

## Saving Memory with __slots__
- Simple Measure of __slot__ Savings
- Summarizing the Issues with __slots__

## Overriding Class Attributes

## Chapter Summary

## Further Reading

<!-- file: ch12.xhtml -->

## Chapter 12. Special Methods for Sequences

## What’s New in This Chapter

## Vector: A User-Defined Sequence Type

## Vector Take #1: Vector2d Compatible

## Protocols and Duck Typing

## Vector Take #2: A Sliceable Sequence
- How Slicing Works
- A Slice-Aware __getitem__

## Vector Take #3: Dynamic Attribute Access

## Vector Take #4: Hashing and a Faster ==

## New zip() Option in Python 3.10

## Vector Take #5: Formatting

## Chapter Summary

## Further Reading

<!-- file: ch13.xhtml -->

## Chapter 13. Interfaces, Protocols, and ABCs

## The Typing Map

## What’s New in This Chapter

## Two Kinds of Protocols

## Programming Ducks
- Python Digs Sequences
- Monkey Patching: Implementing a Protocol at Runtime
- Defensive Programming and “Fail Fast”

## Goose Typing
- Subclassing an ABC
- ABCs in the Standard Library
- Defining and Using an ABC
- ABC Syntax Details
- Subclassing an ABC
- A Virtual Subclass of an ABC
- Usage of register in Practice
- Structural Typing with ABCs

## Static Protocols
- The Typed double Function
- Runtime Checkable Static Protocols
- Limitations of Runtime Protocol Checks
- Supporting a Static Protocol
- Designing a Static Protocol
- Best Practices for Protocol Design
- Extending a Protocol
- The numbers ABCs and Numeric Protocols

## Chapter Summary

## Further Reading

<!-- file: ch14.xhtml -->

## Chapter 14. Inheritance: For Better or for Worse

## What’s New in This Chapter

## The super() Function

## Subclassing Built-In Types Is Tricky

## Multiple Inheritance and Method Resolution Order

## Mixin Classes
- Case-Insensitive Mappings

## Multiple Inheritance in the Real World
- ABCs Are Mixins Too
- ThreadingMixIn and ForkingMixIn
- Django Generic Views Mixins
- Multiple Inheritance in Tkinter

## Coping with Inheritance
- Favor Object Composition over Class Inheritance
- Understand Why Inheritance Is Used in Each Case
- Make Interfaces Explicit with ABCs
- Use Explicit Mixins for Code Reuse
- Provide Aggregate Classes to Users
- Subclass Only Classes Designed for Subclassing
- Avoid Subclassing from Concrete Classes
- Tkinter: The Good, the Bad, and the Ugly

## Chapter Summary

## Further Reading

<!-- file: ch15.xhtml -->

## Chapter 15. More About Type Hints

## What’s New in This Chapter

## Overloaded Signatures

## Take Advantage of Gradual Typing
- Max Overload
  - Arguments implementing SupportsLessThan, but key and default not provided
  - Argument key provided, but no default
  - Argument default provided, but no key
  - Arguments key and default provided
- Takeaways from Overloading max

## TypedDict

## Type Casting

## Reading Type Hints at Runtime
- Problems with Annotations at Runtime
- Dealing with the Problem

## Implementing a Generic Class
- Basic Jargon for Generic Types

## Variance
- An Invariant Dispenser
- A Covariant Dispenser
- A Contravariant Trash Can
- Variance Review
  - Invariant types
  - Covariant types
  - Contravariant types
  - Variance rules of thumb

## Implementing a Generic Static Protocol

## Chapter Summary

## Further Reading

<!-- file: ch16.xhtml -->

## Chapter 16. Operator Overloading

## What’s New in This Chapter

## Operator Overloading 101

## Unary Operators

## Overloading + for Vector Addition

## Overloading * for Scalar Multiplication

## Using @ as an Infix Operator

## New zip() Feature in Python 3.10

## Wrapping-Up Arithmetic Operators

## Rich Comparison Operators

## Augmented Assignment Operators

## Chapter Summary

## Further Reading

<!-- file: ch17.xhtml -->

## Chapter 17. Iterators, Generators, and Classic Coroutines

## What’s New in This Chapter

## A Sequence of Words

## Why Sequences Are Iterable: The iter Function
- Using iter with a Callable

## Iterables Versus Iterators

## Sentence Classes with __iter__
- Sentence Take #2: A Classic Iterator
- Don’t Make the Iterable an Iterator for Itself
- Sentence Take #3: A Generator Function
- How a Generator Works

## Lazy Sentences
- Sentence Take #4: Lazy Generator
- Sentence Take #5: Lazy Generator Expression

## When to Use Generator Expressions

## Syntax Tip

## An Arithmetic Progression Generator
- Arithmetic Progression with itertools

## Generator Functions in the Standard Library

## Iterable Reducing Functions

## Subgenerators with yield from
- Reinventing chain
- Traversing a Tree

## Generic Iterable Types

## Classic Coroutines
- Example: Coroutine to Compute a Running Average
- Returning a Value from a Coroutine
- Generic Type Hints for Classic Coroutines

## Chapter Summary

## Further Reading

<!-- file: ch18.xhtml -->

## Chapter 18. with, match, and else Blocks

## What’s New in This Chapter

## Context Managers and with Blocks

## Parenthesized Context Managers in Python 3.10
- The contextlib Utilities
- Using @contextmanager

## Pattern Matching in lis.py: A Case Study
- Scheme Syntax
- Imports and Types
- The Parser
- The Environment
- The REPL
- The Evaluator
  - Evaluating numbers
  - Evaluating symbols
  - (quote …)
  - (if …)
  - (lambda …)
  - (define …)
  - (set! …)
  - Function call
  - Catch syntax errors
- Procedure: A Class Implementing a Closure
- Using OR-patterns

## Do This, Then That: else Blocks Beyond if

## Chapter Summary

## Further Reading

<!-- file: ch19.xhtml -->

## Chapter 19. Concurrency Models in Python

## What’s New in This Chapter

## The Big Picture

## A Bit of Jargon
- Processes, Threads, and Python’s Infamous GIL

## A Concurrent Hello World
- Spinner with Threads
- Spinner with Processes
- Spinner with Coroutines
  - Experiment: Break the spinner for an insight
- Supervisors Side-by-Side

## The Real Impact of the GIL
- Quick Quiz
  - 1. Answer for multiprocessing
  - 2. Answer for threading
  - 3. Answer for asyncio

## A Homegrown Process Pool
- Process-Based Solution
- Understanding the Elapsed Times
- Code for the Multicore Prime Checker
- Experimenting with More or Fewer Processes
- Thread-Based Nonsolution

## Python in the Multicore World
- System Administration
- Data Science
- Server-Side Web/Mobile Development
- WSGI Application Servers

## ASGI—Asynchronous Server Gateway Interface
- Distributed Task Queues

## Chapter Summary

## Further Reading
- Concurrency with Threads and Processes
- The GIL
- Concurrency Beyond the Standard Library
- Concurrency and Scalability Beyond Python

<!-- file: ch20.xhtml -->

## Chapter 20. Concurrent Executors

## What’s New in This Chapter

## Concurrent Web Downloads
- A Sequential Download Script
- Downloading with concurrent.futures
- Where Are the Futures?

## Launching Processes with concurrent.futures
- Multicore Prime Checker Redux

## Experimenting with Executor.map

## Downloads with Progress Display and Error Handling

## Be Careful when Testing Concurrent Clients

## Setting Up Test Servers
- Error Handling in the flags2 Examples
- Using futures.as_completed

## Chapter Summary

## Further Reading

<!-- file: ch21.xhtml -->

## Chapter 21. Asynchronous Programming

## What’s New in This Chapter

## A Few Definitions

## @asyncio.coroutine has No Future4

## An asyncio Example: Probing Domains
- Guido’s Trick to Read Asynchronous Code

## New Concept: Awaitable

## Downloading with asyncio and HTTPX
- The Secret of Native Coroutines: Humble Generators
- The All-or-Nothing Problem

## Asynchronous Context Managers

## Caleb Hattingh on asyncpg

## Enhancing the asyncio Downloader

## Act Responsibly When Testing Concurrent Clients
- Using asyncio.as_completed and a Thread
- Throttling Requests with a Semaphore
- Making Multiple Requests for Each Download

## Delegating Tasks to Executors

## Caleb’s Warning about run_in_executors

## Writing asyncio Servers
- A FastAPI Web Service
- An asyncio TCP Server

## Asynchronous Iteration and Asynchronous Iterables
- Asynchronous Generator Functions
  - Experimenting with Python’s async console
  - Implementing an asynchronous generator
  - Asynchronous generators as context managers
  - Asynchronous generators versus native coroutines
- Async Comprehensions and Async Generator Expressions
  - Defining and using an asynchronous generator expression
  - Asynchronous comprehensions

## async Beyond asyncio: Curio

## Type Hinting Asynchronous Objects

## How Async Works and How It Doesn’t
- Running Circles Around Blocking Calls
- The Myth of I/O-Bound Systems
- Avoiding CPU-Bound Traps

## Chapter Summary

## Further Reading

<!-- file: ch22.xhtml -->

## Chapter 22. Dynamic Attributes and Properties

## What’s New in This Chapter

## Data Wrangling with Dynamic Attributes
- Exploring JSON-Like Data with Dynamic Attributes
- The Invalid Attribute Name Problem
- Flexible Object Creation with __new__

## Computed Properties
- Step 1: Data-Driven Attribute Creation
- Step 2: Property to Retrieve a Linked Record
- Step 3: Property Overriding an Existing Attribute
- Step 4: Bespoke Property Cache
- Step 5: Caching Properties with functools

## Using a Property for Attribute Validation
- LineItem Take #1: Class for an Item in an Order
- LineItem Take #2: A Validating Property

## A Proper Look at Properties
- Properties Override Instance Attributes
- Property Documentation

## Coding a Property Factory

## Handling Attribute Deletion

## Essential Attributes and Functions for Attribute Handling
- Special Attributes that Affect Attribute Handling
- Built-In Functions for Attribute Handling
- Special Methods for Attribute Handling

## Chapter Summary

## Further Reading

<!-- file: ch23.xhtml -->

## Chapter 23. Attribute Descriptors

## What’s New in This Chapter

## Descriptor Example: Attribute Validation
- LineItem Take #3: A Simple Descriptor
  - Terms to understand descriptors
- LineItem Take #4: Automatic Naming of Storage Attributes
- LineItem Take #5: A New Descriptor Type

## Overriding Versus Nonoverriding Descriptors
- Overriding Descriptors
- Overriding Descriptor Without __get__
- Nonoverriding Descriptor
- Overwriting a Descriptor in the Class

## Methods Are Descriptors

## Descriptor Usage Tips

## Descriptor Docstring and Overriding Deletion

## Chapter Summary

## Further Reading

<!-- file: ch24.xhtml -->

## Chapter 24. Class Metaprogramming

## What’s New in This Chapter

## Classes as Objects

## type: The Built-In Class Factory

## A Class Factory Function

## Introducing __init_subclass__

## Checked Subclasses and Static Type Checking
- Why __init_subclass__ Cannot Configure __slots__

## Enhancing Classes with a Class Decorator

## What Happens When: Import Time Versus Runtime
- Evaluation Time Experiments

## Metaclasses 101
- How a Metaclass Customizes a Class
- A Nice Metaclass Example
- Metaclass Evaluation Time Experiment

## A Metaclass Solution for Checked

## Metaclasses in the Real World
- Modern Features Simplify or Replace Metaclasses
- Metaclasses Are Stable Language Features
- A Class Can Only Have One Metaclass
- Metaclasses Should Be Implementation Details

## A Metaclass Hack with __prepare__

## Wrapping Up

## Chapter Summary

## Further Reading

<!-- file: colophon01.xhtml -->

## About the Author

<!-- file: colophon02.xhtml -->

## Colophon

<!-- file: copyright-page01.xhtml -->

## Fluent Python

## Revision History for the Second Edition

<!-- file: dedication01.xhtml -->

## Dedication

<!-- file: ix01.xhtml -->

## Index
  - Symbols
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

<!-- file: part01.xhtml -->

## Part I. Data Structures

<!-- file: part02.xhtml -->

## Part II. Functions as Objects

<!-- file: part03.xhtml -->

## Part III. Classes and Protocols

<!-- file: part04.xhtml -->

## Part IV. Control Flow

<!-- file: part05.xhtml -->

## Part V. Metaprogramming

<!-- file: preface01.xhtml -->

## Preface

## Who This Book Is For

## Who This Book Is Not For

## Five Books in One
- How the Book Is Organized

## Hands-On Approach

## Soapbox: My Personal Perspective

## Companion Website: fluentpython.com

## Conventions Used in This Book

## Using Code Examples

## O’Reilly Online Learning

## How to Contact Us

## Acknowledgments
- Acknowledgments for the First Edition

<!-- file: titlepage01.xhtml -->

## Fluent Python
