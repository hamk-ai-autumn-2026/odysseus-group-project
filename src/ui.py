import streamlit as st
import streamlit.components.v1 as components

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
            font-weight: 600 !important;
            background-color: rgba(30, 41, 59, 0.4) !important;
            border: 1px solid rgba(255, 255, 255, 0.05) !important;
            color: #94a3b8 !important;
            transition: all 0.2s ease !important;
        }

        .stTabs [aria-selected="true"] {
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

def render_metric_cards(total_pages: int, total_words: int, total_chars: int, est_read_min: int):
    """
    Renders stylized metric summary cards.
    """
    c1, c2, c3, c4 = st.columns(4)
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


