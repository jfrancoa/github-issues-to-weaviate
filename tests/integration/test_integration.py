import weaviate
import json
import os
import time
import pytest

MOCK_ISSUES_PATH = os.path.join(os.path.dirname(__file__), "mock_issues.json")
COLLECTION = "GitHubIssues"


@pytest.fixture(scope="session")
def client():
    client = weaviate.connect_to_local()
    # Wait for Weaviate to be ready
    for _ in range(30):
        if client.is_ready():
            break
        time.sleep(1)
    else:
        raise RuntimeError("Weaviate did not become ready in time")
    yield client
    client.close()


def load_mock_issues():
    with open(MOCK_ISSUES_PATH) as f:
        return json.load(f)


def test_all_mock_issues_present(client):
    mock_issues = load_mock_issues()
    collection = client.collections.get(COLLECTION)
    # Wait for indexing
    for _ in range(10):
        count = collection.query.count().total_count
        if count >= len(mock_issues):
            break
        time.sleep(1)
    assert collection.query.count().total_count >= len(mock_issues)


def test_duplicates_detected(client):
    collection = client.collections.get(COLLECTION)
    # Find issues with same title and body
    all_issues = collection.query.fetch_objects().objects
    seen = set()
    dups = 0
    for obj in all_issues:
        key = (obj.properties["title"], obj.properties["body"])
        if key in seen:
            dups += 1
        else:
            seen.add(key)
    # We know there are 3 "Bug: Crash on startup" issues
    assert dups >= 2


def test_search_by_named_vector(client):
    collection = client.collections.get(COLLECTION)
    # Search for a bug by title vector
    results = collection.query.near_text(
        query="startup crash", vector="title", limit=3
    ).objects
    assert any("startup" in obj.properties["title"].lower() for obj in results)
    # Search for a feature by all_content vector
    results = collection.query.near_text(
        query="dark mode", vector="all_content", limit=3
    ).objects
    assert any("dark mode" in obj.properties["title"].lower() for obj in results)
