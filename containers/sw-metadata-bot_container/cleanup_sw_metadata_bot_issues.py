#!/usr/bin/env python3
"""Close obsolete sw-metadata-bot issues using one snapshot as source of truth."""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


BOT_ISSUE_TITLE = "Automated Metadata Quality Report from CodeMetaSoft"
BOT_BODY_MARKERS = (
    "This analysis is performed by the [CodeMetaSoft]",
    "This report was generated automatically by [sw-metadata-bot]",
)
GITHUB_API_BASE = "https://api.github.com"


@dataclass(frozen=True)
class RepositoryIssuePlan:
    repo_url: str
    canonical_issue_url: str | None
    kept_issue: str | None
    obsolete_issues: list[dict[str, Any]]
    skipped_reason: str | None = None


class GitHubClient:
    def __init__(self, token: str):
        self.token = token

    def _headers(self) -> dict[str, str]:
        return {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {self.token}",
            "User-Agent": "sqoo-sw-metadata-bot-cleanup",
        }

    def _request(
        self,
        method: str,
        url: str,
        payload: dict[str, Any] | None = None,
    ) -> Any:
        data = None
        headers = self._headers()
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        request = Request(url, data=data, headers=headers, method=method)
        try:
            with urlopen(request, timeout=20) as response:
                body = response.read().decode("utf-8")
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"GitHub API error {exc.code} for {method} {url}: {detail}"
            ) from exc

        if not body:
            return None
        return json.loads(body)

    def list_open_issues(self, repo_url: str) -> list[dict[str, Any]]:
        owner, repo = parse_github_repo_url(repo_url)
        issues: list[dict[str, Any]] = []
        page = 1

        while True:
            url = (
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues"
                f"?state=open&per_page=100&page={page}"
            )
            batch = self._request("GET", url)
            if not isinstance(batch, list):
                raise RuntimeError(f"Unexpected GitHub issues response for {repo_url}")

            issues.extend(
                issue
                for issue in batch
                if isinstance(issue, dict) and "pull_request" not in issue
            )

            if len(batch) < 100:
                break
            page += 1

        return issues

    def add_issue_comment(self, issue_url: str, body: str) -> None:
        owner, repo, number = parse_github_issue_url(issue_url)
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues/{number}/comments"
        self._request("POST", url, {"body": body})

    def close_issue(self, issue_url: str) -> None:
        owner, repo, number = parse_github_issue_url(issue_url)
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues/{number}"
        self._request("PATCH", url, {"state": "closed"})


