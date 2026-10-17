import sqlite3
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime

DEFAULT_DB_FILENAME = "documind.db"


def get_default_db_path() -> str:
    """Returns absolute path to default documind.db database file."""
    return os.environ.get("DOCUMIND_DB_PATH", str(Path.cwd() / DEFAULT_DB_FILENAME))


def calculate_file_hash(file_bytes: bytes) -> str:
    """Calculates SHA-256 hex digest for document file contents."""
    return hashlib.sha256(file_bytes).hexdigest()


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """
    Creates and returns a thread-safe SQLite connection with WAL mode enabled.
    """
    target_path = db_path or get_default_db_path()
    # Ensure parent directory exists
    Path(target_path).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(target_path, timeout=10.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    
    # Enable WAL mode and foreign keys for safety & concurrent performance
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
    except sqlite3.Error:
        pass
        
    return conn


def init_db(db_path: Optional[str] = None) -> None:
    """Initializes SQLite tables for documents, summaries, and chat history."""
    conn = get_connection(db_path)
    try:
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    file_hash TEXT PRIMARY KEY,
                    file_name TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    total_pages INTEGER NOT NULL,
                    total_words INTEGER NOT NULL,
                    total_chars INTEGER NOT NULL,
                    est_reading_time INTEGER NOT NULL,
                    extracted_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS summaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_hash TEXT NOT NULL,
                    preset_name TEXT NOT NULL,
                    language TEXT NOT NULL,
                    custom_instruction TEXT DEFAULT '',
                    model TEXT DEFAULT '',
                    summary_text TEXT NOT NULL,
                    audio_data BLOB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (file_hash) REFERENCES documents(file_hash) ON DELETE CASCADE
                );
            """)

            try:
                conn.execute("ALTER TABLE summaries ADD COLUMN audio_data BLOB;")
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_hash TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (file_hash) REFERENCES documents(file_hash) ON DELETE CASCADE
                );
            """)
            
            # Indexes for faster queries
            conn.execute("CREATE INDEX IF NOT EXISTS idx_summaries_file_hash ON summaries(file_hash);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_file_hash ON chat_history(file_hash);")
    finally:
        conn.close()


def save_document(
    file_hash: str,
    file_name: str,
    file_bytes: bytes,
    pdf_data: Dict[str, Any],
    db_path: Optional[str] = None,
) -> None:
    """Inserts or updates document record and its parsed extracted data."""
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        # Omit large base64 page images from SQLite document cache to avoid database bloat,
        # but retain page_images for standalone image inputs where the image is the core content.
        if pdf_data.get("input_type") == "image":
            cached_data = dict(pdf_data)
        else:
            cached_data = {k: v for k, v in pdf_data.items() if k != "page_images"}
            cached_data["page_images"] = []
        data_json = json.dumps(cached_data, ensure_ascii=False)
        now = datetime.now().isoformat()
        with conn:
            conn.execute(
                """
                INSERT INTO documents (
                    file_hash, file_name, file_size, total_pages, total_words,
                    total_chars, est_reading_time, extracted_data, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(file_hash) DO UPDATE SET
                    file_name = excluded.file_name,
                    file_size = excluded.file_size,
                    total_pages = excluded.total_pages,
                    total_words = excluded.total_words,
                    total_chars = excluded.total_chars,
                    est_reading_time = excluded.est_reading_time,
                    extracted_data = excluded.extracted_data,
                    updated_at = excluded.updated_at;
                """,
                (
                    file_hash,
                    file_name,
                    len(file_bytes),
                    pdf_data.get("total_pages", 1),
                    pdf_data.get("total_words", 0),
                    pdf_data.get("total_chars", 0),
                    pdf_data.get("est_reading_time", 0),
                    data_json,
                    now,
                    now,
                ),
            )
    finally:
        conn.close()


