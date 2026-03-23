import streamlit as st
from database import create_message, get_messages_by_user, get_replies_for_message


# ─────────────────────────────────────────────
# SHARED STYLES
# ─────────────────────────────────────────────
_WA_CSS = """
<style>
.wa-bg {
    background: #ece5dd;
    border-radius: 0 0 12px 12px;
    padding: 1.1rem 1rem;
    min-height: 340px;
    max-height: 460px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 10px;
}
.wa-row-right { display: flex; justify-content: flex-end; }
.wa-row-left  { display: flex; justify-content: flex-start; }

.wa-bubble-user {
    background: #302b63;
    color: white;
    border-radius: 16px 4px 16px 16px;
    padding: 9px 14px;
    max-width: 72%;
    font-size: 0.9rem;
    line-height: 1.6;
    white-space: pre-wrap;
    word-wrap: break-word;
}
.wa-bubble-admin {
    background: #ffffff;
    color: #1d1d3b;
    border-radius: 4px 16px 16px 16px;
    padding: 9px 14px;
    max-width: 72%;
    font-size: 0.9rem;
    line-height: 1.6;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    white-space: pre-wrap;
    word-wrap: break-word;
}
.wa-ts       { font-size: 0.69rem; color: #aaa; margin-top: 3px; padding: 0 3px; }
.wa-ts-right { text-align: right; }
</style>
"""


