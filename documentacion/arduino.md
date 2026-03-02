#include "DHT.h"
#include <Servo.h> 

// Configuración DHT22
#define DHTPIN 2      
#define DHTTYPE DHT22 
DHT dht(DHTPIN, DHTTYPE);

// Configuración Sensor de Gas
const int pinGas = A0; 

// Configuración Ultrasonido HC-SR04
const int pinTrig = 4;
const int pinEcho = 5;

// Configuración LEDs de Alarma (Pines en orden para el círculo)
const int ledsAlarma[] = {13, 12, 11, 10}; 

// Configuración Servomotor
Servo miServo;
const int pinServo = 9;

// Variables Globales
unsigned long tiempoPrevioClima = 0;
const long intervaloClima = 2000; 
bool ledManualEncendido = false; 

void setup() {
  Serial.begin(9600); 
  pinMode(pinGas, INPUT);
  pinMode(pinTrig, OUTPUT);
  pinMode(pinEcho, INPUT);
  
  // Inicializar los 4 pines de alerta
  for(int i = 0; i < 4; i++) {
    pinMode(ledsAlarma[i], OUTPUT);
  }
  
  miServo.attach(pinServo);
  miServo.write(0); 
  
  dht.begin();
  Serial.println("--- Sistema con Alarma Circular: Gas + Clima + Distancia + Servo ---");
}

void loop() {
  // --- 1. Lectura de Comandos Seriales ---
  if (Serial.available() > 0) {
    String comando = Serial.readStringUntil('\n');
    comando.trim();
    
    if (comando.startsWith("SERVO:")) {
      int angulo = comando.substring(6).toInt();
      miServo.write(constrain(angulo, 0, 90));
    }
    
    if (comando == "LED:1") ledManualEncendido = true;
    if (comando == "LED:0") ledManualEncendido = false;
  }

  // --- 2. Lógica de Sensores ---
  digitalWrite(pinTrig, LOW);
  delayMicroseconds(2);
  digitalWrite(pinTrig, HIGH);
  delayMicroseconds(10);
  digitalWrite(pinTrig, LOW);
  
  long duracion = pulseIn(pinEcho, HIGH, 30000); 
  int distancia = duracion * 0.034 / 2;
  int valorGasActual = analogRead(pinGas);

  // --- Lógica Automática del Servo (Distancia <= 10cm) ---
  if (distancia > 0 && distancia <= 10) {
    Serial.println("--- Puerta Abierta por Proximidad ---");
    miServo.write(90);  
    delay(5000);        
    miServo.write(0);   
    delay(1000);
  }

  // --- 3. Lógica de Alarma Circular (Gas > 400) ---
  if (valorGasActual > 400) {
    // IMPORTANTE: Avisar a la web INMEDIATAMENTE, sin esperar al temporizador
    Serial.print("ALERTA | Gas: ");
    Serial.println(valorGasActual);

    // Ciclo para encender uno por uno en círculo
    for (int i = 0; i < 4; i++) {
      for (int j = 0; j < 4; j++) digitalWrite(ledsAlarma[j], LOW);
      digitalWrite(ledsAlarma[i], HIGH);
      delay(100); 
    }
  } else {
    // Modo Manual
    int estadoManual = ledManualEncendido ? HIGH : LOW;
    for (int i = 0; i < 4; i++) digitalWrite(ledsAlarma[i], estadoManual);
  }

  // --- 4. Envío de Datos a la Web (Periódico) ---
  unsigned long tiempoActual = millis();
  
  // Solo imprimimos distancia si no estamos en medio de una alerta de gas (para no ensuciar el serial)
  if (valorGasActual <= 400) {
      Serial.print("Distancia: ");
      Serial.print(distancia > 0 && distancia < 400 ? String(distancia) + "cm" : "---");
  }

  if (tiempoActual - tiempoPrevioClima >= intervaloClima) {
    tiempoPrevioClima = tiempoActual;
    float h = dht.readHumidity();
    float t = dht.readTemperature();
    Serial.print(" | Gas: ");
    Serial.print(valorGasActual);
    Serial.print(" | Temp: ");
    Serial.print(t);
    Serial.print("C | Hum: ");
    Serial.print(h);
    Serial.println("%");
  } else if (valorGasActual <= 400) {
    Serial.println();
  }
  
  delay(50); 
}
