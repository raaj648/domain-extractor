# Cookie Extractor (Manual Login → Export Cookies)

This folder contains a **separate** testing utility. It does **not** modify the main project code.

## What it does
- Opens `https://member.expireddomains.net/`
- You manually log in in the browser window
- Script exports cookies from the authenticated session
- Writes them to a local JSON file you can inspect/copy

## Prerequisites
- Python 3.10+
- Install dependencies:
  
```bash
  pip install playwright
  playwright install chromium
  ```

## Run
```bash
python manual_cookie_export.py --output cookies.json --show-values false
```

### Usage notes
- Keep the browser window open until the script finishes exporting.
- Cookies are exported only for `member.expireddomains.net`.

## Security
- This utility does not include credentials in code.
