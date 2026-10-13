import streamlit as st
import datetime
import base64
from src.pdf_processor import extract_document_data, chunk_pdf_pages, search_in_pages
from src.llm_client import (
    DEFAULT_BASE_URL,
    DEFAULT_API_KEY,
    PROMPT_PRESETS,
    get_openai_client,
    check_lm_studio_connection,
    run_single_pass_summary,
    run_image_summary,
    ImageAnalysisError,
    map_reduce_summary,
    should_use_map_reduce,
    chat_stream_response,
)
from src.ui import (
    inject_custom_css,
    render_hero_header,
    render_metric_cards,
    render_lm_studio_setup_guide,
    trigger_browser_notification,
    render_tts_player,
)
from src.db import (
    init_db,
    calculate_file_hash,
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
)

# Initialize SQLite Database Schema
init_db()

st.set_page_config(
    page_title="DocuMind Local AI - Document Analyzer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject CSS styling
inject_custom_css()

# Initialize Session State
if "pdf_data" not in st.session_state:
    st.session_state.pdf_data = None
if "file_name" not in st.session_state:
    st.session_state.file_name = None
if "file_hash" not in st.session_state:
    st.session_state.file_hash = None
if "from_cache" not in st.session_state:
    st.session_state.from_cache = False
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "summary_output" not in st.session_state:
    st.session_state.summary_output = ""
if "current_preset" not in st.session_state:
    st.session_state.current_preset = "Executive Summary"
if "stop_requested" not in st.session_state:
    st.session_state.stop_requested = False


# Helper function to switch active document from SQLite cache
def load_document_from_db(file_hash: str):
    doc_record = get_document_by_hash(file_hash)
    if doc_record:
        st.session_state.pdf_data = doc_record["pdf_data"]
        st.session_state.file_name = doc_record["file_name"]
        st.session_state.file_hash = doc_record["file_hash"]
        st.session_state.from_cache = True
        st.session_state.chat_history = get_chat_history_for_document(file_hash)
        summaries = get_summaries_for_document(file_hash)
        st.session_state.summary_output = summaries[0]["summary_text"] if summaries else ""
        st.session_state.stop_requested = False


# --- SIDEBAR ---
with st.sidebar:
    st.markdown("## ⚙️ Control Center")

    # Recent Documents Library Expander
    recent_docs = list_recent_documents(limit=15)
    if recent_docs:
        with st.expander("📚 Recent Documents Library", expanded=False):
            doc_options = {f"{doc['file_name']} ({doc['total_pages']} p.)": doc['file_hash'] for doc in recent_docs}
            selected_doc_label = st.selectbox(
                "Select Saved Document",
                options=["-- Choose Document --"] + list(doc_options.keys()),
                key="recent_doc_select"
            )
            
            rec_c1, rec_c2 = st.columns(2)
            with rec_c1:
                if st.button("📂 Load Document", width="stretch") and selected_doc_label != "-- Choose Document --":
                    load_document_from_db(doc_options[selected_doc_label])
                    st.rerun()
            with rec_c2:
                if st.button("🗑️ Delete Record", width="stretch") and selected_doc_label != "-- Choose Document --":
                    delete_document(doc_options[selected_doc_label])
                    if st.session_state.file_hash == doc_options[selected_doc_label]:
                        st.session_state.pdf_data = None
                        st.session_state.file_name = None
                        st.session_state.file_hash = None
                        st.session_state.chat_history = []
                        st.session_state.summary_output = ""
                    st.success("Document deleted from local SQLite store.")
                    st.rerun()

    with st.expander("🔌 LM Studio Connection", expanded=True):
        lm_url = st.text_input("LM Studio Server URL", value=DEFAULT_BASE_URL, help="Default: http://localhost:1234/v1")
        lm_key = st.text_input("API Key", value=DEFAULT_API_KEY, type="password", help="Leave as default for local LM Studio")

        col_conn1, col_conn2 = st.columns([1, 1])
        with col_conn1:
            test_conn_btn = st.button("🔌 Check Connection", width="stretch")
        with col_conn2:
            if st.button("🔄 Reload App", width="stretch", help="Force reload and refresh the application"):
                st.rerun()

        # Check server status
        is_connected, status_msg, available_models = check_lm_studio_connection(lm_url, lm_key)

        if is_connected:
            st.markdown(
                f"""
                <div style="padding: 10px 14px; background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(52, 211, 153, 0.3); border-radius: 10px; margin: 10px 0;">
                    <span class="badge-pill badge-online">🟢 SERVER ONLINE</span><br/>
                    <small style="color: #cbd5e1; display: inline-block; margin-top: 6px;">{status_msg}</small>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div style="padding: 10px 14px; background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(248, 113, 113, 0.3); border-radius: 10px; margin: 10px 0;">
                    <span class="badge-pill badge-offline">🔴 SERVER OFFLINE</span><br/>
                    <small style="color: #fca5a5; display: inline-block; margin-top: 6px;">{status_msg}</small>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with st.expander("🤖 Model Selection", expanded=True):
        if available_models:
            selected_model = st.selectbox("Active Model", options=available_models, index=0)
        else:
            selected_model = st.text_input("Model Name", value="local-model")

    with st.expander("🎛️ Processing Settings", expanded=False):
        temperature = st.slider("Temperature (Creativity)", min_value=0.0, max_value=1.0, value=0.3, step=0.05)
        max_chunk_chars = st.slider(
            "Chunk Size (Characters)",
            min_value=1500,
            max_value=8000,
            value=3500,
            step=500,
            help="Controls size of text chunks for large documents",
        )
        enable_map_reduce = st.checkbox(
            "Enable Map-Reduce for Large Documents",
            value=True,
            help="Splits large documents into chunks and synthesizes them",
        )
        enable_notifications = st.checkbox(
            "🔔 Desktop Notifications when ready",
            value=True,
            help="Triggers system desktop notification when analysis finishes",
        )

# --- MAIN APP LAYOUT ---
render_hero_header()

# File Uploader Section
uploaded_file = st.file_uploader(
    "Upload a document to begin analysis",
    type=[
        "pdf",
        "md",
        "markdown",
        "txt",
        "json",
        "csv",
        "png",
        "jpg",
        "jpeg",
        "webp",
        "py",
        "pyi",
        "cpp",
        "cxx",
        "cc",
        "c",
        "h",
        "hpp",
    ],
    key="pdf_uploader",
)

if uploaded_file is not None:
    file_bytes = uploaded_file.read()
    file_hash = calculate_file_hash(file_bytes)

    # Check if this file is different from current active document
    if st.session_state.file_hash != file_hash:
        # First check if document already exists in SQLite cache
        cached_doc = get_document_by_hash(file_hash)
        if cached_doc:
            st.session_state.pdf_data = cached_doc["pdf_data"]
            st.session_state.file_name = uploaded_file.name
            st.session_state.file_hash = file_hash
            st.session_state.from_cache = True
            st.session_state.chat_history = get_chat_history_for_document(file_hash)
            saved_summaries = get_summaries_for_document(file_hash)
            st.session_state.summary_output = saved_summaries[0]["summary_text"] if saved_summaries else ""
            st.session_state.stop_requested = False
        else:
            with st.spinner("📄 Extracting text and metadata from document..."):
                try:
                    pdf_data = extract_document_data(
                        file_bytes,
                        uploaded_file.name,
                        include_images=True,
                    )
                except ValueError as error:
                    st.session_state.pdf_data = None
                    st.error(f"⚠️ Could not read document: {error}")
                else:
                    # Save parsed document to SQLite
                    save_document(file_hash, uploaded_file.name, file_bytes, pdf_data)
                    st.session_state.pdf_data = pdf_data
                    st.session_state.file_name = uploaded_file.name
                    st.session_state.file_hash = file_hash
                    st.session_state.from_cache = False
                    st.session_state.chat_history = []
                    st.session_state.summary_output = ""
                    st.session_state.stop_requested = False

pdf_data = st.session_state.pdf_data

if pdf_data:
    is_standalone_image = pdf_data.get("input_type") == "image"
    if is_standalone_image:
        st.info("Image analysis requires a vision-capable model in LM Studio. Model names alone do not confirm image support.")
    cache_badge = (
        '<span style="background: rgba(59, 130, 246, 0.15); border: 1px solid rgba(96, 165, 250, 0.4); color: #93c5fd; padding: 3px 8px; border-radius: 6px; font-size: 0.8rem; margin-left: 10px;">⚡ SQLite Cached</span>'
        if st.session_state.from_cache
        else '<span style="background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(52, 211, 153, 0.4); color: #6ee7b7; padding: 3px 8px; border-radius: 6px; font-size: 0.8rem; margin-left: 10px;">💾 Saved to SQLite</span>'
    )
    st.markdown(f"#### 📑 Document: `{st.session_state.file_name}` {cache_badge}", unsafe_allow_html=True)

    # Display Stats Cards
    render_metric_cards(
        total_pages=pdf_data["total_pages"],
        total_words=pdf_data["total_words"],
        total_chars=pdf_data["total_chars"],
        est_read_min=pdf_data["est_reading_time"],
    )

    # Document metadata expander
    with st.expander("ℹ️ Document Metadata & File Details"):
        meta = pdf_data["metadata"]
        m_col1, m_col2 = st.columns(2)
        with m_col1:
            st.write(f"**Title:** {meta['title']}")
            st.write(f"**Author:** {meta['author']}")
            st.write(f"**Subject:** {meta['subject']}")
        with m_col2:
            st.write(f"**Creator:** {meta['creator']}")
            st.write(f"**Producer:** {meta['producer']}")
            st.write(f"**Creation Date:** {meta['creation_date']}")

    st.markdown("<br/>", unsafe_allow_html=True)

    # --- TABS ---
    tab_summary, tab_chat, tab_inspect, tab_setup = st.tabs([
        "📊 Summarization & Analysis",
        "💬 Chat with Document",
        "🔍 Inspection & Search",
        "🛠️ LM Studio Setup",
    ])

    # --- TAB 1: SUMMARIZATION & ANALYSIS ---
    with tab_summary:
        st.markdown("### 🎯 Select Analysis Mode")

        sum_col1, sum_col2 = st.columns([1, 2])

        with sum_col1:
            preset_choice = st.selectbox(
                "📊 Analysis Preset",
                options=list(PROMPT_PRESETS.keys()),
                index=0,
                key="preset_selectbox",
                help="Select the prompt preset or custom prompt for document analysis",
            )

            language_choice = st.selectbox(
                "🌐 Output Language",
                options=["Same as Document", "English", "Finnish"],
                index=0,
                help="Choose summary report output language",
            )

            custom_instruction = ""
            if preset_choice == "Custom Prompt":
                custom_instruction = st.text_area(
                    "Custom Analysis Prompt",
                    placeholder="e.g., Extract all financial figures, budget estimates, and financial risks mentioned in this report...",
                    height=120,
                )
            else:
                custom_instruction = st.text_input(
                    "Additional Guidance (Optional)",
                    placeholder="e.g., Focus specifically on section 3...",
                )

            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                start_analysis = st.button("🚀 Run Analysis", type="primary", width="stretch")
            with btn_col2:
                stop_analysis = st.button("⏹️ Stop Analysis", type="secondary", width="stretch")
                if stop_analysis:
                    st.session_state.stop_requested = True

            # Display Saved Summaries Selector if available
            saved_summaries = get_summaries_for_document(st.session_state.file_hash) if st.session_state.file_hash else []
            if saved_summaries:
                st.markdown("---")
                st.markdown("##### 📜 Saved Analysis Reports")
                sum_labels = {
                    f"[{s['created_at'][:16]}] {s['preset_name']} ({s['language']})": s
                    for s in saved_summaries
                }
                selected_sum_label = st.selectbox(
                    "Load Previous Report",
                    options=list(sum_labels.keys()),
                    key="saved_summary_select"
                )
                sum_c1, sum_c2 = st.columns(2)
                with sum_c1:
                    if st.button("📖 View Selected Report", width="stretch"):
                        st.session_state.summary_output = sum_labels[selected_sum_label]["summary_text"]
                        st.rerun()
                with sum_c2:
                    if st.button("🗑️ Delete Report", width="stretch"):
                        delete_summary(sum_labels[selected_sum_label]["id"])
                        remaining = get_summaries_for_document(st.session_state.file_hash)
                        st.session_state.summary_output = remaining[0]["summary_text"] if remaining else ""
                        st.rerun()

        with sum_col2:
            st.markdown("#### 📝 Analysis Report Output")

            output_container = st.empty()

            if start_analysis:
                st.session_state.stop_requested = False
                if not is_connected:
                    st.error("❌ Cannot run analysis: LM Studio local server is offline or unreachable. Please check LM Studio in sidebar.")
                else:
                    client = get_openai_client(lm_url, lm_key)
                    full_text = pdf_data["full_text"]

                    # Prepare Chunks
                    chunks = [] if is_standalone_image else chunk_pdf_pages(pdf_data["pages"], max_chars=max_chunk_chars)

                    try:
                        if is_standalone_image:
                            st.session_state.summary_output = ""
                            with st.spinner("Analyzing image with the selected LM Studio model..."):
                                generator = run_image_summary(
                                    client=client,
                                    model=selected_model,
                                    page_images=pdf_data["page_images"],
                                    preset_name=preset_choice,
                                    custom_instruction=custom_instruction,
                                    language=language_choice,
                                    temperature=temperature,
                                    check_stop=lambda: st.session_state.get("stop_requested", False),
                                )
                                st.session_state.summary_output = output_container.write_stream(generator)
                        elif should_use_map_reduce(
                            st.session_state.file_name, full_text, len(chunks), enable_map_reduce
                        ):
                            status_box = st.status(f"Processing multi-page document across {len(chunks)} chunks...", expanded=True)

                            def update_status(msg):
                                status_box.write(f"⏳ {msg}")

                            generator = map_reduce_summary(
                                client=client,
                                model=selected_model,
                                chunks=chunks,
                                preset_name=preset_choice,
                                custom_instruction=custom_instruction,
                                language=language_choice,
                                temperature=temperature,
                                status_callback=update_status,
                                check_stop=lambda: st.session_state.get("stop_requested", False),
                                page_images=pdf_data.get("page_images", []),
                            )

                            full_response = output_container.write_stream(generator)
                            if st.session_state.stop_requested:
                                status_box.update(label="⏹️ Analysis Stopped", state="error", expanded=False)
                            else:
                                status_box.update(label="✅ Analysis Complete!", state="complete", expanded=False)
                            st.session_state.summary_output = full_response
                        else:
                            with st.spinner("Generating local AI analysis..."):
                                generator = run_single_pass_summary(
                                    client=client,
                                    model=selected_model,
                                    document_text=full_text,
                                    preset_name=preset_choice,
                                    custom_instruction=custom_instruction,
                                    language=language_choice,
                                    temperature=temperature,
                                    check_stop=lambda: st.session_state.get("stop_requested", False),
                                    page_images=pdf_data.get("page_images", []),
                                )
                                full_response = output_container.write_stream(generator)
                                st.session_state.summary_output = full_response

                        # Save generated summary to SQLite
                        if st.session_state.summary_output and not st.session_state.stop_requested and st.session_state.file_hash:
                            save_summary(
                                file_hash=st.session_state.file_hash,
                                preset_name=preset_choice,
                                language=language_choice,
                                summary_text=st.session_state.summary_output,
                                custom_instruction=custom_instruction,
                                model=selected_model,
                            )

                        # Fire desktop tray notification if enabled and completed cleanly
                        if enable_notifications and not st.session_state.stop_requested and st.session_state.summary_output:
                            trigger_browser_notification(
                                title="DocuMind AI: Analysis Ready! 📄",
                                body=f"The {preset_choice} for {st.session_state.file_name} has completed.",
                            )
                    except Exception as e:
                        st.error(f"⚠️ Error during LLM generation: {str(e)}")
            elif st.session_state.summary_output:
                output_container.markdown(st.session_state.summary_output)
            else:
                output_container.info("Select an analysis preset on the left and click **Run Analysis** to generate insights.")

            # Export & Audio Options
            if st.session_state.summary_output:
                st.markdown("---")
                
                # Text-to-Speech Player Component
                render_tts_player(st.session_state.summary_output, language=language_choice)

                st.markdown("##### 📥 Export Report")
                exp_c1, exp_c2 = st.columns(2)
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                report_filename = f"Summary_{st.session_state.file_name}_{timestamp}.md"

                with exp_c1:
                    st.download_button(
                        label="📄 Download Markdown (.md)",
                        data=st.session_state.summary_output,
                        file_name=report_filename,
                        mime="text/markdown",
                        width="stretch",
                    )
                with exp_c2:
                    st.download_button(
                        label="📝 Download Text (.txt)",
                        data=st.session_state.summary_output,
                        file_name=f"Summary_{st.session_state.file_name}_{timestamp}.txt",
                        mime="text/plain",
                        width="stretch",
                    )

    # --- TAB 2: CHAT WITH DOCUMENT ---
    with tab_chat:
        st.markdown("### 💬 Interactive Q&A with Document")
        st.caption("Ask questions about specific sections, figures, statements, or details in this document.")

        # Display suggestion buttons
        st.markdown("**Suggested Quick Questions:**")
        q_cols = st.columns(3)
        suggested_q = None
        with q_cols[0]:
            if st.button("📌 Summarize main points", key="sq1", width="stretch"):
                suggested_q = "What are the main key points of this document?"
        with q_cols[1]:
            if st.button("❓ Key conclusions & outcomes", key="sq2", width="stretch"):
                suggested_q = "What are the primary conclusions and final outcomes stated in the text?"
        with q_cols[2]:
            if st.button("🔍 Methods & Methodology", key="sq3", width="stretch"):
                suggested_q = "What methods, techniques, or datasets were used in this document?"

        # Clear chat history button
        if st.session_state.chat_history:
            if st.button("🗑️ Clear Chat History", type="secondary"):
                if st.session_state.file_hash:
                    clear_chat_history_for_document(st.session_state.file_hash)
                st.session_state.chat_history = []
                st.rerun()

        # Display Chat History
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Chat input box
        prompt_input = st.chat_input("Ask any question about this document...")

        user_query = prompt_input or suggested_q

        if user_query:
            if not is_connected:
                st.error("❌ Cannot answer: LM Studio local server is offline.")
            else:
                # Add user message to state and SQLite DB
                st.session_state.chat_history.append({"role": "user", "content": user_query})
                if st.session_state.file_hash:
                    save_chat_message(st.session_state.file_hash, "user", user_query)

                with st.chat_message("user"):
                    st.markdown(user_query)

                # Generate Assistant Response
                with st.chat_message("assistant"):
                    client = get_openai_client(lm_url, lm_key)
                    doc_chunks = [] if is_standalone_image else chunk_pdf_pages(pdf_data["pages"], max_chars=max_chunk_chars)
                    generator = chat_stream_response(
                        client=client,
                        model=selected_model,
                        document_context=pdf_data["full_text"],
                        chat_history=st.session_state.chat_history[:-1],
                        user_question=user_query,
                        temperature=temperature,
                        chunks=doc_chunks,
                        page_images=pdf_data["page_images"] if is_standalone_image else None,
                    )
                    try:
                        assistant_response = st.write_stream(generator)
                    except ImageAnalysisError as error:
                        st.error(str(error))
                    else:
                        st.session_state.chat_history.append({"role": "assistant", "content": assistant_response})
                        if st.session_state.file_hash:
                            save_chat_message(st.session_state.file_hash, "assistant", assistant_response)

    # --- TAB 3: INSPECTION & SEARCH ---
    with tab_inspect:
        st.markdown("### 🔍 Document Search & Page Inspector")

        insp_tab1, insp_tab2, insp_tab3 = st.tabs(["🔎 Keyword Search", "📖 Page Viewer", "🧩 Chunk Inspector"])

        with insp_tab1:
            search_query = st.text_input("Search term or phrase within document", placeholder="Type keywords...")
            if search_query:
                results = search_in_pages(pdf_data["pages"], search_query)
                if results:
                    st.success(f"Found match(es) on {len(results)} page(s):")
                    for res in results:
                        st.markdown(
                            f"""
                            <div class="snippet-box">
                                <b>Page {res['page_num']}</b> ({res['matches_on_page']} match(es)):<br/>
                                <span style="color: #cbd5e1;">{res['snippet']}</span>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                else:
                    st.warning(f"No occurrences of '{search_query}' found in document.")

        with insp_tab2:
            page_numbers = [p["page_num"] for p in pdf_data["pages"]]
            selected_page_num = st.selectbox("Select Page Number", options=page_numbers, index=0)
            page_obj = next(p for p in pdf_data["pages"] if p["page_num"] == selected_page_num)

            st.markdown(f"#### Page {selected_page_num} ({page_obj['word_count']} words, {page_obj['char_count']} chars)")
            if is_standalone_image:
                image_url = pdf_data["page_images"][0]["data_url"]
                st.image(base64.b64decode(image_url.split(",", 1)[1]))
            st.text_area("Page Text Content", value=page_obj["text"], height=400, key=f"page_text_{selected_page_num}")

        with insp_tab3:
            chunks = chunk_pdf_pages(pdf_data["pages"], max_chars=max_chunk_chars)
            st.info(f"Document segmented into {len(chunks)} chunk(s) based on max chunk size of {max_chunk_chars} characters.")
            for c in chunks:
                with st.expander(f"🧩 Chunk #{c['chunk_id']} ({c['page_range']}) - {len(c['text'])} characters"):
                    st.text(c["text"])

    # --- TAB 4: SETUP GUIDE ---
    with tab_setup:
        render_lm_studio_setup_guide(lm_url)

else:
    # Empty state prompt
    render_lm_studio_setup_guide(lm_url)
