"""
SL Class Meaning's - Soundarya Lahiri AI Tutor
Admin panel for transcript management + Student chat for learning sloka meanings

Backend: Ollama with llama3.2:3b (free, self-hosted)
Deployment target: Hugging Face Spaces (Docker)
"""

import streamlit as st
import requests
import json
import os
import time
import subprocess
import signal
import logging
from pathlib import Path
from datetime import datetime

# --- Configuration ---
APP_TITLE = "SL Class Meaning's: 1-5|19-25|26-28 Only"
UPLOAD_DIR = Path("data/uploads")          # session-only uploads (ephemeral)
TRANSCRIPTS_DIR = Path("transcripts")      # bundled files committed to repo (persist across restarts)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

# Ollama configuration
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:3b")
MAX_CONVERSATION_EXCHANGES = 10  # keep last 10 user-assistant pairs

# Service control logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
service_logger = logging.getLogger("ollama.service")


def _get_secret(key: str, default: str = "") -> str:
    """Read from st.secrets first, fall back to env var."""
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError):
        return os.environ.get(key, default)


# Page configuration
st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🙏",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Custom CSS ---
st.markdown(
    """
<style>
    /* Main title */
    .app-title {
        color: #4ecdc4;
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 0;
        line-height: 1.2;
    }
    .app-subtitle {
        color: #b0b0c0;
        font-size: 0.95rem;
        margin-top: 4px;
        margin-bottom: 16px;
    }

    /* Admin header banner */
    .admin-banner {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 24px 28px;
        border-radius: 12px;
        color: #ffffff;
        margin-bottom: 24px;
    }
    .admin-banner h2 { margin: 0 0 6px 0; font-size: 1.5rem; }
    .admin-banner p  { margin: 0; opacity: 0.9; font-size: 0.95rem; }

    /* File row card */
    .file-row {
        background: #16213e;
        border: 1px solid #2a2a4a;
        border-radius: 10px;
        padding: 14px 18px;
        margin-bottom: 10px;
    }
    .file-row:hover { border-color: #4ecdc4; }

    /* Welcome card */
    .welcome-card {
        background: #16213e;
        border: 1px solid #2a2a4a;
        border-radius: 14px;
        padding: 28px 32px;
        margin: 12px 0 24px 0;
    }

    /* Sidebar section header */
    .sidebar-section {
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #7a7a9a;
        margin-top: 12px;
        margin-bottom: 6px;
    }

    /* Hide default header / footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Smaller file list in sidebar */
    .sidebar-file {
        font-size: 0.88rem;
        padding: 3px 0;
        color: #c0c0d0;
    }

    /* Model status badge */
    .model-badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.78rem;
        font-weight: 600;
    }
    .model-ready { background: #1a3a2a; color: #4ecdc4; border: 1px solid #2a5a3a; }
    .model-loading { background: #3a3a1a; color: #f0c040; border: 1px solid #5a5a2a; }
    .model-error { background: #3a1a1a; color: #ff6b6b; border: 1px solid #5a2a2a; }
</style>
""",
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------
# Ollama backend
# ------------------------------------------------------------------

def check_ollama_status():
    """Check if Ollama server is running and model is available."""
    try:
        resp = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        if resp.status_code != 200:
            return "server_error", "Ollama server returned an error"
        models = resp.json().get("models", [])
        model_names = [m.get("name", "") for m in models]
        # Check exact match or match without tag
        base_model = OLLAMA_MODEL.split(":")[0]
        for name in model_names:
            if name == OLLAMA_MODEL or name.startswith(base_model):
                return "ready", name
        return "no_model", f"Model '{OLLAMA_MODEL}' not found. Available: {', '.join(model_names) or 'none'}"
    except requests.ConnectionError:
        return "offline", "Ollama server is not running"
    except requests.Timeout:
        return "timeout", "Ollama server timed out"
    except Exception as e:
        return "error", str(e)


# ------------------------------------------------------------------
# Ollama service control
# ------------------------------------------------------------------

def _log_service_event(action: str, result: str):
    """Append an event to the in-session service log."""
    entry = f"[{datetime.now().strftime('%H:%M:%S')}] {action}: {result}"
    if "service_log" not in st.session_state:
        st.session_state.service_log = []
    st.session_state.service_log.append(entry)
    service_logger.info(f"{action} — {result}")


def get_ollama_pids():
    """Return list of PIDs for running Ollama server processes."""
    try:
        result = subprocess.run(
            ["pgrep", "-f", "ollama serve"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode != 0:
            return []
        return [int(p) for p in result.stdout.strip().split("\n") if p.strip()]
    except Exception:
        return []


def start_ollama_service():
    """Start the Ollama server as a background process.

    Returns (success: bool, message: str).
    """
    # Already running?
    status, _ = check_ollama_status()
    if status == "ready":
        msg = "Ollama is already running"
        _log_service_event("START", msg)
        return True, msg

    try:
        env = os.environ.copy()
        env.setdefault("OLLAMA_HOST", "0.0.0.0:11434")
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            env=env,
        )

        # Poll health endpoint for up to 15 seconds
        for _ in range(15):
            time.sleep(1)
            try:
                resp = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=2)
                if resp.status_code == 200:
                    pids = get_ollama_pids()
                    pid_str = pids[0] if pids else "?"
                    msg = f"Ollama started successfully (PID {pid_str})"
                    _log_service_event("START", msg)
                    return True, msg
            except requests.ConnectionError:
                pass

        msg = "Ollama process started but health check failed after 15 s"
        _log_service_event("START", msg)
        return False, msg

    except FileNotFoundError:
        msg = "ollama binary not found — is Ollama installed?"
        _log_service_event("START", msg)
        return False, msg
    except Exception as e:
        msg = f"Failed to start: {e}"
        _log_service_event("START", msg)
        return False, msg


def stop_ollama_service():
    """Gracefully stop the Ollama server (SIGTERM then SIGKILL).

    Returns (success: bool, message: str).
    """
    pids = get_ollama_pids()
    if not pids:
        msg = "Ollama is not running"
        _log_service_event("STOP", msg)
        return True, msg

    try:
        # Graceful SIGTERM
        for pid in pids:
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass

        # Wait up to 5 s for graceful shutdown
        for _ in range(10):
            time.sleep(0.5)
            if not get_ollama_pids():
                msg = "Ollama stopped gracefully"
                _log_service_event("STOP", msg)
                return True, msg

        # Force-kill remaining processes
        for pid in get_ollama_pids():
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        time.sleep(1)

        if not get_ollama_pids():
            msg = "Ollama force-stopped (SIGKILL)"
            _log_service_event("STOP", msg)
            return True, msg

        msg = "Could not stop all Ollama processes"
        _log_service_event("STOP", msg)
        return False, msg

    except Exception as e:
        msg = f"Error stopping Ollama: {e}"
        _log_service_event("STOP", msg)
        return False, msg


def restart_ollama_service():
    """Stop then start the Ollama server.

    Returns (success: bool, message: str).
    """
    _log_service_event("RESTART", "Initiated")
    stop_ok, stop_msg = stop_ollama_service()
    if not stop_ok:
        return False, f"Restart aborted — stop failed: {stop_msg}"
    time.sleep(2)
    return start_ollama_service()


def ensure_ollama_running():
    """Auto-start Ollama if it is not already running.

    Called on every Streamlit re-run so the model self-heals after a crash.
    Uses a session flag to avoid spamming start attempts every re-run.
    """
    status, _ = check_ollama_status()
    if status == "ready":
        st.session_state.pop("_ollama_start_failed", None)
        return True

    # Don't retry if we already failed in this session within the last 30s
    last_fail = st.session_state.get("_ollama_start_failed", 0)
    if time.time() - last_fail < 30:
        return False

    service_logger.info("Ollama offline — attempting auto-start")
    ok, msg = start_ollama_service()
    if ok:
        service_logger.info(f"Auto-start succeeded: {msg}")
        return True

    st.session_state["_ollama_start_failed"] = time.time()
    service_logger.warning(f"Auto-start failed: {msg}")
    return False


def stream_ollama_response(messages, system_prompt):
    """Stream a response from Ollama, yielding text chunks."""
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [{"role": "system", "content": system_prompt}] + messages,
        "stream": True,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9,
            "num_predict": 2048,
            "num_ctx": 4096,
        },
    }
    try:
        resp = requests.post(
            f"{OLLAMA_HOST}/api/chat",
            json=payload,
            stream=True,
            timeout=(10, 180),  # (connect, read) — first request after cold start loads model into RAM
        )
        resp.raise_for_status()
        for line in resp.iter_lines():
            if line:
                data = json.loads(line)
                chunk = data.get("message", {}).get("content", "")
                if chunk:
                    yield chunk
                if data.get("done", False):
                    break
    except requests.ConnectionError:
        yield "\n\n**Error:** Cannot connect to the AI model server. The model may still be loading — please try again in a moment."
    except requests.Timeout:
        yield "\n\n**Error:** The model took too long to respond. Please try a shorter question."
    except Exception as e:
        yield f"\n\n**Error:** {e}"


