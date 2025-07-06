// ========== Velostat 双通道感应 + 映射输出 + 调试打印 ==========

class PressureSensor {
  public:
    PressureSensor(int pin, float alpha = 0.1, int minStableFrames = 50, float noiseThreshold = 0.005) {
      _pin = pin;
      _alpha = alpha;
      _minStableFrames = minStableFrames;
      _noiseThreshold = noiseThreshold;
      _minVal = 1.0;
      _maxVal = 0.0;
      _stableCount = 0;
      _smoothed = 0.0;
    }

    void update() {
      float val = analogRead(_pin) / 1023.0;
      _smoothed = _alpha * val + (1 - _alpha) * _smoothed;

      if (abs(_smoothed - _minVal) < _noiseThreshold) {
        _stableCount++;
        if (_stableCount > _minStableFrames) {
          _minVal = (_minVal * 9 + _smoothed) / 10.0;
          _stableCount = _minStableFrames;
        }
      } else {
        _stableCount = 0;
      }

      if (_smoothed > _maxVal) {
        _maxVal = _smoothed;
      }
    }

    int getMappedValue() {
      float norm = (_smoothed - _minVal) / (_maxVal - _minVal + 0.0001);
      norm = constrain(norm, 0.0, 1.0);
      return 1 + int(norm * 9);  // 映射为 1~10
    }

    bool isActivated(float threshold = 0.001) {
      return (_smoothed - _minVal) > threshold;
    }

    void debugPrint(String label = "") {
      Serial.print(label);
      Serial.print(" smoothed: ");
      Serial.print(_smoothed, 4);
      Serial.print(" | min: ");
      Serial.print(_minVal, 4);
      Serial.print(" | diff: ");
      Serial.println(_smoothed - _minVal, 4);
    }

  private:
    int _pin;
    float _alpha;
    float _smoothed;
    float _minVal;
    float _maxVal;
    int _stableCount;
    int _minStableFrames;
    float _noiseThreshold;
};

// ========== 实例化传感器 ==========

PressureSensor sensorA0(A0);
PressureSensor sensorA1(A1);

unsigned long lastSendTime = 0;
const unsigned long sendInterval = 100;

bool wasActive = false;  // 边缘触发锁

void setup() {
  Serial.begin(9600);
  delay(1000);
  Serial.println("✅ 系统已启动，等待压力输入...");
}

void loop() {
  sensorA0.update();
  sensorA1.update();

  // 调试打印
  sensorA0.debugPrint("A0");
  sensorA1.debugPrint("A1");

  bool isNowActive = sensorA0.isActivated(0.001) || sensorA1.isActivated(0.001);

  if (isNowActive && !wasActive) {
    unsigned long now = millis();
    if (now - lastSendTime > sendInterval) {
      int val0 = sensorA0.getMappedValue();
      int val1 = sensorA1.getMappedValue();

      Serial.println("⚡ 检测到激活，准备输出...");
      Serial.print(val0);
      Serial.print(",");
      Serial.println(val1);

      lastSendTime = now;
    }
  }

  // 显示状态是否改变
  Serial.print("isNowActive: ");
  Serial.print(isNowActive);
  Serial.print(" | wasActive: ");
  Serial.println(wasActive);

  wasActive = isNowActive;
  delay(1000);  // 稍作延时，避免刷屏
}
