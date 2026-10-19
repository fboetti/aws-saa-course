# AWS Regions

A **region** is a separate geographical area containing multiple Availability Zones.
Every resource you launch - an EC2 instance, an S3 bucket, a database - lives in exactly
one region.

## Anatomy of a region name

`eu-north-1` = `<geo>`-`<place>`-`<number>`

| Part    | Example | Meaning                                      |
|---------|---------|----------------------------------------------|
| `eu`    | geo     | Geographic area: `us`, `eu`, `ap`, `sa`, `ca`, `me`, `af` |
| `north` | place   | Directional qualifier inside that area       |
| `1`     | number  | Instance number of that region (older regions drop the place part: `us-east-1`) |

The **region code** (`eu-north-1`) is what you put in `AWS_DEFAULT_REGION`, in Terraform
`provider "aws" { region = ... }`, and in resource ARNs.

The **console name** (`Europe (Stockholm)`) is only for humans.

## What a region guarantees

- **Data residency** - data stored in the region stays in that geographic area unless you
  choose otherwise. This is the driver behind sovereignty and compliance requirements.
- **Service isolation** - an outage or an API throttle in one region does not affect
  another.
- **Independent pricing** - AWS prices services per region, so the same EC2 instance type
  costs different amounts in `us-east-1` versus `ap-southeast-3`.

## Things that are *not* in a region

- **Edge locations** - the CloudFront / Route 53 / Global Accelerator points of presence
  that sit in front of regions (hundreds of them worldwide).
- **AWS Global Accelerator anycast** - routes users to the nearest healthy region.
- **IAM** - a single global account-wide service.

## Choosing a region (a typical exam question)

Weigh these factors in roughly this order:

1. **Compliance / data residency** - does the law require the data to stay in a country or
   bloc (GDPR, data localization)? If yes, this decides the region for you.
2. **Proximity to users** - lower latency. Pick the region closest to the majority of
   traffic.
3. **Service availability** - not every AWS service launches in every region at the same
   time. Verify with the [AWS Regional Services list](https://aws.amazon.com/about-aws/global-infrastructure/regional-product-services/).
4. **Cost** - prices vary by region; `us-east-1` is usually the cheapest.
5. **Resilience strategy** - the primary region must have at least two AZs (all current
   regions do) if you want multi-AZ designs.

## Useful commands

```bash
# List regions with their opt-in status
aws ec2 describe-regions --all-regions \
  --query "Regions[?RegionStatus!='opt-in-not-required'].[RegionName,RegionStatus]" \
  --output table

# What is the current region?
aws configure get region
echo $AWS_REGION

# Per-region service availability
aws ec2 describe-regions --region-names eu-north-1 us-east-1
```

## Exam traps

- The account must **opt in** to most regions outside `us-east-1`, `us-west-2` and
  `eu-west-1` before they can be used.
- A resource is regional by default; "global" resources (IAM users, Route 53 hosted zones,
  CloudFront distributions) are exceptions you have to memorize.
- Moving between regions means **copying or replicating** - there is no automatic
  cross-region movement of data.

Next: [Availability Zones](../availability-zones/README.md)
