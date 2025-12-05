import streamlit as st
import yfinance as yf
from transformers import pipeline
from deep_translator import GoogleTranslator
import plotly.graph_objects as go
import pandas as pd
import time
from datetime import datetime
import pytz
import hashlib
import json
import os

# ==========================================
# 1. CONFIGURACIÓN DEL SISTEMA PRO
# ==========================================
st.set_page_config(
    page_title="TERMINAL TITANIUM | PRO", 
    page_icon="💠", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 2. ESTÉTICA PROFESIONAL (CSS INYECTADO)
# ==========================================
st.markdown("""
<style>
    /* IMPORTAR FUENTES TÉCNICAS */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=JetBrains+Mono:wght@400;700&display=swap');

    /* FUENTE GLOBAL */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #0e0e0e;
        color: #e0e0e0;
    }

    /* BARRA LATERAL ESTILO TERMINAL */
    section[data-testid="stSidebar"] {
        background-color: #111111;
        border-right: 1px solid #333;
    }
    
    /* INPUTS DE LOGIN */
    .stTextInput>div>div>input {
        background-color: #1a1a1a;
        color: #fff;
        border: 1px solid #333;
        font-family: 'JetBrains Mono', monospace;
    }
    .stTextInput>div>div>input:focus {
        border-color: #00d4ff;
    }

    /* MÉTRICAS (KPI CARDS) */
    div[data-testid="stMetric"] {
        background-color: #1a1a1a;
        border: 1px solid #2d2d2d;
        padding: 15px;
        border-radius: 4px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.5);
    }
    div[data-testid="stMetric"] label {
        color: #888;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.5rem;
        color: #fff;
    }

    /* BOTONES TÉCNICOS - CON MÁS ESPACIO */
    .stButton>button {
        background-color: #222;
        color: #bbb;
        border: 1px solid #333;
        border-radius: 4px; /* Un poco más redondeado */
        font-family: 'Inter', sans-serif;
        font-size: 0.9rem;
        transition: all 0.2s;
        text-transform: uppercase;
        font-weight: 500;
        margin: 5px 0px; /* ESPACIO VERTICAL AÑADIDO */
    }
    .stButton>button:hover {
        border-color: #00d4ff;
        color: #00d4ff;
        background-color: #1a1a1a;
    }
    .stButton>button:active {
        background-color: #00d4ff;
        color: #000;
    }

    /* TABS ESTILO NAVEGADOR */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px; /* ESPACIO ENTRE TABS */
        background-color: #111;
        padding: 10px;
        border-bottom: 1px solid #333;
    }
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        background-color: transparent;
        border: none;
        color: #666;
        font-family: 'Inter', sans-serif;
    }
    .stTabs [aria-selected="true"] {
        background-color: #222;
        color: #fff;
        border-top: 2px solid #00d4ff;
    }

    /* LOGOTIPO TÍTULO */
    .title-text {
        font-family: 'JetBrains Mono', monospace;
        font-weight: 700;
        color: #fff;
        letter-spacing: -1px;
        border-bottom: 2px solid #333;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }
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
        # Usuario Admin por defecto si no existe archivo
        default_db = {'admin': make_hashes('admin123')}
        save_users(default_db)
        return default_db

def save_users(db):
    with open(DB_FILE, 'w') as f:
        json.dump(db, f)

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text:
        return hashed_text
    return False

# Cargar usuarios al inicio
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
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown(
            """
            <div style='text-align: center; margin-bottom: 30px;'>
                <h1 style='font-family: JetBrains Mono; color: #fff; font-size: 3rem;'>TITANIUM</h1>
                <p style='color: #00d4ff; letter-spacing: 3px; font-size: 0.9rem;'>ACCESO SEGURO A TERMINAL V4.2</p>
            </div>
            """, unsafe_allow_html=True
        )
        
        tab_login, tab_signup = st.tabs(["INICIAR SESIÓN", "NUEVA IDENTIDAD"])
        
        with tab_login:
            st.markdown("<div style='background: #111; padding: 20px; border: 1px solid #333;'>", unsafe_allow_html=True)
            username = st.text_input("ID USUARIO", key="login_user")
            password = st.text_input("CONTRASEÑA", type='password', key="login_pass")
            
            if st.button("AUTENTICAR", type="primary", use_container_width=True):
                # Recargar DB por si hubo cambios externos
                st.session_state['db_users'] = load_users()
                
                if username in st.session_state['db_users']:
                    if check_hashes(password, st.session_state['db_users'][username]):
                        st.session_state['authenticated'] = True
                        st.session_state['user_current'] = username
                        st.toast(f"ACCESO CONCEDIDO: BIENVENIDO {username.upper()}", icon="🔓")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("ACCESO DENEGADO: CREDENCIALES INVÁLIDAS")
                else:
                    st.error("ACCESO DENEGADO: USUARIO NO ENCONTRADO")
            st.markdown("</div>", unsafe_allow_html=True)

        with tab_signup:
            st.markdown("<div style='background: #111; padding: 20px; border: 1px solid #333;'>", unsafe_allow_html=True)
            new_user = st.text_input("CREAR ID USUARIO", key="new_user")
            new_pass = st.text_input("CREAR CONTRASEÑA", type='password', key="new_pass")
            confirm_pass = st.text_input("CONFIRMAR CONTRASEÑA", type='password', key="conf_pass")
            
            if st.button("REGISTRAR IDENTIDAD", use_container_width=True):
                # Recargar DB antes de validar
                st.session_state['db_users'] = load_users()
                
                if new_pass == confirm_pass:
                    if new_user in st.session_state['db_users']:
                        st.warning("ERROR: EL ID YA EXISTE")
                    elif len(new_pass) < 4:
                        st.warning("ERROR: CONTRASEÑA DEMASIADO CORTA")
                    else:
                        st.session_state['db_users'][new_user] = make_hashes(new_pass)
                        save_users(st.session_state['db_users']) # GUARDAR EN ARCHIVO
                        st.success("IDENTIDAD CREADA. PROCEDA A INICIAR SESIÓN.")
                else:
                    st.error("ERROR: LAS CONTRASEÑAS NO COINCIDEN")
            st.markdown("</div>", unsafe_allow_html=True)
            
        st.markdown("<div style='text-align: center; margin-top: 50px; color: #444; font-size: 0.7rem;'>CONEXIÓN ENCRIPTADA SHA-256</div>", unsafe_allow_html=True)

# ==========================================
# 5. APLICACIÓN PRINCIPAL (SOLO SI AUTENTICADO)
# ==========================================
def main_app():
    # --- GESTIÓN DE ESTADO INTERNO ---
    if 'dinero' not in st.session_state: st.session_state['dinero'] = 10000.0
    if 'acciones' not in st.session_state: st.session_state['acciones'] = 0.0
    if 'historial' not in st.session_state: st.session_state['historial'] = []
    if 'ticker_actual' not in st.session_state: st.session_state['ticker_actual'] = 'BTC-USD'
    if 'analisis_pendiente' not in st.session_state: st.session_state['analisis_pendiente'] = None

    # --- MOTORES IA ---
    @st.cache_resource
    def cargar_motores():
        try:
            model = pipeline("sentiment-analysis", model="yiyanghkust/finbert-tone")
            trans = GoogleTranslator(source='auto', target='es')
            return model, trans
        except Exception:
            return None, None

    analista_ia, traductor = cargar_motores()

    # --- FUNCIONES ---
    def cambiar_ticker(ticker):
        st.session_state['ticker_actual'] = ticker
        st.session_state['analisis_pendiente'] = None
        st.rerun()

    def traducir_seguro(texto, traductor_obj):
        if not traductor_obj: return texto
        try:
            return traductor_obj.translate(texto)
        except Exception:
            return texto 

    def obtener_titular(item):
        if not item: return None
        if 'title' in item: return item['title']
        if 'content' in item and 'title' in item['content']: 
            return item['content']['title']
        return None

    def obtener_precio_live(ticker_obj):
        try:
            price = ticker_obj.fast_info.last_price
            if price is not None: return float(price)
        except:
            pass
        try:
            hist = ticker_obj.history(period='1d')
            if not hist.empty:
                return float(hist['Close'].iloc[-1])
        except:
            pass
        return 0.0

    def verificar_mercado(ticker_symbol):
        try:
            if any(x in ticker_symbol for x in ["-USD", "=X", "-EUR"]):
                return True, datetime.now(pytz.utc), "MERCADO GLOBAL 24/7"
            tz = pytz.timezone('US/Eastern')
            now = datetime.now(tz)
            if now.weekday() < 5: 
                start = now.replace(hour=9, minute=30, second=0, microsecond=0)
                end = now.replace(hour=16, minute=0, second=0, microsecond=0)
                if start <= now <= end:
                    return True, now, "NYSE: ABIERTO"
            return False, now, "NYSE: CERRADO"
        except:
            return False, datetime.now(), "ESTADO: DESCONOCIDO"

    # --- BARRA LATERAL ---
    with st.sidebar:
        st.markdown(f"<div style='font-family: JetBrains Mono; font-size: 1.2em; color: #00d4ff; font-weight: bold; margin-bottom: 5px;'>TITANIUM<br><span style='color: white; font-size: 0.8em;'>TERMINAL_PRO</span></div>", unsafe_allow_html=True)
        st.caption(f"OPERADOR: {st.session_state['user_current'].upper()}")
        
        if st.button("🔒 CERRAR SESIÓN", type="primary"):
            st.session_state['authenticated'] = False
            st.rerun()

        st.markdown("---")
        
        # Input de Ticker Estilizado
        st.markdown("<div style='color: #666; font-size: 0.8rem; margin-bottom: 5px;'>SELECCIÓN DE ACTIVO</div>", unsafe_allow_html=True)
        nuevo_ticker_input = st.text_input("Símbolo Ticker", value=st.session_state['ticker_actual'], label_visibility="collapsed").upper().strip()
        if nuevo_ticker_input and nuevo_ticker_input != st.session_state['ticker_actual']:
            cambiar_ticker(nuevo_ticker_input)

        st.markdown("---")

        # Status del Mercado
        abierto, hora_actual, etiqueta_mercado = verificar_mercado(st.session_state['ticker_actual'])
        modo_sim = st.checkbox("MODO SIMULACIÓN", value=True)
        mercado_activo = abierto or modo_sim
        
        color_status = "#00ff41" if abierto else "#ff003c"
        st.markdown(
            f"""
            <div style='display: flex; align-items: center; justify-content: space-between; background: #1a1a1a; padding: 10px; border: 1px solid #333; margin-bottom: 20px;'>
                <span style='font-size: 0.8rem; color: #aaa;'>ESTADO MERCADO</span>
                <span style='color: {color_status}; font-weight: bold; font-family: JetBrains Mono;'>● {etiqueta_mercado}</span>
            </div>
            """, unsafe_allow_html=True
        )

        # Métricas de Cartera
        st.markdown("<div style='color: #666; font-size: 0.8rem; margin-bottom: 5px;'>RESUMEN PORTAFOLIO</div>", unsafe_allow_html=True)
        ticker_obj = yf.Ticker(st.session_state['ticker_actual'])
        precio_live = obtener_precio_live(ticker_obj)
        
        if precio_live > 0:
            patrimonio = st.session_state['dinero'] + (st.session_state['acciones'] * precio_live)
            
            col_w1, col_w2 = st.columns(2)
            col_w1.metric("LIQUIDEZ", f"${st.session_state['dinero'] / 1000:.1f}k")
            col_w2.metric("POSICIONES", f"{st.session_state['acciones']:.4f}")
            
            st.metric("VALOR NETO LIQUIDACIÓN", f"${patrimonio:,.2f}", 
                      delta=f"{(patrimonio - 10000) / 10000 * 100:.2f}% YTD")
        else:
            st.error("ERROR DE DATOS")

        st.markdown("---")
        
        # Controles Operativos
        st.markdown("<div style='color: #666; font-size: 0.8rem; margin-bottom: 5px;'>CONFIGURACIÓN OPERATIVA</div>", unsafe_allow_html=True)
        monto_op = st.number_input("Tamaño Orden ($)", min_value=10.0, value=2000.0, step=100.0)
        umbral_ia = st.slider("Umbral Confianza IA", 0.50, 0.99, 0.75)
        
        if st.button("REINICIAR CUENTA"):
            st.session_state['dinero'] = 10000.0
            st.session_state['acciones'] = 0.0
            st.session_state['historial'] = []
            st.rerun()

    # --- DASHBOARD PRINCIPAL ---
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.markdown(f"<h1 class='title-text'>{st.session_state['ticker_actual']} <span style='font-weight:300; color: #666;'>DATOS DE MERCADO</span></h1>", unsafe_allow_html=True)
    with col_h2:
        if precio_live > 0:
            st.markdown(f"<div style='text-align: right; font-family: JetBrains Mono; font-size: 2rem; color: #fff;'>${precio_live:,.2f}</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='text-align: right; font-family: Inter; font-size: 0.8rem; color: #00d4ff;'>PRECIO REAL-TIME</div>", unsafe_allow_html=True)

    # --- MARKET DISCOVERY HUB (Español y Espaciado) ---
    with st.expander("📡 CENTRO DE INTELIGENCIA DE MERCADO", expanded=False):
        tab_pop, tab_vol, tab_cry, tab_new = st.tabs(["MÁS ACTIVOS", "ALTA VOLATILIDAD", "CRYPTO/FX", "EMERGENTES"])
        
        def crear_botones(lista, suffix):
            # Usamos gap="small" para dar espacio horizontal nativo, más el CSS inyectado para vertical
            cols = st.columns(len(lista), gap="small")
            for i, t in enumerate(lista):
                if cols[i].button(t, key=f"btn_{t}_{suffix}", use_container_width=True):
                    cambiar_ticker(t)

        with tab_pop: crear_botones(["NVDA", "TSLA", "AAPL", "AMD", "MSFT"], "pop")
        with tab_vol: crear_botones(["GME", "PLTR", "MSTR", "COIN", "MARA"], "vol")
        with tab_cry: crear_botones(["BTC-USD", "ETH-USD", "SOL-USD", "EURUSD=X", "JPY=X"], "cry")
        with tab_new: crear_botones(["ARM", "RDDT", "PLTR", "SOFI", "HOOD"], "new")

    # --- LÓGICA DE DATOS ---
    if precio_live > 0:
        tab_chart, tab_analysis, tab_ledger = st.tabs(["GRÁFICOS", "ANÁLISIS NEURONAL", "LIBRO DE ÓRDENES"])
        
        with tab_chart:
            df = ticker_obj.history(period="1mo", interval="60m")
            
            if not df.empty:
                fig = go.Figure()
                fig.add_trace(go.Candlestick(
                    x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                    name="OHLC",
                    increasing_line_color='#00ff41', decreasing_line_color='#ff003c'
                ))
                sma = df['Close'].rolling(window=20).mean()
                fig.add_trace(go.Scatter(x=df.index, y=sma, mode='lines', name='SMA 20', line=dict(color='#00d4ff', width=1)))

                fig.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="#111",
                    plot_bgcolor="#111",
                    height=500,
                    margin=dict(t=20, b=20, l=40, r=40),
                    xaxis_rangeslider_visible=False,
                    xaxis=dict(showgrid=True, gridcolor='#222'),
                    yaxis=dict(showgrid=True, gridcolor='#222', side='right'),
                    font=dict(family="JetBrains Mono", size=10)
                )
                st.plotly_chart(fig, use_container_width=True)
                
                col_k1, col_k2, col_k3, col_k4 = st.columns(4)
                chg = ((precio_live - df['Close'].iloc[0]) / df['Close'].iloc[0]) * 100
                col_k1.metric("CAMBIO SESIÓN", f"{chg:.2f}%", delta_color="normal")
                col_k2.metric("VOLUMEN (PROM)", f"{df['Volume'].mean()/1000000:.1f}M")
                col_k3.metric("MÁX (30D)", f"${df['High'].max():,.2f}")
                col_k4.metric("MÍN (30D)", f"${df['Low'].min():,.2f}")

            st.markdown("---")
            c1, c2, c3 = st.columns([2, 2, 4])
            if c1.button("COMPRAR (MKT)", disabled=not mercado_activo):
                if st.session_state['dinero'] >= monto_op:
                    cant = monto_op / precio_live
                    st.session_state['dinero'] -= monto_op
                    st.session_state['acciones'] += cant
                    st.session_state['historial'].append(f"[{datetime.now().strftime('%H:%M:%S')}] COMPRA MKT {cant:.4f} @ {precio_live:.2f}")
                    st.rerun()
            
            if c2.button("VENDER (MKT)", disabled=not mercado_activo):
                if st.session_state['acciones'] > 0:
                    val = st.session_state['acciones'] * precio_live
                    st.session_state['dinero'] += val
                    st.session_state['acciones'] = 0.0
                    st.session_state['historial'].append(f"[{datetime.now().strftime('%H:%M:%S')}] VENTA MKT TODO @ {precio_live:.2f}")
                    st.rerun()
                    
            with c3:
                st.caption(f"VALOR ORDEN: ${monto_op:,.2f} | PODER DE COMPRA: ${st.session_state['dinero']:,.2f}")

        with tab_analysis:
            col_ia1, col_ia2 = st.columns([1, 2])
            with col_ia1:
                st.markdown("#### MOTOR NEURONAL")
                st.info("Utilizando modelo Transformer FinBERT para extracción de sentimiento en noticias globales.")
                
                if st.button("EJECUTAR SECUENCIA DE ANÁLISIS", type="primary"):
                    if not analista_ia:
                        st.error("MOTOR OFFLINE")
                    else:
                        with st.spinner("PROCESANDO FLUJOS DE DATOS..."):
                            try:
                                news = ticker_obj.news
                                if not news:
                                    st.warning("NO HAY FLUJO DE DATOS DISPONIBLE")
                                else:
                                    evidencia = []
                                    score = 0
                                    count = 0
                                    for item in news:
                                        tit = obtener_titular(item)
                                        if not tit: continue
                                        res = analista_ia(tit[:512])[0]
                                        val = 1 if res['label'] == "Positive" else -1 if res['label'] == "Negative" else 0
                                        weight = res['score']
                                        score += (val * weight)
                                        count += 1
                                        evidencia.append({
                                            "txt": tit,
                                            "score": res['score'],
                                            "label": res['label']
                                        })
                                    final_score = (score / count) if count > 0 else 0
                                    prob = ((final_score + 1) / 2) * 100
                                    decision = "MANTENER"
                                    if prob > (umbral_ia * 100): decision = "COMPRA FUERTE"
                                    elif prob < (100 - (umbral_ia * 100)): decision = "VENTA FUERTE"
                                    st.session_state['analisis_pendiente'] = {
                                        "dec": decision,
                                        "prob": prob,
                                        "data": evidencia,
                                        "px": precio_live
                                    }
                            except Exception as e:
                                st.error(f"ERROR EN EJECUCIÓN: {str(e)}")

            with col_ia2:
                if st.session_state['analisis_pendiente']:
                    res = st.session_state['analisis_pendiente']
                    st.markdown(f"""
                    <div style="background: #111; padding: 20px; border: 1px solid #333; text-align: center;">
                        <h2 style="color: {'#00ff41' if res['dec'] == 'COMPRA FUERTE' else '#ff003c' if res['dec'] == 'VENTA FUERTE' else '#888'}; font-family: JetBrains Mono;">{res['dec']}</h2>
                        <div style="width: 100%; background: #333; height: 10px; margin-top: 10px;">
                            <div style="width: {res['prob']}%; background: linear-gradient(90deg, #ff003c 0%, #888 50%, #00ff41 100%); height: 100%;"></div>
                        </div>
                        <p style="margin-top: 5px; font-family: JetBrains Mono;">NIVEL DE CONFIANZA: {res['prob']:.1f}/100</p>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown("#### SEÑALES PROCESADAS")
                    for d in res['data'][:5]:
                        color = "#00ff41" if d['label'] == "Positive" else "#ff003c" if d['label'] == "Negative" else "#888"
                        # Traducir labels para visualización
                        lbl_es = "POSITIVO" if d['label'] == "Positive" else "NEGATIVO" if d['label'] == "Negative" else "NEUTRO"
                        st.markdown(f"<div style='border-left: 3px solid {color}; padding-left: 10px; margin-bottom: 10px; font-size: 0.8rem;'>{d['txt']} <br><span style='color:{color}'>{lbl_es} ({d['score']:.2f})</span></div>", unsafe_allow_html=True)

                    if mercado_activo:
                        if st.button("EJECUTAR ORDEN ALGO"):
                            if res['dec'] == "COMPRA FUERTE":
                                if st.session_state['dinero'] >= monto_op:
                                    cant = monto_op / precio_live
                                    st.session_state['dinero'] -= monto_op
                                    st.session_state['acciones'] += cant
                                    st.session_state['historial'].append(f"[{datetime.now().strftime('%H:%M:%S')}] ALGO COMPRA {cant:.4f} @ {precio_live:.2f}")
                                    st.session_state['analisis_pendiente'] = None
                                    st.rerun()
                            elif res['dec'] == "VENTA FUERTE":
                                if st.session_state['acciones'] > 0:
                                    val = st.session_state['acciones'] * precio_live
                                    st.session_state['dinero'] += val
                                    st.session_state['acciones'] = 0.0
                                    st.session_state['historial'].append(f"[{datetime.now().strftime('%H:%M:%S')}] ALGO VENTA TODO @ {precio_live:.2f}")
                                    st.session_state['analisis_pendiente'] = None
                                    st.rerun()

        with tab_ledger:
            st.markdown("#### REGISTRO DE TRANSACCIONES")
            if not st.session_state['historial']:
                st.markdown("<div style='color: #444; font-family: JetBrains Mono;'>NO HAY REGISTROS</div>", unsafe_allow_html=True)
            else:
                txt_log = ""
                for h in reversed(st.session_state['historial']):
                    txt_log += f"{h}\n"
                st.text_area("LOG", txt_log, height=300, disabled=True)
    else:
        st.warning("SISTEMA EN ESPERA: AGUARDANDO ENTRADA VÁLIDA")

# ==========================================
# 6. ORQUESTADOR DE FLUJO
# ==========================================
if not st.session_state['authenticated']:
    login_screen()
else:
    main_app()