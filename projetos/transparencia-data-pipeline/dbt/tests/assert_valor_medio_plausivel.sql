-- Teste singular: valor médio por beneficiário fora de uma faixa plausível indica erro de carga.
select *
from {{ ref('fct_bolsa_familia_mensal') }}
where valor_medio_por_beneficiario not between 50 and 5000
