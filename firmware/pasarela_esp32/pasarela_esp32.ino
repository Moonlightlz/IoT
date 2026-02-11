

// --- Inclusión de Librerías ---
#include <WiFi.h>
#include <WebServer.h>

// --- Constantes de Configuración ---
const char* ssid = "mapache_test"; // Nombre del Punto de Acceso Wi-Fi
const int pinLedAzul = 2;                 // Pin donde está conectado el LED azul (GPIO2)

// Configuración de la dirección IP estática del servidor
IPAddress ipLocal(192, 168, 4, 1);    // IP estática del ESP32
IPAddress gateway(192, 168, 4, 1);    // La puerta de enlace es la misma IP
IPAddress subnet(255, 255, 255, 0);   // Máscara de subred estándar

// --- Objetos Globales ---
WebServer server(80); // Objeto para gestionar el servidor web en el puerto 80

// --- Funciones Manejadoras de Rutas (Handlers) ---

/**
 * @brief Maneja las peticiones para encender el LED.
 * Responde al cliente con un mensaje de confirmación.
 */
void handleLedOn() {
  Serial.println("Peticion recibida: /led/on");
  digitalWrite(pinLedAzul, HIGH); // Encender el LED
  server.send(200, "text/plain", "LED encendido correctamente.");
}

/**
 * @brief Maneja las peticiones para apagar el LED.
 * Responde al cliente con un mensaje de confirmación.
 */
void handleLedOff() {
  Serial.println("Peticion recibida: /led/off");
  digitalWrite(pinLedAzul, LOW); // Apagar el LED
  server.send(200, "text/plain", "LED apagado correctamente.");
}

/**
 * @brief Maneja las peticiones a la raíz del servidor.
 * Sirve para verificar que el servidor está activo.
 */
void handleRoot() {
  Serial.println("Peticion recibida en la raíz /");
  server.send(200, "text/plain", "Servidor ESP32 activo. Bienvenido a la Casa Inteligente.");
}

/**
 * @brief Maneja las peticiones a rutas no encontradas.
 */
void handleNotFound() {
  String message = "Ruta no encontrada\n\n";
  message += "URI: ";
  message += server.uri();
  message += "\nMetodo: ";
  message += (server.method() == HTTP_GET) ? "GET" : "POST";
  message += "\n";
  server.send(404, "text/plain", message);
  Serial.println("Peticion a una ruta no encontrada.");
}


// --- Funciones Principales de Arduino ---

/**
 * @brief Función de configuración inicial. Se ejecuta una sola vez al encender el ESP32.
 */
void setup() {
  // 1. Iniciar comunicación serial para depuración
  Serial.begin(115200);
  Serial.println("\nIniciando sistema de pasarela...");

  // 2. Configurar el pin del LED como salida
  pinMode(pinLedAzul, OUTPUT);
  digitalWrite(pinLedAzul, LOW); // Asegurarse de que el LED empieza apagado

  // 3. Configurar y levantar el Punto de Acceso (Access Point)
  Serial.print("Configurando punto de acceso...");
  WiFi.softAPConfig(ipLocal, gateway, subnet);
  if (WiFi.softAP(ssid)) {
    Serial.println(" ¡Éxito!");
    Serial.print("SSID de la red: ");
    Serial.println(ssid);
    Serial.print("Dirección IP: ");
    Serial.println(WiFi.softAPIP());
  } else {
    Serial.println(" ¡Fallo!");
  }

  // 4. Definir las rutas del servidor web y sus manejadores
  server.on("/", HTTP_GET, handleRoot);
  server.on("/led/on", HTTP_GET, handleLedOn);
  server.on("/led/off", HTTP_GET, handleLedOff);
  server.onNotFound(handleNotFound);

  // 5. Iniciar el servidor web
  server.begin();
  Serial.println("Servidor HTTP iniciado. Esperando peticiones...");
}

/**
 * @brief Bucle principal. Se ejecuta repetidamente después de setup().
 */
void loop() {
  // Gestiona las peticiones de clientes que lleguen al servidor
  server.handleClient();
}
