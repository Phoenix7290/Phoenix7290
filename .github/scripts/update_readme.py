#!/usr/bin/env python3
"""Update the RECENT_REPOS section in README.md using the GitHub REST API."""

import json
import os
import re
import urllib.request
from pathlib import Path

USERNAME = os.environ.get("GITHUB_REPOSITORY_OWNER", "Phoenix7290")
README_PATH = Path("README.md")
START_MARKER = "<!-- RECENT_REPOS:START -->"
END_MARKER = "<!-- RECENT_REPOS:END -->"


def fetch_recent_repos(username: str, limit: int = 4) -> list[dict]:
    """Fetch the most recently pushed public non-fork repositories."""
    url = f"https://api.github.com/users/{username}/repos?sort=pushed&direction=desc&per_page=20&type=owner"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": f"{username}-profile-updater",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        repos = json.loads(resp.read().decode("utf-8"))

    filtered = [
        r for r in repos
        if not r.get("fork") and not r.get("private") and r.get("name") != username
    ]
    return filtered[:limit]


def format_repos(repos: list[dict]) -> str:
    """Format repository list as clean Markdown bullets."""
    lines = []
    for repo in repos:
        name = repo["name"]
        url = repo["html_url"]
        lang = repo.get("language") or "Markdown"
        desc = (repo.get("description") or "").strip()
        updated = repo.get("pushed_at", "")[:10]
        if desc:
            lines.append(f"- **[{name}]({url})** (`{lang}` · updated {updated}) — {desc}")
        else:
            lines.append(f"- **[{name}]({url})** (`{lang}` · updated {updated})")
    return "\n".join(lines)


def main() -> None:
    content = README_PATH.read_text(encoding="utf-8")
    pattern = re.compile(
        rf"({re.escape(START_MARKER)}\n)(.*?)(\n{re.escape(END_MARKER)})",
        re.DOTALL,
    )
    if not pattern.search(content):
        raise SystemExit("Markers not found in README.md")

    repos = fetch_recent_repos(USERNAME)
    block = format_repos(repos)
    updated = pattern.sub(rf"\1{block}\3", content, count=1)

    if updated != content:
        README_PATH.write_text(updated, encoding="utf-8")
        print("README.md updated.")
    else:
        print("README.md already up to date.")


if __name__ == "__main__":
    main()