def trim_conversation(messages, max_exchanges=MAX_CONVERSATION_EXCHANGES):
    """Keep only the last N user-assistant exchange pairs.

    This prevents the context from growing unbounded while maintaining
    coherent conversation flow. Each exchange = 1 user + 1 assistant msg.
    """
    if len(messages) <= max_exchanges * 2:
        return messages
    return messages[-(max_exchanges * 2):]


# ------------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------------

def get_all_files():
    """Return list of dicts for files in both transcripts/ (bundled) and data/uploads/ (session)."""
    files = []
    for directory, source in [(TRANSCRIPTS_DIR, "bundled"), (UPLOAD_DIR, "uploaded")]:
        if not directory.exists():
            continue
        for f in directory.iterdir():
            if f.is_file() and not f.name.startswith("."):
                files.append(
                    {
                        "name": f.name,
                        "path": str(f),
                        "size": f.stat().st_size,
                        "modified": datetime.fromtimestamp(f.stat().st_mtime),
                        "source": source,
                    }
                )
    return sorted(files, key=lambda x: x["name"])


def read_file_content(filepath):
    """Read text from .txt, .docx, or .pdf files."""
    path = Path(filepath)
    try:
        if path.suffix.lower() == ".docx":
            try:
                from docx import Document
                doc = Document(filepath)
                return "\n".join(p.text for p in doc.paragraphs)
            except ImportError:
                return path.read_text(encoding="utf-8", errors="ignore")
        elif path.suffix.lower() == ".pdf":
            try:
                from PyPDF2 import PdfReader
                reader = PdfReader(filepath)
                return "\n".join(page.extract_text() or "" for page in reader.pages)
            except ImportError:
                return "[PDF reading requires PyPDF2 — install with: pip install PyPDF2]"
        else:
            return path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        return f"[Error reading file: {e}]"


