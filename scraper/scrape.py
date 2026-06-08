import os
import re
import sys
import time
import traceback
from datetime import datetime
from bs4 import BeautifulSoup
from curl_cffi import requests as cffi_requests
import requests as normal_requests
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Missing Supabase configuration environment variables.")
    sys.exit(1)

db: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
job_id = None
job_logs = []

def log_message(msg):
    timestamp = datetime.utcnow().isoformat()
    formatted = f"[{timestamp}] {msg}"
    print(formatted)
    job_logs.append(formatted)

def notify_telegram(token, chat_id, text):
    if not token or not chat_id:
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        normal_requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}, timeout=10)
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")

def main():
    global job_id
    # Initialize job entry
    res = db.table("scrape_jobs").insert({"status": "running"}).execute()
    job_id = res.data[0]["id"]
    log_message(f"Scraper job initialized with ID: {job_id}")

    try:
        # Load settings
        settings_res = db.table("settings").select("*").execute()
        settings = {item["key"]: item["value"] for item in settings_res.data}
        
        tg_conf = settings.get("telegram", {})
        cookies_conf = settings.get("cookies", {})
        
        bot_token = tg_conf.get("bot_token")
        chat_id = tg_conf.get("chat_id")
        notify_discovery = tg_conf.get("notify_on_discovery", True)
        
        session_id = cookies_conf.get("sessionid")
        ed_session = cookies_conf.get("expireddomains_session")
        
        if not session_id or not ed_session:
            raise Exception("ExpiredDomains session cookies are missing in Supabase settings. Please update them in settings.")

        # Load active targets
        targets_res = db.table("targets").select("*").eq("is_active", True).execute()
        active_targets = targets_res.data
        
        if not active_targets:
            log_message("No active targets found in database. Exiting.")
            db.table("scrape_jobs").update({
                "status": "success",
                "logs": "\n".join(job_logs),
                "ended_at": datetime.utcnow().isoformat()
            }).eq("id", job_id).execute()
            return

        total_found = 0
        total_inserted = 0
        date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")

        # Run scraper for each target
        for target in active_targets:
            log_message(f"Scraping target: {target['name']} - URL: {target['url']}")
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Connection": "keep-alive"
            }
            
            cookies = {
                "sessionid": session_id,
                "expireddomains_session": ed_session
            }

            # Use curl_cffi to match browser TLS fingerprint
            response = cffi_requests.get(
                target["url"],
                headers=headers,
                cookies=cookies,
                impersonate="chrome120",
                timeout=30
            )

            if response.status_code != 200:
                raise Exception(f"HTTP error {response.status_code} requesting target '{target['name']}'.")
            
            if "Login / Sign Up" in response.text or "You must be logged in" in response.text:
                raise Exception("Cookies session has expired on ExpiredDomains.net. Please refresh cookies on Settings dashboard.")

            soup = BeautifulSoup(response.text, "html.parser")
            table = soup.find("table", class_="base_table")
            if not table:
                log_message(f"No table matching 'base_table' found for '{target['name']}'. Check URL configuration or cookie permissions.")
                continue

            tbody = table.find("tbody")
            if not tbody:
                log_message("No table body found in table.")
                continue

            rows = tbody.find_all("tr")
            log_message(f"Scraped {len(rows)} rows for target '{target['name']}'.")
            
            target_found = 0
            target_inserted = 0

            for row in rows:
                cols = row.find_all("td")
                if not cols or len(cols) < 2:
                    continue
                
                # Extract domain link
                domain_a = cols[0].find("a")
                if not domain_a:
                    continue
                domain_name = domain_a.text.strip().lower()
                
                if not domain_name or "." not in domain_name:
                    continue

                tld = domain_name.split(".")[-1]

                # Parse metrics and delete dates safely
                delete_date_str = None
                backlinks = 0
                age = 0

                # Search row values for YYYY-MM-DD deletion date
                for col in cols:
                    text = col.text.strip()
                    if date_pattern.match(text):
                        delete_date_str = text
                        break

                # Attempt to retrieve common metrics (backlinks) by checking title tooltips
                # E.g., looking at columns with a links or titles containing SEO abbreviations
                for col in cols:
                    a_tag = col.find("a")
                    if a_tag and "backlink" in a_tag.get("title", "").lower():
                        try:
                            backlinks = int(re.sub(r"[^\d]", "", a_tag.text))
                        except ValueError:
                            pass

                metrics = {
                    "scraped_at": datetime.utcnow().isoformat(),
                    "backlinks": backlinks,
                    "age": age
                }

                # Check if domain is already tracked
                domain_check = db.table("tracked_domains").select("domain,status").eq("domain", domain_name).execute()

                domain_data = {
                    "domain": domain_name,
                    "tld": tld,
                    "source_target_id": target["id"],
                    "metrics": metrics
                }

                if delete_date_str:
                    domain_data["delete_date"] = delete_date_str

                if not domain_check.data:
                    # Insert new pending domain
                    domain_data["status"] = "pending_delete"
                    db.table("tracked_domains").insert(domain_data).execute()
                    target_inserted += 1
                    total_inserted += 1

                    if notify_discovery:
                        notify_telegram(
                            bot_token, chat_id,
                            f"🔍 *New Domain Found!*\n"
                            f"🌐 *Domain:* `{domain_name}`\n"
                            f"📅 *Delete Date:* {delete_date_str or 'Unknown'}\n"
                            f"🎯 *Source Target:* {target['name']}"
                        )
                target_found += 1
                total_found += 1

            # Update target last scraped timestamp
            db.table("targets").update({"last_scraped_at": datetime.utcnow().isoformat()}).eq("id", target["id"]).execute()
            log_message(f"Completed target '{target['name']}': found {target_found}, inserted {target_inserted} new.")
            time.sleep(3) # Polite crawl delay

        # Finalize job entry as success
        db.table("scrape_jobs").update({
            "status": "success",
            "domains_found": total_found,
            "domains_inserted": total_inserted,
            "logs": "\n".join(job_logs),
            "ended_at": datetime.utcnow().isoformat()
        }).eq("id", job_id).execute()
        log_message("Scraper finished successfully.")

    except Exception as e:
        error_msg = str(e)
        stack = traceback.format_exc()
        log_message(f"Fatal error: {error_msg}\n{stack}")
        
        try:
            # Load settings for Telegram alert
            settings_res = db.table("settings").select("*").execute()
            settings = {item["key"]: item["value"] for item in settings_res.data}
            tg_conf = settings.get("telegram", {})
            if tg_conf.get("notify_on_errors", True):
                notify_telegram(
                    tg_conf.get("bot_token"),
                    tg_conf.get("chat_id"),
                    f"⚠️ *Scraper Job Failed!*\n*Error:* `{error_msg[:200]}`"
                )
        except Exception:
            pass

        if job_id:
            db.table("scrape_jobs").update({
                "status": "failed",
                "error_message": error_msg,
                "logs": "\n".join(job_logs),
                "ended_at": datetime.utcnow().isoformat()
            }).eq("id", job_id).execute()
        sys.exit(1)

if __name__ == "__main__":
    main()