def get_document_by_hash(file_hash: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieves document record and deserialized extracted_data dict if present."""
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT file_hash, file_name, file_size, total_pages, total_words, total_chars, est_reading_time, extracted_data, created_at, updated_at FROM documents WHERE file_hash = ?",
            (file_hash,),
        ).fetchone()
        
        if not row:
            return None
            
        try:
            pdf_data = json.loads(row["extracted_data"])
            pdf_data.setdefault("page_images", [])
        except Exception:
            return None
            
        return {
            "file_hash": row["file_hash"],
            "file_name": row["file_name"],
            "file_size": row["file_size"],
            "total_pages": row["total_pages"],
            "total_words": row["total_words"],
            "total_chars": row["total_chars"],
            "est_reading_time": row["est_reading_time"],
            "pdf_data": pdf_data,
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
    finally:
        conn.close()


def list_recent_documents(limit: int = 20, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Lists recently processed documents sorted by most recently updated."""
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            """
            SELECT file_hash, file_name, file_size, total_pages, total_words, total_chars, est_reading_time, created_at, updated_at
            FROM documents
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        
        return [dict(row) for row in rows]
    finally:
        conn.close()


def delete_document(file_hash: str, db_path: Optional[str] = None) -> None:
    """Deletes document record and cascading summaries/chat history."""
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        with conn:
            conn.execute("DELETE FROM documents WHERE file_hash = ?", (file_hash,))
    finally:
        conn.close()


def save_summary(
    file_hash: str,
    preset_name: str,
    language: str,
    summary_text: str,
    custom_instruction: str = "",
    model: str = "",
    db_path: Optional[str] = None,
) -> int:
    """Saves generated summary report for a document."""
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.execute(
                """
                INSERT INTO summaries (file_hash, preset_name, language, custom_instruction, model, summary_text)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (file_hash, preset_name, language, custom_instruction or "", model or "", summary_text),
            )
            # Update document updated_at timestamp
            conn.execute(
                "UPDATE documents SET updated_at = ? WHERE file_hash = ?",
                (datetime.now().isoformat(), file_hash),
            )
            return cursor.lastrowid
    finally:
        conn.close()


def get_summaries_for_document(file_hash: str, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieves all saved summaries for a given document hash ordered by newest first."""
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            """
            SELECT id, file_hash, preset_name, language, custom_instruction, model, summary_text, audio_data, created_at
            FROM summaries
            WHERE file_hash = ?
            ORDER BY created_at DESC, id DESC
            """,
            (file_hash,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def update_summary_audio(summary_id: int, audio_bytes: bytes, db_path: Optional[str] = None) -> None:
    """Updates stored audio BLOB for a specific summary record."""
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        with conn:
            conn.execute(
                "UPDATE summaries SET audio_data = ? WHERE id = ?",
                (audio_bytes, summary_id),
            )
    finally:
        conn.close()


def get_summary_audio(summary_id: int, db_path: Optional[str] = None) -> Optional[bytes]:
    """Retrieves stored audio BLOB bytes for a specific summary record."""
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT audio_data FROM summaries WHERE id = ?",
            (summary_id,),
        ).fetchone()
        return row["audio_data"] if row else None
    finally:
        conn.close()


def delete_summary(summary_id: int, db_path: Optional[str] = None) -> None:
    """Deletes a specific summary record by ID."""
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        with conn:
            conn.execute("DELETE FROM summaries WHERE id = ?", (summary_id,))
    finally:
        conn.close()


def save_chat_message(
    file_hash: str,
    role: str,
    content: str,
    db_path: Optional[str] = None,
) -> int:
    """Saves a single chat message (user or assistant) tied to document hash."""
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.execute(
                """
                INSERT INTO chat_history (file_hash, role, content)
                VALUES (?, ?, ?)
                """,
                (file_hash, role, content),
            )
            # Update document updated_at timestamp
            conn.execute(
                "UPDATE documents SET updated_at = ? WHERE file_hash = ?",
                (datetime.now().isoformat(), file_hash),
            )
            return cursor.lastrowid
    finally:
        conn.close()


def get_chat_history_for_document(file_hash: str, db_path: Optional[str] = None) -> List[Dict[str, str]]:
    """Retrieves all chat messages for a document hash formatted for OpenAI/Streamlit chat."""
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            """
            SELECT role, content
            FROM chat_history
            WHERE file_hash = ?
            ORDER BY id ASC
            """,
            (file_hash,),
        ).fetchall()
        return [{"role": row["role"], "content": row["content"]} for row in rows]
    finally:
        conn.close()


def clear_chat_history_for_document(file_hash: str, db_path: Optional[str] = None) -> None:
    """Clears all chat history entries for a specific document hash."""
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        with conn:
            conn.execute("DELETE FROM chat_history WHERE file_hash = ?", (file_hash,))
    finally:
        conn.close()


def get_database_stats(db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Returns general database statistics, table counts, file size, and journal mode.
    """
    init_db(db_path)
    target_path = db_path or get_default_db_path()
    file_path = Path(target_path)
    file_size_bytes = file_path.stat().st_size if file_path.exists() else 0

    if file_size_bytes < 1024:
        size_str = f"{file_size_bytes} B"
    elif file_size_bytes < 1024 * 1024:
        size_str = f"{file_size_bytes / 1024:.1f} KB"
    else:
        size_str = f"{file_size_bytes / (1024 * 1024):.2f} MB"

    conn = get_connection(db_path)
    try:
        journal_mode = conn.execute("PRAGMA journal_mode;").fetchone()[0]
        
        tables = get_table_names(db_path)
        table_counts = {}
        total_rows = 0
        for tbl in tables:
            cnt = conn.execute(f"SELECT COUNT(*) FROM `{tbl}`").fetchone()[0]
            table_counts[tbl] = cnt
            total_rows += cnt

        return {
            "db_path": str(file_path.resolve()),
            "file_size_bytes": file_size_bytes,
            "file_size_formatted": size_str,
            "journal_mode": str(journal_mode).upper(),
            "table_counts": table_counts,
            "total_tables": len(tables),
            "total_rows": total_rows,
        }
    finally:
        conn.close()


def get_table_names(db_path: Optional[str] = None) -> List[str]:
    """Retrieves list of user-created table names in SQLite database."""
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name ASC"
        ).fetchall()
        return [row["name"] for row in rows]
    finally:
        conn.close()


