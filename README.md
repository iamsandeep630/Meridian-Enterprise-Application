# Meridian Enterprise Application

Employee IT & Finance Helpdesk Portal featuring the **Self-Help AI Copilot Agent**, Confluence Knowledge Base RAG, MeshCentral Remote Diagnostics & Atlassian Jira Cloud Integration.

---

## Overview

- **Port**: `8001`
- **Default User**: Maya Sharma (`maya.sharma@meridian.com` / `password123`)
- **Agent**: Self-Help AI Copilot (`SelfHelpAgent` powered by AWS Bedrock Claude 3 Haiku / Sonnet)
- **Database**: SQLite (`backend/database/shopmart.db`)
- **Knowledge Base**: Confluence RAG with Dense FAISS + Lexical BM25 Hybrid Retriever
- **Remote Diagnostics**: MeshCentral integration for 30-min ephemeral remote desktop links & Zoom cache clearing
- **Jira Integration**: Directly creates and escalates tickets in Jira Cloud with embedded **'Chat with User'** and **'Remote Device'** links

---

## Directory Layout

```
Meridian Enterprise Application/
├── run.py                     # Entry point (port 8001)
├── .env                       # Environment variables
├── requirements.txt           # Dependencies
├── backend/                   # Backend Python subsystem
│   ├── main.py                # FastAPI entry point
│   ├── config.py              # Configuration & settings
│   ├── schemas.py             # Pydantic schemas
│   ├── tools.py               # Tool registry & execution dispatcher
│   ├── auth/                  # Authentication & JWT security
│   ├── routers/               # API & page routers (Self-Help agent only)
│   ├── agents/                # Self-Help Agent & system prompt
│   ├── database/              # SQLite connection, models & seed data
│   ├── services/              # MeshCentral, Jira & Escalation services
│   ├── knowledge_base/        # Confluence RAG indexer & hybrid retriever
│   └── uploaded_tax_documents/# Tax document uploads
└── frontend/                  # Frontend UI subsystem
    ├── templates/             # HTML templates (Employee Portal, Chat, Login)
    │   ├── employee_portal.html
    │   ├── support_chat.html  # Live SSE chat window for Maya & Alex
    │   ├── customer_store.html
    │   └── login.html
    └── static/                # Static assets (CSS, JS, icons)
```

---

## Running the Application

```bash
cd "Meridian Enterprise Application"
python run.py
```

Access the portal at: **http://localhost:8001**
- Employee Portal: `http://localhost:8001/` or `http://localhost:8001/portal`
- Support Chat Window: `http://localhost:8001/support/chat/{sessionId}`
