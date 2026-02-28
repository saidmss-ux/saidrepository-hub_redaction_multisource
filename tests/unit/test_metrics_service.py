from backend.services.metrics_service import (
    inc_error_code,
    observe_batch_size,
    observe_extract,
    observe_request,
    render_prometheus,
)


def test_metrics_render_contains_expected_keys() -> None:
    observe_request(120)
    observe_extract(80)
    observe_batch_size(3)
    inc_error_code("file_not_found")

    output = render_prometheus()
    assert "docuhub_request_total" in output
    assert "docuhub_extract_duration_ms_sum" in output
    assert 'docuhub_error_code_total{code="file_not_found"}' in output
