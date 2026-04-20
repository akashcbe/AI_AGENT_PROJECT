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

# --- Page Config ---
st.set_page_config(
    page_title="Auto Code Builder",
    page_icon="💻",
    layout="wide"
)

# --- Custom UI Styling ---
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0f172a, #1e293b);
    color: #e2e8f0;
    font-family: 'Segoe UI', sans-serif;
}
.block-container { max-width: 1100px; padding-top: 2rem; }
.main-title {
    text-align: center; font-size: 48px; font-weight: 700;
    color: #38bdf8; margin-bottom: 10px;
}
.subtitle {
    text-align: center; font-size: 18px;
    color: #94a3b8; margin-bottom: 30px;
}
.card {
    background: #1e293b; padding: 25px; border-radius: 18px;
    box-shadow: 0 8px 30px rgba(0,0,0,0.35); margin-bottom: 20px;
}
.stButton>button {
    background: linear-gradient(90deg, #38bdf8, #6366f1);
    color: white; border-radius: 12px; height: 50px; width: 100%;
    font-size: 17px; font-weight: 600; border: none; transition: 0.3s;
}
.stButton>button:hover {
    transform: scale(1.02);
    background: linear-gradient(90deg, #0ea5e9, #4f46e5);
}
textarea { border-radius: 12px !important; padding: 10px !important; }
.streamlit-expanderHeader { font-size: 17px; font-weight: 600; color: #38bdf8; }
pre { border-radius: 10px !important; }
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown('<div class="main-title">💻 Auto Code Builder</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Turn your idea into working code instantly</div>', unsafe_allow_html=True)

# --- API Key Check ---
api_key_present = bool(os.environ.get("GROQ_API_KEY", ""))
if not api_key_present:
    st.error(
        "⚠️ **GROQ_API_KEY is not set.**\n\n"
        "Go to your Streamlit Cloud app → **Settings → Secrets** and add:\n"
        "```\nGROQ_API_KEY = \"your_key_here\"\n```"
    )
    st.stop()

# --- Input Card ---
st.markdown('<div class="card">', unsafe_allow_html=True)
user_prompt = st.text_area(
    "📝 Describe your project",
    placeholder="Example: Build a todo app with FastAPI backend and React frontend...",
    height=180
)
generate_btn = st.button("🚀 Generate Code")
st.markdown('</div>', unsafe_allow_html=True)

with st.expander("💡 Tips for better results"):
    st.write("""
    - Be clear about features you want
    - Mention the tech stack (Python, React, FastAPI, etc.)
    - Add constraints (simple UI, REST API, SQLite DB, etc.)
    """)

def create_zip(files: dict) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for filename, content in files.items():
            zf.writestr(filename, content)
    return buffer.getvalue()

if generate_btn:
    if not user_prompt.strip():
        st.warning("⚠️ Please enter a project description.")
    else:
        with st.spinner("⚙️ Generating your project... This may take 30–60 seconds."):
            try:
                result = agent.invoke({"user_prompt": user_prompt.strip()})
                plan = result.get("plan", "")
                task_plan = result.get("task_plan", "")
                code_files = result.get("code_files", {})

                if not code_files:
                    st.error("❌ No files were generated. Try rephrasing your prompt.")
                else:
                    save_files(code_files)
                    st.success(f"✅ Generated {len(code_files)} file(s) successfully!")

                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    col1, col2 = st.columns(2)
                    with col1:
                        with st.expander("📌 Project Plan"):
                            st.write(plan)
                    with col2:
                        with st.expander("🧩 Architecture"):
                            st.write(task_plan)

                    st.markdown("### 📂 Generated Files")
                    for filename, content in code_files.items():
                        with st.expander(f"📄 {filename}"):
                            ext = filename.rsplit(".", 1)[-1] if "." in filename else "text"
                            st.code(content, language=ext)

                    zip_bytes = create_zip(code_files)
                    st.download_button(
                        label="📦 Download All Files as ZIP",
                        data=zip_bytes,
                        file_name="generated_project.zip",
                        mime="application/zip"
                    )
                    st.markdown('</div>', unsafe_allow_html=True)

            except Exception as e:
                st.error(f"❌ Generation Error: {e}")
