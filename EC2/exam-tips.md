# EC2 Exam Info and Tips (SAA-C03)

## Scenario → Answer

| Scenario | Answer |
|---|---|
| Steady workload for 1–3 years | Reserved Instances / Savings Plans |
| Fault-tolerant batch, lowest cost | Spot Instances |
| BYOL with per-socket/core licence | Dedicated Host |
| Guarantee capacity in an AZ | On-Demand Capacity Reservation |
| Bursty low-average CPU | T-family (burstable) |
| In-memory DB / cache | Memory optimised (R, X) |
| HPC, low node latency | Compute optimised + Cluster placement group + EFA |
| ML training | P/Trn (accelerated); inference → Inf/G |
| Highest local IOPS, temp data | Instance store |
| Durable high IOPS DB | io2 / io2 Block Express |
| Cheap large sequential throughput | st1 |
| Shared Linux file system across AZs | EFS |
| Share EBS across instances | io1/io2 Multi-Attach (same AZ) or EFS |
| Move volume/instance to another AZ/region | Snapshot/AMI → copy → restore |
| Faster boot, repeatable environment | Custom (golden) AMI / Image Builder |
| Static public IP | Elastic IP (or NLB) |
| Reduce correlated hardware failure | Spread placement group |
| Big-data distributed, rack-aware | Partition placement group |
| Shell access with no open ports | SSM Session Manager |
| App needs AWS API access | IAM instance role |
| Run script at launch | User data |
| Self-healing, scalable web tier | ASG + ALB across AZs |

## Traps

- Instance store data is **lost on stop/terminate** (not reboot).
- Stop/start changes **public IPv4** (not private) and may change host.
- Root EBS deletes on terminate by default; extra volumes do not.
- EBS is **AZ-bound**; snapshots are regional.
- Security groups are **allow-only and stateful**; NACLs are stateless.
- Spread group: max **7 instances per AZ**.
- st1/sc1 **cannot be boot** volumes.
- Hibernate requires **encrypted root EBS**.
- Encrypted AMI sharing needs a **customer-managed KMS key** shared too.
- Elastic IPs and public IPv4 addresses **cost money**; idle EIP still charged.
- Spot gives a **2-minute** warning, not guaranteed capacity.
- ALB = L7, NLB = L4 with static IPs.

## Quick-Fire Facts

- Billing: per second (min 60 s) for Linux On-Demand.
- Metadata IP: `169.254.169.254`.
- User data limit 16 KB, runs as root.
- CloudWatch basic monitoring 5 min (free); detailed 1 min (paid). Memory/disk metrics need the **CloudWatch agent**.
- Status checks: **system** (AWS hardware) and **instance** (OS). CloudWatch alarm action **recover** fixes system failures keeping IP/ID.
- Default Auto Scaling cooldown 300 s.
