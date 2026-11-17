# Amazon Elastic Transcoder

**Amazon Elastic Transcoder** is a managed **media transcoding** service: it converts media files stored in **S3** from their original format into versions suited to playback on phones, tablets, browsers and TVs. You pay only for the minutes of video (or audio) you transcode.

> **Note:** AWS ended support for Elastic Transcoder on **November 13, 2025**, and recommends **AWS Elemental MediaConvert** instead. The concepts still appear in older SAA course material, and the exam answer for "transcode media files" is now **MediaConvert**.

It cannot be used with CFN (Cloud Formation)

## Purpose

- Convert **video and audio** files into multiple formats, bitrates and resolutions.
- Generate output for different devices (e.g. MP4/H.264 for mobile, HLS/MPEG-DASH for adaptive streaming).
- Add **thumbnails**, **watermarks**, captions and clip/trim files.

## Core Concepts

| Concept | What it is |
|---|---|
| **Pipeline** | A queue that manages transcoding jobs. Defines the **input S3 bucket**, **output S3 bucket**, IAM role and **SNS** notifications. |
| **Job** | One transcoding task: converts an input file using a preset. Runs in a pipeline. |
| **Preset** | Template of transcoding settings (codec, resolution, bitrate, frame rate). AWS provides **system presets**; you can create your own. |
| **Notifications** | **SNS** topics for job progress, completion, warnings and errors. |

## How It Works

```
Upload source file ─► S3 input bucket ─► Create job (pipeline + preset)
      ─► Elastic Transcoder converts ─► S3 output bucket ─► (CloudFront delivery)
                                      └► SNS notification
```

- **Automation**: S3 upload event → **Lambda** → create Elastic Transcoder job (today: → MediaConvert).
- Supports **multiple outputs per job** (several resolutions and formats from one input).
- Pair with **CloudFront** to deliver the converted media globally.

## Security

- The pipeline uses an **IAM role** to read from the input bucket and write to the output bucket.
- Output can be **encrypted** (S3 server-side encryption, KMS) and content protected with **DRM / HLS encryption**.

## Replacement: AWS Elemental MediaConvert

| | **Elastic Transcoder** (discontinued) | **MediaConvert** |
|---|---|---|
| Status | Support ended Nov 2025 | **Current** |
| Formats and features | Basic | Broader codecs (**HEVC**, **AV1**), **HDR**, captions, ad insertion, DRM |
| Pricing | Per minute | Per minute, with on-demand and reserved queues |
| Queues | Pipelines | **Queues** (on-demand or reserved) |

Related media services: **MediaLive** (live video encoding), **MediaPackage** (packaging and origination), **Kinesis Video Streams** (streaming from devices), **IVS** (live streaming).

## Exam Tips

- "**Convert media files** (video / audio) stored in S3 into formats for different devices" → **Elastic Transcoder** (older exams) or **MediaConvert** (current).
- Components to remember: **pipeline**, **job**, **preset**, with **S3** in and out and **SNS** notifications.
- "Trigger transcoding when a file is uploaded" → **S3 event → Lambda → transcoding job**.
- "**Live** video encoding" → **MediaLive**, not a file-based transcoder.
- Deliver the transcoded output with **CloudFront**.

Related: [S3](../S3/README.md), [CloudFront](../CloudFront/README.md), [IAM](../IAM/README.md).
