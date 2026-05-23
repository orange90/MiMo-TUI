import pytest
from mimo_tui.config.schema import AppConfig, EndpointConfig, ModelConfig


@pytest.fixture
def test_cfg() -> AppConfig:
    cfg = AppConfig()
    cfg.endpoint = EndpointConfig(
        url="http://localhost:9999/v1",
        anthropic_url="http://localhost:9999/anthropic",
        api_key="test-key",
        timeout_s=5,
    )
    cfg.model = ModelConfig(name="MiMo-V2.5-Pro", max_tokens=512)
    return cfg
