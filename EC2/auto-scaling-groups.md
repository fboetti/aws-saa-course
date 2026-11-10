# Auto Scaling Groups (ASG)

Follows the ASG section of the [freeCodeCamp AWS SAA course](https://www.youtube.com/watch?v=c3Cn4xYfxJY&t=77806s) (starts around **21:36:46**), refined for **SAA-C03**.

An **Auto Scaling group** is a logical collection of EC2 instances that AWS launches, monitors and terminates for you, so the fleet matches demand and stays healthy. It is **free**: you pay only for the instances, EBS volumes and CloudWatch alarms it creates.

Goals:

- **Elasticity**: add instances when load rises, remove them when it drops (cost saving).
- **Availability / self-healing**: replace failed instances automatically, spread across AZs.
- **Fault tolerance**: keep a minimum number of healthy instances at all times.

## Capacity Settings

| Setting | Meaning |
|---|---|
| **Minimum** | Floor. The ASG never scales in below this |
| **Desired** | The number the ASG tries to maintain right now. Scaling policies change this value |
| **Maximum** | Ceiling. The ASG never scales out above this (also a cost guardrail) |

- Always `min ≤ desired ≤ max`.
- `min = max = desired = 1` is a valid trick for a **self-healing single instance** (replaced if it dies, no scaling).
- Scaling policies move **desired** between min and max. Manual changes to desired are allowed too.

## Launch Template

The ASG needs a blueprint for new instances: a **launch template** (versioned).

- Includes: AMI, instance type, key pair, security groups, IAM instance profile, EBS volumes, user data, tags, network settings, placement/tenancy.
- **Launch configurations** are the legacy, non-versioned option. **Deprecated**: no new features, and new accounts cannot create them. Use launch templates.
- Supports **mixed instances policy**: several instance types and a mix of **On-Demand and Spot** (for example a base of On-Demand plus Spot above it), with allocation strategies such as `price-capacity-optimized`.
- Use a **custom AMI** (baked) to make scale-out fast instead of long user data scripts. See [AMIs](amis.md).

## Networking and Multi-AZ

- You choose **subnets** (in one or more AZs) for the ASG. A VPC with the ASG spanning **≥ 2 AZs** is the standard HA design.
- The ASG tries to keep instances **balanced across AZs**. If an AZ becomes unhealthy, it launches replacements in the remaining AZs (**AZ rebalancing**).
- An ASG is **regional**: it cannot span regions.
- Place instances in **private subnets** behind a public load balancer where possible.

## Health Checks

| Type | Detects | Notes |
|---|---|---|
| **EC2** (default) | Instance state and EC2 status checks (stopped, terminated, impaired hardware) | Does not notice a crashed app on a running instance |
| **ELB** | Failed load balancer target-group health check (for example HTTP 200 on `/health`) | Enable it when the ASG is attached to a load balancer |
| **VPC Lattice** / **EBS** | Lattice target health, EBS volume health | Newer, optional |
| **Custom** | Anything: your code calls `set-instance-health` | For external monitoring |

- An unhealthy instance is **terminated and replaced**.
- **Health check grace period** (default 300 s): time after launch before health checks count, so the app can boot. Set it longer than your bootstrap time or the ASG may kill instances in a loop.

## Load Balancer Integration

- Attach the ASG to an **ELB target group** (ALB, NLB or GWLB). New instances register automatically and terminating ones are **deregistered** (with **connection draining** / deregistration delay).
- Turn on **ELB health checks** so a failing app (not only a failing VM) triggers replacement.
- Instance security group should allow traffic **only from the load balancer's security group**.
- See [Scaling and Load Balancing](scaling-load-balancing.md) for the ELB types.

## Scaling Policies

| Policy | How it works | When to use |
|---|---|---|
| **Manual** | Change min/desired/max yourself | Testing, one-off changes |
| **Simple scaling** | One CloudWatch alarm → one adjustment → wait for cooldown | Legacy, rarely best |
| **Step scaling** | Alarm with steps: bigger breach → bigger adjustment. No fixed cooldown, uses warm-up | Need finer response than target tracking |
| **Target tracking** | Hold a metric near a target value (for example average CPU 50%). ASG creates and manages the alarms | **Default recommendation**, easiest |
| **Scheduled** | Change capacity at a set time/recurrence (cron) | Known patterns (office hours, Black Friday) |
| **Predictive** | ML forecasts load from up to 14 days of history and scales **ahead** of demand (forecast-only or forecast-and-scale) | Recurring, cyclical traffic |

Common metrics:

- `ASGAverageCPUUtilization`, `ASGAverageNetworkIn` / `ASGAverageNetworkOut`
- `ALBRequestCountPerTarget` (good fit for web apps behind an ALB)
- **Custom CloudWatch metrics**, for example **SQS queue backlog per instance** (`ApproximateNumberOfMessagesVisible` ÷ running instances) for worker fleets.

Timing controls:

- **Default cooldown** (300 s): after a scaling activity, wait before another **simple** scaling action, to avoid thrashing.
- **Instance warm-up**: time before a new instance's metrics count towards the group's aggregated metrics (stops over-scaling while instances boot).
- EC2 **detailed monitoring** (1-minute metrics) helps scaling react faster; basic is 5 minutes.

## Termination (Scale-In)

Default termination policy, in order:

1. Pick the **AZ with the most instances** (keep balance).
2. Within it, terminate the instance with the **oldest launch template/configuration**.
3. If still tied, the one **closest to the next billing hour** (historical rule), then random.

Other options: `OldestInstance`, `NewestInstance`, `OldestLaunchTemplate`, `AllocationStrategy`, `ClosestToNextInstanceHour`, custom Lambda.

- **Scale-in protection**: mark instances (or the whole group) as not eligible to be terminated by scale-in. It does **not** stop health-check replacement, manual termination or Spot interruptions.
- **Standby**: take an instance out of service temporarily (for patching or debugging) without it being replaced.

## Lifecycle Hooks

Pause an instance at a transition so you can run custom actions.

- **Launch hook** → instance waits in `Pending:Wait` (install agents, register with a system).
- **Terminate hook** → instance waits in `Terminating:Wait` (drain connections, upload logs, copy data).
- Notify via **EventBridge**, **SNS** or **SQS**, then complete the action (`CONTINUE` or `ABANDON`) or let the **heartbeat timeout** expire (default 1 hour, up to 48 h).

## Other Features

- **Instance refresh**: rolling replacement of all instances after a new AMI or launch template version. Set min healthy percentage and warm-up. Supports checkpoints and auto rollback.
- **Warm pools**: pre-initialised, **stopped** (or running/hibernated) instances waiting to join, to cut scale-out time for apps with slow startup. Stopped instances cost only EBS.
- **Maximum instance lifetime**: force instances to be recycled after N days (security, memory leaks). Range 1 to 365 days.
- **Notifications**: SNS messages on launch, terminate and failures.
- **Capacity rebalancing** (Spot): launch a replacement proactively when a Spot instance gets a rebalance recommendation.
- **Attribute-based instance type selection**: describe vCPU/memory needs instead of listing instance types.
- **Suspend processes**: pause `Launch`, `Terminate`, `HealthCheck`, `ReplaceUnhealthy`, `AZRebalance`, `AlarmNotification`, `ScheduledActions`, `AddToLoadBalancer`.

## Typical Design

```
Route 53 → ALB (public subnets, 2+ AZs)
              └─ target group → ASG (private subnets, 2+ AZs)
                                   └─ launch template (custom AMI, IAM role, SG from ALB)
                                RDS Multi-AZ (data subnets)
```

Decoupled worker pattern: **SQS queue → ASG of workers**, scale on backlog per instance.

## Exam Tips

- "Self-healing / replace failed instances / keep N instances running" → **ASG** (even with min=max=1).
- "HA across AZs" → ASG over **≥ 2 AZs** (subnets) behind an ELB.
- "Scale to keep CPU at X%" → **target tracking**. "Known weekly peak" → **scheduled**. "Cyclical, scale ahead of time" → **predictive**.
- "Scale on queue length" → custom metric of **SQS messages per instance**.
- App crashes but instance is "running" and isn't replaced → enable **ELB health checks** on the ASG.
- Instances keep being killed right after launch → raise the **health check grace period**.
- Slow scale-out because of long boot → **custom AMI** and/or **warm pool**.
- Roll out a new AMI without downtime → update launch template, then **instance refresh**.
- Run custom code before an instance is added or removed → **lifecycle hooks**.
- Cut cost with fault-tolerant workloads → **mixed instances policy** with **Spot**.
- ASG is **free** and **regional**; it cannot span regions. Launch configurations are **deprecated**.
- Default scale-in: balance AZs first, then oldest launch template/config.
- Fargate doesn't use ASG

