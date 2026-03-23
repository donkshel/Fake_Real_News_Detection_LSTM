import streamlit as st
import pandas as pd
from database import (
    get_admin_stats,
    get_all_users,
    get_all_history,
    get_all_messages,
    get_messages_by_user,
    get_replies_for_message,
    create_reply,
    update_message_status,
    delete_message,
    get_open_message_count,
    delete_user,
    update_user_role,
    update_user_password,
)


# ─────────────────────────────────────────────
# SHARED STYLES  (injected once)
# ─────────────────────────────────────────────
_INBOX_CSS = """
<style>
.wa-bg-admin {
    background: #ece5dd;
    border-radius: 0 0 0 0;
    padding: 1rem;
    min-height: 400px;
    max-height: 520px;
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
    max-width: 100%;
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
    max-width: 70%;
    font-size: 0.9rem;
    line-height: 1.6;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    white-space: pre-wrap;
    word-wrap: break-word;
}
.wa-ts       { font-size: 0.68rem; color: #aaa; margin-top: 3px; padding: 0 3px; }
.wa-ts-left { text-align: left; }
.wa-divider  {
    text-align: center;
    font-size: 0.72rem;
    color: #bbb;
    padding: 4px 0;
    font-style: italic;
}
</style>
"""


# ─────────────────────────────────────────────
# ADMIN DASHBOARD
# ─────────────────────────────────────────────
def show_admin_page():
    st.markdown('<h3 class="section-label">🛡️ Admin Dashboard</h3>', unsafe_allow_html=True)

    stats = get_admin_stats()
    total_users   = stats.get("total_users", 0)
    total_classif = stats.get("total_classif", 0)
    recent_7days  = stats.get("recent_7days", 0)
    real_count    = stats.get("real_count", 0)
    fake_count    = stats.get("fake_count", 0)
    uncertain     = stats.get("uncertain", 0)

    users       = get_all_users()
    admin_count = sum(1 for u in users if u["role"] == "admin") if users else 0

    # ── Overview metrics ──────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    _stat_card(c1, total_users,   "Registered Users",      "#6c63ff")
    _stat_card(c2, total_classif, "Total Classifications", "#4a90d9")
    _stat_card(c3, recent_7days,  "Last 7 Days",           "#52b788")
    _stat_card(c4, admin_count,   "Admin Accounts",        "#f4a261")

    st.divider()

    # ── Label distribution ────────────────────────────────────────────
    st.markdown("<h4>🔍 Classification Breakdown</h4>", unsafe_allow_html=True)
    col_r, col_f, col_u = st.columns(3)
    _stat_card(col_r, real_count, "REAL",      "#52b788")
    _stat_card(col_f, fake_count, "FAKE",      "#e63946")
    _stat_card(col_u, uncertain,  "UNCERTAIN", "#f4a261")

    st.divider()

    # ── Live Monitoring ───────────────────────────────────────────────
    st.markdown("<h4>⚡ Live Fake News Detection Monitoring</h4>", unsafe_allow_html=True)
    chart_data = pd.DataFrame({
        "Label": ["REAL", "FAKE", "UNCERTAIN"],
        "Count": [real_count, fake_count, uncertain],
    })
    st.bar_chart(chart_data.set_index("Label"))
    st.caption("Live distribution of predictions across the platform.")

    # ── User Management ───────────────────────────────────────────────
    st.divider()
    st.markdown("<h4>👩‍🦲 User Management</h4>", unsafe_allow_html=True)

    if not users:
        st.info("No users yet.")
    else:
        users_df = pd.DataFrame(
            [dict(u) for u in users],
            columns=["id", "username", "email", "role", "created_at"],
        )
        users_df.insert(0, "#", range(1, len(users_df) + 1))
        st.dataframe(users_df.drop(columns=["id"]), use_container_width=True, hide_index=True)

        st.markdown("<h4>⚙️ Manage a user</h4>", unsafe_allow_html=True)
        user_options  = {u["username"]: u["id"] for u in users}
        selected_name = st.selectbox("Select user", list(user_options.keys()))
        selected_id   = user_options[selected_name]
        selected_user = next((u for u in users if u["id"] == selected_id), None)

        action_col, role_col = st.columns(2)

        with role_col:
            new_role = st.selectbox(
                "Change role",
                ["user", "admin"],
                index=0 if selected_user and selected_user["role"] == "user" else 1,
                key="admin_role_sel",
            )
            if st.button("Update Role", use_container_width=True):
                update_user_role(selected_id, new_role)
                st.success(f"Role updated to '{new_role}' for {selected_name}.")
                st.rerun()

        with action_col:
            st.markdown("<br>", unsafe_allow_html=True)
            me = st.session_state.get("current_user", {})

            if "pending_delete_id" not in st.session_state:
                st.session_state.pending_delete_id = None
            if st.session_state.pending_delete_id != selected_id:
                st.session_state.pending_delete_id = None

            if st.session_state.pending_delete_id == selected_id:
                st.warning(f"Delete **{selected_name}**? This cannot be undone.")
                confirm_col, cancel_col = st.columns(2)
                with confirm_col:
                    if st.button("✅ Yes, delete", use_container_width=True, type="primary"):
                        if selected_id == me.get("id"):
                            st.error("You cannot delete your own account.")
                        else:
                            delete_user(selected_id)
                            st.session_state.pending_delete_id = None
                            st.success(f"User '{selected_name}' deleted.")
                            st.rerun()
                with cancel_col:
                    if st.button("✖ Cancel", use_container_width=True):
                        st.session_state.pending_delete_id = None
                        st.rerun()
            else:
                if st.button(f"🗑️ Delete {selected_name}", use_container_width=True):
                    if selected_id == me.get("id"):
                        st.error("You cannot delete your own account.")
                    else:
                        st.session_state.pending_delete_id = selected_id
                        st.rerun()

        st.markdown("---")
        st.markdown("<h4>🔑 Reset Password</h4>", unsafe_allow_html=True)
        st.markdown(
            f"<p style='font-size:0.88rem;color:#666;margin-top:-0.4rem;'>"
            f"Set a new password for <b>{selected_name}</b>. "
            f"Share it with them securely after resetting.</p>",
            unsafe_allow_html=True,
        )
        pw_col1, pw_col2 = st.columns(2)
        with pw_col1:
            new_pw = st.text_input(
                "New password", type="password",
                key="admin_new_pw", placeholder="Min. 6 characters",
            )
        with pw_col2:
            confirm_pw = st.text_input(
                "Confirm new password", type="password",
                key="admin_confirm_pw", placeholder="Repeat password",
            )
        if st.button("🔒 Reset Password", key="admin_reset_pw_btn"):
            if not new_pw or not confirm_pw:
                st.error("Please fill in both password fields.")
            elif len(new_pw) < 6:
                st.error("Password must be at least 6 characters.")
            elif new_pw != confirm_pw:
                st.error("Passwords do not match.")
            else:
                ok = update_user_password(selected_id, new_pw)
                if ok:
                    st.success(f"✅ Password for **{selected_name}** has been reset successfully.")
                else:
                    st.error("Something went wrong. Please try again.")

    st.divider()

    # ── Support Inbox — WhatsApp style ────────────────────────────────
    _show_inbox()

    st.divider()

    # ── Global History ────────────────────────────────────────────────
    st.markdown("<h4>👁‍🗨 Classifications History (all users)</h4>", unsafe_allow_html=True)
    all_history = get_all_history(limit=200)

    if not all_history:
        st.info("No classifications yet.")
    else:
        hist_df = pd.DataFrame(
            [dict(h) for h in all_history],
            columns=["id","user_id","input_text","label","real_prob",
                     "fake_prob","word_count","classified_at","deleted_by_user","username"],
        )
        hist_df["input_text"] = hist_df["input_text"].str[:80] + "…"
        hist_df["real_prob"]  = hist_df["real_prob"].round(3)
        hist_df["fake_prob"]  = hist_df["fake_prob"].round(3)
        # Human-readable cleared indicator
        hist_df["visibility"] = hist_df["deleted_by_user"].apply(
            lambda x: "🗑 Cleared by user" if x == 1 else "✅ Visible to user"
        )

        # Summary callout
        n_cleared = int(hist_df["deleted_by_user"].sum())
        if n_cleared:
            st.markdown(
                f'<div style="background:#fff8e1;border:1px solid #ffe082;border-radius:8px;'
                f'padding:0.6rem 1rem;font-size:0.88rem;color:#7a5c00;margin-bottom:0.6rem;">'
                f'⚠️ <b>{n_cleared}</b> record(s) were cleared by users but are retained here '
                f'for audit purposes.</div>',
                unsafe_allow_html=True,
            )

        st.dataframe(
            hist_df[["username","label","real_prob","fake_prob",
                     "word_count","classified_at","visibility","input_text"]],
            use_container_width=True,
            hide_index=True,
        )


