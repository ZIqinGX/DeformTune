const int sensorPinA0 = A0;
const int sensorPinA1 = A1;

int baselineA0 = 0;
int baselineA1 = 0;

int stableCountA0 = 0;
int stableCountA1 = 0;

const int stabilityThreshold = 10;    // allowable noise range
const int maxStableCount = 50;        // how many stable readings before updating baseline

float smoothedA0 = 0.0;
float smoothedA1 = 0.0;
const float alpha = 0.1;              // smoothing factor

void setup() {
  Serial.begin(9600);
  delay(1000);
  baselineA0 = analogRead(sensorPinA0);
  baselineA1 = analogRead(sensorPinA1);
  Serial.println("Auto-calibrating Velostat interface...");
}

void loop() {
  int rawA0 = analogRead(sensorPinA0);
  int rawA1 = analogRead(sensorPinA1);

  // ==== A0 Auto-baseline logic ====
  if (abs(rawA0 - baselineA0) < stabilityThreshold) {
    stableCountA0++;
    if (stableCountA0 > maxStableCount) {
      baselineA0 = (baselineA0 * 9 + rawA0) / 10;  // smooth baseline update
      stableCountA0 = maxStableCount;
    }
  } else {
    stableCountA0 = 0;
  }

  // ==== A1 Auto-baseline logic ====
  if (abs(rawA1 - baselineA1) < stabilityThreshold) {
    stableCountA1++;
    if (stableCountA1 > maxStableCount) {
      baselineA1 = (baselineA1 * 9 + rawA1) / 10;
      stableCountA1 = maxStableCount;
    }
  } else {
    stableCountA1 = 0;
  }

  // Subtract baseline to get relative values
  int relativeA0 = rawA0 - baselineA0;
  int relativeA1 = rawA1 - baselineA1;

  // Optional smoothing
  smoothedA0 = alpha * relativeA0 + (1 - alpha) * smoothedA0;
  smoothedA1 = alpha * relativeA1 + (1 - alpha) * smoothedA1;

  // Map to -1.0 to 0.0 (optional depending on your model)
  float normA0 = constrain(-1.0 + (smoothedA0 / 1023.0), -1.0, 0.0);
  float normA1 = constrain(-1.0 + (smoothedA1 / 1023.0), -1.0, 0.0);

  Serial.print(normA0, 4);
  Serial.print(",");
  Serial.println(normA1, 4);

  delay(100);  // send data every 100ms
}
