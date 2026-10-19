# Resilience patterns with Regions and AZs

How the building blocks from [Regions](../regions/README.md) and
[Availability Zones](../availability-zones/README.md) combine into designs the SAA exam
asks about.

## Picking the right scope

| Requirement wording                                        | Scope        | Example tools |
|------------------------------------------------------------|--------------|---------------|
| Survive a data centre / AZ failure                         | Multi-AZ     | ALB + EC2 in 2 AZs, RDS Multi-AZ, Auto Scaling across AZ subnets |
| Survive a whole region failure                             | Multi-region | Route 53 health checks + failover, S3 CRR, DynamoDB Global Tables |
| Low latency for global users                               | Global edge  | CloudFront, Global Accelerator, Route 53 latency routing |
| Data must not leave a country / EU                         | Single region| Choose an `eu-*` region, block replication elsewhere |
| RPO in seconds/minutes, RTO in minutes                     | Pilot light / warm standby across regions | Snapshot copy, replicated database |
| RPO/RTO near zero                                          | Active-active multi-region | Global Tables, Route 53 weighted/latency routing |

## Multi-AZ blueprint (the everyday answer)

```text
                 Route 53
                    │
                    ▼
            ┌── Load balancer (regional, nodes in each AZ) ──┐
            │                     │                           │
      ┌─────▼─────┐         ┌─────▼─────┐              ┌──────▼────┐
      │  AZ a     │         │  AZ b     │              │  AZ c     │
      │  EC2/ASG  │         │  EC2/ASG  │              │  EC2/ASG  │
      │  RDS      │◄─sync──►│  RDS      │              │           │
      │  primary  │  standby│  standby  │              │           │
      └───────────┘         └───────────┘              └───────────┘
```

Deployment steps in Terraform / CDK terms:

1. Create **one subnet per AZ** (or use existing ones).
2. Put the Auto Scaling group's `vpc_zone_identifier` across those subnets.
3. Attach **all** subnets to the load balancer's target group / ALB.
4. Enable **RDS Multi-AZ** (or Aurora, which replicates across three AZs by design).
5. Store static state in **S3 / EFS / DynamoDB** so instances stay stateless.

## Multi-region blueprint (disaster recovery)

- **Backup and restore (pilot light):** snapshots or replicas copied to a second region;
  cheapest, longest RTO.
- **Warm standby:** a scaled-down copy of the stack running in the second region; failover
  by scaling up and shifting traffic.
- **Active-active:** Route 53 latency or weighted routing to both regions, data replicated
  with DynamoDB Global Tables / S3 cross-region replication; lowest RTO, highest cost.

## Global services that tie it together

- **Route 53** - health checks and routing policies (latency, failover, weighted) decide
  which region users hit.
- **CloudFront** - caches at edge locations, origin can be a region or S3.
- **Global Accelerator** - anycast IP routing to the closest healthy region.
- **AWS Organizations** - separate accounts per environment/region when isolation matters.

## Exam decision flow

1. Does it need to survive an **AZ** failure? → multi-AZ (near-zero extra cost for most
   designs, and the exam expects it).
2. Does it need to survive a **region** failure? → multi-region + Route 53 failover.
3. Does it need **low latency worldwide**? → CloudFront / Global Accelerator / latency
   routing.
4. Does data have to **stay in one place**? → single region, no cross-region replication.

Related reading: [Regions](../regions/README.md) ·
[Availability Zones](../availability-zones/README.md)
