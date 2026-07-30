"""
Day 1 - Live NAV Fetch
Fetches live NAV data from mfapi.in for HDFC Top 100 and 5 key benchmark schemes,
parses the JSON response, and saves each as a raw CSV.
"""

import requests
import pandas as pd
from pathlib import Path

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://api.mfapi.in/mf/{code}"

SCHEMES = {
    "hdfc_top_100_direct": 125497,
    "sbi_bluechip": 119551,
    "icici_bluechip": 120503,
    "nippon_large_cap": 118632,
    "axis_bluechip": 119092,
    "kotak_bluechip": 120841,
}


def fetch_scheme_nav(scheme_name: str, code: int) -> pd.DataFrame | None:
    url = BASE_URL.format(code=code)
    print(f"Fetching {scheme_name} (code {code}) from {url}")
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  !! Request failed for {scheme_name}: {e}")
        return None

    payload = resp.json()
    if payload.get("status") != "SUCCESS" and "data" not in payload:
        print(f"  !! Unexpected response for {scheme_name}: {payload}")
        return None

    meta = payload.get("meta", {})
    nav_data = payload.get("data", [])

    df = pd.DataFrame(nav_data)
    df["scheme_code"] = code
    df["scheme_name"] = meta.get("scheme_name", scheme_name)
    df["fund_house"] = meta.get("fund_house", "")

    print(f"  Rows fetched: {len(df)}")
    return df


def save_nav_csv(df: pd.DataFrame, scheme_name: str):
    out_path = RAW_DIR / f"live_nav_{scheme_name}.csv"
    df.to_csv(out_path, index=False)
    print(f"  Saved -> {out_path}")


if __name__ == "__main__":
    for scheme_name, code in SCHEMES.items():
        df = fetch_scheme_nav(scheme_name, code)
        if df is not None:
            save_nav_csv(df, scheme_name)
        print()

    print("Live NAV fetch complete.")
