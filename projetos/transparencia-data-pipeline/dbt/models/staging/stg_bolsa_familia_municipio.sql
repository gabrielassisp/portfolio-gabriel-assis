-- Interpreta o JSON bruto da bronze. Os caminhos JSON devem ser conferidos
-- com uma resposta real da API (rode a extração e inspecione o payload).
with origem as (
    select payload, _carregado_em, _ano, _mes
    from {{ source('bronze', 'bolsa_familia_municipio') }}
)
select
    json_value(payload, '$.municipio.codigoIBGE')                 as cod_municipio_ibge,
    json_value(payload, '$.municipio.nomeIBGE')                   as nome_municipio,
    json_value(payload, '$.municipio.uf.sigla')                   as uf,
    parse_date('%Y%m', json_value(payload, '$.dataReferencia'))   as mes_referencia,
    safe_cast(json_value(payload, '$.valor') as numeric)          as valor_total,
    safe_cast(json_value(payload, '$.quantidadeBeneficiados') as int64) as qtd_beneficiados,
    timestamp(_carregado_em)                                      as carregado_em
from origem
