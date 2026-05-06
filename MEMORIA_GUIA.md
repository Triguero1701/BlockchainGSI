# GUÍA PARA GENERAR LA MEMORIA DEL PROYECTO
# Sistema de Trazabilidad Blockchain — Queso Manchego (GSI)

> **Instrucción para el agente:** Usando esta guía, genera un documento de memoria técnica
> en formato Markdown de más de 10 páginas (mínimo ~4000 palabras). Debe tener tono académico
> formal y estar en español. El documento final debe guardarse como `MEMORIA.md` en la raíz del proyecto.

---

## 1. DATOS DEL PROYECTO

- **Título:** Sistema de Trazabilidad Espacio-Temporal con Blockchain para Cadena de Frío
- **Asignatura:** Gestión de Sistemas de Información (GSI)
- **Tipo:** Prueba de Concepto (PoC)
- **Caso de uso:** Transporte frigorífico de Queso Manchego (Castilla-La Mancha)
- **Repositorio:** BlockchainGSI
- **Fecha inicio:** 28 marzo 2026
- **Fecha última versión:** 4 mayo 2026
- **Total líneas de código:** ~1079

## 2. ESTRUCTURA DE CAPÍTULOS RECOMENDADA

### Portada
- Título, asignatura, autor(es), fecha, universidad

### Capítulo 1: Introducción (1-1.5 páginas)
- Contexto: industria alimentaria, cadena de frío, normativa sanitaria
- Problema: manipulación de registros de temperatura en transporte refrigerado
- Objetivo: demostrar que blockchain puede garantizar inmutabilidad de datos de trazabilidad
- Alcance: PoC educativa, no red pública, SHA-256 nativo

### Capítulo 2: Estado del Arte y Marco Teórico (1.5-2 páginas)
- Blockchain: definición, tipos (pública, privada, consorcio)
- Hashing criptográfico: SHA-256, propiedades (determinismo, avalancha, irreversibilidad)
- Modelo híbrido On-Chain / Off-Chain: ventajas de rendimiento
- Trazabilidad alimentaria: normativas EU (Reglamento CE 178/2002), APPCC
- IoT en logística: sensores de temperatura, GPS, telemetría
- Tecnologías similares: IBM Food Trust, VeChain, TE-FOOD

### Capítulo 3: Análisis de Requisitos (1 página)
- **Requisitos funcionales:**
  - RF1: Registrar datos de telemetría (lat, lon, temperatura, lote, viaje)
  - RF2: Sellar cada registro con hash SHA-256 en blockchain
  - RF3: Almacenar datos legibles off-chain en SQLite
  - RF4: Visualizar rutas en tiempo real sobre mapa
  - RF5: Auditar integridad comparando on-chain vs off-chain
  - RF6: Detectar manipulaciones en base de datos
  - RF7: Simular múltiples viajes concurrentes
  - RF8: Filtrar y auditar por viaje individual
- **Requisitos no funcionales:**
  - RNF1: Sin dependencias de redes externas (Ethereum, Hyperledger)
  - RNF2: Despliegue simple (Python + navegador)
  - RNF3: Interfaz oscura, moderna, responsiva
  - RNF4: Containerización con Docker

### Capítulo 4: Arquitectura del Sistema (2 páginas)
- **Diagrama de 4 capas** (describir y dibujar en texto):
  1. **Capa Core (blockchain.py, 67 líneas):** Clase `Bloque` y `Blockchain`. Bloque génesis. `calcular_hash()` con JSON determinista + SHA-256. `validar_cadena()` recorre toda la cadena verificando hashes.
  2. **Capa de Persistencia Híbrida (database.py, 70 líneas):** SQLite3. Tabla `telemetria` con campos: id, numero_viaje, id_lote, lat, lon, temperatura, timestamp, block_hash. Modelo: dato crudo off-chain + hash notarial on-chain.
  3. **Capa de Ingesta IoT (simulador.py, 165 líneas):** Simula sensores GPS y temperatura. Usa OSRM para rutas reales por carretera. 3 rutas preconfiguradas (Ciudad Real→Membrilla, Valdepeñas→Manzanares, Daimiel→Almagro). Avance metro a metro, fluctuaciones termodinámicas.
  4. **Capa de Visualización (frontend/, ~576 líneas):** HTML5 + CSS Variables + Vanilla JS. Mapa Leaflet.js con tema oscuro (CartoDB Dark). Long-polling cada 2s. Feed de bloques en vivo. Selector de viajes. Botón de auditoría forense.
  5. **Herramienta de ataque (simular_ataque.py, 70 líneas):** Acceso directo a SQLite saltándose el backend. Modifica temperatura a 4.5°C para encubrir rotura de cadena de frío.

