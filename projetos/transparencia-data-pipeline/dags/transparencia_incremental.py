"""Carga mensal incremental. Com catchup=True, a mesma DAG faz o backfill histórico:
cada execução lógica processa e sobrescreve só a partição do seu mês (idempotente).

Os caminhos são resolvidos a partir deste arquivo, então a DAG roda igual no Docker
(/opt/airflow), num clone local ou num DAG bundle do Git (Airflow 3).
"""
import os
import sys
from datetime import timedelta
from pathlib import Path

import pendulum
from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import dag, task

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))  # permite "from ingestion import ..."

DBT_DIR = REPO / "dbt"
DBT_BIN = os.environ.get("DBT_BIN", "dbt")

def mes_fechado(logical_date):
    """Mês anterior à execução. No Airflow 3 o cron agenda por instante (CronTriggerTimetable):
    data_interval_start == logical_date. A execução do dia 5 deve processar o mês já fechado."""
    ultimo_dia_mes_anterior = logical_date.replace(day=1) - timedelta(days=1)
    return ultimo_dia_mes_anterior.year, ultimo_dia_mes_anterior.month


DEFAULT_ARGS = {"owner": "gabriel", "retries": 2, "retry_delay": timedelta(minutes=10)}


@dag(
    dag_id="transparencia_incremental",
    schedule="0 2 5 * *",          # dia 5, 02h: janela de 700 req/min e dados do mês fechado
    start_date=pendulum.datetime(2024, 1, 1, tz="America/Sao_Paulo"),
    catchup=True,
    max_active_runs=1,             # respeita o rate limit compartilhado da chave
    default_args=DEFAULT_ARGS,
    tags=["transparencia", "ingestao"],
)
def transparencia_incremental():
    @task
    def extrair_bolsa_familia(logical_date=None):
        from ingestion.extract import extrair
        ano, mes = mes_fechado(logical_date)
        return extrair("bolsa_familia_municipio", ano, mes)

    @task
    def extrair_despesas(logical_date=None):
        from ingestion.extract import extrair
        ano, _ = mes_fechado(logical_date)
        return extrair("despesas_por_orgao", ano)

    @task
    def registrar_auditoria(cargas: list[dict]):
        # TODO etapa 3: gravar em BigQuery (dataset audit, tabela cargas)
        for c in cargas:
            print(c)

    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command=f"cd {DBT_DIR} && {DBT_BIN} deps && {DBT_BIN} build --target prod",
    )

    cargas = [extrair_bolsa_familia(), extrair_despesas()]
    registrar_auditoria(cargas) >> dbt_build


transparencia_incremental()
