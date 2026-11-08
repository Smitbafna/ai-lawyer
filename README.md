# AI Lawyer - Tenant–Landlord Dispute Intake (M1)

Project foundation and conversational case intake engine for tenant–landlord
disputes in India, focused on security deposit refund disputes.

## Architecture

### Backend (`backend/`)
- **FastAPI** application with modular structure
- **SQLAlchemy** ORM with SQLite database
- **Pydantic** v2 for validation and schemas
- **Gemini API** via a provider-independent adapter (`llm/provider.py`)
- **Mock provider** for deterministic testing (`tests/mock_provider.py`)

### Frontend (`frontend/`)
- **React + TypeScript** with Vite
- Plain CSS (no Tailwind)
- Chat interface with case summary panel

### Directory Structure
```
backend/
  app/
    main.py              # FastAPI app entry point
    api/
      cases.py           # Case CRUD endpoints
      chat.py            # Chat/intake endpoints
      deps.py            # Dependency injection
    orchestrator/
      workflow.py        # Intake workflow orchestration
    agents/
      intake.py          # Intake agent with LLM integration
    services/
      case_service.py    # Case database operations
      conversation_service.py  # Conversation/message operations
    schemas/
      case.py            # Case Pydantic schemas
      conversation.py    # Conversation/chat Pydantic schemas
    database/
      connection.py      # SQLAlchemy connection
      models.py          # DB models (Case, Conversation, Message)
    llm/
      provider.py        # LLM provider interface
      gemini_provider.py # Gemini implementation
    core/
      config.py          # Application settings
  tests/
    test_cases.py        # Case API tests
    test_intake.py       # Intake agent tests
    test_conversation.py # Conversation persistence tests
    test_workflow.py     # Workflow orchestration tests
    mock_provider.py     # Mock LLM provider for tests
frontend/
  src/
    components/          # React components
    pages/               # Page components
    services/            # API service layer
    types/               # TypeScript type definitions
```

## Installation

### Backend

```bash
cd /home/smit-bafna/Projects/kuku/backend
cp .env.example .env
# Edit .env and set GEMINI_API_KEY if you want to use the real Gemini API
pip install -r requirements.txt
```

### Frontend

```bash
cd /home/smit-bafna/Projects/kuku/frontend
npm install
```

## Running

### Backend

```bash
cd /home/smit-bafna/Projects/kuku/backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`. Health check: `GET /health`

### Frontend

```bash
cd /home/smit-bafna/Projects/kuku/frontend
npm run dev
```

The frontend will be available at `http://localhost:3000`. It proxies `/api` requests to `http://localhost:8000`.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/cases` | Create a new case (status: `intake_in_progress`) |
| GET | `/cases/{case_id}` | Get current structured case |
| PATCH | `/cases/{case_id}` | Update case facts |
| POST | `/cases/{case_id}/chat` | Send a message and run intake workflow |
| GET | `/cases/{case_id}/messages` | Get conversation history |

### POST /cases
Response: Case object with `id`, `case_type`, `status`, etc.

### POST /cases/{case_id}/chat
Request: `{ "message": "string" }`
Response: `{ "assistant_message", "updated_case", "missing_information", "intake_status" }`

## Testing

```bash
cd /home/smit-bafna/Projects/kuku/backend
python3 -m pytest tests/ -v --asyncio-mode=auto
```

Tests use a mock LLM provider and do not require a Gemini API key. All 17 tests pass.

## Environment Variables

See `.env.example` for required variables:
- `GEMINI_API_KEY` - Your Gemini API key (optional for tests, required for real LLM)
- `GEMINI_MODEL` - Gemini model name (default: `gemini-1.5-flash`)
- `DATABASE_URL` - SQLite database URL (default: `sqlite:///./app.db`)

## Completion Criteria (M1)

1. ✅ Backend starts successfully
2. ✅ Frontend starts successfully
3. ✅ User can create a case
4. ✅ User can describe a dispute in natural language
5. ✅ System extracts structured facts
6. ✅ System asks relevant follow-up questions
7. ✅ Case is updated across multiple turns
8. ✅ Conversation history persists in SQLite
9. ✅ Case summary updates in the frontend
10. ✅ All automated tests pass
11. ✅ README contains installation and execution instructions
12. ✅ `.env.example` documents required environment variables


## M1.2 Reliability and Data Integrity Notes

- Fact corrections: the intake agent distinguishes explicit user corrections
  (`corrections`) from ordinary new information (`extracted_updates`). Conflicting
  values preserve the existing fact and are reported in `confirmation_needed`
  until the user confirms.
- Fact provenance: each fact records `source` (`model` or `user`),
  `confirmed` (boolean), and `turn`. Existing SQLite records without
  provenance are treated as having an empty provenance map.
- Atomic persistence: a chat turn reads the case, calls the LLM outside any
  transaction, then persists the user message, updated facts, and assistant
  message in a single transaction. A failed LLM call leaves no orphaned
  message or partial fact update. Optimistic versioning rejects concurrent
  conflicting updates with HTTP 409.
- LLM reliability: the Gemini provider uses a bounded timeout, retries bounded
  retryable failures (HTTP 429 / 503) with exponential backoff, and does not
  retry timeouts, invalid JSON, or schema-validation failures.
- Authentication/authorization: none. This application is a single-user /
  local-prototype only and must not be deployed on an untrusted or multi-user
  network. CORS is restricted to the local frontend origins
  (`http://localhost:3000`, `http://127.0.0.1:3000`).

## Known Limitations

- Only supports `security_deposit_dispute` case type
- No RAG, legal research, or document generation (out of scope for M1)
- LLM integration requires a Gemini API key for real usage (mock provider for tests)
- Frontend is minimal and functional without animations or visual polish
- Hindi translation and voice input not implemented
- No authentication or authorization; single-user/local-prototype only
## M2.1B — Legal Knowledge Base

The `M2.1B/` directory contains the legal research knowledge base for tenant-landlord
security-deposit disputes in India:

- `provision_inventory.md` — provision-level inventory (central + state/UT statutes)
- `source_register.md` — source register
- `state_applicability_table.md` — state/UT applicability table
- `temporal_metadata.md` — temporal metadata recommendations
- `evaluation_dataset.md` — clean evaluation dataset (32 cases)
- `research_notes/` — methodology, verification backlog, open questions
- `sources/` — cached reference excerpts

See `M2.1B/INDEX.md` for the full index.
## Scope Clarification

This AI Lawyer application is currently **just for Uttarakhand**, not for all of India.

### Supported Jurisdiction:
- **Uttarakhand** — Uttarakhand Tenancy Act, 2021 (Act No. 02 of 2022), commenced 01.01.2023
- Security deposit cap: 2 months rent (residential), 6 months rent (non-residential)
- Refund on vacant possession after liability deduction

### Unsupported Jurisdictions (explicitly marked):
- Tamil Nadu — Tamil Nadu Regulation of Rights and Responsibilities of Landlords and Tenants Act, 2017
- Uttar Pradesh — Uttar Pradesh Regulation of Urban Premises Tenancy Act, 2021
- No other states/UTs are in the supported corpus

### Technical Implementation:
- Jurisdiction is **server-enforced** as `'Uttarakhand'` — the API rejects any attempts to override jurisdiction
- Chroma vector store collection name: `uttarakhand_provisions`
- All legal provisions are traced to Uttarakhand Gazette (SRC-02)
