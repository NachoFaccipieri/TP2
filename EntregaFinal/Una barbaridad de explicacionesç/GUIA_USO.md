# 🚪 Guía de Uso - Sistema FaceID

## 👋 Inicio Rápido

### Para Usuarios Finales (Acceso a la Puerta)

#### 1️⃣ Para Entrar (Ya Registrado)
```
1. Acérquese a la puerta
2. Presione el botón físico en la puerta
3. El LED cambiará a AMARILLO (procesando)
4. Su rostro será capturado y comparado
5. Si coincide: Panel web muestra "✅ Coincidencia"
   → Usuario web presiona "✅ Permitir acceso"
   → LED se pone VERDE
   → Servo abre la puerta por 10 segundos
   → Puede entrar
6. Si NO coincide: Panel web muestra "❌ No se encontró coincidencia"
   → Puerta permanece cerrada
```

#### 2️⃣ Botones en el Panel Web
- **✅ Permitir acceso**: Abre puerta por 10 segundos
- **❌ Denegar acceso**: Cierra puerta, LED rojo por 10 segundos
- **🔄 Actualizar**: Recarga la imagen de cámara

---

### Para Administradores (Registrar Nuevas Personas)

#### 1️⃣ Registrar un Nuevo Rostro
```
1. Acceder al panel web en: http://<IP_RASPBERRY>:5000
2. Hacer clic en "📸 Registrar nuevo rostro"
3. Ingresar el nombre de la persona (ej: "Nacho")
4. Sistema muestra: "Presiona el botón físico para registrar nuevo rostro"
5. LED cambia a AZUL TITILANTE (parpadea)
6. La persona presiona el botón físico en la puerta
7. Se captura la foto y se genera el embedding
8. LED vuelve a AZUL SOLIDO
9. Persona registrada exitosamente
```

#### 2️⃣ Verificar Personas Registradas
```bash
# Ver archivo de nombres
cat embeddings.txt
cat names.txt

# O desde web: ver el panel de estado
```

---

## 🟡🔵🟢🔴 Significado de Colores del LED

| Color | Significado | Duración | Acción |
|-------|-------------|----------|--------|
| 🟡 Amarillo titilante | Iniciando/conectando | Inicio | Esperar |
| 🔵 Azul sólido | Sistema listo | Indefinido | Listo para usar |
| 🟡 Amarillo sólido | Procesando rostro | ~5s | Esperar resultado |
| 🟢 Verde (10s) | Acceso PERMITIDO ✅ | 10 segundos | Puerta abierta |
| 🔴 Rojo (10s) | Acceso DENEGADO ❌ | 10 segundos | Puerta cerrada |
| 🔵 Azul titilante | Registrando rostro | Registro | Presionar botón |

---

## 📊 Panel Web

### Interfaz Principal
```
┌─────────────────────────────┐
│   CONTROL DE ACCESO         │
├─────────────────────────────┤
│                              │
│ Estado: [Esperando evento]   │
│                              │
│ ℹ️ Presiona el botón físico   │
│ para iniciar reconocimiento  │
│                              │
│ 📸 REGISTRAR NUEVO ROSTRO    │
│                              │
│ [Imagen de cámara]           │
│ [Botón Actualizar 🔄]       │
│                              │
│ RESULTADO ROSTRO:            │
│ Nombre: Nacho                │
│ Distancia: 0.456             │
│                              │
│ ✅ PERMITIR ACCESO          │
│ ❌ DENEGAR ACCESO           │
│                              │
└─────────────────────────────┘
```

### Estados del Panel
1. **Inicio**: "Conectando a broker MQTT..."
2. **Listo**: "Esperando evento..."
3. **Procesando**: "ℹ️ [Estado actual]"
4. **Resultado**: Muestra nombre y distancia
5. **Esperando confirmación**: Botones de permitir/denegar

---

## 🔌 Hardware

### El Botón Físico
```
┌──────────────┐
│   BOTON      │ ← Presionar para iniciar reconocimiento
│     TIMBRE   │
└──────────────┘
```
- **Una presión**: Inicia reconocimiento
- **Durante registro**: Captura para nuevo rostro

### El LED RGB
```
┌─────────────┐
│   LED RGB   │ ← Indica estado del sistema
│  Cátodo     │
│  Común      │
└─────────────┘
```
- Se ilumina según el estado
- Parpadea durante operaciones críticas

