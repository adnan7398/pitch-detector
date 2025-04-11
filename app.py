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

# Configure Gemini
api_key = os.environ.get('GOOGLE_API_KEY', 'AIzaSyB-5eHo38zN9BdYIY1AwyEJLubYCzpYgNc')
genai.configure(api_key=api_key)

# Initialize Gemini model with correct model name
model = genai.GenerativeModel('gemini-2.0-flash')

# Set page config
st.set_page_config(
    page_title="Pitch Deck Analyzer",
    page_icon="📊",
    layout="wide"
)

# Custom CSS for better UI with dark/light theme support
st.markdown("""
    <style>
    :root {
        --primary-color: #4CAF50;
        --primary-hover: #45a049;
        --text-color: #2c3e50;
        --text-secondary: #666;
        --bg-color: #f8f9fa;
        --card-bg: #ffffff;
        --border-color: #e0e0e0;
        --shadow-color: rgba(0,0,0,0.1);
    }
    
    [data-theme="dark"] {
        --primary-color: #4CAF50;
        --primary-hover: #45a049;
        --text-color: #ffffff;
        --text-secondary: #b0b0b0;
        --bg-color: #1a1a1a;
        --card-bg: #2d2d2d;
        --border-color: #404040;
        --shadow-color: rgba(0,0,0,0.3);
    }
    
    .main {
        padding: 2rem;
        background-color: var(--bg-color);
        transition: all 0.3s ease;
    }
    
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 3.5em;
        background-color: var(--primary-color);
        color: white;
        font-weight: bold;
        font-size: 1.1em;
        transition: all 0.3s ease;
        border: none;
    }
    
    .stButton>button:hover {
        background-color: var(--primary-hover);
        transform: translateY(-2px);
        box-shadow: 0 4px 8px var(--shadow-color);
    }
    
    .stTextArea>div>div>textarea {
        min-height: 250px;
        border-radius: 12px;
        border: 2px solid var(--border-color);
        padding: 1rem;
        font-size: 1rem;
        background-color: var(--card-bg);
        color: var(--text-color);
    }
    
    .feedback-box {
        background-color: var(--card-bg);
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        border-left: 4px solid var(--primary-color);
        box-shadow: 0 4px 6px var(--shadow-color);
        color: var(--text-color);
        font-size: 1rem;
        line-height: 1.6;
        transition: all 0.3s ease;
    }
    
    .feedback-box:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px var(--shadow-color);
    }
    
    .analysis-header {
        color: var(--text-color);
        font-size: 1.5rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid var(--primary-color);
        font-weight: 600;
    }
    
    .stExpander {
        background-color: var(--card-bg);
        border-radius: 12px;
        box-shadow: 0 2px 4px var(--shadow-color);
    }
    
    .stExpander > div {
        padding: 1.5rem;
        color: var(--text-color);
    }
    
    .stTextArea > div > div > textarea {
        color: var(--text-color);
    }
    
    .stFileUploader {
        border-radius: 12px;
        border: 2px dashed var(--border-color);
        padding: 2rem;
        text-align: center;
        background-color: var(--card-bg);
    }
    
    .stFileUploader:hover {
        border-color: var(--primary-color);
    }
    
    .sidebar .sidebar-content {
        background-color: var(--card-bg);
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px var(--shadow-color);
    }
    
    .stMarkdown h1 {
        color: var(--text-color);
        font-size: 2.5rem;
        margin-bottom: 1.5rem;
    }
    
    .stMarkdown h2 {
        color: var(--text-color);
        font-size: 1.8rem;
        margin-bottom: 1rem;
    }
    
    .theme-switch {
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 1000;
    }
    
    .gradient-text {
        background: linear-gradient(45deg, #4CAF50, #2196F3);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: bold;
    }
    
    .card {
        background-color: var(--card-bg);
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px var(--shadow-color);
        transition: all 0.3s ease;
    }
    
    .card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px var(--shadow-color);
    }
    </style>
""", unsafe_allow_html=True)

