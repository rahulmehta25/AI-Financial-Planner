{{
  config(
    materialized='ephemeral',
    description='Staging model for raw transaction data with cleaning and standardization'
  )
}}

WITH source_data AS (
    SELECT *
    FROM {{ source('raw', 'transactions') }}
    WHERE created_at >= '{{ var("start_date") }}'
      AND created_at <= CURRENT_TIMESTAMP
),

cleaned_transactions AS (
    SELECT
        -- Primary identifiers
        transaction_id,
        account_id,
        user_id,
        
        -- Dates and times
        CAST(transaction_date AS DATE) AS transaction_date,
        CAST(posted_date AS DATE) AS posted_date,
        CAST(authorized_date AS DATE) AS authorized_date,
        EXTRACT(HOUR FROM transaction_timestamp) * 3600 + 
        EXTRACT(MINUTE FROM transaction_timestamp) * 60 + 
        EXTRACT(SECOND FROM transaction_timestamp) AS time_seconds,
        
        -- Amounts and currency
        CAST(amount AS DECIMAL(15,2)) AS amount,
        COALESCE(UPPER(TRIM(currency)), 'USD') AS currency,
        CASE 
            WHEN amount > 0 THEN FALSE 
            ELSE TRUE 
        END AS is_debit,
        CASE 
            WHEN amount > 0 THEN TRUE 
            ELSE FALSE 
        END AS is_credit,
        ABS(amount) AS absolute_amount,
        
        -- Transaction details
        UPPER(TRIM(transaction_type)) AS transaction_type,
        TRIM(description) AS description,
        TRIM(merchant_name) AS merchant_name,
        COALESCE(TRIM(reference_number), '') AS reference_number,
        
        -- Categories
        COALESCE(TRIM(category), 'Other') AS category,
        COALESCE(TRIM(subcategory), 'Other') AS subcategory,
        
        -- Location data
        TRIM(location_city) AS location_city,
        TRIM(location_state) AS location_state,
        COALESCE(UPPER(TRIM(location_country)), 'US') AS location_country,
        CAST(location_latitude AS DECIMAL(10,8)) AS location_latitude,
        CAST(location_longitude AS DECIMAL(11,8)) AS location_longitude,
        
        -- Flags and status
        COALESCE(is_pending, FALSE) AS is_pending,
        COALESCE(is_transfer, FALSE) AS is_transfer,
        COALESCE(is_recurring, FALSE) AS is_recurring,
        COALESCE(is_disputed, FALSE) AS is_disputed,
        COALESCE(UPPER(TRIM(status)), 'PENDING') AS status,
        COALESCE(UPPER(TRIM(payment_method)), 'UNKNOWN') AS payment_method,
        
        -- Data quality and source
        COALESCE(data_source, 'unknown') AS data_source,
        COALESCE(confidence_score, 1.0) AS confidence_score,
        CASE 
            WHEN amount IS NULL OR transaction_date IS NULL OR account_id IS NULL 
            THEN 0.5
            WHEN description IS NULL OR description = '' 
            THEN 0.8
            ELSE 1.0
        END AS data_quality_score,
        
        -- Derived fields for categorization
        CASE 
            WHEN LOWER(description) LIKE '%salary%' OR LOWER(description) LIKE '%payroll%' 
            THEN TRUE 
            ELSE FALSE 
        END AS is_salary,
        
        CASE 
            WHEN LOWER(description) LIKE '%dividend%' OR LOWER(description) LIKE '%interest%' 
            THEN TRUE 
            ELSE FALSE 
        END AS is_investment_income,
        
        CASE 
            WHEN LOWER(merchant_name) LIKE '%grocery%' OR LOWER(merchant_name) LIKE '%supermarket%'
                OR LOWER(description) LIKE '%grocery%' OR LOWER(description) LIKE '%food%'
            THEN 'Food & Dining'
            WHEN LOWER(merchant_name) LIKE '%gas%' OR LOWER(merchant_name) LIKE '%fuel%'
                OR LOWER(merchant_name) LIKE '%exxon%' OR LOWER(merchant_name) LIKE '%shell%'
            THEN 'Transportation'
            WHEN LOWER(merchant_name) LIKE '%amazon%' OR LOWER(merchant_name) LIKE '%walmart%'
                OR LOWER(merchant_name) LIKE '%target%'
            THEN 'Shopping'
            WHEN LOWER(merchant_name) LIKE '%netflix%' OR LOWER(merchant_name) LIKE '%spotify%'
                OR LOWER(merchant_name) LIKE '%hulu%'
            THEN 'Entertainment'
            WHEN LOWER(merchant_name) LIKE '%electric%' OR LOWER(merchant_name) LIKE '%water%'
                OR LOWER(merchant_name) LIKE '%cable%' OR LOWER(merchant_name) LIKE '%phone%'
            THEN 'Utilities'
            WHEN LOWER(merchant_name) LIKE '%mortgage%' OR LOWER(merchant_name) LIKE '%rent%'
            THEN 'Housing'
            WHEN LOWER(merchant_name) LIKE '%insurance%'
            THEN 'Insurance'
            WHEN LOWER(merchant_name) LIKE '%doctor%' OR LOWER(merchant_name) LIKE '%hospital%'
                OR LOWER(merchant_name) LIKE '%pharmacy%' OR LOWER(merchant_name) LIKE '%medical%'
            THEN 'Healthcare'
            ELSE COALESCE(category, 'Other')
        END AS derived_category,
        
        -- Spending pattern indicators
        CASE 
            WHEN ABS(amount) > 1000 THEN 'HIGH_VALUE'
            WHEN ABS(amount) > 100 THEN 'MEDIUM_VALUE'
            WHEN ABS(amount) > 10 THEN 'LOW_VALUE'
            ELSE 'MICRO_TRANSACTION'
        END AS amount_category,
        
        -- Time pattern indicators
        CASE 
            WHEN EXTRACT(HOUR FROM transaction_timestamp) BETWEEN 9 AND 17 THEN 'BUSINESS_HOURS'
            WHEN EXTRACT(HOUR FROM transaction_timestamp) BETWEEN 18 AND 22 THEN 'EVENING'
            WHEN EXTRACT(HOUR FROM transaction_timestamp) BETWEEN 6 AND 8 THEN 'MORNING'
            ELSE 'OFF_HOURS'
        END AS time_pattern,
        
        CASE 
            WHEN EXTRACT(DOW FROM transaction_date) IN (0, 6) THEN 'WEEKEND'
            ELSE 'WEEKDAY'
        END AS day_pattern,
        
        -- Metadata
        created_at AS source_created_at,
        CURRENT_TIMESTAMP AS processed_at
        
    FROM source_data
    WHERE transaction_id IS NOT NULL
      AND account_id IS NOT NULL
      AND transaction_date IS NOT NULL
),

