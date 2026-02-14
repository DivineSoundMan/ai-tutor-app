"""AI Assistant Tutor App
Takes class transcripts and helps teach concepts with interactive quizzes
"""

import streamlit as st
import anthropic
import os
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="AI Tutor Assistant",
    page_icon="📚",
    layout="wide"
)

class AITutor:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        self.model = "claude-3-5-sonnet-20241022"
    
    def analyze_transcript(self, transcript):
        """Analyze class transcript and extract key concepts"""
        prompt = f"""Analyze this class transcript and extract:
        1. Main concepts covered
        2. Key learning objectives
        3. Important definitions
        4. Suggested study topics
        
        Transcript:
        {transcript}
        
        Please provide a structured analysis.
        """
        
        message = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    
    def generate_quiz(self, transcript, num_questions=5):
        """Generate quiz questions based on transcript"""
        prompt = f"""Based on this transcript, create {num_questions} multiple-choice questions to test understanding.
        
        Format each question as:
        Q: [question]
        A) [option]
        B) [option]
        C) [option]
        D) [option]
        Correct: [letter]
        Explanation: [why this is correct]
        
        Transcript:
        {transcript}
        """
        
        message = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    
    def explain_concept(self, concept, context=""):
        """Explain a specific concept in detail"""
        prompt = f"""Please explain this concept in a clear, educational way:
        
        Concept: {concept}
        
        {f'Context from class: {context}' if context else ''}
        
        Include:
        - Simple explanation
        - Real-world examples
        - Common misconceptions
        - Practice tips
        """
        
        message = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text

def main():
    st.title("📚 AI Tutor Assistant")
    st.markdown("Upload class transcripts and get personalized tutoring help!")
    
    # Initialize tutor
    if 'tutor' not in st.session_state:
        st.session_state.tutor = AITutor()
    
    # Sidebar for navigation
    with st.sidebar:
        st.header("Navigation")
        page = st.radio(
            "Choose a feature:",
            ["📝 Upload Transcript", "🎯 Take Quiz", "💡 Ask About Concepts"]
        )
    
    if page == "📝 Upload Transcript":
        st.header("Upload Class Transcript")
        
        # Text area for transcript input
        transcript = st.text_area(
            "Paste your class transcript here:",
            height=300,
            placeholder="Paste lecture notes, transcript, or class materials here..."
        )
        
        if st.button("Analyze Transcript", type="primary"):
            if transcript:
                with st.spinner("Analyzing transcript..."):
                    analysis = st.session_state.tutor.analyze_transcript(transcript)
                    st.session_state['transcript'] = transcript
                    st.session_state['analysis'] = analysis
                    
                st.success("Analysis complete!")
                st.markdown("### Analysis Results")
                st.markdown(analysis)
            else:
                st.warning("Please paste a transcript first.")
    
    elif page == "🎯 Take Quiz":
        st.header("Quiz Time!")
        
        if 'transcript' not in st.session_state:
            st.info("Please upload a transcript first in the 'Upload Transcript' tab.")
        else:
            num_questions = st.slider("Number of questions:", 3, 10, 5)
            
            if st.button("Generate Quiz", type="primary"):
                with st.spinner("Creating quiz questions..."):
                    quiz = st.session_state.tutor.generate_quiz(
                        st.session_state['transcript'],
                        num_questions
                    )
                    st.session_state['quiz'] = quiz
                
                st.markdown("### Your Quiz")
                st.markdown(quiz)
    
    elif page == "💡 Ask About Concepts":
        st.header("Learn About Concepts")
        
        concept = st.text_input("What concept would you like to understand better?")
        
        context = ""
        if 'transcript' in st.session_state:
            use_context = st.checkbox("Use context from uploaded transcript")
            if use_context:
                context = st.session_state['transcript']
        
        if st.button("Explain", type="primary"):
            if concept:
                with st.spinner("Generating explanation..."):
                    explanation = st.session_state.tutor.explain_concept(concept, context)
                
                st.markdown("### Explanation")
                st.markdown(explanation)
            else:
                st.warning("Please enter a concept to explain.")

if __name__ == "__main__":
    main()
