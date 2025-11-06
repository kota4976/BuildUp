#!/bin/bash

# BuildUp API Test Runner
# This script sets up the test environment and runs pytest

set -e

echo "🧪 BuildUp API Test Runner"
echo "=========================="

# Check if test database exists
echo "📊 Checking test database..."
if psql -lqt | cut -d \| -f 1 | grep -qw buildup_test; then
    echo "✓ Test database 'buildup_test' exists"
else
    echo "⚠ Test database 'buildup_test' not found. Creating..."
    createdb buildup_test || {
        echo "❌ Failed to create test database"
        echo "Please create it manually: createdb buildup_test"
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

