# Amazon CloudWatch

**Amazon CloudWatch** is the AWS **monitoring and observability** service. It collects **metrics**, **logs** and **events** from AWS resources, applications and on-premises servers, lets you **visualize** them (dashboards), **alarm** on them, and **act** on them automatically (Auto Scaling, EC2 actions, SNS, Lambda). It is regional, fully managed, and integrated with almost every AWS service.

## Observability: the three pillars

**Monitoring** tells you *when* something is wrong (known failure modes, predefined thresholds). **Observability** lets you ask *why*, even about problems you didn't anticipate, by inspecting the system's outputs. It rests on three types of telemetry:

| Pillar | What it is | Answers | AWS service |
|---|---|---|---|
| **Metrics** | **Numeric** measurements sampled **over time** (CPU %, request count, latency). Cheap, aggregated, ideal for **trends and alerting**. | *Is something wrong? How much?* | **CloudWatch Metrics** |
| **Logs** | **Timestamped records of discrete events** (text or JSON): errors, requests, audit trail. High detail, higher volume and cost. | *What exactly happened?* | **CloudWatch Logs** |
| **Traces** | The **end-to-end path of a single request** across services, split into **spans** with timing. | *Where is the time spent? Which service failed?* | **AWS X-Ray** (and CloudWatch ServiceLens / Application Signals) |

```
Metric alarm fires (latency up)  ──►  Trace shows slow call to DB  ──►  Logs show the exact error
        "something is wrong"            "where in the request path"          "why it happened"
```

- The pillars are **complementary**: metrics **detect**, traces **locate**, logs **explain**.
- **Correlate** them with shared identifiers (request ID, trace ID) and tools like **Logs Insights**, **ServiceLens** and **Contributor Insights**.
- Traces are **not** a CloudWatch feature proper: they live in **AWS X-Ray**, surfaced inside CloudWatch. **CloudTrail** (API audit) and **AWS Config** (resource state) are related but different services.
- **OpenTelemetry (OTel)** is the vendor-neutral standard to emit all three. AWS offers **ADOT** (AWS Distro for OpenTelemetry) and the **CloudWatch agent** as collectors.

## CloudWatch Metrics

A **metric** is a time-ordered set of **data points**. Metrics are grouped in **namespaces** (e.g. `AWS/EC2`, `AWS/SQS`) and identified by **name + dimensions** (name/value pairs such as `InstanceId=i-123`). Each data point has a **timestamp**, a value and a unit.

- **Default (AWS-published) metrics**: most services publish for free. **EC2** every **5 min** (basic) or **1 min** with **detailed monitoring** (paid).
- **Not published by default** for EC2: **memory**, **disk space usage**, swap. Use the **CloudWatch agent** to push them as **custom metrics**.
- **Custom metrics**: your own data via `PutMetricData` (API/CLI/SDK) or the agent. **Standard resolution** = **1 min**, **high resolution** = down to **1 s** (costs more).
- **Retention** (automatic roll-up): 1 s data kept **3 hours**, 1 min kept **15 days**, 5 min kept **63 days**, 1 hour kept **455 days (15 months)**.
- **Statistics**: Average, Sum, Min, Max, SampleCount, **percentiles** (p90, p99...).
- **Metric Math**: compute new time series from others (e.g. error rate = errors / requests).
- **Metric Streams**: continuously stream metrics near real time to **Kinesis Data Firehose** (S3, Datadog, Splunk...).
- **Cross-account / cross-Region** dashboards and **cross-account observability** (monitoring accounts and source accounts) are supported.
- Metrics **cannot be deleted**: they expire when no new data arrives.

### Alarms

An **alarm** watches **one metric** (or a metric math expression) over a number of **periods** and changes state.

| State | Meaning |
|---|---|
| **OK** | Metric is within the threshold. |
| **ALARM** | Metric breached the threshold. |
| **INSUFFICIENT_DATA** | Not enough data yet (just started, or metric stopped reporting). |

**Anatomy of an alarm**

| Setting | Meaning |
|---|---|
| **Metric** (+ namespace, dimensions) | What to watch. Can be a **metric math** expression or a **metric filter** metric (to alarm on log content). |
| **Statistic** | Average, Sum, Min, Max, SampleCount or a **percentile** (p99). |
| **Period** | Length of each evaluation window (**10 s**, **30 s**, or multiples of **60 s**). |
| **Evaluation periods (M)** / **Datapoints to alarm (N)** | Alarm when **N out of the last M** periods breach (e.g. 3 out of 5). Avoids reacting to single spikes. |
| **Threshold + comparison** | `>`, `>=`, `<`, `<=`, or **anomaly detection** (ML band learned from history, with a width you choose). |
| **Missing data treatment** | `missing` (keep state, default), `notBreaching`, `breaching`, `ignore`. |
| **Actions** | What to run on each **state change** (OK / ALARM / INSUFFICIENT_DATA). |

