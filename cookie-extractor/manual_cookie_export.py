import argparse
import json
from datetime import datetime

from playwright.sync_api import sync_playwright

LOGIN_URL = "https://member.expireddomains.net/"
TARGET_DOMAIN = "member.expireddomains.net"


def cookie_to_item(c, show_values: bool):
    item = {
        "name": c.get("name"),
        "domain": c.get("domain"),
        "path": c.get("path"),
        "httpOnly": c.get("httpOnly"),
        "secure": c.get("secure"),
        "sameSite": c.get("sameSite"),
        "expires": c.get("expires"),
    }
    if show_values:
        item["value"] = c.get("value")
    return item


def export_all_cookies(context, show_values: bool):
    cookies = context.cookies()
    return [cookie_to_item(c, show_values=show_values) for c in cookies]


def export_cookies_for_target_domain(context, show_values: bool):
    cookies = context.cookies()
    filtered = [c for c in cookies if c.get("domain") and TARGET_DOMAIN in c.get("domain", "")]
    return [cookie_to_item(c, show_values=show_values) for c in filtered]


def main():
    parser = argparse.ArgumentParser(description="Manual login cookie export (no credentials in code).")
    parser.add_argument("--output", default="cookies_member.json", help="Output JSON file path for target domain cookies.")
    parser.add_argument("--show-values", default="false", help="true/false. Only show if you must.")
    parser.add_argument("--wait-seconds", type=int, default=30, help="Time to allow manual login.")
    parser.add_argument("--all-output", default="cookies_all.json", help="Output JSON file path for ALL cookies in the context.")
    args = parser.parse_args()

    show_values = str(args.show_values).lower() in ("1", "true", "yes", "y")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print(f"[1] Opening: {LOGIN_URL}")
        page.goto(LOGIN_URL, wait_until="load")

        print("\n[2] Please log in manually in the opened browser window.")
        print(f"[3] Waiting {args.wait_seconds} seconds for you to complete login...")
        page.wait_for_timeout(args.wait_seconds * 1000)

        cookies_target = export_cookies_for_target_domain(context, show_values=show_values)
        cookies_all = export_all_cookies(context, show_values=show_values)

        payload_target = {
            "exported_at_utc": datetime.utcnow().isoformat() + "Z",
            "target_domain": TARGET_DOMAIN,
            "cookie_count": len(cookies_target),
            "cookies": cookies_target,
            "show_values": show_values,
            "note": "Filtered to cookies where TARGET_DOMAIN is included in cookie.domain.",
        }

        payload_all = {
            "exported_at_utc": datetime.utcnow().isoformat() + "Z",
            "cookie_count": len(cookies_all),
            "cookies": cookies_all,
            "show_values": show_values,
            "note": "All cookies returned by Playwright context.cookies().",
        }

        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(payload_target, f, indent=2)

        with open(args.all_output, "w", encoding="utf-8") as f:
            json.dump(payload_all, f, indent=2)

        print(f"\n[✓] Exported {len(cookies_target)} target-domain cookies to: {args.output}")
        print(f"[✓] Exported {len(cookies_all)} all cookies to: {args.all_output}")

        if not show_values:
            print("    (Cookie values were NOT included. Re-run with --show-values true if needed.)")

        print("\n[4] Keeping browser open for 10 seconds...")
        page.wait_for_timeout(10 * 1000)
        browser.close()


if __name__ == "__main__":
    main()
