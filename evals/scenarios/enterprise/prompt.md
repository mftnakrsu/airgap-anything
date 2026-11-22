# Scenario: enterprise

We are a 2,000-person company with twelve departments. Departments must not see each other's data, every request must be attributable and retained, and the service may not go down.

Usage: about 70% chat, 20% coding assistants and 10% question answering over documents. We will serve one 70-billion-parameter model in 8-bit precision. Its architecture: 80 layers, 8 key-value heads, head dimension 128, 16-bit KV cache. Typical context is 8,192 tokens.

Hardware: twenty-four GPUs with 141 GB and 700 W each. A platform team operates the system and runs OpenShift today. We already operate Kong as our API gateway and Active Directory as our directory.

Artifacts enter the network through a data diode, about once a month.

The user is not available for follow-up questions. Treat anything not stated here as "unknown".
