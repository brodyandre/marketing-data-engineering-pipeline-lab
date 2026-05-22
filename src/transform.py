from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from src.config import ensure_directories, get_settings
from src.extract import extract_data


CONVERSION_EVENTS = {"purchase", "generate_lead"}
UNKNOWN_VALUE = "unknown"


def _standardize_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    normalized_columns = [
        re.sub(r"[^a-z0-9]+", "_", column.strip().lower()).strip("_")
        for column in dataframe.columns
    ]
    dataframe = dataframe.copy()
    dataframe.columns = normalized_columns
    return dataframe


def _validate_columns(dataframe: pd.DataFrame, required: set[str], dataset_name: str) -> None:
    missing = sorted(required - set(dataframe.columns))
    if missing:
        raise ValueError(
            f"Dataset '{dataset_name}' is missing required columns: {', '.join(missing)}"
        )


def _clean_text(series: pd.Series, default: str = UNKNOWN_VALUE) -> pd.Series:
    return (
        series.astype("string")
        .fillna(default)
        .str.strip()
        .replace("", default)
        .str.lower()
    )


def _to_numeric(series: pd.Series, default: float = 0.0) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(default)


def _safe_campaign_id(campaign_name: str) -> str:
    if campaign_name == UNKNOWN_VALUE:
        return UNKNOWN_VALUE
    slug = re.sub(r"[^a-z0-9]+", "_", campaign_name).strip("_")
    return f"evt_{slug}" if slug else UNKNOWN_VALUE


def _prepare_ga4_events(
    ga4_events: pd.DataFrame,
    campaign_lookup: dict[str, str],
) -> pd.DataFrame:
    required = {
        "event_id",
        "event_date",
        "user_pseudo_id",
        "session_id",
        "event_name",
        "source",
        "medium",
        "campaign",
        "device_category",
        "revenue",
    }
    _validate_columns(ga4_events, required, "ga4_events")

    df = _standardize_columns(ga4_events)
    df["event_date"] = pd.to_datetime(df["event_date"], errors="coerce")
    df["user_pseudo_id"] = _clean_text(df["user_pseudo_id"])
    df["session_id"] = _clean_text(df["session_id"])
    df["event_name"] = _clean_text(df["event_name"])
    df["source"] = _clean_text(df["source"])
    df["medium"] = _clean_text(df["medium"])
    df["campaign"] = _clean_text(df["campaign"])
    df["device_category"] = _clean_text(df["device_category"])
    df["revenue"] = _to_numeric(df["revenue"], default=0.0)

    df["campaign_id"] = df["campaign"].map(campaign_lookup)
    df["campaign_id"] = df["campaign_id"].fillna(df["campaign"].map(_safe_campaign_id))
    df["campaign_name"] = df["campaign"]
    df["is_conversion"] = df["event_name"].isin(CONVERSION_EVENTS).astype(int)
    return df


def _prepare_ads(google_ads_campaigns: pd.DataFrame) -> pd.DataFrame:
    required = {
        "campaign_id",
        "campaign_name",
        "date",
        "impressions",
        "clicks",
        "cost",
        "conversions",
    }
    _validate_columns(google_ads_campaigns, required, "google_ads_campaigns")

    df = _standardize_columns(google_ads_campaigns)
    df["campaign_id"] = _clean_text(df["campaign_id"])
    df["campaign_name"] = _clean_text(df["campaign_name"])
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["impressions"] = _to_numeric(df["impressions"], default=0).astype(int)
    df["clicks"] = _to_numeric(df["clicks"], default=0).astype(int)
    df["cost"] = _to_numeric(df["cost"], default=0.0)
    df["conversions"] = _to_numeric(df["conversions"], default=0).astype(int)
    return df


