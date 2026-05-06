const API_URL = "http://127.0.0.1:5000";

// --- INICIALIZAR LEAFLET MAP ---
// Usaremos Leaflet con Dark Theme
let map = L.map('map').setView([39.2800, -2.9700], 12);
L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; <a href="https://carto.com/">CARTO</a>'
}).addTo(map);

// Variables de estado
let markers = [];
let routePolylines = [];
let knownBlocks = 0;

const ROUTE_COLORS = ['#58a6ff', '#2ea043', '#f2cc60', '#bc8cff', '#ff7b72', '#39c5bb'];

// Elementos del DOM
const blocksFeed = document.getElementById("blocksFeed");
const btnAuditar = document.getElementById("btnAuditar");
const auditResult = document.getElementById("auditResult");
const tripSelector = document.getElementById("tripSelector");
const btnAddTrip = document.getElementById("btnAddTrip");
const tripInstructions = document.getElementById("tripInstructions");
let latestCadena = [];

let isSelectingTrip = false;
let tripStart = null;
let tempMarkers = [];


function startPolling() {
    setInterval(fetchBlockchain, 2000);
}

// 1. OBTENER BLOCKCHAIN
async function fetchBlockchain() {
    try {
        const res = await fetch(`${API_URL}/blockchain`);
        const data = await res.json();
        
        if (data.longitud > knownBlocks) {
            latestCadena = data.cadena;
            renderNewBlocks(data.cadena);
            populateTripSelector(data.cadena);
            knownBlocks = data.longitud;
        }
    } catch (err) {
        console.error("No se pudo conectar con el backend", err);
    }
}

function renderNewBlocks(cadena) {
    blocksFeed.innerHTML = ""; // Recrear
    
    // Renderizamos iterando desde el más nuevo al más viejo
    for(let i = cadena.length - 1; i >= 0; i--) {
        const bloque = cadena[i];
        const isGenesis = i === 0;
        
        const el = document.createElement('div');
        el.className = `block-item ${isGenesis ? 'genesis' : 'normal'}`;
        
        let payloadHtml = "";
        
        if(isGenesis) {
            payloadHtml = `<p><span>Mensaje:</span> <span class="val">Bloque Genesis</span></p>`;
        } else {
            const p = bloque.payload;
            
            // Add to route coords array (we do it here but order matters for polyline)
            // Polyline needs from genesis to newest
            let tempColor = p.temperatura > 8 || p.temperatura < 4 ? "warning" : "";
            
            payloadHtml = `
                <p><span>Viaje:</span> <span class="val" style="color:#58a6ff;">${p.numero_viaje || 'N/A'}</span></p>
                <p><span>Temp:</span> <span class="val ${tempColor}">${p.temperatura} °C</span></p>
                <p><span>Lat/Lon:</span> <span class="val">${p.lat}, ${p.lon}</span></p>
                <p><span>DB ID Off-Chain:</span> <span class="val">${p.db_id}</span></p>
            `;
        }

        let idLote = !isGenesis ? bloque.payload.id_lote : "INIT";
        
        // Hash formatting
        let hashFmt = bloque.hash.substring(0, 15) + "...";

        el.innerHTML = `
            <div class="block-header">
                <span class="block-id">Bloque #${bloque.index} - ${idLote}</span>
                <span class="block-hash" title="${bloque.hash}">${hashFmt}</span>
            </div>
            <div class="block-payload">
                ${payloadHtml}
            </div>
        `;
        
        if (!isGenesis) {
            el.style.cursor = 'pointer';
            el.title = "Haz clic para centrar en el mapa";
            el.addEventListener('click', () => {
                map.flyTo([bloque.payload.lat, bloque.payload.lon], 15, { animate: true });
            });
        }
        
        blocksFeed.appendChild(el);
    }
    
    // Render markers on the map
    renderMapPath(cadena);
}

function renderMapPath(cadena) {
    // Limpiamos los markers viejos
    markers.forEach(m => map.removeLayer(m));
    markers = [];
    routePolylines.forEach(poly => map.removeLayer(poly));
    routePolylines = [];
    
    const puntosPorLote = {};
    let ultimoPunto = null;
    
    cadena.forEach(bloque => {
        if(bloque.index === 0) return; // skip genesis
        
        const p = bloque.payload;
        const lote = p.id_lote || 'SIN_LOTE';

        if (!puntosPorLote[lote]) {
            puntosPorLote[lote] = [];
        }
        puntosPorLote[lote].push({
            coord: [p.lat, p.lon],
            temperatura: p.temperatura,
            bloque
        });

        ultimoPunto = [p.lat, p.lon];
    });

    const lotes = Object.keys(puntosPorLote).sort();

    lotes.forEach((lote, idx) => {
        const colorRuta = ROUTE_COLORS[idx % ROUTE_COLORS.length];
        const puntos = puntosPorLote[lote];
        const routeCoords = puntos.map(x => x.coord);

        const polyline = L.polyline(routeCoords, {color: colorRuta, weight: 3, opacity: 0.9}).addTo(map);
        routePolylines.push(polyline);

        puntos.forEach(item => {
            const p = item.bloque.payload;
            const b = item.bloque;
        
            // Determina color si se rompe la cadena de frio (>8 grados o <4 grados)
            let alertMarker = p.temperatura > 8 || p.temperatura < 4;
        
            let marker = L.circleMarker([p.lat, p.lon], {
                radius: 6,
                fillColor: alertMarker ? "#da3633" : colorRuta,
                color: "#fff",
                weight: 1,
                opacity: 1,
                fillOpacity: 0.8
            }).addTo(map);
        
            marker.bindPopup(`
                <b>Bloque #${b.index}</b><br>
                Lote: ${lote}<br>
                Hash: ${b.hash.substring(0,8)}...<br>
                🌡️ Temp: ${p.temperatura} °C<br>
                🕒 TS: ${new Date(b.timestamp).toLocaleTimeString()}
            `);
        
            markers.push(marker);
        });
    });

    // El auto-centrado ha sido desactivado (requisito 1)
}

