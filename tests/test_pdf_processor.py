import io
import json
import base64
from PIL import Image
import pytest
from pypdf import PdfWriter, PageObject
from src.pdf_processor import (
    extract_document_data,
    extract_pdf_data,
    chunk_pdf_pages,
    search_in_pages,
)

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
    assert len(data["page_images"]) == 2
    assert data["page_images"][0]["data_url"].startswith("data:image/jpeg;base64,")
    assert all(page["has_image"] for page in data["pages"])


def test_extract_pdf_data_rejects_corrupt_bytes():
    with pytest.raises(ValueError, match="Could not open or parse PDF file"):
        extract_pdf_data(b"Not a valid PDF file content at all")


def test_extract_pdf_data_rejects_empty_pdf():
    writer = PdfWriter()
    buf = io.BytesIO()
    writer.write(buf)
    with pytest.raises(ValueError, match="0 pages or contains no content"):
        extract_pdf_data(buf.getvalue())


@pytest.mark.parametrize(
    ("filename", "content", "expected_text"),
    [
        ("notes.txt", b"Plain text\nwith two lines.", "Plain text\nwith two lines."),
        ("README.md", b"# Heading\n\nMarkdown content.", "# Heading\n\nMarkdown content."),
        ("data.json", b'{"name": "DocuMind", "items": [1, 2]}', '"name": "DocuMind"'),
    ],
)
def test_extract_document_data_text_formats(filename, content, expected_text):
    data = extract_document_data(content, filename)

    assert data["total_pages"] == 1
    assert data["full_text"].find(expected_text) >= 0
    assert data["page_images"] == []
    assert data["pages"][0]["has_image"] is False


def test_extract_document_data_rejects_invalid_json():
    with pytest.raises(ValueError, match="invalid JSON"):
        extract_document_data(b'{"missing": }', "data.json")


@pytest.mark.parametrize(
    ("extension", "image_format", "mime_type"),
    [("png", "PNG", "image/png"), ("jpg", "JPEG", "image/jpeg"),
     ("jpeg", "JPEG", "image/jpeg"), ("webp", "WEBP", "image/webp")],
)
def test_extract_standalone_image(extension, image_format, mime_type):
    buffer = io.BytesIO()
    Image.new("RGB", (8, 8), "red").save(buffer, format=image_format)
    image_bytes = buffer.getvalue()
    data = extract_document_data(image_bytes, f"PHOTO.{extension.upper()}")

    assert data["input_type"] == "image"
    assert data["full_text"] == data["pages"][0]["text"] == ""
    assert data["total_words"] == data["total_chars"] == data["est_reading_time"] == 0
    assert data["total_pages"] == 1
    assert data["pages"][0]["has_image"] is True
    image = data["page_images"][0]
    assert image["page_num"] == 1
    prefix, payload = image["data_url"].split(",", 1)
    assert prefix == f"data:{mime_type};base64"
    assert base64.b64decode(payload) == image_bytes
    # Its serializable data can use the existing SQLite cache.
    assert json.loads(json.dumps(data)) == data


@pytest.mark.parametrize("extension", ["png", "jpg", "jpeg", "webp"])
@pytest.mark.parametrize("content", [b"", b"This is plain text, not an image."])
def test_extract_standalone_image_rejects_invalid_bytes(extension, content):
    with pytest.raises(ValueError, match="invalid.*image"):
        extract_document_data(content, f"photo.{extension}")


def test_extract_standalone_image_rejects_mislabeled_and_truncated_files():
    buffer = io.BytesIO()
    Image.new("RGB", (8, 8), "red").save(buffer, format="PNG")
    image_bytes = buffer.getvalue()
    with pytest.raises(ValueError, match="valid JPEG"):
        extract_document_data(image_bytes, "photo.jpg")
    with pytest.raises(ValueError):
        extract_document_data(image_bytes[:40], "photo.png")


def test_extract_document_data_rejects_unsupported_extension():
    with pytest.raises(ValueError, match="Unsupported document type"):
        extract_document_data(b"content", "data.xml")


