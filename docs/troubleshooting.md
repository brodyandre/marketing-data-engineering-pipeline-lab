# Troubleshooting

Este guia cobre os erros mais comuns ao executar o pipeline local.

## 1) Erro de conexão com PostgreSQL

Sintomas comuns:

- `Could not connect to PostgreSQL...`
- `connection timeout expired`
- `OperationalError` no `src/load.py`

Diagnóstico:

1. Verifique se o container está ativo:
   - `docker compose ps`
2. Confirme se o serviço `postgres` está `healthy`.
3. Valide variáveis de ambiente em `.env`:
   - `POSTGRES_HOST`
   - `POSTGRES_PORT`
   - `POSTGRES_DB`
   - `POSTGRES_USER`
   - `POSTGRES_PASSWORD`

Correção rápida:

- Subir/recriar containers:
  - `docker compose down`
  - `docker compose up -d`

Se o erro persistir após mudança de usuário/senha no `docker-compose.yml` ou `.env`:

- o volume antigo pode manter as credenciais anteriores;
- recrie o banco removendo volume:
  - `docker compose down -v`
  - `docker compose up -d`

## 2) Porta 5432 ocupada

Sintomas comuns:

- erro ao subir container com mensagem de bind/port already in use.

Diagnóstico:

- Verifique processo usando a porta `5432`.
  - Windows PowerShell:
    - `netstat -ano | findstr :5432`

Correções possíveis:

1. Encerrar o processo que está usando a porta.
2. Alterar porta publicada no `docker-compose.yml`, por exemplo `5433:5432`.
3. Se alterar porta, atualizar também `POSTGRES_PORT` no `.env`.

## 3) Container não sobe

Sintomas comuns:

- `docker compose up -d` falha.
- container entra em estado `exited` ou `unhealthy`.

Diagnóstico:

1. Inspecione logs:
   - `docker compose logs postgres`
2. Verifique espaço em disco e permissões Docker.
3. Confirme se imagem foi baixada corretamente.

Correções possíveis:

1. Recriar ambiente:
   - `docker compose down`
   - `docker compose up -d --force-recreate`
2. Se necessário, remover volumes e subir novamente:
   - `docker compose down -v`
   - `docker compose up -d`

## 4) Arquivo CSV não encontrado

Sintomas comuns:

- `FileNotFoundError` em `src.extract`.
- mensagem indicando ausência em `data/raw`.

Diagnóstico:

1. Confirme existência dos arquivos:
   - `data/raw/ga4_events.csv`
   - `data/raw/google_ads_campaigns.csv`
   - `data/raw/customers.csv`
2. Verifique se o nome dos arquivos está exatamente igual.

Correções possíveis:

1. Recriar arquivos de entrada na pasta `data/raw`.
2. Ajustar permissões de leitura da pasta.
3. Executar novamente:
   - `python -m src.extract`

## 5) Erro de dependências Python

Sintomas comuns:

- `ModuleNotFoundError`
- `ImportError`
- falhas de versão ao instalar pacotes

Diagnóstico:

1. Verifique versão do Python:
   - `python --version` (esperado: 3.11+)
2. Confirme ativação do ambiente virtual.

Correção rápida:

1. Recriar ambiente:
   - `python -m venv .venv`
   - ativar `.venv`
2. Reinstalar dependências:
   - `pip install -r requirements.txt`

## 6) Erro nos testes

Sintomas comuns:

- `pytest` com testes falhando.

Diagnóstico:

1. Rode testes detalhados:
   - `pytest -vv`
2. Execute módulo isolado com problema:
   - `python -m src.transform`
   - `python -m src.quality`
3. Verifique se os CSVs de `data/raw` estão no formato esperado.

Correções possíveis:

1. Corrigir dados de entrada inválidos (tipos, colunas, nulos inesperados).
2. Atualizar regra de transformação/qualidade e testes em conjunto.
3. Validar novamente:
   - `pytest`