function populateTripSelector(cadena) {
    const currentVal = tripSelector.value;
    const trips = new Set();
    cadena.forEach(b => {
        if (b.index > 0 && b.payload && b.payload.numero_viaje) {
            trips.add(b.payload.numero_viaje);
        }
    });

    if (tripSelector.options.length - 1 !== trips.size) {
        tripSelector.innerHTML = '<option value="ALL">Todos los viajes</option>';
        Array.from(trips).sort().forEach(trip => {
            const opt = document.createElement("option");
            opt.value = trip;
            opt.innerText = trip;
            tripSelector.appendChild(opt);
        });
        
        // Mantener seleccion
        if (Array.from(tripSelector.options).some(o => o.value === currentVal)) {
            tripSelector.value = currentVal;
        }
    }
}

tripSelector.addEventListener('change', () => {
    const selected = tripSelector.value;
    let coords = [];
    latestCadena.forEach(b => {
        if(b.index > 0 && b.payload && b.payload.lat && b.payload.lon) {
            if (selected === "ALL" || b.payload.numero_viaje === selected) {
                coords.push([b.payload.lat, b.payload.lon]);
            }
        }
    });
    
    if (coords.length > 0) {
        map.fitBounds(coords, {padding: [50, 50], animate: true});
    }
});

// 2. AUDITAR INTEGRIDAD
btnAuditar.addEventListener('click', async () => {
    btnAuditar.innerText = "Auditando algoritmos...";
    btnAuditar.style.opacity = 0.7;
    
    try {
        const viajeId = tripSelector.value;
        const res = await fetch(`${API_URL}/auditar?numero_viaje=${viajeId}`);
        const result = await res.json();
        
        auditResult.className = `alert ${result.integridad ? 'success' : 'error'}`;
        auditResult.innerHTML = `
            <strong>${result.integridad ? '✅ Integridad Confirmada' : '❌ BRECHA DE INTEGRIDAD'}</strong><br>
            ${result.razon}
        `;
        auditResult.classList.remove('hidden');
    } catch (err) {
        auditResult.className = 'alert error';
        auditResult.innerHTML = "Error al intentar contactar al servidor.";
        auditResult.classList.remove('hidden');
    } finally {
        setTimeout(()=> {
            btnAuditar.innerText = "🔍 Auditar Integridad";
            btnAuditar.style.opacity = 1;
        }, 500);
    }
});

// Iniciamos app
fetchBlockchain();
startPolling();

// 3. AÑADIR VIAJE INTERACTIVO
btnAddTrip.addEventListener("click", () => {
    isSelectingTrip = true;
    tripStart = null;
    tempMarkers.forEach(m => map.removeLayer(m));
    tempMarkers = [];
    document.getElementById("map").classList.add("map-selecting");
    tripInstructions.innerHTML = "Haz clic en el mapa para el <b>punto de inicio</b>.";
    tripInstructions.classList.remove("hidden");
    btnAddTrip.disabled = true;
});

map.on('click', async function(e) {
    if (!isSelectingTrip) return;
    
    const latlng = e.latlng;
    
    if (!tripStart) {
        tripStart = [latlng.lat, latlng.lng];
        let marker = L.circleMarker(tripStart, {
            radius: 8, fillColor: "#f2cc60", color: "#fff", weight: 2, opacity: 1, fillOpacity: 0.9
        }).addTo(map);
        tempMarkers.push(marker);
        tripInstructions.innerHTML = "Ahora selecciona el <b>punto de destino</b> en el mapa.";
    } else {
        const tripEnd = [latlng.lat, latlng.lng];
        let marker = L.circleMarker(tripEnd, {
            radius: 8, fillColor: "#f2cc60", color: "#fff", weight: 2, opacity: 1, fillOpacity: 0.9
        }).addTo(map);
        tempMarkers.push(marker);
        
        tripInstructions.innerHTML = "Enviando solicitud de viaje...";
        document.getElementById("map").classList.remove("map-selecting");
        
        let maxViaje = 0;
        latestCadena.forEach(b => {
            if (b.index > 0 && b.payload && b.payload.numero_viaje) {
                let match = b.payload.numero_viaje.match(/VIAJE-(\d+)/);
                if (match) {
                    let num = parseInt(match[1]);
                    if (num > maxViaje) maxViaje = num;
                }
            }
        });
        const nextNum = maxViaje + 1;
        const numViajeStr = nextNum.toString().padStart(3, '0');
        
        const numViaje = "VIAJE-" + numViajeStr;
        const idLote = "QUESO_MANCHEGO_" + numViajeStr;
        
        try {
            await fetch(`${API_URL}/viaje`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    numero_viaje: numViaje,
                    id_lote: idLote,
                    start: tripStart,
                    end: tripEnd
                })
            });
            tripInstructions.innerHTML = "¡Viaje añadido a la simulación!";
        } catch (err) {
            tripInstructions.innerHTML = "Error al contactar con el backend.";
            console.error(err);
        }
        
        setTimeout(() => {
            tripInstructions.classList.add("hidden");
            btnAddTrip.disabled = false;
            isSelectingTrip = false;
            tripStart = null;
            tempMarkers.forEach(m => map.removeLayer(m));
            tempMarkers = [];
        }, 3000);
    }
});
