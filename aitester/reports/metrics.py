def calculate_metrics(results: list[dict], endpoints: list[dict] | None = None) -> dict:
    total = len(results)
    passed = sum(1 for r in results if r.get("status") == "passed")
    failed = sum(1 for r in results if r.get("status") == "failed")
    error = sum(1 for r in results if r.get("status") == "error")

    pass_rate = (passed / total * 100) if total > 0 else 0.0

    valid_response_times: list[float] = [float(r["response_time_ms"]) for r in results if r.get("response_time_ms") is not None]
    avg_response_time_ms = (sum(valid_response_times) / len(valid_response_times)) if valid_response_times else 0.0

    by_category = {}
    for r in results:
        cat = r.get("category", "unknown")
        if cat not in by_category:
            by_category[cat] = {"total": 0, "passed": 0, "failed": 0, "error": 0}
        by_category[cat]["total"] += 1
        status = r.get("status", "error")
        if status in by_category[cat]:
            by_category[cat][status] += 1

    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "error": error,
        "pass_rate": pass_rate,
        "avg_response_time_ms": avg_response_time_ms,
        "by_category": by_category,
    }
