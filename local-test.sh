#!/bin/bash
set -e

# Colors for better output formatting
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Setting up local test environment for GitHub Issues Vectorizer Action${NC}"

# Simulated GitHub Actions inputs (modify these values for your testing)
WEAVIATE_URL=${WEAVIATE_URL:-"http://localhost:8080"}
WEAVIATE_API_KEY=${WEAVIATE_API_KEY:-"your-api-key"}
GITHUB_TOKEN=${GITHUB_TOKEN:-"your-github-token"}
TARGET_REPOSITORY=${TARGET_REPOSITORY:-""}
COLLECTION_NAME=${COLLECTION_NAME:-"GitHubIssues"}
VECTORIZER=${VECTORIZER:-"text2vec-transformers"}
INCLUDE_COMMENTS=${INCLUDE_COMMENTS:-"false"}
BATCH_SIZE=${BATCH_SIZE:-100}

# Check if GitHub token is provided or warn user
if [ "$GITHUB_TOKEN" == "your-github-token" ]; then
echo -e "${RED}Warning: Using placeholder GitHub token. Set GITHUB_TOKEN env var for real API access.${NC}"
fi

# Build the Docker image locally
echo -e "${GREEN}Building Docker image...${NC}"
docker build --load -t github-issues-vectorizer:test .

# Run the Docker container with simulated environment variables
echo -e "${GREEN}Running container with simulated GitHub Actions environment...${NC}"
docker run --rm \
-e WEAVIATE_URL="$WEAVIATE_URL" \
-e WEAVIATE_API_KEY="$WEAVIATE_API_KEY" \
-e GITHUB_TOKEN="$GITHUB_TOKEN" \
-e TARGET_REPOSITORY="$TARGET_REPOSITORY" \
-e COLLECTION_NAME="$COLLECTION_NAME" \
-e VECTORIZER="$VECTORIZER" \
-e BATCH_SIZE="$BATCH_SIZE" \
-e INCLUDE_COMMENTS="$INCLUDE_COMMENTS" \
github-issues-vectorizer:test

echo -e "${GREEN}Local test completed!${NC}"

# Usage instructions
echo -e "${YELLOW}Usage Notes:${NC}"
echo "- Set environment variables before running to customize inputs:"
echo "  WEAVIATE_URL, WEAVIATE_API_KEY, GITHUB_TOKEN, TARGET_REPOSITORY, etc."
echo "- Example: TARGET_REPOSITORY=weaviate/weaviate GITHUB_TOKEN=xyz WEAVIATE_URL=http://weaviate:8080 ./local-test.sh"

# Make the script executable
chmod +x ./local-test.sh

