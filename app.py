import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# --- Inject secret into env BEFORE importing graph ---
try:
    import streamlit as st
    _key = st.secrets.get("GROQ_API_KEY", "")
    if _key:
        os.environ["GROQ_API_KEY"] = _key
except Exception:
    pass

import zipfile
import io
import streamlit as st
from graph import agent, save_files

st.set_page_config(
    page_title="CodeForge AI",
    page_icon="⚡",
    layout="wide"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:ital,wght@0,400;0,700;1,400&family=Syne:wght@400;600;700;800&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

.stApp {
    background-color: #0a0a0a;
    background-image:
        linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px);
    background-size: 40px 40px;
    font-family: 'Syne', sans-serif;
    color: #f0f0f0;
}

.block-container {
    max-width: 1000px !important;
    padding: 3rem 2rem !important;
}

/* ── Header ── */
.forge-header {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    margin-bottom: 3.5rem;
    border-left: 4px solid #e8ff47;
    padding-left: 1.5rem;
}
.forge-tag {
    font-family: 'Space Mono', monospace;
    font-size: 11px;
    letter-spacing: 4px;
    color: #e8ff47;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
}
.forge-title {
    font-size: clamp(42px, 7vw, 72px);
    font-weight: 800;
    line-height: 1;
    color: #f0f0f0;
    letter-spacing: -2px;
}
.forge-title span {
    color: #e8ff47;
}
.forge-sub {
    margin-top: 0.75rem;
    font-family: 'Space Mono', monospace;
    font-size: 13px;
    color: #666;
    letter-spacing: 0.5px;
}

/* ── Input panel ── */
.panel {
    background: #111;
    border: 1px solid #222;
    border-radius: 2px;
    padding: 2rem;
    margin-bottom: 1.5rem;
    position: relative;
}
.panel::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 40px; height: 3px;
    background: #e8ff47;
}
.panel-label {
    font-family: 'Space Mono', monospace;
    font-size: 10px;
    letter-spacing: 3px;
    color: #555;
    text-transform: uppercase;
    margin-bottom: 1rem;
}

/* ── Streamlit overrides ── */
.stTextArea textarea {
    background: #0a0a0a !important;
    border: 1px solid #333 !important;
    border-radius: 2px !important;
    color: #f0f0f0 !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 13px !important;
    padding: 1rem !important;
    resize: vertical !important;
}
.stTextArea textarea:focus {
    border-color: #e8ff47 !important;
    box-shadow: 0 0 0 1px #e8ff47 !important;
}
.stTextArea label { display: none !important; }

.stButton > button {
    background: #e8ff47 !important;
    color: #0a0a0a !important;
    border: none !important;
    border-radius: 2px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 15px !important;
    letter-spacing: 1px !important;
    height: 52px !important;
    width: 100% !important;
    text-transform: uppercase !important;
    transition: all 0.15s ease !important;
    cursor: pointer !important;
}
.stButton > button:hover {
    background: #f5ff8a !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(232, 255, 71, 0.25) !important;
}
.stButton > button:active {
    transform: translateY(0) !important;
}

/* ── Success / error ── */
.stSuccess {
    background: #0f1a00 !important;
    border: 1px solid #e8ff47 !important;
    border-radius: 2px !important;
    color: #e8ff47 !important;
}
.stAlert { border-radius: 2px !important; }

/* ── Stats bar ── */
.stats-bar {
    display: flex;
    gap: 2px;
    margin-bottom: 2rem;
}
.stat-chip {
    background: #111;
    border: 1px solid #222;
    padding: 0.6rem 1.2rem;
    font-family: 'Space Mono', monospace;
    font-size: 11px;
    color: #555;
    flex: 1;
    text-align: center;
}
.stat-chip b {
    display: block;
    font-size: 18px;
    color: #e8ff47;
    font-family: 'Syne', sans-serif;
    font-weight: 700;
}

/* ── Output section ── */
.section-title {
    font-family: 'Space Mono', monospace;
    font-size: 10px;
    letter-spacing: 4px;
    color: #555;
    text-transform: uppercase;
    padding: 0.5rem 0;
    border-bottom: 1px solid #1a1a1a;
    margin-bottom: 1.5rem;
}

/* ── Expanders ── */
.streamlit-expanderHeader {
    background: #111 !important;
    border: 1px solid #222 !important;
    border-radius: 2px !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 12px !important;
    color: #aaa !important;
    padding: 0.75rem 1rem !important;
}
.streamlit-expanderHeader:hover {
    border-color: #e8ff47 !important;
    color: #e8ff47 !important;
}
.streamlit-expanderContent {
    background: #0d0d0d !important;
    border: 1px solid #1a1a1a !important;
    border-top: none !important;
}

