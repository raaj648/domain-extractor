# AGENTS.md for scraper

## Purpose
- Extract domain listings from ExpiredDomains.net and store them in Supabase.

## Ownership
- Owner: Project maintainer (AR Khan)

## Local Contracts
- Reads configuration from the `settings` table in Supabase.
- Must respect the `max_extract_domains` integer limit (if set) to cap the number of domains processed per run.
- Uses cookies from `settings.cookies` (JSON object) for authentication.
- Sends Telegram alerts based on `settings.telegram` preferences.
- Stores results in `tracked_domains` table and logs in `scrape_jobs` table.

## Work Guidance
- Run via `python scraper/scrape.py` (requires `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` env vars).
- During testing, set `max_extract_domains` to a low value (e.g., 10) in the dashboard Settings → Scraper Limits.
- If the limit is reached, the scraper logs a notice and stops processing further rows/targets.
- Ensure cookies are fresh; expired cookies will raise an exception.

## Verification
- Run with a low limit (e.g., 5) and verify only 5 domains are inserted into `tracked_domains`.
- Check `scrape_jobs` table for `domains_found` and `domains_inserted` counts matching the limit.
- Telegram notifications should fire per `notify_on_discovery` setting.

## Child DOX Index
- No further child AGENTS.md files at this time.
