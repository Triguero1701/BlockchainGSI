const API_URL = "http://127.0.0.1:5000";

// --- INICIALIZAR LEAFLET MAP ---
// Usaremos Leaflet con Dark Theme
let map = L.map('map').setView([39.2800, -2.9700], 12);
L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; <a href="https://carto.com/">CARTO</a>'
}).addTo(map);

// Variables de estado
let markers = [];
let routePolyline = L.polyline([], {color: '#58a6ff', weight: 3}).addTo(map);
let knownBlocks = 0;

// Elementos del DOM
const blocksFeed = document.getElementById("blocksFeed");
const btnAuditar = document.getElementById("btnAuditar");
const auditResult = document.getElementById("auditResult");

function startPolling() {
    setInterval(fetchBlockchain, 2000);
}

// 1. OBTENER BLOCKCHAIN
async function fetchBlockchain() {
    try {
        const res = await fetch(`${API_URL}/blockchain`);
        const data = await res.json();
        
        if (data.longitud > knownBlocks) {
            renderNewBlocks(data.cadena);
            knownBlocks = data.longitud;
        }
    } catch (err) {
        console.error("No se pudo conectar con el backend", err);
    }
}

function renderNewBlocks(cadena) {
    blocksFeed.innerHTML = ""; // Recrear
    
    // Coordenadas para la polyline
    let routeCoords = [];
    
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
        blocksFeed.appendChild(el);
    }
    
    // Render markers on the map
    renderMapPath(cadena);
}

function renderMapPath(cadena) {
    // Limpiamos los markers viejos
    markers.forEach(m => map.removeLayer(m));
    markers = [];
    
    let routeCoords = [];
    
    cadena.forEach(bloque => {
        if(bloque.index === 0) return; // skip genesis
        
        const p = bloque.payload;
        routeCoords.push([p.lat, p.lon]);
        
        // Determina color si se rompe la cadena de frio (>8 grados)
        let alertMarker = p.temperatura > 8 || p.temperatura < 4;
        
        // Create a custom cirle marker
        let marker = L.circleMarker([p.lat, p.lon], {
            radius: 6,
            fillColor: alertMarker ? "#da3633" : "#58a6ff",
            color: "#fff",
            weight: 1,
            opacity: 1,
            fillOpacity: 0.8
        }).addTo(map);
        
        marker.bindPopup(`
            <b>Bloque #${bloque.index}</b><br>
            Hash: ${bloque.hash.substring(0,8)}...<br>
            🌡️ Temp: ${p.temperatura} °C<br>
            🕒 TS: ${new Date(bloque.timestamp).toLocaleTimeString()}
        `);
        
        markers.push(marker);
    });
    
    // Refresh polyline
    routePolyline.setLatLngs(routeCoords);
    
    // Centrar mapa si hay ruta
    if(routeCoords.length > 0) {
        map.panTo(routeCoords[routeCoords.length - 1], {animate: true});
    }
}

// 2. AUDITAR INTEGRIDAD
btnAuditar.addEventListener('click', async () => {
    btnAuditar.innerText = "Auditando algoritmos...";
    btnAuditar.style.opacity = 0.7;
    
    try {
        const res = await fetch(`${API_URL}/auditar`);
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
