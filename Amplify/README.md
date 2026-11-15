# AWS Amplify

**AWS Amplify** is a set of tools and services for building, deploying and hosting **full-stack web and mobile applications** quickly. 
It's an **opinionated framework** (at 2024 it is disappointing and difficult to use).
Front-end developers get managed hosting with CI/CD plus a simple way to add a cloud backend (auth, data, storage, functions) **without wiring each AWS service by hand**.

Amplify has **direct integrations** with **Amazon Cognito**, **API Gateway**, **AWS AppSync**, **Amazon S3**, **Amazon DynamoDB** and **AWS Lambda**.

> Think of it as the AWS answer to **Vercel / Netlify / Firebase**: "Elastic Beanstalk for web and mobile apps".

## Main Components

| Component | What it does |
|---|---|
| **Amplify Hosting** | Managed **CI/CD + hosting** for static sites and SSR web apps (React, Next.js, Vue, Angular, Nuxt, Gatsby...). Connects to a Git repo and deploys on every push |
| **Amplify Backend** (Gen 2, code-first in TypeScript; Gen 1 used the Amplify CLI) | Defines backend resources (auth, data, storage, functions) as code; Amplify provisions them with **CloudFormation / CDK** underneath |
| **Amplify Libraries** | Client SDKs (JavaScript, React Native, Swift/iOS, Android, Flutter) to call the backend from the app |
| **Amplify UI** | Ready-made UI components (e.g. the **Authenticator** login screen) |
| **Amplify Studio** | Visual console to model data and build UI (Figma to React code) |

## Backend Features and the AWS Services Behind Them

| Feature | Underlying service |
|---|---|
| **Authentication** (sign-up, sign-in, MFA, social login) | **Amazon Cognito** (User Pools + Identity Pools) |
| **Data / API** (GraphQL, real-time subscriptions, offline sync) | **AWS AppSync** + **DynamoDB** |
| **REST API** | **API Gateway** + **Lambda** |
| **Storage** (files, images, video) | **Amazon S3** |
| **Functions** (business logic) | **AWS Lambda** |
| **Analytics / notifications** | Pinpoint, Kinesis |
| **Search / AI** | OpenSearch, Bedrock, Rekognition, Translate, Polly |

Amplify does **not** add a new runtime: everything it creates is a normal AWS resource in your account that you can see and extend.

## Amplify Hosting

- **Git-based CI/CD**: connect GitHub, GitLab, Bitbucket or CodeCommit; each push builds and deploys (build settings in `amplify.yml`).
- **Branch deployments**: one environment per branch (`main` = prod, `dev` = staging), plus **pull request previews**.
- **Global delivery** via **CloudFront** (CDN) and S3 under the hood, all managed for you.
- **Custom domains** with free **SSL/TLS certificates** (ACM), Route 53 integration.
- **SSR support** (e.g. Next.js) using managed compute.
- **Atomic deployments**: the new version goes live only when the build is complete; easy **rollback**.
- Password protection per branch, redirects/rewrites, custom headers, monitoring (CloudWatch metrics, access logs).
- Manual deploy (drag and drop a zip) is also possible without Git.

## Typical Workflow (Gen 2)

```bash
npm create amplify@latest        # scaffolds amplify/ folder (auth, data resources)
npx ampx sandbox                 # per-developer cloud sandbox, hot-redeploys backend changes
git push                         # Amplify Hosting builds front end + backend per branch
```

```ts
// amplify/auth/resource.ts
import { defineAuth } from '@aws-amplify/backend';
export const auth = defineAuth({ loginWith: { email: true } });
```

## Pricing (high level)

- Pay as you go: **build minutes**, **storage** of hosted assets, **data served** (GB out), SSR requests/duration.
- Backend resources (Cognito, AppSync, DynamoDB, S3, Lambda) are billed at **their normal prices**.
- Free tier available for hosting.

## Amplify vs Similar Services

| Need | Service |
|---|---|
| Full-stack **web/mobile app** with auth, data, storage, CI/CD from Git | **Amplify** |
| Host only a **static website** with full control | **S3 static website + CloudFront** |
| Deploy a traditional server app (Java, .NET, PHP, Python...) on EC2 | **Elastic Beanstalk** |
| Containerized web app/API from source or image, no infrastructure | **App Runner** |
| Just a GraphQL API | **AppSync** |
| Just user sign-in for an app | **Cognito** |

## Exam Tips

- "**Front-end / mobile developers** want to build a **full-stack app quickly** with authentication, storage and API" → **AWS Amplify**.
- "**Host a static or SSR web app (React, Next.js...) with CI/CD from a Git repository**" → **Amplify Hosting**.
- Keywords: **web and mobile**, **full-stack**, **Git-based CI/CD**, **branch previews**, **front-end developers**.
- Amplify auth = **Cognito**; Amplify data = **AppSync + DynamoDB**; Amplify storage = **S3**; Amplify hosting = **S3 + CloudFront** (managed).
- Amplify is a **developer productivity** layer: it provisions standard AWS resources via CloudFormation, it does not replace them.
- Server-side app on EC2 with platform choice → **Elastic Beanstalk**, not Amplify.

Related: [CloudFront](../CloudFront/README.md), [S3](../S3/README.md), [IAM](../IAM/README.md).
