# kubernetes-programming-with-go-programming-kubernetes-clients-and-operators-using-go-and-the-kuberne


<!-- file: 533908_1_En_10_Chapter.xhtml -->

## 10. Writing Operators withthe Controller-Runtime Library
- The Manager
- The Controller
  - Creating a Controller
  - Watching Resources
  - A First Example
  - Using the Controller Builder
  - A Second Example Using the ControllerBuilder
  - Injecting Manager Resources into the Reconciler
    - Passing the Values When Creating the Reconciler Structure
    - Using Injectors
- Using the Client
  - Getting Information About a Resource
  - Listing Resources
  - Creating a Resource
  - Deleting a Resource
  - Deleting a Collection of Resources
  - Updating a Resource
  - Patching a Resource
    - Server-side Apply
    - Strategic Merge Patch
    - Merge Patch
  - Updating the Status of a Resource
  - Patching the Status of a Resource
- Logging
  - Verbosity
  - Predefined Values
  - Logger Name
  - Getting the Logger from Context
- Events
- Conclusion

<!-- file: 533908_1_En_11_Chapter.xhtml -->

## 11. Writing the Reconcile Loop
- Writing the Reconcile Function
  - Checking Whether the Resource Exists
  - Implementing the Reconciled Resource
  - Simple Implementation Example
- Conclusion

<!-- file: 533908_1_En_12_Chapter.xhtml -->

## 12. Testing the Reconcile Loop
- The envtest Package
  - Installing envtest Binaries
  - Using envtest
- Defining a ginkgo Suite
- Writing the Tests
  - Test 1
  - Test 2
  - Test 3
  - Test 4
- Conclusion

<!-- file: 533908_1_En_13_Chapter.xhtml -->

## 13. Creating an Operator with Kubebuilder
- Installing Kubebuilder
- Creating a Project
- Adding a Custom Resource to the Project
- Building and Deploying Manifests
- Running the Manager Locally
- Personalizing the Custom Resource
  - Editing the Go Structures
  - Enabling the Status Subresource
  - Defining Printer Columns
  - Regenerating the Files
- Implementing the Reconcile Function
- Adding RBAC Annotations
- Deploying the Operator on the Cluster
- Creating a New Version of the Resource
  - Defining a New Version
  - Implementing Hub and Convertible
  - Setting Up the webhook
  - Updating kustomization Files
  - Using Various Versions
- Conclusion

<!-- file: 533908_1_En_1_Chapter.xhtml -->

## 1. Kubernetes API Introduction
- Kubernetes Platform at a Glance
- OpenAPI Specification
- Verbs and Kinds
- Group-Version-Resource
- Sub-resources
- Official API Reference Documentation
  - The Deployment Documentation
  - Operations Documentation
  - The Pod Documentation
  - One-Page Version of the Documentation
- Conclusion

<!-- file: 533908_1_En_2_Chapter.xhtml -->

## 2. Kubernetes API Operations
- Examining Requests
- Making Requests
  - Using kubectl as a Proxy
  - Creating a Resource
  - Getting Information About a Resource
  - Getting the List of Resources
    - Cluster-wide
    - In a Specific namespace
  - Filtering the Result of a List
    - Using Label Selectors
    - Using Field Selectors
  - Deleting a Resource
  - Deleting a Collection of Resources
  - Updating a Resource
  - Managing Conflicts When Updating a Resource
  - Using a Strategic Merge Patch to Update a Resource
    - Patching Array Fields
    - Special Directives
  - Applying Resources Server-side
  - Watching Resources
  - Filtering During a Watch Session
  - Watching After Listing Resources
  - Restarting a watch Request
  - Allowing Bookmarks to Efficiently Restart a watch Request
  - Paginating Results
    - Consistency of the Full List
    - Detecting the Last Chunk
- Getting Results in Various Formats
  - Getting Results as a Table
    - Column Definitions
    - Row Data
  - Using the YAML Format
  - Using the Protobuf Format
- Conclusion

<!-- file: 533908_1_En_3_Chapter.xhtml -->

## 3. Working with API Resources in Go
- API Library Sources and Import
- Content of a Package
  - types.go
  - register.go
  - doc.go
  - generated.pb.go and generated.proto
  - types_swagger_doc_generated.go
  - zz_generated.deepcopy.go
- Specific Content in core/v1
  - ObjectReference
  - ResourceList
  - Taint
  - Toleration
  - Well-Known Labels
- Writing Kubernetes Resources in Go
  - Importing the Package
  - The TypeMeta Fields
  - The ObjectMeta Fields
    - Name
    - Namespace
    - UID, ResourceVersion, and Generation
    - Labels and Annotations
    - OwnerReferences
  - Spec and Status
  - Comparison with Writing YAML Manifests