def test_extract_csv_preserves_headers_values_and_text_pipeline():
    content = '\ufeffName,Code,Notes,Empty\r\n"Mäki, Anna",001,"First line\r\nSecond ""quoted"" line",\r\n\r\nBob,002,=SUM(A1:A2),\r\n'
    data = extract_document_data(content.encode("utf-8"), "DATA.CSV")
    parts = data["full_text"].split("\n\n")

    assert json.loads(parts[0].removeprefix("Columns: ")) == ["Name", "Code", "Notes", "Empty"]
    assert json.loads(parts[1].removeprefix("Row 1: ")) == [
        {"column": "Name", "value": "Mäki, Anna"},
        {"column": "Code", "value": "001"},
        {"column": "Notes", "value": 'First line\r\nSecond "quoted" line'},
        {"column": "Empty", "value": ""},
    ]
    assert json.loads(parts[2].removeprefix("Row 2: "))[2]["value"] == "=SUM(A1:A2)"
    assert data["total_pages"] == 1
    assert data["pages"][0]["text"] == data["full_text"]
    assert data["total_chars"] == len(data["full_text"])
    assert data["total_words"] == len(data["full_text"].split())
    assert data["metadata"]["subject"] == "CSV document"
    assert data["page_images"] == []
    assert data["pages"][0]["has_image"] is False
    assert chunk_pdf_pages(data["pages"])[0]["text"] == data["full_text"]
    assert search_in_pages(data["pages"], "001")


def test_extract_csv_preserves_duplicate_and_empty_column_names():
    data = extract_document_data(b"Name,Name,\na,b,c\n", "data.csv")
    row = json.loads(data["full_text"].split("\n\n")[1].removeprefix("Row 1: "))
    assert row == [
        {"column": "Name", "value": "a"},
        {"column": "Name", "value": "b"},
        {"column": "", "value": "c"},
    ]


def test_extract_csv_header_only():
    data = extract_document_data(b"Name,Age\n", "data.csv")
    assert data["full_text"] == 'Columns: ["Name", "Age"]'


@pytest.mark.parametrize(
    ("content", "message"),
    [
        (b"", "no CSV header"),
        (b"\n\r\n", "no CSV header"),
        (b'Name,Age\n"unfinished,20', "invalid CSV"),
        (b'Name\n"value"junk\n', "invalid CSV"),
        (b"Name,Age\nAlice\n", "expected 2 columns"),
        (b"Name,Age\nAlice,20,extra\n", "expected 2 columns"),
        (b"Name\n\xff", "not valid UTF-8"),
    ],
)
def test_extract_csv_rejects_invalid_input(content, message):
    with pytest.raises(ValueError, match=message):
        extract_document_data(content, "data.csv")

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

@pytest.mark.parametrize(
    ("overlap", "expected_pages", "expected_range"),
    [(5, [2, 3], "Pages 2-3"), (15, [1, 2, 3], "Pages 1-3")],
)
def test_chunk_pdf_pages_preserves_overlap_page_metadata(overlap, expected_pages, expected_range):
    pages = [
        {"page_num": 1, "text": "AAAAAAAAAA"},
        {"page_num": 2, "text": "BBBBBBBBBB"},
        {"page_num": 3, "text": "CCCCCCCCCC"},
        {"page_num": 4, "text": "DDDDDDDDDD"},
    ]

    chunks = chunk_pdf_pages(pages, max_chars=25, overlap=overlap)

    assert chunks[0]["pages"] == [1, 2]
    assert chunks[1]["text"] == chunks[0]["text"][-overlap:] + "\n\n" + pages[2]["text"]
    assert chunks[1]["pages"] == expected_pages
    assert chunks[1]["page_range"] == expected_range
    # A later overlap must drop pages whose text no longer survives.
    assert chunks[2]["pages"] == ([3, 4] if overlap == 5 else [2, 3, 4])


def test_chunk_pdf_pages_zero_overlap():
    pages = [
        {"page_num": 1, "text": "Paragraph A\n\nParagraph B"},
        {"page_num": 2, "text": "Paragraph C"},
    ]
    chunks = chunk_pdf_pages(pages, max_chars=15, overlap=0)
    assert len(chunks) == 3
    assert chunks[0]["text"] == "Paragraph A"
    assert chunks[1]["text"] == "Paragraph B"
    assert chunks[2]["text"] == "Paragraph C"
    assert chunks[0]["pages"] == [1]
    assert chunks[1]["pages"] == [1]
    assert chunks[2]["pages"] == [2]
    assert chunks[0]["page_range"] == "Page 1"
    assert chunks[1]["page_range"] == "Page 1"
    assert chunks[2]["page_range"] == "Page 2"


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
