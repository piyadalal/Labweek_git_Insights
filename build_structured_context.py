import json
from collections import Counter

INPUT_FILE = "git_metadata_advanced.json"


def load_commits():
    with open(INPUT_FILE, "r") as f:
        return json.load(f)


def compute_repo_metrics(commits):
    author_counts = Counter(commit["author"] for commit in commits)
    file_counts = Counter(file for commit in commits for file in commit["files"])

    revert_count = sum(1 for c in commits if "revert" in c["message"].lower())

    metrics = {
        "total_commits": len(commits),
        "top_author": author_counts.most_common(1)[0] if author_counts else None,
        "most_modified_file": file_counts.most_common(1)[0] if file_counts else None,
        "reverts_detected": revert_count
    }

    return metrics

def format_commits_for_llm(commits):
    blocks = []

    for commit in commits:
        block = f"""
Commit: {commit['hash']}
Author: {commit['author']}
Date: {commit['date']}
Type: {commit['commit_type']}
Message: {commit['message']}
Files: {", ".join(commit['files'][:5])}
Insertions: {commit['insertions']}
Deletions: {commit['deletions']}
"""
        blocks.append(block)

    return "\n".join(blocks)

def build_structured_context():
    commits = load_commits()
    metrics = compute_repo_metrics(commits)

    context_blocks = []

    # Add metrics summary first
    summary = f"""
Repository Metrics:
- Total commits analyzed: {metrics['total_commits']}
- Top contributor: {metrics['top_author']}
- Most modified file: {metrics['most_modified_file']}
- Reverts detected: {metrics['reverts_detected']}
"""
    context_blocks.append(summary)

    # Add formatted commits
    for commit in commits:
        block = f"""
Commit: {commit['hash']}
Author: {commit['author']}
Date: {commit['date']}
Message: {commit['message']}
Files Changed: {", ".join(commit['files'])}
Insertions: {commit['insertions']}
Deletions: {commit['deletions']}
"""
        context_blocks.append(block)

    return "\n".join(context_blocks)


if __name__ == "__main__":
    print(build_structured_context())