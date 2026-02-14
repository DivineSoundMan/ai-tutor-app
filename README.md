# 📚 AI Tutor Assistant App

An intelligent tutoring application powered by Claude AI that helps students learn from class transcripts through interactive features including concept analysis, quiz generation, and personalized explanations.

## ✨ Features

- **📝 Transcript Analysis**: Upload class transcripts and get structured analysis of key concepts, learning objectives, and definitions
- **🎯 Interactive Quizzes**: Generate customized multiple-choice quizzes to test understanding of the material
- **💡 Concept Explanations**: Ask questions about specific concepts and get detailed explanations with real-world examples
- **🤖 Powered by Claude 3.5 Sonnet**: Leverages advanced AI for accurate, educational responses

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- An Anthropic API key ([Get one here](https://console.anthropic.com/))

### Installation

1. Clone the repository:
```bash
git clone https://github.com/DivineSoundMan/ai-tutor-app.git
cd ai-tutor-app
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your Anthropic API key:
```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

For Windows:
```cmd
set ANTHROPIC_API_KEY=your-api-key-here
```

### Running the App

```bash
streamlit run app.py
```

The app will open in your default web browser at `http://localhost:8501`

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
├── .gitignore         # Git ignore rules
└── README.md          # This file
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
