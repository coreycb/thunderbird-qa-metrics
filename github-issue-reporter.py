#!/usr/bin/env python3

import requests
from collections import Counter

REPO = "thunderbird/thunderbird-android"
AUTHORS = ["VladLucaci", "ramonagavrilescu"]
GITHUB_API = "https://api.github.com"
HEADERS = {"Accept": "application/vnd.github+json"}
PER_PAGE = 100

def fetch_issues(author):
    issues = []
    page = 1

    while True:
        url = f"{GITHUB_API}/search/issues"
        params = {
            "q": f"repo:{REPO} is:issue author:{author}",
            "per_page": PER_PAGE,
            "page": page,
        }

        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()

        issues.extend(data["items"])
        if len(data["items"]) < PER_PAGE:
            break
        page += 1

    return issues

def analyze_issues(issues):
    stats = Counter()

    for issue in issues:
        state = issue["state"]
        stats[state] += 1

        if state == "closed":
            labels = [label["name"].lower() for label in issue.get("labels", [])]

            state_reason = issue.get("state_reason")

            if state_reason == "completed":
                stats["closed_as_completed"] += 1
            if state_reason == "duplicate" or "duplicate" in labels:
                stats["closed_as_duplicate"] += 1
            if state_reason == "not_planned" or any(
                lbl in labels for lbl in {"not planned", "not_planned", "wontfix"}
            ):
                stats["closed_as_not_planned"] += 1

    return stats

def main(verbose=False):
    total_issues = []
    combined_stats = Counter()

    for author in AUTHORS:
        print(f"\n🔍 Fetching issues by {author}...")
        issues = fetch_issues(author)
        print(f"  ➕ Found {len(issues)} issues.")
        stats = analyze_issues(issues)
        total_issues.extend(issues)
        combined_stats.update(stats)

    print("\n📊 Combined Summary:")
    print(f"Total issues opened: {len(total_issues)}")
    print(f"Currently open: {combined_stats['open']}")
    print(f"Currently closed: {combined_stats['closed']}")
    print(f"Closed as completed: {combined_stats.get('closed_as_completed', 0)}")
    print(f"Closed as duplicate: {combined_stats.get('closed_as_duplicate', 0)}")
    print(f"Closed as not planned: {combined_stats.get('closed_as_not_planned', 0)}")

if __name__ == "__main__":
    main()

