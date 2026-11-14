# AWS EC2 — Theoretical Overview

Notes on **Amazon Elastic Compute Cloud (EC2)**, AWS's virtual-server service. Follows the EC2 section of the [freeCodeCamp AWS SAA course](https://www.youtube.com/watch?v=c3Cn4xYfxJY&t=69223s) (section starts around **19:14:03**), refined for the **SAA-C03** exam.

| Note | Read it for |
|---|---|
| **This page** | The EC2 map: what it is, lifecycle, key facts |
| [Instance Types](instance-types.md) | Families (M, C, R, T, I, G…), naming, burstable CPU, Graviton, Nitro |
| [Lifecycle and Actions](lifecycle.md) | Launch, reboot, stop/start, hibernate, terminate, retire, recover, status checks |
| [AMIs](amis.md) | Images, root device, copying across regions, sharing, building |
| [Purchasing Options](purchasing-options.md) | On-Demand, Reserved, Savings Plans, Spot, Dedicated, Capacity Reservations |
| [Storage: EBS, Instance Store, EFS](storage.md) | Volume types, snapshots, encryption, instance store, sharing file systems |
| [EBS and EFS in Depth](ebs-efs.md) | Volume types, Multi-Attach, snapshots, encryption, EFS classes, performance/throughput modes, security |
| [Networking](networking.md) | ENI, public/private/Elastic IP, ENA/EFA, placement groups |
| [Security](security.md) | Security groups vs NACLs, key pairs, IAM roles, IMDS, SSM |
| [User Data and Metadata](user-data-metadata.md) | Bootstrapping, instance metadata service, IMDSv2 |
| [Cloud-Init](cloud-init.md) | How user data is executed: formats, `#cloud-config`, stages, logs, re-running |
| [Auto Scaling Groups](auto-scaling-groups.md) | Capacity, launch templates, health checks, scaling policies, termination, lifecycle hooks |
| [Application Auto Scaling](application-auto-scaling.md) | Scaling ECS, DynamoDB, Aurora, Lambda; scaling plans; extra ASG exam details |
| [Elastic Load Balancing](elastic-load-balancing.md) | ALB, NLB, GWLB, listeners, target groups, cross-zone, TLS/SNI, sticky sessions |
| [Scaling and Load Balancing](scaling-load-balancing.md) | Short summary of ASG and ELB |
| [Exam Info and Tips](exam-tips.md) | Scenario → answer cheat sheet, traps |

Related notes elsewhere in this repo: [VPC](../VPC/README.md), [IAM](../IAM/README.md), [S3](../S3/README.md).

## What is EC2?

EC2 provides **resizable virtual machines (instances)** in the cloud, billed per second (Linux) or per hour (some other OSes/marketplace AMIs).

- **Regional service**, but each instance lives in **one Availability Zone** (inside one subnet of a VPC).
- You choose: **AMI** (OS + software), **instance type** (CPU/RAM/network), **storage**, **network/security group**, **key pair**, **IAM role**, **user data**.
- You are responsible for the guest OS (patching, hardening) — **shared responsibility model**.
- Runs on the **Nitro System** (hypervisor + dedicated hardware) for most modern types.

## Instance Lifecycle

| State | Billed for compute? | Notes |
|---|---|---|
| **pending** | No | Starting up |
| **running** | Yes | Usable |
| **stopping / stopped** | No (EBS storage and Elastic IPs still billed) | Can change instance type; may move hosts; public IP lost |
| **stopping (hibernate)** | No compute | RAM saved to encrypted EBS root volume; fast resume |
| **shutting-down / terminated** | No | Deleted; root EBS volume deleted by default (`DeleteOnTermination`) |

Key points:

- **Reboot** keeps the same host, IPs and instance store data.
- **Stop/start** usually moves to a new host: **instance store data is lost**, public IPv4 changes (unless Elastic IP), private IP stays.
- **Termination protection** blocks API/console termination; **stop protection** blocks stop.
- **Hibernate** needs an encrypted root EBS volume, RAM < 150 GB, supported instance types, max 60 days.

## Quick Facts

- Max **EBS-backed** root volume up to 64 TiB (gp3/io2); instance store root is possible on older/special AMIs.
- Default limits: On-Demand **vCPU-based service quotas** per region.
- **User data** runs once at first launch (by default), as root.
- **Connect**: SSH (22), RDP (Remote Desktop, port 3389), **EC2 Instance Connect**, **Session Manager** (no open ports needed).
- Pricing dimensions: instance type, purchasing option, region, EBS, data transfer out, Elastic IPs, load balancers.
