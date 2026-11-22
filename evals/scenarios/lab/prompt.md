# Scenario: lab

We are a 12-person research lab, one team. We want a private chat assistant on our own network, which has no internet connection. Nobody else shares the system. We have no audit or compliance rules, and people may see each other's conversations. If it is down for a day, nobody is hurt.

One of us looks after the machine part-time. We do not run Kubernetes. Hardware: one workstation with a single 24 GB GPU. We plan to run an 8-billion-parameter chat model in 8-bit precision; we do not know its architecture numbers.

There is no existing identity provider, API gateway, cluster or registry. Files reach the network on removable media.

The user is not available for follow-up questions. Treat anything not stated here as "unknown".
