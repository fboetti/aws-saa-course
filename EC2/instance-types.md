# EC2 Instance Types

## Naming

`m5.2xlarge` → **family** `m`, **generation** `5`, **size** `2xlarge`.
Suffix letters add attributes: `a` AMD, `g` Graviton (ARM), `i` Intel, `d` local NVMe instance store, `n` enhanced networking, `e` extra memory/storage, `b` EBS-optimised. Example: `c6gn.large` = compute, gen 6, Graviton, network-optimised.

## Sizes

Order within a family: `nano` < `micro` < `small` < `medium` < `large` < `xlarge` < `2xlarge` < `4xlarge` … < `metal`.

- `large` is the baseline: **2 vCPU**. From `xlarge` upward, vCPU and RAM **double** with each step (`xlarge` = 4, `2xlarge` = 8, `4xlarge` = 16 vCPU).
- **Price doubles** with each step too, so one `2xlarge` costs about the same as two `xlarge`.
- RAM per vCPU is fixed by the family (e.g. M ≈ 4 GiB, C ≈ 2 GiB, R ≈ 8 GiB per vCPU). Changing size scales it, changing family changes the ratio.
- Network bandwidth and EBS bandwidth also grow with size. Small sizes get "up to X Gbps" burst, large ones get sustained.
- `nano`, `micro`, `small` and `medium` mostly exist in the **T** family.
- Sizes are **fixed**: you can't pick custom vCPU/RAM combinations.
- Generally when scaling up from X to X + 1, you are doubling the vCPU and RAM resources.
- Scale **up** (bigger size) = vertical scaling, which needs a stop/start. Scale **out** (more instances) = horizontal scaling, done with Auto Scaling.

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

How credits work:

- Each instance has a **baseline** CPU utilisation per vCPU (e.g. `t3.micro` ≈ 10%, `t3.small` ≈ 20%, `t3.large` ≈ 30%). Below baseline it **earns** credits, above it **spends** them.
- **1 CPU credit** = 1 vCPU at 100% for 1 minute.
- New instances get **launch credits** so they can burst right after start.
- Earned credits accrue up to a **cap** (24 hours' worth of earning) and the oldest expire first. Credits are lost on stop for **T2**, while **T3** and later keep them for a limited time after stop.
- Monitor with CloudWatch: `CPUCreditBalance` (current credits) and `CPUCreditUsage`. A balance near zero with sustained high CPU means the instance is too small. Move to a bigger T size or to **M/C**.
- **T2** defaults to Standard, **T3/T3a/T4g** default to **Unlimited**, which can raise the bill if CPU stays above baseline.
- Not suited to steady high CPU (use **M/C**) or for constant load tests, where credits run out fast.

## Processors

| Vendor | Suffix | Arch | Notes |
|---|---|---|---|
| **Intel** (Xeon) | `i` or none (e.g. `m6i`, `m5`) | x86_64 | Default; widest software compatibility |
| **AMD** (EPYC) | `a` (e.g. `m6a`) | x86_64 | ~10% cheaper than Intel equivalent |
| **AWS Graviton** | `g` (e.g. `m7g`) | **ARM64** | Best price/performance, see below |

- Intel and AMD share the **x86_64** architecture, so the same AMI works on both.
- Switching between x86 and ARM needs a **different AMI** (an AMI is architecture-specific).
- Other chips: **Trainium / Inferentia** (`trn`, `inf`) for ML training / inference; **Mac** instances run Apple silicon.

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
