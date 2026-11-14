# AWS Auto Scaling: Beyond EC2 Auto Scaling Groups (SAA-C03)

> The ASG basics (min/desired/max, launch templates, health checks, termination, lifecycle hooks) are in [Auto Scaling Groups](auto-scaling-groups.md). This note covers the **other "Auto Scaling" services** and the extra details the exam likes to test.

## Three Things Called "Auto Scaling"

| Name | Scales | Notes |
|---|---|---|
| **Amazon EC2 Auto Scaling** | EC2 instances in an **Auto Scaling group** | Uses launch templates, CloudWatch alarms, ELB. Covered in [ASG notes](auto-scaling-groups.md) |
| **Application Auto Scaling** | Everything else (API and CLI service, no console of its own) | ECS services, DynamoDB, Aurora, Lambda, and more (see below) |
| **AWS Auto Scaling** (scaling plans) | One console to build **scaling plans** across EC2 ASG, ECS, DynamoDB, Aurora | Convenience wrapper over the two above. Rarely the exam answer |

## Application Auto Scaling: Scalable Targets

| Service | What scales | Typical metric |
|---|---|---|
| **ECS (incl. Fargate)** | Task **desired count** of a service | `ECSServiceAverageCPUUtilization`, `ALBRequestCountPerTarget` |
| **DynamoDB** | **Provisioned** read/write capacity (tables and GSIs) | Consumed capacity vs provisioned (target utilization, e.g. 70%) |
| **Aurora** | Number of **Aurora Replicas** (read replicas) | Average CPU or connections of replicas |
| **Lambda** | **Provisioned concurrency** | Utilization of provisioned concurrency |
| **EMR**, **SageMaker endpoints**, **Amazon Keyspaces**, **MSK** (storage), **ElastiCache** (replicas/shards), **Neptune**, **Comprehend**, **AppStream fleets**, **EC2 Spot Fleet** | Capacity of each | Service-specific |

- Same policy types as ASG: **target tracking**, **step**, **scheduled** (**predictive** is EC2 Auto Scaling only).
- **Min and max capacity** are required per target, as with an ASG.
- Uses CloudWatch alarms behind the scenes (target tracking creates and manages them).

### Key Cases

- **ECS/Fargate**: **Fargate has no ASG** (no instances to manage). Scale the **service desired task count** with Application Auto Scaling.
  - **ECS on EC2**: two layers. (1) **Service auto scaling** (tasks) and (2) **EC2 capacity**: ASG, ideally with an **ECS capacity provider** (managed scaling) so the ASG grows when tasks cannot be placed.
- **DynamoDB**: auto scaling only applies to **provisioned mode**. **On-demand mode** needs no scaling. Autoscaling reacts in minutes, so it **cannot absorb sudden spikes**; on-demand or **DAX** helps. Reserved capacity is a separate cost feature.
- **Aurora**: scales **read replicas** (up to 15), **not the writer** and not storage (storage grows automatically). **Aurora Serverless v2** scales compute (ACUs) itself.
- **Lambda**: scales concurrency automatically by default. Application Auto Scaling only matters for **provisioned concurrency** (avoid cold starts on a schedule or load).
- **S3, SQS, SNS, Kinesis on-demand, API Gateway, DynamoDB on-demand**: scale on their own, nothing to configure.

## Scaling Out vs Up

| | Horizontal (out/in) | Vertical (up/down) |
|---|---|---|
| Change | Number of instances | Instance size |
| AWS tool | ASG, Application Auto Scaling | Resize instance type or RDS class (stop/restart, **downtime**) |
| Exam angle | Elasticity, HA, no downtime | Quick fix, but not automatic and not HA |

> ASG does **horizontal** scaling. It never changes instance size.

## Extra ASG Details Worth Knowing

- **Metrics resolution**: ASG group metrics are **1-minute**, but they are **opt-in** (enable group metrics collection). Detailed EC2 monitoring gives 1-minute instance metrics for faster policies.
- **Scale-in vs ELB**: terminating instances are **deregistered** first and **connection draining** (deregistration delay, default 300 s) lets in-flight requests finish.
- **Attach / detach**: you can attach an **existing running instance** to an ASG (it must be in the same AZ/subnets, AMI exists) or detach one, which lowers desired unless told otherwise.
- **Launch template changes** affect **only new instances**. Existing ones keep the old config until replaced by an **instance refresh**.
- **Scheduled actions** can set min/desired/max, so scheduling `min=0` at night **stops all instances** (cost saving for dev/test).
- **Cannot span regions**. For multi-region, use Route 53 failover/latency plus an ASG per Region.
- **Spot and ASG**: mixed instances policy with an On-Demand base. For **Spot interruptions** the ASG replaces the instance (enable **capacity rebalancing** to act on rebalance recommendations early).
- **Cost**: ASG is free. Alarms and detailed monitoring cost a little. **Reserved Instances / Savings Plans** discounts apply automatically to ASG instances.
- **Notifications**: **SNS** and **EventBridge** events for launch, terminate, and failed launch (for example, instance limit reached or AMI missing).
- **Service quotas**: an ASG fails to launch if you hit the **vCPU/instance quota**, there is no capacity for the type in an AZ (use several instance types or AZs), or the launch template references a deleted AMI/key/security group.

## Design Patterns

```
Web tier     : ALB ──► ASG (target tracking on ALBRequestCountPerTarget)
Worker tier  : SQS ──► ASG (custom metric: backlog per instance)
Containers   : ALB ──► ECS service on Fargate (Application Auto Scaling on task count)
Data tier    : Aurora writer + replicas (replica auto scaling), DynamoDB (provisioned + auto scaling)
Known peaks  : scheduled scaling (or predictive) + target tracking for the surprises
```

- Decouple tiers with **SQS** or **ELB** so each tier scales **independently**.
- Combine **scheduled** (known events) with **target tracking** (unknown variation).

## Exam Tips

- "Scale **EC2 instances** automatically" → **EC2 Auto Scaling group**.
- "Scale **ECS service tasks**, **DynamoDB** capacity, **Aurora replicas**" → **Application Auto Scaling**.
- "**Fargate**" never needs an ASG.
- "Aurora **write** performance" → bigger writer instance (**vertical**), **not** auto scaling. Auto scaling only adds **read replicas**.
- "DynamoDB unpredictable, spiky traffic, no capacity planning" → **on-demand mode**. "Predictable, cost-optimized" → **provisioned + auto scaling**.
- "Keep CPU at 50%" → **target tracking**. "Every day at 9am" → **scheduled**. "Learned daily/weekly pattern" → **predictive**.
- "Scale on **queue depth**" → custom metric: **backlog per instance** (SQS `ApproximateNumberOfMessagesVisible` ÷ instances).
- "New AMI rollout with no downtime" → update launch template + **instance refresh**.
- "Application is down but instances show healthy" → enable **ELB health checks** in the ASG.
- "Instances terminate right after launch" → raise **health check grace period**.
- "Reduce cost of dev environment overnight" → **scheduled action with min/desired = 0**.
- "Resize an instance automatically" → not possible with ASG (**horizontal only**).
- ASG, Application Auto Scaling and scaling plans are **free**. You pay for the resources.

Related: [Auto Scaling Groups](auto-scaling-groups.md), [Elastic Load Balancing](elastic-load-balancing.md), [Scaling and Load Balancing](scaling-load-balancing.md), [Purchasing Options](purchasing-options.md), [Exam Info and Tips](exam-tips.md).
