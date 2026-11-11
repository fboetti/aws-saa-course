# EBS and EFS in Depth

Deeper notes on **Amazon EBS** (block storage) and **Amazon EFS** (shared file storage). Follows the EBS/EFS part of the [freeCodeCamp AWS SAA course](https://www.youtube.com/watch?v=c3Cn4xYfxJY&t=81005s) (starts around **22:30:05**). For the one-page comparison see [Storage](storage.md).

## EBS vs EFS at a Glance

| | **EBS** | **EFS** |
|---|---|---|
| Type | Block storage (a "virtual hard disk") | File storage (NFS) |
| Attached to | **One instance** at a time (Multi-Attach exception) | **Thousands** of instances/containers/Lambdas at once |
| Scope | **One AZ** | **Regional** (multi-AZ) or One Zone |
| OS | Linux and Windows | **Linux only** (POSIX) |
| Capacity | Provisioned (pay for what you provision) | Elastic, grows/shrinks automatically (pay for what you use) |
| Typical use | Boot volume, databases, single-instance data | Shared content, CMS/web farm, home directories, big data, containers |

## EBS (Elastic Block Store)

### Core Behaviour

- A **network drive** (not physically attached), so latency is a bit higher than instance store, but data **outlives the instance**.
- Created in **one AZ** and can only be attached to an instance in the **same AZ**.
- Detach from one instance, attach to another (same AZ) while keeping the data.
- An instance can have **many** EBS volumes; a volume is normally attached to **one** instance.
- **Provisioned**: you choose size (GiB) and, for some types, IOPS/throughput. You pay for it even if unused.
- **Elastic Volumes**: change size, type, IOPS and throughput **while attached**, no downtime. You can only **increase** size (never shrink), and wait ~6 h between modifications of the same volume. After growing, extend the partition and file system in the OS.
- Replicated automatically **within the AZ** for durability (it is not multi-AZ: use snapshots for that).

### Volume Types

| Group | Types | Notes |
|---|---|---|
| **General purpose SSD** | `gp3`, `gp2` | `gp3`: 3,000 IOPS and 125 MB/s baseline included, IOPS (up to 16,000) and throughput (up to 1,000 MB/s) set **independently of size**, ~20% cheaper than gp2. `gp2`: IOPS tied to size (3 IOPS/GiB), burst credits for small volumes |
| **Provisioned IOPS SSD** | `io1`, `io2`, `io2 Block Express` | Consistent high IOPS, sub-millisecond latency. `io2` has 99.999% durability (vs 99.8-99.9%) and better IOPS:GiB ratio (500:1). Block Express up to 256,000 IOPS / 64 TiB |
| **Throughput HDD** | `st1` | Low-cost, big sequential workloads: big data, data warehouse, logs |
| **Cold HDD** | `sc1` | Cheapest, infrequent access |

Rules to remember:

- **Only SSD types (gp2, gp3, io1, io2) can be boot volumes.** st1 and sc1 cannot.
- Need **more than 16,000 IOPS** on one volume → `io1`/`io2`. Need more than 80,000 IOPS on one instance → **instance store** (or RAID of volumes).
- Sustained, database-style, latency-sensitive → provisioned IOPS; everything else default to **gp3**.
- Provisioned IOPS volumes support **Multi-Attach** (see below).

### Multi-Attach (io1/io2)

- Attach the **same volume** to up to **16 Nitro instances** in the **same AZ**.
- Every instance gets full read/write.
- Meant for clustered apps (for example Teradata) and higher availability; the application must manage concurrent writes, so use a **cluster-aware file system**, not XFS/ext4.

### Snapshots

- **Point-in-time backup** of a volume, stored in **S3** (managed by AWS, not visible in your buckets).
- **Incremental**: the first one is a full copy, later ones store only changed blocks. Deleting an old snapshot never breaks newer ones; AWS keeps the blocks still needed.
- Do not need to detach the volume, but for consistency **pause writes / flush** (or stop the instance) for the root volume.
- **Regional**, but can be **copied** to another region or shared with other accounts. This is also how you **move a volume to another AZ or region**: snapshot → (copy) → create volume.
- A volume created from a snapshot is **lazily loaded**: blocks are fetched from S3 on first access, so first reads are slow. Fix by **initialising** (reading all blocks) or enabling **Fast Snapshot Restore (FSR)** (extra cost per AZ/hour).
- **Snapshot Archive**: up to ~75% cheaper, restore takes 24-72 hours. Good for snapshots kept for months.
- **Recycle Bin**: retention rules so accidentally deleted snapshots (and AMIs) can be recovered within 1 day to 1 year.
- **Amazon Data Lifecycle Manager (DLM)**: scheduled, automated creation, retention and deletion of snapshots/AMIs. AWS Backup can also manage them.
- **EBS direct APIs** read snapshot blocks and write incremental snapshots without creating a volume.

### Encryption

- Uses **AES-256** with **KMS keys** (aws/ebs managed key or a customer-managed key).
- When enabled you get: data **at rest** encrypted, data **in transit** between instance and volume, **snapshots** encrypted, and volumes created from those snapshots encrypted.
- Handled transparently by EC2/EBS with **minimal latency impact**.
- Account setting **"Encryption by default"** is **per region**.
- Encrypt an existing unencrypted volume: **snapshot → copy snapshot with encryption → create volume from the copy**.
- Snapshot of an encrypted volume is encrypted. A snapshot of an unencrypted volume can be shared publicly; an encrypted one cannot (share the KMS key and snapshot with a specific account instead).

### Delete on Termination

- Root volume: **deleted** by default. Extra volumes attached at launch: **kept** by default.
- Controlled by the `DeleteOnTermination` attribute; change it to keep the root volume for forensics or recovery.

### EBS-Optimized Instances

- Dedicated bandwidth between the instance and EBS so storage traffic does not compete with network traffic.
- Default (free) on current-generation types; each instance type has its own max EBS throughput/IOPS, which can be lower than what the volume supports. Check the **instance** limit too.

### RAID with EBS (not managed by AWS)

- **RAID 0** (stripe): more IOPS/throughput, no redundancy.
- **RAID 1** (mirror): redundancy across two volumes.
- RAID 5/6 is not recommended on EBS.

## EFS (Elastic File System)

### Core Behaviour

- Fully managed **NFSv4.0/4.1** file system, **POSIX-compliant**, for **Linux** (Windows → FSx for Windows File Server).
- **Shared**: mounted concurrently by many EC2 instances across **multiple AZs**, plus ECS/EKS containers, Lambda and on-premises servers (via Direct Connect or VPN).
- **Elastic**: grows and shrinks automatically up to petabytes, no capacity planning. Pay per GB stored per month (more expensive than EBS per GB, roughly 3x gp2).
- Highly available and durable: data stored across **multiple AZs** (Standard) with 99.999999999% (11 nines) durability.
- Works through **mount targets**: one ENI per AZ in your VPC subnets. Mount with the `amazon-efs-utils` helper (`mount -t efs fs-1234:/ /mnt/efs`) or plain NFS.
- Regional service but **VPC-scoped** for access (mount targets live in subnets).

### Storage Classes

| Class | Use | Notes |
|---|---|---|
| **Standard** | Frequently accessed | Multi-AZ |
| **Standard-IA** | Infrequently accessed | Lower storage price, per-GB retrieval fee, multi-AZ |
| **Archive** | Rarely accessed (few times a year) | Cheapest multi-AZ |
| **One Zone** | Frequently accessed, single AZ | ~47% cheaper, no AZ-level resilience (dev/test, recreatable data) |
| **One Zone-IA** | Infrequently accessed, single AZ | Cheapest of the non-archive classes |

- **Lifecycle management** policies move files automatically after N days without access (for example Standard → IA → Archive) and can move them back on access (Intelligent-Tiering behaviour).

### Performance Modes (chosen at creation, cannot be changed)

- **General Purpose** (default): lowest latency, web servers, CMS, home directories.
- **Max I/O**: higher aggregate throughput and parallelism (thousands of clients), higher latency; for big data and media processing. Not available for One Zone or Elastic throughput.

### Throughput Modes (can be changed)

| Mode | Behaviour |
|---|---|
| **Elastic** (recommended) | Scales up and down automatically with the workload, pay for what you use. Best for spiky/unpredictable |
| **Provisioned** | Set throughput independent of storage size, pay for it |
| **Bursting** | Throughput scales with storage size (50 MiB/s per TiB baseline, burst credits). Legacy default |

### Security

- **Network**: security group on the **mount targets** must allow **NFS (TCP 2049)** from the clients.
- **Identity**: **IAM** authorisation for clients (via the EFS mount helper) and **EFS file system policies** (resource policy; can enforce encryption in transit and deny anonymous access).
- **File-level**: POSIX permissions (user/group IDs) and **EFS Access Points** (enforce a root directory and POSIX identity per application).
- **Encryption at rest** with KMS (enable at creation, **cannot be added later**), **encryption in transit** with TLS (mount option `-o tls`).

### Backup and Replication

- **AWS Backup** automatic daily backups (enabled by default for new file systems from the console).
- **EFS Replication**: replicate to another region or AZ-set, asynchronous (RPO of minutes).
- **AWS DataSync** to copy data between EFS and other storage, including on-premises NFS.

## FSx (Brief)

**Amazon FSx** is a family of fully managed, third-party-style file systems for workloads EFS does not fit.

| Flavor | Protocol / OS | Use |
|---|---|---|
| **FSx for Windows File Server** | **SMB**, NTFS, Windows + Linux clients, **Active Directory** integration, DFS | Windows shares, home directories, SQL Server, Windows apps |
| **FSx for Lustre** | POSIX, parallel file system | **HPC**, ML training, video processing; millions of IOPS, sub-ms latency; links to **S3** (lazy-load data, write results back) |
| **FSx for NetApp ONTAP** | NFS, SMB, iSCSI | Migrate on-premises NetApp, multi-protocol, snapshots, cloning, compression/dedup |
| **FSx for OpenZFS** | NFS | Migrate ZFS workloads, low latency, snapshots, cloning |

- Deployment: **Multi-AZ** (HA, synchronous standby) or **Single-AZ**. Accessible from on-premises via Direct Connect or VPN.
- Windows: supports **Shadow Copies**, user quotas, encryption (KMS), and backups to S3.
- Lustre: **Scratch** (temporary, fastest, no replication) vs **Persistent** (long-term, replicated within the AZ).
- Exam: "Windows / SMB / Active Directory" → **FSx for Windows**; "HPC / fast parallel processing with S3" → **FSx for Lustre**; "NetApp/ZFS migration" → **ONTAP/OpenZFS**; "Linux NFS shared, simple" → **EFS**.

## Amazon File Cache (Brief)

**Amazon File Cache** is a fully managed, high-speed **cache for data stored elsewhere**, built on Lustre.

- Links to **on-premises NFS file systems** and/or **S3 buckets**, presenting them as one fast POSIX file system with a unified namespace.
- Data is **lazy-loaded** on first access and cached; writes can be exported back to the origin. It is a cache, not the system of record.
- Sub-millisecond latency, up to hundreds of GB/s throughput; Lustre-based, accessed from EC2, ECS/EKS and on-premises via Direct Connect or VPN.
- Use cases: **cloud bursting** of HPC, media rendering, ML, and EDA workloads that need data held on-premises or in S3 without migrating it first.
- Exam: "burst on-premises NFS data into AWS for fast processing without copying it" → **File Cache**; "high-performance file system you own, optionally linked to S3" → **FSx for Lustre**.

## Choosing Between Them

| Requirement | Pick |
|---|---|
| Boot volume, single-instance database | **EBS** |
| Lowest latency, highest IOPS for one instance | **EBS io2** (or instance store for temporary data) |
| Same data readable/writable from many instances in multiple AZs | **EFS** |
| Unknown or fast-growing capacity, no provisioning | **EFS** |
| Windows file shares (SMB, Active Directory) | **FSx for Windows** |
| HPC / parallel file system | **FSx for Lustre** |
| Cheapest durable object storage with API access | **S3** |
| Share a block volume between a few clustered instances | **EBS Multi-Attach** (io1/io2, same AZ) |

## Exam Tips

- EBS is **AZ-locked**; to use it in another AZ or region → **snapshot, then restore (or copy then restore)**.
- Encrypt an existing unencrypted EBS volume → **snapshot → encrypted copy → new volume**.
- Root EBS volume is **deleted on termination** by default; additional volumes are not.
- Boot volume must be SSD (**gp2/gp3/io1/io2**); **st1/sc1 cannot boot**.
- "Sub-millisecond latency, critical database, > 16,000 IOPS" → **io2 / io2 Block Express**.
- "Big sequential throughput, logs, data warehouse, low cost" → **st1**; "cheapest, rarely accessed" → **sc1**.
- Slow first read of a restored volume → **Fast Snapshot Restore**.
- Recover accidentally deleted snapshots → **Recycle Bin**; automate snapshots → **Data Lifecycle Manager**.
- "Shared file system, Linux, multiple AZs" → **EFS** (security group must allow **TCP 2049**).
- "Cut EFS cost for files that are rarely used" → **lifecycle policy to IA/Archive**; "dev/test or recreatable data" → **One Zone**.
- EFS performance mode **cannot be changed** after creation; throughput mode can.
- Encryption at rest on EFS must be chosen **at creation**.
