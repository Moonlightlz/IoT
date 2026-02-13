# Resumen Técnico: Estrategias y Métodos (Proyecto WASI)

Este documento recopila las funciones críticas, métodos y estrategias de ingeniería de software utilizadas en el desarrollo del sistema IoT.

## 1. Backend (Python) - Inteligencia Artificial (`gestion_ia.py`)

### Estrategia: Prompt Engineering Estructurado
**Explicación:** Se define un prompt rígido ("System Prompt") para forzar al modelo de lenguaje (Llama 3) a comportarse como un motor de extracción de datos JSON, prohibiendo el texto conversacional.

```python
prompt_estructurado = (
    "Eres un asistente de domótica... "
    "Tu respuesta debe ser ESTRICTAMENTE un objeto JSON con la clave 'acciones'..."
    "Formato JSON: {\"acciones\": [{\"accion\": \"ON\"|\"OFF\", \"lugar\": \"codigo_interno\"}, ...]} "
)
```

### Método: Recuperación de Errores JSON (Parsing Resiliente)
**Explicación:** Los LLMs locales a veces generan JSON malformado. Se implementa lógica para limpiar etiquetas Markdown y "parchear" cierres de llaves faltantes.

```python
# Limpieza de etiquetas markdown que suele añadir el modelo
limpio = respuesta_modelo.replace('```json', '').replace('```', '').strip()

# Parche para error observado: si empieza con { y termina en ], le falta la } final
if limpio.startswith('{') and limpio.endswith(']'):
    limpio += '}'
```

## 2. Backend (Python) - Servidor y Audio (`app.py`)

### Estrategia: Procesamiento de Audio en Memoria (In-Memory Buffers)
**Explicación:** Para evitar latencia de disco (I/O), se convierte el audio recibido (WebM) a WAV utilizando buffers en RAM (`io.BytesIO`) antes de pasarlo al reconocedor.

```python
song = AudioSegment.from_file(audio_file) # Lee formato WebM
wav_io = io.BytesIO()
song.export(wav_io, format="wav") # Exporta a WAV en memoria RAM
wav_io.seek(0)
```

### Método: Inferencia Local de Voz (Whisper)
**Explicación:** Uso de la librería `SpeechRecognition` con el motor `whisper` configurado para CPU (`fp16=False`) para transcribir voz sin depender de internet.

```python
recognizer = sr.Recognizer()
# fp16=False es CRUCIAL para evitar errores en CPUs estándar
texto_transcrito = recognizer.recognize_whisper(audio_data, language="spanish", fp16=False)
```

## 3. Backend (Python) - Comunicación (`control_red.py`)

### Método: Peticiones HTTP Síncronas
**Explicación:** Abstracción del control de hardware mediante peticiones GET estándar, normalizando los parámetros para asegurar compatibilidad con el ESP32.

```python
# Normalización a minúsculas para coincidir con el firmware
lugar_param = lugar.lower()
url_comando = f"{URL_BASE_ESP32}/control"

# Envío de parámetros en la query string (?lugar=...&accion=...)
response = requests.get(url_comando, params={'lugar': lugar_param, 'accion': estado_param}, timeout=5)
```

## 4. Frontend (JavaScript) - Interfaz (`script.js`)

### Estrategia: Captura de Audio Nativa (MediaRecorder API)
**Explicación:** Uso de APIs modernas del navegador para capturar el flujo del micrófono y empaquetarlo en un `Blob` para su envío, sin plugins externos.

```javascript
const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
mediaRecorder = new MediaRecorder(stream);

// Acumulación de fragmentos de audio
mediaRecorder.ondataavailable = event => { audioChunks.push(event.data); };

// Creación del archivo virtual al detener
const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
```

### Método: Manipulación del DOM Reactiva
**Explicación:** Actualización visual de los indicadores LED basada estrictamente en la respuesta del servidor, garantizando que la UI refleje el estado real.

```javascript
const updateIndicators = (intention, lugar) => {
    const el = document.getElementById(`status-${lugar}`);
    if (intention === 'ON') el.classList.add('on'); // Añade clase CSS 'encendido'
    else if (intention === 'OFF') el.classList.remove('on');
};
```

## 5. Hardware (C++ / Arduino) - Firmware

### Estrategia: Servidor Web Embebido
**Explicación:** El microcontrolador implementa un servidor HTTP ligero para escuchar comandos en rutas específicas, actuando como una API REST básica.

```cpp
WebServer server(80);

void manejarControl() {
    String lugar = server.arg("lugar"); // Obtiene param URL
    // Lógica de control de pines...
    server.send(200, "text/plain", "OK");
}
```