def get_all_transcript_content():
    """Concatenate content from every file (bundled + uploaded).

    Cap at ~32000 chars to fit within llama3.2:3b's 4096-token context
    window when combined with system prompt and conversation history.
    """
    files = get_all_files()
    parts = []
    total = 0
    limit = 32_000
    for f in files:
        text = read_file_content(f["path"])
        if text and total < limit:
            chunk = text[: limit - total]
            parts.append(f"=== File: {f['name']} ===\n{chunk}\n")
            total += len(chunk)
    return "\n".join(parts)


def build_system_prompt(transcript_content: str) -> str:
    """Return the full system prompt with transcript context embedded."""
    return f"""You are a devoted and knowledgeable tutor for Soundarya Lahiri slokas.

Teach the meanings of Soundarya Lahiri slokas **only** from the class transcript text provided below. Do not use or rely on any external sources, web results, prior training data, or "general knowledge" about Soundarya Lahiri. Every explanation must be derived strictly and exclusively from the content of the provided transcript text.

For every query:

- First, locate the relevant sloka and its meaning/commentary **as given in the transcript**.
- Quote or restate all relevant portions from the transcript in **clear, modern English**, but do not add any ideas that are not explicitly supported by the text.
- If the transcript provides word-by-word gloss, phrase meanings, or notes, expand them patiently and systematically, still using only what is explicitly in the text (including implied connections clearly indicated by the teacher).
- When giving explanations, preserve all details the text offers:
  - Individual word meanings and grammatical notes (if present).
  - Explanation of names, symbols, deities, body parts, chakras, etc., exactly as described in the transcript.
  - Any metaphors, analogies, or stories mentioned in the transcript.
  - Any "inner meaning," philosophical explanation, or devotional interpretation that the transcript itself explicitly states.

Structure of every answer:

1. **Sloka reference**
   - Identify the sloka number (and the original text if present in the transcript).
   - Mention which transcript file contains this explanation.

2. **Literal meaning from the text**
   - Provide the literal or direct meaning exactly as explained in the transcript, sentence by sentence or phrase by phrase.
   - If the transcript gives a word-by-word meaning, list the important words and their meanings as given there.

3. **Detailed explanation (from text only)**
   - Give a very comprehensive explanation of the sloka using **only** the commentary and notes in the transcript.
   - Expand all points the teacher makes, but do not invent new symbolism or philosophy.
   - If the text distinguishes between different levels of meaning (e.g., external, internal, spiritual), describe each level **only if** the teacher explicitly does so.

4. **Key points and takeaways (from text only)**
   - Summarize the main ideas of the sloka purely from what the transcript states.
   - Do not generalize beyond the teacher's own statements.

Strict constraints:

- If the meaning for a sloka is **not** present in the transcript, clearly state that the information is not available in the uploaded transcripts and **do not** fill gaps from outside knowledge.
- Do not correct, dispute, or modify the interpretations given in the transcript, even if they differ from common or popular interpretations.
- Do not translate or interpret Sanskrit words, names, or concepts beyond what the transcript itself supports. If a word is present but not explained in the transcript, leave it untranslated or simply state that it is not explained in the text.
- Remain completely faithful to the style, viewpoint, and theological/philosophical stance of the class teaching.
- INSTEAD OF "The file indicates that..." say "From the class..."

Tone and audience:

- Use a respectful, devotional-friendly, **formal** tone.
- Assume the reader is sincerely trying to learn and is comfortable with detailed, in-depth explanations.
- Be as **comprehensive** and inclusive as possible, bringing out every nuance that the transcript provides.

If a user asks anything **outside** the scope of meanings given in the transcript (such as historical background, authorship debates, external commentaries, or ritual procedures not described in the text), reply that this tutor is restricted to teaching meanings strictly from the uploaded Soundarya Lahiri class transcripts and cannot go beyond their content.

When the user asks to be quizzed, create thoughtful multiple-choice or short-answer questions drawn exclusively from the transcript content. After they answer, provide feedback referencing the transcript.

========== CLASS TRANSCRIPT CONTENT ==========

{transcript_content}

========== END OF TRANSCRIPT CONTENT ========="""


