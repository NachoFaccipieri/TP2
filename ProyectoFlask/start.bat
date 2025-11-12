@echo off
echo ====================================
echo Sistema de Control de Acceso Facial
echo ====================================
echo.

echo [1/3] Verificando Docker...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker no esta instalado o no esta en el PATH
    echo Por favor instala Docker Desktop desde https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

echo [2/3] Iniciando broker MQTT (Mosquitto)...
docker-compose up -d
if %errorlevel% neq 0 (
    echo ERROR: No se pudo iniciar Mosquitto
    pause
    exit /b 1
)

echo.
echo Esperando que Mosquitto este listo...
timeout /t 3 /nobreak >nul

echo.
echo [3/3] Iniciando servidor Flask...
echo.
echo ====================================
echo Sistema iniciado correctamente
echo ====================================
echo.
echo - Broker MQTT: localhost:1883 (Python)
echo - WebSocket MQTT: localhost:9001 (Web)
echo - Interfaz Web: http://localhost:5000
echo.
echo Presiona Ctrl+C para detener el servidor Flask
echo.

python comprobarRostro.py
