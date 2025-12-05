from alpaca_trade_api.rest import REST, TimeFrame
import time

# --- 1. TUS CREDENCIALES (Cámbialas por las tuyas) ---
API_KEY = "PKYUQQVTYS4GSDRSXP2XM2EOXF"
SECRET_KEY = "FRFabiHozG4U5b2y5pc42kmyhiJoPZ2xyGULYGN4PASG"

# Conectamos con la URL de "Paper Trading" (Dinero Ficticio)
BASE_URL = "https://paper-api.alpaca.markets"

def probar_conexion():
    try:
        # Inicializamos la conexión
        api = REST(API_KEY, SECRET_KEY, BASE_URL)
        
        # 1. Verificamos cuánto dinero tienes
        cuenta = api.get_account()
        print("--- CONEXIÓN EXITOSA 🚀 ---")
        print(f"Estado de la cuenta: {cuenta.status}")
        print(f"Dinero disponible para invertir: ${float(cuenta.cash):,.2f}")
        
        # 2. Intentamos comprar 1 acción de Apple (AAPL)
        print("\n--- ENVIANDO ORDEN DE COMPRA... ---")
        
        # Verificamos si el mercado está abierto
        clock = api.get_clock()
        if clock.is_open:
            print("🕒 El mercado está ABIERTO. La orden se ejecutará ya.")
        else:
            print("zzz El mercado está CERRADO. La orden quedará en cola para mañana.")

        # Enviamos la orden
        orden = api.submit_order(
            symbol='AAPL',      # Empresa
            qty=1,              # Cantidad
            side='buy',         # Comprar
            type='market',      # Al precio que esté ahora
            time_in_force='gtc' # 'Good Till Cancelled' (Mantenla activa hasta que se cumpla)
        )
        
        print(f"✅ ¡ORDEN ENVIADA! ID: {orden.id}")
        print(f"Estado de la orden: {orden.status}")
        print("Ve a tu panel de Alpaca en la web para verla.")

    except Exception as e:
        print(f"❌ Ocurrió un error: {e}")

if __name__ == "__main__":
    probar_conexion()