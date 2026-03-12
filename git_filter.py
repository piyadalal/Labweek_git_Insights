import re
from datetime import datetime, timedelta


def parse_git_date(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S %z")


def filter_commits(commits, question):
    question_lower = question.lower()
    author_filter = None

    for commit in commits:
        if commit["author"].lower() in question_lower:
            author_filter = commit["author"]
            break
    now = datetime.now().astimezone()

    # ---------------------------------
    # 1️⃣ Time Filtering
    # ---------------------------------

    time_filtered = commits
    if author_filter:
        time_filtered = [
            c for c in time_filtered
            if c["author"] == author_filter
        ]

    # "last week"
    if "last week" in question_lower:
        cutoff = now - timedelta(days=7)
        time_filtered = [
            c for c in commits
            if parse_git_date(c["date"]) >= cutoff
        ]

    # "last month"
    elif "last month" in question_lower:
        cutoff = now - timedelta(days=30)
        time_filtered = [
            c for c in commits
            if parse_git_date(c["date"]) >= cutoff
        ]

    # "last X days"
    else:
        match = re.search(r"last (\d+) days", question_lower)
        if match:
            days = int(match.group(1))
            cutoff = now - timedelta(days=days)
            time_filtered = [
                c for c in commits
                if parse_git_date(c["date"]) >= cutoff
            ]

    # ---------------------------------
    # 2️⃣ Keyword Filtering
    # ---------------------------------

    keywords = re.findall(r"\b\w+\b", question_lower)
    stopwords = {"what", "who", "when", "why", "how", "did", "the", "is", "are", "was"}

    keywords = [k for k in keywords if k not in stopwords]

    keyword_filtered = []

    for commit in time_filtered:
        message = commit["message"].lower()
        files = " ".join(commit.get("files", [])).lower()

        score = 0

        for word in keywords:
            if word in message:
                score += 3
            if word in files:
                score += 2

        # Boost specific intent
        if "revert" in question_lower and commit["commit_type"] == "revert":
            score += 5

        if "merge" in question_lower and commit["is_merge"]:
            score += 5

        if "large" in question_lower and commit["size_category"] == "large":
            score += 4

        if score > 0:
            commit_copy = commit.copy()
            commit_copy["relevance_score"] = score
            keyword_filtered.append(commit_copy)

    # ---------------------------------
    # 3️⃣ Fallback Logic
    # ---------------------------------

    if keyword_filtered:
        filtered = keyword_filtered
    elif time_filtered:
        filtered = time_filtered
    else:
        # fallback to most recent commits
        filtered = sorted(
            commits,
            key=lambda c: parse_git_date(c["date"]),
            reverse=True
        )

    # ---------------------------------
    # 4️⃣ Sort by relevance or recency
    # ---------------------------------

    filtered.sort(
        key=lambda c: (
            c.get("relevance_score", 0),
            parse_git_date(c["date"])
        ),
        reverse=True
    )

    # ---------------------------------
    # 5️⃣ Safety Limit
    # ---------------------------------

    return filtered[:50]