#!/usr/bin/env python3
"""
Script de prueba para LED RGB
Ejecutar con: sudo python3 test_led.py
"""

import RPi.GPIO as GPIO
import time
import sys

# Pines
PIN_LED_ROJO = 17
PIN_LED_VERDE = 27
PIN_LED_AZUL = 22

def test_led():
    """Prueba cada color del LED"""
    
    print("[LED TEST] Inicializando GPIO...")
    
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        GPIO.setup(PIN_LED_ROJO, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(PIN_LED_VERDE, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(PIN_LED_AZUL, GPIO.OUT, initial=GPIO.LOW)
        
        print("[LED TEST] ✅ GPIO inicializado correctamente\n")
        
        # Prueba ROJO
        print("[LED TEST] Probando LED ROJO (2 segundos)...")
        GPIO.output(PIN_LED_ROJO, GPIO.HIGH)
        GPIO.output(PIN_LED_VERDE, GPIO.LOW)
        GPIO.output(PIN_LED_AZUL, GPIO.LOW)
        time.sleep(2)
        print("[LED TEST] ✅ Rojo OK\n")
        
        # Prueba VERDE
        print("[LED TEST] Probando LED VERDE (2 segundos)...")
        GPIO.output(PIN_LED_ROJO, GPIO.LOW)
        GPIO.output(PIN_LED_VERDE, GPIO.HIGH)
        GPIO.output(PIN_LED_AZUL, GPIO.LOW)
        time.sleep(2)
        print("[LED TEST] ✅ Verde OK\n")
        
        # Prueba AZUL
        print("[LED TEST] Probando LED AZUL (2 segundos)...")
        GPIO.output(PIN_LED_ROJO, GPIO.LOW)
        GPIO.output(PIN_LED_VERDE, GPIO.LOW)
        GPIO.output(PIN_LED_AZUL, GPIO.HIGH)
        time.sleep(2)
        print("[LED TEST] ✅ Azul OK\n")
        
        # Prueba AMARILLO (Rojo + Verde)
        print("[LED TEST] Probando LED AMARILLO (Rojo + Verde, 2 segundos)...")
        GPIO.output(PIN_LED_ROJO, GPIO.HIGH)
        GPIO.output(PIN_LED_VERDE, GPIO.HIGH)
        GPIO.output(PIN_LED_AZUL, GPIO.LOW)
        time.sleep(2)
        print("[LED TEST] ✅ Amarillo OK\n")
        
        # Prueba CIAN (Verde + Azul)
        print("[LED TEST] Probando LED CIAN (Verde + Azul, 2 segundos)...")
        GPIO.output(PIN_LED_ROJO, GPIO.LOW)
        GPIO.output(PIN_LED_VERDE, GPIO.HIGH)
        GPIO.output(PIN_LED_AZUL, GPIO.HIGH)
        time.sleep(2)
        print("[LED TEST] ✅ Cian OK\n")
        
        # Prueba MAGENTA (Rojo + Azul)
        print("[LED TEST] Probando LED MAGENTA (Rojo + Azul, 2 segundos)...")
        GPIO.output(PIN_LED_ROJO, GPIO.HIGH)
        GPIO.output(PIN_LED_VERDE, GPIO.LOW)
        GPIO.output(PIN_LED_AZUL, GPIO.HIGH)
        time.sleep(2)
        print("[LED TEST] ✅ Magenta OK\n")
        
        # Prueba BLANCO (Todos)
        print("[LED TEST] Probando LED BLANCO (Todos, 2 segundos)...")
        GPIO.output(PIN_LED_ROJO, GPIO.HIGH)
        GPIO.output(PIN_LED_VERDE, GPIO.HIGH)
        GPIO.output(PIN_LED_AZUL, GPIO.HIGH)
        time.sleep(2)
        print("[LED TEST] ✅ Blanco OK\n")
        
        # Apagar
        print("[LED TEST] Apagando LED...")
        GPIO.output(PIN_LED_ROJO, GPIO.LOW)
        GPIO.output(PIN_LED_VERDE, GPIO.LOW)
        GPIO.output(PIN_LED_AZUL, GPIO.LOW)
        time.sleep(1)
        
        print("\n" + "="*50)
        print("[LED TEST] ✅ ¡TODOS LOS COLORES FUNCIONAN OK!")
        print("="*50 + "\n")
        
    except Exception as e:
        print(f"\n[LED TEST] ❌ Error: {e}")
        print("[LED TEST] Posibles causas:")
        print("[LED TEST] 1. No ejecutaste con sudo")
        print("[LED TEST] 2. Pines GPIO no están disponibles")
        print("[LED TEST] 3. LED no está conectado correctamente")
        sys.exit(1)
        
    finally:
        print("[LED TEST] Limpiando GPIO...")
        GPIO.cleanup()
        print("[LED TEST] ✅ GPIO limpiado\n")

if __name__ == "__main__":
    print("\n" + "="*50)
    print("TEST DE LED RGB")
    print("="*50 + "\n")
    
    print("⚠️  Este script debe ejecutarse con sudo:")
    print("   sudo python3 test_led.py\n")
    
    if not sys.argv[0].startswith('sudo'):
        import os
        if os.geteuid() != 0:
            print("❌ ERROR: No tienes permisos de root")
            print("   Ejecuta: sudo python3 test_led.py\n")
            sys.exit(1)
    
    test_led()
