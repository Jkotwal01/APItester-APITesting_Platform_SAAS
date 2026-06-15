# AITester Architecture & Client Guide

Welcome to the **AITester** platform guide! This document provides a comprehensive overview of how the system works under the hood. It is designed to help developers, maintainers, and clients understand the architecture, data flow, and components of this AI-Powered API Testing SaaS.

---

## 🏗️ High-Level Architecture

AITester is built as a modern, asynchronous Python application. It takes an OpenAPI specification as input, intelligently generates a comprehensive suite of test cases (including AI-driven business logic tests), executes them asynchronously against a target API, analyzes the results for failures and security flaws, and generates rich HTML/JSON reports.

The project is structured into distinct, decoupled layers:

### 1. API Layer (`aitester/api/`)
The entry point for the SaaS platform, built with **FastAPI**.
- **Routes**: Manages Projects, Test Runs, and Reports.
- **Background Tasks**: Test execution is heavily asynchronous. When a user triggers a test run, the API queues the execution in the background so the HTTP request doesn't block.
- **Dependencies & Schemas**: Handles database session injection and Pydantic validation for incoming requests.

### 2. CLI Layer (`aitester/cli/`)
For local development and CI/CD integration, AITester provides a powerful CLI built with **Typer**.
- It allows users to parse specs (`analyze`), execute test suites (`run`), and generate visual reports (`report`) directly from the terminal without spinning up the FastAPI server.

### 3. Parser Layer (`aitester/parser/`)
The foundation of the testing engine. 
- It ingests an OpenAPI (Swagger) v3 specification (JSON or YAML) from a file or URL.
- It normalizes the specification into structured internal Pydantic models (`ParsedSpec`, `ParsedEndpoint`, `ParsedParameter`, etc.), ignoring the complexities of the raw OpenAPI format for the rest of the application.

### 4. Generation Layer (`aitester/generators/`)
This is where the magic happens. The `TestGenerationCoordinator` orchestrates multiple specialized generators to create `TestCase` objects for each API endpoint:
- **FunctionalGenerator**: Creates standard "happy path" tests (e.g., Status 200 checks).
- **EdgeCaseGenerator**: Creates boundary tests (e.g., missing required fields, invalid types, empty payloads) to ensure the API handles bad data gracefully.
- **SecurityGenerator**: Generates malicious payloads to test for common vulnerabilities like SQL Injection, Path Traversal, and XSS.
- **BusinessLogicGenerator (AI)**: Hooks into the AI Engine to generate complex, context-aware tests based on the endpoint's description and parameters.

### 5. Execution Layer (`aitester/executor/`)
Responsible for running the generated test cases against the target API.
- Built on top of **httpx**, it executes HTTP requests asynchronously (`AsyncTestRunner`), allowing hundreds of tests to run concurrently.
- It captures the actual status codes, response times, and raw response bodies, creating `TestResult` records.

### 6. Security Analysis Layer (`aitester/security/`)
Once tests are executed, the results are scanned for vulnerabilities.
- **Detector**: Analyzes response bodies and headers to detect if a security payload was successful (e.g., detecting database error messages indicating SQLi).
- **Scorer**: Aggregates the findings and calculates an overall security score out of 100 for the test run.

### 7. AI Engine Layer (`aitester/ai/`)
Powered by **Google's Gemini** models, this layer adds deep intelligence to the platform.
- **Client**: Manages rate-limited, asynchronous communication with the Gemini API.
- **Validators**: Enforces strict JSON schemas on the AI's output using Pydantic, automatically retrying if the AI hallucinates bad JSON.
- **Failure Analyzer**: When a test fails, it sends the request payload and error response to Gemini to determine the root cause and suggest a fix.
- **Risk Scorer**: Evaluates the severity of security findings to generate an executive risk summary.

### 8. Reporting Layer (`aitester/reports/`)
Transforms raw database results into beautiful, actionable formats.
- **Metrics Calculator**: Aggregates pass rates, average latencies, and category breakdowns.
- **HTML/JSON Generators**: Uses **Jinja2** templates to render premium, dark-mode, responsive HTML reports that executives and developers can easily consume.

### 9. Database Layer (`aitester/db/`)
Built with **SQLAlchemy 2.0 (async)** and **PostgreSQL**.
- Stores Projects, Test Runs, Test Cases, and Test Results.
- Uses Alembic for database migrations.

---

## 🔄 The Test Run Workflow

When a client initiates a test run (via the API or CLI), the system follows this exact lifecycle:

