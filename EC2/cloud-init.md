# Cloud-Init

**cloud-init** is the industry-standard, open-source (Canonical) package that initialises cloud instances at boot. It is preinstalled on Amazon Linux, Ubuntu, and most other cloud AMIs. It is what actually **executes EC2 [user data](user-data-metadata.md)**.

## What It Does

At first boot (and optionally later boots) it reads data from the instance's datasource (on EC2: the [metadata service](user-data-metadata.md#instance-metadata-service-imds)) and configures the machine:

- Set hostname, create users, inject SSH keys
- Install packages, run commands
- Write files, mount volumes, configure networking
- Run user-data shell scripts

## Boot Stages

| Stage | Purpose |
|---|---|
| **Local** | Find datasource, apply network config |
| **Network** (`init`) | Set up disks/filesystems, fetch user data |
| **Config** | Run `cloud_config_modules` (packages, users, etc.) |
| **Final** | Run `cloud_final_modules`: user-data scripts, `runcmd`, final messages |

## User Data Formats

cloud-init detects the format from the first line:

| Starts with | Type |
|---|---|
| `#!` (e.g. `#!/bin/bash`) | Shell script, run once at first boot |
| `#cloud-config` | YAML declarative config |
| `Content-Type: multipart/mixed` | Mix several parts (script + cloud-config) |
| `#cloud-boothook` | Runs very early, on **every** boot |
| `#include` | List of URLs to fetch |

### Example: `#cloud-config`

```yaml
#cloud-config
package_update: true
packages:
  - httpd
write_files:
  - path: /var/www/html/index.html
    content: Hello from cloud-init
runcmd:
  - systemctl enable --now httpd
users:
  - name: deploy
    sudo: ALL=(ALL) NOPASSWD:ALL
    ssh_authorized_keys:
      - ssh-ed25519 AAAA...
```

Declarative config is more readable and idempotent than a long bash script.

## Run-Once Behaviour

- Scripts run **once per instance ID**; stored state lives in `/var/lib/cloud/`.
- To rerun: `sudo cloud-init clean --logs && sudo reboot` (or per-module frequency settings, e.g. `scripts-user: always`).
- An AMI built from a used instance keeps old state unless you `cloud-init clean` first.

## Debugging

| Path / command | Content |
|---|---|
| `/var/log/cloud-init-output.log` | stdout/stderr of your user-data script |
| `/var/log/cloud-init.log` | cloud-init's own detailed log |
| `cloud-init status --long` | Done / running / error |
| `cloud-init schema --system` | Validate `#cloud-config` YAML |

## Exam Tips

- User data on Linux AMIs is processed by **cloud-init**; on Windows by **EC2Launch**.
- cloud-init needs no SSH and no manual access, so it fits Auto Scaling launch templates.
- Heavy installs make launches slow: prefer a pre-baked [AMI](amis.md).
