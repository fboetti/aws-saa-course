# EC2 Purchasing Options

| Option | Commitment | Discount vs On-Demand | Best for |
|---|---|---|---|
| **On-Demand** | None, per-second billing | 0% | Short, unpredictable, first-time workloads |
| **Reserved Instances (Standard)** | 1 or 3 years | up to ~72% | Steady-state, predictable usage |
| **Reserved Instances (Convertible)** | 1 or 3 years | up to ~66% | Steady-state but may change family/OS/tenancy |
| **Savings Plans** | $/hour for 1 or 3 years | up to ~72% | Flexible steady spend |
| **Spot Instances** | None; can be interrupted | up to ~90% | Fault-tolerant, flexible, stateless jobs |
| **Dedicated Hosts** | On-Demand or 1/3 yr reservation | varies | BYOL, compliance, per-socket/core licensing |
| **Dedicated Instances** | On-Demand | extra fee | Hardware not shared with other accounts |
| **Capacity Reservations** | None (billed whether used or not) | 0% (combine with RI/SP) | Guaranteed capacity in a specific AZ |

## Reserved Instances

- Attributes: instance type, region (or AZ), tenancy, OS.
- **Payment**: All Upfront (best), Partial Upfront, No Upfront.
- **Regional RI**: discount applies across AZs, size flexibility (Linux). **Zonal RI**: reserves capacity in an AZ.
- Sell unused Standard RIs on the **Reserved Instance Marketplace**.

## Savings Plans

- **Compute Savings Plan**: any instance family/size/region/OS, also Fargate and Lambda. Most flexible (~66%).
- **EC2 Instance Savings Plan**: fixed family + region, flexible size/OS/tenancy (~72%).
- Commit to $ per hour of usage; overflow is billed On-Demand.

## Spot Instances

- Uses spare capacity; **2-minute interruption notice** when AWS needs it back (or price exceeds your max).
- Pay the current **spot price**; you set an optional max price.
- Request types: **one-time** or **persistent**; behaviour on interruption: terminate, stop, hibernate.
- **Spot Fleet** / **EC2 Fleet**: pool of Spot (+ On-Demand) capacity with allocation strategies (`lowestPrice`, `capacityOptimized`, `diversified`, `priceCapacityOptimized`).
- **Spot Block** (fixed duration 1–6 hours) is discontinued.
- Not for: databases, critical jobs. Great for: batch, CI/CD, big data, containers (ECS/EKS), image rendering.

## Dedicated Hosts vs Dedicated Instances

| | Dedicated Host | Dedicated Instance |
|---|---|---|
| Physical server | Whole server for you, visibility of sockets/cores/host ID | Hardware dedicated, no host control |
| Licensing (BYOL) | Yes (socket/core/VM-based licences) | No |
| Placement control | Yes (affinity to host) | No |

## Exam Tips

- "Steady 24/7 for 1-3 years" → **Reserved/Savings Plan**.
- "Can tolerate interruption, lowest cost" → **Spot**.
- "Server-bound software licence" → **Dedicated Host**.
- "Guaranteed capacity in one AZ" → **On-Demand Capacity Reservation**.
- "Unpredictable, short-term, can't be interrupted" → **On-Demand**.
