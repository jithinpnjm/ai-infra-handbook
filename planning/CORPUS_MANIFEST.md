# Corpus manifest (private; lives outside the repo)

Location: `~/Desktop/books-toon-rag/<slug>/` with `<slug>_chunks.jsonl` (+ `.toon`, `OEBPS/` for books). Search index: `~/Desktop/books-toon-rag/_index/chunks.db`.

## How to rebuild or extend
1. O'Reilly books: log in to learning.oreilly.com in Chrome, run `scripts/refresh_cookies.py --watch 60` inside `~/oreilly-downloader`, reload the tab whenever the token expires (about every 15 min), then run `tools/corpus/download_books.py <book-id> ...` using the `~/oreilly-downloader/.venv` Python. The downloader's `plugins/chunking.py` contains our overlap fix (uncommitted in that repo; without it chunk files explode in size).
2. Vendor PDFs: `python3 tools/coverage/ingest_pdfs.py file.pdf ...` (needs `pdftotext` and `pypdf`).
3. Author's volumes: `python3 tools/coverage/ingest_md.py` (reads `~/Documents/GitHub/nvidia-devops/docs`).
4. Outlines: `python3 tools/coverage/extract_outlines.py` (books) , outlines for PDFs/volumes are written by their ingest scripts.
5. Search index: `python3 tools/study_rag/ingest.py`, then `python3 tools/study_rag/query.py "terms" -n 8 [--book SUBSTR] [--full]`.

## Entries

