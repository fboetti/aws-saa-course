# AWS Machine Learning Managed Services

AWS offers **pre-trained, fully managed AI/ML services** you call through an **API**, with **no ML expertise** and **no model training or infrastructure** needed. For building **custom** models use **SageMaker**.

```
 Most control / effort                                         Least effort
 ┌────────────────┐   ┌──────────────────┐   ┌─────────────────────────────┐
 │ ML frameworks  │   │ SageMaker        │   │ AI services (Rekognition,   │
 │ on EC2 / DLAMI │   │ build/train/host │   │ Comprehend, CodeGuru, ...)  │
 └────────────────┘   └──────────────────┘   └─────────────────────────────┘
```

## Service Overview

| Category | Service | What it does |
|---|---|---|
| **Vision** | **Rekognition** | Image and video analysis: **object/scene/face detection**, face comparison, **celebrity** recognition, **content moderation**, **text in images**, **PPE** detection. |
| | **Textract** | Extracts **text, forms and tables** from scanned documents, PDFs and images (**OCR+**). |
| **Language** | **Comprehend** | **NLP**: **sentiment**, entities, key phrases, language detection, topic modeling, **PII** detection. **Comprehend Medical** for clinical text. |
| | **Translate** | **Neural machine translation** between languages. |
| | **Kendra** | **Intelligent enterprise search** (natural language questions) over documents. |
| **Speech** | **Polly** | **Text → speech** (lifelike voices, SSML, lexicons). |
| | **Transcribe** | **Speech → text** (automatic speech recognition), speaker identification, **PII redaction**, custom vocabulary. **Transcribe Medical** for clinical speech. |
| **Conversational** | **Lex** | Build **chatbots / voice bots** (same tech as **Alexa**): intents, slots, utterances. Integrates with **Lambda** and **Connect**. |
| **Forecasting / personalization** | **Forecast** | **Time-series forecasting** (demand, inventory, resources). |
| | **Personalize** | **Real-time recommendations** (same tech as Amazon.com). |
| | **Fraud Detector** | Detect **online fraud** (fake accounts, payment fraud). |
| **Code and DevOps** | **CodeGuru** | ML-powered **code review** and **application profiling** (below). |
| | **DevOps Guru** | ML-detected **operational anomalies** in your AWS resources (below). |
| **Business** | **Lookout** (Equipment / Metrics / Vision) | **Anomaly detection** on equipment sensors, business metrics, and industrial images. |
| | **Monitron** | End-to-end **predictive maintenance** with sensors for industrial equipment. |
| | **Augmented AI (A2I)** | **Human review** workflows for low-confidence ML predictions. |
| **Healthcare** | **HealthLake**, **HealthScribe** | Health data store/analytics, and clinical note generation from conversations. |
| **Generative AI** | **Bedrock** | Managed access to **foundation models** (Anthropic Claude, Amazon Nova, Llama, etc.) via API, with **RAG** (Knowledge Bases), **Agents**, **Guardrails** and **fine-tuning**. |
| | **Amazon Q** | Generative AI **assistant** (Q Business for enterprise data, Q Developer for coding/AWS help). |
| **Custom ML** | **SageMaker** | **Build, train, tune and deploy** your own models (notebooks, Studio, Ground Truth, Feature Store, endpoints). |

## Amazon CodeGuru

**CodeGuru** uses ML and automated reasoning to improve **code quality** and find **expensive/inefficient code**. It has two components:

