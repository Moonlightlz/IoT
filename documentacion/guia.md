# Guía del Proyecto WASI - Casa Inteligente

Esta guía proporciona una visión general rápida sobre el funcionamiento, las tecnologías y los servicios que componen el sistema WASI.

## 1. Funcionamiento General

El sistema WASI permite controlar dispositivos físicos (luces, motores, etc.) en una maqueta mediante una interfaz web. El flujo principal es:

1.  **Entrada:** El usuario da una orden por voz ("Enciende la cocina") o presiona un botón en la web.
2.  **Procesamiento:**
    *   Si es voz: El servidor transcribe el audio a texto (Whisper) y luego usa Inteligencia Artificial (Llama 3) para entender la intención.
    *   Si es botón: La orden pasa directamente al controlador de red.
3.  **Ejecución:** El servidor envía una señal WiFi al microcontrolador ESP32.
4.  **Hardware:** El ESP32 activa o desactiva el pin correspondiente (enciende/apaga la luz).

## 2. Tecnologías Utilizadas

### Backend (Servidor Central)
*   **Lenguaje:** Python 3.
*   **Framework Web:** Flask (Maneja las rutas y la página web).
*   **Inteligencia Artificial:**
    *   **Ollama:** Ejecuta el modelo de lenguaje **Llama 3** localmente para interpretar comandos complejos.
    *   **SpeechRecognition + Whisper:** Convierte grabaciones de voz a texto con alta precisión.
*   **Audio:** Pydub y FFmpeg para conversión de formatos de audio.

### Frontend (Interfaz de Usuario)
*   **Estructura y Estilo:** HTML5, CSS3 y Bootstrap 5 (Modo oscuro).
*   **Lógica:** JavaScript (ES6+) para manejar la grabación de micrófono y actualizaciones en tiempo real sin recargar la página.

### Hardware
*   **Microcontrolador:** ESP32 (Programado en C++/Arduino).
*   **Comunicación:** Protocolo HTTP sobre WiFi local.

## 3. Servicios Web (API)

El servidor expone los siguientes puntos de acceso (endpoints) para que el frontend se comunique con él:

| Método | Ruta | Descripción |
| :--- | :--- | :--- |
| `GET` | `/` | Carga la página principal del panel de control. |
| `POST` | `/api/command` | Recibe comandos de texto (JSON). Usa IA para procesarlos. |
| `POST` | `/api/voice-command` | Recibe archivos de audio. Transcribe, analiza con IA y ejecuta acciones. |
| `POST` | `/api/device/control` | Control manual directo. Recibe `lugar` y `accion` (ON/OFF). No usa IA. |

## 4. Mapeo de Lugares (Visual vs Interno)

Debido a la configuración física actual, existe una diferencia entre el nombre visual en la web y el identificador interno del sistema:

| Etiqueta en Web (Visual) | ID Interno (Backend/ESP32) |
| :--- | :--- |
| **Dormitorio** | `descanso` |
| **Cocina** | `cocina` |
| **Patio** | `principal` |
| **Sala de Descanso** | `cochera` |
| **Cochera** | `habitacion` |

> **Nota:** Al realizar mantenimiento en el código, utilice siempre el **ID Interno**.

## 5. Servicios Web Consumidos (Dependencias)

El sistema funciona orquestando la comunicación entre distintos servicios web locales:

### 5.1. API de Inteligencia Artificial (Ollama)
*   **Endpoint:** `http://localhost:11434/api/generate`
*   **Método:** `POST`
*   **Uso:** Se utiliza para enviar el prompt con la orden del usuario y recibir la interpretación estructurada en JSON por parte del modelo Llama 3.

### 5.2. Servidor Web del ESP32
*   **Endpoint:** `http://192.168.4.1/control`
*   **Método:** `GET`
*   **Uso:** Recibe peticiones directas para cambiar el estado de los pines. Ejemplo de petición: `?lugar=cocina&accion=on`.