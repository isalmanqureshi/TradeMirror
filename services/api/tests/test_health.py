from app.api.health import health_check


def test_health_endpoint() -> None:
    payload = health_check()

    assert payload.status == "ok"
    assert payload.service
    assert payload.environment