- A Complete Example
- Conclusion

<!-- file: 533908_1_En_4_Chapter.xhtml -->

## 4. Using Common Types
- Pointers
  - Getting the Reference of a Value
  - Dereferencing a Pointer
  - Comparing Two Referenced Values
- Quantities
  - Parsing a String as Quantity
  - Using an inf.Dec as a Quantity
  - Using a Scaled Integer as a Quantity
  - Operations on Quantities
- IntOrString
- Time
  - Factory Methods
  - Operations on Time
- Conclusion

<!-- file: 533908_1_En_5_Chapter.xhtml -->

## 5. The API Machinery
- The Schema Package
- Scheme
  - Initialization
  - Mapping
  - Conversion
    - Adding Conversion Functions
    - Converting
  - Serialization
    - JSON and YAML Serializer
    - Protobuf Serializer
    - Encoding and Decoding
- RESTMapper
  - Kind to Resource
  - Resource to Kind
  - Finding Resources
  - The DefaultRESTMapper Implementation
- Conclusion

<!-- file: 533908_1_En_6_Chapter.xhtml -->

## 6. The Client-go Library
- Connecting to the Cluster
  - In-cluster Configuration
  - Out-of-Cluster Configuration
    - From kubeconfig in Memory
    - From a kubeconfig on Disk
    - From a Personalized kubeconfig
    - From Several kubeconfig Files
    - Overriding kubeconfig with CLI Flags
- Getting a Clientset
- Using the Clientset
- Examining the Requests
- Creating a Resource
- Getting Information About a Resource
- Getting List of Resources
- Filtering the Result of a List
  - Setting LabelSelector Using the Labels Package
    - Using Requirements
    - Parsing a LabelSelector String
    - Using a Set of Key-value Pairs
  - Setting Fieldselector Using the Fields Package
    - Assembling One Term Selectors
    - Parsing a FieldSelector String
    - Using a Set of Key-Value Pairs
- Deleting a Resource
- Deleting a Collection of Resources
- Updating a Resource
- Using a Strategic Merge Patch to Update a Resource
- Applying Resources Server-side with Patch
- Server-side Apply Using Apply Configurations
  - Building an ApplyConfiguration from Scratch
  - Building an ApplyConfiguration from an Existing Resource
- Watching Resources
- Errors and Statuses
  - Definition of the metav1.Status Structure
  - Error Returned by Clientset Operations
- RESTClient
  - Building the Request
  - Executing the Request
  - Exploiting the Result
- Getting Result as a Table
- Discovery Client
- RESTMapper
  - PriorityRESTMapper
  - DeferredDiscoveryRESTMapper
- Conclusion

<!-- file: 533908_1_En_7_Chapter.xhtml -->

## 7. Testing Applications Using Client-go
- Fake Clientset
  - Checking the Result of the Function
  - Reacting to Actions
  - Checking the Actions
- Fake REST Client
- FakeDiscovery Client
  - Stubbing the ServerVersion
  - Actions
  - Mocking Resources
- Conclusion

<!-- file: 533908_1_En_8_Chapter.xhtml -->

## 8. Extending Kubernetes API with Custom Resources Definitions
- Performing Operations in Go
- The CustomResourceDefinition in Detail
  - Naming the Resource
  - Definition of the Resource Versions
  - Converting Between Versions
- Schema of the Resource
- Deploying a Custom Resource Definition
- Additional Printer Columns
- Conclusion

<!-- file: 533908_1_En_9_Chapter.xhtml -->

## 9. Working with Custom Resources
- Generating a Clientset
  - Using deepcopy-gen
    - Installing deepcopy-gen
    - Adding Annotations
    - Running deepcopy-gen
  - Using client-gen
    - Installing client-go
    - Adding Annotations
    - Adding AddToScheme Function
    - Running client-go
  - Using the Generated Clientset
  - Using the Generated fake Clientset
- Using the Unstructured Package and Dynamic Client
  - The Unstructured Type
    - Getters and Setters to Access TypeMeta Fields
    - Getters and Setters to Access ObjectMeta Fields
    - Methods for Creating and Converting
    - Helpers to Access Non-meta Fields
    - Example
  - The UnstructuredList Type
    - Getters and Setters to Access TypeMeta Fields
    - Getters and Setters to Access ListMeta Fields
    - Methods for Creating and Converting
  - Converting Between Typed and Unstructured Objects
  - The Dynamic Client
    - Getting the dynamic Client
    - Working with the dynamic Client
    - Example
    - The fake dynamic Client
- Conclusion

<!-- file: 533908_1_En_BookFrontmatter_OnlinePDF.xhtml -->

## Kubernetes Programming with Go
- Programming Kubernetes Clients and Operators Using Go and the Kubernetes API
- Chapters at a Glance
