#!/usr/bin/env python3

"""
Example script demonstrating how to search GitHub issues using the different named vectors
created by the github-issues-to-weaviate action.
"""

import weaviate
import os
from typing import List, Dict, Any


def connect_to_weaviate():
    """Connect to Weaviate instance."""
    weaviate_url = os.getenv("WEAVIATE_URL")
    weaviate_api_key = os.getenv("WEAVIATE_API_KEY", "")

    if "localhost" in weaviate_url:
        if ":" in weaviate_url:
            host, port = weaviate_url.split(":")
        else:
            host = weaviate_url
            port = 8080
        client = weaviate.connect_to_local(
            host=host,
            port=port,
            auth_credentials=(
                weaviate.classes.init.Auth.api_key(weaviate_api_key)
                if weaviate_api_key
                else None
            ),
        )
    else:
        client = weaviate.connect_to_weaviate_cloud(
            cluster_url=weaviate_url,
            auth_credentials=(
                weaviate.classes.init.Auth.api_key(weaviate_api_key)
                if weaviate_api_key
                else None
            ),
        )

    return client


def search_issues_by_title(client, query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search issues by title only."""
    collection = client.collections.get("GitHubIssues")

    response = collection.query.near_text(
        query=query, limit=limit, target_vector="title"
    )

    return response.objects


def search_issues_by_comments(
    client, query: str, limit: int = 5
) -> List[Dict[str, Any]]:
    """Search issues by comments only."""
    collection = client.collections.get("GitHubIssues")

    response = collection.query.near_text(
        query=query, limit=limit, target_vector="comments"
    )

    return response.objects


def search_issues_by_body(client, query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search issues by body/description only."""
    collection = client.collections.get("GitHubIssues")

    response = collection.query.near_text(
        query=query, limit=limit, target_vector="body"
    )

    return response.objects


def search_issues_all_content(
    client, query: str, limit: int = 5
) -> List[Dict[str, Any]]:
    """Search issues across all content (title, body, comments)."""
    collection = client.collections.get("GitHubIssues")

    response = collection.query.near_text(
        query=query, limit=limit, target_vector="all_content"
    )

    return response.objects


def search_issues_default(client, query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search issues using the default vector (all vectorizable properties)."""
    collection = client.collections.get("GitHubIssues")

    response = collection.query.near_text(query=query, limit=limit)

    return response.objects


def print_search_results(results: List[Dict[str, Any]], search_type: str):
    """Print search results in a formatted way."""
    print(f"\n=== {search_type.upper()} SEARCH RESULTS ===")
    if not results:
        print("No results found.")
        return

    for i, obj in enumerate(results, 1):
        print(f"\n{i}. Issue #{obj.properties.get('number', 'N/A')}")
        print(f"   Title: {obj.properties.get('title', 'N/A')}")
        print(f"   State: {obj.properties.get('state', 'N/A')}")
        print(f"   Author: {obj.properties.get('author', 'N/A')}")
        print(f"   URL: {obj.properties.get('url', 'N/A')}")
        print(f"   Comment Count: {obj.properties.get('commentCount', 0)}")

        # Show a snippet of the body if available
        body = obj.properties.get("body", "")
        if body and len(body) > 100:
            print(f"   Body: {body[:100]}...")
        elif body:
            print(f"   Body: {body}")

        # Show a snippet of comments if available
        comments = obj.properties.get("comments", "")
        if comments and len(comments) > 100:
            print(f"   Comments: {comments[:100]}...")
        elif comments:
            print(f"   Comments: {comments}")


def main():
    """Main function demonstrating different search capabilities."""
    try:
        client = connect_to_weaviate()
        print("✅ Connected to Weaviate successfully!")

        # Example searches
        query = "authentication error"

        print(f"\n🔍 Searching for: '{query}'")

        # Search by title only
        title_results = search_issues_by_title(client, query)
        print_search_results(title_results, "Title")

        # Search by comments only
        comment_results = search_issues_by_comments(client, query)
        print_search_results(comment_results, "Comments")

        # Search by body only
        body_results = search_issues_by_body(client, query)
        print_search_results(body_results, "Body")

        # Search across all content
        all_content_results = search_issues_all_content(client, query)
        print_search_results(all_content_results, "All Content")

        # Search using default vector
        default_results = search_issues_default(client, query)
        print_search_results(default_results, "Default")

    except Exception as e:
        print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    main()
