# -*- coding: utf-8 -*-
"""
Módulo para la gestión de la comunicación de red con los nodos de hardware,
como el ESP32 que actúa como pasarela.
"""

import requests
from datetime import datetime

# --- Constantes de Configuración ---
IP_ESP32 = "192.168.4.1"
URL_BASE_ESP32 = f"http://{IP_ESP32}"

# --- Funciones de Logging ---

def log_depuracion(mensaje, logs):
    """
    Añade un mensaje de depuración a una lista de logs con marca de tiempo.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logs.append(f"[DEPURACION] [{timestamp}] {mensaje}")

# --- Funciones de Control de Hardware ---

def verificar_conexion_nodo(logs):
    """
    Intenta conectar con el nodo ESP32 para verificar que está en línea.
    """
    log_depuracion(f"Intentando conexión con el nodo ESP32: {IP_ESP32}", logs)
    try:
        # Se hace una petición a la raíz del servidor del ESP32.
        # El ESP32 actual solo tiene /control, por lo que la raíz puede devolver 404.
        # Consideramos conexión exitosa si responde 200 (OK) o 404 (Not Found pero online).
        response = requests.get(URL_BASE_ESP32, timeout=5)
        if response.status_code in [200, 404]:
            log_depuracion("Conexión con el nodo ESP32 establecida con éxito.", logs)
            return True
        else:
            log_depuracion(f"Error de conexión. El nodo respondió con código: {response.status_code}", logs)
            return False
    except requests.exceptions.RequestException as e:
        log_depuracion(f"Fallo crítico de conexión con el nodo ESP32. Error: {e}", logs)
        return False

def controlar_maqueta(lugar, estado, logs):
    """
    Envía un comando HTTP GET al ESP32 para controlar un ambiente específico.

    Args:
        lugar (str): El ambiente ('descanso', 'cocina', 'principal', 'cochera', 'habitacion', 'todas').
        estado (str): El estado deseado ('on' o 'off').
        logs (list): La lista para registrar los logs.

    Returns:
        bool: True si el comando fue exitoso, False en caso contrario.
    """
    # Normalizamos a minúsculas para coincidir con el código del ESP32
    lugar_param = lugar.lower()
    estado_param = estado.lower()

    url_comando = f"{URL_BASE_ESP32}/control"
    params = {'lugar': lugar_param, 'accion': estado_param}
    
    log_depuracion(f"Enviando comando a {url_comando} con params: {params}", logs)

    try:
        response = requests.get(url_comando, params=params, timeout=5)
        if response.status_code == 200:
            log_depuracion(f"Respuesta del hardware: {response.status_code} OK - Acción completada.", logs)
            return True
        else:
            log_depuracion(f"El hardware respondió con un error: {response.status_code}", logs)
            return False
    except requests.exceptions.RequestException as e:
        mensaje_error = f"Fallo en la petición HTTP al controlar el LED. Error: {e}"
        if "192.168.4.1" in URL_BASE_ESP32 and "ConnectTimeout" in str(e):
            mensaje_error += " [SUGERENCIA] Verifica que tu PC esté conectada a la red WiFi 'mapache_test'."
        log_depuracion(mensaje_error, logs)
        return False

# --- Espacio para Futuros Sensores ---

def leer_sensor_temperatura_dht22(logs):
    """
    (Futura implementación)
    Obtiene la lectura del sensor de temperatura y humedad DHT22.
    """
    log_depuracion("Función leer_sensor_temperatura_dht22() no implementada aún.", logs)
    # Lógica para hacer una petición GET a, por ejemplo, /sensor/dht22
    return None

def leer_sensor_gas_mq2(logs):
    """
    (Futura implementación)
    Obtiene la lectura del sensor de gas MQ-2.
    """
    log_depuracion("Función leer_sensor_gas_mq2() no implementada aún.", logs)
    # Lógica para hacer una petición GET a, por ejemplo, /sensor/mq2
    return None

def leer_sensor_movimiento_pir(logs):
    """
    (Futura implementación)
    Obtiene el estado del sensor de movimiento PIR.
    """
    log_depuracion("Función leer_sensor_movimiento_pir() no implementada aún.", logs)
    # Lógica para hacer una petición GET a, por ejemplo, /sensor/pir
    return None
