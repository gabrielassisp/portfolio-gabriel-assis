# Pipeline de dados do Portal da Transparência

Pipeline de engenharia de dados com dados públicos do Governo Federal: ingestão da API do Portal da Transparência, data lake em camadas no GCP e modelagem dimensional com dbt, orquestrado pelo Airflow.

A arquitetura é baseada em uma plataforma que construí profissionalmente com Airflow, dbt e PostgreSQL, reimplementada do zero com dados públicos.

> Status: em construção. Veja o [plano por etapas](#plano).

## Arquitetura

```
API REST / arquivos mensais
        │  ingestion/ (Python: paginação, rate limit, retry)
        ▼
GCS  bronze/<dominio>/ano=YYYY/mes=MM/dados.parquet   (JSON bruto + metadados de carga)
        │  BigQuery: tabelas externas (Terraform)
        ▼
dbt  silver: staging (tipagem) → intermediate (incremental, merge)
        ▼
dbt  gold: fatos e dimensões, particionados e clusterizados
        ▼
Looker Studio / Power BI

Orquestração: Airflow · Infra: Terraform · CI: GitHub Actions
```

## Decisões de engenharia

- **Ingestão idempotente.** Cada execução grava uma única partição (`ano=/mes=`) e a sobrescreve. Reprocessar um mês não duplica dados.
- **Backfill e incremental na mesma DAG.** `catchup=True`: cada execução lógica processa só o mês do seu intervalo.
- **Rate limit da API.** A API permite 700 req/min entre 00h e 06h, 400 req/min no resto do dia e 180 req/min nos endpoints restritos. O cliente espaça as chamadas com 10% de margem, e a DAG roda às 02h com `max_active_runs=1`.
- **Retry com backoff exponencial** em 429 e 5xx. Erros 4xx falham na hora, sem insistir.
- **Bronze sem schema.** O payload é guardado como JSON bruto; a tipagem fica no dbt. Mudanças na API não quebram a ingestão.
- **Particionamento e clustering** nos modelos incrementais e na gold, com trava de custo (`maximum_bytes_billed`) no perfil do dbt.
- **Qualidade:** testes genéricos, `dbt_utils`, `dbt_expectations` e testes singulares de plausibilidade.

## Como rodar

```bash
cp .env.example .env            # preencha TRANSPARENCIA_API_KEY
pip install -r requirements-dev.txt
pytest                           # testes do cliente e da ingestão

# Extração avulsa (grava em ./data com STORAGE_BACKEND=local)
python -m ingestion.extract bolsa_familia_municipio --ano 2026 --mes 1

# Airflow local
docker compose up -d             # http://localhost:8080 (usuário/senha nos logs do container)

# Infra no GCP
cd infra && cp terraform.tfvars.example terraform.tfvars && terraform init && terraform apply
```

## Plano

| Etapa | Entrega | Status |
|---|---|---|
| 1. Setup | repositório, Docker Compose, Terraform | ✅ esqueleto |
| 2. Ingestão | cliente com paginação, rate limit e retry, testes | ✅ esqueleto |
| 3. Histórico | backfill de 2–3 anos, tabela de auditoria no BigQuery | ⏳ |
| 4. dbt | staging, incremental, estrela, SCD2 de favorecidos | 🚧 Bolsa Família iniciado |
| 5. Otimização | comparação de custo com e sem partição/cluster | ⏳ |
| 6. CI e docs | dbt build no CI, `dbt docs` no GitHub Pages | 🚧 CI Python pronto |
| 7. Visualização | dashboard e resultados | ⏳ |

## Fonte

Dados do [Portal da Transparência](https://portaldatransparencia.gov.br) (CGU), via API pública com chave gratuita.
