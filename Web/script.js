// Simulación: en producción esto vendría de MQTT o API REST
// Podés probar simular eventos llamando a la función simulateEvent()
function simulateEvent(nombre, confianza) {
  document.getElementById("status").innerHTML = "<p>🚪 Alguien tocó el timbre</p>";

  document.getElementById("person-info").classList.remove("hidden");
  document.getElementById("name").innerText = "Nombre: " + nombre;
  document.getElementById("confidence").innerText = "Coincidencia: " + confianza + "%";
}

// Botones
document.getElementById("allow").addEventListener("click", () => {
  alert("✅ Acceso permitido");
  resetUI();
});

document.getElementById("deny").addEventListener("click", () => {
  alert("❌ Acceso denegado");
  resetUI();
});

function resetUI() {
  document.getElementById("status").innerHTML = "<p>Esperando evento...</p>";
  document.getElementById("person-info").classList.add("hidden");
}

// --- Ejemplo de simulación automática ---
setTimeout(() => {
  simulateEvent("Juan Pérez", 97);
}, 3000);
