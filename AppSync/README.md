# AWS AppSync

**AWS AppSync** is a fully managed, serverless service for building **GraphQL APIs** (and **real-time Pub/Sub APIs**). One API endpoint lets web and mobile apps **query, combine and update data from many sources** (DynamoDB, Lambda, Aurora, OpenSearch, HTTP APIs...) and get **real-time updates** over WebSockets.

## Purpose

- **One endpoint, many data sources**: the client asks for exactly the fields it needs in **one request**, and AppSync fetches them from different back ends. No over-fetching or multiple REST calls.
- **Real-time data**: clients subscribe to changes (chat, live dashboards, scores, collaborative apps) with **GraphQL subscriptions** over **WebSockets**, without running your own socket servers.
- **Offline and sync for mobile**: with Amplify DataStore, apps work offline and sync when back online, with conflict resolution.
- **Serverless**: no servers to manage. It scales automatically and you pay per request.

## GraphQL in 30 Seconds

```graphql
type Post { id: ID!  title: String  author: Author  comments: [Comment] }

query   { getPost(id: "1") { title author { name } } }      # read
mutation { createPost(title: "Hello") { id } }               # write
subscription { onCreatePost { id title } }                   # real-time push
```

- **Schema**: defines types and operations (the API contract).
- **Query** = read, **Mutation** = write, **Subscription** = real-time updates triggered by mutations.

## How It Works

```
Web / mobile client ──► AppSync GraphQL endpoint ──► Resolvers ──► Data sources
     (HTTPS + WebSocket)     (schema, auth, cache)                ├─ DynamoDB
                                                                  ├─ Lambda (any logic / source)
                                                                  ├─ Aurora (RDS Data API)
                                                                  ├─ OpenSearch
                                                                  ├─ HTTP endpoints (REST APIs, other AWS APIs)
                                                                  └─ EventBridge, none (local)
```

- **Resolvers** link each field to a data source. They are written in **JavaScript** (APPSYNC_JS) or **VTL** templates. **Pipeline resolvers** chain several steps.
- **Lambda data source**: lets you reach **anything** (third-party APIs, other databases).
- **Merged APIs**: combine several team-owned AppSync APIs into one endpoint.
- **AppSync Events**: plain serverless **WebSocket Pub/Sub** channels, no GraphQL needed.

## Security (Authorization Modes)

| Mode | Use case |
|---|---|
| **API key** | Public or prototype APIs (keys expire) |
| **IAM (SigV4)** | AWS services, users with IAM / Cognito Identity Pool credentials |
| **Amazon Cognito User Pools** | App users signed in, group-based access |
| **OpenID Connect (OIDC)** | Third-party identity providers (Auth0, Okta...) |
| **Lambda authorizer** | Custom auth logic |

- Several modes can be enabled on the **same API**; fine-grained access per field/type.
- **AWS WAF** can protect the API. **Private APIs** are reachable only from a VPC (via interface VPC endpoint).
- **Encryption** in transit (TLS) and of the cache at rest.

## Other Features

- **Server-side caching** (managed, in-memory) to cut latency and data source load.
- **Custom domain names** with ACM certificates.
- Monitoring with **CloudWatch** metrics and logs, **X-Ray** tracing, and **CloudTrail**.
- Pricing: per million **query/mutation** operations, per million **real-time messages** and connection-minutes, plus caching per hour.

## AppSync vs API Gateway

| | **AppSync** | **API Gateway** |
|---|---|---|
| API style | **GraphQL** (+ WebSocket Pub/Sub) | **REST**, HTTP, **WebSocket** APIs |
| Real-time | Built-in **subscriptions** tied to mutations | WebSocket APIs (you manage connection logic) |
| Multiple sources in one call | Yes (resolvers) | One integration per route |
| Offline sync for mobile | Yes (with Amplify) | No |
| Typical client | Web/mobile front ends | Any client, microservices, public REST APIs |

## Exam Tips

- "**GraphQL**" → **AppSync**. (REST → API Gateway.)
- "**Real-time updates** / live data to web and mobile clients / **subscriptions** / **WebSockets** without managing servers" → **AppSync**.
- "**Mobile app offline sync** with conflict resolution" → **AppSync** (with Amplify DataStore).
- "**Combine data from several sources** (DynamoDB, Aurora, Lambda, HTTP) in a single API request" → **AppSync**.
- Authorization: **Cognito User Pools** for app users, **IAM** for AWS services, **API key** for public, **OIDC** / **Lambda** for external or custom auth.
- **Amplify** uses AppSync + DynamoDB for its data/API layer.
- Serverless and auto-scaling. Protect it with **WAF**. Speed it up with **AppSync caching**.

Related: [Amplify](../Amplify/README.md), [CloudFront](../CloudFront/README.md), [IAM](../IAM/README.md), [API (SigV4)](../API/sigv4.md).
