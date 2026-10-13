from typing import List, Dict, Any
import pypdf
import io
import math
import base64
import pymupdf
import json
import csv
from pathlib import Path


SUPPORTED_DOCUMENT_EXTENSIONS = ("pdf", "md", "markdown", "txt", "json", "csv")


def _render_page_images(file_bytes: bytes, max_dimension: int = 1600) -> List[Dict[str, Any]]:
    """Render each PDF page as a compressed image for vision-capable LLMs."""
    document = pymupdf.open(stream=file_bytes, filetype="pdf")
    images = []
    try:
        for page_number, page in enumerate(document, start=1):
            rect = page.rect
            scale = min(max_dimension / max(rect.width, rect.height), 2.0)
            matrix = pymupdf.Matrix(scale, scale)
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            image_bytes = pixmap.tobytes("jpeg", jpg_quality=75)
            images.append({
                "page_num": page_number,
                "data_url": "data:image/jpeg;base64,"
                + base64.b64encode(image_bytes).decode("ascii"),
            })
    finally:
        document.close()
    return images


def extract_pdf_data(file_bytes: bytes, include_images: bool = True) -> Dict[str, Any]:
    """
    Extracts text, metadata, and statistics from PDF file bytes.
    """
    doc = pymupdf.open(stream=file_bytes, filetype="pdf")
    total_pages = len(doc)
    pages_data = []
    full_text = ""
    
    pdf_stream = io.BytesIO(file_bytes)
    reader = pypdf.PdfReader(pdf_stream)
    
    for i, page in enumerate(doc):
        # Extract text via PyMuPDF (superior handling for math formulas, LaTeX font CMaps, equations & symbols)
        page_text = page.get_text("text") or ""
        # Fallback to pypdf if PyMuPDF yields empty string for page
        if not page_text.strip() and i < len(reader.pages):
            page_text = reader.pages[i].extract_text() or ""
            
        clean_text = page_text.strip()
        pages_data.append({
            "page_num": i + 1,
            "text": clean_text,
            "char_count": len(clean_text),
            "word_count": len(clean_text.split()),
            "has_image": False,
        })
        if clean_text:
            full_text += f"\n--- Page {i + 1} ---\n" + clean_text
            
    doc.close()

            
    # Extract metadata
    raw_meta = reader.metadata or {}
    metadata = {
        "title": str(raw_meta.get('/Title', 'N/A')),
        "author": str(raw_meta.get('/Author', 'N/A')),
        "subject": str(raw_meta.get('/Subject', 'N/A')),
        "creator": str(raw_meta.get('/Creator', 'N/A')),
        "producer": str(raw_meta.get('/Producer', 'N/A')),
        "creation_date": str(raw_meta.get('/CreationDate', 'N/A'))
    }
    
    total_words = sum(p["word_count"] for p in pages_data)
    total_chars = sum(p["char_count"] for p in pages_data)
    # Average reading speed ~ 200 words per min
    est_reading_time = math.ceil(total_words / 200) if total_words > 0 else 0
    
    page_images = _render_page_images(file_bytes) if include_images else []
    images_by_page = {image["page_num"]: image for image in page_images}
    for page in pages_data:
        page["has_image"] = page["page_num"] in images_by_page

    return {
        "pages": pages_data,
        "full_text": full_text.strip(),
        "total_pages": total_pages,
        "total_words": total_words,
        "total_chars": total_chars,
        "est_reading_time": est_reading_time,
        "metadata": metadata,
        "page_images": page_images,
    }


def extract_document_data(
    file_bytes: bytes,
    filename: str,
    include_images: bool = True,
) -> Dict[str, Any]:
    """Extract text and analysis metadata from a supported document format."""
    extension = Path(filename).suffix.lower().lstrip(".")
    if extension == "pdf":
        return extract_pdf_data(file_bytes, include_images=include_images)

    if extension not in SUPPORTED_DOCUMENT_EXTENSIONS:
        supported = ", ".join(f".{item}" for item in SUPPORTED_DOCUMENT_EXTENSIONS)
        raise ValueError(f"Unsupported document type '.{extension or 'unknown'}'. Supported types: {supported}.")

    try:
        text = file_bytes.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise ValueError(f"{filename} is not valid UTF-8 text.") from error

    if extension == "json":
        try:
            parsed_json = json.loads(text)
        except json.JSONDecodeError as error:
            raise ValueError(f"{filename} contains invalid JSON: {error.msg}.") from error
        text = json.dumps(parsed_json, indent=2, ensure_ascii=False)
    elif extension == "csv":
        try:
            rows = csv.reader(io.StringIO(text, newline=""), strict=True)
            columns = next((row for row in rows if row), None)
            if columns is None:
                raise ValueError(f"{filename} contains no CSV header.")
            parts = ["Columns: " + json.dumps(columns, ensure_ascii=False)]
            row_number = 0
            for row in rows:
                if not row:
                    continue
                row_number += 1
                if len(row) != len(columns):
                    raise ValueError(
                        f"{filename} CSV row {row_number} has {len(row)} values; "
                        f"expected {len(columns)} columns."
                    )
                cells = [{"column": column, "value": value} for column, value in zip(columns, row)]
                parts.append(f"Row {row_number}: " + json.dumps(cells, ensure_ascii=False))
        except csv.Error as error:
            raise ValueError(f"{filename} contains invalid CSV: {error}.") from error
        text = "\n\n".join(parts)

    clean_text = text.strip()
    page = {
        "page_num": 1,
        "text": clean_text,
        "char_count": len(clean_text),
        "word_count": len(clean_text.split()),
        "has_image": False,
    }
    total_words = page["word_count"]
    total_chars = page["char_count"]

    return {
        "pages": [page],
        "full_text": clean_text,
        "total_pages": 1,
        "total_words": total_words,
        "total_chars": total_chars,
        "est_reading_time": math.ceil(total_words / 200) if total_words else 0,
        "metadata": {
            "title": filename,
            "author": "N/A",
            "subject": f"{extension.upper()} document",
            "creator": "N/A",
            "producer": "N/A",
            "creation_date": "N/A",
        },
        "page_images": [],
    }

