# AITester — AI-Powered Universal API Testing Platform

> Give it your OpenAPI spec. Get back hundreds of tests, a security audit,
> and AI-powered failure analysis — automatically.

## Quick Start

```bash
# Clone and setup
git clone https://github.com/your-username/aitester.git
cd aitester

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt -r requirements-dev.txt

# Copy environment config
cp .env.example .env
# Edit .env with your GEMINI_API_KEY

# Start infrastructure
docker compose -f docker/docker-compose.yml up -d

# Run migrations
alembic upgrade head

# Start the API server
uvicorn aitester.main:app --reload

# Run via CLI
aitester analyze path/to/openapi.yaml
aitester run --spec path/to/openapi.yaml --base-url http://your-api.com
```

## Features

- 📋 **OpenAPI Parser** — Parses OpenAPI 3.x specs (file or URL), resolves `$ref`
- 🧪 **Functional Test Generator** — Auto-generates happy-path tests
- ⚡ **Edge Case Generator** — Boundary, null, overflow, type-mismatch tests
- 🤖 **AI Business Logic Tests** — Google Gemini infers domain-specific rules
- 🔐 **Security Testing** — OWASP Top 10: SQLi, XSS, Path Traversal, Command Injection, JWT
- ⚡ **Async Executor** — 50 concurrent tests via httpx + asyncio
- 🔍 **AI Failure Analysis** — Gemini explains *why* each test failed
- 📊 **HTML + JSON Reports** — Full coverage dashboard with AI executive summary
- 🐳 **Docker Ready** — Multi-stage build, docker-compose full stack
- 🔄 **GitHub Actions CI/CD** — Lint → Test → Docker → Self-test pipeline

## Project Structure

```
aitester/
├── api/          FastAPI routers
├── cli/          Typer CLI commands
├── parser/       OpenAPI spec parser
├── generators/   Test case generators
├── ai/           Gemini AI engine
├── executor/     Async HTTP test runner
├── security/     Security payload library
├── reports/      HTML/JSON report builder
├── db/           SQLAlchemy models + migrations
└── core/         Config, logging, exceptions
```

## CLI Reference

```bash
aitester analyze --spec ./api.yaml           # Parse and display spec
aitester generate --spec ./api.yaml          # Generate test cases
aitester run --spec ./api.yaml --base-url http://api.example.com  # Full run
aitester report --run-id <uuid> --format html  # Generate report
```

## License

MIT
