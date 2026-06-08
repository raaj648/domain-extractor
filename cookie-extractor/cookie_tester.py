import argparse
import json
import re
from pathlib import Path

import requests


LOGIN_REQUIRED_PATTERNS = [
    re.compile(r"Login\s*/\s*Sign\s*Up", re.IGNORECASE),
    re.compile(r"You must be logged in", re.IGNORECASE),
]


def load_cookies_from_export(export_path: str):
    p = Path(export_path)
    if not p.exists():
        raise FileNotFoundError(f"Cookie export not found: {export_path}")

    data = json.loads(p.read_text(encoding="utf-8"))

    # Accept both formats:
    # 1) {"cookies":[{"name":...,"value":...,...}, ...], ...}
    # 2) {"cookies":[{"name":...,"value":...}, ...]} (same)
    cookies = data.get("cookies")
    if not isinstance(cookies, list):
        raise ValueError("Invalid export JSON: expected top-level 'cookies' array.")

    cookie_dict = {}
    for c in cookies:
        name = c.get("name")
        value = c.get("value")
        if not name:
            continue
        if value is None:
            raise ValueError(
                "Cookie export does not include values. Re-run manual_cookie_export.py with --show-values true."
            )
        cookie_dict[name] = value

    return cookie_dict


def looks_authenticated(html: str):
    return not any(p.search(html or "") for p in LOGIN_REQUIRED_PATTERNS)


def main():
    parser = argparse.ArgumentParser(description="Test whether exported cookies can access authenticated pages.")
    parser.add_argument("--cookies-export", default="cookies_member.json", help="Path to the exported cookies JSON (must include values).")
    parser.add_argument("--url", default="https://member.expireddomains.net/", help="URL to test with cookies.")
    parser.add_argument("--output-html", default="last_response.html", help="Where to save the HTML response.")
    args = parser.parse_args()

    cookies = load_cookies_from_export(args.cookies_export)

    # Note: requests uses a simple Cookie jar; HttpOnly/secure/samesite flags are not needed here.
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    resp = requests.get(args.url, headers=headers, cookies=cookies, timeout=30)

    Path(args.output_html).write_text(resp.text or "", encoding="utf-8")

    ok = looks_authenticated(resp.text)
    print("=== Cookie Tester Result ===")
    print(f"URL: {args.url}")
    print(f"HTTP Status: {resp.status_code}")
    print(f"Authenticated Likely: {ok}")
    print(f"Cookie keys sent: {list(cookies.keys())}")
    print(f"Saved HTML to: {args.output_html}")

    if not ok:
        # Show a short snippet around the first match if present
        for pat in LOGIN_REQUIRED_PATTERNS:
            m = pat.search(resp.text or "")
            if m:
                start = max(m.start() - 120, 0)
                end = min(m.end() + 120, len(resp.text))
                snippet = (resp.text or "")[start:end]
                print("\nLogin-required pattern snippet (for debugging):")
                print(snippet)
                break


if __name__ == "__main__":
    main()
