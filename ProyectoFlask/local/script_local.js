// Versión local del cliente MQTT para pruebas.
// Conecta por defecto al broker en tu máquina local (WebSocket puerto 9001).
// Cambiá la IP si tu PC tiene otra dirección.

const BROKER_WS = 'ws://192.168.0.6:9001'; // usar la IP de tu PC con mosquitto+websockets
const TOPIC_REGISTRO = 'cerradura/registro';
const TOPIC_TIMBRE = 'cerradura/timbre';
const TOPIC_RESPUESTA = 'cerradura/persona';
const TOPIC_STATUS = 'cerradura/status';

const STATUS_EL = document.getElementById('status');
const PERSON_INFO = document.getElementById('person-info');
const NAME_EL = document.getElementById('name');
const CONF_EL = document.getElementById('confidence');

let client = null;

function setStatus(text) { STATUS_EL.innerHTML = `<p>${text}</p>`; }
function resetUI() { setStatus('Esperando evento...'); PERSON_INFO.classList.add('hidden'); }

function onMessage(topic, payload) {
  let msg = null;
  try { msg = JSON.parse(payload.toString()); } catch (e) { msg = payload.toString(); }
  if (topic === TOPIC_STATUS) { setStatus(`ℹ️ ${msg}`); return; }
  if (topic === TOPIC_RESPUESTA) {
    if (typeof msg === 'string') { setStatus(msg); return; }
    if (msg.coincidencia) {
      setStatus(`✅ Coincidencia: ${msg.nombre} (dist ${Number(msg.distancia).toFixed(3)})`);
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
  setStatus(`Conectando a ${BROKER_WS} ...`);
  client = mqtt.connect(BROKER_WS);
  client.on('connect', () => { setStatus('Conectado al broker de pruebas'); client.subscribe(TOPIC_RESPUESTA); client.subscribe(TOPIC_STATUS); });
  client.on('message', (t, m) => onMessage(t, m));
  client.on('error', (e) => setStatus('Error MQTT: ' + e));
  client.on('close', () => { setStatus('Conexion MQTT cerrada'); setTimeout(connectMqtt, 3000); });
}

function registrarNuevoRostro() {
  const nombre = prompt('Ingresá el nombre de la persona:');
  if (!nombre) return;
  if (!client || !client.connected) { alert('No conectado al broker'); return; }
  client.publish(TOPIC_REGISTRO, JSON.stringify({ nombre }));
  setStatus(`Enviando petición de registro para "${nombre}"...`);
}

function tocarTimbre() {
  if (!client || !client.connected) { alert('No conectado al broker'); return; }
  client.publish(TOPIC_TIMBRE, 'ping');
  setStatus('Timbre enviado. Esperando respuesta...');
}

document.getElementById('allow').addEventListener('click', () => { alert('✅ Acceso permitido'); resetUI(); });
document.getElementById('deny').addEventListener('click', () => { alert('❌ Acceso denegado'); resetUI(); });
document.getElementById('register-face').addEventListener('click', registrarNuevoRostro);
document.getElementById('ring-bell').addEventListener('click', tocarTimbre);

resetUI();
connectMqtt();
