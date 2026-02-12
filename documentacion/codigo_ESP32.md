#include <WiFi.h>
#include <WebServer.h>


const char* ssid = "mapache_test";
const char* password = "mapache123";


WebServer server(80);


// Pines según la placa física
const int LED_DEBUG   = 2;   // LED Azul interno
const int PIN_DESCANS = 23;
const int PIN_COCINA  = 22;
const int PIN_PRINCI  = 5;
const int PIN_COCHERA = 4;
const int PIN_HABITAC = 15;


int ambientes[] = {23, 22, 5, 4, 15};


void logDebug(String msg) {
  Serial.println("[DEPURACION] " + msg);
}


// Función para actualizar el LED azul de depuración
void actualizarLedDebug() {
  bool algunEncendido = false;
  for(int i=0; i<5; i++) {
    if(digitalRead(ambientes[i]) == HIGH) {
      algunEncendido = true;
      break;
    }
  }
  digitalWrite(LED_DEBUG, algunEncendido ? HIGH : LOW);
  logDebug("Estado LED Debug: " + String(algunEncendido ? "ENCENDIDO" : "APAGADO"));
}


void manejarControl() {
  String lugar = server.arg("lugar");
  String estado = server.arg("accion");
  int val = (estado == "on") ? HIGH : LOW;


  logDebug("Peticion IA: " + lugar + " -> " + estado);


  if (lugar == "todas") {
    for(int i=0; i<5; i++) digitalWrite(ambientes[i], val);
  } else {
    if (lugar == "descanso") digitalWrite(PIN_DESCANS, val);
    else if (lugar == "cocina") digitalWrite(PIN_COCINA, val);
    else if (lugar == "principal") digitalWrite(PIN_PRINCI, val);
    else if (lugar == "cochera") digitalWrite(PIN_COCHERA, val);
    else if (lugar == "habitacion") digitalWrite(PIN_HABITAC, val);
  }


  actualizarLedDebug();
  server.send(200, "text/plain", "OK");
}


void setup() {
  Serial.begin(115200);
 
  // Configurar y APAGAR inmediatamente para evitar el encendido inicial
  pinMode(LED_DEBUG, OUTPUT);
  digitalWrite(LED_DEBUG, LOW);
 
  logDebug("Configurando pines de ambientes...");
  for(int i=0; i<5; i++) {
    pinMode(ambientes[i], OUTPUT);
    digitalWrite(ambientes[i], LOW); // Fuerza el apagado inicial
  }


  WiFi.softAP(ssid, password);
  logDebug("Red 'mapache_test' lista. IP: " + WiFi.softAPIP().toString());


  server.on("/control", manejarControl);
  server.begin();
  logDebug("Servidor iniciado y pines reseteados a LOW.");
}


void loop() {
  server.handleClient();
}

asdasdasd