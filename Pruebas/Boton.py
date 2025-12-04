from gpiozero import Button
from signal import pause

# Definimos el botón en el GPIO 21.
# gpiozero configura automáticamente la resistencia interna (Pull-up).
# Asegúrate de conectar la otra pata del botón a GND.
boton = Button(21)

def decir_hola():
    print("¡Botón presionado!")

def decir_adios():
    print("Botón soltado")

print("Esperando a que presiones el botón...")

# Asignamos las funciones a los eventos
boton.when_pressed = decir_hola
boton.when_released = decir_adios

# Mantiene el programa corriendo
pause()