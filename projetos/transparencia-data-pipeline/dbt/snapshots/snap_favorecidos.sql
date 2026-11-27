-- SCD tipo 2 (etapa 4): ative quando o modelo de despesas/favorecidos existir.
{% snapshot snap_favorecidos %}
{{ config(enabled=false, target_schema='snapshots', unique_key='cod_favorecido',
          strategy='check', check_cols=['nome_favorecido', 'uf', 'natureza_juridica']) }}
select * from {{ ref('stg_favorecidos') }}
{% endsnapshot %}
