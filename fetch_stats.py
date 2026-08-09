#!/usr/bin/env python3
"""
Pulls live GitHub numbers (repos, stars, commits, followers, lines of code)
and caches them to assets/stats.json, which generate_neofetch.py
reads when it renders the SVGs.

    GH_USER=Just-Taco GH_PAT=<token> python fetch_stats.py

Run without a token and it does nothing (leaving the last cached numbers in
place), so local runs of generate_neofetch.py still work offline.

A classic PAT with `public_repo` + `read:user` gives the best numbers.
The Action's built-in GITHUB_TOKEN also works, but cannot see commits made
to repositories outside this one, so the commit count will read low.
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request

USER = os.environ.get("GH_USER", "Just-Taco")
TOKEN = os.environ.get("GH_PAT") or os.environ.get("GITHUB_TOKEN") or ""

# Public repos only by default. Set GH_INCLUDE_PRIVATE=1 to fold private
# repos into the totals — the counts are aggregate, no names are published,
# but it does reveal roughly how much private work there is.
PRIVACY = None if os.environ.get("GH_INCLUDE_PRIVATE") else "PUBLIC"

# Languages to leave out of the breakdown — vendored assets and generated
# files otherwise drown out the code you actually wrote.
EXCLUDE_LANGUAGES = {"Roff", "Makefile", "Batchfile", "Dockerfile"}

TOP_LANGUAGES = 8
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "assets", "stats.json")

API = "https://api.github.com"
GRAPHQL = "https://api.github.com/graphql"


def request(url, data=None, retries=6):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "just-taco-profile",
        "Authorization": f"bearer {TOKEN}",
    }
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers)

    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                # 202 = GitHub is computing the stats; ask again shortly.
                if resp.status == 202:
                    time.sleep(3 * (attempt + 1))
                    continue
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as err:
            if err.code in (202, 403, 502) and attempt < retries - 1:
                time.sleep(3 * (attempt + 1))
                continue
            raise
    return None


def graphql(query, **variables):
    payload = request(GRAPHQL, {"query": query, "variables": variables})
    if payload and payload.get("errors"):
        raise RuntimeError(payload["errors"])
    return (payload or {}).get("data")


PROFILE_QUERY = """
query($login: String!, $cursor: String, $privacy: RepositoryPrivacy) {
  user(login: $login) {
    createdAt
    followers { totalCount }
    repositories(first: 100, after: $cursor, ownerAffiliations: OWNER,
                 privacy: $privacy, isFork: false,
                 orderBy: {field: PUSHED_AT, direction: DESC}) {
      totalCount
      pageInfo { hasNextPage endCursor }
      nodes {
        name
        stargazerCount
        languages(first: 12, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
      }
    }
  }
}
"""

CONTRIB_QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      totalCommitContributions
      restrictedContributionsCount
    }
  }
}
"""


def collect_repos():
    """All non-fork repos, plus stars, followers and the language mix."""
    repos, stars, cursor = [], 0, None
    created, followers, total = None, 0, 0
    sizes, colours = {}, {}

    while True:
        user = graphql(PROFILE_QUERY, login=USER, cursor=cursor,
                       privacy=PRIVACY)["user"]
        block = user["repositories"]
        created = created or user["createdAt"]
        followers = user["followers"]["totalCount"]
        total = block["totalCount"]

        for node in block["nodes"]:
            repos.append(node["name"])
            stars += node["stargazerCount"]

            for edge in node["languages"]["edges"]:
                name = edge["node"]["name"]
                if name in EXCLUDE_LANGUAGES:
                    continue
                sizes[name] = sizes.get(name, 0) + edge["size"]
                colours[name] = edge["node"]["color"] or "#8b949e"

        if not block["pageInfo"]["hasNextPage"]:
            break
        cursor = block["pageInfo"]["endCursor"]

    ranked = sorted(sizes.items(), key=lambda kv: kv[1], reverse=True)
    languages = [{"name": name, "size": size, "color": colours[name]}
                 for name, size in ranked[:TOP_LANGUAGES]]

    return repos, stars, followers, total, created, languages


def collect_commits(created_at):
    """Commit contributions, summed year by year since the account opened."""
    total = 0
    year = int(created_at[:4])
    now = time.gmtime().tm_year

    while year <= now:
        data = graphql(CONTRIB_QUERY, login=USER,
                       **{"from": f"{year}-01-01T00:00:00Z",
                          "to": f"{year}-12-31T23:59:59Z"})
        block = data["user"]["contributionsCollection"]
        total += (block["totalCommitContributions"]
                  + block["restrictedContributionsCount"])
        year += 1

    return total


def collect_lines(repos):
    """
    Additions/deletions authored by USER across every repo.

    Also reports how many repos we failed to read. GitHub computes the
    contributor statistics lazily and answers 202 until the numbers are
    ready, so a repo can drop out of a run through no fault of its own —
    and silently undercounting would make the published total jitter.
    """
    added = deleted = skipped = 0

    for name in repos:
        try:
            contributors = request(
                f"{API}/repos/{USER}/{name}/stats/contributors")
        except urllib.error.HTTPError as err:
            print(f"  skip {name}: HTTP {err.code}", file=sys.stderr)
            skipped += 1
            continue

        if contributors is None:
            print(f"  skip {name}: stats still computing", file=sys.stderr)
            skipped += 1
            continue

        for entry in contributors or []:
            author = (entry.get("author") or {}).get("login", "")
            if author.lower() != USER.lower():
                continue
            for week in entry.get("weeks", []):
                added += week.get("a", 0)
                deleted += week.get("d", 0)

    return added, deleted, skipped


def main():
    if not TOKEN:
        print("No GH_PAT / GITHUB_TOKEN set — keeping cached stats.")
        return 0

    repos, stars, followers, repo_count, created, languages = collect_repos()
    print(f"{repo_count} repos, {stars} stars, {followers} followers")
    print("languages: " + ", ".join(l["name"] for l in languages))

    commits = collect_commits(created)
    print(f"{commits} commits")

    added, deleted, skipped = collect_lines(repos)
    print(f"{added} added, {deleted} deleted ({skipped} repos unavailable)")

    # An incomplete scan must never publish a smaller total than we already
    # have, or the line count would visibly bounce around between runs.
    if skipped:
        try:
            with open(OUT, encoding="utf-8") as fh:
                previous = json.load(fh)
            if previous.get("loc_added", 0) > added:
                print("keeping previous line counts; this scan was partial")
                added = previous["loc_added"]
                deleted = previous["loc_deleted"]
        except (OSError, ValueError, KeyError):
            pass

    stats = {
        "repos": repo_count,
        "stars": stars,
        "commits": commits,
        "followers": followers,
        "loc_added": added,
        "loc_deleted": deleted,
        "loc_total": added - deleted,
        "languages": languages,
        "updated": time.strftime("%Y-%m-%d", time.gmtime()),
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(stats, fh, indent=2)
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
