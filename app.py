"""AI Assistant Tutor App - Chat Interface
Helps students learn from class transcripts through conversational AI tutoring
"""

import streamlit as st
import anthropic
import os
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="🎓 AI Tutor Assistant",
    page_icon="🎓",
    layout="wide"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []
if "transcript_content" not in st.session_state:
    st.session_state.transcript_content = ""

# Initialize Anthropic client
try:
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    model = "claude-3-5-sonnet-20241022"
except:
    client = None

# Sidebar for file uploads
with st.sidebar:
    st.header("📁 Files")
    st.caption("Files to use as context for learning")
    
    uploaded_file = st.file_uploader(
        "Upload class transcript",
        type=["txt", "docx", "pdf"],
        help="Upload your class transcripts for AI analysis"
    )
    
    if uploaded_file:
        if uploaded_file not in st.session_state.uploaded_files:
            st.session_state.uploaded_files.append(uploaded_file)
            # Read the file content
            try:
                st.session_state.transcript_content = uploaded_file.read().decode("utf-8")
                st.success(f"✅ {uploaded_file.name} loaded")
            except:
                st.session_state.transcript_content = uploaded_file.read()
                st.success(f"✅ {uploaded_file.name} loaded")
    
    # Show uploaded files
    if st.session_state.uploaded_files:
        st.divider()
        st.subheader("Loaded Files:")
        for f in st.session_state.uploaded_files:
            st.text(f"📄 {f.name}")
    
    st.divider()
    st.markdown("""
    ### 💡 Example prompts:
    - "Explain the main concepts from the transcript"
    - "Quiz me on topic X"
    - "What are the key learning objectives?"
    - "Explain this concept in detail"
    """)

# Main chat interface
st.title("🎓 AI Tutor Assistant")
st.caption("Learn from your class transcripts with AI-powered explanations and quizzes")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask anything about your class materials. Type @ for sources and / for shortcuts."):
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate AI response
    with st.chat_message("assistant"):
        if client and st.session_state.transcript_content:
            # Create system prompt with transcript context
            system_prompt = f"""You are an expert AI tutor helping students learn from their class materials.
            
Class Transcript Context:
{st.session_state.transcript_content[:5000]}

Your role:
- Explain concepts clearly with examples
- Generate quizzes to test understanding
- Provide detailed explanations when asked
- Reference the transcript content when relevant
- Be encouraging and supportive
"""
            
            try:
                with st.spinner("Thinking..."):
                    message = client.messages.create(
                        model=model,
                        max_tokens=2048,
                        system=system_prompt,
                        messages=[
                            {"role": m["role"], "content": m["content"]}
                            for m in st.session_state.messages
                        ]
                    )
                    response = message.content[0].text
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.info("💡 Make sure to set your ANTHROPIC_API_KEY in the app settings")
        elif not st.session_state.transcript_content:
            response = "Please upload a class transcript first using the sidebar. I'll help you learn from it!"
            st.info(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
        else:
            response = "Please configure your ANTHROPIC_API_KEY to use the AI tutor."
            st.warning(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

# Welcome message if no chat history
if not st.session_state.messages:
    st.markdown("""
    ### 👋 Welcome to AI Tutor Assistant!
    
    This AI-powered tutor helps you:
    - 📚 **Understand concepts** from your class transcripts
    - 📝 **Test your knowledge** with interactive quizzes
    - 💡 **Get explanations** with real-world examples
    - 🎯 **Focus on key topics** from your classes
    
    **To get started:**
    1. Upload your class transcript using the sidebar
    2. Ask questions about the material
    3. Request quizzes to test your understanding
    
    Try asking: *"Explain the main concepts from this transcript"* or *"Quiz me on the key topics"*
    """)
