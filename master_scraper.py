
import json, time, re, os
from bs4 import BeautifulSoup

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException
except ImportError:
    print("Run: pip install selenium"); exit(1)

try:
    from webdriver_manager.chrome import ChromeDriverManager
    USE_WDM = True
except ImportError:
    USE_WDM = False

# ── All Elections ─────────────────────────────────────────────────────────────

ELECTIONS = [
    {"label": "Lok Sabha 2024",         "type": "MP",  "slug": "LokSabha2024"},
    {"label": "Andhra Pradesh 2024",    "type": "MLA", "slug": "AndhraPradesh2024"},
    {"label": "Arunachal Pradesh 2024", "type": "MLA", "slug": "ArunachalPradesh2024"},
    {"label": "Assam 2021",             "type": "MLA", "slug": "assam2021"},
    {"label": "Bihar 2025",             "type": "MLA", "slug": "Bihar2025"},
    {"label": "Chhattisgarh 2023",      "type": "MLA", "slug": "Chhattisgarh2023"},
    {"label": "Delhi 2025",             "type": "MLA", "slug": "Delhi2025"},
    {"label": "Goa 2022",               "type": "MLA", "slug": "goa2022"},
    {"label": "Gujarat 2022",           "type": "MLA", "slug": "gujarat2022"},
    {"label": "Haryana 2024",           "type": "MLA", "slug": "haryana2024"},
    {"label": "Himachal Pradesh 2022",  "type": "MLA", "slug": "HimachalPradesh2022"},
    {"label": "Jammu & Kashmir 2024",   "type": "MLA", "slug": "jammukashmir2024"},
    {"label": "Jharkhand 2024",         "type": "MLA", "slug": "Jharkhand2024"},
    {"label": "Karnataka 2023",         "type": "MLA", "slug": "karnataka2023"},
    {"label": "Kerala 2021",            "type": "MLA", "slug": "kerala2021"},
    {"label": "Madhya Pradesh 2023",    "type": "MLA", "slug": "madhyapradesh2023"},
    {"label": "Maharashtra 2024",       "type": "MLA", "slug": "maharashtra2024"},
    {"label": "Manipur 2022",           "type": "MLA", "slug": "manipur2022"},
    {"label": "Meghalaya 2023",         "type": "MLA", "slug": "meghalaya2023"},
    {"label": "Mizoram 2023",           "type": "MLA", "slug": "mizoram2023"},
    {"label": "Nagaland 2023",          "type": "MLA", "slug": "nagaland2023"},
    {"label": "Odisha 2024",            "type": "MLA", "slug": "odisha2024"},
    {"label": "Puducherry 2021",        "type": "MLA", "slug": "puducherry2021"},
    {"label": "Punjab 2022",            "type": "MLA", "slug": "punjab2022"},
    {"label": "Rajasthan 2023",         "type": "MLA", "slug": "rajasthan2023"},
    {"label": "Sikkim 2024",            "type": "MLA", "slug": "sikkim2024"},
    {"label": "Tamil Nadu 2021",        "type": "MLA", "slug": "tamilnadu2021"},
    {"label": "Telangana 2023",         "type": "MLA", "slug": "telangana2023"},
    {"label": "Tripura 2023",           "type": "MLA", "slug": "tripura2023"},
    {"label": "Uttar Pradesh 2022",     "type": "MLA", "slug": "uttarpradesh2022"},
    {"label": "Uttarakhand 2022",       "type": "MLA", "slug": "uttarakhand2022"},
    {"label": "West Bengal 2021",       "type": "MLA", "slug": "westbengal2021"},
]

PROGRESS_FILE = "scrape_progress.json"
OUTPUT_FILE   = "all_india_data.json"

# ── Browser ───────────────────────────────────────────────────────────────────

def create_driver():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--log-level=3")
    opts.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120")
    if USE_WDM:
        return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
    return webdriver.Chrome(options=opts)

def clean(t):
    return re.sub(r'\s+', ' ', t or '').strip()

def fetch(driver, url):
    driver.get(url)
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "table"))
        )
    except TimeoutException:
        pass
    time.sleep(2)
    return BeautifulSoup(driver.page_source, "html.parser")

def best_table(soup):
    tables = soup.find_all("table")
    return max(tables, key=lambda t: len(t.find_all("tr"))) if tables else None

def max_page_num(soup):
    nums = [int(m) for a in soup.find_all("a", href=True)
            for m in re.findall(r'page=(\d+)', a.get("href", ""))]
    return max(nums) if nums else 1

