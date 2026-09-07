"""Guard against reading $.model from LLM_RESPONSE rows (SDK stores model_version)."""

from pathlib import Path
import re
import unittest

REPO_ROOT = Path(__file__).resolve().parents[1]
SQL_PATHS = [
    REPO_ROOT / "ctes" / "base_llm_responses.sql",
    REPO_ROOT / "queries" / "latency_analysis.sql",
    REPO_ROOT / "queries" / "token_usage_trends.sql",
    REPO_ROOT / "queries" / "session_cost_estimate.sql",
    REPO_ROOT / "queries" / "model_comparison.sql",
]

BAD_PATTERN = re.compile(
    r"JSON_VALUE\(attributes,\s*'\$\.model'\)\s+AS\s+model_id",
    re.IGNORECASE,
)
GOOD_PATTERN = re.compile(
    r"COALESCE\(\s*JSON_VALUE\(attributes,\s*'\$\.model_version'\)",
    re.IGNORECASE,
)


class ModelIdSqlTests(unittest.TestCase):
    def test_llm_response_queries_use_model_version_for_model_id(self):
        for path in SQL_PATHS:
            sql = path.read_text(encoding="utf-8")
            self.assertIn("LLM_RESPONSE", sql, path.name)
            self.assertIsNone(
                BAD_PATTERN.search(sql),
                f"{path.name} reads $.model from LLM_RESPONSE rows",
            )
            self.assertIsNotNone(
                GOOD_PATTERN.search(sql),
                f"{path.name} should COALESCE model_version and model",
            )


if __name__ == "__main__":
    unittest.main()