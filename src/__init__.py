"""Document Analyzer and Summarizer core package."""
from src.pdf_processor import (
    extract_document_data,
    extract_pdf_data,
    chunk_pdf_pages,
    search_in_pages,
)
from src.code_analyzer import (
    detect_language,
    extract_code_data,
    chunk_code_lines,
    search_in_code,
    analyze_code,
)
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
from src.ui import (
    inject_custom_css,
    render_hero_header,
    render_metric_cards,
    render_lm_studio_setup_guide,
    trigger_browser_notification
)

__all__ = [
    "extract_document_data",
    "extract_pdf_data",
    "chunk_pdf_pages",
    "search_in_pages",
    "detect_language",
    "extract_code_data",
    "chunk_code_lines",
    "search_in_code",
    "analyze_code",
    "DEFAULT_BASE_URL",
    "DEFAULT_API_KEY",
    "PROMPT_PRESETS",
    "get_openai_client",
    "check_lm_studio_connection",
    "run_single_pass_summary",
    "map_reduce_summary",
    "chat_stream_response",
    "inject_custom_css",
    "render_hero_header",
    "render_metric_cards",
    "render_lm_studio_setup_guide",
    "trigger_browser_notification"
]
