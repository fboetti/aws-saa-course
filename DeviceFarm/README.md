# AWS Device Farm

**AWS Device Farm** is a fully managed **application testing service**. You upload your **mobile app** (Android, iOS, Fire OS) or **web app** and run tests on **real physical devices** and **desktop browsers** hosted by AWS, in parallel, without buying or maintaining a device lab. You pay per device minute (or a flat monthly fee for unmetered testing).

## Purpose

- Test apps on **hundreds of real phones and tablets** (different models, OS versions, screen sizes, manufacturers) instead of only emulators.
- Test **web apps** across **desktop browsers** (Chrome, Firefox, Edge, Safari) using **Selenium**.
- Run tests **in parallel** to get results quickly and catch device-specific bugs before release.
- **Remote access**: interact with a real device in real time through your browser to reproduce a bug.
- Integrate into **CI/CD** pipelines (CodePipeline, Jenkins, etc.).

## Core Concepts

| Concept | What it is |
|---|---|
| **Project** | Top-level workspace that holds your runs and settings. |
| **Run** | One execution of your app and tests on a chosen set of devices. |
| **Device pool** | A group of devices to test on (AWS-curated, such as "Top Devices", or your own rules by OS, model, manufacturer). |
| **Job** | One run of the tests on one device within a run. |
| **Test suite / test spec** | Your tests plus a YAML file with the commands to run them. |
| **Artifacts** | Outputs: **screenshots**, **videos**, device and test **logs**, performance data. |

## Test Types

| Type | Frameworks |
|---|---|
| **Built-in, no scripts** | **Fuzz test** (random user events: taps, gestures) to find crashes |
| **Android** | Appium (Java / Python / Node / Ruby), Espresso, instrumentation (JUnit) |
| **iOS** | Appium, XCTest, XCTest UI |
| **Web** | **Appium** / **Selenium** (TestGrid for desktop browsers) |

## How It Works

```
Upload app (.apk / .ipa) + tests ─► Choose device pool ─► Start run
        ─► Tests execute in parallel on real devices ─► Results, logs, screenshots, videos
```

- **Private devices**: you can reserve **dedicated devices** for exclusive use (e.g. unreleased builds, custom configurations).
- **Device Farm TestGrid**: runs **Selenium** tests against desktop browsers, with no device management.
- You can simulate **network conditions**, **GPS location**, locale and more, and **install extra apps** on devices.

## Pricing

- **Metered**: pay per **device minute** (first 1,000 minutes free as a one-time trial).
- **Unmetered**: flat monthly fee per device slot for unlimited testing.

## Security

- Devices are **wiped** after each test run (data removed).
- Access controlled by **IAM**.
- Can test apps that need a **private endpoint** (e.g. a backend in a VPC) through **VPC endpoint** connectivity (Amazon VPC ENI).

## Comparison

| Need | Service |
|---|---|
| Test mobile / web apps on **real devices and browsers** | **Device Farm** |
| Build / test your **code** (compile, unit tests) | **CodeBuild** |
| **Load test** backend with **simulated traffic** | Distributed load testing (not Device Farm) |
| **Synthetic canaries** monitoring a live site | **CloudWatch Synthetics** |
| Build a mobile / web app backend | **Amplify** |

## Exam Tips

- "Test a **mobile app** on **real devices** / many device and OS combinations" → **Device Farm**.
- "Test a **web app** on different **desktop browsers**" → **Device Farm** (Selenium).
- "**Fuzz** testing for crashes" → Device Farm built-in fuzz test.
- Device Farm tests your **app's behavior and UI**, not infrastructure performance.
- Can be part of a **CI/CD** pipeline, for example as a test action in **CodePipeline**.

Related: [Amplify](../Amplify/README.md), [AppSync](../AppSync/README.md), [API](../API/README.md).
