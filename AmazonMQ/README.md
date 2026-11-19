# Amazon MQ

**Amazon MQ** is a fully managed **message broker** service for **Apache ActiveMQ** and **RabbitMQ**. It exists mainly to **migrate existing on-premises applications** that already use open-source brokers and standard messaging protocols to AWS **without rewriting** them.

## Why Amazon MQ (vs SQS / SNS)

**SQS** and **SNS** are AWS-proprietary services accessed with the AWS API/SDK. Applications that were built on **open standards** speak other protocols and expect a real broker.

| | **SQS / SNS** | **Amazon MQ** |
|---|---|---|
| API / protocols | **AWS API** (HTTP, SDK) | **Industry-standard** protocols: **JMS**, **AMQP**, **MQTT**, **OpenWire**, **STOMP**, **WebSocket** |
| Typical use | **New**, cloud-native applications | **Migrating** existing apps with minimal or no code changes |
| Scaling | **Serverless**, practically unlimited | **Provisioned brokers** (instance type, storage). You choose the size |
| Management | Nothing to manage | AWS manages the broker (patching, provisioning, failover), but you pick **instance sizes** |
| Network | Public endpoint (VPC endpoints available) | Runs **inside your VPC** (private by default) |
| Features | Queues, topics | Both **queues and topics** in one broker, plus broker features (e.g. virtual topics, message selectors) |

> **Rule of thumb**: new app → **SQS/SNS**. Existing app using **JMS/AMQP/MQTT/ActiveMQ/RabbitMQ** → **Amazon MQ**.

## Supported Engines

| Engine | Protocols | Notes |
|---|---|---|
| **Apache ActiveMQ** (Classic) | **JMS**, **OpenWire**, **AMQP**, **STOMP**, **MQTT**, **WebSocket** | Common in Java/JMS enterprise apps. |
| **RabbitMQ** | **AMQP 0-9-1** | Supports exchanges, queues, bindings and routing. |

## Protocols in Detail

| | **AMQP** | **MQTT** |
|---|---|---|
| Full name | **Advanced Message Queuing Protocol** | **Message Queuing Telemetry Transport** |
| Purpose | Reliable, **enterprise** messaging between applications | **Lightweight** messaging for **IoT** and constrained devices / networks |
| Model | **Broker-centric**: producers publish to **exchanges**, which route to **queues** via **bindings** | **Pub/sub** on hierarchical **topics** (e.g. `home/livingroom/temp`) with wildcards (`+` single level, `#` multi-level) |
| Transport | **TCP** (port **5672**, **5671** with TLS) | **TCP** (port **1883**, **8883** with TLS), also over **WebSocket** |
| Overhead | Moderate (richer headers and features) | **Very small** header (as little as 2 bytes) |
| Delivery guarantees | Acknowledgements, **transactions**, publisher confirms | **QoS 0** (at most once), **QoS 1** (at least once), **QoS 2** (exactly once) |
| Extras | Routing (direct, topic, fanout, headers exchanges), message TTL, priorities | **Retained messages**, **Last Will and Testament** (message sent if a client disconnects unexpectedly), persistent sessions |
| Versions | **AMQP 0-9-1** (RabbitMQ), **AMQP 1.0** (ActiveMQ, an open ISO standard) | **MQTT 3.1.1** and **5.0** (ActiveMQ supports 3.1/3.1.1) |
| On Amazon MQ | **ActiveMQ** (1.0) and **RabbitMQ** (0-9-1) | **ActiveMQ** only |

### STOMP

**STOMP** (**Simple/Streaming Text Oriented Messaging Protocol**) is a **simple, text-based** (HTTP-like) messaging protocol. A frame is a **command** (e.g. `CONNECT`, `SEND`, `SUBSCRIBE`, `ACK`, `BEGIN`/`COMMIT`), **headers**, and a **body**, so it is easy to implement and debug in **any language**, even by hand with `telnet`.

| | **STOMP** |
|---|---|
| Purpose | **Simple interoperability**: lightweight clients (scripts, web apps) talking to a broker without a heavy client library |
| Format | **Text** frames (readable), unlike the **binary** AMQP and MQTT |
| Model | Clients **SEND** to and **SUBSCRIBE** to **destinations** (`/queue/...`, `/topic/...`). The broker decides the semantics, there are **no exchanges** like AMQP |
| Transport | **TCP** (default port **61613**, **61614** with TLS), also over **WebSocket** (browsers) |
| Features | Acknowledgements (`ACK`/`NACK`), **transactions**, receipts, heartbeats |
| On Amazon MQ | **ActiveMQ** only (not RabbitMQ) |

