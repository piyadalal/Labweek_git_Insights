import streamlit as st
import os
from dotenv import load_dotenv
from openai import OpenAI

from git_filter import filter_commits
from build_full_structured_context import (
    build_structured_context,
    load_full_data,
    format_commits_for_llm
)

# ------------------------
# Load Environment
# ------------------------
load_dotenv()

client = OpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    base_url=os.getenv("AZURE_ENDPOINT")
)

MODEL = "gpt-4o-mini"

# ------------------------
# Page Config
# ------------------------
st.set_page_config(page_title="Git Insight AI", layout="wide")
st.title("Git Insight AI")
st.markdown("Ask intelligent questions about your repository history (no code sent to LLM).")

# ------------------------
# Ask LLM Function
# ------------------------

def ask_git_insight(question):
    full_data = load_full_data()
    commits = full_data.get("commits", [])

    # Filter relevant commits
    filtered_commits = filter_commits(commits, question)

    # Build repo-level summary (branches, merges, etc.)
    repo_context = build_structured_context(limit_commits=0)

    # Format relevant commits
    commit_context = format_commits_for_llm(filtered_commits, limit=50)

    structured_context = (
        repo_context
        + "\n\n=== Relevant Commits ===\n"
        + commit_context
    )

    system_prompt = """
You analyze Git repository metadata.

If the question asks about a specific contributor:
- Identify their most recent commit.
- List files modified.
- Identify associated branch.
- Provide date.

Use only provided metadata.
Be concise.

You are given:
1. Repository-level metadata (branches, merges, divergence, metrics)
2. Relevant commit metadata

You DO NOT have access to source code.
Only use the provided metadata.

When answering:
- Use branch data if question relates to branches
- Use merge data if question relates to merges
- Use commit data for file/module questions
- Be analytical and concise
- If no data matches, clearly say so
"""

    user_prompt = f"""
Repository Data:

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

    answer = response.choices[0].message.content

    return answer, len(filtered_commits)


# ------------------------
# UI Input
# ------------------------

question = st.text_input(
    "Ask a question about your repo:",
    placeholder="e.g. Why was the payment module reverted last week?"
)

if st.button("Analyze Repository") and question.strip():

    with st.spinner("Analyzing repository intelligence..."):

        try:
            answer, commit_count = ask_git_insight(question)

            #st.success(f"Analyzed {commit_count} relevant commits")

            st.subheader("AI Insight")
            st.write(answer)

        except Exception as e:
            st.error(f"Error: {e}")