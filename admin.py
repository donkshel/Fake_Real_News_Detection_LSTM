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


# ══════════════════════════════════════════════════════════════════════════════
#  CSS  
# ══════════════════════════════════════════════════════════════════════════════
_ADMIN_CSS = """
<style>
/* ── Palette tokens ───────────────────────────────────────────────────────── */
:root {
    --blue:    #4a90d9;
    --purple:  #6c63ff;
    --green:   #27ae60;
    --red:     #e63946;
    --orange:  #f4a261;
    --ink:     #1d1d3b;
    --muted:   #7a7a9a;
    --border:  #eaeaf4;
    --surface: #ffffff;
    --page-bg: #f6f7fb;
}


/* ── Section header ───────────────────────────────────────────────────────── */
.sec-header {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin: 0.4rem 0 1rem 0;
}
.sec-header-icon {
    width: 34px; height: 34px;
    border-radius: 9px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1rem;
    flex-shrink: 0;
}
.sec-header-text h4 {
    font-family: 'Syne', sans-serif;
    font-weight: 700;
    font-size: 1.05rem;
    color: var(--ink);
    margin: 0;
    line-height: 1.2;
}
.sec-header-text p {
    font-size: 0.74rem;
    color: var(--muted);
    margin: 0.1rem 0 0 0;
}
.sec-divider {
    height: 1px;
    background: linear-gradient(to right, var(--border), transparent);
    margin: 1.6rem 0;
}

/* ── Metric overview card ─────────────────────────────────────────────────── */
.mc {
    background: var(--surface);
    border-radius: 16px;
    padding: 1.4rem 1.3rem 1.2rem;
    border: 1px solid var(--border);
    border-left: 5px solid var(--mc-accent);
    box-shadow: 0 2px 10px rgba(0,0,0,0.045);
    transition: transform 0.3s ease, box-shadow 0.3s ease;
    cursor: default;
    position: relative;
    overflow: hidden;
}
.mc::before {
    content: '';
    position: absolute;
    top: -18px; right: -18px;
    width: 80px; height: 80px;
    border-radius: 50%;
    background: var(--mc-accent);
    opacity: 0.06;
}
.mc:hover {
    transform: translateY(-5px);
    box-shadow: 0 12px 30px rgba(0,0,0,0.10);
}
.mc-icon-wrap {
    width: 40px; height: 40px;
    border-radius: 11px;
    background: var(--mc-accent);
    opacity: 0.13;
    display: flex; align-items: center; justify-content: center;
    margin-bottom: 0.9rem;
    /* icon is overlaid via the emoji span */
}
.mc-icon-box {
    position: relative;
    width: 40px; height: 40px;
    margin-bottom: 0.9rem;
}
.mc-icon-bg {
    position: absolute; inset: 0;
    border-radius: 11px;
    background: var(--mc-accent);
    opacity: 0.13;
}
.mc-icon-emoji {
    position: absolute; inset: 0;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.15rem;
    line-height: 1;
}
.mc-value {
    font-family: 'Syne', sans-serif;
    font-size: 2.2rem;
    font-weight: 700;
    text-align: center;
    color: var(--mc-accent);
    line-height: 1;
    margin-bottom: 0.3rem;
}
.mc-label {
    font-size: 0.7rem;
    font-weight: 600;
    text-align: center;
    text-transform: uppercase;
    letter-spacing: 1.1px;
    color: var(--muted);
}
.mc-trend {
    margin-top: 0.75rem;
    padding-top: 0.7rem;
    border-top: 1px solid var(--border);
    display: flex; align-items: center; gap: 0.4rem;
}
.mc-trend-up   { color: #27ae60; font-size: 0.72rem; font-weight: 700; }
.mc-trend-down { color: #e63946; font-size: 0.72rem; font-weight: 700; }
.mc-trend-neu  { color: var(--muted); font-size: 0.72rem; font-weight: 700; }
.mc-trend-desc { font-size: 0.68rem; color: #b0b0c8; }

/* ── Breakdown card ───────────────────────────────────────────────────────── */
.bd {
    background: var(--surface);
    border-radius: 16px;
    padding: 1.3rem 1.3rem 1.15rem;
    border: 1px solid var(--border);
    border-top: 5px solid var(--bd-accent);
    box-shadow: 0 2px 10px rgba(0,0,0,0.045);
    transition: transform 0.3s ease, box-shadow 0.3s ease;
    cursor: default;
}
.bd:hover {
    transform: translateY(-5px);
    box-shadow: 0 12px 30px rgba(0,0,0,0.10);
}
.bd-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.7rem;
}
.bd-pill {
    font-size: 0.65rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color: var(--bd-accent);
    background: color-mix(in srgb, var(--bd-accent) 12%, white);
    border: 1px solid color-mix(in srgb, var(--bd-accent) 22%, white);
    border-radius: 20px;
    padding: 3px 10px;
}
.bd-emoji { font-size: 1.25rem; }
.bd-count {
    font-family: 'Syne', sans-serif;
    font-size: 2.1rem;
    font-weight: 700;
    text-align: center;
    color: var(--bd-accent);
    line-height: 1;
    margin-bottom: 0.25rem;
}
.bd-sub {
    font-size: 0.7rem;
    color: var(--muted);
    margin-bottom: 0.75rem;
    text-align: center;
    text-transform: uppercase;
    font-weight: 500;
}
.bd-bar-label {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 0.3rem;
}
.bd-bar-name { font-size: 0.7rem; color: var(--muted); font-weight: 600; text-transform: uppercase; letter-spacing: 0.8px; }
.bd-bar-pct  { font-size: 0.78rem; color: var(--bd-accent); font-weight: 700; }
.bd-bar-bg {
    background: #f0f0f7;
    border-radius: 99px;
    height: 7px;
    width: 100%;
    overflow: hidden;
}
.bd-bar-fill {
    height: 100%;
    border-radius: 99px;
    background: linear-gradient(90deg, var(--bd-accent), color-mix(in srgb, var(--bd-accent) 70%, white));
    transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

/* ── Live monitoring container ────────────────────────────────────────────── */
.monitor-wrap {
    background: var(--surface);
    border-radius: 16px;
    padding: 1.4rem 1.4rem 0.5rem;
    border: 1px solid var(--border);
    box-shadow: 0 2px 10px rgba(0,0,0,0.045);
}
.monitor-legend {
    display: flex;
    gap: 1.4rem;
    margin-bottom: 1rem;
    flex-wrap: wrap;
}
.legend-dot {
    width: 9px; height: 9px;
    border-radius: 50%;
    display: inline-block;
    margin-right: 5px;
    vertical-align: middle;
}

/* ── Section pills for user mgmt / history ────────────────────────────────── */
.section-card {
    background: var(--surface);
    border-radius: 16px;
    padding: 1.4rem;
    border: 1px solid var(--border);
    box-shadow: 0 2px 10px rgba(0,0,0,0.035);
    margin-bottom: 0.6rem;
}

/* ── WhatsApp inbox bubbles ) ───────────────────────────────────── */
.wa-bg-admin {
    background: #ece5dd;
    border-radius: 0;
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
    max-width: 100%;
    font-size: 0.9rem;
    line-height: 1.6;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    white-space: pre-wrap;
    word-wrap: break-word;
}
.wa-ts       { font-size: 0.68rem; color: #aaa; margin-top: 3px; padding: 0 3px; }
.wa-ts-left  { text-align: left; }
.wa-divider  {
    text-align: center;
    font-size: 0.72rem;
    color: #bbb;
    padding: 4px 0;
    font-style: italic;
}
</style>
"""

