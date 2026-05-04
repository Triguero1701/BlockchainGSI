# Sistema Trazabilidad Blockchain - Queso Manchego

Prueba de Concepto (PoC) sobre la validación de integridad inmutable en sistemas de transporte frigorífico utilizando criptografía SHA-256 (Notaría Blockchain + SQLite SQLite Off-Chain Data).

## 📌 Requisitos Previos
* **Python 3.9+** instalado en el sistema.
* Un navegador moderno (Chrome, Firefox, Safari).
* Conexión a internet (para descargar los mapas de Leaflet y contactar a OSRM para trazar las carreteras).
* *(Opcional)* **Docker** y **Docker Compose** si prefieres la ejecución automatizada mediante contenedores.

---

## 🐳 Instalación y Ejecución con Docker (Recomendado)

Si tienes Docker instalado en tu sistema, puedes levantar toda la infraestructura (backend, frontend y simulador) con un solo comando:

1. Abre una terminal en la raíz del proyecto.
2. Ejecuta el siguiente comando:
```bash
docker-compose up --build
```
3. Abre tu navegador y accede a: [http://localhost](http://localhost)

*(El simulador arrancará automáticamente y empezarás a ver la ruta del camión en tiempo real).*

---

## 🛠 Instalación y Configuración (Modo Local)

Sigue estos 3 pasos básicos desde la terminal abierta en la raíz de este proyecto:

1. **Crea el Entorno Virtual (Aislado)**:
```bash
python -m venv venv
```

2. **Activa el Entorno Virtual**:
* En **Windows** (PowerShell o CMD):
```bash
.\venv\Scripts\activate
```
* En **Mac/Linux** (Bash):
```bash
source venv/bin/activate
```

3. **Instala las Dependencias**:
```bash
pip install -r requirements.txt
```

---

## 🚀 Cómo arrancar la Demostración (Modo Local)

La PoC se compone de elementos desconectados que hay que encender simultáneamente. Necesitarás tener tu pantalla compartida o abierta con al menos dos consolas y el navegador.

### Paso 1: Levantar los Servidores Centrales (Notaría y BD)
Abre tu primera terminal con el entorno virtual activado y ejecuta:
```bash
python backend/main.py
```
*(Verás que el Framework `Flask` indica que está corriendo en http://127.0.0.1:5000)*

### Paso 2: Abrir el Cuadro de Mando Visual (Frontend)
No hace falta levantar ningún servidor de Node.js ni Nginx. Ve a la carpeta `frontend` y simplemente dale doble clic al archivo `index.html` (o arrástralo a tu navegador favorito). Verás el panel oscuro de mapas, pero no verás el camión... porque el camión aún no ha arrancado el motor.

### Paso 3: Arrancar el Camión / Sensores IoT (Simulador)
Abre **otra consola/terminal nueva** (activa de nuevo tu entorno virtual con `.\venv\Scripts\activate`) y ejecuta:
```bash
python simulador/simulador.py
```
*(Inmediatamente verás como la consola empieza a trazar puntos y el mapa de tu navegador empieza a moverse metro a metro de la A-43 mientras sella los datos térmica e inmutablemente en el servidor.)*

---

## 💥 Cómo probar el Sistema Antifraude y Hackeos

Si en tu presentación quieres demostrar qué pasa cuando una persona "hackea" tu base de datos centralizada (para engañar a Sanidad y decir que no ha roto la cadena de frío), puedes utilizar el script automatizado que hemos preparado:

1. Con los servidores en marcha (Backend y Simulador de sensores), abre una **tercera consola/terminal** (asegúrate de tener el entorno virtual activado con `.\venv\Scripts\activate`).
2. Ejecuta el script de ataque malicioso:
```bash
python simular_ataque.py
```
*(El script buscará automáticamente en la base de datos Off-Chain un registro con exceso de temperatura y lo modificará en crudo a 4.5 °C para tratar de encubrirlo).*

3. Vuelve a tu **Dashboard y haz clic en "Auditar Integridad"**. El frontal se pondrá rojo sangre informando al momento de que *"La firma criptográfica Blockchain no se corresponde con el valor falsificado en la BD. FRAUDE DETECTADO!"*.

*(Nota: Para limpiar toda la simulación, basta con parar el Servidor Backend **Ctrl+C** y volverlo a ejecutar. Su memoria se auto-limpiará).*
