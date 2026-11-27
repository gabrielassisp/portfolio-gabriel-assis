"""Cliente da API do Portal da Transparência com paginação, rate limit e retry."""
from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable, Iterator
from datetime import datetime
from zoneinfo import ZoneInfo

import requests

BASE_URL = "https://api.portaldatransparencia.gov.br/api-de-dados"
FUSO_API = ZoneInfo("America/Sao_Paulo")  # a janela 00h-06h segue o horário de Brasília
log = logging.getLogger(__name__)


def limite_por_minuto(restrito: bool, agora: datetime | None = None) -> int:
    """Limites documentados: 700/min (00h-06h), 400/min (demais), 180/min (restritos)."""
    if restrito:
        return 180
    hora = (agora or datetime.now(FUSO_API)).astimezone(FUSO_API).hour
    return 700 if hora < 6 else 400


class RateLimiter:
    """Espaça as chamadas para não passar de N por minuto (com margem de 10%)."""

    def __init__(self, por_minuto: int, relogio: Callable[[], float] = time.monotonic,
                 dormir: Callable[[float], None] = time.sleep):
        self.intervalo = 60.0 / (por_minuto * 0.9)
        self._ultimo = 0.0
        self._relogio, self._dormir = relogio, dormir
        self._lock = threading.Lock()

    def aguardar(self) -> None:
        with self._lock:
            espera = self._ultimo + self.intervalo - self._relogio()
            if espera > 0:
                self._dormir(espera)
            self._ultimo = self._relogio()


class TransparenciaClient:
    def __init__(self, api_key: str, restrito: bool = False, max_tentativas: int = 5,
                 backoff_base: float = 2.0, session: requests.Session | None = None,
                 dormir: Callable[[float], None] = time.sleep, timeout: int = 60):
        if not api_key:
            raise ValueError("TRANSPARENCIA_API_KEY não definida")
        self.session = session or requests.Session()
        self.session.headers.update({"chave-api-dados": api_key, "Accept": "application/json"})
        self.limiter = RateLimiter(limite_por_minuto(restrito), dormir=dormir)
        self.max_tentativas, self.backoff_base = max_tentativas, backoff_base
        self.dormir, self.timeout = dormir, timeout

    def _get(self, path: str, params: dict) -> list[dict]:
        for tentativa in range(1, self.max_tentativas + 1):
            self.limiter.aguardar()
            try:
                resp = self.session.get(BASE_URL + path, params=params, timeout=self.timeout)
            except requests.RequestException as exc:
                erro = str(exc)
            else:
                if resp.status_code == 200:
                    return resp.json() or []
                if resp.status_code not in (429, 500, 502, 503, 504):
                    resp.raise_for_status()
                erro = f"HTTP {resp.status_code}"
            espera = self.backoff_base ** tentativa
            log.warning("Falha em %s %s (%s). Tentativa %s, aguardando %.0fs",
                        path, params, erro, tentativa, espera)
            self.dormir(espera)
        raise RuntimeError(f"Esgotadas {self.max_tentativas} tentativas em {path} {params}")

    def paginar(self, path: str, params: dict, max_paginas: int = 10_000) -> Iterator[list[dict]]:
        """A API pagina com o parâmetro `pagina` (1, 2, ...); uma página vazia encerra."""
        for pagina in range(1, max_paginas + 1):
            registros = self._get(path, {**params, "pagina": pagina})
            if not registros:
                return
            yield registros
        raise RuntimeError(f"Limite de {max_paginas} páginas atingido em {path}")