| | **CodeGuru Reviewer** | **CodeGuru Profiler** |
|---|---|---|
| Purpose | **Automated code review** (static analysis) | **Runtime performance** analysis of running apps |
| Finds | **Bugs**, **security vulnerabilities**, resource leaks, **hard-coded secrets**, concurrency issues, input validation problems, AWS best-practice violations | **CPU hotspots**, **latency** and inefficient code paths, **cost** drivers (heap/CPU) |
| When | **Before deploy** (on PRs / commits) | **In production / testing** (while the app runs) |
| Languages | **Java, Python** (also JavaScript, C#, etc. in newer detectors) | **Java and Python** (JVM languages) |
| Sources | **CodeCommit, GitHub, GitHub Enterprise, Bitbucket, GitLab**, S3 | Agent in your app on **EC2, ECS, EKS, Lambda, on-premises** |
| Output | Recommendations as **PR comments** | **Flame graphs** + **recommendations** to cut CPU and cost |

- **Reviewer** = "find **bugs and vulnerabilities** in code **before** release". **Profiler** = "find **slow/expensive** code **while running**".
- The CodeGuru **Security** feature (scanning for vulnerabilities) is now part of the Reviewer / **Amazon Q Developer**.
- **How it works**: Reviewer is triggered by **pull requests** (and full repository scans) and posts findings as comments. Profiler needs a small **agent/library** added to the app and sends data to the **Profiler** service (view results in the console as **flame graphs**).
- **Pricing**: Reviewer per **lines of code** analyzed, Profiler per **sampling hour** of each profiled application.
- **Note**: AWS has been **winding down** parts of CodeGuru (e.g. no new Reviewer repository associations), pointing to **Amazon Q Developer** and **Inspector**. Still appears in SAA study material.

## Amazon DevOps Guru

- ML-based **operational insights**: detects **anomalous behavior** in your **AWS resources** and applications, then recommends fixes.
- Learns from **CloudWatch** metrics, **CloudTrail**, **Config** and **X-Ray**. Analyzes **by resource scope** (a whole account, **CloudFormation stacks** or **tags**).
- Sends **insights** to **SNS**, **EventBridge**, and ticketing (e.g. **Systems Manager OpsCenter**).
- Examples: **RDS** CPU/IO spikes, **DynamoDB** throttling, **Lambda** errors or concurrency limits.
- **DevOps Guru for RDS** diagnoses database performance (like **Performance Insights**).

## Rekognition (the one asked most)

- **Image and video** analysis through API calls. Video is processed **asynchronously** from **S3** or in **streaming** from **Kinesis Video Streams**.
- **Content moderation** flags inappropriate content (with **A2I** for human review of uncertain results).
- **Facial analysis and search**: build a **face collection**, then search it (identity verification, access).
- **Custom Labels** to train it to find **your own objects**.
- Pricing: **per image analyzed** or **per minute of video**.

## Amazon Comprehend

**Comprehend** is a managed **natural language processing (NLP)** service that finds **meaning and insights in text**, with no ML expertise needed. Input is text (from **S3**, documents, social media, emails, support tickets, call transcripts).

| Feature | What it does |
|---|---|
| **Sentiment analysis** | **Positive, negative, neutral, mixed** (also **targeted sentiment** per entity) |
| **Entity recognition** | People, places, organizations, dates, quantities, etc. |
| **Key phrases** | Important phrases in the text |
| **Language detection** | Identifies the **language** of the text |
| **Syntax analysis** | Parts of speech, tokens |
| **PII detection / redaction** | Finds and **masks** personal data (names, addresses, card numbers) |
| **Topic modeling** | Groups a large set of documents into **topics** |
| **Events detection** | Finds events (e.g. bankruptcy, mergers) in news and filings |
| **Custom classification** | Train **your own categories** on your labeled data |
| **Custom entity recognition** | Train it to find **your own entity types** (e.g. product codes) |

- **Real-time** (single, synchronous API call) and **asynchronous batch** (large sets of documents from S3, results back to S3) analysis.
- **Comprehend Medical**: extracts **medical info** (conditions, medications, dosage) from clinical text, detects **PHI**, and is **HIPAA** eligible.
- Common pattern: **Transcribe** (audio → text) → **Comprehend** (sentiment, PII) → **S3** → **Athena** / **QuickSight**. Also **Textract** → **Comprehend** for scanned documents.
- Pricing: per **unit of text** (100 characters) analyzed, and extra for custom model training and hosting.
- **Exam**: "**sentiment** of customer reviews", "**find PII** in text", "**classify** or extract entities from documents" → **Comprehend**.

## Amazon Forecast

**Forecast** is a managed **time-series forecasting** service (same technology as **Amazon.com** demand forecasting). It claims up to ~**50% more accurate** forecasts than traditional methods, with no ML expertise needed.

- **Use cases**: product **demand** planning, **inventory**, **resource** and **staffing** needs, **financial** planning, web traffic, energy demand.
- **Inputs** (from **S3**):
  - **Target time series** (required): historical values, e.g. sales per item per day.
  - **Related time series** (optional): things that influence the target (price, promotions, weather, holidays).
  - **Item metadata** (optional): attributes of each item (brand, category, color).
- **Workflow**: import data into a **dataset group** → train a **predictor** (**AutoML** picks the best algorithm, e.g. **ARIMA**, **ETS**, **Prophet**, **DeepAR+**, **CNN-QR**) → generate a **forecast** → query it via **API** or **export to S3**.
- Output includes **probabilistic forecasts** (quantiles such as P10, P50, P90), so you can plan for over/under-stocking.
- Handles **cold-start** items (little or no history) and supports **what-if analysis**.
- Pricing: per **data storage**, **training hour** and **forecasts generated**.
- **Note**: AWS **stopped onboarding new customers** to Forecast in 2024 and points to **SageMaker Canvas** instead. It still appears in SAA study material.
- **Exam**: "**predict future demand** / time-series forecasting" → **Forecast**. "Recommendations" → **Personalize**.

## Amazon Fraud Detector

**Fraud Detector** is a managed service that uses ML (based on **Amazon's own fraud detection experience**) to flag **potentially fraudulent online activity**, with no ML expertise needed.

- **Use cases**: **fake account** creation, **online payment** fraud, **new account** fraud, **guest checkout** abuse, **trial/promo abuse**, account takeover.
- **How it works**:
  1. Upload **historical events** (labeled fraud / legitimate) to **S3**.
  2. Train a **model** (e.g. **Online Fraud Insights**, **Transaction Fraud Insights**, **Account Takeover Insights**).
  3. Create **rules** and **outcomes** in a **detector** (e.g. *approve*, *review*, *block*).
  4. Call the **`GetEventPrediction`** API in real time to get a **risk score** (0-1000) and the outcome.
- Models are trained on **your data** plus enriched with **Amazon signals** (IP, email, device), so they get better with more data.
- Optional **human review** for borderline scores (e.g. with **A2I**), and integrate results with **Lambda**, **SNS**, **EventBridge**.
- Pricing: per **training hour**, per **prediction**, and **storage** of event data.
- **Note**: AWS has **stopped onboarding new customers** to Fraud Detector (announced for 2025) and points to **SageMaker** or **AutoGluon**. It still appears in SAA study material.
- **Exam**: "**detect online fraud** / fake accounts / payment fraud with ML" → **Fraud Detector**. "**Anomalies** in business metrics" → **Lookout for Metrics**.

## Amazon Kendra

**Kendra** is a managed **intelligent enterprise search** service powered by ML. Users ask **natural-language questions** ("Where is the IT support desk?") and get **specific answers**, not just a list of keyword matches.

- **Data sources** (via **connectors**): **S3**, **RDS**, **SharePoint**, **OneDrive**, **Salesforce**, **ServiceNow**, **Confluence**, **Google Drive**, web crawler, and more. Supports **PDF, Word, HTML, PowerPoint, text, FAQs**.
- **Index**: Kendra builds an **index** over your documents and **syncs** with the sources on a schedule (or on demand).
- **Features**:
  - **Natural-language** questions, with **factoid**, **descriptive** and **FAQ** answers.
  - **Incremental learning**: improves from user **feedback** (clicks, thumbs up/down).
  - **Relevance tuning**: **boost** by field, source or freshness.
  - **Synonyms** and custom document metadata.
  - **Access control**: results are **filtered by user permissions** (**ACLs**, via IAM Identity Center / AD / token-based access).
- **Generative AI**: often used as the **retriever for RAG** with **Bedrock** (retrieve relevant passages, then let an LLM answer).
- Pricing: per **index-hour** (Developer vs Enterprise edition) plus **connector** and document-scan charges. It is **not cheap**, so avoid leaving a test index running.
- **Exam**: "**Natural-language search** across company documents / intranet / FAQs" → **Kendra**. "**Full-text and log search**, dashboards" → **OpenSearch**. "**Query S3 with SQL**" → **Athena**.

## Amazon Lex

**Lex** is a managed service for building **conversational interfaces** (**chatbots** and **voice bots**) using text or speech. It uses the same deep learning technology as **Alexa**: **automatic speech recognition (ASR)** to convert speech to text and **natural language understanding (NLU)** to detect the user's **intent**.

| Concept | Meaning |
|---|---|
| **Bot** | The conversational agent (e.g. a hotel booking bot). |
| **Intent** | What the user wants to do (`BookHotel`, `CheckBalance`). |
| **Utterances** | Sample phrases that trigger an intent ("I want to book a room"). |
| **Slots** | Parameters the bot must collect (city, date, number of nights), each with a **slot type**. |
| **Prompts** | Questions the bot asks to fill missing slots. |
| **Fulfillment** | What happens once the slots are filled, usually a **Lambda** function. |
| **Versions / aliases** | Publish bot versions and point an alias (e.g. `prod`) at one. |

- **Integrations**:
  - **Lambda** for **validation and fulfillment** (call APIs, query **DynamoDB**, etc.).
  - **Amazon Connect** for **contact center** self-service (IVR) and call routing.
  - **Channels**: **Slack**, **Facebook Messenger**, **Twilio SMS**, web/mobile apps (via SDK or API).
  - **Polly** for spoken responses, **Comprehend** for sentiment, **Kendra** for FAQ search.
- **Multi-language** support, **context** carry-over between intents, and **conversation logs** to **CloudWatch Logs** / **S3**.
- **Generative AI**: can use **Bedrock** to build slots, improve intent matching and answer questions.
- Pricing: **pay per request** (text or speech), no upfront cost.
- **Exam**: "**Chatbot** / voice bot / conversational interface" → **Lex**. "**Cloud contact center**" → **Connect** (with Lex). "**Speech to text** only" → **Transcribe**.

## Amazon Personalize

**Personalize** is a managed service for **real-time personalized recommendations**, built on the same technology used by **Amazon.com**. No ML expertise needed, and no need to build your own recommender system.

- **Use cases**: **product recommendations** ("customers who bought this also bought"), **personalized rankings** of search results or content, **personalized emails and notifications**, **similar items**, **next best action**, **user segmentation**.
- **Data** (imported from **S3**, or streamed in real time via **API / events**):
  - **Interactions** (required): what users did (clicks, purchases, views, watch time).
  - **Items** (optional): item metadata (category, price, genre).
  - **Users** (optional): user attributes (age, location).
- **Workflow**: create a **dataset group** → import data → pick a **recipe** (algorithm) or a **use-case domain** (**e-commerce**, **video on demand**) → train a **solution/model** → deploy a **campaign** (real-time API endpoint) or run **batch** recommendations to S3.
- **Real-time**: new user events (via **event tracker**) update recommendations **within seconds**, and **cold-start** items and users are handled.
- **Filters** to include or exclude items (e.g. hide already purchased or out-of-stock products).
- **Integrations**: **S3**, **Lambda**, **API Gateway**, **Pinpoint / SES / SNS** for personalized messaging, **Kinesis** and **Segment** for event ingestion.
- **Security**: data is **encrypted** (KMS), private to your account and **not shared** with other customers. **IAM** and **VPC endpoints** supported.
- Pricing: **pay per use** (data ingested, training hours, and **recommendations/TPS** served), no minimum fees.
- **Exam**: "**Recommendations** / personalization (same as Amazon.com)" → **Personalize**. "**Forecast** future demand" → **Forecast**. "**Fraud**" → **Fraud Detector**.

## Textract vs Rekognition vs Comprehend

| If the input is... | Use |
|---|---|
| A **photo / video** (objects, faces, scenes) | **Rekognition** |
| A **scanned form / invoice / PDF** (text, key-value pairs, tables) | **Textract** |
| **Text** where you need **meaning** (sentiment, entities, PII) | **Comprehend** |
| **Audio** to text | **Transcribe** |
| Text to **audio** | **Polly** |
| Text in **another language** | **Translate** |
| A **chat interface** | **Lex** |
| **Natural-language search** over company documents | **Kendra** |

A common pipeline: **Transcribe** (call audio → text) → **Translate** → **Comprehend** (sentiment, PII) → store in **S3** and query with **Athena**.

## SageMaker (custom ML) in Brief

- **Fully managed** platform to **build, train, tune and deploy** models.
- **Studio** (IDE), **notebooks**, **Ground Truth** (data labeling), **Data Wrangler**, **Feature Store**, **Autopilot** (AutoML), **JumpStart** (pretrained models), **Clarify** (bias and explainability), **Model Monitor** (drift).
- **Inference**: **real-time** endpoints, **serverless**, **asynchronous** (large payloads, long jobs), and **batch transform**.
- Use it when pre-trained AI services **don't fit** your data or task.

## Security and Integration

- **IAM** for API access. Use **VPC endpoints (PrivateLink)** for private access.
- **Encryption** with **KMS** for data at rest, **TLS** in transit.
- Data is usually read from **S3**. Results go to S3, **Lambda**, **SNS/EventBridge**.
- **CloudTrail** logs API calls. Some services allow you to **opt out** of using your content to improve the services.

## Exam Tips (SAA)

- "**Detect objects / faces / unsafe content** in images or video" → **Rekognition**.
- "**Extract text from scanned documents / forms / tables**" → **Textract**.
- "**Sentiment**, entities, **PII** in text" → **Comprehend**.
- "**Text to speech**" → **Polly**. "**Speech to text**" → **Transcribe**. "**Translate**" → **Translate**.
- "**Chatbot** / voice bot" → **Lex** (backed by **Lambda**, used by **Connect**).
- "**Recommendations**" → **Personalize**. "**Forecast** demand" → **Forecast**. "**Fraud**" → **Fraud Detector**.
- "**Search** across enterprise documents with natural language" → **Kendra**.
- "**Automated code review / find bugs and vulnerabilities**" → **CodeGuru Reviewer**.
- "**Find CPU hotspots / reduce cost** of a running application" → **CodeGuru Profiler**.
- "**Detect operational anomalies** in AWS resources with ML" → **DevOps Guru**.
- "**Human review** of low-confidence ML results" → **Amazon A2I**.
- "**Build and train a custom model**" → **SageMaker**. "**Use foundation models / generative AI** via API" → **Bedrock**.
- "**No ML expertise**, quick to implement" → a **pre-trained AI service**, not SageMaker.

Related: [S3](../S3/README.md), [Lambda](../Lambda/README.md), [Kinesis](../Kinesis/README.md), [Athena](../Athena/README.md), [CloudWatch](../CloudWatch/README.md), [IAM](../IAM/README.md).
