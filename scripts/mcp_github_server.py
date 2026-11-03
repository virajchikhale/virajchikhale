"""Minimal MCP server (stdio transport, JSON-RPC 2.0, newline-delimited) exposing one tool: recent_commits.

Stdlib only. The commit agent in generate.py spawns this and talks to it as an MCP client.
"""
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timedelta, timezone

PROTOCOL = "2025-06-18"
USER_RE = re.compile(r"^[A-Za-z0-9-]{1,39}$")
# repos that hold data/content rather than code; their pushes say nothing about what is being built
EXCLUDE_REPOS = {"insta_studio"}

TOOLS = [{
    "name": "recent_commits",
    "description": ("Recent public commits by a GitHub user across their most recently pushed repos, one line each: "
                    "'date repo (+added/-removed, N files): message'. Newest first."),
    "inputSchema": {
        "type": "object",
        "properties": {
            "user": {"type": "string"},
            "per_repo": {"type": "integer", "default": 5},
            "days": {"type": "integer", "default": 30},
            "max_repos": {"type": "integer", "default": 6},
        },
        "required": ["user"],
    },
}]


def recent_commits(user: str, per_repo: int = 5, days: int = 30, max_repos: int = 6) -> list[str]:
    if not USER_RE.match(user):
        raise ValueError("invalid GitHub username")
    per_repo, days, max_repos = max(1, min(per_repo, 10)), max(1, min(days, 90)), max(1, min(max_repos, 10))
    since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    repos = _get(f"https://api.github.com/users/{user}/repos?sort=pushed&per_page=30")
    picked = [r for r in repos
              if not r["fork"] and not r["archived"] and r["name"] not in EXCLUDE_REPOS
              and r["name"].lower() != user.lower() and (r.get("pushed_at") or "") >= since][:max_repos]
    lines = []
    for r in picked:
        try:
            commits = _get(f'https://api.github.com/repos/{r["full_name"]}/commits'
                           f'?author={user}&since={since}&per_page={per_repo * 3}')
        except Exception:  # private/deleted repo or rate limit: skip this repo
            continue
        kept = 0
        for c in commits:
            if kept >= per_repo:
                break
            if len(c.get("parents", [])) > 1:  # PR merge commit: its real commits are listed on their own
                continue
            kept += 1
            subject = c["commit"]["message"].splitlines()[0][:90]
            try:
                d = _get(f'https://api.github.com/repos/{r["full_name"]}/commits/{c["sha"]}')
                st = d.get("stats", {})
                size = f' (+{st.get("additions", 0)}/-{st.get("deletions", 0)}, {len(d.get("files", []))} files)'
            except Exception:  # size is a hint only
                size = ""
            lines.append((c["commit"]["author"]["date"], f'{c["commit"]["author"]["date"][:10]} {r["name"]}{size}: {subject}'))
    return [text for _, text in sorted(lines, reverse=True)]


def _get(url: str):
    headers = {"User-Agent": "profile-mcp-github", "Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if token:  # raises the API limit from 60 to 5000 requests/hour; read-only use
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.load(r)


def handle(msg: dict) -> dict | None:
    method, mid = msg.get("method"), msg.get("id")
    if mid is None:  # notification (e.g. notifications/initialized): no response
        return None
    if method == "initialize":
        result = {"protocolVersion": PROTOCOL, "capabilities": {"tools": {}},
                  "serverInfo": {"name": "github-commits", "version": "1.0.0"}}
    elif method == "tools/list":
        result = {"tools": TOOLS}
    elif method == "tools/call":
        params = msg.get("params", {})
        try:
            if params.get("name") != "recent_commits":
                raise ValueError("unknown tool")
            args = params.get("arguments", {})
            out = recent_commits(args["user"], int(args.get("per_repo", 5)), int(args.get("days", 30)),
                                 int(args.get("max_repos", 6)))
            result = {"content": [{"type": "text", "text": json.dumps(out)}]}
        except Exception as e:
            result = {"isError": True, "content": [{"type": "text", "text": str(e)}]}
    else:
        return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": "method not found"}}
    return {"jsonrpc": "2.0", "id": mid, "result": result}


def main() -> None:
    for line in sys.stdin:
        if not line.strip():
            continue
        resp = handle(json.loads(line))
        if resp is not None:
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
