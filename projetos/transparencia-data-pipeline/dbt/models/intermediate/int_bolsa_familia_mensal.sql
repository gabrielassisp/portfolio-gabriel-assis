-- Incremental com merge: reprocessar um mês substitui as linhas daquele mês.
{{ config(
    unique_key=['cod_municipio_ibge', 'mes_referencia'],
    incremental_strategy='merge',
    partition_by={'field': 'mes_referencia', 'data_type': 'date', 'granularity': 'month'},
    cluster_by=['uf', 'cod_municipio_ibge']
) }}
select *
from {{ ref('stg_bolsa_familia_municipio') }}
{% if is_incremental() %}
where carregado_em > (select coalesce(max(carregado_em), timestamp('1900-01-01')) from {{ this }})
{% endif %}
