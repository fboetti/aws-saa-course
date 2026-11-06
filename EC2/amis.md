# Amazon Machine Images (AMIs)

An **AMI** is a template used to launch instances: OS, pre-installed software, launch permissions and block device mappings.

## Components

- **Root volume template**: EBS snapshot or an instance-store template (in S3).
- **Launch permissions**: who can use the AMI (public, specific accounts, private).
- **Block device mapping**: which volumes attach at launch.

## Sources

- **AWS-provided** (Amazon Linux 2023, Ubuntu, Windows…)
- **AWS Marketplace** (vendor software, may add hourly fees)
- **Community AMIs**
- **Your own** custom AMIs ("golden images")

## Key Properties

- **Regional**: an AMI exists in one region. To use elsewhere → **copy** it (creates a new AMI ID in the target region).
- Copying an AMI copies its **snapshots**; you can **re-encrypt** with a different KMS key during copy.
- **Architecture-specific**: x86_64 vs arm64.
- **Virtualisation**: HVM (current); PV is legacy.
- **Root device type**:
  - **EBS-backed**: can stop/start, persists, fast boot (typical).
  - **Instance-store backed**: no stop (only reboot/terminate), data lost on termination.

## Creating an AMI

1. Configure an instance.
2. (Optional) stop it for a consistent image, or use "no reboot".
3. **Create image** → AWS snapshots attached EBS volumes and registers the AMI.

Automate with **EC2 Image Builder** (pipelines, tests, distribution across regions/accounts).

## Sharing

- Share with specific **account IDs** or make **public**.
- For an **encrypted** AMI: share the snapshot AND the **KMS key** (customer-managed key; AWS-managed keys cannot be shared).
- Cross-account sharing then **copy** to own it.

## Lifecycle

- **Deregister** an AMI; then delete its snapshots separately (snapshots keep costing).
- **Recycle Bin** can protect against accidental deregistration.
- **Data Lifecycle Manager (DLM)** automates AMI/snapshot creation and retention.

## Exam Tips

- Faster launches/bootstrapping → **bake software into a custom AMI** instead of long user data scripts.
- Need the same environment in another region → **copy AMI**.