def chunk_pdf_pages(pages: List[Dict[str, Any]], max_chars: int = 3500, overlap: int = 400) -> List[Dict[str, Any]]:
    """
    Chunks extracted pages into overlapping sections for long document LLM context fitting.
    Returns list of chunk objects with chunk_id, page_range, and text.
    """
    chunks = []
    current_chunk_text = ""
    current_pages = set()
    current_page_spans = []
    chunk_id = 1
    
    for page in pages:
        page_num = page["page_num"]
        text = page["text"]
        
        if not text and not page.get("has_image", False):
            continue

        if not text:
            text = "[Image-only page. Analyze the attached page image.]"
            
        # Split page into paragraphs or sentences if page text is huge
        paragraphs = text.split("\n\n")
        for para in paragraphs:
            para_clean = para.strip()
            if not para_clean:
                continue
                
            if len(current_chunk_text) + len(para_clean) > max_chars and current_chunk_text:
                pages_list = sorted(list(current_pages))
                page_str = f"Page {pages_list[0]}" if len(pages_list) == 1 else f"Pages {pages_list[0]}-{pages_list[-1]}"
                
                chunks.append({
                    "chunk_id": chunk_id,
                    "page_range": page_str,
                    "pages": pages_list,
                    "text": current_chunk_text.strip()
                })
                chunk_id += 1
                
                # Apply overlap from end of current_chunk_text
                if overlap > 0:
                    overlap_text = current_chunk_text[-overlap:] if len(current_chunk_text) > overlap else current_chunk_text
                else:
                    overlap_text = ""
                overlap_start = len(current_chunk_text) - len(overlap_text)
                current_page_spans = [
                    (max(start, overlap_start) - overlap_start, end - overlap_start, number)
                    for start, end, number in current_page_spans
                    if end > overlap_start
                ]
                paragraph_start = len(overlap_text) + (2 if overlap_text else 0)
                current_chunk_text = (overlap_text + "\n\n" if overlap_text else "") + para_clean
                current_page_spans.append((paragraph_start, len(current_chunk_text), page_num))
                current_pages = {number for _, _, number in current_page_spans}
            else:
                paragraph_start = len(current_chunk_text) + (2 if current_chunk_text else 0)
                current_chunk_text += ("\n\n" if current_chunk_text else "") + para_clean
                current_page_spans.append((paragraph_start, len(current_chunk_text), page_num))
                current_pages.add(page_num)
                
    # Append final chunk if exists
    if current_chunk_text.strip():
        pages_list = sorted(list(current_pages)) if current_pages else [1]
        page_str = f"Page {pages_list[0]}" if len(pages_list) == 1 else f"Pages {pages_list[0]}-{pages_list[-1]}"
        chunks.append({
            "chunk_id": chunk_id,
            "page_range": page_str,
            "pages": pages_list,
            "text": current_chunk_text.strip()
        })
        
    return chunks

def search_in_pages(pages: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
    """
    Searches for a query string across pages and returns snippets.
    """
    if not query.strip():
        return []
    
    results = []
    q_lower = query.lower()
    
    for p in pages:
        text = p["text"]
        t_lower = text.lower()
        if q_lower in t_lower:
            # Find context snippet around match
            pos = t_lower.find(q_lower)
            start = max(0, pos - 80)
            end = min(len(text), pos + len(query) + 80)
            snippet = ("..." if start > 0 else "") + text[start:end] + ("..." if end < len(text) else "")
            
            # Count occurrences on this page
            count = t_lower.count(q_lower)
            results.append({
                "page_num": p["page_num"],
                "snippet": snippet,
                "matches_on_page": count
            })
            
    return results
