# Amazon Machine Images (AMIs)

An **AMI** is a template used to launch instances: OS, pre-installed software, launch permissions and block device mappings.
AMIs are REGION SPECIFIC!!

## Components

- **Root volume template**: EBS snapshot or an instance-store template (in S3).
- **Launch permissions**: who can use the AMI (public, specific accounts, private).
- **Block device mapping**: which volumes attach at launch.

## Sources

- **AWS-provided** (Amazon Linux 2023, Ubuntu, Windows…)
- **AWS Marketplace** (vendor software, may add hourly fees)
- **Community AMIs**
- **Your own** custom AMIs ("golden images")

## Amazon Linux

- AWS's own Linux distribution, **free**, optimised for EC2 and supported by AWS. Default user `ec2-user`. Comes with the AWS CLI, SSM Agent, cloud-init and EC2 Instance Connect preinstalled.
- **Amazon Linux 2023 (AL2023)**: current version. Fedora-based, uses `dnf`, `systemd`, SELinux enabled (permissive by default), IMDSv2 by default, and a fixed release cadence with long-term support.
- **Amazon Linux 2 (AL2)**: older, CentOS/RHEL 7-like, uses `yum`. Reaches end of support in **2026**, so migrate to AL2023.
- Runs on x86_64 and arm64 (Graviton). Also runs on-premises or in VMs (images for VMware, KVM, Hyper-V, VirtualBox) for dev and test.

## EPEL

- **Extra Packages for Enterprise Linux**: a Fedora-project repository of additional packages (for example `htop`, `nginx` on some versions, `certbot`) for **RHEL and its clones** (CentOS Stream, Rocky, AlmaLinux).
- **Not for Amazon Linux 2023**: AL2023 is not RHEL-compatible and does not support EPEL. Packages come from AWS's own repositories instead.
- On **Amazon Linux 2** it was available through `amazon-linux-extras` (for example `sudo amazon-linux-extras install epel`).
- On RHEL-family instances: `sudo dnf install epel-release`.
- Exam relevance is low. Just remember it is a **third-party repo for RHEL-like distros**, not AWS-managed.

## Key Properties

- **Regional**: an AMI exists in one region. To use elsewhere → **copy** it (creates a new AMI ID in the target region).
- Copying an AMI copies its **snapshots**; you can **re-encrypt** with a different KMS key during copy.
- **Architecture-specific**: x86_64 vs arm64.
- **Virtualisation**: HVM (current); PV is legacy.
- **ENA support**: the AMI must have the **Elastic Network Adapter (ENA)** driver and the `enaSupport` attribute set, or instance types that require ENA (all current Nitro types) won't launch from it. Current AWS-provided AMIs include it. For a custom or imported AMI, install the driver and set it with `aws ec2 modify-image-attribute --ena-support` (or `register-image --ena-support`). See [Networking](networking.md#enhanced-networking) for ENA speeds and EFA.
- **Root device type**:
  - **EBS-backed**: can stop/start, persists, fast boot (typical).
  - **Instance-store backed**: no stop (only reboot/terminate), data lost on termination.

## Boot Modes

How the instance firmware starts the OS. It is a property of the **AMI** (`BootMode`) and must be supported by the **instance type**.

| Mode | What it is | Notes |
|---|---|---|
| **Legacy BIOS** | Traditional BIOS boot | x86 only. Works on all older types. No Secure Boot or TPM |
| **UEFI** | Modern firmware: faster boot, GPT partitions, larger boot volumes, Secure Boot capable | Required for **Graviton (arm64)**. Needed for Secure Boot and NitroTPM |
| **uefi-preferred** | AMI default on supported types | Uses UEFI if the instance type supports it, else legacy BIOS. Default for most AWS-provided x86 AMIs |

- The AMI's boot mode must match what the instance type supports. Graviton instances run **UEFI only**, so a legacy BIOS AMI cannot launch on them. Some types (for example a few older ones) support only legacy BIOS.
- Check an AMI's mode with `aws ec2 describe-images` (`BootMode` field). A launched instance shows the mode it actually used.
- The boot mode **cannot be changed on a running instance**. To change it, register a new AMI from a snapshot with `--boot-mode`.

### Secure Boot and NitroTPM

- **UEFI Secure Boot**: the firmware only runs **signed** bootloaders and kernels, protecting against bootkits and rootkits. Needs a UEFI AMI with Secure Boot enabled and a key database (a UEFI variable store, `--uefi-data`) in the AMI.
- **NitroTPM**: a virtual **TPM 2.0** for Nitro-based instances. Enable with `--tpm-support v2.0` on the AMI. Use it for **measured boot**, storing keys or certificates sealed to the instance state, and disk encryption (for example BitLocker on Windows).
- NitroTPM requires **UEFI** and a supported Nitro instance type. It cannot be enabled after the instance is launched.
- Typical use: compliance workloads that need boot integrity attestation.

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
- Graviton (arm64) instance won't launch from your AMI → boot mode must be **UEFI**.
- "Protect against bootkits/rootkits" → **UEFI Secure Boot**. "Hardware-backed keys or measured boot" → **NitroTPM**.
