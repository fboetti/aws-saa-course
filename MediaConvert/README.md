# AWS Elemental MediaConvert

**AWS Elemental MediaConvert** is a fully managed, **file-based video transcoding** service. It converts video files stored in **S3** into formats for broadcast and multiscreen delivery (TV, web, mobile, set-top boxes), with broadcast-grade features at pay-as-you-go prices. It is the **successor of Elastic Transcoder**, which AWS discontinued.

## Purpose

- **Transcode on-demand (VOD) content**: convert source files into many formats, resolutions and bitrates.
- Create **adaptive bitrate (ABR) packages** such as **HLS**, **DASH**, **CMAF** and **Smooth Streaming** for streaming.
- Apply **video processing**: scaling, cropping, deinterlacing, watermarks / image overlays, color correction, clipping and stitching of inputs.
- Add **captions and subtitles**, multiple **audio tracks**, **thumbnails** and **timecode** metadata.
- Protect content with **DRM** and encryption.

## Core Concepts

| Concept | What it is |
|---|---|
| **Job** | One transcoding task: inputs, output groups and settings. Runs on a queue. |
| **Output group** | Defines the **type and destination** of outputs: file group (MP4, MOV), **HLS**, **DASH**, **CMAF**, **Smooth**. |
| **Output** | One rendition inside a group (codec, resolution, bitrate). |
| **Output preset** | Saved settings for an output (system presets provided, or your own). |
| **Job template** | Reusable job settings (output groups and presets) to submit many similar jobs. |
| **Queue** | Where jobs wait to run. **On-demand** (default, pay per minute) or **reserved** (fixed capacity, monthly fee). |

## How It Works

```
Source file in S3 ─► Create job (template + presets) ─► Queue ─► MediaConvert transcodes
     ─► Output in S3 ─► CloudFront (delivery)
     └► EventBridge events (status change) ─► Lambda / SNS
```

- Typical automation: **S3 upload event → Lambda (or EventBridge) → CreateJob**, then job status events through **EventBridge** → Lambda / SNS.
- Handles **multiple inputs and outputs** in a single job (e.g. one source → HLS ladder + MP4 + thumbnails).
- **Accelerated transcoding** speeds up large, high-resolution files in parallel.

## Codecs and Features

- **Video**: H.264 (AVC), **H.265 (HEVC)**, **AV1**, VP9, MPEG-2, ProRes and others.
- **Audio**: AAC, AC-3, E-AC-3, MP3, Opus and others.
- **HDR** (HDR10, Dolby Vision), 4K/8K, **frame rate conversion**, and **quality-defined variable bitrate (QVBR)** for better quality per bit.
- **Ad insertion** markers (SCTE-35), **closed captions** (CEA-608/708, WebVTT, etc.).
- Content protection with **DRM** via **SPEKE** (key providers, with **MediaPackage** or third-party DRM) and **AES** encryption for HLS.

## Pricing

- **On-demand**: pay per **output minute**, depending on resolution, codec, frame rate and tier (Basic, Professional).
- **Reserved queues**: pay a monthly fee for guaranteed transcode capacity (**RTSs**), good for steady, high-volume workloads.
- No upfront costs for on-demand.

## Security

- Needs an **IAM role** that lets MediaConvert read the input bucket and write to the output bucket.
- Encrypt with **S3 server-side encryption (KMS)**; use **HTTPS** endpoints and **IAM** for API access.
- Content protection with DRM / HLS AES encryption.

## MediaConvert vs Related Media Services

| Service | Role |
|---|---|
| **MediaConvert** | **File-based** (VOD) transcoding |
| **MediaLive** | **Live** video encoding for broadcast and streaming |
| **MediaPackage** | Packages and **originates** live and VOD streams (just-in-time packaging, DRM) |
| **MediaStore** | Media-optimized storage for live origin (being retired in favor of S3) |
| **CloudFront** | CDN to **deliver** the output to viewers |
| **Kinesis Video Streams** | Ingest video from cameras and devices for analytics / ML |
| **Amazon IVS** | Managed **low-latency live streaming** |
| **Elastic Transcoder** | Older file transcoder; **replaced by MediaConvert** |

## Exam Tips

- "**Convert / transcode video files** in S3 for multiple devices and formats" → **MediaConvert** (the successor to Elastic Transcoder).
- "**Live** video encoding" → **MediaLive**, not MediaConvert.
- Deliver the result with **CloudFront**; trigger jobs on upload with **S3 event → Lambda / EventBridge**.
- Predictable, high-volume transcoding → **reserved queues**; occasional → **on-demand**.
- Core objects: **job**, **queue**, **output group**, **preset**, **job template**; S3 in and out.
- Handles **adaptive bitrate** outputs (**HLS**, **DASH**, **CMAF**).

Related: [Elastic Transcoder](../ElasticTranscoder/README.md), [S3](../S3/README.md), [CloudFront](../CloudFront/README.md), [IAM](../IAM/README.md).
