// === 参数设置 ===
const int analogPins[4] = {A0, A1, A2, A3};
float smoothed[4] = {0.0, 0.0, 0.0, 0.0};
float minVals[4] = {1.0, 1.0, 1.0, 1.0};
float maxVals[4] = {0.0, 0.0, 0.0, 0.0};
int mappedValues[4] = {1, 1, 1, 1};
int activated[4] = {0, 0, 0, 0};

float alpha = 0.2;                  // 平滑系数
float activationThreshold = 0.3;    // 触发的归一化阈值
unsigned long debounceTime = 1000;  // 防抖间隔（毫秒）
unsigned long lastTriggerTime = 0;

bool hasInteracted = false;         // 是否已被用户主动触发过

// === 初始化 ===
void setup() {
  Serial.begin(9600);
  delay(1000);
  Serial.println("✅ Arduino 启动完成");
}

// === 主循环 ===
void loop() {
  bool anyActive = false;

  for (int i = 0; i < 4; i++) {
    int raw = analogRead(analogPins[i]);
    float norm = raw / 1023.0;

    // 更新平滑值
    smoothed[i] = alpha * norm + (1 - alpha) * smoothed[i];

    // 动态归一化
    if (smoothed[i] < minVals[i]) minVals[i] = smoothed[i];
    if (smoothed[i] > maxVals[i]) maxVals[i] = smoothed[i];

    float normed = (smoothed[i] - minVals[i]) / (maxVals[i] - minVals[i] + 0.0001);
    normed = constrain(normed, 0.0, 1.0);
    mappedValues[i] = map(normed * 1000, 0, 1000, 1, 10);

    activated[i] = normed > activationThreshold ? 1 : 0;
    if (activated[i] == 1) anyActive = true;

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

  // 用户第一次按下，才开始允许播放
  if (anyActive) hasInteracted = true;

  unsigned long now = millis();
  if (hasInteracted && anyActive && (now - lastTriggerTime > debounceTime)) {
    Serial.print("DATA,");
    Serial.print(mappedValues[0]); Serial.print(",");
    Serial.print(mappedValues[1]); Serial.print(",");
    Serial.print(mappedValues[2]); Serial.print(",");
    Serial.println(mappedValues[3]);

    lastTriggerTime = now;
  }

  delay(50);
}
