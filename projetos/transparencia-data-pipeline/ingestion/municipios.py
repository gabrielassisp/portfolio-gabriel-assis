"""Lista de municípios do IBGE, usada pelos endpoints que exigem `codigoIbge`."""
from __future__ import annotations

import requests

URL_IBGE = "https://servicodados.ibge.gov.br/api/v1/localidades/estados/{uf}/municipios"


def listar_municipios(ufs: list[str], session: requests.Session | None = None,
                      timeout: int = 60) -> list[str]:
    """Códigos IBGE (7 dígitos) dos municípios das UFs informadas, ordenados."""
    session = session or requests.Session()
    codigos: set[str] = set()
    for uf in ufs:
        resp = session.get(URL_IBGE.format(uf=uf.strip().upper()), timeout=timeout)
        resp.raise_for_status()
        municipios = resp.json()
        if not municipios:
            raise ValueError(f"Nenhum município retornado para a UF '{uf}'")
        codigos.update(str(m["id"]) for m in municipios)
    return sorted(codigos)
