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
    logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
    if not os.path.exists(logo_path):
        return None
    with open(logo_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode("utf-8")


# ─────────────────────────────────────────────
# AUTH PAGE  (login + register tabs)
# ─────────────────────────────────────────────
def show_auth_page():
    st.markdown("""
    <style>
    .auth-hero {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
        border-radius: 15px;
        padding: 0.2rem 1.2rem;
        margin-bottom: 0.5rem;
        box-shadow: 0 8px 32px rgba(0,0,0,0.35);
        width: 60%;
        margin-left: auto;
        margin-right: auto;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
    }
    .auth-hero-left {
        display: flex;
        align-items: center;
        gap: 1rem;
        min-width: 0;
    }
    .auth-hero h2 {
        font-family: 'Syne', sans-serif;
        font-size: 1.7rem;
        font-weight: 600;
        color: #fff;
        margin: 0;
        line-height: 1.1;
        letter-spacing: -0.3px;
        white-space: nowrap;
    }
    .auth-hero p {
        color: rgba(255,255,255,0.55);
        font-size: 0.8rem;
        margin: 0.25rem 0 0 0;
        line-height: 1.4;
        white-space: nowrap;
    }
    .auth-hero-badge {
        background: rgba(255,255,255,0.1);
        border: 1px solid rgba(255,255,255,0.2);
        color: rgba(255,255,255,0.85);
        border-radius: 30px;
        font-size: 0.75rem;
        padding: 0.45rem 1.1rem;
        letter-spacing: 0.8px;
        text-transform: uppercase;
        font-weight: 600;
        white-space: nowrap;
        flex-shrink: 0;
    }

    /* ── Tablet ── */
    @media (max-width: 768px) {
        .auth-hero {
            width: 90%;
            padding: 0.2rem 1.2rem;
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 0.9rem;
        }
        .auth-hero h2 {
            font-size: 1.4rem;
            white-space: normal;
        }
        .auth-hero p {
            white-space: normal;
            font-size: 0.78rem;
        }
        .auth-hero-badge {
            white-space: nowrap;
            flex-shrink: 0;
            align-self: flex-end;
            padding: 0.45rem 1.1rem;
        }
    }

    /* ── Mobile ── */
    @media (max-width: 480px) {
        .auth-hero {
            width: 100%;
            padding: 0.5rem 1rem;
            border-radius: 12px;
            gap: 0.75rem;
        }
        .auth-hero h2 {
            font-size: 1.2rem;
        }
        .auth-hero p {
            font-size: 0.74rem;
        }
        .auth-hero-badge {
            font-size: 0.68rem;
            padding: 0.35rem 0.85rem;
        }
    }
    </style>

    <div class="auth-hero">
        <div class="auth-hero-left">
            <div>
                <h2>Hey, Welcome ...</h2>
                <p>Sign in or create an account to classify news articles/headlines.</p>
            </div>
        </div>
        <div class="auth-hero-badge">⚡ Fake News Detector</div>
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
        background: rgba(48,43,99,0.15) !important;
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
    /* ── Auth buttons — rotating green edge animation ── */

/* Base button */
div[data-testid="stVerticalBlock"] .stButton > button {
    background: #ffffff !important;
    color: #302b63 !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    padding: 0.65rem 2rem !important;
    position: relative !important;
    z-index: 0 !important;
    overflow: hidden !important;
    transition: color 0.2s ease !important;
}

/* Rotating conic-gradient ring — sits behind the button */
div[data-testid="stVerticalBlock"] .stButton > button::before {
    content: '' !important;
    position: absolute !important;
    inset: -4px !important;
    border-radius: 13px !important;
    background: conic-gradient(
        from 0deg,
        transparent 0deg,
        #6c63ff 60deg,
        #a78bfa 100deg,
        #e879f9 140deg,
        #38bdf8 200deg,
        transparent 260deg
    ) !important;
    opacity: 0 !important;
    animation: none !important;
    transition: opacity 0.3s ease !important;
    z-index: -2 !important;
}

/* Solid dark fill layer — covers the center so only the edge glows */
div[data-testid="stVerticalBlock"] .stButton > button::after {
    content: '' !important;
    position: absolute !important;
    inset: 2px !important;
    background: #ffff !important;
    border-radius: 9px !important;
    z-index: -1 !important;
}

/* On hover — start the spin */
div[data-testid="stVerticalBlock"] .stButton > button:hover::before {
    opacity: 1 !important;
    animation: border-spin 1s linear infinite !important;
}

/* Keyframe — full 360 rotation */
@keyframes border-spin {
    from { transform: rotate(0deg); }
    to   { transform: rotate(360deg); }
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
