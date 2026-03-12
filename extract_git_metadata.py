import subprocess
import json
from datetime import datetime
import sys

TARGET_REPO_PATH = sys.argv[1]
TARGET_REPO_PATH = "/Users/prda5207/PycharmProjects/Git_repos/Sky_E2E_Repo/sky-onbox-e2e-skyq-pa-automation"


OUTPUT_FILE = "git_metadata_advanced.json"
MAX_COMMITS = 10000

# 👇 SET YOUR TARGET REPO HERE



def run_git_command(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(result.stderr)
    return result.stdout


def classify_commit(message):
    msg = message.lower()

    if msg.startswith("revert"):
        return "revert"
    if "fix" in msg or "bug" in msg or "hotfix" in msg:
        return "fix"
    if "refactor" in msg or "cleanup" in msg:
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
    else:
        return "large"


def extract_git_metadata():
    git_command = f"""
    git -C {TARGET_REPO_PATH} log --all -n {MAX_COMMITS} \
    --numstat \
    --date=iso \
    --pretty=format:'---COMMIT---%n%H%n%P%n%an%n%ad%n%s'
    """

    output = run_git_command(git_command)

    commits = []
    raw_commits = output.split("---COMMIT---")

    for block in raw_commits:
        lines = block.strip().split("\n")
        if len(lines) < 5:
            continue

        commit_hash = lines[0]
        parents = lines[1].split()
        author = lines[2]
        date_str = lines[3]
        message = lines[4]

        files = []
        insertions = 0
        deletions = 0

        for line in lines[5:]:
            parts = line.split("\t")
            if len(parts) == 3:
                try:
                    insertions += int(parts[0]) if parts[0].isdigit() else 0
                    deletions += int(parts[1]) if parts[1].isdigit() else 0
                except:
                    pass
                files.append(parts[2])

        dt = datetime.fromisoformat(date_str.split(" +")[0])
        day_of_week = dt.strftime("%A")
        hour = dt.hour

        commit_type = classify_commit(message)
        size_category = classify_size(insertions, deletions)

        commits.append({
            "hash": commit_hash,
            "parents": parents,
            "is_merge": len(parents) > 1,
            "author": author,
            "date": date_str,
            "day_of_week": day_of_week,
            "hour_of_day": hour,
            "message": message,
            "commit_type": commit_type,
            "files": files,
            "insertions": insertions,
            "deletions": deletions,
            "size_category": size_category
        })

    with open(OUTPUT_FILE, "w") as f:
        json.dump(commits, f, indent=2)

    print(f"Saved {len(commits)} commits to {OUTPUT_FILE}")


if __name__ == "__main__":
    extract_git_metadata()