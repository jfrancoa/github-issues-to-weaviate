# GitHub Issues to Weaviate

A GitHub Action that vectorizes GitHub issues from a repository and stores them in a Weaviate vector database instance. This action allows for easy semantic search and knowledge management of your project's issues.

## Description

This action connects to a GitHub repository, fetches all issues (open and closed), processes them, and stores them as vectorized objects in a Weaviate instance. This enables powerful semantic search capabilities across your project's issues.

## Usage

Add this action to your GitHub workflow:

```yaml
name: Vectorize GitHub Issues

on:
schedule:
    - cron: '0 0 * * *'  # Run daily at midnight
workflow_dispatch:      # Allow manual triggering

jobs:
vectorize:
    runs-on: ubuntu-latest
    steps:
    - name: Vectorize GitHub Issues
        uses: username/github-issues-to-weaviate@v1
        with:
        weaviate_url: ${{ secrets.WEAVIATE_URL }}
        weaviate_api_key: ${{ secrets.WEAVIATE_API_KEY }}
        github_token: ${{ secrets.GITHUB_TOKEN }}
        # Optional: specify a different repository
        # target_owner: "different-owner"
        # target_repo: "different-repo"
```

## Input Parameters

| Parameter | Required | Description |
| --- | --- | --- |
| `weaviate_url` | Yes | URL of your Weaviate instance |
| `weaviate_api_key` | Yes | API key for your Weaviate instance |
| `github_token` | Yes | GitHub token with permissions to read issues |
| `target_owner` | No | GitHub repository owner (defaults to current repository owner) |
| `target_repo` | No | GitHub repository name (defaults to current repository name) |
| `class_name` | No | Weaviate class name to store issues (defaults to `GitHubIssue`) |
| `vectorizer` | No | Vectorizer used to vectorize all the github issues (defaults to `text2vec-weaviate`) |
| `batch_size` | No | Number of issues to process in a single batch (defaults to 25) |

## Local Testing

For local testing and development, you can use the provided `local-test.sh` script:

1. Make sure the script is executable:
```bash
chmod +x local-test.sh
```

2. Set up your test environment variables in a `.env` file:
```
WEAVIATE_URL=https://your-weaviate-instance.com
WEAVIATE_API_KEY=your-api-key
GITHUB_TOKEN=your-github-token
TARGET_OWNER=optional-target-owner
TARGET_REPO=optional-target-repo
```

3. Run the test script:
```bash
./local-test.sh
```

The script will build a Docker container and run the action with your specified environment variables, allowing you to test and debug without deploying to GitHub.

## How It Works

The action:

1. Authenticates with the GitHub API using the provided token
2. Fetches all issues from the specified repository
3. Processes issues and their metadata
4. Connects to the Weaviate instance
5. Creates the Weaviate schema if it doesn't exist
6. Vectorizes and stores the issues in Weaviate

## Limitations

- The action requires a running Weaviate instance with API access
- Large repositories with thousands of issues may require multiple runs due to GitHub API rate limits
- The GitHub token must have permissions to read issues from the target repository

## License

See the [LICENSE](LICENSE) file for details.
