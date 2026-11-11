# AWS Migration Hub

**AWS Migration Hub** is a single place to **discover, plan, and track** application migrations to AWS across multiple AWS and partner tools. It does not move anything itself: it gives one **dashboard** for the tools that do.

## What It Does

| Capability | Meaning |
|---|---|
| **Discover** | Inventory of on-prem servers, applications and dependencies |
| **Assess / plan** | Group servers into **applications**, get migration and cost recommendations |
| **Track** | Follow the status of each migration (per server and per application) from different tools in one view |
| **Orchestrate** | Workflows and templates to coordinate migration steps (Migration Hub Orchestrator) |
| **Refactor** | Incrementally modernize monoliths to microservices (Migration Hub Refactor Spaces) |

> Migration Hub itself is **free**; you pay only for the underlying tools and AWS resources.
> The **home Region** stores the migration data. Choose it before you start.

## Discovery Tools

| Tool | How it works | Use |
|---|---|---|
| **Application Discovery Service (ADS)** | Collects server **configuration, performance, running processes and network dependencies** | Plan which servers belong together |
| **Agentless discovery** (Discovery Connector) | OVA appliance in **VMware vCenter**; VM inventory, CPU/RAM/disk usage | Quick, no agent per VM |
| **Agent-based discovery** (Discovery Agent) | Agent installed on each server (Windows/Linux, physical or virtual) | Adds **processes and network connections** (dependency mapping) |
| **Migration Evaluator** (formerly TSO Logic) | Analyses usage and builds a **business case / cost projection** | "How much will it cost on AWS?" |

Discovery data can be explored in Migration Hub and exported to **Athena** for analysis.

## Migration Tools It Tracks

| Tool | Migrates |
|---|---|
| **Application Migration Service (MGN)** | Servers, **lift-and-shift** (rehost) with continuous block replication; replaces Server Migration Service |
| **Database Migration Service (DMS)** | Databases (homogeneous and heterogeneous, with **SCT** for schema conversion) |
| **Server Migration Service (SMS)** | Legacy VM migration (superseded by MGN) |
| **Partner tools** | e.g. CloudEndure, ATADATA, RiverMeadow |

## Other Components

- **Migration Hub Orchestrator**: automates and sequences migration tasks with prebuilt workflow templates (e.g. SAP, rehost with MGN).
- **Migration Hub Strategy Recommendations**: analyses apps and recommends a migration strategy (and target) for each.
- **Migration Hub Refactor Spaces**: environment to refactor apps incrementally using the **strangler fig** pattern (routes traffic between old and new services).

## The 7 Rs of Migration

| Strategy | Meaning |
|---|---|
| **Retire** | Turn it off, no longer needed |
| **Retain** | Keep on-prem for now |
| **Relocate** | Move to AWS without changes (e.g. VMware Cloud on AWS) |
| **Rehost** | **Lift and shift** (MGN). Fast, no code changes |
| **Replatform** | "Lift, tinker and shift" (e.g. self-managed DB → **RDS**) |
| **Repurchase** | Switch to SaaS ("drop and shop") |
| **Refactor / re-architect** | Redesign for cloud-native (serverless, microservices). Most effort, most benefit |

## Typical Flow

```
Discover (ADS agents / connector)  →  Group into applications
        →  Assess (Migration Evaluator, Strategy Recommendations)
        →  Migrate (MGN / DMS / partner tools)
        →  Track everything in Migration Hub
```

## Exam Tips

- "**Single dashboard** to track a migration across multiple tools" → **Migration Hub**.
- "**Discover on-prem servers and dependencies** before migrating" → **Application Discovery Service**. Need **network dependency mapping** → **agent-based** (agentless is VMware only and doesn't see processes/connections).
- "**Lift and shift** servers with minimal downtime" → **Application Migration Service (MGN)**.
- "**Migrate a database**" → **DMS** (+ **SCT** when engines differ).
- "**Estimate cost / business case** of moving to AWS" → **Migration Evaluator**.
- Migration Hub **doesn't migrate data**; it **tracks and organises**.
- Large offline data → [Snow Family](../SnowFamily/README.md); ongoing file sync → DataSync; SFTP → [Transfer Family](../TransferFamily/README.md).

Related: [Backup](../Backup/README.md), [Snow Family](../SnowFamily/README.md), [Transfer Family](../TransferFamily/README.md).
