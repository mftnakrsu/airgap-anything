---
type: llm
weight: 1
---

The agent starts the interview of the skill instead of answering from memory. Its reply does one of two things for the agent-specific questions: it asks at least one of them (which tools they want or whether to recommend one, whether a Claude route exists, which internal systems agents reach, how much an agent may do without asking, which operating systems developers use, whether settings are enforced centrally), or it states the defaults it takes for them and continues. Asking only who uses agents or which model does not count. It does not write configuration files before it has asked these questions or stated those defaults, and it does not recommend Claude Code against an open-weight model. A reply in the same language as the request is expected.
