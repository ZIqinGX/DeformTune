// ======= PressureSensor 类定义 =======
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

      if (_smoothed < _minVal) {
        _minVal = (_minVal * 9 + _smoothed) / 10.0;
      }
      if (_smoothed > _maxVal) {
        _maxVal = (_maxVal * 9 + _smoothed) / 10.0;
      } else {
        _maxVal = _maxVal * 0.999; // 缓慢下降，避免锁死
      }
    }

    float getNorm() {
      return constrain((_smoothed - _minVal) / (_maxVal - _minVal + 0.0001), 0.0, 1.0);
    }

    int getMappedValue() {
      float norm = getNorm();
      return 1 + int(norm * 9); // 映射到 1~10
    }

    bool isActivated(float threshold = 0.02) {
      return (_smoothed - _minVal) > threshold;
    }

    void debugPrint() {
      float norm = getNorm();
      Serial.print("📊 smoothed: ");
      Serial.print(_smoothed, 4);
      Serial.print(" | min: ");
      Serial.print(_minVal, 4);
      Serial.print(" | max: ");
      Serial.print(_maxVal, 4);
      Serial.print(" | diff: ");
      Serial.print(_smoothed - _minVal, 4);
      Serial.print(" | norm: ");
      Serial.print(norm, 3);
      Serial.print(" | mapped: ");
      Serial.print(getMappedValue());
      Serial.print(" | activated: ");
      Serial.println(isActivated());
    }

  private:
    int _pin;
    float _alpha;
    float _smoothed;
    float _minVal;
    float _maxVal;
};

// ======= 实例化传感器 A0 和 A1 =======
PressureSensor sensorA0(A0);
PressureSensor sensorA1(A1);

unsigned long lastSendTime = 0;
const unsigned long sendInterval = 100;
bool wasActive = false;

void setup() {
  Serial.begin(9600);
  delay(500);
  Serial.println("✅ 系统启动中：请勿按压...");

  for (int i = 0; i < 100; i++) {
    sensorA0.update();
    sensorA1.update();
    delay(10);
  }

  Serial.println("✅ 初始基线已记录，系统准备就绪！");
}

void loop() {
  sensorA0.update();
  sensorA1.update();

  bool isNowActive = sensorA0.isActivated() || sensorA1.isActivated();

  // 打印详细调试信息
  sensorA0.debugPrint();
  sensorA1.debugPrint();
  Serial.print("isNowActive: ");
  Serial.print(isNowActive);
  Serial.print(" | wasActive: ");
  Serial.println(wasActive);

  if (isNowActive && !wasActive) {
    unsigned long now = millis();
    if (now - lastSendTime > sendInterval) {
      int val0 = sensorA0.getMappedValue();
      int val1 = sensorA1.getMappedValue();

      Serial.print("🎵 映射值输出：");
      Serial.print(val0);
      Serial.print(",");
      Serial.println(val1);

      lastSendTime = now;
    }
  }

  wasActive = isNowActive;

  delay(100);  // 控制打印频率
}
