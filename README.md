# 📚 AI Tutor Assistant App

An intelligent tutoring application powered by **Llama 3.2** (via Ollama) that helps students learn from class transcripts through interactive features including concept analysis, quiz generation, and personalized explanations.

**$0/month** — fully self-hosted with open-source models.

## ✨ Features

- **📝 Transcript Analysis**: Upload class transcripts and get structured analysis of key concepts, learning objectives, and definitions
- **🎯 Interactive Quizzes**: Generate customized multiple-choice quizzes to test understanding of the material
- **💡 Concept Explanations**: Ask questions about specific concepts and get detailed explanations
- **🤖 Powered by Llama 3.2 (3B)**: Free, self-hosted open-source LLM via Ollama
- **⚡ Streaming Responses**: Real-time token streaming for better UX
- **💬 Conversation Memory**: Maintains context across the last 10 exchanges

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│          Hugging Face Spaces            │
│  ┌──────────┐    ┌───────────────────┐  │
│  │ Streamlit│◄──►│  Ollama Server    │  │
│  │   :8501  │    │  llama3.2:3b      │  │
│  └──────────┘    └───────────────────┘  │
│       │                                  │
│  ┌──────────┐                           │
│  │Transcripts│ (bundled + uploads)      │
│  └──────────┘                           │
└─────────────────────────────────────────┘
```

- **LLM Backend**: Ollama with llama3.2:3b (Meta's latest 3B model)
- **Web UI**: Streamlit with custom dark theme
- **Deployment**: Docker on Hugging Face Spaces (free tier)
- **Cost**: $0/month

## 🚀 Getting Started

### Deploy to Hugging Face Spaces (Recommended — Free)

1. Create a new Space at [huggingface.co/spaces](https://huggingface.co/spaces)
2. Select **Docker** as the SDK
3. Push this repo to the Space:
   ```bash
   git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/ai-tutor-app
   git push hf main
   ```
4. Set secrets in Space Settings:
   - `ADMIN_PASSWORD` — password for the admin panel
5. The Space will build the Docker image (model is baked in, ~2GB)

### Adding Transcript Files

Transcript files committed to the `transcripts/` folder in the repo are **permanently available** and persist across app restarts. To add files:

1. Place `.txt`, `.docx`, or `.pdf` files in the `transcripts/` folder
2. Commit and push
3. The app will automatically redeploy with the new files

Files uploaded via the admin panel are **session-only** and are lost when the app restarts.

### Run Locally with Docker

```bash
docker build -t ai-tutor .
docker run -p 8501:8501 -e ADMIN_PASSWORD=your-password ai-tutor
```

Open `http://localhost:8501` in your browser.

### Run Locally without Docker

1. Install [Ollama](https://ollama.com/):
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ```

2. Pull the model:
   ```bash
   ollama pull llama3.2:3b
   ```

3. Start Ollama (runs in background):
   ```bash
   ollama serve &
   ```

4. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Set secrets (optional):
   ```bash
   export ADMIN_PASSWORD='your-password'
   ```

6. Run the app:
   ```bash
   streamlit run app.py
   ```

The app will open at `http://localhost:8501`

## 📖 How to Use

### 1. Upload Transcript
- Navigate to the "📝 Upload Transcript" section
- Paste your class transcript, lecture notes, or study materials
- Click "Analyze Transcript" to extract key concepts and learning objectives

### 2. Take Quiz
- Go to the "🎯 Take Quiz" section
- Choose the number of questions (3-10)
- Click "Generate Quiz" to create multiple-choice questions based on your transcript
- Each question includes the correct answer and detailed explanation

### 3. Ask About Concepts
- Visit the "💡 Ask About Concepts" section
- Type any concept you'd like to understand better
- Optionally use context from your uploaded transcript
- Get comprehensive explanations with:
  - Simple, clear definitions
  - Real-world examples
  - Common misconceptions
  - Practice tips

## 🛠️ Technical Details

### Built With

- **Streamlit**: Web application framework
- **Ollama**: Self-hosted LLM inference server
- **Llama 3.2 (3B)**: Meta's open-source language model
- **Docker**: Containerized deployment
- **Python**: Core programming language

### Project Structure

```
ai-tutor-app/
├── app.py              # Main application file
├── requirements.txt    # Python dependencies
├── Dockerfile          # Docker build for HF Spaces
├── start.sh            # Startup script (Ollama + Streamlit)
├── transcripts/        # Bundled transcript files (persistent)
├── data/uploads/       # Session uploads (ephemeral)
├── .streamlit/
│   └── config.toml     # Streamlit theme & settings
├── .gitignore          # Git ignore rules
└── README.md           # This file
```

### Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `llama3.2:3b` | Model to use |
| `ADMIN_PASSWORD` | `admin` | Admin panel password |
| `PORT` | `8501` | Streamlit server port |

### Alternative Models

You can swap models by setting `OLLAMA_MODEL`:

| Model | Size | Best For |
|-------|------|----------|
| `llama3.2:3b` | 2.0 GB | General tutoring (default) |
| `phi3:mini` | 2.3 GB | Education-focused, fast |
| `mistral:7b` | 4.1 GB | Complex reasoning |
| `gemma2:2b` | 1.6 GB | Lightweight, fastest |

## 🎓 Use Cases

- **Students**: Review lecture materials and prepare for exams
- **Lifelong Learners**: Understand complex topics from online courses or textbooks
- **Educators**: Create study materials and quizzes for students
- **Self-Study**: Test comprehension and identify knowledge gaps

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest new features
- Submit pull requests

## 📝 License

This project is open source and available for educational purposes.

## 🙏 Acknowledgments

- LLM powered by [Ollama](https://ollama.com/) + [Meta Llama 3.2](https://llama.meta.com/)
- UI powered by [Streamlit](https://streamlit.io/)
- Hosted on [Hugging Face Spaces](https://huggingface.co/spaces)

## 📧 Contact

For questions or suggestions, please open an issue on GitHub.

---

**Happy Learning! 🎉**
