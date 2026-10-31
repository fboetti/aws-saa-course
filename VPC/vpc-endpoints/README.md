# VPC Endpoints and PrivateLink — Exam Notes

A **VPC endpoint** lets resources in a VPC reach an AWS service (or a service hosted by
someone else) **privately**, over the AWS network, **without** an Internet Gateway, NAT
device, VPN or Direct Connect, and without public IP addresses.

```
 Without endpoint:  EC2 (private) ──> NAT GW ──> IGW ──> internet ──> S3
 With endpoint:     EC2 (private) ───────────── AWS network ────────> S3
```

## Purpose

- **Security:** traffic never touches the public internet; instances need no public IP.
- **Cost:** a gateway endpoint is free and removes **NAT Gateway** data-processing charges.
- **Control:** endpoint policies restrict *which* resources/actions are reachable.
- **Compliance:** keeps data on the AWS backbone.
- **Service sharing:** PrivateLink exposes your service to other VPCs/accounts safely.

## The Three Endpoint Types

| | **Gateway endpoint** | **Interface endpoint** (PrivateLink) | **Gateway Load Balancer endpoint** |
|---|---|---|---|
| Services | **S3, DynamoDB** only | 100+ AWS services, your own, partner/SaaS | Third-party security/inspection appliances |
| Mechanism | **Route table** entry (prefix list → `vpce-…`) | **ENI** with a private IP in your subnet | Endpoint in a subnet, used as a route **target** |
| Backed by | AWS (no resource in your subnet) | **AWS PrivateLink** | **GWLB** in the provider VPC |
| Security | **Endpoint policy** (+ bucket policy) | Endpoint policy **+ security group** | Route tables, NACLs |
| DNS | Normal service name; routing does the work | **Private DNS** resolves the service name to the ENI IPs | n/a |
| Access from on-premises / peered VPC / other Region | **No** | **Yes** (DX, VPN, peering, TGW) | Inspection path inside AWS |
| Cost | **Free** | Per **hour per AZ** + per **GB** | Per hour + per GB |
| Scope | VPC, **same Region** as the service | VPC, AZ-specific ENIs | VPC |

## Gateway Endpoints (S3 and DynamoDB)

- Created in a VPC and **associated with route tables**; AWS adds a route whose destination
  is the service **prefix list** (`pl-…`) and target the endpoint (`vpce-…`).
- **Free**, highly available, scaled by AWS.
- Only reachable from **inside the VPC** — **not** from on-premises, a peered VPC, or
  another Region.
- Same-Region only: the endpoint and the S3 bucket must be in the **same Region**.
- Control access with the **endpoint policy** and with the **S3 bucket policy**, using
  `aws:sourceVpce` or `aws:sourceVpc` conditions to force traffic through the endpoint.
- Works with the **private IP** of the instance; uses the public service DNS name.

```
 Private subnet route table
   10.0.0.0/16      → local
   pl-68a54001 (S3) → vpce-0abc1234      ← added by the gateway endpoint
```

## Interface Endpoints (AWS PrivateLink)

- An **elastic network interface (ENI)** with a **private IP** in each subnet (AZ) you
  select; the service is reached at that IP.
- **Private DNS** (`enableDnsSupport` + `enableDnsHostnames` on the VPC) makes the usual
  service name, for example `sqs.eu-west-1.amazonaws.com`, resolve to the endpoint ENIs.
- Protected by a **security group** (allow inbound 443 from clients) plus an **endpoint
  policy**.
- **Not tied to a route table** entry: traffic reaches the ENI over the `local` route.
- Reachable from **on-premises** (Direct Connect or VPN), **peered VPCs** and **Transit
  Gateway**.
- Deploy in **multiple AZs** for resilience; each AZ ENI is billed per hour.
- **S3 is available both ways:** gateway endpoint (free, in-VPC only) and interface endpoint
  (paid, reachable from on-premises).

## PrivateLink for Your Own Services

```
 Provider VPC                            Consumer VPC(s)
 ┌────────────────────────┐            ┌─────────────────────┐
 │ service ◄─ NLB/GWLB ◄──┼─ endpoint ─┤ interface endpoint  │
 └────────────────────────┘   service  └─────────────────────┘
```

- The provider puts a **Network Load Balancer** (or **Gateway Load Balancer**) in front of
  the service and creates an **endpoint service**.
- Consumers create an **interface endpoint** to it, optionally after provider approval.
- **One-directional** (consumer → provider), **no peering**, **no route tables**, no IGW.
- **Overlapping CIDRs are fine** — only the ENI IP in the consumer VPC is used.
- The right answer for "expose one service to hundreds of VPCs or customers" without
  exposing the whole network.

## Endpoint Policies

- A **resource-based IAM policy** attached to the endpoint that limits what can be done
  **through it** (for example only `s3:GetObject` on one bucket).
- The **default policy allows everything**.
- It is **in addition** to IAM policies and bucket policies — it never grants access on its
  own; the effective access is the intersection.
- Common pattern: bucket policy with `"aws:sourceVpce": "vpce-…"` to say "only reachable via
  this endpoint".

## Endpoints vs Other Connectivity

| Need | Choice |
|---|---|
| Private instances need S3/DynamoDB, cheapest | **Gateway endpoint** |
| On-premises must reach S3 privately over DX/VPN | **S3 interface endpoint** |
| Private access to SQS, SNS, KMS, Secrets Manager, ECR, SSM… | **Interface endpoint** |
| Internet access for updates (patches, any website) | **NAT Gateway** |
| Share one internal service with many VPCs/accounts | **PrivateLink (NLB + endpoint service)** |
| Connect two whole networks | **Peering / Transit Gateway** |
| Insert a third-party firewall in the path | **GWLB endpoint** |