# ── Scrape one paginated URL ──────────────────────────────────────────────────

def scrape_url(driver, url_pattern, label, base_url, election_type, election_label, has_case_col=True):
    """
    Scrape all pages of a URL.
    has_case_col: True if the page has a criminal cases column (crime list)
                  False if it's a plain winners list (no case count column)
    Returns list of candidate dicts.
    """
    all_rows = []
    page = 1

    while True:
        url = url_pattern.format(page)
        if page == 1:
            print(f"      Fetching page 1...", end=" ")
        else:
            print(f"      Page {page}...", end=" ")

        soup = fetch(driver, url)
        table = best_table(soup)

        if not table or len(table.find_all("tr")) < 3:
            if page == 1:
                print("no table!")
            else:
                print("empty, stopping.")
            break

        if page == 1:
            # Show columns
            header = table.find("tr")
            if header:
                cols = [clean(c.get_text()) for c in header.find_all(["th","td"])]
                print(f"cols={cols[:6]}")
            total_pages = max_page_num(soup)
            print(f"      Total pages: {total_pages}")
        
        rows = table.find_all("tr")[1:]
        parsed = []

        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 3:
                continue
            try:
                col_texts = [clean(td.get_text()) for td in cols]

                name, href = "", ""
                for td in cols:
                    lt = td.find("a")
                    if lt and clean(lt.get_text()):
                        name = clean(lt.get_text())
                        href = lt.get("href", "")
                        break

                if not name or name.lower() in ("candidate","name","winner","s.no","#","sr","no",""):
                    continue

                candidate_url = (base_url + "/" + href.lstrip("/")
                                 if href and not href.startswith("http") else href)

                # Columns: S.No | Candidate | Constituency | Party | Criminal Cases | ...
                constituency = col_texts[2] if len(col_texts) > 2 else ""
                party        = col_texts[3] if len(col_texts) > 3 else ""

                if has_case_col:
                    cases_str = col_texts[4] if len(col_texts) > 4 else "0"
                    try:
                        case_count = int(re.sub(r'[^\d]', '', cases_str) or '0')
                    except:
                        case_count = 0
                else:
                    cases_str  = "0"
                    case_count = 0

                parsed.append({
                    "name": name,
                    "url": candidate_url,
                    "type": election_type,
                    "state": election_label,
                    "constituency": constituency,
                    "party": party,
                    "case_count": case_count,
                    "total_cases_declared": cases_str,
                })

            except Exception:
                continue

        print(f"      → {len(parsed)} rows on page {page}")
        if not parsed:
            break

        all_rows.extend(parsed)

        total_pages = max_page_num(soup)
        if page >= total_pages:
            break
        page += 1
        time.sleep(0.8)

    return all_rows

# ── Scrape one election (both lists, merge) ───────────────────────────────────

def scrape_election(driver, election):
    slug    = election["slug"]
    base    = f"https://myneta.info/{slug}"
    etype   = election["type"]
    elabel  = election["label"]

    # ── LIST 1: Winners WITH criminal cases (has case counts) ──
    print(f"\n    📋 LIST 1 — Winners with criminal cases:")
    crime_rows = []
    for crime_url in [
        f"{base}/index.php?action=summary&subAction=winner_analyzed&sort=candidate&page={{}}",
        f"{base}/index.php?action=summary&subAction=winner_crime&sort=candidate&page={{}}",
    ]:
        rows = scrape_url(driver, crime_url, "crime", base, etype, elabel, has_case_col=True)
        if rows:
            crime_rows = rows
            break

    # Build lookup from crime list: name → case_count
    crime_lookup = {r["name"].lower().strip(): r for r in crime_rows}
    print(f"      ✅ {len(crime_rows)} winners with criminal cases")

    # ── LIST 2: ALL winners (including clean, no case count column) ──
    print(f"\n    📋 LIST 2 — All winners (including clean record):")
    all_winner_rows = []
    for all_url in [
        f"{base}/index.php?action=summary&subAction=winner_analyzed&sort=candidate&order=asc&page={{}}",
        f"{base}/index.php?action=show_winners&sort=criminal&page={{}}",
        f"{base}/index.php?action=show_winners&sort=default&page={{}}",
    ]:
        rows = scrape_url(driver, all_url, "all", base, etype, elabel, has_case_col=True)
        if rows:
            all_winner_rows = rows
            break

    print(f"      ✅ {len(all_winner_rows)} total winners found")

    # ── MERGE ──
    # Start with all winners (clean + with cases)
    # For each winner, use case count from crime_lookup if available
    seen = set()
    merged = []

    for w in all_winner_rows:
        key = w["name"].lower().strip()
        if key in seen:
            continue
        seen.add(key)

        if key in crime_lookup:
            # Use verified case count from crime list
            w["case_count"] = crime_lookup[key]["case_count"]
            w["total_cases_declared"] = crime_lookup[key]["total_cases_declared"]
            if crime_lookup[key].get("url") and "candidate.php" in crime_lookup[key].get("url",""):
                w["url"] = crime_lookup[key]["url"]

        merged.append(w)

    # Add anyone from crime list not caught by all_winner list (edge case)
    for key, r in crime_lookup.items():
        if key not in seen:
            seen.add(key)
            merged.append(r)

    # If all_winner_rows was empty, fall back to crime list only
    if not merged:
        merged = crime_rows

    with_cases  = sum(1 for c in merged if c["case_count"] > 0)
    clean_count = sum(1 for c in merged if c["case_count"] == 0)
    print(f"\n    ✅ MERGED: {len(merged)} total  |  {with_cases} with cases  |  {clean_count} clean")
    return merged

