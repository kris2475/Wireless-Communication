void setup() {

  // initialize both serial ports:

  Serial.begin(9600);

  Serial1.begin(9600);
}

void loop() {

  // read from port 1, send to port 0:
  if (Serial1.available()) {
    //Serial.println("Serial1");

    int inByte1 = Serial1.read();

    Serial.write(inByte1);

  }

  // read from port 0, send to port 1:
  if (Serial.available()) {
    //Serial.println("Serial");
    
    int inByte0 = Serial.read();

    Serial1.write(inByte0);

  }
}
