import streamlit as st
import yfinance as yf
from transformers import pipeline

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Inversor IA", page_icon="📈", layout="wide")

# --- 2. CARGAMOS EL CEREBRO (IA) ---
# Usamos caché para que no se descargue cada vez que tocas un botón
@st.cache_resource
def cargar_modelo():
    return pipeline("sentiment-analysis", model="yiyanghkust/finbert-tone")

# Mensaje de carga inicial
with st.spinner('Cargando Cerebro Financiero...'):
    analista_ia = cargar_modelo()

# --- 3. BARRA LATERAL (CONFIGURACIÓN) ---
st.sidebar.header("Configuración")
empresa = st.sidebar.text_input("Ticker (Ej: AAPL, NVDA, TSLA):", "AAPL")

# ESTE ES EL ÚNICO BOTÓN QUE DEBE EXISTIR
analizar_btn = st.sidebar.button("🔍 Analizar Mercado Ahora")

# Información extra de la empresa en la barra lateral
if empresa:
    try:
        ticker_info = yf.Ticker(empresa).info
        st.sidebar.markdown("---")
        st.sidebar.subheader("🏢 Perfil")
        st.sidebar.write(f"**Sector:** {ticker_info.get('sector', 'N/A')}")
        st.sidebar.write(f"**País:** {ticker_info.get('country', 'N/A')}")
    except:
        pass

# --- 4. TÍTULO PRINCIPAL ---
st.title(f"🤖 Inversor IA: Análisis de {empresa.upper()}")

# --- 5. LÓGICA PRINCIPAL (BACKEND) ---
if analizar_btn:
    try:
        # A) OBTENER DATOS FINANCIEROS Y GRÁFICOS
        ticker = yf.Ticker(empresa)
        historial = ticker.history(period="1mo")
        
        if not historial.empty:
            datos_hoy = historial.iloc[-1]
            datos_ayer = historial.iloc[-2]
            
            precio_actual = datos_hoy['Close']
            cambio = precio_actual - datos_ayer['Close']
            cambio_pct = (cambio / datos_ayer['Close']) * 100

            # KPIs (Tarjetas de métricas)
            st.write("### 📊 Tablero de Control")
            kpi1, kpi2, kpi3 = st.columns(3)
            
            with kpi1:
                st.metric(label="Precio", value=f"${precio_actual:.2f}", delta=f"{cambio:.2f} ({cambio_pct:.2f}%)")
            with kpi2:
                volumen = datos_hoy.get('Volume', 0)
                st.metric(label="Volumen", value=f"{volumen:,}")
            with kpi3:
                pe = ticker.info.get('forwardPE', 'N/A')
                st.metric(label="Ratio P/E", value=pe)
            
            st.markdown("---")
            
            # GRÁFICO
            st.write("### 📉 Tendencia (30 días)")
            st.line_chart(historial['Close'])
            st.markdown("---")

        # B) NOTICIAS E INTELIGENCIA ARTIFICIAL
        st.write(f"### 📡 Noticias y Análisis de Sentimiento")
        
        noticias = ticker.news
        
        if not noticias:
            st.warning("No se encontraron noticias recientes.")
        else:
            # Encabezados de la tabla
            col1, col2, col3 = st.columns([3, 1, 1])
            col1.subheader("Titular")
            col2.subheader("Veredicto IA")
            col3.subheader("Certeza")
            st.markdown("---")

            conteo_pos = 0
            conteo_neg = 0
            
            barra = st.progress(0)

            for i, item in enumerate(noticias):
                # Extracción segura del título (Solución al error de Yahoo)
                titular = item.get('title')
                if not titular and 'content' in item:
                    titular = item['content'].get('title')
                
                if titular:
                    # Análisis
                    resultado = analista_ia(titular)[0]
                    sentimiento = resultado['label']
                    score = resultado['score']
                    
                    if sentimiento == "Positive": conteo_pos += 1
                    if sentimiento == "Negative": conteo_neg += 1
                    
                    # Mostrar fila
                    with col1:
                        st.write(titular)
                    with col2:
                        if sentimiento == "Positive":
                            st.success("🟢 COMPRA")
                        elif sentimiento == "Negative":
                            st.error("🔴 VENTA")
                        else:
                            st.info("🟡 NEUTRAL")
                    with col3:
                        st.write(f"{score:.2f}")
                    
                    st.markdown("---")
                
                barra.progress((i + 1) / len(noticias))
            
            # Resumen final
            st.success(f"Resumen Final: {conteo_pos} Señales de Compra vs {conteo_neg} de Venta")

    except Exception as e:
        st.error(f"Error: {e}")