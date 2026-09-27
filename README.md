# PostCare AI

**A multi-agent system for monitoring heart-failure patients after hospital discharge — detecting recovery deviations early using RAG-grounded clinical reasoning.**

Heart-failure patients have one of the highest 30-day hospital readmission rates (~20–25%), and most readmissions are preventable if early warning signs are caught in time. PostCare AI runs a daily patient check-in through a pipeline of specialized AI agents that compare the patient's trajectory against clinical guidelines, detect dangerous deviations, and escalate high-risk cases — turning a discharge paper into continuous, intelligent monitoring.

---

## What it does

A patient submits a daily check-in (pain level, symptoms, medication adherence, weight, reason for any missed dose). The system:

1. **Stores** the check-in and reconstructs the patient's recovery history from a database.
2. **Analyzes the trajectory** — is the patient improving, stable, or declining over time?
3. **Detects deviations** by comparing the trajectory against a RAG knowledge base built from real heart-failure clinical guidelines.
4. **Triages risk** (LOW / MEDIUM / HIGH) and generates a plain-language recommendation.
5. **Routes** the outcome — stable patients get monitoring guidance; deviating patients are flagged for clinician attention.

---

## Architecture

```
Patient check-in
      │
      ▼
  FastAPI  (async /check_in endpoint)
      │
      ├──► PostgreSQL  — save check-in, fetch patient history
      │
      ▼
  LangGraph pipeline
      │
      ├─ Agent 1: State Analyst      → builds recovery trajectory from history
      ├─ Agent 2: Deviation Detector → RAG search vs. clinical guidelines → deviation? (bool)
      │        │
      │        └─ conditional routing
      │             ├─ no deviation → END (stable)
      │             └─ deviation    → Agent 3
      │
      └─ Agent 3: Risk Triager       → risk level + recommendation
      │
      ▼
  Structured JSON response
```

### Why multi-agent?

Each agent has one specialized job and communicates only through a shared state object. This separation of concerns produces sharper output than a single monolithic prompt, and the conditional routing means stable patients skip unnecessary risk analysis — mirroring how a real triage system avoids alert fatigue.

---

## Tech stack

| Layer | Technology | Purpose |
|---|---|---|
| Backend API | FastAPI (async) | Receives check-ins, returns structured decisions |
| Agent orchestration | LangGraph | Multi-agent pipeline with conditional routing |
| LLM | Groq (LLaMA / GPT-OSS) | Reasoning inside each agent |
| Knowledge base | ChromaDB + HuggingFace embeddings (`all-MiniLM-L6-v2`) | RAG over clinical guidelines |
| Document ingestion | PyPDFLoader + RecursiveCharacterTextSplitter | Builds the medical knowledge base |
| Database | PostgreSQL (`psycopg`) | Stores check-ins, reconstructs patient history |
| Config | python-dotenv | Environment-based secrets, deployment-ready |

---

## Project structure

```
postcare-ai/
├── main.py        # FastAPI app — /check_in endpoint
├── agents.py      # AgentState + the 3 agents + LangGraph graph
├── database.py    # PostgreSQL connection, save_checkin, fetch_history
├── ingest.py      # Builds the ChromaDB medical knowledge base
├── requirements.txt
├── .gitignore
└── data/          # (gitignored) place a heart-failure clinical guideline PDF here
```

---

## Running locally

**Prerequisites:** Python 3.11+, PostgreSQL running locally, a Groq API key.

1. **Clone and install**
   ```bash
   git clone https://github.com/antariksha-agi/postcare-ai.git
   cd postcare-ai
   pip install -r requirements.txt
   ```

2. **Set up the database.** Create a `checkins` table:
   ```sql
   CREATE TABLE checkins (
       id SERIAL PRIMARY KEY,
       patient_id TEXT,
       checkin_date TIMESTAMP DEFAULT NOW(),
       pain_lvl INT,
       symptoms TEXT,
       medication_taken BOOLEAN,
       weight FLOAT,
       missed_reason TEXT
   );
   ```

3. **Add a knowledge base.** Place a heart-failure clinical guideline PDF in `data/`
   (e.g. an AHA post-discharge guideline). Then run `ingest.py` to build the vector store.
   *The PDF is not included in this repo for copyright reasons — supply your own source.*

4. **Configure environment.** Create a `.env` file:
   ```
   GROQ_API_KEY=your_groq_key
   TAVILY_API_KEY=your_tavily_key
   DB_HOST=localhost
   DB_NAME=postgres
   DB_USER=postgres
   DB_PASSWORD=your_db_password
   DB_PORT=5432
   ```

5. **Run**
   ```bash
   uvicorn main:app --reload
   ```
   Open `http://127.0.0.1:8000/docs` and test the `/check_in` endpoint.

### Example

**Request**
```json
{
  "patient_id": "patient_1",
  "pain_lvl": 7,
  "symptoms": "breathlessness, swelling",
  "medication_taken": false,
  "weight": 74.5,
  "missed_reason": "forgot"
}
```

**Response**
```json
{
  "trajectory": "Patient declining — pain rising, weight up 2.5kg over 3 days, diuretic missed...",
  "deviation": true,
  "risk_level": "High",
  "recommendation": "Contact your healthcare provider promptly to discuss worsening symptoms..."
}
```

---

## Design decisions & what I learned

- **Temporal intelligence over snapshots.** A single check-in can't reveal deterioration — the State Analyst compares against stored history, so the system reasons about *trends*, not isolated readings.
- **RAG-grounded decisions.** The Deviation Detector doesn't guess what's dangerous — every judgment is grounded in retrieved clinical guidelines, making the reasoning traceable rather than hallucinated.
- **Defensive LLM parsing.** LLM output format is never guaranteed, so parsing is hardened (case-normalization, fallback defaults) to avoid crashes on unexpected responses.
- **Deployment-ready config.** Database and API credentials are read from environment variables with sensible local defaults, so the same code runs locally and in the cloud without changes.

---

## Future work

- **WhatsApp interface** via Twilio — let patients check in conversationally instead of through an API form.
- **n8n orchestration** — route high-risk alerts to clinicians over SMS/WhatsApp and track acknowledgement (delivery ≠ acknowledgement).
- **Structured LLM outputs** — replace string-parsing with a typed decision model (e.g. a System-One model like Jev) for faster, hallucination-free classification.
- **Cloud deployment** — the RAG stack (torch + sentence-transformers) exceeds free-tier memory limits; a hosted embedding API would make full cloud deployment viable.
- **Ragas evaluation** — add automated retrieval-quality metrics to measure how well the knowledge base grounds each decision.

---

## Note

This is a portfolio project built for learning, not a certified medical device. It does not provide medical advice and must not be used for real clinical decisions. Any real-world use would require clinical oversight, validation, and regulatory review.

---

*Built by Antariksha Mandal.*
