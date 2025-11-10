#!/bin/bash

# BuildUp API Test Runner
# This script sets up the test environment and runs pytest

set -e

echo "🧪 BuildUp API Test Runner"
echo "=========================="

# PostgreSQL commands path (adjust if needed)
PSQL_PATH="/opt/homebrew/opt/postgresql@15/bin/psql"
CREATEDB_PATH="/opt/homebrew/opt/postgresql@15/bin/createdb"

# Use system psql/createdb if custom path doesn't exist
if [ ! -f "$PSQL_PATH" ]; then
    PSQL_PATH="psql"
fi
if [ ! -f "$CREATEDB_PATH" ]; then
    CREATEDB_PATH="createdb"
fi

# Check if test database exists
echo "📊 Checking test database..."
if $PSQL_PATH -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw buildup_test; then
    echo "✓ Test database 'buildup_test' exists"
else
    echo "⚠ Test database 'buildup_test' not found. Creating..."
    $CREATEDB_PATH buildup_test || {
        echo "❌ Failed to create test database"
        echo "Please create it manually: $CREATEDB_PATH buildup_test"
        exit 1
    }
    echo "✓ Test database created"
fi

# Run migrations on test database
echo ""
echo "🔄 Running migrations on test database..."
export DATABASE_URL="postgresql://localhost:5432/buildup_test"
alembic upgrade head || {
    echo "⚠ Migration failed, but continuing with tests..."
}

# Run tests
echo ""
echo "🧪 Running tests..."
pytest "$@"

echo ""
echo "✅ Tests completed!"

