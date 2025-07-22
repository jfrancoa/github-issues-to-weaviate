import weaviate
from weaviate.classes.query import Filter
import json
import os
import time
import pytest

MOCK_ISSUES_PATH = os.path.join(os.path.dirname(__file__), "mock_issues.json")
CREATED_ISSUES_PATH = os.path.join(os.path.dirname(__file__), "created_issues.json")
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


def load_created_issues() -> list[int]:
    with open(CREATED_ISSUES_PATH) as f:
        return json.load(f)


def load_mock_issues() -> list[dict]:
    with open(MOCK_ISSUES_PATH) as f:
        return json.load(f)


def test_all_mock_issues_present(client):
    mock_issues = load_mock_issues()
    collection = client.collections.get(COLLECTION)
    # Wait for indexing
    for _ in range(10):
        count = len(collection)
        if count >= len(mock_issues):
            break
        time.sleep(1)
    assert len(collection) >= len(mock_issues)
    created_issues = load_created_issues()
    all_issues = collection.query.fetch_objects().objects
    for obj in all_issues:
        assert obj.properties["number"] in created_issues


def test_search_by_named_vector(client):
    collection = client.collections.get(COLLECTION)
    # Search for a bug by title vector
    results = collection.query.near_text(
        query="startup crash", target_vector="title", limit=5
    ).objects
    assert any("startup" in obj.properties["title"].lower() for obj in results)
    assert any("crash" in obj.properties["title"].lower() for obj in results)
    # Search for a feature by all_content vector
    results = collection.query.near_text(
        query="dark mode", target_vector="all_content", limit=5
    ).objects
    assert any("dark mode" in obj.properties["title"].lower() for obj in results)
    # Search for a bug by body vector
    results = collection.query.near_text(
        query="segmentation fault", target_vector="body", limit=5
    ).objects
    assert any(
        "segmentation fault" in obj.properties["body"].lower() for obj in results
    )
    # Search for a refactor by title vector
    results = collection.query.near_text(
        query="refactor", target_vector="title", limit=5
    ).objects
    assert any("refactor" in obj.properties["title"].lower() for obj in results)
    # Search for a documentation update by all_content vector
    results = collection.query.near_text(
        query="update readme", target_vector="all_content", limit=5
    ).objects
    assert any(
        "readme" in obj.properties["title"].lower()
        or "readme" in obj.properties["body"].lower()
        for obj in results
    )
    # Search for a security issue by body vector
    results = collection.query.near_text(
        query="xss vulnerability", target_vector="body", limit=5
    ).objects
    assert any("xss" in obj.properties["body"].lower() for obj in results)
    # Search for a performance issue by title vector
    results = collection.query.near_text(
        query="slow loading", target_vector="title", limit=5
    ).objects
    assert any("slow loading" in obj.properties["title"].lower() for obj in results)
    # Search for a feature by body vector
    results = collection.query.near_text(
        query="multi-language support", target_vector="body", limit=5
    ).objects
    assert any(
        "spanish" in obj.properties["body"].lower()
        or "french" in obj.properties["body"].lower()
        for obj in results
    )


def test_search_by_label_vector(client):
    collection = client.collections.get(COLLECTION)
    # Search for a bug by label
    results = collection.query.fetch_objects(
        filters=Filter.by_property("labels").equal("bug"), limit=5
    )
    assert any("bug" in obj.properties["labels"] for obj in results.objects)
    # Search for a feature by label
    results = collection.query.fetch_objects(
        filters=Filter.by_property("labels").equal("enhancement"), limit=5
    )
    assert any("enhancement" in obj.properties["labels"] for obj in results.objects)
    # Search for a documentation issue by label
    results = collection.query.fetch_objects(
        filters=Filter.by_property("labels").equal("documentation"), limit=5
    )
    assert any("documentation" in obj.properties["labels"] for obj in results.objects)


def test_search_by_comment_vector(client):
    collection = client.collections.get(COLLECTION)
    # Search for a comment body
    results = collection.query.near_text(
        query="heap dump", target_vector="comments", limit=5
    ).objects
    assert any(
        "heap dump" in obj.properties.get("comments", []).lower() for obj in results
    )

    # Search for a comment about translation
    results = collection.query.near_text(
        query="translations", target_vector="comments", limit=5
    ).objects
    assert any(
        "translation" in obj.properties.get("comments", []).lower() for obj in results
    )
