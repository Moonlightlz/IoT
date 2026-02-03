# Documentación Técnica: Sistema de Casa Inteligente (Servidor Central)

## 1. Descripción General

El sistema **Casa Inteligente** es una aplicación web diseñada para controlar una maqueta domótica mediante comandos de voz y texto. El núcleo del sistema reside en un servidor central que orquesta la comunicación entre una interfaz de usuario web, un modelo de Inteligencia Artificial local (para procesamiento de lenguaje natural) y los nodos de hardware (ESP32).

**Funcionalidad Principal:**
*   Interpretación de comandos en lenguaje natural (ej: "Enciende la luz de la cocina y apaga la cochera").
*   Transcripción de audio a texto en local.
*   Control manual de dispositivos mediante botones.
*   Visualización de logs y estado del sistema en tiempo real.

---

## 2. Tecnologías y Lenguajes

El proyecto utiliza una arquitectura modular basada en los siguientes lenguajes y herramientas:

*   **Backend:** Python 3.
    *   **Framework Web:** Flask (API REST y servicio de archivos estáticos).
    *   **IA Generativa:** Ollama (Llama 3) para interpretación de intenciones.
    *   **Reconocimiento de Voz:** SpeechRecognition con motor OpenAI Whisper (ejecución local).
    *   **Audio:** Pydub (manipulación de archivos de audio).
*   **Frontend:**
    *   **Lenguajes:** HTML5, CSS3, JavaScript (ES6+).
    *   **Librerías:** Bootstrap 5 (Diseño responsivo).
*   **Comunicación Hardware:** Protocolo HTTP (GET requests) sobre WiFi.

---

## 3. Arquitectura del Backend

El backend se divide en tres módulos principales de Python:

### 3.1. `app.py` (Controlador Principal)
Es el punto de entrada de la aplicación Flask. Gestiona las rutas HTTP y coordina los otros módulos.

**Rutas de la API:**
*   `GET /`: Renderiza la interfaz principal (`index.html`).
*   `POST /api/command`: Recibe comandos de texto JSON, los procesa con IA y ejecuta acciones.
*   `POST /api/voice-command`: Recibe archivos de audio (blob), los convierte a formato WAV, transcribe el audio a texto usando Whisper y luego procesa el texto resultante.
*   `POST /api/device/control`: Endpoint para control manual directo (bypassea la IA para mayor velocidad).

**Funciones Clave:**
*   `ejecutar_logica_domotica(comando_usuario, logs)`: Función auxiliar que centraliza el flujo: Texto -> IA -> Lista de Acciones -> Ejecución Hardware.

### 3.2. `gestion_ia.py` (Capa de Inteligencia)
Encargado de la comunicación con el modelo de lenguaje local (Ollama).

**Funciones:**
*   `procesar_comando_voz(texto_usuario, logs)`:
    *   Construye un *prompt* estructurado con las reglas del sistema y los lugares válidos ('descanso', 'cocina', 'principal', 'cochera', 'habitacion').
    *   Envía la solicitud a la API de Ollama (`localhost:11434`).
    *   Limpia y parsea la respuesta para extraer un objeto JSON estricto.
    *   **Retorno:** Un diccionario con una lista de acciones normalizadas (ej: `{'acciones': [{'accion': 'ON', 'lugar': 'cocina'}]}`).
*   `log_ia(mensaje, logs)`: Sistema de registro específico para eventos de IA.

### 3.3. `control_red.py` (Capa de Hardware)
Gestiona la comunicación de red con el microcontrolador ESP32.

**Configuración:**
*   Dirección IP del nodo hardware: `192.168.4.1`.

**Funciones:**
*   `controlar_maqueta(lugar, estado, logs)`: Envía una petición HTTP GET al ESP32 (ej: `http://192.168.4.1/control?lugar=cocina&accion=on`). Retorna `True` si el hardware responde con código 200.
*   `verificar_conexion_nodo(logs)`: Comprueba si el ESP32 está accesible en la red.
*   **Funciones Placeholder (Futuras):** `leer_sensor_temperatura_dht22`, `leer_sensor_gas_mq2`, `leer_sensor_movimiento_pir`. Actualmente solo registran logs de "no implementado".

---

## 4. Arquitectura del Frontend

La interfaz de usuario reside en la carpeta `static` y `templates`.

### 4.1. Interfaz (`index.html` & `style.css`)
*   Diseño oscuro ("Dark Mode") utilizando clases de Bootstrap y estilos personalizados.
*   Sección de consola de comandos con entrada de texto y botón de micrófono.
*   Panel de logs tipo consola para depuración visual.
*   Lista de estados de dispositivos con indicadores visuales (LEDs virtuales) y botones de control manual.

### 4.2. Lógica de Cliente (`script.js`)
Maneja la interacción del usuario y las llamadas asíncronas al backend.

