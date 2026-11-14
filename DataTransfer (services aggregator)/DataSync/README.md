# AWS DataSync

**AWS DataSync** is a managed **online data transfer** service that moves large amounts of data between on-premises storage and AWS, or between AWS storage services. It automates and accelerates copying (up to ~10x faster than open-source tools), handling scheduling, retries, encryption, and integrity checks for you.

## Supported Locations

| Source / Destination | Examples |
|---|---|
| **On-premises / other clouds** (needs an agent) | NFS, SMB, HDFS, object storage (S3-compatible), Google Cloud Storage, Azure Files/Blob |
| **AWS storage** (no agent needed) | **S3** (all storage classes), **EFS**, **FSx** (Windows File Server, Lustre, NetApp ONTAP, OpenZFS) |

- Transfers can go **on-prem → AWS**, **AWS → on-prem**, or **AWS → AWS** (e.g. EFS in one Region to EFS in another, S3 to FSx).
- You can pick the **S3 storage class** directly at the destination (e.g. Glacier Deep Archive).

## How It Works

```
On-prem NFS/SMB ──► DataSync Agent (VM or EC2) ──► DataSync service ──► S3 / EFS / FSx
                      (TLS, over Internet / Direct Connect / VPN)
```

1. **Agent**: a VM (VMware, KVM, Hyper-V) or EC2 instance installed near the source storage. It reads the source and sends data to the service. Not needed for AWS-to-AWS transfers.
2. **Location**: defines a source or destination (and its credentials/role).
3. **Task**: links a source and destination location, with options (filters, bandwidth limit, verification, schedule).
4. **Task execution**: a single run of the task.

## Connectivity Options

| Path | Notes |
|---|---|
| **Public internet** (TLS) | Simplest |
| **VPC endpoint (PrivateLink)** | Traffic stays on the AWS network, no public internet |
| **Direct Connect** (private/public VIF) | Dedicated, consistent bandwidth for large transfers |
| **Site-to-Site VPN** | Encrypted over the internet |

## Key Features

- **Scheduled** (hourly, daily, weekly) or on-demand runs.
- **Incremental**: after the first full copy, transfers **only changed data**.
- **Preserves metadata**: permissions, timestamps, ownership (POSIX, NTFS ACLs).
- **Data integrity verification** during and after transfer (checksums).
- **Encryption in transit** (TLS) and at rest (via the destination service).
- **Bandwidth throttling** so it does not saturate the corporate link.
- **Filters** (include/exclude patterns) to copy only part of a dataset.
- **Monitoring** via CloudWatch metrics/logs, EventBridge, and CloudTrail.
- Pricing: **pay per GB transferred** (no upfront cost or minimum fee).

## DataSync vs Other Services

| Need | Use |
|---|---|
| **Online**, scheduled bulk copy on-prem ↔ AWS (NFS/SMB/HDFS) | **DataSync** |
| Migrate **huge data offline** (limited bandwidth, PB scale) | [Snow Family](../SnowFamily/README.md) |
| Partners must upload using **SFTP/FTPS/FTP** | [Transfer Family](../TransferFamily/README.md) |
| On-prem apps need **ongoing low-latency access** to cloud-backed files | **Storage Gateway** |
| Replicate data between S3 buckets continuously | **S3 Replication** (not DataSync) |
| Track migration of servers/apps | [Migration Hub](../../MigrationHub/README.md) |

> **Snowcone** can also run a DataSync agent, so you can ship data offline **or** send it online with DataSync.
> DataSync **moves data**; Storage Gateway **extends your storage** into AWS. DataSync is a **transfer** tool, not a sync-forever mount.

## Exam Tips

- "Move **large amounts of data** from on-prem **NFS/SMB** to **S3/EFS/FSx**, **scheduled**, **encrypted**, with **metadata preserved**" → **AWS DataSync**.
- Requires an **agent** on-prem; **no agent** for AWS-to-AWS.
- Can transfer **to/from** S3, EFS, and FSx, including **between Regions and accounts**.
- Only wins over Snow when **network bandwidth is sufficient**; if the network would take weeks or months → **Snow Family**.
- Use **Direct Connect** or a **VPC endpoint** for private, predictable transfers.
- It is a **one-way task** (source → destination), not bi-directional sync.
- Preserves **file permissions and metadata**, which plain `aws s3 sync` does not fully do for NFS/SMB sources.

Related: [S3](../../S3/README.md), [EBS and EFS in Depth](../../EC2/ebs-efs.md), [Snow Family](../SnowFamily/README.md), [Transfer Family](../TransferFamily/README.md), [Migration Hub](../../MigrationHub/README.md).
