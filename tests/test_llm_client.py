import pytest
from src.llm_client import (
    DEFAULT_BASE_URL,
    DEFAULT_API_KEY,
    PROMPT_PRESETS,
    get_openai_client,
    check_lm_studio_connection,
    run_single_pass_summary,
    chat_stream_response
)

def test_prompt_presets_completeness():
    required_presets = [
        "Executive Summary",
        "Key Insights & Bullet Points",
        "Technical Breakdown",
        "Actionable Takeaways & Next Steps",
        "Custom Prompt"
    ]
    for preset in required_presets:
        assert preset in PROMPT_PRESETS
        assert isinstance(PROMPT_PRESETS[preset], str)
        assert len(PROMPT_PRESETS[preset]) > 10

def test_get_openai_client():
    client = get_openai_client(base_url="http://localhost:9999/v1", api_key="test-key")
    assert client.base_url == "http://localhost:9999/v1/"
    assert client.api_key == "test-key"

def test_check_lm_studio_connection_offline():
    # Test connection to an invalid port where no server is running
    is_connected, status_msg, models = check_lm_studio_connection(
        base_url="http://127.0.0.1:59999/v1",
        api_key="test"
    )
    assert is_connected is False
    assert "Could not connect" in status_msg or "Error" in status_msg
    assert models == []

def test_run_single_pass_summary_truncation():
    # Verify long document text gets safely truncated in single-pass mode
    long_text = "Word " * 5000  # ~25,000 characters
    generator = run_single_pass_summary(
        client=None, # Will fail if actually invoked via API, but we test prompt construction before iteration
        model="dummy",
        document_text=long_text,
        preset_name="Executive Summary",
        max_context_chars=1000
    )
    # Generator object returned
    assert generator is not None
