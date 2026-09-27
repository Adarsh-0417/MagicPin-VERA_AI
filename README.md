# Vera Engine — magicpin AI Challenge Merchant Assistant

**Vera Engine** is a context-aware AI merchant engagement engine built for the **magicpin Vera AI Challenge**. It combines deterministic business logic with LLM-assisted response generation to decide **when to engage, what to say, and when to stop**.

### 🌐 Live Production Deployment

- **Live Service:** https://magicpin-vera-ai-guml.onrender.com

---

## 1. Architecture

```text
                    ┌──────────────────────────┐
                    │     Judge / API Client   │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │        FastAPI API        │
                    └────────────┬─────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              ▼                  ▼                  ▼
        Context Store       Trigger Ranker     Conversation FSM
              │                  │                  │
              └──────────────────┼──────────────────┘
                                 ▼
                    ┌──────────────────────────┐
                    │      Decision Engine      │
                    │  Send / Wait / End        │
                    └────────────┬─────────────┘
                                 ▼
                    ┌──────────────────────────┐
                    │   Facts + Playbooks      │
                    │   Response Composer       │
                    └────────────┬─────────────┘
                                 ▼
                    ┌──────────────────────────┐
                    │        Validator          │
                    └────────────┬─────────────┘
                                 ▼
                         Final Response
```

### Core Context Model

```text
Category
   +
Merchant
   +
Trigger
   +
Customer
   ↓
Grounded Engagement
```

The system follows the challenge signature:

```python
compose(category, merchant, trigger, customer=None)
```

---

## 2. Key Features

- **Context-aware engagement** across category, merchant, trigger and customer.
- **Trigger ranking** to prioritize relevant merchant actions.
- **Deterministic decision engine** for send / wait / end decisions.
- **Suppression layer** to prevent unnecessary repeated engagement.
- **Conversation state management** for multi-turn interactions.
- **Auto-reply detection** with loop prevention.
- **Intent transition** from conversation to direct action.
- **Grounded response composition** using known business facts.
- **Response validation** to block invalid or unsafe outputs.
- **Docker + Render deployment** for production execution.

---

## 3. Conversation Flow

```text
Incoming Message
       ↓
Intent / Auto-Reply Detection
       ↓
Conversation State
       ↓
 ┌─────┼──────────┐
 ▼     ▼          ▼
SEND  WAIT       END
 │
 ▼
Response Composer
 │
 ▼
Validator
 │
 ▼
Merchant
```

### Auto-Reply Defense

```text
Auto Reply #1 → Follow-up
Auto Reply #2 → WAIT
Auto Reply #3+ → END
```

### Positive Intent

```text
"Ok lets do it. Whats next?"
              ↓
        Action Mode
              ↓
       Next Concrete Step
```

---

## 4. API Endpoints

| Endpoint | Purpose |
|---|---|
| `GET /v1/healthz` | Health / liveness check |
| `GET /v1/metadata` | Engine metadata |
| `POST /v1/context` | Ingest context |
| `POST /v1/tick` | Evaluate active triggers |
| `POST /v1/reply` | Process merchant replies |

Swagger:

**https://magicpin-vera-ai-guml.onrender.com/docs**

---

## 5. Project Structure

```text
MagicPin-VERA_AI/
│
├── app/
│   ├── composer.py
│   ├── context_resolver.py
│   ├── context_store.py
│   ├── conversation_store.py
│   ├── dataset_loader.py
│   ├── decision_engine.py
│   ├── facts.py
│   ├── main.py
│   ├── models.py
│   ├── playbooks.py
│   ├── reply_fsm.py
│   ├── suppression.py
│   ├── trigger_ranker.py
│   └── validator.py
│
├── dataset/
├── examples/
├── judge_simulator.py
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## 6. Tech Stack

**Python · FastAPI · Pydantic · Gemini · Docker · Render · OpenAPI/Swagger**

---

## 7. Local Setup

```bash
git clone <your-repository-url>
cd MagicPin-VERA_AI

python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
```

Set the Gemini API key:

```bash
GEMINI_API_KEY=YOUR_API_KEY
```

Run:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open:

```text
http://127.0.0.1:8000/docs
```

---

## 8. Design Principle

> **Code decides. Context grounds. LLM composes. Validator protects.**

The architecture intentionally keeps business decisions outside the LLM. This makes the system more predictable, testable and resistant to hallucinated merchant data.

---

## Built for the magicpin Vera AI Challenge

**Context-aware • Stateful • Grounded • Trigger-driven**