- **API REST (main.py, 131 líneas):** Flask + Flask-CORS
  - `POST /sensor` → recibe telemetría, inserta off-chain, mina bloque, actualiza hash
  - `GET /blockchain` → devuelve cadena completa
  - `GET /telemetria` → devuelve todos los registros off-chain
  - `GET /auditar?numero_viaje=X` → valida cadena + compara off-chain vs on-chain

### Capítulo 5: Decisiones Técnicas y Justificación (1.5 páginas)
- **¿Por qué blockchain propia y no Ethereum/Hyperledger?** → Fines educativos, control total, sin costes de gas, simplicidad para PoC
- **¿Por qué SHA-256?** → Estándar de la industria, usado en Bitcoin, resistente a colisiones
- **¿Por qué modelo híbrido on/off-chain?** → Las blockchain son lentas para queries; SQLite permite consultas SQL rápidas; el hash garantiza la integridad
- **¿Por qué Flask?** → Microframework ligero, ideal para APIs REST, mínima configuración
- **¿Por qué SQLite?** → Sin servidor, archivo único, ideal para PoC, integrado en Python
- **¿Por qué Leaflet.js?** → Open source, ligero, soporte de tiles oscuros (CartoDB)
- **¿Por qué OSRM?** → API gratuita de routing, rutas reales por carretera, no líneas rectas
- **¿Por qué Vanilla JS sin frameworks?** → Demostrar que no se necesita React/Vue para un dashboard funcional
- **¿Por qué Docker?** → Reproducibilidad, despliegue con un solo comando, aislamiento

### Capítulo 6: Implementación Detallada (2 páginas)
- **Flujo de datos completo:** Sensor → POST /sensor → insert_telemetria() → agregar_bloque() → update_block_hash() → respuesta 201
- **Algoritmo de sellado:** JSON canónico (sort_keys=True) → encode UTF-8 → SHA-256 → hexdigest
- **Algoritmo de auditoría:** 1) validar_cadena() recorre bloques verificando hash actual y previous_hash. 2) Comparar campo a campo cada registro off-chain vs payload on-chain con tolerancia float.
- **Simulación de movimiento:** OSRM devuelve geometría GeoJSON. El simulador avanza STEP_SIZE_DEGREES por tick. Interpolación lineal entre waypoints.
- **Modelo térmico:** Temperatura base 4°C. Fluctuación aleatoria ±0.1°C. 5% probabilidad de pico +0.5-1.0°C. En destino 20% probabilidad de subida (puerta abierta). Retorno gradual (compresor: diff*0.15).
- **Docker Compose:** 3 servicios (backend:5000, frontend:80 via nginx:alpine, simulador). Red interna Docker para comunicación entre servicios.

### Capítulo 7: Demostración y Pruebas (1 página)
- **Escenario normal:** Arrancar backend → abrir frontend → arrancar simulador → ver rutas en vivo
- **Escenario de ataque:** Con sistema en marcha → ejecutar simular_ataque.py → dashboard muestra "todo OK" visualmente → clic en Auditar → FRAUDE DETECTADO con detalle del registro adulterado
- **Resultados esperados:** La auditoría detecta la discrepancia entre el hash sellado on-chain y los datos modificados off-chain
- **Capturas de pantalla:** (indicar que se deben incluir capturas del dashboard, del ataque, y de la auditoría)

### Capítulo 8: Evolución del Proyecto (0.5 páginas)
- Historial de commits:
  - 28/03/2026: Primer commit — PoC básica con 1 ruta
  - 27/04/2026: Script de ataque, aumento de pedidos
  - 30/04/2026: Multi-viaje, filtrado por viaje, bloques clicables, parada en destino
  - 04/05/2026: Soporte Docker, actualización README

### Capítulo 9: Limitaciones y Trabajo Futuro (1 página)
- **Limitaciones actuales:**
  - Blockchain solo en memoria (se pierde al reiniciar)
  - Sin Proof of Work / Proof of Stake (no hay minado real)
  - Nodo único (no distribuido)
  - Sin autenticación en la API
  - Sin HTTPS
  - OSRM depende de servidor público externo
- **Trabajo futuro:**
  - Persistir blockchain en disco o base de datos
  - Implementar consenso distribuido (múltiples nodos)
  - Migrar a Hyperledger Fabric para producción
  - Añadir autenticación JWT
  - Dashboard con históricos y gráficas de temperatura
  - Alertas automáticas por email/SMS
  - Integración con sensores IoT reales (Raspberry Pi, Arduino)
  - Smart contracts para automatizar sanciones

### Capítulo 10: Conclusiones (0.5 páginas)
- La PoC demuestra exitosamente que la criptografía SHA-256 y la estructura blockchain pueden garantizar la inmutabilidad de datos de trazabilidad
- El modelo híbrido on-chain/off-chain es viable y eficiente para aplicaciones reales
- La detección de fraude funciona: cualquier modificación directa en la BD es detectada
- La tecnología blockchain tiene un potencial significativo en la industria alimentaria

