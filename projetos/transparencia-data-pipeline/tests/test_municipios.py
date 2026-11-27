import pytest

from ingestion.municipios import listar_municipios


class Resp:
    def __init__(self, dados): self.dados = dados
    def raise_for_status(self): pass
    def json(self): return self.dados


class SessaoFalsa:
    def __init__(self, por_uf): self.por_uf, self.urls = por_uf, []
    def get(self, url, timeout):
        self.urls.append(url)
        return Resp(self.por_uf[url.split("/estados/")[1].split("/")[0]])


def test_lista_codigos_ordenados_e_sem_duplicata():
    s = SessaoFalsa({"MG": [{"id": 3143302}, {"id": 3106200}], "SP": [{"id": 3550308}]})
    assert listar_municipios(["mg", "SP"], session=s) == ["3106200", "3143302", "3550308"]


def test_uf_sem_municipios_falha():
    with pytest.raises(ValueError):
        listar_municipios(["XX"], session=SessaoFalsa({"XX": []}))