# ── Progress & Save ───────────────────────────────────────────────────────────

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"done": [], "data": []}

def save_progress(progress):
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False)

def print_summary(data):
    total      = len(data)
    with_cases = sum(1 for d in data if d.get("case_count", 0) > 0)
    clean      = sum(1 for d in data if d.get("case_count", 0) == 0)
    mps        = sum(1 for d in data if d["type"] == "MP")
    mlas       = sum(1 for d in data if d["type"] == "MLA")
    top10      = sorted(data, key=lambda x: x.get("case_count", 0), reverse=True)[:10]
    states     = {}
    for d in data:
        s = d.get("state","?")
        states[s] = states.get(s,0) + 1

    print("\n" + "="*60)
    print("📊 FINAL SUMMARY")
    print("="*60)
    print(f"  Total records    : {total}")
    print(f"  Lok Sabha MPs    : {mps}")
    print(f"  State MLAs       : {mlas}")
    if total:
        print(f"  With cases       : {with_cases} ({round(with_cases/total*100)}%)")
    print(f"  Clean record     : {clean}")
    print(f"\n  Per state:")
    for s, c in sorted(states.items()):
        print(f"    {s:35s}: {c}")
    print(f"\n  Top 10 by cases:")
    for d in top10:
        print(f"    {d['name']:40s} {d.get('case_count',0):>4}  ({d.get('party','')} | {d.get('state','')})")
    print("="*60)

# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("="*60)
    print("  PoliCrime — Master Scraper (All Winners + All States)")
    print("="*60)
    print(f"\n  Elections   : {len(ELECTIONS)}")
    print(f"  Output      : {OUTPUT_FILE}")
    print(f"  Auto-saves  : {PROGRESS_FILE}")
    print(f"  Est. time   : 60-90 minutes")
    print(f"\n  Scrapes BOTH:")
    print(f"    Winners WITH criminal cases (with case counts)")
    print(f"    Winners WITHOUT criminal cases (clean record = 0)\n")

    try:
        print(" Launching Chrome...")
        driver = create_driver()
        print(" Chrome ready!\n")
    except Exception as e:
        print(f" Chrome failed: {e}"); exit(1)

    progress = load_progress()
    done_labels = set(progress["done"])
    all_data = progress["data"]

    if done_labels:
        print(f"  Resuming — {len(done_labels)} states already done\n")

    try:
        for i, election in enumerate(ELECTIONS):
            label = election["label"]
            if label in done_labels:
                print(f"  [{i+1}/{len(ELECTIONS)}]   Skipping {label}")
                continue

            print(f"\n  [{i+1}/{len(ELECTIONS)}]   {label}")
            print(f"  {'─'*50}")

            result = scrape_election(driver, election)
            all_data.extend(result)

            progress["done"].append(label)
            progress["data"] = all_data
            save_progress(progress)

            total_so_far = len(all_data)
            print(f"     Saved progress — {total_so_far} total records so far")

    except KeyboardInterrupt:
        print("\n\n  Interrupted! Re-run to continue from where you left off.")
    finally:
        driver.quit()
        print("\n Browser closed.")

    if all_data:
        print_summary(all_data)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
        print(f"\n Saved → {OUTPUT_FILE}")
        if os.path.exists(PROGRESS_FILE):
            os.remove(PROGRESS_FILE)
    else:
        print("\n No data collected.")
