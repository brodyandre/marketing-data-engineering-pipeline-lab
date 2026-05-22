from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.config import ensure_directories, get_settings


RAW_FILES = {
    "ga4_events": "ga4_events.csv",
    "google_ads_campaigns": "google_ads_campaigns.csv",
    "customers": "customers.csv",
}


def _required_paths(raw_dir: Path) -> dict[str, Path]:
    return {name: raw_dir / filename for name, filename in RAW_FILES.items()}


def _validate_required_files(paths: dict[str, Path]) -> None:
    missing = [f"{name} ({path})" for name, path in paths.items() if not path.exists()]
    if missing:
        details = "\n- ".join([""] + missing)
        raise FileNotFoundError(
            "One or more required source files are missing in data/raw:"
            f"{details}\nExpected files: {', '.join(RAW_FILES.values())}"
        )


def _read_csv(path: Path, *, parse_dates: list[str] | None = None) -> pd.DataFrame:
    return pd.read_csv(path, parse_dates=parse_dates)


def extract_data() -> dict[str, pd.DataFrame]:
    """
    Read required raw marketing files and return each dataset as a separate DataFrame.
    """
    settings = get_settings()
    ensure_directories(settings)
    raw_dir = settings.raw_data_dir

    print(f"[extract] Reading raw data from: {raw_dir}")
    paths = _required_paths(raw_dir)
    _validate_required_files(paths)

    ga4_events = _read_csv(paths["ga4_events"], parse_dates=["event_date"])
    google_ads_campaigns = _read_csv(paths["google_ads_campaigns"], parse_dates=["date"])
    customers = _read_csv(paths["customers"], parse_dates=["first_seen_date"])

    print(f"[extract] ga4_events loaded: {len(ga4_events)} rows")
    print(f"[extract] google_ads_campaigns loaded: {len(google_ads_campaigns)} rows")
    print(f"[extract] customers loaded: {len(customers)} rows")
    print("[extract] Extraction finished successfully.")

    return {
        "ga4_events": ga4_events,
        "google_ads_campaigns": google_ads_campaigns,
        "customers": customers,
    }


def extract_sources(force: bool = True) -> dict[str, Path]:
    """
    Compatibility wrapper used by existing pipeline steps.
    Validates required files and returns their paths.
    """
    del force  # Force is not needed for file-based extraction in data/raw.
    settings = get_settings()
    ensure_directories(settings)
    paths = _required_paths(settings.raw_data_dir)
    _validate_required_files(paths)
    return paths


def main() -> None:
    extract_data()


if __name__ == "__main__":
    main()
