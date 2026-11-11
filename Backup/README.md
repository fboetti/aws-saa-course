# AWS Backup

**AWS Backup** is a fully managed, **centralized** service to automate and monitor backups across many AWS services (and on-premises via Storage Gateway / VMware), from one place. Instead of scripting snapshots per service, you define **policies** once and apply them to resources.

## Supported Services (main ones)

| Category | Services |
|---|---|
| Compute / block | EC2 (AMIs + EBS), EBS |
| File | EFS, FSx (Windows, Lustre, NetApp ONTAP, OpenZFS) |
| Object | S3 (continuous + periodic) |
| Databases | RDS, Aurora, DynamoDB, DocumentDB, Neptune, Redshift, Timestream |
| Hybrid | Storage Gateway (volume gateway), VMware workloads |
| Other | CloudFormation stacks, SAP HANA on EC2 |

## Core Concepts

| Concept | Meaning |
|---|---|
| **Backup plan** | The policy: **schedule** (cron / frequency), **backup window**, **lifecycle** (move to cold storage, expire), target **vault**, copy rules |
| **Resource assignment** | Which resources the plan protects: by **resource ID** or by **tags** (e.g. `backup=daily`) |
| **Backup vault** | Container that stores recovery points. Encrypted with a **KMS key**. Has its own access policy |
| **Recovery point** | A single backup of a resource (snapshot, etc.) |
| **Restore** | Creates a **new** resource from a recovery point (does not overwrite the original) |

## Key Features

- **Scheduled backups** and **on-demand** backups.
- **Lifecycle**: transition to **cold storage** after N days (min 90 days retention in cold) then delete. Supported for a subset of services (e.g. EFS, DynamoDB, EC2/VSS...). Cheaper for long retention.
- **Point-in-Time Recovery (PITR)**: continuous backups for **RDS, Aurora, S3, SAP HANA** (restore to any second within the retention, up to 35 days).
- **Cross-Region backup**: copy recovery points to another Region (**disaster recovery**).
- **Cross-account backup**: copy to a vault in another account, managed via **AWS Organizations** (central backup policies, protects against a compromised account).
- **Tag-based** assignment, so new tagged resources are protected automatically.
- **Encryption**: backups encrypted with KMS; cross-account/Region copies can use a different key.
- **Monitoring and audit**: CloudWatch, EventBridge, SNS notifications, CloudTrail, and **AWS Backup Audit Manager** (compliance reports against frameworks).

## Backup Vault Lock (WORM)

- Makes a vault **Write Once Read Many**: nobody (not even root) can delete recovery points or shorten retention before expiry.
- Protects against **ransomware, insider threat and accidental deletion**.
- Two modes:
  - **Governance mode**: privileged users with the right IAM permissions can remove the lock.
  - **Compliance mode**: after a **cooling-off period** (min 3 days) the lock becomes **immutable**; not even AWS can remove it. Meets regulations such as SEC 17a-4.
- Complementary: **Logically air-gapped vault** (isolated, can be shared for restore to another account).

## AWS Backup vs Service-Native Backup

| | **AWS Backup** | **Native** (EBS snapshots + DLM, RDS automated backups, S3 versioning) |
|---|---|---|
| Scope | Many services, one policy | One service at a time |
| Cross-account / Region | Built in, Organizations policies | Manual or scripted |
| Compliance / audit | Audit Manager, Vault Lock | Per service |
| Underlying mechanism | Uses the service's own snapshot/backup engine | Same |

## Exam Tips

- "**Centrally manage / automate backups across multiple services and accounts**" → **AWS Backup** (with Organizations backup policies).
- "**Backups must not be deletable / WORM / regulatory retention**" → **Backup Vault Lock** (compliance mode).
- "**Disaster recovery in another Region**" → **cross-Region copy** in the backup plan.
- "**Protect against compromised account**" → cross-account copy to a dedicated backup account.
- "**Restore to any second**" → continuous backup / PITR (RDS, Aurora, S3).
- Restores create a **new** resource; they never overwrite the source.
- Only EBS snapshots to schedule? Use **Data Lifecycle Manager (DLM)**; need multi-service or compliance? Use **AWS Backup**.
- Backup (RPO of hours/days) is the cheapest DR strategy: **Backup and Restore**. See [Resilience](../concepts/resilience/README.md).

Related: [EBS and EFS in Depth](../EC2/ebs-efs.md), [S3](../S3/README.md).
