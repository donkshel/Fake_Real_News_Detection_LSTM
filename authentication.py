# authentication.py 
import streamlit as st
import base64
import os
from database import (
    create_user,
    get_user_by_username,
    verify_password,
)


# ─────────────────────────────────────────────
# SESSION STATE HELPERS
# ─────────────────────────────────────────────
def is_logged_in() -> bool:
    return st.session_state.get("logged_in", False)

# Returns a dict with id, username, email, role — or None if not logged in.
def current_user() -> dict | None:
    """Return a plain dict with id, username, email, role — or None."""
    if not is_logged_in():
        return None
    return st.session_state.get("current_user")

# Check if current user is admin (returns False if not logged in)
def is_admin() -> bool:
    u = current_user()
    return u is not None and u.get("role") == "admin"

# Store user info in session after a successful login
def _login_user(user_row):
    """Store user info in session after a successful login."""
    st.session_state.logged_in = True
    st.session_state.current_user = {
        "id":       user_row["id"],
        "username": user_row["username"],
        "email":    user_row["email"],
        "role":     user_row["role"],
    }

# Clear session to log out
def logout():
    for key in ["logged_in", "current_user"]:
        st.session_state.pop(key, None)
    st.rerun()


# ─────────────────────────────────────────────
# LOGO HELPER
# ─────────────────────────────────────────────
def _get_logo_base64() -> str | None:
    """Read logo.png from the project root and return a base64 string."""
    logo_path = os.path.join(os.path.dirname(__file__), "images/logo.png")
    if not os.path.exists(logo_path):
        return None
    with open(logo_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode("utf-8")


# ─────────────────────────────────────────────
# AUTH PAGE  (login + register tabs)
# ─────────────────────────────────────────────
def show_auth_page():
    """
    Render the full authentication page.
    Call this from news_app.py when the user is not logged in.
    """
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
        border-radius: 15px;
        padding: 0.5rem;
        margin-bottom: 0.5rem;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0,0,0,0.35);
        height: fit-content;
        width: 50%;
        margin-left: auto;
        margin-right: auto;
    ">
        <div style="
            display:inline-block;background:rgba(255,255,255,0.1);
            border:1px solid rgba(255,255,255,0.2);color:#c9c3f5;
            border-radius:50px;font-size:.78rem;padding:4px 14px;
            margin-bottom:1rem;letter-spacing:1.5px;text-transform:uppercase;
            font-weight:700;
        ">Fake News Detector</div>
        <h2 style="
            font-family:'Syne',sans-serif;font-size:1.8rem;font-weight:500;
            color:#fff;margin:0 0 .1rem;letter-spacing:-.5px;
        ">Hey, Welcome </h2>
        <p style="color:#b0aed8;font-size:1.05rem;margin:0;line-height:1;">
            Sign in or create an account to classify news articles/headlines.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Logo ──────────────────────────────────
    logo_b64 = _get_logo_base64()
    if logo_b64:
        st.markdown(f"""
        <div style="text-align:center; margin: 0.8rem 0;">
            <img src="data:image/png;base64,{logo_b64}" alt="Logo"
                 style="height:100px; object-fit:contain;" />
        </div>
        """, unsafe_allow_html=True)

    # ── Card styling via CSS 
    st.markdown("""
    <style>
    /* Target the middle column to look like a card */
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) > div[data-testid="stVerticalBlockBorderWrapper"],
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) {
        background: #ffffff;
        border-radius: 16px;
        border: 1px solid #e2e5ec;
        box-shadow: 0 4px 20px rgba(0,0,0,0.07);
        padding: 1rem !important;
    }
 
    /* Pill-style tab container */
    div[data-testid="stTabs"] > div:first-child {
        background: linear-gradient(135deg, #e0dff0, #c9c3f5);
        border-radius: 12px;
        padding: 15px 50px;
        gap: 10px !important;
        width: fit-content;
        margin: 0 auto 1.2rem auto;
        border: 1px solid #e0dff0;
    }
 
    /* Each tab button */
    div[data-testid="stTabs"] button[data-baseweb="tab"] {
        border-radius: 9px !important;
        padding: 0.45rem 1.4rem !important;
        font-family: 'Syne', sans-serif !important;
        font-weight: 700 !important;
        font-size: 0.88rem !important;
        color: #6b6b9a !important;
        background: transparent !important;
        border: none !important;
        transition: all 0.2s ease !important;
    }
 
    /* Active tab */
    div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, #302b63, #24243e) !important;
        color: #ffffff !important;
        box-shadow: 0 2px 8px rgba(48,43,99,0.3) !important;
    }
 
    /* Hide default underline and border */
    div[data-testid="stTabs"] [data-baseweb="tab-highlight"],
    div[data-testid="stTabs"] [data-baseweb="tab-border"] {
        display: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

    _, col, _ = st.columns([1, 2, 1])
    with col:
                
        tab_login, tab_register = st.tabs(["🔑 Sign In", "📝 Register"])

        # ── Login ──────────────────────────────
        with tab_login:
            st.markdown("<br>", unsafe_allow_html=True)
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("Sign In", key="btn_login", use_container_width=True):
                if not username or not password:
                    st.error("Please fill in all fields.")
                else:
                    user = get_user_by_username(username.strip().lower())
                    if user is None or not verify_password(password, user["password"]):
                        st.error("Invalid username or password.")
                    else:
                        _login_user(user)
                        st.success(f"Welcome back, {user['username']}!")
                        st.rerun()

        # ── Register ───────────────────────────
        with tab_register:
            st.markdown("<br>", unsafe_allow_html=True)
            new_username = st.text_input("Username",        key="reg_username", placeholder="e.g    don")
            new_email    = st.text_input("Email",           key="reg_email", placeholder="e.g   don@example.com")
            new_pw       = st.text_input("Password",        type="password", key="reg_pw")
            new_pw2      = st.text_input("Confirm password",type="password", key="reg_pw2")
            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("Create Account", key="btn_register", use_container_width=True):
                errors = _validate_registration(new_username, new_email, new_pw, new_pw2)
                if errors:
                    for e in errors:
                        st.error(e)
                else:
                    ok = create_user(new_username, new_email, new_pw)
                    if ok:
                        user = get_user_by_username(new_username)
                        _login_user(user)
                        st.success("Account created! You are now signed in.")
                        st.rerun()
                    else:
                        st.error("Username or email already taken. Please choose another.")
        
        
# ─────────────────────────────────────────────
# VALIDATION
# ─────────────────────────────────────────────
def _validate_registration(username, email, pw, pw2) -> list[str]:
    errors = []

    if not username or len(username) < 3:
        errors.append("Username must be at least 3 characters.")

    if " " in username:
        errors.append("Username cannot contain spaces.")

    if not email or "@" not in email or "." not in email:
        errors.append("Enter a valid email address.")

    if not pw or len(pw) < 6:
        errors.append("Password must be at least 6 characters.")

    if pw != pw2:
        errors.append("Passwords do not match.")

    return errors


# ─────────────────────────────────────────────
# SIDEBAR USER WIDGET
# ─────────────────────────────────────────────
def show_user_sidebar():
    """
    Call this inside `with st.sidebar:` to show the logged-in user badge + logout.
    """
    u = current_user()
    if u is None:
        return

    role_badge = "🛡️ Admin" if u["role"] == "admin" else "👤 User"
    st.markdown(f"""
    <div style="
        background:rgba(48,43,99,0.1);border:1px solid rgba(48,43,99,0.25);
        border-radius:10px;padding:.8rem 1rem;margin-bottom:1rem;
    ">
        <div style="font-weight:700;font-size:.95rem;">{u['username']}</div>
        <div style="font-size:.78rem;color:#888;">{role_badge} &nbsp;·&nbsp; {u['email']}</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🔒 Sign Out", use_container_width=True):
        logout()
