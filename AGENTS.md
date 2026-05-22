# AGENTS.md

Guia para futuras interações com o Codex neste repositório.

## Perfil do projeto

Este repositório foi criado para demonstrar habilidades práticas de Engenharia de Dados para processos seletivos.

## Objetivo do projeto

Implementar um pipeline de dados de marketing digital (inspirado em GA4 e Google Ads) com:

- extração de dados CSV;
- transformação para modelo dimensional;
- validações de qualidade;
- carga em PostgreSQL (schema `analytics`);
- testes automatizados e CI.

## Padrão de código esperado

- Priorizar código simples, legível e com funções pequenas.
- Usar nomes claros em `snake_case`.
- Evitar lógica duplicada e efeitos colaterais desnecessários.
- Tratar erros com mensagens objetivas para troubleshooting.
- Manter compatibilidade com execução local (`python -m src.pipeline`).
- Incluir testes ao alterar regras de transformação/qualidade.

## Regras sobre dados

- Não usar dados reais de usuários, clientes ou empresas.
- Utilizar apenas dados sintéticos/fictícios.
- Não adicionar informações pessoais identificáveis.

## Regras sobre credenciais e segurança

- Nunca inserir credenciais reais no código, documentação ou commits.
- Não versionar arquivos `.env` com segredos.
- Usar somente valores de exemplo (ex.: `postgres/postgres`) para ambiente local.

## Comandos principais do projeto

Com `Makefile`:

- `make install`
- `make up`
- `make down`
- `make pipeline`
- `make quality`
- `make test`
- `make clean`

Comandos diretos:

- `python -m src.pipeline`
- `python -m src.quality`
- `pytest`
- `docker compose up -d`

## Padrão de commits sugerido

Preferir commits pequenos e descritivos, por exemplo:

- `feat: adiciona validações de qualidade para métricas negativas`
- `fix: corrige mapeamento de campaign_id unknown`
- `docs: atualiza troubleshooting de conexão postgres`
- `test: cobre cenário de revenue nulo na transformação`
- `chore: ajusta workflow de CI`

## Cuidados ao alterar README e documentação

- Manter README e `docs/` alinhados com o código atual.
- Atualizar exemplos de comandos quando houver mudança de execução.
- Evitar promessas de features não implementadas.
- Preservar linguagem técnica clara e foco em recrutadores.

## Regras de simplicidade, didática e empregabilidade

- Evitar overengineering e dependências desnecessárias.
- Priorizar clareza de arquitetura e rastreabilidade do fluxo de dados.
- Garantir que o projeto rode localmente com poucos passos.
- Explicar decisões técnicas de forma objetiva.
- Manter o projeto orientado a portfólio: demonstrar fundamentos sólidos de Engenharia de Dados.
