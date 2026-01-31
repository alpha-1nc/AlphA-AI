#!/bin/bash
# Reset all memory data (SQLite + Chroma) for testing
# This will delete all saved memories and embeddings

set -e

# Navigate to project root
cd "$(dirname "$0")/.."

echo "🗑️  Resetting memory data..."

# Remove data directory
if [ -d "data" ]; then
    rm -rf data/
    echo "✅ Removed data/ directory"
else
    echo "ℹ️  data/ directory does not exist"
fi

# Remove backend/data directory if it exists (shouldn't be used but just in case)
if [ -d "backend/data" ]; then
    rm -rf backend/data/
    echo "✅ Removed backend/data/ directory"
else
    echo "ℹ️  backend/data/ directory does not exist"
fi

echo ""
echo "✨ Data reset complete!"
echo "The database and Chroma collections will be recreated on next backend startup."
