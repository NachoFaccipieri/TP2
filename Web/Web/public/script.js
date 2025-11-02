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

document.getElementById("register-face").addEventListener("click", registrarNuevoRostro);
document.getElementById("ring-bell").addEventListener("click", tocarTimbre);

function registrarNuevoRostro() {
  const nombre = prompt("Ingresá el nombre de la persona:");
  if (!nombre) return;

  // --- CAMBIO AQUÍ ---
  // Apunta a la IP de la Pi, no a 'localhost'
  fetch('http://192.168.1.84:5000/registrar-rostro', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ nombre })
  })
    .then(res => res.json())
    .then(data => alert(data.mensaje))
    .catch(err => {
      alert("Error: " + err);
      console.log(err);
    });
}

function tocarTimbre() {
  // --- CAMBIO AQUÍ ---
  // Apunta a la IP de la Pi, no a 'localhost'
  fetch('http://192.168.1.84:5000/tocar-timbre', { method: 'POST' })
    .then(res => res.json())
    .then(data => {
      if (data.coincidencia) {
        document.getElementById("status").innerHTML = `<p>✅ Coincidencia encontrada: ${data.nombre}</p>`;
      } else {
        document.getElementById("status").innerHTML = `<p>❌ No se encontró coincidencia</p>`;
      }
      alert(data.mensaje);
    })
    .catch(err => {
      alert("Error: " + err);
      console.log(err);
    });
}

function resetUI() {
  document.getElementById("status").innerHTML = "<p>Esperando evento...</p>";
  document.getElementById("person-info").classList.add("hidden");
}
