import streamlit as st
from components.sidebar import render_sidebar
from components.upload import render_upload_form

render_sidebar()

st.title("Documents")
st.markdown("Upload PDFs to index them into the Enterprise Vector Store.")

render_upload_form()

st.divider()
st.subheader("Indexed Documents")
st.info("Feature coming soon: View all indexed PDF documents in a table.")