```
Metric ──► [ statistic over period ] ──► compare to threshold (N of M) ──► state ──► actions
```

**Actions**
- **SNS** notification (email, SMS, Lambda, chat via Amazon Q Developer / Chatbot).
- **EC2**: **stop**, **terminate**, **reboot**, **recover** (restores an instance after a **system status check** failure, keeping instance ID, private IP and EBS volumes).
- **Auto Scaling**: scale policy of an **ASG** (alarm-driven **step** or **simple** scaling). Target tracking creates its own alarms.
- **Systems Manager**: create an **OpsItem** or **incident**.
- Alarms can also be an **EventBridge** event source (state change events), which opens any target.
- Actions fire on **state transitions**, and an alarm can have actions for **each state**. They are **not** re-sent while the state stays the same.

**Alarm types**
- **Metric alarm**: watches one metric or one math expression.
- **Composite alarm**: combines other alarms with `AND` / `OR` / `NOT` (`ALARM(a) AND ALARM(b)`), to cut **alarm noise** and trigger only on meaningful combinations. Composite alarms can have actions, but **not** EC2 or Auto Scaling ones.
- **Anomaly detection alarm**: threshold is a **band** instead of a fixed number, adapts to daily and weekly patterns.
- **Metrics Insights alarm**: alarm on a **SQL-like query** across many metrics.

**Good to know**
- **High-resolution alarms** (period of **10 s** or **30 s**) cost more and need **high-resolution metrics**.
- **Alarm on logs**: **metric filter** (or **EMF**) → metric → alarm.
- **Alarm on a missing heartbeat**: set missing data to `breaching`.
- **Alarm on a single resource** (dimension) vs the **whole fleet**: pick the dimensions carefully (e.g. `AutoScalingGroupName` for aggregate CPU).
- **Test** from the CLI without touching the metric: `aws cloudwatch set-alarm-state --state-value ALARM`. State goes back at the next evaluation.
- **Cross-account** alarms are supported through **cross-account observability**. Alarms are **regional** and watch metrics in **their own Region**.
- **Cost**: charged **per alarm per month** (standard vs high-resolution vs composite vs anomaly detection).
- **Exam**: CPU high → **ASG scale out**. Instance impaired → **EC2 recover**. Billing guardrail → **billing alarm** (billing metrics live only in **us-east-1**, and require enabling **billing alerts**).

## CloudWatch Logs

Stores, searches and analyzes **log data** from AWS services, applications and servers.

```
Log Group  (app / service, retention, encryption, access)
 └── Log Stream  (one source: instance, container, Lambda instance)
      └── Log Events  (timestamp + message)
```

- **Log group**: container with shared **retention**, **KMS encryption** and permissions. **Retention** is **never expire** by default, configurable from **1 day to 10 years**.
- **Log stream**: sequence of events from a single source.
- **Sources**: **Lambda** (automatic), **ECS/Fargate** (`awslogs` driver), **EKS**, **EC2** via **CloudWatch agent**, **VPC Flow Logs**, **Route 53 query logs**, **API Gateway**, **CloudTrail**, on-premises via agent.
- **Logs Insights**: interactive **query language** (`fields`, `filter`, `stats`, `sort`, `parse`) to analyze logs. Query across multiple log groups.
- **Metric filters**: extract a pattern from logs and turn it into a **metric** (e.g. count `ERROR`), then **alarm** on it.
- **Subscription filters**: stream logs in **real time** to **Kinesis Data Streams**, **Data Firehose**, **Lambda** or **OpenSearch** (up to 2 filters per log group). Supports **cross-account** and **cross-Region** aggregation.
- **Export to S3**: `CreateExportTask` is **batch** (up to ~12 hours delay), **not real time**. For real time use subscription filters.
- **Log classes**: **Standard** (full features) and **Infrequent Access** (cheaper, fewer features).
- **Data protection policies**: detect and **mask sensitive data** (PII).
- **Embedded Metric Format (EMF)**: write structured JSON logs and CloudWatch **extracts custom metrics** automatically (great for Lambda, no `PutMetricData` calls).
- **Live Tail**: stream logs in near real time in the console.

### Logs Insights: discovered fields

