# Resumen del Proyecto: Trazabilidad Espacio-Temporal Blockchain (PoC)

Este proyecto nace como una Prueba de Concepto (PoC) técnica diseñada para la asignatura de **Gestión de Sistemas de Información**. 

Su objetivo principal es ensayar, de forma práctica y sin frameworks externos, cómo la tecnología de Registros Distribuidos (Blockchain / DLT) y la criptografía de hash pueden asegurar la inmutabilidad de los datos referidos a la trazabilidad logística de la cadena de frío (ej. Queso Manchego).

## Marco Arquitectónico de 4 Capas

La solución se divide en cuatro capas claramente abstraídas para demostrar el ciclo completo de la información desde su recolección física hasta su auditoría algorítmica:

### 1. Capa Core (Criptografía y Blockchain Nativa)
Para fines educacionales, **no se utilizan redes públicas (Ethereum, Hyperledger)** ni contratos inteligentes de la industria. Todo el motor DLT está codificado en la clase `Blockchain` (`backend/blockchain.py`). 
* Utiliza el algoritmo de digestión **SHA-256**.
* Contiene una validación nativa (`validar_cadena()`) que recomputa la entropía completa de la cadena para descubrir fisuras lógicas en cualquier eslabón de la historia.

### 2. Capa de Persistencia Híbrida (Off-Chain / On-Chain)
Alojada en el backend `backend/database.py`, esta capa utiliza un modelo **híbrido** implementado con `SQLite3`:
* El *"Payload Crudo"* legible (Coordenadas, Temperatura, ID de Lote) se guarda de manera relacional (Off-Chain) permitiendo realizar consultas ágiles en SQL sin el coste y lentitud que requeriría la Blockchain.
* La *"Notaría Criptográfica"* (El Hash generado de esos datos sellados por el Bloque) se añade a ese registro. Cualquier alteración de los datos Off-Chain romperá su concordancia matemática con el Hash sellado On-Chain.

### 3. Capa de Ingesta (Simulador de Telemetría IoT)
Emula los sensores instalados en una flota de transporte refrigerado (`simulador/simulador.py`).
* Realiza peticiones `HTTP POST` enviando objetos JSON hacia la API de la capa de persistencia.
* **Componente de Realismo Motor**: Integra conexión a la **Open Source Routing Machine (OSRM)** para obtener la representación geométrica real (curvas completas) de la Autovía A-43 (Ciudad Real -> Membrilla) y mueve el sensor metro a metro simulando un GPS sobre asfalto además de aplicar fluctuaciones termodinámicas aleatorias simulando el compresor frigorífico.
* **Soporte Multi-Viaje**: Permite configurar y simular diferentes rutas concurrentemente (ej. Ciudad Real -> Membrilla, Valdepeñas -> Manzanares), asignando un identificador único de viaje (`numero_viaje`) a cada flujo de telemetría.

### 4. Capa de Visualización (Dashboard Forense UI)
El frontal visual interactivo desarrollado en HTML5, CSS Variables y Vanilla JS.
* A diferencia de otros Dashboards estáticos, este funciona mediante **Long-Polling** pasivo contra el servidor, "dibujando" la cadena en vivo sobre la cartografía de `Leaflet.js` y alertando si la temperatura sale de rango (`>8 °C`).
* Actúa como centro forense ejecutando llamadas REST (`GET /auditar`) que obligan al Core a re-analizar toda la estructura matemática para buscar discrepancias (simulación de fraudes y hackeos).
* **Filtrado y Auditoría por Viaje**: Incluye un selector dinámico para aislar visualmente las rutas en el mapa y focalizar la auditoría criptográfica en un viaje específico.

### 5. Herramienta de Auditoría y Simulación de Ataques (Opcional)
Para facilitar la demostración de la inmutabilidad y la respuesta del sistema frente a modificaciones malintencionadas, se incluye el script `simular_ataque.py`.
* Actúa como un **actor malicioso** que se salta la lógica de la aplicación y accede directamente a la capa de persistencia Off-Chain (base de datos relacional).
* Modifica sigilosamente los valores de los registros (ej. altera una temperatura alta para encubrir la ruptura de la cadena de frío).
* Permite poner a prueba la capa *Core Blockchain* en tiempo real durante las auditorías, forzando la detección y localización exacta de los eslabones adulterados.
