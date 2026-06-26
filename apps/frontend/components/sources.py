import streamlit as st

def render_sources(sources: list):
    if not sources:
        return
        
    with st.expander("📚 Sources & Citations", expanded=False):
        for idx, source in enumerate(sources):
            # Attempt to extract metadata based on different possible source formats
            if isinstance(source, dict):
                # Format from GitHub or custom PDF extraction
                source_type = source.get("source", "Document")
                
                if source_type == "github":
                    repo = source.get("repository", "Unknown Repo")
                    path = source.get("path", "Unknown Path")
                    url = source.get("url", "#")
                    st.markdown(f"**{idx + 1}. [GitHub] {repo}**")
                    st.markdown(f"📄 [`{path}`]({url})")
                else:
                    document = source.get("document", "Unknown Document")
                    page = source.get("page", "Unknown Page")
                    st.markdown(f"**{idx + 1}. [PDF] {document}** (Page {page})")
                    
                # optionally show a snippet
                snippet = source.get("text", "")
                if snippet:
                    st.caption(f"_{snippet[:150]}..._")
            else:
                st.markdown(f"**{idx + 1}.** {str(source)}")
