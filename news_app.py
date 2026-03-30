#import necessary libraries
import streamlit as st
import numpy as np
import pandas as pd
import pickle
import tensorflow as tf
import string
import re
import nltk
import json
import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from nltk.corpus import stopwords
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences

# ----------------------------------------
#  Authentication and database utilities
#-----------------------------------------
from database import init_db, save_classification, get_user_history, clear_user_history, delete_selected_history, get_open_message_count
from authentication import show_auth_page, show_user_sidebar, is_logged_in, current_user, is_admin
from admin import show_admin_page
from chat import show_chat_page

init_db()

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Fake News Detector",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
if "user_text" not in st.session_state:
    st.session_state.user_text = ""
if "file_uploader_key" not in st.session_state:
    st.session_state.file_uploader_key = 0
if "show_admin" not in st.session_state:
    st.session_state.show_admin = False

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:

    if is_logged_in():
        show_user_sidebar()

        u = current_user()

        if is_admin():
            if st.button("⚙️ Admin Panel", use_container_width=True, key="sidebar_admin"):
                st.session_state.show_admin = True
                st.rerun()

        # ── Navigation ───────────────────────
        st.markdown("---")
        st.markdown("""
        <p style="
            font-family:'Syne',sans-serif;
            font-size:0.75rem;font-weight:700;
            color:#9b97cc;letter-spacing:1.5px;
            text-transform:uppercase;margin-bottom:0.4rem;
        ">Navigation</p>
        """, unsafe_allow_html=True)

        # Show unread badge on Support nav item
        open_count   = get_open_message_count() if not is_admin() else 0
        support_label = f"💬  Messages  ({open_count} new)" if open_count > 0 else "💬  Messages"

        selected_page = st.radio(
            label="Navigation",
            options=[
                "🔍  Detect",
                "📊  Model Evaluation",
                "📁  Dataset & Training",
                "🕒  History",
                support_label,
            ],
            label_visibility="collapsed",
        )

    else:
        st.markdown("""
        <div style="
            padding:1rem;border-radius:10px;
            background:rgba(48,43,99,0.2);
            border:1px solid rgba(48,43,99,0.2);
        ">
            <h4>🔐 Welcome!</h4>
            <p style="font-size:0.85rem;">Please sign in to continue.</p>
        </div>
        """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Authentication gate
# ─────────────────────────────────────────────
if not is_logged_in():
    show_auth_page()
    st.stop()

# ─────────────────────────────────────────────
# ADMIN PANEL
# ─────────────────────────────────────────────
if st.session_state.get("show_admin") and is_admin():
    show_admin_page()
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("⬅️ Back to App"):
        st.session_state.show_admin = False
        st.rerun()
    st.stop()

# ─────────────────────────────────────────────
# CSS STYLE
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Sans:wght@400;500&display=swap');

html, body, [data-testid="stAppViewContainer"] { font-family: 'DM Sans', sans-serif; }
#MainMenu, footer, header { visibility: visible; }

/* ── Hero ── */
.hero {
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    border-radius: 18px;
    height: auto;
    padding: 0.2rem 0.6rem;
    margin-bottom: 0.2rem;
    box-shadow: 0 8px 32px rgba(0,0,0,0.35);
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    
}
.hero-left {
    display: flex;
    align-items: center;
    gap: 1rem;
}
.hero-icon {
    font-size: 2.2rem;
    filter: drop-shadow(0 0 12px rgba(108,99,255,0.6));
    flex-shrink: 0;
}
.hero h1 {
    font-family: 'Syne', sans-serif;
    font-size: 1.7rem;
    font-weight: 700;
    color: #fff;
    margin: 0;
    line-height: 1.1;
    letter-spacing: -0.3px;
}
.hero-badge {
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
/* ── Mobile ── */
@media (max-width: 480px) {
    .hero {
        padding: 0.2rem 0.3rem;
        border-radius: 12px;
        gap: 0.75rem;
        display: flex-start;
    }
    .hero h1 {
        font-size: 1rem;
        line-height: 0.8;
    }
    .hero-badge {
        font-size: 0.50rem;
        padding: 0.35rem 0.85rem;
        display: flex-start;
    }
}
/* ── Section labels ── */
.section-label {
    font-family: 'Syne', sans-serif; font-size: 1rem; font-weight: 700;
    color: #4a4a7a; letter-spacing: 1.2px; text-transform: uppercase; margin-bottom: 0.2rem;
}

/* ── Verdict cards ── */
.verdict-real {
    background: linear-gradient(135deg, #1a472a, #2d6a4f); border-left: 5px solid #52b788;
    border-radius: 14px; padding: 1.5rem 1.8rem; color: white;
    box-shadow: 0 4px 20px rgba(82,183,136,0.25);
}
.verdict-fake {
    background: linear-gradient(180deg, #6b1a1a, #9b2226); border-left: 5px solid #e63946;
    border-radius: 14px; padding: 1.5rem 1.8rem; color: white;
    box-shadow: 0 4px 20px rgba(230,57,70,0.25);
}
.verdict-uncertain {
    background: linear-gradient(135deg, #4a3800, #7a5f00); border-left: 5px solid #f4a261;
    border-radius: 14px; padding: 1.5rem 1.8rem; color: white;
    box-shadow: 0 4px 20px rgba(244,162,97,0.25);
}
.verdict-title { font-family: 'Syne', sans-serif; font-size: 1.6rem; font-weight: 500; margin-bottom: 0.3rem; }
.verdict-sub { font-size: 0.95rem; opacity: 0.85; }

/* ── Stat boxes ── */
.stat-box {
    background: #f8f9fb; border-radius: 12px; padding: 1rem 1.2rem;
    text-align: center; border: 1px solid #e2e5ec;
}
.stat-value { font-family: 'Syne', sans-serif; font-size: 1.8rem; font-weight: 500; color: #1d1d3b; }
.stat-label { font-size: 0.78rem; color: #888; text-transform: uppercase; letter-spacing: 0.8px; }

/* ── Score cards ── */
.score-card {
    background: rgba(48,43,99,0.15);
    border-radius: 16px;
    padding: 1.6rem 2rem; color: white; margin-bottom: 1rem;
}
.score-card-title { font-family: 'Syne', sans-serif; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1.5px; color: #9b97cc; margin-bottom: 0.3rem; }
.score-card-value { font-family: 'Syne', sans-serif; font-size: 1.8rem; font-weight: 400; color: #fff; line-height: 1; }
.score-card-sub { font-size: 0.8rem; color: #9b97cc; margin-top: 0.2rem; }
.score-badge-good   { color: #52b788; }
.score-badge-warn   { color: #f4a261; }
.score-badge-danger { color: #e63946; }

/* ── Confusion matrix ── */
.cm-table { width: 100%; border-collapse: collapse; text-align: center; }
.cm-table td { padding: 1rem; font-family: 'Syne', sans-serif; font-size: 1.2rem; font-weight: 500; border-radius: 8px; }
.cm-tp { background: rgba(82,183,136,0.2);  color: #1b7a4e; }
.cm-tn { background: rgba(74,144,217,0.2);  color: #1a5fa0; }
.cm-fp { background: rgba(244,162,97,0.2);  color: #c4620a; }
.cm-fn { background: rgba(230,57,70,0.2);   color: #9b2226; }

/* ── Insight / info boxes ── */
.insight-box {
    background: #f0f3ff; border: 1px solid #c5cfff; border-radius: 10px;
    padding: 0.9rem 1.1rem; font-size: 0.9rem; color: #3a3a7a;
    margin-bottom: 0.7rem; line-height: 1.6;
}
.info-box {
    background: #f0f3ff; border: 1px solid #c5cfff; border-radius: 10px;
    padding: 0.9rem 1.1rem; font-size: 0.9rem; color: #3a3a7a; margin-top: 0.5rem;
}

/* ── Main buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #302b63, #24243e); color: white !important;
    font-family: 'Syne', sans-serif; font-size: 1rem; font-weight: 700;
    padding: 0.7rem 2rem; border-radius: 10px; border: none; width: 100%;
    transition: all 0.25s ease; letter-spacing: 0.5px;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #4a4490, #302b63);
    transform: translateY(-2px); box-shadow: 0 6px 20px rgba(48,43,99,0.35);
}

/* ── Sidebar base ── */
[data-testid="stSidebar"] { padding-top: 10px; }
.user-badge { word-wrap: break-word; overflow-wrap: break-word; }

/* ── Sidebar nav — button style matching user badge, red dot = selection indicator ── */
[data-testid="stSidebar"] .stRadio > div { gap: 5px !important; }

/* Every nav item — same dark card look as the user badge */
[data-testid="stSidebar"] .stRadio > div > label {
    display: flex !important;
    align-items: center !important;
    gap: 0.5rem !important;
    width: 100% !important;
    padding: 0.6rem 1rem !important;
    border-radius: 10px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.88rem !important;
    color: #c9c3f5 !important;
    background: rgba(48,43,99,0.15) !important;
    border: 1px solid rgba(48,43,99,0.25) !important;
    cursor: pointer !important;
    transition: background 0.2s ease, border-color 0.2s ease !important;
    margin-bottom: 2px !important;
}

/* Hover — slightly darker, same as badge hover */
[data-testid="stSidebar"] .stRadio > div > label:hover {
    background: rgba(48,43,99,0.28) !important;
    border-color: rgba(48,43,99,0.45) !important;
    color: #ffffff !important;
}

/* Selected — background stays exactly the same, red dot does the work */
[data-testid="stSidebar"] .stRadio > div > label:has(input:checked) {
    background: rgba(48,43,99,0.15) !important;
    border-color: rgba(48,43,99,0.25) !important;
    color: #c9c3f5 !important;
    box-shadow: none !important;
}

/* ── Tabs (inside Detect page) ── */
.stTabs [data-baseweb="tab-list"] { gap: 8px; background: transparent; }
.stTabs [data-baseweb="tab"] { border-radius: 8px; font-family: 'Syne', sans-serif; font-weight: 700; font-size: 0.88rem; }
div[data-testid="stTabs"] > div:first-child { background: transparent; padding: 0; gap: 10px !important; border: none; margin-bottom: 1rem; }
div[data-testid="stTabs"] > div:first-child button[data-baseweb="tab"] {
    border-radius: 10px !important; padding: 0.55rem 1.6rem !important;
    font-family: 'Syne', sans-serif !important; font-weight: 700 !important;
    font-size: 0.88rem !important; color: #302b63 !important;
    background: #f0f0f8 !important; border: 1.5px solid #c5c0e8 !important;
    transition: all 0.2s ease !important;
}
div[data-testid="stTabs"] > div:first-child button[data-baseweb="tab"]:hover {
    background: #e2e0f5 !important; border-color: #9b97cc !important;
}
div[data-testid="stTabs"] > div:first-child button[data-baseweb="tab"][aria-selected="true"] {
    background: linear-gradient(135deg, #302b63, #24243e) !important;
    color: #ffffff !important; border-color: transparent !important;
    box-shadow: 0 3px 10px rgba(48,43,99,0.35) !important;
}
div[data-testid="stTabs"] [data-baseweb="tab-highlight"],
div[data-testid="stTabs"] [data-baseweb="tab-border"] { display: none !important; }

</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# LOAD RESOURCES
# ─────────────────────────────────────────────
@st.cache_resource
def load_resources():
    if os.path.exists('lstm_model.keras'):
        model = load_model('lstm_model.keras')
    elif os.path.exists('lstm_model.h5'):
        model = load_model('lstm_model.h5')
    else:
        st.error("Model file not found.")
        st.stop()
    with open('tokenizer.pickle', 'rb') as f:
        tokenizer = pickle.load(f)
    maxlen = 531
    if os.path.exists('model_config.json'):
        with open('model_config.json') as f:
            maxlen = json.load(f).get('smart_maxlen', 531)
    return model, tokenizer, maxlen

@st.cache_resource
def load_stopwords():
    for pkg in ['stopwords', 'punkt']:
        nltk.download(pkg, quiet=True)
    sw = set(stopwords.words('english'))
    sw.update(['from', 'subject', 're', 'use'])
    return sw

@st.cache_data
def load_eval_metrics():
    if os.path.exists('eval_metrics.json'):
        with open('eval_metrics.json') as f:
            return json.load(f)
    return None

model, tokenizer, MAXLEN = load_resources()
stop_words = load_stopwords()
eval_data  = load_eval_metrics()


# ─────────────────────────────────────────────
# PREPROCESSING
# ─────────────────────────────────────────────
def preprocess_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r'<.*?>', '', text)
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'^.*?\(reuters\)\s*-\s*', '', text)
    text = re.sub(r'^[a-z\s/]+\s-\s', '', text)
    text = re.sub(r'[^a-z\s]', '', text)
    text = re.sub(r'[%s]' % re.escape(string.punctuation), '', text)
    text = re.sub(r'\n', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return " ".join([w for w in text.split() if w not in stop_words])


# ─────────────────────────────────────────────
# PREDICTION
# ─────────────────────────────────────────────
def predict(text: str) -> dict | None:
    cleaned = preprocess_text(text)
    if not cleaned.strip():
        return None
    seq    = tokenizer.texts_to_sequences([cleaned])
    padded = pad_sequences(seq, maxlen=MAXLEN, padding='post', truncating='post')
    with tf.device('/CPU:0'):
        raw = float(model.predict(padded, verbose=0)[0][0])
    real_p = raw * 100
    fake_p = (1 - raw) * 100
    label  = 'REAL' if raw > 0.7 else ('FAKE' if raw < 0.3 else 'UNCERTAIN')
    return {'label': label, 'raw': raw, 'real_prob': real_p, 'fake_prob': fake_p,
            'word_count': len(cleaned.split()), 'cleaned': cleaned}


# ─────────────────────────────────────────────
# PLOTLY HELPERS
# ─────────────────────────────────────────────
def make_gauge(real_prob: float) -> go.Figure:
    color = '#52b788' if real_prob > 70 else ('#e63946' if real_prob < 30 else '#f4a261')
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=real_prob,
        number={'suffix': '%', 'font': {'size': 38, 'family': 'Syne', 'color': color}},
        title={'text': "Authenticity Score", 'font': {'size': 14, 'color': '#666', 'family': 'DM Sans'}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': '#ccc', 'tickfont': {'size': 11}},
            'bar': {'color': color, 'thickness': 0.25}, 'bgcolor': '#f4f4f8', 'borderwidth': 0,
            'steps': [
                {'range': [0,  30], 'color': 'rgba(230,57,70,0.12)'},
                {'range': [30, 70], 'color': 'rgba(244,162,97,0.12)'},
                {'range': [70,100], 'color': 'rgba(82,183,136,0.12)'},
            ],
            'threshold': {'line': {'color': color, 'width': 4}, 'thickness': 0.8, 'value': real_prob}
        }
    ))
    fig.update_layout(height=240, margin=dict(l=20, r=20, t=20, b=10),
                      paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    return fig


def make_roc_chart(e):
    fpr, tpr, roc_auc = e['roc_fpr'], e['roc_tpr'], e['roc_auc']
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[0,1], y=[0,1], mode='lines', line=dict(color='#aaa', dash='dash', width=1.5), name='Random (AUC = 0.50)', hoverinfo='skip'))
    fig.add_trace(go.Scatter(x=fpr, y=tpr, mode='lines', line=dict(color='#6c63ff', width=3), fill='tozeroy', fillcolor='rgba(108,99,255,0.12)', name=f'LSTM (AUC = {roc_auc:.4f})'))
    fig.update_layout(title='ROC Curve', xaxis=dict(title='False Positive Rate', range=[0,1]), yaxis=dict(title='True Positive Rate', range=[0,1.02]), height=400, paper_bgcolor='white', plot_bgcolor='#f9f9fc', margin=dict(l=30,r=20,t=50,b=40), legend=dict(x=0.5,y=0.1,bgcolor='rgba(255,255,255,0.8)',bordercolor='#ddd',borderwidth=1))
    return fig


def make_pr_chart(e):
    prec, rec, ap = e['pr_precision'], e['pr_recall'], e['average_precision']
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[0,1], y=[0.5,0.5], mode='lines', line=dict(color='#aaa', dash='dash', width=1.5), name='Random', hoverinfo='skip'))
    fig.add_trace(go.Scatter(x=rec, y=prec, mode='lines', line=dict(color='#52b788', width=3), fill='tozeroy', fillcolor='rgba(82,183,136,0.12)', name=f'LSTM (AP = {ap:.4f})'))
    fig.update_layout(title='Precision-Recall Curve', xaxis=dict(title='Recall', range=[0,1]), yaxis=dict(title='Precision', range=[0,1.02]), height=400, paper_bgcolor='white', plot_bgcolor='#f9f9fc', margin=dict(l=30,r=20,t=50,b=40), legend=dict(x=0.05,y=0.1,bgcolor='rgba(255,255,255,0.8)',bordercolor='#ddd',borderwidth=1))
    return fig


def make_threshold_chart(e, selected_threshold):
    tx   = e['thresh_x']
    data = [(e['thresh_acc'],'Accuracy','#4a90d9'),(e['thresh_prec'],'Precision','#f4a261'),(e['thresh_rec'],'Recall','#e63946'),(e['thresh_f1'],'F1-Score','#52b788')]
    fig  = go.Figure()
    for vals, name, color in data:
        fig.add_trace(go.Scatter(x=tx, y=vals, mode='lines', name=name, line=dict(color=color, width=2.5)))
    fig.add_vline(x=0.5, line_dash='dash', line_color='#888', annotation_text='Default (0.5)', annotation_position='top right')
    fig.add_vline(x=e['optimal_threshold_f1'], line_dash='dot', line_color='#52b788', annotation_text=f"Best F1 ({e['optimal_threshold_f1']:.2f})", annotation_position='top left')
    if selected_threshold not in [0.5, e['optimal_threshold_f1']]:
        fig.add_vline(x=selected_threshold, line_dash='solid', line_color='#6c63ff', annotation_text=f'Selected ({selected_threshold:.2f})', annotation_position='bottom right')
    fig.update_layout(title='Threshold Sensitivity', xaxis=dict(title='Decision Threshold', range=[0,1]), yaxis=dict(title='Score', range=[0,1.05]), height=400, paper_bgcolor='white', plot_bgcolor='#f9f9fc', hovermode='x unified', margin=dict(l=30,r=20,t=60,b=60), legend=dict(orientation='h',y=-0.22))
    return fig


def make_cm_chart(e):
    tp, tn, fp, fn = e['tp'], e['tn'], e['fp'], e['fn']
    fig = go.Figure(go.Heatmap(
        z=[[tn,fp],[fn,tp]], x=['Predicted: Fake','Predicted: Real'], y=['Actual: Fake','Actual: Real'],
        text=[[f'TN\n{tn}',f'FP\n{fp}'],[f'FN\n{fn}',f'TP\n{tp}']], texttemplate='%{text}',
        colorscale=[[0,'#f0f4ff'],[0.5,'#a5b4fc'],[1,'#4338ca']], showscale=False, textfont=dict(size=18,family='Syne'),
    ))
    fig.update_layout(title='Confusion Matrix (threshold = 0.5)', height=360, paper_bgcolor='white', plot_bgcolor='white', margin=dict(l=20,r=20,t=50,b=20), xaxis=dict(side='bottom'))
    return fig


def make_class_bar(e):
    metrics = ['precision','recall','f1-score']
    keys    = {'precision':('precision_fake_at_0.5','precision_real_at_0.5'),'recall':('recall_fake_at_0.5','recall_real_at_0.5'),'f1-score':('f1_fake_at_0.5','f1_real_at_0.5')}
    colors  = ['#e63946','#52b788','#4a90d9']
    fig = go.Figure()
    for metric, color in zip(metrics, colors):
        fk, rk = keys[metric]
        fig.add_trace(go.Bar(name=metric.capitalize(), x=['Fake','Real'], y=[e[fk],e[rk]], marker_color=color, text=[f"{e[fk]:.3f}",f"{e[rk]:.3f}"], textposition='outside'))
    fig.update_layout(title='Per-Class Metrics', barmode='group', yaxis=dict(title='Score',range=[0,1.12]), xaxis=dict(title='Class'), height=380, paper_bgcolor='white', plot_bgcolor='#f9f9fc', margin=dict(l=20,r=20,t=50,b=40), legend=dict(orientation='h',y=-0.2))
    return fig


# ─────────────────────────────────────────────
# HERO
# ─────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="hero-left">
        <span class="hero-icon">🔍</span>
        <div>
            <h1>Fake News Detection System</h1>            
        </div>
    </div>
    <div class="hero-badge">⚡ LSTM · NLP · Deep Learning</div>
</div>
""", unsafe_allow_html=True)
st.divider()
st.write("This app uses a Bidirectional LSTM model trained on the Kaggle Fake and True News and scraped kenyan news datasets."
         " The model was trained to classify news articles as REAL, FAKE or UNCERTAIN based on their text content."
         " Use the sidebar 👈 to navigate between sections.")


# ─────────────────────────────────────────────
# PAGE ROUTING
# ─────────────────────────────────────────────

# ══════════════════════════════════════════════
# PAGE 1 — DETECT
# ══════════════════════════════════════════════
if selected_page == "🔍  Detect":
    st.write("Choose an input method, then click **Analyse Article** to see the model's prediction and confidence scores.")

    tab_text, tab_file = st.tabs(["✏️  Text / Headline", "📂  Upload File"])
    file_text     = ""
    uploaded_file = None

    with tab_text:
        st.markdown('<p class="section-label">News Article or Headline</p>', unsafe_allow_html=True)
        user_input = st.text_area(label="text_input", label_visibility="collapsed", placeholder="Paste the full article or just a headline here…", height=200, key="user_text")

    with tab_file:
        st.markdown('<p class="section-label">Upload .txt or .csv</p>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Upload a news article", type=["txt","csv"], label_visibility="collapsed", key=st.session_state.file_uploader_key)
        if uploaded_file is not None:
            ext = uploaded_file.name.rsplit(".", 1)[-1].lower()
            if ext == "txt":
                file_text = uploaded_file.read().decode("utf-8")
                st.text_area("File contents", file_text, height=180, disabled=True)
            elif ext == "csv":
                df_up    = pd.read_csv(uploaded_file)
                st.dataframe(df_up.head(), use_container_width=True)
                text_col  = st.selectbox("Select the text column", df_up.columns)
                file_text = " ".join(df_up[text_col].astype(str).tolist())

    col_analyse, col_clear = st.columns([3, 1])
    with col_analyse:
        analyse_clicked = st.button("🔍  Analyse Article")
    with col_clear:
        def clear_form():
            st.session_state.user_text = ""  
            st.session_state.file_uploader_key += 1
        st.button("🗑  Clear Inputs", on_click=clear_form)

    if analyse_clicked:
        has_text = user_input.strip() != ""
        has_file = uploaded_file is not None and file_text.strip() != ""
        if has_text and has_file:
            st.error("⚠️ **Conflict:** Use either the text box OR the file upload — not both.")
            st.info("Click **Clear Inputs** to reset, then choose one input method.")
        elif not has_text and not has_file:
            st.warning("Please enter some text or upload a file before analysing.")
        else:
            input_text = file_text if has_file else user_input
            source_tag = "📂 Uploaded File" if has_file else "✏️ Text Input"
            with st.spinner("Running Bidirectional LSTM inference…"):
                result = predict(input_text)
            if result is None:
                st.error("The input produced no usable words after preprocessing. Try a longer article.")
            else:
                u = current_user()
                if u:
                    save_classification(u["id"], input_text, result)
                st.divider()
                label, real_prob, fake_prob = result['label'], result['real_prob'], result['fake_prob']
                if label == 'REAL':
                    css_cls = 'verdict-real'; icon, title = '✅', 'REAL NEWS DETECTED'
                    sub = f"The model is {real_prob:.1f}% confident this article is authentic."
                elif label == 'FAKE':
                    css_cls = 'verdict-fake'; icon, title = '🚨', 'FAKE NEWS DETECTED'
                    sub = f"The model is {fake_prob:.1f}% confident this is misinformation."
                else:
                    css_cls = 'verdict-uncertain'; icon, title = '⚠️', 'UNCERTAIN — MIXED SIGNALS'
                    sub = "The model cannot confidently classify this article. Verify independently."
                st.markdown(f'<div class="{css_cls}"><div class="verdict-title">{icon} {title}</div><div class="verdict-sub">{sub}</div></div>', unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
                c1, c2, c3, c4 = st.columns([1,1,1,2])
                with c1:
                    st.markdown(f'<div class="stat-box"><div class="stat-value" style="color:#52b788">{real_prob:.1f}%</div><div class="stat-label">Real probability</div></div>', unsafe_allow_html=True)
                with c2:
                    st.markdown(f'<div class="stat-box"><div class="stat-value" style="color:#e63946">{fake_prob:.1f}%</div><div class="stat-label">Fake probability</div></div>', unsafe_allow_html=True)
                with c3:
                    st.markdown(f'<div class="stat-box"><div class="stat-value" style="color:#4a4a7a">{result["word_count"]}</div><div class="stat-label">Words analysed</div></div>', unsafe_allow_html=True)
                with c4:
                    st.plotly_chart(make_gauge(real_prob), use_container_width=True)
                fig_bar = go.Figure(go.Bar(x=[real_prob, fake_prob], y=['Real','Fake'], orientation='h', marker_color=['#52b788','#e63946'], text=[f"{real_prob:.1f}%",f"{fake_prob:.1f}%"], textposition='inside', textfont=dict(color='white',family='Syne',size=13)))
                fig_bar.update_layout(height=120, margin=dict(l=0,r=0,t=10,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(range=[0,100],showgrid=False,showticklabels=False,zeroline=False), yaxis=dict(showgrid=False), showlegend=False)
                st.plotly_chart(fig_bar, use_container_width=True)
                st.markdown(f'<div class="info-box"><b>Source:</b> {source_tag} &nbsp;·&nbsp; <b>MAXLEN:</b> {MAXLEN} &nbsp;·&nbsp; <b>Model:</b> Bidirectional LSTM</div>', unsafe_allow_html=True)
                with st.expander("🔎 View preprocessed text"):
                    st.code(result['cleaned'][:1000] + ("…" if len(result['cleaned']) > 1000 else ""), language=None)
                if label == 'UNCERTAIN':
                    st.info("💡 **Tip:** Uncertain results often arise from short text, satire, or opinion pieces. Cross-check with a trusted fact-checking source.")


# ══════════════════════════════════════════════
# PAGE 2 — MODEL EVALUATION
# ══════════════════════════════════════════════
elif selected_page == "📊  Model Evaluation":
    if eval_data is None:
        st.warning("**`eval_metrics.json` not found.** Run the training notebook through to Cell 26 to generate this file.")
    else:
        e = eval_data
        st.markdown('<div style="margin-bottom:1.5rem;"><p class="section-label">Model Performance on Held-Out Test Set</p><p style="color:#666;font-size:0.95rem;margin:0;">All metrics computed on the 20% test split.</p></div>', unsafe_allow_html=True)

        def badge(val, good=0.95, warn=0.85):
            return 'score-badge-good' if val >= good else ('score-badge-warn' if val >= warn else 'score-badge-danger')

        sc1, sc2, sc3, sc4 = st.columns(4)
        with sc1:
            st.markdown(f'<div class="score-card"><div class="score-card-title">AUC-ROC</div><div class="score-card-value {badge(e["roc_auc"],0.97,0.90)}">{e["roc_auc"]:.4f}</div><div class="score-card-sub">Threshold-independent · 1.0 = perfect</div></div>', unsafe_allow_html=True)
        with sc2:
            st.markdown(f'<div class="score-card"><div class="score-card-title">Average Precision</div><div class="score-card-value {badge(e["average_precision"],0.97,0.90)}">{e["average_precision"]:.4f}</div><div class="score-card-sub">Area under PR curve</div></div>', unsafe_allow_html=True)
        with sc3:
            st.markdown(f'<div class="score-card"><div class="score-card-title">Accuracy (t = 0.50)</div><div class="score-card-value {badge(e["accuracy_at_0.5"],0.97,0.90)}">{e["accuracy_at_0.5"]:.4f}</div><div class="score-card-sub">Overall correct predictions</div></div>', unsafe_allow_html=True)
        with sc4:
            st.markdown(f'<div class="score-card"><div class="score-card-title">Macro F1 (t = 0.50)</div><div class="score-card-value {badge(e["macro_f1_at_0.5"],0.97,0.90)}">{e["macro_f1_at_0.5"]:.4f}</div><div class="score-card-sub">Balanced across both classes</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<p class="section-label">Curves</p>', unsafe_allow_html=True)
        col_roc, col_pr = st.columns(2)
        with col_roc:
            st.markdown('<div class="insight-box">📌 <b>ROC Curve:</b> Plots True Positive Rate vs False Positive Rate across all thresholds. AUC = 1.0 is perfect.</div>', unsafe_allow_html=True)
            st.plotly_chart(make_roc_chart(e), use_container_width=True)
        with col_pr:
            st.markdown('<div class="insight-box">📌 <b>Precision-Recall Curve:</b> More informative for imbalanced datasets. AP = area under this curve.</div>', unsafe_allow_html=True)
            st.plotly_chart(make_pr_chart(e), use_container_width=True)

        st.divider()
        st.markdown('<p class="section-label">Threshold Sensitivity</p>', unsafe_allow_html=True)
        st.markdown('<div class="insight-box">🎚️ <b>How to use this:</b> Move the slider to explore how each metric changes as the decision threshold shifts.</div>', unsafe_allow_html=True)
        selected_threshold = st.slider("Decision Threshold", min_value=0.01, max_value=0.99, value=0.50, step=0.01, format="%.2f")
        tx      = e['thresh_x']
        nearest = min(range(len(tx)), key=lambda i: abs(tx[i] - selected_threshold))
        lc1, lc2, lc3, lc4 = st.columns(4)
        for col, label_t, val, color in [(lc1,'Accuracy',e['thresh_acc'][nearest],'#4a90d9'),(lc2,'Precision',e['thresh_prec'][nearest],'#f4a261'),(lc3,'Recall',e['thresh_rec'][nearest],'#e63946'),(lc4,'F1-Score',e['thresh_f1'][nearest],'#52b788')]:
            with col:
                st.markdown(f'<div class="stat-box"><div class="stat-value" style="color:{color}">{val:.3f}</div><div class="stat-label">{label_t} @ {selected_threshold:.2f}</div></div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.plotly_chart(make_threshold_chart(e, selected_threshold), use_container_width=True)

        st.divider()
        st.markdown('<p class="section-label">Classification Breakdown</p>', unsafe_allow_html=True)
        col_cm, col_bar = st.columns(2)
        with col_cm:
            st.markdown('<div class="insight-box">📌 <b>Confusion Matrix</b> at threshold 0.5. TP/TN = correct, FP = real flagged as fake, FN = fake missed.</div>', unsafe_allow_html=True)
            st.plotly_chart(make_cm_chart(e), use_container_width=True)
            tp, tn, fp, fn = e['tp'], e['tn'], e['fp'], e['fn']
            total = tp + tn + fp + fn
            st.markdown(f'<table class="cm-table"><tr><td></td><td><b>Pred: Fake</b></td><td><b>Pred: Real</b></td></tr><tr><td><b>Actual: Fake</b></td><td class="cm-tn">{tn}<br><small>TN ({tn/total*100:.1f}%)</small></td><td class="cm-fp">{fp}<br><small>FP ({fp/total*100:.1f}%)</small></td></tr><tr><td><b>Actual: Real</b></td><td class="cm-fn">{fn}<br><small>FN ({fn/total*100:.1f}%)</small></td><td class="cm-tp">{tp}<br><small>TP ({tp/total*100:.1f}%)</small></td></tr></table>', unsafe_allow_html=True)
        with col_bar:
            st.markdown('<div class="insight-box">📌 <b>Per-Class Metrics</b> — comparing Fake vs Real. Prioritise Fake class Recall to catch all fakes.</div>', unsafe_allow_html=True)
            st.plotly_chart(make_class_bar(e), use_container_width=True)
            metrics_df = pd.DataFrame({'Metric':['Precision','Recall','F1-Score'],'Fake (0)':[f"{e['precision_fake_at_0.5']:.4f}",f"{e['recall_fake_at_0.5']:.4f}",f"{e['f1_fake_at_0.5']:.4f}"],'Real (1)':[f"{e['precision_real_at_0.5']:.4f}",f"{e['recall_real_at_0.5']:.4f}",f"{e['f1_real_at_0.5']:.4f}"]})
            st.dataframe(metrics_df, use_container_width=True, hide_index=True)

        st.divider()
        opt_t = e['optimal_threshold_f1']
        st.markdown(f'<div class="insight-box" style="border-color:#52b788;background:#f0fff6;">✅ <b>Recommendation:</b> Best F1 threshold is <b>{opt_t:.2f}</b> (accuracy={e["accuracy_at_optimal"]:.4f}, Fake F1={e["f1_fake_at_optimal"]:.4f}, Real F1={e["f1_real_at_optimal"]:.4f}).</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════
# PAGE 3 — DATASET & TRAINING
# ══════════════════════════════════════════════
elif selected_page == "📁  Dataset & Training":
    st.markdown('<p class="section-label">Dataset & Training Insights</p>', unsafe_allow_html=True)
    st.markdown("""<h5>Dataset</h5>
                The model was trained on the following datasets:<br>  
                > Kaggle Fake and True News Dataset (True.csv and Fake.csv) (~44,000 articles).<br>
                > kenyan news(news.csv and kenya.csv) which was scraped from news sources including the standard and nation<br><br>
                <h5>Preprocessing & Model</h5>
                The dataset was cleaned and only required columns were retained that is title, text and label.<br>
                Key techniques: text preprocessing, tokenisation, padding to 531 tokens, Bidirectional LSTM, EarlyStopping, ReduceLROnPlateau.<br>
                80/20 stratified train-test split was used to evaluate performance on unseen data.<br>
                <h5>Evaluation</h5>
                The model achieved strong performance on the test set, with an AUC-ROC of 0.9996 and an accuracy of 0.9918 at the default threshold of 0.5.<br>
                Detailed evaluation metrics, curves, and confusion matrix are available in the Model Evaluation section.
                <h5>Additional Notes</h5>
                - The model is more likely to misclassify short articles or headlines, which may lack sufficient context for accurate classification.<br>
                - The dataset contains a mix of news topics and writing styles, which can influence model performance on certain types of articles.<br>
                - The model may classify satire or opinion pieces as "UNCERTAIN" due to mixed signals in the text. Always verify uncertain results with trusted sources.<br>
                - The model is not in real time and may classify real news as fake if it contains sensational language or lacks credible context. Use the authenticity score as a guide, not an absolute verdict.<br>
                """, unsafe_allow_html=True)
    
    st.divider()
    st.markdown('<div class="insight-box"><b>Model Architecture:</b> Bidirectional LSTM (128+64 units), SpatialDropout1D, 128-dim Embedding, sigmoid output. Trained on 80/20 stratified split.</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════
# PAGE 4 — HISTORY
# ══════════════════════════════════════════════
elif selected_page == "🕒  History":
    st.markdown('<p class="section-label">Classification history</p>', unsafe_allow_html=True)
    u = current_user()
    if u is None:
        st.warning("You must be logged in to view history.")
    else:
        rows = get_user_history(u['id'], limit=50)

        # ── Session state for checkboxes ──────────────────────────
        if "hist_selected" not in st.session_state:
            st.session_state.hist_selected = set()

        # Keep only IDs that still exist in the fetched rows
        valid_ids = {dict(r)["id"] for r in rows} if rows else set()
        st.session_state.hist_selected &= valid_ids

        # ── Pre-sync checkboxes BEFORE computing n_sel ────────────
        if rows:
            hist_df_temp = pd.DataFrame([dict(r) for r in rows])
            all_ids = set(hist_df_temp["id"].tolist())

            current_select_all = st.session_state.get("hist_select_all", False)
            prev_select_all    = st.session_state.get("hist_select_all_prev", False)

            if current_select_all:
                # Select All just ticked → force-select every row
                st.session_state.hist_selected = all_ids.copy()
                for rid in all_ids:
                    st.session_state[f"hist_row_{rid}"] = True

            elif not current_select_all and prev_select_all:
                # Select All just UN-ticked → force-clear every row
                st.session_state.hist_selected = set()
                for rid in all_ids:
                    st.session_state[f"hist_row_{rid}"] = False

            else:
                # Normal individual checkbox sync
                for rid in all_ids:
                    key = f"hist_row_{rid}"
                    if key in st.session_state:
                        if st.session_state[key]:
                            st.session_state.hist_selected.add(rid)
                        else:
                            st.session_state.hist_selected.discard(rid)

            # Remember current value for next rerun
            st.session_state.hist_select_all_prev = current_select_all

        # ── Top action bar ────────────────────────────────────────
        col_info, col_del_sel, col_clear = st.columns([3, 1.4, 1.4])
        with col_info:
            st.write(f"Showing your last **{min(len(rows), 50)}** classification(s).")
        with col_del_sel:
            n_sel = len(st.session_state.hist_selected)
            del_label = f"🗑  Delete Selected ({n_sel})" if n_sel else "🗑  Delete Selected"
            if st.button(del_label, use_container_width=True, disabled=(n_sel == 0)):
                delete_selected_history(u['id'], list(st.session_state.hist_selected))
                for rid in list(st.session_state.hist_selected):
                    st.session_state.pop(f"hist_row_{rid}", None)
                st.session_state.hist_selected = set()
                st.session_state.pop("hist_select_all", None)
                st.session_state.pop("hist_select_all_prev", None)
                st.success(f"Deleted {n_sel} record(s).")
                st.rerun()
        with col_clear:
            if st.button("🗑  Clear All History", use_container_width=True):
                clear_user_history(u['id'])
                for rid in valid_ids:
                    st.session_state.pop(f"hist_row_{rid}", None)
                st.session_state.hist_selected = set()
                st.session_state.pop("hist_select_all", None)
                st.session_state.pop("hist_select_all_prev", None)
                st.success("History cleared.")
                st.rerun()

        if not rows:
            st.info("No classifications yet. Go to **Detect** in the sidebar to analyse your first article.")
        else:
            hist_df = pd.DataFrame([dict(r) for r in rows])
            hist_df["real_prob"]  = hist_df["real_prob"].round(3)
            hist_df["fake_prob"]  = hist_df["fake_prob"].round(3)
            hist_df["input_text"] = hist_df["input_text"].str[:80] + "…"

            # ── Select All checkbox ───────────────────────────────
            all_ids    = set(hist_df["id"].tolist())
            all_ticked = st.session_state.hist_selected == all_ids
            st.checkbox(
                "Select All",
                value=all_ticked,
                key="hist_select_all",
            )

            st.markdown("<br>", unsafe_allow_html=True)

            # ── Label colour helper ───────────────────────────────
            LABEL_STYLES = {
                "REAL":      ("background:#d4edda;color:#155724;", "REAL"),
                "FAKE":      ("background:#f8d7da;color:#721c24;", "FAKE"),
                "UNCERTAIN": ("background:#fff3cd;color:#856404;", "UNCERTAIN"),
            }

            # ── Column headers ────────────────────────────────────
            hc0, hc1, hc2, hc3, hc4, hc5, hc6 = st.columns([0.4, 1.2, 0.8, 0.8, 0.7, 1.3, 3.6])
            for col, label in zip(
                [hc1, hc2, hc3, hc4, hc5, hc6],
                ["Label", "Real %", "Fake %", "Words", "Classified At", "Article Preview"],
            ):
                col.markdown(
                    f'<p style="font-size:0.78rem;font-weight:700;color:#888;'
                    f'text-transform:uppercase;letter-spacing:0.8px;margin:0">{label}</p>',
                    unsafe_allow_html=True,
                )
            st.markdown('<hr style="margin:4px 0 8px;border-color:#e2e5ec">', unsafe_allow_html=True)

            # ── Rows ──────────────────────────────────────────────
            for _, row in hist_df.iterrows():
                row_id     = row["id"]
                is_checked = row_id in st.session_state.hist_selected

                c0, c1, c2, c3, c4, c5, c6 = st.columns([0.4, 1.2, 0.8, 0.8, 0.7, 1.3, 3.6])

                # Checkbox
                with c0:
                    st.checkbox(
                        label=f"Select record {row_id}",
                        value=is_checked,
                        key=f"hist_row_{row_id}",
                        label_visibility="collapsed",
                    )

                # Label badge
                with c1:
                    style, text = LABEL_STYLES.get(row["label"], ("", row["label"]))
                    st.markdown(
                        f'<span style="padding:3px 10px;border-radius:50px;font-size:0.78rem;'
                        f'font-weight:700;{style}">{text}</span>',
                        unsafe_allow_html=True,
                    )

                with c2:
                    st.markdown(f'<p style="margin:0;font-size:0.88rem;color:#155724"><b>{row["real_prob"]:.3f}</b></p>', unsafe_allow_html=True)
                with c3:
                    st.markdown(f'<p style="margin:0;font-size:0.88rem;color:#721c24"><b>{row["fake_prob"]:.3f}</b></p>', unsafe_allow_html=True)
                with c4:
                    st.markdown(f'<p style="margin:0;font-size:0.88rem">{row["word_count"]}</p>', unsafe_allow_html=True)
                with c5:
                    st.markdown(f'<p style="margin:0;font-size:0.78rem;color:#666">{row["classified_at"]}</p>', unsafe_allow_html=True)
                with c6:
                    st.markdown(f'<p style="margin:0;font-size:0.83rem;color:#333">{row["input_text"]}</p>', unsafe_allow_html=True)

                st.markdown('<hr style="margin:4px 0;border-color:#f0f0f0">', unsafe_allow_html=True)
# ══════════════════════════════════════════════
# PAGE 6 — SUPPORT CHAT
# ══════════════════════════════════════════════
else:
    u = current_user()
    if u:
        show_chat_page(u)
