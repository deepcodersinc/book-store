# Architecture

```mermaid
%%{init: {'theme':'neutral'}}%%
graph LR
    subgraph Web_App_Container["Web App Container (Docker Compose, uvicorn)"]
        Customer_Storefront[/"Customer Storefront (Python, FastAPI, Jinja2)"\]
        Staff_Console[/"Staff Console (Python, FastAPI, Jinja2)"\]
        Public_API["Public API (Python, FastAPI)"]
    end
    subgraph Fulfilment_Worker_Container["Fulfilment Worker Container (Docker Compose)"]
        Fulfilment_Worker[\"Fulfilment Worker (Python)"/]
        Operations_CLI>"Operations CLI (Python)"]
    end
    Business_Services["Business Services (Python)"]
    Data_Access_Layer(["Data Access Layer (Python, SQLite)"])
    Third_Party_Integrations(["Third-Party Integrations (Python)"])
    Shared_Web_Toolkit(["Shared Web Toolkit (Python, Jinja2)"])
    Domain_Schemas(["Domain Schemas (Python, Pydantic)"])

    Bookstore_Database[("Bookstore Database")]
    Stripe[["Stripe"]]
    SendGrid[["SendGrid"]]
    Twilio[["Twilio"]]
    Object_Storage[("Object Storage")]

    Customer_Storefront --> Business_Services
    Customer_Storefront --> Shared_Web_Toolkit
    Staff_Console --> Business_Services
    Staff_Console --> Shared_Web_Toolkit
    Staff_Console --> Fulfilment_Worker
    Public_API --> Business_Services
    Public_API --> Third_Party_Integrations
    Business_Services --> Data_Access_Layer
    Business_Services --> Third_Party_Integrations
    Business_Services --> Domain_Schemas
    Data_Access_Layer --> Bookstore_Database
    Third_Party_Integrations --> Stripe
    Third_Party_Integrations --> SendGrid
    Third_Party_Integrations --> Twilio
    Third_Party_Integrations --> Object_Storage
    Fulfilment_Worker --> Business_Services
    Fulfilment_Worker --> Data_Access_Layer
    Fulfilment_Worker --> Domain_Schemas
    Operations_CLI --> Business_Services
    Operations_CLI --> Data_Access_Layer
    Operations_CLI --> Fulfilment_Worker
```

---

## Components

How work moves through the system. Modules that have components are drawn as containers.

<details>
<summary>Show the component diagram</summary>