### Referencias / Bibliografía
- Nakamoto, S. (2008). Bitcoin: A Peer-to-Peer Electronic Cash System
- Reglamento (CE) 178/2002 del Parlamento Europeo
- NIST FIPS 180-4 (Secure Hash Standard)
- Documentación Flask: https://flask.palletsprojects.com/
- Documentación Leaflet.js: https://leafletjs.com/
- OSRM API: http://project-osrm.org/
- IBM Food Trust: https://www.ibm.com/food

---

## 3. STACK TECNOLÓGICO (para tabla en la memoria)

| Componente | Tecnología | Versión | Propósito |
|---|---|---|---|
| Backend API | Flask | 3.0.0 | Servidor REST |
| CORS | Flask-CORS | 4.0.0 | Acceso cross-origin |
| HTTP Client | Requests | 2.31.0 | Comunicación simulador→API |
| Base de datos | SQLite3 | (stdlib) | Persistencia off-chain |
| Criptografía | hashlib (SHA-256) | (stdlib) | Sellado de bloques |
| Frontend | HTML5 + CSS3 + JS | ES6+ | Dashboard interactivo |
| Mapas | Leaflet.js | 1.9.4 | Visualización geoespacial |
| Tiles | CartoDB Dark | — | Tema oscuro del mapa |
| Routing | OSRM | Público | Rutas reales por carretera |
| Contenedores | Docker + Compose | 3.8 | Despliegue automatizado |
| Servidor web | Nginx Alpine | — | Servir frontend estático |
| Lenguaje | Python | 3.10+ | Backend y simulador |

## 4. ARCHIVOS DEL PROYECTO (para anexo)

```
BlockchainGSI/
├── backend/
│   ├── Dockerfile          (13 líneas)
│   ├── blockchain.py       (67 líneas) — Motor blockchain + SHA-256
│   ├── database.py         (70 líneas) — Capa SQLite off-chain
│   └── main.py             (131 líneas) — API REST Flask
├── frontend/
│   ├── Dockerfile          (8 líneas)
│   ├── index.html          (59 líneas) — Estructura HTML del dashboard
│   ├── style.css           (272 líneas) — Diseño oscuro con CSS Variables
│   └── app.js              (245 líneas) — Lógica: polling, mapa, auditoría
├── simulador/
│   ├── Dockerfile          (11 líneas)
│   └── simulador.py        (165 líneas) — Emulador IoT multi-ruta
├── docker-compose.yml      (30 líneas) — Orquestación de servicios
├── requirements.txt        (3 deps) — Dependencias Python
├── simular_ataque.py       (70 líneas) — Herramienta de ataque
├── README.md               — Guía de instalación y uso
└── Agent.md                — Documentación arquitectónica
```

## 5. RUTAS SIMULADAS

| Viaje | Lote | Origen | Destino |
|---|---|---|---|
| VIAJE-001 | QUESO_MANCHEGO_001 | Ciudad Real (38.9856, -3.9189) | Membrilla (38.9744, -3.3486) |
| VIAJE-002 | QUESO_MANCHEGO_002 | Valdepeñas (38.7597, -3.3841) | Manzanares (38.9959, -3.3692) |
| VIAJE-003 | QUESO_MANCHEGO_003 | Daimiel (39.0700, -3.6160) | Almagro (38.8908, -3.7110) |

## 6. ENDPOINTS API

| Método | Ruta | Descripción | Código éxito |
|---|---|---|---|
| POST | /sensor | Recibe JSON telemetría, crea bloque | 201 |
| GET | /blockchain | Devuelve cadena completa | 200 |
| GET | /telemetria | Devuelve registros off-chain | 200 |
| GET | /auditar?numero_viaje=X | Audita integridad | 200 |

## 7. ESQUEMA BASE DE DATOS

```sql
CREATE TABLE telemetria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero_viaje TEXT NOT NULL,
    id_lote TEXT NOT NULL,
    lat REAL NOT NULL,
    lon REAL NOT NULL,
    temperatura REAL NOT NULL,
    timestamp REAL NOT NULL,
    block_hash TEXT
);
```

## 8. NOTAS ADICIONALES PARA REDACCIÓN

- Usar tono formal académico en tercera persona
- Incluir diagramas: arquitectura por capas, flujo de datos, secuencia del ataque
- Mencionar que el proyecto se desarrolló de forma iterativa (ver commits)
- Destacar que NO se usa ningún framework blockchain externo
- El bloque génesis tiene timestamp=0 y previous_hash de 64 ceros
- La tolerancia en auditoría para floats es 0.0001 (coordenadas) y 0.001 (temperatura)
- El frontend usa long-polling cada 2 segundos (no WebSockets)
- Los colores de ruta son: azul, verde, amarillo, púrpura, rojo, cyan
- El frontend marca en rojo temperaturas >8°C o <4°C
