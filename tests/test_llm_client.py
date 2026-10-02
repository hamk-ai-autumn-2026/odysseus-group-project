import pytest
from src.llm_client import (
    DEFAULT_BASE_URL,
    DEFAULT_API_KEY,
    PROMPT_PRESETS,
    get_openai_client,
    check_lm_studio_connection,
    run_single_pass_summary,
    map_reduce_summary,
    chat_stream_response
)

def test_prompt_presets_completeness():
    required_presets = [
        "Executive Summary",
        "Key Insights & Bullet Points",
        "Technical Breakdown",
        "Actionable Takeaways & Next Steps",
        "Math & Quantitative Analysis",
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

def test_run_single_pass_summary_generator():
    long_text = "Word " * 500
    generator = run_single_pass_summary(
        client=None,
        model="dummy",
        document_text=long_text,
        preset_name="Executive Summary",
        max_context_chars=1000
    )
    assert generator is not None
    assert hasattr(generator, "__next__")

def test_map_reduce_summary_generator():
    chunks = [
        {"chunk_id": 1, "page_range": "Page 1", "text": "Sample text for page 1"},
        {"chunk_id": 2, "page_range": "Page 2", "text": "Sample text for page 2"}
    ]
    generator = map_reduce_summary(
        client=None,
        model="dummy",
        chunks=chunks,
        preset_name="Executive Summary"
    )
    assert generator is not None
    assert hasattr(generator, "__next__")
