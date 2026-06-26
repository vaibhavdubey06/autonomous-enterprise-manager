import streamlit as st
from services.api_client import api_client

def render_upload_form():
    st.subheader("Upload Document")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
    
    if uploaded_file is not None:
        if st.button("Upload and Index", type="primary"):
            with st.spinner("Uploading and indexing document..."):
                try:
                    result = api_client.upload_pdf(uploaded_file.getvalue(), uploaded_file.name)
                    st.success("Upload successful!")
                    st.json(result)
                except Exception as e:
                    st.error(f"Upload failed: {str(e)}")
