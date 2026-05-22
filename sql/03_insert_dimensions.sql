-- Small seed set for manual SQL demonstrations.

INSERT INTO analytics.dim_date (
    date_id,
    full_date,
    year,
    month,
    day,
    month_name
)
VALUES
    (20260301, DATE '2026-03-01', 2026, 3, 1, 'March'),
    (20260302, DATE '2026-03-02', 2026, 3, 2, 'March'),
    (20260303, DATE '2026-03-03', 2026, 3, 3, 'March')
ON CONFLICT (date_id) DO NOTHING;

INSERT INTO analytics.dim_campaign (
    campaign_id,
    campaign_name,
    source,
    medium
)
VALUES
    ('camp_001', 'spring_sale', 'google', 'cpc'),
    ('camp_002', 'brand_search', 'google', 'cpc'),
    ('camp_003', 'reactivation_q1', 'email', 'newsletter'),
    ('unknown', 'unknown', 'unknown', 'unknown')
ON CONFLICT (campaign_id) DO NOTHING;

INSERT INTO analytics.dim_customer (
    customer_id,
    user_pseudo_id,
    customer_segment,
    city,
    state
)
VALUES
    ('cust_001', 'u_1001', 'vip', 'sao paulo', 'sp'),
    ('cust_002', 'u_1002', 'new', 'rio de janeiro', 'rj'),
    ('cust_003', 'u_1003', 'returning', 'curitiba', 'pr'),
    ('unknown', 'unknown', 'unknown', 'unknown', 'unknown')
ON CONFLICT (customer_id) DO NOTHING;

INSERT INTO analytics.dim_device (
    device_id,
    device_category
)
VALUES
    ('dev_desktop', 'desktop'),
    ('dev_mobile', 'mobile'),
    ('dev_tablet', 'tablet'),
    ('unknown', 'unknown')
ON CONFLICT (device_id) DO NOTHING;
