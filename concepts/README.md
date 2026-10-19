# AWS Global Infrastructure

Notes for the AWS Solutions Architect Associate course. This folder explains how AWS
organizes its infrastructure around the world, and how that layout drives the design
decisions you are tested on (high availability, disaster recovery, latency and compliance).

## Contents

- [Regions](regions/README.md) - what a region is, how they are named, and how to choose one.
- [Availability Zones](availability-zones/README.md) - what an AZ is and why multi-AZ is the default answer.
- [Resilience patterns](resilience/README.md) - how regions and AZs combine into HA and DR designs.

## The 10,000 ft view

```
AWS (global)
 └── Region (eu-north-1, us-east-1, ...)          isolated geographical area
      ├── Availability Zone A (eu-north-1a)       one or more data centres, own power/network
      ├── Availability Zone B (eu-north-1b)
      └── Availability Zone C (eu-north-1c)
           └── Edge locations / data caches        CloudFront, Route 53 (outside the region model)
```

Three rules worth memorizing:

1. **Regions are isolated.** No region can see another region's resources unless you
   explicitly replicate or route to them.
2. **AZs are physically separate but close.** Typically less than 100 km apart, connected
   by low-latency, redundant fibre - close enough for synchronous replication, far enough
   that a power or cooling failure does not take both down.
3. **Services are either regional or global.** S3, EC2 and RDS live in a region. IAM,
   Route 53, CloudFront and WAF are global services that you configure once.

## Quick commands

```bash
# All enabled regions for the account
aws ec2 describe-regions --query "Regions[].RegionName" --output table

# Availability Zones of the current region
aws ec2 describe-availability-zones

# Where your current credentials are pointing
aws configure get region
aws sts get-caller-identity
```
