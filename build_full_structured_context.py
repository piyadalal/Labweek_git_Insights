import json
from collections import Counter
from datetime import datetime

INPUT_FILE = "git_full_metadata.json"


# ------------------------
# Load Full Data
# ------------------------

def load_full_data():
    with open(INPUT_FILE, "r") as f:
        return json.load(f)


# ------------------------
# Commit-Level Metrics
# ------------------------

def compute_commit_metrics(commits):
    author_counts = Counter(c["author"] for c in commits)
    file_counts = Counter(
        file for c in commits for file in c.get("files", [])
    )

    commit_type_counts = Counter(c["commit_type"] for c in commits)
    large_commits = sum(1 for c in commits if c["size_category"] == "large")
    revert_count = commit_type_counts.get("revert", 0)

    return {
        "total_commits": len(commits),
        "top_author": author_counts.most_common(1)[0] if author_counts else None,
        "most_modified_file": file_counts.most_common(1)[0] if file_counts else None,
        "reverts_detected": revert_count,
        "large_commits": large_commits,
        "commit_type_distribution": dict(commit_type_counts)
    }


# ------------------------
# Branch Metrics
# ------------------------

def compute_branch_metrics(branches):
    branch_count = len(branches)

    stale_branches = []
    now = datetime.now()

    for b in branches:
        if b["last_commit"]:
            try:
                last_commit_date = datetime.strptime(
                    b["last_commit"], "%Y-%m-%d %H:%M:%S %z"
                )
                days_inactive = (now - last_commit_date.replace(tzinfo=None)).days
                if days_inactive > 90:
                    stale_branches.append(b["branch_name"])
            except:
                pass

    return {
        "total_branches": branch_count,
        "stale_branches": stale_branches[:5]
    }


# ------------------------
# Merge Metrics
# ------------------------

def compute_merge_metrics(merges):
    merge_authors = Counter(m["author"] for m in merges)

    return {
        "total_merges": len(merges),
        "top_merger": merge_authors.most_common(1)[0] if merge_authors else None
    }


# ------------------------
# Branch Divergence Metrics
# ------------------------

def compute_divergence_metrics(comparisons):
    most_diverged = None
    max_diff = 0

    for comp in comparisons:
        if comp["diff_files_count"] > max_diff:
            max_diff = comp["diff_files_count"]
            most_diverged = comp["branch"]

    return {
        "most_diverged_branch": most_diverged,
        "max_diff_files": max_diff
    }


# ------------------------
# Format Commits for LLM
# ------------------------

def format_commits_for_llm(commits, limit=50):
    blocks = []

    for commit in commits[:limit]:
        block = f"""
    Commit: {commit['hash']}
    Author: {commit['author']}
    Date: {commit['date']}
    Branch/Refs: {commit.get('refs', '')}
    Type: {commit['commit_type']}
    Message: {commit['message']}
    Files: {", ".join(commit['files'][:5])}
    Insertions: {commit['insertions']}
    Deletions: {commit['deletions']}
    """
        blocks.append(block)

    return "\n".join(blocks)


# ------------------------
# Build Structured Context
# ------------------------

def build_structured_context(limit_commits=50):
    data = load_full_data()

    commits = data.get("commits", [])
    branches = data.get("branches", [])
    branch_metrics = compute_branch_metrics(branches)
    branch_names = [b["branch_name"] for b in branches]
    branch_names_text = "\n".join(branch_names[:30])

    merges = data.get("merges", [])
    comparisons = data.get("branch_comparisons", [])

    commit_metrics = compute_commit_metrics(commits)
    branch_metrics = compute_branch_metrics(branches)
    merge_metrics = compute_merge_metrics(merges)
    divergence_metrics = compute_divergence_metrics(comparisons)

    summary = f"""
Repository: {data.get("repository")}

=== Commit Metrics ===
Total Commits: {commit_metrics['total_commits']}
Top Contributor: {commit_metrics['top_author']}
Most Modified File: {commit_metrics['most_modified_file']}
Reverts Detected: {commit_metrics['reverts_detected']}
Large Commits: {commit_metrics['large_commits']}
Commit Type Distribution: {commit_metrics['commit_type_distribution']}

=== Branch Metrics ===
Branch Metrics
Total Branches: {branch_metrics['total_branches']}
Branch Names:
{branch_names_text}
Stale Branches: {branch_metrics['stale_branches']}

=== Merge Metrics ===
Total Merges: {merge_metrics['total_merges']}
Top Merger: {merge_metrics['top_merger']}

=== Branch Divergence ===
Most Diverged Branch: {divergence_metrics['most_diverged_branch']}
Max Different Files from Main: {divergence_metrics['max_diff_files']}
"""

    commit_blocks = format_commits_for_llm(commits, limit_commits)

    return summary + "\n\n=== Recent Commits ===\n" + commit_blocks


# ------------------------
# Run
# ------------------------

if __name__ == "__main__":
    print(build_structured_context())