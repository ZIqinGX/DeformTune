// ======= PressureSensor 类定义 =======
class PressureSensor {
  public:
    PressureSensor(int pin, float alpha = 0.3) {
      _pin = pin;
      _alpha = alpha;
      _smoothed = 0.0;
      _minVal = 1.0;
    }

    void update() {
      float val = analogRead(_pin) / 1023.0;
      _smoothed = _alpha * val + (1 - _alpha) * _smoothed;
      if (_smoothed < _minVal) {
        _minVal = (_minVal * 9 + _smoothed) / 10.0; // 平滑更新基线
      }
    }

    int getMappedValue() {
      float norm = (_smoothed - _minVal) / (1.0 - _minVal + 0.0001); // 上升映射
      norm = constrain(norm, 0.0, 1.0);
      return 1 + int(norm * 9);  // 映射为 1~10
    }

    bool isActivated(float threshold = 0.02) {
      return (_smoothed - _minVal) > threshold;  // 触发：电压上升
    }

    void debugPrint() {
      Serial.print("📊 smoothed: ");
      Serial.print(_smoothed, 4);
      Serial.print(" | min: ");
      Serial.print(_minVal, 4);
      Serial.print(" | diff: ");
      Serial.print(_smoothed - _minVal, 4);
      Serial.print(" | activated: ");
      Serial.println(isActivated());
    }

  private:
    int _pin;
    float _alpha;
    float _smoothed;
    float _minVal;
};

// ======= 实例化两个传感器（A0 和 A1）=======
PressureSensor sensorA0(A0);
PressureSensor sensorA1(A1);

unsigned long lastSendTime = 0;
const unsigned long sendInterval = 100;
bool wasActive = false;

// ======= setup：初始化并记录初始基线 =======
void setup() {
  Serial.begin(9600);
  delay(500);
  Serial.println("✅ 系统启动中：请勿按压...");

  // 初始化读取，建立初始 _minVal
  for (int i = 0; i < 100; i++) {
    sensorA0.update();
    sensorA1.update();
    delay(10);
  }

  Serial.println("✅ 初始基线已记录，系统准备就绪！");
}

// ======= loop 主程序 =======
void loop() {
  sensorA0.update();
  sensorA1.update();

  bool isNowActive = sensorA0.isActivated() || sensorA1.isActivated();

  // 打印调试信息
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

      Serial.print("🎵 输出映射值：");
      Serial.print(val0);
      Serial.print(",");
      Serial.println(val1);

      lastSendTime = now;
    }
  }

  wasActive = isNowActive;

  delay(100);  // ✅ 降低刷新频率，防止刷屏
}
