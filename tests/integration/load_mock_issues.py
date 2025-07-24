"""
Load mock issues into the GitHub repository.
"""

import os
import json
import requests

MOCK_ISSUES_PATH = os.path.join(os.path.dirname(__file__), "mock_issues.json")
GITHUB_PAT = os.environ["GITHUB_PAT"]
GITHUB_REPO = os.environ["GITHUB_REPOSITORY"]  # format: owner/repo

with open(MOCK_ISSUES_PATH) as f:
    issues = json.load(f)

headers = {
    "Authorization": f"token {GITHUB_PAT}",
    "Accept": "application/vnd.github.v3+json",
}

created = []
for issue in issues:
    # Remove fields not accepted by the create API
    issue_data = {k: v for k, v in issue.items() if k not in ("state", "comments")}
    resp = requests.post(
        f"https://api.github.com/repos/{GITHUB_REPO}/issues",
        headers=headers,
        json=issue_data,
    )
    resp.raise_for_status()
    data = resp.json()
    created.append(data["number"])
    print(f"Created issue #{data['number']}: {data['title']}")
    # Add comments if present
    for comment in issue.get("comments", []):
        comment_body = comment["body"]
        comment_payload = {"body": comment_body}
        c_resp = requests.post(
            f"https://api.github.com/repos/{GITHUB_REPO}/issues/{data['number']}/comments",
            headers=headers,
            json=comment_payload,
        )
        c_resp.raise_for_status()
        print("  Added comment")

with open(os.path.join(os.path.dirname(__file__), "created_issues.json"), "w") as f:
    json.dump(created, f)
