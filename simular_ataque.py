import sqlite3
import os

# Obtener la ruta correcta de la base de datos
BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
DB_FILE = os.path.join(BASE_DIR, "trazabilidad.db")

def simular_ataque():
    print("==========================================================")
    print("      SIMULADOR DE ATAQUE A BASE DE DATOS (OFF-CHAIN)     ")
    print("==========================================================")
    
    print(f"[*] Conectando a la base de datos: {DB_FILE}")
    if not os.path.exists(DB_FILE):
        print("[-] Error: La base de datos no existe.")
        print("    Asegúrate de ejecutar primero el backend y el simulador para generar datos.")
        return

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # Buscar un registro preferiblemente con temperatura fuera de rango (ej. > 7) para ocultar el fraude
    c.execute('SELECT id, lat, lon, temperatura FROM telemetria WHERE temperatura > 7 LIMIT 1')
    row = c.fetchone()

    # Si no hay ninguno > 7, coger el último
    if not row:
        c.execute('SELECT id, lat, lon, temperatura FROM telemetria ORDER BY id DESC LIMIT 1')
        row = c.fetchone()

    if not row:
        print("[-] No hay registros en la tabla 'telemetria'. Deja correr el simulador unos segundos.")
        conn.close()
        return

    record_id, lat, lon, temp_original = row
    
    # Supongamos que la temperatura legal es 4.5
    temp_falsa = 4.5

    print(f"[*] Objetivo localizado -> ID: {record_id}")
    print(f"    - Latitud:     {lat}")
    print(f"    - Longitud:    {lon}")
    print(f"    - Temp real:   {temp_original} °C")
    
    print(f"\n[!] INYECTANDO VALOR FALSO DE TEMPERATURA: {temp_falsa} °C...")

    # Ejecutar UPDATE saltándose la lógica de backend
    c.execute('UPDATE telemetria SET temperatura = ? WHERE id = ?', (temp_falsa, record_id))
    conn.commit()

    # Verificar el cambio
    c.execute('SELECT temperatura FROM telemetria WHERE id = ?', (record_id,))
    nueva_temp = c.fetchone()[0]

    if nueva_temp == temp_falsa:
        print("\n[+] ¡ATAQUE EJECUTADO CON ÉXITO!")
        print("[+] La base de datos relacional (Off-Chain) ha sido alterada.")
        print("[+] Ahora mismo los datos de sanidad mostrarían todo correcto.")
        print("\n[?] ¿Será capaz el sistema de descubrir la manipulación?")
        print("    Vaya al Frontend (Dashboard) y haga clic en 'Auditar Integridad'.")
    else:
        print("\n[-] El ataque falló. No se pudo sobrescribir el registro.")

    conn.close()

if __name__ == "__main__":
    simular_ataque()
