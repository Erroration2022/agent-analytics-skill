-- CTE: errors
-- Extracts error events using the canonical BQAA predicate (matches SDK
-- event_semantics.ERROR_SQL_PREDICATE). Catches TOOL_ERROR / LLM_ERROR rows
-- even when status = 'OK', plus rows with populated error_message.
-- Use this CTE as a starting point for any error investigation.

WITH errors AS (
  SELECT
    timestamp,
    event_type,
    agent,
    session_id,
    invocation_id,
    user_id,
    trace_id,
    span_id,
    content,
    attributes,
    latency_ms,
    error_message
  FROM `{PROJECT}.{DATASET}.{TABLE}`
  WHERE (
    ENDS_WITH(event_type, '_ERROR')
    OR error_message IS NOT NULL
    OR status = 'ERROR'
  )
    AND timestamp BETWEEN @start AND @end
)