def load_json_file(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def normalize_repo_url(repo_url: str) -> str:
    normalized = repo_url.strip().rstrip("/")
    if normalized.lower().endswith(".git"):
        normalized = normalized[:-4]
    return normalized


def normalize_for_lookup(repo_url: str) -> str:
    return normalize_repo_url(repo_url).lower()


def parse_github_repo_url(repo_url: str) -> tuple[str, str]:
    parsed = urlparse(normalize_repo_url(repo_url))
    if parsed.netloc.lower() != "github.com":
        raise ValueError(f"Only GitHub repository URLs are supported: {repo_url}")

    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(parts) < 2:
        raise ValueError(f"Invalid GitHub repository URL: {repo_url}")

    return parts[0], parts[1]


def parse_github_issue_url(issue_url: str) -> tuple[str, str, int]:
    parsed = urlparse(issue_url.strip())
    if parsed.netloc.lower() != "github.com":
        raise ValueError(f"Not a GitHub issue URL: {issue_url}")

    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(parts) < 4 or parts[2] != "issues":
        raise ValueError(f"Invalid GitHub issue URL: {issue_url}")

    return parts[0], parts[1], int(parts[3])


def issue_label(issue: dict[str, Any]) -> str:
    number = issue.get("number")
    if isinstance(number, int):
        return f"#{number}"
    html_url = issue.get("html_url")
    return str(html_url) if html_url else "#unknown"


def load_repositories_from_config(config_file: Path) -> list[str]:
    config = load_json_file(config_file)
    if not isinstance(config, dict):
        raise ValueError(f"Invalid config format in {config_file}: expected object")

    analysis = config.get("analysis")
    repos = None
    if isinstance(analysis, dict):
        repos = analysis.get("repositories")
    if repos is None:
        repos = config.get("repos_url")
    if repos is None:
        repos = config.get("repositories")

    if not isinstance(repos, list) or not all(isinstance(item, str) for item in repos):
        raise ValueError(
            f"{config_file} must contain a string list in 'analysis.repositories', "
            "'repos_url', or 'repositories'"
        )

    seen: set[str] = set()
    unique_repos: list[str] = []
    for repo in repos:
        normalized = normalize_repo_url(repo)
        lookup_key = normalize_for_lookup(normalized)
        if normalized and lookup_key not in seen:
            seen.add(lookup_key)
            unique_repos.append(normalized)

    return unique_repos


def load_snapshot_records(run_report_file: Path) -> dict[str, dict[str, Any]]:
    run_report = load_json_file(run_report_file)
    if not isinstance(run_report, dict):
        raise ValueError(f"Invalid run report format in {run_report_file}")

    records = run_report.get("records")
    if not isinstance(records, list):
        raise ValueError(f"{run_report_file} must contain a 'records' list")

    by_repo: dict[str, dict[str, Any]] = {}
    for record in records:
        if not isinstance(record, dict):
            continue

        repo_url = record.get("repo_url")
        if isinstance(repo_url, str) and repo_url.strip():
            by_repo[normalize_for_lookup(repo_url)] = record

    return by_repo


def canonical_issue_from_record(record: dict[str, Any]) -> str | None:
    for field in ("issue_url", "previous_issue_url"):
        value = record.get(field)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def normalize_issue_url(issue_url: str) -> str:
    return issue_url.strip().rstrip("/")


def body_mentions_repo(body: str, repo_url: str) -> bool:
    normalized_body = body.replace(".git", "")
    return normalize_repo_url(repo_url).lower() in normalized_body.lower()


def is_bot_issue(issue: dict[str, Any], repo_url: str) -> bool:
    if issue.get("title") != BOT_ISSUE_TITLE:
        return False

    body = issue.get("body")
    if not isinstance(body, str):
        return False

    return (
        all(marker in body for marker in BOT_BODY_MARKERS)
        and "**Repository:**" in body
        and body_mentions_repo(body, repo_url)
    )


def build_cleanup_plan(
    client: GitHubClient,
    repo_url: str,
    record: dict[str, Any] | None,
) -> RepositoryIssuePlan:
    if record is None:
        return RepositoryIssuePlan(
            repo_url=repo_url,
            canonical_issue_url=None,
            kept_issue=None,
            obsolete_issues=[],
            skipped_reason="repository not found in snapshot",
        )

    if record.get("action") == "failed":
        return RepositoryIssuePlan(
            repo_url=repo_url,
            canonical_issue_url=None,
            kept_issue=None,
            obsolete_issues=[],
            skipped_reason="snapshot record action is failed",
        )

    canonical_issue_url = canonical_issue_from_record(record)
    if record.get("action") == "closed":
        canonical_issue_url = None

    issues = client.list_open_issues(repo_url)
    obsolete_issues: list[dict[str, Any]] = []
    kept_issue: str | None = None

    for issue in issues:
        if not is_bot_issue(issue, repo_url):
            continue

        issue_url = issue.get("html_url")
        if not isinstance(issue_url, str) or not issue_url.strip():
            continue

        if canonical_issue_url and normalize_issue_url(issue_url) == normalize_issue_url(
            canonical_issue_url
        ):
            kept_issue = issue_url
            continue

        obsolete_issues.append(issue)

    return RepositoryIssuePlan(
        repo_url=repo_url,
        canonical_issue_url=canonical_issue_url,
        kept_issue=kept_issue,
        obsolete_issues=obsolete_issues,
    )


def print_repository_plan(plan: RepositoryIssuePlan, apply: bool) -> None:
    print(f"Repository: {plan.repo_url}")

    if plan.skipped_reason:
        print(f"SKIP: {plan.skipped_reason}")
        print()
        return

    canonical = plan.canonical_issue_url or "None"
    print(f"Canonical issue: {canonical}")
    print()

    if plan.kept_issue:
        print(f"KEEP:  {plan.kept_issue}")
    elif plan.canonical_issue_url:
        print(f"KEEP:  {plan.canonical_issue_url} (not currently open or not detected)")
    else:
        print("KEEP:  none")

    close_label = "CLOSED" if apply else "CLOSE"
    if plan.obsolete_issues:
        for issue in plan.obsolete_issues:
            print(f"{close_label}: {issue_label(issue)} {issue.get('html_url', '')}")
    else:
        print(f"{close_label}: none")

    print()


def cleanup_obsolete_issues(
    client: GitHubClient,
    plan: RepositoryIssuePlan,
    *,
    apply: bool,
) -> int:
    if not apply or plan.skipped_reason:
        return 0

    closed = 0
    for issue in plan.obsolete_issues:
        issue_url = issue.get("html_url")
        if not isinstance(issue_url, str) or not issue_url:
            continue

        if plan.canonical_issue_url:
            comment = (
                "Closing this obsolete automated metadata report. "
                f"The issue selected by the snapshot is {plan.canonical_issue_url}."
            )
        else:
            comment = (
                "Closing this obsolete automated metadata report because the selected "
                "snapshot does not require an open metadata issue for this repository."
            )

        client.add_issue_comment(issue_url, comment)
        client.close_issue(issue_url)
        closed += 1

    return closed


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Close obsolete sw-metadata-bot GitHub issues using a run_report.json "
            "snapshot as source of truth."
        )
    )
    parser.add_argument(
        "--run-report",
        type=Path,
        required=True,
        help="Path to the selected snapshot run_report.json.",
    )
    parser.add_argument(
        "--config-file",
        type=Path,
        required=True,
        help=(
            "Project config JSON containing analysis.repositories, repos_url, "
            "or repositories."
        ),
    )

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Only print which issue would be kept and which issues would be closed.",
    )
    mode.add_argument(
        "--apply",
        action="store_true",
        help="Comment on and close obsolete issues on GitHub.",
    )

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])

    token = os.environ.get("GITHUB_API_TOKEN")
    if not token:
        print("ERROR: GITHUB_API_TOKEN environment variable is required.", file=sys.stderr)
        return 2

    try:
        repos = load_repositories_from_config(args.config_file)
        records_by_repo = load_snapshot_records(args.run_report)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    client = GitHubClient(token)
    total_closed = 0
    total_obsolete = 0
    total_skipped = 0

    for repo_url in repos:
        try:
            record = records_by_repo.get(normalize_for_lookup(repo_url))
            plan = build_cleanup_plan(client, repo_url, record)

            if plan.skipped_reason:
                print_repository_plan(plan, apply=args.apply)
                total_skipped += 1
                continue

            total_obsolete += len(plan.obsolete_issues)
            closed = cleanup_obsolete_issues(client, plan, apply=args.apply)
            total_closed += closed
            print_repository_plan(plan, apply=args.apply)
        except Exception as exc:
            total_skipped += 1
            print(f"Repository: {repo_url}")
            print(f"SKIP: {exc}")
            print()

    mode = "apply" if args.apply else "dry-run"
    print("Summary")
    print(f"Mode: {mode}")
    print(f"Repositories requested: {len(repos)}")
    print(f"Repositories skipped: {total_skipped}")
    print(f"Obsolete issues found: {total_obsolete}")
    if args.apply:
        print(f"Obsolete issues closed: {total_closed}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