1. **Ingest & Parse**: The OpenAPI spec is fetched and parsed into internal models.
2. **Generate**: The `TestGenerationCoordinator` iterates through every endpoint and invokes the requested generators (Functional, Edge, Security, AI).
3. **Save State**: The generated `TestCase` models are saved to the database with a status of `RUNNING`.
4. **Execute**: The `AsyncTestRunner` fires all requests concurrently against the target API base URL.
5. **Analyze**: The responses are captured. Failed tests trigger the AI Failure Analyzer to determine *why* they failed. Security tests are routed through the Security Detector.
6. **Finalize**: `TestResult` models are saved to the database. The run is marked as `COMPLETED`.
7. **Report**: The user requests a report, which aggregates the data, passes security findings to the AI Risk Scorer for a summary, and renders the final HTML/JSON output.

---

## 🛠️ Technology Stack Summary

| Component | Technology | Purpose |
|---|---|---|
| **Web Framework** | FastAPI | High-performance async API server |
| **CLI Framework** | Typer | Terminal commands (`aitester run`) |
| **Database ORM** | SQLAlchemy 2.0 | Async database operations |
| **Database System**| PostgreSQL + asyncpg | Relational data storage |
| **Caching / Queues**| Redis + aioredis | Rate limiting, async task coordination |
| **HTTP Client** | httpx | High-concurrency async HTTP requests |
| **AI Integration** | Google Gemini SDK | Logic generation & failure analysis |
| **Data Validation**| Pydantic V2 | Strict typing for spec and AI outputs |
| **Templating** | Jinja2 | HTML report generation |
| **Migrations** | Alembic | Database schema versioning |

---

## 🎯 Value for Clients

By utilizing this architecture, clients achieve:
- **Zero-Configuration Testing**: No need to write hundreds of manual test scripts. Just provide a Swagger/OpenAPI file.
- **Deep Coverage**: Edge cases and malicious payloads are generated automatically.
- **Intelligent Debugging**: When a test fails, the AI explains the exact cause and suggests code fixes, drastically reducing developer debugging time.
- **Executive Visibility**: The HTML reports provide clear metrics (Pass Rates, Security Scores, Latency) for stakeholders, while retaining deep technical logs for engineers.

---

## 🚀 How to Use the Software

AITester can be used as a CLI tool or deployed as an API/SaaS platform. Before starting, ensure that you have your environment variables set up, particularly `GEMINI_API_KEY` for AI features and `DATABASE_URL` (plus `REDIS_URL`) for local infrastructure if using the full pipeline.

### Option 1: Using the Command Line Interface (CLI)
The CLI is perfect for local testing and CI/CD pipelines.

**1. Analyze an OpenAPI Spec**
Validates and parses a given specification file or URL.
```bash
poetry run aitester analyze path/to/openapi.yaml
```

**2. Run a Full Test Suite**
Generates and executes tests against a live endpoint. You can specify which types of tests to run (functional, edge, security, ai).
```bash
poetry run aitester run path/to/openapi.yaml https://api.example.com --types functional,edge,security,ai --enable-ai
```

**3. Generate a Report**
After a run completes, generate a beautiful HTML report from the results.
```bash
poetry run aitester report <TEST_RUN_ID> --format html
```

*Note: For a fully standalone quick-start demonstration bypassing the local database requirement, you can run the `generate_report.py` script included in the root directory.*

### Option 2: Using the FastAPI Server
The API server is ideal for integrating AITester into web dashboards, SaaS platforms, and enterprise workflows.

**1. Start the Server**
Ensure your PostgreSQL and Redis instances are running (e.g. via `docker-compose up -d`), then start the FastAPI application:
```bash
poetry run uvicorn aitester.api.main:app --reload
```

**2. Trigger a Test Run (via HTTP)**
Send a `POST` request to create a new test run for a specific project:
```http
POST /api/v1/projects/{project_id}/runs
Content-Type: application/json

{
  "spec_path": "path/or/url/to/openapi.yaml",
  "base_url": "https://api.example.com",
  "types": ["functional", "edge", "security", "ai"],
  "enable_ai": true
}
```
*The execution happens asynchronously in the background. The API will respond immediately with a `202 Accepted` and a `run_id`.*

**3. Check Status and Fetch Reports**
Use the `run_id` to poll for the status of the run:
```http
GET /api/v1/runs/{run_id}/status
```

Once completed, you can fetch the final interactive HTML report:
```http
GET /api/v1/runs/{run_id}/report/html
```
