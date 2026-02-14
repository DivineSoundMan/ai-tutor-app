# 📚 AI Tutor Assistant App

An intelligent tutoring application powered by Claude AI that helps students learn from class transcripts through interactive features including concept analysis, quiz generation, and personalized explanations.

## ✨ Features

- **📝 Transcript Analysis**: Upload class transcripts and get structured analysis of key concepts, learning objectives, and definitions
- **🎯 Interactive Quizzes**: Generate customized multiple-choice quizzes to test understanding of the material
- **💡 Concept Explanations**: Ask questions about specific concepts and get detailed explanations with real-world examples
- **🤖 Powered by Claude 3.5 Sonnet**: Leverages advanced AI for accurate, educational responses

## 🚀 Getting Started

### Deploy to Streamlit Community Cloud (Recommended)

The easiest way to run this app is on [Streamlit Community Cloud](https://share.streamlit.io/) (free):

1. Push this repo to GitHub (e.g. `github.com/DivineSoundMan/ai-tutor-app`)
2. Go to [share.streamlit.io](https://share.streamlit.io/) and click **New app**
3. Select your repo, branch `main`, and main file `app.py`
4. Click **Advanced settings** and add your secrets:
   ```toml
   ANTHROPIC_API_KEY = "sk-ant-..."
   ADMIN_PASSWORD = "your-secure-password"
   ```
5. Click **Deploy**

Your app will be live at `https://<your-app>.streamlit.app`.

### Adding Transcript Files

Transcript files committed to the `transcripts/` folder in the repo are **permanently available** and persist across app restarts. To add files:

1. Place `.txt`, `.docx`, or `.pdf` files in the `transcripts/` folder
2. Commit and push to GitHub
3. Streamlit Cloud will automatically redeploy with the new files

Files uploaded via the admin panel are **session-only** and are lost when the app restarts.

### Run Locally (Alternative)

1. Clone the repository:
```bash
git clone https://github.com/DivineSoundMan/ai-tutor-app.git
cd ai-tutor-app
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your secrets (choose one):

   **Option A** — Environment variables:
   ```bash
   export ANTHROPIC_API_KEY='your-api-key-here'
   export ADMIN_PASSWORD='your-password'
   ```

   **Option B** — Streamlit secrets file (`.streamlit/secrets.toml`):
   ```toml
   ANTHROPIC_API_KEY = "your-api-key-here"
   ADMIN_PASSWORD = "your-password"
   ```

4. Run the app:
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
- **Anthropic Claude**: AI language model for educational content
- **Python**: Core programming language

### Project Structure

```
ai-tutor-app/
├── app.py              # Main application file
├── requirements.txt    # Python dependencies
├── transcripts/        # Bundled transcript files (persist on Streamlit Cloud)
├── data/uploads/       # Session uploads (ephemeral)
├── .streamlit/
│   └── config.toml     # Streamlit theme & settings
├── .gitignore          # Git ignore rules
└── README.md           # This file
```

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

- Built with [Anthropic's Claude API](https://www.anthropic.com/)
- UI powered by [Streamlit](https://streamlit.io/)

## 📧 Contact

For questions or suggestions, please open an issue on GitHub.

---

**Happy Learning! 🎉**
