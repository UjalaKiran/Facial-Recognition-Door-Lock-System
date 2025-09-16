#include <WebServer.h>

#include <WiFi.h>

#include <esp32cam.h>



const char* WIFI_SSID = "Dur E";

const char* WIFI_PASS = "abcs1234";



WebServer server(80);



static auto loRes = esp32cam::Resolution::find(320, 240);

static auto hiRes = esp32cam::Resolution::find(800, 600);



const int solenoidPin = 13; 


void serveJpg() {

  auto frame = esp32cam::capture();

  if (frame == nullptr) {

    Serial.println("CAPTURE FAIL");

    server.send(503, "", "");

    return;

  }

  Serial.printf("CAPTURE OK %dx%d %db\n", frame->getWidth(), frame->getHeight(),

                static_cast<int>(frame->size()));



  server.setContentLength(frame->size());

  server.send(200, "image/jpeg");

  WiFiClient client = server.client();

  frame->writeTo(client);

}



void handleJpgLo() {

  if (!esp32cam::Camera.changeResolution(loRes)) {

    Serial.println("SET-LO-RES FAIL");

  }

  serveJpg();

}



void handleJpgHi() {

  if (!esp32cam::Camera.changeResolution(hiRes)) {

    Serial.println("SET-HI-RES FAIL");

  }

  serveJpg();

}



void handleUnlock() {

  digitalWrite(solenoidPin, HIGH); // Unlock the solenoid

  Serial.print("unlocked solenoid");

  delay(20000);                     // Keep it unlocked for 5 seconds

  digitalWrite(solenoidPin, LOW);  // Lock it again

  server.send(200, "text/plain", "Lock activated");

}



void setup() {

  Serial.begin(115200);

  Serial.println();



  // Initialize solenoid pin

  pinMode(solenoidPin, OUTPUT);

  digitalWrite(solenoidPin, LOW); // Ensure solenoid is locked initially



  // Initialize ESP32-CAM

  using namespace esp32cam;

  Config cfg;

  cfg.setPins(pins::AiThinker);

  cfg.setResolution(hiRes);

  cfg.setBufferCount(2);

  cfg.setJpeg(80);



  bool ok = Camera.begin(cfg);

  Serial.println(ok ? "CAMERA OK" : "CAMERA FAIL");



  // Connect to Wi-Fi

  WiFi.persistent(false);

  WiFi.mode(WIFI_STA);

  WiFi.begin(WIFI_SSID, WIFI_PASS);

  while (WiFi.status() != WL_CONNECTED) {

    delay(500);

    Serial.print(".");

  }

  Serial.println("\nWi-Fi Connected!");

  Serial.print("Access the camera at: http://");

  Serial.println(WiFi.localIP());



  // Register endpoints

  server.on("/cam-lo.jpg", handleJpgLo);

  server.on("/cam-hi.jpg", handleJpgHi);

  server.on("/unlock", handleUnlock); // Endpoint for unlocking the solenoid



  server.begin();

}



void loop() {

  server.handleClient();

}