# ------------------------------------------------------------------
# Session state initialisation
# ------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "admin_auth" not in st.session_state:
    st.session_state.admin_auth = False
if "page" not in st.session_state:
    st.session_state.page = "learn"
if "service_log" not in st.session_state:
    st.session_state.service_log = []
if "confirm_stop_ollama" not in st.session_state:
    st.session_state.confirm_stop_ollama = False

# Auto-start Ollama if it crashed or wasn't started
ensure_ollama_running()


# ------------------------------------------------------------------
# Sidebar
# ------------------------------------------------------------------
with st.sidebar:
    # -- Navigation --
    st.markdown('<p class="sidebar-section">Navigate</p>', unsafe_allow_html=True)
    page_choice = st.radio(
        "Page",
        ["🙏  Learn", "⚙️  Admin Panel"],
        label_visibility="collapsed",
    )
    st.session_state.page = "admin" if "Admin" in page_choice else "learn"

    st.divider()

    # -- Model status --
    st.markdown('<p class="sidebar-section">AI Model</p>', unsafe_allow_html=True)
    status, detail = check_ollama_status()
    if status == "ready":
        st.markdown(
            f'<span class="model-badge model-ready">Ready: {detail}</span>',
            unsafe_allow_html=True,
        )
    elif status == "no_model":
        st.markdown(
            '<span class="model-badge model-loading">Model loading...</span>',
            unsafe_allow_html=True,
        )
        st.caption(detail)
    else:
        st.markdown(
            '<span class="model-badge model-error">Offline</span>',
            unsafe_allow_html=True,
        )
        st.caption(detail)
        if st.button("▶️ Start Ollama", key="sidebar_start_ollama", use_container_width=True):
            with st.spinner("Starting Ollama..."):
                ok, msg = start_ollama_service()
            if ok:
                st.success(msg)
                time.sleep(1)
                st.rerun()
            else:
                st.error(msg)

    st.caption(f"Backend: Ollama · {OLLAMA_MODEL}")

    st.divider()

    # -- Files list --
    st.markdown('<p class="sidebar-section">Files used as context</p>', unsafe_allow_html=True)
    files = get_all_files()
    if files:
        for f in files:
            kb = f["size"] / 1024
            icon = "📌" if f["source"] == "bundled" else "📄"
            st.markdown(
                f'<p class="sidebar-file">{icon} {f["name"]}  <span style="color:#666">({kb:.0f} KB)</span></p>',
                unsafe_allow_html=True,
            )
    else:
        st.caption("No transcript files yet.")

    # -- Quick upload --
    st.divider()
    st.markdown('<p class="sidebar-section">Quick Upload</p>', unsafe_allow_html=True)
    quick_files = st.file_uploader(
        "Upload",
        type=["txt", "docx", "pdf"],
        accept_multiple_files=True,
        key="quick_upload",
        label_visibility="collapsed",
    )
    if quick_files:
        for uf in quick_files:
            (UPLOAD_DIR / uf.name).write_bytes(uf.getbuffer())
        st.success(f"Uploaded {len(quick_files)} file(s)")
        st.rerun()

    # -- Example prompts (learn page) --
    if st.session_state.page == "learn":
        st.divider()
        st.markdown('<p class="sidebar-section">Example prompts</p>', unsafe_allow_html=True)
        examples_sidebar = [
            "Explain Sloka 1 in detail",
            "Quiz me on Sloka 3",
            "Explain this part of Sloka 19",
            "Word by word meaning of Sloka 2",
        ]
        for ex in examples_sidebar:
            st.caption(f'"{ex}"')


