from typing import List, Dict, Any
import pypdf
import io
import math

def extract_pdf_data(file_bytes: bytes) -> Dict[str, Any]:
    """
    Extracts text, metadata, and statistics from PDF file bytes.
    """
    pdf_stream = io.BytesIO(file_bytes)
    reader = pypdf.PdfReader(pdf_stream)
    
    total_pages = len(reader.pages)
    pages_data = []
    full_text = ""
    
    for i, page in enumerate(reader.pages):
        page_text = page.extract_text() or ""
        # Clean basic invisible control chars while preserving newlines
        clean_text = page_text.strip()
        pages_data.append({
            "page_num": i + 1,
            "text": clean_text,
            "char_count": len(clean_text),
            "word_count": len(clean_text.split())
        })
        if clean_text:
            full_text += f"\n--- Page {i + 1} ---\n" + clean_text
            
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
    
    return {
        "pages": pages_data,
        "full_text": full_text.strip(),
        "total_pages": total_pages,
        "total_words": total_words,
        "total_chars": total_chars,
        "est_reading_time": est_reading_time,
        "metadata": metadata
    }

def chunk_pdf_pages(pages: List[Dict[str, Any]], max_chars: int = 3500, overlap: int = 400) -> List[Dict[str, Any]]:
    """
    Chunks extracted pages into overlapping sections for long document LLM context fitting.
    Returns list of chunk objects with chunk_id, page_range, and text.
    """
    chunks = []
    current_chunk_text = ""
    current_pages = set()
    chunk_id = 1
    
    for page in pages:
        page_num = page["page_num"]
        text = page["text"]
        
        if not text:
            continue
            
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
                overlap_text = current_chunk_text[-overlap:] if len(current_chunk_text) > overlap else current_chunk_text
                current_chunk_text = overlap_text + "\n\n" + para_clean
                current_pages = {page_num}
            else:
                current_chunk_text += ("\n\n" if current_chunk_text else "") + para_clean
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
