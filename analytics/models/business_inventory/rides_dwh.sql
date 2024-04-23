{{
    config(
        materialized='incremental', 
        unique_key='ride_id',
        incremental_strategy='insert_overwrite',
        partition_by = {
            'field': 'time_ride_start',
            'data_type': 'timestamp',
            'granularity': 'day'
        }
    )
}}

SELECT DISTINCT ride_id,
                vehicle_id,
                vehicle_type,
                time_ride_start,
                time_ride_end,
                lng_start,
                lat_start,
                lat_end,
                lng_end,
                gross_amount,
                pass_purchase_id,
                city_name 
    FROM   {{ source('dott_raw_layer','rides_raw') }}