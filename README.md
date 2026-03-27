# PoliCrime - Election Data Scraper

A Python-based master scraper designed to extract data of elected candidates (Lok Sabha MPs and State MLAs) and their declared criminal cases from [myneta.info](https://myneta.info/).

## Overview

The scraper iterates over multiple election datasets, collecting both:
- Winners **with** declared criminal cases.
- Winners **without** criminal cases (clean record).

It automatically merges the data, tracks progress to allow pausing and resuming, and ultimately outputs a structured JSON file (`all_india_data.json`) containing all collected records.

## Features

- **Comprehensive Coverage:** Scrapes data for Lok Sabha 2024 and numerous recent State Assembly elections.
- **Resilient Execution:** Auto-saves progress incrementally in `scrape_progress.json`. If interrupted, simply re-run the script to resume from the last completed state.
- **Headless Browsing:** Uses Selenium with headless Chrome for reliable rendering of dynamic tables.
- **Detailed Data Extraction:** Extracts Candidate Name, URL profile, Election Type (MP/MLA), State, Constituency, Party, and Criminal Case Count.
- **Summary Reports:** Automatically generates console summaries showing total records, clean vs. case-laden breakdowns, state-wise counts, and top 10 candidates by criminal cases.

## Prerequisites

- Python 3.x
- Google Chrome browser installed

Install the required Python packages:

```bash
pip install selenium beautifulsoup4 webdriver-manager
```

## Usage

Run the master scraper script:

```bash
python master_scraper.py
```

- **Estimated Time:** 60-90 minutes for a complete run across all configured states.
- **Output:** The final dataset is saved as `all_india_data.json`.
- **Progress Tracking:** A temporary `scrape_progress.json` file is created during the run and removed upon successful completion.

## Project Files

- `master_scraper.py`: The core scraping script containing the election configurations and extraction logic.
- `all_india_data.json`: The generated dataset (JSON format) containing the extracted election records.
- `index.html`: A frontend web page to visualize or serve the extracted dataset.

## Data Structure Example

The generated `all_india_data.json` will contain a list of objects structured like this:

```json
[
  {
    "name": "Sample Candidate",
    "url": "https://myneta.info/.../candidate.php?...'",
    "type": "MLA",
    "state": "Maharashtra 2024",
    "constituency": "Sample Constituency",
    "party": "Sample Party",
    "case_count": 2,
    "total_cases_declared": "2"
  }
]
```

## Disclaimer & License

This project is for educational and public awareness purposes. Candidate data is sourced from public declarations available on [myneta.info](https://myneta.info/). Please adhere to any Terms of Service specified by the source website when using this scraper.
