import pytest
from unittest.mock import patch, MagicMock
from main import GitHubIssueVectorizer


# Helper to create a minimal vectorizer with env patched
def make_vectorizer():
    with patch.dict(
        "os.environ",
        {
            "INPUT_GITHUB_TOKEN": "dummy",
            "INPUT_WEAVIATE_URL": "http://localhost:8080",
            "INPUT_TARGET_REPO_OWNER": "owner",
            "INPUT_TARGET_REPO_NAME": "repo",
        },
    ):
        return GitHubIssueVectorizer()


def test_fetch_github_issues_single_page():
    vectorizer = make_vectorizer()
    fake_issues = [
        {
            "number": 1,
            "title": "Test",
            "state": "open",
            "labels": [],
            "user": {"login": "alice"},
            "body": "body",
            "html_url": "url",
            "created_at": "2020-01-01T00:00:00Z",
            "updated_at": "2020-01-01T00:00:00Z",
            "closed_at": None,
            "comments_url": "url",
            "comments": 0,
        }
    ]
    with patch("requests.get") as mock_get:
        mock_get.return_value.json.return_value = fake_issues
        mock_get.return_value.status_code = 200
        mock_get.return_value.raise_for_status = lambda: None
        issues = vectorizer.fetch_github_issues()
        assert issues == fake_issues
        assert mock_get.call_count == 1


def test_fetch_github_issues_pagination():
    vectorizer = make_vectorizer()
    page1 = [
        {
            "number": i + 1,
            "title": f"Issue {i + 1}",
            "state": "open",
            "labels": [],
            "user": {"login": f"user{i % 5}"},
            "body": f"body {i + 1}",
            "html_url": f"url{i + 1}",
            "created_at": f"2020-01-{(i % 28) + 1:02d}T00:00:00Z",
            "updated_at": f"2020-01-{(i % 28) + 1:02d}T00:00:00Z",
            "closed_at": None,
            "comments_url": f"url{i + 1}",
            "comments": 0,
        }
        for i in range(100)
    ]
    page2 = [
        {
            "number": 100 + i + 1,
            "title": f"Issue {i + 1}",
            "state": "open",
            "labels": [],
            "user": {"login": f"user{i % 5}"},
            "body": f"body {i + 1}",
            "html_url": f"url{i + 1}",
            "created_at": f"2020-01-{(i % 28) + 1:02d}T00:00:00Z",
            "updated_at": f"2020-01-{(i % 28) + 1:02d}T00:00:00Z",
            "closed_at": None,
            "comments_url": f"url{i + 1}",
            "comments": 0,
        }
        for i in range(100)
    ]
    with patch("requests.get") as mock_get:
        mock_get.side_effect = [
            MagicMock(
                json=lambda: page1, status_code=200, raise_for_status=lambda: None
            ),
            MagicMock(
                json=lambda: page2, status_code=200, raise_for_status=lambda: None
            ),
            MagicMock(json=lambda: [], status_code=200, raise_for_status=lambda: None),
        ]
        issues = vectorizer.fetch_github_issues()
        assert issues == page1 + page2
        assert mock_get.call_count == 3


def test_fetch_github_issue_comments():
    vectorizer = make_vectorizer()
    comments = [
        {"body": "First", "user": {"login": "alice"}},
        {"body": "Second", "user": {"login": "bob"}},
    ]
    with patch("requests.get") as mock_get:
        mock_get.return_value.json.return_value = comments
        mock_get.return_value.status_code = 200
        mock_get.return_value.raise_for_status = lambda: None
        result = vectorizer.fetch_github_issue_comments(1, "url")
        assert result == comments
        assert mock_get.call_count == 1


def test_process_and_store_issues_skips_pull_requests():
    vectorizer = make_vectorizer()
    # Patch client and batch
    mock_collection = MagicMock()
    mock_batch = MagicMock()
    mock_collection.batch.dynamic.return_value.__enter__.return_value = mock_batch
    vectorizer.client = MagicMock()
    vectorizer.client.collections.get.return_value = mock_collection
    # One issue, one PR
    issues = [
        {
            "number": 1,
            "title": "A",
            "state": "open",
            "labels": [],
            "user": {"login": "alice"},
            "body": "body",
            "html_url": "url",
            "created_at": "2020-01-01T00:00:00Z",
            "updated_at": "2020-01-01T00:00:00Z",
            "closed_at": None,
            "comments_url": "url",
            "comments": 0,
        },
        {
            "number": 2,
            "title": "PR",
            "state": "open",
            "labels": [],
            "user": {"login": "bob"},
            "body": "body2",
            "html_url": "url2",
            "created_at": "2020-01-02T00:00:00Z",
            "updated_at": "2020-01-02T00:00:00Z",
            "closed_at": None,
            "comments_url": "url2",
            "comments": 0,
            "pull_request": {},
        },
    ]
    vectorizer.include_comments = False
    vectorizer.collection_name = "GitHubIssues"
    vectorizer.repo_owner = "owner"
    vectorizer.repo_name = "repo"
    vectorizer.process_and_store_issues(issues)
    # Only one object should be added (the issue, not the PR)
    assert mock_batch.add_object.call_count == 1


def test_process_and_store_issues_with_comments():
    vectorizer = make_vectorizer()
    mock_collection = MagicMock()
    mock_batch = MagicMock()
    mock_collection.batch.dynamic.return_value.__enter__.return_value = mock_batch
    vectorizer.client = MagicMock()
    vectorizer.client.collections.get.return_value = mock_collection
    # Patch fetch_github_issue_comments
    vectorizer.fetch_github_issue_comments = MagicMock(
        return_value=[{"body": "hi", "user": {"login": "alice"}}]
    )
    issues = [
        {
            "number": 1,
            "title": "A",
            "state": "open",
            "labels": [],
            "user": {"login": "alice"},
            "body": "body",
            "html_url": "url",
            "created_at": "2020-01-01T00:00:00Z",
            "updated_at": "2020-01-01T00:00:00Z",
            "closed_at": None,
            "comments_url": "url",
            "comments": 1,
        },
    ]
    vectorizer.include_comments = True
    vectorizer.collection_name = "GitHubIssues"
    vectorizer.repo_owner = "owner"
    vectorizer.repo_name = "repo"
    vectorizer.process_and_store_issues(issues)
    # Should call add_object with comments field populated
    args, kwargs = mock_batch.add_object.call_args
    assert "[alice]: hi" in kwargs["properties"]["comments"]
