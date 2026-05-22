-- ============================================================
-- Business Analytics Queries - Marketing Performance
-- Schema: analytics
-- ============================================================
--
-- Metric definitions used in this file:
-- CTR (Click-Through Rate) = clicks / impressions
-- CPC (Cost Per Click)     = cost / clicks
-- ROAS (Return on Ad Spend)= revenue / cost
-- Conversion Rate          = conversions / clicks
--
-- Notes:
-- - All divisions use NULLIF to avoid division-by-zero errors.
-- - ROUND(..., 6) standardizes decimal precision.
-- ============================================================

-- 1) Quais campanhas geraram mais receita?
SELECT
    c.campaign_id,
    c.campaign_name,
    SUM(f.revenue) AS total_revenue
FROM analytics.fact_marketing_performance f
JOIN analytics.dim_campaign c
    ON c.campaign_id = f.campaign_id
GROUP BY c.campaign_id, c.campaign_name
ORDER BY total_revenue DESC;

-- 2) Quais campanhas tiveram maior custo?
SELECT
    c.campaign_id,
    c.campaign_name,
    SUM(f.cost) AS total_cost
FROM analytics.fact_marketing_performance f
JOIN analytics.dim_campaign c
    ON c.campaign_id = f.campaign_id
GROUP BY c.campaign_id, c.campaign_name
ORDER BY total_cost DESC;

-- 3) Qual campanha teve melhor ROAS?
-- ROAS = revenue / cost
SELECT
    c.campaign_id,
    c.campaign_name,
    SUM(f.revenue) AS total_revenue,
    SUM(f.cost) AS total_cost,
    ROUND(SUM(f.revenue) / NULLIF(SUM(f.cost), 0), 6) AS roas
FROM analytics.fact_marketing_performance f
JOIN analytics.dim_campaign c
    ON c.campaign_id = f.campaign_id
GROUP BY c.campaign_id, c.campaign_name
ORDER BY roas DESC NULLS LAST, total_revenue DESC;

-- 4) Qual origem de tráfego gerou mais conversões?
SELECT
    c.source,
    SUM(f.conversions) AS total_conversions
FROM analytics.fact_marketing_performance f
JOIN analytics.dim_campaign c
    ON c.campaign_id = f.campaign_id
GROUP BY c.source
ORDER BY total_conversions DESC;

-- 5) Qual dispositivo teve melhor performance?
-- Performance é observada por receita, conversões e ROAS.
SELECT
    d.device_category,
    SUM(f.sessions) AS sessions,
    SUM(f.conversions) AS conversions,
    SUM(f.cost) AS total_cost,
    SUM(f.revenue) AS total_revenue,
    ROUND(SUM(f.revenue) / NULLIF(SUM(f.cost), 0), 6) AS roas
FROM analytics.fact_marketing_performance f
JOIN analytics.dim_device d
    ON d.device_id = f.device_id
GROUP BY d.device_category
ORDER BY total_revenue DESC, conversions DESC;

-- 6) Qual foi o CPC médio por campanha?
-- CPC = cost / clicks
SELECT
    c.campaign_id,
    c.campaign_name,
    SUM(f.cost) AS total_cost,
    SUM(f.clicks) AS total_clicks,
    ROUND(SUM(f.cost) / NULLIF(SUM(f.clicks), 0), 6) AS cpc
FROM analytics.fact_marketing_performance f
JOIN analytics.dim_campaign c
    ON c.campaign_id = f.campaign_id
GROUP BY c.campaign_id, c.campaign_name
ORDER BY cpc ASC NULLS LAST;

-- 7) Qual foi o CTR por campanha?
-- CTR = clicks / impressions
SELECT
    c.campaign_id,
    c.campaign_name,
    SUM(f.clicks) AS total_clicks,
    SUM(f.impressions) AS total_impressions,
    ROUND(SUM(f.clicks)::NUMERIC / NULLIF(SUM(f.impressions), 0), 6) AS ctr
FROM analytics.fact_marketing_performance f
JOIN analytics.dim_campaign c
    ON c.campaign_id = f.campaign_id
GROUP BY c.campaign_id, c.campaign_name
ORDER BY ctr DESC NULLS LAST;

-- 8) Qual foi a taxa de conversão por campanha?
-- Conversion Rate = conversions / clicks
SELECT
    c.campaign_id,
    c.campaign_name,
    SUM(f.conversions) AS total_conversions,
    SUM(f.clicks) AS total_clicks,
    ROUND(SUM(f.conversions)::NUMERIC / NULLIF(SUM(f.clicks), 0), 6) AS conversion_rate
FROM analytics.fact_marketing_performance f
JOIN analytics.dim_campaign c
    ON c.campaign_id = f.campaign_id
GROUP BY c.campaign_id, c.campaign_name
ORDER BY conversion_rate DESC NULLS LAST;

-- 9) Quais campanhas tiveram custo, mas não tiveram conversão?
SELECT
    c.campaign_id,
    c.campaign_name,
    SUM(f.cost) AS total_cost,
    SUM(f.conversions) AS total_conversions
FROM analytics.fact_marketing_performance f
JOIN analytics.dim_campaign c
    ON c.campaign_id = f.campaign_id
GROUP BY c.campaign_id, c.campaign_name
HAVING SUM(f.cost) > 0
   AND SUM(f.conversions) = 0
ORDER BY total_cost DESC;

-- 10) Quais campanhas precisam de investigação por baixa performance?
-- Regras de investigação:
-- - custo > 0
-- - e pelo menos um dos critérios:
--   a) ROAS < 1
--   b) conversion_rate < 0.02 (2%)
--   c) CTR < 0.01 (1%)
WITH campaign_metrics AS (
    SELECT
        c.campaign_id,
        c.campaign_name,
        SUM(f.cost) AS total_cost,
        SUM(f.revenue) AS total_revenue,
        SUM(f.clicks) AS total_clicks,
        SUM(f.impressions) AS total_impressions,
        SUM(f.conversions) AS total_conversions,
        ROUND(SUM(f.revenue) / NULLIF(SUM(f.cost), 0), 6) AS roas,
        ROUND(SUM(f.conversions)::NUMERIC / NULLIF(SUM(f.clicks), 0), 6) AS conversion_rate,
        ROUND(SUM(f.clicks)::NUMERIC / NULLIF(SUM(f.impressions), 0), 6) AS ctr
    FROM analytics.fact_marketing_performance f
    JOIN analytics.dim_campaign c
        ON c.campaign_id = f.campaign_id
    GROUP BY c.campaign_id, c.campaign_name
)
SELECT
    campaign_id,
    campaign_name,
    total_cost,
    total_revenue,
    total_clicks,
    total_impressions,
    total_conversions,
    roas,
    conversion_rate,
    ctr,
    CASE
        WHEN roas < 1 THEN 'ROAS abaixo de 1'
        WHEN conversion_rate < 0.02 THEN 'Taxa de conversao abaixo de 2%'
        WHEN ctr < 0.01 THEN 'CTR abaixo de 1%'
        ELSE 'Sem alerta'
    END AS investigation_reason
FROM campaign_metrics
WHERE total_cost > 0
  AND (
      roas < 1
      OR conversion_rate < 0.02
      OR ctr < 0.01
  )
ORDER BY total_cost DESC, roas ASC NULLS LAST;
