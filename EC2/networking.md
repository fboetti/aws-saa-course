# EC2 Networking

Instances live in a **subnet** of a [VPC](../VPC/README.md), in one AZ.

## IP Addresses

| Type | Behaviour |
|---|---|
| **Private IPv4** | Fixed for the instance's lifetime (survives stop/start); within VPC CIDR |
| **Public IPv4** | Auto-assigned (if subnet allows); **changes on stop/start**; charged hourly since 2024 |
| **Elastic IP (EIP)** | Static public IPv4 owned by your account; remap between instances; charged (also when idle); max 5 per region by default |
| **IPv6** | Globally unique, public by default; no NAT needed |

Prefer a **DNS name / load balancer** over Elastic IPs where possible.

## Elastic Network Interface (ENI)

- Virtual network card: one primary private IPv4, optional secondary IPs, EIP, security groups, MAC address, source/destination check flag.
- Created independently; can be **attached/detached** to instances in the **same AZ** → useful for failover (move ENI and its IP to a standby).
- Each instance has a primary ENI (eth0) that cannot be detached.
- Number of ENIs/IPs depends on instance type.

## Enhanced Networking

- **ENA** (Elastic Network Adapter): up to 100 Gbps.
- **EFA** (Elastic Fabric Adapter): ENA plus OS-bypass, for HPC/MPI/ML (Linux only), lowest latency.
- Intel 82599 VF (legacy, 10 Gbps).

## Source/Destination Check

- A per-ENI (per-instance in the console) flag, **enabled by default**.
- When enabled, the instance must be **the source or the destination of every packet** it sends or receives. Traffic that is merely passing through is dropped.
- **Disable it** when the instance forwards traffic that is not addressed to or from itself:
  - **NAT instance** (the classic exam case: private subnet traffic is forwarded to the internet)
  - Routers, VPN gateways, firewall or IDS/IPS appliances, load balancing or proxy appliances
  - Instances that are a **route table target** for a CIDR they don't own
- Change it any time, even while running: console **Actions → Networking → Change source/destination check**, or `aws ec2 modify-network-interface-attribute --network-interface-id eni-... --no-source-dest-check`.
- Disabling does **not** change security groups or NACLs, which still apply. A NAT instance also needs a public IP/EIP, an SG allowing the private subnet's traffic, and a route `0.0.0.0/0 → instance` in the private route table.
- **NAT Gateway** is managed, so you don't touch this flag. This is one reason it replaces NAT instances.
- Symptom of a forgotten check: the NAT or firewall instance is reachable and healthy, but private instances get no internet or traffic is silently dropped.

## Placement Groups

| Strategy | Layout | Pros | Cons / Limits | Use |
|---|---|---|---|---|
| **Cluster** | Same rack/AZ, close together | Lowest latency, 10+ Gbps | Single AZ, all fail together | HPC, big data jobs needing fast network |
| **Spread** | Each instance on distinct hardware | Reduced correlated failure; can span AZs | Max **7 instances per AZ per group** | Small critical apps |
| **Partition** | Groups of racks (partitions), up to 7 per AZ | Isolates failures per partition; hundreds of instances | Partition-aware apps | Hadoop, Cassandra, Kafka |

## Connectivity Notes

- Internet access needs: public IP/EIP + **Internet Gateway** + route in route table (public subnet).
- Private subnets reach the internet via a **NAT Gateway**.
- Disable **source/destination check** on NAT instances / routers / firewall appliances.
- **Instance in a different VPC** → VPC peering, Transit Gateway, PrivateLink.
- Data transfer: in is free; within AZ (private IP) free; cross-AZ and out to the internet cost money.

## Exam Tips

- "Low-latency node-to-node" → cluster placement group + ENA/EFA.
- "Failover keeping the same IP/MAC (licensing)" → move ENI.
- "Static IP that survives stop/start" → Elastic IP.
- "NAT instance / firewall appliance not forwarding traffic" → **disable source/destination check**.
