# Arquitetura

## Visão geral da arquitetura

Este projeto implementa um pipeline local de Engenharia de Dados para marketing digital, com foco em dados sintéticos inspirados em GA4 e Google Ads.  
O objetivo arquitetural é separar claramente ingestão, transformação, validação e carga em Data Warehouse para facilitar manutenção, testes e evolução.

Fontes simuladas:

- `data/raw/ga4_events.csv`
- `data/raw/google_ads_campaigns.csv`
- `data/raw/customers.csv`

Saídas principais:

- tabelas dimensionais e fato em `data/processed/*.csv`;
- carga no PostgreSQL, schema `analytics`.

## Fluxo dos dados

O pipeline segue esta sequência:

1. `src.extract.extract_data()` lê CSVs da camada `raw`.
2. `src.transform.transform_data()` padroniza dados e monta o modelo dimensional.
3. `src.quality.run_quality_checks()` valida integridade e regras críticas.
4. `src.transform.save_transformed_data()` persiste CSVs na camada `processed`.
5. `src.load.load_to_postgres()` cria schema/tabelas e carrega no PostgreSQL.

Orquestração ponta a ponta: `python -m src.pipeline`.

## Camadas de dados

### Camada `raw`

- Representa a entrada bruta dos dados.
- Mantém estrutura próxima da origem (eventos GA4, campanhas Ads, clientes).
- Útil para reprocessamento e auditoria.

### Camada `processed`

- Contém datasets tratados e agregados.
- Estrutura já orientada ao consumo analítico (dimensões e fato).
- Permite inspeção local do resultado antes da carga no banco.

### Camada `analytics` (PostgreSQL)

- Camada de Data Warehouse relacional para consultas SQL.
- Recebe tabelas finais:
  - `dim_date`
  - `dim_campaign`
  - `dim_customer`
  - `dim_device`
  - `fact_marketing_performance`
- Suporta análises de performance por campanha, custo, receita e conversão.

## Papel do Python

Python é o motor do pipeline e cobre:

- ingestão com `pandas`;
- normalização de colunas e tipos;
- tratamento de nulos e defaults (ex.: campanha `unknown`);
- agregações por data, campanha e cliente;
- validações de qualidade e mensagens de troubleshooting.

## Papel do PostgreSQL

PostgreSQL atua como camada analítica persistente:

- centraliza o modelo dimensional no schema `analytics`;
- permite consultas analíticas reproduzíveis e validações SQL;
- facilita integração com ferramentas de BI e painéis futuros.

## Papel do Docker

Docker padroniza o ambiente local:

- provisiona PostgreSQL com `docker compose up -d`;
- isola dependências do banco;
- permite subir opcionalmente o pgAdmin para inspeção visual dos dados.

Isso reduz divergência de ambiente entre máquinas de desenvolvimento.

## Possibilidades futuras com GCP e BigQuery

Evoluções naturais para cenário cloud:

1. Orquestração no GCP (Cloud Composer/Airflow ou Cloud Run Jobs).
2. Armazenamento de dados brutos no Google Cloud Storage (`raw`).
3. Transformações ELT no BigQuery (SQL + scheduled queries/dbt).
4. Camada analítica final em BigQuery com particionamento por data.
5. Observabilidade com Cloud Logging + alertas de qualidade.

Com isso, o pipeline evolui de ambiente local para arquitetura escalável e orientada a produção.
