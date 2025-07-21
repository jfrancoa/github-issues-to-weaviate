"""
Delete mock issues from the GitHub repository.
"""

import os
import json
import requests

CREATED_ISSUES_PATH = os.path.join(os.path.dirname(__file__), "created_issues.json")
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
GITHUB_REPO = os.environ["GITHUB_REPOSITORY"]  # format: owner/repo

with open(CREATED_ISSUES_PATH) as f:
    issue_numbers = json.load(f)

headers_rest = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}
headers_graphql = {
    "Authorization": f"bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
    "Content-Type": "application/json",
}


def get_issue_node_id(number):
    resp = requests.get(
        f"https://api.github.com/repos/{GITHUB_REPO}/issues/{number}",
        headers=headers_rest,
    )
    if resp.status_code == 200:
        return resp.json().get("node_id")
    else:
        print(
            f"Failed to get node_id for issue #{number}: {resp.status_code} {resp.text}"
        )
        return None


def delete_issue(node_id, client_mutation_id=None):
    mutation = {
        "query": """
        mutation($input: DeleteIssueInput!) {
          deleteIssue(input: $input) {
            clientMutationId
          }
        }
        """,
        "variables": {
            "input": {
                "issueId": node_id,
                "clientMutationId": client_mutation_id or "delete-mock-issue",
            }
        },
    }
    resp = requests.post(
        "https://api.github.com/graphql",
        headers=headers_graphql,
        json=mutation,
    )
    if resp.status_code == 200:
        data = resp.json()
        if "errors" in data:
            print(f"Failed to delete issue node {node_id}: {data['errors']}")
            return False
        print(f"Deleted issue node {node_id}")
        return True
    else:
        print(
            f"GraphQL error deleting issue node {node_id}: {resp.status_code} {resp.text}"
        )
        return False


for number in issue_numbers:
    node_id = get_issue_node_id(number)
    if node_id:
        delete_issue(node_id, client_mutation_id=f"delete-issue-{number}")

try:
    os.remove(CREATED_ISSUES_PATH)
    print(f"Deleted {CREATED_ISSUES_PATH}")
except FileNotFoundError:
    print(f"{CREATED_ISSUES_PATH} not found, nothing to delete.")