# Theme toggle button
st.markdown("""
    <div class="theme-switch">
        <button onclick="toggleTheme()" style="
            background-color: var(--primary-color);
            color: white;
            border: none;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            font-size: 20px;
            cursor: pointer;
            box-shadow: 0 2px 4px var(--shadow-color);
        ">🌓</button>
    </div>
    
    <script>
    function toggleTheme() {
        const html = document.documentElement;
        const currentTheme = html.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        html.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
    }
    
    // Check for saved theme preference
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    </script>
""", unsafe_allow_html=True)

# Header with improved styling
st.markdown("""
    <div class="card" style='text-align: center; margin-bottom: 3rem;'>
        <h1 class="gradient-text" style='margin-bottom: 1.5rem;'>📊 Pitch Deck Analyzer</h1>
        <p style='color: var(--text-secondary); font-size: 1.2rem; margin-bottom: 1.5rem;'>
            Get AI-powered feedback on your pitch deck to improve your chances of success
        </p>
        <div style='display: flex; justify-content: center; gap: 2rem;'>
            <div style='text-align: left;'>
                <h3 style='color: var(--primary-color); margin-bottom: 1rem;'>What we analyze:</h3>
                <ul style='list-style-type: none; padding: 0; color: var(--text-secondary);'>
                    <li style='margin-bottom: 0.5rem;'>• Clarity and Structure</li>
                    <li style='margin-bottom: 0.5rem;'>• Market Potential</li>
                    <li style='margin-bottom: 0.5rem;'>• Investor Appeal</li>
                    <li style='margin-bottom: 0.5rem;'>• Areas for Improvement</li>
                </ul>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# Initialize session state
if 'feedback' not in st.session_state:
    st.session_state.feedback = None

def extract_text_from_pdf(pdf_file):
    """Extract text and handle images from PDF using PyMuPDF."""
    try:
        # Create a BytesIO object from the uploaded file
        pdf_bytes = io.BytesIO(pdf_file.read())
        
        # Open the PDF using PyMuPDF
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        # Extract text from each page
        text = ""
        for page_num, page in enumerate(doc):
            # Extract text with better formatting
            page_text = page.get_text("text")
            if page_text.strip():
                text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
            
            # Handle images and charts
            image_list = page.get_images()
            if image_list:
                text += f"\n[Visual content found on page {page_num + 1}]\n"
                for img_index, img in enumerate(image_list):
                    text += f"[Image/Chart {img_index + 1}]\n"
            
            # Extract tables if present
            try:
                blocks = page.get_text("dict")["blocks"]
                for block in blocks:
                    if block["type"] == 1:  # Table block
                        text += "\n[Table found]\n"
                        if "lines" in block:
                            for line in block["lines"]:
                                if "spans" in line:
                                    text += " | ".join([span["text"] for span in line["spans"]]) + "\n"
            except Exception as e:
                # Skip table extraction if there's an error
                continue
        
        # Close the document
        doc.close()
        
        if not text.strip():
            # Try OCR if no text is found
            try:
                import pytesseract
                from pdf2image import convert_from_bytes
                
                # Convert PDF to images
                images = convert_from_bytes(pdf_bytes.getvalue())
                ocr_text = ""
                
                for i, image in enumerate(images):
                    ocr_text += f"\n--- Page {i + 1} (OCR) ---\n"
                    ocr_text += pytesseract.image_to_string(image)
                
                if ocr_text.strip():
                    text = ocr_text
                else:
                    raise ValueError("No text could be extracted from the PDF.")
            except ImportError:
                st.warning("For better PDF text extraction, install: pip install pytesseract pdf2image")
                raise ValueError("No text could be extracted from the PDF. Consider installing OCR tools.")
            
        return text
    except Exception as e:
        st.error(f"Error extracting text from PDF: {str(e)}")
        return None

# File upload and text input with improved layout
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
        <div class="card">
            <h2 style='color: var(--text-color); margin-bottom: 1rem;'>📄 Upload PDF</h2>
            <p style='color: var(--text-secondary); margin-bottom: 1rem;'>Upload your pitch deck in PDF format</p>
        </div>
    """, unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Choose a PDF file", type=['pdf'], label_visibility="collapsed")
    
    if uploaded_file is not None:
        try:
            # Extract text from PDF
            pitch_text = extract_text_from_pdf(uploaded_file)
            if pitch_text:
                st.session_state.pitch_text = pitch_text
                st.success("✅ PDF processed successfully!")
                # Show a preview of the extracted text
                with st.expander("📝 Preview Extracted Text", expanded=True):
                    st.text_area("Extracted Text", pitch_text[:1000] + "..." if len(pitch_text) > 1000 else pitch_text, height=200)
            else:
                st.error("❌ Failed to extract text from PDF. Please try another file or enter text manually.")
        except Exception as e:
            st.error(f"❌ Error processing PDF: {str(e)}")

with col2:
    st.markdown("""
        <div class="card">
            <h2 style='color: var(--text-color); margin-bottom: 1rem;'>✍️ Or Enter Pitch Text</h2>
            <p style='color: var(--text-secondary); margin-bottom: 1rem;'>Paste your pitch text directly</p>
        </div>
    """, unsafe_allow_html=True)
    pitch_text_input = st.text_area("Paste your pitch text here", height=300, label_visibility="collapsed")
    if pitch_text_input:
        st.session_state.pitch_text = pitch_text_input

# Analysis button with improved styling
st.markdown("""
    <div style='text-align: center; margin: 2rem 0;'>
        <style>
        .analyze-button {
            background: linear-gradient(45deg, #4CAF50, #2196F3);
            color: white;
            padding: 1rem 2rem;
            border: none;
            border-radius: 12px;
            font-size: 1.2rem;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 6px var(--shadow-color);
        }
        .analyze-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 12px var(--shadow-color);
        }
        </style>
    </div>
""", unsafe_allow_html=True)

if st.button("🔍 Analyze Pitch", type="primary"):
    if 'pitch_text' in st.session_state and st.session_state.pitch_text:
        try:
            # Create pitch analyzer
            analyzer = PitchAnalyzer(model=model)
            
            # Generate feedback
            with st.spinner("🤖 Analyzing your pitch..."):
                feedback = analyzer.analyze_pitch(st.session_state.pitch_text)
                st.session_state.feedback = feedback

        except Exception as e:
            st.error(f"❌ Error analyzing pitch: {str(e)}")
    else:
        st.warning("⚠️ Please upload a PDF or enter pitch text to analyze.")

# Display feedback with improved layout
if st.session_state.feedback:
    st.markdown("""
        <div class="card" style='text-align: center; margin: 3rem 0;'>
            <h2 style='color: var(--text-color);'>📝 Analysis Results</h2>
            <p style='color: var(--text-secondary);'>Here's what our AI thinks about your pitch</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Create columns for better layout
    col1, col2 = st.columns(2)
    
    for i, (category, analysis) in enumerate(st.session_state.feedback.items()):
        with (col1 if i % 2 == 0 else col2):
            st.markdown(f"""
            <div class="card">
                <div class="analysis-header">{category} Analysis</div>
                <div class="feedback-box">
                    {analysis}
                </div>
            </div>
            """, unsafe_allow_html=True)

# Sidebar with improved styling
with st.sidebar:
    st.markdown("""
        <div class="card">
            <h2 style='color: var(--text-color); margin-bottom: 1.5rem;'>About</h2>
            <p style='color: var(--text-secondary); margin-bottom: 1rem;'>
                Pitch Deck Analyzer is an AI-powered tool that helps entrepreneurs improve their pitch decks.
            </p>
            <h3 style='color: var(--primary-color); margin-bottom: 1rem;'>What we analyze:</h3>
            <ul style='color: var(--text-secondary);'>
                <li style='margin-bottom: 0.5rem;'>• Clarity and Structure</li>
                <li style='margin-bottom: 0.5rem;'>• Market Potential</li>
                <li style='margin-bottom: 0.5rem;'>• Investor Appeal</li>
                <li style='margin-bottom: 0.5rem;'>• Areas for Improvement</li>
            </ul>
            <p style='color: var(--text-secondary); margin-top: 2rem;'>
                Made with ❤️ using Gemini AI
            </p>
        </div>
    """, unsafe_allow_html=True)

