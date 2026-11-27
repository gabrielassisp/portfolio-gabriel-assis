"""Gravação idempotente em Parquet particionado (local ou GCS)."""
from __future__ import annotations

import io
import json
from datetime import UTC, datetime
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq


def caminho_particao(dominio: str, particao: dict[str, str]) -> str:
    partes = "/".join(f"{k}={v}" for k, v in particao.items())
    return f"bronze/{dominio}/{partes}/dados.parquet"


def para_tabela(registros: list[dict], metadados: dict) -> pa.Table:
    """Guarda cada registro como JSON bruto + metadados de carga.

    A bronze não interpreta o schema: os tipos são resolvidos no dbt (silver).
    Assim, mudanças de schema na API não quebram a ingestão.
    """
    carregado_em = datetime.now(UTC).isoformat()
    return pa.table({
        "payload": [json.dumps(r, ensure_ascii=False, sort_keys=True) for r in registros],
        "_carregado_em": [carregado_em] * len(registros),
        **{f"_{k}": [str(v)] * len(registros) for k, v in metadados.items()},
    })


class Storage:
    def __init__(self, backend: str = "local", raiz: str = "data", bucket: str | None = None):
        self.backend, self.raiz, self.bucket = backend, raiz, bucket
        if backend == "gcs":
            from google.cloud import storage  # import tardio: testes não precisam do GCP
            self._bucket = storage.Client().bucket(bucket)

    def gravar(self, tabela: pa.Table, caminho: str) -> str:
        """Sobrescreve o arquivo da partição: reexecutar não duplica dados."""
        if self.backend == "local":
            destino = Path(self.raiz) / caminho
            destino.parent.mkdir(parents=True, exist_ok=True)
            pq.write_table(tabela, destino, compression="snappy")
            return str(destino)
        buffer = io.BytesIO()
        pq.write_table(tabela, buffer, compression="snappy")
        self._bucket.blob(caminho).upload_from_string(buffer.getvalue())
        return f"gs://{self.bucket}/{caminho}"
