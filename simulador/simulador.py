import time
import random
import requests
import datetime
import math

API_URL = "http://127.0.0.1:5000/sensor"
LOTE_ID = "QUESO_MANCHEGO_001"

print("="*60)
print(f"🚚 INICIANDO SIMULADOR IOT (RUTA REAL A-43 CARRETERAS) - LOTE {LOTE_ID}")
print("="*60)

# Coordenadas de Inicio y Fin
# Inicio: Ciudad Real (Zona industrial)
START_LAT, START_LON = 38.9856, -3.9189
# Fin: Membrilla (Planta de distribución)
END_LAT, END_LON = 38.9744, -3.3486

def obtener_ruta_real(lon1, lat1, lon2, lat2):
    """
    Se conecta al servidor público de OSRM (Open Source Routing Machine)
    para obtener todas las coordenadas geométricas exactas (curvas, rotondas)
    de un viaje por carretera entre dos puntos.
    """
    print("🌍 Trazando ruta GPS exacta por carreteras...")
    osrm_url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson"
    try:
        res = requests.get(osrm_url).json()
        coords = res['routes'][0]['geometry']['coordinates']
        # OSRM devuelve [lon, lat], lo invertimos a [lat, lon] para nuestro uso
        waypoints = [(lat, lon) for lon, lat in coords]
        print(f"✅ ¡Ruta calculada con {len(waypoints)} puntos de paso por asfalto!")
        return waypoints
    except Exception as e:
        print("⚠️ Fallo al obtener la ruta de OSRM, usando línea simple de fallback.")
        return [(lat1, lon1), (lat2, lon2)]

# Obtenemos los cientos de waypoints que trazan con precisión milimétrica la carretera
WAYPOINTS = obtener_ruta_real(START_LON, START_LAT, END_LON, END_LAT)

# Parámetros físicos
# Subimos un poco el salto porque ahora tenemos muchísimos puntos (curvas)
STEP_SIZE_DEGREES = 0.003   # Avance del GPS por tick sobre la carretera
TICK_SECONDS = 3            # La telemetría se envía cada 3 segundos
temperatura_actual = 4.0    # El queso necesita entre 4 y 8 °C

current_wp_idx = 0
current_lat, current_lon = WAYPOINTS[0]

def distance(lat1, lon1, lat2, lon2):
    return math.sqrt((lat2 - lat1)**2 + (lon2 - lon1)**2)

while True:
    # 1. Movimiento guiado por el asfalto (Interpolación entre curvaturas)
    if current_wp_idx < len(WAYPOINTS) - 1:
        target_lat, target_lon = WAYPOINTS[current_wp_idx + 1]
        dist = distance(current_lat, current_lon, target_lat, target_lon)
        
        if dist <= STEP_SIZE_DEGREES:
            # Hemos rebasado o alcanzado el punto de la curva, apuntamos al siguiente
            current_wp_idx += 1
            current_lat, current_lon = target_lat, target_lon
        elif dist > 0:
            # Interpolación matemática (avanzar unos metros hacia el siguiente punto de la curva)
            ratio = STEP_SIZE_DEGREES / dist
            current_lat += (target_lat - current_lat) * ratio
            current_lon += (target_lon - current_lon) * ratio
    else:
        # Hemos llegado al destino. Damos vueltas pequeñitas simulando aparcamiento
        current_lat += random.uniform(-0.0001, 0.0001)
        current_lon += random.uniform(-0.0001, 0.0001)

    # 2. Variación de temperatura realista
    if current_wp_idx == len(WAYPOINTS) - 1 and random.random() < 0.2:
        # Han abierto las puertas en el muelle de descarga
        temperatura_actual += random.uniform(0.5, 1.5)
    elif random.random() < 0.05:
        # Fuga temporal de frío por baches
        temperatura_actual += random.uniform(0.5, 1.0)
    else:
        # El compresor estabiliza a 4.0 °C
        diff = 4.0 - temperatura_actual
        temperatura_actual += diff * 0.15 + random.uniform(-0.1, 0.1)
        
    if temperatura_actual < 1.0: temperatura_actual = 1.0

    timestamp = datetime.datetime.now().isoformat()
    payload = {
        "id_lote": LOTE_ID,
        "lat": round(current_lat, 6),
        "lon": round(current_lon, 6),
        "temperatura": round(temperatura_actual, 2),
        "timestamp": timestamp
    }

    # Barra visual de progreso aproximado
    progreso = int((current_wp_idx / len(WAYPOINTS)) * 100)
    
    print(f"📡 [{timestamp[-14:-6]}] Temp: {payload['temperatura']}°C | Pos: ({payload['lat']}, {payload['lon']}) [Ruta: {progreso}%]")
    
    try:
        response = requests.post(API_URL, json=payload, timeout=5)
        if response.status_code == 201:
            print(f"   => ✅ Bloque #{response.json().get('block_index')} minado")
        else:
            print(f"   => ❌ Error Servidor: {response.text}")
    except requests.exceptions.RequestException:
        print("   => ⚠️ Error de conexión.")

    time.sleep(TICK_SECONDS)