/* ── Code blocks ── */
.stCodeBlock {
    border-radius: 2px !important;
}
pre {
    background: #0a0a0a !important;
    border: 1px solid #1a1a1a !important;
    border-radius: 2px !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 12px !important;
}

/* ── Download button ── */
.stDownloadButton > button {
    background: transparent !important;
    border: 1px solid #e8ff47 !important;
    color: #e8ff47 !important;
    border-radius: 2px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    letter-spacing: 1px !important;
    text-transform: uppercase !important;
    width: 100% !important;
    height: 48px !important;
    transition: all 0.15s ease !important;
}
.stDownloadButton > button:hover {
    background: #e8ff47 !important;
    color: #0a0a0a !important;
}

/* ── Spinner ── */
.stSpinner > div { border-top-color: #e8ff47 !important; }

/* ── Tips expander ── */
.tips-wrap .streamlit-expanderHeader {
    color: #555 !important;
    font-size: 11px !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: #111; }
::-webkit-scrollbar-thumb { background: #333; border-radius: 2px; }
::-webkit-scrollbar-thumb:hover { background: #e8ff47; }
</style>
""", unsafe_allow_html=True)

# ── Header ──
st.markdown("""
<div class="forge-header">
    <div class="forge-tag">// AI-Powered · Multi-Agent · LangGraph</div>
    <div class="forge-title">Code<span>Forge</span></div>
    <div class="forge-sub">describe an idea → get a full project in seconds</div>
</div>
""", unsafe_allow_html=True)

# ── API Key Check ──
api_key_present = bool(os.environ.get("GROQ_API_KEY", ""))
if not api_key_present:
    st.error("⚠️ GROQ_API_KEY is not set. Go to App Settings → Secrets and add: GROQ_API_KEY = \"your_key\"")
    st.stop()

# ── Input Panel ──
st.markdown('<div class="panel"><div class="panel-label">// Your idea</div>', unsafe_allow_html=True)
user_prompt = st.text_area(
    "prompt",
    placeholder="e.g. Build a REST API with FastAPI and SQLite for a bookstore with full CRUD operations...",
    height=160,
    label_visibility="collapsed"
)
st.markdown('</div>', unsafe_allow_html=True)

generate_btn = st.button("⚡ Forge Project")

with st.expander("── tips for better output"):
    st.markdown("""
```
✦ name the tech stack  →  FastAPI, React, SQLite...
✦ list key features    →  auth, CRUD, search...
✦ set constraints      →  no external DB, simple UI...
✦ be specific          →  more detail = better code
```
    """)

# ── ZIP helper ──
def create_zip(files: dict) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    return buf.getvalue()

# ── Generation ──
if generate_btn:
    if not user_prompt.strip():
        st.warning("Enter a project description first.")
    else:
        with st.spinner("Forging your project..."):
            try:
                result = agent.invoke({"user_prompt": user_prompt.strip()})
                plan       = result.get("plan", "")
                task_plan  = result.get("task_plan", "")
                code_files = result.get("code_files", {})

                if not code_files:
                    st.error("No files generated. Try rephrasing your prompt.")
                else:
                    save_files(code_files)
                    n = len(code_files)

                    # ── Stats ──
                    st.markdown(f"""
                    <div class="stats-bar">
                        <div class="stat-chip"><b>{n}</b>files generated</div>
                        <div class="stat-chip"><b>3</b>agents used</div>
                        <div class="stat-chip"><b>✓</b>ready to run</div>
                    </div>
                    """, unsafe_allow_html=True)

                    # ── Plan + Architecture ──
                    st.markdown('<div class="section-title">// pipeline output</div>', unsafe_allow_html=True)
                    c1, c2 = st.columns(2)
                    with c1:
                        with st.expander("01 · planner output"):
                            st.write(plan)
                    with c2:
                        with st.expander("02 · architect output"):
                            st.write(task_plan)

                    # ── Files ──
                    st.markdown('<div class="section-title">// generated files</div>', unsafe_allow_html=True)
                    for i, (filename, content) in enumerate(code_files.items(), 1):
                        ext = filename.rsplit(".", 1)[-1] if "." in filename else "text"
                        with st.expander(f"{i:02d} · {filename}"):
                            st.code(content, language=ext)

                    # ── Download ──
                    st.markdown('<div class="section-title">// export</div>', unsafe_allow_html=True)
                    st.download_button(
                        label="↓ Download ZIP",
                        data=create_zip(code_files),
                        file_name="codeforge_project.zip",
                        mime="application/zip"
                    )

            except Exception as e:
                st.error(f"Error: {e}")
