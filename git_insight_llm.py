import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from build_full_structured_context import (
    build_structured_context,
    load_full_data,
    format_commits_for_llm
)
from git_filter import filter_commits


load_dotenv()

client = OpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    base_url=os.getenv("AZURE_ENDPOINT")
)

MODEL = "gpt-4o-mini"


def ask_git_insight(question):
    full_data = load_full_data()
    commits = full_data.get("commits", [])

    filtered_commits = filter_commits(commits, question)

    # Repo-level summary (branches, merges, divergence)
    repo_context = build_structured_context(limit_commits=0)

    # Relevant commit context
    commit_context = format_commits_for_llm(filtered_commits, limit=50)

    structured_context = (
        repo_context
        + "\n\n=== Relevant Commits ===\n"
        + commit_context
    )

    system_prompt = """
You are a Git repository intelligence analyst.

You are given:
1. Repository-level metadata (branches, merges, divergence, metrics)
2. Relevant commit metadata

You DO NOT have access to source code.
Only use the provided metadata.

Be analytical and concise.
If no data matches, say so clearly.
"""

    user_prompt = f"""
Repository Intelligence:

{structured_context}

User Question:
{question}
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.2
    )

    return response.choices[0].message.content


if __name__ == "__main__":
    question = "Who commited this repo max times?"
    answer = ask_git_insight(question)
    print("\nAI Insight:\n")
    print(answer)