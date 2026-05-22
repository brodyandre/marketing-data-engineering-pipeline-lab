# Modelo de Dados

Schema analítico: `analytics`

## Modelo dimensional

O projeto adota **Star Schema** (esquema estrela), com:

- uma tabela fato central (`fact_marketing_performance`);
- dimensões de contexto (`dim_date`, `dim_campaign`, `dim_customer`, `dim_device`).

Essa modelagem favorece consultas analíticas simples, bom desempenho em agregações e entendimento rápido por analistas e recrutadores técnicos.

## Por que usar Star Schema

Principais motivos:

- separa fatos quantitativos de atributos descritivos;
- reduz complexidade de joins em análises de marketing;
- facilita expansão de métricas e dimensões no futuro;
- é um padrão comum em Data Warehouses corporativos.

## Tabelas dimensão

### `analytics.dim_date`

Dimensão temporal para análise por período.

Campos principais:

- `date_id` (PK, `YYYYMMDD`)
- `full_date` (DATE)
- `year`
- `month`
- `day`
- `month_name`

### `analytics.dim_campaign`

Dimensão de campanhas e aquisição.

Campos principais:

- `campaign_id` (PK)
- `campaign_name`
- `source`
- `medium`

Observação: campanhas ausentes no dado bruto são padronizadas como `unknown`.

### `analytics.dim_customer`

Dimensão de clientes para segmentação analítica.

Campos principais:

- `customer_id` (PK)
- `user_pseudo_id`
- `customer_segment`
- `city`
- `state`

Inclui registro técnico `unknown` para manter integridade em casos sem mapeamento.

### `analytics.dim_device`

Dimensão de dispositivo para análise de performance por contexto de acesso.

Campos principais:

- `device_id` (PK)
- `device_category`

Inclui registro técnico `unknown` para linhas sem granularidade de dispositivo
(por exemplo, métricas agregadas de mídia paga).

## Tabela fato

### `analytics.fact_marketing_performance`

Tabela central com métricas de marketing.

Chaves:

- `date_id` (FK -> `dim_date.date_id`)
- `campaign_id` (FK -> `dim_campaign.campaign_id`)
- `customer_id` (FK -> `dim_customer.customer_id`)
- `device_id` (FK -> `dim_device.device_id`)

Métricas:

- `sessions`
- `events`
- `conversions`
- `impressions`
- `clicks`
- `cost`
- `revenue`

Grão da fato: **uma linha por (`date_id`, `campaign_id`, `customer_id`, `device_id`)**.

## Principais métricas analíticas

Métricas base disponíveis:

- Receita total (`SUM(revenue)`)
- Custo total (`SUM(cost)`)
- Cliques e impressões
- Conversões

Métricas derivadas comuns:

- CTR = `SUM(clicks) / SUM(impressions)`
- CPC = `SUM(cost) / SUM(clicks)`
- Taxa de conversão = `SUM(conversions) / SUM(clicks)` (ou por sessão, conforme regra de negócio)
- ROAS = `SUM(revenue) / SUM(cost)`

Essas métricas estão exemplificadas em `sql/04_analytics_queries.sql`.
