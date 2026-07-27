from __future__ import annotations

import argparse
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

ORGANIZATION = "loganpendragonmultiverse"
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "monitoring-data"


def gh_json(arguments: list[str]) -> Any:
    completed = subprocess.run(
        ["gh", "api", *arguments], capture_output=True, text=True, check=False, encoding="utf-8"
    )
    if completed.returncode:
        raise RuntimeError(completed.stderr.strip() or "GitHub CLI request failed")
    return json.loads(completed.stdout)


def public_repositories() -> list[dict[str, Any]]:
    return gh_json([f"orgs/{ORGANIZATION}/repos?type=public&per_page=100&sort=full_name"])


def repository_metrics(repository: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    name = str(repository["name"])
    base = f"repos/{ORGANIZATION}/{name}"
    views = gh_json([f"{base}/traffic/views"])
    clones = gh_json([f"{base}/traffic/clones"])
    releases = gh_json([f"{base}/releases?per_page=100"])
    downloads = sum(
        int(asset.get("download_count", 0))
        for release in releases
        for asset in release.get("assets", [])
    )
    return name, {
        "url": repository["html_url"],
        "stars": int(repository.get("stargazers_count", 0)),
        "forks": int(repository.get("forks_count", 0)),
        "open_issues_and_prs": int(repository.get("open_issues_count", 0)),
        "views_14d": {"count": int(views["count"]), "uniques": int(views["uniques"])},
        "clones_14d": {"count": int(clones["count"]), "uniques": int(clones["uniques"])},
        "release_asset_downloads": downloads,
    }


def recent_pull_requests(since: str) -> list[dict[str, Any]]:
    query = """query($org:String!){organization(login:$org){repositories(first:100,privacy:PUBLIC){nodes{name pullRequests(first:20,orderBy:{field:CREATED_AT,direction:DESC}){nodes{id number title url createdAt state author{login}}}}}}}"""
    result = gh_json(["graphql", "-f", f"query={query}", "-F", f"org={ORGANIZATION}"])
    pull_requests = []
    for repository in result["data"]["organization"]["repositories"]["nodes"]:
        for item in repository["pullRequests"]["nodes"]:
            if item["createdAt"][:10] < since:
                continue
            pull_requests.append(
                {"id": item["id"], "number": item["number"], "title": item["title"],
                 "url": item["url"], "repository": repository["name"],
                 "created_at": item["createdAt"], "state": item["state"],
                 "author": item["author"]["login"] if item["author"] else "deleted-user"}
            )
    return sorted(pull_requests, key=lambda item: item["created_at"], reverse=True)


def recent_discussions() -> list[dict[str, Any]]:
    query = """query($org:String!){organization(login:$org){repositories(first:100,privacy:PUBLIC){nodes{name discussions(first:20,orderBy:{field:CREATED_AT,direction:DESC}){nodes{id number title url createdAt author{login}}}}}}}"""
    result = gh_json(["graphql", "-f", f"query={query}", "-F", f"org={ORGANIZATION}"])
    discussions = []
    for repository in result["data"]["organization"]["repositories"]["nodes"]:
        for item in repository["discussions"]["nodes"]:
            discussions.append(
                {"id": item["id"], "number": item["number"], "title": item["title"],
                 "url": item["url"], "repository": repository["name"],
                 "created_at": item["createdAt"],
                 "author": item["author"]["login"] if item["author"] else "deleted-user"}
            )
    return sorted(discussions, key=lambda item: item["created_at"], reverse=True)


def capture(data_dir: Path = DATA_DIR) -> Path:
    now = datetime.now(UTC)
    repositories = public_repositories()
    metrics: dict[str, dict[str, Any]] = {}
    failures = []
    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = {executor.submit(repository_metrics, repository): repository["name"] for repository in repositories}
        for future in as_completed(futures):
            try:
                name, values = future.result()
                metrics[name] = values
            except (KeyError, RuntimeError, TypeError, ValueError) as exc:
                failures.append({"repository": futures[future], "error": str(exc)})
    snapshot = {
        "schema_version": 1, "organization": ORGANIZATION, "captured_at": now.isoformat(),
        "repository_count": len(repositories), "repositories": dict(sorted(metrics.items())),
        "pull_requests": recent_pull_requests((now - timedelta(days=14)).date().isoformat()),
        "discussions": recent_discussions(), "failures": failures,
    }
    data_dir.mkdir(parents=True, exist_ok=True)
    path = data_dir / f"{now.date().isoformat()}.json"
    path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def snapshots(data_dir: Path = DATA_DIR) -> list[dict[str, Any]]:
    return [json.loads(path.read_text(encoding="utf-8")) for path in sorted(data_dir.glob("*.json"))]


def new_activity(current: dict[str, Any], previous: dict[str, Any] | None) -> dict[str, list[dict[str, Any]]]:
    previous = previous or {"pull_requests": [], "discussions": []}
    old_prs = {item["id"] for item in previous["pull_requests"]}
    old_discussions = {item["id"] for item in previous["discussions"]}
    return {
        "pull_requests": [item for item in current["pull_requests"] if item["id"] not in old_prs],
        "discussions": [item for item in current["discussions"] if item["id"] not in old_discussions],
    }


def build_digest(history: list[dict[str, Any]]) -> str:
    if not history:
        raise ValueError("no monitoring snapshots are available")
    current = history[-1]
    baseline = history[max(0, len(history) - 8)]
    activity = new_activity(current, baseline)
    rows = []
    for name, values in current["repositories"].items():
        old = baseline["repositories"].get(name, {})
        rows.append((values["views_14d"]["count"], name, values,
                     values["release_asset_downloads"] - int(old.get("release_asset_downloads", 0)),
                     values["stars"] - int(old.get("stars", 0))))
    rows.sort(reverse=True)
    lines = ["# Logan Pendragon Multiverse Open-Source Digest", "",
             f"Captured: {current['captured_at']} - Repositories: {current['repository_count']}", "",
             f"New pull requests: **{len(activity['pull_requests'])}** - New discussions: **{len(activity['discussions'])}**", "",
             "Traffic and clone totals are aggregate GitHub signals and can include automation or CI; they do not identify individual users.", "",
             "## Most Viewed (rolling 14 days)", "", "| Repository | Views | Unique visitors | Clones | Downloads change | Stars change |", "|---|---:|---:|---:|---:|---:|"]
    for _, name, values, downloads_delta, stars_delta in rows[:15]:
        lines.append(f"| {name} | {values['views_14d']['count']} | {values['views_14d']['uniques']} | {values['clones_14d']['count']} | {downloads_delta:+d} | {stars_delta:+d} |")
    for title, key in (("New Pull Requests", "pull_requests"), ("New Discussions", "discussions")):
        lines.extend(["", f"## {title}", ""])
        items = activity[key]
        lines.extend([f"- [{item['repository']} #{item.get('number', '')}: {item['title']}]({item['url']}) by @{item['author']}" for item in items] or ["- None."])
    if current["failures"]:
        lines.extend(["", "## Collection Warnings", ""])
        lines.extend(f"- {item['repository']}: {item['error']}" for item in current["failures"])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Retain organization-wide GitHub activity and usage signals.")
    parser.add_argument("command", choices=("capture", "digest", "capture-and-digest"))
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    args = parser.parse_args()
    if args.command in {"capture", "capture-and-digest"}:
        print(capture(args.data_dir))
    if args.command in {"digest", "capture-and-digest"}:
        digest = build_digest(snapshots(args.data_dir))
        output = args.data_dir / "latest-digest.md"
        output.write_text(digest, encoding="utf-8")
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
