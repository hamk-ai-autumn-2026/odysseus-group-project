import os
import tempfile
import pytest
from pathlib import Path
from src.db import (
    calculate_file_hash,
    init_db,
    save_document,
    get_document_by_hash,
    list_recent_documents,
    delete_document,
    save_summary,
    get_summaries_for_document,
    delete_summary,
    save_chat_message,
    get_chat_history_for_document,
    clear_chat_history_for_document,
    get_database_stats,
    get_table_names,
    get_table_schema,
    get_table_data,
    execute_readonly_query,
    clear_table_records,
)


@pytest.fixture
def temp_db_path():
    """Provides a temporary database file path and cleans it up after tests."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    yield db_path
    if os.path.exists(db_path):
        os.remove(db_path)


def test_calculate_file_hash():
    bytes1 = b"Hello DocuMind AI World!"
    bytes2 = b"Hello DocuMind AI World!"
    bytes3 = b"Different document content"

    hash1 = calculate_file_hash(bytes1)
    hash2 = calculate_file_hash(bytes2)
    hash3 = calculate_file_hash(bytes3)

    assert hash1 == hash2
    assert hash1 != hash3
    assert len(hash1) == 64  # SHA-256 length


def test_document_lifecycle(temp_db_path):
    init_db(temp_db_path)
    file_bytes = b"Test document text content for SQLite persistence."
    file_hash = calculate_file_hash(file_bytes)
    file_name = "test_doc.pdf"

    mock_pdf_data = {
        "pages": [{"page_num": 1, "text": "Test page text", "char_count": 14, "word_count": 3, "has_image": False}],
        "full_text": "Test page text",
        "total_pages": 1,
        "total_words": 3,
        "total_chars": 14,
        "est_reading_time": 1,
        "metadata": {"title": "Test Title", "author": "Tester"},
        "page_images": [{"page_num": 1, "data_url": "data:image/jpeg;base64,sample_large_image_bytes"}],
    }

    # Verify initially not present
    assert get_document_by_hash(file_hash, temp_db_path) is None

    # Save document
    save_document(file_hash, file_name, file_bytes, mock_pdf_data, temp_db_path)

    # Retrieve document
    doc_record = get_document_by_hash(file_hash, temp_db_path)
    assert doc_record is not None
    assert doc_record["file_hash"] == file_hash
    assert doc_record["file_name"] == file_name
    assert doc_record["total_pages"] == 1
    assert doc_record["pdf_data"]["full_text"] == "Test page text"
    assert doc_record["pdf_data"]["page_images"] == []

    # List recent
    recent = list_recent_documents(limit=10, db_path=temp_db_path)
    assert len(recent) == 1
    assert recent[0]["file_hash"] == file_hash

    # Delete document
    delete_document(file_hash, temp_db_path)
    assert get_document_by_hash(file_hash, temp_db_path) is None


def test_summaries_lifecycle(temp_db_path):
    init_db(temp_db_path)
    file_bytes = b"Document for summary testing."
    file_hash = calculate_file_hash(file_bytes)
    file_name = "report.pdf"
    mock_pdf_data = {"pages": [], "full_text": "Sample", "total_pages": 1, "total_words": 1, "total_chars": 6, "est_reading_time": 1, "metadata": {}, "page_images": []}

    save_document(file_hash, file_name, file_bytes, mock_pdf_data, temp_db_path)

    # Save summary 1
    s1_id = save_summary(
        file_hash=file_hash,
        preset_name="Executive Summary",
        language="English",
        summary_text="This is an executive summary.",
        model="llama-3.2-3b",
        db_path=temp_db_path,
    )
    assert s1_id > 0

    # Save summary 2
    s2_id = save_summary(
        file_hash=file_hash,
        preset_name="Key Insights & Bullet Points",
        language="Finnish",
        summary_text="Tässä on tärkeimmät havainnot.",
        model="qwen-2.5-7b",
        db_path=temp_db_path,
    )
    assert s2_id > 0

    # Retrieve summaries
    summaries = get_summaries_for_document(file_hash, temp_db_path)
    assert len(summaries) == 2
    # Should be ordered newest first (s2 then s1)
    assert summaries[0]["preset_name"] == "Key Insights & Bullet Points"
    assert summaries[1]["preset_name"] == "Executive Summary"

    # Delete one summary
    delete_summary(s1_id, temp_db_path)
    summaries_after = get_summaries_for_document(file_hash, temp_db_path)
    assert len(summaries_after) == 1
    assert summaries_after[0]["id"] == s2_id


def test_chat_history_lifecycle(temp_db_path):
    init_db(temp_db_path)
    file_bytes = b"Document for chat history testing."
    file_hash = calculate_file_hash(file_bytes)
    file_name = "chat_doc.txt"
    mock_pdf_data = {"pages": [], "full_text": "Sample text", "total_pages": 1, "total_words": 2, "total_chars": 11, "est_reading_time": 1, "metadata": {}, "page_images": []}

    save_document(file_hash, file_name, file_bytes, mock_pdf_data, temp_db_path)

    # Initially empty
    assert get_chat_history_for_document(file_hash, temp_db_path) == []

    # Add messages
    save_chat_message(file_hash, "user", "What is the topic of this document?", temp_db_path)
    save_chat_message(file_hash, "assistant", "The topic is document analysis testing.", temp_db_path)

    chat_history = get_chat_history_for_document(file_hash, temp_db_path)
    assert len(chat_history) == 2
    assert chat_history[0] == {"role": "user", "content": "What is the topic of this document?"}
    assert chat_history[1] == {"role": "assistant", "content": "The topic is document analysis testing."}

    # Clear chat history
    clear_chat_history_for_document(file_hash, temp_db_path)
    assert get_chat_history_for_document(file_hash, temp_db_path) == []


def test_cascading_deletion(temp_db_path):
    init_db(temp_db_path)
    file_bytes = b"Cascade document test."
    file_hash = calculate_file_hash(file_bytes)
    mock_pdf_data = {"pages": [], "full_text": "Sample", "total_pages": 1, "total_words": 1, "total_chars": 6, "est_reading_time": 1, "metadata": {}, "page_images": []}

    save_document(file_hash, "cascade.pdf", file_bytes, mock_pdf_data, temp_db_path)
    save_summary(file_hash, "Executive Summary", "English", "Summary text", db_path=temp_db_path)
    save_chat_message(file_hash, "user", "Hello!", temp_db_path)

    assert len(get_summaries_for_document(file_hash, temp_db_path)) == 1
    assert len(get_chat_history_for_document(file_hash, temp_db_path)) == 1

    # Deleting document should cascade delete summaries and chat history
    delete_document(file_hash, temp_db_path)

    assert get_document_by_hash(file_hash, temp_db_path) is None
    assert len(get_summaries_for_document(file_hash, temp_db_path)) == 0
    assert len(get_chat_history_for_document(file_hash, temp_db_path)) == 0


def test_database_inspection_and_queries(temp_db_path):
    init_db(temp_db_path)
    file_bytes = b"Inspection test file"
    file_hash = calculate_file_hash(file_bytes)
    mock_pdf_data = {"pages": [], "full_text": "Text sample", "total_pages": 1, "total_words": 2, "total_chars": 11, "est_reading_time": 1, "metadata": {}, "page_images": []}

    save_document(file_hash, "inspect_doc.pdf", file_bytes, mock_pdf_data, temp_db_path)
    save_summary(file_hash, "Executive Summary", "English", "Great summary", db_path=temp_db_path)
    save_chat_message(file_hash, "user", "Hello DB", temp_db_path)

    # Test get_table_names
    tables = get_table_names(temp_db_path)
    assert "documents" in tables
    assert "summaries" in tables
    assert "chat_history" in tables

    # Test get_database_stats
    stats = get_database_stats(temp_db_path)
    assert stats["total_tables"] == 3
    assert stats["total_rows"] == 3
    assert stats["table_counts"]["documents"] == 1
    assert stats["table_counts"]["summaries"] == 1
    assert stats["table_counts"]["chat_history"] == 1

    # Test get_table_schema
    doc_schema = get_table_schema("documents", temp_db_path)
    col_names = [col["name"] for col in doc_schema]
    assert "file_hash" in col_names
    assert "file_name" in col_names

    # Test get_table_data with search
    cols, rows, total = get_table_data("documents", limit=10, search_query="inspect", db_path=temp_db_path)
    assert total == 1
    assert len(rows) == 1
    assert rows[0]["file_name"] == "inspect_doc.pdf"

    # Test execute_readonly_query
    cols, rows = execute_readonly_query("SELECT file_name, file_size FROM documents WHERE file_hash = ?", (file_hash,), db_path=temp_db_path)
    assert len(rows) == 1
    assert rows[0]["file_name"] == "inspect_doc.pdf"

    # Test execute_readonly_query rejecting mutation SQL
    with pytest.raises(ValueError, match="read-only"):
        execute_readonly_query("DELETE FROM documents", db_path=temp_db_path)

    # Test clear_table_records
    clear_table_records("chat_history", temp_db_path)
    assert get_database_stats(temp_db_path)["table_counts"]["chat_history"] == 0

