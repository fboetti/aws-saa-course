# AWS Batch

**AWS Batch** is a fully managed service for running **batch computing jobs** at any scale. You submit jobs (packaged as **Docker containers**), and Batch **provisions the compute**, **queues and schedules** the jobs, runs them, and **scales the resources down** when the work is done. There is **no extra charge** for Batch itself: you pay only for the EC2 / Fargate resources the jobs use.

## Purpose

- **Run large numbers of jobs** (hundreds of thousands) without installing or managing batch software or job schedulers.
- **Dynamic provisioning**: Batch picks the right instance types and amount of capacity based on the jobs' CPU, memory and GPU requirements.
- **Cost optimization**: run on **Spot Instances** (up to ~90% cheaper) or Fargate Spot for fault-tolerant work.
- Typical workloads: **financial risk modeling**, **genomics**, **media transcoding / rendering**, **scientific simulations**, **ML training and data processing**, nightly **ETL**.

## Core Concepts

```
Job definition ─► Submit job ─► Job queue (priority) ─► Scheduler ─► Compute environment
 (image, vCPU,                   ├─ high-priority queue              ├─ EC2 On-Demand
  memory, role,                  └─ low-priority queue               ├─ EC2 Spot
  retries, timeout)                                                  ├─ Fargate / Fargate Spot
                                                                     └─ EKS cluster
```

| Concept | What it is |
|---|---|
| **Job** | A unit of work: a container image + command (shell script, binary, Linux executable). |
| **Job definition** | Template for a job: image, vCPU/memory/GPU, IAM role, environment variables, volumes, **retry strategy**, **timeout**. |
| **Job queue** | Where submitted jobs wait. Has a **priority** and is mapped to one or more compute environments (in order). |
| **Compute environment** | The pool of compute that runs the jobs. **Managed** (Batch scales it) or **unmanaged** (you manage the instances). |
| **Scheduler** | Decides when, where and in what order jobs run, using queue priority and **fair-share scheduling policies**. |

## Compute Environment Options

| Option | When to use |
|---|---|
| **EC2 On-Demand** | Steady, time-critical jobs; need specific instance types, GPUs, large memory |
| **EC2 Spot** | Fault-tolerant, flexible jobs at lowest cost (set allocation strategy, e.g. `SPOT_PRICE_CAPACITY_OPTIMIZED`) |
| **Fargate / Fargate Spot** | Serverless: no instances to manage, faster start, smaller jobs (up to 16 vCPU / 120 GB) |
| **EKS** | Run Batch jobs on an existing Amazon EKS (Kubernetes) cluster |

- Managed EC2 environments set **min / desired / max vCPUs**. With min = 0, nothing runs (and nothing is billed) when the queue is empty.
- You can provide a **launch template** and custom AMI (e.g. extra software or larger disks).
- Instances run **in your VPC/subnets**, so jobs can reach private resources (RDS, EFS...).

## Job Types and Features

- **Array jobs**: one submission runs **many copies** of the same job (up to 10,000), each with its own index (`AWS_BATCH_JOB_ARRAY_INDEX`). Good for "process each of these N files".
- **Job dependencies**: a job starts only after other jobs finish (simple workflows, e.g. pre-process → process → aggregate).
- **Multi-node parallel jobs**: one job spans **several EC2 instances** (tightly coupled HPC, MPI, distributed ML training). Not supported on Fargate. Pair with **EFA** and a **cluster placement group**.
- **Retries and timeouts**: automatic retry on failure (e.g. Spot interruption), and a timeout to kill stuck jobs.
- **Scheduling**: run jobs on a schedule with **EventBridge Scheduler**, or trigger them from events (e.g. a file uploaded to **S3** → EventBridge → Batch job).
- **Orchestration**: use **Step Functions** for complex multi-step workflows.
- **Monitoring**: job logs go to **CloudWatch Logs**; job state changes are sent to **EventBridge**.

## Security

- **IAM job role**: permissions the container gets (e.g. read from S3, write to DynamoDB).
- **Execution role**: lets Batch/ECS pull the image from ECR and write logs.
- **Service-linked role** for Batch to manage resources; **instance role** for EC2 container instances.
- Network control with **security groups** and private subnets (use NAT or **VPC endpoints** to reach ECR/S3).

## AWS Batch vs Lambda

| | **AWS Batch** | **AWS Lambda** |
|---|---|---|
| Max run time | **No limit** | **15 minutes** |
| Runtime | Any **Docker** image, any language | Supported runtimes or container image (≤ 10 GB) |
| Resources | Any EC2 instance type, **GPUs**, large memory and disk (EBS) | Up to 10 GB memory, 10 GB `/tmp` storage, no GPUs |
| Compute | Managed EC2 / Spot / Fargate (still **real instances**) | Fully serverless |
| Best for | Long, heavy, high-throughput batch jobs | Short, event-driven functions |

## Other Comparisons

- **Batch vs ECS / EKS**: ECS/EKS run **long-running services** and you manage the scaling/scheduling. Batch adds **job queues, priorities, retries and auto-provisioning** for run-to-completion jobs (and runs on top of ECS/EKS).
- **Batch vs EMR / Glue**: EMR (Spark, Hadoop) and Glue (serverless ETL) are for **big-data frameworks**. Batch runs **any containerized code**.
- **Batch vs ParallelCluster**: ParallelCluster builds a traditional **HPC cluster** (Slurm). Batch is the managed, queue-based option.

## Exam Tips

- "**Batch jobs** / batch processing at any scale / run **Docker** jobs, **no servers or job scheduler to manage**" → **AWS Batch**.
- "Job runs **longer than 15 minutes**" or needs **GPU / large memory** → **Batch**, not Lambda.
- "Lowest cost for **fault-tolerant** batch work" → **Batch + Spot Instances** (with retries).
- "Run a batch job **on a schedule**" → **EventBridge (Scheduler)** → Batch. "When a file lands in **S3**" → S3 event → EventBridge → Batch.
- "**Tightly coupled HPC** across multiple instances" → **multi-node parallel jobs** (+ EFA, cluster placement group).
- "Same job for **thousands of inputs**" → **array jobs**.
- Batch itself is **free**; you pay for the underlying **EC2 / Fargate**. It is a **regional** service.

Related: [EC2 Purchasing Options](../EC2/purchasing-options.md), [EC2 Networking (EFA, placement groups)](../EC2/networking.md), [Auto Scaling Groups](../EC2/auto-scaling-groups.md), [S3](../S3/README.md), [IAM](../IAM/README.md).