```mermaid
%%{init: {'theme':'neutral'}}%%
graph LR
    Customer_Storefront[/"Customer Storefront (Python, FastAPI, Jinja2)"\]
    Staff_Console[/"Staff Console (Python, FastAPI, Jinja2)"\]
    Public_API["Public API (Python, FastAPI)"]
    subgraph Business_Services["Business Services (Python)"]
        Business_Services_Catalog["Catalog"]
        Business_Services_Checkout___Pricing["Checkout & Pricing"]
        Business_Services_Orders["Orders"]
        Business_Services_Payments["Payments"]
        Business_Services_Fulfilment_Jobs["Fulfilment Jobs"]
        Business_Services_Inventory["Inventory"]
        Business_Services_Customer_Identity["Customer Identity"]
        Business_Services_Notifications["Notifications"]
        Business_Services_Audit_Trail["Audit Trail"]
    end
    subgraph Data_Access_Layer["Data Access Layer (Python, SQLite)"]
        Data_Access_Layer_Database_Connection___Schema(["Database Connection & Schema"])
        Data_Access_Layer_Book_Repository(["Book Repository"])
        Data_Access_Layer_Inventory_Repository(["Inventory Repository"])
        Data_Access_Layer_Customer_Repository(["Customer Repository"])
        Data_Access_Layer_Cart_Repository(["Cart Repository"])
        Data_Access_Layer_Order_Repository(["Order Repository"])
        Data_Access_Layer_Payment_Repository(["Payment Repository"])
        Data_Access_Layer_Fulfilment_Repository(["Fulfilment Repository"])
        Data_Access_Layer_Outbox_Repository(["Outbox Repository"])
        Data_Access_Layer_Audit_Log_Repository(["Audit Log Repository"])
    end
    subgraph Third_Party_Integrations["Third-Party Integrations (Python)"]
        Third_Party_Integrations_Payment_Client(["Payment Client"])
        Third_Party_Integrations_Email_Client(["Email Client"])
        Third_Party_Integrations_SMS_Client(["SMS Client"])
        Third_Party_Integrations_File_Storage(["File Storage"])
    end
    Shared_Web_Toolkit(["Shared Web Toolkit (Python, Jinja2)"])
    Domain_Schemas(["Domain Schemas (Python, Pydantic)"])
    Fulfilment_Worker[\"Fulfilment Worker (Python)"/]
    subgraph Operations_CLI["Operations CLI (Python)"]
        Operations_CLI_Command_Runner>"Command Runner"]
        Operations_CLI_Demo_Data_Seeder>"Demo Data Seeder"]
    end

    Bookstore_Database[("Bookstore Database")]
    Stripe[["Stripe"]]
    SendGrid[["SendGrid"]]
    Twilio[["Twilio"]]
    Object_Storage[("Object Storage")]

    Customer_Storefront --> Business_Services
    Customer_Storefront --> Shared_Web_Toolkit
    Staff_Console --> Business_Services
    Staff_Console --> Shared_Web_Toolkit
    Staff_Console --> Fulfilment_Worker
    Public_API --> Business_Services
    Public_API --> Third_Party_Integrations
    Business_Services_Catalog --> Data_Access_Layer_Book_Repository
    Business_Services_Catalog --> Third_Party_Integrations_File_Storage
    Business_Services_Catalog --> Domain_Schemas
    Business_Services_Checkout___Pricing --> Business_Services_Catalog
    Business_Services_Checkout___Pricing --> Business_Services_Inventory
    Business_Services_Checkout___Pricing --> Business_Services_Orders
    Business_Services_Checkout___Pricing --> Business_Services_Payments
    Business_Services_Checkout___Pricing --> Business_Services_Customer_Identity
    Business_Services_Checkout___Pricing --> Data_Access_Layer_Cart_Repository
    Business_Services_Checkout___Pricing --> Domain_Schemas
    Business_Services_Orders --> Business_Services_Notifications
    Business_Services_Orders --> Business_Services_Fulfilment_Jobs
    Business_Services_Orders --> Data_Access_Layer_Order_Repository
    Business_Services_Orders --> Domain_Schemas
    Business_Services_Payments --> Business_Services_Orders
    Business_Services_Payments --> Business_Services_Notifications
    Business_Services_Payments --> Data_Access_Layer_Order_Repository
    Business_Services_Payments --> Data_Access_Layer_Payment_Repository
    Business_Services_Payments --> Third_Party_Integrations_Payment_Client
    Business_Services_Payments --> Domain_Schemas
    Business_Services_Fulfilment_Jobs --> Data_Access_Layer_Fulfilment_Repository
    Business_Services_Inventory --> Data_Access_Layer_Inventory_Repository
    Business_Services_Customer_Identity --> Data_Access_Layer_Customer_Repository
    Business_Services_Customer_Identity --> Domain_Schemas
    Business_Services_Notifications --> Business_Services_Customer_Identity
    Business_Services_Notifications --> Data_Access_Layer_Outbox_Repository
    Business_Services_Notifications --> Third_Party_Integrations_Email_Client
    Business_Services_Notifications --> Third_Party_Integrations_SMS_Client
    Business_Services_Audit_Trail --> Data_Access_Layer_Audit_Log_Repository
    Data_Access_Layer_Database_Connection___Schema --> Bookstore_Database
    Data_Access_Layer_Book_Repository --> Data_Access_Layer_Database_Connection___Schema
    Data_Access_Layer_Inventory_Repository --> Data_Access_Layer_Database_Connection___Schema
    Data_Access_Layer_Customer_Repository --> Data_Access_Layer_Database_Connection___Schema
    Data_Access_Layer_Cart_Repository --> Data_Access_Layer_Database_Connection___Schema
    Data_Access_Layer_Order_Repository --> Data_Access_Layer_Database_Connection___Schema
    Data_Access_Layer_Payment_Repository --> Data_Access_Layer_Database_Connection___Schema
    Data_Access_Layer_Fulfilment_Repository --> Data_Access_Layer_Database_Connection___Schema
    Data_Access_Layer_Outbox_Repository --> Data_Access_Layer_Database_Connection___Schema
    Data_Access_Layer_Audit_Log_Repository --> Data_Access_Layer_Database_Connection___Schema
    Third_Party_Integrations_Payment_Client --> Stripe
    Third_Party_Integrations_Email_Client --> SendGrid
    Third_Party_Integrations_SMS_Client --> Twilio
    Third_Party_Integrations_File_Storage --> Object_Storage
    Fulfilment_Worker --> Business_Services
    Fulfilment_Worker --> Data_Access_Layer
    Fulfilment_Worker --> Domain_Schemas
    Operations_CLI_Command_Runner --> Operations_CLI_Demo_Data_Seeder
    Operations_CLI_Command_Runner --> Business_Services_Catalog
    Operations_CLI_Command_Runner --> Business_Services_Fulfilment_Jobs
    Operations_CLI_Command_Runner --> Business_Services_Inventory
    Operations_CLI_Command_Runner --> Business_Services_Orders
    Operations_CLI_Command_Runner --> Data_Access_Layer_Database_Connection___Schema
    Operations_CLI_Command_Runner --> Fulfilment_Worker
    Operations_CLI_Demo_Data_Seeder --> Business_Services_Customer_Identity
    Operations_CLI_Demo_Data_Seeder --> Data_Access_Layer_Book_Repository
    Operations_CLI_Demo_Data_Seeder --> Data_Access_Layer_Customer_Repository
    Operations_CLI_Demo_Data_Seeder --> Data_Access_Layer_Inventory_Repository
    Operations_CLI_Demo_Data_Seeder --> Data_Access_Layer_Order_Repository
    Operations_CLI_Demo_Data_Seeder --> Data_Access_Layer_Payment_Repository
```