## Exam Facts (SAA-C03)

- Endpoint = **private connection to a service**, no IGW, NAT, VPN or public IP needed.
- **Gateway endpoint: S3 and DynamoDB only, free, route table entry.**
- **Interface endpoint: ENI + private IP, PrivateLink, paid, security group.**
- Gateway endpoints are **not reachable from on-premises, other Regions or peered VPCs**;
  interface endpoints **are**.
- Gateway endpoints are **Regional**: same Region as the service.
- **Endpoint policies** restrict actions/resources; the default allows all.
- **Bucket policy** with `aws:sourceVpce` forces S3 access through a given endpoint.
- **PrivateLink = NLB/GWLB + endpoint service + interface endpoint**; works with
  **overlapping CIDRs**.
- Interface endpoints need **DNS support + hostnames** enabled for private DNS names.
- **NAT Gateway is not required** to reach AWS services if endpoints exist.
- Endpoints are **highly available** (AWS-managed); for interface endpoints deploy in
  **several AZs**.

### Scenario → Answer

| Scenario | Answer |
|---|---|
| EC2 in a private subnet must write to S3 with no internet access and lowest cost | **S3 gateway endpoint** |
| Cut NAT Gateway data-processing bill for S3/DynamoDB traffic | **Gateway endpoint** |
| On-premises servers must access S3 over Direct Connect without the internet | **S3 interface endpoint** (public VIF is the alternative) |
| Lambda in a VPC must call SQS/KMS/Secrets Manager with no NAT | **Interface endpoint** |
| Only one S3 bucket should be reachable from the VPC | **Endpoint policy** |
| Bucket must only accept requests from the VPC | **Bucket policy** with `aws:sourceVpce` / `aws:sourceVpc` |
| SaaS vendor must serve customers' VPCs privately | **PrivateLink** (NLB + endpoint service) |
| Customers have overlapping CIDRs with your service | **PrivateLink**, not peering |
| Route all VPC egress through a third-party firewall | **GWLB endpoint** |
| Gateway endpoint exists but traffic still goes via NAT | Check the **route table association** / prefix-list route |

## Exam Traps

- **"S3 and DynamoDB" = gateway endpoint** (free). Anything else = interface endpoint.
- **Gateway endpoints need route table associations**; creating one but forgetting the
  subnets' tables does nothing.
- **A gateway endpoint can't be used from on-premises** — use an interface endpoint.
- **Interface endpoints cost money** (per hour per AZ + data) — don't pick them for plain
  in-VPC S3/DynamoDB when free gateway is enough.
- **Endpoint policy ≠ permission.** It only limits; IAM must still allow.
- **Security groups apply to interface endpoints**, not gateway endpoints.
- **Private DNS needs DNS support and hostnames** enabled on the VPC.
- **PrivateLink is one-way** and doesn't connect networks.
- **Not for the internet.** Endpoints reach AWS/partner services; arbitrary internet sites
  still need a NAT Gateway.
- **Cross-Region:** gateway endpoints can't reach buckets in another Region; use interface
  endpoints with inter-Region connectivity or other designs.

## Commands

```bash
# Gateway endpoint for S3, associated with route tables
aws ec2 create-vpc-endpoint --vpc-id vpc-0abc1234 \
  --service-name com.amazonaws.eu-west-1.s3 --vpc-endpoint-type Gateway \
  --route-table-ids rtb-0priv1234

# Interface endpoint for SQS with private DNS
aws ec2 create-vpc-endpoint --vpc-id vpc-0abc1234 \
  --service-name com.amazonaws.eu-west-1.sqs --vpc-endpoint-type Interface \
  --subnet-ids subnet-0a1111 subnet-0b2222 --security-group-ids sg-0endpt1234 \
  --private-dns-enabled

# Restrict an endpoint with a policy
aws ec2 modify-vpc-endpoint --vpc-endpoint-id vpce-0abc1234 \
  --policy-document file://endpoint-policy.json

# List endpoints and available service names
aws ec2 describe-vpc-endpoints \
  --query 'VpcEndpoints[].[VpcEndpointId,VpcEndpointType,ServiceName,State]' --output table
aws ec2 describe-vpc-endpoint-services --query 'ServiceNames' --output text

# Delete
aws ec2 delete-vpc-endpoints --vpc-endpoint-ids vpce-0abc1234
```

## Study Checklist

- [ ] Say which services gateway endpoints support, and what they cost.
- [ ] Contrast gateway and interface endpoints on mechanism, security, reachability, cost.
- [ ] Explain how a gateway endpoint appears in a route table.
- [ ] Choose gateway vs interface endpoint for S3 access from the VPC and from on-premises.
- [ ] Describe PrivateLink with NLB + endpoint service, and why overlapping CIDRs are fine.
- [ ] Write a bucket policy condition using `aws:sourceVpce`.
- [ ] Decide between endpoint, NAT Gateway and peering for a given requirement.

## References

- AWS docs — VPC endpoints: https://docs.aws.amazon.com/vpc/latest/privatelink/vpc-endpoints.html
- AWS docs — Gateway endpoints: https://docs.aws.amazon.com/vpc/latest/privatelink/gateway-endpoints.html
- AWS docs — Interface endpoints: https://docs.aws.amazon.com/vpc/latest/privatelink/create-interface-endpoint.html
- Related notes: [VPC overview](../README.md#vpc-endpoints-and-privatelink), [Gateways](../gateways/README.md), [Route Tables](../route-tables/README.md), [Security Groups](../security-groups/README.md), [Direct Connect](../direct-connect/README.md)
