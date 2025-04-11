import streamlit as st
import google.generativeai as genai
import os
from streamlit.components.v1 import html
from langchain_community.document_loaders import PyPDFLoader
from typing import List
from langchain.prompts.chat import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    BaseMessage,
)
import time
from CAMELAgent import CAMELAgent, PitchAnalyzer
from PIL import Image
import backoff
import tempfile
import fitz  # PyMuPDF
import io


api_key = os.environ.get('GOOGLE_API_KEY', 'AIzaSyB-5eHo38zN9BdYIY1AwyEJLubYCzpYgNc')
genai.configure(api_key=api_key)


model = genai.GenerativeModel(
    model_name='gemini-1.0-pro',
    generation_config=genai.types.GenerationConfig(
        temperature=0.7,
        top_p=0.8,
        top_k=40,
        max_output_tokens=1024,
    )
)

# Set page config
st.set_page_config(
    page_title="Pitch Deck Analyzer",
    page_icon="📊",
    layout="wide"
)

st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
    }
    .stTextArea>div>div>textarea {
        min-height: 200px;
    }
    .feedback-box {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.title("📊 Pitch Deck Analyzer")
st.markdown("""
    Upload your pitch deck (PDF) or paste your pitch text to get AI-powered feedback on:
    - Clarity and Structure
    - Market Potential
    - Investor Appeal
    - Areas for Improvement
""")

# Initialize session state
if 'feedback' not in st.session_state:
    st.session_state.feedback = None

def extract_text_from_pdf(pdf_file):
    """Extract text from PDF using PyMuPDF."""
    try:
        # Create a BytesIO object from the uploaded file
        pdf_bytes = io.BytesIO(pdf_file.read())
        
        # Open the PDF using PyMuPDF
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        # Extract text from each page
        text = ""
        for page in doc:
            text += page.get_text()
        
        # Close the document
        doc.close()
        
        if not text.strip():
            raise ValueError("No text could be extracted from the PDF. The file might be scanned or contain only images.")
            
        return text
    except Exception as e:
        st.error(f"Error extracting text from PDF: {str(e)}")
        return None

# File upload and text input
col1, col2 = st.columns(2)

with col1:
    st.subheader("Upload PDF")
    uploaded_file = st.file_uploader("Choose a PDF file", type=['pdf'])
    
    if uploaded_file is not None:
        try:
            # Extract text from PDF
            pitch_text = extract_text_from_pdf(uploaded_file)
            if pitch_text:
                st.session_state.pitch_text = pitch_text
                st.success("PDF processed successfully!")
                # Show a preview of the extracted text
                with st.expander("Preview Extracted Text"):
                    st.text_area("Extracted Text", pitch_text[:1000] + "..." if len(pitch_text) > 1000 else pitch_text, height=200)
            else:
                st.error("Failed to extract text from PDF. Please try another file or enter text manually.")
        except Exception as e:
            st.error(f"Error processing PDF: {str(e)}")

with col2:
    st.subheader("Or Enter Pitch Text")
    pitch_text_input = st.text_area("Paste your pitch text here", height=300)
    if pitch_text_input:
        st.session_state.pitch_text = pitch_text_input

# Analysis button
if st.button("Analyze Pitch", type="primary"):
    if 'pitch_text' in st.session_state and st.session_state.pitch_text:
        try:
            # Create pitch analyzer
            analyzer = PitchAnalyzer(model)
            
            # Generate feedback
            with st.spinner("Analyzing pitch..."):
                feedback = analyzer.analyze_pitch(st.session_state.pitch_text)
                st.session_state.feedback = feedback

        except Exception as e:
            st.error(f"Error analyzing pitch: {str(e)}")
    else:
        st.warning("Please upload a PDF or enter pitch text to analyze.")

# Display feedback
if st.session_state.feedback:
    st.markdown("## 📝 Analysis Results")
    
    for category, analysis in st.session_state.feedback.items():
        with st.expander(f"### {category} Analysis", expanded=True):
            st.markdown(f"""
            <div class="feedback-box">
                {analysis}
            </div>
            """, unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("""
    # About 
    Pitch Deck Analyzer is an AI-powered tool that helps entrepreneurs improve their pitch decks.
    It provides detailed feedback on:
    - Clarity and Structure
    - Market Potential
    - Investor Appeal
    - Areas for Improvement
    
    Made with ❤️ using Gemini AI
    """)

