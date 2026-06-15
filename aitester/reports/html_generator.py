import os

from jinja2 import Environment, FileSystemLoader

from aitester.reports.metrics import calculate_metrics


def generate_html_report(run_data: dict) -> str:
    """
    Generates an HTML string representing the test run report.
    """
    metrics = calculate_metrics(run_data.get("results", []))

    # Setup Jinja2 environment pointing to the templates directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    templates_dir = os.path.join(current_dir, "templates")
    env = Environment(loader=FileSystemLoader(templates_dir))

    template = env.get_template("report.html.j2")

    # Render template with data
    html = template.render(
        project_name=run_data.get("project_name", "Unknown Project"),
        run_id=run_data.get("run_id"),
        started_at=run_data.get("started_at"),
        duration_ms=run_data.get("duration_ms"),
        metrics=metrics,
        security_score=run_data.get("security_score"),
        ai_executive_summary=run_data.get("ai_executive_summary"),
        results=run_data.get("results", []),
        security_findings=run_data.get("security_findings", [])
    )

    return html
