# Network Address Usage (NAU) — Exam Notes

**Network Address Usage (NAU)** is a **metric that measures the size and complexity of a
VPC** in *units*. AWS uses it to cap how large a VPC (and the peered/attached network around
it) can grow, so that routing and network performance stay predictable. It is a **quota
planning tool**, not a billing item.

It is **separate from the IP-address count**: a VPC can hit its NAU limit long before it
runs out of CIDR space, because some resources (NAT gateways, endpoints, TGW attachments)
weigh **more than one unit**.

## How units are counted

| Resource in the VPC | NAU units |
|---|---|
| Each **IPv4 / IPv6 address** assigned to a network interface (ENI) | **1** each |
| Each **ENI** itself | **1** |
| An IP **prefix** (e.g. a /28 delegated to an ENI) | **1** per prefix, not per address |
| **NAT gateway**, **interface VPC endpoint**, **Transit Gateway attachment**, **GWLB endpoint**, **Network Firewall endpoint** | **6** each (heavier "network" resources) |

> Exact per-resource weights change; remember the idea: **IPs and ENIs count 1, managed
> network components count more (6)**, and prefix delegation counts **per prefix**.

## Quotas

| Quota | Default | Adjustable |
|---|---|---|
| **NAU per VPC** | **64,000** units | up to **256,000** |
| **NAU for peered VPCs in the same Region** (combined) | **128,000** units | up to **512,000** |

- The **peering limit applies to the sum** of all VPCs in the same Region that are directly
  **peered** together.
- VPCs connected through **Transit Gateway do not** count towards the combined peering NAU.
- Inter-Region peered VPCs are **not** added together.
- Quotas are raised through **Service Quotas** (some require AWS support).

## Monitoring

- **Off by default**: enable **Network Address Usage metrics** per VPC (console / API
  `ModifyVpcAttribute`-style setting) to publish to **CloudWatch**.
- Metrics: **`NetworkAddressUsage`** (the VPC) and **`NetworkAddressUsagePeered`** (the VPC plus its peers).
- Create a **CloudWatch alarm** (e.g. at 80%) before you hit the quota.
- Hitting the NAU limit blocks creating **new ENIs/IPs** (launching instances, endpoints, etc.) with a quota error.

```bash
# Enable NAU metrics on a VPC
aws ec2 modify-vpc-attribute --vpc-id vpc-0abc1234 --enable-network-address-usage-metrics

# Inspect the setting
aws ec2 describe-vpc-attribute --vpc-id vpc-0abc1234 --attribute enableNetworkAddressUsageMetrics
```

## Reducing NAU

- **Consolidate** NAT gateways / interface endpoints (share them via a hub VPC and **Transit Gateway**).
- Use **IP prefix delegation** for container/pod density (EKS) instead of one IP per pod.
- Split a huge VPC into several VPCs, **connected with TGW** rather than a peering mesh.
- Delete unused ENIs, endpoints and attachments.
- Right-size interface endpoints: avoid creating one endpoint per service per VPC if a shared services VPC can host them.

## NAU vs other limits — do not confuse

| | **NAU** | **CIDR / subnet IPs** | **ENI / EIP quotas** |
|---|---|---|---|
| What | Weighted "size" of VPC | Address space of subnets | Count of interfaces / Elastic IPs |
| Adjustable | Yes (Service Quotas) | CIDR is fixed; add secondary CIDRs | Yes |
| Hit when | Many ENIs/endpoints/NATs | Subnet runs out of IPs | Too many ENIs/EIPs |
| Peering effect | **Summed across peers** | None | None |

## Exam tips

- **"Metric that measures the size of a VPC"** -> **Network Address Usage (NAU)**.
- **Default 64,000 per VPC; 128,000 for peered VPCs in a Region**; adjustable up to 256,000 / 512,000.
- **Peering sums NAU; Transit Gateway does not** — a reason to choose TGW for large networks.
- NAU is **about quotas, not cost**; monitor with the **CloudWatch** metric `NetworkAddressUsage`.
- **Not enabled by default** — you must turn on the metrics.
- NAT gateways, interface endpoints and TGW attachments weigh **more than 1 unit**.
- **Prefix delegation** is a way to cut NAU for dense workloads (e.g. EKS pods).
- Adding a **secondary CIDR** adds addresses but does **not** raise the NAU quota.

## Sample questions

1. *A company hit an error creating new network interfaces in a large VPC although subnets
   still have free IPs. What quota may be reached?* -> The **Network Address Usage** quota; request an increase via **Service Quotas**.
2. *How can the team be alerted before the VPC reaches its NAU limit?* -> Enable **NAU
   metrics** and a **CloudWatch alarm** on `NetworkAddressUsage`.
3. *A large set of peered VPCs hits a combined NAU limit.* -> Raise the **peered NAU quota**,
   or move to **Transit Gateway**, which does not sum NAU.
4. *Which design reduces NAU for thousands of pods per node?* -> **Prefix delegation** on ENIs.

## References

- NAU docs: https://docs.aws.amazon.com/vpc/latest/userguide/network-address-usage.html
- VPC quotas: https://docs.aws.amazon.com/vpc/latest/userguide/amazon-vpc-limits.html
- Related notes: [VPC overview](../README.md), [VPC Peering](../vpc-peering/README.md), [Transit Gateway](../transit-gateway/README.md), [VPC Endpoints](../vpc-endpoints/README.md), [Gateways (NAT/IGW)](../gateways/README.md)
