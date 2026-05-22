-- 1) Detectar nulos em chaves (PK/FK e chaves de negocio)
SELECT 'dim_date.date_id' AS check_name, COUNT(*) AS invalid_rows
FROM analytics.dim_date
WHERE date_id IS NULL

UNION ALL
SELECT 'dim_campaign.campaign_id' AS check_name, COUNT(*) AS invalid_rows
FROM analytics.dim_campaign
WHERE campaign_id IS NULL OR BTRIM(campaign_id) = ''

UNION ALL
SELECT 'dim_customer.customer_id' AS check_name, COUNT(*) AS invalid_rows
FROM analytics.dim_customer
WHERE customer_id IS NULL OR BTRIM(customer_id) = ''

UNION ALL
SELECT 'dim_device.device_id' AS check_name, COUNT(*) AS invalid_rows
FROM analytics.dim_device
WHERE device_id IS NULL OR BTRIM(device_id) = ''

UNION ALL
SELECT 'fact keys' AS check_name, COUNT(*) AS invalid_rows
FROM analytics.fact_marketing_performance
WHERE date_id IS NULL
   OR campaign_id IS NULL OR BTRIM(campaign_id) = ''
   OR customer_id IS NULL OR BTRIM(customer_id) = ''
   OR device_id IS NULL OR BTRIM(device_id) = '';

-- 2) Detectar metricas negativas
SELECT *
FROM analytics.fact_marketing_performance
WHERE cost < 0
   OR revenue < 0
   OR clicks < 0
   OR impressions < 0
   OR conversions < 0
   OR sessions < 0
   OR events < 0;

-- 3) Verificar duplicidades no grao da fato
SELECT
    date_id,
    campaign_id,
    customer_id,
    device_id,
    COUNT(*) AS duplicate_count
FROM analytics.fact_marketing_performance
GROUP BY date_id, campaign_id, customer_id, device_id
HAVING COUNT(*) > 1;

-- 4) Verificar campanhas sem nome
SELECT *
FROM analytics.dim_campaign
WHERE campaign_name IS NULL OR BTRIM(campaign_name) = '';

-- 5a) Verificar datas invalidas na dimensao de datas
SELECT *
FROM analytics.dim_date
WHERE full_date IS NULL
   OR date_id <> TO_CHAR(full_date, 'YYYYMMDD')::INTEGER
   OR year <> EXTRACT(YEAR FROM full_date)::SMALLINT
   OR month <> EXTRACT(MONTH FROM full_date)::SMALLINT
   OR day <> EXTRACT(DAY FROM full_date)::SMALLINT;

-- 5b) Verificar fatos com date_id inexistente na dimensao
SELECT f.*
FROM analytics.fact_marketing_performance f
LEFT JOIN analytics.dim_date d
    ON f.date_id = d.date_id
WHERE d.date_id IS NULL;