def _prepare_customers(customers: pd.DataFrame) -> pd.DataFrame:
    required = {
        "customer_id",
        "user_pseudo_id",
        "customer_segment",
        "city",
        "state",
    }
    _validate_columns(customers, required, "customers")

    df = _standardize_columns(customers)
    df["customer_id"] = _clean_text(df["customer_id"])
    df["user_pseudo_id"] = _clean_text(df["user_pseudo_id"])
    df["customer_segment"] = _clean_text(df["customer_segment"])
    df["city"] = _clean_text(df["city"])
    df["state"] = _clean_text(df["state"])

    dim_customer = df[
        ["customer_id", "user_pseudo_id", "customer_segment", "city", "state"]
    ].drop_duplicates()

    if UNKNOWN_VALUE not in set(dim_customer["customer_id"]):
        dim_customer = pd.concat(
            [
                dim_customer,
                pd.DataFrame(
                    [
                        {
                            "customer_id": UNKNOWN_VALUE,
                            "user_pseudo_id": UNKNOWN_VALUE,
                            "customer_segment": UNKNOWN_VALUE,
                            "city": UNKNOWN_VALUE,
                            "state": UNKNOWN_VALUE,
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )

    return dim_customer.sort_values("customer_id").reset_index(drop=True)


def _build_dim_date(ga4_events: pd.DataFrame, ads: pd.DataFrame) -> pd.DataFrame:
    dates = pd.concat([ga4_events["event_date"], ads["date"]], ignore_index=True).dropna()
    dim_date = pd.DataFrame({"full_date": sorted(dates.dt.normalize().unique())})
    dim_date["date_id"] = dim_date["full_date"].dt.strftime("%Y%m%d").astype(int)
    dim_date["year"] = dim_date["full_date"].dt.year.astype(int)
    dim_date["month"] = dim_date["full_date"].dt.month.astype(int)
    dim_date["day"] = dim_date["full_date"].dt.day.astype(int)
    dim_date["month_name"] = dim_date["full_date"].dt.month_name()
    return dim_date[
        ["date_id", "full_date", "year", "month", "day", "month_name"]
    ].sort_values("date_id")


def _build_dim_campaign(ga4_events: pd.DataFrame, ads: pd.DataFrame) -> pd.DataFrame:
    campaign_from_events = ga4_events[
        ["campaign_id", "campaign_name", "source", "medium"]
    ].drop_duplicates()

    campaign_from_ads = ads[["campaign_id", "campaign_name"]].drop_duplicates()
    campaign_from_ads["source"] = "google"
    campaign_from_ads["medium"] = "cpc"

    dim_campaign = pd.concat(
        [campaign_from_events, campaign_from_ads],
        ignore_index=True,
    )
    dim_campaign["campaign_id"] = _clean_text(dim_campaign["campaign_id"])
    dim_campaign["campaign_name"] = _clean_text(dim_campaign["campaign_name"])
    dim_campaign["source"] = _clean_text(dim_campaign["source"])
    dim_campaign["medium"] = _clean_text(dim_campaign["medium"])

    dim_campaign = dim_campaign.sort_values(["campaign_id", "source", "medium"])
    dim_campaign = dim_campaign.drop_duplicates(subset=["campaign_id"], keep="first")

    if UNKNOWN_VALUE not in set(dim_campaign["campaign_id"]):
        dim_campaign = pd.concat(
            [
                dim_campaign,
                pd.DataFrame(
                    [
                        {
                            "campaign_id": UNKNOWN_VALUE,
                            "campaign_name": UNKNOWN_VALUE,
                            "source": UNKNOWN_VALUE,
                            "medium": UNKNOWN_VALUE,
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )

    return dim_campaign[
        ["campaign_id", "campaign_name", "source", "medium"]
    ].sort_values("campaign_id")


def _safe_device_id(device_category: str) -> str:
    if device_category == UNKNOWN_VALUE:
        return UNKNOWN_VALUE
    slug = re.sub(r"[^a-z0-9]+", "_", device_category).strip("_")
    return f"dev_{slug}" if slug else UNKNOWN_VALUE


def _build_dim_device(ga4_events: pd.DataFrame) -> pd.DataFrame:
    dim_device = ga4_events[["device_category"]].drop_duplicates().copy()
    dim_device["device_category"] = _clean_text(dim_device["device_category"])
    dim_device["device_id"] = dim_device["device_category"].map(_safe_device_id)

    if UNKNOWN_VALUE not in set(dim_device["device_id"]):
        dim_device = pd.concat(
            [
                dim_device,
                pd.DataFrame(
                    [
                        {
                            "device_id": UNKNOWN_VALUE,
                            "device_category": UNKNOWN_VALUE,
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )

    return dim_device[["device_id", "device_category"]].drop_duplicates().sort_values(
        "device_id"
    )


def _build_fact_marketing_performance(
    ga4_events: pd.DataFrame,
    ads: pd.DataFrame,
    dim_date: pd.DataFrame,
    dim_customer: pd.DataFrame,
    dim_device: pd.DataFrame,
) -> pd.DataFrame:
    customer_lookup = dim_customer[["user_pseudo_id", "customer_id"]].drop_duplicates()
    device_lookup = dim_device[["device_category", "device_id"]].drop_duplicates()

    events_enriched = ga4_events.merge(customer_lookup, on="user_pseudo_id", how="left")
    events_enriched["customer_id"] = events_enriched["customer_id"].fillna(UNKNOWN_VALUE)
    events_enriched = events_enriched.merge(device_lookup, on="device_category", how="left")
    events_enriched["device_id"] = events_enriched["device_id"].fillna(UNKNOWN_VALUE)

    fact_events = (
        events_enriched.groupby(
            ["event_date", "campaign_id", "customer_id", "device_id"], as_index=False
        )
        .agg(
            sessions=("session_id", "nunique"),
            events=("event_id", "count"),
            conversions=("is_conversion", "sum"),
            revenue=("revenue", "sum"),
        )
        .rename(columns={"event_date": "full_date"})
    )
    fact_events["impressions"] = 0
    fact_events["clicks"] = 0
    fact_events["cost"] = 0.0

    fact_ads = (
        ads.groupby(["date", "campaign_id"], as_index=False)
        .agg(
            impressions=("impressions", "sum"),
            clicks=("clicks", "sum"),
            cost=("cost", "sum"),
            conversions=("conversions", "sum"),
        )
        .rename(columns={"date": "full_date"})
    )
    fact_ads["customer_id"] = UNKNOWN_VALUE
    fact_ads["device_id"] = UNKNOWN_VALUE
    fact_ads["sessions"] = 0
    fact_ads["events"] = 0
    fact_ads["revenue"] = 0.0

    fact = pd.concat(
        [
            fact_events[
                [
                    "full_date",
                    "campaign_id",
                    "customer_id",
                    "device_id",
                    "sessions",
                    "events",
                    "conversions",
                    "impressions",
                    "clicks",
                    "cost",
                    "revenue",
                ]
            ],
            fact_ads[
                [
                    "full_date",
                    "campaign_id",
                    "customer_id",
                    "device_id",
                    "sessions",
                    "events",
                    "conversions",
                    "impressions",
                    "clicks",
                    "cost",
                    "revenue",
                ]
            ],
        ],
        ignore_index=True,
    )

    fact = (
        fact.groupby(["full_date", "campaign_id", "customer_id", "device_id"], as_index=False)[
            [
                "sessions",
                "events",
                "conversions",
                "impressions",
                "clicks",
                "cost",
                "revenue",
            ]
        ]
        .sum()
    )

    fact = fact.merge(dim_date[["date_id", "full_date"]], on="full_date", how="left")
    fact["date_id"] = fact["date_id"].fillna(0).astype(int)

    int_columns = ["sessions", "events", "conversions", "impressions", "clicks"]
    for column in int_columns:
        fact[column] = _to_numeric(fact[column], default=0).astype(int)

    fact["cost"] = _to_numeric(fact["cost"], default=0.0).round(2)
    fact["revenue"] = _to_numeric(fact["revenue"], default=0.0).round(2)

    return fact[
        [
            "date_id",
            "campaign_id",
            "customer_id",
            "device_id",
            "sessions",
            "events",
            "conversions",
            "impressions",
            "clicks",
            "cost",
            "revenue",
        ]
    ].sort_values(["date_id", "campaign_id", "customer_id", "device_id"])


def transform_data(
    extracted_data: dict[str, pd.DataFrame] | None = None,
) -> dict[str, pd.DataFrame]:
    """
    Transform raw extracted datasets into dimensional and fact tables.
    """
    if extracted_data is None:
        extracted_data = extract_data()

    required_datasets = {"ga4_events", "google_ads_campaigns", "customers"}
    missing_datasets = sorted(required_datasets - set(extracted_data.keys()))
    if missing_datasets:
        raise ValueError(
            "Missing extracted datasets for transform: "
            + ", ".join(missing_datasets)
        )

    ads = _prepare_ads(extracted_data["google_ads_campaigns"])
    campaign_lookup = (
        ads[["campaign_name", "campaign_id"]]
        .drop_duplicates(subset=["campaign_name"])
        .set_index("campaign_name")["campaign_id"]
        .to_dict()
    )
    ga4_events = _prepare_ga4_events(extracted_data["ga4_events"], campaign_lookup)
    dim_customer = _prepare_customers(extracted_data["customers"])
    dim_date = _build_dim_date(ga4_events, ads)
    dim_campaign = _build_dim_campaign(ga4_events, ads)
    dim_device = _build_dim_device(ga4_events)
    fact_marketing_performance = _build_fact_marketing_performance(
        ga4_events=ga4_events,
        ads=ads,
        dim_date=dim_date,
        dim_customer=dim_customer,
        dim_device=dim_device,
    )

    return {
        "dim_date": dim_date.reset_index(drop=True),
        "dim_campaign": dim_campaign.reset_index(drop=True),
        "dim_customer": dim_customer.reset_index(drop=True),
        "dim_device": dim_device.reset_index(drop=True),
        "fact_marketing_performance": fact_marketing_performance.reset_index(drop=True),
    }


def transform_marketing_data(raw_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    """
    Backward-compatible entrypoint used by existing pipeline code.
    """
    if raw_dir is None:
        return transform_data(extract_data())

    ga4_events = pd.read_csv(raw_dir / "ga4_events.csv")
    google_ads_campaigns = pd.read_csv(raw_dir / "google_ads_campaigns.csv")
    customers = pd.read_csv(raw_dir / "customers.csv")
    return transform_data(
        {
            "ga4_events": ga4_events,
            "google_ads_campaigns": google_ads_campaigns,
            "customers": customers,
        }
    )


def save_transformed_data(
    datasets: dict[str, pd.DataFrame],
    processed_dir: Path | None = None,
) -> dict[str, Path]:
    settings = get_settings()
    ensure_directories(settings)

    output_dir = processed_dir or settings.processed_data_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    output_paths: dict[str, Path] = {}
    for name, dataframe in datasets.items():
        output_path = output_dir / f"{name}.csv"
        dataframe.to_csv(output_path, index=False)
        output_paths[name] = output_path
    return output_paths


def main() -> None:
    print("[transform] Starting transformation...")
    datasets = transform_data()
    output_paths = save_transformed_data(datasets)
    print("[transform] Transformation finished:")
    for name, path in output_paths.items():
        print(f"- {name}: {path}")


if __name__ == "__main__":
    main()
