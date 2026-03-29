"""
app_presentation.py — PixelOptimize · Light Premium Design
Lance avec : streamlit run app_presentation.py
"""

import streamlit as st
import requests, base64, json, re, time, io, os, zipfile
from PIL import Image
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
try:
    from streamlit_extras.add_vertical_space import add_vertical_space
except ImportError:
    def add_vertical_space(n):
        for _ in range(n): st.write("")

N8N_WEBHOOK_URL = "http://localhost:5678/webhook/compression-pipeline"
RAPPORTS_DIR = BASE_DIR / "rapports"
RAPPORTS_DIR.mkdir(parents=True, exist_ok=True)

LOGO_PATH = os.path.join(os.path.dirname(__file__), "PixelOptimize_Logo_2.png")

with open(LOGO_PATH, "rb") as f:
    LOGO_DATA_URI = "data:image/png;base64," + base64.b64encode(f.read()).decode()

_page_icon = Image.open(os.path.join(os.path.dirname(__file__), "PixelOptimize_Logo_2.png"))

st.set_page_config(
    page_title="PixelOptimize",
    layout="wide",
    page_icon=_page_icon,
    initial_sidebar_state="expanded"
)

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
:root {
  --bg:#F8F7FF;--bg2:#FFFFFF;--bg3:#F2F0FC;--card:#FFFFFF;
  --border:#E8E4F8;--violet:#7C5CBF;--pink:#E8559A;
  --gold:#E5A800;--green:#22C55E;--red:#EF4444;
  --text:#1A1F2E;--muted:#6B7280;--shadow:rgba(124,92,191,0.1);
  --grad:linear-gradient(135deg,#7C5CBF 0%,#E8559A 100%);
}
*{box-sizing:border-box;margin:0;padding:0;}
html,body,[class*="css"]{font-family:'Plus Jakarta Sans',sans-serif!important;background:var(--bg)!important;color:var(--text)!important;}
.stApp{background:var(--bg)!important;}
::-webkit-scrollbar{width:5px}::-webkit-scrollbar-track{background:var(--bg3)}::-webkit-scrollbar-thumb{background:var(--violet);border-radius:10px}
[data-testid="stSidebar"]{background:#fff!important;border-right:1px solid var(--border)!important;box-shadow:2px 0 20px rgba(124,92,191,0.06)!important;}
[data-testid="stSidebar"] *{color:var(--text)!important;}
section[data-testid="stSidebar"]>div{padding:0!important;}
[data-testid="stSidebar"] .stButton>button{
  background:transparent!important;color:var(--muted)!important;
  border:1px solid var(--border)!important;border-radius:10px!important;
  box-shadow:none!important;font-weight:500!important;font-size:0.84rem!important;
  padding:9px 14px!important;transition:all 0.2s!important;margin-bottom:3px!important;
  transform:none!important;filter:none!important;
}
[data-testid="stSidebar"] .stButton>button:hover{
  background:var(--bg3)!important;color:var(--violet)!important;
  border-color:rgba(124,92,191,0.35)!important;transform:none!important;box-shadow:none!important;
}
.main .block-container{padding:0 2.5rem 3rem 2.5rem!important;max-width:1400px;background:var(--bg)!important;}
.hero-wrap{min-height:85vh;display:flex;flex-direction:column;justify-content:center;padding:60px 0 40px;position:relative;overflow:hidden;}
.hero-glow-1{position:absolute;top:-100px;right:-60px;width:450px;height:450px;border-radius:50%;background:radial-gradient(circle,rgba(124,92,191,0.1) 0%,transparent 70%);pointer-events:none;animation:floatGlow 6s ease-in-out infinite;}
.hero-glow-2{position:absolute;bottom:-80px;left:-40px;width:320px;height:320px;border-radius:50%;background:radial-gradient(circle,rgba(232,85,154,0.08) 0%,transparent 70%);pointer-events:none;animation:floatGlow 8s ease-in-out infinite reverse;}
.hero-chip{display:inline-flex;align-items:center;gap:8px;background:rgba(124,92,191,0.08);border:1px solid rgba(124,92,191,0.25);color:var(--violet)!important;padding:6px 16px;border-radius:100px;font-size:0.72rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;margin-bottom:24px;width:fit-content;}
.hero-chip::before{content:'';width:6px;height:6px;border-radius:50%;background:var(--violet);animation:blink 1.8s infinite;}
.hero-title{font-size:clamp(2.4rem,5vw,3.8rem)!important;font-weight:800!important;line-height:1.1!important;letter-spacing:-1.5px!important;color:var(--text)!important;margin-bottom:18px!important;}
.hero-title .grad{background:var(--grad);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}
.hero-sub{font-size:1.05rem!important;color:var(--muted)!important;max-width:500px;line-height:1.75;margin-bottom:32px!important;}
.hero-tags{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:44px;}
.hero-tag{background:white;border:1px solid var(--border);color:var(--muted)!important;padding:6px 14px;border-radius:8px;font-size:0.77rem;font-weight:500;box-shadow:0 1px 4px var(--shadow);}
.hero-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;max-width:480px;}
.hero-stat{background:white;border:1px solid var(--border);border-radius:14px;padding:18px 14px;text-align:center;box-shadow:0 2px 12px var(--shadow);transition:transform 0.2s,box-shadow 0.2s;}
.hero-stat:hover{transform:translateY(-3px);box-shadow:0 6px 20px var(--shadow);}
.hero-stat-val{font-size:1.6rem;font-weight:800;font-family:'JetBrains Mono',monospace;background:var(--grad);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}
.hero-stat-lbl{font-size:0.68rem;color:var(--muted);margin-top:4px;text-transform:uppercase;letter-spacing:1px;}
.sec-hd{font-size:0.65rem;font-weight:700;letter-spacing:2.5px;text-transform:uppercase;color:var(--muted);display:flex;align-items:center;gap:12px;margin:32px 0 16px;}
.sec-hd::after{content:'';flex:1;height:1px;background:var(--border);}
.card{background:white;border:1px solid var(--border);border-radius:16px;padding:22px;margin-bottom:16px;box-shadow:0 2px 12px var(--shadow);transition:box-shadow 0.2s,transform 0.2s;}
.card:hover{box-shadow:0 6px 24px var(--shadow);transform:translateY(-1px);}
.m-tile{background:white;border:1px solid var(--border);border-radius:14px;padding:18px 14px;text-align:center;position:relative;overflow:hidden;box-shadow:0 2px 10px var(--shadow);transition:all 0.25s;}
.m-tile::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:var(--grad);}
.m-tile:hover{box-shadow:0 8px 24px rgba(124,92,191,0.18);transform:translateY(-2px);}
.m-val{font-size:1.7rem;font-weight:800;font-family:'JetBrains Mono',monospace;color:var(--text);line-height:1;margin:8px 0 4px;}
.m-lbl{font-size:0.65rem;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:var(--muted);}
.m-sub{font-size:0.72rem;color:var(--violet);margin-top:3px;font-weight:500;}
.dash-card{background:white;border:1px solid var(--border);border-radius:14px;padding:20px;box-shadow:0 2px 12px var(--shadow);transition:all 0.2s;}
.dash-card:hover{box-shadow:0 8px 24px var(--shadow);transform:translateY(-2px);}
.dash-card-icon{width:40px;height:40px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:18px;margin-bottom:12px;}
.dash-card-val{font-size:1.6rem;font-weight:800;font-family:'JetBrains Mono',monospace;color:var(--text);}
.dash-card-lbl{font-size:0.75rem;color:var(--muted);margin-top:3px;}
.ag-row{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0;}
.ag-badge{display:inline-flex;align-items:center;gap:6px;padding:6px 14px;border-radius:8px;font-size:0.77rem;font-weight:600;border:1px solid transparent;transition:all 0.3s;}
.ag-wait{background:#F9F9F9;color:var(--muted);border-color:var(--border);}
.ag-run{background:rgba(124,92,191,0.08);color:var(--violet);border-color:rgba(124,92,191,0.25);animation:pulse 1.2s infinite;}
.ag-done{background:rgba(34,197,94,0.08);color:#16A34A;border-color:rgba(34,197,94,0.25);}
.ag-error{background:rgba(239,68,68,0.08);color:#DC2626;border-color:rgba(239,68,68,0.25);}
.tag{display:inline-block;padding:3px 10px;border-radius:6px;font-size:0.72rem;font-weight:600;background:rgba(124,92,191,0.08);color:var(--violet);border:1px solid rgba(124,92,191,0.2);}
.rpt{background:var(--bg3);border:1px solid var(--border);border-radius:12px;padding:16px 20px;font-size:0.87rem;line-height:2;color:var(--text);margin:10px 0;}
.hist-wrap{background:white;border:1px solid var(--border);border-radius:14px;overflow:hidden;box-shadow:0 2px 12px var(--shadow);}
.hist-row{display:grid;grid-template-columns:2fr 1fr 1fr 1fr 1fr 90px;gap:12px;padding:12px 16px;font-size:0.82rem;align-items:center;border-bottom:1px solid var(--border);}
.hist-row:last-child{border-bottom:none;}
.hist-header{color:var(--muted);font-size:0.68rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;background:var(--bg3);}
.ch-badge{background:rgba(229,168,0,0.1);color:var(--gold);border:1px solid rgba(229,168,0,0.25);padding:4px 12px;border-radius:8px;font-size:0.73rem;font-weight:600;}
.stButton>button{background:var(--grad)!important;color:white!important;border:none!important;border-radius:12px!important;font-family:'Plus Jakarta Sans',sans-serif!important;font-weight:700!important;font-size:0.88rem!important;padding:12px 24px!important;width:100%!important;transition:all 0.3s cubic-bezier(0.4,0,0.2,1)!important;box-shadow:0 4px 15px rgba(124,92,191,0.3)!important;}
.stButton>button:hover{box-shadow:0 8px 25px rgba(232,85,154,0.4)!important;transform:translateY(-2px) scale(1.01)!important;filter:brightness(1.05)!important;}
.stButton>button:active{transform:translateY(0) scale(0.98)!important;}
.stTabs [data-baseweb="tab-list"]{gap:4px;background:white;border:1px solid var(--border);border-radius:12px;padding:4px;margin-bottom:24px;box-shadow:0 2px 8px var(--shadow);}
.stTabs [data-baseweb="tab"]{border-radius:9px!important;font-weight:600!important;font-size:0.85rem!important;color:var(--muted)!important;padding:8px 20px!important;border:none!important;}
.stTabs [aria-selected="true"]{background:var(--grad)!important;color:white!important;box-shadow:0 4px 12px rgba(124,92,191,0.3)!important;}
.streamlit-expanderHeader{background:white!important;border:1px solid var(--border)!important;border-radius:12px!important;color:var(--text)!important;font-weight:600!important;box-shadow:0 1px 4px var(--shadow)!important;}
.streamlit-expanderHeader:hover{border-color:rgba(124,92,191,0.35)!important;}
[data-testid="stFileUploader"]{border:2px dashed rgba(124,92,191,0.3)!important;border-radius:14px!important;background:var(--bg3)!important;}
.sb-logo{padding:24px 18px 18px;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:12px;}
.sb-logo img{width:38px;height:38px;border-radius:10px;object-fit:cover;}
.sb-logo-name{font-size:1.05rem;font-weight:800;letter-spacing:-0.3px;color:var(--text);}
.sb-logo-name span{background:var(--grad);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
.sb-logo-sub{font-size:0.62rem;color:var(--muted);letter-spacing:1.5px;text-transform:uppercase;margin-top:3px;}
.sb-section-lbl{font-size:0.6rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:var(--muted);padding:14px 18px 6px;}
.sb-agent{display:flex;align-items:center;gap:10px;padding:9px 16px;border-radius:10px;margin:2px 8px;border:1px solid transparent;transition:all 0.2s;}
.sb-agent:hover{background:var(--bg3);border-color:var(--border);}
.sb-agent-icon{width:28px;height:28px;border-radius:7px;display:flex;align-items:center;justify-content:center;font-size:13px;background:var(--bg3);flex-shrink:0;}
.sb-agent-name{font-size:.82rem;font-weight:600;color:var(--text);}
.sb-agent-who{font-size:.65rem;color:var(--muted);}
.topbar{display:flex;align-items:center;justify-content:space-between;padding:18px 0 12px;border-bottom:1px solid var(--border);margin-bottom:0;}
.topbar-logo{display:flex;align-items:center;gap:14px;}
.topbar-brand{font-size:1.25rem;font-weight:800;letter-spacing:-0.5px;}
.topbar-brand span{background:var(--grad);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
.user-badge{display:inline-flex;align-items:center;gap:7px;background:rgba(124,92,191,0.08);border:1px solid rgba(124,92,191,0.2);border-radius:100px;padding:5px 14px;font-size:0.75rem;font-weight:600;color:var(--violet);}
.login-wrap{max-width:420px;margin:80px auto;background:white;border:1px solid var(--border);border-radius:20px;padding:40px;box-shadow:0 8px 40px var(--shadow);}
.eff-badge-excellent{background:rgba(34,197,94,0.1);color:#16A34A;border:1px solid rgba(34,197,94,0.3);padding:3px 10px;border-radius:6px;font-size:0.72rem;font-weight:600;}
.eff-badge-bon{background:rgba(34,197,94,0.08);color:#16A34A;border:1px solid rgba(34,197,94,0.2);padding:3px 10px;border-radius:6px;font-size:0.72rem;font-weight:600;}
.eff-badge-modere{background:rgba(229,168,0,0.1);color:#B45309;border:1px solid rgba(229,168,0,0.3);padding:3px 10px;border-radius:6px;font-size:0.72rem;font-weight:600;}
.eff-badge-faible{background:rgba(239,68,68,0.1);color:#DC2626;border:1px solid rgba(239,68,68,0.3);padding:3px 10px;border-radius:6px;font-size:0.72rem;font-weight:600;}
#MainMenu{visibility:hidden}footer{visibility:hidden}header{visibility:hidden}
@keyframes blink{0%,100%{opacity:1}50%{opacity:0.3}}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.6}}
@keyframes fadeUp{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:translateY(0)}}
@keyframes floatGlow{0%,100%{transform:translateY(0)}50%{transform:translateY(-20px)}}
@keyframes slideIn{from{opacity:0;transform:translateX(-10px)}to{opacity:1;transform:translateX(0)}}
.anim-1{animation:fadeUp 0.4s 0.1s both}
.anim-2{animation:fadeUp 0.4s 0.2s both}
.anim-3{animation:fadeUp 0.4s 0.3s both}
.slide-in{animation:slideIn 0.35s ease both}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# AUTH
# ══════════════════════════════════════════════════════
USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")

def load_users():
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except: return {}

def save_users(users):
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
    except: pass

def hash_password(p):
    import hashlib
    return hashlib.sha256(p.encode("utf-8")).hexdigest()

def verify_password(users, email, password):
    user = users.get(email.lower().strip())
    if not user: return False
    return user.get("password","") == hash_password(password)

def register_user(users, email, password):
    e = email.lower().strip()
    if e in users: return False, "Email déjà enregistré."
    users[e] = {"password": hash_password(password), "created_at": datetime.now().isoformat()}
    save_users(users)
    return True, None

USERS = load_users()

for k,v in [("auth_user",None),("auth_mode","guest"),("show_auth_modal",False),("page","accueil"),("history",[])]:
    if k not in st.session_state: st.session_state[k] = v

def is_logged_in(): return st.session_state["auth_user"] is not None
def is_guest(): return not is_logged_in()

def logout():
    st.session_state["auth_user"] = None
    st.session_state["auth_mode"] = "guest"
    st.session_state["page"] = "accueil"
    st.rerun()

def show_auth_dialog():
    tabs = st.tabs(["Connexion", "Inscription"])
    with tabs[0]:
        with st.form("auth_login_form"):
            email    = st.text_input("Email", placeholder="votre@email.com")
            password = st.text_input("Mot de passe", type="password")
            ok       = st.form_submit_button("🔐 Se connecter", use_container_width=True)
            if ok:
                if verify_password(USERS, email, password):
                    st.session_state["auth_user"] = email.strip()
                    st.session_state["auth_mode"] = "user"
                    st.session_state["show_auth_modal"] = False
                    st.session_state["page"] = "accueil"
                    st.rerun()
                else:
                    st.error("Email ou mot de passe invalide.")
    with tabs[1]:
        with st.form("auth_signup_form"):
            email_s = st.text_input("Email", key="sign_email")
            pass1   = st.text_input("Mot de passe", type="password", key="sign_pwd1")
            pass2   = st.text_input("Confirmer le mot de passe", type="password", key="sign_pwd2")
            s_ok    = st.form_submit_button("📝 Créer un compte", use_container_width=True)
            if s_ok:
                if not re.match(r"[^@]+@[^@]+\.[^@]+", email_s or ""):
                    st.error("Email invalide.")
                elif not pass1 or len(pass1) < 6:
                    st.error("Mot de passe trop court (≥ 6 caractères).")
                elif pass1 != pass2:
                    st.error("Les mots de passe ne correspondent pas.")
                else:
                    users = load_users()
                    ok2, err = register_user(users, email_s, pass1)
                    if ok2: st.success("Compte créé. Vous pouvez vous connecter.")
                    else: st.error(err or "Échec de l'inscription.")
    st.markdown('<hr style="margin: 20px 0 10px">', unsafe_allow_html=True)
    if st.button("← Retour à l'accueil", use_container_width=True):
        st.session_state["show_auth_modal"] = False
        st.session_state["page"] = "accueil"
        st.rerun()

# ══════════════════════════════════════════════════════
# TOPBAR
# ══════════════════════════════════════════════════════
st.markdown(
    f'''<div class="topbar">
<div style="width: 100%; display: flex; justify-content: center;">
    <div class="topbar-logo" style="display: flex; flex-direction: column; align-items: center; margin-bottom: 32px;">
        <div style="display: flex; align-items: center; gap: 12px;">
            <img src="{LOGO_DATA_URI}" alt="PixelOptimize Logo" style="width: 48px; height: auto;"/>
            <div class="topbar-brand" style="font-size: 2.9rem; font-weight: 800;"><span>Pixel</span>Optimize</div>
        </div>
        <div style="font-size:.7rem; color:var(--muted); letter-spacing:1.5px; text-transform:uppercase; margin-top: 5px; padding-left: 40px;">Compression IA · Multi-Agents</div>
    </div>
</div>
</div>''',
    unsafe_allow_html=True
)

top_spacer, top_auth = st.columns([5, 1])
with top_auth:
    if is_logged_in():
        st.markdown(f'<div class="user-badge" style="margin-top:4px">👤 {st.session_state["auth_user"]}</div>', unsafe_allow_html=True)
        if st.button("Déconnexion", key="logout_top"):
            logout()
    else:
        if st.button("🔐 Se connecter", key="login_top", use_container_width=True):
            st.session_state["show_auth_modal"] = True

if st.session_state.get("show_auth_modal"):
    show_auth_dialog()
    st.stop()

# ══════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════
def compute_eval(ssim_val):
    try:
        sv = float(ssim_val)
        if sv >= 0.95: return "Excellent"
        if sv >= 0.90: return "Bon"
        if sv >= 0.80: return "Acceptable"
        return "Dégradé"
    except: return "?"

def compute_compression_efficiency(tau_val):
    try:
        t = float(tau_val)
        if t > 50:  return "Excellent"
        if t > 30:  return "Bon"
        if t > 15:  return "Modéré"
        return "Faible"
    except: return "?"

def efficiency_badge_class(eff):
    m = {"Excellent":"eff-badge-excellent","Bon":"eff-badge-bon","Modéré":"eff-badge-modere","Faible":"eff-badge-faible"}
    return m.get(eff,"eff-badge-modere")

def safe_dict(val):
    if isinstance(val, dict): return val
    if isinstance(val, str):
        try:
            parsed = json.loads(val)
            if isinstance(parsed, dict): return parsed
        except: pass
    return {}

def safe_b64decode(s):
    if not s: return None
    try:
        if isinstance(s, str):
            if ',' in s and s.startswith('data:'): s = s.split(',', 1)[1]
            s = s.strip().replace('\n','').replace('\r','').replace(' ','')
        missing = len(s) % 4
        if missing: s += '=' * (4 - missing)
        return base64.b64decode(s)
    except Exception as e:
        print(f"[safe_b64decode] Erreur : {e}")
        return None

def strip_html(text):
    if not text: return ""
    return re.sub(r'<[^>]+>', '', str(text)).strip()

# ══════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════
if is_logged_in():
    with st.sidebar:
        st.markdown(
            f'''<div class="sb-logo">
            <img src="{LOGO_DATA_URI}" alt="logo"/>
            <div>
                <div class="sb-logo-name"><span>Pixel</span>Optimize</div>
                <div class="sb-logo-sub">Compression IA · Groq</div>
            </div></div>''',
            unsafe_allow_html=True
        )
        st.markdown('<div class="sb-section-lbl">Navigation</div>', unsafe_allow_html=True)
        nav_pages = [
            ("nav_home", "🏠  Accueil",    "accueil"),
            ("nav_comp", "🗜️  Compresser", "compress"),
            ("nav_dash", "📊  Dashboard",  "dashboard"),
            ("nav_hist", "🕒  Historique", "history"),
            ("nav_30",   "🖼️  30 Images",  "n8n"),
        ]
        for key, label, pg in nav_pages:
            if st.button(label, key=key, use_container_width=True):
                st.session_state["page"] = pg; st.rerun()

        st.markdown('<hr style="border:none;border-top:1px solid #E8E4F8;margin:12px 8px">', unsafe_allow_html=True)
        st.markdown('<div class="sb-section-lbl">Pipeline d\'agents</div>', unsafe_allow_html=True)
        for icon, name, role in [
            ("🔬", "Agent Analyste",    "Extraction des caractéristiques"),
            ("🧠", "Agent Décideur",    "Décision intelligente de compression"),
            ("⚖️", "Agent Comparateur", "Validation double LLM"),
            ("⚙️", "Agent Exécuteur",   "Compression du format"),
            ("📋", "Agent Rapporteur",  "SSIM · PSNR · MSE · τ% · Q/T"),
        ]:
            st.markdown(
                f'''<div class="sb-agent slide-in">
                <div class="sb-agent-icon">{icon}</div>
                <div><div class="sb-agent-name">{name}</div>
                <div class="sb-agent-who">{role}</div></div>
                </div>''',
                unsafe_allow_html=True
            )
        st.markdown('<hr style="border:none;border-top:1px solid #E8E4F8;margin:12px 8px">', unsafe_allow_html=True)
        if st.button("🚪 Déconnexion", key="logout_sidebar", use_container_width=True):
            logout()

# ══════════════════════════════════════════════════════
# NAVIGATION INVITÉ
# ══════════════════════════════════════════════════════
if is_guest():
    nav_col1, nav_col2, nav_col3 = st.columns(3)
    nav_items = [
        (nav_col1, "nav_g_home", "🏠 Accueil",    "accueil"),
        (nav_col2, "nav_g_comp", "🗜️ Compresser", "compress"),
        (nav_col3, "nav_g_30",   "🖼️ 30 Images",  "n8n"),
    ]
    for col, key, label, pg in nav_items:
        with col:
            if st.button(label, key=key, use_container_width=True):
                st.session_state["page"] = pg; st.rerun()
    st.markdown('<hr style="border:none;border-top:1px solid var(--border);margin:8px 0 20px">', unsafe_allow_html=True)

page = st.session_state["page"]

# ══════════════════════════════════════════════════════
# PIPELINE
# ══════════════════════════════════════════════════════
def run_pipeline(img_bytes, filename):
    img_b64 = base64.b64encode(img_bytes).decode()
    ph = st.empty()
    states = {
        "Agent Analyste":    "wait",
        "Agent Décideur":    "wait",
        "Agent Comparateur": "wait",
        "Agent Exécuteur":   "wait",
        "Agent Rapporteur":  "wait"
    }

    def show(s):
        icons = {"wait":"○","run":"◉","done":"●","error":"✕"}
        cls   = {"wait":"ag-wait","run":"ag-run","done":"ag-done","error":"ag-error"}
        badges = "".join(f'<span class="ag-badge {cls[v]}">{icons[v]} {k}</span>' for k,v in s.items())
        ph.markdown(f'<div class="ag-row">{badges}</div>', unsafe_allow_html=True)

    for agent in states: states[agent] = "run"
    show(states)

    try:
        response = requests.post(N8N_WEBHOOK_URL, json={"image_base64": img_b64, "filename": filename}, timeout=300)
        raw_text = response.text.strip()
        if not raw_text:
            st.error(f"n8n a renvoyé une réponse vide (HTTP {response.status_code})")
            for agent in states: states[agent] = "error"
            show(states); return None
        try:
            result = response.json()
        except Exception:
            st.error(f"n8n a renvoyé une réponse invalide : {raw_text[:300]}")
            for agent in states: states[agent] = "error"
            show(states); return None

        if isinstance(result, list): result = result[0] if result else {}
        if not isinstance(result, dict):
            st.error(f"Format inattendu depuis n8n : {type(result)}")
            for agent in states: states[agent] = "error"
            show(states); return None

        if result.get("status") != "success":
            for agent in states: states[agent] = "error"
            show(states); st.error(f"Erreur pipeline n8n : {result}"); return None

        for agent in states: states[agent] = "done"
        show(states)

        features         = safe_dict(result.get("features", {}))
        decision_init    = safe_dict(result.get("decision_initiale", {}))
        decision_fin     = safe_dict(result.get("decision_finale", {}))
        metrics          = safe_dict(result.get("metrics", {}))
        rapport          = safe_dict(result.get("rapport", {}))
        fichiers         = safe_dict(result.get("fichiers", {}))
        compressed_b64   = result.get("compressed_b64", "") or ""
        decision_changee = result.get("decision_changee", False)

        fmt = str(decision_fin.get("format_choisi", decision_fin.get("format", "WEBP"))).upper()
        try:
            qual_raw = decision_fin.get("qualite", decision_fin.get("quality", 85))
            qual = float(qual_raw)
            if qual <= 1.0:   # format décimal 0.9 → 90
                qual = int(qual * 100)
            else:
                qual = int(qual)
        except:
            qual = 85

        ssim_val = metrics.get("ssim", "?")
        gain_val = metrics.get("taux_compression_pct", "?")
        ev_val   = compute_eval(ssim_val)
        eff_val  = compute_compression_efficiency(gain_val)

        st.session_state["history"].insert(0, {
            "image": filename, "format": fmt, "ssim": ssim_val, "gain": gain_val,
            "eval": ev_val, "efficacite": eff_val, "time": datetime.now().strftime("%d/%m/%Y %H:%M"),
        })

        return {
            "filename": filename, "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "analyste": features, "decision_initiale": decision_init,
            "decision_finale": decision_fin, "decision_changee": decision_changee,
            "metrics": metrics, "compressed_b64": compressed_b64,
            "rapport": rapport, "fichiers": fichiers,
        }
    except Exception as e:
        for agent in states: states[agent] = "error"
        show(states); st.error(f"Erreur connexion n8n : {e}")
        import traceback; print(traceback.format_exc())
        return None

# ═══════════════════════════════════════════════════════
# ACCUEIL
# ═══════════════════════════════════════════════════════
if page == "accueil":
    st.markdown(
        f'''<div class="hero-wrap">
        <div class="hero-glow-1"></div><div class="hero-glow-2"></div>
        <div style="display:flex;align-items:center;gap:24px;margin-bottom:32px">
            <img src="{LOGO_DATA_URI}" style="width:72px;height:72px;border-radius:18px;box-shadow:0 4px 20px rgba(124,92,191,0.25);animation:fadeUp 0.5s both" alt="logo"/>
            <div>
                <div class="hero-chip">Système Multi-Agents · IA Générative</div>
            </div>
        </div>
        <h1 class="hero-title">Compression d\'images<br><span class="grad">intelligente & adaptative</span></h1>
        <p class="hero-sub">Un pipeline automatisé de 5 agents IA qui analyse chaque image, choisit la meilleure stratégie de compression et génère un rapport complet avec métriques de qualité.</p>
        <div class="hero-tags">
            <span class="hero-tag">PSNR · SSIM · MSE</span>
            <span class="hero-tag">JPEG · PNG · WebP · AVIF</span>
            <span class="hero-tag">Groq LLM (llama-3.3-70b)</span>
            <span class="hero-tag">Rapport automatique</span>
            <span class="hero-tag">5 agents autonomes</span>
        </div>
        <div class="hero-stats">
            <div class="hero-stat"><div class="hero-stat-val">5</div><div class="hero-stat-lbl">Agents IA</div></div>
            <div class="hero-stat"><div class="hero-stat-val">5</div><div class="hero-stat-lbl">Métriques</div></div>
            <div class="hero-stat"><div class="hero-stat-val">30+</div><div class="hero-stat-lbl">Images testées</div></div>
        </div></div>''',
        unsafe_allow_html=True
    )

    st.markdown('<div class="sec-hd">Pipeline de traitement</div>', unsafe_allow_html=True)
    cols5 = st.columns(5)
    for col, (icon, name, desc, role) in zip(cols5, [
        ("🔬", "Agent Analyste",    "Extrait les caractéristiques visuelles de l'image",  "Extraction"),
        ("🧠", "Agent Décideur",    "Groq llama-70b sélectionne le format optimal",        "Groq LLM"),
        ("⚖️", "Agent Comparateur", "2 LLM Groq comparent et valident la décision",        "Validation"),
        ("⚙️", "Agent Exécuteur",   "Applique la compression physique au format choisi",   "Compression"),
        ("📋", "Agent Rapporteur", "Calcule SSIM · PSNR · MSE · τ% · Q/T et génère le rapport complet", "Rapport"),
    ]):
        with col:
            st.markdown(
                f'''<div class="card anim-1" style="text-align:center;padding:24px 14px">
                <div style="font-size:1.9rem;margin-bottom:10px">{icon}</div>
                <div style="font-weight:700;font-size:.88rem;margin-bottom:5px">{name}</div>
                <div style="font-size:.72rem;color:var(--muted);line-height:1.5;margin-bottom:10px">{desc}</div>
                <span style="font-size:.66rem;background:rgba(124,92,191,0.08);color:var(--violet);padding:3px 10px;border-radius:100px;border:1px solid rgba(124,92,191,0.2)">{role}</span>
                </div>''',
                unsafe_allow_html=True
            )

    st.markdown('<br>', unsafe_allow_html=True)
    btn_cols = st.columns([1, 2, 1])
    with btn_cols[1]:
        if st.button("🚀  Commencer la compression →", use_container_width=True):
            st.session_state["page"] = "compress"; st.rerun()

    if is_guest():
        st.markdown('<br>', unsafe_allow_html=True)
        auth_cols = st.columns([1, 2, 1])
        with auth_cols[1]:
            st.markdown(
                '<div class="card" style="text-align:center;padding:28px">' +
                '<div style="font-size:1.4rem;margin-bottom:8px">🔐</div>' +
                '<div style="font-weight:700;margin-bottom:6px">Accédez à toutes les fonctionnalités</div>' +
                '<div style="font-size:.82rem;color:var(--muted);margin-bottom:16px">Dashboard, Historique et plus encore avec un compte gratuit.</div>' +
                '</div>',
                unsafe_allow_html=True
            )
            if st.button("Créer un compte gratuit →", use_container_width=True):
                st.session_state["show_auth_modal"] = True; st.rerun()

# ═══════════════════════════════════════════════════════
# COMPRESSER
# ═══════════════════════════════════════════════════════
elif page == "compress":
    st.markdown('<div class="sec-hd">Importer & compresser</div>', unsafe_allow_html=True)
    left, right = st.columns([1, 1.5], gap="large")

    with left:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("**📤 Image source**")
        uploaded = st.file_uploader("", type=["jpg","jpeg","png","webp","bmp","tiff"], label_visibility="collapsed")
        if uploaded:
            st.image(uploaded.getvalue(), use_container_width=True)
            st.markdown(f'<p style="font-size:.75rem;color:var(--muted);margin-top:8px">📁 {uploaded.name} · {uploaded.size/1024:.1f} KB</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("**🤖 Pipeline Multi-Agents (Groq)**")
        st.markdown('<p style="font-size:.8rem;color:var(--muted);margin-bottom:16px">Agent Analyste → Agent Décideur (Groq) → Agent Comparateur → Agent Exécuteur → Agent Rapporteur </p>', unsafe_allow_html=True)
        if uploaded:
            if st.button("▶  Lancer l'optimisation", use_container_width=True):
                with st.spinner("Pipeline en cours…"):
                    res = run_pipeline(uploaded.getvalue(), uploaded.name)
                if res:
                    st.session_state["results"]        = res
                    st.session_state["original_bytes"] = uploaded.getvalue()
                    st.success("✅ Pipeline terminé !")
        else:
            st.info("⬅ Importe une image pour commencer")
        st.markdown('</div>', unsafe_allow_html=True)

    if "results" in st.session_state and "original_bytes" in st.session_state:
        results    = st.session_state["results"]
        orig_bytes = st.session_state["original_bytes"]
        metrics    = results.get("metrics", {})
        features   = results.get("analyste", {})
        dec_init   = results.get("decision_initiale", {})
        dec_fin    = results.get("decision_finale", {})
        changed    = results.get("decision_changee", False)
        rapport    = results.get("rapport", {})
        comp_b64   = results.get("compressed_b64", "")
        fichiers   = results.get("fichiers", {})

        fmt  = dec_fin.get("format_choisi", dec_fin.get("format", "?"))
        qual = dec_fin.get("qualite", dec_fin.get("quality", "?"))

        st.markdown('<div class="sec-hd">Métriques de qualité</div>', unsafe_allow_html=True)
        t1,t2,t3,t4,t5 = st.columns(5)
        for col, (val, lbl, sub) in zip([t1,t2,t3,t4,t5], [
            (metrics.get("ssim","—"),                        "SSIM",  "Qualité visuelle"),
            (f"{metrics.get('psnr_db','—')} dB",            "PSNR",  "Fidélité signal"),
            (metrics.get("mse","—"),                          "MSE",   "Erreur pixel"),
            (f"{metrics.get('taux_compression_pct','—')}%", "Gain τ","Espace économisé"),
            (metrics.get("ratio_qualite_taille","—"),         "Q/T",   "Score composite"),
        ]):
            with col:
                st.markdown(f'<div class="m-tile"><div class="m-lbl">{lbl}</div><div class="m-val">{val}</div><div class="m-sub">{sub}</div></div>', unsafe_allow_html=True)

        ssim_raw    = metrics.get("ssim", 0)
        tau_raw     = metrics.get("taux_compression_pct", 0)
        ev_qualite  = metrics.get("evaluation_qualite", compute_eval(ssim_raw))
        ev_compress = metrics.get("evaluation_compression", compute_compression_efficiency(tau_raw))
        eff_cls     = efficiency_badge_class(ev_compress)
        ev_color    = "#16A34A" if ev_qualite == "Excellent" else "#E5A800" if ev_qualite in ("Bon","Acceptable") else "#EF4444"

        try: tau_float = float(tau_raw or 0)
        except: tau_float = 0

        # ✅ warn_bar HORS du f-string pour éviter HTML cassé
        warn_bar = ('<br><span style="font-size:.72rem;color:#B45309"> ⚠️ Gain faible · envisager qualité plus basse</span>'
                    if tau_float < 20 else '')

        # ✅ Les 2 cartes même style, même hauteur fixe
        card_style = (
            "background:white;border:1px solid var(--border);border-radius:14px;"
            "padding:20px 24px;box-shadow:0 2px 12px var(--shadow);"
            "height:90px;display:flex;flex-direction:column;justify-content:center;"
        )
        col_q, col_e = st.columns(2)
        with col_q:
            st.markdown(
                f'''<div style="{card_style}">
                <span style="font-size:.65rem;color:var(--muted);text-transform:uppercase;letter-spacing:1.5px;font-weight:700">Qualité visuelle (SSIM)</span>
                <div style="font-weight:800;font-size:1.4rem;color:{ev_color};margin-top:6px">{ev_qualite}</div>
                </div>''',
                unsafe_allow_html=True
            )
        with col_e:
            st.markdown(
                f'''<div style="{card_style}">
                <span style="font-size:.65rem;color:var(--muted);text-transform:uppercase;letter-spacing:1.5px;font-weight:700">Efficacité compression (τ)</span>
                <div style="margin-top:6px"><span class="{eff_cls}">{ev_compress} — {tau_raw}%</span>{warn_bar}</div>
                </div>''',
                unsafe_allow_html=True
            )

        st.markdown('<div class="sec-hd">Résultat visuel</div>', unsafe_allow_html=True)
        ca, cb = st.columns(2)
        with ca:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("**Originale**")
            st.image(orig_bytes, use_container_width=True)
            st.markdown(f'<p style="font-size:.75rem;color:var(--muted);margin-top:6px">{metrics.get("original_size_kb","?")} KB</p>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with cb:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            if changed:
                init_fmt = dec_init.get("format_choisi", dec_init.get("format","?"))
                st.markdown(f'<span class="ch-badge">⚡ {init_fmt} → {fmt}</span>', unsafe_allow_html=True)
            st.markdown(f"**Compressée — {fmt} q={qual}**")
            if comp_b64:
                comp_bytes = safe_b64decode(comp_b64)
                if comp_bytes:
                    st.image(comp_bytes, use_container_width=True)
                    st.markdown(
                        f'''<p style="font-size:.75rem;color:#16A34A;margin-top:6px">
                        ▼ {metrics.get("compressed_size_kb","?")} KB · économie {metrics.get("taux_compression_pct","?")}%
                        </p>''', unsafe_allow_html=True
                    )
                    fmt_ext   = {"JPEG":"jpg","PNG":"png","WEBP":"webp","JPEG2000":"jp2"}.get(str(fmt).upper(),"webp")
                    base_name = os.path.splitext(results.get("filename","image"))[0]
                    rj = json.dumps(
                        {"image":results.get("filename"),"analyse":features,"decision":dec_fin,"metriques":metrics,"rapport":rapport},
                        indent=2, ensure_ascii=False
                    ).encode("utf-8")
                    d1,d2,d3 = st.columns(3)
                    d1.download_button("⬇ Image", comp_bytes, file_name=f"{base_name}.{fmt_ext}", use_container_width=True)
                    d2.download_button("⬇ JSON",  rj, file_name=f"{base_name}_rapport.json", mime="application/json", use_container_width=True)
                    zb = io.BytesIO()
                    with zipfile.ZipFile(zb,"w",zipfile.ZIP_DEFLATED) as zf:
                        zf.writestr(f"{base_name}.{fmt_ext}", comp_bytes)
                        zf.writestr(f"{base_name}_rapport.json", rj)
                    zb.seek(0)
                    d3.download_button("⬇ ZIP", zb, file_name=f"{base_name}_pack.zip", mime="application/zip", use_container_width=True)
                else:
                    st.warning("⚠️ Image compressée non disponible (erreur décodage base64)")
            else:
                st.info("Image compressée non reçue depuis n8n")
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="sec-hd">Rapport par agent</div>', unsafe_allow_html=True)

        with st.expander("🔬 Agent Analyste — Extraction des caractéristiques"):
            feat_data = features.get("features", features)
            meta  = feat_data.get("metadonnees", features.get("metadonnees", {}))
            stats = feat_data.get("features_statistiques", features.get("features_statistiques", {}))
            cont  = feat_data.get("contours", features.get("contours", {}))
            ocr   = feat_data.get("ocr", features.get("ocr", {}))

            type_img    = feat_data.get("type_image", features.get("type_image", "?"))
            taille_kb   = feat_data.get("taille_kb",  features.get("taille_kb",  meta.get("taille_kb","?")))
            fmt_orig    = feat_data.get("format_original", features.get("format_original", meta.get("format","?")))
            largeur     = meta.get("largeur", feat_data.get("resolution","?"))
            hauteur     = meta.get("hauteur","?")
            entropie    = stats.get("entropy", feat_data.get("entropy", feat_data.get("entropie","?")))
            variance    = stats.get("variance","?")
            nb_contours = cont.get("nombre_contours", feat_data.get("densite_contours","?"))
            has_text    = ocr.get("contient_texte", feat_data.get("contient_texte", False))

            c1, c2 = st.columns(2)
            c1.markdown(f'<div class="rpt"><b>Type</b> <span class="tag">{type_img}</span><br><b>Résolution</b> {largeur}×{hauteur} px<br><b>Format</b> {fmt_orig}<br><b>Taille</b> {taille_kb} KB</div>', unsafe_allow_html=True)
            c2.markdown(f'<div class="rpt"><b>Entropie</b> {entropie}<br><b>Variance</b> {variance}<br><b>Contours</b> {nb_contours}<br><b>Texte</b> {"✅" if has_text else "❌"}</div>', unsafe_allow_html=True)

        with st.expander("🧠 Agent Décideur — Décision intelligente de compression"):
            raison_init = strip_html(dec_init.get("raison", "") or dec_init.get("justification",
                                                                                "") or "Décision basée sur les caractéristiques visuelles de l'image")
            source_init = strip_html(dec_init.get("cas_usage", "") or dec_init.get("source", "") or "Agent Décideur")
            st.markdown(
                f'''<div class="rpt">
                <b>Format choisi</b> <span class="tag">{dec_init.get("format_choisi", dec_init.get("format", "?"))}</span> q={dec_init.get("qualite", "?")}<br>
                <b>Raison</b> {raison_init}<br>
                <b>Cas usage</b> {source_init}
                </div>''', unsafe_allow_html=True
            )

        with st.expander("⚖️ Agent Comparateur — Validation double LLM"):
            if changed:
                st.info(f"Décision corrigée : {dec_init.get('format_choisi','?')} → **{fmt}**")
            else:
                st.success(f"Décision confirmée : {fmt} q={qual}")
            methode    = strip_html(dec_fin.get("methode_selection","") or "Sélection par score de confiance")
            raison_fin = strip_html(dec_fin.get("raison","") or dec_fin.get("justification","") or "Les deux modèles convergent vers ce format pour ce type d'image")
            st.markdown(
                f'''<div class="rpt">
                <b>Méthode sélection</b> {methode}<br>
                <b>Format final</b> <span class="tag">{fmt}</span> q={qual}<br>
                <b>Raison</b> {raison_fin}
                </div>''', unsafe_allow_html=True
            )

        with st.expander("⚙️ Agent Exécuteur — Compression du format"):
            adj = metrics.get("quality_adjusted", False)
            st.markdown(
                f'''<div class="rpt">
                <b>Rôle</b> Compression physique de l'image uniquement<br>
                <b>Format appliqué</b> <span class="tag">{metrics.get("format_used","?")}</span><br>
                <b>Qualité</b> {metrics.get("quality_used","?")} {"(ajustée automatiquement)" if adj else ""}<br>
                <b>Réduction taille</b> {metrics.get("original_size_kb","?")} KB → {metrics.get("compressed_size_kb","?")} KB (ratio {metrics.get("compression_ratio","?")}×)
                </div>''', unsafe_allow_html=True
            )
            m1, m2 = st.columns(2)
            m1.metric("Taille originale", f"{metrics.get('original_size_kb','?')} KB")
            m2.metric("Taille compressée", f"{metrics.get('compressed_size_kb','?')} KB",
                      delta=f"-{metrics.get('taux_compression_pct','?')}%")

        with st.expander("📋 Agent Rapporteur — SSIM · PSNR · MSE · τ% · Q/T", expanded=True):
            rc_data      = rapport.get("rapport_compression", {})
            metriques_rc = rc_data.get("metriques_qualite", {})
            ia_ok        = rc_data.get("decision_ia", {}).get("decision_pertinente", False)

            # ✅ Nettoyage agressif HTML résiduel de n8n
            concl_raw = rc_data.get("conclusion", "")
            concl = re.sub(r'<[^>]+>', '', str(concl_raw)).strip()

            ev_q = metriques_rc.get("evaluation_qualite_visuelle",
                   metrics.get("evaluation_qualite", compute_eval(metrics.get("ssim", 0))))
            ev_c = metriques_rc.get("evaluation_efficacite_compression",
                   metrics.get("evaluation_compression", compute_compression_efficiency(metrics.get("taux_compression_pct", 0))))

            if not concl:
                tau_c = metrics.get("taux_compression_pct", "?")
                concl = (f"Qualité visuelle : {ev_q} (SSIM={metrics.get('ssim','?')}, PSNR={metrics.get('psnr_db','?')} dB). "
                         f"Efficacité compression : {ev_c} — {tau_c}% économisé.")

            ev_q_color = "#16A34A" if ev_q == "Excellent" else "#E5A800" if ev_q in ("Bon","Acceptable") else "#EF4444"
            ev_c_class = efficiency_badge_class(ev_c)
            tau_display = metrics.get("taux_compression_pct", "?")

            try: tau_d_float = float(tau_display or 0)
            except: tau_d_float = 0

            # ✅ warn_html HORS du f-string
            warn_html = ('<br><span style="font-size:.78rem;color:#B45309">⚠️ Gain faible : envisager une qualité plus basse.</span>'
                         if tau_d_float < 20 else '')

            ia_txt = "✅ Oui" if ia_ok else "⚠️ À revoir"

            st.markdown(
                f'''<div class="rpt">
                <b>Qualité visuelle (SSIM)</b> <span style="color:{ev_q_color};font-weight:700">{ev_q}</span><br>
                <b>SSIM</b> {metrics.get("ssim", "?")} · <b>PSNR</b> {metrics.get("psnr_db", "?")} dB · <b>MSE</b> {metrics.get("mse", "?")}<br>
                <b>Taux compression (τ%)</b> <span class="{ev_c_class}">{ev_compress} — {tau_display}%</span>{warn_html}<br>
                <b>Ratio Qualité/Taille (Q/T)</b> {metrics.get("ratio_qualite_taille", "?")}<br>
                <b>Décision IA pertinente</b> {ia_txt}<br>
                <b>Conclusion</b> {concl}
                </div>''', unsafe_allow_html=True
            )

            # Graphiques centrés et réduits
            if fichiers.get("gauge") or fichiers.get("metrics_chart"):
                if fichiers.get("gauge") and fichiers.get("metrics_chart"):
                    _, col_g, col_m, _ = st.columns([0.5, 4, 4, 0.5])
                    col_g.image(fichiers["gauge"], caption="Jauge SSIM", use_container_width=True)
                    col_m.image(fichiers["metrics_chart"], caption="Comparaison stratégies", use_container_width=True)
                elif fichiers.get("metrics_chart"):
                    _, mid, _ = st.columns([1, 6, 1])
                    with mid:
                        st.image(fichiers["metrics_chart"], caption="Comparaison stratégies", use_container_width=True)
                elif fichiers.get("gauge"):
                    _, mid, _ = st.columns([1, 6, 1])
                    with mid:
                        st.image(fichiers["gauge"], caption="Jauge SSIM", use_container_width=True)

        with st.expander("{ } JSON brut"):
            st.json(results)

# ═══════════════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════════════
elif page == "dashboard":
    if is_guest():
        st.markdown(
            '<div class="card" style="text-align:center;padding:60px">' +
            '<div style="font-size:2rem;margin-bottom:12px">🔒</div>' +
            '<div style="font-weight:700;font-size:1.1rem;margin-bottom:8px">Accès réservé aux comptes</div>' +
            '<div style="color:var(--muted);font-size:.85rem">Connectez-vous pour accéder au dashboard et à vos statistiques.</div>' +
            '</div>', unsafe_allow_html=True)
        if st.button("🔐 Se connecter"): st.session_state["show_auth_modal"] = True
        st.stop()

    st.markdown('<div class="sec-hd">Dashboard · Vue d\'ensemble</div>', unsafe_allow_html=True)
    hist      = st.session_state.get("history", [])
    total     = len(hist)
    excellent = sum(1 for h in hist if str(h.get("eval","")) == "Excellent")
    bon       = sum(1 for h in hist if str(h.get("eval","")) == "Bon")
    gains     = []
    for h in hist:
        try:
            g = h.get("gain","")
            if g and str(g) not in ("","?"): gains.append(float(g))
        except: pass
    avg_gain = round(sum(gains)/max(len(gains),1), 1)

    c1,c2,c3,c4 = st.columns(4)
    for col, (icon, lbl, val, sub, bg) in zip([c1,c2,c3,c4], [
        ("🗜️","Total traité",  str(total),     "images",    "rgba(124,92,191,0.1)"),
        ("✅","Excellent",     str(excellent), "qualité",   "rgba(34,197,94,0.1)"),
        ("📊","Bon",           str(bon),       "qualité",   "rgba(229,168,0,0.1)"),
        ("💾","Gain moyen τ",  f"{avg_gain}%", "économisé", "rgba(124,92,191,0.1)"),
    ]):
        with col:
            st.markdown(
                f'''<div class="dash-card anim-1">
                <div class="dash-card-icon" style="background:{bg}">{icon}</div>
                <div class="dash-card-val">{val}</div>
                <div class="dash-card-lbl">{lbl} · {sub}</div>
                </div>''', unsafe_allow_html=True
            )

    if hist:
        df_h = pd.DataFrame(hist)
        df_h["ssim_f"] = pd.to_numeric(df_h["ssim"], errors='coerce')
        df_h["gain_f"] = pd.to_numeric(df_h["gain"], errors='coerce')
        st.markdown('<div class="sec-hd">Activité récente</div>', unsafe_allow_html=True)
        g1, g2 = st.columns(2)
        with g1:
            sv = df_h["ssim_f"].fillna(0).tolist()[::-1]
            nm = df_h["image"].tolist()[::-1]
            bc = ["#22C55E" if v>0.95 else "#E5A800" if v>0.9 else "#EF4444" for v in sv]
            fig = go.Figure(go.Bar(x=nm, y=sv, marker_color=bc, text=[f'{v:.3f}' for v in sv], textposition='outside', textfont=dict(color='#1A1F2E',size=10)))
            fig.update_layout(title="SSIM par image (qualité visuelle)", height=280, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#1A1F2E',family='Plus Jakarta Sans'), xaxis=dict(tickangle=-30,gridcolor='#F0EDE8'), yaxis=dict(range=[0,1.15],gridcolor='#F0EDE8'), margin=dict(t=32,b=0,l=0,r=0))
            st.plotly_chart(fig, use_container_width=True)
        with g2:
            gv = df_h["gain_f"].fillna(0).tolist()[::-1]
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=list(range(len(gv))), y=gv, fill='tozeroy', fillcolor='rgba(124,92,191,0.1)', line=dict(color='#7C5CBF',width=2), mode='lines+markers', marker=dict(color='#E8559A',size=7)))
            fig2.update_layout(title="Taux compression τ% (efficacité)", height=280, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#1A1F2E',family='Plus Jakarta Sans'), xaxis=dict(gridcolor='#F0EDE8'), yaxis=dict(gridcolor='#F0EDE8'), margin=dict(t=32,b=0,l=0,r=0))
            st.plotly_chart(fig2, use_container_width=True)
        g3, g4 = st.columns(2)
        with g3:
            fc = pd.Series([h.get("format","?") for h in hist]).value_counts()
            fig3 = go.Figure(go.Pie(labels=fc.index.tolist(), values=fc.values.tolist(), hole=0.55, marker_colors=['#7C5CBF','#E8559A','#4AAFCA','#E5A800']))
            fig3.update_layout(title="Formats utilisés", height=260, paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#1A1F2E',family='Plus Jakarta Sans'), margin=dict(t=32,b=0,l=0,r=0))
            st.plotly_chart(fig3, use_container_width=True)
        with g4:
            ec  = pd.Series([h.get("eval","?") for h in hist]).value_counts()
            ecm = {"Excellent":"#22C55E","Bon":"#E5A800","Acceptable":"#F97316","Dégradé":"#EF4444","?":"#9CA3AF"}
            bc2 = [ecm.get(e,"#9CA3AF") for e in ec.index.tolist()]
            fig4 = go.Figure(go.Bar(x=ec.index.tolist(), y=ec.values.tolist(), marker_color=bc2, text=ec.values.tolist(), textposition='outside', textfont=dict(color='#1A1F2E')))
            fig4.update_layout(title="Évaluation qualité visuelle (SSIM)", height=260, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#1A1F2E',family='Plus Jakarta Sans'), xaxis=dict(gridcolor='#F0EDE8'), yaxis=dict(gridcolor='#F0EDE8'), margin=dict(t=32,b=0,l=0,r=0))
            st.plotly_chart(fig4, use_container_width=True)
    else:
        st.markdown('<div class="card" style="text-align:center;padding:60px;color:var(--muted)">Aucune donnée · Compresse d\'abord des images</div>', unsafe_allow_html=True)
        if st.button("→ Aller à Compresser"): st.session_state["page"] = "compress"; st.rerun()

# ═══════════════════════════════════════════════════════
# HISTORIQUE
# ═══════════════════════════════════════════════════════
elif page == "history":
    if is_guest():
        st.markdown(
            '<div class="card" style="text-align:center;padding:60px">' +
            '<div style="font-size:2rem;margin-bottom:12px">🔒</div>' +
            '<div style="font-weight:700;font-size:1.1rem;margin-bottom:8px">Accès réservé aux comptes</div>' +
            '<div style="color:var(--muted);font-size:.85rem">Connectez-vous pour consulter votre historique de compressions.</div>' +
            '</div>', unsafe_allow_html=True)
        if st.button("🔐 Se connecter"): st.session_state["show_auth_modal"] = True
        st.stop()

    st.markdown('<div class="sec-hd">Historique des compressions</div>', unsafe_allow_html=True)
    hist = st.session_state.get("history", [])
    if hist:
        st.markdown(f'<p style="font-size:.8rem;color:var(--muted);margin-bottom:16px">{len(hist)} compression(s) cette session</p>', unsafe_allow_html=True)
        header    = '<div class="hist-wrap"><div class="hist-row hist-header" style="grid-template-columns:2fr 1fr 1fr 1fr 1fr 1fr 80px"><span>Image</span><span>Format</span><span>SSIM</span><span>Gain τ</span><span>Qualité</span><span>Efficacité</span><span>Heure</span></div>'
        rows_html = ""
        for h in hist:
            ev  = str(h.get("eval","?"))
            eff = str(h.get("efficacite","?"))
            ec  = "#16A34A" if ev=="Excellent" else "#E5A800" if ev=="Bon" else "#EF4444"
            ef_cls = efficiency_badge_class(eff)
            rows_html += (
                f'<div class="hist-row" style="grid-template-columns:2fr 1fr 1fr 1fr 1fr 1fr 80px">' +
                f'<span style="font-weight:600">{h.get("image","?")}</span>' +
                f'<span><span class="tag">{h.get("format","?")}</span></span>' +
                f'<span style="font-family:JetBrains Mono,monospace">{h.get("ssim","?")}</span>' +
                f'<span style="color:#16A34A;font-weight:600">{h.get("gain","?")}%</span>' +
                f'<span style="color:{ec};font-weight:600">{ev}</span>' +
                f'<span><span class="{ef_cls}">{eff}</span></span>' +
                f'<span style="color:var(--muted);font-size:.73rem">{h.get("time","")}</span>' +
                f'</div>'
            )
        st.markdown(header + rows_html + '</div>', unsafe_allow_html=True)
        st.markdown('<br>', unsafe_allow_html=True)
        if st.button("🗑  Effacer l\'historique"): st.session_state["history"] = []; st.rerun()
    else:
        st.markdown('<div class="card" style="text-align:center;padding:60px;color:var(--muted)">Aucun historique · Compresse d\'abord une image</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════
# 30 IMAGES
# ═══════════════════════════════════════════════════════
elif page == "n8n":
    st.markdown('<div class="sec-hd">Résultats · 30 images via n8n</div>', unsafe_allow_html=True)
    DATABASE_DIR = BASE_DIR / "database-projet"
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)
    c1, c2 = st.columns([3, 1])
    with c2:
        if st.button("▶ Lancer les tests", use_container_width=True):
            import glob as gb
            extensions = ['jpg', 'jpeg', 'png', 'bmp', 'webp', 'tiff']
            images = []; seen = set()
            for ext in extensions:
                for p in gb.glob(os.path.join(DATABASE_DIR, '**', f'*.{ext}'), recursive=True):
                    if p.lower() not in seen: seen.add(p.lower()); images.append(p)
                for p in gb.glob(os.path.join(DATABASE_DIR, '**', f'*.{ext.upper()}'), recursive=True):
                    if p.lower() not in seen: seen.add(p.lower()); images.append(p)

            st.info(f"📁 {len(images)} images trouvées — envoi vers n8n...")
            resultats = []
            progress = st.progress(0)
            status_text = st.empty()

            # ✅ Chrono réel
            debut_total = time.time()

            for i, img_path in enumerate(images):
                nom = os.path.basename(img_path)
                categorie = os.path.basename(os.path.dirname(img_path))
                status_text.text(f"⚡ Traitement {i + 1}/{len(images)} : {nom}")
                try:
                    with open(img_path, 'rb') as f:
                        img_bytes = f.read()
                    img_b64 = base64.b64encode(img_bytes).decode()
                    N8N_PROD_URL = "http://localhost:5678/webhook/compression-pipeline"

                    response = requests.post(
                        N8N_PROD_URL,
                        json={"image_base64": img_b64, "filename": nom, "categorie": categorie},
                        timeout=300
                    )

                    # ✅ Vérification réponse vide
                    raw_text = response.text.strip()
                    if not raw_text:
                        raise ValueError(f"Réponse vide HTTP {response.status_code}")

                    # ✅ Parse JSON sécurisé
                    try:
                        result = response.json()
                    except Exception:
                        raise ValueError(f"Non-JSON: {raw_text[:150]}")

                    if isinstance(result, list):
                        result = result[0] if result else {}
                    if not isinstance(result, dict):
                        result = {}

                    # ✅ Extraction sécurisée
                    metrics_n = safe_dict(result.get("metrics", {}))
                    dec_fin_n = safe_dict(result.get("decision_finale", {}))
                    fmt_n  = str(dec_fin_n.get("format_choisi", "?")).upper()
                    tau_n  = metrics_n.get("taux_compression_pct", "?")
                    ssim_n = metrics_n.get("ssim", "?")
                    statut = "✅" if result.get("status") == "success" else "❌"

                    resultats.append({
                        "image":              nom,
                        "categorie":          categorie,
                        "decision_finale":    fmt_n,
                        "ssim":               ssim_n,
                        "psnr_db":            metrics_n.get("psnr_db", "?"),
                        "mse":                metrics_n.get("mse", "?"),
                        "tau":                tau_n,
                        "qualite_visuelle":   metrics_n.get("evaluation_qualite", compute_eval(ssim_n)),
                        "efficacite_compress":metrics_n.get("evaluation_compression", compute_compression_efficiency(tau_n)),
                        "statut":             statut,
                        "erreur":             "",
                    })

                except Exception as e:
                    resultats.append({
                        "image":               nom,
                        "categorie":           categorie,
                        "decision_finale":     "—",
                        "ssim":                "—",
                        "psnr_db":             "—",
                        "mse":                 "—",
                        "tau":                 "—",
                        "qualite_visuelle":    "—",
                        "efficacite_compress": "—",
                        "statut":              "❌",
                        "erreur":              str(e)[:120],
                    })

                progress.progress((i + 1) / len(images))

            # ✅ Durée réelle
            duree_sec = round(time.time() - debut_total, 1)
            status_text.text(f"✅ Terminé en {duree_sec}s !")

            resume = {
                "total":      len(images),
                "succes":     sum(1 for r in resultats if r.get("statut") == "✅"),
                "erreurs":    sum(1 for r in resultats if r.get("statut") == "❌"),
                "duree_sec":  duree_sec,
                "resultats":  resultats,
            }
            os.makedirs(RAPPORTS_DIR, exist_ok=True)
            with open(os.path.join(RAPPORTS_DIR, "resume_global.json"), 'w', encoding='utf-8') as f:
                json.dump(resume, f, indent=2, ensure_ascii=False)
            st.success(f"✅ {resume['succes']}/{len(images)} images traitées en {duree_sec}s !")
            st.rerun()

    resume_path = os.path.join(RAPPORTS_DIR, "resume_global.json")
    if not os.path.exists(resume_path):
        st.markdown('<div class="card" style="text-align:center;padding:60px;color:var(--muted)">Aucun résultat · Lance les tests d\'abord</div>', unsafe_allow_html=True)
    else:
        with open(resume_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        m1, m2, m3, m4 = st.columns(4)
        for col, (lbl, val, sub) in zip([m1, m2, m3, m4], [
            ("Total",   data.get("total",  0),           "images"),
            ("Succès",  data.get("succes", 0),           "OK"),
            ("Erreurs", data.get("erreurs",0),           "failed"),
            ("Durée",   f"{data.get('duree_sec',0)}s",   "elapsed"),
        ]):
            with col:
                st.markdown(f'<div class="m-tile"><div class="m-lbl">{lbl}</div><div class="m-val">{val}</div><div class="m-sub">{sub}</div></div>', unsafe_allow_html=True)

        if data.get("resultats"):
            df = pd.DataFrame(data["resultats"])
            df["ssim_num"] = pd.to_numeric(df["ssim"], errors='coerce')
            df["tau_num"]  = pd.to_numeric(df["tau"],  errors='coerce')

            st.markdown('<div class="sec-hd">Tableau détaillé</div>', unsafe_allow_html=True)

            # ✅ Afficher erreurs détaillées
            nb_err = int(data.get("erreurs", 0))
            if nb_err > 0:
                df_err = df[df["statut"] == "❌"]
                with st.expander(f"⚠️ {nb_err} erreur(s) — voir détails", expanded=False):
                    st.dataframe(
                        df_err[["image","categorie","erreur"]],
                        use_container_width=True, hide_index=True
                    )

            st.dataframe(
                df.drop(columns=["ssim_num","tau_num","erreur"], errors="ignore"),
                use_container_width=True, hide_index=True
            )

            # ✅ Graphiques uniquement sur les succès avec données valides
            df_ok = df[df["ssim_num"].notna() & df["tau_num"].notna()].copy()

            g1, g2 = st.columns(2)
            with g1:
                if "categorie" in df_ok.columns and len(df_ok) > 0:
                    ssim_mean = df_ok.groupby("categorie")["ssim_num"].mean().reset_index()
                    ssim_mean.columns = ["categorie", "ssim_moyen"]
                    ssim_mean["ssim_moyen"] = ssim_mean["ssim_moyen"].round(4)
                    colors = ["#7C5CBF","#E8559A","#4AAFCA","#E5A800","#22C55E","#F97316"]
                    fig = go.Figure(go.Bar(
                        x=ssim_mean["categorie"],
                        y=ssim_mean["ssim_moyen"],
                        marker_color=colors[:len(ssim_mean)],
                        text=ssim_mean["ssim_moyen"].astype(str),
                        textposition='outside',
                        textfont=dict(color='#1A1F2E', size=11)
                    ))
                    fig.update_layout(
                        title="SSIM moyen par catégorie",
                        height=320,
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='#1A1F2E', family='Plus Jakarta Sans'),
                        xaxis=dict(gridcolor='#F0EDE8'),
                        yaxis=dict(range=[0, 1.12], gridcolor='#F0EDE8', title="SSIM moyen"),
                        margin=dict(t=40, b=20, l=20, r=20)
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Pas assez de données SSIM valides pour le graphique.")

            with g2:
                if "categorie" in df_ok.columns and len(df_ok) > 0:
                    tau_mean = df_ok.groupby("categorie")["tau_num"].mean().reset_index()
                    tau_mean.columns = ["categorie", "tau_moyen"]
                    tau_mean["tau_moyen"] = tau_mean["tau_moyen"].round(1)
                    max_tau = float(tau_mean["tau_moyen"].max()) if len(tau_mean) > 0 else 10
                    colors = ["#7C5CBF","#E8559A","#4AAFCA","#E5A800","#22C55E","#F97316"]
                    fig2 = go.Figure(go.Bar(
                        x=tau_mean["categorie"],
                        y=tau_mean["tau_moyen"],
                        marker_color=colors[:len(tau_mean)],
                        text=(tau_mean["tau_moyen"].astype(str) + "%"),
                        textposition='outside',
                        textfont=dict(color='#1A1F2E', size=11)
                    ))
                    fig2.update_layout(
                        title="Taux compression moyen τ% par catégorie",
                        height=320,
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='#1A1F2E', family='Plus Jakarta Sans'),
                        xaxis=dict(gridcolor='#F0EDE8'),
                        yaxis=dict(range=[0, max_tau * 1.2], gridcolor='#F0EDE8', title="τ% moyen"),
                        margin=dict(t=40, b=20, l=20, r=20)
                    )
                    st.plotly_chart(fig2, use_container_width=True)
                else:
                    st.info("Pas assez de données τ% valides pour le graphique.")

            if st.button("🔄 Rafraîchir"): st.rerun()

st.markdown(
    '<p style="text-align:center;color:var(--muted);font-size:.7rem;margin-top:40px;border-top:1px solid var(--border);padding-top:20px">' +
    '© 2025-2026 · Équipe 4 · Université Hassan II · FSTM · <b>PixelOptimize</b></p>',
    unsafe_allow_html=True
)