# ─────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────
def show_chat_page(user: dict):
    st.markdown(_WA_CSS, unsafe_allow_html=True)
    st.markdown('<p class="section-label">Messages</p>', unsafe_allow_html=True)

    if "chat_active_id" not in st.session_state:
        st.session_state.chat_active_id = None
    if "chat_composing" not in st.session_state:
        st.session_state.chat_composing = False

    messages = [dict(m) for m in get_messages_by_user(user["id"])]

    left, right = st.columns([1, 2.4], gap="small")

    # ── LEFT — thread list ───────────────────────────────────────────
    with left:
        st.markdown(
            '<p style="font-family:Syne,sans-serif;font-weight:700;font-size:0.8rem;'
            'color:#4a4a7a;text-transform:uppercase;letter-spacing:1.2px;margin-bottom:0.6rem;">'
            'Conversations</p>',
            unsafe_allow_html=True,
        )

        if st.button("✏️  New Message", use_container_width=True, key="chat_new_btn"):
            st.session_state.chat_composing = True
            st.session_state.chat_active_id = None
            st.rerun()

        st.markdown("<div style='margin-top:8px'></div>", unsafe_allow_html=True)

        if not messages:
            st.markdown(
                '<p style="font-size:0.82rem;color:#bbb;text-align:center;margin-top:1.2rem;">'
                'No conversations yet.</p>',
                unsafe_allow_html=True,
            )
        else:
            for m in messages:
                is_active = st.session_state.chat_active_id == m["id"]
                dot     = "🟢" if m["status"] == "resolved" else "🟠"
                preview = (m["body"][:38] + "…") if len(m["body"]) > 38 else m["body"]
                subj    = (m["subject"][:20] + "…") if len(m["subject"]) > 20 else m["subject"]
                bg      = "rgba(48,43,99,0.1)" if is_active else "#fff"
                border  = "#9b97cc"            if is_active else "#e2e5ec"

                st.markdown(
                    f"""<div style="border:1px solid {border};border-radius:10px;
                        padding:9px 11px;background:{bg};margin-bottom:4px;">
                        <div style="display:flex;justify-content:space-between;
                                    font-weight:700;font-size:0.87rem;color:#1d1d3b;">
                            <span>{subj}</span>
                            <span style="font-size:0.78rem">{dot}</span>
                        </div>
                        <div style="font-size:0.74rem;color:#999;margin-top:3px;">{preview}</div>
                        <div style="font-size:0.69rem;color:#bbb;margin-top:4px;">{m['created_at'][:16]}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
                if st.button("Open →", key=f"open_{m['id']}", use_container_width=True):
                    st.session_state.chat_active_id = m["id"]
                    st.session_state.chat_composing = False
                    st.rerun()

    # ── RIGHT — compose or conversation ─────────────────────────────
    with right:
        if st.session_state.chat_composing:
            _compose_panel(user)

        elif st.session_state.chat_active_id:
            active = next(
                (m for m in messages if m["id"] == st.session_state.chat_active_id), None
            )
            if active:
                _conversation_panel(active)
            else:
                st.info("Message not found.")

        else:
            st.markdown(
                """<div style="display:flex;flex-direction:column;align-items:center;
                    justify-content:center;min-height:380px;background:#f8f9fb;
                    border-radius:12px;border:1.5px dashed #e2e5ec;">
                    <div style="font-size:3rem;">💬</div>
                    <div style="font-family:Syne,sans-serif;font-weight:700;color:#4a4a7a;
                                margin-top:0.5rem;font-size:1.05rem;">Support Messages</div>
                    <div style="font-size:0.85rem;color:#aaa;margin-top:0.3rem;">
                        Select a conversation or start a new one.</div>
                </div>""",
                unsafe_allow_html=True,
            )


# ─────────────────────────────────────────────
# COMPOSE PANEL
# ─────────────────────────────────────────────
def _compose_panel(user: dict):
    st.markdown(
        '<div style="background:linear-gradient(135deg,#302b63,#24243e);'
        'border-radius:12px 12px 0 0;padding:0.8rem 1.1rem;">'
        '<span style="font-family:Syne,sans-serif;font-weight:700;font-size:1rem;color:white;">'
        '✏️  New Message to Support</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    subject = st.text_input("Subject", placeholder="e.g. Issue with detection result", key="compose_subj")
    body    = st.text_area("Message", placeholder="Describe your question or feedback…", height=150, key="compose_body")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("📨  Send Message", use_container_width=True, key="compose_send"):
            if not subject.strip():
                st.error("Please add a subject.")
            elif not body.strip():
                st.error("Please write a message.")
            else:
                ok = create_message(user["id"], subject, body)
                if ok:
                    st.session_state.chat_composing = False
                    st.success("✅ Message sent! Admin will reply shortly.")
                    st.rerun()
                else:
                    st.error("Something went wrong. Please try again.")
    with c2:
        if st.button("✖  Cancel", use_container_width=True, key="compose_cancel"):
            st.session_state.chat_composing = False
            st.rerun()


# ─────────────────────────────────────────────
# CONVERSATION PANEL
# ─────────────────────────────────────────────
def _conversation_panel(msg: dict):
    replies      = [dict(r) for r in get_replies_for_message(msg["id"])]
    status_label = "✅ Resolved" if msg["status"] == "resolved" else "🕐 Open"

    # Header bar
    st.markdown(
        f'<div style="background:linear-gradient(135deg,#302b63,#24243e);'
        f'border-radius:12px 12px 0 0;padding:0.8rem 1.1rem;'
        f'display:flex;justify-content:space-between;align-items:center;">'
        f'<span style="font-family:Syne,sans-serif;font-weight:700;font-size:0.97rem;color:white;">'
        f'🛡️ Support &nbsp;·&nbsp; {msg["subject"]}</span>'
        f'<span style="font-size:0.72rem;background:rgba(255,255,255,0.15);'
        f'border-radius:20px;padding:3px 11px;color:white;">{status_label}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Bubble area
    html = '<div class="wa-bg">'

    # User's original message — right
    html += (
        f'<div class="wa-row-right"><div style="max-width:72%">'
        f'<div class="wa-bubble-user">{msg["body"]}</div>'
        f'<div class="wa-ts wa-ts-right">You &nbsp;·&nbsp; {msg["created_at"][:16]}</div>'
        f'</div></div>'
    )

    # Admin replies — left
    if replies:
        for r in replies:
            html += (
                f'<div class="wa-row-left"><div style="max-width:72%">'
                f'<div class="wa-bubble-admin">{r["body"]}</div>'
                f'<div class="wa-ts">🛡️ <b>{r["admin_name"]}</b> &nbsp;·&nbsp; {r["created_at"][:16]}</div>'
                f'</div></div>'
            )
    else:
        html += (
            '<div style="text-align:center;color:#aaa;font-size:0.83rem;padding:2rem 0;">'
            '⏳ Waiting for admin reply…</div>'
        )

    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)