| Slug | Title | Book id | Kind |
|---|---|---|---|
| ai-data-center-network-design-and-technologies | AI Data Center Network Design and Technologies | 9780135436370 | O'Reilly book |
| ai-engineering | AI Engineering | 9781098166298 | O'Reilly book |
| ai-factory | AI Factory | 9781000865073 | O'Reilly book |
| ai-networking-cookbook | AI Networking Cookbook | 9781805807995 | O'Reilly book |
| ai-systems-performance-engineering | AI Systems Performance Engineering | 9798341627772 | O'Reilly book |
| ansible-up-and-running-3rd-edition | Ansible: Up and Running, 3rd Edition | 9781098109141 | O'Reilly book |
| bcm11-admin |  | - | vendor PDF |
| bcm11-containerization |  | - | vendor PDF |
| bcm11-install |  | - | vendor PDF |
| building-python-web-apis-with-fastapi | Building Python Web APIs with FastAPI | 9781801076630 | O'Reilly book |
| computer-networking-problems-and-solutions | Computer Networking Problems and Solutions | 9780134762814 | O'Reilly book |
| designing-machine-learning-systems | Designing Machine Learning Systems | 9781098107956 | O'Reilly book |
| distributed-ai-systems | Distributed AI Systems | 9781807301712 | O'Reilly book |
| engineering-ai-systems-architecture-and-devops-essentials | Engineering AI Systems: Architecture and DevOps Essentials | 9780138261542 | O'Reilly book |
| fluent-python-2nd-edition | Fluent Python, 2nd Edition | 9781492056348 | O'Reilly book |
| generative-ai-on-kubernetes | Generative AI on Kubernetes | 9781098171919 | O'Reilly book |
| hands-on-llm-serving-and-optimization | Hands-On LLM Serving and Optimization | 9798341621480 | O'Reilly book |
| how-linux-works-3rd-edition | How Linux Works, 3rd Edition | 9781098128913 | O'Reilly book |
| kubernetes-for-generative-ai-solutions | Kubernetes for Generative AI Solutions | 9781836209935 | O'Reilly book |
| kubernetes-programming-with-go-programming-kubernetes-clients-and-operators-using-go-and-the-kuberne | Kubernetes Programming with Go: Programming Kubernetes Clients and Operators Using Go and the Kubernetes API | 9781484290262 | O'Reilly book |
| kubernetes-up-and-running-3rd-edition | Kubernetes: Up and Running, 3rd Edition | 9781098110192 | O'Reilly book |
| learning-python-6th-edition | Learning Python, 6th Edition | 9781098171292 | O'Reilly book |
| llm-engineers-handbook | LLM Engineer's Handbook | 9781836200079 | O'Reilly book |
| llmops | LLMOps | 9781098154196 | O'Reilly book |
| llms-in-production | LLMs in Production | 9781633437203 | O'Reilly book |
| machine-learning-platform-engineering | Machine Learning Platform Engineering | 9781633437333 | O'Reilly book |
| network-programmability-and-automation-2nd-edition | Network Programmability and Automation, 2nd Edition | 9781098110826 | O'Reilly book |
| networking-and-kubernetes | Networking and Kubernetes | 9781492081647 | O'Reilly book |
| nvidia-devops-core-interview |  | - | author's own volume |
| nvidia-devops-intro |  | - | author's own volume |
| nvidia-devops-legacy-v01 |  | - | author's own volume |
| nvidia-devops-legacy-v02 |  | - | author's own volume |
| nvidia-devops-legacy-v03 |  | - | author's own volume |
| nvidia-devops-legacy-v04 |  | - | author's own volume |
| nvidia-devops-legacy-v05 |  | - | author's own volume |
| nvidia-devops-legacy-v06 |  | - | author's own volume |
| nvidia-devops-legacy-v07 |  | - | author's own volume |
| nvidia-devops-legacy-v08 |  | - | author's own volume |
| nvidia-devops-legacy-v09 |  | - | author's own volume |
| nvidia-devops-zth-v01 |  | - | author's own volume |
| nvidia-devops-zth-v02 |  | - | author's own volume |
| nvidia-devops-zth-v03 |  | - | author's own volume |
| nvidia-devops-zth-v04 |  | - | author's own volume |
| nvidia-devops-zth-v05 |  | - | author's own volume |
| nvidia-devops-zth-v06 |  | - | author's own volume |
| nvidia-devops-zth-v07 |  | - | author's own volume |
| nvidia-devops-zth-v08 |  | - | author's own volume |
| nvidia-devops-zth-v09 |  | - | author's own volume |
| nvidia-devops-zth-v10 |  | - | author's own volume |
| nvidia-devops-zth-v11 |  | - | author's own volume |
| nvidia-devops-zth-v12 |  | - | author's own volume |
| nvidia-devops-zth-v13 |  | - | author's own volume |
| nvidia-devops-zth-v14 |  | - | author's own volume |
| nvidia-devops-zth-v15 |  | - | author's own volume |
| nvidia-devops-zth-v16 |  | - | author's own volume |
| nvidia-devops-zth-v17 |  | - | author's own volume |
| nvidia-devops-zth-v18 |  | - | author's own volume |
| nvidia-devops-zth-v19 |  | - | author's own volume |
| nvidia-devops-zth-v20 |  | - | author's own volume |
| nvidia-devops-zth-v21 |  | - | author's own volume |
| nvidia-devops-zth-v22 |  | - | author's own volume |
| nvidia-devops-zth-v23 |  | - | author's own volume |
| nvidia-devops-zth-v24 |  | - | author's own volume |
| nvidia-devops-zth-v25 |  | - | author's own volume |
| nvidia-devops-zth-v26 |  | - | author's own volume |
| parallel-and-high-performance-computing | Parallel and High Performance Computing | 9781617296468 | O'Reilly book |
| practical-mlops | Practical MLOps | 9781098103002 | O'Reilly book |
| production-kubernetes | Production Kubernetes | 9781492092292 | O'Reilly book |
| redfish-resource-guide |  | - | vendor PDF |
| redfish-schema |  | - | vendor PDF |
| redfish-spec |  | - | vendor PDF |
| scalable-kubernetes-infrastructure-for-ai-platforms | Scalable Kubernetes Infrastructure for AI Platforms | 9798341608191 | O'Reilly book |
| supercomputers-for-linux-sysadmins-managing-modern-hpc-clusters-and-supercomputers-from-software-to | Supercomputers for Linux SysAdmins: Managing Modern HPC Clusters and Supercomputers from Software to Hardware | 9798868816000 | O'Reilly book |
| superpod-b200-dc |  | - | vendor PDF |
| superpod-gb300-ra |  | - | vendor PDF |
| systems-performance-2nd-edition | Systems Performance, 2nd Edition | 9780136821694 | O'Reilly book |
| terraform-up-and-running-3rd-edition | Terraform: Up and Running, 3rd Edition | 9781098116736 | O'Reilly book |