</details>

---

### Customer Storefront `Python, FastAPI, Jinja2`

Server-rendered shop where customers browse books, manage a cart, check out and view their orders.

**Path:** `apps/storefront`

**Depends on:** Business Services, Shared Web Toolkit


### Staff Console `Python, FastAPI, Jinja2`

Back-office pages for staff to manage books, inventory, orders, fulfilment jobs, the message outbox and the audit log.

**Path:** `apps/admin`

**Depends on:** Business Services, Shared Web Toolkit, Fulfilment Worker


### Public API `Python, FastAPI`

JSON endpoints for the catalogue, ebook downloads and the Stripe payment webhook.

**Path:** `apps/api`

**Depends on:** Business Services, Third-Party Integrations


### Business Services `Python`

Domain logic for the bookshop, sitting between the web layer and the data repositories.

**Path:** `services`

**Depends on:** Data Access Layer, Third-Party Integrations, Domain Schemas

- **Catalog** — Looks up books, their physical and digital editions, and bestseller lists.
- **Checkout & Pricing** — Manages guest and signed-in carts, prices them and turns them into paid orders.
- **Orders** — Creates orders and moves them through their lifecycle.
- **Payments** — Charges customers through Stripe and reconciles webhook events with orders.
- **Fulfilment Jobs** — Queues fulfilment work and manages download grants for ebooks.
- **Inventory** — Tracks stock levels for physical editions.
- **Customer Identity** — Registers and authenticates customers and manages sessions.
- **Notifications** — Records and sends transactional emails and text messages to customers.
- **Audit Trail** — Records staff actions for the audit log.

### Data Access Layer `Python, SQLite`

Owns the database schema and connection, and exposes one repository per domain area.

**Path:** `data`

**Depends on:** Bookstore Database

