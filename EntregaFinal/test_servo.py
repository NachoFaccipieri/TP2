#!/usr/bin/env python3
"""
Script de prueba para Servo
Ejecutar con: sudo python3 test_servo.py
"""

import RPi.GPIO as GPIO
import time
import sys

# Pin
PIN_SERVO = 14

def test_servo():
    """Prueba el movimiento del servo"""
    
    print("[SERVO TEST] Inicializando GPIO...")
    
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Configurar servo
        GPIO.setup(PIN_SERVO, GPIO.OUT)
        pwm = GPIO.PWM(PIN_SERVO, 50)  # 50 Hz
        pwm.start(0)
        
        print("[SERVO TEST] ✅ Servo inicializado\n")
        
        print("="*50)
        print("[SERVO TEST] Moviendo servo...")
        print("="*50 + "\n")
        
        # Posición inicial: Cerrado (0°)
        print("[SERVO TEST] Posición: CERRADO (0°)")
        print("[SERVO TEST] Duty Cycle: 5%")
        pwm.ChangeDutyCycle(5)
        time.sleep(1)
        pwm.ChangeDutyCycle(0)
        time.sleep(0.5)
        print("[SERVO TEST] ✅ Servo en posición cerrada\n")
        
        input("[SERVO TEST] Presiona Enter para abrir...")
        
        # Posición abierta: (90°)
        print("[SERVO TEST] Posición: ABIERTO (90°)")
        print("[SERVO TEST] Duty Cycle: 7.5%")
        pwm.ChangeDutyCycle(7.5)
        time.sleep(1)
        pwm.ChangeDutyCycle(0)
        time.sleep(0.5)
        print("[SERVO TEST] ✅ Servo en posición abierta\n")
        
        input("[SERVO TEST] Presiona Enter para cerrar...")
        
        # Volver a cerrado
        print("[SERVO TEST] Posición: CERRADO (0°)")
        print("[SERVO TEST] Duty Cycle: 5%")
        pwm.ChangeDutyCycle(5)
        time.sleep(1)
        pwm.ChangeDutyCycle(0)
        time.sleep(0.5)
        print("[SERVO TEST] ✅ Servo en posición cerrada\n")
        
        print("="*50)
        print("[SERVO TEST] ✅ ¡SERVO FUNCIONA CORRECTAMENTE!")
        print("="*50 + "\n")
        
        pwm.stop()
        
    except Exception as e:
        print(f"\n[SERVO TEST] ❌ Error: {e}")
        print("[SERVO TEST] Posibles causas:")
        print("[SERVO TEST] 1. No ejecutaste con sudo")
        print("[SERVO TEST] 2. Pin GPIO 14 no está disponible")
        print("[SERVO TEST] 3. Servo no tiene alimentación 5V")
        sys.exit(1)
        
    finally:
        print("[SERVO TEST] Limpiando GPIO...")
        GPIO.cleanup()
        print("[SERVO TEST] ✅ GPIO limpiado\n")

if __name__ == "__main__":
    print("\n" + "="*50)
    print("TEST DE SERVO")
    print("="*50 + "\n")
    
    print("⚠️  Este script debe ejecutarse con sudo:")
    print("   sudo python3 test_servo.py\n")
    
    import os
    if os.geteuid() != 0:
        print("❌ ERROR: No tienes permisos de root")
        print("   Ejecuta: sudo python3 test_servo.py\n")
        sys.exit(1)
    
    test_servo()