- Typical use: **web browsers** (STOMP over WebSocket) and **scripting languages** (Python, Ruby, JavaScript) that need a quick broker connection.
- Less efficient than **AMQP** or **OpenWire** (ActiveMQ's native binary protocol) for high throughput, since text must be parsed.

### Quick Comparison

| Protocol | Format | Best for | Amazon MQ engine |
|---|---|---|---|
| **JMS** | Java **API** (not a wire protocol) | Java enterprise apps | ActiveMQ |
| **OpenWire** | Binary, ActiveMQ native | Fast ActiveMQ clients | ActiveMQ |
| **AMQP** | Binary | Enterprise, cross-language | ActiveMQ (1.0), RabbitMQ (0-9-1) |
| **MQTT** | Binary, tiny | IoT devices | ActiveMQ |
| **STOMP** | **Text** | Simple scripts, web clients | ActiveMQ |

- **AMQP** is **wire-level and language-neutral**: unlike **JMS**, which is a **Java API**, clients in any language can interoperate with the broker.
- **MQTT** is designed for **unreliable networks, low bandwidth and low power**: sensors, mobile devices, vehicles.
- For **IoT at scale** with managed device connections, **AWS IoT Core** (also MQTT) is usually the better fit. Amazon MQ is for **existing** MQTT clients/brokers being migrated.

## Broker Architectures

| Deployment | Description | Availability |
|---|---|---|
| **Single-instance broker** | One broker in **one AZ** + durable storage. | Lower cost, **no AZ failover**. For dev/test. |
| **Active/standby (ActiveMQ)** | Two brokers in **two AZs**, one active and one standby. Storage on **Amazon EFS** (shared). On failure, the standby takes over automatically. | **High availability**. |
| **Cluster deployment (RabbitMQ)** | **Three nodes** across **three AZs** behind a **Network Load Balancer**. | **High availability**. |
| **Network of brokers (ActiveMQ)** | Several brokers connected to scale throughput and connections. | Scale-out. |

- **Durable storage**: **EFS** for ActiveMQ (multi-AZ, durable) or **EBS** (single AZ, throughput-optimized). RabbitMQ uses **EBS**.
- Failover is automatic. Clients should use the **failover transport** (list of broker endpoints) to reconnect.

## Security

- **Network**: brokers live in a **VPC** (private subnets), controlled with **security groups**. Can be made **publicly accessible** (optional).
- **Authentication**: **broker users** (username/password) or **LDAP** (ActiveMQ) / **IAM** is used only to manage the broker via the AWS API, **not** to send messages.
- **Encryption in transit**: **TLS** for client connections.
- **Encryption at rest**: with **KMS** (AWS-owned, AWS managed or customer managed key).
- **Logging / monitoring**: **CloudWatch** metrics and logs. **CloudTrail** for API calls.

## Pricing Model

- Pay for **broker instance hours** and **storage**, plus data transfer. Unlike SQS/SNS, **not** per request.

## Common Use Cases

- **Lift-and-shift** of an on-premises ActiveMQ/RabbitMQ broker to AWS (keep the same protocols and client libraries).
- **Hybrid** setups: on-prem producers/consumers connecting to a broker in AWS over **VPN** or **Direct Connect**.
- **IoT** devices using **MQTT** to publish to a broker.
- Apps that need **JMS** semantics (transactions, selectors, durable subscriptions).

## Exam Tips

- "**Migrate** a messaging system using **JMS / AMQP / MQTT / OpenWire / STOMP** (or **ActiveMQ / RabbitMQ**) **without changing code**" → **Amazon MQ**.
- "**New** application, **decoupling**, no protocol requirement" → **SQS / SNS**, not Amazon MQ.
- "**Highly available** Amazon MQ" → **active/standby** across **two AZs** (ActiveMQ, EFS storage) or a **3-node cluster** (RabbitMQ).
- "Need **queue and topic** features in one broker with industry-standard protocols" → Amazon MQ.
- "**MQTT** devices on **ActiveMQ**" → Amazon MQ. "Managed **IoT** device connectivity at scale" → **AWS IoT Core**.
- **AMQP** = application messaging with exchanges/queues (RabbitMQ). **MQTT** = lightweight device pub/sub (QoS 0/1/2).
- **STOMP** = simple **text-based** protocol, good for scripts and **browsers** (over WebSocket). Supported on **ActiveMQ**.
- Amazon MQ does **not scale automatically** like SQS: you choose the **instance size**.
- Runs in a **VPC**. For on-prem access use **VPN** or **Direct Connect**.

Related: [SQS](../SQS/README.md), [SNS](../SNS/README.md), [VPC](../VPC/README.md), [IAM](../IAM/README.md).
