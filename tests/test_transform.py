from __future__ import annotations

import pandas as pd

from src.transform import transform_data


def _build_extracted_data() -> dict[str, pd.DataFrame]:
    ga4_events = pd.DataFrame(
        [
            {
                "event_id": "e1",
                "event_date": "2026-02-01",
                "user_pseudo_id": "u1",
                "session_id": "s1",
                "event_name": "purchase",
                "source": "google",
                "medium": "cpc",
                "campaign": "brand_search",
                "device_category": "mobile",
                "country": "BR",
                "page_location": "/checkout",
                "revenue": 120.0,
            },
            {
                "event_id": "e2",
                "event_date": "2026-02-01",
                "user_pseudo_id": "u1",
                "session_id": "s1",
                "event_name": "page_view",
                "source": "google",
                "medium": "cpc",
                "campaign": "brand_search",
                "device_category": "mobile",
                "country": "BR",
                "page_location": "/home",
                "revenue": 0.0,
            },
            {
                "event_id": "e3",
                "event_date": "2026-02-01",
                "user_pseudo_id": "u2",
                "session_id": "s2",
                "event_name": "purchase",
                "source": "direct",
                "medium": "none",
                "campaign": None,
                "device_category": "desktop",
                "country": "BR",
                "page_location": "/checkout",
                "revenue": None,
            },
        ]
    )

    google_ads_campaigns = pd.DataFrame(
        [
            {
                "campaign_id": "camp_001",
                "campaign_name": "brand_search",
                "date": "2026-02-01",
                "impressions": 1000,
                "clicks": 100,
                "cost": 200.0,
                "conversions": 3,
            }
        ]
    )

    customers = pd.DataFrame(
        [
            {
                "customer_id": "cust_001",
                "user_pseudo_id": "u1",
                "first_seen_date": "2026-01-15",
                "customer_segment": "vip",
                "city": "Sao Paulo",
                "state": "SP",
            },
            {
                "customer_id": "cust_002",
                "user_pseudo_id": "u2",
                "first_seen_date": "2026-01-20",
                "customer_segment": "new",
                "city": "Rio de Janeiro",
                "state": "RJ",
            }
        ]
    )

    return {
        "ga4_events": ga4_events,
        "google_ads_campaigns": google_ads_campaigns,
        "customers": customers,
    }


def test_transform_data_returns_expected_tables() -> None:
    datasets = transform_data(_build_extracted_data())

    assert set(datasets.keys()) == {
        "dim_date",
        "dim_campaign",
        "dim_customer",
        "dim_device",
        "fact_marketing_performance",
    }


def test_dim_date_has_records() -> None:
    datasets = transform_data(_build_extracted_data())
    dim_date = datasets["dim_date"]
    assert not dim_date.empty
    assert len(dim_date) >= 1


def test_fact_has_aggregated_metrics() -> None:
    datasets = transform_data(_build_extracted_data())
    fact = datasets["fact_marketing_performance"]

    customer_row = fact[
        (fact["campaign_id"] == "camp_001")
        & (fact["customer_id"] == "cust_001")
        & (fact["device_id"] == "dev_mobile")
    ]
    assert len(customer_row) == 1
    assert int(customer_row.iloc[0]["sessions"]) == 1
    assert int(customer_row.iloc[0]["events"]) == 2
    assert int(customer_row.iloc[0]["conversions"]) == 1
    assert float(customer_row.iloc[0]["revenue"]) == 120.0

    ads_row = fact[
        (fact["campaign_id"] == "camp_001")
        & (fact["customer_id"] == "unknown")
        & (fact["device_id"] == "unknown")
    ]
    assert len(ads_row) == 1
    assert int(ads_row.iloc[0]["impressions"]) == 1000
    assert int(ads_row.iloc[0]["clicks"]) == 100
    assert float(ads_row.iloc[0]["cost"]) == 200.0


def test_revenue_null_is_treated_as_zero() -> None:
    datasets = transform_data(_build_extracted_data())
    fact = datasets["fact_marketing_performance"]
    unknown_campaign_customer = fact[
        (fact["campaign_id"] == "unknown")
        & (fact["customer_id"] == "cust_002")
        & (fact["device_id"] == "dev_desktop")
    ]
    assert len(unknown_campaign_customer) == 1
    assert float(unknown_campaign_customer.iloc[0]["revenue"]) == 0.0


def test_missing_campaign_becomes_unknown() -> None:
    datasets = transform_data(_build_extracted_data())
    dim_date = datasets["dim_date"]
    dim_campaign = datasets["dim_campaign"]
    dim_device = datasets["dim_device"]
    fact = datasets["fact_marketing_performance"]

    assert not dim_date.empty
    assert "unknown" in set(dim_campaign["campaign_id"])
    assert "camp_001" in set(dim_campaign["campaign_id"])
    assert "dev_mobile" in set(dim_device["device_id"])
    assert ((fact["campaign_id"] == "unknown") & (fact["customer_id"] == "cust_002")).any()