- **Database Connection & Schema** — Opens the database connection, runs queries and creates the schema.
- **Book Repository** — Reads and writes books and editions, and ranks bestsellers from paid orders.
- **Inventory Repository** — Reads and adjusts stock levels for physical editions.
- **Customer Repository** — Stores customer accounts and login sessions.
- **Cart Repository** — Persists carts for signed-in shoppers.
- **Order Repository** — Stores orders, their line items and status changes.
- **Payment Repository** — Stores payment and refund records.
- **Fulfilment Repository** — Stores shipments, ebook download grants and the background job queue.
- **Outbox Repository** — Records every email and text message sent to customers.
- **Audit Log Repository** — Stores the audit trail of staff actions.

### Third-Party Integrations `Python`

Clients for payments, email, text messages and object storage that fall back to local mocks when no credentials are set.

**Path:** `integrations`

**Depends on:** Stripe, SendGrid, Twilio, Object Storage

- **Payment Client** — Creates charges and refunds and verifies payment webhook signatures.
- **Email Client** — Sends transactional emails.
- **SMS Client** — Sends text messages.
- **File Storage** — Resolves and reads cover images and ebook files from a bucket or local disk.

### Shared Web Toolkit `Python, Jinja2`

Shared templating setup, base layout and form helpers used by the storefront and staff console.

**Path:** `packages/web`


### Domain Schemas `Python, Pydantic`

Shared data models for books, carts, customers, orders, payments and fulfilment.

**Path:** `packages/schemas`


### Fulfilment Worker `Python`

Drains the job queue, granting ebook downloads or shipping physical copies and reconciling inventory.

**Path:** `workers/fulfillment`

**Depends on:** Business Services, Data Access Layer, Domain Schemas


### Operations CLI `Python`

Command-line tool for seeding the database and running fulfilment from the terminal.

**Path:** `tools/cli`

**Depends on:** Business Services, Data Access Layer, Fulfilment Worker

- **Command Runner** — Parses terminal commands and dispatches them to seeding, stock and fulfilment operations.
- **Demo Data Seeder** — Loads the demo catalogue, customer accounts and order history.

---

## Deployment

```mermaid
%%{init: {'theme':'neutral'}}%%
graph TB
    subgraph Web_App_Container["Web App Container (Docker Compose, uvicorn)"]
        Web_App_Container_Customer_Storefront["Customer Storefront"]
        Web_App_Container_Staff_Console["Staff Console"]
        Web_App_Container_Public_API["Public API"]
    end
    subgraph Fulfilment_Worker_Container["Fulfilment Worker Container (Docker Compose)"]
        Fulfilment_Worker_Container_Fulfilment_Worker["Fulfilment Worker"]
        Fulfilment_Worker_Container_Operations_CLI["Operations CLI"]
    end
    subgraph PostgreSQL["PostgreSQL (Docker Compose, postgres:16)"]
        PostgreSQL_Bookstore_Database["Bookstore Database"]
    end
    Redis[("Redis (Docker Compose, redis:7)")]
    subgraph MinIO["MinIO (Docker Compose, minio)"]
        MinIO_Object_Storage["Object Storage"]
    end

    Web_App_Container --> PostgreSQL
    Web_App_Container --> Redis
    Web_App_Container --> MinIO
    Fulfilment_Worker_Container --> PostgreSQL
```

**Web App Container** `Docker Compose, uvicorn`
: Serves the storefront, staff console and public API as one ASGI app on port 8000.
  Hosts: Customer Storefront, Staff Console, Public API
  Depends on: PostgreSQL, Redis, MinIO

**Fulfilment Worker Container** `Docker Compose`
: Runs the fulfilment loop through the operations CLI.
  Hosts: Fulfilment Worker, Operations CLI
  Depends on: PostgreSQL

**PostgreSQL** `Docker Compose, postgres:16`
: Database server declared in the compose topology.
  Hosts: Bookstore Database

**Redis** `Docker Compose, redis:7`
: Cache server declared in the compose topology but not used by any code.

**MinIO** `Docker Compose, minio`
: S3-compatible object store for covers and ebook files.
  Hosts: Object Storage
