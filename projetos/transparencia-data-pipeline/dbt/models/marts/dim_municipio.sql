-- TODO etapa 4: enriquecer com população e região (seed do IBGE em dbt/seeds).
select distinct
    cod_municipio_ibge,
    nome_municipio,
    uf
from {{ ref('int_bolsa_familia_mensal') }}
