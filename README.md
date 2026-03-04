# TimeIQ Email Ingestion Service

## Overview

This service automatically **fetches emails from Gmail, filters them using a whitelist, and ingests the email data into the database** for further processing such as **timesheet extraction, classification, and analytics**.

The system integrates **Gmail API with a scalable worker architecture** that allows background email processing.

The application uses a **Redis-backed queue system with background workers** to process emails asynchronously and reliably.

The platform uses:

- **FastAPI** for the API server
- **Gmail API (OAuth2)** for reading emails
- **PostgreSQL** for storing email data
- **Redis** for message queue management
- **Background Workers** for email ingestion
- **Docker Compose** for containerized deployment

---

# Architecture

```
Gmail Account
      │
      ▼
Gmail API (OAuth)
      │
      ▼
Email Polling Service
      │
      ▼
Redis Queue
      │
      ▼
Worker Service
      │
      ▼
Whitelist Filter
      │
      ▼
Database Ingestion
      │
      ▼
Attachments Stored Locally
```

The **polling service fetches new emails** and pushes tasks into **Redis**, while **workers process emails asynchronously**.

This architecture ensures:

- scalability
- reliability
- non-blocking API operations
- easier horizontal scaling

---

# Features

- Fetch **only new emails** using Gmail `historyId`
- **Redis queue based processing**
- **Background worker architecture**
- Email **whitelisting based on client configuration**
- Automatic **thread detection**
- Store:
  - Email threads
  - Email messages
  - Attachments

- Prevent **duplicate message ingestion**
- **Attachment storage system**
- **Docker-ready deployment**

---

# Tech Stack

| Component        | Technology              |
| ---------------- | ----------------------- |
| API              | FastAPI                 |
| Email Provider   | Gmail API               |
| Authentication   | OAuth2                  |
| Database         | PostgreSQL              |
| Queue            | Redis                   |
| Workers          | Async Workers           |
| ORM              | SQLAlchemy (Async)      |
| Containerization | Docker / Docker Compose |

---

# Gmail OAuth Setup

Each user must configure **their own Gmail OAuth credentials**.

This ensures the application can securely access the user's Gmail account.

---

# Step 1 — Create Google Cloud Project

Go to:

```
https://console.cloud.google.com
```

Create a new project.

---

# Step 2 — Enable Gmail API

Navigate to:

```
APIs & Services → Library
```

Enable:

```
Gmail API
```

---

# Step 3 — Create OAuth Client

Navigate to:

```
APIs & Services → Credentials
```

Create:

```
OAuth Client ID
```

Choose:

```
Desktop App
```

Download the credentials file.

---

# Step 4 — Add Credentials to Project

Rename the downloaded file to:

```
credentials.json
```

Place it in the project root.

Example:

```
credentials.json
```

⚠️ **Important**

Do **not commit this file** to Git.

---

# Running the Project with Docker

## Step 1 — Clone the Repository

```
git clone <repository-url>
cd project
```

---

## Step 2 — Add Gmail Credentials

Place your downloaded OAuth file:

```
credentials.json
```

inside the project root.

---

## Step 3 — Start Services

Run:

```
docker compose up --build
```

This will start:

- FastAPI application
- PostgreSQL database
- Redis queue
- Email polling service
- Background worker services

---

# Gmail Authentication

When running the system for the first time:

Open your browser and go to:

```
http://localhost:8000/auth/google
```

Google will prompt you to **log in and grant Gmail access**.

After successful authentication:

```
token.json
```

will be generated automatically.

This token allows the system to access your Gmail account.

---

# Token Storage

The OAuth token is stored locally in:

```
token.json
```

This file contains:

- access token
- refresh token

⚠️ **Do not share or commit this file.**

---

# Email Processing Flow

When a new email arrives:

1. Polling service checks Gmail API for new emails
2. New email IDs are pushed into the **Redis queue**
3. Worker consumes tasks from Redis
4. Email metadata is extracted
5. Sender email is normalized
6. Whitelist table is checked

If sender is allowed:

- Thread is created (if new)
- Email message is stored
- Attachments are downloaded
- Email marked as read

If sender is not whitelisted:

- Email is ignored

---

# Whitelist Configuration

Emails are filtered using the **email_whitelist** table.

Example:

| allowed_email                                     | client_id |
| ------------------------------------------------- | --------- |
| [hr@clientA.com](mailto:hr@clientA.com)           | clientA   |
| [payroll@clientB.com](mailto:payroll@clientB.com) | clientB   |

Only emails from **allowed senders** are processed.

---

# Attachments

Attachments are saved locally in:

```
attachments/
```

Attachment metadata is stored in the database.

---

# API Endpoints

### Health Check

```
GET /
```

Response

```
{
  "status": "Email worker running"
}
```

---

# Important Files

| File               | Purpose                                  |
| ------------------ | ---------------------------------------- |
| auth.py            | Gmail OAuth authentication               |
| service.py         | Gmail API email fetching                 |
| email_whitelist.py | Sender whitelist validation              |
| email_ingestion.py | Email processing logic                   |
| database.py        | Async PostgreSQL connection              |
| models.py          | SQLAlchemy database models               |
| main.py            | FastAPI server and worker initialization |

---

# Security Notes

Do **not commit** the following files:

```
credentials.json
token.json
history.txt
```

Add them to:

```
.gitignore
```

---

# Future Enhancements

Planned improvements include:

- AI-based email classification
- Automatic **timesheet extraction**
- Attachment OCR processing
- Multi-client Gmail account support
- Horizontal worker scaling
- Observability and monitoring
- Email processing dashboards
