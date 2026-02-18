# -*- coding: utf-8 -*-
"""
Servidor web principal con Flask para la Casa Inteligente.

Este servidor expone una API para ser consumida por un frontend (panel de control).
Reemplaza la lógica de `principal.py` para operar en un entorno web.
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import speech_recognition as sr
from pydub import AudioSegment
import io
import traceback
import time
import threading
import serial
import re

# --- Importaciones de Módulos Propios ---
from control_red import controlar_maqueta
from gestion_ia import procesar_comando_voz

# --- Configuración de la Aplicación Flask ---
app = Flask(__name__)
# Habilitar CORS para permitir peticiones desde el frontend
CORS(app)

# --- Configuración Serial (Arduino - Sensor Gas) ---
# IMPORTANTE: Cambia 'COM3' por el puerto USB real de tu Arduino
ARDUINO_PORT = 'COM3' 
ARDUINO_BAUD = 9600
latest_gas_level = 0
latest_temp = 0.0
latest_hum = 0.0

def leer_sensor_arduino():
    """Hilo en segundo plano para leer el puerto serial sin bloquear Flask."""
    global latest_gas_level, latest_temp, latest_hum
    try:
        ser = serial.Serial(ARDUINO_PORT, ARDUINO_BAUD, timeout=1)
        print(f"[ARDUINO] Conectado exitosamente en {ARDUINO_PORT}")
        while True:
            if ser.in_waiting > 0:
                try:
                    linea = ser.readline().decode('utf-8', errors='ignore').strip()
                    # [DEBUG] Imprimir lo que llega para verificar
                    if linea: print(f"[SERIAL RAW] Recibido: '{linea}'")
                    
                    # Parsear línea: "Gas: 120 | Temp: 24.50C | Hum: 60.00%"
                    
                    # 1. Gas
                    match_gas = re.search(r'Gas:\s*(\d+)', linea)
                    if match_gas:
                        latest_gas_level = int(match_gas.group(1))
                    
                    # 2. Temperatura
                    match_temp = re.search(r'Temp:\s*([\d\.]+)', linea)
                    if match_temp:
                        latest_temp = float(match_temp.group(1))
                        
                    # 3. Humedad
                    match_hum = re.search(r'Hum:\s*([\d\.]+)', linea)
                    if match_hum:
                        latest_hum = float(match_hum.group(1))
                        
                except Exception as e:
                    print(f"[SERIAL ERROR] {e}")
            time.sleep(0.1) # Pequeña pausa para no saturar CPU
    except serial.SerialException as e:
        print(f"[ADVERTENCIA] Error conectando al Arduino en {ARDUINO_PORT}: {e}")

# --- Definición de Rutas de la API ---

@app.route("/")
def index():
    """
    Ruta raíz que sirve el panel de control web.
    """
    return render_template('index.html')

# --- Función Auxiliar para Lógica de Domótica ---
def ejecutar_logica_domotica(comando_usuario, logs):
    """Procesa el texto del comando y ejecuta la acción correspondiente."""
    # 2. Procesar el comando con el modelo de IA
    try:
        resultado_ia = procesar_comando_voz(comando_usuario, logs)
        lista_acciones = resultado_ia.get('acciones', [])
    except Exception as e:
        logs.append(f"[ERROR_IA] Fallo durante el procesamiento de la IA: {e}")
        return "error", []

    # 3. Actuar según la intención reconocida
    resultados_ejecucion = []
    exito_global = False
    
    if not lista_acciones:
        logs.append("[SISTEMA] No se han detectado acciones válidas en el comando.")
        return "failed", []

    for item in lista_acciones:
        accion = item.get('accion', 'NONE').upper()
        lugar = item.get('lugar', 'unknown').lower()
        
        if accion in ['ON', 'OFF']:
            try:
                logs.append(f"[SISTEMA] Ejecutando: {accion} en {lugar.upper()}")
                exito = controlar_maqueta(lugar, accion, logs)
                resultados_ejecucion.append({'accion': accion, 'lugar': lugar, 'exito': exito})
                if exito: exito_global = True
                # Pequeño retraso para evitar saturar el ESP32 con peticiones seguidas
                time.sleep(0.3)
            except Exception as e:
                logs.append(f"[ERROR_HW] Fallo al controlar {lugar}: {e}")
                resultados_ejecucion.append({'accion': accion, 'lugar': lugar, 'exito': False})
        else:
            logs.append(f"[SISTEMA] Acción desconocida ignorada: {accion}")

    return ("success" if exito_global else "failed"), resultados_ejecucion

@app.route("/api/command", methods=['POST'])
def handle_command():
    """
    Punto de entrada principal de la API para procesar comandos de usuario.
    Espera un JSON con la clave 'command'.
    Ej: {"command": "enciende la luz"}
    """
    # Lista para recolectar todos los logs generados durante esta petición
    logs = []
    
    # 1. Obtener datos de la petición
    data = request.json
    if not data or 'command' not in data:
        return jsonify({"status": "error", "message": "Petición inválida. Se requiere un JSON con la clave 'command'."}), 400
    
    comando_usuario = data['command']
    if not comando_usuario.strip():
        return jsonify({"status": "error", "message": "El comando no puede estar vacío."}), 400

    status, resultados = ejecutar_logica_domotica(comando_usuario, logs)

    return jsonify({"status": status, "resultados": resultados, "logs": logs})

@app.route("/api/voice-command", methods=['POST'])
def handle_voice_command():
    """
    Recibe un archivo de audio (blob), lo transcribe localmente y ejecuta el comando.
    """
    logs = []
    if 'audio' not in request.files:
        return jsonify({"status": "error", "message": "No se recibió archivo de audio"}), 400
        
    audio_file = request.files['audio']
    texto_transcrito = ""

    try:
        # 1. Convertir WebM (navegador) a WAV (compatible con SpeechRecognition)
        # Requiere ffmpeg instalado en el sistema
        logs.append("[VOZ] Procesando archivo de audio recibido...")
        song = AudioSegment.from_file(audio_file) # pydub detecta formato automáticamente
        wav_io = io.BytesIO()
        song.export(wav_io, format="wav")
        wav_io.seek(0)
        
        # 2. Transcribir usando SpeechRecognition + Whisper (Local)
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_io) as source:
            audio_data = recognizer.record(source)
            logs.append("[VOZ] Transcribiendo audio localmente (Whisper)...")
            # 'recognize_whisper' usa el modelo local de OpenAI Whisper
            # fp16=False es CRUCIAL para evitar errores en CPUs (laptops)
            texto_transcrito = recognizer.recognize_whisper(audio_data, language="spanish", fp16=False)
            logs.append(f"[VOZ] Texto detectado: '{texto_transcrito}'")
            
    except Exception as e:
        traceback.print_exc() # Muestra el error real en la terminal del servidor
        # Detectar error de conexión al intentar descargar el modelo por primera vez
        if "getaddrinfo failed" in str(e):
            logs.append("[ERROR_RED] Se requiere internet la primera vez para descargar el modelo Whisper.")
        logs.append(f"[ERROR_VOZ] Fallo al procesar audio: {repr(e)}")
        return jsonify({"status": "error", "message": str(e), "logs": logs}), 500

    # 3. Ejecutar la lógica con el texto transcrito
    status, resultados = ejecutar_logica_domotica(texto_transcrito, logs)
    
    return jsonify({"status": status, "resultados": resultados, "logs": logs, "transcription": texto_transcrito})

@app.route("/api/device/control", methods=['POST'])
def handle_device_control():
    """
    Endpoint para control manual directo (botones del frontend).
    Evita el procesamiento de IA para una respuesta más rápida.
    """
    logs = []
    data = request.json
    lugar = data.get('lugar')
    accion = data.get('accion')

    if not lugar or not accion:
        return jsonify({"status": "error", "message": "Faltan parámetros 'lugar' o 'accion'."}), 400

    logs.append(f"[MANUAL] Usuario activó botón: {accion} en {lugar.upper()}")
    
    # Llamada directa al hardware
    exito = controlar_maqueta(lugar, accion, logs)
    
    # Mantenemos compatibilidad de estructura devolviendo una lista de un solo elemento
    resultados = [{'accion': accion, 'lugar': lugar, 'exito': exito}]
    
    return jsonify({"status": "success" if exito else "error", "resultados": resultados, "logs": logs})

@app.route("/api/sensor/gas", methods=['GET'])
def handle_gas_sensor():
    """
    Devuelve los últimos valores leídos de los sensores (Arduino).
    """
    return jsonify({
        "status": "success", 
        "level": latest_gas_level,
        "temp": latest_temp,
        "hum": latest_hum
    })

# --- Bloque de Ejecución ---
if __name__ == "__main__":
    # Iniciar el hilo de lectura serial aquí para evitar duplicidad de procesos
    hilo_serial = threading.Thread(target=leer_sensor_arduino, daemon=True)
    hilo_serial.start()

    # Iniciar el servidor de desarrollo de Flask
    # IMPORTANTE: use_reloader=False es OBLIGATORIO al usar puertos Serial y Threads.
    # Evita que Flask cree un proceso hijo que no pueda acceder al puerto COM.
    print("Iniciando servidor Flask en http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
