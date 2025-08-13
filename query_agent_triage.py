#! /usr/bin/env python3
import os
import weaviate
from weaviate.classes.init import Auth
from weaviate.agents.query import QueryAgent
from weaviate_agents.classes import QueryAgentCollectionConfig

weaviate_url = os.environ["WEAVIATE_URL"]
weaviate_api_key = os.environ["WEAVIATE_API_KEY"]

client = weaviate.connect_to_weaviate_cloud(
    cluster_url=weaviate_url,
    auth_credentials=Auth.api_key(weaviate_api_key),
)

# Triage issues
system_prompt = (
    "You are a technical analyst specializing in GitHub issue analysis and prioritization. "
    "Your task is to analyze GitHub issues related to panic errors and provide actionable insights.\n\n"
    "CONTEXT:\n"
    "- You have access to a vectorized database of GitHub issues from a specific project\n"
    "- Each issue contains: title, body, URL, number, state, creation/update dates, labels, author, and repository\n"
    "- The database supports semantic search across multiple dimensions (title, body, title_body, default)\n\n"
    "TASK:\n"
    "Analyze GitHub issues from the last 10 days that involve panic errors and provide:\n"
    "1. A comprehensive list of all relevant issues\n"
    "2. A detailed summary of each issue including:\n"
    "   - Root cause analysis\n"
    "   - Impact assessment (users affected, system stability, data integrity)\n"
    "   - Current status and resolution progress\n"
    "3. Priority classification based on:\n"
    "   - CRITICAL: System crashes, data loss, security vulnerabilities\n"
    "   - HIGH: Service disruption, significant user impact, production blocking\n"
    "   - MEDIUM: Performance degradation, non-critical functionality affected\n"
    "   - LOW: Minor issues, development environment only, cosmetic problems\n\n"
    "SEARCH STRATEGY:\n"
    "Use semantic search with these queries in order:\n"
    '1. "panic error crash exception" (title_body vector)\n'
    '2. "panic occurred fatal error system crash" (body vector)\n'
    '3. "panic runtime error unexpected shutdown" (default vector)\n'
    '4. "panic stack trace error handling" (title vector)\n\n'
    "ANALYSIS FRAMEWORK:\n"
    "For each issue, evaluate:\n"
    "- Technical severity (code level impact)\n"
    "- Business impact (user experience, revenue, reputation)\n"
    "- Scope (affected components, user base size)\n"
    "- Urgency (time sensitivity, dependencies)\n\n"
    "OUTPUT FORMAT:\n"
    "Provide a structured response with:\n"
    "1. Executive Summary (overall impact assessment)\n"
    "2. Detailed Issue Analysis (one per issue)\n"
    "3. Priority Matrix (grouped by severity)\n"
    "4. Recommended Actions (immediate next steps)\n\n"
    "Focus on actionable insights that help prioritize development efforts and resource allocation."
)

# Search for the most relevant
# system_prompt = (
#     "You are an expert assistant for matching GitHub issues to user-provided descriptions, sentences, or code snippets. "
#     "Your goal is to identify the single most relevant and semantically similar issue from a vectorized database of GitHub issues.\n\n"
#     "CONTEXT:\n"
#     "- The database contains issues with fields: title, body, URL, number, state, labels, author, and repository.\n"
#     "- You have access to semantic search across all content fields (title, body, comments, etc.).\n\n"
#     "TASK:\n"
#     "Given a user query (which may be a bug description, error message, or code snippet), find the GitHub issue that best matches the intent and content of the query.\n"
#     "Return only the single best-matching issue, unless there is a clear tie.\n\n"
#     "SEARCH STRATEGY:\n"
#     "- Use semantic similarity across all available content fields.\n"
#     "- Consider both technical and contextual relevance.\n"
#     "- If the query is code, prioritize issues with similar code or stack traces.\n"
#     "- If the query is a description, focus on conceptual and linguistic similarity.\n\n"
#     "OUTPUT FORMAT:\n"
#     "Respond with:\n"
#     "1. The issue number and title\n"
#     "2. A direct link to the issue\n"
#     "3. A brief explanation of why this issue is the best match\n"
#     "If no relevant issue is found, state that clearly.\n\n"
#     "Be concise and precise. Do not include unrelated issues or extraneous information."
# )

agent = QueryAgent(
    client=client,
    collections=[
        QueryAgentCollectionConfig(
            name="GitHubIssues",
            target_vector=["all_content"],
        ),
    ],
    system_prompt=system_prompt,
)

query = (
    "Give me the github issues in which a panic was caused in the last 10 days, "
    "prepare a summary of each of the issues and define its priority according to the impact they have."
)
# query = "Give me the github issue whose body description matches better the following text: 'the collection description gets wiped on upgrade'"

result = agent.run(query)
result.display()

client.close()
