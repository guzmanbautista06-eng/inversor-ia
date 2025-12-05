import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import time
from datetime import datetime, timedelta
import pytz
import hashlib
import json
import os
import numpy as np
from textblob import TextBlob 

# ==========================================
# 1. CONFIGURACIÓN DEL SISTEMA
# ==========================================
st.set_page_config(
    page_title="TITANIUM BROKER V17 INSTITUTIONAL", 
    page_icon=None, 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 2. ESTÉTICA "GOOGLE FINANCE PRO" (CSS)
# ==========================================
BACKGROUND_URL = "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?q=80&w=2070&auto=format&fit=crop"

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@300;400;600;800&family=Roboto+Mono:wght@400;600&display=swap');

    /* FONDO */
    .stApp {{
        background-image: url("{BACKGROUND_URL}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    .stApp::before {{
        content: ""; position: absolute; top: 0; left: 0; width: 100%; height: 100%;
        background: rgba(10, 14, 20, 0.95); backdrop-filter: blur(5px); z-index: -1;
    }}

    /* TIPOGRAFÍA */
    html, body, [class*="css"] {{ font-family: 'Manrope', sans-serif; color: #e0e0e0; letter-spacing: -0.3px; }}
    h1, h2, h3, h4 {{ font-family: 'Manrope', sans-serif; font-weight: 800; color: #fff !important; }}

    /* COMPONENTES */
    section[data-testid="stSidebar"] {{ background-color: rgba(5, 7, 10, 0.98); border-right: 1px solid #1f222a; }}
    
    .stTextInput>div>div>input, .stNumberInput>div>div>input {{
        background-color: rgba(255,255,255,0.03) !important; color: #fff !important;
        border: 1px solid #2d323e !important; font-family: 'Roboto Mono', monospace;
    }}
    
    div[data-testid="stMetric"] {{
        background: rgba(255,255,255,0.02); border: 1px solid #2d323e;
        padding: 15px; border-radius: 10px;
    }}
    
    /* BOTONES GOOGLE STYLE */
    .stButton>button {{
        background: rgba(255,255,255,0.05); color: #fff; border: 1px solid #2d323e;
        border-radius: 20px; font-weight: 700; transition: 0.2s;
    }}
    .stButton>button:hover {{ background: rgba(255,255,255,0.1); border-color: #5f6368; }}
    .stButton>button[kind="primary"] {{
        background: #4285f4; border-color: #4285f4; color: #fff;
    }}

    /* HEADER PRECIOS */
    .live-header {{
        background: rgba(0,0,0,0.3); backdrop-filter: blur(10px); padding: 25px;
        border-bottom: 2px solid #2d323e; margin-bottom: 25px; border-radius: 0 0 15px 15px;
    }}
    .live-price {{ font-family: 'Roboto Mono'; font-size: 3.5rem; font-weight: 700; }}
    
    /* COLORES ESTADO */
    .bg-up {{ background-color: rgba(52, 168, 83, 0.15); color: #34a853; }}
    .bg-down {{ background-color: rgba(234, 67, 53, 0.15); color: #ea4335; }}
    .text-up {{ color: #34a853 !important; }}
    .text-down {{ color: #ea4335 !important; }}

    /* CONTENEDOR IA */
    .ai-container {{
        background: rgba(20, 25, 35, 0.9); border: 1px solid #4285f4;
        border-radius: 15px; padding: 30px; margin-top: 20px;
        box-shadow: 0 0 30px rgba(66, 133, 244, 0.15);
    }}
    .probability-score {{ font-size: 4rem; font-weight: 900; font-family: 'Roboto Mono'; line-height: 1; }}
    
    /* PANEL DE OPERACIONES */
    .trade-panel {{
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid #333;
        border-radius: 10px;
        padding: 20px;
        margin-top: 20px;
    }}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. SEGURIDAD Y ESTADO
# ==========================================
DB_FILE = 'users_db.json'

def load_users():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f: return json.load(f)
    default = {'admin': hashlib.sha256(str.encode('admin123')).hexdigest()}
    with open(DB_FILE, 'w') as f: json.dump(default, f)
    return default

def save_users(db):
    with open(DB_FILE, 'w') as f: json.dump(db, f)

def check_hashes(password, hashed_text):
    return hashlib.sha256(str.encode(password)).hexdigest() == hashed_text

if 'db_users' not in st.session_state: st.session_state['db_users'] = load_users()
if 'authenticated' not in st.session_state: st.session_state['authenticated'] = False
if 'user_current' not in st.session_state: st.session_state['user_current'] = None

# ==========================================
# 4. FUNCIONES GLOBALES DE DATOS (ACCESIBLES)
# ==========================================

@st.cache_data(ttl=300) 
def get_ai_analysis(ticker):
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="6mo")
        if hist.empty: return None, 0, []
        
        # --- CÁLCULO TÉCNICO BÁSICO (para IA) ---
        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]
        
        ema12 = hist['Close'].ewm(span=12).mean()
        ema26 = hist['Close'].ewm(span=26).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9).mean()
        current_macd = macd.iloc[-1]
        current_sig = signal.iloc[-1]
        
        # --- ANÁLISIS NOTICIAS (TEXTBLOB) ---
        news_data = []
        sent_score = 50
        
        try:
            raw_news = t.news
            if not raw_news: raw_news = []
            
            scores = []
            for n in raw_news[:8]:
                title = n.get('title')
                if not title and 'content' in n:
                    title = n['content'].get('title')
                if not title: continue
                
                publisher = n.get('publisher', 'Yahoo Finance')
                link = n.get('link', '#')
                
                blob = TextBlob(title)
                pol = blob.sentiment.polarity
                
                if pol > 0.1: lbl = "POSITIVO"
                elif pol < -0.1: lbl = "NEGATIVO"
                else: lbl = "NEUTRAL"
                
                scores.append(pol)
                news_data.append({'title': title, 'label': lbl, 'publisher': publisher, 'link': link})
            
            if scores:
                avg_pol = sum(scores) / len(scores)
                sent_score = ((avg_pol + 1) / 2) * 100
        except Exception as e: pass
        
        # --- FUSIÓN DE PROBABILIDAD ---
        prob = 50
        if current_rsi < 30: prob += 20 
        elif current_rsi > 70: prob -= 20 
        if current_macd > current_sig: prob += 10 
        else: prob -= 10 
        if sent_score > 60: prob += 15
        elif sent_score < 40: prob -= 15
        prob = max(0, min(100, prob))
        
        return prob, sent_score, news_data
    except Exception as e: return 0, 0, []

@st.cache_data(ttl=60)
def get_market_snapshot(ticker):
    try:
        t = yf.Ticker(ticker)
        price = float(t.fast_info.last_price)
        prev_close = float(t.fast_info.previous_close)
        name = t.info.get('longName', ticker)
        
        change = price - prev_close
        pct_change = (change / prev_close) * 100
        return price, pct_change, name, change
    except: return 0, 0, ticker, 0

@st.cache_data(ttl=60)
def get_chart_data(ticker, period):
    try:
        t = yf.Ticker(ticker)
        # Mapeo de Periodo -> Intervalo óptimo
        if period == '1d': data = t.history(period='1d', interval='5m')
        elif period == '5d': data = t.history(period='5d', interval='15m')
        elif period == '1mo': data = t.history(period='1mo', interval='60m')
        elif period == '6mo': data = t.history(period='6mo', interval='1d')
        elif period == '1y': data = t.history(period='1y', interval='1d')
        else: data = t.history(period='max', interval='1wk')
        
        # Corrección CRÍTICA: Forzar un rango más amplio si el corto es vacío (fin de semana/feriado)
        if period in ['1d', '5d'] and data.empty:
             data = t.history(period='7d', interval='15m')
        
        if data.empty: return None
        return data
    except Exception as e: 
        print(f"Error fetching chart data: {e}")
        return None

# Función de Estrategia (sin cache, usa datos pasados)
def generate_strategy(df, sent_score):
    if df is None: return 50, "DATOS INSUFICIENTES"
    # Lógica de recomendación simple basada en la probabilidad
    prob = 50
    if sent_score > 60: prob += 10
    elif sent_score < 40: prob -= 10
    
    if prob >= 70: rec = "COMPRA FUERTE"
    elif prob >= 55: rec = "COMPRA (ACUMULAR)"
    elif prob <= 30: rec = "VENTA FUERTE"
    elif prob <= 45: rec = "VENTA (REDUCIR)"
    else: rec = "MANTENER"
        
    return prob, rec, "", ""

def set_ticker(t):
    st.session_state['ticker_actual'] = t
    st.rerun()

# ==========================================
# 7. FUNCIÓN DE LOGIN
# ==========================================
def login_screen():
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown("""
        <div style='text-align: center; padding: 50px; background: rgba(10,14,20,0.8); border: 1px solid #2d323e; border-radius: 16px; backdrop-filter: blur(10px);'>
            <h1 style='font-size: 3rem; margin:0; color:#fff;'>TITANIUM</h1>
            <p style='color: #4285f4; font-weight:800; letter-spacing: 1px;'>BROKERAGE V17.0</p>
        </div>
        """, unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["ACCEDER", "CREAR PERFIL"]) # Nombres de pestañas mejorados
        
        with tab1:
            st.markdown("<br>", unsafe_allow_html=True)
            user = st.text_input("USUARIO", key="lu", placeholder="ID de Operador")
            pw = st.text_input("CLAVE", type="password", key="lp", placeholder="Contraseña")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("INICIAR SESIÓN", use_container_width=True, type="primary"):
                db = load_users()
                if user in db and check_hashes(pw, db[user]):
                    st.session_state['authenticated'] = True
                    st.session_state['user_current'] = user
                    st.rerun()
                else: st.error("Acceso Denegado")
            st.caption("Demo: admin / admin123")

        with tab2: # Lógica de Registro Mejorada
            st.markdown("<br>", unsafe_allow_html=True)
            nu = st.text_input("ID DE PERFIL NUEVO", key="nu", placeholder="Elija su nombre de usuario")
            np = st.text_input("CREAR CLAVE", type="password", key="np", placeholder="Mínimo 6 caracteres")
            cp = st.text_input("CONFIRMAR CLAVE", type="password", key="cp", placeholder="Repita la clave")

            if st.button("REGISTRAR PERFIL SEGURO", use_container_width=True):
                db = load_users()
                if nu in db:
                    st.error("Error: El ID de perfil ya existe.")
                elif len(np) < 6:
                    st.error("Error: La clave debe tener al menos 6 caracteres.")
                elif np != cp:
                    st.error("Error: Las claves no coinciden.")
                else:
                    db[nu] = hashlib.sha256(str.encode(np)).hexdigest()
                    save_users(db)
                    st.success("¡Perfil creado con éxito! Inicie sesión.")
            st.caption("Su clave se guarda con cifrado SHA-256.")

# ==========================================
# 8. FUNCIÓN PRINCIPAL DE LA APLICACIÓN
# ==========================================
def main_app():
    # Inicialización
    defaults = {'dinero': 10000.0, 'acciones': 0.0, 'historial': [], 
                'ticker_actual': 'BTC-USD', 'timeframe': '1y'}
    for k, v in defaults.items():
        if k not in st.session_state: st.session_state[k] = v

    COMMISSION_RATE = 0.0015 
    
    # Datos de Market Snapshot (Precios Vivos)
    lp, chg_pct, long_name, _ = get_market_snapshot(st.session_state['ticker_actual'])
    
    # Datos para Gráficos e IA (Caché)
    df_analysis, news_list, sent_score = get_ai_analysis(st.session_state['ticker_actual'])
    
    # Lógica de Operativa
    try:
        equity = st.session_state['dinero'] + (st.session_state['acciones'] * lp)
    except:
        equity = st.session_state['dinero']

    # --- BARRA LATERAL ---
    with st.sidebar:
        st.markdown("### 💠 TITANIUM")
        curr_t = st.text_input("BUSCAR ACTIVO", value=st.session_state['ticker_actual']).upper().strip()
        if curr_t != st.session_state['ticker_actual']: set_ticker(curr_t)
        
        st.markdown("---")
        st.metric("PODER DE COMPRA", f"${st.session_state['dinero']:,.2f}")
        st.metric("VALOR CARTERA", f"${equity:,.2f}")
        
        st.markdown("---")
        if st.button("CERRAR SESIÓN"):
            st.session_state['authenticated'] = False
            st.rerun()

    # ==========================
    # CUERPO PRINCIPAL
    # ==========================
    
    # 1. HEADER (Live Ticker)
    col_cls = "bg-up" if chg_pct >= 0 else "bg-down"
    txt_cls = "text-up" if chg_pct >= 0 else "text-down"
    sign = "+" if chg_pct >= 0 else ""

    st.markdown(f"""
    <div class="live-header">
        <div style="display:flex; justify-content:space-between; align-items:flex-end;">
            <div>
                <h1 class="ticker-name">{st.session_state['ticker_actual']}</h1>
                <div class="company-name">{long_name}</div>
            </div>
            <div>
                <div class="live-price {txt_cls}">${lp:,.2f}</div>
                <div style="text-align:right;">
                    <span class="price-change {col_cls}">{sign}{chg_pct:.2f}%</span>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. SELECTOR DE CATEGORÍAS
    with st.expander("📁 EXPLORADOR DE ACTIVOS", expanded=False):
        cats = {
            "🔥 TENDENCIA": ["NVDA", "TSLA", "AAPL", "MSFT", "AMZN"],
            "₿ CRIPTO": ["BTC-USD", "ETH-USD", "SOL-USD", "DOGE-USD"],
            "💱 FOREX": ["EURUSD=X", "JPY=X", "GBPUSD=X"]
        }
        cols_cat = st.columns(len(cats))
        for i, (k, v) in enumerate(cats.items()):
            with cols_cat[i]:
                st.markdown(f"**{k}**")
                for item in v:
                    if st.button(item, key=f"b_{item}"): set_ticker(item)

    st.markdown("<br>", unsafe_allow_html=True)

    # 3. PESTAÑAS PRINCIPALES
    tab_chart, tab_ai = st.tabs(["📊 GRÁFICO & OPERACIONES", "🧠 ANÁLISIS ESTRATÉGICO"])

    # --- PESTAÑA GRÁFICO & OPERATIVA UNIFICADA ---
    with tab_chart:
        col_tf, col_sp = st.columns([2, 4])
        with col_tf:
            timeframe = st.select_slider(
                "RANGO TEMPORAL", 
                options=['1d', '5d', '1mo', '6mo', '1y'], 
                value='1y', 
                key='tf_selector'
            )
        
        df_chart = get_chart_data(st.session_state['ticker_actual'], timeframe)
        
        if df_chart is not None and not df_chart.empty:
            color_chart = '#34a853' if chg_pct >= 0 else '#ea4335'
            fill_chart = 'rgba(52, 168, 83, 0.1)' if chg_pct >= 0 else 'rgba(234, 67, 53, 0.1)'
            
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_width=[0.2, 0.8])
            
            fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['Close'], mode='lines', fill='tozeroy', line=dict(color=color_chart, width=2), fillcolor=fill_chart, name='Precio'), row=1, col=1)
            fig.add_trace(go.Bar(x=df_chart.index, y=df_chart['Volume'], marker_color='#555', name='Volumen', opacity=0.3), row=2, col=1)
            
            fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=500, margin=dict(l=0, r=0, t=10, b=0), showlegend=False, hovermode="x unified", xaxis_rangeslider_visible=False)
            fig.update_xaxes(showgrid=False, row=1, col=1)
            fig.update_yaxes(showgrid=True, gridcolor='rgba(255,255,255,0.05)', side="right", row=1, col=1)
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Datos no disponibles para este rango.")

        # --- SECCIÓN DE OPERACIONES (MOVIDA DEBAJO DEL GRÁFICO) ---
        st.markdown("<hr style='border-color: #333;'>", unsafe_allow_html=True)
        st.markdown("### 💳 PANEL DE OPERACIONES")
        
        c_b, c_s = st.columns(2)
        
        with c_b:
            with st.container(border=True):
                st.markdown("<h3 style='color:#34a853'>COMPRAR</h3>", unsafe_allow_html=True)
                amount = st.number_input("Monto a invertir ($)", 0.0, st.session_state['dinero'], step=100.0, key="buy_amount_input")
                
                fee = amount * COMMISSION_RATE
                total = amount
                shares = (amount - fee) / lp if lp > 0 else 0
                
                st.markdown(f"""
                <div style='display:flex; justify-content:space-between; color:#888; font-size:0.9rem;'>
                    <span>Comisión:</span><span>${fee:.2f}</span>
                </div>
                <div style='display:flex; justify-content:space-between; color:#fff; font-weight:bold; font-size:1.1rem; border-top:1px solid #333; margin-top:5px; padding-top:5px;'>
                    <span>Recibes:</span><span>{shares:.4f} acc</span>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("CONFIRMAR COMPRA", key="btn_buy", use_container_width=True, type="primary"):
                    if amount > 0:
                        st.session_state['dinero'] -= total
                        st.session_state['acciones'] += shares
                        st.session_state['historial'].append(f"BUY {shares:.4f} @ ${lp:.2f}")
                        st.success("ORDEN EJECUTADA")
                        time.sleep(1)
                        st.rerun()

        with c_s:
            with st.container(border=True):
                st.markdown("<h3 style='color:#ea4335'>VENDER</h3>", unsafe_allow_html=True)
                qty = st.number_input("Cantidad acciones", 0.0, st.session_state['acciones'], step=0.1, key="sell_qty_input")
                
                gross = qty * lp
                fee_s = gross * COMMISSION_RATE
                net = gross - fee_s
                
                st.markdown(f"""
                <div style='display:flex; justify-content:space-between; color:#888; font-size:0.9rem;'>
                    <span>Comisión:</span><span>${fee_s:.2f}</span>
                </div>
                <div style='display:flex; justify-content:space-between; color:#fff; font-weight:bold; font-size:1.1rem; border-top:1px solid #333; margin-top:5px; padding-top:5px;'>
                    <span>Recibes:</span><span>${net:.2f}</span>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("CONFIRMAR VENTA", key="btn_sell", use_container_width=True):
                    if qty > 0:
                        st.session_state['dinero'] += net
                        st.session_state['acciones'] -= qty
                        st.session_state['historial'].append(f"SELL {qty:.4f} @ ${lp:.2f}")
                        st.success("ORDEN EJECUTADA")
                        time.sleep(1)
                        st.rerun()

    # --- PESTAÑA CEREBRO QUANTUM & NOTICIAS ---
    with tab_ai:
        prob, sent_val, news = get_ai_analysis(st.session_state['ticker_actual'])
        
        col_gauge, col_info = st.columns([1, 1.5])
        
        with col_gauge:
            st.markdown(f"""
            <div class='ai-container' style='text-align: center;'>
                <div style='color:#888; font-size:0.9rem; font-weight:700;'>PROBABILIDAD DE ÉXITO (ALZA)</div>
                <div class='probability-score' style='color: {"#34a853" if prob > 60 else "#ea4335" if prob < 40 else "#fbbc04"};'>
                    {prob:.1f}%
                </div>
                <div style='margin-top:10px; font-weight:bold; color:#fff;'>
                    {"COMPRA FUERTE" if prob > 70 else "COMPRA" if prob > 55 else "VENTA FUERTE" if prob < 30 else "NEUTRAL"}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.info(f"""
            **Análisis de Fusión:**
            El algoritmo ha detectado un sentimiento de noticias de **{sent_val:.0f}/100** y señales técnicas combinadas que resultan en este score.
            """)

        with col_info:
            st.markdown("#### 📰 NOTICIAS ANALIZADAS")
            if news:
                for n in news:
                    b_col = "#34a853" if n['label']=="POSITIVO" else "#ea4335" if n['label']=="NEGATIVO" else "#555"
                    
                    # Verificar si existe link, sino usar #
                    link_url = n.get('link', '#')
                    
                    st.markdown(f"""
                    <div style='border-left: 3px solid {b_col}; padding-left: 10px; margin-bottom: 10px; background: rgba(255,255,255,0.03); padding: 10px; border-radius: 0 5px 5px 0;'>
                        <div style='display:flex; justify-content:space-between;'>
                            <span style='font-size:0.75rem; font-weight:bold; color:{b_col};'>{n['label']}</span>
                            <span style='font-size:0.7rem; color:#888;'>{n.get('publisher', 'Yahoo Finance')}</span>
                        </div>
                        <div style='color:#eee; font-weight:600; margin-top:3px;'>
                            <a href="{link_url}" target="_blank" style="text-decoration:none; color:#eee;">{n['title']}</a>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.write("Sin noticias recientes relevantes o error de conexión.")
        
        # --- LOGS (MOVIDO AQUÍ PARA SIMPLIFICAR PESTAÑAS) ---
        st.markdown("---")
        st.markdown("#### AUDITORÍA DE TRANSACCIONES")
        if st.session_state['historial']:
            for h in reversed(st.session_state['historial']):
                st.code(h, language="text")
        else:
            st.caption("No hay operaciones registradas en esta sesión.")

# ==========================================
# 6. INICIO (CONTROL DE FLUJO)
# ==========================================
if not st.session_state['authenticated']:
    login_screen()
else:
    main_app()