# ══════════════════════════════════════════════════════════════════════════════
#  ADMIN DASHBOARD  —  main entry point
# ══════════════════════════════════════════════════════════════════════════════
def show_admin_page():
    # Inject CSS once
    st.markdown(_ADMIN_CSS, unsafe_allow_html=True)

    # ── Data ──────────────────────────────────────────────────────────────────
    stats         = get_admin_stats()
    total_users   = stats.get("total_users",   0)
    total_classif = stats.get("total_classif", 0)
    recent_7days  = stats.get("recent_7days",  0)
    real_count    = stats.get("real_count",    0)
    fake_count    = stats.get("fake_count",    0)
    uncertain     = stats.get("uncertain",     0)

    users       = get_all_users()
    admin_count = sum(1 for u in users if u["role"] == "admin") if users else 0

    # Derived helpers
    total_safe     = max(total_classif, 1)
    daily_avg      = max(round(recent_7days / 7), 0)   # rough daily rate from 7-day window

     # ── Hero header ───────────
    import streamlit.components.v1 as components
    components.html("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&display=swap');
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: transparent; }
        .dash-hero {
            background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
            border-radius: 18px;
            padding: 1.5rem 2rem;
            display: flex;
            height: 70px;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            font-family: 'DM Sans', sans-serif;
        }
        .left { display: flex; align-items: center; gap: 1rem; }
        .shield { font-size: 2.6rem; filter: drop-shadow(0 0 12px rgba(108,99,255,0.6)); }
        .title {
            font-family: 'Syne', sans-serif;
            font-size: 1.7rem; font-weight: 700;
            text-transform: uppercase;
            color: #fff; line-height: 1.1;
        }
        .sub {
            font-size: 0.8rem; color: rgba(255,255,255,0.55);
            margin-top: 0.25rem; letter-spacing: 0.5px;
        }
        .badge {
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 30px;
            padding: 0.45rem 1.1rem;
            font-size: 0.75rem;
            color: rgba(255,255,255,0.85);
            font-weight: 600;
            letter-spacing: 0.5px;
            white-space: nowrap;
        }
        /* ═══════════════════════════════════════
           MOBILE HERO FIX
           ═══════════════════════════════════════ */
        @media (max-width: 768px) {

            .dash-hero {
                flex-direction: column !important;
                align-items: flex-start !important;
                height: auto !important;
                padding: 1rem 1.2rem !important;
                gap: 6px !important;
            }

            /* Top row: icon + title */
            .left {
                width: 100% !important;
                display: flex !important;
                align-items: center !important;
                gap: 0.6rem !important;
            }

            /* Remove subtitle on mobile to keep ONE clean line */
            .sub {
                display: none !important;
            }

            /* Force title to stay in one line */
            .title {
                font-size: 1.1rem !important;
                white-space: nowrap !important;
                overflow: hidden !important;
                text-overflow: ellipsis !important;
            }

            /* Slightly reduce icon */
            .shield {
                font-size: 2rem !important;
            }

            /* Time goes below and right */
            .badge {
                align-self: flex-end !important;
                font-size: 0.7rem !important;
                padding: 0.35rem 0.8rem !important;
                margin-top: 2px !important;
            }
        }
        </style>
        <div class="dash-hero">
            <div class="left">
                <span class="shield">🛡️</span>
                <div>
                    <div class="title">Admin Dashboard</div>
                    <div class="sub">Fake News Detection System · Control Panel</div>
                </div>
            </div>
            <div class="badge" id="clk">🕐 --:--:--</div>
        </div>
        <script>
        function pad(n) { return String(n).padStart(2, '0'); }
        function tick() {
            var now  = new Date();
            var eat  = new Date(now.toLocaleString('en-US', { timeZone: 'Africa/Nairobi' }));
            var mon  = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
            var str  = eat.getDate() + ' ' + mon[eat.getMonth()] + ' ' + eat.getFullYear()
                     + ' · ' + pad(eat.getHours()) + ':' + pad(eat.getMinutes()) + ':' + pad(eat.getSeconds());
            document.getElementById('clk').textContent = '🕐 ' + str;
        }
        tick();
        setInterval(tick, 1000);
        </script>
    """, height=100, scrolling=False)

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 1 — Overview metrics
    # ─────────────────────────────────────────────────────────────────────────
    _section_header("📊", "#4a90d9", "Platform Overview", "Live snapshot of system activity")

    c1, c2, c3, c4 = st.columns(4, gap="small")
    _metric_card(c1,
        icon="👥", value=total_users, label="Registered Users",
        color="#6c63ff",
        trend_value=f"+{admin_count} admin{'s' if admin_count != 1 else ''}",
        trend_dir="neu",  trend_desc="role breakdown",
    )
    _metric_card(c2,
        icon="📋", value=total_classif, label="Total Classifications",
        color="#4a90d9",
        trend_value=f"+{recent_7days}",
        trend_dir="up",   trend_desc="last 7 days",
    )
    _metric_card(c3,
        icon="⚡", value=recent_7days, label="Last 7 Days",
        color="#27ae60",
        trend_value=f"~{daily_avg}/day",
        trend_dir="up",   trend_desc="daily average",
    )
    _metric_card(c4,
        icon="🛡️", value=admin_count, label="Admin Accounts",
        color="#f4a261",
        trend_value=f"{total_users - admin_count} regular",
        trend_dir="neu",  trend_desc="non-admin users",
    )

    st.markdown('<div class="sec-divider"></div>', unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 2 — Classification Breakdown
    # ─────────────────────────────────────────────────────────────────────────
    _section_header("🔍", "#6c63ff", "Classification Breakdown",
                    f"Distribution across {total_classif} total predictions")

    col_r, col_f, col_u = st.columns(3, gap="small")
    _breakdown_card(col_r,
        value=real_count, label="REAL", color="#27ae60",
        emoji="✅", total=total_safe,
        sub="Verified credible articles",
    )
    _breakdown_card(col_f,
        value=fake_count, label="FAKE", color="#e63946",
        emoji="🚨", total=total_safe,
        sub="Flagged misinformation",
    )
    _breakdown_card(col_u,
        value=uncertain, label="UNCERTAIN", color="#f4a261",
        emoji="❓", total=total_safe,
        sub="Low-confidence results",
    )

    st.markdown('<div class="sec-divider"></div>', unsafe_allow_html=True)

        # ─────────────────────────────────────────────────────────────────────────
    # SECTION 3 — Live Monitoring
    # ─────────────────────────────────────────────────────────────────────────
    _section_header("⚡", "#f4a261", "Live Detection Monitoring",
                    "Real-time distribution of predictions across the platform")
 
    import plotly.graph_objects as go
    fig_monitor = go.Figure(data=[
        go.Bar(
            x=["REAL", "FAKE", "UNCERTAIN"],
            y=[real_count, fake_count, uncertain],
            marker_color=["#27ae60", "#e63946", "#f4a261"],
            marker_line_width=0,
            text=[real_count, fake_count, uncertain],
            textposition="outside",
            textfont=dict(family="Syne, sans-serif", size=14, color=["#27ae60", "#e63946", "#f4a261"]),
            hovertemplate="<b>%{x}</b><br>Count: %{y}<extra></extra>",
        )
    ])
    fig_monitor.update_layout(
        paper_bgcolor="white",
        plot_bgcolor="#f8f9fb",
        height=320,
        margin=dict(l=20, r=20, t=20, b=40),
        xaxis=dict(
            tickfont=dict(family="Syne, sans-serif", size=13, color="#1d1d3b"),
            showgrid=False,
            linecolor="#eaeaf4",
        ),
        yaxis=dict(
            tickfont=dict(size=11, color="#aaa"),
            gridcolor="#eaeaf4",
            showline=False,
        ),
        showlegend=False,
    )
    st.plotly_chart(fig_monitor, use_container_width=True)
    st.caption("Chart auto-refreshes on page reload. Data reflects all-time totals.")
 
    st.markdown('<div class="sec-divider"></div>', unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 4 — User Management
    # ─────────────────────────────────────────────────────────────────────────
    _section_header("👥", "#4a90d9", "User Management", "View, edit roles, and manage accounts")

    if not users:
        st.info("No users registered yet.")
    else:
        users_df = pd.DataFrame(
            [dict(u) for u in users],
            columns=["id", "username", "email", "role", "created_at"],
        )
        users_df.insert(0, "#", range(1, len(users_df) + 1))
        st.dataframe(users_df.drop(columns=["id"]), use_container_width=True, hide_index=True)

        st.markdown("<br>", unsafe_allow_html=True)
        _section_header("⚙️", "#6c63ff", "Manage a User", "Update roles or remove accounts")

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
        _section_header("🔑", "#f4a261", "Reset Password",
                        f"Set a new password for {selected_name} — share securely after resetting.")
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

    st.markdown('<div class="sec-divider"></div>', unsafe_allow_html=True)

    # ── Support Inbox ─────────────────────────────────────────────────────────
    _show_inbox()

    st.markdown('<div class="sec-divider"></div>', unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 5 — Classification History
    # ─────────────────────────────────────────────────────────────────────────
    _section_header("👁", "#27ae60", "Classifications History",
                    "Full audit log of all user predictions (last 200 records)")

    all_history = get_all_history(limit=200)

    if not all_history:
        st.info("No classifications yet.")
    else:
        hist_df = pd.DataFrame(
            [dict(h) for h in all_history],
            columns=["id", "user_id", "input_text", "label", "real_prob",
                     "fake_prob", "word_count", "classified_at", "deleted_by_user", "username"],
        )
        hist_df["input_text"] = hist_df["input_text"].str[:80] + "…"
        hist_df["real_prob"]  = hist_df["real_prob"].round(3)
        hist_df["fake_prob"]  = hist_df["fake_prob"].round(3)
        hist_df["visibility"] = hist_df["deleted_by_user"].apply(
            lambda x: "🗑 Cleared by user" if x == 1 else "✅ Visible to user"
        )

        n_cleared = int(hist_df["deleted_by_user"].sum())
        if n_cleared:
            st.markdown(
                f'<div style="background:#fff8e1;border:1px solid #ffe082;border-radius:10px;'
                f'padding:0.65rem 1rem;font-size:0.85rem;color:#7a5c00;margin-bottom:0.8rem;">'
                f'⚠️ &nbsp;<b>{n_cleared}</b> record(s) cleared by users are retained here for audit purposes.</div>',
                unsafe_allow_html=True,
            )

        st.dataframe(
            hist_df[["username", "label", "real_prob", "fake_prob",
                     "word_count", "classified_at", "visibility", "input_text"]],
            use_container_width=True,
            hide_index=True,
        )


# ══════════════════════════════════════════════════════════════════════════════
#  SUPPORT INBOX  (WhatsApp-style, logic unchanged)
# ══════════════════════════════════════════════════════════════════════════════
def _show_inbox():
    open_count = get_open_message_count()
    badge_html = (
        f"&nbsp;<span style='background:#e63946;color:white;border-radius:12px;"
        f"padding:2px 9px;font-size:0.78rem;'>{open_count} open</span>"
        if open_count > 0 else ""
    )
    _section_header("💬", "#302b63", f"Support Inbox",
                    "User messages and admin replies")
    if open_count > 0:
        st.markdown(
            f'<div style="margin-top:-0.6rem;margin-bottom:0.8rem;">'
            f'<span style="background:#e63946;color:white;border-radius:12px;'
            f'padding:3px 11px;font-size:0.78rem;font-weight:700;">'
            f'● {open_count} unresolved thread{"s" if open_count != 1 else ""}</span></div>',
            unsafe_allow_html=True,
        )

    all_messages = get_all_messages()
    if not all_messages:
        st.info("No messages from users yet.")
        return

    if "admin_inbox_uid" not in st.session_state:
        st.session_state.admin_inbox_uid = None
    if "admin_reply_mid" not in st.session_state:
        st.session_state.admin_reply_mid = None

    from collections import defaultdict
    users_map = {}
    for msg in all_messages:
        m   = dict(msg)
        uid = m["user_id"]
        if uid not in users_map:
            users_map[uid] = {"username": m["username"], "messages": [], "open": 0}
        users_map[uid]["messages"].append(m)
        if m["status"] == "open":
            users_map[uid]["open"] += 1

    left, right = st.columns([1, 2.4], gap="small")

    # ── LEFT — user list ──────────────────────────────────────────────────────
    with left:
        st.markdown(
            '<p style="font-family:Syne,sans-serif;font-weight:700;font-size:0.75rem;'
            'color:#4a4a7a;text-transform:uppercase;letter-spacing:1.3px;margin-bottom:0.6rem;">'
            'Conversations</p>',
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
            last_msg = data["messages"][0]["created_at"][:16]
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

    # ── RIGHT — conversation view ─────────────────────────────────────────────
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
                        Select a conversation on the left.</div>
                </div>""",
                unsafe_allow_html=True,
            )
            return

        data     = users_map[uid]
        username = data["username"]
        msgs     = data["messages"]
        msgs_asc = list(reversed(msgs))

        n_open   = data["open"]
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

        html = '<div class="wa-bg-admin">'
        for m in msgs_asc:
            m_id    = m["id"]
            replies = [dict(r) for r in get_replies_for_message(m_id)]
            html += (
                f'<div class="wa-divider">── {m["subject"]} '
                f'· {m["created_at"][:16]} ──</div>'
            )
            html += (
                f'<div class="wa-row-left"><div style="max-width:80%">'
                f'<div class="wa-bubble-user">{m["body"]}</div>'
                f'<div class="wa-ts wa-ts-left">'
                f'{username} &nbsp;·&nbsp; {m["created_at"][:16]}</div>'
                f'</div></div>'
            )
            for r in replies:
                html += (
                    f'<div class="wa-row-right"><div style="max-width:100%">'
                    f'<div class="wa-bubble-admin">{r["body"]}</div>'
                    f'<div class="wa-ts">🛡️ <b>{r["admin_name"]}</b>'
                    f' &nbsp;·&nbsp; {r["created_at"][:16]}</div>'
                    f'</div></div>'
                )
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)

        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        for m in msgs_asc:
            m_id          = m["id"]
            is_reply_open = st.session_state.admin_reply_mid == m_id
            status_label  = "✅ Resolved" if m["status"] == "resolved" else "🕐 Open"

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


