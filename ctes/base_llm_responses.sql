-- CTE: llm_responses
-- Flattens LLM_RESPONSE events from the agent_events table.
-- Extracts token counts, latency, model info from nested JSON fields.
-- ALWAYS use this CTE for token usage, latency, and model analysis.

WITH llm_responses AS (
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
    CAST(COALESCE(
      CAST(JSON_VALUE(attributes, '$.usage_metadata.prompt_token_count') AS INT64),
      CAST(JSON_VALUE(attributes, '$.usage_metadata.prompt_tokens') AS INT64),
      CAST(JSON_VALUE(content, '$.usage.prompt') AS INT64),
      CAST(JSON_VALUE(attributes, '$.input_tokens') AS INT64)
    ) AS INT64)   AS prompt_tokens,
    CAST(COALESCE(
      CAST(JSON_VALUE(attributes, '$.usage_metadata.candidates_token_count') AS INT64),
      CAST(JSON_VALUE(attributes, '$.usage_metadata.completion_tokens') AS INT64),
      CAST(JSON_VALUE(content, '$.usage.completion') AS INT64),
      CAST(JSON_VALUE(attributes, '$.output_tokens') AS INT64)
    ) AS INT64)   AS completion_tokens,
    CAST(COALESCE(
      CAST(JSON_VALUE(attributes, '$.usage_metadata.total_token_count') AS INT64),
      CAST(JSON_VALUE(attributes, '$.usage_metadata.total_tokens') AS INT64),
      CAST(JSON_VALUE(content, '$.usage.total') AS INT64),
      COALESCE(
        CAST(JSON_VALUE(attributes, '$.input_tokens') AS INT64), 0
      ) + COALESCE(
        CAST(JSON_VALUE(attributes, '$.output_tokens') AS INT64), 0
      )
    ) AS INT64)   AS total_tokens,
    CAST(JSON_VALUE(latency_ms, '$.total_ms')                          AS FLOAT64) AS total_latency_ms,
    CAST(JSON_VALUE(latency_ms, '$.time_to_first_token_ms')            AS FLOAT64) AS ttft_ms,
    status,
    error_message
  FROM `{PROJECT}.{DATASET}.{TABLE}`
  WHERE event_type = 'LLM_RESPONSE'
    AND timestamp BETWEEN @start AND @end
)
