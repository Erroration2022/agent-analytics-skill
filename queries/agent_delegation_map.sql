-- Agent Delegation Map
-- Shows which agents delegate to which other agents and how often.
-- Detects runaway delegation loops (A -> B -> A).
-- Requires: base_agent_tree CTE.

WITH agent_starts AS (
  SELECT
    trace_id,
    span_id,
    agent,
    parent_span_id
  FROM `{PROJECT}.{DATASET}.{TABLE}`
  WHERE event_type = 'AGENT_STARTING'
    AND timestamp BETWEEN @start AND @end
    AND agent IS NOT NULL
    AND parent_span_id IS NOT NULL
),
span_agents AS (
  SELECT
    trace_id,
    span_id,
    ANY_VALUE(agent) AS agent
  FROM `{PROJECT}.{DATASET}.{TABLE}`
  WHERE timestamp BETWEEN @start AND @end
    AND span_id IS NOT NULL
    AND agent IS NOT NULL
  GROUP BY trace_id, span_id
),
agent_tree AS (
  SELECT
    child.trace_id,
    child.agent   AS child_agent,
    parent.agent  AS parent_agent
  FROM agent_starts child
  INNER JOIN span_agents parent
    ON  child.parent_span_id = parent.span_id
    AND child.trace_id       = parent.trace_id
  WHERE child.agent != parent.agent
)
SELECT
  parent_agent,
  child_agent,
  COUNT(*)                 AS delegation_count,
  COUNT(DISTINCT trace_id) AS unique_traces
FROM agent_tree
GROUP BY parent_agent, child_agent
ORDER BY delegation_count DESC;
