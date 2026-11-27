from datetime import datetime

import pytest
import requests
import responses

from ingestion.client import (
    BASE_URL,
    FUSO_API,
    RateLimiter,
    TransparenciaClient,
    limite_por_minuto,
)

PATH = "/novo-bolsa-familia-por-municipio"


def cliente(**kw):
    return TransparenciaClient("chave-teste", dormir=lambda s: None, **kw)


def test_limites_documentados():
    assert limite_por_minuto(False, datetime(2026, 1, 1, 3, tzinfo=FUSO_API)) == 700
    assert limite_por_minuto(False, datetime(2026, 1, 1, 14, tzinfo=FUSO_API)) == 400
    assert limite_por_minuto(True, datetime(2026, 1, 1, 3, tzinfo=FUSO_API)) == 180


def test_rate_limiter_espaca_chamadas():
    t = [0.0]
    esperas = []
    lim = RateLimiter(60, relogio=lambda: t[0], dormir=lambda s: (esperas.append(s), t.__setitem__(0, t[0] + s)))
    lim.aguardar()
    lim.aguardar()
    assert esperas and esperas[0] == pytest.approx(60 / 54)


@responses.activate
def test_paginacao_para_na_pagina_vazia_e_envia_chave():
    for pagina, corpo in [(1, [{"id": 1}, {"id": 2}]), (2, [{"id": 3}]), (3, [])]:
        responses.get(BASE_URL + PATH, json=corpo,
                      match=[responses.matchers.query_param_matcher({"mesAno": "202601", "pagina": str(pagina)})])
    paginas = list(cliente().paginar(PATH, {"mesAno": "202601"}))
    assert [len(p) for p in paginas] == [2, 1]
    assert responses.calls[0].request.headers["chave-api-dados"] == "chave-teste"


@responses.activate
def test_retry_em_429_e_depois_sucesso():
    responses.get(BASE_URL + PATH, status=429)
    responses.get(BASE_URL + PATH, json=[])
    assert list(cliente().paginar(PATH, {})) == []
    assert len(responses.calls) == 2


@responses.activate
def test_desiste_apos_max_tentativas():
    responses.get(BASE_URL + PATH, status=503)
    with pytest.raises(RuntimeError, match="Esgotadas 3"):
        list(cliente(max_tentativas=3).paginar(PATH, {}))


@responses.activate
def test_erro_4xx_nao_faz_retry():
    responses.get(BASE_URL + PATH, status=401)
    with pytest.raises(requests.HTTPError):
        list(cliente().paginar(PATH, {}))
    assert len(responses.calls) == 1


def test_janela_usa_horario_de_brasilia():
    from datetime import UTC
    # 05h UTC = 02h em Brasília -> janela da madrugada
    assert limite_por_minuto(False, datetime(2026, 1, 1, 5, tzinfo=UTC)) == 700


def test_sem_chave_falha_cedo():
    with pytest.raises(ValueError):
        TransparenciaClient("")
