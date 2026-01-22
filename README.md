### 1. Research Objective

The project focuses on the automatic detection and simplification of figurative language (specifically idioms and metaphors) into **Easy-to-Read (E2R)** English to improve accessibility for people with cognitive disabilities or low language proficiency.

### 2. Scope & Datasets

The research will target two primary types of figurative language using established English datasets:

- **Conceptual Metaphors:** Utilizing the **VU Metaphor Corpus**, **TroFi/MOH-X**, and **MetaNet**.
- **Idioms:** Utilizing **SemEval 2022 Task 2**, **MAGPIE**, and **ID10** (which includes human-created explanations).

### 3. Proposed Methodology
The workflow follows these stages:

1. **Detection:** Evaluate the presence of figurative language (Yes/No).
2. **Context Extraction:** Strip text to the context relevant to the identified expression.
3. **Simplification:** Replace/rewrite the idiom or metaphor following E2R guidelines.
4. **Validation (Guardrails):** Evaluate semantic equality between the original and altered text to ensure meaning is preserved.

### 4. Technical Stack

- **Models:** Open-weight LLMs (e.g., **Mistral-7B**, **Qwen-2.5-7B**, **Gemma-2-9B**).
- **Orchestration:** **LangGraph** for the multi-node workflow.
- **Infrastructure:** **UPM Compute Cluster** (access granted via the signed form) supplemented by **OpenRouter**.
- **Observability:** **LangSmith** or **Weights & Biases** for tracing metrics and workflow results.
- **Output:** An **Open Source Web Application** to showcase results and facilitate evaluation.