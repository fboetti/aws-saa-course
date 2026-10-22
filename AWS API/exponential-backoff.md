# Exponential Backoff (API Retries)

When an AWS API call fails with a **retryable** error, wait before retrying and **double the wait after each attempt** — e.g. 1 s, 2 s, 4 s, 8 s … — instead of hammering the service. This gives a throttled or overloaded backend time to recover and prevents your own retries from making the problem worse.

- **Retry only retryable errors:** `5xx` responses, throttling (`ThrottlingException`, `RequestLimitExceeded`, `ProvisionedThroughputExceededException`, S3 `503 SlowDown`), timeouts and connection errors. **Not** `4xx` client errors (`400`/`403`/`404`) — those will fail the same way every time.
- **Add jitter:** randomize each delay (e.g. full jitter between `0` and the capped backoff), otherwise many clients retry in lockstep and create a **thundering herd** at the moment the service recovers.
- **Cap the backoff and the attempts** (e.g. max 5 retries, max 20 s per wait), then fail fast rather than retrying forever.
- **Never blindly retry non-idempotent calls** — a duplicated `RunInstances` or write may repeat side effects; make operations idempotent (client tokens/idempotency keys) before adding retries.
- **You usually don't implement it yourself:** AWS SDKs and the CLI apply exponential backoff automatically (SDK for Python/JS/Java: `standard` mode with max ~3 attempts, plus an `adaptive` mode; configurable via `max_attempts`/`retry_mode`). Custom HTTP code should use the SDK's built-in retryer.

**Exam mapping:** "requests intermittently fail with throttling / `ProvisionedThroughputExceededException` / `503 SlowDown` — how do you make the application resilient?" → **exponential backoff with jitter and a retry limit** (the SDK does it for you), not more capacity. Cached/queued work + dead-letter queues are the companion pattern when retries are exhausted.