### El Servo (Puerta)
```
┌─────────────┐
│   SERVO     │ ← Controla apertura/cierre de puerta
│   MOTOR     │
└─────────────┘
```
- Se abre automáticamente si acceso permitido
- Se cierra después de 10 segundos
- Posición: 0° = cerrado, 90° = abierto

---

## 🚨 Solución de Problemas para Usuarios

### Problema: "Conectando a broker MQTT..." (no avanza)
**Solución:**
- Verificar que MQTT broker esté corriendo
- Verificar conexión de red
- Reiniciar la Raspberry Pi

### Problema: Botón no funciona
**Solución:**
- Verificar que el botón está correctamente conectado
- Presionar un poco más fuerte (asegurar contacto)
- Esperar 200ms entre presiones (debounce)

### Problema: LED no prende
**Solución:**
- Verificar conexiones (GND en pin común)
- Verificar polaridad (ánodo/cátodo)
- Probar con otra resistencia

### Problema: Servo no se mueve
**Solución:**
- Verificar alimentación 5V externa
- Verificar signal en GPIO 14
- No forzar movimiento manual

### Problema: No reconoce mi rostro
**Solución:**
- Verificar que existe registro previo
- Intentar con mejor iluminación
- Acercarse más a la cámara
- Registrar nuevamente

---

## 📱 Acceso Remoto (Opcional)

### Si tienes VPN configurada
```
1. Conectarse a VPN de la casa
2. Ir a: http://<IP_RASPBERRY>:5000
3. Usar normalmente desde remoto
```

### Advertencia de Seguridad ⚠️
**NO usar sin VPN en internet público:**
- Las credenciales podrían ser interceptadas
- Cualquiera podría controlar la puerta

---

## 🔧 Diagnósticos Rápidos

### Verificar que todo funciona
```bash
# 1. Desde la Raspberry Pi
ping localhost

# 2. Verificar MQTT
mosquitto_pub -h localhost -t "test" -m "prueba"

# 3. Verificar Flask
curl http://localhost:5000/

# 4. Verificar GPIO
python3 -c "import RPi.GPIO as GPIO; print('GPIO: OK')"
```

### Chequeo del Sistema
```bash
# Ver logs en tiempo real
sudo journalctl -u faceid -f

# Ver uso de recursos
free -h          # Memoria
top              # CPU
```

---

## 📊 Specs Técnicas (Para Técnicos)

| Componente | Especificación |
|-----------|----------------|
| **LED RGB** | Cátodo Común, GPIO 17/27/22 |
| **Servo** | PWM 50Hz, GPIO 14 |
| **Botón** | GPIO 21, Pull-up, debounce 200ms |
| **MQTT** | Puerto 1883 (interna), 9001 (WebSocket) |
| **Web** | Puerto 5000, Flask |
| **Cámara** | PiCamera (PiCam v2 o v3) |
| **Distancia umbral** | 0.8 (menor = más restrictivo) |
| **Tiempo servo abierto** | 10 segundos |

---

## 💡 Consejos y Buenas Prácticas

### Antes de Salir de Casa
- [ ] Verificar que LED está AZUL SOLIDO
- [ ] Probar botón físico una vez
- [ ] Verificar que puerta se abre y cierra

### Al Regresar
- [ ] Panel web muestra "Conectado"
- [ ] Presionar botón físico
- [ ] Sistema captura y reconoce
- [ ] Permitir desde web

### Mantenimiento Regular
- [ ] Limpiar lente de cámara (mensual)
- [ ] Registrar nuevas personas conforme sea necesario
- [ ] Revisar logs de intentos fallidos
- [ ] Actualizar base de datos

### Seguridad
- ✅ Cambiar contraseña MQTT después de instalar
- ✅ No compartir token de web con desconocidos
- ✅ Usar VPN si acceso remoto es necesario
- ✅ Mantener Raspberry Pi actualizada

---

## 📞 Contacto de Soporte

Para problemas técnicos avanzados:
1. Revisar documentación en carpeta: `Faq/TP2/EntregaFinal/`
2. Consultar `GUIA_INSTALACION_RPI.md`
3. Revisar `REFERENCIA_RAPIDA.md` para configuración
4. Leer `DIAGRAMAS_ESTADOS.md` para entender flujos

---

## 🎓 Videos de Tutorial (Futuros)

- [ ] Instalación inicial
- [ ] Primer reconocimiento
- [ ] Registrar nuevo usuario
- [ ] Troubleshooting básico

---

**Versión**: 1.0  
**Última actualización**: Diciembre 2025  
**Compatibilidad**: Raspberry Pi 3+, Raspbian/Pi OS  
**Estado**: ✅ Listo para usar
