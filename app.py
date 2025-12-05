import streamlit as st
import yfinance as yf
from transformers import pipeline

# --- 1. CONFIGURACIÓN INICIAL ---
st.set_page_config(page_title="Hedge Fund IA", page_icon="💰", layout="wide")

# --- 2. GESTIÓN DE MEMORIA (SESSION STATE) ---
if 'dinero' not in st.session_state:
    st.session_state['dinero'] = 10000.0
if 'acciones' not in st.session_state:
    st.session_state['acciones'] = 0
if 'historial_transacciones' not in st.session_state:
    st.session_state['historial_transacciones'] = []

# --- 3. CARGA DE MODELO ---
@st.cache_resource
def cargar_modelo():
    return pipeline("sentiment-analysis", model="yiyanghkust/finbert-tone")

with st.spinner('Despertando a la IA...'):
    analista_ia = cargar_modelo()

# --- 4. BARRA LATERAL ---
st.sidebar.header("🏦 Tu Billetera Virtual")

saldo_actual = st.session_state['dinero']
acciones_actuales = st.session_state['acciones']

st.sidebar.metric(label="Dinero Disponible (USD)", value=f"${saldo_actual:,.2f}")
st.sidebar.metric(label="Acciones en Cartera", value=f"{acciones_actuales:.4f}")

st.sidebar.markdown("---")
st.sidebar.header("Configuración de Trading")
empresa = st.sidebar.text_input("Ticker (Ej: AAPL, TSLA):", "TSLA")
umbral = st.sidebar.slider("Nivel de Confianza para operar", 0.50, 0.99, 0.85)

if st.sidebar.button("🔄 Reiniciar Cuenta"):
    st.session_state['dinero'] = 10000.0
    st.session_state['acciones'] = 0
    st.session_state['historial_transacciones'] = []
    st.rerun()

# --- 5. LÓGICA PRINCIPAL ---
st.title(f"🤖 Auto-Trading con IA: {empresa.upper()}")

if st.button("🔴 EJECUTAR ANÁLISIS Y OPERAR"):
    try:
        # A) OBTENER PRECIO
        ticker = yf.Ticker(empresa)
        historial = ticker.history(period="1mo")
        
        if historial.empty:
            st.error("No se pudo obtener el precio. Revisa el Ticker.")
        else:
            precio_actual = historial['Close'].iloc[-1]
            st.metric("Precio de Mercado Actual", f"${precio_actual:.2f}")

            # B) DESCARGAR NOTICIAS
            noticias = ticker.news
            st.write("---")
            st.subheader("📢 Bitácora de Operaciones de la IA")
            
            col_noticias, col_log = st.columns([2, 1])

            with col_noticias:
                if not noticias:
                    st.warning("Sin noticias nuevas hoy.")
                
                barra = st.progress(0)
                
                for i, item in enumerate(noticias):
                    titular = item.get('title')
                    if not titular and 'content' in item:
                        titular = item['content'].get('title')
                    
                    if titular:
                        # 1. ANÁLISIS
                        resultado = analista_ia(titular)[0]
                        sentimiento = resultado['label'] # Definimos 'sentimiento'
                        score = resultado['score']
                        
                        # 2. ICONOS (Aquí estaba el error, ahora dice 'sentimiento')
                        icono = "⚪"
                        if sentimiento == "Positive": icono = "🟢"
                        elif sentimiento == "Negative": icono = "🔴"
                        
                        st.markdown(f"**{icono} {sentimiento}** ({score:.2f}): _{titular}_")

                        # 3. LÓGICA DE INVERSIÓN
                        if score > umbral:
                            # COMPRA
                            if sentimiento == "Positive" and st.session_state['dinero'] > precio_actual:
                                monto_inversion = st.session_state['dinero'] * 0.20
                                cantidad_comprada = monto_inversion / precio_actual
                                
                                st.session_state['dinero'] -= monto_inversion
                                st.session_state['acciones'] += cantidad_comprada
                                
                                msg = f"COMPRA: {cantidad_comprada:.2f} acciones a ${precio_actual:.2f}"
                                st.session_state['historial_transacciones'].append(f"🟢 {msg}")
                                st.success(f"💰 ¡ORDEN EJECUTADA! {msg}")

                            # VENTA
                            elif sentimiento == "Negative" and st.session_state['acciones'] > 0:
                                ganancia = st.session_state['acciones'] * precio_actual
                                
                                st.session_state['dinero'] += ganancia
                                st.session_state['acciones'] = 0
                                
                                msg = f"VENTA: Se liquidaron todas las acciones. Recibes ${ganancia:.2f}"
                                st.session_state['historial_transacciones'].append(f"🔻 {msg}")
                                st.error(f"📉 ¡ORDEN EJECUTADA! {msg}")
                        
                    barra.progress((i + 1) / len(noticias))

            # C) MOSTRAR HISTORIAL
            with col_log:
                st.subheader("📜 Historial")
                for log in reversed(st.session_state['historial_transacciones']):
                    st.caption(log)
            
            # D) ACTUALIZAR VALOR TOTAL
            st.write("---")
            valor_total = st.session_state['dinero'] + (st.session_state['acciones'] * precio_actual)
            rentabilidad = ((valor_total - 10000) / 10000) * 100
            
            col1, col2 = st.columns(2)
            col1.metric("Valor Total del Portafolio", f"${valor_total:,.2f}")
            col2.metric("Rentabilidad Total", f"{rentabilidad:.2f}%")
            
            if valor_total > 10000:
                st.balloons()

    except Exception as e:
        st.error(f"Error en el sistema: {e}")

# Disclaimer
st.markdown("---")
st.caption("⚠️ Simulador educativo. El dinero es ficticio.")