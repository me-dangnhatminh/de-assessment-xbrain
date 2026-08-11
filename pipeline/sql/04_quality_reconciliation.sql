WITH ledger AS (
    SELECT
        source_line,
        final_action,
        issues
    FROM read_json(?)
),
action_categories AS (
    SELECT UNNEST(['ACCEPT', 'REPAIR', 'REJECT']) AS final_action
),
record_totals AS (
    SELECT
        'record_total' AS metric_type,
        NULL::VARCHAR AS issue_code,
        action_categories.final_action,
        COUNT(ledger.source_line) AS record_count,
        NULL::BIGINT AS issue_occurrences,
        NULL::BOOLEAN AS is_reconciled,
        1 AS metric_order,
        CASE action_categories.final_action
            WHEN 'ACCEPT' THEN 1
            WHEN 'REPAIR' THEN 2
            WHEN 'REJECT' THEN 3
        END AS detail_order
    FROM action_categories
    LEFT JOIN ledger USING (final_action)
    GROUP BY action_categories.final_action
),
issue_occurrences AS (
    SELECT
        'issue_occurrence' AS metric_type,
        issue.issue_code,
        issue.action AS final_action,
        COUNT(DISTINCT ledger.source_line) AS record_count,
        COUNT(*) AS issue_occurrences,
        NULL::BOOLEAN AS is_reconciled,
        2 AS metric_order,
        0 AS detail_order
    FROM ledger
    CROSS JOIN UNNEST(ledger.issues) AS entry(issue)
    GROUP BY issue.issue_code, issue.action
),
ledger_counts AS (
    SELECT
        COUNT(*) AS input_lines,
        COUNT(*) FILTER (WHERE final_action = 'ACCEPT') AS accepted_records,
        COUNT(*) FILTER (WHERE final_action = 'REPAIR') AS repaired_records,
        COUNT(*) FILTER (WHERE final_action = 'REJECT') AS rejected_records
    FROM ledger
),
parquet_counts AS (
    SELECT COUNT(*) AS analytical_rows
    FROM read_parquet(?)
),
conservation AS (
    SELECT
        'conservation' AS metric_type,
        NULL::VARCHAR AS issue_code,
        'INPUT_EQUALS_ACTIONS' AS final_action,
        input_lines AS record_count,
        accepted_records + repaired_records + rejected_records AS issue_occurrences,
        input_lines = accepted_records + repaired_records + rejected_records AS is_reconciled,
        3 AS metric_order,
        1 AS detail_order
    FROM ledger_counts
    UNION ALL
    SELECT
        'conservation' AS metric_type,
        NULL::VARCHAR AS issue_code,
        'ANALYTICAL_EQUALS_PARQUET' AS final_action,
        accepted_records + repaired_records AS record_count,
        analytical_rows AS issue_occurrences,
        accepted_records + repaired_records = analytical_rows AS is_reconciled,
        3 AS metric_order,
        2 AS detail_order
    FROM ledger_counts
    CROSS JOIN parquet_counts
),
all_metrics AS (
    SELECT * FROM record_totals
    UNION ALL
    SELECT * FROM issue_occurrences
    UNION ALL
    SELECT * FROM conservation
)
SELECT
    metric_type,
    issue_code,
    final_action,
    record_count,
    issue_occurrences,
    is_reconciled
FROM all_metrics
ORDER BY metric_order, detail_order, issue_code ASC NULLS FIRST, final_action ASC;
