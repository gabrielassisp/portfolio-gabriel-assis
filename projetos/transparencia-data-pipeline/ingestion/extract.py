"""Extrai um endpoint para uma partição da bronze. Usado pelas DAGs e pela CLI."""
from __future__ import annotations

import argparse
import logging
import os
import time
from pathlib import Path

import yaml

from ingestion.client import TransparenciaClient
from ingestion.municipios import listar_municipios
from ingestion.storage import Storage, caminho_particao, para_tabela

CONFIG = Path(__file__).resolve().parent.parent / "config" / "endpoints.yml"
log = logging.getLogger(__name__)


def carregar_config(dominio: str) -> dict:
    endpoints = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))["endpoints"]
    if dominio not in endpoints:
        raise KeyError(f"Domínio '{dominio}' não está em {CONFIG.name}")
    return endpoints[dominio]


def params_da_particao(tipo: str, ano: int, mes: int | None) -> tuple[dict, dict]:
    if tipo == "ano":
        return {"ano": ano}, {"ano": str(ano)}
    if tipo == "mes_ano":
        if mes is None:
            raise ValueError("Partição mensal exige mês")
        return {"mesAno": f"{ano}{mes:02d}"}, {"ano": str(ano), "mes": f"{mes:02d}"}
    raise ValueError(f"Tipo de partição desconhecido: {tipo}")


def ufs_configuradas(cfg: dict) -> list[str]:
    env = os.environ.get("BF_UFS", "")
    return [u for u in env.split(",") if u.strip()] or cfg.get("ufs", [])


def extrair(dominio: str, ano: int, mes: int | None = None, client=None, storage=None,
            params_extra: dict | None = None, municipios: list[str] | None = None) -> dict:
    cfg = carregar_config(dominio)
    client = client or TransparenciaClient(os.environ.get("TRANSPARENCIA_API_KEY", ""),
                                           restrito=cfg.get("restrito", False))
    storage = storage or Storage(os.environ.get("STORAGE_BACKEND", "local"),
                                 raiz=os.environ.get("DATA_DIR", "data"),
                                 bucket=os.environ.get("GCS_BUCKET"))
    params, particao = params_da_particao(cfg["particao"], ano, mes)
    params = {**cfg.get("params_fixos", {}), **params, **(params_extra or {})}

    if cfg.get("iterar_por") == "codigoIbge":
        codigos = municipios if municipios is not None else listar_municipios(ufs_configuradas(cfg))
        requisicoes = [{**params, "codigoIbge": c} for c in codigos]
    else:
        requisicoes = [params]

    inicio, registros, paginas = time.monotonic(), [], 0
    for req in requisicoes:
        for pagina in client.paginar(cfg["path"], req):
            registros.extend(pagina)
            paginas += 1

    caminho = caminho_particao(dominio, particao)
    destino = storage.gravar(para_tabela(registros, {"dominio": dominio, **particao}), caminho)
    auditoria = {"dominio": dominio, **particao, "requisicoes": len(requisicoes),
                 "paginas": paginas, "linhas": len(registros),
                 "destino": destino, "duracao_s": round(time.monotonic() - inicio, 2)}
    log.info("Carga concluída: %s", auditoria)
    return auditoria


def main() -> None:
    from dotenv import load_dotenv
    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    p = argparse.ArgumentParser(description="Extrai um endpoint do Portal da Transparência")
    p.add_argument("dominio")
    p.add_argument("--ano", type=int, required=True)
    p.add_argument("--mes", type=int)
    a = p.parse_args()
    print(extrair(a.dominio, a.ano, a.mes))


if __name__ == "__main__":
    main()
