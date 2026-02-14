"""
SL Class Meaning's - Soundarya Lahiri AI Tutor
Admin panel for transcript management + Student chat for learning sloka meanings
"""

import streamlit as st
import anthropic
import os
from pathlib import Path
from datetime import datetime

# --- Configuration ---
APP_TITLE = "SL Class Meaning's: 1-5|19-25|26-28 Only"
UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

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
</style>
""",
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------------

def get_uploaded_files():
    """Return list of dicts for every file in the uploads dir."""
    files = []
    for f in UPLOAD_DIR.iterdir():
        if f.is_file() and not f.name.startswith("."):
            files.append(
                {
                    "name": f.name,
                    "path": str(f),
                    "size": f.stat().st_size,
                    "modified": datetime.fromtimestamp(f.stat().st_mtime),
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
    """Concatenate content from every uploaded file (cap at ~120 000 chars)."""
    files = get_uploaded_files()
    parts = []
    total = 0
    limit = 120_000
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

# Anthropic client
try:
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    MODEL = "claude-sonnet-4-5-20250929"
except Exception:
    client = None

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

    # -- Files list --
    st.markdown('<p class="sidebar-section">Files used as context</p>', unsafe_allow_html=True)
    files = get_uploaded_files()
    if files:
        for f in files:
            kb = f["size"] / 1024
            st.markdown(
                f'<p class="sidebar-file">📄 {f["name"]}  <span style="color:#666">({kb:.0f} KB)</span></p>',
                unsafe_allow_html=True,
            )
    else:
        st.caption("No files uploaded yet.")

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
                if pw == os.environ.get("ADMIN_PASSWORD", "admin"):
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
        files = get_uploaded_files()
        total_kb = sum(f["size"] for f in files) / 1024
        extensions = set(Path(f["name"]).suffix for f in files) if files else set()

        c1, c2, c3 = st.columns(3)
        c1.metric("📁 Total Files", len(files))
        c2.metric("💾 Total Size", f"{total_kb:.1f} KB")
        c3.metric("📄 File Types", ", ".join(extensions) if extensions else "—")

        st.divider()

        # --- Upload section ---
        st.subheader("📤 Upload Transcripts")
        admin_files = st.file_uploader(
            "Drag and drop transcript files here",
            type=["txt", "docx", "pdf"],
            accept_multiple_files=True,
            key="admin_upload",
            help="Supported formats: .txt, .docx, .pdf",
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
        st.subheader("📁 Manage Uploaded Files")
        files = get_uploaded_files()

        if not files:
            st.info("No files uploaded yet. Use the section above to add class transcripts.")
        else:
            for f in files:
                with st.container():
                    col_name, col_preview, col_dl, col_del = st.columns([4, 1, 1, 1])

                    with col_name:
                        st.markdown(f"**📄 {f['name']}**")
                        st.caption(
                            f"{f['size']/1024:.1f} KB  ·  Modified {f['modified'].strftime('%b %d, %Y %I:%M %p')}"
                        )

                    with col_preview:
                        if st.button("👁️", key=f"prev_{f['name']}", help="Preview"):
                            toggle_key = f"_show_{f['name']}"
                            st.session_state[toggle_key] = not st.session_state.get(toggle_key, False)

                    with col_dl:
                        raw = Path(f["path"]).read_bytes()
                        st.download_button("⬇️", data=raw, file_name=f["name"], key=f"dl_{f['name']}", help="Download")

                    with col_del:
                        if st.button("🗑️", key=f"del_{f['name']}", help="Delete"):
                            Path(f["path"]).unlink()
                            st.success(f"Deleted {f['name']}")
                            st.rerun()

                    # Preview
                    toggle_key = f"_show_{f['name']}"
                    if st.session_state.get(toggle_key, False):
                        content = read_file_content(f["path"])
                        preview = content[:5000] + ("\n\n… (truncated)" if len(content) > 5000 else "")
                        st.text_area(
                            f"Preview — {f['name']}",
                            value=preview,
                            height=220,
                            disabled=True,
                            key=f"txt_{f['name']}",
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
No external sources are used.</p>
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

            if client and transcript_content:
                system = build_system_prompt(transcript_content)
                try:
                    with st.spinner("🙏 Contemplating the teachings..."):
                        resp = client.messages.create(
                            model=MODEL,
                            max_tokens=4096,
                            system=system,
                            messages=[
                                {"role": m["role"], "content": m["content"]}
                                for m in st.session_state.messages
                            ],
                        )
                        answer = resp.content[0].text
                        st.markdown(answer)
                        st.session_state.messages.append(
                            {"role": "assistant", "content": answer}
                        )
                except Exception as e:
                    st.error(f"Error: {e}")
                    st.info("Make sure the ANTHROPIC_API_KEY environment variable is set correctly.")

            elif not transcript_content:
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
                key_msg = "Please configure the ANTHROPIC_API_KEY environment variable to use the AI tutor."
                st.warning(key_msg)
                st.session_state.messages.append(
                    {"role": "assistant", "content": key_msg}
                )
