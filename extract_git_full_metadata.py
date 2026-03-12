import subprocess
import json
from datetime import datetime
import sys

TARGET_REPO_PATH = sys.argv[1]
TARGET_REPO_PATH = "/Users/prda5207/PycharmProjects/Git_repos/Sky_E2E_Repo/sky-onbox-e2e-skyq-pa-automation"
OUTPUT_FILE = "git_full_metadata.json"
MAX_COMMITS = 10000


# ------------------------
# Utilities
# ------------------------

def run_git_command(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def parse_git_date(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S %z")


def classify_commit(message):
    msg = message.lower()
    if msg.startswith("revert"):
        return "revert"
    if "fix" in msg or "bug" in msg:
        return "fix"
    if "refactor" in msg:
        return "refactor"
    if "feat" in msg or "add" in msg:
        return "feature"
    return "other"


def classify_size(insertions, deletions):
    total = insertions + deletions
    if total < 50:
        return "small"
    elif total < 300:
        return "medium"
    return "large"


# ------------------------
# Commit Extraction
# ------------------------

def extract_commits():
    print("Extracting commits...")
    git_command = f"""
    git -C {TARGET_REPO_PATH} log --all -n {MAX_COMMITS} \
    --numstat \
    --date=iso \
    --pretty=format:'---COMMIT---%n%H%n%D%n%P%n%an%n%ae%n%ad%n%s'
    """

    output = run_git_command(git_command)
    raw_commits = output.split("---COMMIT---")
    commits = []

    for block in raw_commits:
        lines = block.strip().split("\n")
        if len(lines) < 6:
            continue

        commit_hash = lines[0]
        parents = lines[1].split()
        author = lines[2]
        email = lines[3]
        date_str = lines[4]
        message = lines[5]

        files = []
        insertions = 0
        deletions = 0

        for line in lines[6:]:
            parts = line.split("\t")
            if len(parts) == 3:
                try:
                    insertions += int(parts[0]) if parts[0].isdigit() else 0
                    deletions += int(parts[1]) if parts[1].isdigit() else 0
                except:
                    pass
                files.append(parts[2])

        dt = parse_git_date(date_str)

        commits.append({
            "hash": commit_hash,
            "parents": parents,
            "is_merge": len(parents) > 1,
            "author": author,
            "email": email,
            "date": date_str,
            "day_of_week": dt.strftime("%A"),
            "hour_of_day": dt.hour,
            "message": message,
            "commit_type": classify_commit(message),
            "files": files,
            "insertions": insertions,
            "deletions": deletions,
            "size_category": classify_size(insertions, deletions)
        })

    return commits


# ------------------------
# Branch Extraction
# ------------------------

def extract_branches():
    print("Extracting branches...")
    branches_raw = run_git_command(
        f"git -C {TARGET_REPO_PATH} branch -a --format='%(refname:short)'"
    ).split("\n")

    branches = []

    for branch in branches_raw:
        if not branch.strip():
            continue

        first_commit = run_git_command(
            f"git -C {TARGET_REPO_PATH} log {branch} --reverse -1 --pretty=format:'%ad' --date=iso"
        )

        last_commit = run_git_command(
            f"git -C {TARGET_REPO_PATH} log {branch} -1 --pretty=format:'%ad' --date=iso"
        )

        total_commits = run_git_command(
            f"git -C {TARGET_REPO_PATH} rev-list --count {branch}"
        )

        authors = run_git_command(
            f"git -C {TARGET_REPO_PATH} log {branch} --pretty=format:'%ae'"
        ).split("\n")

        branches.append({
            "branch_name": branch,
            "created_at": first_commit,
            "last_commit": last_commit,
            "total_commits": int(total_commits) if total_commits.isdigit() else 0,
            "unique_authors": list(set(authors))
        })

    return branches


# ------------------------
# Merge Extraction
# ------------------------

def extract_merges():
    print("Extracting merge commits...")
    merges_raw = run_git_command(
        f"git -C {TARGET_REPO_PATH} log --merges --pretty=format:'%H|%an|%ad|%s' --date=iso"
    ).split("\n")

    merges = []

    for line in merges_raw:
        parts = line.split("|")
        if len(parts) != 4:
            continue

        merges.append({
            "hash": parts[0],
            "author": parts[1],
            "date": parts[2],
            "message": parts[3]
        })

    return merges


# ------------------------
# Branch Comparison (main vs others)
# ------------------------

def extract_branch_differences(branches):
    print("Extracting branch comparisons...")
    comparisons = []

    main_branch = "main"

    for branch in branches:
        name = branch["branch_name"]
        if name == main_branch:
            continue

        diff_files = run_git_command(
            f"git -C {TARGET_REPO_PATH} diff --name-only {main_branch} {name}"
        ).split("\n")

        divergence = run_git_command(
            f"git -C {TARGET_REPO_PATH} rev-list --left-right --count {main_branch}...{name}"
        )

        comparisons.append({
            "branch": name,
            "diff_files_count": len([f for f in diff_files if f]),
            "ahead_behind": divergence
        })

    return comparisons


# ------------------------
# MAIN
# ------------------------

def extract_full_git_intelligence():
    commits = extract_commits()
    branches = extract_branches()
    merges = extract_merges()
    comparisons = extract_branch_differences(branches)

    full_data = {
        "repository": TARGET_REPO_PATH,
        "total_commits": len(commits),
        "commits": commits,
        "branches": branches,
        "merges": merges,
        "branch_comparisons": comparisons
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(full_data, f, indent=2)

    print(f"\nSaved full git intelligence to {OUTPUT_FILE}")


if __name__ == "__main__":
    extract_full_git_intelligence()