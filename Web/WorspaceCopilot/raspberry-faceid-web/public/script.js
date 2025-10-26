// filepath: raspberry-faceid-web/public/script.js
const mqtt = require('mqtt');
const client = mqtt.connect('mqtt://localhost'); // Conectar al broker MQTT en la Raspberry Pi

// Elementos del DOM
const statusElement = document.getElementById("status");
const personInfoElement = document.getElementById("person-info");
const nameElement = document.getElementById("name");
const confidenceElement = document.getElementById("confidence");

// Función para manejar la llegada de mensajes MQTT
client.on('message', (topic, message) => {
    const data = JSON.parse(message.toString());
    if (data.coincidencia) {
        statusElement.innerHTML = `<p>✅ Persona reconocida: ${data.nombre}</p>`;
        nameElement.innerText = "Nombre: " + data.nombre;
        confidenceElement.innerText = "Coincidencia: " + data.confianza + "%";
        personInfoElement.classList.remove("hidden");
    } else {
        statusElement.innerHTML = `<p>❌ No se encontró coincidencia</p>`;
        personInfoElement.classList.add("hidden");
    }
});

// Suscribirse al tema de reconocimiento de rostros
client.on('connect', () => {
    client.subscribe('face_recognition', (err) => {
        if (!err) {
            console.log('Suscrito al tema face_recognition');
        }
    });
});

// Botones
document.getElementById("allow").addEventListener("click", () => {
    alert("✅ Acceso permitido");
    resetUI();
});

document.getElementById("deny").addEventListener("click", () => {
    alert("❌ Acceso denegado");
    resetUI();
});

document.getElementById("register-face").addEventListener("click", registrarNuevoRostro);
document.getElementById("ring-bell").addEventListener("click", tocarTimbre);

function registrarNuevoRostro() {
    const nombre = prompt("Ingresá el nombre de la persona:");
    if (!nombre) return;
    // Aquí se puede agregar la lógica para registrar el rostro
}

function tocarTimbre() {
    // Aquí se puede agregar la lógica para tocar el timbre
}

function resetUI() {
    statusElement.innerHTML = "<p>Esperando evento...</p>";
    personInfoElement.classList.add("hidden");
}