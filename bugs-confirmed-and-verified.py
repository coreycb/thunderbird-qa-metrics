#!/usr/bin/env python3
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

BUGZILLA_API = "https://bugzilla.mozilla.org/rest"

usernames = [
    "vlucaci@mozilla.com",
    "ramona@thunderbird.net",
]
search_products = ["Thunderbird", "MailNews Core", "Calendar"]
limit = 1000
since = "2024-04-03T00:00:00Z"

HEADERS = {
    "Accept": "application/json"
}

def fetch_history(bug_id):
    max_retries = 10
    delay = 10
    url = f"{BUGZILLA_API}/bug/{bug_id}/history"
    for attempt in range(max_retries):
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        if "bugs" not in data:
            time.sleep(delay)
            print("Bad response. Retrying")
            continue
        return bug_id, response.json()["bugs"][0]["history"]
    raise RuntimeError("API returned unexpected data")

def search_bugs_commented_on_by_user(user_email, product=None, limit=100, since=None):
    params = {
        "include_fields": "id,last_change_time",
        "limit": limit,
        "commenter": user_email,
    }
    if product:
        params["product"] = product
    if since:
        params["last_change_time"] = since

    bugs = []
    offset = 0

    while True:
        params["offset"] = offset
        response = requests.get(f"{BUGZILLA_API}/bug", params=params, headers=HEADERS)
        response.raise_for_status()
        page = response.json()["bugs"]

        if not page:
            break

        bugs.extend(page)
        offset += limit

    return bugs

def filter_changed_by_user(bug_ids, user_email, confirmed=False, verified=False):
    confirmed_bugs = []
    verified_bugs = []

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(fetch_history, bug["id"]): bug["id"] for bug in bug_ids}
        for future in as_completed(futures):
            bug_id, history = future.result()
            for change in history:
                if change["who"].lower() == user_email.lower():
                    for field in change["changes"]:
                        if confirmed:
                            if field["field_name"] == "status" and field["removed"] == "UNCONFIRMED":
                                confirmed_bugs.append(bug_id)
                        if verified:
                            if field["field_name"] == "status" and field["added"] == "VERIFIED":
                                verified_bugs.append(bug_id)
                        if bug_id in confirmed_bugs and bug_id in verified_bugs:
                            break

    return confirmed_bugs, verified_bugs

if __name__ == "__main__":
    for username in usernames:
        print(f"🔎 Fetching bugs commented on by {username} since {since}...")
        bugs = search_bugs_commented_on_by_user(username, product=search_products, limit=limit, since=since)
        print(f"=== 📝 Bugs commented on by {username}: {len(bugs)} ===")

        confirmed_bugs, verified_bugs = filter_changed_by_user(bugs, username, confirmed=True, verified=True)
        print(f"\n=== 📝 Bugs confirmed by {username}: {len(confirmed_bugs)} ===")
        for bug_id in confirmed_bugs:
            print(f"https://bugzilla.mozilla.org/show_bug.cgi?id={bug_id}")
        print(f"\n=== 📝 Bugs verified by {username}: {len(verified_bugs)} ===")
        for bug_id in verified_bugs:
            print(f"https://bugzilla.mozilla.org/show_bug.cgi?id={bug_id}")
