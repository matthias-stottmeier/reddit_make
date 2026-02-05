"""
Simple password authentication for the dashboard
"""
import streamlit as st
import hashlib

# Password hash (MakE2026!)
PASSWORD_HASH = hashlib.sha256("MakE2026!".encode()).hexdigest()


def check_password() -> bool:
    """
    Returns True if the user has entered the correct password.
    Shows a login form if not authenticated.
    """

    def password_entered():
        """Check if the entered password is correct."""
        entered = st.session_state.get("password", "")
        if hashlib.sha256(entered.encode()).hexdigest() == PASSWORD_HASH:
            st.session_state["authenticated"] = True
            del st.session_state["password"]  # Don't store password
        else:
            st.session_state["authenticated"] = False

    # Already authenticated
    if st.session_state.get("authenticated", False):
        return True

    # Show login form
    st.markdown("""
    <style>
        .login-container {
            max-width: 400px;
            margin: 100px auto;
            padding: 40px;
            text-align: center;
        }
        .make-logo-large {
            font-size: 3rem;
            font-weight: 800;
            color: #5B5BF7;
            margin-bottom: 8px;
        }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown('<p class="make-logo-large">MAKE</p>', unsafe_allow_html=True)
        st.markdown("### Reddit Scraper")
        st.markdown("---")

        st.text_input(
            "Password",
            type="password",
            key="password",
            on_change=password_entered,
            placeholder="Enter password"
        )

        if st.session_state.get("authenticated") == False:
            st.error("Incorrect password")

        st.caption("Contact admin for access")

    return False