def get_table_schema(table_name: str, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieves column metadata schema for a specific table."""
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        rows = conn.execute(f"PRAGMA table_info(`{table_name}`)").fetchall()
        return [
            {
                "cid": row["cid"],
                "name": row["name"],
                "type": row["type"],
                "notnull": bool(row["notnull"]),
                "dflt_value": row["dflt_value"],
                "pk": bool(row["pk"]),
            }
            for row in rows
        ]
    finally:
        conn.close()


def get_table_data(
    table_name: str,
    limit: int = 100,
    offset: int = 0,
    search_query: Optional[str] = None,
    db_path: Optional[str] = None,
) -> Tuple[List[str], List[Dict[str, Any]], int]:
    """
    Retrieves column names, paginated row dicts, and total matching count for a table.
    Supports optional text search across all columns.
    """
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        schema = get_table_schema(table_name, db_path)
        col_names = [col["name"] for col in schema]
        if not col_names:
            return [], [], 0

        where_clause = ""
        params: List[Any] = []

        if search_query and search_query.strip():
            sq = f"%{search_query.strip()}%"
            conditions = [f"`{col}` LIKE ?" for col in col_names]
            where_clause = " WHERE " + " OR ".join(conditions)
            params = [sq] * len(col_names)

        count_sql = f"SELECT COUNT(*) FROM `{table_name}`{where_clause}"
        total_count = conn.execute(count_sql, params).fetchone()[0]

        data_sql = f"SELECT * FROM `{table_name}`{where_clause} LIMIT ? OFFSET ?"
        data_params = params + [max(1, limit), max(0, offset)]
        
        rows = conn.execute(data_sql, data_params).fetchall()
        row_dicts = [dict(row) for row in rows]

        return col_names, row_dicts, total_count
    finally:
        conn.close()


def execute_readonly_query(
    sql_query: str,
    params: Tuple[Any, ...] = (),
    limit: int = 200,
    db_path: Optional[str] = None,
) -> Tuple[List[str], List[Dict[str, Any]]]:
    """
    Safely executes a read-only SQL query (SELECT / EXPLAIN / PRAGMA) and returns column names and row dicts.
    Raises ValueError if write/mutation queries are attempted.
    """
    normalized = sql_query.strip().upper()
    allowed_prefixes = ("SELECT", "EXPLAIN", "PRAGMA", "WITH")
    if not any(normalized.startswith(prefix) for prefix in allowed_prefixes):
        raise ValueError("Only read-only queries (SELECT, EXPLAIN, PRAGMA, WITH) are permitted.")

    forbidden = ("INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE", "REPLACE", "VACUUM", "ATTACH", "DETACH")
    words = set(normalized.split())
    if any(kw in words for kw in forbidden):
        raise ValueError("Data definition or modification commands are not permitted in read-only mode.")

    init_db(db_path)
    conn = get_connection(db_path)
    try:
        cursor = conn.execute(sql_query, params)
        rows = cursor.fetchmany(limit)
        col_names = [desc[0] for desc in cursor.description] if cursor.description else []
        row_dicts = [{col_names[i]: row[i] for i in range(len(col_names))} for row in rows]
        return col_names, row_dicts
    finally:
        conn.close()


def clear_table_records(table_name: str, db_path: Optional[str] = None) -> None:
    """Deletes all records from a specified database table."""
    tables = get_table_names(db_path)
    if table_name not in tables:
        raise ValueError(f"Table '{table_name}' does not exist in database.")

    init_db(db_path)
    conn = get_connection(db_path)
    try:
        with conn:
            conn.execute(f"DELETE FROM `{table_name}`")
    finally:
        conn.close()
