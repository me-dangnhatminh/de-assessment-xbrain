WITH service_counts AS (
    SELECT
        service,
        COUNT(*) AS error_count
    FROM read_parquet(?)
    WHERE level = 'ERROR'
    GROUP BY service
)
SELECT
    ROW_NUMBER() OVER (ORDER BY error_count DESC, service ASC) AS rank,
    service,
    error_count
FROM service_counts
ORDER BY error_count DESC, service ASC;
