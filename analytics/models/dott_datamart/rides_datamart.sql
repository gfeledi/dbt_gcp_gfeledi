{{
    config(
        materialized='incremental', 
        unique_key='ride_id',
        incremental_strategy='insert_overwrite',
        partition_by = {
            'field': 'ride_day',
            'data_type': 'date',
            'granularity': 'day'
        }
    )
}}

WITH pass_per_ride AS (
SELECT DISTINCT pass_purchase_id, count(ride_id) rides_per_pass FROM {{ ref('rides_dwh') }} WHERE pass_purchase_id is not null GROUP by 1  
),

ride_extract AS (
SELECT `ride_id`, EXTRACT(DATE FROM TIMESTAMP(time_ride_start))  ride_day, EXTRACT(HOUR FROM TIMESTAMP(time_ride_start))  ride_hour, TIMESTAMP_DIFF(`time_ride_end`,`time_ride_start`, MINUTE) ride_mins,  `gross_amount` amount_ride,`vehicle_type` ,`city_name`, `pass_purchase_id`
FROM  {{ ref('rides_dwh') }}
),

pass_amounts AS (
SELECT pass_purchase_id, gross_amount pass_amount FROM  {{ ref('pass_purchases_dwh') }}
)

SELECT ride_id, ride_day, ride_hour, vehicle_type, city_name, ride_mins, amount_ride, CASE WHEN pass_purchase_id is null THEN 0 ELSE pass_amount/rides_per_pass END  amount_pass
FROM ride_extract
LEFT JOIN pass_per_ride USING(pass_purchase_id)
LEFT JOIN pass_amounts USING(pass_purchase_id)