import streamlit as st
import streamlit.components.v1 as components
from typing import Optional, Dict, Any, List

def inject_custom_css():
    """
    Injects ultra-premium custom CSS styling into Streamlit.
    """
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Outfit:wght@400;600;700;800&display=swap');

        /* Root styling & typography */
        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        /* Hide default Streamlit sidebar page navigation (app & db options) */
        [data-testid="stSidebarNav"],
        [data-testid="stSidebarNavItems"],
        [data-testid="stSidebarNavSeparator"] {
            display: none !important;
        }

        h1, h2, h3, h4, .stTitle {
            font-family: 'Outfit', 'Inter', sans-serif !important;
            font-weight: 700 !important;
            letter-spacing: -0.02em !important;
        }

        /* Hero Banner Container */
        .hero-container {
            background: linear-gradient(135deg, rgba(30, 27, 75, 0.9) 0%, rgba(15, 23, 42, 0.95) 50%, rgba(49, 46, 129, 0.85) 100%);
            border: 1px solid rgba(139, 92, 246, 0.25);
            border-radius: 18px;
            padding: 2.2rem 2.5rem;
            margin-bottom: 2rem;
            box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.5), inset 0 1px 1px rgba(255, 255, 255, 0.1);
            position: relative;
            overflow: hidden;
        }

        .hero-title {
            font-size: 2.4rem !important;
            font-weight: 800 !important;
            background: linear-gradient(135deg, #a78bfa 0%, #38bdf8 50%, #818cf8 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.4rem;
        }

        .hero-subtitle {
            color: #94a3b8;
            font-size: 1.05rem;
            font-weight: 400;
            max-width: 720px;
        }

        .badge-pill {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.78rem;
            font-weight: 600;
            letter-spacing: 0.03em;
            text-transform: uppercase;
        }

        .badge-online {
            background: rgba(16, 185, 129, 0.15);
            color: #34d399;
            border: 1px solid rgba(52, 211, 153, 0.3);
        }

        .badge-offline {
            background: rgba(239, 68, 68, 0.15);
            color: #f87171;
            border: 1px solid rgba(248, 113, 113, 0.3);
        }

        .badge-local {
            background: rgba(139, 92, 246, 0.15);
            color: #c084fc;
            border: 1px solid rgba(192, 132, 252, 0.3);
        }

        /* Metric Cards */
        .metric-card {
            background: rgba(30, 41, 59, 0.5);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 14px;
            padding: 1.2rem;
            margin-bottom: 1rem;
            text-align: center;
            transition: all 0.25s ease;
        }

        .metric-card:hover {
            transform: translateY(-3px);
            border-color: rgba(139, 92, 246, 0.4);
            box-shadow: 0 10px 25px -5px rgba(139, 92, 246, 0.2);
        }

        .metric-value {
            font-size: 1.8rem;
            font-weight: 700;
            color: #f8fafc;
            line-height: 1.2;
        }

        .metric-label {
            font-size: 0.82rem;
            color: #94a3b8;
            font-weight: 500;
            margin-top: 4px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        /* Tab adjustments */
        .stTabs [data-baseweb="tab-list"] {
            gap: 12px;
            background-color: transparent;
            padding-bottom: 8px;
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: 10px !important;
            padding: 10px 20px !important;
            box-sizing: border-box !important;
            font-weight: 600 !important;
            background-color: rgba(30, 41, 59, 0.4) !important;
            border: 1px solid rgba(255, 255, 255, 0.05) !important;
            color: #94a3b8 !important;
            transition: all 0.2s ease !important;
        }

        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background: linear-gradient(135deg, rgba(139, 92, 246, 0.2) 0%, rgba(56, 189, 248, 0.2) 100%) !important;
            border-color: rgba(139, 92, 246, 0.5) !important;
            color: #f8fafc !important;
        }

        /* Expander & Container tweaks */
        .stExpander {
            border-radius: 12px !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            background-color: rgba(15, 23, 42, 0.4) !important;
        }

        /* Highlight block */
        .snippet-box {
            background: rgba(15, 23, 42, 0.7);
            border-left: 3px solid #8b5cf6;
            padding: 12px 16px;
            border-radius: 0 8px 8px 0;
            font-family: monospace;
            font-size: 0.9rem;
            margin-bottom: 8px;
        }

        /* File uploader styling */
        section[data-testid="stFileUploader"] {
            border-radius: 16px;
            padding: 1.5rem;
            background: rgba(30, 41, 59, 0.3);
            border: 2px dashed rgba(139, 92, 246, 0.3);
        }

        /* Chat bubble overrides */
        .stChatMessage {
            border-radius: 14px;
            padding: 12px 16px;
            margin-bottom: 12px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def render_hero_header():
    """
    Renders app hero banner.
    """
    st.markdown(
        """
        <div class="hero-container">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <div class="hero-title">📄 DocuMind AI</div>
                    <div class="hero-subtitle">
                        Privacy-first, 100% local Document Analyzer & Summarizer powered by <b>LM Studio</b>.
                    </div>
                </div>
                <div>
                    <span class="badge-pill badge-local">🔒 100% Local Processing</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_metric_cards(
    total_pages: int,
    total_words: int,
    total_chars: int,
    est_read_min: int,
    picture_count: int = 0,
):
    """
    Renders stylized metric summary cards.
    """
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{total_pages:,}</div>
                <div class="metric-label">Total Pages</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with c2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{total_words:,}</div>
                <div class="metric-label">Word Count</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with c3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{total_chars:,}</div>
                <div class="metric-label">Characters</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with c4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{picture_count:,}</div>
                <div class="metric-label">Picture Count</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with c5:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">~{est_read_min} min</div>
                <div class="metric-label">Est. Read Time</div>
            </div>
            """,
            unsafe_allow_html=True
        )

def render_lm_studio_setup_guide(base_url: str):
    """
    Renders an aesthetic step-by-step setup guide for LM Studio.
    """
    st.markdown("### 🚀 Setting up LM Studio for Local Document Analysis")
    
    st.markdown(
        f"""
        To run this app fully locally without external cloud API calls, configure **LM Studio**:

        1. **Download & Install LM Studio**:
           - Get LM Studio from [https://lmstudio.ai](https://lmstudio.ai) (Windows, macOS, Linux).

        2. **Download an LLM Model**:
           - In LM Studio, search for models such as:
             - `Llama-3.2-3B-Instruct` or `Llama-3.1-8B-Instruct`
             - `Mistral-7B-Instruct-v0.3`
             - `Qwen2.5-7B-Instruct` / `Qwen2.5-Coder`
             - `Phi-3.5-mini-instruct`
           - Download your preferred quantized model (GGUF Q4_K_M or Q5_K_M recommended).

        3. **Start Local Inference Server**:
           - Open the **Developer / Local Server** tab (`<->` icon) on the left sidebar in LM Studio.
           - Select your loaded model from the top dropdown.
           - Click **Start Server** (default address: `{base_url}`).
           - Ensure CORS is enabled if accessing across network.

        4. **Connect**:
           - Enter server URL in the sidebar settings on the left and hit **Test Connection**.
        """
    )

import time

def trigger_browser_notification(title: str, body: str):
    """
    Fires a multi-layer notification:
    1. Web Audio API chime sound (works in all browsers without external files)
    2. Updates browser tab title ("🔔 Analysis Complete!")
    3. Native HTML5 desktop tray notification
    """
    safe_title = title.replace('"', '\\"').replace('\n', ' ')
    safe_body = body.replace('"', '\\"').replace('\n', ' ')
    ts = int(time.time() * 1000)
    
    js_code = f"""
    <script>
    (function() {{
        var title = "{safe_title}";
        var body = "{safe_body}";
        var ts = {ts};

        // 1. Play Web Audio API Chime Sound
        try {{
            var audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            var osc = audioCtx.createOscillator();
            var gain = audioCtx.createGain();
            osc.type = "sine";
            osc.frequency.setValueAtTime(587.33, audioCtx.currentTime); // D5
            osc.frequency.setValueAtTime(880, audioCtx.currentTime + 0.12); // A5
            gain.gain.setValueAtTime(0.15, audioCtx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.35);
            osc.connect(gain);
            gain.connect(audioCtx.destination);
            osc.start();
            osc.stop(audioCtx.currentTime + 0.35);
        }} catch(e) {{}}

        // 2. Flash Parent Browser Tab Title
        try {{
            if (window.parent && window.parent.document) {{
                window.parent.document.title = "🔔 Analysis Complete! - DocuMind AI";
                setTimeout(function() {{
                    window.parent.document.title = "DocuMind Local AI - Document Analyzer";
                }}, 6000);
            }}
        }} catch(e) {{}}

        // 3. Desktop Tray Notification with unique tag
        if ("Notification" in window) {{
            var options = {{
                body: body,
                tag: "documind_notif_" + ts,
                requireInteraction: false
            }};
            if (Notification.permission === "granted") {{
                new Notification(title, options);
            }} else if (Notification.permission !== "denied") {{
                Notification.requestPermission().then(function (permission) {{
                    if (permission === "granted") {{
                        new Notification(title, options);
                    }}
                }});
            }}
        }}
    }})();
    </script>
    """
    components.html(js_code, height=0, width=0)


def render_tts_player(
    summary_text: str,
    language: str = "Same as Document",
    summary_id: Optional[int] = None,
    existing_audio: Optional[bytes] = None,
):
    """
    Renders an ultra-modern, glassmorphic Text-to-Speech (TTS) audio control panel.
    Persists audio bytes to SQLite database when synthesized or available.
    """
    if not summary_text or not summary_text.strip():
        return

    import hashlib
    from src.tts import generate_tts_audio_bytes
    from src.db import update_summary_audio

    text_hash = hashlib.md5(f"{summary_text}_{language}".encode("utf-8")).hexdigest()
    tts_key = f"tts_audio_{text_hash}"

    # Auto-load existing audio from SQLite cache if present
    if tts_key not in st.session_state and existing_audio:
        st.session_state[tts_key] = existing_audio

    has_audio = tts_key in st.session_state and st.session_state[tts_key] is not None
    status_badge = (
        '<span style="background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(52, 211, 153, 0.3); color: #34d399; padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; letter-spacing: 0.03em;">🟢 AUDIO READY</span>'
        if has_audio
        else '<span style="background: rgba(148, 163, 184, 0.15); border: 1px solid rgba(148, 163, 184, 0.3); color: #94a3b8; padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; letter-spacing: 0.03em;">⏳ NOT SYNTHESIZED</span>'
    )

    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, rgba(30, 27, 75, 0.75) 0%, rgba(15, 23, 42, 0.85) 50%, rgba(49, 46, 129, 0.65) 100%);
            border: 1px solid rgba(139, 92, 246, 0.3);
            border-radius: 16px;
            padding: 1.4rem 1.6rem;
            box-shadow: 0 12px 30px -10px rgba(0, 0, 0, 0.4), inset 0 1px 1px rgba(255, 255, 255, 0.1);
            margin-top: 1rem;
            margin-bottom: 1rem;
        ">
            <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <div style="
                        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
                        width: 42px; height: 42px; border-radius: 12px;
                        display: flex; align-items: center; justify-content: center;
                        font-size: 1.3rem; box-shadow: 0 4px 14px rgba(99, 102, 241, 0.4);
                    ">🎧</div>
                    <div>
                        <div style="font-family: 'Outfit', sans-serif; font-size: 1.15rem; font-weight: 700; color: #f8fafc;">
                            Audio Summary Voiceover
                        </div>
                        <div style="font-size: 0.82rem; color: #94a3b8;">
                            Synthesize and stream audio report ({language})
                        </div>
                    </div>
                </div>
                <div>{status_badge}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c_left, c_right = st.columns([1, 2])
    with c_left:
        btn_label = "⚡ Re-synthesize Voiceover" if has_audio else "🔊 Generate Audio Voiceover"
        if st.button(btn_label, key=f"btn_gen_tts_{text_hash}", width="stretch", type="primary"):
            with st.spinner("Synthesizing neural audio voiceover..."):
                try:
                    audio_bytes = generate_tts_audio_bytes(summary_text, language=language)
                    st.session_state[tts_key] = audio_bytes
                    if summary_id:
                        update_summary_audio(summary_id, audio_bytes)
                    st.rerun()
                except Exception as e:
                    st.error(f"⚠️ TTS Generation failed: {e}")

    with c_right:
        if has_audio:
            st.audio(st.session_state[tts_key], format="audio/wav", autoplay=False)
        else:
            st.info("Click **Generate Audio Voiceover** to create and play a neural voiceover.", icon="🎧")


def render_sqlite_db_viewer(db_path: Optional[str] = None):
    """
    Renders an interactive SQLite Database Viewer component in Streamlit.
    """
    import json
    import csv
    import io
    from src.db import (
        get_database_stats,
        get_table_names,
        get_table_schema,
        get_table_data,
        execute_readonly_query,
        clear_table_records,
    )

    st.markdown("### 🗄️ SQLite Database Explorer")
    st.caption("Inspect stored document caches, generated summaries, chat history, and database schema.")

    try:
        stats = get_database_stats(db_path)
    except Exception as err:
        st.error(f"Failed to read SQLite database: {err}")
        return

    # Top Metrics Header
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Database File Size", stats["file_size_formatted"])
    with m2:
        st.metric("Total Tables", stats["total_tables"])
    with m3:
        st.metric("Total Records", f"{stats['total_rows']:,}")
    with m4:
        st.metric("Journal Mode", stats["journal_mode"])

    st.markdown(f"**Database Location:** `{stats['db_path']}`")

    # DB Viewer Tabs
    db_tab1, db_tab2, db_tab3 = st.tabs([
        "📋 Table Explorer",
        "💻 Read-Only SQL Console",
        "⚙️ Database Stats & Actions",
    ])

    # --- TAB 1: TABLE EXPLORER ---
    with db_tab1:
        tables = get_table_names(db_path)
        if not tables:
            st.info("No user tables found in database.")
            return

        col_sel, col_srch, col_lim = st.columns([2, 3, 1.5])
        with col_sel:
            selected_table = st.selectbox(
                "Select Table",
                options=tables,
                index=0,
                key="db_viewer_table_select",
            )
        with col_srch:
            search_term = st.text_input(
                "Filter Rows",
                placeholder="Search text in table...",
                key="db_viewer_search_input",
            )
        with col_lim:
            limit_val = st.selectbox(
                "Rows per Page",
                options=[10, 25, 50, 100],
                index=1,
                key="db_viewer_limit_select",
            )

        col_names, row_dicts, total_count = get_table_data(
            table_name=selected_table,
            limit=limit_val,
            offset=0,
            search_query=search_term,
            db_path=db_path,
        )

        st.markdown(
            f"Showing **{len(row_dicts)}** of **{total_count}** matching row(s) in `{selected_table}`"
        )

        if row_dicts:
            # Display Table Data Grid
            st.dataframe(row_dicts, width="stretch")

            # Export Buttons
            exp_c1, exp_c2 = st.columns(2)
            with exp_c1:
                # Generate CSV download
                csv_buffer = io.StringIO()
                if row_dicts:
                    writer = csv.DictWriter(csv_buffer, fieldnames=col_names)
                    writer.writeheader()
                    writer.writerows(row_dicts)
                st.download_button(
                    label=f"📥 Export `{selected_table}` to CSV",
                    data=csv_buffer.getvalue(),
                    file_name=f"{selected_table}_export.csv",
                    mime="text/csv",
                    width="stretch",
                    key=f"dl_csv_{selected_table}",
                )

            with exp_c2:
                # Generate JSON download
                json_data = json.dumps(row_dicts, indent=2, ensure_ascii=False)
                st.download_button(
                    label=f"📥 Export `{selected_table}` to JSON",
                    data=json_data,
                    file_name=f"{selected_table}_export.json",
                    mime="application/json",
                    width="stretch",
                    key=f"dl_json_{selected_table}",
                )

            # Record Detail Viewer
            with st.expander(f"🔍 Inspect Row JSON Details (`{selected_table}`)", expanded=False):
                row_idx = st.number_input(
                    "Row Index to Inspect",
                    min_value=0,
                    max_value=max(0, len(row_dicts) - 1),
                    value=0,
                    step=1,
                    key="db_viewer_row_idx",
                )
                if row_dicts and 0 <= row_idx < len(row_dicts):
                    st.json(row_dicts[int(row_idx)])

        else:
            st.warning(f"No records found in table `{selected_table}`.")

        # Table Schema Metadata Expander
        with st.expander(f"📐 Table Schema & Columns (`{selected_table}`)", expanded=False):
            schema = get_table_schema(selected_table, db_path)
            st.dataframe(schema, width="stretch")

    # --- TAB 2: READ-ONLY SQL CONSOLE ---
    with db_tab2:
        st.markdown("#### 💻 Execute Custom Read-Only SQL Query")
        st.caption("Execute SELECT, EXPLAIN, or PRAGMA statements to analyze your data.")

        preset_queries = {
            "Select All Documents": "SELECT file_hash, file_name, file_size, total_pages, total_words, created_at FROM documents ORDER BY created_at DESC;",
            "Select Recent Summaries": "SELECT id, file_hash, preset_name, language, model, created_at FROM summaries ORDER BY created_at DESC LIMIT 20;",
            "Select Recent Chat Messages": "SELECT id, file_hash, role, substr(content, 1, 80) AS snippet, created_at FROM chat_history ORDER BY id DESC LIMIT 20;",
            "Summary Count by Preset": "SELECT preset_name, COUNT(*) as report_count FROM summaries GROUP BY preset_name ORDER BY report_count DESC;",
        }

        col_preset, _ = st.columns([3, 1])
        with col_preset:
            selected_preset_label = st.selectbox(
                "Quick Preset Query",
                options=["-- Custom Query --"] + list(preset_queries.keys()),
                key="db_sql_preset_select",
            )

        default_sql = preset_queries.get(
            selected_preset_label,
            "SELECT file_name, file_size, total_pages, created_at FROM documents ORDER BY created_at DESC;",
        )

        user_sql = st.text_area(
            "SQL Query (SELECT / EXPLAIN / PRAGMA)",
            value=default_sql,
            height=110,
            key="db_viewer_sql_input",
        )

        if st.button("🚀 Run SQL Query", type="primary", key="btn_run_sql"):
            if not user_sql.strip():
                st.warning("Please enter a SQL query.")
            else:
                try:
                    cols, rows = execute_readonly_query(user_sql, db_path=db_path)
                    st.success(f"Query returned {len(rows)} row(s).")
                    if rows:
                        st.dataframe(rows, width="stretch")
                    else:
                        st.info("Query executed successfully but returned 0 rows.")
                except Exception as e:
                    st.error(f"❌ SQL Execution Error: {str(e)}")

    # --- TAB 3: STATS & ACTIONS ---
    with db_tab3:
        st.markdown("#### 📊 Table Record Counts")
        for tbl, count in stats["table_counts"].items():
            st.write(f"• Table **`{tbl}`**: `{count}` row(s)")

        st.markdown("---")
        st.markdown("#### 🗑️ Purge Table Data")
        st.warning("Warning: Purging a table permanently deletes all its stored records.")

        target_purge_table = st.selectbox(
            "Select Table to Clear",
            options=get_table_names(db_path),
            key="purge_table_select",
        )
        confirm_purge = st.checkbox(
            f"I confirm I want to clear all records from `{target_purge_table}`",
            key="confirm_purge_checkbox",
        )

        if st.button(f"🔥 Clear All Records from `{target_purge_table}`", type="secondary", disabled=not confirm_purge):
            try:
                clear_table_records(target_purge_table, db_path)
                st.success(f"Table `{target_purge_table}` cleared successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to clear table: {e}")



