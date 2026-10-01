import io
import pytest
from pypdf import PdfWriter, PageObject
from src.pdf_processor import extract_pdf_data, chunk_pdf_pages, search_in_pages

def create_sample_pdf_bytes() -> bytes:
    """Helper to create a 2-page sample PDF in memory with known text."""
    writer = PdfWriter()
    
    # Page 1
    page1 = writer.add_blank_page(width=612, height=792)
    # Page 2
    page2 = writer.add_blank_page(width=612, height=792)
    
    writer.add_metadata({
        "/Title": "Automated Test Document",
        "/Author": "PyTest Suite",
        "/Subject": "Sanity Checking"
    })
    
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()

def test_extract_pdf_data_structure():
    pdf_bytes = create_sample_pdf_bytes()
    data = extract_pdf_data(pdf_bytes)
    
    assert "pages" in data
    assert "full_text" in data
    assert "total_pages" in data
    assert "metadata" in data
    assert data["total_pages"] == 2
    assert data["metadata"]["title"] == "Automated Test Document"
    assert data["metadata"]["author"] == "PyTest Suite"

def test_chunk_pdf_pages():
    mock_pages = [
        {
            "page_num": 1,
            "text": "Paragraph one is short.\n\nParagraph two contains more words and details about artificial intelligence.",
            "char_count": 96,
            "word_count": 13
        },
        {
            "page_num": 2,
            "text": "Paragraph three on page two discusses local LLMs and Streamlit interfaces.\n\nParagraph four wraps up.",
            "char_count": 97,
            "word_count": 14
        }
    ]
    
    # Test small chunk max_chars (forces splitting into multiple chunks)
    chunks = chunk_pdf_pages(mock_pages, max_chars=80, overlap=10)
    assert len(chunks) > 1
    assert "chunk_id" in chunks[0]
    assert "page_range" in chunks[0]
    assert "text" in chunks[0]

def test_search_in_pages():
    mock_pages = [
        {"page_num": 1, "text": "The quick brown fox jumps over the lazy dog."},
        {"page_num": 2, "text": "Artificial intelligence and local LLM models are revolutionary."}
    ]
    
    results = search_in_pages(mock_pages, "fox")
    assert len(results) == 1
    assert results[0]["page_num"] == 1
    assert "fox" in results[0]["snippet"].lower()
    
    results_llm = search_in_pages(mock_pages, "LLM")
    assert len(results_llm) == 1
    assert results_llm[0]["page_num"] == 2

def test_search_in_pages_empty_query():
    mock_pages = [{"page_num": 1, "text": "Hello world"}]
    results = search_in_pages(mock_pages, "   ")
    assert results == []
