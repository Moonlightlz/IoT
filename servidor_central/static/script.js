/**
 * Lógica del frontend para el panel de control de la Casa Inteligente.
 */

document.addEventListener('DOMContentLoaded', () => {

    const commandInput = document.getElementById('command-input');
    const micBtn = document.getElementById('mic-btn');
    const sendBtn = document.getElementById('send-command-btn');
    const btnText = document.getElementById('btn-text');
    const loadingSpinner = document.getElementById('loading-spinner');
    const logsOutput = document.getElementById('logs-output');

    const API_URL = 'http://127.0.0.1:5000/api/command';
    const VOICE_API_URL = 'http://127.0.0.1:5000/api/voice-command';
    const DEVICE_CONTROL_URL = 'http://127.0.0.1:5000/api/device/control';

    /**
     * Añade un mensaje de log a la consola del frontend.
     * @param {string} message - El mensaje a mostrar.
     * @param {string} type - 'info', 'error', 'success' para el estilo.
     */
    const logToConsole = (message, type = 'info') => {
        const timestamp = new Date().toLocaleTimeString();
        logsOutput.innerHTML += `[${timestamp}] <span class="log-${type}">${message}</span>\n`;
        // Hacer scroll automático al final
        logsOutput.scrollTop = logsOutput.scrollHeight;
    };

    /**
     * Actualiza el estado visual de los indicadores LED.
     * @param {string} intention - 'ON' o 'OFF'.
     * @param {string} lugar - El lugar afectado ('cocina', 'todas', etc).
     */
    const updateIndicators = (intention, lugar) => {
        const validPlaces = ['descanso', 'cocina', 'principal', 'cochera', 'habitacion'];
        
        if (lugar === 'todas') {
            validPlaces.forEach(place => {
                const el = document.getElementById(`status-${place}`);
                if (el) {
                    if (intention === 'ON') el.classList.add('on');
                    else if (intention === 'OFF') el.classList.remove('on');
                }
            });
            logToConsole(`Acción ${intention} aplicada a TODAS las zonas.`, 'success');
        } else {
            const el = document.getElementById(`status-${lugar}`);
            if (el) {
                if (intention === 'ON') el.classList.add('on');
                else if (intention === 'OFF') el.classList.remove('on');
                logToConsole(`Acción ${intention} aplicada en: ${lugar.toUpperCase()}.`, 'success');
            } else {
                logToConsole(`Lugar desconocido o no visualizado: ${lugar}`, 'warning');
            }
        }
    };

    /**
     * Envía el comando al backend a través de la API.
     */
    const sendCommand = async () => {
        const command = commandInput.value.trim();
        if (command === '') {
            logToConsole('El comando no puede estar vacío.', 'error');
            return;
        }

        // Desactivar botón y mostrar spinner
        sendBtn.disabled = true;
        btnText.textContent = 'Procesando...';
        loadingSpinner.classList.remove('d-none');
        logToConsole(`Enviando comando: "${command}"`, 'info');

        try {
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ command: command }),
            });

            const result = await response.json();

            // Mostrar logs del backend
            if (result.logs && Array.isArray(result.logs)) {
                result.logs.forEach(log => {
                    logsOutput.innerHTML += `${log}\n`;
                });
                logsOutput.scrollTop = logsOutput.scrollHeight;
            }

            // Actualizar indicadores visuales
            if (result.resultados && Array.isArray(result.resultados)) {
                result.resultados.forEach(res => {
                    if (res.exito) {
                        updateIndicators(res.accion, res.lugar);
                    }
                });
            } else if (result.status === 'failed') {
                logToConsole('No se ejecutaron acciones o hubo un error.', 'error');
            }


        } catch (error) {
            logToConsole(`Error de conexión con el servidor: ${error.message}`, 'error');
            console.error('Error en la petición fetch:', error);
        } finally {
            // Reactivar el botón y ocultar spinner
            sendBtn.disabled = false;
            btnText.textContent = 'Enviar';
            loadingSpinner.classList.add('d-none');
            commandInput.value = ''; // Limpiar el input
        }
    };

    // --- Lógica de Grabación de Voz Local (MediaRecorder) ---
    let mediaRecorder;
    let audioChunks = [];
    let recordingTimeout;

    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        micBtn.addEventListener('click', async () => {
            if (micBtn.classList.contains('recording')) {
                // Detener grabación
                clearTimeout(recordingTimeout);
                mediaRecorder.stop();
                micBtn.classList.remove('recording', 'btn-danger');
                micBtn.classList.add('btn-secondary');
                micBtn.innerHTML = '<i class="bi bi-mic"></i>';
                logToConsole('Procesando audio localmente...', 'info');
                
                // UI de carga
                sendBtn.disabled = true;
                loadingSpinner.classList.remove('d-none');
            } else {
                // Iniciar grabación
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    mediaRecorder = new MediaRecorder(stream);
                    audioChunks = [];

                    mediaRecorder.ondataavailable = event => {
                        audioChunks.push(event.data);
                    };

                    mediaRecorder.onstop = async () => {
                        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                        const formData = new FormData();
                        formData.append('audio', audioBlob, 'recording.webm');

                        try {
                            const response = await fetch(VOICE_API_URL, {
                                method: 'POST',
                                body: formData
                            });
                            const result = await response.json();

                            if (result.transcription) {
                                commandInput.value = result.transcription;
                                logToConsole(`Transcripción local: "${result.transcription}"`, 'success');
                            }
                            
                            // Mostrar logs y actualizar estado (reutilizando lógica visual)
                            if (result.logs) result.logs.forEach(l => logsOutput.innerHTML += `${l}\n`);
                            
                            if (result.resultados && Array.isArray(result.resultados)) {
                                result.resultados.forEach(res => {
                                    if (res.exito) updateIndicators(res.accion, res.lugar);
                                });
                                
                            } else if (result.status === 'failed') {
                                logToConsole('Error: El hardware no respondió.', 'error');
                            }
                            
                            logsOutput.scrollTop = logsOutput.scrollHeight;

                        } catch (error) {
                            logToConsole(`Error al enviar audio: ${error.message}`, 'error');
                        } finally {
                            sendBtn.disabled = false;
                            loadingSpinner.classList.add('d-none');
                        }
                    };

                    mediaRecorder.start();
                    micBtn.classList.add('recording', 'btn-danger');
                    micBtn.classList.remove('btn-secondary');
                    micBtn.innerHTML = '<i class="bi bi-mic-fill"></i>';
                    logToConsole('Grabando audio (máx 3s)...', 'info');

                    recordingTimeout = setTimeout(() => {
                        if (mediaRecorder.state === 'recording') {
                            mediaRecorder.stop();
                            micBtn.classList.remove('recording', 'btn-danger');
                            micBtn.classList.add('btn-secondary');
                            micBtn.innerHTML = '<i class="bi bi-mic"></i>';
                            logToConsole('Tiempo límite alcanzado. Procesando...', 'info');
                            
                            sendBtn.disabled = true;
                            loadingSpinner.classList.remove('d-none');
                        }
                    }, 5000);

                } catch (err) {
                    logToConsole(`No se pudo acceder al micrófono: ${err}`, 'error');
                }
            }
        });
    } else {
        logToConsole('Tu navegador no soporta grabación de audio.', 'error');
        micBtn.disabled = true;
    }

    // --- Lógica para Botones Manuales (ON/OFF) ---
    const manualButtons = document.querySelectorAll('.btn-manual');
    manualButtons.forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const lugar = e.target.getAttribute('data-lugar');
            const accion = e.target.getAttribute('data-accion');
            
            logToConsole(`Enviando comando manual: ${accion} -> ${lugar}...`, 'info');

            try {
                const response = await fetch(DEVICE_CONTROL_URL, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ lugar: lugar, accion: accion })
                });
                
                const result = await response.json();

                // Mostrar logs del backend
                if (result.logs) result.logs.forEach(l => logsOutput.innerHTML += `${l}\n`);
                logsOutput.scrollTop = logsOutput.scrollHeight;

                // Actualizar UI
                if (result.resultados && result.resultados.length > 0) {
                    const res = result.resultados[0];
                    if (res.exito) updateIndicators(res.accion, res.lugar);
                    else logToConsole('Error: Fallo de conexión con el hardware.', 'error');
                } else {
                    logToConsole('Error: Fallo de conexión con el hardware.', 'error');
                }
            } catch (error) {
                logToConsole(`Error en control manual: ${error.message}`, 'error');
            }
        });
    });

    // --- Event Listeners ---
    sendBtn.addEventListener('click', sendCommand);

    // Permitir enviar con la tecla Enter
    commandInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            sendCommand();
        }
    });

    logToConsole('Panel de control inicializado. Listo para recibir órdenes.');
});
