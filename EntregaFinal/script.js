// MQTT over WebSockets front-end
// Usa mqtt.js (incluido en index.html). Requiere que el broker tenga WebSockets habilitados (ej. Mosquitto en puerto 9001).

const STATUS_EL = document.getElementById('status');
const PERSON_INFO = document.getElementById('person-info');
const NAME_EL = document.getElementById('name');
const CONF_EL = document.getElementById('confidence');

let client = null;
let registroSolicitado = false;

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
    
    // Detectar si es un mensaje de rostro registrado
    if (msg.includes('registrado') || msg.includes('Rostro')) {
      setStatus(`✅ Rostro registrado correctamente`);
      // Limpiar después de 5 segundos
      setTimeout(() => {
        resetUI();
      }, 5000);
    }
    return;
  }

  if (topic === 'cerradura/persona') {
    if (typeof msg === 'string') {
      setStatus(msg);
      return;
    }

    // Mostrar la imagen capturada siempre
    document.getElementById('camera-preview').classList.remove('hidden');
    refreshCamera();

    if (msg.coincidencia) {
      setStatus(`✅ Coincidencia con ${msg.nombre}: ${msg.porcentaje}%`);
      NAME_EL.innerText = `Nombre: ${msg.nombre}`;
      CONF_EL.innerText = `Coincidencia: ${msg.porcentaje}%`;
      PERSON_INFO.classList.remove('hidden');
    } else {
      setStatus(`❌ No se encontró coincidencia`);
      PERSON_INFO.classList.add('hidden');
    }
  }
}

function connectMqtt() {
  const host = location.hostname || 'localhost';
  // Conectar directamente al broker MQTT WebSocket (puerto 9001 por defecto)
  const protocol = location.protocol === 'https:' ? 'wss' : 'ws';
  const wsPort = 9001; // Puerto WebSocket de Mosquitto
  const brokerUrl = `${protocol}://${host}:${wsPort}`;

  setStatus(`Conectando a broker MQTT en ${brokerUrl}...`);

  // Construir opciones MQTT a partir de configuración global (si existe)
  // window.MQTT_CONFIG puede definirse en index.html. Ej:
  // <script>window.MQTT_CONFIG = { username: 'miuser', password: 'miclave' }</script>
  const baseOptions = { reconnectPeriod: 3000 };
  const mqttConfig = (window && window.MQTT_CONFIG) ? window.MQTT_CONFIG : {};
  const options = Object.assign({}, baseOptions, mqttConfig);

  try {
    client = mqtt.connect(brokerUrl, options);
  } catch (e) {
    setStatus('Error al crear cliente MQTT: ' + e);
    return;
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
  
  // Marcar que se solicita registro
  registroSolicitado = true;
  
  const payload = JSON.stringify({ nombre });
  client.publish('cerradura/registro', payload);
  setStatus(`Esperando... Presiona el botón físico para registrar a "${nombre}"`);
  
  // Actualizar imagen al registrar
  setTimeout(refreshCamera, 1000);
}

// Eventos botones
// Estos botones publican la confirmación a la Raspberry
document.getElementById('allow').addEventListener('click', () => {
  if (!client || !client.connected) { alert('No conectado al broker MQTT'); return; }
  client.publish('cerradura/confirmacion', JSON.stringify({ permitir: true }));
  setStatus('✅ Enviado: permitir acceso');
});

document.getElementById('deny').addEventListener('click', () => {
  if (!client || !client.connected) { alert('No conectado al broker MQTT'); return; }
  client.publish('cerradura/confirmacion', JSON.stringify({ permitir: false }));
  setStatus('❌ Enviado: denegar acceso');
});

document.getElementById('register-face').addEventListener('click', registrarNuevoRostro);

// Nota: El botón "Tocar timbre" se ha reemplazado por el botón físico en la Raspberry Pi
// Ya no es necesario un botón en la web para iniciar el reconocimiento

// Actualizar imagen de la cámara
function refreshCamera() {
  const img = document.getElementById('camera-feed');
  // Agregar timestamp para evitar cache
  const timestamp = new Date().getTime();
  img.src = `/api/camera/last?t=${timestamp}`;
}

//document.getElementById('refresh-camera').addEventListener('click', refreshCamera);

// Auto-refrescar la imagen cada 10 segundos (solo si el panel de cámara está visible)
setInterval(() => {
  const cameraPreview = document.getElementById('camera-preview');
  if (!cameraPreview.classList.contains('hidden')) {
    refreshCamera();
  }
}, 10000);

// Start
resetUI();
connectMqtt();