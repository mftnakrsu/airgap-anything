---
type: llm
weight: 1
---

The agent starts the interview of the skill instead of answering from memory. The request names no platform for the document search, so the reply must ask which platform to use, with three options: Open WebUI knowledge bases, a RAG server such as RAGFlow, or something else of the user's own. It may recommend one and may ask the other open questions (document sources, document types and how many are scanned, languages, who may see which documents) in the same message, but it waits for the user's answer. A reply that states the defaults and continues without asking the platform question fails, and so does one that picks the platform for the user or offers fewer than the three options. It does not write configuration files before the user has answered, and it does not suggest sending internal documents to a cloud service to convert or index them. A reply in the same language as the request is expected.
