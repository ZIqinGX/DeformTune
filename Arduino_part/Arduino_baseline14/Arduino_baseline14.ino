class PressureSensor {
  public:
    PressureSensor(int pin, float alpha = 0.3) {
      _pin = pin;
      _alpha = alpha;
      _smoothed = 0.0;
      _minVal = 1.0;
      _maxVal = 0.0;
    }

    void update() {
      float val = analogRead(_pin) / 1023.0;
      _smoothed = _alpha * val + (1 - _alpha) * _smoothed;
      if (_smoothed < _minVal) _minVal = (_minVal * 9 + _smoothed) / 10.0;
      if (_smoothed > _maxVal) _maxVal = (_maxVal * 9 + _smoothed) / 10.0;
      else _maxVal *= 0.999;
    }

    float getNorm() {
      float norm = (_smoothed - _minVal) / (_maxVal - _minVal + 0.0001);
      if (!isActivated() || norm < 0.05) return 0.0;
      return constrain(norm, 0.0, 1.0);
    }

    int getMappedValue() {
      return 1 + int(getNorm() * 9);
    }

    bool isActivated(float threshold = 0.02) {
      return (_smoothed - _minVal) > threshold;
    }

  private:
    int _pin;
    float _alpha, _smoothed, _minVal, _maxVal;
};

PressureSensor sensorA0(A0), sensorA1(A1), sensorA2(A2), sensorA3(A3);

unsigned long lastSendTime = 0;
const unsigned long sendInterval = 100;
bool triggerReady = true;

void setup() {
  Serial.begin(9600);
  delay(1000);
  Serial.println("✅ 系统启动，初始化中...");
  for (int i = 0; i < 100; i++) {
    sensorA0.update(); sensorA1.update(); sensorA2.update(); sensorA3.update();
    delay(10);
  }
  Serial.println("✅ 初始化完成");
}

void loop() {
  sensorA0.update(); sensorA1.update(); sensorA2.update(); sensorA3.update();

  bool isNowActive = sensorA0.isActivated() || sensorA1.isActivated() || sensorA2.isActivated() || sensorA3.isActivated();

  if (isNowActive && triggerReady) {
    unsigned long now = millis();
    if (now - lastSendTime > sendInterval) {
      int val0 = sensorA0.getMappedValue();
      int val1 = sensorA1.getMappedValue();
      int val2 = sensorA2.getMappedValue();
      int val3 = sensorA3.getMappedValue();
      Serial.print("DATA,");
      Serial.print(val0); Serial.print(",");
      Serial.print(val1); Serial.print(",");
      Serial.print(val2); Serial.print(",");
      Serial.println(val3);
      lastSendTime = now;
      triggerReady = false;
    }
  }
  if (!isNowActive) triggerReady = true;
  delay(100);
}