When you run a query, **Logs Insights automatically discovers the fields** in the selected log groups and lists them in the **Discovered fields** side panel of the console. You can click one to add it to the query, and you don't have to define any schema.

| Kind | Examples | Notes |
|---|---|---|
| **System fields** (always present, start with `@`) | `@message`, `@timestamp`, `@logStream`, `@log`, `@ingestionTime` | `@message` is the raw event. `@log` is `account-id:log-group` (useful when querying **several log groups**). |
| **AWS service fields** (known log formats) | **Lambda**: `@requestId`, `@duration`, `@billedDuration`, `@maxMemoryUsed`, `@memorySize`, `@type`, `@xrayTraceId`. **VPC Flow Logs**, **Route 53**, **CloudTrail**, **API Gateway**: their own fields | Discovered for services whose log format Insights recognizes. |
| **JSON fields** | `userIdentity.type`, `eventName`, `latencyMs` | Every JSON key becomes a field. **Nested** keys use **dot notation**, arrays use an index (`items.0.id`). Insights discovers **up to 200** fields per JSON event. |

```
fields @timestamp, @message
| filter level = "ERROR" and latencyMs > 500
| stats count() by userIdentity.type
```

- **Plain text / custom formats are not auto-parsed**: only the system fields exist. Use **`parse`** to extract **ephemeral fields** (via glob or regex) and then filter or aggregate on them: `parse @message "user=* action=*" as user, action`.
- **Field names with special characters** (`-`, `.`, `@`, spaces) must be wrapped in **backticks**: `` `user-id` ``.
- Discovery is based on **sampled** events from the selected **time range** and log groups, so a field that appears rarely may not show in the panel. You can still query it by name.
- **Structured (JSON) logging** is the best way to get useful discovered fields, and it is also what **EMF** and **metric filters** work best with.
- Discovered fields live only in the **query layer**: they are **not** indexed and don't change what is stored. Querying costs **per GB scanned**, so narrow the **time range** and **log groups**, and filter early.

### Logs as the foundation of CloudWatch

CloudWatch Logs is the **storage and processing layer for log data**, and many higher-level features are built **on top of it**. But it is **not** the base of *everything*: **Metrics** have their own store and API (`PutMetricData`), and AWS services publish metrics **directly**, without going through Logs.

```
                         ┌─► Logs Insights / Live Tail         (query)
                         ├─► Metric filters ──► Metrics ──► Alarms   (logs → metrics)
 App / AWS service ─► [ CloudWatch Logs ] ─┼─► EMF (JSON logs) ──► Custom metrics
                         ├─► Contributor Insights               (top-N from logs)
                         ├─► Subscription filters ──► Kinesis / Firehose / Lambda / OpenSearch
                         └─► Export to S3

 AWS service ─► [ CloudWatch Metrics ] ─► Alarms, Dashboards, Metric Math   (no Logs needed)
```

| Feature | Relation to Logs |
|---|---|
| **Logs Insights, Live Tail, Contributor Insights** | **Built on** log data. |
| **Metric filters, Embedded Metric Format** | **Turn logs into metrics**. This is how logs reach alarms. |
| **Container Insights, Lambda Insights, Application Signals** | Ship **performance events as structured logs** (EMF) and derive metrics from them. |
| **Synthetics, RUM** | Write run and session details to **log groups** (alongside metrics). |
| **ServiceLens** | **Correlates** logs with metrics and X-Ray traces. Doesn't store them. |
| **Dashboards** | Can **display** log widgets (Insights queries), but also metrics and alarms. |
| **Metrics, Alarms, Metric Math** | **Independent** of Logs. Alarms watch metrics (use a metric filter to alarm on log content). |
| **EventBridge** | **Separate** event bus. Logs can be a **target**, not a dependency. |
| **X-Ray traces** | **Separate** service and data store. |

- **Rule of thumb**: if the data starts as **text or JSON events**, it goes through Logs. If it starts as a **number over time**, it goes straight to Metrics.
- Logs are the **richest** source of detail, so most CloudWatch "insight" features extract **metrics or patterns from logs**.

## CloudWatch Agent

- Installed on **EC2** and **on-premises servers** to collect **system-level metrics** (memory, disk, processes) and **log files**.
- Configured with a JSON file (wizard) and commonly stored in **SSM Parameter Store**.
- The instance needs an **IAM role** (`CloudWatchAgentServerPolicy`) to push data.
- Older **unified agent** replaces the legacy CloudWatch Logs agent.

## Dashboards, Events and More

