import json

import pyarrow.parquet as pq
import pytest

from ingestion.extract import extrair, params_da_particao
from ingestion.storage import Storage, caminho_particao


class ClienteFalso:
    def __init__(self, paginas):
        self.paginas, self.chamadas = paginas, []

    def paginar(self, path, params):
        self.chamadas.append((path, params))
        yield from self.paginas


def test_params_da_particao():
    assert params_da_particao("mes_ano", 2026, 3) == ({"mesAno": "202603"}, {"ano": "2026", "mes": "03"})
    assert params_da_particao("ano", 2025, None) == ({"ano": 2025}, {"ano": "2025"})
    with pytest.raises(ValueError):
        params_da_particao("mes_ano", 2026, None)


def test_caminho_hive():
    assert caminho_particao("x", {"ano": "2026", "mes": "01"}) == "bronze/x/ano=2026/mes=01/dados.parquet"


def test_extracao_grava_payload_bruto_e_e_idempotente(tmp_path):
    storage = Storage("local", raiz=str(tmp_path))
    paginas = [[{"valor": 10, "municipio": {"codigoIBGE": "3143302"}}], [{"valor": 20}]]

    for _ in range(2):  # reexecução da mesma partição
        auditoria = extrair("bolsa_familia_municipio", 2026, 1,
                            client=ClienteFalso(paginas), storage=storage,
                            municipios=["3143302"])

    arquivo = tmp_path / "bronze/bolsa_familia_municipio/ano=2026/mes=01/dados.parquet"
    tabela = pq.read_table(arquivo)
    assert tabela.num_rows == 2                     # não duplicou
    assert json.loads(tabela.column("payload")[0].as_py())["valor"] == 10
    assert set(tabela.column_names) >= {"payload", "_carregado_em", "_dominio", "_ano", "_mes"}
    assert auditoria["linhas"] == 2 and auditoria["paginas"] == 2


def test_dominio_inexistente():
    with pytest.raises(KeyError):
        extrair("nao_existe", 2026, 1, client=ClienteFalso([]), storage=object())


def test_bolsa_familia_faz_uma_chamada_por_municipio(tmp_path):
    cliente = ClienteFalso([[{"valor": 1}]])
    auditoria = extrair("bolsa_familia_municipio", 2024, 1, client=cliente,
                        storage=Storage("local", raiz=str(tmp_path)),
                        municipios=["3106200", "3143302"])
    assert [p["codigoIbge"] for _, p in cliente.chamadas] == ["3106200", "3143302"]
    assert all(p["mesAno"] == "202401" for _, p in cliente.chamadas)
    assert auditoria["requisicoes"] == 2 and auditoria["linhas"] == 2


def test_endpoint_sem_iteracao_faz_uma_chamada(tmp_path):
    cliente = ClienteFalso([[{"valor": 1}]])
    extrair("despesas_por_orgao", 2024, client=cliente, storage=Storage("local", raiz=str(tmp_path)))
    assert len(cliente.chamadas) == 1 and "codigoIbge" not in cliente.chamadas[0][1]


def test_ufs_por_variavel_de_ambiente(monkeypatch):
    from ingestion.extract import ufs_configuradas
    monkeypatch.setenv("BF_UFS", "MG, SP")
    assert [u.strip() for u in ufs_configuradas({"ufs": ["RJ"]})] == ["MG", "SP"]
    monkeypatch.delenv("BF_UFS")
    assert ufs_configuradas({"ufs": ["RJ"]}) == ["RJ"]
