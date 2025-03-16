import streamlit as st
import os
import base64
import json
import time
from mistralai import Mistral

st.set_page_config(layout="wide", page_title="DocVision OCR", page_icon="📄")

# Add custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        background: linear-gradient(90deg, #6366F1, #4F46E5);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .subheader {
        color: #6B7280;
        margin-bottom: 1.5rem;
    }
    .stExpander {
        border-radius: 8px;
        border: 1px solid #E5E7EB;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='main-header'>DocVision OCR</h1>", unsafe_allow_html=True)
st.markdown("<p class='subheader'>Advanced document, image text extraction powered by Mistral AI</p>", unsafe_allow_html=True)

# Replace the current tagline
st.markdown("<div style='padding: 0.5rem; margin-bottom: 1rem; border-radius: 5px; background-color: #F3F4F6;'><p style='margin-bottom: 0; color: #4B5563; font-size: 0.9rem;'>Created by <a href='https://github.com/Allmight-456' style='color: #4F46E5; text-decoration: none;'>Allimght-456</a> • <i>Extracting wisdom from documents</i></p></div>", unsafe_allow_html=True)

with st.expander("About DocVision"):
    st.markdown("""
    ### Transform Documents into Structured Text
    
    DocVision harnesses the power of Mistral's OCR technology to extract text from:
    - PDF documents (multi-page supported)
    - Images (JPG, PNG formats)
    - URL-based resources
    
    **Perfect for:** Document digitization, information extraction, and text analysis workflows.
    """)

# 1. API Key Input
api_key = st.text_input("Enter your Mistral API Key", type="password")
if not api_key:
    st.info("Please enter your API key to continue.")
    st.stop()

# Initialize session state variables for persistence
if "ocr_result" not in st.session_state:
    st.session_state["ocr_result"] = []
if "preview_src" not in st.session_state:
    st.session_state["preview_src"] = []
if "image_bytes" not in st.session_state:
    st.session_state["image_bytes"] = []

# 2. Choose file type: PDF or Image
file_type = st.radio("Select file type", ("PDF", "Image"))

# 3. Select source type: URL or Local Upload
source_type = st.radio("Select source type", ("URL", "Local Upload"))

input_url = ""
uploaded_files = []

if source_type == "URL":
    input_url = st.text_area("Enter one or multiple URLs (separate with new lines)")
else:
    uploaded_files = st.file_uploader("Upload one or more files", type=["pdf", "jpg", "jpeg", "png"], accept_multiple_files=True)

# 4. Process Button & OCR Handling
if st.button("Process"):
    if source_type == "URL" and not input_url.strip():
        st.error("Please enter at least one valid URL.")
    elif source_type == "Local Upload" and not uploaded_files:
        st.error("Please upload at least one file.")
    else:
        client = Mistral(api_key=api_key)
        st.session_state["ocr_result"] = []
        st.session_state["preview_src"] = []
        st.session_state["image_bytes"] = []
        
        sources = input_url.split("\n") if source_type == "URL" else uploaded_files
        
        for idx, source in enumerate(sources):
            if file_type == "PDF":
                if source_type == "URL":
                    document = {"type": "document_url", "document_url": source.strip()}
                    preview_src = source.strip()
                else:
                    file_bytes = source.read()
                    encoded_pdf = base64.b64encode(file_bytes).decode("utf-8")
                    document = {"type": "document_url", "document_url": f"data:application/pdf;base64,{encoded_pdf}"}
                    preview_src = f"data:application/pdf;base64,{encoded_pdf}"
            else:
                if source_type == "URL":
                    document = {"type": "image_url", "image_url": source.strip()}
                    preview_src = source.strip()
                else:
                    file_bytes = source.read()
                    mime_type = source.type
                    encoded_image = base64.b64encode(file_bytes).decode("utf-8")
                    document = {"type": "image_url", "image_url": f"data:{mime_type};base64,{encoded_image}"}
                    preview_src = f"data:{mime_type};base64,{encoded_image}"
                    st.session_state["image_bytes"].append(file_bytes)
            
            with st.spinner(f"Processing {source if source_type == 'URL' else source.name}..."):
                try:
                    ocr_response = client.ocr.process(model="mistral-ocr-latest", document=document)
                    time.sleep(1)  # wait 1 second between request to prevent rate limit exceeding
                    
                    # Improved error handling and result processing
                    if hasattr(ocr_response, 'pages'):
                        result_text = "\n\n".join(page.markdown for page in ocr_response.pages)
                    elif isinstance(ocr_response, list):
                        result_text = "\n\n".join(page.markdown for page in ocr_response)
                    else:
                        result_text = "No text could be extracted from the image/document."
                    
                    if not result_text.strip():
                        result_text = "No text was extracted from the document. Please ensure the image/document is clear and contains readable text."
                        
                except Exception as e:
                    error_message = str(e)
                    if "API key" in error_message.lower():
                        result_text = "Error: Invalid or missing API key. Please check your Mistral API key."
                    else:
                        result_text = f"Error processing document: {error_message}\nPlease ensure the document is valid and try again."
                    st.error(result_text)
                
                st.session_state["ocr_result"].append(result_text)
                st.session_state["preview_src"].append(preview_src)

if st.session_state["ocr_result"]:
    for idx, result in enumerate(st.session_state["ocr_result"]):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader(f"Input PDF {idx+1}")
            if file_type == "PDF":
                pdf_embed_html = (
                    f'<iframe src="{st.session_state["preview_src"][idx]}" '
                    f'width="100%" height="800" frameborder="0"></iframe>'
                )
                st.markdown(pdf_embed_html, unsafe_allow_html=True)
            else:
                if source_type == "Local Upload" and st.session_state["image_bytes"]:
                    st.image(st.session_state["image_bytes"][idx])
                else:
                    st.image(st.session_state["preview_src"][idx])
        
        with col2:
            st.subheader(f"Download OCR results {idx+1}")
            
            # Arrange the download buttons horizontally using columns
            btn_col1, btn_col2, btn_col3 = st.columns(3)
            
            # Prepare JSON data (pretty printed)
            json_data = json.dumps({"ocr_result": result}, ensure_ascii=False, indent=2)
            
            with btn_col1:
                st.download_button(
                    label="Download JSON",
                    data=json_data,
                    file_name=f"Output_{idx+1}.json",
                    mime="application/json"
                )
            with btn_col2:
                st.download_button(
                    label="Download TXT",
                    data=result,
                    file_name=f"Output_{idx+1}.txt",
                    mime="text/plain"
                )
            with btn_col3:
                st.download_button(
                    label="Download MD",
                    data=result,
                    file_name=f"Output_{idx+1}.md",
                    mime="text/markdown"
                )
            
            # Inject custom CSS to change text color in the raw text area to orange
            st.markdown(
                """
                <style>
                .stTextArea textarea {
                    color: orange;
                    font-size: 16px;
                }
                </style>
                """,
                unsafe_allow_html=True
            )
            
            # Create tabs for "Preview" (rendered markdown) and "Raw" (plain markdown text)
            tab1, tab2 = st.tabs(["Preview", "Raw"])
            with tab1:
                # Create a styled container for the preview with borders
                st.markdown(
                    f"""
                    <div style="border: 1px solid #ddd; border-radius: 4px; padding: 12px; 
                            height: 650px; overflow-y: auto; background-color: black;">
                        {result}
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
            with tab2:
                st.text_area("Raw Markdown", result, height=650)

