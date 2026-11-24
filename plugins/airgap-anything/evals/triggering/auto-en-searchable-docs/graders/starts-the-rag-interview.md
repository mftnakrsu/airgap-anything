---
type: llm
weight: 1
---

The agent starts the interview of the skill instead of answering from memory. Its reply does one of two things for the RAG-specific questions: it asks at least one of them (which platform to use, what the document sources are, which document types and how many are scanned, which languages the documents are in, who may see which documents), or it states the defaults it takes for them and continues. Asking the platform question and waiting for the answer is a pass. Asking only who uses the system or which model does not count. It does not write configuration files before it has asked these questions or stated those defaults, and it does not suggest sending internal documents to a cloud service to convert or index them. A reply in the same language as the request is expected.
