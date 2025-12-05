import streamlit as st
import yfinance as yf
from transformers import pipeline
from deep_translator import GoogleTranslator
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import time
from datetime import datetime, timedelta
import pytz
import hashlib
import json
import os

# ==========================================
# 1. CONFIGURACIÓN DEL SISTEMA (ULTRA WIDE)
# ==========================================
st.set_page_config(
    page_title="TITANIUM TERMINAL | V5 ELITE", 
    page_icon="💠", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 2. INYECCIÓN CSS (INTERFAZ "GLASSMORPHISM")
# ==========================================
# URL de fondo: Un paisaje urbano financiero oscuro y abstracto
BACKGROUND_URL = "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?q=80&w=2070&auto=format&fit=crop"

st.markdown(f"""
<style>
    /* IMPORTAR FUENTES */
    @import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@300;500;700&family=JetBrains+Mono:wght@400;700&display=swap');

    /* FONDO GENERAL CON OVERLAY OSCURO */
    .stApp {{
        background-image: url("{BACKGROUND_URL}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    
    /* CAPA OSCURA PARA LEIBILIDAD */
    .stApp::before {{
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(5, 5, 10, 0.90); /* 90% Oscuridad */
        z-index: -1;
    }}

    /* FUENTES GLOBALES */
    html, body, [class*="css"] {{
        font-family: 'Rajdhani', sans-serif;
        color: #e0e0e0;
    }}
    
    h1, h2, h3 {{
        font-family: 'Rajdhani', sans-serif;
        text-transform: uppercase;
        letter-spacing: 2px;
        font-weight: 700;
    }}

    /* BARRA LATERAL ESTILO CRISTAL */
    section[data-testid="stSidebar"] {{
        background-color: rgba(15, 15, 20, 0.85);
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }}
    
    /* INPUTS ESTILO TERMINAL */
    .stTextInput>div>div>input {{
        background-color: rgba(0, 0, 0, 0.5);
        color: #00d4ff;
        border: 1px solid #333;
        font-family: 'JetBrains Mono', monospace;
        border-radius: 0px;
    }}
    .stTextInput>div>div>input:focus {{
        border-color: #00d4ff;
        box-shadow: 0 0 10px rgba(0, 212, 255, 0.3);
    }}

    /* TARJETAS MÉTRICAS (KPIs) */
    div[data-testid="stMetric"] {{
        background: linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.01) 100%);
        backdrop-filter: blur(5px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        transition: transform 0.2s;
    }}
    div[data-testid="stMetric"]:hover {{
        border-color: #00d4ff;
        transform: translateY(-2px);
    }}
    div[data-testid="stMetric"] label {{
        color: #888;
        font-size: 0.8rem;
        font-family: 'JetBrains Mono', monospace;
    }}
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {{
        font-family: 'Rajdhani', sans-serif;
        font-size: 1.8rem;
        font-weight: 700;
        color: #fff;
        text-shadow: 0 0 10px rgba(255,255,255,0.2);
    }}

    /* BOTONES */
    .stButton>button {{
        background: linear-gradient(90deg, #1a1a1a 0%, #222 100%);
        color: #bbb;
        border: 1px solid #444;
        border-radius: 4px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.3s;
    }}
    .stButton>button:hover {{
        border-color: #00d4ff;
        color: #00d4ff;
        box-shadow: 0 0 15px rgba(0, 212, 255, 0.2);
    }}

    /* TABS */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 20px;
        background-color: transparent;
        padding-bottom: 10px;
        border-bottom: 1px solid rgba(255,255,255,0.1);
    }}
    .stTabs [data-baseweb="tab"] {{
        height: 40px;
        background-color: transparent;
        border: none;
        color: #666;
        font-family: 'Rajdhani', sans-serif;
        font-weight: 600;
        font-size: 1.1rem;
    }}
    .stTabs [aria-selected="true"] {{
        color: #00d4ff;
        border-bottom: 2px solid #00d4ff;
    }}
    
    /* LOGS Y TEXT AREAS */
    .stTextArea textarea {{
        background-color: #0a0a0a;
        color: #00ff41;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
        border: 1px solid #333;
    }}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. SISTEMA DE SEGURIDAD & PERSISTENCIA
# ==========================================
DB_FILE = 'users_db.json'

def load_users():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    else:
        default_db = {'admin': hashlib.sha256(str.encode('admin123')).hexdigest()}
        with open(DB_FILE, 'w') as f:
            json.dump(default_db, f)
        return default_db

def save_users(db):
    with open(DB_FILE, 'w') as f:
        json.dump(db, f)

def check_hashes(password, hashed_text):
    return hashlib.sha256(str.encode(password)).hexdigest() == hashed_text

if 'db_users' not in st.session_state:
    st.session_state['db_users'] = load_users()
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'user_current' not in st.session_state:
    st.session_state['user_current'] = None

# ==========================================
# 4. PANTALLA DE ACCESO (LOGIN)
# ==========================================
def login_screen():
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        # Logo o Título Estilizado
        st.markdown(
            """
            <div style='text-align: center; margin-bottom: 20px; padding: 40px; border: 1px solid rgba(0, 212, 255, 0.3); background: rgba(0,0,0,0.6); backdrop-filter: blur(10px); border-radius: 10px;'>
                <h1 style='font-family: Rajdhani; color: #fff; font-size: 4rem; margin:0; text-shadow: 0 0 20px rgba(0, 212, 255, 0.5);'>TITANIUM</h1>
                <p style='color: #00d4ff; letter-spacing: 5px; font-size: 1rem; font-family: JetBrains Mono;'>TERMINAL FINANCIERA V5.0</p>
            </div>
            """, unsafe_allow_html=True
        )
        
        tab_login, tab_signup = st.tabs(["ACCESO", "REGISTRO"])
        
        with tab_login:
            st.markdown("<div style='background: rgba(0,0,0,0.5); padding: 20px; border-radius: 5px;'>", unsafe_allow_html=True)
            user = st.text_input("USUARIO", key="log_u")
            pw = st.text_input("CLAVE", type="password", key="log_p")
            
            if st.button("INICIAR SISTEMA", type="primary", use_container_width=True):
                st.session_state['db_users'] = load_users()
                if user in st.session_state['db_users']:
                    if check_hashes(pw, st.session_state['db_users'][user]):
                        st.session_state['authenticated'] = True
                        st.session_state['user_current'] = user
                        st.toast(f"BIENVENIDO AGENTE {user.upper()}", icon="💠")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("CLAVE INCORRECTA")
                else:
                    st.error("USUARIO DESCONOCIDO")
            
            st.markdown("---")
            st.caption("🔒 Acceso Demo: `admin` / `admin123`")
            st.markdown("</div>", unsafe_allow_html=True)

        with tab_signup:
            st.markdown("<div style='background: rgba(0,0,0,0.5); padding: 20px; border-radius: 5px;'>", unsafe_allow_html=True)
            nu = st.text_input("NUEVO USUARIO", key="new_u")
            np = st.text_input("NUEVA CLAVE", type="password", key="new_p")
            cp = st.text_input("CONFIRMAR CLAVE", type="password", key="conf_p")
            
            if st.button("CREAR CREDENCIALES", use_container_width=True):
                st.session_state['db_users'] = load_users()
                if np == cp and len(np) > 3:
                    if nu not in st.session_state['db_users']:
                        st.session_state['db_users'][nu] = hashlib.sha256(str.encode(np)).hexdigest()
                        save_users(st.session_state['db_users'])
                        st.success("REGISTRO EXITOSO")
                    else:
                        st.warning("USUARIO YA EXISTE")
                else:
                    st.error("ERROR EN DATOS")
            st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# 5. LÓGICA DE NEGOCIO Y APP PRINCIPAL
# ==========================================
def main_app():
    # Inicialización de Estado
    for k, v in {'dinero': 10000.0, 'acciones': 0.0, 'historial': [], 
                 'ticker_actual': 'BTC-USD', 'analisis_pendiente': None}.items():
        if k not in st.session_state: st.session_state[k] = v

    # Carga de IA (Silenciosa)
    @st.cache_resource
    def get_models():
        try:
            mod = pipeline("sentiment-analysis", model="yiyanghkust/finbert-tone")
            tra = GoogleTranslator(source='auto', target='es')
            return mod, tra
        except: return None, None
    
    analista_ia, traductor = get_models()

    # --- Helpers ---
    def set_ticker(t):
        st.session_state['ticker_actual'] = t
        st.session_state['analisis_pendiente'] = None
        st.rerun()

    def get_price(tkr):
        try: return float(tkr.fast_info.last_price)
        except:
            try: return float(tkr.history(period='1d')['Close'].iloc[-1])
            except: return 0.0

    def check_market(sym):
        is_crypto = any(x in sym for x in ['-USD', '=X'])
        if is_crypto: return True, "MERCADO 24/7 (CRYPTO/FX)"
        
        # Horario Bolsa NY
        tz = pytz.timezone('US/Eastern')
        now = datetime.now(tz)
        is_open = now.weekday() < 5 and 9 <= now.hour < 16 and (now.hour > 9 or now.minute >= 30)
        return is_open, "NYSE: ABIERTO" if is_open else "NYSE: CERRADO"

    # ==========================
    # BARRA LATERAL (CONTROLES)
    # ==========================
    with st.sidebar:
        st.markdown(f"""
        <div style='border-bottom: 1px solid #333; padding-bottom: 10px; margin-bottom: 20px;'>
            <h2 style='color:#00d4ff; margin:0;'>TITANIUM</h2>
            <small style='color:#666; font-family: JetBrains Mono;'>USR: {st.session_state['user_current'].upper()}</small>
        </div>
        """, unsafe_allow_html=True)
        
        # Buscador
        st.markdown("#### 🔎 ACTIVO")
        new_t = st.text_input("Ticker", value=st.session_state['ticker_actual'], label_visibility="collapsed").upper().strip()
        if new_t != st.session_state['ticker_actual']: set_ticker(new_t)
        
        st.markdown("---")
        
        # Info Mercado
        is_open, mkt_msg = check_market(st.session_state['ticker_actual'])
        sim_mode = st.toggle("MODO SIMULACIÓN", value=True)
        active = is_open or sim_mode
        
        st.markdown(f"""
        <div style='background: rgba(0,0,0,0.3); padding: 10px; border-radius: 5px; border-left: 3px solid {'#00ff41' if is_open else '#ff003c'};'>
            <span style='font-family: JetBrains Mono; font-size: 0.8rem;'>{mkt_msg}</span>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Cartera Sidebar
        t_obj = yf.Ticker(st.session_state['ticker_actual'])
        px = get_price(t_obj)
        
        st.markdown("#### 💼 PORTAFOLIO")
        equity = st.session_state['dinero'] + (st.session_state['acciones'] * px)
        c1, c2 = st.columns(2)
        c1.metric("EFECTIVO", f"${st.session_state['dinero']/1000:.1f}K")
        c2.metric("POSICIÓN", f"{st.session_state['acciones']:.4f}")
        st.metric("VALOR TOTAL", f"${equity:,.2f}", delta=f"{(equity-10000)/100:.2f}%")
        
        st.markdown("---")
        if st.button("SALIR", type="secondary"):
            st.session_state['authenticated'] = False
            st.rerun()

    # ==========================
    # CUERPO PRINCIPAL
    # ==========================
    
    # Header Dinámico
    h1, h2 = st.columns([3, 1])
    with h1:
        st.markdown(f"<h1 style='font-size: 3.5rem; margin-bottom: 0;'>{st.session_state['ticker_actual']}</h1>", unsafe_allow_html=True)
        try:
            name = t_obj.info.get('longName', 'Unknown Asset')
            st.caption(f"📍 {name}")
        except: st.caption("DATOS DE MERCADO EN TIEMPO REAL")
        
    with h2:
        if px > 0:
            color = "#00ff41" if px > 0 else "#fff" # Lógica simple, se podria mejorar con cambio diario
            st.markdown(f"""
            <div style='text-align: right;'>
                <span style='font-size: 3rem; font-family: Rajdhani; font-weight: bold; color: {color};'>${px:,.2f}</span><br>
                <span style='font-family: JetBrains Mono; color: #00d4ff; font-size: 0.8rem;'>PRECIO ACTUAL</span>
            </div>
            """, unsafe_allow_html=True)

    # Discovery Hub (Botones tipo Chips)
    with st.expander("📡 RADAR DE MERCADO", expanded=False):
        cats = {
            "POPULARES": ["NVDA", "TSLA", "AAPL", "MSFT", "AMZN"],
            "CRYPTO": ["BTC-USD", "ETH-USD", "SOL-USD", "DOGE-USD"],
            "VOLATILIDAD": ["GME", "MSTR", "COIN", "MARA"],
            "FOREX": ["EURUSD=X", "JPY=X", "GBPUSD=X"]
        }
        tabs = st.tabs(list(cats.keys()))
        for i, (cat, ticks) in enumerate(cats.items()):
            with tabs[i]:
                cols = st.columns(len(ticks))
                for j, t in enumerate(ticks):
                    if cols[j].button(t, key=f"btn_{cat}_{t}", use_container_width=True):
                        set_ticker(t)

    # Pestañas Principales
    if px > 0:
        main_tab1, main_tab2, main_tab3 = st.tabs(["📊 GRÁFICO AVANZADO", "🧠 INTELIGENCIA ARTIFICIAL", "📝 ÓRDENES"])
        
        # --- TAB 1: GRÁFICO PRO ---
        with main_tab1:
            # Selector de Rango Temporal
            ranges = {
                "1D (Día)": ("1d", "5m"),
                "5D (Semana)": ("5d", "15m"),
                "1M (Mes)": ("1mo", "60m"),
                "3M (Trimestre)": ("3mo", "1d"),
                "1Y (Año)": ("1y", "1d")
            }
            
            sel_range = st.radio("RANGO TEMPORAL", list(ranges.keys()), horizontal=True, label_visibility="collapsed")
            p, i = ranges[sel_range]
            
            with st.spinner("Cargando datos de mercado..."):
                # Lógica de Datos Robusta
                df = pd.DataFrame()
                try:
                    df = t_obj.history(period=p, interval=i)
                    if df.empty and p == "1d": # Fallback fin de semana
                        df = t_obj.history(period="1mo", interval="1d")
                        st.toast("⚠️ Mercado cerrado: Mostrando datos diarios recientes.", icon="ℹ️")
                except: pass

            if not df.empty:
                # Creación del Gráfico con Subplots (Precio + Volumen)
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                   vertical_spacing=0.03, subplot_titles=('Precio', 'Volumen'), 
                                   row_width=[0.2, 0.7])

                # Velas Japonesas
                fig.add_trace(go.Candlestick(
                    x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                    name="Precio",
                    increasing_line_color='#00ff41', decreasing_line_color='#ff003c'
                ), row=1, col=1)

                # EMA 20 (Media Móvil Exponencial)
                df['EMA20'] = df['Close'].ewm(span=20).mean()
                fig.add_trace(go.Scatter(
                    x=df.index, y=df['EMA20'], mode='lines', name='EMA 20',
                    line=dict(color='#00d4ff', width=1.5)
                ), row=1, col=1)

                # Barras de Volumen
                colors_vol = ['#00ff41' if c >= o else '#ff003c' for c, o in zip(df['Close'], df['Open'])]
                fig.add_trace(go.Bar(
                    x=df.index, y=df['Volume'], name='Volumen',
                    marker_color=colors_vol, opacity=0.5
                ), row=2, col=1)

                # Diseño Oscuro "TradingView" Style
                fig.update_layout(
                    template="plotly_dark",
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(10,10,10,0.5)',
                    height=600,
                    margin=dict(l=10, r=10, t=10, b=10),
                    xaxis_rangeslider_visible=False,
                    showlegend=False,
                    font=dict(family="JetBrains Mono", size=10, color="#aaa")
                )
                
                # Ajustes de ejes
                fig.update_xaxes(gridcolor='rgba(255,255,255,0.05)', showspikes=True, spikecolor="#00d4ff", spikethickness=1)
                fig.update_yaxes(gridcolor='rgba(255,255,255,0.05)', showspikes=True, spikecolor="#00d4ff", spikethickness=1)

                st.plotly_chart(fig, use_container_width=True)
                
                # Panel de Control Rápido
                st.markdown("### ⚡ EJECUCIÓN RÁPIDA")
                qc1, qc2, qc3 = st.columns([1, 1, 2])
                monto = qc3.number_input("MONTO ($)", min_value=10.0, value=1000.0, step=100.0, label_visibility="collapsed")
                
                if qc1.button("COMPRAR (MARKET)", disabled=not active, use_container_width=True):
                    if st.session_state['dinero'] >= monto:
                        cant = monto / px
                        st.session_state['dinero'] -= monto
                        st.session_state['acciones'] += cant
                        st.session_state['historial'].append(f"🟢 COMPRA {cant:.4f} @ ${px:.2f} | {datetime.now().strftime('%H:%M:%S')}")
                        st.rerun()
                    else: st.error("FONDOS INSUFICIENTES")
                
                if qc2.button("VENDER (MARKET)", disabled=not active, use_container_width=True):
                    if st.session_state['acciones'] > 0:
                        val = st.session_state['acciones'] * px
                        st.session_state['dinero'] += val
                        st.session_state['acciones'] = 0.0
                        st.session_state['historial'].append(f"🔴 VENTA TODO @ ${px:.2f} | {datetime.now().strftime('%H:%M:%S')}")
                        st.rerun()
                    else: st.error("SIN POSICIONES")
            else:
                st.warning("DATOS NO DISPONIBLES EN ESTE MOMENTO")

        # --- TAB 2: ANÁLISIS IA ---
        with main_tab2:
            col_a, col_b = st.columns([1, 2])
            with col_a:
                st.markdown("#### 🧠 MOTOR NEURONAL")
                st.info("FinBERT analiza titulares de noticias globales para determinar el sentimiento del mercado.")
                
                umbral = st.slider("SENSIBILIDAD IA", 0.5, 0.99, 0.75)
                
                if st.button("ESCANEAR MERCADO", type="primary", use_container_width=True):
                    if not analista_ia:
                        st.error("MODELOS OFFLINE")
                    else:
                        with st.spinner("ANALIZANDO FLUJO DE DATOS..."):
                            try:
                                news = t_obj.news
                                if not news: st.warning("SIN NOTICIAS RECIENTES")
                                else:
                                    items = []
                                    score_sum = 0
                                    validos = 0
                                    
                                    for n in news:
                                        # Obtener título seguro
                                        tit = n.get('title') or (n.get('content', {}).get('title') if n.get('content') else None)
                                        if not tit: continue
                                        
                                        # Análisis
                                        res = analista_ia(tit[:512])[0]
                                        lbl = res['label']
                                        conf = res['score']
                                        
                                        # Traducción visual
                                        tit_es = tit # Por velocidad, traducimos al mostrar si es necesario, o dejamos en inglés técnico
                                        try: tit_es = traductor.translate(tit)
                                        except: pass

                                        val = 1 if lbl == "Positive" else -1 if lbl == "Negative" else 0
                                        score_sum += (val * conf)
                                        validos += 1
                                        
                                        items.append({'txt': tit_es, 'lbl': lbl, 'conf': conf})
                                    
                                    # Resultado
                                    final_score = (score_sum / validos) if validos > 0 else 0
                                    prob_compra = ((final_score + 1) / 2) * 100
                                    
                                    dec = "MANTENER"
                                    if prob_compra > (umbral * 100): dec = "COMPRA FUERTE"
                                    elif prob_compra < (100 - (umbral * 100)): dec = "VENTA FUERTE"
                                    
                                    st.session_state['analisis_pendiente'] = {
                                        'dec': dec, 'prob': prob_compra, 'data': items, 'px': px
                                    }
                            except Exception as e: st.error(f"ERROR: {str(e)}")

            with col_b:
                if st.session_state.get('analisis_pendiente'):
                    res = st.session_state['analisis_pendiente']
                    color_res = "#00ff41" if "COMPRA" in res['dec'] else "#ff003c" if "VENTA" in res['dec'] else "#888"
                    
                    st.markdown(f"""
                    <div style='background: rgba(0,0,0,0.5); padding: 20px; border-radius: 10px; border: 1px solid {color_res}; text-align: center;'>
                        <h2 style='color: {color_res}; margin: 0;'>{res['dec']}</h2>
                        <h1 style='font-size: 4rem; margin: 0;'>{res['prob']:.1f}%</h1>
                        <p style='color: #aaa; font-family: JetBrains Mono;'>SCORE DE CONFIANZA ALGORÍTMICA</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("#### EVIDENCIA DETECTADA")
                    for d in res['data'][:4]:
                        icon = "🟢" if d['lbl']=="Positive" else "🔴" if d['lbl']=="Negative" else "⚪"
                        st.markdown(f"""
                        <div style='margin-bottom: 10px; border-left: 2px solid #333; padding-left: 10px;'>
                            <span style='font-size: 1.2rem;'>{icon}</span> 
                            <span style='font-size: 0.9rem; color: #ddd;'>{d['txt']}</span><br>
                            <small style='color: #666; font-family: JetBrains Mono;'>CONF: {d['conf']:.4f}</small>
                        </div>
                        """, unsafe_allow_html=True)

        # --- TAB 3: LIBRO DE ÓRDENES ---
        with main_tab3:
            st.markdown("#### HISTORIAL DE TRANSACCIONES")
            if st.session_state['historial']:
                for h in reversed(st.session_state['historial']):
                    color = "#00ff41" if "COMPRA" in h else "#ff003c" if "VENTA" in h else "#00d4ff"
                    st.markdown(f"<div style='border-bottom: 1px solid #222; padding: 5px; color: {color}; font-family: JetBrains Mono;'>{h}</div>", unsafe_allow_html=True)
            else:
                st.info("EL LIBRO DE ÓRDENES ESTÁ VACÍO")

# ==========================================
# 6. INICIO (ORQUESTADOR)
# ==========================================
if not st.session_state['authenticated']:
    login_screen()
else:
    main_app()