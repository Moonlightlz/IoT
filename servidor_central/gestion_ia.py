# -*- coding: utf-8 -*-
"""
Módulo para la gestión de la inteligencia artificial, incluyendo la comunicación
con el modelo de lenguaje local (Ollama con Llama 3).
"""

import requests
import json
from datetime import datetime

# --- Constantes de Configuración de IA ---
URL_OLLAMA_API = "http://localhost:11434/api/generate"
MODELO_LLAMA = "llama3"

# --- Funciones de Logging ---

def log_ia(mensaje, logs):
    """
    Añade un mensaje de log específico de la IA a una lista de logs.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logs.append(f"[IA_LOG] [{timestamp}] {mensaje}")

# --- Funciones de Procesamiento de Lenguaje ---

def procesar_comando_voz(texto_usuario, logs):
    """
    Envía un comando de texto a la API de Ollama y extrae la intención.

    Args:
        texto_usuario (str): El comando de voz transcrito.
        logs (list): La lista para registrar los logs.

    Returns:
        dict: Un diccionario con {'acciones': [{'accion': '...', 'lugar': '...'}, ...]}
    """
    log_ia(f"Enviando consulta a {MODELO_LLAMA}: '{texto_usuario}'", logs)

    # Prompt diseñado para devolver una LISTA de acciones.
    lugares_validos = ['descanso', 'cocina', 'principal', 'cochera', 'habitacion']
    prompt_estructurado = (
        "Eres un asistente de domótica. Analiza la orden y desglósala en acciones individuales. "
        f"Lugares disponibles: {', '.join(lugares_validos)} y 'todas'. "
        "Reglas: "
        "1. Si la orden afecta a varios lugares (ej: 'cocina y sala'), genera una acción para cada uno. "
        "2. Si la orden es excluyente (ej: 'todas menos cocina'), genera acciones individuales para el resto de lugares. "
        "3. Tu respuesta debe ser ESTRICTAMENTE un objeto JSON con la clave 'acciones' que contenga una lista. "
        "Formato JSON: {\"acciones\": [{\"accion\": \"ON\"|\"OFF\", \"lugar\": \"nombre_lugar\"}, ...]} "
        "No incluyas texto fuera del JSON. "
        f"La orden es: '{texto_usuario}'"
    )

    payload = {
        "model": MODELO_LLAMA,
        "prompt": prompt_estructurado,
        "stream": False  # Para recibir la respuesta completa de una vez
    }

    # --- Log detallado para depuración en la consola del servidor ---
    print("\n" + "="*50)
    print("CONTACTANDO A LA API DE OLLAMA")
    print(f"URL: {URL_OLLAMA_API}")
    print("--- INICIO PAYLOAD OLLAMA ---")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    print("--- FIN PAYLOAD OLLAMA ---\n")
    # ----------------------------------------------------------------

    try:
        response = requests.post(URL_OLLAMA_API, json=payload, timeout=30)
        
        if response.status_code == 200:
            respuesta_json = response.json()
            
            # --- Log detallado de la respuesta para depuración ---
            print("--- INICIO RESPUESTA OLLAMA ---")
            print(json.dumps(respuesta_json, indent=2, ensure_ascii=False))
            print("--- FIN RESPUESTA OLLAMA ---")
            print("="*50 + "\n")
            # ----------------------------------------------------

            # La respuesta de Ollama está en la clave 'response'
            respuesta_modelo = respuesta_json.get("response", "").strip()
            
            log_ia(f"Respuesta del modelo: {respuesta_modelo}", logs)

            # 1. Limpieza básica de markdown
            limpio = respuesta_modelo.replace('```json', '').replace('```', '').strip()

            # 2. Parche para error observado: si empieza con { y termina en ], le falta la } final
            if limpio.startswith('{') and limpio.endswith(']'):
                limpio += '}'

            try:
                datos = json.loads(limpio)
            except json.JSONDecodeError:
                # 3. Si falla, intentamos extracción estricta (útil si hay texto conversacional alrededor)
                inicio = respuesta_modelo.find('{')
                fin = respuesta_modelo.rfind('}')
                if inicio != -1 and fin != -1:
                    try:
                        datos = json.loads(respuesta_modelo[inicio:fin+1])
                    except json.JSONDecodeError as e:
                        log_ia(f"Error JSON persistente: {e}. Texto: {limpio}", logs)
                        return {'acciones': []}
                else:
                    log_ia(f"No se encontró JSON válido. Texto: {limpio}", logs)
                    return {'acciones': []}

            # Normalizamos la respuesta para asegurar que siempre sea una lista
            acciones = datos.get('acciones', [])
            
            # Si el modelo devolvió el formato antiguo (solo un objeto), lo convertimos a lista
            if not acciones and 'accion' in datos:
                acciones = [{'accion': datos['accion'], 'lugar': datos.get('lugar', 'unknown')}]
            
            return {'acciones': acciones}

        else:
            log_ia(f"Error en la comunicación con la API de Ollama. Código: {response.status_code}", logs)
            log_ia(f"Respuesta del servidor: {response.text}", logs)
            return {'acciones': []}
            
    except requests.exceptions.RequestException as e:
        log_ia(f"Fallo crítico en la conexión con la API de Ollama. Error: {e}", logs)
        # También imprimimos en consola en este caso crítico para el desarrollador
        print(f"\n[ERROR] No se pudo conectar a Ollama. Asegúrate de que esté en ejecución y sea accesible en {URL_OLLAMA_API}\n")
        return {'acciones': []}
    except json.JSONDecodeError as e:
        log_ia(f"No se pudo decodificar la respuesta JSON de Ollama. Error: {e}", logs)
        return {'acciones': []}

# --- Ejemplo de uso (para pruebas directas del módulo) ---
if __name__ == '__main__':
    logs_prueba = []
    print("Iniciando prueba del módulo de gestión de IA.")
    
    comando_test_1 = "Enciende la luz del salón"
    resultado_1 = procesar_comando_voz(comando_test_1, logs_prueba)
    print(f"Comando: '{comando_test_1}' -> Intención: {resultado_1}\n")

    comando_test_2 = "Por favor, apaga el led"
    resultado_2 = procesar_comando_voz(comando_test_2, logs_prueba)
    print(f"Comando: '{comando_test_2}' -> Intención: {resultado_2}\n")

    comando_test_3 = "Qué tiempo hace hoy?"
    resultado_3 = procesar_comando_voz(comando_test_3, logs_prueba)
    print(f"Comando: '{comando_test_3}' -> Intención: {resultado_3}\n")
    
    print("--- LOGS GENERADOS ---")
    for log in logs_prueba:
        print(log)
