import streamlit as st
from services.api_client import api_client
from components.sidebar import render_sidebar

render_sidebar()

st.title("GitHub Repositories")
st.markdown("Index GitHub repositories (Code, Markdown, Issues, PRs) into the Enterprise Vector Store.")

repository = st.text_input("Repository (e.g., owner/repository)", placeholder="e.g., hwchase17/langchain")

if st.button("Index Repository", type="primary"):
    if not repository:
        st.warning("Please enter a repository name.")
    else:
        with st.spinner(f"Fetching and indexing {repository}... This may take a while."):
            try:
                result = api_client.index_github(repository)
                st.success("Indexing successful!")
                st.json(result)
            except Exception as e:
                st.error(f"Failed to index repository: {str(e)}")

st.divider()
st.subheader("Indexed Repositories")
st.info("Feature coming soon: View all indexed repositories and their status.")
