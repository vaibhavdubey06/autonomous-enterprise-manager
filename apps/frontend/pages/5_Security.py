import streamlit as st

from utils.config import settings

st.set_page_config(page_title="Enterprise Security", page_icon="🛡️", layout="wide")

st.title("🛡️ Enterprise Security Platform")
st.markdown("Identity, Authorization, and Auditing Platform")

# Since the frontend does not have authentication built-in, we simulate being an Admin
# In a real app, Streamlit would capture an OAuth token or ask for a login.

tab1, tab2, tab3 = st.tabs(["Overview", "Tenants & Users", "Security Audit Logs"])

API_URL = f"{settings.BACKEND_URL.rstrip('/')}/api/v1/security"

with tab1:
    st.header("Security Operations Center")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Active Sessions", "12", "Normal")
    col2.metric("Failed Logins (24h)", "3", "-2")
    col3.metric("Rate Limits Triggered", "0", "0")
    col4.metric("Permission Denials", "1", "1")

    st.subheader("Authorization Pipeline")
    st.info("Identity Context ➔ Tenant ➔ RBAC ➔ ABAC ➔ Capability Permissions")

with tab2:
    st.header("Multi-Tenancy & Identity")
    st.markdown("Tenants automatically partition knowledge, operations, and execution.")
    # Here we would fetch from /api/v1/security/tenants if implemented.
    # For now we display a dummy view since it's just the interface.
    st.table(
        [
            {
                "Tenant ID": "00000000-0000-0000-0000-000000000000",
                "Name": "Default Enterprise",
                "Status": "Active",
            }
        ]
    )

with tab3:
    st.header("Security Audit Logs")
    st.markdown("Immutable records of all security events.")

    if st.button("Refresh Audit Logs"):
        try:
            # We must pass the capability in headers to bypass security or authenticate
            # But the mock /audit route requires 'security.manage' permission
            st.error("Authentication required to view audit logs in this view.")
        except Exception as e:
            st.error(f"Error connecting to backend: {e}")
