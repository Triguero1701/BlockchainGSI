import time
import random
import requests
import datetime
import math

API_URL = "http://127.0.0.1:5000/sensor"

RUTAS = [
    {
        "id_lote": "QUESO_MANCHEGO_001",
        "start": (38.9856, -3.9189),    # Ciudad Real
        "end": (38.9744, -3.3486),      # Membrilla
    },
    {
        "id_lote": "QUESO_MANCHEGO_002",
        "start": (38.7597, -3.3841),    # Valdepeñas
        "end": (38.9959, -3.3692),      # Manzanares
    },
    {
        "id_lote": "QUESO_MANCHEGO_003",
        "start": (39.0700, -3.6160),    # Daimiel
        "end": (38.8908, -3.7110),      # Almagro
    },
]

print("=" * 70)
print("🚚 INICIANDO SIMULADOR IOT MULTI-TRAYECTO (RUTAS REALES POR CARRETERA)")
print("=" * 70)
print(f"📦 Lotes activos: {', '.join(r['id_lote'] for r in RUTAS)}")

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

# Parámetros físicos
STEP_SIZE_DEGREES = 0.003   # Avance del GPS por tick sobre la carretera
TICK_SECONDS = 3            # La telemetría se envía cada 3 segundos

def distance(lat1, lon1, lat2, lon2):
    return math.sqrt((lat2 - lat1)**2 + (lon2 - lon1)**2)

def crear_envio(config):
    start_lat, start_lon = config["start"]
    end_lat, end_lon = config["end"]
    waypoints = obtener_ruta_real(start_lon, start_lat, end_lon, end_lat)
    current_lat, current_lon = waypoints[0]
    return {
        "id_lote": config["id_lote"],
        "waypoints": waypoints,
        "current_wp_idx": 0,
        "lat": current_lat,
        "lon": current_lon,
        "temperatura": round(4.0 + random.uniform(-0.4, 0.6), 2),
    }


def actualizar_posicion(envio):
    waypoints = envio["waypoints"]
    idx = envio["current_wp_idx"]

    if idx < len(waypoints) - 1:
        target_lat, target_lon = waypoints[idx + 1]
        dist = distance(envio["lat"], envio["lon"], target_lat, target_lon)

        if dist <= STEP_SIZE_DEGREES:
            envio["current_wp_idx"] += 1
            envio["lat"], envio["lon"] = target_lat, target_lon
        elif dist > 0:
            ratio = STEP_SIZE_DEGREES / dist
            envio["lat"] += (target_lat - envio["lat"]) * ratio
            envio["lon"] += (target_lon - envio["lon"]) * ratio
    else:
        envio["lat"] += random.uniform(-0.0001, 0.0001)
        envio["lon"] += random.uniform(-0.0001, 0.0001)


def actualizar_temperatura(envio):
    waypoints = envio["waypoints"]
    en_destino = envio["current_wp_idx"] == len(waypoints) - 1

    if en_destino and random.random() < 0.2:
        envio["temperatura"] += random.uniform(0.5, 1.5)
    elif random.random() < 0.05:
        envio["temperatura"] += random.uniform(0.5, 1.0)
    else:
        diff = 4.0 - envio["temperatura"]
        envio["temperatura"] += diff * 0.15 + random.uniform(-0.1, 0.1)

    if envio["temperatura"] < 1.0:
        envio["temperatura"] = 1.0


def construir_payload(envio, timestamp):
    return {
        "id_lote": envio["id_lote"],
        "lat": round(envio["lat"], 6),
        "lon": round(envio["lon"], 6),
        "temperatura": round(envio["temperatura"], 2),
        "timestamp": timestamp,
    }


def enviar_payload(payload):
    try:
        response = requests.post(API_URL, json=payload, timeout=5)
        if response.status_code == 201:
            print(f"   => ✅ [{payload['id_lote']}] Bloque #{response.json().get('block_index')} minado")
        else:
            print(f"   => ❌ [{payload['id_lote']}] Error Servidor: {response.text}")
    except requests.exceptions.RequestException:
        print(f"   => ⚠️ [{payload['id_lote']}] Error de conexión.")


envios = [crear_envio(config) for config in RUTAS]

while True:
    timestamp = datetime.datetime.now().isoformat()

    for envio in envios:
        actualizar_posicion(envio)
        actualizar_temperatura(envio)
        payload = construir_payload(envio, timestamp)

        progreso = int((envio["current_wp_idx"] / len(envio["waypoints"])) * 100)
        print(
            f"📡 [{timestamp[-14:-6]}] {envio['id_lote']} | Temp: {payload['temperatura']}°C | "
            f"Pos: ({payload['lat']}, {payload['lon']}) [Ruta: {progreso}%]"
        )

        enviar_payload(payload)

    time.sleep(TICK_SECONDS)
