# Availability Zones (AZs)

An **Availability Zone** is one or more discrete data centres inside a region, each with
its own power, cooling and networking. A region normally has **2 or more AZs** (most have
three).

```
eu-north-1 (Stockholm)
├── eu-north-1a   <- data centre(s), independent power + network
├── eu-north-1b
└── eu-north-1c
      ↕  low-latency redundant fibre (typically < 2 ms round trip)
```

## Key properties

- **Physically separated** - a fire, flood or power failure in one AZ does not affect the
  others.
- **Logically connected** - tens to hundreds of Gbit/s of redundant fibre between AZs in
  the same region, so synchronous replication (RDS Multi-AZ, EFS, shared EBS via
  replication) is viable with low latency.
- **Independent failure domain** - this is the unit AWS designs fault tolerance around.
- **Named per account, not per customer** - the labels `1a`, `1b`, `1c` are mapped
  differently for different AWS accounts inside the same region. Never hard-code
  `eu-north-1a` in infrastructure code; look it up dynamically.

## Why multi-AZ is the default answer

| Requirement                  | Typical design                                            |
|------------------------------|-----------------------------------------------------------|
| High availability            | Load balancer across 2+ AZs, instances in each AZ         |
| Database failover            | RDS Multi-AZ (standby in a second AZ, automatic failover) |
| File storage                 | EFS / S3, both inherently regional with AZ redundancy     |
| Fault tolerance (compute)    | Auto Scaling group with `multiple A Zs` subnets           |

Rule of thumb for the exam: **"the application must remain available if an AZ fails"**
→ put the same workload in at least two AZs behind a load balancer.

## What an AZ is *not*

- It is **not a single data centre** - it may contain several.
- It is **not a region** - it has no separate control plane; the region's API serves all
  of its AZs.
- It is **not automatically multi-AZ** - you have to place resources in more than one AZ
  yourself (subnets are the mechanism: each subnet lives in exactly one AZ).

## Working with AZs

- A **subnet** belongs to exactly one AZ. Spreading an application means creating one
  subnet per AZ and placing resources in each.
- **S3, EFS and DynamoDB** replicate across AZs internally; you do not "put them in two
  AZs".
- **Load balancers** (ALB/NLB) are regional objects whose *nodes* live in the AZs you
  attach subnets for; they fail over per AZ automatically.
- **EBS volumes** are AZ-scoped - to move a volume you must create a snapshot and restore
  it in another AZ.
- **EC2 instances and security groups** are AZ-scoped; security groups can reference
  resources across AZs in the same region.

## Commands

```bash
# AZs of the current region and their state
aws ec2 describe-availability-zones \
  --query "AvailabilityZones[].[ZoneName,ZoneType,State]" --output table

# Which AZ does my instance sit in?
aws ec2 describe-instances \
  --filters "Name=instance-id,Values=i-0123456789abcdef0" \
  --query "Reservations[].Instances[].Placement.AvailabilityZone"

# Default VPC subnets (one per AZ)
aws ec2 describe-subnets \
  --query "Subnets[].[CidrBlock,AvailabilityZone,MapPublicIpOnLaunch]" --output table
```

## Exam traps

- AZs in a region are **not** named the same way for every account - look them up, don't
  assume.
- Multi-AZ ≠ multi-region. Multi-AZ gives **high availability**; multi-region gives
  **disaster recovery / geo-redundancy**.
- Cross-AZ traffic between instances can incur **data transfer charges**; keep tiers of a
  single application mindful of that when designing for cost.
- "The application must survive an entire region going down" → you need **multi-region**,
  not multi-AZ.

Next: [Resilience patterns](../resilience/README.md)