**Métodos y Flujos:**
*   **Grabación de Audio:** Utiliza la API `MediaRecorder` del navegador.
    1.  Captura el audio del micrófono.
    2.  Genera un `Blob` de tipo `audio/webm`.
    3.  Envía el archivo mediante `FormData` al endpoint `/api/voice-command`.
*   **Actualización de UI:**
    *   `logToConsole()`: Inyecta mensajes en el panel de logs HTML.
    *   `updateIndicators()`: Cambia el estilo CSS de los indicadores de estado (azul para ON, gris para OFF) basándose en la respuesta del servidor.
*   **Manejo de Errores:** Captura excepciones de red (fetch) y muestra alertas en la consola visual.

---

## 5. Flujo de Datos (Ejemplo: Comando de Voz)

1.  **Usuario:** Presiona el botón de micrófono y dice "Enciende la cocina".
2.  **Frontend (JS):** Graba el audio, crea un archivo WebM y lo envía vía POST a Flask.
3.  **Backend (App):**
    *   Recibe el archivo.
    *   Usa `pydub` para convertir WebM a WAV.
    *   Usa `SpeechRecognition` + `Whisper` para transcribir a texto: "Enciende la cocina".
4.  **Backend (IA):**
    *   Envía el texto a Ollama.
    *   Ollama analiza la intención y devuelve JSON: `{"acciones": [{"accion": "ON", "lugar": "cocina"}]}`.
5.  **Backend (Red):**
    *   Itera sobre las acciones.
    *   Envía GET a `http://192.168.4.1/control?lugar=cocina&accion=on`.
6.  **Hardware:** Ejecuta la acción física.
7.  **Respuesta:** El backend devuelve el resultado y los logs al frontend.
8.  **Frontend:** Muestra la transcripción, los logs y enciende el indicador visual de la cocina.

---

## 6. Consideraciones Técnicas y Limitaciones

### 6.1. Dependencias de Hardware
*   **Red WiFi:** El servidor asume que el ESP32 actúa como punto de acceso (AP) o tiene una IP estática asignada (`192.168.4.1`). Si la IP cambia, debe actualizarse en `control_red.py`.
*   **Conectividad:** El servidor donde corre la app debe estar en la misma red que el ESP32.

### 6.2. Dependencias de Software Local
*   **Ollama:** Debe estar ejecutándose en segundo plano (`ollama serve`) y tener descargado el modelo especificado en `gestion_ia.py` (actualmente `llama3`).
*   **FFmpeg:** Necesario en el sistema operativo anfitrión para que `pydub` pueda convertir formatos de audio.

### 6.3. Latencia
*   El uso de modelos locales (Whisper y Llama 3) introduce una latencia variable dependiendo de la potencia de la CPU/GPU del servidor central.
*   Se ha implementado un pequeño retraso (`time.sleep(0.3)`) entre peticiones al hardware en `app.py` para evitar saturar el servidor web del ESP32.

### 6.4. Manejo de Errores de IA
*   El módulo `gestion_ia.py` incluye lógica de recuperación ("parches") para corregir JSONs mal formados que a veces devuelve el modelo de lenguaje (ej: falta de llaves de cierre).

---

## 7. Guía de Instalación y Ejecución Paso a Paso

### 7.1. Prerrequisitos
1.  **Python 3.x**: Asegúrese de tener Python instalado y agregado al PATH del sistema.
2.  **FFmpeg**: Necesario para el procesamiento de audio (`pydub`).
    *   Descargar y agregar la carpeta `bin` a las variables de entorno (PATH).
3.  **Ollama**: Descargar e instalar desde ollama.com.

### 7.2. Configuración de Ollama (IA Local)
Es crucial ejecutar Ollama como servidor para ver los logs de inferencia y asegurar que la API esté escuchando correctamente.

1.  Abra una terminal (CMD o PowerShell).
2.  Ejecute el siguiente comando para iniciar el servidor y ver los logs en tiempo real:
    ```bash
    ollama serve
    ```
    *Mantenga esta terminal abierta en segundo plano. Aquí verá cuándo el modelo se carga y procesa tokens.*
3.  Abra una **nueva** terminal y descargue el modelo Llama 3 (si no lo ha hecho antes):
    ```bash
    ollama pull llama3
    ```

### 7.3. Instalación del Servidor Central
1.  Navegue a la carpeta del servidor central en su terminal:
    ```bash
    cd ruta/al/proyecto/servidor_central
    ```
2.  Instale las librerías de Python necesarias:
    ```bash
    pip install Flask Flask-CORS requests SpeechRecognition pydub
    ```

### 7.4. Ejecución del Sistema
1.  Conecte el hardware (ESP32) y asegúrese de que esté en la misma red WiFi.
2.  En la terminal del proyecto, inicie la aplicación Flask:
    ```bash
    python app.py
    ```
3.  Abra un navegador web e ingrese a la siguiente dirección para ver el panel de control:
    `http://localhost:5000`
