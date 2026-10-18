# S3 Bucket Naming Rules

Because every object is addressable with a URL, the bucket name is effectively part of a public DNS name:

```
https://<bucket-name>.s3.<region>.amazonaws.com/<object-key>
       \_______/               \______/ \____________/
        bucket                region      amazonaws.com
```

Since anyone in the world can request that URL, **bucket names must be unique across all AWS accounts and all regions** — once someone registers a name, nobody else (not even in another region) can use it. This is also why bucket names double as DNS names: they can be used as CNAMEs/aliases for custom domains, so they must be DNS-compatible.

## The Rules

- **Length**: 3–63 characters.
- **Allowed characters**: lowercase letters (`a–z`), numbers (`0–9`), **dots** (`.`) and **hyphens** (`-`) only.
  - No uppercase letters (`A–Z`) — S3 forbids them.
  - No underscores (`_`), no spaces, no other special characters (slashes, `@`, `+`, etc.).
  - If the name contains dots and you need HTTPS access with a custom domain, note that `*.s3.amazonaws.com` wildcard certificates don't cover dotted names — use a wildcard certificate of your own or path-style requests.
- **Start and end**: must begin and end with a letter or number.
- **No adjacent dots**: names like `my..bucket` are rejected (to avoid confusing certificate/URL parsing).
- **Not an IP address**: names that look like `192.168.5.4` are rejected.
- **Reserved prefixes** (cannot start with):
  - `xn--` — reserved for punycode-encoded names (IDN).
  - `sthree-` — reserved by AWS for its own use.
- **Reserved suffixes** (cannot end with):
  - `-s3alias` — used for general purpose bucket *access point aliases*.
  - `--ol-s3` — used for S3 Object Lambda access point aliases.
- **Immutable name**: a bucket cannot be renamed after creation, and after deletion its name can take up to **24 hours** (sometimes longer) to become available again.

## Examples

Good names: `my-company-logs-2026`, `assets.example.com`, `backup-bucket-01`.

Bad names:

| Name | Why it fails |
|---|---|
| `MyBucket` | uppercase letters |
| `my_bucket` | underscore not allowed |
| `my bucket` | space not allowed |
| `my..bucket` | adjacent dots |
| `192.168.5.4` | looks like an IP address |
| `ab` | too short (min 3 chars) |
| `-mybucket` / `mybucket-` | starts/ends with a hyphen |

← Back to the [S3 overview](README.md)
