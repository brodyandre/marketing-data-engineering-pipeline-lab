# Extensão Opcional: GCP + BigQuery

Este documento descreve como o projeto pode evoluir para uma arquitetura em Google Cloud Platform (GCP), **sem implementar conexão real** e **sem uso de credenciais reais**.

## Objetivo da extensão

Migrar o pipeline local (CSV + Python + PostgreSQL) para um desenho cloud-native orientado a escala, observabilidade e consumo analítico de dados de marketing.

## Diagrama textual da arquitetura futura

```text
GA4 / Google Ads / CRM
        ↓
Cloud Storage
        ↓
Cloud Run ou Cloud Functions
        ↓
BigQuery Raw
        ↓
BigQuery Analytics
        ↓
Looker Studio / Dashboards
```

## 1) Como substituir PostgreSQL por BigQuery

No desenho atual, o carregamento final usa PostgreSQL (`schema analytics`).  
Na evolução para GCP:

- substituir `src/load.py` para gravar tabelas no BigQuery;
- manter a separação entre camada bruta e camada analítica;
- usar datasets no BigQuery, por exemplo:
  - `marketing_raw`
  - `marketing_analytics`

Mapeamento conceitual:

- `analytics.dim_date` -> `marketing_analytics.dim_date`
- `analytics.dim_campaign` -> `marketing_analytics.dim_campaign`
- `analytics.dim_customer` -> `marketing_analytics.dim_customer`
- `analytics.fact_marketing_performance` -> `marketing_analytics.fact_marketing_performance`

## 2) Como armazenar arquivos raw em Cloud Storage

Em vez de manter somente `data/raw` local:

- criar bucket dedicado (ex.: `gs://marketing-pipeline-raw`);
- organizar por partição de data de ingestão, por exemplo:
  - `raw/ga4_events/ingestion_date=2026-05-22/*.csv`
  - `raw/google_ads_campaigns/ingestion_date=2026-05-22/*.csv`
  - `raw/customers/ingestion_date=2026-05-22/*.csv`

Benefícios:

- versionamento de entradas por data;
- reprocessamento histórico;
- trilha de auditoria.

## 3) Como usar Cloud Run ou Cloud Functions para executar o pipeline

### Opção A: Cloud Run (recomendado para jobs mais robustos)

- empacotar pipeline Python em container;
- executar via job com parâmetros de data;
- vantagem: maior controle de dependências, timeout e memória.

### Opção B: Cloud Functions

- usar função acionada por evento (upload no Cloud Storage);
- bom para fluxos menores e simples.

Em ambos os casos:

- manter etapas lógicas: extract -> transform -> quality -> load;
- registrar logs estruturados para troubleshooting.

## 4) Como usar Cloud Scheduler para agendamento

Cloud Scheduler pode disparar execução periódica:

- diariamente (ex.: `0 6 * * *`);
- por janela de campanha (ex.: de hora em hora em períodos de mídia paga).

Integrações comuns:

- Scheduler -> HTTP target (Cloud Run);
- Scheduler -> Pub/Sub -> Cloud Function.

## 5) Como usar Secret Manager para credenciais

Para não expor segredos no código:

- armazenar segredos no Secret Manager;
- injetar em runtime como variáveis de ambiente;
- controlar acesso via IAM com princípio de menor privilégio.

Exemplos de segredos (conceituais):

- token de API de mídia;
- senha de serviço externo;
- chave de integração entre sistemas.

**Importante:** este repositório não deve conter credenciais reais.

## 6) Como conectar dados simulados de GA4 exportados para BigQuery

GA4 em produção normalmente exporta dados para BigQuery em tabelas como:

- `events_YYYYMMDD`
- `events_intraday_YYYYMMDD`

Para manter coerência com este laboratório:

- criar tabelas simuladas no dataset `marketing_raw` com estrutura simplificada;
- aplicar transformação para o mesmo modelo dimensional do projeto;
- normalizar campos de aquisição (`source`, `medium`, `campaign`) e conversão.

Assim, o laboratório continua didático, mas alinhado a um cenário real de GA4 + BigQuery.

## 7) Como esse desenho se aplica a dados de marketing

A arquitetura proposta é adequada para marketing porque:

- integra múltiplas fontes com granularidades diferentes (eventos, mídia, CRM);
- suporta análises de funil, performance de campanha e eficiência de investimento;
- permite governança e qualidade antes da publicação para BI;
- facilita consumo por times de negócio em dashboards (Looker Studio).

## Referência de evolução incremental

1. Substituir camada de storage local por Cloud Storage.
2. Publicar pipeline em Cloud Run.
3. Carregar camadas `raw` e `analytics` no BigQuery.
4. Agendar execução com Cloud Scheduler.
5. Expor métricas em Looker Studio.
