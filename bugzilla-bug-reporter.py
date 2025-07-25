#!/usr/bin/env python3

import requests
import argparse
from collections import Counter

BUGZILLA_API = "https://bugzilla.mozilla.org/rest/bug"
HEADERS = {"Accept": "application/json"}

REPORTERS = [
    "ramona@thunderbird.net",
    "vlucaci@mozilla.com",
]

PRODUCTS = ["Calendar", "MailNews Core", "Thunderbird"]
MAX_PER_PAGE = 5000

def fetch_bugs_by_reporter(reporter_email):
    bugs = []
    offset = 0

    while True:
        params = {
            "product": PRODUCTS,
            "reporter": reporter_email,
            "include_fields": "id,summary,creation_time,status,resolution,severity",
            "limit": MAX_PER_PAGE,
            "offset": offset,
        }

        response = requests.get(BUGZILLA_API, params=params, headers=HEADERS)
        response.raise_for_status()
        page = response.json().get("bugs", [])
        if not page:
            break

        bugs.extend(page)
        offset += MAX_PER_PAGE

    return bugs

def main(verbose=False):
    all_bugs = []
    severity_counter = Counter()
    resolution_counter = Counter()
    status_counter = Counter()

    for reporter in REPORTERS:
        print(f"\n🔍 Fetching bugs reported by: {reporter}")
        bugs = fetch_bugs_by_reporter(reporter)
        print(f"✅ Found {len(bugs)} bugs.")

        for bug in bugs:
            severity = bug.get("severity", "unknown")
            resolution = bug.get("resolution", "")
            status = bug.get("status", "unknown")

            severity_counter[severity] += 1
            if resolution:
                resolution_counter[resolution] += 1
            status_counter[status] += 1

            if verbose:
                print( f"- Bug {bug['id']} [{severity}] [{status}] [{resolution or 'OPEN'}]: "
                    f"{bug['summary']} (Created: {bug['creation_time']})"
                )

        all_bugs.extend(bugs)

    print(f"\n📊 Total bugs found across reporters: {len(all_bugs)}")

    if severity_counter:
        print("\n📈 Bugs by Severity:")
        for level in sorted(severity_counter):
            print(f"  {level}: {severity_counter[level]}")

    if resolution_counter:
        print("\n📁 Closed Bugs by Resolution:")
        for resolution, count in resolution_counter.items():
            print(f"  {resolution}: {count}")

    if status_counter:
        print("\n🔄 Bugs by Status:")
        for status, count in status_counter.items():
            print(f"  {status}: {count}")

    if "NEW" in status_counter:
        print(f"\n🆕 Bugs in NEW state: {status_counter['NEW']}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query Bugzilla for bugs by reporter")
    parser.add_argument("--verbose", action="store_true", help="Print detailed bug info")
    args = parser.parse_args()

    main(verbose=args.verbose)

