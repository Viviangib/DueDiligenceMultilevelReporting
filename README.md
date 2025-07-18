# Sustainability Standards Benchmarking Backend

## Overview

This backend system benchmarks Voluntary Sustainability Standards (VSS) against regulatory requirements using LLMs (GPT-4o mini) and Retrieval-Augmented Generation (RAG) with Pinecone. It supports document upload, indicator extraction, regulatory evidence retrieval, alignment analysis, and summary report generation.

## Features

- Upload VSS and regulation documents (PDF/DOCX)
- Extract indicators from VSS using LLM
- Retrieve regulatory evidence for each indicator (RAG)
- Analyze alignment between VSS and regulations (GPT-4o mini)
- Save results to Excel
- Generate professional summary reports (Markdown)
- Robust logging and error handling
- API authentication for all endpoints

## Project Setup

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd backend
   ```
2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv benv
   source benv/bin/activate
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Set environment variables:**
   - Copy `config.py.example` to `config.py` and fill in your OpenAI API key, Pinecone API key, and other settings.
   - Example (in `.env` or shell):
     ```bash
     export OPENAI_API_KEY=your-key
     export PINECONE_API_KEY=your-key
     ```
5. **Run database migrations (if using Alembic):**
   ```bash
   alembic upgrade head
   ```
6. **Start the server:**
   ```bash
   uvicorn server:app --reload
   ```

## API Authentication

- All endpoints require authentication via a Bearer token.
- Obtain a token via `/auth/login` and include it in the `Authorization` header:
  ```http
  Authorization: Bearer <your_token>
  ```

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

- `POST /analysis/run` — Run alignment analysis on uploaded indicators
- `GET /analysis/{analysis_id}` — Get analysis results/status
- `POST /analysis/generate-report` — Generate summary report from Excel file
- `POST /analysis/generate-report-upload` — Generate summary report from uploaded Excel

## Logging & Debugging

- All major steps (file upload, extraction, LLM calls, batch processing, saving results) are logged.
- Logs include batch/chunk numbers, file names, status updates, and errors.
- Check logs for progress and troubleshooting.

## Example Usage

1. **Sign up and log in to get a token.**
2. **Upload a VSS document for indicator extraction.**
3. **Check extraction status and download indicators.**
4. **Upload regulation document.**
5. **Run analysis.**
6. **Generate and download summary report.**

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
