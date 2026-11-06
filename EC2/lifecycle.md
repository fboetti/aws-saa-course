# EC2 Instance Lifecycle and Actions

States are summarised in the [README](README.md#instance-lifecycle). This note covers what each **action** does.

## Actions at a Glance

| Action | State change | Same host? | Instance store | Public IPv4 | Billing |
|---|---|---|---|---|---|
| **Launch** | → pending → running | n/a | Empty | Assigned (if enabled) | Starts (per second, 60 s minimum) |
| **Reboot** | stays running | Yes | Kept | Kept | Unchanged |
| **Stop** | → stopping → stopped | Released | **Lost** | **Released** | Compute stops; EBS and Elastic IP still billed |
| **Start** | stopped → pending → running | Usually new | Empty | New (unless Elastic IP) | Compute resumes |
| **Hibernate** | → stopping → stopped | Released | **Lost** | Released | Like stop; RAM saved to EBS |
| **Terminate** | → shutting-down → terminated | n/a | **Lost** | Released | Stops |
| **Retire** | AWS-scheduled stop or terminate | n/a | Lost on terminate | n/a | n/a |
| **Recover** | Moved to new hardware | New | **Lost** | Kept | Unchanged |

## Launch

- API call is `RunInstances`. Instance goes **pending** (allocating host, attaching volumes/ENI) then **running**.
- **User data** runs at first boot only (by default). See [User Data and Metadata](user-data-metadata.md).
- Launch fails with `InsufficientInstanceCapacity` if AWS has no capacity of that type in the AZ. Retry later, try another AZ or type, or use a **Capacity Reservation**.
- Also fails when the vCPU **service quota** is reached.

## Reboot

- OS-level restart, instance stays in **running**. Same host, same IPs, **instance store data kept**, EBS stays attached.
- Does **not** start a new billing period.
- Use for OS patches or hung processes. Does not fix hardware (system status check) problems.

## Stop and Start

- Only **EBS-backed** instances can be stopped. Instance store-backed ones can only be rebooted or terminated.
- On stop: RAM is gone, instance store data is **lost**, public IPv4 is released, **private IPv4 and IPv6 are kept**, Elastic IP stays associated.
- On start: instance usually lands on a **new host**.
- Stopped is the only state where you can change **instance type**, **user data**, **kernel/RAM disk** and some attributes.
- **Shutdown behaviour**: an OS-initiated shutdown (`shutdown -h`) either **stops** (default) or **terminates** the instance, depending on the `InstanceInitiatedShutdownBehavior` attribute.
- **Stop protection** (`DisableApiStop`) blocks the stop API.

## Hibernate

- Saves RAM to the root EBS volume, then stops. On start, RAM is restored and processes resume.
- Needs: hibernation enabled **at launch**, **encrypted** root volume, supported types, RAM under 150 GB, max 60 days.
- Good for long-running processes with slow warm-up (caches, in-memory data).

## Terminate

- Permanent. Instance goes **shutting-down** then **terminated**, and stays visible in the console for about an hour.
- Root EBS volume is deleted by default (`DeleteOnTermination` = true). **Additional EBS volumes are kept** by default.
- **Termination protection** (`DisableApiTermination`) blocks console/API termination only. It does **not** stop:
  - Auto Scaling scale-in. Use **instance scale-in protection** instead.
  - An OS shutdown when shutdown behaviour is set to terminate.
- Spot instances are terminated or stopped/hibernated by AWS on interruption (2-minute warning).

## Retire (scheduled events)

- When the underlying host is degrading, AWS schedules **retirement** and sends a notice through the **Health Dashboard** and email, with several days' lead time.
- **EBS-backed**: AWS **stops** the instance at the deadline. Do a **stop/start yourself earlier** to move to healthy hardware on your own schedule.
- **Instance store-backed**: AWS **terminates** it, so you must replace it yourself. Data is lost.
- Other scheduled events: **reboot** (host maintenance) and **maintenance**. A plain reboot of an instance with a scheduled reboot event does not clear the event, but a stop/start does.

## Recover

- Triggered when the **system status check** fails (hardware, power, network or hypervisor problem on AWS's side).
- Instance is moved to **new hardware** and keeps its **instance ID, private IPs, Elastic IPs and metadata**. It is in the same AZ, so it is a reboot-like experience. **RAM contents and instance store data are lost.**
- **Simplified automatic recovery** is on by default for supported types.
- You can also set a **CloudWatch alarm** on `StatusCheckFailed_System` with the **Recover** action.
- Not available for instance store-backed instances or Dedicated Hosts on older types.

### Status checks

| Check | Detects | Typical fix |
|---|---|---|
| **System status** | AWS-side hardware or network problem | **Recover** (or stop/start) |
| **Instance status** | Your OS or config: bad network config, full disk, kernel panic | **Reboot** or fix the OS |
| **Attached EBS status** | Volume I/O stalls | Check the volume |

## Console Screenshot and Output

For troubleshooting an instance you can't reach (SSH/RDP fails, instance check failing):

- **Get instance screenshot** (console: Actions → Monitor and troubleshoot): an image of what the instance's "screen" shows right now. Useful for Windows (blue screen, stuck on login or boot) and for Linux stuck at boot or a GRUB prompt.
- **Get system log** (console output): the text boot log. Shows kernel panics, failed mounts and cloud-init errors on Linux.
- Both work **without network access** to the instance, because they come from the hypervisor.
- Screenshot is available only for **running** instances on Nitro-based types. It is not a live view, and you can't type into it. For input, use the **EC2 Serial Console** (Nitro types).
- API calls: `GetConsoleScreenshot` and `GetConsoleOutput`.

## Exam Tips

- **Reboot** keeps everything. **Stop/start** loses instance store and public IP. **Recover** keeps IDs and IPs but loses RAM.
- System check fails → **recover**. Instance check fails → **reboot**.
- Retirement notice on an EBS-backed instance → **stop and start** it to migrate before the deadline.
- "Data must survive termination" → non-root EBS volume, or set `DeleteOnTermination` to false.
- "Prevent accidental termination" → **termination protection**. For ASG instances → **scale-in protection**.
- "Preserve in-memory state across stop" → **hibernate**.