# ══════════════════════════════════════════════════════════════════════════════
#  REUSABLE UI COMPONENTS
# ══════════════════════════════════════════════════════════════════════════════

def _section_header(icon: str, icon_bg: str, title: str, subtitle: str = ""):
    """Render a styled section heading with icon pill + title + optional subtitle."""
    sub_html = (
        f'<p style="font-size:0.73rem;color:#7a7a9a;margin:0.1rem 0 0 0;">{subtitle}</p>'
        if subtitle else ""
    )
    st.markdown(
        f"""<div class="sec-header">
            <div class="sec-header-icon"
                 style="background:color-mix(in srgb,{icon_bg} 14%,white);
                        border:1px solid color-mix(in srgb,{icon_bg} 25%,white);">
                {icon}
            </div>
            <div class="sec-header-text">
                <h4>{title}</h4>
                {sub_html}
            </div>
        </div>""",
        unsafe_allow_html=True,
    )


def _metric_card(
    col,
    icon:        str,
    value:       int | float,
    label:       str,
    color:       str,
    trend_value: str = "",
    trend_dir:   str = "neu",   # "up" | "down" | "neu"
    trend_desc:  str = "",
):
    """
    Render a metric overview card with:
      - Tinted icon box
      - Large bold value in accent colour
      - UPPERCASE label
      - Trend row with directional arrow and description
    """
    arrow_map = {"up": "▲", "down": "▼", "neu": "●"}
    class_map = {"up": "mc-trend-up", "down": "mc-trend-down", "neu": "mc-trend-neu"}
    arrow = arrow_map.get(trend_dir, "●")
    cls   = class_map.get(trend_dir, "mc-trend-neu")

    trend_html = ""
    if trend_value:
        trend_html = (
            f'<div class="mc-trend">'
            f'  <span class="{cls}">{arrow} {trend_value}</span>'
            f'  <span class="mc-trend-desc">{trend_desc}</span>'
            f'</div>'
        )

    with col:
        st.markdown(
            f"""<div class="mc" style="--mc-accent:{color};">
                    <div class="mc-icon-box">
                        <div class="mc-icon-bg"></div>
                        <div class="mc-icon-emoji">{icon}</div>
                    </div>
                    <div class="mc-value">{value}</div>
                    <div class="mc-label">{label}</div>
                    {trend_html}
                </div>""",
            unsafe_allow_html=True,
        )


def _breakdown_card(
    col,
    value: int,
    label: str,
    color: str,
    emoji: str,
    total: int,
    sub:   str = "",
):
    """
    Render a classification breakdown card with:
      - Pill label + emoji header
      - Large count
      - Gradient progress bar
      - Percentage caption
    """
    pct = round((value / total) * 100, 1) if total else 0.0
    sub_html = (
        f'<div class="bd-sub">{sub}</div>' if sub else ""
    )
    with col:
        st.markdown(
            f"""<div class="bd" style="--bd-accent:{color};">
                    <div class="bd-top">
                        <span class="bd-pill">{label}</span>
                        <span class="bd-emoji">{emoji}</span>
                    </div>
                    <div class="bd-count">{value}</div>
                    {sub_html}
                    <div class="bd-bar-label">
                        <span class="bd-bar-name">Share of total</span>
                        <span class="bd-bar-pct">{pct}%</span>
                    </div>
                    <div class="bd-bar-bg">
                        <div class="bd-bar-fill" style="width:{pct}%;"></div>
                    </div>
                </div>""",
            unsafe_allow_html=True,
        )
