from flask import Flask, request, jsonify
from flask_cors import CORS
from blockchain import Blockchain
from database import init_db, insert_telemetria, update_block_hash, get_all_telemetria
import os

app = Flask(__name__)
# Habilitar CORS para que el frontend pueda consumir los datos (local)
CORS(app)

# Iniciar la infraestructura
# 1. Base de datos on-disk para of-chain legible
# El path ya se maneja de forma absoluta en database.py
init_db()

# 2. In-memory persistente blockchain
mi_blockchain = Blockchain()

rutas_pendientes = []

@app.route('/viaje', methods=['POST'])
def agregar_viaje():
    datos = request.get_json()
    rutas_pendientes.append(datos)
    return jsonify({"status": "success"})

@app.route('/rutas_pendientes', methods=['GET'])
def obtener_rutas():
    global rutas_pendientes
    rutas = rutas_pendientes
    rutas_pendientes = []
    return jsonify(rutas)


@app.route('/sensor', methods=['POST'])
def recibir_sensor():
    datos = request.get_json()
    if not datos:
        return jsonify({"error": "No JSON payload", "status": "error"}), 400
        
    required_keys = ["numero_viaje", "id_lote", "lat", "lon", "temperatura", "timestamp"]
    if not all(k in datos for k in required_keys):
        return jsonify({"error": "Missing parameters", "status": "error"}), 400

    # 1. Almacenar raw en SQLite off-chain
    row_id = insert_telemetria(
        datos["numero_viaje"],
        datos["id_lote"],
        datos["lat"],
        datos["lon"],
        datos["temperatura"],
        datos["timestamp"]
    )

    # 2. Crear un payload canónico para el bloque
    block_payload = {
        "db_id": row_id,
        "numero_viaje": datos["numero_viaje"],
        "id_lote": datos["id_lote"],
        "lat": datos["lat"],
        "lon": datos["lon"],
        "temperatura": datos["temperatura"]
        # we omit timestamp here as the block itself has its creation timestamp, 
        # or we could include it, but let's keep it simple.
    }

    # 3. Minar / Agregar el bloque a la cadena
    nuevo_bloque = mi_blockchain.agregar_bloque(block_payload)

    # 4. Actualizar el hash notarial en la BD
    update_block_hash(row_id, nuevo_bloque.hash)

    return jsonify({"status": "success", "message": "Datos registrados de forma inmutable", "block_index": nuevo_bloque.index}), 201


@app.route('/blockchain', methods=['GET'])
def obtener_blockchain():
    return jsonify({
        "longitud": len(mi_blockchain.cadena),
        "cadena": [bloque.to_dict() for bloque in mi_blockchain.cadena]
    })


@app.route('/telemetria', methods=['GET'])
def obtener_telemetria():
    return jsonify(get_all_telemetria())


@app.route('/auditar', methods=['GET'])
def auditar_integridad():
    numero_viaje = request.args.get('numero_viaje')
    
    # 1. Validar la integridad algorítmica de la cadena
    cadena_valida, indice_error = mi_blockchain.validar_cadena()
    if not cadena_valida:
        return jsonify({
            "integridad": False, 
            "razon": f"Alerta Crítica: La cadena de bloques ha sido corrompida internamente en el índice {indice_error}."
        })

    # 2. Validar que la BD off-chain no haya sido manipulada
    filas_bd = get_all_telemetria()
    
    # Si se nos pide validar un viaje específico, filtramos las filas de la base de datos
    if numero_viaje and numero_viaje != "ALL":
        filas_bd = [f for f in filas_bd if f["numero_viaje"] == numero_viaje]
        
    bloques_por_hash = {b.hash: b for b in mi_blockchain.cadena}

    for fila in filas_bd:
        hash_esperado = fila["block_hash"]
        
        # El bloque desapareció de la cadena
        if hash_esperado not in bloques_por_hash:
             return jsonify({
                "integridad": False, 
                "razon": f"Fraude Detectado: Registro DB={fila['id']} apunta a un hash fantasma."
            })
             
        # El bloque está, pero vamos a comparar la inmutabilidad de los datos
        bloque = bloques_por_hash[hash_esperado]
        p = bloque.payload
        
        try:
            # Tolerancia leve para los double/float traidos de SQLite
            if p.get("db_id") != fila["id"]: raise ValueError("ID dispar")
            if p.get("numero_viaje") != fila["numero_viaje"]: raise ValueError("Número de viaje modificado")
            if p.get("id_lote") != fila["id_lote"]: raise ValueError("Lote modificado")
            if abs(p.get("lat") - fila["lat"]) > 0.0001: raise ValueError("Latitud alterada")
            if abs(p.get("lon") - fila["lon"]) > 0.0001: raise ValueError("Longitud alterada")
            if abs(p.get("temperatura") - fila["temperatura"]) > 0.001: raise ValueError("Temperatura adulterada")
        except ValueError as err:
            return jsonify({
                "integridad": False, 
                "razon": f"Fraude Detectado (DB manipulada): Registro ID={fila['id']} ha sido alterado. El hash notariado no se corresponde con los datos visibles. Detalle: {str(err)}"
            })

    return jsonify({
        "integridad": True, 
        "razon": "Todos los datos son consistentes e inmutables (Off-chain = On-chain validado por SHA-256)."
    })


if __name__ == '__main__':
    # Habilitamos Flask server en puerto 5000
    app.run(host='0.0.0.0', port=5000, debug=True)
