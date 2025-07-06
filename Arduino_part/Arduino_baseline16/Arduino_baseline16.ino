const int analogPins[4] = {A0, A1, A2, A3};
float smoothed[4] = {0, 0, 0, 0};
float minVals[4] = {1, 1, 1, 1};
float maxVals[4] = {0, 0, 0, 0};
int mappedValues[4] = {1, 1, 1, 1};
int activated[4] = {0, 0, 0, 0};

const float alpha = 0.2;
const float activationThreshold = 0.55;

unsigned long lastTriggerTime = 0;
const unsigned long debounceTime = 1500;

void setup() {
  Serial.begin(9600);
  delay(1000);
  Serial.println("✅ Arduino 启动完成");
}

void loop() {
  bool anyActive = false;
  bool allMappedValid = true;

  for (int i = 0; i < 4; i++) {
    int raw = analogRead(analogPins[i]);
    float norm = raw / 1023.0;

    smoothed[i] = alpha * norm + (1 - alpha) * smoothed[i];

    if (smoothed[i] < minVals[i]) minVals[i] = smoothed[i];
    if (smoothed[i] > maxVals[i]) maxVals[i] = smoothed[i];

    float normed = (smoothed[i] - minVals[i]) / (maxVals[i] - minVals[i] + 0.0001);
    normed = constrain(normed, 0.0, 1.0);

    mappedValues[i] = map(normed * 1000, 0, 1000, 1, 10);
    activated[i] = normed > activationThreshold ? 1 : 0;

    if (activated[i] == 1) anyActive = true;
    if (mappedValues[i] < 1 || mappedValues[i] > 10) allMappedValid = false;

    // 打印调试信息
    Serial.print("A");
    Serial.print(i);
    Serial.print(" smoothed: "); Serial.print(smoothed[i], 4);
    Serial.print(" | min: "); Serial.print(minVals[i], 4);
    Serial.print(" | max: "); Serial.print(maxVals[i], 4);
    Serial.print(" | norm: "); Serial.print(normed, 3);
    Serial.print(" | mapped: "); Serial.print(mappedValues[i]);
    Serial.print(" | activated: "); Serial.println(activated[i]);
  }

  unsigned long now = millis();

  // 新的触发逻辑：任意一个激活 且 所有 mapped 合法
  if (anyActive && allMappedValid && (now - lastTriggerTime > debounceTime)) {
    Serial.print("DATA,");
    Serial.print(mappedValues[0]); Serial.print(",");
    Serial.print(mappedValues[1]); Serial.print(",");
    Serial.print(mappedValues[2]); Serial.print(",");
    Serial.println(mappedValues[3]);

    lastTriggerTime = now;
  }

  delay(50);
}