| Feature | What it does |
|---|---|
| **Dashboards** | Customizable **global** (cross-Region, cross-account) views of metrics, alarms and logs widgets. |
| **EventBridge** (formerly CloudWatch Events) | **Event bus** and **rules** reacting to AWS events or on a **schedule** (cron) and routing to targets. Same underlying service. |
| **Synthetics (canaries)** | Scripts (Node.js/Python) running on a **schedule** to test endpoints and UI flows, **monitoring availability** from the outside. |
| **RUM** (Real User Monitoring) | Collects **client-side** performance data from real user browser sessions. |
| **Evidently** | Feature flags and A/B experiments (being retired in favor of **AWS AppConfig**). |
| **Application Signals** | Auto-instrumented **APM**: service map, SLOs, golden signals. |
| **Container Insights** | Metrics and logs for **ECS, EKS, Kubernetes**. |
| **Lambda Insights** | Enhanced metrics for Lambda (memory, cold starts, CPU). |
| **Contributor Insights** | Finds the **top-N contributors** (noisy IPs, heavy users) from logs. |
| **Application Insights** | Auto-detects and sets up monitoring and alarms for app stacks. |
| **ServiceLens** | Correlates **metrics, logs and X-Ray traces** in one view. |
| **Internet Monitor** | Monitors internet performance and availability impacting your apps. |

## AWS X-Ray (the traces pillar)

- Collects **traces** of requests as they travel through your distributed app (API Gateway, Lambda, ECS, EC2, SQS, DynamoDB...).
- **Service map**: graph of services with latency and error rates. **Segments** and **subsegments** (spans) detail each call.
- **Annotations** (indexed, searchable key/values) and **metadata** (not indexed).
- **Sampling** rules control how many requests are traced (cost control).
- Instrument with the **X-Ray SDK** or **OpenTelemetry (ADOT)**. Lambda: enable **active tracing**. The X-Ray **daemon** relays data (UDP 2000).

## CloudWatch vs. Related Services

| Service | Purpose | Question it answers |
|---|---|---|
| **CloudWatch** | Metrics, logs, alarms, dashboards | *How is it performing? Is it healthy?* |
| **X-Ray** | Distributed traces | *Where is the latency / error in the request path?* |
| **CloudTrail** | **API call audit** (who did what, when) | *Who changed this resource?* |
| **AWS Config** | Resource **configuration history** and compliance | *What did it look like, is it compliant?* |
| **EventBridge** | Event routing and scheduling | *React to this event.* |

## Security and Cost

- **Access**: IAM policies per action (`cloudwatch:PutMetricData`, `logs:PutLogEvents`...). Logs support **resource policies** and **KMS** encryption.
- **Transit**: API calls over HTTPS. **VPC interface endpoints** (PrivateLink) available for private access.
- **Cost drivers**: **custom metrics** (per metric), **alarms** (per alarm, high-res cost more), **log ingestion** (per GB, usually the biggest bill), **log storage**, **Logs Insights queries** (per GB scanned), **dashboards** (beyond the free ones), **API requests**.
- **Save money**: set log **retention**, use the **Infrequent Access** class, avoid high-cardinality dimensions, filter noise before ingestion.

## Exam Tips (SAA)

- **EC2 memory / disk usage** is **not** a default metric → **CloudWatch agent** (custom metric).
- Basic EC2 monitoring = **5 min**, detailed = **1 min**. Custom **high-resolution** = **1 s**.
- **Alarm** + **EC2 recover** action restores an instance after a **system status check failure** (same instance ID, IP, EBS).
- **Alarm** → **Auto Scaling** policy to scale on a metric (CPU, SQS queue depth `ApproximateNumberOfMessagesVisible`).
- **Real-time** log processing → **subscription filter** (Kinesis / Firehose / Lambda). **S3 export** is **not** real time.
- **Query** logs ad hoc → **Logs Insights**. **Count errors** from logs → **metric filter** + alarm.
- **Scheduled** or event-driven automation → **EventBridge** (CloudWatch Events).
- **Who called the API?** → **CloudTrail**, not CloudWatch. **Trace a request across microservices** → **X-Ray**.
- **Test a website / API endpoint** on a schedule → **Synthetics canary**. **Real user** browser metrics → **RUM**.
- **Custom metrics from Lambda** without extra API calls → **Embedded Metric Format**.
- **Cross-account** monitoring → **CloudWatch cross-account observability** (monitoring + source accounts).
- Metrics are **regional**; logs stay in the Region where created (use subscription filters / export for aggregation).
