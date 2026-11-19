# AWS Service Catalog

**AWS Service Catalog** lets an organization create and manage **catalogs of approved IT products** (infrastructure, apps, stacks) that end users can **self-service deploy** with **pre-approved configuration**. Admins define *what* can be launched and *with which guardrails*; users launch it without needing broad IAM permissions or deep AWS knowledge.

```
Admin ──► Portfolio ──► [ Product A (CFN/Terraform template) ]
                        [ Product B ... ]      ──share/grant──► Users / Roles / Other accounts
                                                                       │ launch
                                                                       ▼
                                                      Provisioned product (CloudFormation stack)
```

- **Governance + self-service**: the exam keyword is "**allow users to launch only approved/compliant resources**" (standardization, compliance, least privilege).
- Products are **IaC templates**: **CloudFormation** (most common), plus Terraform (open source / Cloud / Enterprise), and **AWS Marketplace** products.
- Provisioning is done by Service Catalog, not by the user, through a **launch role**.
- The service itself is **free**. You pay only for the resources users provision.

## Core Concepts

| Concept | What it is |
|---|---|
| **Product** | A **versioned** IaC template (e.g. a CloudFormation template describing an EC2 + RDS stack). Can be an AMI, a server, a full multi-tier app, etc. |
| **Portfolio** | A **collection of products** plus **who can use them** and **under which constraints**. |
| **Provisioned product** | A running **instance** of a product launched by a user (it is a **CloudFormation stack**). |
| **Constraint** | A **rule** that controls how a product can be deployed within a portfolio (launch, notification, template, StackSet, tagOptions). |
| **Access** | **IAM users, groups or roles** are granted access to a **portfolio**. |
| **TagOptions** | Enforce **tag keys and allowed values** on provisioned resources (cost allocation, compliance). |
| **Version** | Products have versions, so users can **update** a provisioned product to a newer version. |

## Users: Catalog Administrator vs End User

| | **Catalog administrator** | **End user** |
|---|---|---|
| Role | Builds and governs the catalog | Consumes the catalog (self-service) |
| Typical team | Cloud platform / central IT / governance | Developers, analysts, project teams |
| Main tasks | Create **products** (versioned templates), organize them in **portfolios**, add **constraints** (launch role, template rules), **TagOptions**, **grant access** and **share** portfolios with other accounts or the Organization | **Browse** the products they have access to, **launch** them (fill only the allowed parameters), **update** to new versions, **terminate** |
| IAM permissions | Service Catalog admin access (e.g. `AWSServiceCatalogAdminFullAccess`) plus rights to the underlying templates and the launch role (`iam:PassRole`) | Service Catalog end-user access (e.g. `AWSServiceCatalogEndUserFullAccess`). **No** permissions on the underlying services (EC2, RDS...) |
| Console view | Admin console (products, portfolios, constraints) | End-user console (products list and provisioned products) |

- The admin **decides what can be launched and how**. The end user only **picks and launches**.
- Resources are created through the **launch role**, so the end user never needs direct permissions on them. This is **least privilege** and the main reason to use the service.
- Access is granted per **portfolio** to **IAM users, groups or roles**. Users see only products in portfolios they were given access to.

## Product

A **product** is an **IT service packaged as a template** that users can deploy from the catalog. In Service Catalog, it is the **deployable unit**: a single resource (an EC2 instance, an AMI) or a **whole stack** (a multi-tier web app with VPC, ALB, EC2 and RDS), described as **infrastructure as code**.

**Purpose**
- **Standardize**: everyone deploys the same **approved, pre-configured** architecture instead of building it by hand.
- **Hide complexity**: users see a name, a description and a few **parameters**. The template details stay with the admin.
- **Enforce compliance**: security, tagging and sizing rules are **baked into the template**, and constraints add more on top.
- **Reuse**: one product, launched many times, by many users, in many portfolios.

**Details**
- **Source types**: **CloudFormation template** (most common, from S3 or a local file), **Terraform** (open source / Cloud / Enterprise, through an engine), or an **AWS Marketplace** product.
- **Versioned**: each product has **versions** (provisioning artifacts, e.g. `v1`, `v2`). Users can **update** a provisioned product to a newer version. Old versions can be **deactivated**.
- **Metadata**: name, owner, description, support contact and support link.
- **Launching** a product creates a **provisioned product** (a CloudFormation stack).
- A product must be added to a **portfolio** before any user can see it.
- **Owned** by the catalog administrator (the **template** itself is what the admin authors).

## Portfolio

A **portfolio** is a **collection of products** plus the **configuration** that says **who can use them** and **how they can be deployed**. It is the unit of **access control, constraints and sharing**.

```
Portfolio "Dev-Approved-Stacks"
 ├── Products:     Standard-WebServer, Dev-Database ...
 ├── Access:       IAM users / groups / roles
 ├── Constraints:  launch role, template rules, notifications
 ├── TagOptions:   Env = dev | test
 └── Shares:       other accounts / AWS Organization
```

