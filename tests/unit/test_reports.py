import pytest
import json
from datetime import datetime, timezone
from aitester.reports.metrics import calculate_metrics
from aitester.reports.json_generator import generate_json_report
from aitester.reports.html_generator import generate_html_report

@pytest.fixture
def sample_run_data():
    return {
        "project_name": "Test API",
        "run_id": "test-run-123",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "duration_ms": 5000,
        "results": [
            {"test_case_name": "T1", "category": "functional", "status": "passed",
             "method": "GET", "path": "/users", "actual_status_code": 200,
             "response_time_ms": 120, "ai_analysis": None, "security_finding": None},
            {"test_case_name": "T2", "category": "functional", "status": "failed",
             "method": "POST", "path": "/users", "actual_status_code": 500,
             "response_time_ms": 340, "ai_analysis": "Server error occurred",
             "security_finding": None},
            {"test_case_name": "T3", "category": "security", "status": "passed",
             "method": "GET", "path": "/users", "actual_status_code": 400,
             "response_time_ms": 89, "ai_analysis": None,
             "security_finding": {"type": "sqli", "severity": "high"}},
        ],
        "security_score": 74.5,
        "security_findings": [],
        "ai_executive_summary": "2 of 3 tests passed."
    }

class TestMetrics:
    def test_pass_rate_calculated(self, sample_run_data):
        metrics = calculate_metrics(sample_run_data["results"])
        assert metrics["pass_rate"] == pytest.approx(66.66, rel=0.01) # 2 passed out of 3

    def test_total_count_correct(self, sample_run_data):
        metrics = calculate_metrics(sample_run_data["results"])
        assert metrics["total"] == 3
        assert metrics["passed"] == 2
        assert metrics["failed"] == 1

    def test_avg_response_time_calculated(self, sample_run_data):
        metrics = calculate_metrics(sample_run_data["results"])
        assert metrics["avg_response_time_ms"] > 0

    def test_category_breakdown(self, sample_run_data):
        metrics = calculate_metrics(sample_run_data["results"])
        assert "functional" in metrics["by_category"]
        assert "security" in metrics["by_category"]

class TestJSONReport:
    def test_json_report_is_valid_json(self, sample_run_data):
        output = generate_json_report(sample_run_data)
        parsed = json.loads(output)
        assert isinstance(parsed, dict)

    def test_json_report_has_required_keys(self, sample_run_data):
        output = generate_json_report(sample_run_data)
        parsed = json.loads(output)
        assert "meta" in parsed
        assert "summary" in parsed
        assert "test_results" in parsed

    def test_json_report_result_count_correct(self, sample_run_data):
        output = generate_json_report(sample_run_data)
        parsed = json.loads(output)
        assert len(parsed["test_results"]) == 3

class TestHTMLReport:
    def test_html_report_is_string(self, sample_run_data):
        html = generate_html_report(sample_run_data)
        assert isinstance(html, str)
        assert len(html) > 100

    def test_html_report_has_doctype(self, sample_run_data):
        html = generate_html_report(sample_run_data)
        assert "<!DOCTYPE html>" in html

    def test_html_report_contains_project_name(self, sample_run_data):
        html = generate_html_report(sample_run_data)
        assert "Test API" in html

    def test_html_report_contains_pass_rate(self, sample_run_data):
        html = generate_html_report(sample_run_data)
        assert "66" in html  # 66.66% pass rate

    def test_html_report_contains_security_score(self, sample_run_data):
        html = generate_html_report(sample_run_data)
        assert "74" in html  # security score 74.5

    def test_html_report_contains_ai_summary(self, sample_run_data):
        html = generate_html_report(sample_run_data)
        assert "2 of 3 tests passed" in html
