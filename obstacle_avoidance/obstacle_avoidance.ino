#include <stdint.h>
#include <NewPing.h>

#define DIST_MAX_CM 400
#define SEND_DELAY_MS 20

// Serial Protocol
#define SERIAL_START 'S'
#define SERIAL_DELIM ' '
#define SERIAL_STOP '\n'
#define SERIAL_CHARS 3

#define NUM_SENSORS 3

// Sonar devices
NewPing sonar_arr[] = {
  NewPing(2, 3, DIST_MAX_CM),
  NewPing(4, 5, DIST_MAX_CM),
  NewPing(6, 7, DIST_MAX_CM)
};

// Latest updated distances
uint16_t distances[NUM_SENSORS];

void setup() {
  Serial.begin(115200);
}

void loop() {
  delay(SEND_DELAY_MS);
  update_distances();
  serial_send_distances();
}

void update_distances() {
  int i = 0;
  for (i = 0; i < NUM_SENSORS; i++) {
    distances[i] = sonar_arr[i].ping_cm();
  }
}

void serial_send_distances() {
  Serial.write(SERIAL_START);

  int i = 0;
  for (i = 0; i < NUM_SENSORS; i++) {
    Serial.write(SERIAL_DELIM);
    serial_send_3_digits(distances[i]);
  }
  
  Serial.write(SERIAL_STOP);
  Serial.flush();
}

// Always sends 3 digits:
// 0-9 sends 00X
// 10-99 sends 0XX
// 100-999 sends XXX
// > 1000 sends 999
void serial_send_3_digits(uint16_t dist) {
  if (dist < 10){
     Serial.write("00");
     Serial.print(dist);
  } else if (dist < 100){
     Serial.write('0');
     Serial.print(dist);
  } else if (dist < 1000){
     Serial.print(dist);
  } else {
     // Too big :(
     Serial.print(999);
  }
}