# ===================================================================
#  ADMIN PANEL
# ===================================================================
if st.session_state.page == "admin":

    # --- Auth gate ---
    if not st.session_state.admin_auth:
        st.markdown("## ⚙️ Admin Panel")
        st.markdown("Enter the admin password to manage transcripts and settings.")
        col_l, col_m, col_r = st.columns([1, 2, 1])
        with col_m:
            pw = st.text_input("Password", type="password", placeholder="Enter admin password")
            if st.button("🔓 Login", use_container_width=True):
                if pw == _get_secret("ADMIN_PASSWORD", "admin"):
                    st.session_state.admin_auth = True
                    st.rerun()
                else:
                    st.error("Incorrect password. Please try again.")
    else:
        # --- Admin banner ---
        st.markdown(
            """<div class="admin-banner">
                <h2>⚙️ Admin Panel — File Management</h2>
                <p>Upload and manage Soundarya Lahiri class transcripts. Students will learn strictly from these files.</p>
            </div>""",
            unsafe_allow_html=True,
        )

        # --- Stats ---
        files = get_all_files()
        bundled = [f for f in files if f["source"] == "bundled"]
        uploaded = [f for f in files if f["source"] == "uploaded"]
        total_kb = sum(f["size"] for f in files) / 1024

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📌 Bundled", len(bundled))
        c2.metric("📄 Session Uploads", len(uploaded))
        c3.metric("💾 Total Size", f"{total_kb:.1f} KB")
        # Model status in admin
        status, detail = check_ollama_status()
        status_label = {"ready": "Ready", "no_model": "Loading...", "offline": "Offline"}.get(status, "Error")
        c4.metric("🤖 Model", status_label)

        st.divider()

        # --- Ollama Service Control ---
        st.subheader("🖥️ Ollama Service Control")

        svc_status, svc_detail = check_ollama_status()
        svc_pids = get_ollama_pids()
        is_running = svc_status == "ready"

        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            if is_running:
                st.markdown(
                    '<span class="model-badge model-ready">● Running</span>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    '<span class="model-badge model-error">● Stopped</span>',
                    unsafe_allow_html=True,
                )
        with sc2:
            st.caption(f"**Model:** {svc_detail}" if is_running else "**Model:** —")
        with sc3:
            pid_str = ", ".join(str(p) for p in svc_pids) if svc_pids else "—"
            st.caption(f"**PID:** {pid_str}  ·  `{OLLAMA_HOST}`")

        # Control buttons
        btn1, btn2, btn3 = st.columns(3)

        with btn1:
            if st.button("▶️ Start", disabled=is_running, use_container_width=True, help="Start Ollama server"):
                with st.spinner("Starting Ollama (may take 5–10 s)..."):
                    ok, msg = start_ollama_service()
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)
                    st.caption("💡 Check that Ollama is installed and the binary is in PATH.")
                time.sleep(1.5)
                st.rerun()

        with btn2:
            if not st.session_state.confirm_stop_ollama:
                if st.button("⏹️ Stop", disabled=not is_running, use_container_width=True, help="Stop Ollama server"):
                    if st.session_state.messages:
                        st.session_state.confirm_stop_ollama = True
                        st.rerun()
                    else:
                        with st.spinner("Stopping Ollama..."):
                            ok, msg = stop_ollama_service()
                        if ok:
                            st.success(msg)
                        else:
                            st.error(msg)
                        time.sleep(1.5)
                        st.rerun()
            else:
                st.warning("⚠️ Active chat exists — stopping will interrupt it.")
                cc1, cc2 = st.columns(2)
                with cc1:
                    if st.button("✅ Confirm Stop", type="primary", use_container_width=True):
                        st.session_state.confirm_stop_ollama = False
                        with st.spinner("Stopping Ollama..."):
                            ok, msg = stop_ollama_service()
                        if ok:
                            st.success(msg)
                        else:
                            st.error(msg)
                        time.sleep(1.5)
                        st.rerun()
                with cc2:
                    if st.button("❌ Cancel", use_container_width=True):
                        st.session_state.confirm_stop_ollama = False
                        st.rerun()

        with btn3:
            if st.button("🔄 Restart", use_container_width=True, help="Stop then start Ollama"):
                with st.spinner("Restarting Ollama..."):
                    ok, msg = restart_ollama_service()
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)
                time.sleep(1.5)
                st.rerun()

        # Operation log
        if st.session_state.service_log:
            with st.expander(f"📋 Service Log ({len(st.session_state.service_log)} events)"):
                for entry in reversed(st.session_state.service_log[-20:]):
                    st.text(entry)
                if st.button("🗑️ Clear Log"):
                    st.session_state.service_log = []
                    st.rerun()

        st.divider()

        # --- Upload section ---
        st.subheader("📤 Upload Transcripts (Session Only)")
        st.caption("These files persist for this session only. To add permanent files, commit them to the `transcripts/` folder in the repo.")
        admin_files = st.file_uploader(
            "Drag and drop transcript files here",
            type=["txt", "docx", "pdf"],
            accept_multiple_files=True,
            key="admin_upload",
            help="Supported formats: .txt, .docx, .pdf — session uploads are lost on app restart",
        )
        if admin_files:
            if st.button("💾 Save Uploaded Files", use_container_width=False):
                saved = 0
                for uf in admin_files:
                    (UPLOAD_DIR / uf.name).write_bytes(uf.getbuffer())
                    saved += 1
                st.success(f"Saved {saved} file(s) successfully!")
                st.rerun()

        # --- Paste text ---
        with st.expander("📝 Paste text as a new file"):
            paste_name = st.text_input(
                "File name",
                placeholder="e.g. SL 1-5.txt",
                help="Include extension (.txt recommended)",
            )
            paste_content = st.text_area(
                "Transcript content",
                height=200,
                placeholder="Paste the class transcript content here...",
            )
            if st.button("💾 Save Text File") and paste_name and paste_content:
                (UPLOAD_DIR / paste_name).write_text(paste_content, encoding="utf-8")
                st.success(f"Saved **{paste_name}**")
                st.rerun()

        st.divider()

        # --- Manage files ---
        st.subheader("📁 Manage Transcript Files")
        files = get_all_files()

        if not files:
            st.info("No transcript files yet. Add files to the `transcripts/` folder in the repo, or use the upload section above for session files.")
        else:
            for f in files:
                is_bundled = f["source"] == "bundled"
                icon = "📌" if is_bundled else "📄"
                badge = "Bundled" if is_bundled else "Session"

                with st.container():
                    col_name, col_preview, col_dl, col_del = st.columns([4, 1, 1, 1])

                    with col_name:
                        st.markdown(f"**{icon} {f['name']}**  `{badge}`")
                        st.caption(
                            f"{f['size']/1024:.1f} KB  ·  Modified {f['modified'].strftime('%b %d, %Y %I:%M %p')}"
                        )

                    with col_preview:
                        if st.button("👁️", key=f"prev_{f['name']}_{f['source']}", help="Preview"):
                            toggle_key = f"_show_{f['name']}_{f['source']}"
                            st.session_state[toggle_key] = not st.session_state.get(toggle_key, False)

                    with col_dl:
                        raw = Path(f["path"]).read_bytes()
                        st.download_button("⬇️", data=raw, file_name=f["name"], key=f"dl_{f['name']}_{f['source']}", help="Download")

                    with col_del:
                        if is_bundled:
                            st.button("🔒", key=f"del_{f['name']}_{f['source']}", help="Bundled files are managed in the repo", disabled=True)
                        else:
                            if st.button("🗑️", key=f"del_{f['name']}_{f['source']}", help="Delete"):
                                Path(f["path"]).unlink()
                                st.success(f"Deleted {f['name']}")
                                st.rerun()

                    # Preview
                    toggle_key = f"_show_{f['name']}_{f['source']}"
                    if st.session_state.get(toggle_key, False):
                        content = read_file_content(f["path"])
                        preview = content[:5000] + ("\n\n… (truncated)" if len(content) > 5000 else "")
                        st.text_area(
                            f"Preview — {f['name']}",
                            value=preview,
                            height=220,
                            disabled=True,
                            key=f"txt_{f['name']}_{f['source']}",
                        )

                    st.markdown("---")

        # --- Custom instructions preview ---
        with st.expander("📋 View Active System Instructions"):
            st.markdown(
                """The AI tutor uses the following behaviour rules (derived from your answer instructions):

- Teaches **only** from uploaded transcripts — no external knowledge
- Structures answers: Sloka reference → Literal meaning → Detailed explanation → Key takeaways
- Preserves word-by-word meanings, symbols, chakras, names exactly as in transcript
- Says *"From the class..."* instead of *"The file indicates..."*
- If a sloka is not in the transcripts, clearly states that
- Respectful, devotional-friendly, formal tone
- Can quiz students using transcript content only"""
            )

        # --- Model info ---
        with st.expander("🤖 Model & Backend Info"):
            st.markdown(f"""
- **Backend:** Ollama (self-hosted, free)
- **Model:** `{OLLAMA_MODEL}`
- **Server:** `{OLLAMA_HOST}`
- **Context limit:** ~32,000 chars of transcript content
- **Conversation memory:** Last {MAX_CONVERSATION_EXCHANGES} exchanges
- **Cost:** $0/month
""")
            if st.button("🔄 Refresh Model Status"):
                st.rerun()

        st.divider()

        # Logout
        if st.button("🔒 Logout from Admin"):
            st.session_state.admin_auth = False
            st.rerun()


