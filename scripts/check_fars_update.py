"""
Check whether NHTSA has published FARS data beyond the year currently in the database.

Usage:
    python scripts/check_fars_update.py [--from-year YEAR]

Probes static.nhtsa.gov with HEAD requests — no data is downloaded.
"""

import argparse
import sys
import requests

BASE_URL = "https://static.nhtsa.gov/nhtsa/downloads/FARS"
DB_MAX_YEAR = 2023  # update this when new data is ingested


def year_available(year: int, timeout: int = 10) -> bool:
    url = f"{BASE_URL}/{year}/National/FARS{year}NationalCSV.zip"
    try:
        r = requests.head(url, timeout=timeout, allow_redirects=True)
        return r.status_code == 200
    except requests.RequestException:
        return False


def find_latest_available(from_year: int, max_lookahead: int = 5) -> int | None:
    latest = None
    for year in range(from_year, from_year + max_lookahead):
        print(f"  Checking {year}...", end=" ", flush=True)
        if year_available(year):
            print("available")
            latest = year
        else:
            print("not found")
            break
    return latest


def main():
    parser = argparse.ArgumentParser(description="Check NHTSA FARS data availability")
    parser.add_argument("--from-year", type=int, default=DB_MAX_YEAR + 1,
                        help=f"First year to probe (default: {DB_MAX_YEAR + 1})")
    args = parser.parse_args()

    print(f"Database max year : {DB_MAX_YEAR}")
    print(f"Probing NHTSA from: {args.from_year}\n")

    latest = find_latest_available(args.from_year)

    print()
    if latest is None:
        print(f"No new data found. Database is current through {DB_MAX_YEAR}.")
        sys.exit(0)
    else:
        print(f"New data available: {latest} (database has through {DB_MAX_YEAR})")
        print(f"Download page: https://www.nhtsa.gov/research-data/fatality-analysis-reporting-system-fars")
        sys.exit(1)  # non-zero exit so CI/cron can detect the update


if __name__ == "__main__":
    main()
