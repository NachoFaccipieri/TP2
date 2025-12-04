#!/usr/bin/env python3
"""
Script de prueba para Botón
Ejecutar con: sudo python3 test_boton.py
"""

import RPi.GPIO as GPIO
import time
import sys

# Pin
PIN_BOTON = 21
boton_presionado_count = 0

def boton_callback(channel):
    """Callback cuando se presiona el botón"""
    global boton_presionado_count
    boton_presionado_count += 1
    print(f"[BOTON TEST] ✅ BOTÓN PRESIONADO! (x{boton_presionado_count})")

def test_boton():
    """Prueba la detección del botón"""
    
    global boton_presionado_count
    
    print("[BOTON TEST] Inicializando GPIO...")
    
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Configurar botón
        GPIO.setup(PIN_BOTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        print("[BOTON TEST] ✅ Botón configurado como entrada con pull-up\n")
        
        # Limpiar evento anterior
        try:
            GPIO.remove_event_detect(PIN_BOTON)
            print("[BOTON TEST] Removido evento anterior\n")
        except:
            pass
        
        # Agregar detección de eventos
        print("[BOTON TEST] Configurando detección de eventos...")
        GPIO.add_event_detect(PIN_BOTON, GPIO.FALLING, callback=boton_callback, bouncetime=200)
        
        print("[BOTON TEST] ✅ Detección de eventos configurada correctamente\n")
        print("="*50)
        print("[BOTON TEST] Presiona el botón físico...")
        print("[BOTON TEST] (Presiona Ctrl+C para salir)")
        print("="*50 + "\n")
        
        # Loop de espera
        while True:
            time.sleep(0.1)
            
    except RuntimeError as e:
        print(f"\n[BOTON TEST] ❌ Error al configurar detección: {e}")
        print("\n[BOTON TEST] Posibles soluciones:")
        print("[BOTON TEST] 1. Ejecutar con sudo: sudo python3 test_boton.py")
        print("[BOTON TEST] 2. Matar otros procesos Python: sudo pkill -f python3")
        print("[BOTON TEST] 3. Reiniciar la Raspberry: sudo reboot")
        print("[BOTON TEST] 4. Agregar usuario al grupo gpio:")
        print("[BOTON TEST]    sudo usermod -a -G gpio $USER")
        sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n\n[BOTON TEST] Interrumpido por usuario")
        if boton_presionado_count > 0:
            print(f"[BOTON TEST] ✅ Botón funcionó correctamente ({boton_presionado_count} presiones)\n")
        else:
            print("[BOTON TEST] ⚠️  Botón no fue presionado\n")
            
    finally:
        print("[BOTON TEST] Limpiando GPIO...")
        GPIO.cleanup()
        print("[BOTON TEST] ✅ GPIO limpiado\n")

if __name__ == "__main__":
    print("\n" + "="*50)
    print("TEST DE BOTÓN")
    print("="*50 + "\n")
    
    print("⚠️  Este script debe ejecutarse con sudo:")
    print("   sudo python3 test_boton.py\n")
    
    import os
    if os.geteuid() != 0:
        print("❌ ERROR: No tienes permisos de root")
        print("   Ejecuta: sudo python3 test_boton.py\n")
        sys.exit(1)
    
    test_boton()
