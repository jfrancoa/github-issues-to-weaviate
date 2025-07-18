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
TARGET_OWNER=${TARGET_OWNER:-""}
TARGET_REPO=${TARGET_REPO:-""}
CLASS_NAME=${CLASS_NAME:-"GitHubIssues"}
VECTORIZER=${VECTORIZER:-"text2vec-transformers"}
BATCH_SIZE=${BATCH_SIZE:-100}

# Check if GitHub token is provided or warn user
if [ "$GITHUB_TOKEN" == "your-github-token" ]; then
echo -e "${RED}Warning: Using placeholder GitHub token. Set GITHUB_TOKEN env var for real API access.${NC}"
fi

# Build the Docker image locally
echo -e "${GREEN}Building Docker image...${NC}"
docker build -t github-issues-vectorizer:test .

# Run the Docker container with simulated environment variables
echo -e "${GREEN}Running container with simulated GitHub Actions environment...${NC}"
docker run --rm \
-e INPUT_WEAVIATE_URL="$WEAVIATE_URL" \
-e INPUT_WEAVIATE_API_KEY="$WEAVIATE_API_KEY" \
-e INPUT_GITHUB_TOKEN="$GITHUB_TOKEN" \
-e INPUT_TARGET_OWNER="$TARGET_OWNER" \
-e INPUT_TARGET_REPO="$TARGET_REPO" \
-e INPUT_CLASS_NAME="$CLASS_NAME" \
-e INPUT_VECTORIZER="$VECTORIZER" \
-e INPUT_BATCH_SIZE="$BATCH_SIZE" \
-e GITHUB_REPOSITORY="${TARGET_OWNER:-$(whoami)}/${TARGET_REPO:-test-repo}" \
github-issues-vectorizer:test

echo -e "${GREEN}Local test completed!${NC}"

# Usage instructions
echo -e "${YELLOW}Usage Notes:${NC}"
echo "- Set environment variables before running to customize inputs:"
echo "  WEAVIATE_URL, WEAVIATE_API_KEY, GITHUB_TOKEN, etc."
echo "- Example: GITHUB_TOKEN=xyz WEAVIATE_URL=http://weaviate:8080 ./local-test.sh"
echo "- If TARGET_OWNER and TARGET_REPO are empty, the action will use the current repository"

# Make the script executable
chmod +x ./local-test.sh

