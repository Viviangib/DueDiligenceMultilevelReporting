# Sustainability Standards Benchmarking Backend

## Overview

This backend benchmarks Voluntary Sustainability Standards (VSS) against regulatory requirements using LLMs (GPT-4o mini) and Retrieval-Augmented Generation (RAG) with Pinecone. It supports document upload, indicator extraction, regulatory evidence retrieval, alignment analysis, and summary report generation.

---

## Features

- Upload VSS and regulation documents (PDF/DOCX)
- Extract indicators from VSS using LLM
- Retrieve regulatory evidence for each indicator (RAG)
- Analyze alignment between VSS and regulations (GPT-4o mini)
- Save results to Excel
- Generate professional summary reports (Markdown)
- Robust logging and error handling
- API authentication for all endpoints
- Dynamic Pinecone namespace selection for analysis

---

## Prerequisites

- **Python 3.9+** (recommend 3.10 or newer)
- **PostgreSQL** (or your configured DB)
- **Pinecone account** (for vector search)
- **OpenAI API key**

---

## Setup Instructions (Step-by-Step for Beginners)

### 1. Install Python

- Download and install Python from [python.org](https://www.python.org/downloads/).
- Verify installation:
  ```bash
  python3 --version
  ```

### 2. Clone the Repository

```bash
# In your terminal:
git clone <repo-url>
cd DueDiligenceMultilevelReporting
```

### 3. Create and Activate a Virtual Environment

```bash
python3 -m venv benv
source benv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Set Up Environment Variables

- Copy `config.py.example` to `config.py` and fill in your OpenAI API key, Pinecone API key, DB URL, and other settings.
- Or create a `.env` file in the root directory with:
  ```env
  OPENAI_API_KEY=your-openai-key
  PINECONE_API_KEY=your-pinecone-key
  PINECONE_INDEX_NAME=your-index
  PINECONE_NAMESPACE=your-default-namespace
  DATABASE_URL=postgresql://user:password@localhost:5432/yourdb
  REGION=us-east-1
  CLOUD=aws
  ```

### 6. Initialize the Database

- Make sure PostgreSQL is running and your DB exists.
- **Apply migrations to create all tables:**
  ```bash
  alembic upgrade head
  ```
  (You should run this command every time you set up a new database or after pulling new migrations.)

### 7. Start the Server

```bash
uvicorn server:app --reload
```

- The API will be available at `http://127.0.0.1:8000` by default.

---

## API Authentication

- All endpoints require authentication via a Bearer token.
- Register a user and log in to get a token:
  1. `POST /auth/signup` — Register a new user
  2. `POST /auth/login` — Obtain JWT token
- Include the token in the `Authorization` header for all requests:
  ```http
  Authorization: Bearer <your_token>
  ```

---

## API Endpoints

### Auth

- `POST /auth/signup` — Register a new user
- `POST /auth/login` — Obtain JWT token

### Indicator Extraction

- `POST /indicators/extract` — Upload VSS (PDF/DOCX) for indicator extraction
- `GET /indicators/extract/status/{status_id}` — Download extracted indicators Excel
- `POST /indicators/upload` — Upload indicators from Excel

### Regulation Upload

- `POST /regulations/upload` — Upload regulation PDF
- `GET /regulations/{regulation_id}/status` — Check embedding status

### Analysis

- `POST /analysis/run` — **Run alignment analysis on uploaded indicators**
  - **Required fields:**
    - `vss_files`: List of VSS files (PDF/DOCX)
    - `process_id`: String (or leave blank to auto-generate)
    - `namespace`: **String, Pinecone namespace to use for RAG search**
  - **Example (using curl):**
    ```bash
    curl -X POST "http://127.0.0.1:8000/api/v1/analysis/run" \
      -H "Authorization: Bearer <your_token>" \
      -F "vss_files=@/path/to/your/vss.pdf" \
      -F "process_id=your-process-id" \
      -F "namespace=your-pinecone-namespace"
    ```
  - If the namespace does not exist, you will get a clear error message.
- `GET /analysis/{analysis_id}` — Get analysis results/status
- `POST /analysis/generate-report-upload` — Generate summary report from uploaded Excel

---

## Example Usage Flow

1. **Sign up and log in to get a token.**
2. **Upload a VSS document for indicator extraction.**
3. **Check extraction status and download indicators.**
4. **Upload regulation document.**
5. **Run analysis:**
   - Specify the correct Pinecone namespace (ask your admin or check your Pinecone dashboard).
   - If you use a namespace that does not exist, the API will return an error.
6. **Generate and download summary report.**

---

## Directory Structure

```
backend/
  alembic/           # DB migrations
  config.py          # Configuration
  constants/         # Hardcoded values
  controllers/       # Business logic
  db/                # DB setup
  enums/             # Enums
  models/            # ORM models
  routers/           # FastAPI routers
  schemas/           # Pydantic schemas
  services/          # Core services
  utils/             # Utilities (LLM, extraction, prompts)
  vector_store/      # Pinecone integration
  results/           # Output files
  vss_uploads/       # Uploaded VSS docs
```

---

## Logging & Debugging

- All major steps (file upload, extraction, LLM calls, batch processing, saving results) are logged.
- Logs include batch/chunk numbers, file names, status updates, and errors.
- The Pinecone namespace used for each RAG search is logged.
- Check logs for progress and troubleshooting.

---

## Troubleshooting & FAQ

**Q: I get a migration error or missing revision error.**

- Make sure you have deleted old migration files and the `alembic_version` table if resetting migrations.
- Run `alembic revision --autogenerate -m "Initial"` and then `alembic upgrade head`.

**Q: I get a Pinecone namespace error.**

- Make sure the namespace you provide exists in your Pinecone index.
- You can check existing namespaces in your Pinecone dashboard or via the API.

**Q: My environment variables are not being picked up.**

- Make sure you have a `.env` file or have set the variables in your shell.
- Restart your terminal and server after making changes.

**Q: How do I see logs?**

- Logs are printed to the console by default. Check your terminal for info, warnings, and errors.

**Q: How do I run this on Windows?**

- Use `python -m venv benv` and `benv\Scripts\activate` to activate your virtual environment.
- All other commands are the same.

---

## Contact & Support

For questions or support, please contact the project maintainer or open an issue in the repository.
