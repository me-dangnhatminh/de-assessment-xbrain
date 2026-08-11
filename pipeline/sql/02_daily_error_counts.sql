WITH date_window AS (
    SELECT generate_series::DATE AS event_date_utc
    FROM generate_series(DATE '2026-07-27', DATE '2026-08-02', INTERVAL 1 DAY)
),
cleaned_errors AS (
    SELECT
        event_date_utc,
        service
    FROM read_parquet(?)
    WHERE level = 'ERROR'
),
daily_error_counts AS (
    SELECT
        event_date_utc,
        COUNT(*) AS daily_error_count
    FROM cleaned_errors
    GROUP BY event_date_utc
),
daily_service_counts AS (
    SELECT
        event_date_utc,
        service,
        COUNT(*) AS service_error_count
    FROM cleaned_errors
    GROUP BY event_date_utc, service
),
daily_window AS (
    SELECT
        date_window.event_date_utc,
        COALESCE(daily_error_counts.daily_error_count, 0) AS daily_error_count
    FROM date_window
    LEFT JOIN daily_error_counts USING (event_date_utc)
),
scored_days AS (
    SELECT
        event_date_utc,
        daily_error_count,
        MEDIAN(daily_error_count) OVER () AS median_error_count
    FROM daily_window
),
service_contributions AS (
    SELECT
        event_date_utc,
        STRING_AGG(service || ':' || service_error_count::VARCHAR, ';' ORDER BY service)
            AS service_contributions
    FROM daily_service_counts
    GROUP BY event_date_utc
)
SELECT
    scored_days.event_date_utc,
    scored_days.daily_error_count,
    scored_days.median_error_count,
    scored_days.daily_error_count::DOUBLE / NULLIF(scored_days.median_error_count, 0)
        AS error_count_to_median_ratio,
    scored_days.daily_error_count > 2 * scored_days.median_error_count
        AS is_unusual_by_2x_median_rule,
    CASE
        WHEN scored_days.daily_error_count > 2 * scored_days.median_error_count
        THEN COALESCE(service_contributions.service_contributions, '')
        ELSE ''
    END AS service_contributions
FROM scored_days
LEFT JOIN service_contributions USING (event_date_utc)
ORDER BY scored_days.event_date_utc ASC;
