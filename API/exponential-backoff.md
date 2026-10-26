# Exponential Backoff (API Retries)

When an AWS API call fails with a **retryable** error, wait before retrying and **double the wait after each attempt** — e.g. 1 s, 2 s, 4 s, 8 s … — instead of hammering the service. This gives a throttled or overloaded backend time to recover and prevents your own retries from making the problem worse.

## The algorithm

```text
wait = min(cap, base * 2^attempt)          # exponential, capped
sleep(random_between(0, wait))             # "full jitter"
stop after max_attempts and surface the error
```

- **Exponential** — the wait doubles each attempt, so pressure on the service drops quickly.
- **Capped** — limit both the single wait (e.g. 20 s) and the number of attempts (e.g. 3–5), then fail fast rather than retrying forever.
- **Jitter** — randomize each delay. Without it, all clients that failed together retry together, in lockstep, and hit the recovering service as a **thundering herd**. *Full jitter* (random between 0 and the backoff) spreads load best.

## What to retry

Decide by **error code**, not just by HTTP status class:

| Retry | Don't retry |
|---|---|
| `500`, `502`, `503`, `504` — server-side / transient | `400` validation errors (`ValidationException`, malformed request) |
| **Throttling** — `ThrottlingException`, `Throttling`, `RequestLimitExceeded`, `TooManyRequestsException` (`429`), `ProvisionedThroughputExceededException`, `RequestThrottledException` | `403` `AccessDenied` / `UnauthorizedOperation` — a permission problem, not a transient one |
| S3 `503 SlowDown` | `404` `NoSuchKey`, `ResourceNotFoundException` |
| Timeouts, connection resets, DNS failures | `409` conflicts that need different input |

Note that many AWS throttling errors come back as **HTTP 400** with a throttling error code — "never retry 4xx" is wrong for AWS. Expired credentials (`ExpiredToken`) are not retried as-is either: refresh the credentials first, then retry.

## Idempotency

Retries are safe only if repeating the call does not repeat its side effects. Reads (`Get*`, `Describe*`, `List*`) are idempotent; many writes are not. AWS APIs that create things offer a **client token** (`ClientToken` on `RunInstances`, `ClientRequestToken` on many others): send the same token on every retry and the service performs the action once.

## You usually don't implement it yourself

The AWS SDKs and the CLI already retry with exponential backoff and jitter. The retry mode is configurable (`retry_mode` / `max_attempts` in `~/.aws/config`, or `AWS_RETRY_MODE` / `AWS_MAX_ATTEMPTS`):

| Mode | Behaviour |
|---|---|
| `legacy` | Older per-SDK behaviour; still the default in some SDKs (e.g. boto3) |
| `standard` | Consistent across SDKs; **3 attempts** total by default, exponential backoff with jitter; default in CLI v2 |
| `adaptive` | `standard` + **client-side rate limiting** that slows the client down when it sees throttling |

Write your own retry loop only for raw HTTP calls or for retrying a whole business operation.

## Related resilience patterns

- **Decouple with SQS**: queue the work so bursts are absorbed and consumers process at the rate the backend can sustain.
- **Dead-letter queues (DLQ)**: messages that keep failing after the retry limit go to a DLQ for inspection instead of blocking the queue.
- **Step Functions** `Retry` blocks (`IntervalSeconds`, `BackoffRate`, `MaxAttempts`) give declarative exponential backoff for workflow steps.
- **Lambda async invocations** retry twice automatically, then send failures to a DLQ or an on-failure destination.
- Backoff fixes **transient** pushback. If throttling is constant, the real fix is capacity: request a quota increase, switch DynamoDB to **on-demand** or raise provisioned capacity, spread S3 load across more **prefixes**, or add caching.

## Exam mapping

| Question phrasing | Answer |
|---|---|
| Requests intermittently fail with throttling / `ProvisionedThroughputExceededException` / `503 SlowDown` — make the app resilient | **Exponential backoff with jitter** and a retry limit (built into the SDK) |
| Many clients retry at the same moment and overload the service again | Add **jitter** |
| Retries create duplicate resources/orders | Make the operation **idempotent** (client token / idempotency key) |
| Some messages keep failing after all retries | **Dead-letter queue** |
| Sustained throttling on a DynamoDB table | Backoff **and** more capacity (on-demand / auto scaling), better partition key |

## References

- AWS SDK retry behavior: https://docs.aws.amazon.com/sdkref/latest/guide/feature-retry-behavior.html
- AWS Architecture Blog — Exponential backoff and jitter: https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/
- Amazon Builders' Library — Timeouts, retries and backoff with jitter: https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/
