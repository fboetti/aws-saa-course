# EC2 Instance Types

## Naming

`m5.2xlarge` → **family** `m`, **generation** `5`, **size** `2xlarge`.
Suffix letters add attributes: `a` AMD, `g` Graviton (ARM), `i` Intel, `d` local NVMe instance store, `n` enhanced networking, `e` extra memory/storage, `b` EBS-optimised. Example: `c6gn.large` = compute, gen 6, Graviton, network-optimised.

## Families

| Family | Optimised for | Examples / use cases |
|---|---|---|
| **General purpose** — T, M, Mac | Balance of CPU/RAM/network | Web servers, small DBs, dev/test, code repos |
| **Compute optimised** — C | High CPU | Batch processing, HPC, gaming servers, media transcoding, ML inference |
| **Memory optimised** — R, X, z, High Memory | Large RAM | In-memory caches, SAP HANA, real-time big data, high-performance DBs |
| **Storage optimised** — I, D, H | High sequential/random IOPS on local disks | NoSQL, data warehousing, distributed file systems, OLTP |
| **Accelerated computing** — P, G, Inf, Trn, F | GPUs / FPGAs / ML chips | ML training, graphics, video, genomics |

Mnemonic: **T**iny burst, **M**ain/balanced, **C**ompute, **R**AM, **I**/O (storage), **G/P** GPU.

## Burstable Performance (T family)

- T2/T3/T3a/T4g earn **CPU credits** while idle and spend them when busy.
- **Standard** mode: throttled to baseline when credits run out.
- **Unlimited** mode (default for T3+): can burst beyond credits, **extra charge** applies.
- Good for spiky, low-average workloads (small websites, dev).

## Graviton

- AWS-designed **ARM** CPUs (`g` suffix, e.g. `m7g`). Better price/performance (~20-40%) and energy efficiency.
- Requires **ARM-compatible** AMI and software.

## Nitro System

- Offloads networking, storage and security to dedicated hardware → near bare-metal performance.
- Enables EBS-optimised by default, ENA, EBS NVMe, **bare metal** instances (`.metal`), enhanced security.

## Other Points

- You can **resize** an EBS-backed instance: stop → change type → start (same family/arch generally).
- **EBS-optimised**: dedicated bandwidth between instance and EBS (default on most current types).
- **Bare metal** (`.metal`): direct hardware access for licensing or special workloads.
- **Choosing**: use **Compute Optimizer** to recommend right-sizing.
