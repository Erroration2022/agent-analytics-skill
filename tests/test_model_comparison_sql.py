"""Static checks for model comparison query semantics."""

from pathlib import Path


def test_model_comparison_includes_llm_error_events():
    sql = Path("queries/model_comparison.sql").read_text()
    assert "LLM_ERROR" in sql
    assert "event_type IN ('LLM_RESPONSE', 'LLM_ERROR')" in sql
    assert "event_type = 'LLM_ERROR' OR status = 'ERROR'" in sql
