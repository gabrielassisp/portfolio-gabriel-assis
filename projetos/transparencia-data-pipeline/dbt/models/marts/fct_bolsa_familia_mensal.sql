{{ config(
    partition_by={'field': 'mes_referencia', 'data_type': 'date', 'granularity': 'month'},
    cluster_by=['cod_municipio_ibge']
) }}
select
    cod_municipio_ibge,
    mes_referencia,
    valor_total,
    qtd_beneficiados,
    safe_divide(valor_total, qtd_beneficiados) as valor_medio_por_beneficiario
from {{ ref('int_bolsa_familia_mensal') }}
