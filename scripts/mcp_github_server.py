"""Minimal MCP server (stdio transport, JSON-RPC 2.0, newline-delimited) exposing one tool: recent_commits.

Stdlib only. The commit agent in generate.py spawns this and talks to it as an MCP client.
"""
import json
import re
import sys
import urllib.request

PROTOCOL = "2025-06-18"
USER_RE = re.compile(r"^[A-Za-z0-9-]{1,39}$")

TOOLS = [{
    "name": "recent_commits",
    "description": "Latest public commit messages pushed by a GitHub user, as 'repo: message' lines.",
    "inputSchema": {
        "type": "object",
        "properties": {"user": {"type": "string"}, "limit": {"type": "integer", "default": 8}},
        "required": ["user"],
    },
}]


def recent_commits(user: str, limit: int = 8) -> list[str]:
    if not USER_RE.match(user):
        raise ValueError("invalid GitHub username")
    events = _get(f"https://api.github.com/users/{user}/events/public")
    msgs, seen = [], set()
    for e in events:
        # public push events carry only the head SHA now, so look the commit up
        if e.get("type") != "PushEvent" or len(msgs) >= limit:
            continue
        head = e["payload"].get("head")
        if not head or head in seen:
            continue
        seen.add(head)
        try:
            c = _get(f'https://api.github.com/repos/{e["repo"]["name"]}/commits/{head}')
        except Exception:  # private/deleted repo or rate limit: skip this push
            continue
        msgs.append(f'{e["repo"]["name"].split("/")[-1]}: {c["commit"]["message"].splitlines()[0][:80]}')
    return msgs


def _get(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "profile-mcp-github"})
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
            out = recent_commits(args["user"], int(args.get("limit", 8)))
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
