import os
import sys
import json
import concurrent.futures
from pathlib import Path
import subprocess

websites = [
    "shein.com", "temu.com", "aliexpress.com", "wayfair.com", "walmart.com", "ebay.com",
    "etsy.com", "newegg.com", "homedepot.com", "lowes.com", "cnn.com", "forbes.com",
    "foxnews.com", "usatoday.com", "dailymail.co.uk", "the-sun.com", "weather.com",
    "tripadvisor.com", "expedia.com", "kayak.com", "skyscanner.net", "booking.com",
    "indeed.com", "glassdoor.com", "linkedin.com", "ziprecruiter.com", "zillow.com",
    "realtor.com", "redfin.com", "apartments.com", "webmd.com", "healthline.com",
    "medicalnewstoday.com", "verywellhealth.com", "drugs.com", "w3schools.com",
    "tutorialspoint.com", "geeksforgeeks.org", "javatpoint.com", "craigslist.org",
    "yellowpages.com", "superpages.com", "mapquest.com", "manta.com", "britannica.com",
    "fandom.com", "quora.com", "medium.com", "substack.com", "mcdonalds.com",
    "dominos.com", "tacobell.com", "chipotle.com", "doordash.com", "paypal.com",
    "robinhood.com", "coinbase.com", "fidelity.com", "nerdwallet.com", "salesforce.com",
    "hubspot.com", "zendesk.com", "notion.so", "canva.com", "shopify.com", "wordpress.com",
    "wix.com", "squarespace.com", "weebly.com", "adrianroselli.com", "w3.org", "lanecc.edu",
    "project2025.org", "web.dev", "gohugo.io", "docs.python.org", "docs.djangoproject.com",
    "developer.mozilla.org", "github.com", "wikipedia.org", "mozilla.org", "python.org",
    "nasa.gov", "mit.edu"
]

OUT_DIR = Path("d:/MarketPlace_Agentic_AI/real_reports_out")
OUT_DIR.mkdir(parents=True, exist_ok=True)

def run_audit(site):
    print(f"Running audit for {site}...")
    # Just run the command
    cmd = [sys.executable, "harness/run_audit.py", "--site", site, "--out", str(OUT_DIR)]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return site, True
    except Exception as e:
        print(f"Failed {site}: {e}")
        return site, False

print(f"Starting audits for {len(websites)} sites...")
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    results = list(executor.map(run_audit, websites))

print("All audits complete. Gathering reports into a JSON array...")

all_reports = []
for file in OUT_DIR.glob("*_report.json"):
    try:
        with open(file, 'r', encoding='utf-8') as f:
            all_reports.append(json.load(f))
    except Exception as e:
        print(f"Failed to read {file}: {e}")

with open("d:/MarketPlace_Agentic_AI/all_real_reports.json", "w", encoding='utf-8') as f:
    json.dump(all_reports, f, indent=2)

print(f"Wrote {len(all_reports)} reports to all_real_reports.json")