- **Many-to-many**: a product can be in **several portfolios** and a portfolio holds **many products**. Each portfolio can apply **different constraints** to the same product (e.g. a bigger instance allowed in the *Prod* portfolio than in *Dev*).
- **Access** is granted **per portfolio** to **IAM users, groups or roles**. Users only see products from portfolios they can access.
- **Constraints** are attached to a **product within a portfolio**, not to the product globally.
- **Sharing**: share with **another account** or an **AWS Organization / OU**. The recipient gets an **imported** portfolio that it cannot edit but can add to its own portfolios and grant to its own users. Changes in the source **sync** to the shares.
- A portfolio can also be **copied** (e.g. to another Region).
- **Regional** resource. Created and managed by the **catalog administrator**.

## Constraints

| Type | Purpose |
|---|---|
| **Launch constraint** | An **IAM role** Service Catalog **assumes** to launch the product. The end user needs **no permission** on the underlying resources, only on Service Catalog. **Most important one for the exam** (least privilege). |
| **Notification constraint** | Sends stack events to an **SNS topic**. |
| **Template constraint** | Restricts parameters (e.g. only `t3.micro` / `t3.small` instance types, allowed sizes) using rules on the template. |
| **StackSet constraint** | Deploys the product to **multiple accounts and Regions** with **CloudFormation StackSets**. |
| **TagUpdate constraint** | Controls whether users can **change tags** when updating a provisioned product. |

## Sharing and Governance

- **Share portfolios with other accounts**, either directly or across an **AWS Organization** (org-wide sharing). Recipients get an **imported** (read-only) copy that they can add to their own portfolios and grant to their own users. Changes in the source portfolio sync to the shares.
- **Centralized management**: a **hub account** owns the catalog and spokes consume it.
- **Product updates**: publish a **new version**; users update their provisioned products. Notifications of available updates are possible.
- **AppRegistry**: Service Catalog also includes **AppRegistry** to organize and track applications and their resources/metadata.
- Integrates with **AWS Organizations**, **CloudFormation**, **IAM**, **SNS**, **Config**, **Control Tower** (Account Factory is built on Service Catalog) and **ServiceNow / Jira** connectors (request via ITSM, provision via Service Catalog).

## Typical Flow

1. **Admin** authors a **CloudFormation template** and creates a **Product**.
2. Admin adds the product to a **Portfolio** and attaches **constraints** (launch role, template rules, tags).
3. Admin **grants access** to IAM users/groups/roles (and optionally **shares** the portfolio with other accounts).
4. **End user** browses the catalog and **launches** the product, filling only the allowed parameters.
5. Service Catalog **assumes the launch role** and creates the **CloudFormation stack**.
6. The user can later **update** (new version), **terminate** or view outputs of the provisioned product.

## CLI Example

```bash
# Create a portfolio
aws servicecatalog create-portfolio \
  --display-name "Dev-Approved-Stacks" \
  --provider-name "CloudPlatformTeam"

# Create a product from a CloudFormation template in S3
aws servicecatalog create-product \
  --name "Standard-WebServer" --owner "CloudPlatformTeam" \
  --product-type CLOUD_FORMATION_TEMPLATE \
  --provisioning-artifact-parameters \
    'Name=v1,Type=CLOUD_FORMATION_TEMPLATE,Info={LoadTemplateFromURL=https://my-bucket.s3.amazonaws.com/web.yaml}'

# Add product to portfolio, grant access, set the launch role
aws servicecatalog associate-product-with-portfolio --product-id prod-xxx --portfolio-id port-xxx
aws servicecatalog associate-principal-with-portfolio --portfolio-id port-xxx \
  --principal-arn arn:aws:iam::123456789012:role/DevRole --principal-type IAM
aws servicecatalog create-constraint --portfolio-id port-xxx --product-id prod-xxx --type LAUNCH \
  --parameters '{"RoleArn":"arn:aws:iam::123456789012:role/SCLaunchRole"}'

# End user launches it
aws servicecatalog provision-product --product-id prod-xxx \
  --provisioning-artifact-id pa-xxx --provisioned-product-name my-web
```

## Service Catalog vs Similar Services

| | **Service Catalog** | **CloudFormation** | **Control Tower** | **AWS Proton** | **Systems Manager** |
|---|---|---|---|---|---|
| Purpose | **Curated, governed self-service** catalog of products | Define/deploy infra as code | Multi-account **landing zone** and guardrails | Platform-team templates for **containers/serverless** apps | Ops tooling (patching, run command) |
| Who uses it | End users, **without** deep AWS permissions | Engineers with permissions | Cloud admins | Platform + dev teams | Ops |
| Key feature | Portfolios, constraints, launch role | Stacks, StackSets | Account Factory, SCP/Config guardrails | Environment + service templates | Automation docs |

## Exam Tips

- "Let users **launch approved resources only**, **without giving them permissions** to the underlying services" → **Service Catalog + launch constraint**.
- "**Standardize** deployments / **restrict instance types** / enforce **tags**" → Service Catalog (**template constraint**, **TagOptions**).
- "Share approved products with **many accounts** in the organization" → **portfolio sharing** via **AWS Organizations**.
- Products are **CloudFormation**-based, and a provisioned product **is a stack**.
- Service Catalog is **regional**, but portfolios can be **shared/copied across Regions and accounts**.
- Just defining reusable IaC for your own use → **CloudFormation**. **Governed self-service for others** → **Service Catalog**.
