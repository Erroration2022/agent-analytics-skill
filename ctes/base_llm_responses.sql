-- CTE: llm_responses
-- Flattens LLM_RESPONSE events from the agent_events table.
-- Deduplicates streaming partial chunks: the ADK plugin logs one LLM_RESPONSE
-- per streaming chunk (shared span_id); keep the final chunk (latest timestamp)
-- which carries usage tokens and total latency.
-- ALWAYS use this CTE for token usage, latency, and model analysis.

WITH raw_llm_responses AS (
  SELECT
    timestamp,
    agent,
    session_id,
    invocation_id,
    user_id,
    trace_id,
    span_id,
    parent_span_id,
    JSON_VALUE(content, '$.response')                                       AS response_text,
    JSON_VALUE(attributes, '$.model')                                       AS model_id,
    CAST(JSON_VALUE(attributes, '$.usage_metadata.prompt_tokens')      AS INT64)   AS prompt_tokens,
    CAST(JSON_VALUE(attributes, '$.usage_metadata.completion_tokens')  AS INT64)   AS completion_tokens,
    CAST(JSON_VALUE(attributes, '$.usage_metadata.total_tokens')       AS INT64)   AS total_tokens,
    CAST(JSON_VALUE(latency_ms, '$.total_ms')                          AS FLOAT64) AS total_latency_ms,
    CAST(JSON_VALUE(latency_ms, '$.time_to_first_token_ms')            AS FLOAT64) AS ttft_ms,
    status,
    error_message
  FROM `{PROJECT}.{DATASET}.{TABLE}`
  WHERE event_type = 'LLM_RESPONSE'
    AND timestamp BETWEEN @start AND @end
),
llm_responses AS (
  SELECT * EXCEPT(row_num)
  FROM (
    SELECT
      *,
      ROW_NUMBER() OVER (
        PARTITION BY session_id, invocation_id, COALESCE(span_id, '')
        ORDER BY timestamp DESC
      ) AS row_num
    FROM raw_llm_responses
  )
  WHERE row_num = 1
)
