# AWS Compute Optimizer

**AWS Compute Optimizer** is a managed service that uses **machine learning** to analyze the **historical utilization metrics** (from **CloudWatch**) of your AWS resources and recommend **optimal configurations**. The goal is to **reduce cost** and **improve performance** by **right-sizing**.

```
CloudWatch metrics ──► Compute Optimizer (ML) ──► Findings + up to 3 recommendations
 (CPU, network, disk,                              (projected utilization, estimated savings)
  memory with agent)                                         │
                                                             ▼
                                              Console / API / Export to S3 (CSV)
```

- **Exam keyword**: "find **over-provisioned** or **under-provisioned** resources / **right-size** with the **least operational effort**".
- Recommendations only: it **never changes** your resources. You apply the change yourself.
- The basic service is **free**. Only *Enhanced infrastructure metrics* costs extra.

## Supported Resources

| Resource | What it recommends |
|---|---|
| **EC2 instances** | A better **instance type / size** (also Graviton options) |
| **EC2 Auto Scaling groups** | Instance type for the group (single instance type groups) |
| **EBS volumes** | Volume **type, size, IOPS, throughput** (e.g. gp2 → gp3) |
| **Lambda functions** | **Memory size** |
| **ECS services on Fargate** | Task **CPU and memory** |
| **RDS / Aurora databases** | **Instance class** and storage |
| **Commercial software licenses** | e.g. **SQL Server on EC2** |
| **Idle resources** | Flags resources that are **not being used** |

## How It Works

1. **Opt in**, for a single account or for a whole **AWS Organization** (from the management account).
2. It collects utilization metrics: **CPU, network in/out, disk I/O**, and **memory** (when available).
3. It looks back **14 days** by default.
4. Each resource gets a **finding** and up to **3 recommendations**, with the **projected utilization** and **estimated savings**.

## Findings Classification

| Finding | Meaning |
|---|---|
| **Under-provisioned** | The resource can't meet the workload's needs. **Performance suffers**. |
| **Over-provisioned** | The resource is bigger than needed. **Money is wasted**. |
| **Optimized** | The resource meets the workload's needs. |
| **None** | No recommendation available (e.g. **unsupported instance type**, or not enough data). |

## Metrics and Lookback

| | Details |
|---|---|
| **Default lookback** | **14 days** |
| **Enhanced infrastructure metrics** | **Paid** feature. Extends lookback to **93 days**. Useful for workloads with **monthly/quarterly patterns** |
| **EC2 memory** | **Not collected by default**. Install the **CloudWatch Agent** to get memory-based recommendations |
| **Lambda** | **No agent** needed. Needs enough invocations (about **50 in the last 14 days**) |
| **External metrics** | Can ingest metrics from observability tools (e.g. Datadog, Dynatrace, New Relic) for EC2 memory |

## Cross-Account and Export

- Integrates with **AWS Organizations**: the management account opts in **all member accounts** and sees all recommendations.
- **Export** recommendations to **S3** as **CSV** for reporting and analysis.
- Recommendations are **regional**: you view them per Region.

## CLI Example

```bash
# Opt in (account level)
aws compute-optimizer update-enrollment-status --status Active

# EC2 instance recommendations
aws compute-optimizer get-ec2-instance-recommendations

# Only over-provisioned instances
aws compute-optimizer get-ec2-instance-recommendations \
  --filters name=Finding,values=Overprovisioned

# Lambda memory recommendations
aws compute-optimizer get-lambda-function-recommendations

# EBS volume recommendations
aws compute-optimizer get-ebs-volume-recommendations

# Export to S3
aws compute-optimizer export-ec2-instance-recommendations \
  --s3-destination-config bucket=my-bucket,keyPrefix=compute-optimizer/
```

## Compute Optimizer vs Similar Services

| | **Compute Optimizer** | **Trusted Advisor** | **Cost Explorer** | **Auto Scaling** |
|---|---|---|---|---|
| Purpose | **ML-based right-sizing** of compute, storage and DB | **Broad checks**: cost, security, fault tolerance, performance, limits | **Cost analysis**, forecasts, basic EC2 rightsizing | **Adjust capacity** automatically |
| Detail level | **High** (instance type, projected utilization) | Lower (e.g. "low utilization EC2") | Medium | n/a |
| Acts on resources | No (recommends) | No (recommends) | No (recommends) | **Yes** |

## Exam Tips

- "Identify **over-provisioned EC2 instances** to **reduce cost** with **minimal operational effort**" → **Compute Optimizer**.
- "Recommendations based on **memory utilization** for EC2" → install the **CloudWatch Agent** (memory is not a default metric).
- "Need a **longer lookback** than 14 days" → **Enhanced infrastructure metrics** (**93 days**, paid).
- "Right-size **Lambda memory**" → Compute Optimizer (no agent needed).
- "Migrate **gp2 to gp3**" or find **idle / oversized EBS volumes** → Compute Optimizer.
- "Review recommendations across **all accounts**" → enable via **AWS Organizations**.
- It **only recommends**. Automatic scaling is **Auto Scaling**, not Compute Optimizer.
- Broad best-practice checks (security groups, MFA, service limits) → **Trusted Advisor**, not Compute Optimizer.
- Do not confuse it with **AWS Cost Explorer** rightsizing: Compute Optimizer is **ML-based and more detailed**.
