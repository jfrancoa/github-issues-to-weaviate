#!/usr/bin/env python3

import os
import sys
import uuid
import logging
import requests
import weaviate
from weaviate.classes.config import Configure, Property, DataType, Tokenization
from weaviate.collections.classes.config_base import _ConfigCreateModel
from datetime import datetime
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("github-issues-vectorizer")



class GitHubIssueVectorizer:
    def __init__(self):
        # Get inputs from GitHub Action
        self.github_token = os.getenv("INPUT_GITHUB_TOKEN")
        self.weaviate_url = os.getenv("INPUT_WEAVIATE_URL")
        self.weaviate_api_key = os.getenv("INPUT_WEAVIATE_API_KEY","")
        
        # Optional: Set custom repository (default is the current repository)
        self.repo_owner = os.getenv("INPUT_TARGET_REPO_OWNER", "")
        self.repo_name = os.getenv("INPUT_TARGET_REPO_NAME", "")
        self.vectorizer = os.getenv("INPUT_VECTORIZER", "text2vec-weaviate")
        
        # GitHub repository context from environment (for current repo)
        if not self.repo_owner or not self.repo_name:
            github_repository = os.getenv("GITHUB_REPOSITORY", "")
            if github_repository and "/" in github_repository:
                self.repo_owner, self.repo_name = github_repository.split("/", 1)
        
        # Optional parameters
        self.class_name = os.getenv("INPUT_CLASS_NAME", "GitHubIssues")
        self.batch_size = int(os.getenv("INPUT_BATCH_SIZE", "100"))
        self.state = os.getenv("INPUT_STATE", "all")  # all, open, closed
        
        # Validate required inputs
        self._validate_inputs()
        
        logger.info(f"Vectorizing issues from {self.repo_owner}/{self.repo_name}")

    def _validate_inputs(self):
        """Validate that all required inputs are provided."""
        missing_inputs = []
        
        if not self.weaviate_url:
            missing_inputs.append("weaviate_url")
        if not self.repo_owner:
            missing_inputs.append("repo_owner")
        if not self.repo_name:
            missing_inputs.append("repo_name")
        
        if missing_inputs:
            raise ValueError(f"Missing required inputs: {', '.join(missing_inputs)}")

    def _get_vectorizer_method(self) -> _ConfigCreateModel:
        """Map vectorizer name to the corresponding Configure.Vectors method."""
        vectorizer_map = {
            "text2vec-weaviate": Configure.Vectors.text2vec_weaviate,
            "text2vec-openai": Configure.Vectors.text2vec_openai,
            "text2vec-transformers": Configure.Vectors.text2vec_transformers,
            "text2vec-contextionary": Configure.Vectors.text2vec_contextionary,
            "text2vec_ollama": Configure.Vectors.text2vec_ollama,
            "text2vec-cohere": Configure.Vectors.text2vec_cohere,
            "text2vec-jinaai": Configure.Vectors.text2vec_jinaai,
        }
        if self.vectorizer not in vectorizer_map.keys():
            raise ValueError(f"Invalid vectorizer: {self.vectorizer}. Valid vectorizers are: {', '.join(vectorizer_map.keys())}")
        
        return vectorizer_map[self.vectorizer]

    def connect_to_weaviate(self):
        """Connect to Weaviate instance and ensure schema exists."""
        try:
            # Connect to Weaviate using v4 client
            if "localhost" in self.weaviate_url:
                if ":" in self.weaviate_url:
                    host, port = self.weaviate_url.split(":")
                else:
                    host = self.weaviate_url
                    port = 8080
                self.client = weaviate.connect_to_local(
                    host=host,
                    port=port,
                    auth_credentials=weaviate.classes.init.Auth.api_key(self.weaviate_api_key) if self.weaviate_api_key != "" else None,
                )
            else:
                self.client = weaviate.connect_to_weaviate_cloud(
                    cluster_url=self.weaviate_url,
                    auth_credentials=weaviate.classes.init.Auth.api_key(self.weaviate_api_key) if self.weaviate_api_key != "" else None,
                )
            
            logger.info(f"Connected to Weaviate at {self.weaviate_url}")
            
            # Check if schema exists, if not create it
            self._ensure_schema_exists()
            
            return True
        except Exception as e:
            logger.error(f"Error connecting to Weaviate: {str(e)}")
            raise

    def _ensure_schema_exists(self):
        """Ensure the GitHubIssue class exists in Weaviate."""
        # Check if class exists
        if self.client.collections.exists(self.class_name):
            logger.info(f"Schema class {self.class_name} already exists in Weaviate")
        else:
            # Get the vectorizer method
            vectorizer_method = self._get_vectorizer_method()
            
            # Define class for GitHub issues with named vectors
            self.client.collections.create(
                name=self.class_name,
                description="GitHub issue vectorized for semantic search",
                vector_config=[
                    # Default vector containing all vectorizable properties
                    vectorizer_method(
                        name="default",
                        vector_index_config=Configure.VectorIndex.hnsw(),
                    ),
                    # Named vector for title only
                    vectorizer_method(
                        name="title",
                        source_properties=["title"],
                        vector_index_config=Configure.VectorIndex.hnsw(),
                    ),
                    # Named vector for body only
                    vectorizer_method(
                        name="body",
                        source_properties=["body"],
                        vector_index_config=Configure.VectorIndex.hnsw(),
                    ),
                    # Named vector for title and body combined
                    vectorizer_method(
                        name="title_body",
                        source_properties=["title", "body"],
                        vector_index_config=Configure.VectorIndex.hnsw(),
                    ),
                ],
                properties=[
                    Property(
                        name="title",
                        data_type=DataType.TEXT,
                        vectorize_property_name=True,
                        tokenization=Tokenization.LOWERCASE,
                        description="The title of the GitHub issue",
                    ),
                    Property(
                        name="body",
                        data_type=DataType.TEXT,
                        vectorize_property_name=True,
                        tokenization=Tokenization.LOWERCASE,
                        description="The body content of the GitHub issue",
                    ),
                    Property(
                        name="url",
                        data_type=DataType.TEXT,
                        skip_vectorization=True,
                        description="URL to the GitHub issue",
                    ),
                    Property(
                        name="number",
                        data_type=DataType.INT,
                        skip_vectorization=True,
                        description="The issue number",
                    ),
                    Property(
                        name="state",
                        data_type=DataType.TEXT,
                        skip_vectorization=True,
                        description="State of the issue (open or closed)",
                    ),
                    Property(
                        name="createdAt",
                        data_type=DataType.DATE,
                        skip_vectorization=True,
                        description="When the issue was created",
                    ),
                    Property(
                        name="updatedAt",
                        data_type=DataType.DATE,
                        skip_vectorization=True,
                        description="When the issue was last updated",
                    ),
                    Property(
                        name="closedAt",
                        data_type=DataType.DATE,
                        skip_vectorization=True,
                        description="When the issue was closed, if applicable",
                    ),
                    Property(
                        name="labels",
                        data_type=DataType.TEXT_ARRAY,
                        skip_vectorization=True,
                        description="Labels attached to the issue",
                    ),
                    Property(
                        name="author",
                        data_type=DataType.TEXT,
                        skip_vectorization=True,
                        description="Username of the author",
                    ),
                    Property(
                        name="repository",
                        data_type=DataType.TEXT,
                        skip_vectorization=True,
                        description="Full repository name (owner/repo)",
                    )
                ]
            )
            logger.info(f"Created schema class {self.class_name} in Weaviate with named vectors")

    def fetch_github_issues(self) -> List[Dict[str, Any]]:
        """Fetch issues from GitHub repository using the GitHub API."""
        all_issues = []
        page = 1
        per_page = 100  # GitHub API limit
        
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {self.github_token}"
        }
        
        while True:
            # Construct URL for GitHub API
            url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/issues"
            params = {
                "state": self.state,
                "per_page": per_page,
                "page": page,
                "sort": "created",
                "direction": "desc"
            }
            
            try:
                response = requests.get(url, headers=headers, params=params)
                response.raise_for_status()
                
                issues = response.json()
                if not issues:  # No more issues
                    break
                    
                all_issues.extend(issues)
                logger.info(f"Fetched {len(issues)} issues (page {page})")
                
                # Check if we've reached the last page
                if len(issues) < per_page:
                    break
                    
                page += 1
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching GitHub issues: {str(e)}")
                if hasattr(e, 'response') and e.response is not None:
                    logger.error(f"Response content: {e.response.text}")
                raise
        
        logger.info(f"Total issues fetched: {len(all_issues)}")
        return all_issues

    def process_and_store_issues(self, issues: List[Dict[str, Any]]):
        """Process GitHub issues and store them in Weaviate."""
        # If no issues, nothing to do
        if not issues:
            logger.info("No issues to process")
            return
        
        # Get collection reference
        collection = self.client.collections.get(self.class_name)
        
        # Process in batches
        batch_size = min(self.batch_size, 100)  # Never use more than 100 in a batch
        
        # Create a batch process - in v4 we use the collection's batch context
        with collection.batch.dynamic() as batch:
            # Configure batch
            batch.batch_size = batch_size
            
            for issue in issues:
                # Skip pull requests (they're also returned by the issues API)
                if "pull_request" in issue:
                    logger.debug(f"Skipping PR #{issue['number']}")
                    continue
                
                # Process issue into a Weaviate object
                issue_data = {
                    "title": issue["title"],
                    "body": issue["body"] if issue["body"] else None,
                    "url": issue["html_url"],
                    "number": issue["number"],
                    "state": issue["state"],
                    "createdAt": issue["created_at"],
                    "updatedAt": issue["updated_at"],
                    "closedAt": issue["closed_at"] if issue["closed_at"] else None,
                    "labels": [label["name"] for label in issue["labels"]] if issue["labels"] else None,
                    "author": issue["user"]["login"] if issue["user"] else None,
                    "repository": f"{self.repo_owner}/{self.repo_name}"
                }
                
                # Create a unique ID for the issue
                unique_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{self.repo_owner}_{self.repo_name}_{issue['number']}"))
                
                # Add to batch - note the API is different in v4
                batch.add_object(
                    properties=issue_data,
                    uuid=unique_id
                )
        
        logger.info(f"Successfully vectorized {len(issues)} issues into Weaviate")

    def run(self):
        """Main execution method for the action."""
        try:
            # Connect to Weaviate
            self.connect_to_weaviate()
            
            # Fetch all issues from GitHub
            issues = self.fetch_github_issues()
            
            # Process and store issues in Weaviate
            self.process_and_store_issues(issues)
            
            # Success
            logger.info("✅ Successfully completed GitHub issues vectorization")
            return True
        except Exception as e:
            logger.error(f"❌ Error: {str(e)}")
            raise


if __name__ == "__main__":
    try:
        vectorizer = GitHubIssueVectorizer()
        vectorizer.run()
    except Exception as e:
        logger.error(f"Failed to vectorize GitHub issues: {str(e)}")
        sys.exit(1)

