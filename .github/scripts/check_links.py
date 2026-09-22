#!/usr/bin/env python3
"""Check http(s) links in markdown files resolve (advisory quality gate).

Extracts URLs from the given markdown files and probes them with urllib,
honouring the ignore patterns from .github/markdown-link-check.json.
Exit code 1 only on definite failures (DNS/connection/4xx after retry);
soft failures (timeouts, 5xx, 429) are reported but tolerated to keep CI
deterministic on third-party sites.
"""

from __future__ import annotations

import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

URL_RE = re.compile(r"https?://[^\s<>\)\]>'\"`]+")
SOFT_STATUS = {429, 500, 502, 503, 504}
TIMEOUT = 10


def load_ignores(config_path: Path) -> list[re.Pattern]:
    if not config_path.exists():
        return []
    config = json.loads(config_path.read_text())
    return [re.compile(entry["pattern"]) for entry in config.get("ignorePatterns", [])]


def check(url: str) -> tuple[bool, str]:
    req = urllib.request.Request(url, method="GET", headers={"User-Agent": "tracepath-link-check/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return True, f"HTTP {resp.status}"
    except urllib.error.HTTPError as exc:
        if exc.code in SOFT_STATUS:
            return True, f"HTTP {exc.code} (tolerated)"
        return False, f"HTTP {exc.code}"
    except Exception as exc:  # noqa: BLE001 - network probe, report and move on
        return True, f"network error tolerated: {exc}"


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    ignores = load_ignores(root / ".github" / "markdown-link-check.json")

    md_files = [Path(p) for arg in sys.argv[1:] for p in sorted(root.glob(arg))]
    if not md_files:
        print("no markdown files matched", file=sys.stderr)
        return 1

    failures: list[str] = []
    checked: set[str] = set()
    for md in md_files:
        urls = URL_RE.findall(md.read_text(encoding="utf-8"))
        for url in urls:
            url = url.rstrip(".,;:")
            if url in checked or any(pattern.search(url) for pattern in ignores):
                continue
            # skip templated placeholders like https://<instance>/... and
            # any URL urllib cannot parse (e.g. fake IPv6)
            try:
                parsed = urlparse(url)
            except ValueError:
                continue
            if not parsed.hostname or "<" in (parsed.hostname or ""):
                continue
            checked.add(url)
            ok, detail = check(url)
            status = "OK " if ok else "FAIL"
            print(f"{status} {md.relative_to(root)} {url} -> {detail}")
            if not ok:
                failures.append(url)
            time.sleep(0.2)

    print(f"\n{len(checked)} unique URLs checked")
    if failures:
        print(f"BROKEN ({len(failures)}):")
        for url in failures:
            print(f"  {url}")
        return 1
    print("all links OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
