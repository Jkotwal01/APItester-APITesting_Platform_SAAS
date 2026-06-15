#!/bin/bash

# AITester Full E2E Demo Script
# This script starts the required infrastructure and runs AITester against a mock spec.

set -e

echo "========================================="
echo " AITester Interactive Demo"
echo "========================================="

echo "[1/4] Starting infrastructure via Docker Compose..."
docker compose -f docker/docker-compose.yml up -d
echo "Waiting for PostgreSQL and Redis to initialize..."
sleep 5

echo "[2/4] Running Database Migrations..."
alembic upgrade head || echo "Alembic migrations failed. Ensure DB is accessible."

echo "[3/4] Preparing Demo OpenAPI Specification..."
cat << 'EOF' > demo-spec.yaml
openapi: 3.0.0
info:
  title: Demo API
  version: 1.0.0
paths:
  /users:
    post:
      summary: Create a user
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [username, email]
              properties:
                username:
                  type: string
                email:
                  type: string
                  format: email
      responses:
        '201':
          description: Created
EOF

echo "[4/4] Executing AITester..."
# Run AITester CLI to analyze and test
echo "> Running spec analysis..."
aitester analyze demo-spec.yaml || echo "Make sure aitester is installed (pip install -e .)"

echo "> Running full test suite on http://localhost:8000 ..."
# Replace this with an actual demo API endpoint if available
RUN_ID=$(aitester run --spec demo-spec.yaml --base-url http://localhost:8000 | grep "Run ID:" | awk '{print $3}') || true

if [ -z "$RUN_ID" ]; then
    echo "Warning: Could not capture run ID, maybe 'aitester run' failed because the API doesn't exist."
    echo "This is expected in the demo since we don't have a live API on port 8000."
else
    echo "> Generating HTML Report for Run $RUN_ID..."
    aitester report --run-id "$RUN_ID" --format html
    echo "Demo complete! Check the generated HTML report."
fi

echo "========================================="
echo " Demo finished. To shut down infrastructure, run:"
echo " docker compose -f docker/docker-compose.yml down"
echo "========================================="
