from __future__ import annotations

import pandas as pd
import pytest

from src.quality import run_quality_checks


def _base_tables() -> dict[str, pd.DataFrame]:
    dim_date = pd.DataFrame(
        [
            {
                "date_id": 20260101,
                "full_date": "2026-01-01",
                "year": 2026,
                "month": 1,
                "day": 1,
                "month_name": "January",
            }
        ]
    )

    dim_campaign = pd.DataFrame(
        [
            {
                "campaign_id": "camp_001",
                "campaign_name": "brand_search",
                "source": "google",
                "medium": "cpc",
            }
        ]
    )

    dim_customer = pd.DataFrame(
        [
            {
                "customer_id": "cust_001",
                "user_pseudo_id": "u_1001",
                "customer_segment": "vip",
                "city": "sao paulo",
                "state": "sp",
            },
            {
                "customer_id": "unknown",
                "user_pseudo_id": "unknown",
                "customer_segment": "unknown",
                "city": "unknown",
                "state": "unknown",
            }
        ]
    )

    dim_device = pd.DataFrame(
        [
            {"device_id": "dev_mobile", "device_category": "mobile"},
            {"device_id": "unknown", "device_category": "unknown"},
        ]
    )

    fact = pd.DataFrame(
        [
            {
                "date_id": 20260101,
                "campaign_id": "camp_001",
                "customer_id": "cust_001",
                "device_id": "dev_mobile",
                "sessions": 10,
                "events": 15,
                "conversions": 3,
                "impressions": 1000,
                "clicks": 100,
                "cost": 200.0,
                "revenue": 600.0,
            },
            {
                "date_id": 20260101,
                "campaign_id": "camp_001",
                "customer_id": "unknown",
                "device_id": "unknown",
                "sessions": 0,
                "events": 0,
                "conversions": 0,
                "impressions": 500,
                "clicks": 25,
                "cost": 0.0,
                "revenue": 0.0,
            }
        ]
    )

    return {
        "dim_date": dim_date,
        "dim_campaign": dim_campaign,
        "dim_customer": dim_customer,
        "dim_device": dim_device,
        "fact_marketing_performance": fact,
    }


def test_quality_passes_for_valid_data() -> None:
    tables = _base_tables()
    assert run_quality_checks(tables) is True


def test_quality_fails_when_negative_metric_exists() -> None:
    tables = _base_tables()
    tables["fact_marketing_performance"].loc[0, "cost"] = -1

    with pytest.raises(ValueError, match="Critical data quality failure"):
        run_quality_checks(tables)


def test_quality_fails_when_required_column_is_missing() -> None:
    tables = _base_tables()
    tables["fact_marketing_performance"] = tables["fact_marketing_performance"].drop(
        columns=["campaign_id"]
    )

    with pytest.raises(ValueError, match="Critical data quality failure"):
        run_quality_checks(tables)