# ─────────────────────────────────────────────
# WHATSAPP-STYLE INBOX
# ─────────────────────────────────────────────
def _show_inbox():
    st.markdown(_INBOX_CSS, unsafe_allow_html=True)

    open_count   = get_open_message_count()
    badge_html   = (
        f" &nbsp;<span style='background:#e63946;color:white;border-radius:12px;"
        f"padding:2px 9px;font-size:0.78rem;'>{open_count} open</span>"
        if open_count > 0 else ""
    )
    st.markdown(f"<h4>💬 Support Inbox{badge_html}</h4>", unsafe_allow_html=True)

    all_messages = get_all_messages()
    if not all_messages:
        st.info("No messages from users yet.")
        return

    # Session state for selected user
    if "admin_inbox_uid" not in st.session_state:
        st.session_state.admin_inbox_uid = None
    if "admin_reply_mid" not in st.session_state:
        st.session_state.admin_reply_mid = None   # which message thread is reply box open for

    # Group messages by user
    from collections import defaultdict
    users_map   = {}   # uid -> {"username": ..., "messages": [...], "open": n}
    for msg in all_messages:
        m = dict(msg)
        uid = m["user_id"]
        if uid not in users_map:
            users_map[uid] = {"username": m["username"], "messages": [], "open": 0}
        users_map[uid]["messages"].append(m)
        if m["status"] == "open":
            users_map[uid]["open"] += 1

    left, right = st.columns([1, 2.4], gap="small")

    # ── LEFT — user list ─────────────────────────────────────────────
    with left:
        st.markdown(
            '<p style="font-family:Syne,sans-serif;font-weight:700;font-size:0.8rem;'
            'color:#4a4a7a;text-transform:uppercase;letter-spacing:1.2px;margin-bottom:0.6rem;">'
            'Users</p>',
            unsafe_allow_html=True,
        )

        for uid, data in users_map.items():
            is_active  = st.session_state.admin_inbox_uid == uid
            bg         = "rgba(48,43,99,0.1)" if is_active else "#fff"
            border     = "#9b97cc"            if is_active else "#e2e5ec"
            n_msgs     = len(data["messages"])
            n_open     = data["open"]
            open_badge = (
                f'<span style="background:#e63946;color:white;border-radius:10px;'
                f'padding:1px 7px;font-size:0.68rem;margin-left:5px;">{n_open}</span>'
                if n_open > 0 else ""
            )
            last_msg = data["messages"][0]["created_at"][:16]   # already ordered DESC

            st.markdown(
                f"""<div style="border:1px solid {border};border-radius:10px;
                    padding:9px 11px;background:{bg};margin-bottom:4px;">
                    <div style="font-weight:700;font-size:0.88rem;color:#1d1d3b;">
                        👤 {data['username']}{open_badge}
                    </div>
                    <div style="font-size:0.72rem;color:#aaa;margin-top:3px;">
                        {n_msgs} message{'s' if n_msgs != 1 else ''} &nbsp;·&nbsp; {last_msg}
                    </div>
                </div>""",
                unsafe_allow_html=True,
            )
            if st.button("Open chat →", key=f"inbox_user_{uid}", use_container_width=True):
                st.session_state.admin_inbox_uid = uid
                st.session_state.admin_reply_mid = None
                st.rerun()

    # ── RIGHT — conversation view ────────────────────────────────────
    with right:
        uid = st.session_state.admin_inbox_uid

        if uid is None or uid not in users_map:
            st.markdown(
                """<div style="display:flex;flex-direction:column;align-items:center;
                    justify-content:center;min-height:400px;background:#f8f9fb;
                    border-radius:12px;border:1.5px dashed #e2e5ec;">
                    <div style="font-size:3rem;">💬</div>
                    <div style="font-family:Syne,sans-serif;font-weight:700;color:#4a4a7a;
                                margin-top:0.5rem;font-size:1.05rem;">Support Inbox</div>
                    <div style="font-size:0.85rem;color:#aaa;margin-top:0.3rem;">
                        Select a user on the left to view their messages.</div>
                </div>""",
                unsafe_allow_html=True,
            )
            return

        data     = users_map[uid]
        username = data["username"]
        msgs     = data["messages"]   # ordered newest first from DB; reverse for chat order
        msgs_asc = list(reversed(msgs))

        # Header bar
        n_open = data["open"]
        open_txt = f"{n_open} open" if n_open else "all resolved"
        st.markdown(
            f'<div style="background:linear-gradient(135deg,#302b63,#24243e);'
            f'border-radius:12px 12px 0 0;padding:0.8rem 1.1rem;'
            f'display:flex;justify-content:space-between;align-items:center;">'
            f'<span style="font-family:Syne,sans-serif;font-weight:700;font-size:1rem;color:white;">'
            f'👤 {username}</span>'
            f'<span style="font-size:0.72rem;background:rgba(255,255,255,0.15);'
            f'border-radius:20px;padding:3px 11px;color:white;">{open_txt}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # ── Build bubble HTML ─────────────────────────────────────────
        html = '<div class="wa-bg-admin">'
        for m in msgs_asc:
            m_id    = m["id"]
            replies = [dict(r) for r in get_replies_for_message(m_id)]

            # Thread subject divider
            html += (
                f'<div class="wa-divider">── {m["subject"]} '
                f'· {m["created_at"][:16]} ──</div>'
            )

            # User message — left
            html += (
                f'<div class="wa-row-left"><div style="max-width:80%">'
                f'<div class="wa-bubble-user">{m["body"]}</div>'
                f'<div class="wa-ts wa-ts-left">'
                f'{username} &nbsp;·&nbsp; {m["created_at"][:16]}</div>'
                f'</div></div>'
            )

            # Replies — right
            for r in replies:
                html += (
                    f'<div class="wa-row-right"><div style="max-width:80%">'
                    f'<div class="wa-bubble-admin">{r["body"]}</div>'
                    f'<div class="wa-ts">🛡️ <b>{r["admin_name"]}</b>'
                    f' &nbsp;·&nbsp; {r["created_at"][:16]}</div>'
                    f'</div></div>'
                )

        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)

        # ── Action buttons per thread ─────────────────────────────────
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        for m in msgs_asc:
            m_id           = m["id"]
            reply_key      = f"admin_reply_open_{m_id}"
            is_reply_open  = st.session_state.admin_reply_mid == m_id
            status_label   = "✅ Resolved" if m["status"] == "resolved" else "🕐 Open"

            with st.expander(f'📩 **{m["subject"]}** — {status_label}', expanded=False):
                col_reply, col_status, col_del = st.columns([2, 2, 1])

                with col_reply:
                    toggle_label = "✖ Close Reply" if is_reply_open else "💬 Reply"
                    if st.button(toggle_label, key=f"toggle_reply_{m_id}", use_container_width=True):
                        st.session_state.admin_reply_mid = m_id if not is_reply_open else None
                        st.rerun()

                with col_status:
                    if m["status"] == "open":
                        if st.button("✅ Mark Resolved", key=f"resolve_{m_id}", use_container_width=True):
                            update_message_status(m_id, "resolved")
                            st.success("Marked as resolved.")
                            st.rerun()
                    else:
                        if st.button("🔄 Reopen", key=f"reopen_{m_id}", use_container_width=True):
                            update_message_status(m_id, "open")
                            st.info("Message reopened.")
                            st.rerun()

                with col_del:
                    if st.button("🗑️", key=f"del_msg_{m_id}", use_container_width=True):
                        delete_message(m_id)
                        st.success("Deleted.")
                        st.rerun()

                # Reply text box
                if is_reply_open:
                    reply_text = st.text_area(
                        "Your reply",
                        placeholder="Type your reply here…",
                        height=110,
                        key=f"reply_text_{m_id}",
                    )
                    if st.button("📨 Send Reply", key=f"send_reply_{m_id}"):
                        if not reply_text.strip():
                            st.error("Reply cannot be empty.")
                        else:
                            admin = st.session_state.get("current_user", {})
                            ok = create_reply(m_id, admin["id"], reply_text)
                            if ok:
                                update_message_status(m_id, "resolved")
                                st.session_state.admin_reply_mid = None
                                st.success("Reply sent and message marked as resolved.")
                                st.rerun()
                            else:
                                st.error("Failed to send reply.")


# ─────────────────────────────────────────────
# HELPER — stat card
# ─────────────────────────────────────────────
def _stat_card(col, value, label, color):
    with col:
        st.markdown(
            f"""<div class="stat-box" style="display:flex;flex-direction:column;align-items:center;padding:1.2rem 1rem;">
                <div style="
                    width:72px;height:72px;border-radius:50%;
                    border:3px solid {color};background:transparent;
                    display:flex;align-items:center;justify-content:center;
                    margin-bottom:0.6rem;
                ">
                    <span style="
                        font-family:'Syne',sans-serif;font-size:1.6rem;
                        font-weight:800;color:{color};line-height:1;
                    ">{value}</span>
                </div>
                <div class="stat-label">{label}</div>
            </div>""",
            unsafe_allow_html=True,
        )