import importlib
import pytest

def test_app_and_src_imports():
    """Verify all top-level application modules can be imported without error."""
    modules = [
        "src",
        "src.pdf_processor",
        "src.llm_client",
        "src.ui",
        "src.desktop_launcher",
        "main",
        "app"
    ]
    for mod in modules:
        imported = importlib.import_module(mod)
        assert imported is not None
