// ========== PressureSensor 类 ==========
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
        _maxVal *= 0.999;  // max 逐渐衰减
      }
    }

    float getNorm() {
      float rawNorm = (_smoothed - _minVal) / (_maxVal - _minVal + 0.0001);
      float clipped = constrain(rawNorm, 0.0, 1.0);
      if (!isActivated() || clipped < 0.05) return 0.0;
      return clipped;
    }

    int getMappedValue() {
      float norm = getNorm();
      return 1 + int(norm * 9);  // 映射到 1~10
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

// ========== 实例化两个压力传感器 ==========
PressureSensor sensorA0(A0);
PressureSensor sensorA1(A1);

unsigned long lastSendTime = 0;
const unsigned long sendInterval = 100;
bool triggerReady = true;

void setup() {
  Serial.begin(9600);
  delay(1000);
  Serial.println("✅ 系统启动中... 初始化基线中");

  // 采集初始数据作为 baseline
  for (int i = 0; i < 100; i++) {
    sensorA0.update();
    sensorA1.update();
    delay(10);
  }

  Serial.println("✅ 基线已设置，系统准备就绪！");
}

void loop() {
  sensorA0.update();
  sensorA1.update();

  bool isNowActive = sensorA0.isActivated() || sensorA1.isActivated();

  // ✅ 本地调试信息，仅串口查看
  sensorA0.debugPrint();
  sensorA1.debugPrint();
  Serial.print("isNowActive: ");
  Serial.print(isNowActive);
  Serial.print(" | triggerReady: ");
  Serial.println(triggerReady);

  // ✅ 映射值仅在激活时发送给 Python
  if (isNowActive && triggerReady) {
    unsigned long now = millis();
    if (now - lastSendTime > sendInterval) {
      int val0 = sensorA0.getMappedValue();
      int val1 = sensorA1.getMappedValue();

      // ✅ 唯一发送给 Python 的串口格式：DATA,x,y
      Serial.print("DATA,");
      Serial.print(val0);
      Serial.print(",");
      Serial.println(val1);

      lastSendTime = now;
      triggerReady = false;
    }
  }

  if (!isNowActive) {
    triggerReady = true;
  }

  delay(100);  // 控制频率（调试更稳定）
}
