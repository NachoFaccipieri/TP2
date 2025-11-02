// MQTT over WebSockets front-end
// Usa mqtt.js (incluido en index.html). Requiere que el broker tenga WebSockets habilitados (ej. Mosquitto en puerto 9001).

const STATUS_EL = document.getElementById('status');
const PERSON_INFO = document.getElementById('person-info');
const NAME_EL = document.getElementById('name');
const CONF_EL = document.getElementById('confidence');

let client = null;

function setStatus(text) {
  STATUS_EL.innerHTML = `<p>${text}</p>`;
}

function resetUI() {
  setStatus('Esperando evento...');
  PERSON_INFO.classList.add('hidden');
}

function onMessage(topic, payload) {
  // payload puede ser JSON o texto
  let msg = null;
  try {
    msg = JSON.parse(payload.toString());
  } catch (e) {
    msg = payload.toString();
  }

  if (topic === 'cerradura/status') {
    setStatus(`ℹ️ ${msg}`);
    return;
  }

  if (topic === 'cerradura/persona') {
    if (typeof msg === 'string') {
      setStatus(msg);
      return;
    }

    if (msg.coincidencia) {
      setStatus(`✅ Coincidencia: ${msg.nombre} (distancia ${Number(msg.distancia).toFixed(3)})`);
      PERSON_INFO.classList.remove('hidden');
      NAME_EL.innerText = `Nombre: ${msg.nombre}`;
      CONF_EL.innerText = `Distancia: ${Number(msg.distancia).toFixed(3)}`;
    } else {
      setStatus('❌ No se encontró coincidencia');
      PERSON_INFO.classList.add('hidden');
    }
  }
}

function connectMqtt() {
  const host = location.hostname || 'localhost';
  // Intentar primero conectar a través de nginx proxy en /mqtt (misma origen).
  // Esto permite usar TLS en nginx y no exponer directamente el puerto 9001.
  const protocol = location.protocol === 'https:' ? 'wss' : 'ws';
  const originPathUrl = `${protocol}://${host}${location.port ? ':' + location.port : ''}/mqtt`;
  const fallbackPort = location.protocol === 'https:' ? 8083 : 9001;
  const fallbackUrl = `${protocol}://${host}:${fallbackPort}`;

  setStatus(`Conectando a broker MQTT (intento proxy /mqtt)...`);

  try {
    // Primero intentamos conectar a /mqtt en el mismo origen (proxy nginx)
    client = mqtt.connect(originPathUrl, { reconnectPeriod: 3000 });
  } catch (e) {
    setStatus('Error al crear cliente MQTT (proxy): ' + e + '. Intentando fallback...');
    try {
      client = mqtt.connect(fallbackUrl, { reconnectPeriod: 3000 });
    } catch (e2) {
      setStatus('Error al crear cliente MQTT (fallback): ' + e2);
      return;
    }
  }

  client.on('connect', () => {
    setStatus('Conectado al broker MQTT');
    // subscribir topics
    client.subscribe('cerradura/persona');
    client.subscribe('cerradura/status');
  });

  client.on('message', (topic, message) => {
    onMessage(topic, message);
  });

  client.on('error', (err) => {
    setStatus('Error MQTT: ' + err);
  });

  client.on('close', () => {
    setStatus('Conexión MQTT cerrada');
    // intentar reconectar en 3s
    setTimeout(() => connectMqtt(), 3000);
  });
}

// Publicar registro
function registrarNuevoRostro() {
  const nombre = prompt('Ingresá el nombre de la persona:');
  if (!nombre) return;
  if (!client || !client.connected) {
    alert('No conectado al broker MQTT');
    return;
  }
  const payload = JSON.stringify({ nombre });
  client.publish('cerradura/registro', payload);
  setStatus(`Enviando petición de registro para "${nombre}"...`);
}

// Publicar timbre
function tocarTimbre() {
  if (!client || !client.connected) {
    alert('No conectado al broker MQTT');
    return;
  }
  client.publish('cerradura/timbre', 'ping');
  setStatus('Timbre enviado. Esperando respuesta...');
}

// Eventos botones
document.getElementById('allow').addEventListener('click', () => { alert('✅ Acceso permitido'); resetUI(); });
document.getElementById('deny').addEventListener('click', () => { alert('❌ Acceso denegado'); resetUI(); });
document.getElementById('register-face').addEventListener('click', registrarNuevoRostro);
document.getElementById('ring-bell').addEventListener('click', tocarTimbre);

// Start
resetUI();
connectMqtt();

