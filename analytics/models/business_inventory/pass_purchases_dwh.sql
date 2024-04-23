{{
    config(
        materialized='incremental', 
        unique_key='pass_purchase_id',
        incremental_strategy='insert_overwrite',
        partition_by = {
            'field': 'time_purchase',
            'data_type': 'timestamp',
            'granularity': 'day'
        }
    )
}}

SELECT DISTINCT pass_purchase_id,
                time_purchase,
                gross_amount
    FROM   {{ source('dott_raw_layer','pass_purchases_raw') }}
