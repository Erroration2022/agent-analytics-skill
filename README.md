# BigQuery Agent Analytics Skill

A lightweight, LLM-discoverable skill for analyzing [Google ADK BigQuery Agent Analytics](https://adk.dev/integrations/bigquery-agent-analytics/) data. No server, no MCP — just a prompt skill file with pre-built CTEs, query templates, and an analysis methodology that any AI coding assistant can use.

## What This Does

When loaded into an AI assistant (Claude Code, Cursor, AG, etc.), this skill teaches the LLM to:

- Query the `agent_events` table correctly, using pre-built CTEs that handle deeply nested JSON/proto structures
- Follow a structured analysis methodology: **Survey → Filter → Deep Dive**
- Diagnose common failure patterns from known signal tables
- Estimate costs, detect delegation loops, find HITL bottlenecks, and compare model performance

## Quick Start

### 1. Set up your environment

```bash
export GCP_PROJECT_ID="your-project-id"
export BQ_DATASET="your-dataset-id"
pip install google-cloud-bigquery
```

### 2. Install in your AI assistant

**Claude Code:**
Reference this repo in your project's `CLAUDE.md`:
```markdown
For agent analytics, follow the skill at: path/to/agent-analytics-skill/skill.md
```
Or copy `skill.md` into `.claude/skills/`.

**Cursor:**
Reference in `.cursorrules` or project rules:
```
@agent-analytics-skill/skill.md
```

**Other agents:**
Include `skill.md` as system/project context.

### 3. Ask questions

```
"What's the error rate for my agents this week?"
"Which tool has the highest failure rate?"
"Compare latency across models for the last 30 days"
"Show me the most expensive sessions"
"Are there any agent delegation loops?"
```

## Repo Structure

```
agent-analytics-skill/
├── skill.md              # The complete skill (schema, CTEs, methodology, patterns)
├── ctes/                 # Base CTEs — never write raw JSON extraction
│   ├── base_llm_responses.sql
│   ├── base_tool_calls.sql
│   ├── base_errors.sql
│   ├── base_sessions.sql
│   └── base_agent_tree.sql
├── queries/              # Ready-to-run analytics queries
│   ├── trace_reconstruction.sql
│   ├── latency_analysis.sql
│   ├── token_usage_trends.sql
│   ├── tool_failure_rates.sql
│   ├── agent_delegation_map.sql
│   ├── hitl_bottlenecks.sql
│   ├── model_comparison.sql
│   └── session_cost_estimate.sql
├── scripts/
│   └── run_bq.py         # Lightweight query executor with safety limits
└── README.md
```

## How It Works

```
User asks question
       │
       ▼
AI client loads skill.md as context
       │
       ▼
LLM uses pre-built CTEs (never writes raw JSON extraction)
       │
       ▼
LLM follows methodology: Survey → Filter → Deep Dive
       │
       ▼
Query executed via scripts/run_bq.py ──► BigQuery
       │
       ▼
LLM interprets results using failure pattern table
       │
       ▼
User gets formatted analysis + recommended next action
```

## Configuration

| Environment Variable | Description | Required |
|---------------------|-------------|----------|
| `GCP_PROJECT_ID` | Your GCP project ID | Yes |
| `BQ_DATASET` | BigQuery dataset containing `agent_events` | Yes |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to service account JSON (if not using ADC) | No |

## Schema

This skill targets the `agent_events` table created by the [ADK BigQuery Agent Analytics plugin](https://adk.dev/integrations/bigquery-agent-analytics/#schema-reference). See `skill.md` Section 2 for the full schema reference embedded in the skill.

## License

MIT
