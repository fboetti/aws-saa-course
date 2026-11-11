# EC2 Storage

Summary page. For deeper EBS and EFS notes see [EBS and EFS in Depth](ebs-efs.md).

## Options at a Glance

| Storage | Type | Persistence | Scope | Use |
|---|---|---|---|---|
| **EBS** | Network block | Persists independently of instance | One AZ | Boot/data volumes, DBs |
| **Instance Store** | Local block (physically attached) | **Lost on stop/terminate/hardware failure** | Instance | Cache, buffers, scratch, temp data |
| **EFS** | Network file (NFS) | Persistent | Regional (multi-AZ) | Shared Linux file system |
| **FSx** | Managed file systems | Persistent | AZ / multi-AZ | Windows (SMB), Lustre HPC, NetApp, OpenZFS |
| **S3** | Object | Persistent | Regional | Not mountable block; via API |

## EBS (Elastic Block Store)

- Network drive attached to **one instance at a time** (except **io1/io2 Multi-Attach**, same AZ, up to 16 Nitro instances).
- **Locked to an AZ**; to move, snapshot → restore in another AZ/region.
- Provisioned capacity (GiB) and optionally IOPS; billed on provisioned size.
- Can be detached and attached to another instance; can be resized/changed type **online** (Elastic Volumes).

### Volume Types

| Type | Class | Size | Max IOPS | Use |
|---|---|---|---|---|
| **gp3** | SSD general purpose | 1 GiB–16 TiB | 16,000 (baseline 3,000, throughput 125 MB/s independent) | Default; boot, dev/test |
| **gp2** | SSD general purpose | 1 GiB–16 TiB | 16,000 (3 IOPS/GiB, bursts to 3,000) | Legacy |
| **io2 / io2 Block Express** | Provisioned IOPS SSD | up to 64 TiB | 64,000 / 256,000 | Critical DBs, sub-ms latency |
| **io1** | Provisioned IOPS SSD | up to 16 TiB | 64,000 | I/O intensive DBs |
| **st1** | Throughput-optimised HDD | 125 GiB–16 TiB | 500 | Big data, logs, streaming (cannot be boot) |
| **sc1** | Cold HDD | 125 GiB–16 TiB | 250 | Infrequently accessed (cannot be boot) |

Only **gp2/gp3/io1/io2** can be boot volumes.

### Snapshots

- Incremental, stored in **S3** (managed by AWS), regional.
- Can copy across regions/accounts; restore creates a new volume (any AZ in that region).
- **Fast Snapshot Restore (FSR)** removes first-access latency.
- **Snapshot Archive**: ~75% cheaper, 24–72 h restore.
- **Recycle Bin** for deleted snapshots.
- Automate with **Data Lifecycle Manager**.

### Encryption

- AES-256 via **KMS**; encrypts data at rest, in transit between instance and volume, snapshots and volumes created from them.
- Minimal latency impact. Enable **encryption by default** per region.
- Encrypt an unencrypted volume: snapshot → copy with encryption → restore.

### Delete on Termination

- Root volume: **deleted** by default. Additional volumes: **kept** by default.

## Instance Store

- High-performance local NVMe SSD (millions of IOPS) on `d`/I/G families.
- Good for cache/buffer/temp. **Not** for long-term data. Back up/replicate yourself.

## EFS

- Managed **NFSv4** file system, mountable by thousands of instances across AZs, Linux only.
- Scales automatically; pay per GB used.
- Performance modes: General Purpose, Max I/O. Throughput: Bursting, Provisioned, Elastic.
- Storage classes: Standard, IA, Archive, One Zone (+ lifecycle policies).
- Security: security group on mount targets, KMS encryption, IAM, POSIX permissions.

## Exam Tips

- "Max IOPS on a single instance" → instance store; "durable high IOPS" → io2.
- "Shared storage across AZs for Linux" → EFS; "Windows shared" → FSx for Windows.
- "Cheap, throughput, big sequential" → st1.
- "Move EBS volume to another AZ" → snapshot and restore.