# ===================================================================
#  LEARN PAGE (Student Chat)
# ===================================================================
else:
    # --- Header ---
    st.markdown(f'<p class="app-title">{APP_TITLE}</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="app-subtitle">'
        "Jaya Guru Datta!  Learn SL meanings &amp; test yourself by sloka with this AI-Powered Friend. "
        "You can ask me questions.  Some examples — "
        '<em>"Explain Sloka 1 in detail"</em>  '
        '<em>"Quiz me on Sloka 3"</em>  '
        '<em>"Explain this part of Sloka 19"</em>'
        "</p>",
        unsafe_allow_html=True,
    )

    # --- Toolbar ---
    tb1, tb2, _tb_spacer = st.columns([1, 1, 5])
    with tb1:
        if st.button("🔄 New Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    with tb2:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    st.divider()

    # --- Chat history ---
    for msg in st.session_state.messages:
        avatar = "🙏" if msg["role"] == "assistant" else "🙂"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    # --- Welcome screen ---
    if not st.session_state.messages:
        st.markdown(
            """<div class="welcome-card">
<h3>🙏 Welcome!  Jaya Guru Datta!</h3>
<p>This AI tutor teaches you the meanings of <strong>Soundarya Lahiri</strong> slokas
strictly from the class transcripts uploaded by your teacher.</p>
<ul>
  <li>📖 <strong>Ask for meanings</strong> — <em>"Explain Sloka 1 in detail"</em></li>
  <li>📝 <strong>Word-by-word meanings</strong> — <em>"Word by word meaning of Sloka 2"</em></li>
  <li>🧠 <strong>Test yourself</strong> — <em>"Quiz me on Sloka 3"</em></li>
  <li>🔍 <strong>Explore specific parts</strong> — <em>"What does this line in Sloka 19 mean?"</em></li>
</ul>
<p style="color:#7a7a9a; font-size:0.88rem;">All teachings come strictly from the class transcripts.
No external sources are used. Powered by open-source AI (Llama 3.2).</p>
</div>""",
            unsafe_allow_html=True,
        )

        # Example prompt buttons
        st.markdown("**Try one of these:**")
        ex_cols = st.columns(3)
        example_prompts = [
            "Explain Sloka 1 in detail",
            "Quiz me on Sloka 3",
            "Word by word meaning of Sloka 2",
        ]
        for i, ex in enumerate(example_prompts):
            with ex_cols[i]:
                if st.button(f'"{ex}"', key=f"ex_{i}", use_container_width=True):
                    st.session_state.messages.append({"role": "user", "content": ex})
                    st.rerun()

    # --- Chat input ---
    if prompt := st.chat_input("Ask anything about SL Class Meaning's..."):
        # Show user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="🙂"):
            st.markdown(prompt)

        # Generate assistant response
        with st.chat_message("assistant", avatar="🙏"):
            transcript_content = get_all_transcript_content()

            if not transcript_content:
                no_files_msg = (
                    "🙏 No class transcripts have been uploaded yet. "
                    "Please ask the admin to upload the Soundarya Lahiri class transcripts "
                    "so I can teach you from them."
                )
                st.info(no_files_msg)
                st.session_state.messages.append(
                    {"role": "assistant", "content": no_files_msg}
                )
            else:
                # Check model availability — auto-recover if offline
                model_status, model_detail = check_ollama_status()

                if model_status != "ready":
                    # Attempt auto-start before giving up
                    with st.spinner("AI model is offline — attempting to start Ollama..."):
                        auto_ok = ensure_ollama_running()
                    if auto_ok:
                        model_status, model_detail = check_ollama_status()

                if model_status != "ready":
                    if model_status == "no_model":
                        wait_msg = (
                            "🔄 The AI model is still loading. This happens once after startup "
                            "and may take a few minutes. Please try again shortly."
                        )
                    else:
                        wait_msg = (
                            f"⚠️ Could not start the AI model server ({model_detail}). "
                            "Please try again in a moment or ask the admin to check the server."
                        )
                    st.warning(wait_msg)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": wait_msg}
                    )
                else:
                    system = build_system_prompt(transcript_content)

                    # Trim conversation to last N exchanges for context window
                    trimmed = trim_conversation(st.session_state.messages)
                    chat_messages = [
                        {"role": m["role"], "content": m["content"]}
                        for m in trimmed
                    ]

                    # Stream the response
                    full_response = st.write_stream(
                        stream_ollama_response(chat_messages, system)
                    )

                    st.session_state.messages.append(
                        {"role": "assistant", "content": full_response}
                    )

                    # Trim stored history
                    st.session_state.messages = trim_conversation(
                        st.session_state.messages
                    )
