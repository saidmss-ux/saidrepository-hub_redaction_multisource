from collections import defaultdict

_REQUEST_DURATION_BUCKETS = [50, 100, 250, 500, 1000, 2500, 5000]

metrics = {
    "request_total": 0,
    "request_duration_ms_bucket": defaultdict(int),
    "error_code_total": defaultdict(int),
    "extract_duration_ms_sum": 0,
    "extract_duration_count": 0,
    "batch_size_sum": 0,
    "batch_count": 0,
}


def observe_request(duration_ms: int) -> None:
    metrics["request_total"] += 1
    bucket = "+Inf"
    for bound in _REQUEST_DURATION_BUCKETS:
        if duration_ms <= bound:
            bucket = str(bound)
            break
    metrics["request_duration_ms_bucket"][bucket] += 1


def observe_extract(duration_ms: int) -> None:
    metrics["extract_duration_ms_sum"] += duration_ms
    metrics["extract_duration_count"] += 1


def observe_batch_size(size: int) -> None:
    metrics["batch_size_sum"] += size
    metrics["batch_count"] += 1


def inc_error_code(code: str) -> None:
    metrics["error_code_total"][code] += 1


def render_prometheus() -> str:
    lines: list[str] = []
    lines.append("# TYPE docuhub_request_total counter")
    lines.append(f"docuhub_request_total {metrics['request_total']}")

    lines.append("# TYPE docuhub_request_duration_ms_bucket counter")
    for bucket, value in metrics["request_duration_ms_bucket"].items():
        lines.append(f'docuhub_request_duration_ms_bucket{{le="{bucket}"}} {value}')

    lines.append("# TYPE docuhub_error_code_total counter")
    for code, value in metrics["error_code_total"].items():
        lines.append(f'docuhub_error_code_total{{code="{code}"}} {value}')

    lines.append("# TYPE docuhub_extract_duration_ms_sum counter")
    lines.append(f"docuhub_extract_duration_ms_sum {metrics['extract_duration_ms_sum']}")
    lines.append("# TYPE docuhub_extract_duration_ms_count counter")
    lines.append(f"docuhub_extract_duration_ms_count {metrics['extract_duration_count']}")

    lines.append("# TYPE docuhub_batch_size_sum counter")
    lines.append(f"docuhub_batch_size_sum {metrics['batch_size_sum']}")
    lines.append("# TYPE docuhub_batch_count counter")
    lines.append(f"docuhub_batch_count {metrics['batch_count']}")

    return "\n".join(lines) + "\n"