-- Add business rules and validations
validated_transactions AS (
    SELECT *,
        -- Data quality validations
        CASE 
            WHEN data_quality_score < {{ var('completeness_threshold') }} THEN 'POOR'
            WHEN data_quality_score < {{ var('accuracy_threshold') }} THEN 'FAIR'
            ELSE 'GOOD'
        END AS quality_tier,
        
        -- Business rule validations
        CASE 
            WHEN ABS(amount) > 100000 THEN 'LARGE_TRANSACTION'
            WHEN is_pending AND (CURRENT_DATE - transaction_date) > 5 THEN 'STALE_PENDING'
            WHEN is_transfer AND merchant_name IS NOT NULL THEN 'INVALID_TRANSFER'
            ELSE 'VALID'
        END AS validation_status,
        
        -- Fraud indicators
        CASE 
            WHEN ABS(amount) > 5000 
                AND time_pattern = 'OFF_HOURS' 
                AND location_country != 'US' 
            THEN 0.8
            WHEN ABS(amount) > 2000 AND time_pattern = 'OFF_HOURS' 
            THEN 0.6
            WHEN location_country != 'US' AND ABS(amount) > 500 
            THEN 0.4
            ELSE 0.1
        END AS fraud_risk_score
        
    FROM cleaned_transactions
),

-- Final output with row numbering for deduplication
final AS (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY transaction_id, account_id 
            ORDER BY source_created_at DESC, confidence_score DESC
        ) AS row_num
    FROM validated_transactions
)

SELECT *
FROM final
WHERE row_num = 1  -- Deduplicate based on latest/highest confidence record
  AND validation_status != 'INVALID_TRANSFER'  -- Filter out invalid records
  AND quality_tier != 'POOR'  -- Filter out poor quality records

-- Data quality tests will be defined separately in schema.yml