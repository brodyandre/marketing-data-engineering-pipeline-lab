-- Recreate tables to keep DDL aligned with code evolution.
DROP TABLE IF EXISTS analytics.fact_marketing_performance;
DROP TABLE IF EXISTS analytics.dim_customer;
DROP TABLE IF EXISTS analytics.dim_campaign;
DROP TABLE IF EXISTS analytics.dim_device;
DROP TABLE IF EXISTS analytics.dim_date;

-- Date dimension:
-- date_id follows YYYYMMDD format for easy joins and partitioning.
CREATE TABLE IF NOT EXISTS analytics.dim_date (
    date_id INTEGER PRIMARY KEY,
    full_date DATE NOT NULL UNIQUE,
    year SMALLINT NOT NULL,
    month SMALLINT NOT NULL,
    day SMALLINT NOT NULL,
    month_name VARCHAR(20) NOT NULL
);

-- Campaign dimension with marketing acquisition attributes.
CREATE TABLE IF NOT EXISTS analytics.dim_campaign (
    campaign_id VARCHAR(120) PRIMARY KEY,
    campaign_name VARCHAR(255) NOT NULL,
    source VARCHAR(80) NOT NULL,
    medium VARCHAR(80) NOT NULL
);

-- Customer dimension used to segment marketing performance.
CREATE TABLE IF NOT EXISTS analytics.dim_customer (
    customer_id VARCHAR(120) PRIMARY KEY,
    user_pseudo_id VARCHAR(120) NOT NULL UNIQUE,
    customer_segment VARCHAR(80) NOT NULL,
    city VARCHAR(120) NOT NULL,
    state VARCHAR(40) NOT NULL
);

-- Device dimension used for channel/device performance analysis.
CREATE TABLE IF NOT EXISTS analytics.dim_device (
    device_id VARCHAR(120) PRIMARY KEY,
    device_category VARCHAR(80) NOT NULL UNIQUE
);

-- Fact table at grain: date_id x campaign_id x customer_id x device_id.
CREATE TABLE IF NOT EXISTS analytics.fact_marketing_performance (
    date_id INTEGER NOT NULL REFERENCES analytics.dim_date(date_id),
    campaign_id VARCHAR(120) NOT NULL REFERENCES analytics.dim_campaign(campaign_id),
    customer_id VARCHAR(120) NOT NULL REFERENCES analytics.dim_customer(customer_id),
    device_id VARCHAR(120) NOT NULL REFERENCES analytics.dim_device(device_id),
    sessions INTEGER NOT NULL DEFAULT 0,
    events INTEGER NOT NULL DEFAULT 0,
    conversions INTEGER NOT NULL DEFAULT 0,
    impressions INTEGER NOT NULL DEFAULT 0,
    clicks INTEGER NOT NULL DEFAULT 0,
    cost NUMERIC(14, 2) NOT NULL DEFAULT 0,
    revenue NUMERIC(14, 2) NOT NULL DEFAULT 0,
    PRIMARY KEY (date_id, campaign_id, customer_id, device_id)
);

CREATE INDEX IF NOT EXISTS idx_fact_marketing_campaign
    ON analytics.fact_marketing_performance (campaign_id);

CREATE INDEX IF NOT EXISTS idx_fact_marketing_customer
    ON analytics.fact_marketing_performance (customer_id);

CREATE INDEX IF NOT EXISTS idx_fact_marketing_device
    ON analytics.fact_marketing_performance (device_id);
