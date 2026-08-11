WITH cleaned_errors AS (
    SELECT
        error_type,
        service
    FROM read_parquet(?)
    WHERE level = 'ERROR'
),
primary_counts AS (
    SELECT
        error_type,
        COUNT(*) AS error_count
    FROM cleaned_errors
    GROUP BY error_type
),
service_counts AS (
    SELECT
        error_type,
        service,
        COUNT(*) AS service_error_count
    FROM cleaned_errors
    GROUP BY error_type, service
),
service_contributions AS (
    SELECT
        error_type,
        '{' || STRING_AGG(
            TO_JSON(service) || ':' || service_error_count::VARCHAR,
            ',' ORDER BY service
        ) || '}' AS service_contributions_json
    FROM service_counts
    GROUP BY error_type
),
ranked_error_types AS (
    SELECT
        ROW_NUMBER() OVER (ORDER BY error_count DESC, error_type ASC) AS rank,
        error_type,
        error_count
    FROM primary_counts
    ORDER BY error_count DESC, error_type ASC
    LIMIT 3
),
unclassified AS (
    SELECT COALESCE(error_count, 0) AS unclassified_error_count
    FROM primary_counts
    WHERE error_type = 'UNCLASSIFIED_ERROR'
    UNION ALL
    SELECT 0
    WHERE NOT EXISTS (
        SELECT 1 FROM primary_counts WHERE error_type = 'UNCLASSIFIED_ERROR'
    )
)
SELECT
    ranked_error_types.rank,
    ranked_error_types.error_type,
    ranked_error_types.error_count,
    service_contributions.service_contributions_json,
    unclassified.unclassified_error_count
FROM ranked_error_types
JOIN service_contributions USING (error_type)
CROSS JOIN unclassified
ORDER BY ranked_error_types.error_count DESC, ranked_error_types.error_type ASC;
