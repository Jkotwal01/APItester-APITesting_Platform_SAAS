import json

from aitester.reports.metrics import calculate_metrics


def generate_json_report(run_data: dict) -> str:
    """
    Generates a JSON string representing the test run report.
    """
    metrics = calculate_metrics(run_data.get("results", []))

    report = {
        "meta": {
            "project_name": run_data.get("project_name", "Unknown Project"),
            "run_id": run_data.get("run_id"),
            "started_at": run_data.get("started_at"),
            "completed_at": run_data.get("completed_at"),
            "duration_ms": run_data.get("duration_ms"),
        },
        "summary": {
            "metrics": metrics,
            "security_score": run_data.get("security_score"),
            "ai_executive_summary": run_data.get("ai_executive_summary"),
        },
        "test_results": run_data.get("results", []),
        "security_findings": run_data.get("security_findings", []),
    }

    return json.dumps(report, indent=2)
