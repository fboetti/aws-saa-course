# AWS Snow Family

The **Snow Family** is a set of **physical, rugged devices** AWS ships to you to **move data into/out of AWS offline** and/or **run compute at the edge** (remote sites with little or no connectivity).

## Why Use It?

Moving big data over the network is slow. Rule of thumb: if the transfer would take **more than ~1 week** over your link (or the link is unreliable/absent), use a Snow device.

| Data | 100 Mbps | 1 Gbps | 10 Gbps |
|---|---|---|---|
| 10 TB | ~12 days | ~30 hours | ~3 hours |
| 100 TB | ~124 days | ~12 days | ~30 hours |
| 1 PB | ~3.4 years | ~124 days | ~12 days |

## Devices

| Device | Storage | Compute | Notes |
|---|---|---|---|
| **Snowcone** | 8 TB HDD / 14 TB SSD | 2 vCPU, 4 GB RAM | Smallest (~2 kg), portable, battery or USB-C power. Can also send data online with **DataSync** |
| **Snowball Edge Storage Optimized** | ~80 TB usable (210 TB NVMe variant) | Up to 104 vCPU, 416 GB RAM | Large data migration, local storage. Cluster of 5-10 devices possible |
| **Snowball Edge Compute Optimized** | 28 TB NVMe (+ 42 TB HDD) | Up to 104 vCPU, 416 GB RAM, optional **GPU** | Edge compute: ML inference, video analysis, processing |
| **Snowmobile** | Up to **100 PB** per truck | n/a | 45-foot shipping container on a truck. For **exabyte** scale. *(Retired by AWS; still appears in older exam material)* |

> Snowball Edge devices are the main ones to know. Storage Optimized = bulk data; Compute Optimized = processing at the edge.

## How a Migration Works

1. **Request** a device in the console (job type: import into S3, export from S3, or local compute/storage).
2. AWS **ships** it to you (E Ink shipping label, no packaging needed).
3. **Connect** it to your network, **unlock** with the manifest + unlock code, and copy data using the **Snowball client / S3 adapter / NFS**.
4. **Ship it back** (label updates automatically).
5. AWS **imports data into S3** and **securely erases** the device (NIST standards).

Data goes to **S3** only (then use lifecycle rules to move to Glacier). You **cannot import directly into Glacier**.

## Edge Computing

- Run **EC2 instances** (special sbe AMIs) and **Lambda functions** (via **IoT Greengrass**) on the device.
- Use cases: preprocessing data, ML inference, media transcoding, in places like ships, mines, oil rigs, military sites, disaster zones.
- Devices can be **clustered** for higher durability and capacity (Storage Optimized).
- Order for edge compute even if you never ship data back.

## Security

- Data is **always encrypted** (256-bit, keys managed by **KMS**; keys are never stored on the device).
- **Tamper-resistant** enclosure, **TPM**, and tracking via SNS/text notifications.
- Chain of custody and **auditing** via CloudTrail.
- Uses **end-to-end** transfer; device wiped after use.

## Snow Family vs Other Transfer Options

| Need | Use |
|---|---|
| Huge one-time/occasional bulk transfer, slow or no network | **Snow Family** |
| Ongoing online transfer on-prem ↔ AWS (NFS/SMB/HDFS, scheduled) | **DataSync** |
| Fast network, accelerate uploads to S3 | **S3 Transfer Acceleration** / multipart |
| Dedicated private connection, steady high throughput | **Direct Connect** (takes weeks to set up) |
| On-prem apps need cloud-backed storage | **Storage Gateway** |
| SFTP/FTPS/FTP into S3 | **Transfer Family** |

## Exam Tips

- "**Petabytes** of data, **limited bandwidth**, or transfer would take **weeks**" → **Snowball Edge**.
- "**Exabytes**" → **Snowmobile**.
- "**Run compute at remote site with no connectivity**" → Snowball Edge **Compute Optimized** (or Snowcone for small/portable).
- "**Small, rugged, space/weight-limited**" (drones, backpack) → **Snowcone**.
- Snow devices import into **S3**, not Glacier directly: pick S3, then a **lifecycle rule** to Glacier.
- Direct Connect takes **weeks to provision**, so it is not the answer for "migrate in the next few days".
- **OpsHub** is the GUI to manage Snow devices.
- Ongoing sync over the network → **DataSync**, not Snow.

Related: [S3](../S3/README.md), [Backup](../Backup/README.md), [Storage](../EC2/storage.md).
