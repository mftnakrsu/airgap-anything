# Scenario: department

Our engineering division has 180 people in four departments. Each department must have its own budget, and departments must not see each other's prompts or data. Every request has to be attributable to a person and kept for audit.

The platform is for chat only. We will serve one very large model: 671 billion parameters in 8-bit precision. We do not know its architecture numbers. Hardware: one server with eight GPUs, 141 GB and 700 W each.

Planned maintenance windows are fine; unplanned downtime should be rare. A team of three operates the system. They do not run Kubernetes today.

We have Active Directory. There is no API gateway, cluster or registry yet. Files reach the network on removable media.

The user is not available for follow-up questions. Treat anything not stated here as "unknown".
