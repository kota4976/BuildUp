#!/bin/bash

# BuildUp API Test Runner
# This script sets up the test environment and runs pytest using Docker

set -e

echo "🧪 BuildUp API Test Runner (Docker)"
echo "===================================="

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Database configuration for the Docker test container
POSTGRES_USER="${POSTGRES_USER:-buildup}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-password}"
export POSTGRES_USER
export POSTGRES_PASSWORD

DB_USER="$POSTGRES_USER"
DB_PASSWORD="$POSTGRES_PASSWORD"
DB_HOST="localhost"
DB_PORT="${TEST_DB_PORT:-5433}"
DB_NAME="${TEST_DB_NAME:-buildup_test}"

cleanup() {
    echo ""
    echo "🧹 Cleaning up..."
    cd "$PROJECT_ROOT/infra"
    docker compose --profile test down >/dev/null 2>&1 || true
}
trap cleanup EXIT

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi

# Start test database with Docker Compose
echo "🐳 Starting test database container..."
cd "$PROJECT_ROOT/infra"
docker compose --profile test up -d --force-recreate db-test

# Wait for database to be ready
echo "⏳ Waiting for test database to be ready..."
RETRIES=30
until docker compose exec -T db-test pg_isready -U "$DB_USER" -d "$DB_NAME" >/dev/null 2>&1 || [ $RETRIES -eq 0 ]; do
    echo "  Waiting... ($RETRIES attempts left)"
    RETRIES=$((RETRIES - 1))
    sleep 1
done

if [ $RETRIES -eq 0 ]; then
    echo "❌ Test database failed to start"
    exit 1
fi

echo "✓ Test database is ready"

# Run migrations on test database
echo ""
echo "🔄 Running migrations on test database..."
cd "$SCRIPT_DIR"
export DATABASE_URL="postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"

# Drop and recreate schema to start fresh
echo "🧨 Resetting test database schema..."
RESET_CMD="PGPASSWORD='${DB_PASSWORD}' psql -U '${DB_USER}' -d '${DB_NAME}' -c \"DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public;\""
if ! docker compose -f "$PROJECT_ROOT/infra/docker-compose.yml" exec -T db-test sh -c "${RESET_CMD}"; then
    echo "❌ Failed to reset test database schema"
    exit 1
fi

# Run migrations
alembic upgrade head || {
    echo "❌ Migration failed"
    exit 1
}
echo "✓ Migrations completed"

# Run tests
echo ""
echo "🧪 Running tests..."
set +e
pytest "$@"
TEST_EXIT_CODE=$?
set -e

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo ""
    echo "✅ Tests completed successfully!"
else
    echo ""
    echo "❌ Tests failed"
fi

exit $TEST_EXIT_CODE

